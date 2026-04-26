from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time
import random

# ============================================================================
# === ZONE 0: GLOBAL VARIABLES ==============================================
# ============================================================================
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800

camera_pos = (0, 75, 200)
look_at = (0, 50, -500)
fovY = 120

game_speed = 1.0
time_survived = 0.0
game_over = False
game_paused = False
score = 0
last_frame_time = 0

# --- Member 1 Globals (World) ---
TUNNEL_WIDTH = 200
TUNNEL_LENGTH = 1500
PILLAR_COUNT = 10
PILLAR_SPACING = 150
SCROLL_SPEED = 300
pillar_z_offsets = []
DAY_NIGHT_CYCLE = 30.0

# --- Member 2 Globals (Player) ---
PLAYER_LANE_SPACING = 100
target_lane = 0
player_x = 0.0
player_y = 0.0
player_z = 0.0

player_y_vel = 0.0
is_jumping = False
is_ducking = False
gravity_inverted = False

GRAVITY = 2000.0
JUMP_VELOCITY = 700.0
CEILING_HEIGHT = 150.0
player_anim_time = 0.0

# --- Member 3 Globals (Obstacles) ---
obstacles = []
spawn_timer = 0.0
SPAWN_INTERVAL = 1.2


# ============================================================================
# === ZONE 1: MEMBER 1 — WORLD & CAMERA =====================================
# ============================================================================
def init_tunnel():
    global pillar_z_offsets
    pillar_z_offsets = [-i * PILLAR_SPACING for i in range(PILLAR_COUNT)]

def get_day_night_color(day_color, night_color):
    t = (time_survived % DAY_NIGHT_CYCLE) / DAY_NIGHT_CYCLE
    factor = (math.sin(t * 2 * math.pi - math.pi/2) + 1) / 2
    return (
        day_color[0] * factor + night_color[0] * (1 - factor),
        day_color[1] * factor + night_color[1] * (1 - factor),
        day_color[2] * factor + night_color[2] * (1 - factor)
    )

def draw_tunnel():
    floor_color = get_day_night_color((0.8, 0.8, 0.85), (0.05, 0.02, 0.15))
    ceiling_color = get_day_night_color((0.7, 0.7, 0.75), (0.02, 0.01, 0.1))
    
    # Floor
    glColor3f(*floor_color)
    glBegin(GL_QUADS)
    glVertex3f(-TUNNEL_WIDTH, 0, 500)
    glVertex3f(TUNNEL_WIDTH, 0, 500)
    glVertex3f(TUNNEL_WIDTH, 0, -TUNNEL_LENGTH)
    glVertex3f(-TUNNEL_WIDTH, 0, -TUNNEL_LENGTH)
    glEnd()

    # Ceiling
    glColor3f(*ceiling_color)
    glBegin(GL_QUADS)
    glVertex3f(-TUNNEL_WIDTH, CEILING_HEIGHT + 50, 500)
    glVertex3f(TUNNEL_WIDTH, CEILING_HEIGHT + 50, 500)
    glVertex3f(TUNNEL_WIDTH, CEILING_HEIGHT + 50, -TUNNEL_LENGTH)
    glVertex3f(-TUNNEL_WIDTH, CEILING_HEIGHT + 50, -TUNNEL_LENGTH)
    glEnd()

    # Pillars
    base_col = get_day_night_color((0.9, 0.9, 0.9), (0.0, 0.8, 1.0))
    col_col = get_day_night_color((0.7, 0.7, 0.75), (1.0, 0.0, 0.6))
    
    for z in pillar_z_offsets:
        for x in [-TUNNEL_WIDTH, TUNNEL_WIDTH]:
            glPushMatrix()
            glTranslatef(x, 0, z)
            
            # Base
            glColor3f(*base_col)
            glTranslatef(0, 15, 0)
            glutSolidCube(30)
            
            # Column
            glColor3f(*col_col)
            glTranslatef(0, 15, 0)
            glRotatef(-90, 1, 0, 0) # point up +Y
            q = gluNewQuadric()
            gluCylinder(q, 10, 10, CEILING_HEIGHT + 20, 8, 1)
            
            glPopMatrix()

def update_tunnel(dt):
    global pillar_z_offsets
    scroll = SCROLL_SPEED * game_speed * dt
    for i in range(len(pillar_z_offsets)):
        pillar_z_offsets[i] += scroll
        if pillar_z_offsets[i] > 200:
            pillar_z_offsets[i] = min(pillar_z_offsets) - PILLAR_SPACING

