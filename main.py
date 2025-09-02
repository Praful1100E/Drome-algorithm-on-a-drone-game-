import pygame
import sys
import random

pygame.init()

# ---------------- Settings ----------------
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Smart Autonomous Drone")

# Colors
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)
DARK_BG = (13, 17, 23)

# Fonts
FONT = pygame.font.SysFont("consolas", 24)

# Drone
DRONE_SIZE = 40
drone = pygame.Rect(100, HEIGHT // 2 - DRONE_SIZE // 2, DRONE_SIZE, DRONE_SIZE)
DRONE_SPEED = 5       # Max speed drone can move per frame

# Obstacles
OBSTACLE_WIDTH = 50
OBSTACLE_HEIGHT = 50
obstacle_list = []
OBSTACLE_SPEED = 5
SPAWN_INTERVAL = 1200  # milliseconds

# Game state
score = 0
level = 1
clock = pygame.time.Clock()
game_over = False

# Timer for spawning obstacles
SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL)

# ---------------- Functions ----------------

def spawn_obstacle():
    """Spawn a new obstacle on the right side"""
    y = random.randint(0, HEIGHT - OBSTACLE_HEIGHT)
    rect = pygame.Rect(WIDTH, y, OBSTACLE_WIDTH, OBSTACLE_HEIGHT)
    obstacle_list.append(rect)

def find_safe_y():
    """Find the safest vertical position to avoid all upcoming obstacles"""
    safe_zones = [(0, HEIGHT)]  # List of free vertical ranges (start, end)

    # Consider only obstacles ahead of the drone
    for obs in obstacle_list:
        if obs.x + OBSTACLE_WIDTH >= drone.x:
            new_safe_zones = []
            for start, end in safe_zones:
                # If obstacle overlaps the safe zone, split the zone
                if obs.top > start and obs.bottom < end:
                    new_safe_zones.append((start, obs.top))
                    new_safe_zones.append((obs.bottom, end))
                elif obs.top <= start < obs.bottom < end:
                    new_safe_zones.append((obs.bottom, end))
                elif start < obs.top < end <= obs.bottom:
                    new_safe_zones.append((start, obs.top))
                elif obs.bottom <= start or obs.top >= end:
                    new_safe_zones.append((start, end))
                # else fully covered → discard zone
            safe_zones = new_safe_zones

    # Choose the zone closest to current drone position
    best_zone = None
    min_dist = HEIGHT
    for start, end in safe_zones:
        center = (start + end) / 2
        dist = abs(center - drone.centery)
        if dist < min_dist:
            min_dist = dist
            best_zone = (start, end)

    # Return center of best zone as target y
    if best_zone:
        return (best_zone[0] + best_zone[1]) / 2 - DRONE_SIZE / 2
    else:
        # No safe zone (rare) → stay in current y
        return drone.y

def auto_dodge_smooth():
    """Smooth auto-dodging AI using optimal path"""
    target_y = find_safe_y()
    # Move smoothly towards target
    if abs(target_y - drone.y) < DRONE_SPEED:
        drone.y = target_y
    elif target_y > drone.y:
        drone.y += DRONE_SPEED
    elif target_y < drone.y:
        drone.y -= DRONE_SPEED

    # Keep drone inside screen
    drone.y = max(0, min(HEIGHT - DRONE_SIZE, drone.y))

def draw_window():
    WIN.fill(DARK_BG)
    pygame.draw.rect(WIN, CYAN, drone)
    for obs in obstacle_list:
        pygame.draw.rect(WIN, WHITE, obs)

    # UI overlay
    score_text = FONT.render(f"Score: {score}", True, CYAN)
    level_text = FONT.render(f"Level: {level}", True, CYAN)
    WIN.blit(score_text, (10, 10))
    WIN.blit(level_text, (WIDTH - 120, 10))

    if game_over:
        msg = FONT.render("Game Over! Press R to restart", True, WHITE)
        WIN.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))

    pygame.display.update()

def reset_game():
    global drone, obstacle_list, score, level, OBSTACLE_SPEED, SPAWN_INTERVAL, game_over
    drone.x = 100
    drone.y = HEIGHT // 2 - DRONE_SIZE // 2
    obstacle_list.clear()
    score = 0
    level = 1
    OBSTACLE_SPEED = 5
    SPAWN_INTERVAL = 1200
    pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL)
    game_over = False

# ---------------- Main Loop ----------------

running = True
while running:
    clock.tick(30)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == SPAWN_EVENT and not game_over:
            spawn_obstacle()
        if event.type == pygame.KEYDOWN and game_over:
            if event.key == pygame.K_r:
                reset_game()

    if not game_over:
        auto_dodge_smooth()  # Fully autonomous

        # Move obstacles left
        for obs in obstacle_list:
            obs.x -= OBSTACLE_SPEED

        # Remove off-screen obstacles
        obstacle_list = [obs for obs in obstacle_list if obs.right > 0]

        # Collision detection
        if any(drone.colliderect(obs) for obs in obstacle_list):
            game_over = True

        # Increase score
        score += 1

        # Level up every 1000 points
        if score % 1000 == 0:
            level += 1
            OBSTACLE_SPEED += 1
            SPAWN_INTERVAL = max(500, SPAWN_INTERVAL - 100)
            pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL)

    draw_window()

pygame.quit()
sys.exit()
