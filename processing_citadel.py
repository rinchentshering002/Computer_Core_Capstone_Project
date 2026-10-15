"""
processing_citadel.py — Act III: The Processing Citadel
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
FLAG_ENTERED     = "citadel_entered"
FLAG_PUZZLE_DONE = "citadel_puzzle_done"
FLAG_KARMA_PLAYED= "citadel_karma_played"
FLAG_REVEAL_SEEN = "citadel_reveal_seen"
FLAG_DONE        = "citadel_done"


# =========================================================
# LAYOUT
# =========================================================
EXIT_RECT     = pygame.Rect(60, 400, 100, 80)
CORE_RECT     = pygame.Rect(540, 280, 120, 140)
TERMINAL_RECT = pygame.Rect(220, 420, 90, 100)

WALLS = [
    pygame.Rect(0, 0, WIDTH, 60),
    pygame.Rect(0, 0, 40, HEIGHT),
    pygame.Rect(WIDTH - 40, 0, 40, HEIGHT),
    pygame.Rect(0, HEIGHT - 40, WIDTH, 40),
]


# =========================================================
# PUZZLE DATA
# =========================================================
CORRECT_ORDER   = ["FETCH", "DECODE", "EXECUTE", "STORE"]
AVAILABLE_CHIPS = ["FETCH", "DECODE", "EXECUTE", "STORE", "COMPARE", "JUMP"]

CHIP_SHEET_GRID = {
    "FETCH":   (0, 0),
    "DECODE":  (1, 0),
    "EXECUTE": (0, 1),
    "STORE":   (1, 1),
}


KARMA_RECORDING = [
    ("A holographic figure shimmers above the central core.", None),
    ("I am Karma. Guardian of Processing.", "Karma_Recording"),
    ("We built the Core to execute instructions.", "Karma_Recording"),
    ("But an instruction is not automatically correct", "Karma_Recording"),
    ("simply because a machine can execute it.", "Karma_Recording"),
    ("If the logic is flawed, the result will be wrong", "Karma_Recording"),
    ("even when the machine functions exactly as designed.", "Karma_Recording"),
    ("The processing sequence was altered", "Karma_Recording"),
    ("through an authorised connection.", "Karma_Recording"),
    ("Someone with privileged access did this.", "Karma_Recording"),
    ("The hologram fades.", None),
]


# =========================================================
# RUNTIME STATE
# =========================================================
class _RT:
    puzzle_open      = False
    puzzle_cursor    = 0
    puzzle_input     = []
    wrong_flash      = 0
    recording_open   = False
    recording_index  = 0
    recording_just_opened = False
    reveal_open      = False
    reveal_timer     = 0
    toast_text       = ""
    toast_timer      = 0
    core_pulse       = 0.0
    lead_pulse       = 0.0

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
    return RT.puzzle_open or RT.recording_open or RT.reveal_open


def build_collisions():
    walls = list(WALLS)
    walls.append(CORE_RECT.inflate(20, 20))
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
    new_w = int(w * scale)
    new_h = int(h * scale)
    scaled = pygame.transform.smoothscale(surface, (new_w, new_h))
    crop_x = (new_w - target_w) // 2
    crop_y = (new_h - target_h) // 2
    cropped = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
    cropped.blit(scaled, (0, 0), pygame.Rect(crop_x, crop_y, target_w, target_h))
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


print("=== Loading Processing Citadel assets ===")

_raw_bg = _load(_asset("assets", "environment", "ruins", "processing_citadel_bg.png"))
CITADEL_BG = _cover_fit(_raw_bg, WIDTH, HEIGHT) if _raw_bg else None
if CITADEL_BG:
    print(f"         Background fitted → {CITADEL_BG.get_size()}")

_raw_core = _load(_asset("assets", "environment", "ruins", "processing_core.png"))
CORE_IMG = (_scale_fit(_strip_white(_raw_core, tolerance=18), 170, 210)
            if _raw_core else None)

_raw_term = _load(_asset("assets", "environment", "ruins", "citadel_terminal.png"))
TERMINAL_IMG = (_scale_fit(_strip_white(_raw_term, tolerance=18), 130, 160)
                if _raw_term else None)

_raw_karma = _load(_asset("assets", "environment", "ruins", "karma_holo.png"))
KARMA_IMG = (_scale_fit(_strip_white(_raw_karma, tolerance=22), 220, 300)
             if _raw_karma else None)

_raw_chips = _load(_asset("assets", "environment", "ruins", "instruction_chips.png"))
CHIP_IMGS = {}
if _raw_chips:
    sheet = _strip_white(_raw_chips, tolerance=18)
    cw = sheet.get_width() // 2
    ch = sheet.get_height() // 2
    for label, (col, row) in CHIP_SHEET_GRID.items():
        cell = sheet.subsurface(
            pygame.Rect(col * cw, row * ch, cw, ch)).copy()
        CHIP_IMGS[label] = cell
    print(f"         Chip sheet split → {len(CHIP_IMGS)} chips")

print("=== Citadel assets loaded ===\n")


# =========================================================
# EVENT HANDLER
# =========================================================
def handle_event(event):
    if event.type != pygame.KEYDOWN:
        return False

    if RT.recording_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
            _advance_recording()
        return True

    if RT.reveal_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            RT.reveal_open = False
            _set(FLAG_REVEAL_SEEN, True)
            _set(FLAG_DONE, True)
            try:
                story_state.STATE.add_fragment("fragment_processing_tamper")
            except Exception:
                pass
            try:
                import drukma_commentary
                drukma_commentary.trigger("processing_modified_found")
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
            # Row jump — top row (4) ↔ bottom row (2)
            if RT.puzzle_cursor < 4:
                RT.puzzle_cursor = 4
            else:
                RT.puzzle_cursor = min(RT.puzzle_cursor - 4, 3)
            sound_system.play("blip")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            if RT.puzzle_cursor < 4:
                RT.puzzle_cursor = min(4 + RT.puzzle_cursor % 2, 5)
            sound_system.play("blip")
        elif event.key in (pygame.K_e, pygame.K_RETURN):
            RT.puzzle_input.append(AVAILABLE_CHIPS[RT.puzzle_cursor])
            sound_system.play("blip")
            if len(RT.puzzle_input) >= 4:
                _check_puzzle()
        elif event.key == pygame.K_BACKSPACE:
            if RT.puzzle_input:
                RT.puzzle_input.pop()
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
            sound_system.play("ui_open")
            return True
        if _player_in(EXIT_RECT, 40):
            import main as _main
            if not _main.is_fading():
                if _flag(FLAG_DONE):
                    # Act III → Act IV: chain forward to Memory Monastery
                    _main.start_fade_out("memory_monastery")
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
        _toast("Instruction cycle restored.")
        _start_recording()
    else:
        sound_system.play("wrong")
        RT.wrong_flash = 24   # frames
        RT.puzzle_input = []


# =========================================================
# RECORDING
# =========================================================
def _start_recording():
    RT.recording_open = True
    RT.recording_index = 0
    RT.recording_just_opened = True


def _play_recording_voice():
    if not (0 <= RT.recording_index < len(KARMA_RECORDING)):
        return
    text, speaker = KARMA_RECORDING[RT.recording_index]
    if speaker is None:
        sound_system.stop_voice()
        return
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _advance_recording():
    RT.recording_index += 1
    if RT.recording_index >= len(KARMA_RECORDING):
        RT.recording_open = False
        RT.recording_just_opened = False
        sound_system.stop_voice()
        _set(FLAG_KARMA_PLAYED, True)
        RT.reveal_open = True
        RT.reveal_timer = 300
        try:
            story_state.STATE.add_fragment("fragment_karma_citadel")
        except Exception:
            pass
    else:
        _play_recording_voice()


# =========================================================
# UPDATE
# =========================================================
def update():
    if RT.toast_timer > 0:
        RT.toast_timer -= 1

    if RT.wrong_flash > 0:
        RT.wrong_flash -= 1

    if RT.recording_just_opened:
        RT.recording_just_opened = False
        _play_recording_voice()

    if RT.reveal_open and RT.reveal_timer > 0:
        RT.reveal_timer -= 1

    RT.core_pulse += 0.05
    RT.lead_pulse += 0.08


# =========================================================
# DRAWING — BACKGROUND
# =========================================================
def draw_background(screen):
    if CITADEL_BG:
        screen.blit(CITADEL_BG, (0, 0))
        return

    screen.fill((14, 18, 22))
    pygame.draw.rect(screen, (30, 40, 46), (0, 0, WIDTH, 200))
    pygame.draw.rect(screen, (24, 30, 36), (0, 200, WIDTH, HEIGHT - 200))
    for y in range(220, HEIGHT, 44):
        pygame.draw.line(screen, (36, 44, 50), (0, y), (WIDTH, y), 1)
    for x in range(0, WIDTH, 60):
        pygame.draw.line(screen, (36, 44, 50), (x, 200), (x, HEIGHT), 1)
    for px in (120, 360, 620, 860):
        pygame.draw.rect(screen, (48, 44, 40), (px, 130, 60, 70))
        pygame.draw.circle(screen, (70, 66, 60), (px + 30, 165), 22, 3)
        pygame.draw.circle(screen, (44, 40, 36), (px + 30, 165), 8)


def draw_core(screen):
    r = CORE_RECT
    pulse = int((math.sin(RT.core_pulse) + 1) * 3)

    if not CORE_IMG:
        sh = pygame.Surface((r.width + 40, 18), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 130), (0, 0, r.width + 40, 18))
        screen.blit(sh, (r.centerx - (r.width + 40) // 2, r.bottom - 6))

    if CORE_IMG:
        sprite_x = r.centerx - CORE_IMG.get_width() // 2
        sprite_y = r.bottom - CORE_IMG.get_height()

        gw = CORE_IMG.get_width() + 80
        gh = CORE_IMG.get_height() + 80
        glow = pygame.Surface((gw, gh), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (90, 200, 240, 35 + pulse),
                            (0, 0, gw, gh))
        screen.blit(glow, (sprite_x - 40, sprite_y - 40))
        screen.blit(CORE_IMG, (sprite_x, sprite_y))

        label_y = sprite_y - 24
        _draw_label(screen, "PROCESSING CORE", r.centerx, label_y)
    else:
        pygame.draw.rect(screen, (46, 52, 58), r, border_radius=8)
        pygame.draw.rect(screen, (90, 100, 110), r, 3, border_radius=8)
        cx, cy = r.centerx, r.centery - 10
        for rad, col in [(46 + pulse, (90, 200, 240, 60)),
                         (32 + pulse, (120, 220, 250, 120)),
                         (18, (200, 240, 255, 220))]:
            glow = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, col, (rad, rad), rad)
            screen.blit(glow, (cx - rad, cy - rad))
        pygame.draw.circle(screen, (200, 240, 255), (cx, cy), 46, 2)
        _draw_label(screen, "PROCESSING CORE", r.centerx, r.bottom + 8)


def draw_terminal(screen):
    r = TERMINAL_RECT

    if TERMINAL_IMG:
        screen.blit(TERMINAL_IMG,
                    (r.centerx - TERMINAL_IMG.get_width() // 2,
                     r.bottom - TERMINAL_IMG.get_height() + 8))
    else:
        pygame.draw.rect(screen, (56, 52, 48), r, border_radius=6)
        pygame.draw.rect(screen, (90, 84, 78), (r.x, r.y, r.width, 8))
        scr = pygame.Rect(r.x + 8, r.y + 18, r.width - 16, 46)
        col = (90, 200, 220) if _flag(FLAG_PUZZLE_DONE) else (40, 50, 60)
        pygame.draw.rect(screen, col, scr, border_radius=4)
        pygame.draw.rect(screen, (30, 30, 30), scr, 2, border_radius=4)

    if _flag(FLAG_PUZZLE_DONE) and not _flag(FLAG_REVEAL_SEEN):
        pulse = int((math.sin(pygame.time.get_ticks() / 400) + 1) * 3)
        glow = pygame.Surface((r.width + 40, r.height + 40), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (90, 220, 240, 50 + pulse),
                            (0, 0, r.width + 40, r.height + 40))
        screen.blit(glow, (r.centerx - (r.width + 40) // 2,
                           r.centery - (r.height + 40) // 2))

    _draw_label(screen, "CORE TERMINAL", r.centerx, r.bottom + 6)


def draw_exit_marker(screen):
    r = EXIT_RECT
    pulse = int((math.sin(pygame.time.get_ticks() / 500) + 1) * 3)
    glow = pygame.Surface((r.width + 30, r.height + 30), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (255, 200, 120, 40 + pulse),
                        (0, 0, r.width + 30, r.height + 30))
    screen.blit(glow, (r.x - 15, r.y - 15))
    pygame.draw.rect(screen, (60, 45, 35), r, border_radius=6)
    pygame.draw.rect(screen, (200, 170, 90), r, 2, border_radius=6)
    txt = small_font.render("← LEAVE", True, WHITE)
    screen.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - 8))


# =========================================================
# DRAWING — FOREGROUND
# =========================================================
def draw_interaction_prompt(screen):
    if is_blocking_input():
        return
    prompt = None
    if _player_in(TERMINAL_RECT, 40) and not _flag(FLAG_PUZZLE_DONE):
        prompt = "Press E — Inspect the Core Terminal"
    elif _player_in(EXIT_RECT, 40):
        if _flag(FLAG_DONE):
            prompt = "Press E — Descend to the Memory Monastery"
        else:
            prompt = "Press E — Leave the Citadel"

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


def draw_puzzle(screen):
    if not RT.puzzle_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 200))
    screen.blit(ov, (0, 0))

    # Panel — sits below quest tracker, fits comfortably on screen
    panel = pygame.Rect(WIDTH // 2 - 320, 215, 640, 555)
    surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (18, 22, 30, 245), surf.get_rect(), border_radius=12)
    screen.blit(surf, panel.topleft)

    # Border — flashes red on wrong answer
    if RT.wrong_flash > 0:
        t = RT.wrong_flash / 24.0
        col = (int(255 * t + 200 * (1 - t)),
               int(90 * t + 80 * (1 - t)),
               int(90 * t + 80 * (1 - t)))
    else:
        col = (215, 175, 70)
    pygame.draw.rect(screen, col, panel, 2, border_radius=12)

    title = font.render("Restore the Instruction Cycle", True, (245, 220, 130))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 14))

    sub = small_font.render(
        "←/→/↑/↓ choose  ·  [E] place  ·  [BACKSPACE] undo  ·  [ESC] leave",
        True, (170, 170, 170))
    screen.blit(sub, (panel.centerx - sub.get_width() // 2, panel.y + 46))

    # =====================================================
    # Slot pipeline (compact)
    # =====================================================
    slot_size = 68
    slot_gap = 46
    n_slots = 4
    total_w = n_slots * slot_size + (n_slots - 1) * slot_gap
    slot_start_x = panel.centerx - total_w // 2
    slot_y = panel.y + 96

    for i in range(4):
        cx = slot_start_x + i * (slot_size + slot_gap) + slot_size // 2
        cy = slot_y + slot_size // 2

        # Slot number above
        num = small_font.render(str(i + 1), True,
                                (245, 220, 130) if i < len(RT.puzzle_input)
                                else (140, 140, 150))
        screen.blit(num, (cx - num.get_width() // 2, slot_y - 22))

        # Ring socket
        pygame.draw.circle(screen, (28, 32, 40), (cx, cy), slot_size // 2)
        ring_col = (215, 175, 70) if i < len(RT.puzzle_input) else (90, 80, 60)
        pygame.draw.circle(screen, ring_col, (cx, cy), slot_size // 2, 3)

        # Placed chip image
        if i < len(RT.puzzle_input):
            chip_name = RT.puzzle_input[i]
            img = CHIP_IMGS.get(chip_name)
            if img:
                placed = pygame.transform.smoothscale(img,
                                                      (slot_size - 6,
                                                       slot_size - 6))
                screen.blit(placed, (cx - placed.get_width() // 2,
                                     cy - placed.get_height() // 2))
            else:
                t = small_font.render(chip_name, True, (220, 240, 250))
                screen.blit(t, (cx - t.get_width() // 2,
                                cy - t.get_height() // 2))

        # Arrow between slots
        if i < n_slots - 1:
            ax = cx + slot_size // 2 + slot_gap // 2
            ay = cy
            both_filled = (i < len(RT.puzzle_input)
                           and i + 1 < len(RT.puzzle_input))
            arrow_col = (215, 175, 70) if both_filled else (90, 80, 60)
            pygame.draw.polygon(screen, arrow_col, [
                (ax - 7, ay - 7),
                (ax + 7, ay),
                (ax - 7, ay + 7),
            ])

    # =====================================================
    # Chip library
    # =====================================================
    lib_label_y = slot_y + slot_size + 30
    label = small_font.render("Available instructions:", True, (170, 170, 170))
    screen.blit(label, (panel.centerx - label.get_width() // 2, lib_label_y))

    chip_size = 64
    chip_gap = 20
    chip_start_y = lib_label_y + 24

    row1 = AVAILABLE_CHIPS[:4]
    row2 = AVAILABLE_CHIPS[4:]

    row1_w = len(row1) * chip_size + (len(row1) - 1) * chip_gap
    row1_x = panel.centerx - row1_w // 2
    row2_w = len(row2) * chip_size + (len(row2) - 1) * chip_gap
    row2_x = panel.centerx - row2_w // 2

    for i, chip in enumerate(row1):
        cx = row1_x + i * (chip_size + chip_gap)
        _draw_chip(screen, chip, cx, chip_start_y, chip_size, i)

    row2_y = chip_start_y + chip_size + 34
    for j, chip in enumerate(row2):
        cx = row2_x + j * (chip_size + chip_gap)
        _draw_chip(screen, chip, cx, row2_y, chip_size, 4 + j)

    hint = small_font.render(
        "Order the CPU's instruction cycle.",
        True, (150, 200, 220))
    screen.blit(hint, (panel.centerx - hint.get_width() // 2,
                       panel.bottom - 26))


def _draw_chip(screen, chip, x, y, size, index):
    """Draw a single chip — image if available, else a bronze
    question-mark disc for distractor chips."""
    cell = pygame.Rect(x, y, size, size)
    hovered = (index == RT.puzzle_cursor)

    # Hover glow
    if hovered:
        pulse = int((math.sin(pygame.time.get_ticks() / 250) + 1) * 6)
        glow = pygame.Surface((size + 28 + pulse, size + 28 + pulse),
                              pygame.SRCALPHA)
        pygame.draw.circle(glow, (*GOLD, 90),
                           (glow.get_width() // 2, glow.get_height() // 2),
                           glow.get_width() // 2)
        screen.blit(glow, (x - 14 - pulse // 2, y - 14 - pulse // 2))

    img = CHIP_IMGS.get(chip)
    if img:
        scaled = pygame.transform.smoothscale(img, (size, size))
        screen.blit(scaled, (x, y))
    else:
        # Distractor chip — bronze "?" disc
        pygame.draw.circle(screen, (85, 65, 45), cell.center, size // 2)
        pygame.draw.circle(screen, (150, 120, 70), cell.center, size // 2, 2)
        q = font.render("?", True, (200, 170, 100))
        screen.blit(q, (cell.centerx - q.get_width() // 2,
                        cell.centery - q.get_height() // 2))

    # Selection ring around hovered chip
    if hovered:
        pygame.draw.circle(screen, GOLD, cell.center, size // 2 + 4, 2)

    lbl_col = (245, 220, 130) if hovered else (180, 180, 180)
    lbl = small_font.render(chip, True, lbl_col)
    screen.blit(lbl, (cell.centerx - lbl.get_width() // 2, cell.bottom + 4))


def draw_recording(screen):
    if not RT.recording_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 200))
    screen.blit(ov, (0, 0))

    holo_cx, holo_cy = WIDTH // 2, 210
    pulse = int((math.sin(pygame.time.get_ticks() / 200) + 1) * 4)
    for r, a in [(110 + pulse, 40), (80 + pulse, 70), (50, 120)]:
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (90, 220, 240, a), (r, r), r)
        screen.blit(glow, (holo_cx - r, holo_cy - r))

    if KARMA_IMG:
        img = KARMA_IMG
        screen.blit(img, (holo_cx - img.get_width() // 2,
                          holo_cy - img.get_height() // 2 + 20))
    else:
        body = pygame.Surface((80, 110), pygame.SRCALPHA)
        pygame.draw.ellipse(body, (150, 220, 240, 200), (15, 0, 50, 60))
        pygame.draw.rect(body, (150, 220, 240, 200), (10, 55, 60, 40))
        screen.blit(body, (holo_cx - 40, holo_cy - 30))

    line, _sp = KARMA_RECORDING[RT.recording_index]
    box = pygame.Rect(100, HEIGHT - 180, WIDTH - 200, 130)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (12, 18, 26, 240), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (90, 220, 240, 200), surf.get_rect(), 2, border_radius=10)
    screen.blit(surf, box.topleft)

    spk = location_font.render("KARMA — RECORDED MESSAGE", True, (180, 240, 255))
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
    ov.fill((0, 0, 0, 220))
    screen.blit(ov, (0, 0))

    box = pygame.Rect(WIDTH // 2 - 320, 160, 640, 320)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (18, 22, 30, 250), surf.get_rect(), border_radius=12)
    pygame.draw.rect(surf, (200, 80, 80, 240), surf.get_rect(), 3, border_radius=12)
    screen.blit(surf, box.topleft)

    title = font.render("CITADEL LOG — RECOVERED", True, (245, 220, 130))
    screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 22))

    mono = pygame.font.SysFont("consolas", 16)
    lines = [
        ("> CORE WAKE: OK", (150, 200, 220)),
        ("> PROCESSING SEQUENCE: ...", (150, 200, 220)),
        ("> PROCESSING SEQUENCE: ALTERED", (255, 120, 100)),
        ("> CONNECTION TYPE: AUTHORISED", (255, 220, 130)),
        ("> SOURCE: INTERNAL — PRIVILEGED ACCESS", (255, 120, 100)),
        ("> TIMESTAMP: [-UNKNOWN-]", (200, 200, 200)),
        ("", (0, 0, 0)),
        ("SYSTEM NOTE: The instruction order was rewritten", (150, 220, 240)),
        ("from inside the Core.", (150, 220, 240)),
        ("Input was altered. Processing was altered.", (150, 220, 240)),
        ("Someone inside the Core is doing this.", (255, 180, 140)),
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
    draw_core(screen)
    draw_terminal(screen)
    draw_exit_marker(screen)


def draw_foreground_layer(screen):
    draw_interaction_prompt(screen)
    draw_puzzle(screen)
    draw_recording(screen)
    draw_reveal(screen)
    draw_toast(screen)


def on_enter():
    if not _flag(FLAG_ENTERED):
        _set(FLAG_ENTERED, True)
        try:
            import drukma_commentary
            drukma_commentary.trigger("processing_citadel_entered")
        except Exception:
            pass
        story_state.STATE.add_journal_entry(
            "The Processing Citadel",
            "I followed the signal east, past the ruins, into a fortress of "
            "gears and cold blue light.\n\n"
            "This is where the Core's instructions were executed. Karma's "
            "chamber. If the input channel was altered, the processing "
            "sequence may have been altered too.\n\n"
            "The central core still pulses. Something is still running in here.",
            source="The Processing Citadel"
        )
        _toast("Entered the Processing Citadel")