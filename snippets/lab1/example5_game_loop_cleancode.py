import pygame
from .example2_game_object import GameObject
from .example3_controller import Controller
from .example4_view import View


# Initialize Pygame
pygame.init()

# Screen dimensions
screen_size = pygame.Vector2(800, 600)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption("Game Loop Example")

# Game objects
circle = GameObject(size=screen_size / 10, position=screen_size / 2, name="circle")

# Wire game-loop components together
controller = Controller(game_object=circle, speed=min(screen_size) / 10)
view = View(game_object=circle, screen=screen)
clock = pygame.time.Clock()

# Main game loop
dt = 0.0 # time elapsed since last loop iteration
running = True # game should stop when set to False
while running:
    controller.handle_inputs()
    controller.update(dt)
    view.render()
    # Ensure the game runs at 60 FPS
    dt = clock.tick(60) / 1000.0  # Time elapsed since last loop iteration in seconds

# Quit Pygame
pygame.quit()
