import pygame
import math
import time
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
level_timer = 0
SPAWN_DELAY = 0.5  # Seconds between each enemy spawn
spawn_timer = 0
max_enemies = 0
enemies_spawned = 0  # Track how many enemies have been spawned
green_enemies = 0
purple_enemies = 0
blue_enemies = 0
red_enemies = 0
total_enemies = 0
fps = 60

# Load level configuration from a JSON file
def load_level_config(filename='level_config.json'):
    with open(filename, 'r') as file:
        return json.load(file)

# Use this function to get the number of enemies for the current level
def get_number_of_enemies_for_level(level, config):
    # Default to an empty dictionary if the level is not found
    level_config = config.get(str(level), {"green": 0, "purple": 0, "blue": 0, "red": 0, "black": 0})

    # Return the number of green and purple enemies for the level
    green_enemies = level_config.get("green", 0)
    purple_enemies = level_config.get("purple", 0)
    blue_enemies = level_config.get("blue", 0)
    red_enemies = level_config.get("red", 0)
    black_enemies = level_config.get("black", 0)

    return {"green": green_enemies, "purple": purple_enemies, "blue": blue_enemies, "red": red_enemies, "black": black_enemies}

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
                    # Instead of transforming, remove the target and spawn a new green enemy
                    if isinstance(self.target, PurpleEnemy):
                        money += self.target.reward
                        new_enemy = Enemy(path, offset=0)
                        new_enemy.update_position(self.target.x, self.target.y, self.target.current_path_index, self.target.current_progress)
                        # Create a new green enemy at the same position
                        enemies.append(new_enemy)  # Adjust spawn if needed based on position
                        enemies.remove(self.target)  # Remove the purple enemy
                        print("Purple enemy defeated and a green enemy spawned!")              
                    elif isinstance(self.target, BlueEnemy):
                        money += self.target.reward
                        new_enemy = PurpleEnemy(path, offset=0)
                        new_enemy.update_position(self.target.x, self.target.y, self.target.current_path_index, self.target.current_progress)
                        # Create a new green enemy at the same position
                        enemies.append(new_enemy)  # Adjust spawn if needed based on position
                        enemies.remove(self.target)  # Remove the blue enemy
                        print("Blue enemy defeated and a purple enemy spawned!")
                    elif isinstance(self.target, RedEnemy):
                        money += self.target.reward
                        new_enemy = BlueEnemy(path, offset=0)
                        new_enemy.update_position(self.target.x, self.target.y, self.target.current_path_index, self.target.current_progress)
                        # Create a new green enemy at the same position
                        enemies.append(new_enemy)  # Adjust spawn if needed based on position
                        enemies.remove(self.target)  # Remove the red enemy
                        print("Red enemy defeated and a blue enemy spawned!")
                    elif isinstance(self.target, BlackEnemy):
                        money += self.target.reward
                        new_enemy = RedEnemy(path, offset=0)
                        new_enemy.update_position(self.target.x, self.target.y, self.target.current_path_index, self.target.current_progress)
                        # Create a new green enemy at the same position
                        enemies.append(new_enemy)  # Adjust spawn if needed based on position
                        enemies.remove(self.target)  # Remove the red enemy
                        print("Black enemy defeated and a red enemy spawned!")
                    else:
                        print(f"Enemy at ({self.target.x}, {self.target.y}) defeated")
                        money += self.target.reward  # Add money when enemy is defeated
                        return True  # Indicate the bullet hit the target

        return False  # Indicate the bullet did not hit the target

