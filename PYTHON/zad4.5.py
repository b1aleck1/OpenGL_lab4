#!/usr/bin/env python3
import sys
import math

from glfw.GLFW import *

from OpenGL.GL import *
from OpenGL.GLU import *


R = 10.0
theta = 0.0
phi = 0.0
pix2angle = 1.0

left_mouse_button_pressed = 0
right_mouse_button_pressed = 0
mouse_x_pos_old = 0
mouse_y_pos_old = 0
delta_x = 0
delta_y = 0

scale = 1.0  # Przywrócone dla trybu 3.5
camera_mode = True  # True = Tryb Kamery (4.0), False = Tryb Obiektu (3.5)


def startup():
    update_viewport(None, 400, 400)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)


def shutdown():
    pass


def axes():
    # ... (bez zmian)
    glBegin(GL_LINES)
    glColor3f(1.0, 0.0, 0.0);
    glVertex3f(-5.0, 0.0, 0.0);
    glVertex3f(5.0, 0.0, 0.0)
    glColor3f(0.0, 1.0, 0.0);
    glVertex3f(0.0, -5.0, 0.0);
    glVertex3f(0.0, 5.0, 0.0)
    glColor3f(0.0, 0.0, 1.0);
    glVertex3f(0.0, 0.0, -5.0);
    glVertex3f(0.0, 0.0, 5.0)
    glEnd()


def example_object():
    glColor3f(1.0, 1.0, 1.0)
    quadric = gluNewQuadric()
    gluQuadricDrawStyle(quadric, GLU_LINE)
    glRotatef(90, 1.0, 0.0, 0.0);
    glRotatef(-90, 0.0, 1.0, 0.0)
    gluSphere(quadric, 1.5, 10, 10)
    glTranslatef(0.0, 0.0, 1.1);
    gluCylinder(quadric, 1.0, 1.5, 1.5, 10, 5);
    glTranslatef(0.0, 0.0, -1.1)
    glTranslatef(0.0, 0.0, -2.6);
    gluCylinder(quadric, 0.0, 1.0, 1.5, 10, 5);
    glTranslatef(0.0, 0.0, 2.6)
    glRotatef(90, 1.0, 0.0, 1.0);
    glTranslatef(0.0, 0.0, 1.5);
    gluCylinder(quadric, 0.1, 0.0, 1.0, 5, 5);
    glTranslatef(0.0, 0.0, -1.5);
    glRotatef(-90, 1.0, 0.0, 1.0)
    glRotatef(-90, 1.0, 0.0, 1.0);
    glTranslatef(0.0, 0.0, 1.5);
    gluCylinder(quadric, 0.1, 0.0, 1.0, 5, 5);
    glTranslatef(0.0, 0.0, -1.5);
    glRotatef(90, 1.0, 0.0, 1.0)
    glRotatef(90, 0.0, 1.0, 0.0);
    glRotatef(-90, 1.0, 0.0, 0.0)
    gluDeleteQuadric(quadric)


def render(time):
    global theta, phi, R, scale

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # rzełączanie trybów
    if camera_mode:
        # Aktualizacja kątów i promienia na podstawie myszy
        if left_mouse_button_pressed:
            theta += delta_x * pix2angle
            phi += delta_y * pix2angle

            # Ograniczenie kątów
            theta = theta % 360  # Ograniczenie theta do [0, 360]
            if phi > 90.0:
                phi = 90.0
            elif phi < -90.0:
                phi = -90.0

        if right_mouse_button_pressed:
            R += delta_y * 0.1
            # Ograniczenie zoomu
            if R < 3.0: R = 3.0
            if R > 20.0: R = 20.0

        theta_rad = theta * math.pi / 180.0
        phi_rad = phi * math.pi / 180.0

        x_eye = R * math.cos(theta_rad) * math.cos(phi_rad)
        y_eye = R * math.sin(phi_rad)
        z_eye = R * math.sin(theta_rad) * math.cos(phi_rad)

        # Ustawienie wektora "up"
        # Jeśli patrzymy prosto z góry lub z dołu, 'up' musi być (0,0,-1) lub (0,0,1)
        # Ale dzięki ograniczeniu phi do [-89, 89], (0,1,0) jest zawsze bezpieczne.
        up_vector = [0.0, 1.0, 0.0]

        gluLookAt(x_eye, y_eye, z_eye,
                  0.0, 0.0, 0.0, up_vector[0], up_vector[1], up_vector[2])

    else:
        # TRYB OBIEKTU (ZADANIE 3.5)
        gluLookAt(0.0, 0.0, 10.0,  # Kamera jest nieruchoma
                  0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

        if left_mouse_button_pressed:
            theta += delta_x * pix2angle
            phi += delta_y * pix2angle

        if right_mouse_button_pressed:
            scale += delta_y * 0.01
            if scale < 0.1: scale = 0.1

        glRotatef(theta, 0.0, 1.0, 0.0)
        glRotatef(phi, 1.0, 0.0, 0.0)
        glScalef(scale, scale, scale)

    axes()
    example_object()

    glFlush()


def update_viewport(window, width, height):
    global pix2angle
    pix2angle = 360.0 / width
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(70, 1.0, 0.1, 300.0)
    if width <= height:
        glViewport(0, int((height - width) / 2), width, width)
    else:
        glViewport(int((width - height) / 2), 0, height, height)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def keyboard_key_callback(window, key, scancode, action, mods):
    global camera_mode

    if action == GLFW_PRESS:
        if key == GLFW_KEY_ESCAPE:
            glfwSetWindowShouldClose(window, GLFW_TRUE)

        # Przełącznik trybu
        if key == GLFW_KEY_M:
            camera_mode = not camera_mode
            if camera_mode:
                print("Tryb Kamery (4.0/4.5)")
            else:
                print("Tryb Obiektu (3.5)")


def mouse_motion_callback(window, x_pos, y_pos):
    global delta_x, mouse_x_pos_old, delta_y, mouse_y_pos_old
    delta_x = x_pos - mouse_x_pos_old
    mouse_x_pos_old = x_pos
    delta_y = y_pos - mouse_y_pos_old
    mouse_y_pos_old = y_pos


def mouse_button_callback(window, button, action, mods):
    global left_mouse_button_pressed, right_mouse_button_pressed
    if button == GLFW_MOUSE_BUTTON_LEFT and action == GLFW_PRESS:
        left_mouse_button_pressed = 1
    else:
        left_mouse_button_pressed = 0
    if button == GLFW_MOUSE_BUTTON_RIGHT and action == GLFW_PRESS:
        right_mouse_button_pressed = 1
    else:
        right_mouse_button_pressed = 0


def main():
    if not glfwInit():
        sys.exit(-1)
    window = glfwCreateWindow(400, 400, "Lab 4 (Ocena 4.5)", None, None)
    if not window:
        glfwTerminate()
        sys.exit(-1)
    glfwMakeContextCurrent(window)
    glfwSetFramebufferSizeCallback(window, update_viewport)
    glfwSetKeyCallback(window, keyboard_key_callback)
    glfwSetCursorPosCallback(window, mouse_motion_callback)
    glfwSetMouseButtonCallback(window, mouse_button_callback)
    glfwSwapInterval(1)
    startup()
    while not glfwWindowShouldClose(window):
        render(glfwGetTime())
        glfwSwapBuffers(window)
        glfwPollEvents()
    shutdown()
    glfwTerminate()


if __name__ == '__main__':
    main()