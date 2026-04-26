def init_tunnel(): # Member 1: Initialize the tunnel function
    global pillar_z_offsets # Member 1: Declare global usage of pillar_z_offsets
    pillar_z_offsets = [-i * PILLAR_SPACING for i in range(PILLAR_COUNT)] # Member 1: Generate initial Z positions for all pillars

def get_day_night_color(day_color, night_color): # Member 1: Calculate interpolated color based on time
    t = (time_survived % DAY_NIGHT_CYCLE) / DAY_NIGHT_CYCLE # Member 1: Get the current normalized time within the day/night cycle
    factor = (math.sin(t * 2 * math.pi - math.pi/2) + 1) / 2 # Member 1: Use sine wave to smoothly transition between 0 and 1
    return ( # Member 1: Return a tuple of RGB values
        day_color[0] * factor + night_color[0] * (1 - factor), # Member 1: Interpolate the Red channel
        day_color[1] * factor + night_color[1] * (1 - factor), # Member 1: Interpolate the Green channel
        day_color[2] * factor + night_color[2] * (1 - factor) # Member 1: Interpolate the Blue channel
    ) # Member 1: End of return statement

def draw_tunnel(): # Member 1: Render the entire 3D tunnel environment
    floor_color = get_day_night_color((0.8, 0.8, 0.85), (0.05, 0.02, 0.15)) # Member 1: Calculate the current dynamic floor color
    ceiling_color = get_day_night_color((0.7, 0.7, 0.75), (0.02, 0.01, 0.1)) # Member 1: Calculate the current dynamic ceiling color
    
    # Floor # Member 1: Start drawing the floor quad
    glColor3f(*floor_color) # Member 1: Set OpenGL color to the calculated floor color
    glBegin(GL_QUADS) # Member 1: Begin specifying vertices for a quadrilateral
    glVertex3f(-TUNNEL_WIDTH, 0, 500) # Member 1: Specify bottom-left vertex
    glVertex3f(TUNNEL_WIDTH, 0, 500) # Member 1: Specify bottom-right vertex
    glVertex3f(TUNNEL_WIDTH, 0, -TUNNEL_LENGTH) # Member 1: Specify top-right vertex
    glVertex3f(-TUNNEL_WIDTH, 0, -TUNNEL_LENGTH) # Member 1: Specify top-left vertex
    glEnd() # Member 1: End drawing the floor quad

    # Ceiling # Member 1: Start drawing the ceiling quad
    glColor3f(*ceiling_color) # Member 1: Set OpenGL color to the calculated ceiling color
    glBegin(GL_QUADS) # Member 1: Begin specifying vertices for a quadrilateral
    glVertex3f(-TUNNEL_WIDTH, CEILING_HEIGHT + 50, 500) # Member 1: Specify bottom-left vertex
    glVertex3f(TUNNEL_WIDTH, CEILING_HEIGHT + 50, 500) # Member 1: Specify bottom-right vertex
    glVertex3f(TUNNEL_WIDTH, CEILING_HEIGHT + 50, -TUNNEL_LENGTH) # Member 1: Specify top-right vertex
    glVertex3f(-TUNNEL_WIDTH, CEILING_HEIGHT + 50, -TUNNEL_LENGTH) # Member 1: Specify top-left vertex
    glEnd() # Member 1: End drawing the ceiling quad

    # Pillars # Member 1: Start drawing the moving side pillars
    base_col = get_day_night_color((0.9, 0.9, 0.9), (0.0, 0.8, 1.0)) # Member 1: Calculate dynamic color for the pillar base
    col_col = get_day_night_color((0.7, 0.7, 0.75), (1.0, 0.0, 0.6)) # Member 1: Calculate dynamic color for the pillar column
    
    for z in pillar_z_offsets: # Member 1: Loop through all active Z offsets for pillars
        for x in [-TUNNEL_WIDTH, TUNNEL_WIDTH]: # Member 1: Loop to draw on both left and right sides of the tunnel
            glPushMatrix() # Member 1: Save the current transformation matrix
            glTranslatef(x, 0, z) # Member 1: Translate origin to the pillar's (X, 0, Z) position
            
            # Base # Member 1: Start drawing the cube base
            glColor3f(*base_col) # Member 1: Set the color for the base
            glTranslatef(0, 15, 0) # Member 1: Move up slightly so the base touches the floor
            glutSolidCube(30) # Member 1: Render a solid cube with size 30
            
            # Column # Member 1: Start drawing the cylindrical column
            glColor3f(*col_col) # Member 1: Set the color for the column
            glTranslatef(0, 15, 0) # Member 1: Move up from the base center to start the column
            glRotatef(-90, 1, 0, 0) # Member 1: Rotate 90 degrees around X to point the cylinder up (+Y)
            q = gluNewQuadric() # Member 1: Create a new quadric object for cylinder rendering
            gluCylinder(q, 10, 10, CEILING_HEIGHT + 20, 8, 1) # Member 1: Render the cylinder up to the ceiling
            
            glPopMatrix() # Member 1: Restore transformation matrix for the next pillar

