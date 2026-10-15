"""
eastern_ruins.py — Act II: The Eastern Ruins

A separate scene (like cpu_dzong) containing:
  - The Record Keeper terminal
  - A three-device input puzzle (Crystal Keypad is correct)
  - A 4-symbol sequence entry
  - Dorji's holographic recording
  - The INPUT CHANNEL: MODIFIED reveal
  - Silent Sentinel logic-gate
  - Optional: Tashi's lost tools
  - Signal lead → Processing Citadel (Act III)
"""

import pygame
import math
import os
import random
import story_state
import sound_system
from setting import (WIDTH, HEIGHT, font, small_font, title_font, location_font,
                     WHITE, GOLD, BLACK, GRASS, SKY)


# Root folder (so paths work from any CWD)
_ROOT = os.path.dirname(os.path.abspath(__file__))


def _asset(*parts):
    """Resolve an asset path relative to the game root."""
    return os.path.join(_ROOT, *parts)


# =========================================================
# FLAGS
# =========================================================
FLAG_ENTERED        = "eastern_ruins_entered"
FLAG_DEVICE_FIXED   = "eastern_ruins_device_fixed"
FLAG_SEQUENCE_DONE  = "eastern_ruins_sequence_done"
FLAG_DORJI_PLAYED   = "eastern_ruins_dorji_played"
FLAG_TAMPER_SEEN    = "eastern_ruins_tamper_seen"
FLAG_SENTINEL_SOLVED= "eastern_ruins_sentinel_solved"
FLAG_TOOLS_TAKEN    = "tashi_tools_taken"


# =========================================================
# LAYOUT
# =========================================================
EXIT_RECT          = pygame.Rect(20, 560, 80, 60)
TERMINAL_RECT      = pygame.Rect(460, 340, 80, 100)
WALL_CARVING_RECT  = pygame.Rect(700, 200, 140, 100)
SENTINEL_RECT      = pygame.Rect(760, 440, 40, 60)
SENTINEL_DOOR_RECT = pygame.Rect(760, 500, 40, 20)
TOOL_CRATE_RECT    = pygame.Rect(120, 480, 40, 40)
LEAD_RECT          = pygame.Rect(580, 460, 60, 60)

RUINS_WALLS = [
    pygame.Rect(0, 0, WIDTH, 60),
    pygame.Rect(0, 0, 40, HEIGHT),
    pygame.Rect(WIDTH - 40, 0, 40, HEIGHT),
    pygame.Rect(0, HEIGHT - 40, WIDTH, 40),
]

DEVICES = [
    {"id": "keypad", "name": "Crystal Keypad",
     "desc": "A slate of nine teal crystal buttons.",
     "hint": "Information enters the system through here.",
     "correct": True},
    {"id": "shard",  "name": "Memory Shard",
     "desc": "A pale blue crystal shard with faint inscriptions.",
     "hint": "It holds something. Nothing enters.",
     "correct": False},
    {"id": "lever",  "name": "Broken Gear Lever",
     "desc": "A rusted brass lever on an iron base.",
     "hint": "It moves physical things, not information.",
     "correct": False},
]

SEQUENCE = ["◇", "○", "△", "□"]
KEYPAD_SYMBOLS = ["◇", "○", "△", "□", "☆", "✦", "◎", "▽", "⬡"]


