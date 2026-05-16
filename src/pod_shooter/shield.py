import pygame

from .constants import NEON_GREEN
from .glow import _bbox, draw_glow_lines


class Shield:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 6
        self.w = 50
        self.h = 20

    @property
    def alive(self):
        return self.health > 0

    @property
    def rect(self):
        return pygame.Rect(self.x - self.w // 2, self.y - self.h // 2, self.w, self.h)

    def draw(self, surface):
        if not self.alive:
            return
        alpha_ratio = self.health / 6
        color = (
            int(NEON_GREEN[0] * alpha_ratio),
            int(NEON_GREEN[1] * alpha_ratio),
            int(NEON_GREEN[2] * alpha_ratio),
        )
        pts = [
            (self.x - self.w // 2, self.y + self.h // 2),
            (self.x - self.w // 2 + 5, self.y - self.h // 2),
            (self.x + self.w // 2 - 5, self.y - self.h // 2),
            (self.x + self.w // 2, self.y + self.h // 2),
        ]
        draw_glow_lines(surface, color, True, pts, 2, 2)
        fill_alpha = int(30 * alpha_ratio)
        bx1, by1, bx2, by2 = _bbox(pts, 1)
        sw = int(bx2 - bx1) + 1
        sh = int(by2 - by1) + 1
        tmp = pygame.Surface((sw, sh), pygame.SRCALPHA)
        local_pts = [(p[0] - bx1, p[1] - by1) for p in pts]
        pygame.draw.polygon(tmp, (*color, fill_alpha), local_pts)
        surface.blit(tmp, (bx1, by1))
