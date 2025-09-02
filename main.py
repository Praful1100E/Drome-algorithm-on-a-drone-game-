import pygame
import sys
import random
import os

pygame.init()

# ---------------- Settings ----------------
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Autonomous Drone - Single Image")

# Colors
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)
DARK_BG = (13, 17, 23)

# Fonts
FONT = pygame.font.SysFont("consolas", 24)

# Drone settings
DRONE_SIZE = 50
DRONE_SPEED = 5  # smooth movement

# Load drone image (your single drone image)
DRONE_IMAGE = pygame.image.load("C:/Users/rajpu/OneDrive/Desktop/drone navigation with ai/5th/drone.png")
DRONE_IMAGE = pygame.transform.scale(DRONE_IMAGE, (DRONE_SIZE, DRONE_SIZE))
drone = pygame.Rect(100, HEIGHT // 2 - DRONE_SIZE // 2, DRONE_SIZE, DRONE_SIZE)

# Obstacle settings
OBSTACLE_WIDTH = 50
OBSTACLE_HEIGHT = 50
OBSTACLE_SPEED = 5
obstacle_list = []

# Load obstacle image (single obstacle image)
OBSTACLE_IMAGE = pygame.image.load("C:/Users/rajpu/OneDrive/Desktop/drone navigation with ai/5th/obstraction.png")
OBSTACLE_IMAGE = pygame.transform.scale(OBSTACLE_IMAGE, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT))

SPAWN_INTERVAL = 1200  # ms
SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL)

# Game state
score = 0
level = 1
clock = pygame.time.Clock()
game_over = False

# ---------------- Functions ----------------

def spawn_obstacle():
    """Spawn obstacle at random vertical position"""
    y = random.randint(0, HEIGHT - OBSTACLE_HEIGHT)
    rect = pygame.Rect(WIDTH, y, OBSTACLE_WIDTH, OBSTACLE_HEIGHT)
    obstacle_list.append(rect)

def find_safe_y():
    """Find optimal vertical position to dodge obstacles"""
    safe_zones = [(0, HEIGHT)]
    for rect in obstacle_list:
        if rect.x + OBSTACLE_WIDTH >= drone.x:
            new_safe_zones = []
            for start, end in safe_zones:
                if rect.top > start and rect.bottom < end:
                    new_safe_zones.append((start, rect.top))
                    new_safe_zones.append((rect.bottom, end))
                elif rect.top <= start < rect.bottom < end:
                    new_safe_zones.append((rect.bottom, end))
                elif start < rect.top < end <= rect.bottom:
                    new_safe_zones.append((start, rect.top))
                elif rect.bottom <= start or rect.top >= end:
                    new_safe_zones.append((start, end))
            safe_zones = new_safe_zones
    best_zone = None
    min_dist = HEIGHT
    for start, end in safe_zones:
        center = (start + end) / 2
        dist = abs(center - drone.centery)
        if dist < min_dist:
            min_dist = dist
            best_zone = (start, end)
    if best_zone:
        return (best_zone[0] + best_zone[1]) / 2 - DRONE_SIZE / 2
    else:
        return drone.y

def auto_dodge_smooth():
    """Smooth auto-dodging AI"""
    target_y = find_safe_y()
    if abs(target_y - drone.y) < DRONE_SPEED:
        drone.y = target_y
    elif target_y > drone.y:
        drone.y += DRONE_SPEED
    elif target_y < drone.y:
        drone.y -= DRONE_SPEED
    drone.y = max(0, min(HEIGHT - DRONE_SIZE, drone.y))

def draw_window():
    WIN.fill(DARK_BG)
    # Draw drone
    WIN.blit(DRONE_IMAGE, (drone.x, drone.y))
    # Draw obstacles
    for rect in obstacle_list:
        WIN.blit(OBSTACLE_IMAGE, rect)
    # UI
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
        auto_dodge_smooth()
        # Move obstacles
        new_list = []
        for rect in obstacle_list:
            rect.x -= OBSTACLE_SPEED
            if rect.right > 0:
                new_list.append(rect)
        obstacle_list = new_list
        # Collision detection
        if any(drone.colliderect(rect) for rect in obstacle_list):
            game_over = True
        # Score
        score += 1
        if score % 1000 == 0:
            level += 1
            OBSTACLE_SPEED += 1
            SPAWN_INTERVAL = max(500, SPAWN_INTERVAL - 100)
            pygame.time.set_timer(SPAWN_EVENT, SPAWN_INTERVAL)

    draw_window()

pygame.quit()
sys.exit()
