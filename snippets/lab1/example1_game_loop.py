import pygame

# Initialize Pygame
pygame.init()

# Screen dimensions
screen_size = pygame.Vector2(800, 600)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Game Loop Example")

# Colours
white = pygame.color.Color(255, 255, 255)  # White color RGB
black = pygame.color.Color(0, 0, 0)  # Black color RGB

# Circle settings
circle_radius = min(screen_size) / 10  # Circle radius is 1/10th of the screen size's smallest dimension
circle_posistion = screen_size / 2  # Start at the center
circle_speed = min(screen_size) / 10  # Absolute speed of the circle is 1/10th of the screen size's smallest dimension
circle_velocity = pygame.Vector2(0, 0)  # Initial velocity of the circle

clock = pygame.time.Clock()

# Main game loop
dt = 0.0 # time elapsed since last loop iteration
running = True # game should stop when set to False
while running:
    # Event handling
    for event in pygame.event.get([pygame.KEYDOWN, pygame.KEYUP]):
        if event.key == pygame.K_ESCAPE:
            running = False # Quit the game
        elif event.key == pygame.K_w:  # Move up
            circle_velocity.y = -circle_speed if event.type == pygame.KEYDOWN else 0
        elif event.key == pygame.K_s:  # Move down
            circle_velocity.y = circle_speed if event.type == pygame.KEYDOWN else 0
        elif event.key == pygame.K_a:  # Move left
            circle_velocity.x = -circle_speed if event.type == pygame.KEYDOWN else 0
        elif event.key == pygame.K_d:  # Move right
            circle_velocity.x = circle_speed if event.type == pygame.KEYDOWN else 0

    # Clear screen
    screen.fill(black)  # Black background

    # Update and logs the circle's position
    old_circle_posistion = circle_posistion.copy()
    circle_posistion += dt * circle_velocity
    if old_circle_posistion != circle_posistion:
        print("Circle moves from", old_circle_posistion, "to", circle_posistion)

    # Draw the circle
    pygame.draw.circle(screen, white, circle_posistion, circle_radius)

    # Update the display
    pygame.display.flip()

    # Ensure the game runs at 60 FPS
    dt = clock.tick(60) / 1000.0 # Time elapsed since last loop iteration in seconds

# Quit Pygame
pygame.quit()
