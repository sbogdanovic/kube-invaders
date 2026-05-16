import math
import random

import pygame

from .bullet import Bullet
from .constants import ALIEN_BULLET_SPEED, NEON_RED
from .glow import draw_glow_lines


class LiquidFill:
    """Simulates an animated liquid inside a polygon mask. Caches rendered
    surface and only redraws every CACHE_INTERVAL frames for performance."""

    CACHE_INTERVAL = 4

    def __init__(self, color, bbox_w, bbox_h):
        self.color = color
        self.w = bbox_w
        self.h = bbox_h
        self.fill_pct = 1.0  # 0.0 – 1.0, controlled by Alien health
        self.phase = random.uniform(0, math.pi * 2)
        self.speed = random.uniform(0.03, 0.07)
        self.wave_amp = random.uniform(2.0, 4.0)
        self.wave_freq = random.uniform(0.12, 0.22)
        self.bubbles = []
        for _ in range(random.randint(2, 4)):
            self.bubbles.append(
                {
                    "x": random.uniform(4, bbox_w - 4),
                    "y": random.uniform(4, bbox_h - 4),
                    "r": random.uniform(1.5, 3.0),
                    "speed": random.uniform(0.3, 0.8),
                    "phase": random.uniform(0, math.pi * 2),
                }
            )
        self._cache = None
        self._cache_size = None
        self._frame = 0

    def update(self):
        self.phase += self.speed
        self._frame += 1
        for b in self.bubbles:
            b["y"] -= b["speed"]
            b["phase"] += 0.05
            b["x"] += math.sin(b["phase"]) * 0.3
            if b["y"] < 2:
                b["y"] = self.h - 2
                b["x"] = random.uniform(4, self.w - 4)

    def _render(self, sw, sh, local_pts, mask_surf):
        liquid_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)

        # fill_pct controls how full the liquid is; small wave animation on top
        wave = 0.05 * math.sin(self.phase * 0.7)
        fill_level = max(0.0, min(1.0, self.fill_pct * 0.85 + wave))
        base_y = int(sh * (1.0 - fill_level))
        r, g, b = self.color[:3]

        for row in range(base_y, sh, 2):
            wave_offset = (
                math.sin(self.phase * 2 + row * self.wave_freq) * self.wave_amp
            )
            depth_ratio = (row - base_y) / max(1, sh - base_y)
            alpha = int(40 + 120 * depth_ratio)
            cr = min(255, int(r * (0.6 + 0.4 * depth_ratio)))
            cg = min(255, int(g * (0.6 + 0.4 * depth_ratio)))
            cb = min(255, int(b * (0.6 + 0.4 * depth_ratio)))

            start_x = max(0, int(wave_offset))
            end_x = min(sw, sw + int(wave_offset))
            if end_x > start_x:
                pygame.draw.line(
                    liquid_surf, (cr, cg, cb, alpha), (start_x, row), (end_x, row), 2
                )

        for dx in range(0, sw, 2):
            wy = base_y + int(
                math.sin(self.phase * 2 + dx * self.wave_freq) * self.wave_amp
            )
            if 0 <= wy < sh:
                highlight_alpha = int(140 + 60 * math.sin(self.phase * 3 + dx * 0.2))
                pygame.draw.circle(
                    liquid_surf,
                    (*self.color[:3], min(255, highlight_alpha)),
                    (dx, wy),
                    1,
                )

        for bub in self.bubbles:
            bx = int(bub["x"] * sw / self.w)
            by = int(bub["y"] * sh / self.h)
            br = max(1, int(bub["r"]))
            if base_y < by < sh:
                balpha = int(80 + 40 * math.sin(bub["phase"] * 3))
                pygame.draw.circle(
                    liquid_surf, (*self.color[:3], min(255, balpha)), (bx, by), br, 1
                )

        liquid_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return liquid_surf

    def draw(self, surface, outline_points, offset_x, offset_y):
        min_x = min(p[0] for p in outline_points)
        min_y = min(p[1] for p in outline_points)
        max_x = max(p[0] for p in outline_points)
        max_y = max(p[1] for p in outline_points)
        sw = int(max_x - min_x) + 4
        sh = int(max_y - min_y) + 4
        if sw < 2 or sh < 2:
            return

        need_render = (
            self._cache is None
            or self._cache_size != (sw, sh)
            or self._frame % self.CACHE_INTERVAL == 0
        )

        if need_render:
            local_pts = [(p[0] - min_x + 2, p[1] - min_y + 2) for p in outline_points]
            mask_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            pygame.draw.polygon(mask_surf, (255, 255, 255, 255), local_pts)
            self._cache = self._render(sw, sh, local_pts, mask_surf)
            self._cache_size = (sw, sh)

        surface.blit(self._cache, (min_x - 2, min_y - 2))


