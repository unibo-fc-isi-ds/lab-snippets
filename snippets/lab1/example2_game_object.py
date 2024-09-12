from pygame.math import Vector2
from pygame.rect import Rect


class GameObject:
    def __init__(self, size, position=None, speed=None, name=None):
        self.size = Vector2(size)
        self.position = Vector2(position) if position is not None else Vector2()
        self.speed = Vector2(speed) if speed is not None else Vector2()
        self.name = name or self.__class__.__name__.lower()
    
    def __eq__(self, other):
        return isinstance(other, type(self)) and \
            self.name == other.name and \
            self.size == other.size and \
            self.position == other.position and \
            self.speed == other.speed

    def __hash__(self):
        return hash((type(self), self.name, self.size, self.position, self.speed))

    def __repr__(self):
        return f'<{type(self).__name__}(id={id(self)}, name={self.name}, size={self.size}, position={self.position}, speed={self.speed})>'

    def __str__(self):
        return f'{self.name}#{id(self)}'
    
    @property
    def bounding_box(self):
        return Rect(self.position - self.size / 2, self.size)
    
    def update(self, dt):
        self.position = self.position + self.speed * dt


if __name__ == '__main__':
    x = GameObject((10, 20), (100, 200), (1, 2), 'myobj')
    assert x.size == Vector2(10, 20)
    assert x.position == Vector2(100, 200)
    assert x.speed == Vector2(1, 2)
    assert x.name == 'myobj'
    assert x.bounding_box.topleft == (95, 190)
    assert x.bounding_box.size == (10, 20)
    assert x.bounding_box.bottomright == (105, 210)
    assert str(x) == 'myobj#' + str(id(x))
    assert repr(x) == ('<GameObject(id=%d, name=myobj, size=[10, 20], position=[100, 200], speed=[1, 2])>' % id(x))
    
    y = GameObject((10, 20), (100, 200), (1, 2), 'myobj')
    z = GameObject((10, 20), (100, 200), (1, 2), 'myobj2')
    assert x == y
    assert x != z

    x.update(2)
    assert x.position == Vector2(102, 204)
    assert x != y

