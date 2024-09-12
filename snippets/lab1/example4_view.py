import pygame


class View:
    def __init__(self, game_object, screen=None, size=None, background_color=None, foreground_color=None):
        if screen is not None:
            size = screen.get_size()
        self._size = size or (800, 600) 
        self.background_color = pygame.Color(background_color or "black")
        self.foreground_color = pygame.Color(foreground_color or "white")
        self._screen = screen or pygame.display.set_mode(self._size)
        assert game_object is not None, "game_object cannot be None"
        self._game_object = game_object

    def render(self):
        self._reset_screen(self._screen, self.background_color)
        self._draw_game_object(self._game_object, self.foreground_color)
        pygame.display.flip()

    def _reset_screen(self, screen, color):
        screen.fill(color)
    
    def _draw_game_object(self, game_object, color):
        pygame.draw.ellipse(self._screen, color, game_object.bounding_box)    
        