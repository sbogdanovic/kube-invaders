import pygame

from .constants import WIDTH, NEON_CYAN, NEON_GREEN, NEON_YELLOW


def draw_hud(surface, font, score, lives, wave):
    score_text = font.render(f"SCORE: {score}", True, NEON_YELLOW)
    surface.blit(score_text, (15, 10))

    wave_text = font.render(f"WAVE {wave}", True, NEON_GREEN)
    surface.blit(wave_text, (WIDTH // 2 - wave_text.get_width() // 2, 10))

    lives_text = font.render("LIVES:", True, NEON_CYAN)
    surface.blit(lives_text, (WIDTH - 180, 10))
    for i in range(lives):
        lx = WIDTH - 100 + i * 25
        ly = 18
        pts = [(lx, ly - 8), (lx + 8, ly + 6), (lx - 8, ly + 6)]
        pygame.draw.lines(surface, NEON_CYAN, True, pts, 1)
