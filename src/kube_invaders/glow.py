import pygame


def _bbox(points, pad=0):
    """Return (min_x, min_y, max_x, max_y) bounding box for a list of points."""
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def draw_glow_lines(surface, color, closed, points, width=2, glow_layers=4):
    """Draw lines with a neon glow effect using a small bounding-box surface."""
    max_expand = width + glow_layers * 3
    pad = max_expand + 2
    bx1, by1, bx2, by2 = _bbox(points, pad)
    sw = int(bx2 - bx1) + 1
    sh = int(by2 - by1) + 1
    if sw < 1 or sh < 1:
        return
    tmp = pygame.Surface((sw, sh), pygame.SRCALPHA)
    local = [(p[0] - bx1, p[1] - by1) for p in points]
    for i in range(glow_layers, 0, -1):
        alpha = max(20, 60 // i)
        w = width + i * 3
        c = (*color[:3], alpha)
        pygame.draw.lines(tmp, c, closed, local, w)
    pygame.draw.lines(tmp, color, closed, local, width)
    surface.blit(tmp, (bx1, by1))


def draw_glow_circle(surface, color, center, radius, width=0, glow_layers=4):
    pad = radius + glow_layers * 2 + 2
    sz = int(pad * 2)
    tmp = pygame.Surface((sz, sz), pygame.SRCALPHA)
    lc = (int(pad), int(pad))
    for i in range(glow_layers, 0, -1):
        alpha = max(15, 50 // i)
        r = radius + i * 2
        c = (*color[:3], alpha)
        pygame.draw.circle(tmp, c, lc, r, 0)
    pygame.draw.circle(tmp, color, lc, radius, width)
    surface.blit(tmp, (center[0] - int(pad), center[1] - int(pad)))


def draw_glow_rect(surface, color, rect, width=1, glow_layers=3):
    pad = glow_layers * 4 + 2
    ox, oy = rect.x - pad, rect.y - pad
    sw = rect.w + pad * 2
    sh = rect.h + pad * 2
    tmp = pygame.Surface((sw, sh), pygame.SRCALPHA)
    for i in range(glow_layers, 0, -1):
        alpha = max(15, 50 // i)
        c = (*color[:3], alpha)
        expanded = rect.inflate(i * 4, i * 4).move(-ox, -oy)
        pygame.draw.rect(tmp, c, expanded, width)
    local_rect = rect.move(-ox, -oy)
    pygame.draw.rect(tmp, color, local_rect, width)
    surface.blit(tmp, (ox, oy))
