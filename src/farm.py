# farm.py
from OpenGL.GL import *

# Lista de objetos estáticos:
# { "meshes", "materials", "pos", "yaw", "scale" }
_farm_objects = []


def add_object(meshes, materials, pos=(0.0, 0.0, 0.0), yaw=0.0, scale=1.0):
    """Regista um OBJ estático na cena."""
    _farm_objects.append({
        "meshes": meshes,
        "materials": materials,
        "pos": pos,
        "yaw": yaw,
        "scale": scale,
    })


def draw():
    """Desenha todos os objetos registados na quinta."""
    for obj in _farm_objects:
        meshes    = obj["meshes"]
        materials = obj["materials"]
        x, y, z   = obj["pos"]
        yaw       = obj["yaw"]
        s         = obj["scale"]

        glPushMatrix()
        glTranslatef(x, y, z)
        
        if yaw != 0.0:
            glRotatef(yaw, 0.0, 1.0, 0.0)
        
        if s != 1.0:
            glScalef(s, s, s)

        for name, mesh in meshes.items():
            mesh.draw(materials)

        glPopMatrix()