class Tower:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.range = 120  # Adjust the range as needed
        self.cost = 375
        self.color = BLUE
        self.cooldown = 0
        self.bullets = []
        self.rate_of_fire = 80 # Fire rate in frames
        self.last_shot_time = 0  # Time when the last shot was fired

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), 20)
        #pygame.draw.circle(screen, RED, (self.x, self.y), self.range, 1)
        range_surface = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)  # Create a surface for the range
        #pygame.draw.circle(range_surface, (255, 0, 0, 50), (self.range, self.range), self.range)  # Red with transparency
        screen.blit(range_surface, (self.x - self.range, self.y - self.range))
        
    
    def draw_range(self, screen):
        # Draw the range circle (if needed separately for placement)
        pygame.draw.circle(screen, RED, (self.x, self.y), self.range, 1)  # Draw range

    def shoot(self, enemies):
        current_time = pygame.time.get_ticks()  # Get current time in milliseconds
        # Check if enough time has passed since the last shot
        if (current_time - self.last_shot_time) > (self.rate_of_fire * 1000 / (fps + 60)):

            # Initialize variable to track the best candidate enemy
            target_enemy = None

            for enemy in enemies:
                # Calculate the distance from the tower to the enemy
                distance = math.sqrt((enemy.x - self.x) ** 2 + (enemy.y - self.y) ** 2)

                # Check if the enemy is within the tower's firing range
                if distance < self.range:
                    # Update target if we have a better candidate based on current_progress
                    if target_enemy is None or enemy.current_progress > target_enemy.current_progress:
                        target_enemy = enemy  # Update the target enemy

            # If a target enemy is found and it's different from the last one
            if target_enemy and (not self.bullets or self.bullets[0].target != target_enemy):
                # Clear existing bullets if the target has changed
                self.bullets.clear()  # Clear old bullets to stop firing at the previous target

                # Fire a new bullet at the new target enemy
                self.bullets.append(Bullet(self.x, self.y, target_enemy))
                self.last_shot_time = current_time  # Update last shot time


    def update(self, enemies):
        global money  # Declare money as global to modify it
        # Continuously update the target enemy
        self.shoot(enemies)  # Call shoot here to ensure it checks for the target every frame
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
    
    def find_target(self, enemies):
        # Find the enemy with the highest path progress within range
        max_progress_enemy = None
        max_progress = -1  # Initialize with a very low value

        for enemy in enemies:
            distance = math.sqrt((enemy.x - self.x) ** 2 + (enemy.y - self.y) ** 2)
            if distance <= self.range:
                # Check if this enemy has the highest path progress
                if enemy.current_progress > max_progress:
                    max_progress_enemy = enemy
                    max_progress = enemy.current_progress

        self.target_enemy = max_progress_enemy

class SniperTower(Tower):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.range = 260  # Adjust the range as needed
        self.cost = 675
        self.color = GREEN
        self.rate_of_fire = 160 # Fire rate in frames

#Base enemy AKA green enemy
class Enemy:
    def __init__(self, path, offset=0):
        self.path = path
        start_x, start_y = path[0]
        self.x = start_x + offset
        self.y = start_y + offset
        self.current_path_index = 0
        self.current_progress = 0.0
        self.speed = 1.15 # Default speed for green enemies
        self.health = 1
        self.max_health = self.health
        self.color = GREEN
        self.reward = 1

    def move(self):
        if self.current_path_index < len(self.path) - 1:
            target_x, target_y = self.path[self.current_path_index + 1]
            direction = math.atan2(target_y - self.y, target_x - self.x)
            self.x += self.speed * math.cos(direction)
            self.y += self.speed * math.sin(direction)

            # Calculate the distance to the next path point
            distance_to_target = math.sqrt((target_x - self.x) ** 2 + (target_y - self.y) ** 2)

            # Calculate the total distance from the current path point to the next path point
            total_distance = math.sqrt((target_x - self.path[self.current_path_index][0]) ** 2 +
                                        (target_y - self.path[self.current_path_index][1]) ** 2)

            # Update the current_progress based on the distance traveled
            if total_distance > 0:
                progress_percentage = (1 - (distance_to_target / total_distance))  # Progress as a fraction (0 to 1)
                self.current_progress = self.current_path_index + progress_percentage  # Keep it a float

            # Convert current_progress to an integer index
            self.current_path_index = int(self.current_progress)

            # Check if the enemy reached the next path point
            if distance_to_target < self.speed:
                self.current_path_index += 1
                self.current_progress = self.current_path_index  # Reset progress when reaching the point
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
    
    def update_position(self, new_x, new_y, index, progress):
        self.x = new_x
        self.y = new_y
        self.current_path_index = index
        self.current_progress = progress

