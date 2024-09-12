import pygame
from pygame.event import Event, custom_type
from enum import Enum


class GameEvent(Enum):
    MOVE_UP: int = custom_type()
    MOVE_DOWN: int = custom_type()
    MOVE_LEFT: int = custom_type()
    MOVE_RIGHT: int = custom_type()
    STOP: int = pygame.QUIT

    def create_event(self, **kwargs):
        return Event(self.value, kwargs)
    
    @classmethod
    def all(cls) -> set['GameEvent']:
        return set(cls.__members__.values())

    @classmethod
    def types(cls) -> list[int]:
        return [event.value for event in cls.all()]


KEYMAP_WASD = {
    pygame.K_w: GameEvent.MOVE_UP,
    pygame.K_s: GameEvent.MOVE_DOWN,
    pygame.K_d: GameEvent.MOVE_RIGHT,
    pygame.K_a: GameEvent.MOVE_LEFT,
    pygame.K_ESCAPE: GameEvent.STOP
}


class InputHandler:
    def __init__(self, keymap=None):
        self.keymap = dict(keymap) if keymap is not None else KEYMAP_WASD

    def handle_inputs(self):
        for event in pygame.event.get([pygame.KEYDOWN, pygame.KEYUP]):
            if event.key in self.keymap.keys():
                game_event = self.keymap[event.key].create_event(up=event.type == pygame.KEYUP)
                self.post_event(game_event)

    def post_event(self, game_event):
        pygame.event.post(game_event)


class Controller(InputHandler):
    def __init__(self, game_object, speed, keymap=None):
        super().__init__(keymap)
        self._game_object = game_object
        self._speed = speed

    def update(self, dt):
        for event in pygame.event.get(GameEvent.types()):
            self._update_object_according_to_event(self._game_object, event)
        self._game_object.update(dt)

    def _update_object_according_to_event(self, game_object, event):
        match GameEvent(event.type):
            case GameEvent.MOVE_UP:
                game_object.speed.y = 0 if event.up else -self._speed
            case GameEvent.MOVE_DOWN:
                game_object.speed.y = 0 if event.up else self._speed
            case GameEvent.MOVE_LEFT:
                game_object.speed.x = 0 if event.up else -self._speed
            case GameEvent.MOVE_RIGHT:
                game_object.speed.x = 0 if event.up else self._speed
            case GameEvent.STOP:
                pygame.quit()
                exit()
