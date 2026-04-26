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

# --- Member 1 Globals (Core Engine & AI Systems) ---
time_survived = 0.0
game_over = False
game_paused = False
score = 0
last_frame_time = 0
cheat_mode = False
TUNNEL_WIDTH = 200
TUNNEL_LENGTH = 1500
PILLAR_COUNT = 10
PILLAR_SPACING = 150
SCROLL_SPEED = 300
pillar_z_offsets = []
DAY_NIGHT_CYCLE = 30.0

# --- Member 2 Globals (Player Controller & Physics) ---
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

# --- Member 3 Globals (Level Design & Collisions) ---
camera_pos = (0, 75, 200)
look_at = (0, 50, -500)
fovY = 120
game_speed = 1.0
obstacles = []
spawn_timer = 0.0
SPAWN_INTERVAL = 1.2


# ============================================================================
# === ZONE 1: MEMBER 1 — CORE ENGINE & AI SYSTEMS ===========================
# Workload & Responsibilities (19 Points):
# 1. Cheat Mode / AI Autopilot (8 pts): Algorithm to scan upcoming obstacles and make lane/ducking decisions.
# 2. Game State Management (4 pts): Pause logic, game over screen logic, reset functionality, and score tracking.
# 3. Day/Night Cycle (4 pts): Skybox and lighting interpolation using math.sin().
# 4. Infinite Tunnel Scrolling (3 pts): Move environment pillars along the Z-axis.
# ============================================================================
def init_tunnel():
    global pillar_z_offsets
    pillar_z_offsets=[-i*PILLAR_SPACING for i in range(PILLAR_COUNT)]

def get_day_night_color(day_color,night_color):
    t=(time_survived%DAY_NIGHT_CYCLE)/DAY_NIGHT_CYCLE
    factor=(math.sin(t*2*math.pi-math.pi/2)+1)/2
    return (
        day_color[0] * factor + night_color[0] * (1 - factor),
        day_color[1] * factor + night_color[1] * (1 - factor),
        day_color[2] * factor + night_color[2] * (1 - factor)
    )

