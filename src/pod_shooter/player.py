import math

import pygame

from .constants import (
    WIDTH, PLAYER_SPEED, BULLET_SPEED, NEON_CYAN, NEON_WHITE, NEON_ORANGE,
    NEON_YELLOW,
)
from .glow import draw_glow_lines


class Player:
    def __init__(self):
        self.x = WIDTH // 2
        self.y = -1  # set properly by Game
        self.w = 40
        self.h = 30
        self.alive = True
        self.respawn_timer = 0
        self.blink = False
        self.thrust_phase = 0.0
        # Load shoot sound
        try:
            import pygame.mixer
            from .constants import ASSET_LASER
            self._shoot_sound = pygame.mixer.Sound(ASSET_LASER)
        except Exception:
            self._shoot_sound = None

    @property
    def rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def update(self, keys):
        if not self.alive:
            return
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x = max(self.w // 2, self.x - PLAYER_SPEED)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x = min(WIDTH - self.w // 2, self.x + PLAYER_SPEED)
        self.thrust_phase += 0.15

    def draw(self, surface):
        if not self.alive:
            return
        cx, cy = self.x, self.y
        hw, hh = self.w // 2, self.h // 2

        # Main hull — triangular
        hull = [
            (cx, cy - hh - 6),
            (cx + hw, cy + hh),
            (cx + hw // 3, cy + hh - 4),
            (cx - hw // 3, cy + hh - 4),
            (cx - hw, cy + hh),
        ]
        draw_glow_lines(surface, NEON_CYAN, True, hull, 2)

        # Cockpit
        cockpit = [
            (cx, cy - hh + 2),
            (cx + 6, cy - 2),
            (cx, cy + 2),
            (cx - 6, cy - 2),
        ]
        draw_glow_lines(surface, NEON_WHITE, True, cockpit, 1, 2)

        # Wing accents
        draw_glow_lines(surface, NEON_CYAN, False,
                        [(cx - hw - 4, cy + hh + 2), (cx - hw, cy + hh), (cx - hw + 4, cy)], 1, 2)
        draw_glow_lines(surface, NEON_CYAN, False,
                        [(cx + hw + 4, cy + hh + 2), (cx + hw, cy + hh), (cx + hw - 4, cy)], 1, 2)

        # Engine thrust — animated flicker
        flicker = math.sin(self.thrust_phase) * 4 + 6
        thrust_color = NEON_ORANGE if int(self.thrust_phase * 10) % 2 == 0 else NEON_YELLOW
        thrust = [
            (cx - 5, cy + hh - 4),
            (cx, cy + hh + flicker),
            (cx + 5, cy + hh - 4),
        ]
        draw_glow_lines(surface, thrust_color, False, thrust, 1, 3)

    def shoot(self):
        if not self.alive:
            return None
        if self._shoot_sound:
            try:
                self._shoot_sound.play()
            except Exception:
                pass
        from .bullet import Bullet
        return Bullet(self.x, self.y - self.h // 2 - 8, -BULLET_SPEED, NEON_CYAN)