class Alien:
    SHAPES = ["diamond", "hexagon", "chevron", "crab", "ufo"]

    MAX_HEALTH = 5  # 5 hits to kill (each hit = 20% liquid)

    def __init__(self, x, y, shape, color):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = color
        self.health = self.MAX_HEALTH
        self.alive = True
        self.w = 30
        self.h = 26
        self.phase = random.uniform(0, math.pi * 2)
        self.liquid = LiquidFill(color, self.w, self.h)

        # Dive state
        self.diving = False
        self.dive_path = []  # list of (x, y) waypoints
        self.dive_index = 0  # current segment index
        self.dive_t = 0.0  # interpolation 0..1 within segment
        self.dive_speed = 3.0  # waypoints per second
        self.formation_ox = 0.0  # offset from formation x while diving
        self.formation_oy = 0.0  # offset from formation y while diving
        self.dive_shot_pending = False
        self.dive_shoot_timer = 0.0
        self._dive_bullet = None

    @property
    def draw_x(self):
        return self.x + self.formation_ox

    @property
    def draw_y(self):
        return self.y + self.formation_oy

    @property
    def rect(self):
        return pygame.Rect(
            self.draw_x - self.w // 2, self.draw_y - self.h // 2, self.w, self.h
        )

    def get_outline(self):
        cx, cy = int(self.draw_x), int(self.draw_y)
        hw, hh = self.w // 2, self.h // 2
        wobble = math.sin(self.phase) * 1.5

        if self.shape == "diamond":
            return [
                (cx, cy - hh - wobble),
                (cx + hw, cy),
                (cx, cy + hh + wobble),
                (cx - hw, cy),
            ]
        elif self.shape == "hexagon":
            pts = []
            for i in range(6):
                angle = math.pi / 6 + i * math.pi / 3
                r = hw + wobble
                pts.append(
                    (cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle)))
                )
            return pts
        elif self.shape == "chevron":
            return [
                (cx - hw, cy - hh),
                (cx, cy - hh // 2 + wobble),
                (cx + hw, cy - hh),
                (cx + hw, cy),
                (cx, cy + hh),
                (cx - hw, cy),
            ]
        elif self.shape == "crab":
            return [
                (cx - hw - 4, cy - hh + 2),
                (cx - hw // 2, cy - hh - wobble),
                (cx, cy - hh + 4),
                (cx + hw // 2, cy - hh - wobble),
                (cx + hw + 4, cy - hh + 2),
                (cx + hw, cy + hh // 2),
                (cx + hw // 2, cy + hh),
                (cx - hw // 2, cy + hh),
                (cx - hw, cy + hh // 2),
            ]
        else:  # ufo
            return [
                (cx - hw // 2, cy - hh),
                (cx + hw // 2, cy - hh),
                (cx + hw + 4, cy + wobble),
                (cx + hw // 2, cy + hh),
                (cx - hw // 2, cy + hh),
                (cx - hw - 4, cy + wobble),
            ]

    def hit(self):
        """Take one hit. Returns True if the alien is now dead."""
        self.health -= 1
        self.liquid.fill_pct = self.health / self.MAX_HEALTH
        self.liquid._cache = None  # force re-render
        if self.health <= 0:
            self.alive = False
            return True
        return False

    def start_dive(self, path):
        """Begin a dive along a list of (dx, dy) offset waypoints relative to
        the alien's formation position.  The path should end at (0, 0) so the
        alien returns to formation."""
        self.diving = True
        self.dive_path = path
        self.dive_index = 0
        self.dive_t = 0.0
        self.dive_shot_pending = True
        self.dive_shoot_timer = random.uniform(0.3, 1.2)

    def update(self, dt=1 / 60):
        self.phase += 0.04
        self.liquid.update()

        if self.diving and self.dive_path:
            # Dive shoot timer
            if self.dive_shot_pending:
                self.dive_shoot_timer -= dt
                if self.dive_shoot_timer <= 0:
                    self.dive_shot_pending = False
                    self._dive_bullet = self.shoot()

            self.dive_t += self.dive_speed * dt
            while self.dive_t >= 1.0 and self.dive_index < len(self.dive_path) - 1:
                self.dive_t -= 1.0
                self.dive_index += 1

            if self.dive_index >= len(self.dive_path) - 1:
                # Dive finished — snap back to formation
                self.diving = False
                self.formation_ox = 0.0
                self.formation_oy = 0.0
                self.dive_path = []
            else:
                ax, ay = self.dive_path[self.dive_index]
                bx, by = self.dive_path[self.dive_index + 1]
                t = self.dive_t
                self.formation_ox = ax + (bx - ax) * t
                self.formation_oy = ay + (by - ay) * t

    def draw(self, surface):
        outline = self.get_outline()
        self.liquid.draw(
            surface,
            outline,
            int(self.draw_x - self.w // 2),
            int(self.draw_y - self.h // 2),
        )
        draw_glow_lines(surface, self.color, True, outline, 2, 3)
        # Eyes
        cx, cy = int(self.draw_x), int(self.draw_y)
        eye_col = (*self.color[:3], 180)
        eye_surf = pygame.Surface((14, 8), pygame.SRCALPHA)
        pygame.draw.circle(eye_surf, eye_col, (2, 4), 2)
        pygame.draw.circle(eye_surf, eye_col, (12, 4), 2)
        surface.blit(eye_surf, (cx - 7, cy - 6))

    def shoot(self):
        return Bullet(
            self.draw_x,
            self.draw_y + self.h // 2 + 4,
            ALIEN_BULLET_SPEED,
            NEON_RED,
            is_alien=True,
        )
