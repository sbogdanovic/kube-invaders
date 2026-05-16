import math
import random

import pygame


class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.5, 5.0)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.life = random.uniform(0.4, 1.0)
        self.max_life = self.life
        self.length = random.uniform(4, 10)

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05
        self.life -= dt

    def draw(self, surface):
        alpha = max(0, int(255 * (self.life / self.max_life)))
        c = (*self.color[:3], alpha)
        ex = self.x + self.vx * self.length * 0.3
        ey = self.y + self.vy * self.length * 0.3
        x1, y1, x2, y2 = int(self.x), int(self.y), int(ex), int(ey)
        sx = min(x1, x2) - 2
        sy = min(y1, y2) - 2
        sw = abs(x2 - x1) + 5
        sh = abs(y2 - y1) + 5
        if sw < 1 or sh < 1:
            return
        tmp = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.line(tmp, c, (x1 - sx, y1 - sy), (x2 - sx, y2 - sy), 2)
        surface.blit(tmp, (sx, sy))
