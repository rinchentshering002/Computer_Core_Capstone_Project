"""
memory_monastery.py — Act IV: The Memory Monastery
"""

import pygame
import math
import os
import random
import story_state
import sound_system
from setting import (WIDTH, HEIGHT, font, small_font, location_font,
                     WHITE, GOLD)


_ROOT = os.path.dirname(os.path.abspath(__file__))


def _asset(*parts):
    return os.path.join(_ROOT, *parts)


# =========================================================
# FLAGS
# =========================================================
FLAG_ENTERED     = "monastery_entered"
FLAG_PUZZLE_DONE = "monastery_puzzle_done"
FLAG_DAWA_PLAYED = "monastery_dawa_played"
FLAG_DRUKMA_SEEN = "monastery_drukma_fragment_seen"
FLAG_REVEAL_SEEN = "monastery_reveal_seen"
FLAG_DONE        = "monastery_done"


# =========================================================
# LAYOUT
# =========================================================
EXIT_RECT     = pygame.Rect(60, 400, 120, 80)
TERMINAL_RECT = pygame.Rect(540, 380, 100, 110)


WALLS = [
    pygame.Rect(0, 0, WIDTH, 60),
    pygame.Rect(0, 0, 40, HEIGHT),
    pygame.Rect(WIDTH - 40, 0, 40, HEIGHT),
    pygame.Rect(0, HEIGHT - 40, WIDTH, 40),
]


PILLAR_POSITIONS = [120, 300, 700, 880]
LANTERN_POSITIONS = [220, 500, 780]


# =========================================================
# PUZZLE DATA
# =========================================================
MEMORY_ITEMS = [
    ("A column of numbers\nbeing added right now",       "RAM"),
    ("The instructions\nthat wake the machine",          "ROM"),
    ("An open document\nnot yet saved",                   "RAM"),
    ("The machine's\nfirmware identifier",               "ROM"),
    ("Unsaved edits\nin a text field",                    "RAM"),
    ("The device's\nboot sequence",                       "ROM"),
]

CHAMBERS = ["RAM", "ROM"]


DAWA_RECORDING = [
    ("A holographic figure of an old archivist shimmers above the shrine.", None),
    ("I am Dawa. Guardian of Memory.", "Dawa_Recording"),
    ("Storage keeps what must survive forever.", "Dawa_Recording"),
    ("But Memory is different.", "Dawa_Recording"),
    ("Some things are held for a moment, then released.", "Dawa_Recording"),
    ("Others are written into the machine itself,", "Dawa_Recording"),
    ("and remain even when the power is gone.", "Dawa_Recording"),
    ("A system that confuses the two", "Dawa_Recording"),
    ("will either forget what it needs,", "Dawa_Recording"),
    ("or keep what it should let go.", "Dawa_Recording"),
    ("Something here remembers too much.", "Dawa_Recording"),
    ("The hologram fades.", None),
]


DRUKMA_FRAGMENT = [
    ("Drukma's glow flickers.", None),
    ("Drukma: I... remember this chamber.", "Drukma"),
    ("You: You have been here before?", "You"),
    ("Drukma: I do not know. I remember the sound of the machines.", "Drukma"),
    ("Drukma: I remember someone asking whether a memory", "Drukma"),
    ("Drukma: could survive after the person it described was gone.", "Drukma"),
    ("A distant, distorted voice plays through the shrine.", None),
    ("Unknown Voice: Preserving information is not the same", "Unknown"),
    ("Unknown Voice: as preserving the person it describes.", "Unknown"),
    ("Drukma is silent for a long moment.", None),
    ("Drukma: ...I think I was there.", "Drukma"),
]


# =========================================================
# RUNTIME STATE
# =========================================================
class _RT:
    puzzle_open          = False
    puzzle_index         = 0
    puzzle_button        = 0
    wrong_flash          = 0
    correct_flash        = 0
    dawa_open            = False
    dawa_index           = 0
    dawa_just_opened     = False
    drukma_open          = False
    drukma_index         = 0
    drukma_just_opened   = False
    reveal_open          = False
    reveal_timer         = 0
    toast_text           = ""
    toast_timer          = 0
    shrine_pulse         = 0.0
    particles            = []

RT = _RT()


# =========================================================
# HELPERS
# =========================================================
def _flag(k, d=False):
    return story_state.STATE.get_flag(k, d)


def _set(k, v=True):
    story_state.STATE.set_flag(k, v)


def _player_in(rect, inflate=20):
    from player import player
    return player.colliderect(rect.inflate(inflate, inflate))


def is_blocking_input():
    return (RT.puzzle_open or RT.dawa_open or
            RT.drukma_open or RT.reveal_open)


def build_collisions():
    walls = list(WALLS)
    walls.append(TERMINAL_RECT.inflate(20, 20))
    return walls


def _toast(text, duration=200):
    RT.toast_text = text
    RT.toast_timer = duration


# =========================================================
# ASSET LOADING
# =========================================================
def _scale_fit(surface, max_w, max_h):
    w, h = surface.get_size()
    if w == 0 or h == 0:
        return surface
    scale = min(max_w / w, max_h / h)
    return pygame.transform.smoothscale(
        surface, (max(1, int(w * scale)), max(1, int(h * scale))))


