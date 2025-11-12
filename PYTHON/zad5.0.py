#!/usr/bin/env python3
import sys
import math
import random
import numpy as np

from glfw.GLFW import *

from OpenGL.GL import *
from OpenGL.GLU import *

# =================================================================
# ZMIENNE GLOBALNE I USTAWIENIA
# =================================================================
MAP_SIZE = 129
HEIGHTMAP = np.zeros((MAP_SIZE, MAP_SIZE))
TERRAIN_SCALE = 5.0
HEIGHT_SCALE = 30.0

camera_pos = np.array([MAP_SIZE * TERRAIN_SCALE / 2, 50.0, MAP_SIZE * TERRAIN_SCALE / 2])
camera_yaw = 0.0
camera_pitch = 0.0
camera_speed = 5.0

mouse_x_pos_old = 0
mouse_y_pos_old = 0
delta_x = 0
delta_y = 0
pix2angle = 0.1

keys = {}


# =================================================================

# =================================================================
# GENEROWANIE TERENU (FRAKTAL PLAZMOWY)
# =================================================================

def get_height(x, y):
    """ Bezpieczne pobieranie wysokości z mapy (z zawijaniem) """
    return HEIGHTMAP[x % (MAP_SIZE - 1)][y % (MAP_SIZE - 1)]


def set_height(x, y, val):
    """ Bezpieczne ustawianie wysokości z zawijaniem """
    HEIGHTMAP[x % (MAP_SIZE - 1)][y % (MAP_SIZE - 1)] = val


def diamond_square_step(step, roughness):
    """ Wykonuje jeden krok algorytmu Diamond-Square """
    half_step = step // 2
    if half_step < 1:
        return

    # Krok Diamentu
    for x in range(half_step, MAP_SIZE, step):
        for y in range(half_step, MAP_SIZE, step):
            avg = (get_height(x - half_step, y - half_step) +
                   get_height(x + half_step, y - half_step) +
                   get_height(x - half_step, y + half_step) +
                   get_height(x + half_step, y + half_step)) / 4.0
            offset = random.uniform(-roughness, roughness)
            set_height(x, y, avg + offset)

    # Krok Kwadratu
    for x in range(0, MAP_SIZE, half_step):
        for y in range((x + half_step) % step, MAP_SIZE, step):
            avg = (get_height(x - half_step, y) +
                   get_height(x + half_step, y) +
                   get_height(x, y - half_step) +
                   get_height(x, y + half_step)) / 4.0
            offset = random.uniform(-roughness, roughness)
            set_height(x, y, avg + offset)

    diamond_square_step(half_step, roughness / 2.0)


def generate_terrain():
    global HEIGHTMAP
    set_height(0, 0, random.random())
    set_height(0, MAP_SIZE - 1, random.random())
    set_height(MAP_SIZE - 1, 0, random.random())
    set_height(MAP_SIZE - 1, MAP_SIZE - 1, random.random())
    diamond_square_step(MAP_SIZE - 1, 1.0)  # Start rekursji


# =================================================================

def startup():
    global mouse_x_pos_old, mouse_y_pos_old

    # update_viewport(None, 400, 400) # <-- Usunięto błędne wywołanie
    glClearColor(0.2, 0.4, 0.8, 1.0)
    glEnable(GL_DEPTH_TEST)

    glfwSetInputMode(glfwGetCurrentContext(), GLFW_CURSOR, GLFW_CURSOR_DISABLED)
    mouse_x_pos_old, mouse_y_pos_old = glfwGetCursorPos(glfwGetCurrentContext())

    print("Generowanie terenu fraktalnego...")
    generate_terrain()
    print("Gotowe. Sterowanie: W, A, S, D, Spacja (góra), Ctrl (dół)")


def shutdown():
    pass


def axes():
    pass


# =================================================================
# POPRAWIONA FUNKCJA DRAW_TERRAIN
# =================================================================
def draw_terrain():
    """ Rysuje teren na podstawie HEIGHTMAP """

    # Znajdź min i max wysokości, aby poprawnie znormalizować kolory
    min_h = np.min(HEIGHTMAP)
    max_h = np.max(HEIGHTMAP)
    h_range = max_h - min_h
    if h_range == 0:
        h_range = 1.0

    for i in range(MAP_SIZE - 1):
        glBegin(GL_TRIANGLE_STRIP)
        for j in range(MAP_SIZE):
            # Wierzchołek 1 (i, j)
            y1_raw = get_height(i, j)
            x1 = i * TERRAIN_SCALE
            y1 = y1_raw * HEIGHT_SCALE
            z1 = j * TERRAIN_SCALE

            # POPRAWKA KOLORU: Normalizuj wysokość do [0, 1]
            color_val = (y1_raw - min_h) / h_range
            glColor3f(0.1, 0.2 + color_val * 0.8, 0.1)  # Od ciemnej do jasnej zieleni
            glVertex3f(x1, y1, z1)

            # Wierzchołek 2 (i+1, j)
            y2_raw = get_height(i + 1, j)
            x2 = (i + 1) * TERRAIN_SCALE
            y2 = y2_raw * HEIGHT_SCALE
            z2 = j * TERRAIN_SCALE

            # POPRAWKA KOLORU: Normalizuj wysokość do [0, 1]
            color_val_2 = (y2_raw - min_h) / h_range
            glColor3f(0.1, 0.2 + color_val_2 * 0.8, 0.1)
            glVertex3f(x2, y2, z2)
        glEnd()


