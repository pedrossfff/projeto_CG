# lighting.py
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# --- ESTADO GLOBAL ---
sun_enabled = True
garage_light_enabled = True


def init():
    """Configurações iniciais de qualidade visual e iluminação."""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)  # Sol
    glEnable(GL_LIGHT1)  # Garagem
    glEnable(GL_NORMALIZE)
    
    # --- FOG (Nevoeiro) ---
    # Esconde recorte dos polígonos ao longe e cria atmosfera
    glEnable(GL_FOG)
    glFogi(GL_FOG_MODE, GL_EXP2)   # Exponencial ao quadrado
    glFogf(GL_FOG_DENSITY, 0.004)  # Densidade
    glHint(GL_FOG_HINT, GL_NICEST)


def update():
    """Chamado a cada frame para atualizar cores, posições e atmosfera."""
    
    # Cores base
    day_color   = [0.6, 0.8, 1.0, 1.0]   # Azul céu
    night_color = [0.05, 0.05, 0.1, 1.0] # Azul meia-noite
    
    # --- 1. SOL / LUA (LIGHT0) ---
    if sun_enabled:
        # === DIA ===
        current_sky = day_color
        # Luz quente e brilhante
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  (1.0, 0.95, 0.8, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 0.9, 0.8, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT,  (0.4, 0.4, 0.4, 1.0))
    else:
        # === NOITE ===
        current_sky = night_color
        # Luz fria, pálida e fraca
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  (0.15, 0.15, 0.25, 1.0))
        glLightfv(GL_LIGHT0, GL_SPECULAR, (0.1, 0.1, 0.15, 1.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT,  (0.02, 0.02, 0.05, 1.0))

    # Aplicar cor ao Fundo e ao Nevoeiro
    glClearColor(*current_sky)
    glFogfv(GL_FOG_COLOR, current_sky)

    # Posicionar o Sol (Direcional)
    sun_dir = (GLfloat * 4)(0.3, 1.0, 0.4, 0.0)
    glLightfv(GL_LIGHT0, GL_POSITION, sun_dir)

    # --- 2. LUZ DA GARAGEM (LIGHT1 - Spotlight) ---
    garage_pos = (GLfloat * 4)(0.0, 12.0, -36.0, 1.0)
    glLightfv(GL_LIGHT1, GL_POSITION, garage_pos)

    if garage_light_enabled:
        # Cor: Laranja muito quente
        color = (1.0, 0.7, 0.3, 1.0)
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  color)
        glLightfv(GL_LIGHT1, GL_SPECULAR, color)

        # Configuração do Cone (Spotlight)
        spot_dir = (GLfloat * 3)(0.0, -1.0, 0.2)
        glLightfv(GL_LIGHT1, GL_SPOT_DIRECTION, spot_dir)
        glLightf(GL_LIGHT1, GL_SPOT_CUTOFF, 45.0)     # Ângulo
        glLightf(GL_LIGHT1, GL_SPOT_EXPONENT, 10.0)   # Foco

        # Atenuação
        glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION, 0.2)
        glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION, 0.01)
        glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.001)
    else:
        # Desligar luz
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  (0.0, 0.0, 0.0, 1.0))
        glLightfv(GL_LIGHT1, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))


def draw_indicators():
    """Desenha os modelos 3D que representam as fontes de luz."""
    _draw_sun_moon_mesh()
    _draw_garage_lamp_mesh()


# --- MESHES DE REPRESENTAÇÃO ---

def _draw_sun_moon_mesh():
    dx, dy, dz = 0.3, 1.0, 0.4
    dist = 140.0
    px, py, pz = dx*dist, dy*dist, dz*dist

    glPushMatrix()
    glTranslatef(px, py, pz)
    glDisable(GL_LIGHTING)
    
    if sun_enabled:
        glColor3f(1.0, 0.9, 0.2) # Sol Dourado
        glutSolidSphere(8.0, 24, 24)
    else:
        glColor3f(0.8, 0.8, 0.9) # Lua Pálida
        glutSolidSphere(6.0, 24, 24)
        
    glEnable(GL_LIGHTING)
    glPopMatrix()


def _draw_garage_lamp_mesh():
    # Posição da lâmpada física
    x, y, z = 0.0, 12.0, -36.0
    quadric = gluNewQuadric()
    gluQuadricNormals(quadric, GLU_SMOOTH)

    glPushMatrix()
    glTranslatef(x, y, z)

    # 1. Lâmpada (Esfera)
    glPushMatrix()
    glDisable(GL_LIGHTING)
    if garage_light_enabled:
        glColor3f(1.0, 1.0, 0.7) # Aceso
    else:
        glColor3f(0.2, 0.2, 0.2) # Apagado
    glutSolidSphere(0.3, 16, 16)
    glEnable(GL_LIGHTING)
    glPopMatrix()

    # 2. Estrutura (Metal Escuro)
    glColor3f(0.1, 0.1, 0.1) 
    
    # Abajur
    glPushMatrix()
    glRotatef(-90, 1.0, 0.0, 0.0)
    glTranslatef(0.0, 0.0, -0.5)
    gluCylinder(quadric, 1.0, 0.2, 1.2, 24, 1)
    glTranslatef(0.0, 0.0, 1.2)
    gluDisk(quadric, 0.0, 0.2, 24, 1)
    
    # Haste (Invertida para apontar à parede)
    glPushMatrix()
    glRotatef(90, 1.0, 0.0, 0.0)
    glRotatef(180, 0.0, 1.0, 0.0) # Flip
    
    gluCylinder(quadric, 0.1, 0.1, 5.3, 12, 1)
    glTranslatef(0.0, 0.0, 5.3)
    gluDisk(quadric, 0.0, 0.6, 24, 1)
    glPopMatrix() # Fim haste
    glPopMatrix() # Fim abajur

    glPopMatrix()
    gluDeleteQuadric(quadric)