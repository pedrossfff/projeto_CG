# main.py
import sys
import os
from PIL import Image

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# Módulos do projeto
import tractor
import scene
import farm
import garage
import lighting
from obj_loader import load_obj_multipart


def load_texture(path, repeat=True):
    """Carrega uma textura de imagem para o OpenGL."""
    try:
        img = Image.open(path)
    except FileNotFoundError:
        print(f"[ERR] Texture not found: {path}")
        return None

    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img = img.convert("RGBA")
    img_data = img.tobytes()
    w, h = img.size

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    
    wrap = GL_REPEAT if repeat else GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
    glGenerateMipmap(GL_TEXTURE_2D)
    
    print(f"[TEX] Loaded: {path} -> ID {tex_id}")
    return tex_id


def setup_opengl():
    """Configura o estado inicial de renderização do OpenGL."""
    print("[GL] SETUP...")
    glEnable(GL_DEPTH_TEST)

    # Blend e Alpha para transparências (vidros)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.1)

    # Back-face culling
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    glFrontFace(GL_CCW)

    # Inicializar o sistema de luzes (Lighting)
    lighting.init()

    # Materiais genéricos
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.5, 0.5, 0.5, 1.0))
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 32.0)

    glShadeModel(GL_SMOOTH)
    
    # Texturas
    glEnable(GL_TEXTURE_2D)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)


def load_assets():
    """Carrega modelos 3D e texturas."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(base_dir, "..", "assets")
    models_dir = os.path.join(assets_dir, "models")
    tex_dir    = os.path.join(assets_dir, "textures")

    # --- TRACTOR ---
    try:
        tractor_path = os.path.join(models_dir, "Lambo", "Lambo.obj")
        parts, mats = load_obj_multipart(tractor_path)
        tractor.set_meshes(parts, mats)
        print("[ASSET] Tractor Loaded")
    except Exception as e: 
        print(f"[WARN] Tractor failed: {e}")

    # --- FARM PROPS ---
    farm_models = os.path.join(models_dir, "farm")
    
    # Garage
    try:
        g_path = os.path.join(farm_models, "garage.obj")
        g_parts, g_mats = load_obj_multipart(g_path)
        garage.set_meshes(g_parts, g_mats)
    except: 
        print("[WARN] Garage missing")

    # House
    try:
        h_path = os.path.join(farm_models, "House.obj")
        h_parts, h_mats = load_obj_multipart(h_path)
        farm.add_object(h_parts, h_mats, pos=(-50, -17, -15), yaw=90, scale=2.0)
    except: 
        print("[WARN] House missing")

    # Cows
    try:
        c_path = os.path.join(farm_models, "cow.obj")
        c_parts, c_mats = load_obj_multipart(c_path)
        farm.add_object(c_parts, c_mats, pos=(25, 0, 5), yaw=90, scale=0.3)
        farm.add_object(c_parts, c_mats, pos=(30, 0, 0), yaw=120, scale=0.3)
    except: 
        print("[WARN] Cow missing")

    # Trees
    try:
        t_path = os.path.join(farm_models, "tree.obj")
        t_parts, t_mats = load_obj_multipart(t_path)
        farm.add_object(t_parts, t_mats, pos=(-40, 6.2, -30), yaw=20, scale=2.0)
        farm.add_object(t_parts, t_mats, pos=(-30, 6.2, -35), yaw=-10, scale=2.2)
        farm.add_object(t_parts, t_mats, pos=(40, 6.2, -30), yaw=-30, scale=2.0)
    except: 
        print("[WARN] Tree missing")

    # --- TEXTURES ---
    grass_id = load_texture(os.path.join(tex_dir, "grass4.jpg"))
    dirt_id  = load_texture(os.path.join(tex_dir, "dirt.jpg"))
    scene.set_ground_textures(grass_id, dirt_id)


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"CG Tractor Farm Final")
    
    # Configuração inicial da cena
    scene._lock_cursor()
    scene.cam_mode = scene.CAM_FREE

    setup_opengl()
    load_assets()

    # Callbacks GLUT
    glutDisplayFunc(scene.display)
    glutReshapeFunc(scene.reshape)
    glutKeyboardFunc(scene.keyboard)
    glutKeyboardUpFunc(scene.keyboard_up)
    glutSpecialFunc(scene.special_keys)
    glutSpecialUpFunc(scene.special_keys_up)
    glutIdleFunc(scene.idle)
    glutPassiveMotionFunc(scene.mouse_motion)

    glutMainLoop()


if __name__ == "__main__":
    main()