class DamageText:
    def __init__(self, x, y, text, color, duration=0.8):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.duration = duration
        self.life = duration
        self.dy = -18  # pixels to move up over lifetime

    @property
    def alive(self):
        return self.life > 0

    def update(self, dt):
        self.life -= dt

    def draw(self, surface, font):
        pct = max(0, self.life / self.duration)
        alpha = int(255 * pct)
        y_offset = int(self.dy * (1 - pct))
        txt_surf = font.render(self.text, True, self.color)
        if txt_surf.get_alpha() is None:
            txt_surf.set_alpha(alpha)
        else:
            txt_surf = txt_surf.copy()
            txt_surf.set_alpha(alpha)
        rect = txt_surf.get_rect(center=(int(self.x), int(self.y + y_offset)))
        surface.blit(txt_surf, rect)