class PurpleEnemy(Enemy):
    def __init__(self, path, offset=0):
        super().__init__(path, offset)  # Pass path and offset to superclass
        self.speed = 1.65  # Set speed for purple enemies
        self.health = 1
        self.max_health = self.health
        self.color = (128, 0, 128)  # Purple color
        self.reward = 2  # Double the reward (15 instead of 10)

class BlueEnemy(Enemy):
    def __init__(self, path, offset = 0):
        super().__init__(path, offset)
        self.speed = 2.15
        self.health = 1
        self.max_health = self.health
        self.color = (52, 119, 235)
        self.reward = 3

class RedEnemy(Enemy):
    def __init__(self, path, offset = 0):
        super().__init__(path, offset)
        self.speed = 2.75
        self.health = 1
        self.max_health = self.health
        self.color = (171, 3, 3)
        self.reward = 5
        
class BlackEnemy(Enemy):
    def __init__(self, path, offset = 0):
        super().__init__(path, offset)
        self.speed = 1.65
        self.health = 3
        self.max_health = self.health
        self.color = (0,0,0)
        self.reward = 1
def draw_path(screen, path):
    for i in range(len(path) - 1):
        pygame.draw.line(screen, BLACK, path[i], path[i + 1], 5)

def is_near_path(x, y, path_surface, radius=25):
    # Check if the coordinates are within the bounds of the path surface
    if 0 <= x < path_surface.get_width() and 0 <= y < path_surface.get_height():
        # Check a circular area around the tower position (x, y) for black pixels
        for check_x in range(x - radius, x + radius):
            for check_y in range(y - radius, y + radius):
                # Make sure the coordinates are within bounds
                if 0 <= check_x < path_surface.get_width() and 0 <= check_y < path_surface.get_height():
                    # Get the color of the pixel at (check_x, check_y) on the path_surface
                    if path_surface.get_at((check_x, check_y))[:3] == (0, 0, 0):  # Black color
                        return True  # Too close to the path
    return False  # Far enough from the path

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

def draw_fps(screen, fps):
    fps_text = font.render(f"FPS: {fps}", True, BLACK)
    screen.blit(fps_text, (WIDTH - 220, 130))

def start_next_level(start_level=False):
    global money, level, enemies, level_timer, next_level_state, max_enemies, spawn_timer, enemies_spawned, can_start_next_level
    if start_level:
        level = 1  # Start at level 1
    else:
        level += 1  # Increment the level
        if level <= 3 and level > 1:
            money += 150
        elif level <= 6 and level > 3:
            money += 150
        elif level <= 10 and level > 6:
            money += 150


    # Get the number of enemies for the current level from the config
    enemy_counts = get_number_of_enemies_for_level(level, level_config)
    
    # Store the total number of enemies (green + purple) for the level
    max_enemies = enemy_counts["green"] + enemy_counts["purple"] + enemy_counts["blue"] + enemy_counts["red"] + enemy_counts["black"]


    # Print enemy counts once
    print(f"Level {level} started with {enemy_counts['green']} green enemies and {enemy_counts['purple']} purple enemies and {enemy_counts['blue']} blue enemies and {enemy_counts['red']} red enemies and {enemy_counts['black']} black enemies")

    enemies = []
    enemies_spawned = 0
    level_timer = time.time()
    spawn_timer = time.time()
    next_level_state = False
    can_start_next_level = False

# Add a flag to track if the message has been printed
all_enemies_spawned_printed = False

tower_radius = 50

