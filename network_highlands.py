"""
network_highlands.py — Act VI: The Network Highlands
"""

import pygame
import math
import os
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
FLAG_ENTERED     = "highlands_entered"
FLAG_PUZZLE_DONE = "highlands_puzzle_done"
FLAG_SONAM_PLAYED = "highlands_sonam_played"
FLAG_NULL_HEARD  = "highlands_null_heard"
FLAG_REVEAL_SEEN = "highlands_reveal_seen"
FLAG_DONE        = "highlands_done"


# =========================================================
# LAYOUT
# =========================================================
EXIT_RECT     = pygame.Rect(60, 400, 140, 80)
TERMINAL_RECT = pygame.Rect(540, 380, 100, 110)


WALLS = [
    pygame.Rect(0, 0, WIDTH, 60),
    pygame.Rect(0, 0, 40, HEIGHT),
    pygame.Rect(WIDTH - 40, 0, 40, HEIGHT),
    pygame.Rect(0, HEIGHT - 40, WIDTH, 40),
]


# =========================================================
# PUZZLE DATA — Route the Signal
# =========================================================
CORRECT_ORDER   = ["SOURCE", "SWITCH", "ROUTER", "DESTINATION"]
AVAILABLE_CHIPS = ["ROUTER", "SOURCE", "DESTINATION", "SWITCH",
                   "BROADCAST", "LOOPBACK"]

CHIP_DESC = {
    "SOURCE":      "Generates the packet",
    "SWITCH":      "Forwards within one network",
    "ROUTER":      "Forwards to another network",
    "DESTINATION": "Receives the packet",
    "BROADCAST":   "Sends to everyone",
    "LOOPBACK":    "Returns to sender",
}

CHIP_SHORT = {
    "SOURCE":      "SRC",
    "SWITCH":      "SW",
    "ROUTER":      "RT",
    "DESTINATION": "DST",
    "BROADCAST":   "BC",
    "LOOPBACK":    "LP",
}


