from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time
import random

# ============================================================================
# === NEURAL NETWORK (From snake-ai) =========================================
# ============================================================================
def lerp(start: float, stop: float, amt: float) -> float:
    return amt * (stop - start) + start

class Level:
    def __init__(self, input_count: int, output_count: int):
        self.input_count = input_count
        self.output_count = output_count
        self.inputs = [0.0 for _ in range(input_count)]
        self.outputs = [0.0 for _ in range(output_count)]
        self.biases = [0.0 for _ in range(output_count)]
        self.weights = [[0.0 for _ in range(output_count)] for _ in range(input_count)]
        self._randomize()

    def _randomize(self):
        for i in range(self.input_count):
            for j in range(self.output_count):
                self.weights[i][j] = random.uniform(-1, 1)

        for i in range(self.output_count):
            self.biases[i] = random.uniform(-1, 1)

    @staticmethod
    def feed_forward(given_inputs: list, level: 'Level') -> list:
        for i in range(level.input_count):
            level.inputs[i] = given_inputs[i]

        for i in range(level.output_count):
            sum_val = 0.0
            for j in range(level.input_count):
                sum_val += level.inputs[j] * level.weights[j][i]

            if sum_val > level.biases[i]:
                level.outputs[i] = 1.0
            else:
                level.outputs[i] = 0.0

        return level.outputs

class NeuralNetwork:
    def __init__(self, neuron_counts: list):
        self.levels = []
        for i in range(len(neuron_counts) - 1):
            self.levels.append(Level(neuron_counts[i], neuron_counts[i + 1]))

    @staticmethod
    def feed_forward(given_inputs: list, network: 'NeuralNetwork') -> list:
        outputs = Level.feed_forward(given_inputs, network.levels[0])
        for i in range(1, len(network.levels)):
            outputs = Level.feed_forward(outputs, network.levels[i])
        return outputs

    @staticmethod
    def mutate(network: 'NeuralNetwork', amount: float = 1.0):
        for level in network.levels:
            for i in range(len(level.biases)):
                level.biases[i] = lerp(level.biases[i], random.uniform(-1, 1), amount)
            for i in range(len(level.weights)):
                for j in range(len(level.weights[i])):
                    level.weights[i][j] = lerp(level.weights[i][j], random.uniform(-1, 1), amount)

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

players = []
generation = 1
population_size = 50

GRAVITY = 2000.0
JUMP_VELOCITY = 700.0
CEILING_HEIGHT = 150.0

# --- Member 3 Globals (Obstacles) ---
obstacles = []
spawn_timer = 0.0
SPAWN_INTERVAL = 0.6


# ============================================================================
# === ZONE 1: MEMBER 1 — WORLD & CAMERA =====================================
# Tasks & Execution Flow:
# 1. The Arcade Tunnel: Draw a grid floor and side pillars and translate them along Z-axis.
# 2. Day/Night Cycle: Interpolate RGB values to change the tunnel color over time.
# 3. Warp Speed Camera: Modify setupCamera() so fovY gently expands as game speed increases.
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
import copy

