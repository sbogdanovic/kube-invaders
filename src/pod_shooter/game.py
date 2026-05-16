import math
import random
import sys
import time

import pygame

from .alien import Alien
from .bullet import Bullet
from .constants import (
    ALIEN_COLORS, ALIEN_DROP, BG_COLOR, FPS, HEIGHT, NEON_CYAN, NEON_GREEN,
    NEON_MAGENTA, NEON_RED, NEON_WHITE, NEON_YELLOW, WIDTH,
)
from .font import PixelFont
from .hud import draw_hud
from .particle import Particle
from .player import Player
from .shield import Shield
from .starfield import Starfield


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pod Invaders")
        self.clock = pygame.time.Clock()
        self.font = PixelFont("monospace", 18)
        self.big_font = PixelFont("monospace", 36)
        self.small_font = PixelFont("monospace", 14)
        self.starfield = Starfield()
        self.reset()
        self._gameover_zoom = 1.0
        self._gameover_fade = 0.0
        self._gameover_text_alpha = 0.0
        self._gameover_text_zoom = 1.4
        # Music
        self._music_state = None
        from .constants import ASSET_MUSIC_MENU, ASSET_MUSIC_GAME, ASSET_HIT_ENEMY_1, ASSET_HIT_ENEMY_3, ASSET_PLAYER_EXPLODE, ASSET_PLAYER_HIT
        self._music_files = {
            'menu': ASSET_MUSIC_MENU,
            'game': ASSET_MUSIC_GAME,
        }
        pygame.mixer.init()
        self._play_music('menu')
        # Load hit sound
        try:
            self._hit_sound = pygame.mixer.Sound(ASSET_HIT_ENEMY_1)
        except Exception:
            self._hit_sound = None
        try:
            self._explode_sound = pygame.mixer.Sound(ASSET_HIT_ENEMY_3)
        except Exception:
            self._explode_sound = None
        try:
            self._player_explode_sound = pygame.mixer.Sound(ASSET_PLAYER_EXPLODE)
        except Exception:
            self._player_explode_sound = None
        try:
            self._player_hit_sound = pygame.mixer.Sound(ASSET_PLAYER_HIT)
        except Exception:
            self._player_hit_sound = None

    def _play_music(self, which):
        """Switch music track if needed."""
        if self._music_state == which:
            return
        self._music_state = which
        try:
            pygame.mixer.music.load(self._music_files[which])
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"[WARN] Could not play music: {e}")

    def reset(self):
        self.player = Player()
        self.player.y = HEIGHT - 60
        self.bullets: list[Bullet] = []
        self.aliens: list[Alien] = []
        self.particles: list[Particle] = []
        self.shields: list[Shield] = []
        self.damagetexts = []
        self.score = 0
        self.lives = 3
        self.wave = 0
        self.alien_dir = 1
        self.alien_speed = 0.5
        self.alien_shoot_timer = 0.0
        self.dive_timer = 0.0
        self.state = 'title'
        self.wave_msg_timer = 0.0
        self.spawn_wave()

    def spawn_wave(self):
        self.wave += 1
        self.aliens.clear()
        self.bullets.clear()
        rows = min(3 + self.wave // 2, 6)
        cols = min(6 + self.wave, 12)
        self.alien_speed = 0.4 + self.wave * 0.1
        self.alien_dir = 1

        for row in range(rows):
            shape = Alien.SHAPES[row % len(Alien.SHAPES)]
            color = ALIEN_COLORS[row % len(ALIEN_COLORS)]
            for col in range(cols):
                ax = 80 + col * 55
                ay = 60 + row * 45
                self.aliens.append(Alien(ax, ay, shape, color))

        self.shields = [
            Shield(WIDTH // 5, HEIGHT - 120),
            Shield(2 * WIDTH // 5, HEIGHT - 120),
            Shield(3 * WIDTH // 5, HEIGHT - 120),
            Shield(4 * WIDTH // 5, HEIGHT - 120),
        ]

        self.wave_msg_timer = 2.0
        self.dive_timer = random.uniform(4.0, 7.0)

    def spawn_explosion(self, x, y, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if self.state == 'title':
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.state = 'playing'
                            self._gameover_zoom = 1.0
                            self._gameover_fade = 0.0
                            self._play_music('game')
                    elif self.state == 'game_over':
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.reset()
                            self.state = 'playing'
                            self._gameover_zoom = 1.0
                            self._gameover_fade = 0.0
                            self._play_music('game')
                    elif self.state == 'playing':
                        if event.key == pygame.K_SPACE:
                            b = self.player.shoot()
                            if b:
                                self.bullets.append(b)

            # Always animate the starfield, even on title/game over screens
            self.starfield.update()

            # Music switching for menu/game over
            if self.state in ('title', 'game_over'):
                self._play_music('menu')


            if self.state == 'playing':
                self.update(dt)
            elif self.state == 'game_over':
                # Animate zoom/fade-out effect with easing (slower, smooth)
                if self._gameover_zoom < 1.25:
                    self._gameover_zoom += (1.25 - self._gameover_zoom) * dt * 1.1
                    if abs(self._gameover_zoom - 1.25) < 0.001:
                        self._gameover_zoom = 1.25
                if self._gameover_fade < 1.0:
                    # Ease out: fade = fade + (1 - fade) * k * dt
                    self._gameover_fade += (1.0 - self._gameover_fade) * dt * 0.85
                    if abs(self._gameover_fade - 1.0) < 0.01:
                        self._gameover_fade = 1.0
                # Fade/zoom in text with ease
                if self._gameover_text_alpha < 1.0:
                    self._gameover_text_alpha += (1.0 - self._gameover_text_alpha) * dt * 1.7
                    if abs(self._gameover_text_alpha - 1.0) < 0.01:
                        self._gameover_text_alpha = 1.0
                if self._gameover_text_zoom > 1.0:
                    self._gameover_text_zoom += (1.0 - self._gameover_text_zoom) * dt * 2.2
                    if abs(self._gameover_text_zoom - 1.0) < 0.01:
                        self._gameover_text_zoom = 1.0

            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # ----- Update logic -----

    def update(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        self.starfield.update()

        if self.wave_msg_timer > 0:
            self.wave_msg_timer -= dt

        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.alive]

        move_down = False
        for a in self.aliens:
            a.update(dt)
            # Collect dive bullets
            if hasattr(a, '_dive_bullet') and a._dive_bullet is not None:
                self.bullets.append(a._dive_bullet)
                a._dive_bullet = None
            a.x += self.alien_speed * self.alien_dir
        for a in self.aliens:
            if a.alive and not a.diving:
                edge_x = a.x + a.w // 2
                if edge_x >= WIDTH - 10 or a.x - a.w // 2 <= 10:
                    move_down = True
                    break
        if move_down:
            self.alien_dir *= -1
            for a in self.aliens:
                a.y += ALIEN_DROP

        # Trigger group dives
        self._update_dives(dt)

        self.alien_shoot_timer -= dt
        if self.alien_shoot_timer <= 0 and self.aliens:
            self.alien_shoot_timer = max(0.3, 1.5 - self.wave * 0.08)
            living = [a for a in self.aliens if a.alive]
            if living:
                shooter = random.choice(living)
                self.bullets.append(shooter.shoot())

        # Player bullets vs aliens
        for b in self.bullets:
            if b.is_alien or not b.alive:
                continue
            for a in self.aliens:
                if a.alive and b.rect.colliderect(a.rect):
                    b.alive = False
                    old_health = a.health
                    killed = a.hit()
                    removed = 1 / a.MAX_HEALTH
                    pct = int(removed * 100)
                    # Play hit sound
                    if hasattr(self, '_hit_sound') and self._hit_sound:
                        try:
                            self._hit_sound.play()
                        except Exception:
                            pass
                    # Show fading damage text next to alien
                    from .damagetext import DamageText
                    dx = a.draw_x + a.w // 2 + 12
                    dy = a.draw_y - a.h // 2
                    self.damagetexts.append(DamageText(dx, dy, f"-{pct}%", a.color))
                    if killed:
                        if hasattr(self, '_explode_sound') and self._explode_sound:
                            try:
                                self._explode_sound.play()
                            except Exception:
                                pass
                        self.score += 100
                        self.spawn_explosion(a.draw_x, a.draw_y, a.color, 20)
                    else:
                        self.score += 20
                        self.spawn_explosion(a.draw_x, a.draw_y, a.color, 5)
                    break

        # Alien bullets vs player
        if self.player.alive:
            for b in self.bullets:
                if not b.is_alien or not b.alive:
                    continue
                if b.rect.colliderect(self.player.rect):
                    b.alive = False
                    self.lives -= 1
                    # Play player explosion or hit sound
                    if self.lives <= 0:
                        if hasattr(self, '_player_explode_sound') and self._player_explode_sound:
                            try:
                                self._player_explode_sound.play()
                            except Exception:
                                pass
                    else:
                        if hasattr(self, '_player_hit_sound') and self._player_hit_sound:
                            try:
                                self._player_hit_sound.play()
                            except Exception:
                                pass
                    self.spawn_explosion(self.player.x, self.player.y, NEON_CYAN, 25)
                    if self.lives <= 0:
                        self.player.alive = False
                        self.state = 'game_over'
                    else:
                        self.player.x = WIDTH // 2

        # Bullets vs shields
        for b in self.bullets:
            if not b.alive:
                continue
            for s in self.shields:
                if s.alive and b.rect.colliderect(s.rect):
                    b.alive = False
                    s.health -= 1
                    self.spawn_explosion(b.x, b.y, NEON_GREEN, 5)
                    break

        # Aliens reaching bottom
        for a in self.aliens:
            if a.alive and a.draw_y + a.h // 2 >= HEIGHT - 50:
                self.state = 'game_over'
                self.player.alive = False
                break

        self.aliens = [a for a in self.aliens if a.alive]

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]
        for t in self.damagetexts:
            t.update(dt)
        self.damagetexts = [t for t in self.damagetexts if t.alive]

        if not self.aliens and self.state == 'playing':
            self.spawn_wave()

    def _update_dives(self, dt):
        """Occasionally send a group of same-shape aliens on a dive sortie."""
        self.dive_timer -= dt
        if self.dive_timer > 0:
            return

        # Cooldown before next dive
        self.dive_timer = random.uniform(3.0, 6.0)

        # Pick aliens that aren't already diving
        available = [a for a in self.aliens if a.alive and not a.diving]
        if len(available) < 2:
            return

        # Pick a random shape that has at least 2 members
        shapes_present = list({a.shape for a in available})
        random.shuffle(shapes_present)
        group = None
        for shape in shapes_present:
            candidates = [a for a in available if a.shape == shape]
            if len(candidates) >= 2:
                group = candidates[:random.randint(2, min(4, len(candidates)))]
                break

        if not group:
            return

        # Generate a swooping dive path (offsets from formation position)
        # Path: swoop down and to one side, loop, return to (0,0)
        direction = random.choice([-1, 1])
        swoop_x = random.uniform(60, 140) * direction
        swoop_y = random.uniform(80, 180)

        path = [
            (0, 0),
            (swoop_x * 0.3, -30),                # lift up slightly
            (swoop_x * 0.7, swoop_y * 0.4),      # swoop out
            (swoop_x, swoop_y),                   # apex
            (swoop_x * 0.8, swoop_y * 1.2),      # curve down
            (swoop_x * 0.3, swoop_y * 0.8),      # curve back
            (-swoop_x * 0.2, swoop_y * 0.3),     # overshoot slightly
            (0, 0),                                # return to formation
        ]

        for i, alien in enumerate(group):
            # Stagger start slightly by offsetting early waypoints
            delayed_path = [(0, 0)] * (1 + i) + path[1:]
            alien.start_dive(delayed_path)

    # ----- Draw -----

    def draw(self):
        # For zoom/fade effect, draw everything to a temp surface first
        if self.state == 'game_over' and (self._gameover_zoom > 1.01 or self._gameover_fade > 0.01):
            base = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            base.fill(BG_COLOR)
            self.starfield.draw(base)
            for s in self.shields:
                s.draw(base)
            for a in self.aliens:
                a.draw(base)
            self.player.draw(base)
            for b in self.bullets:
                b.draw(base)
            for p in self.particles:
                p.draw(base)
            for t in self.damagetexts:
                t.draw(base, self.small_font)
            draw_hud(base, self.font, self.score, self.lives, self.wave)
            # Zoom and fade
            zoom = min(self._gameover_zoom, 1.25)
            fade = min(self._gameover_fade, 1.0)
            zw, zh = int(WIDTH * zoom), int(HEIGHT * zoom)
            surf = pygame.transform.smoothscale(base, (zw, zh))
            # Center zoomed surface
            x = (WIDTH - zw) // 2
            y = (HEIGHT - zh) // 2
            self.screen.fill(BG_COLOR)
            self.screen.blit(surf, (x, y))
            # Fade overlay
            if fade > 0.01:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, int(255 * fade * 0.82)))
                self.screen.blit(overlay, (0, 0))
            # Fade in GAME OVER and text
            self._draw_game_over(fade_in_alpha=self._gameover_text_alpha, zoom=self._gameover_text_zoom)
            return

        # Normal draw
        self.screen.fill(BG_COLOR)
        self.starfield.draw(self.screen)

        if self.state == 'title':
            self._draw_title()
            return

        for s in self.shields:
            s.draw(self.screen)
        for a in self.aliens:
            a.draw(self.screen)
        self.player.draw(self.screen)
        for b in self.bullets:
            b.draw(self.screen)
        for p in self.particles:
            p.draw(self.screen)
        for t in self.damagetexts:
            t.draw(self.screen, self.small_font)

        draw_hud(self.screen, self.font, self.score, self.lives, self.wave)

        if self.wave_msg_timer > 0:
            wave_text = self.big_font.render(f"WAVE {self.wave}", True,
                                              (*NEON_GREEN[:3],))
            rect = wave_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            self.screen.blit(wave_text, rect)

        if self.state == 'game_over':
            self._draw_game_over()

    def _draw_title(self):
        title = self.big_font.render("POD SHOOTER 2", True, NEON_CYAN)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

        subtitle = self.font.render("NEON SPACE INVADERS", True, NEON_MAGENTA)
        self.screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 3 + 45)))

        pulse = int(128 + 127 * math.sin(time.time() * 3))
        prompt_col = (pulse, pulse, min(255, pulse + 50))
        prompt = self.font.render("PRESS SPACE TO START", True, prompt_col)
        self.screen.blit(prompt, prompt.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3)))

        ctrl1 = self.small_font.render("A/D or LEFT/RIGHT to move    SPACE to shoot", True, NEON_WHITE)
        self.screen.blit(ctrl1, ctrl1.get_rect(center=(WIDTH // 2, HEIGHT * 2 // 3 + 40)))

        demo = Alien(WIDTH // 2, HEIGHT // 2 + 10, 'crab', NEON_MAGENTA)
        demo.phase = time.time() * 2
        demo.liquid.phase = time.time()
        demo.liquid.update()
        demo.draw(self.screen)

    def _draw_game_over(self, fade_in_alpha=1.0, zoom=1.0):
        # Overlay is now handled in draw()
        def with_alpha_and_zoom(surf, alpha, zoom, center):
            if surf.get_alpha() is None:
                surf = surf.copy()
            surf.set_alpha(int(255 * alpha))
            if abs(zoom - 1.0) > 0.01:
                zw = max(1, int(surf.get_width() * zoom))
                zh = max(1, int(surf.get_height() * zoom))
                surf = pygame.transform.smoothscale(surf, (zw, zh))
            rect = surf.get_rect(center=center)
            return surf, rect

        go_text = self.big_font.render("GAME OVER", True, NEON_RED)
        surf, rect = with_alpha_and_zoom(go_text, fade_in_alpha, zoom, (WIDTH // 2, HEIGHT // 2 - 30))
        self.screen.blit(surf, rect)

        score_text = self.font.render(f"FINAL SCORE: {self.score}", True, NEON_YELLOW)
        surf, rect = with_alpha_and_zoom(score_text, fade_in_alpha, zoom, (WIDTH // 2, HEIGHT // 2 + 20))
        self.screen.blit(surf, rect)

        pulse = int(128 + 127 * math.sin(time.time() * 3))
        prompt = self.font.render("PRESS SPACE TO RESTART", True, (pulse, pulse, pulse))
        surf, rect = with_alpha_and_zoom(prompt, fade_in_alpha, zoom, (WIDTH // 2, HEIGHT // 2 + 60))
        self.screen.blit(surf, rect)
