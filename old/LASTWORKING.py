import pygame
import math
import time
import random
import json

# Initialize pygame
pygame.init()

# Set up display
WIDTH = 800
HEIGHT = 600
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
can_start_next_level = True
level = 1
next_level_state = False
level_timer = 0
SPAWN_DELAY = 2  # Seconds between each enemy spawn
spawn_timer = 0
max_enemies = 0
enemies_spawned = 0  # Track how many enemies have been spawned

# Load level configuration from a JSON file
def load_level_config(filename='level_config.json'):
    with open(filename, 'r') as file:
        return json.load(file)

# Use this function to get the number of enemies for the current level
def get_number_of_enemies_for_level(level, config):
    enemies = config.get(str(level), 0)  # Default to 0 if level not found in config
    print(f"Enemies for level {level}: {enemies}")  # Debugging line
    return enemies

# Initialize level configuration
level_config = load_level_config()

class Bullet:
    def __init__(self, x, y, target, speed=20):
        self.x = x
        self.y = y
        self.target = target
        self.speed = speed
        self.color = BLACK
        self.radius = 5
        self.hit = False  # Track if the bullet has hit its target

        # Calculate direction towards the target
        direction = math.atan2(target.y - y, target.x - x)
        self.dx = math.cos(direction) * self.speed
        self.dy = math.sin(direction) * self.speed

    def move(self):
        if not self.hit:  # Only move if it hasn't hit the target
            self.x += self.dx
            self.y += self.dy

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def has_hit_target(self):
        return math.sqrt((self.target.x - self.x) ** 2 + (self.target.y - self.y) ** 2) < self.target.speed + 10

    def update(self):
        global money  # Declare money as global to modify it
        if self.has_hit_target() and not self.hit:  # Check if the bullet has hit and hasn't already been marked
            self.hit = True  # Mark the bullet as having hit
            if self.target in enemies:  # Check if the target is still in the list
                self.target.health -= 1
                print(f"Enemy hit! Health left: {self.target.health}")

                if self.target.health <= 0:
                    print(f"Enemy at ({self.target.x}, {self.target.y}) defeated")
                    money += self.target.reward  # Add money when enemy is defeated
                    return True  # Indicate the bullet hit the target
        return False  # Indicate the bullet did not hit the target


class Tower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.range = 100
        self.cost = 175
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

    def update(self, enemies):
        global money  # Declare money as global to modify it
        if self.cooldown > 0:
            self.cooldown -= 1

        for bullet in self.bullets[:]:  # Iterate over a copy to safely remove bullets
            bullet.move()
            if bullet.update():  # Check if the bullet hit the target
                # Ensure the target is removed safely
                if bullet.target in enemies:
                    enemies.remove(bullet.target)  # Remove the enemy from the enemies list
                self.bullets.remove(bullet)  # Remove the bullet after it hits the target
            elif bullet.hit:  # If the bullet has hit but not destroyed the enemy, still remove it
                self.bullets.remove(bullet)  # Remove the bullet from the list


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
        self.reward = 5

    def move(self):
        if self.current_path_index < len(self.path) - 1:
            target_x, target_y = self.path[self.current_path_index + 1]
            direction = math.atan2(target_y - self.y, target_x - self.x)
            self.x += self.speed * math.cos(direction)
            self.y += self.speed * math.sin(direction)
            if math.sqrt((target_x - self.x) ** 2 + (target_y - self.y) ** 2) < self.speed:
                self.current_path_index += 1
        else:
            global lives
            lives -= 1  # Reduce lives when an enemy reaches the end
            enemies.remove(self)  # Remove the enemy from the enemies list

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

# New function to display enemies remaining and money
def draw_enemy_counter_and_money(screen, enemies_remaining, money):
    # Display enemies remaining (count down)
    counter_text = font.render(f"Enemies left: {enemies_remaining}", True, BLACK)
    screen.blit(counter_text, (WIDTH - 220, 10))  # Adjusted x-coordinate

    # Display money below the enemies remaining
    money_text = font.render(f"Money: {money}", True, BLACK)
    screen.blit(money_text, (WIDTH - 220, 50))  # Adjusted x-coordinate

    # Display lives below the money
    lives_text = font.render(f"Lives: {lives}", True, RED)
    screen.blit(lives_text, (WIDTH - 220, 90))  # Adjusted x-coordinate

def draw_level(screen, level):
    level_text = font.render(f"Level: {level}", True, BLACK)
    screen.blit(level_text, (10, 10))

def start_next_level(start_level=False):
    global level, enemies, level_timer, next_level_state, max_enemies, spawn_timer, enemies_spawned, can_start_next_level
    if start_level:  # Check if starting the game
        level = 1  # Start at level 1
    else:
        level += 1  # Increment the level for subsequent levels

    # Get the number of enemies for the current level from the config
    max_enemies = get_number_of_enemies_for_level(level, level_config)

    enemies = []  # Reset enemies list for the new level
    enemies_spawned = 0  # Reset the enemy spawn count
    level_timer = time.time()
    spawn_timer = time.time()  # Reset spawn timer
    next_level_state = False
    can_start_next_level = False  # Reset the flag for the next level

    # Print the number of enemies for the current level to the terminal
    print(f"Level {level} started with {max_enemies} enemies")


