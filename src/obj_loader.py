# obj_loader.py
# ------------------------------------------------------------
#  OBJ LOADER (multipart + materials + textures)
# ------------------------------------------------------------
import os
from typing import Optional
from OpenGL.GL import *
from PIL import Image


# ---------------------------------------------------------
# CLASSES
# ---------------------------------------------------------

class Material:
    def __init__(self, name: str):
        self.name: str = name
        self.texture_path: Optional[str] = None
        self.texture_id: Optional[int] = None


class ObjMesh:
    def __init__(self):
        self.vertices = []      # list[(x,y,z)]
        self.texcoords = []     # list[(u,v)]
        self.normals = []       # list[(nx,ny,nz)]

        # material_name -> list of faces
        # face = list[(vi, ti, ni)]
        self.faces_by_material = {}

        # Display List cache
        self._display_list = None

    def add_face(self, face, material_name):
        if material_name not in self.faces_by_material:
            self.faces_by_material[material_name] = []
        self.faces_by_material[material_name].append(face)

    def _build_display_list(self, materials):
        if self._display_list is not None:
            return 

        self._display_list = glGenLists(1)
        glNewList(self._display_list, GL_COMPILE)

        for mtl_name, faces in self.faces_by_material.items():
            mat = materials.get(mtl_name) if materials else None

            if mat and mat.texture_id:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, mat.texture_id)
            else:
                glDisable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, 0)

            glBegin(GL_TRIANGLES)
            for face in faces:
                for (vi, ti, ni) in face:
                    if ni is not None and self.normals:
                        nx, ny, nz = self.normals[ni]
                        glNormal3f(nx, ny, nz)

                    if ti is not None and self.texcoords:
                        u, v = self.texcoords[ti]
                        glTexCoord2f(u, v)

                    x, y, z = self.vertices[vi]
                    glVertex3f(x, y, z)
            glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)
        glEndList()

    def draw(self, materials=None):
        """Desenha a mesh usando Display Lists (ou fallback imediato)."""
        if materials is not None:
            if self._display_list is None:
                self._build_display_list(materials)
            glCallList(self._display_list)
            return

        # Fallback: Immediate mode
        for mtl_name, faces in self.faces_by_material.items():
            glBegin(GL_TRIANGLES)
            for face in faces:
                for (vi, ti, ni) in face:
                    x, y, z = self.vertices[vi]
                    glVertex3f(x, y, z)
            glEnd()


# ---------------------------------------------------------
# LOADERS AUXILIARES
# ---------------------------------------------------------

def load_texture(path):
    """Carrega imagem para textura OpenGL."""
    if not os.path.isfile(path):
        print(f"[WARN] Texture file not found: {path}")
        return None

    img = Image.open(path).convert("RGBA")
    img_data = img.tobytes("raw", "RGBA", 0, -1)
    width, height = img.size

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)

    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glBindTexture(GL_TEXTURE_2D, 0)
    
    print(f"[TEX] Loaded texture {path} -> id {tex_id}")
    return tex_id


def load_mtl(mtl_path):
    """Lê ficheiro .mtl e carrega texturas associadas."""
    materials = {}
    current = None

    if not os.path.isfile(mtl_path):
        print(f"[WARN] MTL file not found: {mtl_path}")
        return materials

    base_dir = os.path.dirname(mtl_path)

    with open(mtl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            tag = parts[0]

            if tag == "newmtl":
                name = parts[1]
                current = Material(name)
                materials[name] = current

            elif tag == "map_Kd" and current is not None:
                tex_str = line.split(None, 1)[1].strip().strip('"')
                if os.path.isabs(tex_str):
                    tex_str = os.path.basename(tex_str)
                tex_path = os.path.join(base_dir, tex_str)
                current.texture_path = tex_path

    # Carregar texturas para GPU
    for m in materials.values():
        if m.texture_path:
            m.texture_id = load_texture(m.texture_path)

    return materials


# ---------------------------------------------------------
# MAIN OBJ LOADER FUNCTION
# ---------------------------------------------------------

def load_obj_multipart(path):
    """Lê OBJ Multipart + MTL e retorna (meshes, materials)."""
    meshes = {}
    current_name = None
    current_mesh = None
    current_material = None

    # Pools partilhadas
    verts = []
    texs = []
    norms = []

    materials = {}
    base_dir = os.path.dirname(path)

    def start_new_mesh(name):
        nonlocal current_mesh, current_name
        current_name = name
        current_mesh = ObjMesh()
        meshes[name] = current_mesh

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            tag = parts[0]

            if tag == "mtllib":
                mtl_file = parts[1]
                mtl_path = os.path.join(base_dir, mtl_file)
                print(f"[MTL] Loading material library: {mtl_path}")
                materials = load_mtl(mtl_path)

            elif tag in ("o", "g"):
                name = parts[1] if len(parts) > 1 else "unnamed"
                start_new_mesh(name)

            elif tag == "usemtl":
                current_material = parts[1]

            elif tag == "v":
                verts.append(tuple(map(float, parts[1:4])))

            elif tag == "vt":
                texs.append(tuple(map(float, parts[1:3])))

            elif tag == "vn":
                norms.append(tuple(map(float, parts[1:4])))

            elif tag == "f":
                if current_mesh is None:
                    start_new_mesh("default")

                face_raw = parts[1:]
                face = []

                for v_str in face_raw:
                    vals = v_str.split("/")
                    vi = int(vals[0]) - 1 if vals[0] else None
                    ti = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else None
                    ni = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else None
                    face.append((vi, ti, ni))

                # Triangulação simples
                if len(face) == 3:
                    current_mesh.add_face(face, current_material)
                elif len(face) == 4:
                    current_mesh.add_face([face[0], face[1], face[2]], current_material)
                    current_mesh.add_face([face[0], face[2], face[3]], current_material)
                else:
                    for i in range(1, len(face) - 1):
                        current_mesh.add_face([face[0], face[i], face[i+1]], current_material)

    # Atribuir dados às meshes
    for mesh in meshes.values():
        mesh.vertices = verts
        mesh.texcoords = texs
        mesh.normals = norms

    return meshes, materials