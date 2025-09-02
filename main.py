import pygame
import sys
import os
import random

pygame.init()

# Window setup
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Autonomous Drone Navigation (Virtual)")

# Colors
CYAN = (0, 255, 255)
DARK = (30, 30, 40)
WHITE = (255, 255, 255)

# Drone setup
DRONE_SIZE = 40
drone = pygame.Rect(50, HEIGHT // 2, DRONE_SIZE, DRONE_SIZE)
DRONE_SPEED = 3

# Obstacles
obstacles = []
for _ in range(6):  
    x = random.randint(200, WIDTH - 100)
    y = random.randint(50, HEIGHT - 100)
    obstacles.append(pygame.Rect(x, y, 50, 50))

clock = pygame.time.Clock()

def draw_window():
    WIN.fill(DARK)
    pygame.draw.rect(WIN, CYAN, drone)  # Drone
    for obs in obstacles:
        pygame.draw.rect(WIN, WHITE, obs)  # Obstacles
    pygame.display.update()

def check_collision(rect):
    for obs in obstacles:
        if rect.colliderect(obs):
            return True
    return False

def auto_move():
    global drone

    # Predict next forward move
    future = drone.move(DRONE_SPEED, 0)
    
    if not check_collision(future):
        drone = future  # Move forward if safe
    else:
        # Try moving UP
        future_up = drone.move(0, -DRONE_SPEED*2)
        if not check_collision(future_up) and future_up.top > 0:
            drone = future_up
        else:
            # Try moving DOWN
            future_down = drone.move(0, DRONE_SPEED*2)
            if not check_collision(future_down) and future_down.bottom < HEIGHT:
                drone = future_down

def main():
    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        auto_move()
        draw_window()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