def _cover_fit(surface, target_w, target_h):
    w, h = surface.get_size()
    if w == 0 or h == 0:
        return pygame.Surface((target_w, target_h), pygame.SRCALPHA)
    scale = max(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    scaled = pygame.transform.smoothscale(surface, (new_w, new_h))
    cx, cy = (new_w - target_w) // 2, (new_h - target_h) // 2
    cropped = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
    cropped.blit(scaled, (0, 0), pygame.Rect(cx, cy, target_w, target_h))
    return cropped


def _strip_white(surface, tolerance=18):
    surface = surface.convert_alpha()
    w, h = surface.get_size()
    for x in range(w):
        for y in range(h):
            r, g, b, a = surface.get_at((x, y))
            if a < 20:
                continue
            if (r > 255 - tolerance and g > 255 - tolerance
                    and b > 255 - tolerance):
                surface.set_at((x, y), (0, 0, 0, 0))
    return surface


def _load(path):
    if not os.path.isfile(path):
        print(f"  [MISS] {os.path.relpath(path, _ROOT)}")
        return None
    try:
        img = pygame.image.load(path)
        print(f"  [OK]   {os.path.relpath(path, _ROOT)}  → {img.get_size()}")
        return img
    except pygame.error as e:
        print(f"  [FAIL] {os.path.relpath(path, _ROOT)}  ({e})")
        return None


print("=== Loading Memory Monastery assets ===")

# --- Scene ---
_raw_bg = _load(_asset("assets", "environment", "ruins", "memory_monastery_bg.png"))
MONASTERY_BG = _cover_fit(_raw_bg, WIDTH, HEIGHT) if _raw_bg else None

_raw_pillar = _load(_asset("assets", "environment", "ruins", "monastery_pillar.png"))
PILLAR_IMG = (_scale_fit(_strip_white(_raw_pillar, tolerance=15), 100, 420)
              if _raw_pillar else None)

_raw_lantern = _load(_asset("assets", "environment", "ruins", "monastery_lantern.png"))
LANTERN_IMG = (_scale_fit(_strip_white(_raw_lantern, tolerance=15), 80, 80)
               if _raw_lantern else None)

_raw_tile = _load(_asset("assets", "environment", "ruins", "monastery_floor_tile.png"))
FLOOR_TILE = _scale_fit(_raw_tile, 96, 96) if _raw_tile else None

_raw_shrine = _load(_asset("assets", "environment", "ruins", "memory_shrine.png"))
SHRINE_IMG = (_scale_fit(_strip_white(_raw_shrine, tolerance=18), 160, 200)
              if _raw_shrine else None)

# --- Puzzle overlay ---
_raw_panel = _load(_asset("assets", "environment", "ruins", "monastery_panel.png"))
PANEL_IMG = (_scale_fit(_strip_white(_raw_panel, tolerance=15), 760, 560)
             if _raw_panel else None)

_raw_ram = _load(_asset("assets", "environment", "ruins", "ram_icon.png"))
RAM_ICON = (_scale_fit(_strip_white(_raw_ram, tolerance=15), 128, 128)
            if _raw_ram else None)

_raw_rom = _load(_asset("assets", "environment", "ruins", "rom_icon.png"))
ROM_ICON = (_scale_fit(_strip_white(_raw_rom, tolerance=15), 128, 128)
            if _raw_rom else None)

# --- FX ---
_raw_burst = _load(_asset("assets", "environment", "ruins", "correct_burst.png"))
BURST_IMG = (_scale_fit(_strip_white(_raw_burst, tolerance=15), 300, 300)
             if _raw_burst else None)

_raw_particle = _load(_asset("assets", "environment", "ruins", "memory_particle.png"))
PARTICLE_IMG = (_scale_fit(_strip_white(_raw_particle, tolerance=15), 24, 24)
                if _raw_particle else None)

# --- Hologram ---
_raw_dawa = _load(_asset("assets", "environment", "ruins", "dawa_holo.png"))
DAWA_IMG = (_scale_fit(_strip_white(_raw_dawa, tolerance=22), 220, 300)
            if _raw_dawa else None)

print("=== Monastery assets loaded ===\n")


# =========================================================
# EVENT HANDLER
# =========================================================
def handle_event(event):
    if event.type != pygame.KEYDOWN:
        return False

    if RT.dawa_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
            _advance_dawa()
        return True

    if RT.drukma_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
            _advance_drukma()
        return True

    if RT.reveal_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            RT.reveal_open = False
            _set(FLAG_REVEAL_SEEN, True)
            _set(FLAG_DONE, True)
            try:
                story_state.STATE.add_fragment("fragment_memory_duplicate")
            except Exception:
                pass
            try:
                import drukma_commentary
                drukma_commentary.trigger("memory_duplicate_found")
            except Exception:
                pass
        return True

    if RT.puzzle_open:
        if event.key in (pygame.K_LEFT, pygame.K_a):
            RT.puzzle_button = (RT.puzzle_button - 1) % 2
            sound_system.play("blip")
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            RT.puzzle_button = (RT.puzzle_button + 1) % 2
            sound_system.play("blip")
        elif event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            _check_puzzle_answer()
        elif event.key == pygame.K_ESCAPE:
            RT.puzzle_open = False
            RT.puzzle_index = 0
            RT.puzzle_button = 0
            sound_system.play("ui_close")
        return True

    if event.key == pygame.K_e:
        if _player_in(TERMINAL_RECT, 40) and not _flag(FLAG_PUZZLE_DONE):
            RT.puzzle_open = True
            RT.puzzle_index = 0
            RT.puzzle_button = 0
            RT.wrong_flash = 0
            RT.correct_flash = 0
            sound_system.play("ui_open")
            return True
        if _player_in(EXIT_RECT, 40):
            import main as _main
            if not _main.is_fading():
                if _flag(FLAG_DONE):
                    _main.start_fade_out("storage_vault")
                else:
                    _main.start_fade_out("village")
            return True

    return False


def _check_puzzle_answer():
    item_text, correct = MEMORY_ITEMS[RT.puzzle_index]
    chosen = CHAMBERS[RT.puzzle_button]
    if chosen == correct:
        sound_system.play("correct")
        RT.puzzle_index += 1
        RT.puzzle_button = 0
        RT.correct_flash = 30
        if RT.puzzle_index >= len(MEMORY_ITEMS):
            _set(FLAG_PUZZLE_DONE, True)
            RT.puzzle_open = False
            _toast("Memory sorted. The shrine responds.")
            _start_dawa()
    else:
        sound_system.play("wrong")
        RT.wrong_flash = 24


def _start_dawa():
    RT.dawa_open = True
    RT.dawa_index = 0
    RT.dawa_just_opened = True


def _play_dawa_voice():
    if not (0 <= RT.dawa_index < len(DAWA_RECORDING)):
        return
    text, speaker = DAWA_RECORDING[RT.dawa_index]
    if speaker is None:
        sound_system.stop_voice()
        return
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _advance_dawa():
    RT.dawa_index += 1
    if RT.dawa_index >= len(DAWA_RECORDING):
        RT.dawa_open = False
        RT.dawa_just_opened = False
        sound_system.stop_voice()
        _set(FLAG_DAWA_PLAYED, True)
        _start_drukma()
    else:
        _play_dawa_voice()


def _start_drukma():
    RT.drukma_open = True
    RT.drukma_index = 0
    RT.drukma_just_opened = True


def _play_drukma_voice():
    if not (0 <= RT.drukma_index < len(DRUKMA_FRAGMENT)):
        return
    text, speaker = DRUKMA_FRAGMENT[RT.drukma_index]
    if speaker is None:
        sound_system.stop_voice()
        return
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _advance_drukma():
    RT.drukma_index += 1
    if RT.drukma_index >= len(DRUKMA_FRAGMENT):
        RT.drukma_open = False
        RT.drukma_just_opened = False
        sound_system.stop_voice()
        _set(FLAG_DRUKMA_SEEN, True)
        RT.reveal_open = True
        RT.reveal_timer = 300
        try:
            story_state.STATE.add_fragment("fragment_drukma_origin")
        except Exception:
            pass
    else:
        _play_drukma_voice()


# =========================================================
# UPDATE
# =========================================================
def update():
    if RT.toast_timer > 0:
        RT.toast_timer -= 1
    if RT.wrong_flash > 0:
        RT.wrong_flash -= 1
    if RT.correct_flash > 0:
        RT.correct_flash -= 1

    if RT.dawa_just_opened:
        RT.dawa_just_opened = False
        _play_dawa_voice()
    if RT.drukma_just_opened:
        RT.drukma_just_opened = False
        _play_drukma_voice()

    if RT.reveal_open and RT.reveal_timer > 0:
        RT.reveal_timer -= 1

    RT.shrine_pulse += 0.05

    # --- Drifting memory particles ---
    if len(RT.particles) < 40 and random.random() < 0.25:
        RT.particles.append({
            "x": random.uniform(0, WIDTH),
            "y": random.uniform(220, HEIGHT),
            "vx": random.uniform(-0.15, 0.15),
            "vy": random.uniform(-0.25, -0.05),
            "life": 240,
            "max": 240,
            "size": random.choice([3, 4, 5]),
        })
    for p in RT.particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
    RT.particles = [p for p in RT.particles if p["life"] > 0]


# =========================================================
# DRAWING — BACKGROUND
# =========================================================
def _draw_floor_tiles(screen):
    """Tile the stone floor with FLOOR_TILE if available."""
    if not FLOOR_TILE:
        return
    tile_w = FLOOR_TILE.get_width()
    tile_h = FLOOR_TILE.get_height()
    for y in range(200, HEIGHT, tile_h):
        for x in range(0, WIDTH, tile_w):
            screen.blit(FLOOR_TILE, (x, y))


def _draw_pillars(screen):
    """Draw pillars at the four marked positions. Falls back to primitive."""
    for px in PILLAR_POSITIONS:
        if PILLAR_IMG:
            w = PILLAR_IMG.get_width()
            h = PILLAR_IMG.get_height()
            screen.blit(PILLAR_IMG, (px - w // 2, 100))
        else:
            # Fallback primitive pillar
            pygame.draw.rect(screen, (34, 40, 52),
                             (px - 30, 100, 60, HEIGHT - 140))
            pygame.draw.rect(screen, (44, 50, 62),
                             (px - 26, 120, 52, HEIGHT - 180))
            pulse = int((math.sin(RT.shrine_pulse * 0.8) + 1) * 3)
            pygame.draw.line(screen, (100 + pulse, 200 + pulse, 240),
                             (px, 130), (px, HEIGHT - 60), 2)


def _draw_lanterns(screen):
    """Draw hanging lanterns if available. Falls back to primitive."""
    for lx in LANTERN_POSITIONS:
        ly = 60 + int(math.sin(RT.shrine_pulse * 1.3 + lx) * 3)
        if LANTERN_IMG:
            # Chain
            pygame.draw.line(screen, (50, 40, 30), (lx, 0), (lx, ly), 2)
            screen.blit(LANTERN_IMG,
                        (lx - LANTERN_IMG.get_width() // 2, ly))
        else:
            pygame.draw.line(screen, (50, 40, 30), (lx, 0), (lx, ly), 2)
            pulse = int((math.sin(RT.shrine_pulse * 1.4) + 1) * 3)
            glow = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 190, 90, 40), (50, 50), 40 + pulse)
            pygame.draw.circle(glow, (255, 220, 130, 80), (50, 50), 24 + pulse)
            screen.blit(glow, (lx - 50, ly - 30))
            pygame.draw.polygon(screen, (150, 60, 40), [
                (lx - 10, ly), (lx + 10, ly), (lx + 8, ly + 22), (lx - 8, ly + 22)])
            pygame.draw.rect(screen, (255, 220, 140), (lx - 5, ly + 5, 10, 12))


def _draw_primitive_chamber(screen):
    """Fallback background if no bg image exists."""
    screen.fill((14, 22, 30))
    pygame.draw.rect(screen, (26, 40, 52), (0, 0, WIDTH, 200))
    pygame.draw.rect(screen, (18, 28, 38), (0, 200, WIDTH, HEIGHT - 200))
    for y in range(210, HEIGHT, 40):
        pygame.draw.line(screen, (28, 38, 48), (0, y), (WIDTH, y), 1)
    for x in range(0, WIDTH, 60):
        pygame.draw.line(screen, (28, 38, 48), (x, 200), (x, HEIGHT), 1)


def draw_background(screen):
    if MONASTERY_BG:
        screen.blit(MONASTERY_BG, (0, 0))
    else:
        _draw_primitive_chamber(screen)

    # Floor tiles (only if bg is missing or user wants overlay)
    if not MONASTERY_BG and FLOOR_TILE:
        _draw_floor_tiles(screen)

    _draw_pillars(screen)
    _draw_lanterns(screen)

    # Particles on top
    for p in RT.particles:
        alpha = int((p["life"] / p["max"]) * 140)
        if PARTICLE_IMG:
            sprite = PARTICLE_IMG.copy()
            sprite.set_alpha(alpha)
            screen.blit(sprite, (int(p["x"]) - sprite.get_width() // 2,
                                 int(p["y"]) - sprite.get_height() // 2))
        else:
            surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (180, 220, 240, alpha),
                               (p["size"], p["size"]), p["size"])
            screen.blit(surf, (int(p["x"]) - p["size"], int(p["y"]) - p["size"]))


def draw_shrine(screen):
    r = TERMINAL_RECT
    pulse = int((math.sin(RT.shrine_pulse) + 1) * 4)
    t = pygame.time.get_ticks() * 0.001

    # Shadow
    sh = pygame.Surface((r.width + 40, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 130), (0, 0, r.width + 40, 18))
    screen.blit(sh, (r.centerx - (r.width + 40) // 2, r.bottom - 6))

    if SHRINE_IMG:
        sprite_x = r.centerx - SHRINE_IMG.get_width() // 2
        sprite_y = r.bottom - SHRINE_IMG.get_height()
        # Glow behind
        glow = pygame.Surface((SHRINE_IMG.get_width() + 100,
                                SHRINE_IMG.get_height() + 100), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (100, 200, 240, 40 + pulse),
                            (0, 0, glow.get_width(), glow.get_height()))
        screen.blit(glow, (sprite_x - 50, sprite_y - 50))
        screen.blit(SHRINE_IMG, (sprite_x, sprite_y))
        _draw_label(screen, "MEMORY SHRINE", r.centerx, sprite_y - 24)
    else:
        # Rich primitive altar
        base = pygame.Rect(r.x - 20, r.bottom - 24, r.width + 40, 24)
        pygame.draw.rect(screen, (34, 30, 40), base)
        pygame.draw.rect(screen, (60, 52, 66), (base.x, base.y, base.width, 4))
        altar_w = r.width + 10
        altar_x = r.centerx - altar_w // 2
        pygame.draw.rect(screen, (50, 46, 58),
                         (altar_x, r.bottom - 50, altar_w, 30))
        pygame.draw.rect(screen, (66, 60, 74),
                         (altar_x, r.bottom - 50, altar_w, 4))

        float_y = r.bottom - 110 + int(math.sin(t * 1.5) * 4)
        for rad, col in [(70 + pulse, (90, 200, 240, 40)),
                         (50 + pulse, (140, 220, 250, 70)),
                         (30, (200, 240, 255, 130))]:
            glow = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, col, (rad, rad), rad)
            screen.blit(glow, (r.centerx - rad, float_y - rad))
        crystal = pygame.Surface((60, 80), pygame.SRCALPHA)
        pygame.draw.polygon(crystal, (180, 235, 255, 240), [
            (30, 0), (55, 40), (30, 80), (5, 40)])
        pygame.draw.polygon(crystal, (255, 255, 255, 255), [
            (30, 0), (55, 40), (30, 80), (5, 40)], 2)
        screen.blit(crystal, (r.centerx - 30, float_y - 40))

        _draw_label(screen, "MEMORY SHRINE", r.centerx, r.bottom + 4)


def draw_exit_marker(screen):
    r = EXIT_RECT
    pulse = int((math.sin(pygame.time.get_ticks() / 500) + 1) * 3)
    glow = pygame.Surface((r.width + 30, r.height + 30), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (255, 200, 120, 40 + pulse),
                        (0, 0, r.width + 30, r.height + 30))
    screen.blit(glow, (r.x - 15, r.y - 15))
    pygame.draw.rect(screen, (60, 45, 35), r, border_radius=6)
    pygame.draw.rect(screen, (200, 170, 90), r, 2, border_radius=6)
    label = "← DESCEND" if _flag(FLAG_DONE) else "← LEAVE"
    txt = small_font.render(label, True, WHITE)
    screen.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - 8))


# =========================================================
# DRAWING — PUZZLE OVERLAY
# =========================================================
def draw_puzzle(screen):
    if not RT.puzzle_open:
        return

    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 215))
    screen.blit(ov, (0, 0))

    panel = pygame.Rect(WIDTH // 2 - 380, 90, 760, 560)

    # Panel background — image if available, primitive otherwise
    if PANEL_IMG:
        screen.blit(PANEL_IMG, panel.topleft)
    else:
        surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, (24, 22, 28, 248), surf.get_rect(),
                         border_radius=14)
        pygame.draw.rect(surf, (16, 14, 20, 255), surf.get_rect(), 6,
                         border_radius=14)
        screen.blit(surf, panel.topleft)

    # Border — red on wrong, green on correct, gold otherwise
    if RT.wrong_flash > 0:
        t = RT.wrong_flash / 24.0
        border_col = (int(200 + 55 * t),
                      int(80 + 60 * (1 - t)), 70)
    elif RT.correct_flash > 0:
        t = RT.correct_flash / 30.0
        border_col = (int(120 + 100 * t),
                      int(200 + 40 * t),
                      int(150 + 80 * t))
    else:
        border_col = (140, 110, 60)
    pygame.draw.rect(screen, border_col, panel, 3, border_radius=14)

    # Corner studs
    for cx_, cy_ in [(panel.left + 16, panel.top + 16),
                     (panel.right - 16, panel.top + 16),
                     (panel.left + 16, panel.bottom - 16),
                     (panel.right - 16, panel.bottom - 16)]:
        pygame.draw.circle(screen, (150, 120, 60), (cx_, cy_), 5)
        pygame.draw.circle(screen, (60, 45, 25), (cx_, cy_), 3)

    # Title
    title = font.render("SORT THE MEMORY", True, (245, 220, 130))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 18))

    # Divider
    div_y = panel.y + 50
    pygame.draw.line(screen, (140, 110, 60),
                     (panel.centerx - 180, div_y),
                     (panel.centerx - 20, div_y), 1)
    pygame.draw.line(screen, (140, 110, 60),
                     (panel.centerx + 20, div_y),
                     (panel.centerx + 180, div_y), 1)
    pygame.draw.circle(screen, (200, 170, 90), (panel.centerx, div_y), 3)

    # Progress pips
    pip_y = panel.y + 74
    pip_start = panel.centerx - (6 * 26) // 2
    for i in range(len(MEMORY_ITEMS)):
        px = pip_start + i * 26 + 13
        filled = i < RT.puzzle_index
        if filled:
            pulse = int((math.sin(RT.shrine_pulse + i) + 1) * 2)
            pygame.draw.circle(screen, (100, 220, 240), (px, pip_y), 8 + pulse)
            pygame.draw.circle(screen, (220, 250, 255), (px, pip_y), 3)
        else:
            pygame.draw.circle(screen, (60, 70, 80), (px, pip_y), 6)
            pygame.draw.circle(screen, (36, 42, 50), (px, pip_y), 6, 2)

    # Item card
    item_text, correct = MEMORY_ITEMS[RT.puzzle_index]
    card = pygame.Rect(panel.centerx - 260, panel.y + 118, 520, 150)
    sh = pygame.Surface((card.width + 16, card.height + 16), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 140),
                     (8, 8, card.width, card.height), border_radius=12)
    screen.blit(sh, (card.x - 8, card.y - 8))
    pygame.draw.rect(screen, (44, 40, 48), card, border_radius=12)
    pygame.draw.rect(screen, (76, 68, 78), card, 3, border_radius=12)
    pygame.draw.rect(screen, (28, 26, 34), card.inflate(-12, -12), 1,
                     border_radius=10)

    # Carved knot
    knot_cx = card.centerx
    knot_cy = card.y + 26
    for i in range(4):
        a = math.radians(i * 90 + 45)
        x1 = knot_cx + math.cos(a) * 8
        y1 = knot_cy + math.sin(a) * 8
        x2 = knot_cx - math.cos(a) * 8
        y2 = knot_cy - math.sin(a) * 8
        pygame.draw.line(screen, (200, 170, 90), (x1, y1), (x2, y2), 2)
    pygame.draw.circle(screen, (200, 170, 90), (knot_cx, knot_cy), 3)

    # Item text
    for i, ln in enumerate(item_text.split("\n")):
        s = font.render(ln, True, (235, 225, 240))
        screen.blit(s, (card.centerx - s.get_width() // 2,
                        card.y + 54 + i * 28))

    # Two chamber buttons
    btn_w = 300
    btn_h = 160
    btn_gap = 60
    total_w = btn_w * 2 + btn_gap
    btn_y = panel.y + 300
    btn_start_x = panel.centerx - total_w // 2

    _draw_chamber_button(
        screen, btn_start_x, btn_y, btn_w, btn_h,
        "WORKING MEMORY", "RAM",
        "Held in mind only\nwhile the work is happening.",
        (100, 200, 240), (40, 90, 130),
        icon_img=RAM_ICON,
        selected=(RT.puzzle_button == 0),
    )
    _draw_chamber_button(
        screen, btn_start_x + btn_w + btn_gap, btn_y, btn_w, btn_h,
        "PERMANENT MEMORY", "ROM",
        "Written into the machine\nand kept through darkness.",
        (245, 200, 120), (110, 70, 30),
        icon_img=ROM_ICON,
        selected=(RT.puzzle_button == 1),
    )

    # Footer hint
    hint = small_font.render(
        "Some things are held for a moment. Some are written in.",
        True, (170, 190, 210))
    screen.blit(hint, (panel.centerx - hint.get_width() // 2,
                       panel.bottom - 46))

    controls = small_font.render(
        "←/→ choose  ·  [E] confirm  ·  [ESC] leave",
        True, (140, 150, 160))
    screen.blit(controls, (panel.centerx - controls.get_width() // 2,
                           panel.bottom - 22))

    # Correct answer burst
    if RT.correct_flash > 0 and BURST_IMG:
        t = RT.correct_flash / 30.0
        alpha = int(255 * t)
        scale = 1.0 + (1.0 - t) * 0.5
        w = int(BURST_IMG.get_width() * scale)
        h = int(BURST_IMG.get_height() * scale)
        burst = pygame.transform.smoothscale(BURST_IMG, (w, h))
        burst.set_alpha(alpha)
        screen.blit(burst, (panel.centerx - w // 2,
                            panel.y + 190 - h // 2))


def _draw_chamber_button(screen, x, y, w, h, title, subtitle, desc,
                          accent, accent_dark, icon_img, selected):
    rect = pygame.Rect(x, y, w, h)

    # Glow behind if selected
    if selected:
        pulse = int((math.sin(RT.shrine_pulse * 1.5) + 1) * 4)
        glow = pygame.Surface((w + 30, h + 30), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*accent, 60),
                         (0, 0, w + 30, h + 30), border_radius=18)
        pygame.draw.rect(glow, (*accent, 100),
                         (8, 8, w + 14, h + 14), border_radius=16)
        screen.blit(glow, (x - 15, y - 15))

    # Body
    pygame.draw.rect(screen, accent_dark, rect, border_radius=14)
    pygame.draw.rect(screen, (18, 20, 26), rect.inflate(-10, -10),
                     border_radius=10)

    # Inner glow
    inner = pygame.Surface((w - 24, h - 24), pygame.SRCALPHA)
    pulse2 = int((math.sin(RT.shrine_pulse + 2) + 1) * 3)
    pygame.draw.rect(inner, (*accent, 30 + pulse2),
                     (0, 0, w - 24, h - 24), border_radius=8)
    screen.blit(inner, (x + 12, y + 12))

    # Frame
    border_col = accent if selected else (80, 90, 100)
    border_w = 3 if selected else 2
    pygame.draw.rect(screen, border_col, rect, border_w, border_radius=14)

    # Icon — image if available, primitive otherwise
    icon_cx = x + 52
    icon_cy = y + h // 2
    if icon_img:
        screen.blit(icon_img,
                    (icon_cx - icon_img.get_width() // 2,
                     icon_cy - icon_img.get_height() // 2))
    else:
        if "RAM" in subtitle:
            pts = [(icon_cx + 4, icon_cy - 26),
                   (icon_cx - 8, icon_cy + 2),
                   (icon_cx - 1, icon_cy + 2),
                   (icon_cx - 4, icon_cy + 26),
                   (icon_cx + 8, icon_cy - 4),
                   (icon_cx + 1, icon_cy - 4)]
            pygame.draw.polygon(screen, accent, pts)
            pygame.draw.polygon(screen, (255, 255, 255), pts, 1)
        else:
            pygame.draw.rect(screen, accent,
                             (icon_cx - 16, icon_cy - 20, 32, 14),
                             border_radius=3)
            pygame.draw.rect(screen, accent,
                             (icon_cx - 22, icon_cy - 2, 44, 10),
                             border_radius=3)
            pygame.draw.rect(screen, accent,
                             (icon_cx - 20, icon_cy + 14, 40, 8),
                             border_radius=3)

    # Title
    title_s = font.render(title, True, accent if selected else (200, 200, 210))
    screen.blit(title_s, (x + 100, y + 18))

    # Subtitle (RAM / ROM)
    sub_s = small_font.render(subtitle, True, (200, 190, 170))
    screen.blit(sub_s, (x + 100, y + 48))

    # Description lines
    for i, ln in enumerate(desc.split("\n")):
        s = small_font.render(ln, True, (180, 190, 200))
        screen.blit(s, (x + 100, y + 76 + i * 20))

    # "Selected" indicator
    if selected:
        indicator = small_font.render("▶ SELECTED", True, accent)
        screen.blit(indicator, (x + w - indicator.get_width() - 16,
                                 y + h - 22))


# =========================================================
# DRAWING — FOREGROUND PROMPT
# =========================================================
def draw_interaction_prompt(screen):
    if is_blocking_input():
        return
    prompt = None
    if _player_in(TERMINAL_RECT, 40) and not _flag(FLAG_PUZZLE_DONE):
        prompt = "Press E — Touch the Memory Shrine"
    elif _player_in(EXIT_RECT, 40):
        if _flag(FLAG_DONE):
            prompt = "Press E — Descend Further"
        else:
            prompt = "Press E — Leave the Monastery"

    if not prompt:
        return
    msg = small_font.render(prompt, True, WHITE)
    box = pygame.Rect(WIDTH // 2 - msg.get_width() // 2 - 14,
                      HEIGHT - 110, msg.get_width() + 28, 28)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (10, 12, 20, 220), surf.get_rect(), border_radius=6)
    pygame.draw.rect(surf, (*GOLD, 180), surf.get_rect(), 2, border_radius=6)
    screen.blit(surf, box.topleft)
    screen.blit(msg, (box.centerx - msg.get_width() // 2, box.y + 6))


# =========================================================
# DRAWING — RECORDINGS
# =========================================================
def _draw_holo(screen, img, cx, cy, fallback_col=(150, 220, 240)):
    pulse = int((math.sin(pygame.time.get_ticks() / 200) + 1) * 4)
    for r, a in [(110 + pulse, 40), (80 + pulse, 70), (50, 120)]:
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*fallback_col, a), (r, r), r)
        screen.blit(glow, (cx - r, cy - r))
    if img:
        screen.blit(img, (cx - img.get_width() // 2,
                          cy - img.get_height() // 2 + 20))
    else:
        body = pygame.Surface((80, 110), pygame.SRCALPHA)
        pygame.draw.ellipse(body, (*fallback_col, 200), (15, 0, 50, 60))
        pygame.draw.rect(body, (*fallback_col, 200), (10, 55, 60, 40))
        screen.blit(body, (cx - 40, cy - 30))


def draw_dawa(screen):
    if not RT.dawa_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 200))
    screen.blit(ov, (0, 0))

    holo_cx, holo_cy = WIDTH // 2, 210
    _draw_holo(screen, DAWA_IMG, holo_cx, holo_cy, (180, 240, 200))

    line, _sp = DAWA_RECORDING[RT.dawa_index]
    _draw_recording_box(screen, line, "DAWA — RECORDED MESSAGE",
                        (150, 240, 180))


def draw_drukma(screen):
    if not RT.drukma_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 200))
    screen.blit(ov, (0, 0))

    holo_cx, holo_cy = WIDTH // 2, 210
    _draw_holo(screen, None, holo_cx, holo_cy, (120, 220, 240))

    line, _sp = DRUKMA_FRAGMENT[RT.drukma_index]
    if line.startswith("Drukma: "):
        speaker = "DRUKMA — FRAGMENT"
    elif line.startswith("You: "):
        speaker = "YOU"
    elif line.startswith("Unknown Voice: "):
        speaker = "UNKNOWN VOICE"
    else:
        speaker = "MEMORY RECORD"
    _draw_recording_box(screen, line, speaker, (140, 220, 255))