def update_tunnel(dt): # Member 1: Update function to handle moving the tunnel pillars
    global pillar_z_offsets # Member 1: Declare global usage of pillar_z_offsets
    scroll = SCROLL_SPEED * game_speed * dt # Member 1: Calculate scroll distance based on speed and delta time
    for i in range(len(pillar_z_offsets)): # Member 1: Loop through each pillar index
        pillar_z_offsets[i] += scroll # Member 1: Move the pillar towards the camera (+Z)
        if pillar_z_offsets[i] > 200: # Member 1: If the pillar has passed the camera
            pillar_z_offsets[i] = min(pillar_z_offsets) - PILLAR_SPACING # Member 1: Teleport it to the far back to continue the loop

def reset_game(): # Member 1: Function to completely reset the game state
    global game_over, score, time_survived, game_speed # Member 1: Declare global usage of game state vars
    global target_lane, player_x, player_y, is_jumping, player_y_vel, gravity_inverted # Member 1: Declare global usage of player vars
    global obstacles, spawn_timer # Member 1: Declare global usage of obstacle vars
    
    game_over = False # Member 1: Unset game over state
    score = 0 # Member 1: Reset score to zero
    time_survived = 0.0 # Member 1: Reset survival time clock
    game_speed = 1.0 # Member 1: Reset game speed multiplier
    
    target_lane = 0 # Member 1: Reset player target lane to middle
    player_x = 0.0 # Member 1: Reset player visual X position
    gravity_inverted = False # Member 1: Reset player to the floor
    player_y = 0.0 # Member 1: Reset player Y position to floor level
    is_jumping = False # Member 1: Cancel any jumping state
    player_y_vel = 0.0 # Member 1: Reset player vertical velocity
    
    obstacles = [] # Member 1: Clear the list of all obstacles
    spawn_timer = 0.0 # Member 1: Reset the obstacle spawn timer
    init_tunnel() # Member 1: Re-initialize the tunnel pillar positions

