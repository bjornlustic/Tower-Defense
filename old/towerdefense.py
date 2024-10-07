import pygame
import math
import time
import random
import json

# Initialize pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense")

# Define colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)

# Clock to control frame rate
clock = pygame.time.Clock()

# Font for displaying the level and button
pygame.font.init()
font = pygame.font.SysFont('Arial', 30)

# Variables for managing level progression and spawn rates
level = 1
next_level_state = False
level_timer = 0
LEVEL_WAIT_TIME = 10  # Wait 10 seconds before the next level
SPAWN_DELAY = 2  # Seconds between each enemy spawn
spawn_timer = 0
max_enemies = 0

# Load level configuration from a JSON file
def load_level_config(filename='level_config.json'):
    with open(filename, 'r') as file:
        return json.load(file)

# Use this function to get the number of enemies for the current level
def get_number_of_enemies_for_level(level, config):
    return config.get(str(level), 0)  # Default to 0 if level not found in config

# Initialize level configuration
level_config = load_level_config()

# Define game objects
class Bullet:
    def __init__(self, x, y, target, speed=20):
        self.x = x
        self.y = y
        self.target = target
        self.speed = speed
        self.color = BLACK
        self.radius = 5

        # Calculate direction towards the target
        direction = math.atan2(target.y - y, target.x - x)
        self.dx = math.cos(direction) * self.speed
        self.dy = math.sin(direction) * self.speed

    def move(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def has_hit_target(self):
        return math.sqrt((self.target.x - self.x) ** 2 + (self.target.y - self.y) ** 2) < self.target.speed + 10


class Tower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.range = 100
        self.color = BLUE
        self.cooldown = 0
        self.bullets = []

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), 20)
        pygame.draw.circle(screen, RED, (self.x, self.y), self.range, 1)

    def shoot(self, enemies):
        if self.cooldown == 0:
            for enemy in enemies:
                distance = math.sqrt((enemy.x - self.x) ** 2 + (enemy.y - self.y) ** 2)
                if distance < self.range:
                    self.bullets.append(Bullet(self.x, self.y, enemy))
                    self.cooldown = 30
                    break

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

        for bullet in self.bullets:
            bullet.move()
            if bullet.has_hit_target():
                bullet.target.health -= 1
                if bullet.target.health <= 0:
                    print(f"Enemy at ({bullet.target.x}, {bullet.target.y}) defeated")
                self.bullets.remove(bullet)

    def draw_bullets(self, screen):
        for bullet in self.bullets:
            bullet.draw(screen)


class Enemy:
    def __init__(self, path, offset=0, speed=1):
        self.path = path
        start_x, start_y = path[0]
        self.x = start_x + offset
        self.y = start_y + offset
        self.current_path_index = 0
        self.speed = speed
        self.health = 5
        self.max_health = self.health
        self.color = GREEN

    def move(self):
        if self.current_path_index < len(self.path) - 1:
            target_x, target_y = self.path[self.current_path_index + 1]
            direction = math.atan2(target_y - self.y, target_x - self.x)
            self.x += self.speed * math.cos(direction)
            self.y += self.speed * math.sin(direction)
            if math.sqrt((target_x - self.x) ** 2 + (target_y - self.y) ** 2) < self.speed:
                self.current_path_index += 1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 10)
        self.draw_health_bar(screen)

    def draw_health_bar(self, screen):
        health_bar_width = 40
        health_ratio = self.health / self.max_health
        health_bar_color = RED if health_ratio < 0.5 else GREEN

        pygame.draw.rect(screen, BLACK, (self.x - health_bar_width // 2, self.y - 20, health_bar_width, 5))
        pygame.draw.rect(screen, health_bar_color, (self.x - health_bar_width // 2, self.y - 20, health_bar_width * health_ratio, 5))


def draw_path(screen, path):
    for i in range(len(path) - 1):
        pygame.draw.line(screen, BLACK, path[i], path[i + 1], 5)


def is_near_path(x, y, path, radius=50):
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        distance = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
        if distance < radius:
            return True
    return False


def draw_level(screen, level):
    level_text = font.render(f"Level: {level}", True, BLACK)
    screen.blit(level_text, (10, 10))


def draw_enemy_counter(screen, count):
    counter_text = font.render(f"Enemies: {count}", True, BLACK)
    screen.blit(counter_text, (WIDTH - 150, 10))


def draw_next_level_button(screen):
    button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 25, 200, 50)
    pygame.draw.rect(screen, BLUE, button_rect)
    text_surface = font.render("Next Level", True, WHITE)
    screen.blit(text_surface, (WIDTH // 2 - 75, HEIGHT // 2 - 15))
    return button_rect

def start_next_level():
    global level, enemies, level_timer, next_level_state, max_enemies, spawn_timer
    level += 1
    max_enemies = get_number_of_enemies_for_level(level, level_config)
    enemies = []
    level_timer = time.time()
    spawn_timer = time.time()  # Reset spawn timer
    next_level_state = False

    # Print the number of enemies for the current level to the terminal
    print(f"Level {level} started with {max_enemies} enemies")

def spawn_enemy():
    global spawn_timer, max_enemies
    current_time = time.time()
    
    if len(enemies) < max_enemies and current_time - spawn_timer >= SPAWN_DELAY:
        offset = random.randint(-20, 20)
        speed = 1 + level * 0.2
        enemies.append(Enemy(path, offset, speed))
        spawn_timer = current_time

# Define the path for enemies
path = [(50, 50), (200, 50), (200, 200), (400, 200), (400, 400), (600, 400), (600, 550)]

# Game loop
towers = []
enemies = []
running = True
placing_tower = False
valid_tower_location = False

while running:
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if next_level_state:
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if next_level_button.collidepoint(mouse_pos):
                    start_next_level()

        if not next_level_state:
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                if placing_tower:
                    if valid_tower_location:
                        towers.append(Tower(x, y))
                        placing_tower = False
                else:
                    placing_tower = True

    if not next_level_state:
        spawn_enemy()

        for tower in towers:
            tower.shoot(enemies)
            tower.update()

        for enemy in enemies:
            enemy.move()

        draw_path(screen, path)

        for tower in towers:
            tower.draw(screen)
            tower.draw_bullets(screen)

        for enemy in enemies:
            enemy.draw(screen)

        draw_level(screen, level)
        draw_enemy_counter(screen, len(enemies))

        enemies = [enemy for enemy in enemies if enemy.health > 0 and enemy.current_path_index < len(path) - 1]

        if len(enemies) == 0 and len(enemies) < max_enemies:
            next_level_state = True
            level_timer = time.time()

    if next_level_state:
        if time.time() - level_timer > LEVEL_WAIT_TIME:
            start_next_level()
        else:
            next_level_button = draw_next_level_button(screen)

    if placing_tower:
        x, y = pygame.mouse.get_pos()
        valid_tower_location = not is_near_path(x, y, path) and all(
            math.sqrt((x - tower.x) ** 2 + (y - tower.y) ** 2) > 40 for tower in towers)
        tower_color = GREEN if valid_tower_location else RED
        pygame.draw.circle(screen, tower_color, (x, y), 20)
        pygame.draw.circle(screen, RED, (x, y), 100, 1)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
