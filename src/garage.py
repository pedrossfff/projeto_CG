# garage.py
from OpenGL.GL import *

# ---------------------------------------------------------
# CONSTANTES E CONFIGURAÇÕES
# ---------------------------------------------------------
GARAGE_DOOR_MESH_NAME = "door"
GARAGE_DOOR_OPEN_SPEED = 1.5
GARAGE_DOOR_MAX_TILT_DEG = 100

# Transformação da Garagem (World Space)
GARAGE_POS_X = 0.3
GARAGE_POS_Y = 2.8
GARAGE_POS_Z = -30.0
GARAGE_YAW   = 90.0
GARAGE_SCALE = 2.0

# Pivô da Porta (Local Space)
GARAGE_DOOR_HINGE_X = -5.1
GARAGE_DOOR_HINGE_Y = 3
GARAGE_DOOR_HINGE_Z = -0.1

DEBUG_PIVOTS = True

# ---------------------------------------------------------
# ESTADO GLOBAL
# ---------------------------------------------------------
garage_meshes = {}
garage_materials = {}

# 0.0 = fechada, 1.0 = aberta
garage_door_open     = 0.0
garage_door_open_tgt = 0.0


def set_meshes(meshes, materials):
    global garage_meshes, garage_materials
    garage_meshes = meshes
    garage_materials = materials


# ---------------------------------------------------------
# CONTROLO DA PORTA
# ---------------------------------------------------------

def open_door():
    global garage_door_open_tgt
    garage_door_open_tgt = 1.0

def close_door():
    global garage_door_open_tgt
    garage_door_open_tgt = 0.0

def toggle_door():
    global garage_door_open_tgt
    garage_door_open_tgt = 0.0 if garage_door_open_tgt > 0.5 else 1.0


def update(dt):
    """Anima a abertura/fecho da porta."""
    global garage_door_open
    if garage_door_open < garage_door_open_tgt:
        garage_door_open = min(garage_door_open + GARAGE_DOOR_OPEN_SPEED * dt,
                               garage_door_open_tgt)
    elif garage_door_open > garage_door_open_tgt:
        garage_door_open = max(garage_door_open - GARAGE_DOOR_OPEN_SPEED * dt,
                               garage_door_open_tgt)


# ---------------------------------------------------------
# DESENHO
# ---------------------------------------------------------

def _compute_door_transform():
    """Retorna o ângulo de inclinação baseado no estado (0..1)."""
    t = garage_door_open
    return t * GARAGE_DOOR_MAX_TILT_DEG


def draw_garage_door():
    door_mesh = garage_meshes.get(GARAGE_DOOR_MESH_NAME)
    if door_mesh is None:
        # Fallback se não encontrar o nome da malha
        for mesh in garage_meshes.values():
            mesh.draw(garage_materials)
        return

    tilt_deg = _compute_door_transform()

    glPushMatrix()
    # 1. Mover para o pivô
    glTranslatef(GARAGE_DOOR_HINGE_X,
                 GARAGE_DOOR_HINGE_Y,
                 GARAGE_DOOR_HINGE_Z)

    # 2. Rodar
    glRotatef(tilt_deg, 0.0, 0.0, -1.0)

    # 3. Voltar do pivô
    glTranslatef(-GARAGE_DOOR_HINGE_X,
                 -GARAGE_DOOR_HINGE_Y,
                 -GARAGE_DOOR_HINGE_Z)

    door_mesh.draw(garage_materials)
    glPopMatrix()


def draw():
    """Desenha a garagem completa."""
    if not garage_meshes: return

    glPushMatrix()
    glTranslatef(GARAGE_POS_X, GARAGE_POS_Y, GARAGE_POS_Z)
    if GARAGE_YAW != 0.0:
        glRotatef(GARAGE_YAW, 0.0, 1.0, 0.0)
    if GARAGE_SCALE != 1.0:
        glScalef(GARAGE_SCALE, GARAGE_SCALE, GARAGE_SCALE)

    # Malhas Estáticas
    for name, mesh in garage_meshes.items():
        if name == GARAGE_DOOR_MESH_NAME:
            continue
        mesh.draw(garage_materials)

    # Malha Animada
    draw_garage_door()

    glPopMatrix()