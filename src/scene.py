# scene.py
import sys
import time
from math import sin, cos, radians

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import OpenGL.GLUT as GLUT  # Importação como objeto para acesso seguro a constantes

# Módulos do projeto
import lighting 
import garage
import tractor
import farm


# ---------------------------------------------------------
# CONSTANTES E CONFIGURAÇÕES
# ---------------------------------------------------------
CAM_FREE = 0
CAM_COCKPIT = 1
CAM_CHASE = 2

# Input Settings
MOUSE_SENS = 0.05
MOVE_SPEED = 10.0
VERT_SPEED = 6.0
MOUSE_SMOOTH = 0.25

# Window Settings
screen_width = 800
screen_height = 600
center_x = 400
center_y = 300


# ---------------------------------------------------------
# ESTADO GLOBAL
# ---------------------------------------------------------

# Câmaras
cam_mode = CAM_FREE

# Free camera
free_pos = [91.50, 8.68, 149.19]
free_yaw = 220.0
free_pitch = -10.0

# Cockpit camera
cockpit_yaw_offset = 0.0
cockpit_pitch = 0.0
COCKPIT_BASE_YAW = 90

# Chase camera
chase_dist = 12.0
chase_orbit_angle = 0.0

# Mouse state
_warping_mouse = False
mouse_dx_smooth = 0.0
mouse_dy_smooth = 0.0

# UI
help_visible = False

# Textures
_ground_tex_id = None
_path_tex_id = None
_debug_ground_once = False

# Inputs (Teclado)
key_down = {'w': False, 's': False, 'a': False, 'd': False, 'q': False, 'e': False}
arrow_down = {'up': False, 'down': False, 'left': False, 'right': False}

# Tempo / FPS
_last_time = time.time()
_fps_accum = 0.0
_fps_frames = 0


# ---------------------------------------------------------
# LÓGICA DE CÂMARA
# ---------------------------------------------------------

def _update_free_cam(dt: float):
    global free_pos
    yaw_rad = radians(free_yaw)
    pitch_rad = radians(free_pitch)

    fx = cos(pitch_rad) * sin(yaw_rad)
    fy = sin(pitch_rad)
    fz = cos(pitch_rad) * cos(yaw_rad)
    
    len_xz = (fx * fx + fz * fz) ** 0.5 or 1.0
    fwd_x = fx / len_xz
    fwd_z = fz / len_xz
    
    right_x = -cos(yaw_rad)
    right_z =  sin(yaw_rad)

    speed = MOVE_SPEED * dt
    vspeed = VERT_SPEED * dt

    if key_down['w']:
        free_pos[0] += fwd_x * speed
        free_pos[2] += fwd_z * speed
    if key_down['s']:
        free_pos[0] -= fwd_x * speed
        free_pos[2] -= fwd_z * speed
    if key_down['a']:
        free_pos[0] -= right_x * speed
        free_pos[2] -= right_z * speed
    if key_down['d']:
        free_pos[0] += right_x * speed
        free_pos[2] += right_z * speed
    if key_down['q']: free_pos[1] += vspeed
    if key_down['e']: free_pos[1] -= vspeed