def is_valid_position(mouse_x, mouse_y, towers, tower_radius):
    # Check if the position is far enough from existing towers
    for tower in towers:
        distance = math.sqrt((tower.x - mouse_x) ** 2 + (tower.y - mouse_y) ** 2)
        if distance < tower_radius:  # Adjust as needed for your tower radius
            return False
    return True

def spawn_enemy():
    global spawn_timer, enemies_spawned, green_enemies, purple_enemies, blue_enemies, red_enemies, total_enemies, all_enemies_spawned_printed

    current_time = time.time()

    # Get the enemy counts for the current level
    enemy_counts = get_number_of_enemies_for_level(level, level_config)
    green_enemies = enemy_counts["green"]
    purple_enemies = enemy_counts["purple"]
    blue_enemies = enemy_counts["blue"]
    red_enemies = enemy_counts["red"]
    black_enemies = enemy_counts["black"]
    # Calculate the total number of enemies for the current level
    total_enemies = green_enemies + purple_enemies + blue_enemies + red_enemies+black_enemies

    # Early exit if all enemies have been spawned
    if enemies_spawned >= total_enemies:
        if not all_enemies_spawned_printed:  # Check if the message has already been printed
            print("All enemies have been spawned.")
            all_enemies_spawned_printed = True  # Set the flag to True to prevent future prints
        return

    # Only spawn if enough time has passed
    if current_time - spawn_timer >= SPAWN_DELAY:
        # Spawn green enemies first
        if enemies_spawned < green_enemies:
            # Set the enemy's starting position to the first point in the path
            start_position = path[0]
            enemies.append(Enemy(path, offset=0))  # Spawn enemy at the start of the path
            enemies_spawned += 1
            print(f"Green enemy spawned! Total spawned: {enemies_spawned}")

        # Spawn purple enemies next
        elif enemies_spawned < green_enemies + purple_enemies:
            # Set the enemy's starting position to the first point in the path
            start_position = path[0]
            enemies.append(PurpleEnemy(path, offset=0))  # Spawn enemy at the start of the path
            enemies_spawned += 1
            print(f"Purple enemy spawned! Total spawned: {enemies_spawned}")
        
        # Spawn blue enemies next
        elif enemies_spawned < green_enemies + purple_enemies + blue_enemies:
            # Set the enemy's starting position to the first point in the path
            start_position = path[0]
            enemies.append(BlueEnemy(path, offset=0))  # Spawn enemy at the start of the path
            enemies_spawned += 1
            print(f"Blue enemy spawned! Total spawned: {enemies_spawned}")

        # Spawn red enemies next
        elif enemies_spawned < green_enemies + purple_enemies + blue_enemies + red_enemies:
            # Set the enemy's starting position to the first point in the path
            start_position = path[0]
            enemies.append(RedEnemy(path, offset=0))  # Spawn enemy at the start of the path
            enemies_spawned += 1
            print(f"Red enemy spawned! Total spawned: {enemies_spawned}")

        elif enemies_spawned < total_enemies:
            # Set the enemy's starting position to the first point in the path
            start_position = path[0]
            enemies.append(BlackEnemy(path, offset=0))  # Spawn enemy at the start of the path
            enemies_spawned += 1
            print(f"Red enemy spawned! Total spawned: {enemies_spawned}")

        
        
    
        # Print spawn check details after successfully spawning an enemy
        print(f"Spawn check: Green: {green_enemies}, Purple: {purple_enemies}, Blue: {blue_enemies}, Red: {red_enemies}, Black: {black_enemies} Total: {total_enemies}, Spawned: {enemies_spawned}")

        # Reset the spawn timer after an enemy is spawned
        spawn_timer = current_time

# Define the path for enemies
path = [(50, 50), (200, 50), (200, 200), (400, 200), (400, 400), (600, 400), (600, 550)]


# Create a separate surface for the path
path_surface = pygame.Surface((WIDTH, HEIGHT))
path_surface.fill((255, 255, 255))  # Fill with white (background color)

