from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time
import random


# ============================================================================
# === ZONE 0: GLOBAL VARIABLES ==============================================
# ============================================================================
# Shared state used across all zones. Each member may add their own globals
# here, clearly labeled with their member number.
# ============================================================================

# --- Window / Display ---
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800

# --- Camera (Member 1) ---
camera_pos = (0, 500, 500)
fovY = 120              # Field of view (Member 1 will make this dynamic for Warp Speed)
GRID_LENGTH = 600        # Length of grid lines

# --- Game State ---
game_speed = 1.0         # Global game speed multiplier (increases over time)
time_survived = 0.0      # Elapsed survival time in seconds (used for day/night cycle)
game_over = False        # True when player collides with an obstacle
game_paused = False      # True when game is paused
score = 0                # Player's score

# --- Timing ---
last_frame_time = 0      # Timestamp of the last frame (for delta-time calculation)

# --- Member 1 Globals (World & Camera) ---
# (Member 1: add your tunnel/pillar/scroll variables here)

# --- Member 2 Globals (Player) ---
# (Member 2: add your player position, lane, jump, gravity variables here)

# --- Member 3 Globals (Obstacles & Items) ---
# (Member 3: add your obstacle lists, powerup lists, spawn timers here)


# ============================================================================
# === ZONE 1: MEMBER 1 — WORLD & CAMERA =====================================
# ============================================================================
# Member 1 is responsible for:
#   1. 3D Scrolling Arcade Tunnel (floor grid + side pillars, Z-axis scroll)
#   2. Day/Night Cycle (color interpolation based on time_survived)
#   3. Warp Speed Camera (dynamic fovY in setupCamera)
# ============================================================================

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """Draws HUD text at a fixed screen position using orthographic overlay."""
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)  # left, right, bottom, top

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def setupCamera():
    """
    Configures the camera's projection and view settings.
    Uses a perspective projection and positions the camera to look at the target.
    Member 1 TODO: Make fovY dynamic for Warp Speed effect.
    """
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    # Aspect ratio = WINDOW_WIDTH / WINDOW_HEIGHT = 1000/800 = 1.25
    gluPerspective(fovY, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    x, y, z = camera_pos
    gluLookAt(x, y, z,   # Camera position
              0, 0, 0,   # Look-at target
              0, 0, 1)   # Up vector (z-axis)


# Member 1 TODO: Add these functions in this zone:
#   - draw_tunnel()        → Floor grid + side pillars with Z-scroll & wraparound
#   - update_tunnel()      → Move tunnel pieces each frame, snap back when past camera
#   - get_day_night_color() → Interpolate RGB based on time_survived
#   - update_warp_fov()    → Adjust fovY based on game_speed


# ============================================================================
# === ZONE 2: MEMBER 2 — PLAYER CONTROLLER ==================================
# ============================================================================
# Member 2 is responsible for:
#   1. Hierarchical Animated Avatar (body + limbs with glPushMatrix/glPopMatrix)
#   2. Running Animation (sin() wave on limb rotation)
#   3. Smooth Lane-Switching & Jumping Kinematics (interpolation + parabolic jump)
#   4. Gravity Inversion (flip player to ceiling, invert jump math)
# ============================================================================

# Member 2 TODO: Add these functions in this zone:
#   - draw_player()         → Hierarchical robot avatar with animated limbs
#   - update_player()       → Handle lane interpolation, jump physics, gravity state
#   - player_jump()         → Initiate a jump (set velocity, mark airborne)
#   - toggle_gravity()      → Flip gravity_inverted boolean, adjust base Y


# ============================================================================
# === ZONE 3: MEMBER 3 — OBSTACLES & COLLISIONS =============================
# ============================================================================
# Member 3 is responsible for:
#   1. Object Manager (lists of dicts for obstacles & powerups)
#   2. Pattern-Based Spawning (formations at far Z, move toward camera)
#   3. Dynamic 3D AABB Collision (player vs obstacles/powerups)
#   4. Morphing/Pulsing Logic (scale/shape-swap when close to camera)
# ============================================================================

# Member 3 TODO: Add these functions in this zone:
#   - spawn_pattern()       → Select a formation and add obstacles/powerups to lists
#   - update_obstacles()    → Move all obstacles along Z, despawn when past camera
#   - draw_obstacles()      → Render each obstacle (with morphing if close)
#   - check_collisions()    → AABB collision between player and all active objects


# ============================================================================
# === ZONE 4: MAIN GAME LOOP ================================================
# ============================================================================
# Contains input handlers, the display callback, idle function, and main().
# All members may need to ADD CALLS here (e.g., calling draw_player() in
# showScreen), but coordinate with the team before editing this zone.
# ============================================================================

def keyboardListener(key, x, y):
    """
    Handles keyboard inputs for player movement, game controls, and toggles.
    """
    global game_paused, game_over

    # --- Game Controls ---
    # Pause/unpause (P key)
    # if key == b'p':
    #     game_paused = not game_paused

    # Reset the game (R key)
    # if key == b'r':
    #     pass  # TODO: call a reset function

    # --- Player Movement (Member 2 will implement these) ---
    # Move left lane (A key)
    # if key == b'a':
    #     pass

    # Move right lane (D key)
    # if key == b'd':
    #     pass

    # Jump (W key or Space)
    # if key == b'w' or key == b' ':
    #     pass

    # Duck (S key)
    # if key == b's':
    #     pass

    # Toggle gravity inversion (G key)
    # if key == b'g':
    #     pass

    glutPostRedisplay()


def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for adjusting the camera.
    """
    global camera_pos
    x, y, z = camera_pos

    # Move camera up (UP arrow key)
    if key == GLUT_KEY_UP:
        y += 5

    # Move camera down (DOWN arrow key)
    if key == GLUT_KEY_DOWN:
        y -= 5

    # Move camera left (LEFT arrow key)
    if key == GLUT_KEY_LEFT:
        x -= 5

    # Move camera right (RIGHT arrow key)
    if key == GLUT_KEY_RIGHT:
        x += 5

    camera_pos = (x, y, z)


def mouseListener(button, state, x, y):
    """
    Handles mouse inputs.
    """
    # Left click — currently unused
    # if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
    #     pass

    # Right click — currently unused
    # if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
    #     pass
    pass


def idle():
    """
    Idle function — runs continuously for real-time game updates.
    Each member's update function should be called here.
    """
    global last_frame_time, time_survived, game_speed

    # --- Delta time calculation ---
    current_time = time.time()
    if last_frame_time == 0:
        last_frame_time = current_time
    dt = current_time - last_frame_time
    last_frame_time = current_time

    if not game_paused and not game_over:
        time_survived += dt

        # --- Member 1: Update world ---
        # update_tunnel(dt)
        # update_warp_fov()

        # --- Member 2: Update player ---
        # update_player(dt)

        # --- Member 3: Update obstacles & check collisions ---
        # update_obstacles(dt)
        # check_collisions()

    glutPostRedisplay()


def showScreen():
    """
    Display callback — renders the entire game scene each frame.
    """
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

    setupCamera()

    # --- Draw the grid (temporary placeholder — Member 1 will replace with tunnel) ---
    glBegin(GL_QUADS)

    glColor3f(1, 1, 1)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(0, GRID_LENGTH, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(-GRID_LENGTH, 0, 0)

    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(0, -GRID_LENGTH, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(GRID_LENGTH, 0, 0)

    glColor3f(0.7, 0.5, 0.95)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, -GRID_LENGTH, 0)

    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, 0, 0)
    glVertex3f(0, 0, 0)
    glVertex3f(0, GRID_LENGTH, 0)
    glEnd()

    # --- Member 1: Draw tunnel ---
    # draw_tunnel()

    # --- Member 2: Draw player ---
    # draw_player()

    # --- Member 3: Draw obstacles & items ---
    # draw_obstacles()

    # --- HUD ---
    draw_text(10, 770, f"Score: {score}")
    draw_text(10, 740, f"Time: {time_survived:.1f}s | Speed: {game_speed:.1f}x")

    if game_over:
        draw_text(400, 400, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(380, 360, "Press R to restart")

    if game_paused:
        draw_text(420, 400, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)

    glutSwapBuffers()


# --- Entry Point ---
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"Obstacle Runner 423")

    glEnable(GL_DEPTH_TEST)  # Required by project spec

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()


if __name__ == "__main__":
    main()