def apply_camera():
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    tx, tz = tractor.get_position()
    yaw_deg = tractor.get_direction_deg()
    yaw_rad = radians(yaw_deg)

    if cam_mode == CAM_CHASE:
        theta = radians(chase_orbit_angle)
        fwd_x = cos(yaw_rad + radians(180))
        fwd_z = sin(yaw_rad + radians(180))
        
        base_x = tx - fwd_x * chase_dist
        base_z = tz - fwd_z * chase_dist
        
        dx = base_x - tx
        dz = base_z - tz
        rot_x = dx * cos(theta) - dz * sin(theta)
        rot_z = dx * sin(theta) + dz * cos(theta)
        
        gluLookAt(tx + rot_x, 10.0, tz + rot_z,
                  tx, 5.0, tz,
                  0.0, 1.0, 0.0)

    elif cam_mode == CAM_COCKPIT:
        fwd_x = cos(yaw_rad)
        fwd_z = sin(yaw_rad)
        right_x = cos(yaw_rad + radians(90))
        right_z = sin(yaw_rad + radians(90))

        seat_x = tx + fwd_x * 2.0
        seat_z = tz + fwd_z * 2.0
        seat_y = 6.0

        look_yaw = yaw_rad + radians(180) + radians(cockpit_yaw_offset)
        look_pitch = radians(cockpit_pitch)
        
        lx = cos(look_yaw) * cos(look_pitch)
        ly = sin(look_pitch)
        lz = sin(look_yaw) * cos(look_pitch)

        gluLookAt(seat_x, seat_y, seat_z,
                  seat_x + lx, seat_y + ly, seat_z + lz,
                  0.0, 1.0, 0.0)

    else: # CAM_FREE
        yaw_rad = radians(free_yaw)
        pitch_rad = radians(free_pitch)
        fx = cos(pitch_rad) * sin(yaw_rad)
        fy = sin(pitch_rad)
        fz = cos(pitch_rad) * cos(yaw_rad)
        ex, ey, ez = free_pos
        gluLookAt(ex, ey, ez, ex + fx, ey + fy, ez + fz, 0.0, 1.0, 0.0)


# ---------------------------------------------------------
# FUNÇÕES AUXILIARES
# ---------------------------------------------------------

def _lock_cursor():
    glutSetCursor(GLUT_CURSOR_NONE)

def _unlock_cursor():
    glutSetCursor(GLUT_CURSOR_LEFT_ARROW)

def set_ground_textures(g_id, p_id):
    global _ground_tex_id, _path_tex_id
    _ground_tex_id = g_id
    _path_tex_id = p_id

def _draw_text_bitmap(x, y, text):
    """Função auxiliar para desenhar texto 2D com segurança."""
    # Usamos o GLUT. explícito para garantir que a constante existe
    try:
        font = GLUT_BITMAP_HELVETICA_18
    except NameError:
        font = GLUT.GLUT_BITMAP_HELVETICA_18

    glRasterPos2f(x, y)
    for char in text:
        try:
            glutBitmapCharacter(font, ord(char))
        except NameError:
            GLUT.glutBitmapCharacter(font, ord(char))


# ---------------------------------------------------------
# RENDERING (DRAW)
# ---------------------------------------------------------

def draw_ground():
    global _debug_ground_once
    if not _debug_ground_once:
        print(f"[GROUND] Tex IDs: {_ground_tex_id}, {_path_tex_id}")
        _debug_ground_once = True

    size = 400
    tile = 48.0
    glEnable(GL_TEXTURE_2D)
    glColor3f(1.0, 1.0, 1.0)

    # Relva
    if _ground_tex_id: glBindTexture(GL_TEXTURE_2D, _ground_tex_id)
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0);   glVertex3f(-size, 0.0, -size)
    glTexCoord2f(tile, 0.0);  glVertex3f( size, 0.0, -size)
    glTexCoord2f(tile, tile); glVertex3f( size, 0.0,  size)
    glTexCoord2f(0.0, tile);  glVertex3f(-size, 0.0,  size)
    glEnd()

    # Caminho
    if _path_tex_id:
        glBindTexture(GL_TEXTURE_2D, _path_tex_id)
        path_w = 8.0
        x_left = -path_w / 2
        x_right = path_w / 2
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0);   glVertex3f(x_left, 0.01, 120.0)
        glTexCoord2f(1.0, 0.0);   glVertex3f(x_right, 0.01, 120.0)
        glTexCoord2f(1.0, 20.0);  glVertex3f(x_right, 0.01, -40.01)
        glTexCoord2f(0.0, 20.0);  glVertex3f(x_left, 0.01, -40.01)
        glEnd()


