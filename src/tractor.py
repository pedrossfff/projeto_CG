# tractor.py
from math import sin, cos, tan
from OpenGL.GL import *


# ---------------------------------------------------------
# CONSTANTES FÍSICAS E DE ANIMAÇÃO
# ---------------------------------------------------------
GLASS_ALPHA = 0.35

DEG2RAD = 0.017453292519943295
RAD2DEG = 57.29577951308232

# Dinâmica do Trator
BASE_SPEED          = 4.0     # velocidade (unidades/s)
MAX_STEER_DEG       = 30.0    # ângulo máx direção
STEER_SPEED_DEG     = 80.0    # velocidade rotação volante

BACK_SPIN_PER_UNIT  = 40.0    # rotação rodas trás por unidade
FRONT_SPIN_PER_UNIT = 60.0    # rotação rodas frente por unidade

DOOR_SPEED_DEG      = 120.0   # velocidade abertura portas

# Pivôs das Portas (espaço local)
LEFT_DOOR_PIVOT  = (2.2, -2.0, -2.0)
RIGHT_DOOR_PIVOT = (2.2, -2.0,  2.0)
LEFT_DOOR_SIGN  = -1.0
RIGHT_DOOR_SIGN = +1.0

# Pivôs das Rodas (espaço local)
BACK_WHEELS_PIVOT  = (3.55, 1.75, 0.0)
FRONT_WHEELS_PIVOT = (-3.6, 2.35, 0.0)

# Pivôs do Volante
STEERING_WHEEL_PIVOT  = (0.6, -1.25, 0.1)
STEERING_AXIS         = (-10.0, 7.0, -0.1)
STEERING_WHEEL_FACTOR = 3.0

# Distância entre eixos (Bicycle model)
WHEEL_BASE = 6.5


# ---------------------------------------------------------
# ESTADO GLOBAL DO TRATOR
# ---------------------------------------------------------
tractor_parts = {}
tractor_materials = {}

# Transformação Mundo
pos_x = 0.0
pos_z = 100.0
dir_angle = 90.0

# Rodas e Direção
wheel_spin_back = 0.0
wheel_spin_front = 0.0
steer_angle = 0.0

# Portas
door_left_angle = 0.0
door_right_angle = 0.0
door_left_target = 0.0
door_right_target = 0.0

# Debug
_printed_meshes = False


def set_meshes(parts: dict, materials: dict):
    """Regista as malhas e materiais carregados."""
    global tractor_parts, tractor_materials
    tractor_parts = parts
    tractor_materials = materials


# ---------------------------------------------------------
# LÓGICA DE ATUALIZAÇÃO (UPDATE)
# ---------------------------------------------------------

def update(moving_forward: bool, moving_back: bool,
           turning_left: bool, turning_right: bool,
           dt: float = 1.0):
    """Atualiza posição, direção e animações do trator."""
    global pos_x, pos_z, dir_angle
    global wheel_spin_back, wheel_spin_front, steer_angle
    global door_left_angle, door_right_angle

    # 1. Velocidade Linear
    v = 0.0
    if moving_forward: v += BASE_SPEED
    if moving_back:    v -= BASE_SPEED
    dist = v * dt

    # 2. Direção (Steering)
    steer_step = STEER_SPEED_DEG * dt
    if turning_left:
        steer_angle = max(steer_angle - steer_step, -MAX_STEER_DEG)
    if turning_right:
        steer_angle = min(steer_angle + steer_step,  MAX_STEER_DEG)
    
    # Auto-centrar volante
    if not turning_left and not turning_right:
        if steer_angle > 0.0:
            steer_angle = max(0.0, steer_angle - steer_step)
        elif steer_angle < 0.0:
            steer_angle = min(0.0, steer_angle + steer_step)

    # 3. Cálculo de Yaw (Modelo de Bicicleta)
    if abs(dist) > 1e-5 and abs(steer_angle) > 1e-3 and WHEEL_BASE > 1e-4:
        steer_rad = steer_angle * DEG2RAD
        turn_radius = WHEEL_BASE / tan(steer_rad)
        delta_yaw_rad = dist / turn_radius
        dir_angle += delta_yaw_rad * RAD2DEG

    # 4. Nova Posição
    heading_rad = dir_angle * DEG2RAD
    pos_x -= dist * cos(heading_rad)
    pos_z -= dist * sin(heading_rad)

    # 5. Rotação das Rodas
    wheel_spin_back  += BACK_SPIN_PER_UNIT  * dist
    wheel_spin_front += FRONT_SPIN_PER_UNIT * dist

    # 6. Animação das Portas
    if door_left_angle != door_left_target:
        step = DOOR_SPEED_DEG * dt
        if door_left_angle < door_left_target:
            door_left_angle = min(door_left_angle + step, door_left_target)
        else:
            door_left_angle = max(door_left_angle - step, door_left_target)

    if door_right_angle != door_right_target:
        step = DOOR_SPEED_DEG * dt
        if door_right_angle < door_right_target:
            door_right_angle = min(door_right_angle + step, door_right_target)
        else:
            door_right_angle = max(door_right_angle - step, door_right_target)


