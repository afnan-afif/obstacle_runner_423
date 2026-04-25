from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import time


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                            ║
# ║                    3D OBSTACLE RUNNER — CSE 423 PROJECT                    ║
# ║                      (Subway Surfers Style Clone)                          ║
# ║                                                                            ║
# ║   RULES:                                                                   ║
# ║   - NO Shaders, NO Textures                                               ║
# ║   - Only glutSolidCube, gluCylinder, gluSphere + basic transforms         ║
# ║   - All code in this single file                                           ║
# ║   - Each member writes ONLY inside their designated zone                   ║
# ║                                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                            ║
# ║                  ZONE 0: GLOBAL VARIABLES & SHARED UTILS                   ║
# ║                                                                            ║
# ║   Shared game state used by ALL members.                                   ║
# ║   Any member may ADD variables here, but NEVER modify another member's     ║
# ║   existing variables without team agreement.                               ║
# ║                                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# --- Window dimensions ---
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800

# --- Game state ---
game_speed = 1.0        # Global speed multiplier (increases over time)
score = 0               # Player's current score
lives = 3               # Player's remaining lives
game_over = False        # Flag: is the game over?

# --- Lane configuration ---
LANE_LEFT = -100
LANE_CENTER = 0
LANE_RIGHT = 100

# --- Camera ---
camera_pos = [0, 200, 400]   # Camera position [x, y, z]
fovY = 60                    # Field of view (degrees)

# --- Grid / Floor ---
GRID_LENGTH = 600       # Half-length of the floor grid

# --- Timing ---
last_time = 0           # For delta-time calculations


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """
    Draws 2D overlay text on screen at pixel coordinates (x, y).
    Shared utility — any member can call this.
    """
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


# ════════════════════════════════════════════════════════════════════════════════
#                        END OF ZONE 0
# ════════════════════════════════════════════════════════════════════════════════


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                            ║
# ║              ZONE 1: MEMBER 1 — WORLD & CAMERA ARCHITECT                  ║
# ║                                                                            ║
# ║   RESPONSIBILITIES:                                                        ║
# ║   ✦ Setup GL_DEPTH_TEST                                                    ║
# ║   ✦ Draw and animate the infinite scrolling floor grid                     ║
# ║   ✦ Build the HUD logic (score, lives display)                             ║
# ║   ✦ Camera setup (setupCamera)                                             ║
# ║   ✦ NOVELTY: Dynamic Warp Speed (fovY widens with score)                  ║
# ║                                                                            ║
# ║   >>> MEMBER 1: WRITE ALL YOUR FUNCTIONS BELOW THIS LINE <<<              ║
# ║                                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


def setupCamera():
    """
    [MEMBER 1] Configures the camera's projection and view settings.
    Uses a perspective projection and positions the camera to look at the origin.
    """
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    x, y, z = camera_pos
    gluLookAt(x, y, z,    # Camera position
              0, 0, 0,    # Look-at target (origin)
              0, 1, 0)    # Up vector (Y-axis is up)


def draw_floor():
    """
    [MEMBER 1] Draws the scrolling floor grid.
    TODO: Implement infinite scrolling illusion along Z-axis.
    """
    # Placeholder floor — replace with scrolling grid
    glBegin(GL_QUADS)

    glColor3f(0.15, 0.15, 0.2)
    glVertex3f(-GRID_LENGTH,  0, -GRID_LENGTH)
    glVertex3f( GRID_LENGTH,  0, -GRID_LENGTH)
    glVertex3f( GRID_LENGTH,  0,  GRID_LENGTH)
    glVertex3f(-GRID_LENGTH,  0,  GRID_LENGTH)

    glEnd()


def draw_hud():
    """
    [MEMBER 1] Draws the heads-up display: score, lives, speed.
    """
    draw_text(10, WINDOW_HEIGHT - 30, f"Score: {score}")
    draw_text(10, WINDOW_HEIGHT - 60, f"Lives: {lives}")
    draw_text(10, WINDOW_HEIGHT - 90, f"Speed: {game_speed:.1f}x")


def update_warp_speed():
    """
    [MEMBER 1] NOVELTY FEATURE: Dynamic Warp Speed.
    TODO: Increase game_speed and widen fovY based on score.
    """
    pass


# ════════════════════════════════════════════════════════════════════════════════
#                        END OF ZONE 1 (MEMBER 1)
# ════════════════════════════════════════════════════════════════════════════════


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                            ║
# ║            ZONE 2: MEMBER 2 — PLAYER CONTROLLER & PHYSICS                 ║
# ║                                                                            ║
# ║   RESPONSIBILITIES:                                                        ║
# ║   ✦ Render the player cube                                                ║
# ║   ✦ Smooth lane switching (Left / Center / Right)                          ║
# ║   ✦ Jumping (parabolic Y-axis movement)                                   ║
# ║   ✦ Rolling / Ducking (Y-axis scale squash)                               ║
# ║   ✦ NOVELTY: Gravity Inversion (upside-down running)                      ║
# ║                                                                            ║
# ║   >>> MEMBER 2: WRITE ALL YOUR FUNCTIONS BELOW THIS LINE <<<              ║
# ║                                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


def draw_player():
    """
    [MEMBER 2] Renders the player cube at the current lane position.
    TODO: Implement player rendering with lane position, jump height, and duck scale.
    """
    pass


def update_player():
    """
    [MEMBER 2] Updates player state each frame: lane interpolation, jump arc, duck timer.
    TODO: Implement smooth lane switching, jump parabola, and roll/duck logic.
    """
    pass


