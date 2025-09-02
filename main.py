import pygame
import sys
import random

pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Autonomous Drone Dodge AI")

# Colors
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)
DARK_BG = (13, 17, 23)

# Fonts
FONT = pygame.font.SysFont("consolas", 24)

# Drone settings
DRONE_SIZE = 40
drone = pygame.Rect(100, HEIGHT // 2 - DRONE_SIZE // 2, DRONE_SIZE, DRONE_SIZE)
DRONE_SPEED = 5            # Not used, optional for manual
DRONE_DODGE_SPEED = 10     # Increased speed for auto-dodge

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
    y = random.randint(0, HEIGHT - OBSTACLE_HEIGHT)
    rect = pygame.Rect(WIDTH, y, OBSTACLE_WIDTH, OBSTACLE_HEIGHT)
    obstacle_list.append(rect)

def auto_dodge():
    """AI for avoiding obstacles with faster movement"""
    global drone
    # Find nearest obstacle ahead
    nearest = None
    nearest_dist = WIDTH
    for obs in obstacle_list:
        if obs.x + OBSTACLE_WIDTH >= drone.x:
            dist = obs.x - drone.x
            if dist < nearest_dist:
                nearest = obs
                nearest_dist = dist

    if nearest:
        # Predict if collision in next frames
        if drone.colliderect(nearest) or (drone.top < nearest.bottom and drone.bottom > nearest.top and nearest.x - drone.x < 150):
            # Prefer moving up if possible
            if drone.top - DRONE_DODGE_SPEED >= 0:
                drone.y -= DRONE_DODGE_SPEED
            # Else move down
            elif drone.bottom + DRONE_DODGE_SPEED <= HEIGHT:
                drone.y += DRONE_DODGE_SPEED

    # Ensure drone stays inside screen
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
        auto_dodge()  # Only AI, no manual control

        # Move obstacles left
        for obs in obstacle_list:
            obs.x -= OBSTACLE_SPEED

        # Remove off-screen obstacles
        obstacle_list = [obs for obs in obstacle_list if obs.right > 0]

        # Collision detection
        if any(drone.colliderect(obs) for obs in obstacle_list):
            game_over = True

        # Score increases with time
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