def draw_tunnel():
    floor_color = get_day_night_color((0.12, 0.12, 0.18), (0.03, 0.01, 0.08))
    ceiling_color = get_day_night_color((0.08, 0.08, 0.14), (0.02, 0.01, 0.06))
    
    # Floor
    glColor3f(*floor_color)
    glBegin(GL_QUADS)
    glVertex3f(-TUNNEL_WIDTH, 0, 500)
    glVertex3f(TUNNEL_WIDTH, 0, 500)
    glVertex3f(TUNNEL_WIDTH, 0, -TUNNEL_LENGTH)
    glVertex3f(-TUNNEL_WIDTH, 0, -TUNNEL_LENGTH)
    glEnd()

    # Floor grid lines for depth feel
    grid_col = get_day_night_color((0.25, 0.25, 0.35), (0.0, 0.6, 0.8))
    glColor3f(*grid_col)
    glBegin(GL_LINES)
    for gz in range(0, TUNNEL_LENGTH, 80):
        glVertex3f(-TUNNEL_WIDTH, 0.5, -gz)
        glVertex3f(TUNNEL_WIDTH, 0.5, -gz)
    for gx_i in range(-2, 3):
        gx = gx_i * (TUNNEL_WIDTH // 2)
        glVertex3f(gx, 0.5, 500)
        glVertex3f(gx, 0.5, -TUNNEL_LENGTH)
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
    base_col = get_day_night_color((0.3, 0.3, 0.4), (0.0, 0.4, 0.6))
    col_col = get_day_night_color((0.2, 0.2, 0.3), (0.6, 0.0, 0.4))
    
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

def update_cheat_mode():
    global target_lane, is_ducking
    if not cheat_mode or game_over or game_paused: return
    
    # Find the closest cluster of objects in front of the player
    upcoming_objs = [obs for obs in obstacles if obs['active'] and obs['z'] < 100 and obs['z'] > -800]
    if not upcoming_objs:
        target_lane = 0
        is_ducking = False
        if gravity_inverted: toggle_gravity()
        return
        
    upcoming_objs.sort(key=lambda o: o['z'], reverse=True)
    closest_z = upcoming_objs[0]['z']
    
    # Get all objects in this immediate wave
    wave_objs = [obs for obs in upcoming_objs if abs(obs['z'] - closest_z) < 150]
    
    best_score = -9999
    best_state = (0, False, False) # (lane, ducking, inverted)
    
    for lane in [-1, 0, 1]:
        for duck in [False, True]:
            for inverted in [False, True]:
                pw = 30
                ph = PLAYER_DUCK_HEIGHT if duck else PLAYER_VISUAL_HEIGHT
                
                px = lane * PLAYER_LANE_SPACING
                ceiling_foot_y = CEILING_HEIGHT + 50
                py = ceiling_foot_y if inverted else 0
                
                py_center = py - (ph/2) if inverted else py + (ph/2)
                
                state_score = 0
                hit_obstacle = False
                
                for obs in wave_objs:
                    ow, oh = obs['w'], obs['h']
                    ox, oy = obs['x'], obs['y']
                    
                    collision_x = abs(px - ox) < (pw + ow) / 2
                    collision_y = abs(py_center - oy) < (ph + oh) / 2
                    
                    if collision_x and collision_y:
                        if obs['type'] == 'obstacle':
                            hit_obstacle = True
                            break
                        elif obs['type'] == 'powerup':
                            state_score += obs.get('points', 50)
                            
                if hit_obstacle:
                    state_score = -1000
                    
                # Small preference for default states if everything else is equal
                if not duck: state_score += 1
                if not inverted: state_score += 2
                if lane == 0: state_score += 1
                
                if state_score > best_score:
                    best_score = state_score
                    best_state = (lane, duck, inverted)
                    
    target_lane = best_state[0]
    is_ducking = best_state[1]
    if gravity_inverted != best_state[2]:
        toggle_gravity()


# ============================================================================
# === ZONE 2: MEMBER 2 — PLAYER CONTROLLER & PHYSICS ========================
# Workload & Responsibilities (19 Points):
# 1. Hierarchical Avatar (6 pts): Construct the robot using OpenGL primitives.
# 2. Kinematics & Jumping (5 pts): Handle gravity acceleration, smooth lane switching.
# 3. Animation System (4 pts): Program the running, jumping, and ducking visuals.
# 4. Gravity Inversion (4 pts): Flip upside down and run on the ceiling.
# ============================================================================
# Player visual height constants (used for both drawing and collision)
PLAYER_VISUAL_HEIGHT = 67  # From feet (Y=0) to top of head (Y=67)
PLAYER_DUCK_HEIGHT = 34    # Half height when ducking

def draw_player():
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z)
    
    if gravity_inverted:
        # Flip the model so it hangs downward from player_y (ceiling)
        # The model normally goes from 0..67, so we flip around the midpoint
        glScalef(1.0, -1.0, 1.0)  # Mirror on Y axis
        
    if is_ducking:
        glTranslatef(0, 0, 0)
        glScalef(1.0, 0.5, 1.0)
        
    # Body (taller torso)
    glColor3f(0.1, 0.35, 0.7)
    glPushMatrix()
    glTranslatef(0, 38, 0)
    glScalef(1.5, 1.6, 1.0)
    glutSolidCube(20)
    glPopMatrix()
    
    # Body accent stripe
    glColor3f(0.0, 0.8, 1.0)
    glPushMatrix()
    glTranslatef(0, 38, 10.5)
    glScalef(1.2, 0.3, 0.05)
    glutSolidCube(20)
    glPopMatrix()
    
    # Head
    glColor3f(0.9, 0.8, 0.7)
    glPushMatrix()
    glTranslatef(0, 60, 0)
    glutSolidCube(14)
    glPopMatrix()
    
    # Visor on head
    glColor3f(0.0, 0.9, 1.0)
    glPushMatrix()
    glTranslatef(0, 61, 7.5)
    glScalef(1.0, 0.4, 0.1)
    glutSolidCube(12)
    glPopMatrix()
    
    swing = math.sin(player_anim_time * 15 * game_speed) * 45 if not is_jumping else 0
    
    # Left Arm
    glColor3f(0.6, 0.15, 0.15)
    glPushMatrix()
    glTranslatef(-22, 50, 0)
    glRotatef(swing, 1, 0, 0)
    glTranslatef(0, -12, 0)
    glScalef(0.3, 1.2, 0.3)
    glutSolidCube(20)
    glPopMatrix()
    
    # Right Arm
    glPushMatrix()
    glTranslatef(22, 50, 0)
    glRotatef(-swing, 1, 0, 0)
    glTranslatef(0, -12, 0)
    glScalef(0.3, 1.2, 0.3)
    glutSolidCube(20)
    glPopMatrix()
    
    # Left Leg
    glColor3f(0.15, 0.15, 0.4)
    glPushMatrix()
    glTranslatef(-8, 18, 0)
    glRotatef(-swing, 1, 0, 0)
    glTranslatef(0, -12, 0)
    glScalef(0.4, 1.3, 0.4)
    glutSolidCube(20)
    glPopMatrix()
    
    # Right Leg
    glPushMatrix()
    glTranslatef(8, 18, 0)
    glRotatef(swing, 1, 0, 0)
    glTranslatef(0, -12, 0)
    glScalef(0.4, 1.3, 0.4)
    glutSolidCube(20)
    glPopMatrix()
    
    glPopMatrix()