# =================================================================
# MODYFIKACJA FUNKCJI RENDER (KAMERA FPP)
# =================================================================
def render(time):
    global camera_pos, camera_yaw, camera_pitch
    global delta_x, delta_y  # Potrzebne do resetowania

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # --- Aktualizacja kątów kamery na podstawie myszy ---
    camera_yaw += delta_x * pix2angle
    camera_pitch -= delta_y * pix2angle

    if camera_pitch > 89.0: camera_pitch = 89.0
    if camera_pitch < -89.0: camera_pitch = -89.0

    # --- Obliczanie wektorów kierunkowych kamery ---
    yaw_rad = math.radians(camera_yaw)
    pitch_rad = math.radians(camera_pitch)

    forward = np.array([
        math.cos(yaw_rad) * math.cos(pitch_rad),
        math.sin(pitch_rad),
        math.sin(yaw_rad) * math.cos(pitch_rad)
    ])
    forward = forward / np.linalg.norm(forward)

    right = np.cross(forward, np.array([0.0, 1.0, 0.0]))
    right = right / np.linalg.norm(right)

    # --- Aktualizacja pozycji kamery (sterowanie klawiszami) ---
    if keys.get(GLFW_KEY_W):
        camera_pos += forward * camera_speed
    if keys.get(GLFW_KEY_S):
        camera_pos -= forward * camera_speed
    if keys.get(GLFW_KEY_A):
        camera_pos -= right * camera_speed
    if keys.get(GLFW_KEY_D):
        camera_pos += right * camera_speed
    if keys.get(GLFW_KEY_SPACE):
        camera_pos[1] += camera_speed
    if keys.get(GLFW_KEY_LEFT_CONTROL):
        camera_pos[1] -= camera_speed

    # --- Implementacja "nieskończonego" terenu (zawijanie) ---
    camera_pos[0] = camera_pos[0] % ((MAP_SIZE - 1) * TERRAIN_SCALE)
    camera_pos[2] = camera_pos[2] % ((MAP_SIZE - 1) * TERRAIN_SCALE)

    look_at = camera_pos + forward

    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
              look_at[0], look_at[1], look_at[2],
              0.0, 1.0, 0.0)

    axes()
    draw_terrain()

    glFlush()

    # Reset delty myszy po klatce
    delta_x = 0
    delta_y = 0


# =================================================================


def update_viewport(window, width, height):
    global pix2angle

    # --- ZABEZPIECZENIE ---
    if height == 0:
        height = 1
    if width == 0:
        width = 1
    # ----------------------

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    gluPerspective(70, width / height, 0.1, (MAP_SIZE * TERRAIN_SCALE) * 2)

    glViewport(0, 0, width, height)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def keyboard_key_callback(window, key, scancode, action, mods):
    global keys
    if action == GLFW_PRESS:
        keys[key] = True
        if key == GLFW_KEY_ESCAPE:
            glfwSetWindowShouldClose(window, GLFW_TRUE)
    if action == GLFW_RELEASE:
        keys[key] = False


def mouse_motion_callback(window, x_pos, y_pos):
    global delta_x, mouse_x_pos_old
    global delta_y, mouse_y_pos_old

    delta_x = x_pos - mouse_x_pos_old
    mouse_x_pos_old = x_pos

    delta_y = y_pos - mouse_y_pos_old
    mouse_y_pos_old = y_pos


def mouse_button_callback(window, button, action, mods):
    pass


# =================================================================
# POPRAWIONA FUNKCJA MAIN
# =================================================================
def main():
    if not glfwInit():
        sys.exit(-1)

    window = glfwCreateWindow(800, 600, "Lab 4 (Ocena 5.0) - Lot nad terenem", None, None)
    if not window:
        glfwTerminate()
        sys.exit(-1)

    glfwMakeContextCurrent(window)
    glfwSetFramebufferSizeCallback(window, update_viewport)
    glfwSetKeyCallback(window, keyboard_key_callback)
    glfwSetCursorPosCallback(window, mouse_motion_callback)
    glfwSetMouseButtonCallback(window, mouse_button_callback)
    glfwSwapInterval(1)

    # --- POPRAWKA INICJALIZACJI VIEWPORTU ---
    width, height = glfwGetFramebufferSize(window)
    update_viewport(window, width, height)

    startup()
    while not glfwWindowShouldClose(window):
        render(glfwGetTime())
        glfwSwapBuffers(window)
        glfwPollEvents()
    shutdown()

    glfwTerminate()


if __name__ == '__main__':
    main()