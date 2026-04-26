# Obstacle Runner 423 — Technical Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Zones](#architecture--zones)
3. [Global Variables](#global-variables)
4. [Zone 1: Core Engine & AI Systems](#zone-1-core-engine--ai-systems)
5. [Zone 2: Player Controller & Physics](#zone-2-player-controller--physics)
6. [Zone 3: Level Design & Collisions](#zone-3-level-design--collisions)
7. [Zone 4: Main Loop & Input Handling](#zone-4-main-loop--input-handling)
8. [Controls Reference](#controls-reference)

---

## Project Overview

A 3D endless runner game built in Python using **legacy OpenGL** and **GLUT**. The player runs through a neon-lit tunnel, dodging obstacles and collecting powerups while the game progressively increases in speed.

**Constraints:**
- No shaders, no textures — only basic OpenGL primitives
- Shapes used: `glutSolidCube`, `gluCylinder`, `gluSphere`, `GL_QUADS`, `GL_TRIANGLES`, `GL_LINES`
- Transformations: `glTranslatef`, `glRotatef`, `glScalef`
- Depth testing enabled via `glEnable(GL_DEPTH_TEST)`
- Entire game contained in a single `.py` file

---

## Architecture & Zones

The codebase is organized into 5 zones for team collaboration:

| Zone | Owner | Responsibility |
|------|-------|---------------|
| Zone 0 | Shared | Global variables and constants |
| Zone 1 | Member 1 | Tunnel rendering, day/night cycle, cheat mode AI, game state |
| Zone 2 | Member 2 | Player avatar drawing, physics, animation, gravity inversion |
| Zone 3 | Member 3 | Obstacle spawning, collision detection, powerups, camera warp |
| Zone 4 | Template | GLUT boilerplate: input listeners, main loop, display |

---

## Global Variables

### Window & Display
| Variable | Value | Purpose |
|----------|-------|---------|
| `WINDOW_WIDTH` | 1000 | Window width in pixels |
| `WINDOW_HEIGHT` | 800 | Window height in pixels |

### Tunnel Constants
| Variable | Value | Purpose |
|----------|-------|---------|
| `TUNNEL_WIDTH` | 200 | Half-width of the tunnel on X-axis |
| `TUNNEL_LENGTH` | 1500 | Depth of the tunnel on Z-axis |
| `PILLAR_COUNT` | 10 | Number of pillar pairs |
| `PILLAR_SPACING` | 150 | Z-distance between pillars |
| `SCROLL_SPEED` | 300 | Base tunnel scroll speed (units/sec) |
| `DAY_NIGHT_CYCLE` | 30.0 | Full day/night cycle duration in seconds |

### Player Constants
| Variable | Value | Purpose |
|----------|-------|---------|
| `PLAYER_LANE_SPACING` | 100 | X-distance between lanes (-100, 0, +100) |
| `GRAVITY` | 2000.0 | Gravity acceleration (units/sec²) |
| `JUMP_VELOCITY` | 700.0 | Initial upward velocity when jumping |
| `CEILING_HEIGHT` | 150.0 | Logical ceiling reference height |
| `PLAYER_VISUAL_HEIGHT` | 67 | Visual model height from feet to head top |
| `PLAYER_DUCK_HEIGHT` | 34 | Halved height when ducking |

### Game State
| Variable | Default | Purpose |
|----------|---------|---------|
| `game_speed` | 1.0 | Multiplier that increases over time |
| `SPAWN_INTERVAL` | 1.2 | Seconds between obstacle wave spawns |
| `fovY` | 120 | Field of view (increases with speed) |

---

## Zone 1: Core Engine & AI Systems

### `init_tunnel()`
Initializes pillar Z-offsets as evenly spaced positions along the negative Z-axis.

```
pillar_z_offsets[i] = -i * PILLAR_SPACING
```

For 10 pillars with spacing 150: positions are [0, -150, -300, ..., -1350].

---

### `get_day_night_color(day_color, night_color)`
Returns an RGB tuple that smoothly interpolates between day and night colors based on elapsed time.

**Math formula:**
```
t = (time_survived % DAY_NIGHT_CYCLE) / DAY_NIGHT_CYCLE    # Normalized cycle position [0, 1]
factor = (sin(t × 2π − π/2) + 1) / 2                      # Smooth oscillation [0, 1]
result = day_color × factor + night_color × (1 − factor)    # Linear interpolation
```

The `sin()` wave with `-π/2` phase shift starts at the minimum (night), smoothly rises to maximum (day), and returns. This creates a continuous, smooth transition rather than abrupt color jumps.

---

### `draw_tunnel()`
Renders the game environment:

1. **Floor**: Dark `GL_QUADS` plane at Y=0, spanning the full tunnel width and length
2. **Grid Lines**: `GL_LINES` drawn at Y=0.5 (just above floor) for depth perception:
   - Horizontal lines every 80 units along Z
   - 5 vertical lines evenly across X
3. **Ceiling**: `GL_QUADS` plane at Y = `CEILING_HEIGHT + 50` (= 200)
4. **Pillars**: At each pillar Z-offset, two pillars (left/right walls):
   - **Base**: `glutSolidCube(30)` at Y=15
   - **Column**: `gluCylinder` from Y=30 upward, rotated −90° around X to point up

All colors use `get_day_night_color()` for dynamic day/night tinting.

---

### `update_tunnel(dt)`
Scrolls pillars toward the camera each frame:

```
scroll = SCROLL_SPEED × game_speed × dt
pillar_z_offsets[i] += scroll
```

When a pillar passes Z=200 (behind camera), it wraps to the back:
```
pillar_z_offsets[i] = min(all_offsets) − PILLAR_SPACING
```

This creates the illusion of infinite forward movement.

---

### `reset_game()`
Resets all game state variables to their initial values: score, time, speed, player position, gravity, obstacles, and re-initializes the tunnel.

---

### `update_cheat_mode()`
An AI autopilot that evaluates all possible player states and picks the safest one.

**Algorithm:**
1. Filter obstacles in front of the player (Z between -800 and 100)
2. Sort by Z (closest first) and group into a "wave" (objects within 150 Z-units)
3. Brute-force search over all 12 combinations:
   - 3 lanes × 2 duck states × 2 gravity states
4. For each combination, simulate the AABB collision against all wave objects
5. Score each state: −1000 for hitting an obstacle, +points for collecting powerups
6. Tie-breakers: prefer standing (+1), prefer normal gravity (+2), prefer center lane (+1)
7. Apply the best state: set `target_lane`, `is_ducking`, and toggle gravity if needed

**Collision prediction uses the same AABB formula as `check_collisions()`:**
```
collision_x = |px − ox| < (pw + ow) / 2
collision_y = |py_center − oy| < (ph + oh) / 2
```

---

## Zone 2: Player Controller & Physics

### `draw_player()`
Draws a hierarchical robot avatar using nested `glPushMatrix`/`glPopMatrix` transformations.

**Body hierarchy (all relative to feet position):**

| Part | Y Position | Size | Color |
|------|-----------|------|-------|
| Left/Right Legs | Y=18, extend down 12 | 8×26×8 | Dark blue (0.15, 0.15, 0.4) |
| Body (torso) | Y=38 | 30×32×20 | Blue (0.1, 0.35, 0.7) |
| Accent stripe | Y=38, Z=10.5 | 24×6×1 | Cyan (0.0, 0.8, 1.0) |
| Left/Right Arms | Y=50, extend down 12 | 6×24×6 | Red (0.6, 0.15, 0.15) |
| Head | Y=60 | 14×14×14 | Skin (0.9, 0.8, 0.7) |
| Visor | Y=61, Z=7.5 | 12×4.8×1.2 | Cyan (0.0, 0.9, 1.0) |

**Running animation formula:**
```
swing = sin(player_anim_time × 15 × game_speed) × 45°    (when not jumping)
swing = 0°                                                  (when jumping)
```

Arms and legs use `glRotatef(±swing, 1, 0, 0)` to swing around the X-axis. Left arm/right leg swing together (opposite to right arm/left leg) for natural running motion.

**Gravity inversion:**
```
glScalef(1.0, -1.0, 1.0)    # Mirror the entire model on Y-axis
```
This flips the model so it hangs downward from `player_y` (the ceiling contact point).

**Ducking:**
```
glScalef(1.0, 0.5, 1.0)     # Compress to half height
```

---

### `update_player(dt)`
Updates player position each frame.

**Lane switching (X-axis):**
```
player_x += (target_x − player_x) × 10.0 × dt
```
This is exponential interpolation (lerp). The factor `10.0 × dt` means ~63% of the remaining distance is covered each 0.1s, creating smooth deceleration.

**Jumping physics (Y-axis) — Parabolic trajectory:**

Normal gravity:
```
player_y_vel −= GRAVITY × dt        # Decelerate upward (v = v₀ − g·t)
player_y += player_y_vel × dt        # Update position (y = y + v·dt)
```

Inverted gravity:
```
player_y_vel += GRAVITY × dt         # Accelerate upward toward ceiling
player_y += player_y_vel × dt
```

**Landing detection:**
- Normal: `player_y ≤ 0` → snap to ground, stop jumping
- Inverted: `player_y ≥ ceiling_foot_y` (200) → snap to ceiling, stop jumping

**Resting position:**
- Normal: `player_y = 0` (feet on floor)
- Inverted: `player_y = CEILING_HEIGHT + 50` = 200 (feet on ceiling surface)

---

### `player_jump()`
Initiates a jump by setting `is_jumping = True` and applying initial velocity:
- Normal: `player_y_vel = +700` (upward)
- Inverted: `player_y_vel = −700` (downward, toward floor)

---

### `toggle_gravity()`
Flips the `gravity_inverted` flag, instantly teleports the player to the opposite surface, and resets jump state.

---

## Zone 3: Level Design & Collisions

### `spawn_pattern()`
Generates obstacle waves at the far end of the tunnel (`spawn_z = -TUNNEL_LENGTH + 200 = -1300`).

**Pattern types (chosen randomly with weighted distribution):**

| Pattern | Probability | Description | Player Action |
|---------|------------|-------------|---------------|
| `wall_with_gap` | 1/6 | Two lanes blocked (slab or sphere), one open | Dodge to gap lane |
| `low_spheres` | 1/6 | Three spheres on ground (Y=25, size 50) | Jump over them |
| `ceiling_spheres` | 1/6 | Three spheres at Y=80 (size 50) | Duck to avoid |
| `hanging_slabs` | 1/6 | Three slabs at Y=80 (size 80×80) | Duck to avoid |
| `powerup_only` | 2/6 | Single collectible item | Optional pickup |

**Powerup tier system:**

| Tier | Chance | Points | Shape | Color |
|------|--------|--------|-------|-------|
| 1 (Common) | 50% | 10 | Triangle spike | Neon green |
| 2 (Uncommon) | 30% | 30 | Rectangle | Electric blue |
| 3 (Rare) | 15% | 50 | Square cube | Gold |
| 4 (Ultra Rare) | 5% | 100 | Diamond (octahedron) | Pulsing magenta |

**Bonus coin**: 50% chance to spawn a bonus Tier-1 coin alongside obstacle patterns.

---

### `draw_triangle_spike(size)`
Draws a 3D tetrahedron (pyramid) using `GL_TRIANGLES`:
- **Apex** at `(0, size×0.75, 0)` — pointing upward
- **Base** is a square at `Y = -size/2` with corners at `(±size/2, -size/2, ±size/2)`
- 4 triangular side faces + 1 quad bottom face

---

### `draw_diamond(size)`
Draws a 3D octahedron using `GL_TRIANGLES`:
- **Top vertex** at `(0, size×0.75, 0)`
- **Bottom vertex** at `(0, -size×0.75, 0)`
- **4 equatorial vertices** at `(±size/2, 0, 0)` and `(0, 0, ±size/2)`
- 4 upper triangles + 4 lower triangles = 8 faces total

---

### `draw_obstacles()`
Renders all active obstacles with visual effects:

1. **Proximity pulsing**: When Z-distance < 600:
   ```
   scale_pulse = 1.0 + 0.15 × sin(time × 8)
   ```
   Oscillates between 0.85× and 1.15× scale.

2. **Powerup spinning**: Rotates around Y-axis:
   ```
   spin = (time × 120) mod 360°
   ```
   Completes one full rotation every 3 seconds.

3. **Obstacle glow**: Neon red with pulsing brightness:
   ```
   pulse = 0.7 + 0.3 × |sin(time × 5)|
   ```

4. **Tier 4 glow**: Magenta pulsing at a different frequency:
   ```
   glow = 0.7 + 0.3 × |sin(time × 6)|
   ```

---

### `check_collisions()`
Implements 3D Axis-Aligned Bounding Box (AABB) collision detection.

**Player bounding box dimensions:**
| Dimension | Standing | Ducking |
|-----------|----------|---------|
| Width (X) | 30 | 30 |
| Height (Y) | 67 | 34 |
| Depth (Z) | 20 | 20 |

**AABB center calculation:**
```
Normal:   py_center = player_y + height/2     (extends upward from feet)
Inverted: py_center = player_y − height/2     (extends downward from feet)
```

**Collision formula (per axis):**
```
collision_x = |px − ox| < (pw + ow) / 2
collision_y = |py − oy| < (ph + oh) / 2
collision_z = |pz − oz| < (pd + od) / 2
```

This checks if the sum of half-widths exceeds the distance between centers on each axis. A collision occurs when **all three axes** overlap simultaneously.

**Collision outcomes:**
- `obstacle` → `game_over = True`
- `powerup` → deactivate powerup, add points to score

**Collision proof for hanging obstacles (Y=80, size 50):**

| Player State | AABB Center Y | Check: \|center − 80\| < (height + 50)/2 | Result |
|-------------|--------------|----------------------------------------|--------|
| Standing (h=67) | 33.5 | 46.5 < 58.5 | **COLLIDES** ✅ |
| Ducking (h=34) | 17.0 | 63.0 < 42.0 | **MISSES** ✅ |

---

### `update_obstacles(dt)`
Each frame:
1. Scroll all obstacles toward camera: `obs['z'] += SCROLL_SPEED × game_speed × dt`
2. Award +1 score for each obstacle that passes behind camera (Z > 200)
3. Remove objects that are far behind camera (Z > 500)
4. Decrement spawn timer; spawn new wave when timer expires

---

### `update_warp_fov()`
Gradually widens the field of view as game speed increases:
```
target_fov = 120 + (game_speed − 1.0) × 10.0
target_fov = clamp(target_fov, 120, 160)
fovY += (target_fov − fovY) × 0.05           # Smooth interpolation (5% per frame)
```

This creates a "warp speed" tunnel vision effect at high speeds.

---

### `setupCamera()`
Configures the 3D perspective projection:
```
gluPerspective(fovY, WINDOW_WIDTH/WINDOW_HEIGHT, 0.1, 2000)
gluLookAt(0, 75, 200,    # Camera position (behind and above player)
          0, 50, -500,    # Look-at target (far down the tunnel)
          0, 1, 0)        # Up vector (Y-axis)
```

---

## Zone 4: Main Loop & Input Handling

### `draw_text(x, y, text)` / `draw_text_colored(x, y, text, r, g, b)`
Renders bitmap text at screen coordinates using orthographic projection overlay:
1. Save projection matrix
2. Switch to 2D orthographic projection matching window size
3. Render text character-by-character using `glutBitmapCharacter`
4. Restore perspective projection

---

### `idle()`
Called every frame by GLUT. Computes delta time and updates all game systems in order:

```
dt = current_time − last_frame_time     (capped at 0.1s to prevent physics explosions)
game_speed = 1.0 + time_survived × 0.02  (increases 2% per second)
```

**Update order:**
1. `update_tunnel(dt)` — scroll environment
2. `update_warp_fov()` — adjust FOV
3. `update_cheat_mode()` — AI decisions
4. `update_player(dt)` — physics & animation
5. `update_obstacles(dt)` — move & spawn obstacles
6. `check_collisions()` — detect hits

---

### `showScreen()`
Main render function called each frame:
1. Clear color/depth buffers with day/night tinted background
2. Set up 3D camera
3. Draw tunnel → obstacles → player (back-to-front)
4. Overlay HUD text (score, time, speed, cheat mode indicator)
5. Show game over / paused screen if applicable
6. Swap buffers (double buffering)

---

## Controls Reference

| Key | Action |
|-----|--------|
| `A` | Move left one lane |
| `D` | Move right one lane |
| `W` / `Space` | Jump |
| `S` (hold) | Duck |
| `G` | Toggle gravity (floor ↔ ceiling) |
| `P` | Pause / Unpause |
| `R` | Restart game |
| `C` | Toggle cheat mode (AI autopilot) |