def _draw_recording_box(screen, line, speaker, colour):
    box = pygame.Rect(100, HEIGHT - 180, WIDTH - 200, 130)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (12, 18, 26, 240), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (*colour, 200), surf.get_rect(), 2, border_radius=10)
    screen.blit(surf, box.topleft)

    spk = location_font.render(speaker, True, colour)
    screen.blit(spk, (box.x + 20, box.y + 14))

    lines, cur = [], ""
    for word in line.split():
        test = cur + word + " "
        if small_font.size(test)[0] <= box.width - 40:
            cur = test
        else:
            lines.append(cur.strip())
            cur = word + " "
    if cur:
        lines.append(cur.strip())
    for i, ln in enumerate(lines[:3]):
        screen.blit(small_font.render(ln, True, (220, 240, 250)),
                    (box.x + 20, box.y + 46 + i * 22))

    hint = small_font.render("[E] Continue", True, (150, 180, 200))
    screen.blit(hint, (box.right - hint.get_width() - 20, box.bottom - 22))


# =========================================================
# DRAWING — REVEAL
# =========================================================
def draw_reveal(screen):
    if not RT.reveal_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 220))
    screen.blit(ov, (0, 0))

    box = pygame.Rect(WIDTH // 2 - 340, 150, 680, 340)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (18, 22, 30, 250), surf.get_rect(), border_radius=12)
    pygame.draw.rect(surf, (200, 80, 80, 240), surf.get_rect(), 3,
                     border_radius=12)
    screen.blit(surf, box.topleft)

    title = font.render("MEMORY LOG — DUPLICATE FOUND", True, (245, 220, 130))
    screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 22))

    mono = pygame.font.SysFont("consolas", 16)
    lines = [
        ("> SHRINE WAKE: OK", (150, 200, 220)),
        ("> MEMORY CATALOGUE: ...", (150, 200, 220)),
        ("> MATCH FOUND: DRUKMA ↔ ARCHIVE SOURCE 7F", (255, 120, 100)),
        ("> SOURCE 7F: ORIGINAL EXPERIMENT LOG", (200, 200, 200)),
        ("> OVERLAP: 71% BEHAVIOURAL PATTERN", (255, 220, 130)),
        ("", (0, 0, 0)),
        ("SYSTEM NOTE: Drukma's memories do not belong only to Drukma.", (150, 220, 240)),
        ("They were assembled from the same archive that", (150, 220, 240)),
        ("produced another consciousness.", (150, 220, 240)),
        ("The name in the source log is not NULL.", (255, 180, 140)),
        ("But the archive is the same.", (255, 180, 140)),
    ]
    y = box.y + 66
    for text, col in lines:
        if text:
            s = mono.render(text, True, col)
            screen.blit(s, (box.x + 30, y))
        y += 22

    hint = small_font.render("[E] Close", True, (180, 180, 180))
    screen.blit(hint, (box.right - hint.get_width() - 20, box.bottom - 26))