# =========================================================
# SYMBOL RENDERING (font-independent — draws primitives)
# =========================================================
def _draw_symbol(surface, sym, cx, cy, size, color, thickness=2):
    """Draw a puzzle symbol using primitive shapes so it renders
    identically on every system regardless of installed fonts."""
    s = size // 2
    if sym == "◇":
        pygame.draw.polygon(surface, color,
                            [(cx, cy - s), (cx + s, cy),
                             (cx, cy + s), (cx - s, cy)], thickness)
    elif sym == "○":
        pygame.draw.circle(surface, color, (cx, cy), s, thickness)
    elif sym == "△":
        pygame.draw.polygon(surface, color,
                            [(cx, cy - s), (cx + s, cy + s),
                             (cx - s, cy + s)], thickness)
    elif sym == "□":
        pygame.draw.rect(surface, color,
                         (cx - s, cy - s, s * 2, s * 2), thickness)
    elif sym == "☆":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            r = s if i % 2 == 0 else s // 2
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
        pygame.draw.polygon(surface, color, pts, thickness)
    elif sym == "✦":
        pts = [(cx, cy - s),
               (cx + s // 3, cy - s // 3),
               (cx + s, cy),
               (cx + s // 3, cy + s // 3),
               (cx, cy + s),
               (cx - s // 3, cy + s // 3),
               (cx - s, cy),
               (cx - s // 3, cy - s // 3)]
        pygame.draw.polygon(surface, color, pts, thickness)
    elif sym == "◎":
        pygame.draw.circle(surface, color, (cx, cy), s, thickness)
        pygame.draw.circle(surface, color, (cx, cy), s // 3, thickness)
    elif sym == "▽":
        pygame.draw.polygon(surface, color,
                            [(cx, cy + s), (cx + s, cy - s),
                             (cx - s, cy - s)], thickness)
    elif sym == "⬡":
        pts = []
        for i in range(6):
            a = math.pi / 3 * i - math.pi / 2
            pts.append((cx + math.cos(a) * s, cy + math.sin(a) * s))
        pygame.draw.polygon(surface, color, pts, thickness)
    else:
        pygame.draw.circle(surface, color, (cx, cy), s)


# =========================================================
# ASSET LOADING
# =========================================================
def _strip_white(surface, tolerance=12):
    surface = surface.convert_alpha()
    w, h = surface.get_size()
    for x in range(w):
        for y in range(h):
            r, g, b, a = surface.get_at((x, y))
            if a < 20:
                continue
            if r > 255 - tolerance and g > 255 - tolerance and b > 255 - tolerance:
                surface.set_at((x, y), (0, 0, 0, 0))
    return surface


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


def _load(path):
    if not os.path.isfile(path):
        print(f"  [MISS] {os.path.relpath(path, _ROOT)}  (file not found)")
        return None
    try:
        img = pygame.image.load(path)
        print(f"  [OK]   {os.path.relpath(path, _ROOT)}  → {img.get_size()}")
        return img
    except pygame.error as e:
        print(f"  [FAIL] {os.path.relpath(path, _ROOT)}  ({e})")
        return None


print("=== Loading Eastern Ruins assets ===")

# Ruins background
_raw_bg = _load(_asset("assets", "environment", "ruins", "eastern_ruins_bg.png"))
RUINS_BG = _cover_fit(_raw_bg, WIDTH, HEIGHT) if _raw_bg else None
if RUINS_BG:
    print(f"         Background fitted → {RUINS_BG.get_size()}")

# Terminal
_raw_term = _load(_asset("assets", "environment", "ruins", "terminal_main.png"))
TERMINAL_IMG = (_scale_fit(_strip_white(_raw_term, tolerance=12), 100, 130)
                if _raw_term else None)

# Input devices
_raw_keypad = _load(_asset("assets", "environment", "ruins", "input_device_keypad.png"))
DEVICE_KEYPAD_IMG = _scale_fit(_raw_keypad, 52, 52) if _raw_keypad else None

_raw_shard = _load(_asset("assets", "environment", "ruins", "input_device_shard.png"))
DEVICE_SHARD_IMG = (_scale_fit(_strip_white(_raw_shard, tolerance=12), 52, 52)
                    if _raw_shard else None)

_raw_lever = _load(_asset("assets", "environment", "ruins", "input_device_lever.png"))
DEVICE_LEVER_IMG = (_scale_fit(_strip_white(_raw_lever, tolerance=12), 52, 52)
                    if _raw_lever else None)

# Sentinel sprite sheet
_raw_sent = _load(_asset("assets", "sprite", "sentinel_sprite.png"))
if _raw_sent:
    if _raw_sent.get_size() != (1024, 1024):
        print(f"         Resizing sentinel {_raw_sent.get_size()} → (1024, 1024)")
        _raw_sent = pygame.transform.smoothscale(_raw_sent, (1024, 1024))
    SENTINEL_SHEET = _strip_white(_raw_sent, tolerance=15)
else:
    SENTINEL_SHEET = None

# Ruins-side gate sprite  ← NEW
_raw_gate = _load(_asset("assets", "environment", "ruins", "gate_ruins_side.png"))
if _raw_gate:
    GATE_RUINS_IMG = _scale_fit(_strip_white(_raw_gate, tolerance=15), 110, 150)
    print(f"         Ruins gate fitted → {GATE_RUINS_IMG.get_size()}")
else:
    GATE_RUINS_IMG = None

print("=== Ruins assets loaded ===\n")


# =========================================================
# RUNTIME STATE
# =========================================================
class _RT:
    puzzle_open       = False
    puzzle_stage      = 0
    puzzle_cursor     = 0
    sequence_input    = []
    sequence_cursor   = 0
    sentinel_open     = False
    sentinel_cursor   = 0
    recording_open    = False
    recording_index   = 0
    recording_timer   = 0
    tamper_open       = False
    tamper_timer      = 0
    sentinel_frame    = 0
    sentinel_timer    = 0
    toast_text        = ""
    toast_timer       = 0
    recording_last_voiced = -1     # ← track which line's voice was already played
    recording_just_opened = False  # ← play first voice on the opening frame

RT = _RT()


# Each entry: (text, speaker_name or None)
# speaker_name=None means "narrator — no voice file"
DORJI_RECORDING = [
    ("A holographic figure shimmers to life above the terminal.", None),
    ("If this message has survived, then the Input Shrine has failed.", "Dorji_Recording"),
    ("Remember this.", "Dorji_Recording"),
    ("A system cannot produce a reliable result", "Dorji_Recording"),
    ("from information it never received,", "Dorji_Recording"),
    ("or from information that was entered incorrectly.", "Dorji_Recording"),
    ("Guard the input channels.", "Dorji_Recording"),
    ("Everything downstream depends on them.", "Dorji_Recording"),
    ("The hologram fades. The terminal continues to scroll.", None),
]

# Legacy accessor for code that still expects a flat list of strings
DORJI_RECORDING_TEXT = [line for line, _ in DORJI_RECORDING]

SENTINEL_SEQUENCES = [
    {"seq": ["GRANT", "INPUT", "VALIDATE"],  "correct": False,
     "why": "Access cannot be granted before information is entered."},
    {"seq": ["INPUT", "VALIDATE", "GRANT"],  "correct": True,
     "why": ""},
    {"seq": ["VALIDATE", "GRANT", "INPUT"],  "correct": False,
     "why": "Nothing can be validated before it has been received."},
]


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
            RT.tamper_open or RT.sentinel_open)


def build_collisions():
    walls = list(RUINS_WALLS)
    walls.append(TERMINAL_RECT.inflate(20, 20))
    if not _flag(FLAG_SENTINEL_SOLVED):
        walls.append(SENTINEL_RECT.inflate(20, 30))
        walls.append(SENTINEL_DOOR_RECT.inflate(20, 20))
    return walls


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

    if RT.tamper_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            RT.tamper_open = False
            _set(FLAG_TAMPER_SEEN, True)
            try:
                import drukma_commentary
                drukma_commentary.trigger("input_modified_found")
            except Exception:
                pass
            try:
                story_state.STATE.add_fragment("fragment_input_tamper")
            except Exception:
                pass
        return True

    if RT.puzzle_open:
        if RT.puzzle_stage == 0:
            if event.key in (pygame.K_UP, pygame.K_w):
                RT.puzzle_cursor = (RT.puzzle_cursor - 1) % len(DEVICES)
                sound_system.play("blip")
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                RT.puzzle_cursor = (RT.puzzle_cursor + 1) % len(DEVICES)
                sound_system.play("blip")
            elif event.key in (pygame.K_e, pygame.K_RETURN):
                _pick_device()
            elif event.key == pygame.K_ESCAPE:
                RT.puzzle_open = False
                sound_system.play("ui_close")
        elif RT.puzzle_stage == 1:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                RT.sequence_cursor = (RT.sequence_cursor - 1) % len(KEYPAD_SYMBOLS)
                sound_system.play("blip")
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                RT.sequence_cursor = (RT.sequence_cursor + 1) % len(KEYPAD_SYMBOLS)
                sound_system.play("blip")
            elif event.key in (pygame.K_e, pygame.K_RETURN):
                RT.sequence_input.append(KEYPAD_SYMBOLS[RT.sequence_cursor])
                sound_system.play("blip")
                if len(RT.sequence_input) >= 4:
                    _check_sequence()
            elif event.key == pygame.K_BACKSPACE:
                if RT.sequence_input:
                    RT.sequence_input.pop()
            elif event.key == pygame.K_ESCAPE:
                RT.sequence_input = []
                RT.puzzle_stage = 0
                sound_system.play("ui_close")
        return True

    if RT.sentinel_open:
        if event.key in (pygame.K_UP, pygame.K_w):
            RT.sentinel_cursor = (RT.sentinel_cursor - 1) % len(SENTINEL_SEQUENCES)
            sound_system.play("blip")
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            RT.sentinel_cursor = (RT.sentinel_cursor + 1) % len(SENTINEL_SEQUENCES)
            sound_system.play("blip")
        elif event.key in (pygame.K_e, pygame.K_RETURN):
            _pick_sequence()
        elif event.key == pygame.K_ESCAPE:
            RT.sentinel_open = False
            sound_system.play("ui_close")
        return True

    if event.key == pygame.K_e:
        if _player_in(TERMINAL_RECT, 40):
            if not _flag(FLAG_DEVICE_FIXED):
                RT.puzzle_open = True
                RT.puzzle_stage = 0
                RT.puzzle_cursor = 0
                sound_system.play("ui_open")
                return True
            elif _flag(FLAG_SEQUENCE_DONE) and not _flag(FLAG_DORJI_PLAYED):
                _start_recording()
                return True
        if _player_in(SENTINEL_RECT, 40) and not _flag(FLAG_SENTINEL_SOLVED):
            RT.sentinel_open = True
            RT.sentinel_cursor = 0
            sound_system.play("ui_open")
            return True
        if _player_in(TOOL_CRATE_RECT, 40) and not _flag(FLAG_TOOLS_TAKEN):
            _set(FLAG_TOOLS_TAKEN, True)
            sound_system.play("correct")
            _toast("Acquired: Tashi's Brass Tools")
            story_state.STATE.add_journal_entry(
                "Tashi's Lost Tools",
                "I found Tashi's brass tools in a crate near the ruins.\n\n"
                "A hammer, a pair of pliers, and a caliper — each one still clean "
                "and well-kept. He must have left them here weeks ago.\n\n"
                "I should return them to him.",
                source="Eastern Ruins"
            )
            return True
        # ← NEW: signal lead to Processing Citadel
        if (_flag(FLAG_TAMPER_SEEN)
                and not story_state.STATE.get_flag("citadel_entered")
                and _player_in(LEAD_RECT, 40)):
            import main as _main
            if not _main.is_fading():
                _main.start_fade_out("processing_citadel")
            return True
        if _player_in(EXIT_RECT, 30):
            import main as _main
            if not _main.is_fading():
                _main.start_fade_out("village")
            return True

    return False


def _pick_device():
    dev = DEVICES[RT.puzzle_cursor]
    if dev["correct"]:
        sound_system.play("correct")
        _set(FLAG_DEVICE_FIXED, True)
        RT.puzzle_stage = 1
        RT.sequence_input = []
        RT.sequence_cursor = 0
        _toast("Crystal Keypad installed. Enter the sequence.")
    else:
        sound_system.play("wrong")
        _toast("That is not an input device. Look again.")


def _check_sequence():
    if RT.sequence_input == SEQUENCE:
        sound_system.play("correct")
        _set(FLAG_SEQUENCE_DONE, True)
        RT.puzzle_open = False
        _toast("Sequence accepted. The terminal wakes.")
    else:
        sound_system.play("wrong")
        _toast("Sequence rejected. Check the wall carving.")
        RT.sequence_input = []


def _play_recording_voice():
    """Play the voice line for the current recording index, if any."""
    if not (0 <= RT.recording_index < len(DORJI_RECORDING)):
        return
    text, speaker = DORJI_RECORDING[RT.recording_index]
    if speaker is None:
        # Narration line — stop any playing voice, no replacement
        sound_system.stop_voice()
        return
    # Try the real voice file first; fall back to the synthesized beep
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _start_recording():
    RT.recording_open = True
    RT.recording_index = 0
    RT.recording_timer = 0
    RT.recording_last_voiced = -1
    RT.recording_just_opened = True
    try:
        import drukma_commentary
        drukma_commentary.trigger("dorji_recording_played")
    except Exception:
        pass


def _advance_recording():
    RT.recording_index += 1
    if RT.recording_index >= len(DORJI_RECORDING):
        RT.recording_open = False
        RT.recording_last_voiced = -1
        RT.recording_just_opened = False
        sound_system.stop_voice()
        _set(FLAG_DORJI_PLAYED, True)
        RT.tamper_open = True
        RT.tamper_timer = 300
        try:
            story_state.STATE.add_fragment("fragment_dorji_ruins")
        except Exception:
            pass
    else:
        _play_recording_voice()
        RT.recording_last_voiced = RT.recording_index


def _pick_sequence():
    s = SENTINEL_SEQUENCES[RT.sentinel_cursor]
    if s["correct"]:
        sound_system.play("correct")
        _set(FLAG_SENTINEL_SOLVED, True)
        RT.sentinel_open = False
        _toast("Instruction conflict resolved. Access review initiated.")
        story_state.STATE.add_journal_entry(
            "The Silent Sentinel",
            "The Sentinel was blocking my path — not out of malice, but "
            "because its instruction sequence had been corrupted.\n\n"
            "I rearranged the order: INPUT comes first, then VALIDATE, "
            "then GRANT access.\n\n"
            "The Sentinel stood aside. It was never choosing to attack me. "
            "It was following faulty instructions.",
            source="Eastern Ruins"
        )
    else:
        sound_system.play("wrong")
        _toast(s["why"])


def _toast(text, duration=200):
    RT.toast_text = text
    RT.toast_timer = duration


def update():
    if RT.toast_timer > 0:
        RT.toast_timer -= 1

    # First-frame voice trigger when the recording opens
    if RT.recording_just_opened:
        RT.recording_just_opened = False
        _play_recording_voice()
        RT.recording_last_voiced = RT.recording_index

    if RT.recording_open:
        RT.recording_timer += 1
    if RT.tamper_open and RT.tamper_timer > 0:
        RT.tamper_timer -= 1
    RT.sentinel_timer += 1
    if RT.sentinel_timer >= 12:
        RT.sentinel_timer = 0
        RT.sentinel_frame = (RT.sentinel_frame + 1) % 4


# =========================================================
# DRAWING — BACKGROUND LAYER
# =========================================================
def draw_background(screen):
    if RUINS_BG:
        screen.blit(RUINS_BG, (0, 0))
        return

    # Atmospheric primitive fallback
    screen.fill((18, 24, 28))
    pygame.draw.rect(screen, (42, 58, 62), (0, 0, WIDTH, 200))
    pygame.draw.rect(screen, (38, 44, 46), (0, 200, WIDTH, HEIGHT - 200))

    for y in range(210, HEIGHT, 40):
        pygame.draw.line(screen, (52, 60, 62), (0, y), (WIDTH, y), 1)
    for x in range(0, WIDTH, 60):
        pygame.draw.line(screen, (52, 60, 62), (x, 200), (x, HEIGHT), 1)

    for px, py, ph in [(140, 160, 180), (400, 130, 200), (860, 140, 190)]:
        pygame.draw.rect(screen, (68, 66, 60), (px, py, 40, ph))
        pygame.draw.rect(screen, (92, 88, 80), (px, py, 40, 8))
        pygame.draw.rect(screen, (44, 42, 38), (px + 30, py, 10, ph))
        pygame.draw.rect(screen, (55, 90, 55), (px, py + ph - 20, 40, 20))


def draw_wall_carving(screen):
    if _flag(FLAG_SEQUENCE_DONE):
        return
    r = WALL_CARVING_RECT
    pygame.draw.rect(screen, (60, 58, 54), r, border_radius=6)
    pygame.draw.rect(screen, (90, 86, 78), r, 3, border_radius=6)

    positions = [(r.x + 40, r.y + 32),
                 (r.x + 100, r.y + 32),
                 (r.x + 40, r.y + 68),
                 (r.x + 100, r.y + 68)]
    for i, (px, py) in enumerate(positions):
        if i < len(SEQUENCE):
            _draw_symbol(screen, SEQUENCE[i], px, py, 24,
                         (200, 220, 240), thickness=2)

    hint_pulse = int((math.sin(pygame.time.get_ticks() / 600) + 1) * 4)
    hint_surf = pygame.Surface((r.width + 8, r.height + 8), pygame.SRCALPHA)
    pygame.draw.rect(hint_surf, (90, 200, 220, 60 + hint_pulse),
                     (0, 0, r.width + 8, r.height + 8), 2, border_radius=8)
    screen.blit(hint_surf, (r.x - 4, r.y - 4))


def draw_terminal(screen):
    r = TERMINAL_RECT
    shadow = pygame.Surface((r.width + 30, 16), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 100), (0, 0, r.width + 30, 16))
    screen.blit(shadow, (r.centerx - (r.width + 30) // 2, r.bottom - 4))

    if TERMINAL_IMG:
        screen.blit(TERMINAL_IMG,
                    (r.centerx - TERMINAL_IMG.get_width() // 2,
                     r.bottom - TERMINAL_IMG.get_height() + 8))
    else:
        pygame.draw.rect(screen, (60, 58, 54), r)
        pygame.draw.rect(screen, (90, 86, 78), (r.x, r.y, r.width, 8))
        scr = pygame.Rect(r.x + 8, r.y + 20, r.width - 16, 40)
        scr_col = (90, 200, 220) if _flag(FLAG_DEVICE_FIXED) else (40, 50, 60)
        pygame.draw.rect(screen, scr_col, scr, border_radius=4)
        pygame.draw.rect(screen, (30, 30, 30), scr, 2, border_radius=4)

    if _flag(FLAG_SEQUENCE_DONE) and not _flag(FLAG_DORJI_PLAYED):
        pulse = int((math.sin(pygame.time.get_ticks() / 400) + 1) * 3)
        glow = pygame.Surface((r.width + 40, r.height + 40), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (90, 220, 240, 50),
                            (0, 0, r.width + 40, r.height + 40))
        screen.blit(glow, (r.centerx - (r.width + 40) // 2,
                           r.centery - (r.height + 40) // 2))

    _draw_label(screen, "RECORD KEEPER", r.centerx, r.bottom + 6)


def draw_sentinel(screen):
    r = SENTINEL_RECT
    shadow = pygame.Surface((r.width + 20, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 110), (0, 0, r.width + 20, 12))
    screen.blit(shadow, (r.centerx - (r.width + 20) // 2, r.bottom - 4))

    if SENTINEL_SHEET:
        fw = SENTINEL_SHEET.get_width() // 4
        fh = SENTINEL_SHEET.get_height() // 4
        frame = SENTINEL_SHEET.subsurface(
            pygame.Rect(RT.sentinel_frame * fw, 0, fw, fh)).copy()
        frame = pygame.transform.scale(frame, (60, 80))
        screen.blit(frame, (r.centerx - 30, r.bottom - 80))
    else:
        pygame.draw.rect(screen, (85, 82, 78), r)
        pygame.draw.circle(screen, (90, 200, 220), (r.centerx, r.y + 14), 6)
        pygame.draw.rect(screen, (60, 58, 54), (r.x, r.y, r.width, 4))

    if not _flag(FLAG_SENTINEL_SOLVED):
        pulse = int((math.sin(pygame.time.get_ticks() / 500) + 1) * 3)
        glow = pygame.Surface((r.width + 30, r.height + 30), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (200, 60, 60, 40 + pulse),
                            (0, 0, r.width + 30, r.height + 30))
        screen.blit(glow, (r.centerx - (r.width + 30) // 2,
                           r.centery - (r.height + 30) // 2))
        rim = pygame.Surface((r.width + 10, r.height + 10), pygame.SRCALPHA)
        pygame.draw.ellipse(rim, (90, 220, 240, 50 + pulse // 2),
                            (0, 0, r.width + 10, r.height + 10), 3)
        screen.blit(rim, (r.centerx - (r.width + 10) // 2,
                          r.centery - (r.height + 10) // 2))
    else:
        pulse = int((math.sin(pygame.time.get_ticks() / 600) + 1) * 2)
        aura = pygame.Surface((r.width + 30, r.height + 30), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (215, 175, 70, 40 + pulse),
                            (0, 0, r.width + 30, r.height + 30))
        screen.blit(aura, (r.centerx - (r.width + 30) // 2,
                           r.centery - (r.height + 30) // 2))

    door = SENTINEL_DOOR_RECT
    door_col = (60, 40, 30) if not _flag(FLAG_SENTINEL_SOLVED) else (120, 90, 50)
    pygame.draw.rect(screen, door_col, door)
    pygame.draw.rect(screen,
                     (200, 170, 90) if _flag(FLAG_SENTINEL_SOLVED) else (40, 40, 40),
                     door, 2)

    _draw_label(screen, "SILENT SENTINEL", r.centerx, r.bottom + 6)


def draw_ruins_gate(screen):
    """Draw the ruins-side gate sprite at the exit rect."""
    r = EXIT_RECT

    if GATE_RUINS_IMG:
        # Glow behind
        pulse = int((math.sin(pygame.time.get_ticks() / 500) + 1) * 4)
        gw = GATE_RUINS_IMG.get_width() + 40
        gh = GATE_RUINS_IMG.get_height() + 40
        glow = pygame.Surface((gw, gh), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (90, 220, 240, 40 + pulse),
                            (0, 0, gw, gh))
        screen.blit(glow, (r.centerx - gw // 2,
                           r.bottom - GATE_RUINS_IMG.get_height() - 20))

        # Gate sprite
        screen.blit(GATE_RUINS_IMG,
                    (r.centerx - GATE_RUINS_IMG.get_width() // 2,
                     r.bottom - GATE_RUINS_IMG.get_height() + 12))

        # Label under gate
        txt = small_font.render("← DRUKORA VILLAGE", True, WHITE)
        bg = pygame.Surface((txt.get_width() + 14, txt.get_height() + 6),
                            pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 0, 0, 180), bg.get_rect(), border_radius=5)
        pygame.draw.rect(bg, (215, 175, 70, 160), bg.get_rect(),
                         1, border_radius=5)
        screen.blit(bg, (r.centerx - bg.get_width() // 2, r.bottom + 6))
        screen.blit(txt, (r.centerx - txt.get_width() // 2, r.bottom + 9))
    else:
        # Primitive fallback (existing box marker)
        draw_exit_marker(screen)


def draw_exit_marker(screen):
    r = EXIT_RECT
    pygame.draw.rect(screen, (60, 45, 35), r, border_radius=6)
    pygame.draw.rect(screen, (200, 170, 90), r, 2, border_radius=6)
    txt = small_font.render("← DRUKORA VILLAGE", True, WHITE)
    screen.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - 8))


def draw_tool_crate(screen):
    if _flag(FLAG_TOOLS_TAKEN):
        return
    r = TOOL_CRATE_RECT
    pulse = int((math.sin(pygame.time.get_ticks() / 500) + 1) * 3)
    glow = pygame.Surface((r.width + 30, r.height + 30), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 200, 100, 60),
                       (r.width // 2 + 15, r.height // 2 + 15), 20 + pulse)
    screen.blit(glow, (r.x - 15, r.y - 15))
    pygame.draw.rect(screen, (100, 62, 38), r)
    pygame.draw.rect(screen, (140, 90, 55), (r.x, r.y, r.width, 6))
    pygame.draw.line(screen, (60, 40, 25),
                     (r.x + 4, r.y + 10), (r.right - 4, r.bottom - 6), 2)


def draw_processing_lead(screen):
    """Pulsing marker that appears after the tamper reveal.
    Leads the player to the Processing Citadel (Act III)."""
    if not _flag(FLAG_TAMPER_SEEN):
        return
    if story_state.STATE.get_flag("citadel_entered"):
        return
    r = LEAD_RECT
    pulse = int((math.sin(pygame.time.get_ticks() / 400) + 1) * 4)

    # Glow
    glow = pygame.Surface((r.width + 40, r.height + 40), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 140, 90, 70),
                       (r.width // 2 + 20, r.height // 2 + 20), 26 + pulse)
    screen.blit(glow, (r.x - 20, r.y - 20))

    # Marker (signal tower glyph)
    pygame.draw.polygon(screen, (255, 180, 100), [
        (r.centerx, r.y + 10),
        (r.x + 12, r.bottom - 10),
        (r.right - 12, r.bottom - 10),
    ], 3)
    pygame.draw.circle(screen, (255, 220, 160), (r.centerx, r.y + 10), 4)

    # Label
    txt = small_font.render("SIGNAL LEAD", True, (255, 220, 160))
    bg = pygame.Surface((txt.get_width() + 14, txt.get_height() + 6), pygame.SRCALPHA)
    pygame.draw.rect(bg, (0, 0, 0, 180), bg.get_rect(), border_radius=5)
    pygame.draw.rect(bg, (255, 180, 100, 200), bg.get_rect(), 1, border_radius=5)
    screen.blit(bg, (r.centerx - bg.get_width() // 2, r.bottom + 6))
    screen.blit(txt, (r.centerx - txt.get_width() // 2, r.bottom + 9))


# =========================================================
# DRAWING — FOREGROUND LAYER
# =========================================================
def draw_interaction_prompt(screen):
    if is_blocking_input():
        return
    prompt = None
    if _player_in(TERMINAL_RECT, 40):
        if not _flag(FLAG_DEVICE_FIXED):
            prompt = "Press E — Inspect the Terminal"
        elif _flag(FLAG_SEQUENCE_DONE) and not _flag(FLAG_DORJI_PLAYED):
            prompt = "Press E — Play Recording"
    elif _player_in(SENTINEL_RECT, 40) and not _flag(FLAG_SENTINEL_SOLVED):
        prompt = "Press E — Inspect the Sentinel"
    elif _player_in(TOOL_CRATE_RECT, 40) and not _flag(FLAG_TOOLS_TAKEN):
        prompt = "Press E — Pick Up Crate"
    elif (_flag(FLAG_TAMPER_SEEN)
          and not story_state.STATE.get_flag("citadel_entered")
          and _player_in(LEAD_RECT, 40)):
        prompt = "Press E — Follow the Signal Lead"
    elif _player_in(EXIT_RECT, 30):
        prompt = "Press E — Return to Drukora"

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


def draw_puzzle_overlay(screen):
    if not RT.puzzle_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    screen.blit(ov, (0, 0))

    if RT.puzzle_stage == 0:
        _draw_device_picker(screen)
    elif RT.puzzle_stage == 1:
        _draw_sequence_entry(screen)


def _draw_device_picker(screen):
    panel = pygame.Rect(WIDTH // 2 - 260, 80, 520, 420)
    surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (20, 24, 34, 245), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (*GOLD, 220), surf.get_rect(), 2, border_radius=10)
    screen.blit(surf, panel.topleft)

    title = font.render("Which device provides INPUT?", True, (245, 220, 130))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 14))

    sub = small_font.render(
        "↑/↓ to choose  ·  [E] confirm  ·  [ESC] leave",
        True, (170, 170, 170))
    screen.blit(sub, (panel.centerx - sub.get_width() // 2, panel.y + 46))

    device_imgs = [DEVICE_KEYPAD_IMG, DEVICE_SHARD_IMG, DEVICE_LEVER_IMG]
    y = panel.y + 90
    for i, dev in enumerate(DEVICES):
        row = pygame.Rect(panel.x + 18, y, panel.width - 36, 88)
        hovered = (i == RT.puzzle_cursor)
        bg = (60, 50, 34) if hovered else (32, 34, 42)
        pygame.draw.rect(screen, bg, row, border_radius=6)
        pygame.draw.rect(screen,
                         (*GOLD, 200) if hovered else (80, 80, 90),
                         row, 2, border_radius=6)

        icon_slot = pygame.Rect(row.x + 16, row.centery - 28, 56, 56)
        pygame.draw.rect(screen, (48, 42, 34), icon_slot, border_radius=6)
        pygame.draw.rect(screen, (90, 80, 60), icon_slot, 1, border_radius=6)

        img = device_imgs[i] if i < len(device_imgs) else None
        if img:
            screen.blit(img,
                        (icon_slot.centerx - img.get_width() // 2,
                         icon_slot.centery - img.get_height() // 2))
            tx = icon_slot.right + 12
        else:
            pygame.draw.rect(screen, (120, 120, 130),
                             (icon_slot.x + 8, icon_slot.y + 8, 40, 40),
                             border_radius=4)
            tx = icon_slot.right + 12

        screen.blit(small_font.render(dev["name"], True, WHITE), (tx, row.y + 14))
        screen.blit(small_font.render(dev["desc"], True, (190, 190, 190)),
                    (tx, row.y + 38))
        screen.blit(small_font.render(dev["hint"], True, (150, 180, 190)),
                    (tx, row.y + 60))

        y += 100


def _draw_sequence_entry(screen):
    panel = pygame.Rect(WIDTH // 2 - 260, 100, 520, 380)
    surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (20, 24, 34, 245), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (*GOLD, 220), surf.get_rect(), 2, border_radius=10)
    screen.blit(surf, panel.topleft)

    title = font.render("Enter the Sequence", True, (245, 220, 130))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 14))

    sub = small_font.render(
        "←/→ choose  ·  [E] enter  ·  [BACKSPACE] undo  ·  [ESC] restart",
        True, (170, 170, 170))
    screen.blit(sub, (panel.centerx - sub.get_width() // 2, panel.y + 46))

    box_y = panel.y + 100
    total_w = 4 * 80
    start_x = panel.centerx - total_w // 2 + 10
    for i in range(4):
        cell = pygame.Rect(start_x + i * 80, box_y, 60, 60)
        pygame.draw.rect(screen, (32, 34, 42), cell, border_radius=6)
        pygame.draw.rect(screen, (90, 90, 100), cell, 2, border_radius=6)
        if i < len(RT.sequence_input):
            _draw_symbol(screen, RT.sequence_input[i],
                         cell.centerx, cell.centery, 36,
                         (220, 240, 250), thickness=3)

    sym_y = panel.y + 200
    sym_label = small_font.render("Available:", True, (170, 170, 170))
    screen.blit(sym_label, (panel.x + 30, sym_y))
    for i, sym in enumerate(KEYPAD_SYMBOLS):
        cell = pygame.Rect(panel.x + 30 + i * 52, sym_y + 24, 44, 44)
        hovered = (i == RT.sequence_cursor)
        pygame.draw.rect(screen, (60, 50, 34) if hovered else (28, 30, 38),
                         cell, border_radius=6)
        pygame.draw.rect(screen, (*GOLD, 200) if hovered else (80, 80, 90),
                         cell, 2, border_radius=6)
        _draw_symbol(screen, sym, cell.centerx, cell.centery, 22,
                     WHITE, thickness=2)

    hint = small_font.render(
        "The wall carving shows the correct order.",
        True, (150, 200, 220))
    screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 40))


def draw_recording(screen):
    if not RT.recording_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 200))
    screen.blit(ov, (0, 0))

    holo_cx, holo_cy = WIDTH // 2, 220
    pulse = int((math.sin(pygame.time.get_ticks() / 200) + 1) * 4)
    for r, a in [(80 + pulse, 40), (55 + pulse, 80), (30, 140)]:
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (90, 220, 240, a), (r, r), r)
        screen.blit(glow, (holo_cx - r, holo_cy - r))

    pygame.draw.ellipse(screen, (150, 220, 240, 200),
                        (holo_cx - 25, holo_cy - 30, 50, 60))
    pygame.draw.rect(screen, (150, 220, 240, 200),
                     (holo_cx - 30, holo_cy + 25, 60, 30))

    line, _speaker = DORJI_RECORDING[RT.recording_index]
    box = pygame.Rect(100, HEIGHT - 180, WIDTH - 200, 130)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (12, 18, 26, 240), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (90, 220, 240, 200), surf.get_rect(), 2, border_radius=10)
    screen.blit(surf, box.topleft)

    spk = location_font.render("DORJI — RECORDED MESSAGE", True, (180, 240, 255))
    screen.blit(spk, (box.x + 20, box.y + 14))

    lines = []
    cur = ""
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


def draw_tamper(screen):
    if not RT.tamper_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 220))
    screen.blit(ov, (0, 0))

    box = pygame.Rect(WIDTH // 2 - 320, 160, 640, 320)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (18, 22, 30, 250), surf.get_rect(), border_radius=12)
    pygame.draw.rect(surf, (200, 80, 80, 240), surf.get_rect(), 3, border_radius=12)
    screen.blit(surf, box.topleft)

    title = font.render("TERMINAL LOG — RECOVERED", True, (245, 220, 130))
    screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 22))

    mono = pygame.font.SysFont("consolas", 16)
    lines = [
        ("> TERMINAL WAKE: OK", (150, 200, 220)),
        ("> INPUT CHANNEL STATUS: ...", (150, 200, 220)),
        ("> INPUT CHANNEL: MODIFIED", (255, 120, 100)),
        ("> TIMESTAMP: [-UNKNOWN-]", (200, 200, 200)),
        ("> ACCESS: AUTHORIZED", (255, 220, 130)),
        ("> PREVIOUS OPERATOR: [REDACTED]", (200, 200, 200)),
        ("", (0, 0, 0)),
        ("SYSTEM NOTE: This change was NOT made by natural decay.", (150, 220, 240)),
        ("Something inside the Core altered the channel before the collapse.", (150, 220, 240)),
    ]
    y = box.y + 70
    for text, col in lines:
        if text:
            s = mono.render(text, True, col)
            screen.blit(s, (box.x + 30, y))
        y += 22

    hint = small_font.render("[E] Close", True, (180, 180, 180))
    screen.blit(hint, (box.right - hint.get_width() - 20, box.bottom - 26))


def draw_sentinel_overlay(screen):
    if not RT.sentinel_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    screen.blit(ov, (0, 0))

    panel = pygame.Rect(WIDTH // 2 - 280, 90, 560, 420)
    surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (20, 24, 34, 245), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (200, 80, 80, 220), surf.get_rect(), 2, border_radius=10)
    screen.blit(surf, panel.topleft)

    title = font.render("SENTINEL: INSTRUCTION CONFLICT", True, (255, 120, 100))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 14))

    sub = small_font.render(
        "Its sequence is corrupted. Choose the correct order.",
        True, (200, 200, 200))
    screen.blit(sub, (panel.centerx - sub.get_width() // 2, panel.y + 46))

    y = panel.y + 90
    for i, s in enumerate(SENTINEL_SEQUENCES):
        row = pygame.Rect(panel.x + 22, y, panel.width - 44, 60)
        hovered = (i == RT.sentinel_cursor)
        bg = (60, 40, 40) if hovered else (32, 34, 42)
        pygame.draw.rect(screen, bg, row, border_radius=6)
        pygame.draw.rect(screen,
                         (255, 120, 100) if hovered else (80, 80, 90),
                         row, 2, border_radius=6)

        chip_x = row.x + 20
        for step in s["seq"]:
            chip_w = small_font.size(step)[0] + 16
            chip = pygame.Rect(chip_x, row.centery - 14, chip_w, 28)
            pygame.draw.rect(screen, (50, 60, 80), chip, border_radius=6)
            pygame.draw.rect(screen, (150, 180, 220), chip, 1, border_radius=6)
            txt = small_font.render(step, True, (220, 240, 250))
            screen.blit(txt, (chip.centerx - txt.get_width() // 2,
                              chip.centery - txt.get_height() // 2))
            chip_x += chip_w + 8

        y += 70


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
    draw_ruins_gate(screen)         # gate sprite at the exit
    draw_wall_carving(screen)
    draw_tool_crate(screen)
    draw_processing_lead(screen)    # ← NEW: signal lead to Processing Citadel
    draw_terminal(screen)
    draw_sentinel(screen)


def draw_foreground_layer(screen):
    draw_interaction_prompt(screen)
    draw_puzzle_overlay(screen)
    draw_sentinel_overlay(screen)
    draw_recording(screen)
    draw_tamper(screen)
    draw_toast(screen)


def on_enter():
    if not _flag(FLAG_ENTERED):
        _set(FLAG_ENTERED, True)
        try:
            import drukma_commentary
            drukma_commentary.trigger("eastern_ruins_entered")
        except Exception:
            pass
        story_state.STATE.add_journal_entry(
            "The Eastern Ruins",
            "I found the source of the eastern signal.\n\n"
            "These ruins were once a research outpost — a place where the "
            "Guardians studied how information entered the Core.\n\n"
            "A terminal still glows in the central chamber. Someone left a "
            "message for whoever came next.",
            source="Eastern Ruins"
        )