def draw_overlay():
    """Desenha a interface 2D (HUD) por cima da cena 3D."""
    global screen_width, screen_height, help_visible

    # Guardar estado 3D
    glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, screen_width, 0, screen_height)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Configurar para 2D
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_FOG)
    glDisable(GL_TEXTURE_2D)

    # --- Conteúdo da UI ---
    if help_visible:
        # Fundo semi-transparente
        glEnable(GL_BLEND)
        glColor4f(0.0, 0.0, 0.0, 0.0) # Nota: No original estava alpha 0.0? Mantido conforme input.
        padding = 20
        box_w = 300
        box_h = 420
        x1, y1 = padding, screen_height - box_h - padding
        x2, y2 = padding + box_w, screen_height - padding
        
        glBegin(GL_QUADS)
        glVertex2f(x1, y1); glVertex2f(x2, y1)
        glVertex2f(x2, y2); glVertex2f(x1, y2)
        glEnd()
        glDisable(GL_BLEND)

        # Texto
        glColor3f(1.0, 1.0, 1.0)
        line_height = 25
        lines = [
            "COMANDOS",
            "[ H ] Esconder Ajuda",
            "",
            "GERAL:",
            "[ F ] Dia / Noite",
            "[ Rato ] Olhar em Volta",
            "[ A, W, S, D ] Mover Câmara Livre",
            "[ Q, E ] Subir/Descer Câmara Livre",
            "[ 1 ] Câmara Livre",
            "[ 2 ] Primeira Pessoa",
            "[ 3 ] Terceira Pessoa",
            "",
            "TRATOR:",
            "[ Setas ] Mover",
            "[ L / R ] Portas Trator",
            "",
            "INTERACAO:",
            "[ O ] Portão Garagem",
            "[ G ] Luz Garagem",
        ]

        for i, line in enumerate(lines):
            _draw_text_bitmap(20, screen_height - 30 - (i * line_height), line)

    else:
        # Modo Minimizado
        glColor3f(1.0, 1.0, 1.0)
        _draw_text_bitmap(20, screen_height - 30, "[ H ] Comandos")

    # Restaurar estado 3D
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glPopAttrib()


def display():
    lighting.update()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_CULL_FACE)

    apply_camera()

    lighting.draw_indicators()
    draw_ground()
    farm.draw()
    garage.draw()
    tractor.draw()

    draw_overlay()

    glutSwapBuffers()


def reshape(w, h):
    global screen_width, screen_height, center_x, center_y
    if h == 0: h = 1
    screen_width, screen_height = w, h
    center_x, center_y = w // 2, h // 2
    
    glViewport(0, 0, w, h)
    
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, float(w)/h, 0.1, 500.0)
    glMatrixMode(GL_MODELVIEW)


# ---------------------------------------------------------
# INPUT HANDLERS
# ---------------------------------------------------------

def keyboard(key, x, y):
    global cam_mode, cockpit_yaw_offset, cockpit_pitch
    global help_visible
    
    if isinstance(key, bytes): key = key.decode("utf-8", errors="ignore")
    key = key.lower()

    # Câmaras
    if key == '1': cam_mode = CAM_FREE
    elif key == '2':
        cam_mode = CAM_COCKPIT
        cockpit_yaw_offset = 0.0
        cockpit_pitch = 0.0
    elif key == '3': cam_mode = CAM_CHASE

    # Trator e Garagem
    elif key == 'l':
        if tractor.door_left_angle < 1.0: tractor.rotate_left_door(90)
        else: tractor.rotate_left_door(-90)
    elif key == 'r':
        if tractor.door_right_angle < 1.0: tractor.rotate_right_door(90)
        else: tractor.rotate_right_door(-90)
    elif key == 'o':
        garage.toggle_door()

    # Luzes e UI
    elif key == 'f':
        lighting.sun_enabled = not lighting.sun_enabled
        print(f"[LIGHT] Sun: {'DAY' if lighting.sun_enabled else 'NIGHT'}")

    elif key == 'g':
        lighting.garage_light_enabled = not lighting.garage_light_enabled
        print(f"[LIGHT] Garage Lamp: {'ON' if lighting.garage_light_enabled else 'OFF'}")

    elif key == 'h':
        help_visible = not help_visible
        print(f"[UI] Ajuda: {'Visivel' if help_visible else 'Oculta'}")

    if cam_mode != CAM_COCKPIT and key in key_down:
        key_down[key] = True
    
    glutPostRedisplay()


