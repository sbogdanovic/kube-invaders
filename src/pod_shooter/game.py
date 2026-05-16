import math
import random
import sys
import time

import pygame

from .alien import Alien
from .bullet import Bullet
from .constants import (
    ALIEN_COLORS,
    ALIEN_DROP,
    BG_COLOR,
    FPS,
    HEIGHT,
    NEON_CYAN,
    NEON_GREEN,
    NEON_MAGENTA,
    NEON_RED,
    NEON_WHITE,
    NEON_YELLOW,
    WIDTH,
    ASSET_MUSIC_MENU,
    ASSET_MUSIC_GAME,
    ASSET_HIT_ENEMY_1,
    ASSET_HIT_ENEMY_3,
    ASSET_PLAYER_EXPLODE,
    ASSET_PLAYER_HIT,
    ASSET_PLAYER_DIED,
    ASSET_LIFE_LOSE,
)
from .damagetext import DamageText
from .font import PixelFont
from .hud import draw_hud
from .particle import Particle
from .player import Player
from .shield import Shield
from .starfield import Starfield

ALIEN_FAIL_LINE_Y = HEIGHT - 50

COUNTDOWN_DURATION = 4.0
COUNTDOWN_STEPS = [
    (0.0, 1.0, 3),
    (1.0, 2.0, 2),
    (2.0, 3.0, 1),
    (3.0, 4.0, "GO!"),
]

