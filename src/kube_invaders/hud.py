import math

import pygame

from .constants import WIDTH, NEON_CYAN, NEON_GREEN, NEON_RED, NEON_YELLOW


def draw_hud(
    surface,
    font,
    score,
    lives,
    wave,
    alien_win_eta: float | None = None,
    alien_timer_visible: bool = True,
):
    score_text = font.render(f"SCORE: {score}", True, NEON_YELLOW)
    surface.blit(score_text, (15, 10))

    wave_text = font.render(f"WAVE {wave}", True, NEON_GREEN)
    surface.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, 10))

    if alien_win_eta is not None and alien_timer_visible:
        remaining = max(0, math.ceil(alien_win_eta))
        mins, secs = divmod(remaining, 60)
        timer_label = f"TIME LEFT: {mins:02d}:{secs:02d}"
        timer_color = NEON_RED if alien_win_eta <= 10.0 else NEON_YELLOW
        timer_text = font.render(timer_label, True, timer_color)
        surface.blit(timer_text, (15, 34))

    lives_text = font.render("LIVES:", True, NEON_CYAN)
    surface.blit(lives_text, (WIDTH - 180, 10))
    for i in range(lives):
        lx = WIDTH - 100 + i * 25
        ly = 18
        pts = [(lx, ly - 8), (lx + 8, ly + 6), (lx - 8, ly + 6)]
        pygame.draw.lines(surface, NEON_CYAN, True, pts, 1)