class PlayerAI:
    def __init__(self, brain=None):
        self.target_lane = 0
        self.player_x = 0.0
        self.player_y = 0.0
        self.player_z = 0.0
        
        self.player_y_vel = 0.0
        self.is_jumping = False
        self.is_ducking = False
        self.gravity_inverted = False
        
        self.player_anim_time = 0.0
        
        self.alive = True
        self.score = 0
        self.time_survived = 0.0
        
        # 13 inputs, 6 outputs
        if brain:
            self.brain = copy.deepcopy(brain)
        else:
            self.brain = NeuralNetwork([13, 16, 6])
            
    def look(self, obstacles):
        inputs = []
        for lane in [-1, 0, 1]:
            closest_obj = None
            closest_dist = 1000.0
            
            for obs in obstacles:
                if not obs['active'] or obs['z'] > 200 or obs['z'] < -1000:
                    continue
                obs_lane = round(obs['x'] / PLAYER_LANE_SPACING)
                if obs_lane == lane:
                    dist = abs(obs['z'] - self.player_z)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_obj = obs
                        
            if closest_obj:
                inputs.append(closest_dist / 1000.0)
                inputs.append(closest_obj['y'] / CEILING_HEIGHT)
                if closest_obj['type'] == 'obstacle':
                    inputs.append(1.0)
                else:
                    inputs.append(0.5)
            else:
                inputs.append(1.0)
                inputs.append(0.0)
                inputs.append(0.0)

        inputs.append((self.target_lane + 1) / 2.0)
        inputs.append(1.0 if self.is_ducking else 0.0)
        inputs.append(1.0 if self.gravity_inverted else 0.0)
        inputs.append(self.player_y / CEILING_HEIGHT)
        
        return inputs

    def think(self, obstacles):
        inputs = self.look(obstacles)
        outputs = NeuralNetwork.feed_forward(inputs, self.brain)
        
        lane_outputs = outputs[0:3]
        max_idx = lane_outputs.index(max(lane_outputs))
        self.target_lane = max_idx - 1
        
        if outputs[3] > 0.5:
            self.jump()
            
        self.is_ducking = outputs[4] > 0.5
        
        want_inverted = outputs[5] > 0.5
        if self.gravity_inverted != want_inverted:
            self.toggle_gravity()

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.player_y_vel = JUMP_VELOCITY if not self.gravity_inverted else -JUMP_VELOCITY

    def toggle_gravity(self):
        self.gravity_inverted = not self.gravity_inverted
        self.player_y = CEILING_HEIGHT if self.gravity_inverted else 0
        self.is_jumping = False
        self.player_y_vel = 0

    def update(self, dt):
        self.player_anim_time += dt
        self.time_survived += dt
        
        target_x = self.target_lane * PLAYER_LANE_SPACING
        self.player_x = target_x
        
        if self.is_jumping:
            if not self.gravity_inverted:
                self.player_y_vel -= GRAVITY * dt
                self.player_y += self.player_y_vel * dt
                if self.player_y <= 0:
                    self.player_y = 0
                    self.is_jumping = False
                    self.player_y_vel = 0
            else:
                self.player_y_vel += GRAVITY * dt
                self.player_y += self.player_y_vel * dt
                if self.player_y >= CEILING_HEIGHT:
                    self.player_y = CEILING_HEIGHT
                    self.is_jumping = False
                    self.player_y_vel = 0
        else:
            self.player_y = CEILING_HEIGHT if self.gravity_inverted else 0

def draw_players():
    # Only draw alive players
    for i, p in enumerate(players):
        if not p.alive: continue
        
        glPushMatrix()
        glTranslatef(p.player_x, p.player_y, p.player_z)
        
        if p.gravity_inverted:
            glTranslatef(0, 30, 0)
            glRotatef(180, 0, 0, 1) # Rotate around Z to flip upside down
            glTranslatef(0, -30, 0)
            
        if p.is_ducking:
            glTranslatef(0, 15, 0)
            glScalef(1.0, 0.5, 1.0)
            glTranslatef(0, -15, 0)
            
        r = (i * 40 % 255) / 255.0
        g = (i * 80 % 255) / 255.0
        b = (i * 120 % 255) / 255.0
            
        # Body
        glColor3f(r, g, b)
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
        
        swing = math.sin(p.player_anim_time * 15 * game_speed) * 45 if not p.is_jumping else 0
        
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

def update_players(dt):
    for p in players:
        if p.alive:
            p.think(obstacles)
            p.update(dt)

def next_generation():
    global players, generation
    
    for p in players:
        p.fitness = p.score
        
    players.sort(key=lambda p: p.fitness, reverse=True)
    
    best_brain = players[0].brain
    
    new_players = []
    new_players.append(PlayerAI(best_brain)) # Elitism
    
    for i in range(1, population_size):
        child = PlayerAI(best_brain)
        NeuralNetwork.mutate(child.brain, amount=0.1)
        new_players.append(child)
        
    players = new_players
    generation += 1
    
    reset_level()

def reset_level():
    global time_survived, game_speed, obstacles, spawn_timer
    time_survived = 0.0
    game_speed = 3.0
    obstacles = []
    spawn_timer = 0.0
    init_tunnel()


