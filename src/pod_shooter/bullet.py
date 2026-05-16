import math
import random

import pygame

from .constants import HEIGHT
from .glow import draw_glow_lines


class Bullet:
    def __init__(self, x, y, dy, color, is_alien=False):
        self.x = x
        self.y = y
        self.dy = dy
        self.color = color
        self.is_alien = is_alien
        self.alive = True
        self.phase = random.uniform(0, math.pi * 2)

    def update(self):
        self.y += self.dy
        self.phase += 0.3
        if self.y < -10 or self.y > HEIGHT + 10:
            self.alive = False

    def draw(self, surface):
        length = 10
        pulse = math.sin(self.phase) * 2
        x, y = int(self.x), int(self.y)
        if self.is_alien:
            pts = [
                (x, y - 6 - pulse),
                (x + 3, y),
                (x, y + 6 + pulse),
                (x - 3, y),
            ]
            draw_glow_lines(surface, self.color, True, pts, 1, 3)
        else:
            draw_glow_lines(
                surface,
                self.color,
                False,
                [(x, y - length // 2 - pulse), (x, y + length // 2 + pulse)],
                2,
                3,
            )

    @property
    def rect(self):
        return pygame.Rect(self.x - 3, self.y - 6, 6, 12)