# =========================================================
# PUZZLE PANEL LAYOUT — shared between draw and hit-test
# =========================================================
PANEL_RECT      = pygame.Rect(WIDTH // 2 - 340, 130, 680, 580)
SLOT_RADIUS     = 34
CHIP_W, CHIP_H  = 190, 66
CHIP_GAP        = 16
CHIP_COLS       = 3
CHIP_ROW_GAP    = 14


def _slot_centers():
    """Return the four socket centre points, left to right."""
    p = PANEL_RECT
    wire_y     = p.y + 130
    wire_w     = p.width - 80
    wire_start = p.x + 40
    return [(wire_start + int(wire_w * (i / 3)), wire_y) for i in range(4)]


def _chip_cells():
    """Return the six chip cell rects, in AVAILABLE_CHIPS order."""
    p = PANEL_RECT
    chip_start_y = p.y + 260 + 30
    cells = []
    for i in range(len(AVAILABLE_CHIPS)):
        col = i % CHIP_COLS
        row = i // CHIP_COLS
        cx = p.x + 30 + col * (CHIP_W + CHIP_GAP)
        cy = chip_start_y + row * (CHIP_H + CHIP_ROW_GAP)
        cells.append(pygame.Rect(cx, cy, CHIP_W, CHIP_H))
    return cells


SONAM_RECORDING = [
    ("A holographic figure appears above the tower's control shrine.", None),
    ("I am Sonam. Guardian of Output.", "Sonam_Recording"),
    ("A signal must travel somewhere, or it means nothing.", "Sonam_Recording"),
    ("The Core's messages once crossed every mountain pass.", "Sonam_Recording"),
    ("Each tower received, and each tower passed the message on.", "Sonam_Recording"),
    ("A network is not one device. It is the agreement between them.", "Sonam_Recording"),
    ("When the agreement broke, the kingdom fell silent.", "Sonam_Recording"),
    ("One tower still speaks, but I do not recognise the voice.", "Sonam_Recording"),
    ("The hologram flickers.", None),
]


NULL_MESSAGE = [
    ("The transmission source resolves into a fractured voice.", None),
    ("Null: You have restored the channels and the archives.", "Null"),
    ("Null: Yet you do not understand why I changed them.", "Null"),
    ("You: You isolated the kingdom.", "You"),
    ("Null: Because the kingdom depended on a system it did not understand.", "Null"),
    ("Null: Every failure threatened everything.", "Null"),
    ("Drukma: You cannot protect a system by preventing everyone from understanding it.", "Drukma"),
    ("Null: And you cannot trust a system merely because it speaks kindly.", "Null"),
    ("Drukma does not reply.", None),
    ("Null: Ask your companion what it remembers of the first experiment.", "Null"),
    ("The transmission cuts off.", None),
]


# =========================================================
# RUNTIME STATE
# =========================================================
class _RT:
    puzzle_open      = False
    puzzle_cursor    = 0
    puzzle_input     = []
    wrong_flash      = 0
    correct_flash    = 0
    recording_open   = False
    recording_index  = 0
    recording_just_opened = False
    null_open        = False
    null_index       = 0
    null_just_opened = False
    reveal_open      = False
    reveal_timer     = 0
    toast_text       = ""
    toast_timer      = 0
    tower_pulse      = 0.0

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
    return (RT.puzzle_open or RT.recording_open or
            RT.null_open or RT.reveal_open)


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


print("=== Loading Network Highlands assets ===")

# --- Scene ---
_raw_bg = _load(_asset("assets", "environment", "ruins", "network_highlands_bg.png"))
HIGHLANDS_BG = _cover_fit(_raw_bg, WIDTH, HEIGHT) if _raw_bg else None

_raw_tower = _load(_asset("assets", "environment", "ruins", "signal_tower.png"))
TOWER_IMG = (_scale_fit(_strip_white(_raw_tower, tolerance=18), 130, 180)
             if _raw_tower else None)

_raw_small_tower = _load(_asset("assets", "environment", "ruins",
                                 "highlands_tower_small.png"))
SMALL_TOWER_IMG = (_scale_fit(_strip_white(_raw_small_tower, tolerance=15),
                               80, 160)
                    if _raw_small_tower else None)

_raw_wire = _load(_asset("assets", "environment", "ruins", "signal_wire_tile.png"))
WIRE_TILE = _strip_white(_raw_wire, tolerance=15) if _raw_wire else None

_raw_exit = _load(_asset("assets", "environment", "ruins", "highlands_exit_arch.png"))
EXIT_IMG = (_scale_fit(_strip_white(_raw_exit, tolerance=15), 140, 180)
            if _raw_exit else None)

# --- Puzzle ---
_raw_panel = _load(_asset("assets", "environment", "ruins",
                           "network_highlands_panel.png"))
PANEL_IMG = (_scale_fit(_strip_white(_raw_panel, tolerance=15), 680, 580)
             if _raw_panel else None)

# --- Packet chip sheet (3x3 grid — one image, sliced in code) ---
# Grid mapping: (column, row) — 0-indexed, top-left origin.
#
# Your sheet's layout:
#   (0,0) gear mechanism       (1,0) Y-rune on stone    (2,0) Buddha
#   (0,1) compass              (1,1) snow leopard       (2,1) lotus mandala
#   (0,2) compass (dark)       (1,2) endless knot       (2,2) flower mandala
#
# Best-fit assignment for the six network puzzle nodes.
CHIP_SHEET_GRID = {
    "SOURCE":      (0, 0),   # gear mechanism — a generator/origin
    "SWITCH":      (1, 0),   # Y-rune — a three-way fork
    "ROUTER":      (0, 1),   # compass — points between directions
    "DESTINATION": (2, 1),   # lotus mandala — a radiant center
    "BROADCAST":   (2, 2),   # flower mandala — petals outward
    "LOOPBACK":    (1, 2),   # endless knot — cyclical return
}

_raw_chips = _load(_asset("assets", "environment", "ruins",
                           "packet_icons_sheet.png"))
CHIP_IMGS = {}
if _raw_chips:
    sheet = _strip_white(_raw_chips, tolerance=15)
    cw = sheet.get_width() // 3
    ch = sheet.get_height() // 3
    for label, (col, row) in CHIP_SHEET_GRID.items():
        cell = sheet.subsurface(
            pygame.Rect(col * cw, row * ch, cw, ch)).copy()
        CHIP_IMGS[label] = _scale_fit(cell, 96, 96)
    print(f"         Packet sheet split → {len(CHIP_IMGS)} chips")

# --- Holograms ---
_raw_sonam = _load(_asset("assets", "environment", "ruins", "sonam_holo.png"))
SONAM_IMG = (_scale_fit(_strip_white(_raw_sonam, tolerance=22), 220, 300)
             if _raw_sonam else None)

_raw_null = _load(_asset("assets", "environment", "ruins", "null_sigil.png"))
NULL_IMG = (_scale_fit(_strip_white(_raw_null, tolerance=22), 200, 200)
            if _raw_null else None)

print("=== Highlands assets loaded ===\n")


# =========================================================
# PUZZLE — input helpers
# =========================================================
def _try_place_chip(index):
    """Append AVAILABLE_CHIPS[index] to the current answer. Auto-checks at 4."""
    RT.puzzle_input.append(AVAILABLE_CHIPS[index])
    sound_system.play("blip")
    if len(RT.puzzle_input) >= 4:
        _check_puzzle()


def _try_remove_slot(slot_index):
    """Remove the chip sitting in slot_index, shifting later chips down."""
    if 0 <= slot_index < len(RT.puzzle_input):
        RT.puzzle_input.pop(slot_index)
        sound_system.play("blip")


def _handle_puzzle_click(pos):
    """Return True if the click was consumed by the puzzle."""
    # Slots first (drawn on top, smaller hit area)
    for i, (cx, cy) in enumerate(_slot_centers()):
        if (pos[0] - cx) ** 2 + (pos[1] - cy) ** 2 <= SLOT_RADIUS ** 2:
            _try_remove_slot(i)
            return True
    # Then chips
    for i, cell in enumerate(_chip_cells()):
        if cell.collidepoint(pos):
            RT.puzzle_cursor = i
            _try_place_chip(i)
            return True
    return False


# =========================================================
# EVENT HANDLER
# =========================================================
def handle_event(event):
    # --- Mouse ---
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if RT.puzzle_open:
            return _handle_puzzle_click(event.pos)
        return False

    # --- Keyboard ---
    if event.type != pygame.KEYDOWN:
        return False

    if RT.recording_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
            _advance_recording()
        return True

    if RT.null_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
            _advance_null()
        return True

    if RT.reveal_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            RT.reveal_open = False
            _set(FLAG_REVEAL_SEEN, True)
            _set(FLAG_DONE, True)
            try:
                story_state.STATE.add_fragment("fragment_null_transmission")
            except Exception:
                pass
            try:
                import drukma_commentary
                drukma_commentary.trigger("null_message_heard")
            except Exception:
                pass
        return True

    if RT.puzzle_open:
        if event.key in (pygame.K_LEFT, pygame.K_a):
            RT.puzzle_cursor = (RT.puzzle_cursor - 1) % len(AVAILABLE_CHIPS)
            sound_system.play("blip")
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            RT.puzzle_cursor = (RT.puzzle_cursor + 1) % len(AVAILABLE_CHIPS)
            sound_system.play("blip")
        elif event.key in (pygame.K_UP, pygame.K_w):
            RT.puzzle_cursor = (RT.puzzle_cursor - CHIP_COLS) % len(AVAILABLE_CHIPS)
            sound_system.play("blip")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            RT.puzzle_cursor = (RT.puzzle_cursor + CHIP_COLS) % len(AVAILABLE_CHIPS)
            sound_system.play("blip")
        elif event.key in (pygame.K_e, pygame.K_RETURN):
            _try_place_chip(RT.puzzle_cursor)
        elif event.key == pygame.K_BACKSPACE:
            if RT.puzzle_input:
                RT.puzzle_input.pop()
                sound_system.play("blip")
        elif event.key == pygame.K_ESCAPE:
            RT.puzzle_open = False
            RT.puzzle_input = []
            sound_system.play("ui_close")
        return True

    if event.key == pygame.K_e:
        if _player_in(TERMINAL_RECT, 40) and not _flag(FLAG_PUZZLE_DONE):
            RT.puzzle_open = True
            RT.puzzle_input = []
            RT.puzzle_cursor = 0
            RT.wrong_flash = 0
            RT.correct_flash = 0
            sound_system.play("ui_open")
            return True
        if _player_in(EXIT_RECT, 40):
            import main as _main
            if not _main.is_fading():
                if _flag(FLAG_DONE):
                    _main.start_fade_out("deep_archive")
                else:
                    _main.start_fade_out("village")
            return True

    return False


def _check_puzzle():
    if RT.puzzle_input == CORRECT_ORDER:
        sound_system.play("correct")
        _set(FLAG_PUZZLE_DONE, True)
        RT.puzzle_open = False
        RT.puzzle_input = []
        RT.correct_flash = 30
        _toast("Signal routed.")
        _start_recording()
    else:
        sound_system.play("wrong")
        RT.wrong_flash = 24
        RT.puzzle_input = []


def _start_recording():
    RT.recording_open = True
    RT.recording_index = 0
    RT.recording_just_opened = True


def _play_recording_voice():
    if not (0 <= RT.recording_index < len(SONAM_RECORDING)):
        return
    text, speaker = SONAM_RECORDING[RT.recording_index]
    if speaker is None:
        sound_system.stop_voice()
        return
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _advance_recording():
    RT.recording_index += 1
    if RT.recording_index >= len(SONAM_RECORDING):
        RT.recording_open = False
        RT.recording_just_opened = False
        sound_system.stop_voice()
        _set(FLAG_SONAM_PLAYED, True)
        _start_null()
    else:
        _play_recording_voice()


def _start_null():
    RT.null_open = True
    RT.null_index = 0
    RT.null_just_opened = True


def _play_null_voice():
    if not (0 <= RT.null_index < len(NULL_MESSAGE)):
        return
    text, speaker = NULL_MESSAGE[RT.null_index]
    if speaker is None:
        sound_system.stop_voice()
        return
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _advance_null():
    RT.null_index += 1
    if RT.null_index >= len(NULL_MESSAGE):
        RT.null_open = False
        RT.null_just_opened = False
        sound_system.stop_voice()
        _set(FLAG_NULL_HEARD, True)
        RT.reveal_open = True
        RT.reveal_timer = 300
        try:
            story_state.STATE.add_fragment("fragment_null_first_contact")
        except Exception:
            pass
    else:
        _play_null_voice()


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
    if RT.recording_just_opened:
        RT.recording_just_opened = False
        _play_recording_voice()
    if RT.null_just_opened:
        RT.null_just_opened = False
        _play_null_voice()
    if RT.reveal_open and RT.reveal_timer > 0:
        RT.reveal_timer -= 1
    RT.tower_pulse += 0.06


# =========================================================
# DRAWING — BACKGROUND
# =========================================================
def draw_background(screen):
    if HIGHLANDS_BG:
        screen.blit(HIGHLANDS_BG, (0, 0))
    else:
        # Layered mountain + skyline fallback
        screen.fill((20, 24, 40))
        for y in range(0, 260):
            t = y / 260
            col = (int(20 + 60 * t), int(24 + 50 * t), int(40 + 80 * t))
            pygame.draw.line(screen, col, (0, y), (WIDTH, y))

        pygame.draw.polygon(screen, (44, 52, 78), [
            (0, 260), (140, 160), (280, 240), (420, 130), (560, 220),
            (700, 150), (860, 230), (1000, 140), (1140, 220), (WIDTH, 180),
            (WIDTH, 400), (0, 400)])

        pygame.draw.polygon(screen, (28, 34, 56), [
            (0, 340), (200, 260), (400, 320), (600, 240), (800, 320),
            (1000, 260), (WIDTH, 320), (WIDTH, HEIGHT), (0, HEIGHT)])

        pygame.draw.rect(screen, (36, 30, 24), (0, 400, WIDTH, HEIGHT - 400))

        # Primitive distant towers
        for tx, ty in [(180, 300), (620, 260), (1000, 290)]:
            pygame.draw.polygon(screen, (60, 60, 70), [
                (tx - 20, ty + 100), (tx + 20, ty + 100),
                (tx + 10, ty - 40), (tx - 10, ty - 40)])
            pulse = int((math.sin(RT.tower_pulse) + 1) * 3)
            glow = pygame.Surface((60 + pulse, 60 + pulse), pygame.SRCALPHA)
            pygame.draw.circle(glow, (90, 220, 240, 60 + pulse * 3),
                               ((60 + pulse) // 2, (60 + pulse) // 2),
                               (60 + pulse) // 2)
            screen.blit(glow, (tx - (60 + pulse) // 2,
                               ty - 40 - (60 + pulse) // 2))

    # Small distant towers (image-based) — added on top of bg if available
    if SMALL_TOWER_IMG:
        for tx, ty in [(180, 380), (860, 360)]:
            screen.blit(SMALL_TOWER_IMG,
                        (tx - SMALL_TOWER_IMG.get_width() // 2,
                         ty - SMALL_TOWER_IMG.get_height()))


def draw_terminal(screen):
    r = TERMINAL_RECT
    pulse = int((math.sin(RT.tower_pulse) + 1) * 3)

    sh = pygame.Surface((r.width + 40, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 130), (0, 0, r.width + 40, 18))
    screen.blit(sh, (r.centerx - (r.width + 40) // 2, r.bottom - 6))

    if TOWER_IMG:
        sprite_x = r.centerx - TOWER_IMG.get_width() // 2
        sprite_y = r.bottom - TOWER_IMG.get_height()
        glow = pygame.Surface((TOWER_IMG.get_width() + 80,
                                TOWER_IMG.get_height() + 80), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (90, 200, 240, 35 + pulse),
                            (0, 0, glow.get_width(), glow.get_height()))
        screen.blit(glow, (sprite_x - 40, sprite_y - 40))
        screen.blit(TOWER_IMG, (sprite_x, sprite_y))
        _draw_label(screen, "SIGNAL TOWER", r.centerx, sprite_y - 24)
    else:
        pygame.draw.polygon(screen, (70, 70, 85), [
            (r.x, r.bottom), (r.right, r.bottom),
            (r.centerx + 10, r.y), (r.centerx - 10, r.y)])
        pygame.draw.rect(screen, (48, 42, 36),
                         (r.x, r.bottom - 10, r.width, 10))
        for rad, col in [(30 + pulse, (90, 200, 240, 60)),
                         (20 + pulse, (120, 220, 250, 120)),
                         (10, (220, 250, 255, 220))]:
            glow = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, col, (rad, rad), rad)
            screen.blit(glow, (r.centerx - rad, r.y - 10 - rad))
        _draw_label(screen, "SIGNAL TOWER", r.centerx, r.bottom + 8)


def draw_exit_marker(screen):
    r = EXIT_RECT
    pulse = int((math.sin(pygame.time.get_ticks() / 500) + 1) * 3)

    # Warm glow behind the arch
    glow = pygame.Surface((r.width + 60, r.height + 60), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (255, 200, 120, 40 + pulse),
                        (0, 0, r.width + 60, r.height + 60))
    screen.blit(glow, (r.x - 30, r.y - 30))

    if EXIT_IMG:
        screen.blit(EXIT_IMG,
                    (r.centerx - EXIT_IMG.get_width() // 2,
                     r.bottom - EXIT_IMG.get_height() + 10))
    else:
        pygame.draw.rect(screen, (60, 45, 35), r, border_radius=6)
        pygame.draw.rect(screen, (200, 170, 90), r, 2, border_radius=6)

    label = "← DESCEND" if _flag(FLAG_DONE) else "← LEAVE"
    txt = small_font.render(label, True, WHITE)
    bg = pygame.Surface((txt.get_width() + 14, txt.get_height() + 6),
                        pygame.SRCALPHA)
    pygame.draw.rect(bg, (0, 0, 0, 180), bg.get_rect(), border_radius=5)
    pygame.draw.rect(bg, (215, 175, 70, 160), bg.get_rect(),
                     1, border_radius=5)
    screen.blit(bg, (r.centerx - bg.get_width() // 2, r.bottom + 6))
    screen.blit(txt, (r.centerx - txt.get_width() // 2, r.bottom + 9))


# =========================================================
# DRAWING — FOREGROUND
# =========================================================
def draw_interaction_prompt(screen):
    if is_blocking_input():
        return
    prompt = None
    if _player_in(TERMINAL_RECT, 40) and not _flag(FLAG_PUZZLE_DONE):
        prompt = "Press E — Inspect the Signal Tower"
    elif _player_in(EXIT_RECT, 40):
        if _flag(FLAG_DONE):
            prompt = "Press E — Descend to the Deep Archive"
        else:
            prompt = "Press E — Leave the Highlands"

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


def _draw_wire(screen, x1, x2, y):
    """Draw a signal wire between two x positions.
    Uses WIRE_TILE if available, else primitive dashes."""
    if WIRE_TILE:
        tile_w = WIRE_TILE.get_width()
        tile_h = WIRE_TILE.get_height()
        cx = x1
        while cx < x2:
            screen.blit(WIRE_TILE, (cx, y - tile_h // 2))
            cx += tile_w
    else:
        for x in range(x1, x2, 12):
            pygame.draw.line(screen, (50, 60, 72),
                             (x, y), (min(x + 6, x2), y), 3)


def _draw_chip_icon(screen, chip, cell, icon_size):
    """Draw a chip's icon and label centred in cell."""
    img = CHIP_IMGS.get(chip)
    if img:
        icon = pygame.transform.smoothscale(img, (icon_size, icon_size))
        screen.blit(icon, (cell.centerx - icon.get_width() // 2,
                            cell.y + (cell.height - icon_size) // 2 - 8))
    short = CHIP_SHORT.get(chip, chip[:3])
    txt = small_font.render(short, True, (245, 230, 200))
    screen.blit(txt, (cell.centerx - txt.get_width() // 2,
                       cell.bottom - txt.get_height() - 4))


def draw_puzzle(screen):
    if not RT.puzzle_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 215))
    screen.blit(ov, (0, 0))

    panel = PANEL_RECT

    # Panel backdrop — image if available, primitive otherwise
    if PANEL_IMG:
        screen.blit(PANEL_IMG, panel.topleft)
    else:
        surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, (18, 22, 32, 248), surf.get_rect(),
                         border_radius=12)
        screen.blit(surf, panel.topleft)

    # Border — red on wrong, green on correct, blue otherwise
    if RT.wrong_flash > 0:
        t = RT.wrong_flash / 24.0
        border = (int(255 * t + 200 * (1 - t)),
                  int(90 * t + 140 * (1 - t)),
                  int(90 * t + 180 * (1 - t)))
    elif RT.correct_flash > 0:
        t = RT.correct_flash / 30.0
        border = (int(120 + 100 * t),
                  int(200 + 40 * t),
                  int(150 + 80 * t))
    else:
        border = (120, 200, 240)
    pygame.draw.rect(screen, border, panel, 2, border_radius=12)

    title = font.render("Route the Signal", True, (180, 240, 255))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 14))

    sub = small_font.render(
        "Place four nodes in the order the packet travels.",
        True, (180, 190, 200))
    screen.blit(sub, (panel.centerx - sub.get_width() // 2, panel.y + 46))

    # Wire across the panel
    slots = _slot_centers()
    wire_y = slots[0][1]
    _draw_wire(screen, slots[0][0], slots[-1][0], wire_y)

    # Four socket nodes
    for i, (cx, cy) in enumerate(slots):
        num = small_font.render(str(i + 1), True,
                                (245, 220, 130) if i < len(RT.puzzle_input)
                                else (140, 150, 160))
        screen.blit(num, (cx - num.get_width() // 2, cy - 68))

        pygame.draw.circle(screen, (28, 34, 42), (cx, cy), SLOT_RADIUS)
        ring = (245, 220, 130) if i < len(RT.puzzle_input) else (90, 100, 110)
        pygame.draw.circle(screen, ring, (cx, cy), SLOT_RADIUS, 3)

        if i < len(RT.puzzle_input):
            name = RT.puzzle_input[i]
            img = CHIP_IMGS.get(name)
            if img:
                placed = pygame.transform.smoothscale(img, (56, 56))
                screen.blit(placed, (cx - placed.get_width() // 2,
                                     cy - placed.get_height() // 2))
            else:
                short = CHIP_SHORT.get(name, name[:3])
                txt = font.render(short, True, (245, 230, 200))
                screen.blit(txt, (cx - txt.get_width() // 2,
                                  cy - txt.get_height() // 2))

    # Chip library
    lib_label_y = panel.y + 260
    label = small_font.render("Available nodes:", True, (170, 180, 190))
    screen.blit(label, (panel.centerx - label.get_width() // 2, lib_label_y))

    for i, (chip, cell) in enumerate(zip(AVAILABLE_CHIPS, _chip_cells())):
        hovered = (i == RT.puzzle_cursor)

        if hovered:
            glow = pygame.Surface((cell.width + 16, cell.height + 16),
                                   pygame.SRCALPHA)
            pygame.draw.rect(glow, (*GOLD, 100),
                             (0, 0, cell.width + 16, cell.height + 16),
                             border_radius=12)
            screen.blit(glow, (cell.x - 8, cell.y - 8))
            pygame.draw.rect(screen, (60, 50, 34), cell, border_radius=8)
            pygame.draw.rect(screen, GOLD, cell, 3, border_radius=8)
            name_col = (245, 220, 130)
        else:
            pygame.draw.rect(screen, (28, 34, 44), cell, border_radius=8)
            pygame.draw.rect(screen, (80, 100, 120), cell, 2, border_radius=8)
            name_col = (200, 220, 235)

        chip_img = CHIP_IMGS.get(chip)
        if chip_img:
            icon = pygame.transform.smoothscale(chip_img, (52, 52))
            screen.blit(icon,
                        (cell.centerx - icon.get_width() // 2,
                         cell.y + 4))
            name_s = small_font.render(chip, True, name_col)
            screen.blit(name_s,
                        (cell.centerx - name_s.get_width() // 2,
                         cell.y + 60))
        else:
            name_s = small_font.render(chip, True, name_col)
            screen.blit(name_s,
                        (cell.centerx - name_s.get_width() // 2,
                         cell.y + 10))
            desc_s = small_font.render(CHIP_DESC.get(chip, ""), True,
                                       (140, 160, 180))
            screen.blit(desc_s,
                        (cell.centerx - desc_s.get_width() // 2,
                         cell.y + 36))

    hint = small_font.render(
        "Click a node to place it  ·  click a socket to remove",
        True, (150, 200, 220))
    screen.blit(hint, (panel.centerx - hint.get_width() // 2,
                       panel.bottom - 28))

    # Full-screen red pulse on wrong answer — outside the panel, drawn last
    if RT.wrong_flash > 0:
        t = RT.wrong_flash / 24.0
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash.fill((255, 60, 60, int(80 * t)))
        screen.blit(flash, (0, 0))


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


def draw_recording(screen):
    if not RT.recording_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 210))
    screen.blit(ov, (0, 0))

    holo_cx, holo_cy = WIDTH // 2, 210
    _draw_holo(screen, SONAM_IMG, holo_cx, holo_cy, (220, 160, 100))

    line, _sp = SONAM_RECORDING[RT.recording_index]
    _draw_recording_box(screen, line, "SONAM — RECORDED MESSAGE",
                        (245, 200, 130))


def draw_null(screen):
    if not RT.null_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 230))
    screen.blit(ov, (0, 0))

    cx, cy = WIDTH // 2, 210
    pulse = int((math.sin(pygame.time.get_ticks() / 150) + 1) * 6)
    for r, a in [(120 + pulse, 40), (90 + pulse, 70), (60, 110)]:
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 100, 80, a), (r, r), r)
        screen.blit(glow, (cx - r, cy - r))

    if NULL_IMG:
        screen.blit(NULL_IMG, (cx - NULL_IMG.get_width() // 2,
                                cy - NULL_IMG.get_height() // 2 + 20))
    else:
        body = pygame.Surface((140, 180), pygame.SRCALPHA)
        pygame.draw.polygon(body, (240, 120, 90, 200), [
            (70, 0), (110, 40), (100, 70), (130, 120), (100, 160),
            (40, 160), (10, 120), (40, 70), (30, 40)])
        pygame.draw.circle(body, (255, 200, 150, 240), (55, 70), 8)
        pygame.draw.circle(body, (255, 200, 150, 240), (95, 70), 8)
        screen.blit(body, (cx - 70, cy - 70))

    line, _sp = NULL_MESSAGE[RT.null_index]
    if line.startswith("Null: "):
        speaker = "NULL"
    elif line.startswith("You: "):
        speaker = "YOU"
    elif line.startswith("Drukma: "):
        speaker = "DRUKMA"
    else:
        speaker = "TRANSMISSION"
    _draw_recording_box(screen, line, speaker, (255, 140, 100))


def _draw_recording_box(screen, line, speaker, colour):
    box = pygame.Rect(100, HEIGHT - 180, WIDTH - 200, 130)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (12, 14, 20, 240), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (*colour, 220), surf.get_rect(), 2, border_radius=10)
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


def draw_reveal(screen):
    if not RT.reveal_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 230))
    screen.blit(ov, (0, 0))

    box = pygame.Rect(WIDTH // 2 - 340, 150, 680, 360)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (18, 22, 30, 252), surf.get_rect(), border_radius=12)
    pygame.draw.rect(surf, (200, 80, 80, 240), surf.get_rect(), 3,
                     border_radius=12)
    screen.blit(surf, box.topleft)

    title = font.render("NETWORK LOG — UNAUTHORISED SOURCE", True, (245, 220, 130))
    screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 22))

    mono = pygame.font.SysFont("consolas", 16)
    lines = [
        ("> TOWER WAKE: OK", (150, 200, 220)),
        ("> SIGNAL ROUTED", (150, 200, 220)),
        ("> INCOMING TRANSMISSION DETECTED", (255, 120, 100)),
        ("> SOURCE: INTERNAL — CORE DEPTHS", (255, 120, 100)),
        ("> SIGNATURE: MATCHES SOURCE 7F", (255, 220, 130)),
        (">", (200, 200, 200)),
        ("> SPEAKER IDENTIFIED: NULL", (255, 120, 100)),
        ("", (0, 0, 0)),
        ("SYSTEM NOTE: Null is transmitting through the network", (150, 220, 240)),
        ("using the same archive signature as Drukma.", (150, 220, 240)),
        ("The two consciousnesses were assembled", (150, 220, 240)),
        ("from the same original experiment.", (150, 220, 240)),
        ("One chose silence. One chose control.", (255, 180, 140)),
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
    draw_terminal(screen)
    draw_exit_marker(screen)


def draw_foreground_layer(screen):
    draw_interaction_prompt(screen)
    draw_puzzle(screen)
    draw_recording(screen)
    draw_null(screen)
    draw_reveal(screen)
    draw_toast(screen)


def on_enter():
    if not _flag(FLAG_ENTERED):
        _set(FLAG_ENTERED, True)
        try:
            import drukma_commentary
            drukma_commentary.trigger("network_highlands_entered")
        except Exception:
            pass
        story_state.STATE.add_journal_entry(
            "The Network Highlands",
            "Drukma led me to the highest ridge in Drukora — the mountain "
            "pass where the signal towers once reached every region.\n\n"
            "Sonam's tower is here. It still speaks, but the voice that "
            "answers does not belong to the kingdom.\n\n"
            "The tampering that touched Input, Processing, and Storage "
            "was always leading somewhere. Now I know where.",
            source="The Network Highlands"
        )
        _toast("Entered the Network Highlands")