def handle_player_input(key):
    """
    [MEMBER 2] Processes player-specific keyboard input (A/D for lanes, W for jump, S for duck).
    TODO: Implement lane switching, jump trigger, and duck trigger.
    """
    pass


def update_gravity_inversion():
    """
    [MEMBER 2] NOVELTY FEATURE: Gravity Inversion.
    TODO: Flip the player's gravity so they run on the ceiling.
    """
    pass


# ════════════════════════════════════════════════════════════════════════════════
#                        END OF ZONE 2 (MEMBER 2)
# ════════════════════════════════════════════════════════════════════════════════


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                            ║
# ║            ZONE 3: MEMBER 3 — OBSTACLE ENGINE & COLLISIONS                ║
# ║                                                                            ║
# ║   RESPONSIBILITIES:                                                        ║
# ║   ✦ Obstacle data manager (spawn, translate toward player, delete)         ║
# ║   ✦ Draw obstacles (cubes, cylinders, spheres)                             ║
# ║   ✦ AABB collision detection against the player                            ║
# ║   ✦ NOVELTY: Morphing Obstacles (shape transitions near camera)            ║
# ║                                                                            ║
# ║   >>> MEMBER 3: WRITE ALL YOUR FUNCTIONS BELOW THIS LINE <<<              ║
# ║                                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


def spawn_obstacle():
    """
    [MEMBER 3] Spawns a new obstacle at a random lane far down the Z-axis.
    TODO: Implement procedural obstacle generation with random shapes and lanes.
    """
    pass


def update_obstacles():
    """
    [MEMBER 3] Moves all obstacles toward the player along Z-axis. Removes off-screen ones.
    TODO: Implement obstacle translation and cleanup.
    """
    pass


def draw_obstacles():
    """
    [MEMBER 3] Renders all active obstacles.
    TODO: Draw each obstacle using glutSolidCube / gluCylinder / gluSphere.
    """
    pass


def check_collisions():
    """
    [MEMBER 3] Checks AABB collisions between the player and all obstacles.
    TODO: Implement 3D bounding box overlap detection.
    Returns True if a collision is detected, False otherwise.
    """
    return False


def update_morphing_obstacles():
    """
    [MEMBER 3] NOVELTY FEATURE: Morphing Obstacles.
    TODO: Smoothly transition obstacle shapes as they cross a Z-axis threshold.
    """
    pass


# ════════════════════════════════════════════════════════════════════════════════
#                        END OF ZONE 3 (MEMBER 3)
# ════════════════════════════════════════════════════════════════════════════════


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                            ║
# ║                     ZONE 4: MAIN GAME LOOP & GLUT SETUP                   ║
# ║                                                                            ║
# ║   This zone wires everything together. All members' draw/update            ║
# ║   functions are called from here. Modify WITH CAUTION — coordinate         ║
# ║   with the team before changing call order.                                ║
# ║                                                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝


def keyboardListener(key, x, y):
    """
    Routes keyboard input to the appropriate member's handler.
    """
    global game_over, score, lives, game_speed

    # --- Shared controls ---
    # Reset the game (R key)
    if key == b'r':
        score = 0
        lives = 3
        game_speed = 1.0
        game_over = False

    # --- Member 2 handles player movement keys ---
    handle_player_input(key)


def specialKeyListener(key, x, y):
    """
    Handles special key inputs (arrow keys) for camera adjustment.
    """
    global camera_pos
    x_cam, y_cam, z_cam = camera_pos

    if key == GLUT_KEY_UP:
        y_cam += 5
    if key == GLUT_KEY_DOWN:
        y_cam -= 5
    if key == GLUT_KEY_LEFT:
        x_cam -= 5
    if key == GLUT_KEY_RIGHT:
        x_cam += 5

    camera_pos = [x_cam, y_cam, z_cam]


def mouseListener(button, state, x, y):
    """
    Handles mouse inputs.
    """
    pass


def idle():
    """
    Idle function — runs every frame.
    Calls all member update functions, then triggers a redraw.
    """
    global last_time

    # --- Member 1: World updates ---
    update_warp_speed()

    # --- Member 2: Player updates ---
    update_player()
    update_gravity_inversion()

    # --- Member 3: Obstacle updates ---
    update_obstacles()
    update_morphing_obstacles()

    # --- Member 3: Collision check ---
    if check_collisions():
        pass  # TODO: Decrement lives, trigger hit effect, etc.

    glutPostRedisplay()


def showScreen():
    """
    Display callback — renders the entire game scene each frame.
    """
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

    setupCamera()

    # --- Member 1: Draw the world ---
    draw_floor()

    # --- Member 2: Draw the player ---
    draw_player()

    # --- Member 3: Draw the obstacles ---
    draw_obstacles()

    # --- Member 1: Draw the HUD (always last, overlays everything) ---
    draw_hud()

    glutSwapBuffers()


def main():
    """
    Entry point: initializes GLUT, creates the window, registers callbacks,
    and starts the main loop.
    """
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D Obstacle Runner - CSE 423")

    # Enable depth testing for proper 3D rendering
    glEnable(GL_DEPTH_TEST)

    # Set dark background
    glClearColor(0.05, 0.05, 0.1, 1.0)

    # Register callbacks
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()


# ════════════════════════════════════════════════════════════════════════════════
#                        END OF ZONE 4 (MAIN GAME LOOP)
# ════════════════════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    main()