def update_player(dt):
    global player_x, player_y, player_y_vel, is_jumping, player_anim_time
    player_anim_time += dt
    
    target_x = target_lane * PLAYER_LANE_SPACING
    player_x += (target_x - player_x) * 10.0 * dt
    
    # Compute the max Y the player's feet can be at when inverted
    # The visual ceiling is at CEILING_HEIGHT + 50, player model hangs down from feet
    ceiling_foot_y = CEILING_HEIGHT + 50  # Feet touch the visual ceiling surface
    
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
            if player_y >= ceiling_foot_y:
                player_y = ceiling_foot_y
                is_jumping = False
                player_y_vel = 0
    else:
        player_y = ceiling_foot_y if gravity_inverted else 0

def player_jump():
    global is_jumping, player_y_vel
    if not is_jumping:
        is_jumping = True
        player_y_vel = JUMP_VELOCITY if not gravity_inverted else -JUMP_VELOCITY

def toggle_gravity():
    global gravity_inverted, player_y, is_jumping, player_y_vel
    gravity_inverted = not gravity_inverted
    ceiling_foot_y = CEILING_HEIGHT + 50
    player_y = ceiling_foot_y if gravity_inverted else 0
    is_jumping = False
    player_y_vel = 0


# ============================================================================
# === ZONE 3: MEMBER 3 — LEVEL DESIGN & COLLISIONS ==========================
# Workload & Responsibilities (19 Points):
# 1. Obstacle Pattern Spawner (7 pts): Generate waves of obstacles logically.
# 2. 3D AABB Collision Detection (6 pts): Math to detect player and object intersections.
# 3. Powerups & Morphing (3 pts): Tiered coin system and pulsing visual effects.
# 4. Warp Camera & Game Speed (3 pts): Scale difficulty and Field of View as the game gets faster.
# ============================================================================
def spawn_pattern():
    global obstacles
    # Randomly choose a pattern that utilizes spheres and ceiling slabs
    pattern = random.choice(['wall_with_gap', 'low_spheres', 'ceiling_spheres', 'hanging_slabs', 'powerup_only', 'powerup_only'])
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
                    # Large sphere blocking the lane — floor or ceiling
                    sphere_on_ceiling = random.choice([True, False])
                    sphere_y = CEILING_HEIGHT - 40 if sphere_on_ceiling else 40
                    obstacles.append({
                        'type': 'obstacle', 'shape': 'sphere',
                        'x': lane * PLAYER_LANE_SPACING, 'y': sphere_y, 'z': spawn_z,
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
    elif pattern == 'ceiling_spheres':
        # Three spheres hanging low — standing player's head collides, must duck
        for lane in [-1, 0, 1]:
            obstacles.append({
                'type': 'obstacle', 'shape': 'sphere',
                'x': lane * PLAYER_LANE_SPACING, 'y': 80, 'z': spawn_z,
                'w': 50, 'h': 50, 'd': 50,
                'active': True
            })
    elif pattern == 'hanging_slabs':
        # Three slabs hanging low — standing player collides, must duck to pass under
        for lane in [-1, 0, 1]:
            obstacles.append({
                'type': 'obstacle', 'shape': 'slab',
                'x': lane * PLAYER_LANE_SPACING, 'y': 80, 'z': spawn_z,
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

        # Each tier gets a unique shape
        if chance < 0.50: # 50% chance - Common
            tier = 1
            points = 10
            y = base_y
            w = 30
            pshape = 'triangle'  # Triangle spike
        elif chance < 0.80: # 30% chance - Uncommon
            tier = 2
            points = 30
            y = base_y
            w = 30
            pshape = 'rectangle'  # Rectangle
        elif chance < 0.95: # 15% chance - Rare
            tier = 3
            points = 50
            y = base_y
            w = 30
            pshape = 'square'  # Square
        else: # 5% chance - Ultra Rare GIGA point on ceiling
            tier = 4 
            points = 100
            y = CEILING_HEIGHT - 10
            w = 20
            pshape = 'diamond'  # Diamond
            
        obstacles.append({
            'type': 'powerup', 'shape': pshape, 'tier': tier, 'points': points,
            'x': lane * PLAYER_LANE_SPACING, 'y': y, 'z': spawn_z,
            'w': w, 'h': w, 'd': w,
            'active': True
        })

    # --- Bonus coin spawn: 50% chance to also drop a coin with obstacle patterns ---
    if pattern != 'powerup_only' and random.random() < 0.50:
        coin_lane = random.choice([-1, 0, 1])
        coin_ceiling = random.choice([True, False])
        coin_y = CEILING_HEIGHT - 30 if coin_ceiling else 30
        obstacles.append({
            'type': 'powerup', 'shape': 'triangle', 'tier': 1, 'points': 10,
            'x': coin_lane * PLAYER_LANE_SPACING, 'y': coin_y, 'z': spawn_z,
            'w': 30, 'h': 30, 'd': 30,
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

def draw_triangle_spike(size):
    """Draw a 3D triangular spike (tetrahedron-like) pointing upward."""
    s = size / 2
    glBegin(GL_TRIANGLES)
    # Front face
    glVertex3f(0, s * 1.5, 0)
    glVertex3f(-s, -s, s)
    glVertex3f(s, -s, s)
    # Right face
    glVertex3f(0, s * 1.5, 0)
    glVertex3f(s, -s, s)
    glVertex3f(s, -s, -s)
    # Back face
    glVertex3f(0, s * 1.5, 0)
    glVertex3f(s, -s, -s)
    glVertex3f(-s, -s, -s)
    # Left face
    glVertex3f(0, s * 1.5, 0)
    glVertex3f(-s, -s, -s)
    glVertex3f(-s, -s, s)
    glEnd()
    # Bottom
    glBegin(GL_QUADS)
    glVertex3f(-s, -s, s)
    glVertex3f(s, -s, s)
    glVertex3f(s, -s, -s)
    glVertex3f(-s, -s, -s)
    glEnd()

def draw_diamond(size):
    """Draw a 3D diamond (octahedron) shape."""
    s = size / 2
    glBegin(GL_TRIANGLES)
    # Top 4 faces
    for dx, dz, dx2, dz2 in [(s,0,0,s),(0,s,-s,0),(-s,0,0,-s),(0,-s,s,0)]:
        glVertex3f(0, s * 1.5, 0)
        glVertex3f(dx, 0, dz)
        glVertex3f(dx2, 0, dz2)
    # Bottom 4 faces
    for dx, dz, dx2, dz2 in [(s,0,0,s),(0,s,-s,0),(-s,0,0,-s),(0,-s,s,0)]:
        glVertex3f(0, -s * 1.5, 0)
        glVertex3f(dx2, 0, dz2)
        glVertex3f(dx, 0, dz)
    glEnd()

def draw_obstacles():
    for obs in obstacles:
        if not obs['active']: continue
        
        glPushMatrix()
        glTranslatef(obs['x'], obs['y'], obs['z'])
        
        dist = abs(obs['z'] - player_z)
        if dist < 600:
            scale_pulse = 1.0 + 0.15 * math.sin(time.time() * 8)
            glScalef(scale_pulse, scale_pulse, scale_pulse)
        
        # Rotate powerups for visual flair
        if obs['type'] == 'powerup':
            spin = (time.time() * 120) % 360
            glRotatef(spin, 0, 1, 0)
        
        if obs['type'] == 'obstacle':
            # Neon red with slight pulsing brightness
            pulse = 0.7 + 0.3 * abs(math.sin(time.time() * 5))
            glColor3f(1.0 * pulse, 0.1, 0.1)
            if obs['shape'] == 'sphere':
                q = gluNewQuadric()
                gluSphere(q, obs['w']/2, 16, 16)
            elif obs['shape'] == 'slab':
                glScalef(obs['w']/20, obs['h']/20, obs['d']/20)
                glutSolidCube(20)
        else:
            # Powerup colors per tier
            if obs['tier'] == 1:
                glColor3f(0.3, 1.0, 0.4)   # Neon green (Common)
            elif obs['tier'] == 2:
                glColor3f(0.1, 0.7, 1.0)   # Electric blue (Uncommon)
            elif obs['tier'] == 3:
                glColor3f(1.0, 0.85, 0.0)  # Gold (Rare)
            elif obs['tier'] == 4:
                glow = 0.7 + 0.3 * abs(math.sin(time.time() * 6))
                glColor3f(1.0 * glow, 0.1, 1.0 * glow)  # Pulsing magenta (Giga)
                
            # Draw shape based on type
            shape = obs.get('shape', 'triangle')
            sz = obs['w']
            if shape == 'triangle':
                draw_triangle_spike(sz)
            elif shape == 'rectangle':
                glScalef(1.0, 0.6, 1.0)
                glutSolidCube(sz)
            elif shape == 'square':
                glutSolidCube(sz * 0.7)
            elif shape == 'diamond':
                draw_diamond(sz)
            else:
                q = gluNewQuadric()
                gluSphere(q, sz/2, 10, 10)
            
        glPopMatrix()

def check_collisions():
    global game_over, score
    
    pw = 30          # Player width (X) — tighter than visual to be forgiving
    ph_stand = PLAYER_VISUAL_HEIGHT  # 67 — matches the actual drawn model
    ph_duck = PLAYER_DUCK_HEIGHT     # 34 — half when ducking
    ph = ph_duck if is_ducking else ph_stand
    pd = 20          # Player depth (Z) — tight to prevent early Z-axis hits
    
    px = player_x
    pz = player_z
    
    # Calculate the AABB center Y based on where the model actually is
    if not gravity_inverted:
        # Normal: feet at player_y (ground), model extends upward
        py = player_y + (ph / 2)
    else:
        # Inverted: feet at player_y (ceiling), model hangs downward
        py = player_y - (ph / 2)

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
# === ZONE 4: TEMPLATE BOILERPLATE & MAIN LOOP ==============================
# Workload & Responsibilities (0 Points - Provided by 3D_OpenGL_Intro.py):
# - draw_text, keyboard/mouse listeners, idle loop, and display scaffolding.
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
    if key == b'c':
        global cheat_mode
        cheat_mode = not cheat_mode
        
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
        update_cheat_mode()
        update_player(dt)
        update_obstacles(dt)
        check_collisions()
        
    glutPostRedisplay()

def draw_text_colored(x, y, text, r, g, b, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(r, g, b)
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

def showScreen():
    bg = get_day_night_color((0.05, 0.05, 0.1), (0.01, 0.0, 0.04))
    glClearColor(*bg, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    
    setupCamera()
    
    draw_tunnel()
    draw_obstacles()
    draw_player()
    
    draw_text_colored(10, 770, f"Score: {score}", 0.0, 1.0, 0.6)
    draw_text_colored(10, 740, f"Time: {time_survived:.1f}s | Speed: {game_speed:.1f}x", 0.6, 0.8, 1.0)
    
    if cheat_mode:
        draw_text_colored(10, 710, "[CHEAT MODE ON]", 1.0, 0.2, 1.0)
    
    if game_over:
        draw_text_colored(350, 420, "GAME OVER", 1.0, 0.2, 0.2, GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text_colored(360, 380, f"Final Score: {score}", 1.0, 0.85, 0.0)
        draw_text_colored(370, 350, "Press R to restart", 0.7, 0.7, 0.7)
    if game_paused:
        draw_text_colored(400, 400, "PAUSED", 0.0, 0.8, 1.0, GLUT_BITMAP_TIMES_ROMAN_24)
        
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