def rotate_left_door(delta_deg: float):
    global door_left_target
    door_left_target = max(0.0, min(90.0, door_left_target + delta_deg))

def rotate_right_door(delta_deg: float):
    global door_right_target
    door_right_target = max(0.0, min(90.0, door_right_target + delta_deg))


# ---------------------------------------------------------
# IDENTIFICAÇÃO DE MALHAS
# ---------------------------------------------------------

def _is_left_door(name: str) -> bool:
    n = name.lower()
    return "left_door" in n or ("door" in n and "left" in n)

def _is_right_door(name: str) -> bool:
    n = name.lower()
    return "right_door" in n or ("door" in n and "right" in n)

def _is_back_wheels(name: str) -> bool:
    lname = name.lower()
    return ("back_wheel" in lname or "rear_wheel" in lname or 
            "backwheels" in lname or "rearwheels" in lname)

def _is_front_wheels(name: str) -> bool:
    lname = name.lower()
    return ("front_wheel" in lname or "frontwheels" in lname or "fwheels" in lname)

def _is_steering_wheel(name: str) -> bool:
    return "steer" in name.lower()


# ---------------------------------------------------------
# DESENHO (DRAW)
# ---------------------------------------------------------

def _draw_wheel(mesh, pivot, spin_degrees):
    cx, cy, cz = pivot
    glPushMatrix()
    glTranslatef(cx, cy, cz)
    glRotatef(-spin_degrees, 0.0, 0.0, 1.0)
    glTranslatef(-cx, -cy, -cz)
    mesh.draw(tractor_materials)
    glPopMatrix()


def _draw_opaque_part(name: str, mesh):
    # Volante
    if _is_steering_wheel(name):
        glPushMatrix()
        sx, sy, sz = STEERING_WHEEL_PIVOT
        ax, ay, az = STEERING_AXIS
        glTranslatef(sx, sy, sz)
        glRotatef(steer_angle * STEERING_WHEEL_FACTOR, ax, ay, az)
        glTranslatef(-sx, -sy, -sz)
        mesh.draw(tractor_materials)
        glPopMatrix()
        return

    # Rodas Traseiras
    if _is_back_wheels(name):
        _draw_wheel(mesh, BACK_WHEELS_PIVOT, wheel_spin_back)
        return

    # Rodas Dianteiras (Direção + Rotação)
    if _is_front_wheels(name):
        glPushMatrix()
        px, py, pz = FRONT_WHEELS_PIVOT
        glTranslatef(px, py, pz)
        glRotatef(steer_angle, 0.0, 1.0, 0.0)
        glTranslatef(-px, -py, -pz)
        _draw_wheel(mesh, FRONT_WHEELS_PIVOT, wheel_spin_front)
        glPopMatrix()
        return

    # Outras partes opacas
    mesh.draw(tractor_materials)


def _draw_glass_part(name: str, mesh):
    lname = name.lower()

    if _is_left_door(name):
        glPushMatrix()
        px, py, pz = LEFT_DOOR_PIVOT
        glTranslatef(px, py, pz)
        glRotatef(LEFT_DOOR_SIGN * door_left_angle, 0.0, 1.0, 0.0)
        glTranslatef(-px, -py, -pz)
        mesh.draw(tractor_materials)
        glPopMatrix()
        return

    if _is_right_door(name):
        glPushMatrix()
        px, py, pz = RIGHT_DOOR_PIVOT
        glTranslatef(px, py, pz)
        glRotatef(RIGHT_DOOR_SIGN * door_right_angle, 0.0, 1.0, 0.0)
        glTranslatef(-px, -py, -pz)
        mesh.draw(tractor_materials)
        glPopMatrix()
        return

    if "glass" in lname:
        mesh.draw(tractor_materials)


def draw():
    global _printed_meshes
    if not tractor_parts: return

    glPushMatrix()
    glColor3f(1.0, 1.0, 1.0)

    # Transformação Global do Trator
    glTranslatef(pos_x, 4.0, pos_z)
    glRotatef(180.0, 1.0, 0.0, 0.0)
    glRotatef(dir_angle, 0.0, 1.0, 0.0)

    opaque_parts = []
    glass_parts  = []

    for name, mesh in tractor_parts.items():
        lname = name.lower()
        if _is_left_door(name) or _is_right_door(name) or ("glass" in lname):
            glass_parts.append((name, mesh))
        else:
            opaque_parts.append((name, mesh))

    # 1. Desenhar Partes Opacas
    for name, mesh in opaque_parts:
        _draw_opaque_part(name, mesh)

    # 2. Desenhar Vidros (com Blending)
    if glass_parts:
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        glDisable(GL_CULL_FACE)
        glColor4f(1.0, 1.0, 1.0, GLASS_ALPHA)

        for name, mesh in glass_parts:
            _draw_glass_part(name, mesh)

        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_CULL_FACE)
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)

    # Debug: Printar nomes das malhas uma vez
    if not _printed_meshes:
        for name in tractor_parts.keys():
            print("[MESH]", name)
        _printed_meshes = True

    glPopMatrix()


def get_position():
    return pos_x, pos_z

def get_direction_deg():
    return dir_angle