def update_cheat_mode(): # Member 1: AI Autopilot logic that plays the game for the user
    global target_lane, is_ducking # Member 1: Declare global usage to control the player
    if not cheat_mode or game_over or game_paused: return # Member 1: Exit immediately if cheat mode is off or game is stopped
    
    # Find the closest cluster of objects in front of the player # Member 1: Logical grouping comment
    upcoming_objs = [obs for obs in obstacles if obs['active'] and obs['z'] < 100 and obs['z'] > -800] # Member 1: Filter out inactive or passed obstacles
    if not upcoming_objs: # Member 1: If there are no upcoming obstacles
        target_lane = 0 # Member 1: Move to the center lane by default
        is_ducking = False # Member 1: Stand up by default
        if gravity_inverted: toggle_gravity() # Member 1: Return to the floor if on the ceiling
        return # Member 1: Exit early since it's clear
        
    upcoming_objs.sort(key=lambda o: o['z'], reverse=True) # Member 1: Sort objects by Z so the closest ones are first
    closest_z = upcoming_objs[0]['z'] # Member 1: Get the exact Z position of the closest object
    
    # Get all objects in this immediate wave # Member 1: Logical grouping comment
    wave_objs = [obs for obs in upcoming_objs if abs(obs['z'] - closest_z) < 150] # Member 1: Filter objects to only include the current "wave"
    
    best_score = -9999 # Member 1: Initialize the best AI score to a very low value
    best_state = (0, False, False) # (lane, ducking, inverted) # Member 1: Initialize the best move state tuple
    
    for lane in [-1, 0, 1]: # Member 1: Iterate over all possible lane choices
        for duck in [False, True]: # Member 1: Iterate over all possible ducking choices
            for inverted in [False, True]: # Member 1: Iterate over all possible gravity choices
                pw = 40 # Member 1: Define the width of the simulated bounding box
                ph = 30 if duck else 60 # Member 1: Define the height of the simulated bounding box based on duck state
                
                px = lane * PLAYER_LANE_SPACING # Member 1: Calculate the absolute X position for this simulated lane
                py = CEILING_HEIGHT if inverted else 0 # Member 1: Calculate the absolute Y position for this simulated gravity
                
                py_center = py - (ph/2) if inverted else py + (ph/2) # Member 1: Calculate the center Y point for intersection logic
                
                state_score = 0 # Member 1: Reset the score for this specific simulation
                hit_obstacle = False # Member 1: Reset the collision flag for this specific simulation
                
                for obs in wave_objs: # Member 1: Check collision against every object in the wave
                    ow, oh = obs['w'], obs['h'] # Member 1: Extract the width and height of the current object
                    ox, oy = obs['x'], obs['y'] # Member 1: Extract the X and Y positions of the current object
                    
                    collision_x = abs(px - ox) < (pw + ow) / 2 # Member 1: Boolean check for horizontal (X) intersection
                    collision_y = abs(py_center - oy) < (ph + oh) / 2 # Member 1: Boolean check for vertical (Y) intersection
                    
                    if collision_x and collision_y: # Member 1: If bounding boxes intersect on both axes
                        if obs['type'] == 'obstacle': # Member 1: Check if the hit object is a lethal obstacle
                            hit_obstacle = True # Member 1: Flag that this simulated state leads to death
                            break # Member 1: Stop evaluating other objects, this state is discarded
                        elif obs['type'] == 'powerup': # Member 1: Check if the hit object is a coin/powerup
                            state_score += obs.get('points', 50) # Member 1: Add the coin's value to the state's score
                            
                if hit_obstacle: # Member 1: If the collision loop detected an obstacle hit
                    state_score = -1000 # Member 1: Heavily penalize the score so the AI avoids it
                    
                # Small preference for default states if everything else is equal # Member 1: Logical grouping comment
                if not duck: state_score += 1 # Member 1: Add a tiny score bias to favor standing over ducking
                if not inverted: state_score += 2 # Member 1: Add a tiny score bias to favor the floor over the ceiling
                if lane == 0: state_score += 1 # Member 1: Add a tiny score bias to favor the middle lane over edges
                
                if state_score > best_score: # Member 1: If this simulated state score is higher than our previous best
                    best_score = state_score # Member 1: Update the highest recorded score
                    best_state = (lane, duck, inverted) # Member 1: Save this exact combination of moves as the optimal plan
                    
    target_lane = best_state[0] # Member 1: Execute the best lane choice
    is_ducking = best_state[1] # Member 1: Execute the best ducking choice
    if gravity_inverted != best_state[2]: # Member 1: Only toggle gravity if the current gravity doesn't match the optimal gravity
        toggle_gravity() # Member 1: Execute the best gravity choice