# Draw the black path on the path surface by connecting the points
PATH_COLOR = (0, 0, 0)
path_width = 10  # Adjust the path width as needed

for i in range(len(path) - 1):
    # Draw a line between consecutive points in the path
    pygame.draw.line(path_surface, PATH_COLOR, path[i], path[i + 1], path_width)

# Define a background color
BACKGROUND_COLOR = WHITE

# Game loop
towers = []
enemies = []
money = 675
lives = 25
# Define the tower button rectangle
tower_button_rect = pygame.Rect(10, HEIGHT - 60, 150, 50)  

running = True
tower_selected = False
placing_tower = False  # Flag to indicate if the player is in tower placement mode
placing_sniper_tower = False #Flag to indicate if the player is in sniper tower placement mode
current_tower_position = None  # To track the current position of the tower being placed

# Change initial level to 0
level = 0  # Start from level 0
next_level_state = False  # Maintain the existing variable

# Define the start button rectangle
start_button_rect = pygame.Rect(WIDTH - 220, HEIGHT - 60, 200, 50)  

# Define a variable to track whether the game has started
game_started = True

# Update the draw_start_button function
def draw_start_button(screen):
    button_color = GREEN if can_start_next_level else RED  # Change button color based on state
    pygame.draw.rect(screen, button_color, start_button_rect)
    text_surface = font.render("Start", True, WHITE)
    screen.blit(text_surface, (WIDTH - 210, HEIGHT - 50))


def draw_game_elements(screen):
    # Draw path
    draw_path(screen, path)

    # Draw towers
    for tower in towers:
        tower.draw(screen)
        tower.draw_bullets(screen)

    # Draw enemy count, money, and lives
    draw_enemy_counter_and_money(screen, max_enemies - enemies_spawned, money)
    draw_level(screen, level)

    # Draw the tower button with color based on money available
    if money >= 375:
        pygame.draw.rect(screen, GREEN, tower_button_rect)
    else:
        pygame.draw.rect(screen, RED, tower_button_rect)

    # Draw the tower button text
    button_text = font.render("Tower (375)", True, WHITE)
    screen.blit(button_text, (tower_button_rect.x + 10, tower_button_rect.y + 10))