def spawn_enemy():
    global spawn_timer, enemies_spawned, money
    current_time = time.time()
    
    if enemies_spawned < max_enemies and current_time - spawn_timer >= SPAWN_DELAY:
        offset = random.randint(-20, 20)
        speed = 1 + level * 0.2
        enemies.append(Enemy(path, offset, speed))
        enemies_spawned += 1  # Track the spawned enemies
        spawn_timer = current_time
        print(f"Enemy spawned! Total spawned: {enemies_spawned} (Level: {level})")  # Debug statement


# Define the path for enemies
path = [(50, 50), (200, 50), (200, 200), (400, 200), (400, 400), (600, 400), (600, 550)]

# Game loop
towers = []
enemies = []
money = 325
lives = 25
# Define the tower button rectangle
tower_button_rect = pygame.Rect(10, HEIGHT - 60, 150, 50)  

running = True
placing_tower = False  # Flag to indicate if the player is in tower placement mode
current_tower_position = None  # To track the current position of the tower being placed

# Change initial level to 0
level = 0  # Start from level 0
next_level_state = False  # Maintain the existing variable

# Define the start button rectangle
start_button_rect = pygame.Rect(WIDTH - 220, HEIGHT - 60, 200, 50)  

# Define a variable to track whether the game has started
game_started = False

# Update the draw_start_button function
def draw_start_button(screen):
    button_color = GREEN if can_start_next_level else RED  # Change button color based on state
    pygame.draw.rect(screen, button_color, start_button_rect)
    text_surface = font.render("Start", True, WHITE)
    screen.blit(text_surface, (WIDTH - 210, HEIGHT - 50))


while running:
    # Fill the screen with white
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Handle mouse button click for starting the game or next level
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            # Start the game or next level when the button is clicked
            if start_button_rect.collidepoint(mouse_x, mouse_y):
                if not game_started:
                    game_started = True  # Set the game to started
                    start_next_level(True)  # Call start_next_level with True to initialize level 1
                elif can_start_next_level:  # Allow starting next level if conditions are met
                    start_next_level()  # Call without arguments to proceed to the next level

            if tower_button_rect.collidepoint(mouse_x, mouse_y) and game_started:
                # Check if there is enough money to place a tower
                if money >= 175:
                    placing_tower = True  # Set flag to indicate tower placement mode
                    money -= 175  # Deduct the cost of the tower immediately

            elif placing_tower:
                # Place the tower where the mouse is clicked
                towers.append(Tower(mouse_x, mouse_y))  # Use current mouse click for placement
                placing_tower = False  # Reset the flag after placing the tower

    # Draw start button
    draw_start_button(screen)

    if game_started:
        # Draw path
        draw_path(screen, path)

        # Draw towers and update bullets
        for tower in towers:
            tower.draw(screen)
            tower.shoot(enemies)
            tower.update(enemies)
            tower.draw_bullets(screen)

        # Spawn enemies and move them
        spawn_enemy()
        for enemy in enemies:
            enemy.move()  # Move each enemy
            if enemy.health <= 0:  # Check if the enemy is defeated
                money += enemy.reward  # Add money for defeating the enemy
                enemies.remove(enemy)  # Remove the enemy from the enemies list
            enemy.draw(screen)  # Draw each enemy

        # Draw enemy count, money, and lives
        draw_enemy_counter_and_money(screen, max_enemies - enemies_spawned, money)
        draw_level(screen, level)

        # Draw the tower button with color based on money available
        if money >= 175:
            pygame.draw.rect(screen, GREEN, tower_button_rect)
        else:
            pygame.draw.rect(screen, RED, tower_button_rect)

        # Draw the tower button text
        button_text = font.render("Tower (175)", True, WHITE)
        screen.blit(button_text, (tower_button_rect.x + 10, tower_button_rect.y + 10))
    
    # If placing a tower, show it at the current mouse position
    if placing_tower:
        # Get the current mouse position to display the tower being moved
        current_mouse_x, current_mouse_y = pygame.mouse.get_pos()  # Track current mouse position
        
        # Check if the tower is too close to the path
        if is_near_path(current_mouse_x, current_mouse_y, path, radius=25):  # Adjust radius as needed
            tower_color = RED  # Too close to the path
        else:
            tower_color = GREEN  # Far enough away to place the tower
        
        # Draw the tower with the appropriate color
        pygame.draw.circle(screen, tower_color, (current_mouse_x, current_mouse_y), 20)  # Draw the tower

        # Draw the range indicator
        pygame.draw.circle(screen, RED, (current_mouse_x, current_mouse_y), 100, 1)  # Draw range circle (radius is 100)

    # Check for level progression
    if len(enemies) == 0 and enemies_spawned >= max_enemies and game_started:
        can_start_next_level = True  # Set the flag to allow starting the next level

    # Update the display
    pygame.display.flip()
    clock.tick(120)

# Quit pygame
pygame.quit()

