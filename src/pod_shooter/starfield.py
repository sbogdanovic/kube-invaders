import math
import random

import pygame

from .constants import WIDTH, HEIGHT


class _NebulaCloud:
    """A single soft purple haze cloud that drifts slowly downward."""

    def __init__(self, y=None):
        self.x = random.uniform(-100, WIDTH + 100)
        self.y = y if y is not None else random.uniform(-200, HEIGHT + 200)
        self.radius = random.uniform(100, 250)
        self.speed = random.uniform(0.05, 0.15)
        self.phase = random.uniform(0, math.pi * 2)
        self.phase_speed = random.uniform(0.003, 0.01)
        # Purple hue with slight variation
        self.r = random.randint(50, 110)
        self.g = random.randint(0, 30)
        self.b = random.randint(100, 180)
        self._surface = None
        self._build_surface()

    def _build_surface(self):
        sz = int(self.radius * 2)
        self._surface = pygame.Surface((sz, sz), pygame.SRCALPHA)
        cx = cy = sz // 2
        # Draw concentric filled circles from large (dim) to small (brighter)
        layers = 10
        for i in range(layers, 0, -1):
            ratio = i / layers
            r = int(self.radius * ratio)
            # Outer layers dimmer, inner layers brighter
            a = int(15 + 30 * (1.0 - ratio))
            if r > 0:
                pygame.draw.circle(
                    self._surface, (self.r, self.g, self.b, a), (cx, cy), r
                )

    def update(self):
        self.y += self.speed
        self.phase += self.phase_speed
        if self.y - self.radius > HEIGHT + 50:
            self.y = -self.radius - random.uniform(0, 100)
            self.x = random.uniform(-100, WIDTH + 100)

    def draw(self, surface):
        # Gentle pulsing alpha
        pulse = 0.5 + 0.2 * math.sin(self.phase)
        sz = self._surface.get_width()
        x = int(self.x - sz // 2)
        y = int(self.y - sz // 2)
        # Only blit if on screen
        if x + sz > 0 and x < WIDTH and y + sz > 0 and y < HEIGHT:
            if abs(pulse - 1.0) < 0.05:
                surface.blit(self._surface, (x, y))
            else:
                tmp = self._surface.copy()
                tmp.set_alpha(int(255 * pulse))
                surface.blit(tmp, (x, y))


class Starfield:
    def __init__(self):
        self.stars = []
        for _ in range(120):
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            speed = random.uniform(0.2, 1.5)
            brightness = random.randint(80, 200)
            self.stars.append([x, y, speed, brightness])

        # Nebula haze clouds
        self.clouds = [_NebulaCloud() for _ in range(8)]

    def update(self):
        for c in self.clouds:
            c.update()
        for s in self.stars:
            s[1] += s[2]
            if s[1] > HEIGHT:
                s[1] = 0
                s[0] = random.randint(0, WIDTH)

    def draw(self, surface):
        # Draw clouds behind stars
        for c in self.clouds:
            c.draw(surface)
        for x, y, _, b in self.stars:
            c = (b, b, min(255, b + 40))
            pygame.draw.circle(surface, c, (int(x), int(y)), 1)