def update_warp_fov():
    global fovY
    target_fov = 120 + (game_speed - 1.0) * 10.0
    target_fov = max(120, min(target_fov, 160))
    fovY += (target_fov - fovY) * 0.05

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Note: Using standard Y-up coordinate system to properly support gravity logic
    cx, cy, cz = camera_pos
    lx, ly, lz = look_at
    gluLookAt(cx, cy, cz, lx, ly, lz, 0, 1, 0)


# ============================================================================
# === ZONE 2: MEMBER 2 — PLAYER CONTROLLER ==================================
# ============================================================================
def draw_player():
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z)
    
    if gravity_inverted:
        glTranslatef(0, 30, 0)
        glRotatef(180, 0, 0, 1) # Rotate around Z to flip upside down
        glTranslatef(0, -30, 0)
        
    if is_ducking:
        glTranslatef(0, 15, 0)
        glScalef(1.0, 0.5, 1.0)
        glTranslatef(0, -15, 0)
        
    # Body
    glColor3f(0.2, 0.5, 0.8)
    glPushMatrix()
    glTranslatef(0, 30, 0)
    glScalef(1.5, 1.0, 1.0)
    glutSolidCube(20)
    glPopMatrix()
    
    # Head
    glColor3f(0.9, 0.8, 0.7)
    glPushMatrix()
    glTranslatef(0, 50, 0)
    glutSolidCube(12)
    glPopMatrix()
    
    swing = math.sin(player_anim_time * 15 * game_speed) * 45 if not is_jumping else 0
    
    # Left Arm
    glColor3f(0.8, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(-20, 40, 0)
    glRotatef(swing, 1, 0, 0)
    glTranslatef(0, -10, 0)
    glScalef(0.3, 1.0, 0.3)
    glutSolidCube(20)
    glPopMatrix()
    
    # Right Arm
    glPushMatrix()
    glTranslatef(20, 40, 0)
    glRotatef(-swing, 1, 0, 0)
    glTranslatef(0, -10, 0)
    glScalef(0.3, 1.0, 0.3)
    glutSolidCube(20)
    glPopMatrix()
    
    # Left Leg
    glColor3f(0.2, 0.8, 0.2)
    glPushMatrix()
    glTranslatef(-8, 15, 0)
    glRotatef(-swing, 1, 0, 0)
    glTranslatef(0, -10, 0)
    glScalef(0.4, 1.0, 0.4)
    glutSolidCube(20)
    glPopMatrix()
    
    # Right Leg
    glPushMatrix()
    glTranslatef(8, 15, 0)
    glRotatef(swing, 1, 0, 0)
    glTranslatef(0, -10, 0)
    glScalef(0.4, 1.0, 0.4)
    glutSolidCube(20)
    glPopMatrix()
    
    glPopMatrix()

def update_player(dt):
    global player_x, player_y, player_y_vel, is_jumping, player_anim_time
    player_anim_time += dt
    
    target_x = target_lane * PLAYER_LANE_SPACING
    player_x += (target_x - player_x) * 10.0 * dt
    
    if is_jumping:
        if not gravity_inverted:
            player_y_vel -= GRAVITY * dt
            player_y += player_y_vel * dt
            if player_y <= 0:
                player_y = 0
                is_jumping = False
                player_y_vel = 0
        else:
            player_y_vel += GRAVITY * dt
            player_y += player_y_vel * dt
            if player_y >= CEILING_HEIGHT:
                player_y = CEILING_HEIGHT
                is_jumping = False
                player_y_vel = 0
    else:
        player_y = CEILING_HEIGHT if gravity_inverted else 0

def player_jump():
    global is_jumping, player_y_vel
    if not is_jumping:
        is_jumping = True
        player_y_vel = JUMP_VELOCITY if not gravity_inverted else -JUMP_VELOCITY

def toggle_gravity():
    global gravity_inverted, player_y, is_jumping, player_y_vel
    gravity_inverted = not gravity_inverted
    player_y = CEILING_HEIGHT if gravity_inverted else 0
    is_jumping = False
    player_y_vel = 0


# ============================================================================
# === ZONE 3: MEMBER 3 — OBSTACLES & COLLISIONS =============================
# ============================================================================
def spawn_pattern():
    global obstacles
    # Randomly choose a pattern that utilizes spheres and ceiling slabs
    pattern = random.choice(['wall_with_gap', 'low_spheres', 'hanging_slabs', 'powerup_only'])
    spawn_z = -TUNNEL_LENGTH + 200
    
    if pattern == 'wall_with_gap':
        # One safe lane, two blocked by either full slabs or big spheres
        gap_lane = random.choice([-1, 0, 1])
        for lane in [-1, 0, 1]:
            if lane != gap_lane:
                shape = random.choice(['sphere', 'slab'])
                if shape == 'slab':
                    # Full pillar blocking the lane (touches floor and ceiling)
                    obstacles.append({
                        'type': 'obstacle', 'shape': 'slab',
                        'x': lane * PLAYER_LANE_SPACING, 'y': CEILING_HEIGHT / 2, 'z': spawn_z,
                        'w': 60, 'h': CEILING_HEIGHT, 'd': 40,
                        'active': True
                    })
                else:
                    # Large sphere blocking the lane
                    obstacles.append({
                        'type': 'obstacle', 'shape': 'sphere',
                        'x': lane * PLAYER_LANE_SPACING, 'y': 40, 'z': spawn_z,
                        'w': 80, 'h': 80, 'd': 80,
                        'active': True
                    })
    elif pattern == 'low_spheres':
        # Three spheres on the ground — player must jump
        for lane in [-1, 0, 1]:
            obstacles.append({
                'type': 'obstacle', 'shape': 'sphere',
                'x': lane * PLAYER_LANE_SPACING, 'y': 25, 'z': spawn_z,
                'w': 50, 'h': 50, 'd': 50,
                'active': True
            })
    elif pattern == 'hanging_slabs':
        # Three slabs touching the ceiling — player must duck
        for lane in [-1, 0, 1]:
            obstacles.append({
                'type': 'obstacle', 'shape': 'slab',
                'x': lane * PLAYER_LANE_SPACING, 'y': CEILING_HEIGHT - 40, 'z': spawn_z,
                'w': 80, 'h': 80, 'd': 40,
                'active': True
            })
    elif pattern == 'powerup_only':
        lane = random.choice([-1, 0, 1])
        
        # Decide powerup tier based on random chance
        chance = random.random()
        
        # 50% chance for a regular point to be on the ceiling
        is_ceiling = random.choice([True, False])
        base_y = CEILING_HEIGHT - 30 if is_ceiling else 30

        if chance < 0.50: # 50% chance - Common
            tier = 1
            points = 10
            y = base_y
            w = 30 # Slightly bigger
        elif chance < 0.80: # 30% chance - Uncommon
            tier = 2
            points = 30
            y = base_y
            w = 30
        elif chance < 0.95: # 15% chance - Rare
            tier = 3
            points = 50
            y = base_y
            w = 30
        else: # 5% chance - Ultra Rare GIGA point on ceiling
            tier = 4 
            points = 100
            y = CEILING_HEIGHT - 10 # Closer to the ceiling
            w = 20 # Very small so it's hard to get
            
        obstacles.append({
            'type': 'powerup', 'shape': 'sphere', 'tier': tier, 'points': points,
            'x': lane * PLAYER_LANE_SPACING, 'y': y, 'z': spawn_z,
            'w': w, 'h': w, 'd': w,
            'active': True
        })

def update_obstacles(dt):
    global obstacles, spawn_timer, score
    scroll = SCROLL_SPEED * game_speed * dt
    for obs in obstacles:
        obs['z'] += scroll
        
    for obs in obstacles:
        if obs['z'] > 200 and obs['active'] and obs['type'] == 'obstacle':
            score += 1 # Score point for dodging
            obs['active'] = False
            
    obstacles = [obs for obs in obstacles if obs['z'] < 500]
    
    spawn_timer -= dt * game_speed
    if spawn_timer <= 0:
        spawn_pattern()
        spawn_timer = SPAWN_INTERVAL

def draw_obstacles():
    for obs in obstacles:
        if not obs['active']: continue
        
        glPushMatrix()
        glTranslatef(obs['x'], obs['y'], obs['z'])
        
        dist = abs(obs['z'] - player_z)
        if dist < 600:
            scale_pulse = 1.0 + 0.2 * math.sin(time.time() * 10)
            glScalef(scale_pulse, scale_pulse, scale_pulse)
        
        if obs['type'] == 'obstacle':
            glColor3f(1.0, 0.2, 0.2)
            if obs['shape'] == 'sphere':
                q = gluNewQuadric()
                gluSphere(q, obs['w']/2, 16, 16)
            elif obs['shape'] == 'slab':
                glScalef(obs['w']/20, obs['h']/20, obs['d']/20)
                glutSolidCube(20)
        else:
            if obs['tier'] == 1:
                glColor3f(0.5, 1.0, 0.5) # Green (Common)
            elif obs['tier'] == 2:
                glColor3f(0.2, 0.8, 1.0) # Cyan (Uncommon)
            elif obs['tier'] == 3:
                glColor3f(1.0, 0.8, 0.0) # Gold (Rare)
            elif obs['tier'] == 4:
                glColor3f(1.0, 0.2, 1.0) # Magenta (Giga)
                
            q = gluNewQuadric()
            gluSphere(q, obs['w']/2, 10, 10)
            
        glPopMatrix()

def check_collisions():
    global game_over, score
    
    pw = 40
    ph = 30 if is_ducking else 60
    pd = 40
    
    px = player_x
    py = player_y + (ph/2)
    pz = player_z
    
    if gravity_inverted:
        py = player_y - (ph/2)

    for obs in obstacles:
        if not obs['active']: continue
        
        ow, oh, od = obs['w'], obs['h'], obs['d']
        ox, oy, oz = obs['x'], obs['y'], obs['z']
        
        collision_x = abs(px - ox) < (pw + ow) / 2
        collision_y = abs(py - oy) < (ph + oh) / 2
        collision_z = abs(pz - oz) < (pd + od) / 2
        
        if collision_x and collision_y and collision_z:
            if obs['type'] == 'obstacle':
                game_over = True
            elif obs['type'] == 'powerup':
                obs['active'] = False
                score += obs.get('points', 50)


# ============================================================================
# === ZONE 4: MAIN GAME LOOP ================================================
# ============================================================================
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def keyboardListener(key, x, y):
    global game_paused, target_lane, is_ducking
    
    if key == b'p':
        game_paused = not game_paused
    if key == b'r':
        reset_game()
        
    if not game_paused and not game_over:
        if key == b'a' and target_lane > -1:
            target_lane -= 1
        if key == b'd' and target_lane < 1:
            target_lane += 1
        if key == b'w' or key == b' ':
            player_jump()
        if key == b's':
            is_ducking = True
        if key == b'g':
            toggle_gravity()
            
    glutPostRedisplay()

def keyboardUpListener(key, x, y):
    global is_ducking
    if key == b's':
        is_ducking = False

def specialKeyListener(key, x, y):
    pass 

def reset_game():
    global game_over, score, time_survived, game_speed
    global target_lane, player_x, player_y, is_jumping, player_y_vel, gravity_inverted
    global obstacles, spawn_timer
    
    game_over = False
    score = 0
    time_survived = 0.0
    game_speed = 1.0
    
    target_lane = 0
    player_x = 0.0
    gravity_inverted = False
    player_y = 0.0
    is_jumping = False
    player_y_vel = 0.0
    
    obstacles = []
    spawn_timer = 0.0
    init_tunnel()

def idle():
    global last_frame_time, time_survived, game_speed
    
    current_time = time.time()
    if last_frame_time == 0:
        last_frame_time = current_time
    dt = current_time - last_frame_time
    last_frame_time = current_time
    
    if dt > 0.1: dt = 0.1 
    
    if not game_paused and not game_over:
        time_survived += dt
        game_speed = 1.0 + (time_survived * 0.02)
        
        update_tunnel(dt)
        update_warp_fov()
        update_player(dt)
        update_obstacles(dt)
        check_collisions()
        
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    
    setupCamera()
    
    draw_tunnel()
    draw_obstacles()
    draw_player()
    
    draw_text(10, 770, f"Score: {score}")
    draw_text(10, 740, f"Time: {time_survived:.1f}s | Speed: {game_speed:.1f}x")
    
    if game_over:
        draw_text(400, 400, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(380, 360, "Press R to restart")
    if game_paused:
        draw_text(420, 400, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
        
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Obstacle Runner 423 - Full Game")
    
    glEnable(GL_DEPTH_TEST)
    init_tunnel()
    
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(idle)
    
    glutMainLoop()

if __name__ == "__main__":
    main()
