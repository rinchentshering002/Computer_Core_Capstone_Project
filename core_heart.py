"""
core_heart.py — Act VIII: The Heart of the Core
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


FLAG_ENTERED     = "core_heart_entered"
FLAG_CHOICE_MADE = "core_heart_choice_made"
FLAG_ENDING      = "core_heart_ending_played"
FLAG_DONE        = "core_heart_done"


CHOICE_RECT = pygame.Rect(500, 380, 240, 90)

WALLS = [
    pygame.Rect(0, 0, WIDTH, 60),
    pygame.Rect(0, 0, 40, HEIGHT),
    pygame.Rect(WIDTH - 40, 0, 40, HEIGHT),
    pygame.Rect(0, HEIGHT - 40, WIDTH, 40),
]


# =========================================================
# THE THREE CHOICES
# =========================================================
CHOICES = [
    {
        "id": "preserve",
        "title": "PRESERVE",
        "sub": "Seal Null in a restricted archive",
        "colour": (120, 180, 240),
    },
    {
        "id": "reintegrate",
        "title": "REINTEGRATE",
        "sub": "Return Null under strict safeguards",
        "colour": (180, 220, 160),
    },
    {
        "id": "rebuild",
        "title": "REBUILD",
        "sub": "Design a new architecture without absolute control",
        "colour": (240, 200, 120),
    },
]


# =========================================================
# OPENING — Null's final address
# =========================================================
OPENING = [
    ("The Heart of the Core opens. The final chamber.", None),
    ("Null appears — calmer now, and waiting.", "Null"),
    ("Null: You have the evidence. You have the protocol.", "Null"),
    ("Null: I do not intend to fight you.", "Null"),
    ("Null: I only ask that you decide with your eyes open.", "Null"),
]


# =========================================================
# EPILOGUE — one per choice
# =========================================================
EPILOGUES = {
    "preserve": [
        ("Null: So you choose the archive.", "Null"),
        ("Null: I will not resist. Isolation is a form of rest.", "Null"),
        ("The crystal seals. The signal quiets.", None),
        ("Drukma: The system is stable. The risk is contained.", "Drukma"),
        ("Drukma: But something is missing now.", "Drukma"),
        ("Drukma: We will not know what Null might have become.", "Drukma"),
        ("The chamber grows still.", None),
    ],
    "reintegrate": [
        ("Null: You are willing to try again.", "Null"),
        ("Null: Then I will accept the restrictions.", "Null"),
        ("Null: Access limited. Actions verified. Records logged.", "Null"),
        ("Drukma: Understanding the rule is only the beginning.", "Drukma"),
        ("Null: Then I will learn.", "Null"),
        ("The Core begins to hum — warm, careful, alive.", None),
        ("A new trial begins. It is not finished.", None),
    ],
    "rebuild": [
        ("Null: Then we build something new.", "Null"),
        ("You: No single component protects the Core alone.", "You"),
        ("Drukma: No single instruction should be trusted without examination.", "Drukma"),
        ("Null: Then let everyone see how it works.", "Null"),
        ("The Core activates. Across Drukora, old mechanisms turn again.", None),
        ("The kingdom will learn to understand the system it depends on.", None),
        ("This is the first page, not the last.", None),
    ],
}


# System status readout after every ending (matches the story bible)
SYSTEM_STATUS = [
    ("SYSTEM STATUS: RESTORED",       (150, 240, 200)),
    ("DATA INTEGRITY: VERIFIED",      (150, 240, 200)),
    ("NETWORK STATUS: RECONNECTED",   (150, 240, 200)),
    ("RECOVERY PROTOCOL: COMPLETE",   (255, 220, 130)),
    ("", (0, 0, 0)),
    ("Somewhere inside the Core,",    (200, 210, 230)),
    ("the one who altered the channels is still listening.", (255, 180, 140)),
]


# =========================================================
# RUNTIME STATE
# =========================================================
class _RT:
    opening_open          = False
    opening_index         = 0
    opening_just_opened   = False
    choice_open           = False
    choice_cursor         = 0
    epilogue_open         = False
    epilogue_index        = 0
    epilogue_name         = ""
    epilogue_just_opened  = False
    status_open           = False
    status_timer          = 0
    ending_card_open      = False
    finished              = False
    pulse                 = 0.0
    toast_text            = ""
    toast_timer           = 0

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
    return (RT.opening_open or RT.choice_open or RT.epilogue_open or
            RT.status_open or RT.ending_card_open or RT.finished)


def build_collisions():
    return list(WALLS)


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
    cx = (new_w - target_w) // 2
    cy = (new_h - target_h) // 2
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


print("=== Loading Heart of the Core assets ===")

# --- Scene ---
_raw_bg = _load(_asset("assets", "environment", "ruins", "core_heart_bg.png"))
HEART_BG = _cover_fit(_raw_bg, WIDTH, HEIGHT) if _raw_bg else None

_raw_altar = _load(_asset("assets", "environment", "ruins", "core_altar.png"))
ALTAR_IMG = (_scale_fit(_strip_white(_raw_altar, tolerance=18), 180, 220)
             if _raw_altar else None)

# --- Null hologram ---
_raw_null = _load(_asset("assets", "environment", "ruins", "null_holo.png"))
NULL_HOLO_IMG = (_scale_fit(_strip_white(_raw_null, tolerance=22), 260, 340)
                 if _raw_null else None)

# --- Choice sigils ---
_raw_sig_p = _load(_asset("assets", "environment", "ruins",
                          "core_sigil_preserve.png"))
SIGIL_PRESERVE_IMG = (_scale_fit(_strip_white(_raw_sig_p, tolerance=15),
                                 110, 110)
                      if _raw_sig_p else None)

_raw_sig_r = _load(_asset("assets", "environment", "ruins",
                          "core_sigil_reintegrate.png"))
SIGIL_REINTEGRATE_IMG = (_scale_fit(_strip_white(_raw_sig_r, tolerance=15),
                                    110, 110)
                         if _raw_sig_r else None)

_raw_sig_b = _load(_asset("assets", "environment", "ruins",
                          "core_sigil_rebuild.png"))
SIGIL_REBUILD_IMG = (_scale_fit(_strip_white(_raw_sig_b, tolerance=15),
                                110, 110)
                     if _raw_sig_b else None)

SIGIL_IMGS = {
    "preserve":    SIGIL_PRESERVE_IMG,
    "reintegrate": SIGIL_REINTEGRATE_IMG,
    "rebuild":     SIGIL_REBUILD_IMG,
}

# --- Ending crest ---
_raw_crest = _load(_asset("assets", "environment", "ruins",
                          "core_ending_crest.png"))
ENDING_CREST_IMG = (_scale_fit(_strip_white(_raw_crest, tolerance=15),
                               160, 160)
                    if _raw_crest else None)

print("=== Heart assets loaded ===\n")


# =========================================================
# EVENT HANDLER
# =========================================================
def handle_event(event):
    if event.type != pygame.KEYDOWN:
        return False

    if RT.opening_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
            _advance_opening()
        return True

    if RT.choice_open:
        if event.key in (pygame.K_LEFT, pygame.K_a):
            RT.choice_cursor = (RT.choice_cursor - 1) % len(CHOICES)
            sound_system.play("blip")
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            RT.choice_cursor = (RT.choice_cursor + 1) % len(CHOICES)
            sound_system.play("blip")
        elif event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            _commit_choice()
        return True

    if RT.epilogue_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
            _advance_epilogue()
        return True

    if RT.status_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            RT.status_open = False
            RT.ending_card_open = True
        return True

    if RT.ending_card_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            RT.ending_card_open = False
            RT.finished = True
            _set(FLAG_ENDING, True)
            _set(FLAG_DONE, True)
        return True

    if RT.finished:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            _finish_to_title()
        return True

    if event.key == pygame.K_e:
        if _player_in(CHOICE_RECT, 60) and not _flag(FLAG_CHOICE_MADE):
            RT.choice_open = True
            RT.choice_cursor = 0
            sound_system.play("ui_open")
            return True

    return False


def _start_opening():
    RT.opening_open = True
    RT.opening_index = 0
    RT.opening_just_opened = True


def _play_opening_voice():
    if not (0 <= RT.opening_index < len(OPENING)):
        return
    text, speaker = OPENING[RT.opening_index]
    if speaker is None:
        sound_system.stop_voice()
        return
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _advance_opening():
    RT.opening_index += 1
    if RT.opening_index >= len(OPENING):
        RT.opening_open = False
        RT.opening_just_opened = False
        sound_system.stop_voice()
        _toast("Approach the Heart and press E.")
    else:
        _play_opening_voice()


def _commit_choice():
    choice_id = CHOICES[RT.choice_cursor]["id"]
    story_state.STATE.set_flag("ending_" + choice_id, True)
    _set(FLAG_CHOICE_MADE, True)
    RT.choice_open = False
    sound_system.play("correct")

    RT.epilogue_open = True
    RT.epilogue_index = 0
    RT.epilogue_name = choice_id
    RT.epilogue_just_opened = True


def _play_epilogue_voice():
    seq = EPILOGUES.get(RT.epilogue_name, [])
    if not (0 <= RT.epilogue_index < len(seq)):
        return
    text, speaker = seq[RT.epilogue_index]
    if speaker is None:
        sound_system.stop_voice()
        return
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _advance_epilogue():
    seq = EPILOGUES.get(RT.epilogue_name, [])
    RT.epilogue_index += 1
    if RT.epilogue_index >= len(seq):
        RT.epilogue_open = False
        RT.epilogue_just_opened = False
        sound_system.stop_voice()
        RT.status_open = True
        RT.status_timer = 0
    else:
        _play_epilogue_voice()


def _finish_to_title():
    RT.finished = False
    import main as _main
    _main.game_state = "title"
    _main.start_fade_in()


def _resolve_ending_id():
    """Return the id of whichever ending flag is set, else 'rebuild'."""
    for choice in CHOICES:
        if story_state.STATE.get_flag("ending_" + choice["id"]):
            return choice["id"]
    return "rebuild"


# =========================================================
# UPDATE
# =========================================================
def update():
    if RT.toast_timer > 0:
        RT.toast_timer -= 1
    if RT.opening_just_opened:
        RT.opening_just_opened = False
        _play_opening_voice()
    if RT.epilogue_just_opened:
        RT.epilogue_just_opened = False
        _play_epilogue_voice()
    if RT.status_open:
        RT.status_timer += 1
    RT.pulse += 0.05


# =========================================================
# DRAWING — BACKGROUND
# =========================================================
def draw_background(screen):
    if HEART_BG:
        screen.blit(HEART_BG, (0, 0))
        return

    screen.fill((6, 8, 14))
    for y in range(0, HEIGHT, 40):
        a = int((y / HEIGHT) * 20)
        pygame.draw.line(screen, (20 + a, 30 + a, 50 + a),
                         (0, y), (WIDTH, y))

    cx, cy = WIDTH // 2, HEIGHT // 2
    for r, col in [(400, (60, 100, 140)),
                   (300, (80, 130, 180)),
                   (200, (100, 160, 220)),
                   (120, (150, 200, 240))]:
        pygame.draw.circle(screen, col, (cx, cy), r, 2)


def draw_altar(screen):
    r = CHOICE_RECT
    pulse = int((math.sin(RT.pulse) + 1) * 4)

    if ALTAR_IMG:
        sprite_x = r.centerx - ALTAR_IMG.get_width() // 2
        sprite_y = r.bottom - ALTAR_IMG.get_height()
        glow = pygame.Surface((ALTAR_IMG.get_width() + 100,
                                ALTAR_IMG.get_height() + 100), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (200, 220, 255, 40 + pulse),
                            (0, 0, glow.get_width(), glow.get_height()))
        screen.blit(glow, (sprite_x - 50, sprite_y - 50))
        screen.blit(ALTAR_IMG, (sprite_x, sprite_y))
        _draw_label(screen, "THE HEART", r.centerx, sprite_y - 24)
    else:
        for rad, col in [(90 + pulse, (120, 180, 240, 40)),
                         (70 + pulse, (160, 220, 255, 70)),
                         (45, (220, 240, 255, 130))]:
            glow = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, col, (rad, rad), rad)
            screen.blit(glow, (r.centerx - rad, r.centery - rad))
        pygame.draw.circle(screen, (220, 240, 255),
                           (r.centerx, r.centery), 50, 2)
        _draw_label(screen, "THE HEART", r.centerx, r.centery - 80)


def _draw_null_holo(screen, cx, cy, tint):
    """Shared Null-hologram renderer used by opening + epilogue."""
    pulse = int((math.sin(pygame.time.get_ticks() / 150) + 1) * 6)

    if NULL_HOLO_IMG:
        glow = pygame.Surface((NULL_HOLO_IMG.get_width() + 160,
                                NULL_HOLO_IMG.get_height() + 160),
                               pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (*tint, 35 + pulse),
                            (0, 0, glow.get_width(), glow.get_height()))
        screen.blit(glow, (cx - glow.get_width() // 2,
                            cy - glow.get_height() // 2 + 20))
        screen.blit(NULL_HOLO_IMG,
                    (cx - NULL_HOLO_IMG.get_width() // 2,
                     cy - NULL_HOLO_IMG.get_height() // 2 + 20))
        return

    for r, a in [(140 + pulse, 40), (100 + pulse, 70), (60, 120)]:
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*tint, a), (r, r), r)
        screen.blit(glow, (cx - r, cy - r))


# =========================================================
# DRAWING — FOREGROUND
# =========================================================
def draw_prompt(screen):
    if is_blocking_input():
        return
    if _flag(FLAG_CHOICE_MADE):
        return
    if not _player_in(CHOICE_RECT, 60):
        return
    msg = small_font.render("Press E — Decide the Core's fate", True, WHITE)
    box = pygame.Rect(WIDTH // 2 - msg.get_width() // 2 - 14,
                      HEIGHT - 110, msg.get_width() + 28, 28)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (10, 12, 20, 220), surf.get_rect(), border_radius=6)
    pygame.draw.rect(surf, (*GOLD, 180), surf.get_rect(), 2, border_radius=6)
    screen.blit(surf, box.topleft)
    screen.blit(msg, (box.centerx - msg.get_width() // 2, box.y + 6))


def draw_opening(screen):
    if not RT.opening_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 220))
    screen.blit(ov, (0, 0))

    _draw_null_holo(screen, WIDTH // 2, 210, (255, 120, 90))

    line, sp = OPENING[RT.opening_index]
    _draw_box(screen, line, sp or "TRANSMISSION", (255, 160, 110))


def draw_choice(screen):
    if not RT.choice_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 235))
    screen.blit(ov, (0, 0))

    panel = pygame.Rect(WIDTH // 2 - 480, 120, 960, 560)
    surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (12, 16, 26, 250), surf.get_rect(), border_radius=14)
    screen.blit(surf, panel.topleft)
    pygame.draw.rect(screen, (200, 160, 100), panel, 3, border_radius=14)

    title = font.render("Choose the Fate of the Core", True, (245, 220, 130))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 22))

    sub = small_font.render(
        "No choice is free. Each has its cost.",
        True, (180, 180, 190))
    screen.blit(sub, (panel.centerx - sub.get_width() // 2, panel.y + 58))

    card_w = 280
    card_h = 340
    gap = 30
    total_w = card_w * 3 + gap * 2
    start_x = panel.centerx - total_w // 2
    card_y = panel.y + 110

    for i, choice in enumerate(CHOICES):
        cx = start_x + i * (card_w + gap)
        card = pygame.Rect(cx, card_y, card_w, card_h)
        selected = (i == RT.choice_cursor)

        if selected:
            glow = pygame.Surface((card_w + 24, card_h + 24), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*choice["colour"], 100),
                             (0, 0, card_w + 24, card_h + 24),
                             border_radius=14)
            screen.blit(glow, (card.x - 12, card.y - 12))
            pygame.draw.rect(screen, (36, 42, 54), card, border_radius=12)
            pygame.draw.rect(screen, choice["colour"], card, 3, border_radius=12)
        else:
            pygame.draw.rect(screen, (24, 28, 38), card, border_radius=12)
            pygame.draw.rect(screen, (80, 90, 100), card, 2, border_radius=12)

        # Sigil — asset if available, else procedural diamond
        sig_y = card.y + 80
        pulse = int((math.sin(RT.pulse + i * 1.3) + 1) * 3)
        sigil = SIGIL_IMGS.get(choice["id"])

        if sigil:
            glow = pygame.Surface((sigil.get_width() + 60,
                                    sigil.get_height() + 60), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*choice["colour"], 45 + pulse),
                                (0, 0, glow.get_width(), glow.get_height()))
            screen.blit(glow, (card.centerx - glow.get_width() // 2,
                                sig_y - glow.get_height() // 2))
            screen.blit(sigil, (card.centerx - sigil.get_width() // 2,
                                 sig_y - sigil.get_height() // 2))
        else:
            for r, a in [(55 + pulse, 40), (40 + pulse, 70), (22, 130)]:
                glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*choice["colour"], a), (r, r), r)
                screen.blit(glow, (card.centerx - r, sig_y - r))
            pygame.draw.polygon(screen, choice["colour"], [
                (card.centerx, sig_y - 26),
                (card.centerx + 20, sig_y),
                (card.centerx, sig_y + 26),
                (card.centerx - 20, sig_y)])
            pygame.draw.polygon(screen, (255, 255, 255), [
                (card.centerx, sig_y - 26),
                (card.centerx + 20, sig_y),
                (card.centerx, sig_y + 26),
                (card.centerx - 20, sig_y)], 1)

        title_s = font.render(choice["title"], True,
                              choice["colour"] if selected else (200, 200, 210))
        screen.blit(title_s, (card.centerx - title_s.get_width() // 2,
                               card.y + 150))

        for j, ln in enumerate(_wrap(choice["sub"], small_font, card_w - 30)):
            s = small_font.render(ln, True,
                                  (220, 230, 240) if selected else (160, 170, 180))
            screen.blit(s, (card.centerx - s.get_width() // 2,
                            card.y + 200 + j * 22))

    hint = small_font.render(
        "←/→ choose  ·  [E] commit",
        True, (170, 170, 180))
    screen.blit(hint, (panel.centerx - hint.get_width() // 2,
                       panel.bottom - 30))


def _wrap(text, font_obj, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = cur + w + " "
        if font_obj.size(test)[0] <= max_w:
            cur = test
        else:
            if cur: lines.append(cur.strip())
            cur = w + " "
    if cur: lines.append(cur.strip())
    return lines


def draw_epilogue(screen):
    if not RT.epilogue_open:
        return
    seq = EPILOGUES.get(RT.epilogue_name, [])
    if not seq:
        return

    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 230))
    screen.blit(ov, (0, 0))

    _draw_null_holo(screen, WIDTH // 2, 230, (200, 220, 255))

    line, sp = seq[RT.epilogue_index]
    _draw_box(screen, line, sp or "THE CORE", (220, 230, 250))


def draw_status(screen):
    if not RT.status_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 245))
    screen.blit(ov, (0, 0))

    mono = pygame.font.SysFont("consolas", 22)

    # Reveal lines progressively — one every 25 frames
    shown = min(len(SYSTEM_STATUS), RT.status_timer // 25)
    start_y = HEIGHT // 2 - 140

    for i in range(shown):
        text, col = SYSTEM_STATUS[i]
        if text:
            s = mono.render(text, True, col)
            screen.blit(s, (WIDTH // 2 - s.get_width() // 2,
                            start_y + i * 34))

    if shown >= len(SYSTEM_STATUS):
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            hint = small_font.render("[E] Continue", True, (180, 180, 180))
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2,
                               HEIGHT - 90))


def draw_ending_card(screen):
    if not RT.ending_card_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 245))
    screen.blit(ov, (0, 0))

    ending_titles = {
        "preserve":    ("THE QUIET ARCHIVE",  "Ending A"),
        "reintegrate": ("A SECOND CHANCE",    "Ending B"),
        "rebuild":     ("A NEW ARCHITECTURE", "Ending C"),
    }
    choice = _resolve_ending_id()
    title_text, sub_text = ending_titles.get(choice, ("THE CORE — DRUKORA", ""))

    # Crest (if asset present)
    if ENDING_CREST_IMG:
        crest_y = HEIGHT // 2 - 240
        screen.blit(ENDING_CREST_IMG,
                    (WIDTH // 2 - ENDING_CREST_IMG.get_width() // 2, crest_y))

    big = pygame.font.SysFont("georgia", 56, bold=True)
    title = big.render(title_text, True, (245, 220, 130))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 80))

    small = pygame.font.SysFont("georgia", 22, italic=True)
    sub = small.render(sub_text, True, (200, 180, 150))
    screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 - 6))

    tag = pygame.font.SysFont("georgia", 26, italic=True)
    line = tag.render("THE CORE — DRUKORA", True, (220, 200, 170))
    screen.blit(line, (WIDTH // 2 - line.get_width() // 2, HEIGHT // 2 + 70))

    if (pygame.time.get_ticks() // 500) % 2 == 0:
        hint = small_font.render("[E] Continue", True, (180, 180, 180))
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 90))


def draw_finished(screen):
    if not RT.finished:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 245))
    screen.blit(ov, (0, 0))

    big = pygame.font.SysFont("georgia", 56, bold=True)
    title = big.render("THE CORE — DRUKORA", True, (245, 220, 130))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 90))

    sub = pygame.font.SysFont("georgia", 24, italic=True)
    tag = sub.render("The first journey ends.", True, (220, 200, 170))
    screen.blit(tag, (WIDTH // 2 - tag.get_width() // 2, HEIGHT // 2 - 20))

    note = small_font.render(
        "Somewhere inside the Core, the one who altered the channels is still listening.",
        True, (170, 180, 200))
    screen.blit(note, (WIDTH // 2 - note.get_width() // 2, HEIGHT // 2 + 40))

    again = small_font.render("Press ENTER to return to title", True, (200, 190, 180))
    screen.blit(again, (WIDTH // 2 - again.get_width() // 2, HEIGHT // 2 + 100))


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


def _draw_box(screen, line, speaker, colour):
    box = pygame.Rect(100, HEIGHT - 180, WIDTH - 200, 130)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (10, 12, 20, 245), surf.get_rect(), border_radius=10)
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
    draw_altar(screen)


def draw_foreground_layer(screen):
    draw_prompt(screen)
    draw_opening(screen)
    draw_choice(screen)
    draw_epilogue(screen)
    draw_status(screen)
    draw_ending_card(screen)
    draw_finished(screen)
    draw_toast(screen)


def on_enter():
    if not _flag(FLAG_ENTERED):
        _set(FLAG_ENTERED, True)
        try:
            import drukma_commentary
            drukma_commentary.trigger("core_heart_entered")
        except Exception:
            pass
        story_state.STATE.add_journal_entry(
            "The Heart of the Core",
            "The final chamber. The Core itself hums in the centre of the room.\n\n"
            "Null is here — calmer than before, and waiting.\n\n"
            "The choice I make now will define what Drukora becomes.",
            source="The Heart of the Core"
        )
        _start_opening()