def draw_toast(screen):
    if RT.toast_timer <= 0 or not RT.toast_text:
        return
    msg = font.render(RT.toast_text, True, (245, 220, 130))
    box = pygame.Rect(WIDTH // 2 - msg.get_width() // 2 - 20, 60,
                      msg.get_width() + 40, 40)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (12, 14, 22, 220), surf.get_rect(), border_radius=8)
    pygame.draw.rect(surf, (*GOLD, 200), surf.get_rect(), 2, border_radius=8)
    screen.blit(surf, box.topleft)
    screen.blit(msg, (box.centerx - msg.get_width() // 2, box.y + 8))


def _draw_label(screen, text, cx, y):
    s = small_font.render(text, True, WHITE)
    bg = pygame.Surface((s.get_width() + 12, s.get_height() + 4), pygame.SRCALPHA)
    pygame.draw.rect(bg, (0, 0, 0, 170), bg.get_rect(), border_radius=4)
    pygame.draw.rect(bg, (215, 175, 70, 140), bg.get_rect(), 1, border_radius=4)
    screen.blit(bg, (cx - bg.get_width() // 2, y))
    screen.blit(s, (cx - s.get_width() // 2, y + 2))


# =========================================================
# PUBLIC CALLERS
# =========================================================
def draw_background_layer(screen):
    draw_background(screen)
    draw_shrine(screen)
    draw_exit_marker(screen)


def draw_foreground_layer(screen):
    draw_interaction_prompt(screen)
    draw_puzzle(screen)
    draw_dawa(screen)
    draw_drukma(screen)
    draw_reveal(screen)
    draw_toast(screen)


def on_enter():
    if not _flag(FLAG_ENTERED):
        _set(FLAG_ENTERED, True)
        try:
            import drukma_commentary
            drukma_commentary.trigger("memory_monastery_entered")
        except Exception:
            pass
        story_state.STATE.add_journal_entry(
            "The Memory Monastery",
            "Drukma led me north to an old monastery of crystals.\n\n"
            "The chambers here hold two kinds of memory — the kind that "
            "is held only while it is needed, and the kind that is written "
            "into the machine itself.\n\n"
            "Drukma is quiet. It says it has been here before. It does not "
            "know how it knows.",
            source="The Memory Monastery"
        )
        _toast("Entered the Memory Monastery")