def keyboard_up(key, x, y):
    if isinstance(key, bytes): key = key.decode("utf-8")
    key = key.lower()
    if key in key_down: key_down[key] = False


def special_keys(key, x, y):
    if key == GLUT_KEY_UP:      arrow_down['up'] = True
    elif key == GLUT_KEY_DOWN:  arrow_down['down'] = True
    elif key == GLUT_KEY_LEFT:  arrow_down['left'] = True
    elif key == GLUT_KEY_RIGHT: arrow_down['right'] = True


def special_keys_up(key, x, y):
    if key == GLUT_KEY_UP:      arrow_down['up'] = False
    elif key == GLUT_KEY_DOWN:  arrow_down['down'] = False
    elif key == GLUT_KEY_LEFT:  arrow_down['left'] = False
    elif key == GLUT_KEY_RIGHT: arrow_down['right'] = False


def mouse_motion(x, y):
    global free_yaw, free_pitch, cockpit_yaw_offset, cockpit_pitch
    global _warping_mouse, mouse_dx_smooth, mouse_dy_smooth

    if _warping_mouse:
        _warping_mouse = False
        return
    if cam_mode not in (CAM_FREE, CAM_COCKPIT): return

    dx = x - center_x
    dy = y - center_y
    alpha = MOUSE_SMOOTH
    mouse_dx_smooth = mouse_dx_smooth * (1-alpha) + dx * alpha
    mouse_dy_smooth = mouse_dy_smooth * (1-alpha) + dy * alpha

    if cam_mode == CAM_FREE:
        free_yaw -= mouse_dx_smooth * MOUSE_SENS
        free_yaw %= 360.0
        free_pitch -= mouse_dy_smooth * MOUSE_SENS
        free_pitch = max(-89.0, min(89.0, free_pitch))
    elif cam_mode == CAM_COCKPIT:
        sens = MOUSE_SENS * 0.5
        cockpit_yaw_offset += mouse_dx_smooth * sens
        cockpit_yaw_offset = max(-80, min(80, cockpit_yaw_offset))
        cockpit_pitch -= mouse_dy_smooth * sens
        cockpit_pitch = max(-45, min(45, cockpit_pitch))

    _warping_mouse = True
    glutWarpPointer(center_x, center_y)
    glutPostRedisplay()


def idle():
    global _last_time, _fps_accum, _fps_frames, chase_dist, chase_orbit_angle
    
    now = time.time()
    dt = now - _last_time
    _last_time = now
    if dt > 0.1: dt = 0.1

    if cam_mode == CAM_FREE:
        _update_free_cam(dt)
    elif cam_mode == CAM_CHASE:
        if key_down['w']: chase_dist = max(4.0, chase_dist - 15.0 * dt)
        if key_down['s']: chase_dist = min(25.0, chase_dist + 15.0 * dt)
        if key_down['a']: chase_orbit_angle += 60.0 * dt
        if key_down['d']: chase_orbit_angle -= 60.0 * dt

    # Atualizar físicas
    tractor.update(arrow_down['up'], arrow_down['down'],
                   arrow_down['left'], arrow_down['right'], dt)
    garage.update(dt)

    # Contador FPS
    _fps_accum += dt
    _fps_frames += 1
    if _fps_accum >= 1.0:
        print(f"[FPS] {_fps_frames / _fps_accum:.1f}")
        _fps_accum = 0.0
        _fps_frames = 0

    glutPostRedisplay()