GAMEOVER_MUSIC_DELAY = 3.0
SHIELD_POSITIONS = [
    (WIDTH // 5, HEIGHT - 120),
    (2 * WIDTH // 5, HEIGHT - 120),
    (3 * WIDTH // 5, HEIGHT - 120),
    (4 * WIDTH // 5, HEIGHT - 120),
]


# ---------------------------------------------------------------------------
# Sound Manager
# ---------------------------------------------------------------------------


class SoundManager:
    """Centralises all sound effect loading and music playback."""

    _EFFECTS = {
        "hit": ASSET_HIT_ENEMY_1,
        "explode": ASSET_HIT_ENEMY_3,
        "player_explode": ASSET_PLAYER_EXPLODE,
        "player_died": ASSET_PLAYER_DIED,
        "player_hit": ASSET_PLAYER_HIT,
        "life_lose": ASSET_LIFE_LOSE,
    }

    _MUSIC = {
        "menu": ASSET_MUSIC_MENU,
        "game": ASSET_MUSIC_GAME,
    }

    def __init__(self):
        pygame.mixer.init()
        self._sounds: dict[str, pygame.mixer.Sound | None] = {}
        for name, path in self._EFFECTS.items():
            try:
                self._sounds[name] = pygame.mixer.Sound(path)
            except Exception:
                self._sounds[name] = None
        self._current_music: str | None = None

    def play(self, name: str) -> None:
        snd = self._sounds.get(name)
        if snd:
            snd.play()

    def play_music(self, which: str) -> None:
        if self._current_music == which:
            return
        self._current_music = which
        path = self._MUSIC.get(which)
        if not path:
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"[WARN] Could not play music: {e}")

    @staticmethod
    def fadeout_music(ms: int = 400) -> None:
        try:
            pygame.mixer.music.fadeout(ms)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ease_toward(
    current: float, target: float, speed: float, dt: float, snap_threshold: float = 0.01
) -> float:
    """Exponential ease *current* toward *target*.  Snaps when close enough."""
    current += (target - current) * speed * dt
    if abs(current - target) < snap_threshold:
        return target
    return current


def _pulse_value(lo: int = 128, hi: int = 255, freq: float = 3.0) -> int:
    return int(lo + (hi - lo) * (0.5 + 0.5 * math.sin(time.time() * freq)))


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pod Invaders")
        self.clock = pygame.time.Clock()

        self.font = PixelFont("monospace", 18)
        self.big_font = PixelFont("monospace", 36)
        self.small_font = PixelFont("monospace", 14)

        self.sound = SoundManager()
        self.starfield = Starfield()

        self._init_gameover_anim()
        self.reset()
        self.sound.play_music("menu")

    # -- Initialisation helpers --------------------------------------------

    def _init_gameover_anim(self):
        self._gameover_zoom = 1.0
        self._gameover_fade = 0.0
        self._gameover_text_alpha = 0.0
        self._gameover_text_zoom = 1.0
        self._gameover_music_delay = 0.0
        self._gameover_music_started = True

    def reset(self):
        self.player = Player()
        self.player.y = HEIGHT - 60
        self._player_respawn_timer = 0.0
        self._player_blink_timer = 0.0

        self.bullets: list[Bullet] = []
        self.aliens: list[Alien] = []
        self.particles: list[Particle] = []
        self.shields: list[Shield] = []
        self.damagetexts: list[DamageText] = []

        self.score = 0
        self.lives = 3
        self.wave = 0
        self.alien_dir = 1
        self.alien_speed = 0.5
        self.alien_shoot_timer = 0.0
        self.dive_timer = 0.0

        self.state = "title"
        self.wave_msg_timer = 0.0

        self._countdown_timer = 0.0
        self._countdown_state = None
        self._countdown_anim = 0.0
        self._formation_bottom_y = 0.0

        self.spawn_wave()

    # -- State transitions -------------------------------------------------

    def _start_playing(self):
        self.state = "playing"
        self._gameover_zoom = 1.0
        self._gameover_fade = 0.0
        self.sound.play_music("game")

    def _start_game_over(self):
        self.state = "game_over"
        self.player.alive = False
        self._gameover_zoom = 1.4
        self._gameover_fade = 0.0
        self._gameover_text_alpha = 0.0
        self._gameover_text_zoom = 1.25
        self._gameover_music_delay = GAMEOVER_MUSIC_DELAY
        self._gameover_music_started = False

    # -- Wave / spawning ---------------------------------------------------

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
                self.aliens.append(Alien(80 + col * 55, 60 + row * 45, shape, color))

        self.shields = [Shield(x, y) for x, y in SHIELD_POSITIONS]

        self.wave_msg_timer = 0.0
        self.dive_timer = random.uniform(4.0, 7.0)
        self._countdown_timer = COUNTDOWN_DURATION
        self._countdown_anim = 0.0
        self._formation_bottom_y = (
            max(a.y + a.h // 2 for a in self.aliens) if self.aliens else 0.0
        )

    def spawn_explosion(self, x, y, color, count=15):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    # -- Main loop ---------------------------------------------------------

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            self._dt = dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)

            self.starfield.update()

            if self.state == "title":
                self.sound.play_music("menu")
            elif self.state == "playing" and self._countdown_timer > 0.0:
                self._update_countdown(dt)
            elif self.state == "playing":
                self._update_gameplay(dt)
            elif self.state == "game_over":
                self._update_game_over_anim(dt)

            self.draw()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def _handle_key(self, key):
        if self.state == "title":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_playing()
        elif self.state == "game_over":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.reset()
                self._start_playing()
        elif self.state == "playing" and self._countdown_timer <= 0.0:
            if key == pygame.K_SPACE:
                b = self.player.shoot()
                if b:
                    self.bullets.append(b)

    # -- Countdown ---------------------------------------------------------

    def _update_countdown(self, dt):
        self._countdown_timer -= dt
        elapsed = COUNTDOWN_DURATION - self._countdown_timer

        # Animate aliens (visual only -- no shooting or diving)
        for a in self.aliens:
            a.update(dt)

        # Center and blink player during countdown
        self.player.x = WIDTH // 2
        self._player_blink_timer += dt

        # Determine which countdown symbol to show
        self._countdown_state = None
        for start, end, label in COUNTDOWN_STEPS:
            if start <= elapsed < end:
                self._countdown_state = label
                self._countdown_anim = elapsed - start
                break

        if elapsed >= COUNTDOWN_DURATION:
            self._countdown_state = None
            self._player_blink_timer = 0.0

    # -- Game-over animation -----------------------------------------------

    def _update_game_over_anim(self, dt):
        self._gameover_zoom = _ease_toward(self._gameover_zoom, 1.25, 1.1, dt, 0.001)
        self._gameover_fade = _ease_toward(self._gameover_fade, 1.0, 0.85, dt)
        self._gameover_text_alpha = _ease_toward(
            self._gameover_text_alpha, 1.0, 1.7, dt
        )
        self._gameover_text_zoom = _ease_toward(self._gameover_text_zoom, 1.0, 2.2, dt)

        if not self._gameover_music_started:
            self._gameover_music_delay -= dt
            if self._gameover_music_delay <= 0.0:
                self.sound.play_music("menu")
                self._gameover_music_started = True

    # -- Gameplay update ---------------------------------------------------

    def _update_gameplay(self, dt):
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        self.starfield.update()

        if self.wave_msg_timer > 0:
            self.wave_msg_timer -= dt

        self._update_bullets()
        self._update_alien_formation(dt)
        self._update_dives(dt)
        self._update_alien_shooting(dt)
        self._check_bullet_alien_collisions()
        self._check_bullet_player_collisions(dt)
        self._check_bullet_shield_collisions()
        self._check_formation_breach()
        self._update_blink_timer(dt)
        self._prune_dead_entities(dt)

        if not self.aliens and self.state == "playing":
            self.spawn_wave()

    def _update_bullets(self):
        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.alive]

    def _update_alien_formation(self, dt):
        move_down = False
        for a in self.aliens:
            a.update(dt)
            if (
                self._countdown_timer <= 0.0
                and getattr(a, "_dive_bullet", None) is not None
            ):
                self.bullets.append(a._dive_bullet)
                a._dive_bullet = None
            a.x += self.alien_speed * self.alien_dir

        for a in self.aliens:
            if a.alive and not a.diving:
                if a.x + a.w // 2 >= WIDTH - 10 or a.x - a.w // 2 <= 10:
                    move_down = True
                    break

        if move_down:
            self.alien_dir *= -1
            for a in self.aliens:
                a.y += ALIEN_DROP

    def _update_alien_shooting(self, dt):
        self.alien_shoot_timer -= dt
        if self.alien_shoot_timer > 0 or not self.aliens:
            return
        self.alien_shoot_timer = max(0.3, 1.5 - self.wave * 0.08)
        living = [a for a in self.aliens if a.alive]
        if living:
            self.bullets.append(random.choice(living).shoot())

    # -- Collision subsystems ----------------------------------------------

    def _check_bullet_alien_collisions(self):
        for b in self.bullets:
            if b.is_alien or not b.alive:
                continue
            for a in self.aliens:
                if not a.alive or not b.rect.colliderect(a.rect):
                    continue
                b.alive = False
                killed = a.hit()
                pct = int(100 / a.MAX_HEALTH)

                self.sound.play("hit")
                self.damagetexts.append(
                    DamageText(
                        a.draw_x + a.w // 2 + 12,
                        a.draw_y - a.h // 2,
                        f"-{pct}%",
                        a.color,
                    )
                )

                if killed:
                    self.sound.play("explode")
                    self.score += 100
                    self.spawn_explosion(a.draw_x, a.draw_y, a.color, 20)
                else:
                    self.score += 20
                    self.spawn_explosion(a.draw_x, a.draw_y, a.color, 5)
                break

    def _check_bullet_player_collisions(self, dt):
        # Respawn logic
        if not self.player.alive and self.lives > 0:
            if self._player_respawn_timer == 0.0:
                self._player_respawn_timer = 2.0
            else:
                self._player_respawn_timer -= dt
                if self._player_respawn_timer <= 0.0:
                    self.player.alive = True
                    self._player_blink_timer = 3.0
                    self._player_respawn_timer = 0.0
            return

        if not self.player.alive:
            return

        for b in self.bullets:
            if not b.is_alien or not b.alive:
                continue
            if self._player_blink_timer > 0.0:
                continue
            if not b.rect.colliderect(self.player.rect):
                continue

            b.alive = False
            self.lives -= 1
            self.spawn_explosion(self.player.x, self.player.y, NEON_CYAN, 25)

            if self.lives <= 0:
                self.sound.fadeout_music()
                self.sound.play("player_died")
                self._start_game_over()
            else:
                self.sound.play("life_lose")
                self.sound.play("player_hit")
                self.player.alive = False
                self._player_respawn_timer = 2.0
            break

    def _check_bullet_shield_collisions(self):
        for b in self.bullets:
            if not b.alive:
                continue
            for s in self.shields:
                if s.alive and b.rect.colliderect(s.rect):
                    b.alive = False
                    s.health -= 1
                    self.spawn_explosion(b.x, b.y, NEON_GREEN, 5)
                    break

    def _check_formation_breach(self):
        formation_aliens = [a for a in self.aliens if a.alive and not a.diving]
        if formation_aliens:
            self._formation_bottom_y = max(
                max(pt[1] for pt in a.get_outline()) for a in formation_aliens
            )
        if self._formation_bottom_y >= ALIEN_FAIL_LINE_Y:
            self._start_game_over()

    def _update_blink_timer(self, dt):
        if self._player_blink_timer > 0.0:
            self._player_blink_timer -= dt

    def _prune_dead_entities(self, dt):
        self.aliens = [a for a in self.aliens if a.alive]
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]
        for t in self.damagetexts:
            t.update(dt)
        self.damagetexts = [t for t in self.damagetexts if t.alive]

    # -- Dive sorties ------------------------------------------------------

    def _update_dives(self, dt):
        self.dive_timer -= dt
        if self.dive_timer > 0:
            return
        self.dive_timer = random.uniform(3.0, 6.0)

        available = [a for a in self.aliens if a.alive and not a.diving]
        if len(available) < 2:
            return

        # Pick a shape with at least 2 members
        shapes = list({a.shape for a in available})
        random.shuffle(shapes)
        group = None
        for shape in shapes:
            candidates = [a for a in available if a.shape == shape]
            if len(candidates) >= 2:
                group = candidates[: random.randint(2, min(4, len(candidates)))]
                break
        if not group:
            return

        path = self._generate_dive_path()
        for i, alien in enumerate(group):
            delayed_path = [(0, 0)] * (1 + i) + path[1:]
            alien.start_dive(delayed_path)

    @staticmethod
    def _generate_dive_path():
        direction = random.choice([-1, 1])
        sx = random.uniform(60, 140) * direction
        sy = random.uniform(80, 180)
        return [
            (0, 0),
            (sx * 0.3, -30),
            (sx * 0.7, sy * 0.4),
            (sx, sy),
            (sx * 0.8, sy * 1.2),
            (sx * 0.3, sy * 0.8),
            (-sx * 0.2, sy * 0.3),
            (0, 0),
        ]

    # -- Draw --------------------------------------------------------------

    def draw(self):
        if self.state == "game_over":
            self._draw_game_over_screen()
            return

        self.screen.fill(BG_COLOR)
        self.starfield.draw(self.screen)

        # ...existing code...

        if self.state == "title":
            self._draw_title()
            return

        self._draw_world(self.screen)

        if self.state == "playing" and self._countdown_state is not None:
            self._draw_countdown()

        draw_hud(self.screen, self.font, self.score, self.lives, self.wave)

    def _draw_world(self, surface):
        for s in self.shields:
            s.draw(surface)
        for a in self.aliens:
            a.draw(surface)

        if self._should_draw_player():
            self.player.draw(surface)

        for b in self.bullets:
            b.draw(surface)
        for p in self.particles:
            p.draw(surface)
        for t in self.damagetexts:
            t.draw(surface, self.small_font)

    def _should_draw_player(self) -> bool:
        if self._player_respawn_timer > 0.0:
            return False
        if self._player_blink_timer > 0.0 or (
            self.state == "playing" and self._countdown_timer > 0.0
        ):
            return (time.time() * 5) % 1.0 < 0.5
        return True

    # -- Game-over draw ----------------------------------------------------

    def _draw_game_over_screen(self):
        dt = getattr(self, "_dt", 1 / 60)

        # Animate zoom / fade
        if self._gameover_zoom > 1.01:
            self._gameover_zoom = _ease_toward(self._gameover_zoom, 1.0, 1.1, dt, 0.001)
        self._gameover_fade = _ease_toward(self._gameover_fade, 1.0, 0.85, dt)
        self._gameover_text_alpha = _ease_toward(
            self._gameover_text_alpha, 1.0, 1.7, dt
        )
        if self._gameover_text_zoom > 1.0:
            self._gameover_text_zoom = _ease_toward(
                self._gameover_text_zoom, 1.0, 2.2, dt
            )

        # Render world onto temp surface, then zoom
        base = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        base.fill(BG_COLOR)
        self.starfield.draw(base)
        self._draw_world(base)
        draw_hud(base, self.font, self.score, self.lives, self.wave)

        zoom = self._gameover_zoom
        zw, zh = int(WIDTH * zoom), int(HEIGHT * zoom)
        scaled = pygame.transform.smoothscale(base, (zw, zh))

        self.screen.fill(BG_COLOR)
        self.screen.blit(scaled, ((WIDTH - zw) // 2, (HEIGHT - zh) // 2))

        # Dark overlay
        fade = min(self._gameover_fade, 1.0)
        if fade > 0.01:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(255 * fade * 0.82)))
            self.screen.blit(overlay, (0, 0))

        self._draw_game_over_text(self._gameover_text_alpha, self._gameover_text_zoom)

    def _draw_game_over_text(self, alpha=1.0, zoom=1.0):
        pulse = _pulse_value()
        lines = [
            (self.big_font, "GAME OVER", NEON_RED),
            (self.font, f"FINAL SCORE: {self.score}", NEON_YELLOW),
            (self.font, "PRESS SPACE TO RESTART", (pulse, pulse, pulse)),
        ]

        surfaces = []
        for font, text, color in lines:
            size = (
                int(font.glyph_h * zoom) if hasattr(font, "glyph_h") else int(18 * zoom)
            )
            render_font = (
                PixelFont("monospace", size) if hasattr(font, "scale") else font
            )
            surf = render_font.render(text, True, color)
            if alpha < 1.0:
                surf = surf.copy()
                surf.set_alpha(int(255 * alpha))
            surfaces.append(surf)

        spacing = int(18 * zoom)
        total_h = sum(s.get_height() for s in surfaces) + spacing * (len(surfaces) - 1)
        y = HEIGHT // 2 - total_h // 2

        for surf in surfaces:
            rect = surf.get_rect(center=(WIDTH // 2, y + surf.get_height() // 2))
            self.screen.blit(surf, rect)
            y += surf.get_height() + spacing

    # -- Countdown draw ----------------------------------------------------

    def _draw_countdown(self):
        state = self._countdown_state
        anim = self._countdown_anim
        color = NEON_GREEN if state == "GO!" else NEON_YELLOW

        if anim < 0.4:
            progress = anim / 0.4
            ease = 1 - pow(1 - progress, 2.5)
            alpha = int(255 * ease)
            zoom = 1.8 - 0.8 * ease
        elif anim < 0.6:
            alpha = 255
            zoom = 1.0
        else:
            progress = (anim - 0.6) / 0.4
            ease = 1 - pow(1 - progress, 2.5)
            alpha = int(255 * (1 - ease))
            zoom = 1.0 + 0.4 * ease

        surf = self.big_font.render(str(state), True, color)
        zw = max(1, int(surf.get_width() * zoom))
        zh = max(1, int(surf.get_height() * zoom))
        surf = pygame.transform.smoothscale(surf, (zw, zh))
        surf.set_alpha(alpha)
        self.screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        draw_hud(self.screen, self.font, self.score, self.lives, self.wave)

        if self.wave_msg_timer > 0:
            wave_surf = self.big_font.render(f"WAVE {self.wave}", True, NEON_GREEN)
            self.screen.blit(
                wave_surf, wave_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
            )

    # -- Title draw --------------------------------------------------------

    def _draw_title(self):
        cx = WIDTH // 2

        title = self.big_font.render("POD INVADERS", True, NEON_CYAN)
        self.screen.blit(title, title.get_rect(center=(cx, HEIGHT // 3)))

        subtitle = self.font.render("NEON SPACE INVADERS", True, NEON_MAGENTA)
        self.screen.blit(subtitle, subtitle.get_rect(center=(cx, HEIGHT // 3 + 45)))

        pulse = _pulse_value()
        prompt = self.font.render(
            "PRESS SPACE TO START", True, (pulse, pulse, min(255, pulse + 50))
        )
        self.screen.blit(prompt, prompt.get_rect(center=(cx, HEIGHT * 2 // 3)))

        ctrl = self.small_font.render(
            "A/D or LEFT/RIGHT to move    SPACE to shoot", True, NEON_WHITE
        )
        self.screen.blit(ctrl, ctrl.get_rect(center=(cx, HEIGHT * 2 // 3 + 40)))

        demo = Alien(cx, HEIGHT // 2 + 10, "crab", NEON_MAGENTA)
        demo.phase = time.time() * 2
        demo.liquid.phase = time.time()
        demo.liquid.update()
        demo.draw(self.screen)