while running:
    # Fill the screen with the background color
    screen.fill(BACKGROUND_COLOR)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 and money >= 375:
                print("1 button is BEING PRESSED FOR MAXWELL'S HEALTH")
                tower_selected = True  # A tower has been selected
                placing_tower = True    # Begin the placement process
            if event.key == pygame.K_2 and money >= 675:
                print("2 button is BEING PRESSED FOR MAXWELL'S SNIPER")
                tower_selected = True  # A tower has been selected
                placing_sniper_tower = True    # Begin the placement process
            if event.key == pygame.K_EQUALS and fps < 240:
                print("speeding up time")
                fps += 30
            if event.key == pygame.K_MINUS and fps > 60:
                print("speeding down time")
                fps -= 30

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

            # Check if the click is on the tower button (assuming you have a button rect)
            if tower_button_rect.collidepoint(mouse_x, mouse_y) and money >= 375:
                tower_selected = True  # A tower has been selected
                placing_tower = True    # Begin the placement process

            # If placing a tower, allow clicking to place it on the map
            elif placing_tower:
                # Check if it's in a valid position (not too close to path)
                if not is_near_path(mouse_x, mouse_y, path_surface, radius=25) and is_valid_position(mouse_x, mouse_y, towers, tower_radius):  # Check placement validity
                    towers.append(Tower(mouse_x, mouse_y))  # Place the tower
                    money -= 375
                    placing_tower = False  # Finish placement
                    tower_selected = False  # Reset the selection state
                else:
                # Optional: Feedback if trying to place in an invalid area
                    print("Invalid position! Too close to the path.")
            
            elif placing_sniper_tower:
                # Check if it's in a valid position (not too close to path)
                if not is_near_path(mouse_x, mouse_y, path_surface, radius=25) and is_valid_position(mouse_x, mouse_y, towers, tower_radius):  # Check placement validity
                    towers.append(SniperTower(mouse_x, mouse_y))  # Place the tower
                    money -= 675
                    placing_sniper_tower = False  # Finish placement
                    tower_selected = False  # Reset the selection state
                else:
                # Optional: Feedback if trying to place in an invalid area
                    print("Invalid position! Too close to the path.")

    # Draw start button
    draw_start_button(screen)

    # Draw game elements even if the game hasn't started yet
    if game_started:
        # Draw path
        draw_path(screen, path)

        # Draw towers and update bullets
        for tower in towers:
            tower.draw(screen)
            tower.find_target(enemies)
            tower.shoot(enemies)
            tower.update(enemies)
            tower.draw_bullets(screen)

            # Draw the tower range only if placing a new tower
            if placing_tower:
                tower.draw_range(screen)  # Show the range of the current tower being placed

            if placing_sniper_tower:
                tower.draw_range(screen)  # Show the range of the current tower being placed

        # Spawn enemies and move them
        spawn_enemy()

        for enemy in enemies:
            enemy.move()  # Move each enemy
            #print(enemy.current_progress)
            if enemy.health <= 0:  # Check if the enemy is defeated
                money += enemy.reward  # Add money for defeating the enemy
                enemies.remove(enemy)  # Remove the enemy from the enemies list
            enemy.draw(screen)  # Draw each enemy

        # Draw enemy count, money, and lives
        draw_enemy_counter_and_money(screen, max_enemies - enemies_spawned, money)

        if level >= 1:
            draw_level(screen, level)

        draw_fps(screen, fps)

        # Draw the tower button with color based on money available
        if money >= 375:
            pygame.draw.rect(screen, GREEN, tower_button_rect)
        else:
            pygame.draw.rect(screen, RED, tower_button_rect)

        # Draw the tower button text
        button_text = font.render("Tower (375)", True, WHITE)
        screen.blit(button_text, (tower_button_rect.x + 10, tower_button_rect.y + 10))
    
    # Modified tower placement logic with path proximity check
    if placing_tower:
        # Get the current mouse position
        current_mouse_x, current_mouse_y = pygame.mouse.get_pos()

        # Check if it's too close to the path to decide color
        if is_near_path(current_mouse_x, current_mouse_y, path_surface, radius=25) or not is_valid_position(current_mouse_x, current_mouse_y, towers, tower_radius):
            tower_color = RED  # Invalid position (too close to path)
        else:
            tower_color = GREEN  # Valid position

        # Draw the tower in the temporary position (hovering with the mouse)
        pygame.draw.circle(screen, tower_color, (current_mouse_x, current_mouse_y), 20)

        # Optionally draw the range of the tower while placing
        temp_tower = Tower(current_mouse_x, current_mouse_y)
        temp_tower.draw_range(screen)

    if placing_sniper_tower:
        # Get the current mouse position
        current_mouse_x, current_mouse_y = pygame.mouse.get_pos()

        # Check if it's too close to the path to decide color
        if is_near_path(current_mouse_x, current_mouse_y, path_surface, radius=25) or not is_valid_position(current_mouse_x, current_mouse_y, towers, tower_radius):
            tower_color = RED  # Invalid position (too close to path)
        else:
            tower_color = GREEN  # Valid position

        # Draw the tower in the temporary position (hovering with the mouse)
        pygame.draw.circle(screen, tower_color, (current_mouse_x, current_mouse_y), 20)

        # Optionally draw the range of the tower while placing
        temp_sniper_tower = SniperTower(current_mouse_x, current_mouse_y)
        temp_sniper_tower.draw_range(screen)

    # Check for level progression
    if len(enemies) == 0 and enemies_spawned >= total_enemies:
        can_start_next_level = True  # Allow starting the next level

    # Update the display
    pygame.display.flip()
    clock.tick(fps)

# Quit pygame
pygame.quit()