# ============================================================================
# === ZONE 3: MEMBER 3 — OBSTACLES & COLLISIONS =============================
# Tasks & Execution Flow:
# 1. Object Manager: Track active obstacles and powerups (type, X, Y, Z, active state).
# 2. Pattern Spawning: Spawn objects in specific formations moving toward the camera.
# 3. Dynamic 3D AABB Collision: Detect intersections, adjustable player bounding box.
# 4. Morphing Logic: Scale or swap obstacle shape when Z-distance drops below threshold.
# ============================================================================
def spawn_pattern():
    global obstacles
    # Almost exclusively vertical bars and slabs
    pattern = random.choice(['wall_with_gap', 'wall_with_gap', 'wall_with_gap', 'wall_with_gap', 'hanging_slabs', 'powerup_only'])
    spawn_z = -TUNNEL_LENGTH + 200
    
    if pattern == 'wall_with_gap':
        # One safe lane, two blocked by either full slabs or big spheres
        gap_lane = random.choice([-1, 0, 1])
        for lane in [-1, 0, 1]:
            if lane != gap_lane:
                shape = 'slab'
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
        # Three spheres on the ceiling — player must duck or stay low
        for lane in [-1, 0, 1]:
            obstacles.append({
                'type': 'obstacle', 'shape': 'sphere',
                'x': lane * PLAYER_LANE_SPACING, 'y': CEILING_HEIGHT - 25, 'z': spawn_z,
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

    # --- Bonus coin spawn: 50% chance to also drop a coin with obstacle patterns ---
    if pattern != 'powerup_only' and random.random() < 0.50:
        coin_lane = random.choice([-1, 0, 1])
        coin_ceiling = random.choice([True, False])
        coin_y = CEILING_HEIGHT - 30 if coin_ceiling else 30
        obstacles.append({
            'type': 'powerup', 'shape': 'sphere', 'tier': 1, 'points': 10,
            'x': coin_lane * PLAYER_LANE_SPACING, 'y': coin_y, 'z': spawn_z,
            'w': 30, 'h': 30, 'd': 30,
            'active': True
        })

def update_obstacles(dt):
    global obstacles, spawn_timer
    scroll = SCROLL_SPEED * game_speed * dt
    for obs in obstacles:
        obs['z'] += scroll
        
    for obs in obstacles:
        if obs['z'] > 200 and obs['active'] and obs['type'] == 'obstacle':
            for p in players:
                if p.alive:
                    p.score += 1
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
                glColor3f(0.5, 1.0, 0.5)
            elif obs['tier'] == 2:
                glColor3f(0.2, 0.8, 1.0)
            elif obs['tier'] == 3:
                glColor3f(1.0, 0.8, 0.0)
            elif obs['tier'] == 4:
                glColor3f(1.0, 0.2, 1.0)
                
            q = gluNewQuadric()
            gluSphere(q, obs['w']/2, 10, 10)
            
        glPopMatrix()

def check_collisions():
    alive_count = 0
    
    for p in players:
        if not p.alive: continue
        alive_count += 1
        
        pw = 40
        ph = 30 if p.is_ducking else 60
        pd = 40
        
        px = p.player_x
        py = p.player_y + (ph/2)
        pz = p.player_z
        
        if p.gravity_inverted:
            py = p.player_y - (ph/2)

        for obs in obstacles:
            if not obs['active']: continue
            
            ow, oh, od = obs['w'], obs['h'], obs['d']
            ox, oy, oz = obs['x'], obs['y'], obs['z']
            
            collision_x = abs(px - ox) < (pw + ow) / 2
            collision_y = abs(py - oy) < (ph + oh) / 2
            collision_z = abs(pz - oz) < (pd + od) / 2
            
            if collision_x and collision_y and collision_z:
                if obs['type'] == 'obstacle':
                    p.alive = False
                    alive_count -= 1
                    break
                elif obs['type'] == 'powerup':
                    obs['active'] = False
                    p.score += obs.get('points', 50)
                    
    if alive_count == 0 and len(players) > 0:
        next_generation()


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
    global game_paused
    
    if key == b'p':
        game_paused = not game_paused
    if key == b'r':
        reset_game()
        
    glutPostRedisplay()

def keyboardUpListener(key, x, y):
    pass

def specialKeyListener(key, x, y):
    pass 

def reset_game():
    global players, generation, game_over, game_paused
    
    game_over = False
    game_paused = False
    generation = 1
    
    players = [PlayerAI() for _ in range(population_size)]
    reset_level()

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
        game_speed = 3.0 + (time_survived * 0.06)
        
        update_tunnel(dt)
        update_warp_fov()
        update_players(dt)
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
    draw_players()
    
    best_score = max([p.score for p in players]) if players else 0
    alive_count = len([p for p in players if p.alive])
    
    draw_text(10, 770, f"Generation: {generation} | Alive: {alive_count}/{population_size}")
    draw_text(10, 740, f"Best Score: {best_score} | Time: {time_survived:.1f}s | Speed: {game_speed:.1f}x")
    
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
    glutCreateWindow(b"Obstacle Runner 423 - AI Training")
    
    glEnable(GL_DEPTH_TEST)
    reset_game() # Initialize everything including first population
    
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutKeyboardUpFunc(keyboardUpListener)
    glutSpecialFunc(specialKeyListener)
    glutIdleFunc(idle)
    
    glutMainLoop()

if __name__ == "__main__":
    main()
