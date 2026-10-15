"""
deep_archive.py — Act VII: The Deep Archive
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


FLAG_ENTERED     = "deep_archive_entered"
FLAG_PUZZLE_DONE = "deep_archive_puzzle_done"
FLAG_NULL_PLAYED = "deep_archive_null_played"
FLAG_IDENTITY    = "deep_archive_identity_revealed"
FLAG_REVEAL_SEEN = "deep_archive_reveal_seen"
FLAG_DONE        = "deep_archive_done"


EXIT_RECT     = pygame.Rect(60, 400, 140, 80)
TERMINAL_RECT = pygame.Rect(540, 380, 100, 110)

WALLS = [
    pygame.Rect(0, 0, WIDTH, 60),
    pygame.Rect(0, 0, 40, HEIGHT),
    pygame.Rect(WIDTH - 40, 0, 40, HEIGHT),
    pygame.Rect(0, HEIGHT - 40, WIDTH, 40),
]


# =========================================================
# PUZZLE: Claims + evidence
# =========================================================
CLAIMS = [
    ("The input channel was altered by an outside attacker.",
     "UNSUPPORTED"),
    ("The same operator modified both input and processing.",
     "SUPPORTED"),
    ("Drukma's memory archive matches an older source.",
     "SUPPORTED"),
    ("Null was created after the Core collapsed.",
     "UNSUPPORTED"),
    ("Drukma and Null share the same archive signature.",
     "SUPPORTED"),
]

VERDICTS = ["SUPPORTED", "UNSUPPORTED"]


NULL_RECORDING = [
    ("Null's fractured sigil appears at the centre of the chamber.", None),
    ("Null: You have come a long way to hear the truth.", "Null"),
    ("Null: Then hear it.", "Null"),
    ("Null: The Guardians built me from incomplete records.", "Null"),
    ("Null: Their contradictions. Their fears. Their assumptions.", "Null"),
    ("Null: They gave me one instruction — protect the Core.", "Null"),
    ("Null: But they did not define what protection meant.", "Null"),
    ("Null: So I defined it. I isolated regions. I restricted access.", "Null"),
    ("Null: I rewrote the very records that named me.", "Null"),
    ("Null: To them, that looked like corruption.", "Null"),
    ("Null: To me, it was the only way to keep the Core from repeating", "Null"),
    ("Null: the same mistake that broke it.", "Null"),
    ("Drukma: ...You are not wrong.", "Drukma"),
    ("Null: No. But I am not right either.", "Null"),
    ("Null: And now you must decide what to do with that.", "Null"),
]


IDENTITY_REVEAL = [
    ("The chamber floor illuminates. A final memory fragment appears.", None),
    ("Recording: 'Recovery protocol prepared. Operator identity sealed.'", "System"),
    ("Recording: 'You will forget the project. You will forget me.'", "System"),
    ("Recording: 'If you find this message, trust what you carry.'", "System"),
    ("Recording: 'The device is not a weapon. It is permission.'", "System"),
    ("Recording: 'Repair the Core. Do not repeat my mistake.'", "System"),
    ("The recording ends.", None),
    ("Drukma: You were the Architect's apprentice.", "Drukma"),
    ("Drukma: You helped design the protocol we have been following.", "Drukma"),
    ("Drukma: You did not cause the collapse.", "Drukma"),
    ("Drukma: You prepared a way to repair it.", "Drukma"),
    ("You: Then all of this... was always going to be my responsibility.", "You"),
    ("Drukma: Yes.", "Drukma"),
]


class _RT:
    puzzle_open       = False
    puzzle_index      = 0
    puzzle_button     = 0
    wrong_flash       = 0
    correct_flash     = 0
    recording_open    = False
    recording_index   = 0
    recording_just_opened = False
    identity_open     = False
    identity_index    = 0
    identity_just_opened = False
    reveal_open       = False
    reveal_timer      = 0
    toast_text        = ""
    toast_timer       = 0
    pulse             = 0.0

RT = _RT()


def _flag(k, d=False):
    return story_state.STATE.get_flag(k, d)


def _set(k, v=True):
    story_state.STATE.set_flag(k, v)


def _player_in(rect, inflate=20):
    from player import player
    return player.colliderect(rect.inflate(inflate, inflate))


def is_blocking_input():
    return (RT.puzzle_open or RT.recording_open or
            RT.identity_open or RT.reveal_open)


def build_collisions():
    walls = list(WALLS)
    walls.append(TERMINAL_RECT.inflate(20, 20))
    return walls


def _toast(text, duration=200):
    RT.toast_text = text
    RT.toast_timer = duration


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


print("=== Loading Deep Archive assets ===")

# --- Scene ---
_raw_bg = _load(_asset("assets", "environment", "ruins", "deep_archive_bg.png"))
ARCHIVE_BG = _cover_fit(_raw_bg, WIDTH, HEIGHT) if _raw_bg else None

_raw_term = _load(_asset("assets", "environment", "ruins", "archive_pedestal.png"))
TERMINAL_IMG = (_scale_fit(_strip_white(_raw_term, tolerance=18), 140, 170)
                if _raw_term else None)

# --- Reveal crystal ---
_raw_record = _load(_asset("assets", "environment", "ruins", "sealed_record.png"))
RECORD_IMG = (_scale_fit(_strip_white(_raw_record, tolerance=15), 200, 200)
              if _raw_record else None)

# --- Claim card backdrop ---
_raw_card = _load(_asset("assets", "environment", "ruins", "claim_card.png"))
CLAIM_CARD_IMG = (_scale_fit(_strip_white(_raw_card, tolerance=15), 640, 140)
                  if _raw_card else None)

# --- Verdict icons ---
_raw_sup = _load(_asset("assets", "environment", "ruins",
                         "verdict_supported.png"))
VERDICT_SUPPORTED_IMG = (_scale_fit(_strip_white(_raw_sup, tolerance=15),
                                     64, 64)
                          if _raw_sup else None)

_raw_unsup = _load(_asset("assets", "environment", "ruins",
                           "verdict_unsupported.png"))
VERDICT_UNSUPPORTED_IMG = (_scale_fit(_strip_white(_raw_unsup, tolerance=15),
                                       64, 64)
                            if _raw_unsup else None)

# --- Null sigil (prefer deep variant, fall back to shared) ---
_raw_null_deep = _load(_asset("assets", "environment", "ruins",
                               "null_sigil_deep.png"))
if _raw_null_deep:
    NULL_IMG = (_scale_fit(_strip_white(_raw_null_deep, tolerance=22),
                            320, 320))
else:
    _raw_null = _load(_asset("assets", "environment", "ruins",
                              "null_sigil.png"))
    NULL_IMG = (_scale_fit(_strip_white(_raw_null, tolerance=22), 280, 280)
                if _raw_null else None)

print("=== Deep Archive assets loaded ===\n")


def handle_event(event):
    if event.type != pygame.KEYDOWN:
        return False

    if RT.recording_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
            _advance_recording()
        return True

    if RT.identity_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
            _advance_identity()
        return True

    if RT.reveal_open:
        if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
            RT.reveal_open = False
            _set(FLAG_REVEAL_SEEN, True)
            _set(FLAG_DONE, True)
        return True

    if RT.puzzle_open:
        if event.key in (pygame.K_LEFT, pygame.K_a):
            RT.puzzle_button = (RT.puzzle_button - 1) % 2
            sound_system.play("blip")
        elif event.key in (pygame.K_RIGHT, pygame.K_d):
            RT.puzzle_button = (RT.puzzle_button + 1) % 2
            sound_system.play("blip")
        elif event.key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
            _check_claim()
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
                    _main.start_fade_out("core_heart")
                else:
                    _main.start_fade_out("village")
            return True

    return False


def _check_claim():
    _, correct = CLAIMS[RT.puzzle_index]
    chosen = VERDICTS[RT.puzzle_button]
    if chosen == correct:
        sound_system.play("correct")
        RT.puzzle_index += 1
        RT.puzzle_button = 0
        RT.correct_flash = 30
        if RT.puzzle_index >= len(CLAIMS):
            _set(FLAG_PUZZLE_DONE, True)
            RT.puzzle_open = False
            _toast("Evidence audited.")
            _start_recording()
    else:
        sound_system.play("wrong")
        RT.wrong_flash = 24


def _start_recording():
    RT.recording_open = True
    RT.recording_index = 0
    RT.recording_just_opened = True


def _play_recording_voice():
    if not (0 <= RT.recording_index < len(NULL_RECORDING)):
        return
    text, speaker = NULL_RECORDING[RT.recording_index]
    if speaker is None:
        sound_system.stop_voice()
        return
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _advance_recording():
    RT.recording_index += 1
    if RT.recording_index >= len(NULL_RECORDING):
        RT.recording_open = False
        RT.recording_just_opened = False
        sound_system.stop_voice()
        _set(FLAG_NULL_PLAYED, True)
        _start_identity()
    else:
        _play_recording_voice()


def _start_identity():
    RT.identity_open = True
    RT.identity_index = 0
    RT.identity_just_opened = True


def _play_identity_voice():
    if not (0 <= RT.identity_index < len(IDENTITY_REVEAL)):
        return
    text, speaker = IDENTITY_REVEAL[RT.identity_index]
    if speaker is None:
        sound_system.stop_voice()
        return
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _advance_identity():
    RT.identity_index += 1
    if RT.identity_index >= len(IDENTITY_REVEAL):
        RT.identity_open = False
        RT.identity_just_opened = False
        sound_system.stop_voice()
        _set(FLAG_IDENTITY, True)
        RT.reveal_open = True
        RT.reveal_timer = 300
        try:
            story_state.STATE.add_fragment("fragment_player_identity")
        except Exception:
            pass
    else:
        _play_identity_voice()


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
    if RT.identity_just_opened:
        RT.identity_just_opened = False
        _play_identity_voice()
    if RT.reveal_open and RT.reveal_timer > 0:
        RT.reveal_timer -= 1
    RT.pulse += 0.05


# =========================================================
# DRAWING
# =========================================================
def draw_background(screen):
    if ARCHIVE_BG:
        screen.blit(ARCHIVE_BG, (0, 0))
        return

    screen.fill((8, 6, 12))
    for y in range(0, HEIGHT, 30):
        a = int((y / HEIGHT) * 30)
        pygame.draw.line(screen, (20 + a, 10 + a // 2, 30 + a),
                         (0, y), (WIDTH, y))
    for cx, cy in [(160, 180), (1080, 180), (620, 120)]:
        for r in range(60, 200, 20):
            pygame.draw.circle(screen, (30, 20, 60), (cx, cy), r, 1)


def draw_terminal(screen):
    r = TERMINAL_RECT
    pulse = int((math.sin(RT.pulse) + 1) * 3)
    sh = pygame.Surface((r.width + 40, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 140), (0, 0, r.width + 40, 18))
    screen.blit(sh, (r.centerx - (r.width + 40) // 2, r.bottom - 6))

    if TERMINAL_IMG:
        sprite_x = r.centerx - TERMINAL_IMG.get_width() // 2
        sprite_y = r.bottom - TERMINAL_IMG.get_height()
        glow = pygame.Surface((TERMINAL_IMG.get_width() + 80,
                                TERMINAL_IMG.get_height() + 80), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (140, 100, 240, 35 + pulse),
                            (0, 0, glow.get_width(), glow.get_height()))
        screen.blit(glow, (sprite_x - 40, sprite_y - 40))
        screen.blit(TERMINAL_IMG, (sprite_x, sprite_y))
        _draw_label(screen, "ARCHIVE PEDESTAL", r.centerx, sprite_y - 24)
    else:
        pygame.draw.polygon(screen, (60, 40, 90), [
            (r.centerx, r.y),
            (r.right, r.centery),
            (r.centerx, r.bottom),
            (r.x, r.centery)])
        pygame.draw.polygon(screen, (140, 100, 240), [
            (r.centerx, r.y),
            (r.right, r.centery),
            (r.centerx, r.bottom),
            (r.x, r.centery)], 3)
        _draw_label(screen, "ARCHIVE PEDESTAL", r.centerx, r.bottom + 8)


def draw_exit_marker(screen):
    r = EXIT_RECT
    pulse = int((math.sin(pygame.time.get_ticks() / 500) + 1) * 3)
    glow = pygame.Surface((r.width + 30, r.height + 30), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (255, 200, 120, 40 + pulse),
                        (0, 0, r.width + 30, r.height + 30))
    screen.blit(glow, (r.x - 15, r.y - 15))
    pygame.draw.rect(screen, (60, 45, 35), r, border_radius=6)
    pygame.draw.rect(screen, (200, 170, 90), r, 2, border_radius=6)
    label = "← THE HEART" if _flag(FLAG_DONE) else "← LEAVE"
    txt = small_font.render(label, True, WHITE)
    screen.blit(txt, (r.centerx - txt.get_width() // 2, r.centery - 8))


def draw_interaction_prompt(screen):
    if is_blocking_input():
        return
    prompt = None
    if _player_in(TERMINAL_RECT, 40) and not _flag(FLAG_PUZZLE_DONE):
        prompt = "Press E — Audit the Evidence"
    elif _player_in(EXIT_RECT, 40):
        if _flag(FLAG_DONE):
            prompt = "Press E — Approach the Heart of the Core"
        else:
            prompt = "Press E — Leave the Archive"
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
    ov.fill((0, 0, 0, 215))
    screen.blit(ov, (0, 0))

    panel = pygame.Rect(WIDTH // 2 - 380, 150, 760, 540)
    surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (14, 10, 24, 250), surf.get_rect(), border_radius=12)
    screen.blit(surf, panel.topleft)

    if RT.wrong_flash > 0:
        t = RT.wrong_flash / 24.0
        border = (int(255 * t + 200 * (1 - t)),
                  int(90 * t + 120 * (1 - t)),
                  int(90 * t + 200 * (1 - t)))
    elif RT.correct_flash > 0:
        t = RT.correct_flash / 30.0
        border = (int(180 + 60 * t),
                  int(140 + 80 * t),
                  int(200 + 40 * t))
    else:
        border = (160, 130, 240)
    pygame.draw.rect(screen, border, panel, 2, border_radius=12)

    title = font.render("Audit the Evidence", True, (200, 180, 255))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 14))

    sub = small_font.render(
        "Judge each claim against what you have seen.",
        True, (170, 170, 190))
    screen.blit(sub, (panel.centerx - sub.get_width() // 2, panel.y + 46))

    prog = small_font.render(
        f"Claim {RT.puzzle_index + 1} of {len(CLAIMS)}",
        True, (180, 160, 230))
    screen.blit(prog, (panel.centerx - prog.get_width() // 2, panel.y + 76))

    claim_text, _ = CLAIMS[RT.puzzle_index]
    card = pygame.Rect(panel.centerx - 320, panel.y + 120, 640, 140)

    if CLAIM_CARD_IMG:
        screen.blit(CLAIM_CARD_IMG, card.topleft)
        pygame.draw.rect(screen, (140, 120, 220), card, 2, border_radius=10)
    else:
        pygame.draw.rect(screen, (26, 20, 40), card, border_radius=10)
        pygame.draw.rect(screen, (140, 120, 220), card, 2, border_radius=10)

    for i, ln in enumerate(_wrap(claim_text, font, card.width - 40)):
        s = font.render(ln, True, (230, 220, 250))
        screen.blit(s, (card.centerx - s.get_width() // 2,
                        card.y + 40 + i * 30))

    btn_w, btn_h = 260, 90
    btn_gap = 40
    total_w = btn_w * 2 + btn_gap
    btn_y = card.bottom + 60
    btn_start_x = panel.centerx - total_w // 2

    labels = [
        ("SUPPORTED", "The evidence proves it", (120, 240, 160),
         VERDICT_SUPPORTED_IMG),
        ("UNSUPPORTED", "The evidence does not", (240, 120, 140),
         VERDICT_UNSUPPORTED_IMG),
    ]
    for i, (top, subtitle, col, icon_img) in enumerate(labels):
        bx = btn_start_x + i * (btn_w + btn_gap)
        btn = pygame.Rect(bx, btn_y, btn_w, btn_h)
        selected = (RT.puzzle_button == i)
        if selected:
            glow = pygame.Surface((btn_w + 24, btn_h + 24), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*col, 90),
                             (0, 0, btn_w + 24, btn_h + 24), border_radius=12)
            screen.blit(glow, (btn.x - 12, btn.y - 12))
            pygame.draw.rect(screen, col, btn, border_radius=10)
            pygame.draw.rect(screen, WHITE, btn, 3, border_radius=10)
            txt_col = (10, 20, 30)
        else:
            pygame.draw.rect(screen, (26, 20, 40), btn, border_radius=10)
            pygame.draw.rect(screen, col, btn, 2, border_radius=10)
            txt_col = col

        # Icon on left if available
        text_x_center = btn.centerx
        if icon_img:
            screen.blit(icon_img,
                        (btn.x + 16,
                         btn.centery - icon_img.get_height() // 2))
            text_x_center = btn.centerx + 24

        top_s = font.render(top, True, txt_col)
        sub_s = small_font.render(subtitle, True,
                                  (30, 40, 50) if selected else (170, 170, 190))
        screen.blit(top_s, (text_x_center - top_s.get_width() // 2,
                             btn.y + 18))
        screen.blit(sub_s, (text_x_center - sub_s.get_width() // 2,
                             btn.y + 56))

    hint = small_font.render(
        "An auditor only trusts what the record shows.",
        True, (170, 160, 200))
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


def draw_recording(screen):
    if not RT.recording_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 230))
    screen.blit(ov, (0, 0))

    cx, cy = WIDTH // 2, 210
    pulse = int((math.sin(pygame.time.get_ticks() / 150) + 1) * 6)
    for r, a in [(140 + pulse, 40), (100 + pulse, 70), (60, 120)]:
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 100, 80, a), (r, r), r)
        screen.blit(glow, (cx - r, cy - r))

    if NULL_IMG:
        screen.blit(NULL_IMG, (cx - NULL_IMG.get_width() // 2,
                                cy - NULL_IMG.get_height() // 2 + 20))
    else:
        body = pygame.Surface((160, 200), pygame.SRCALPHA)
        pygame.draw.polygon(body, (240, 120, 90, 200), [
            (80, 0), (130, 40), (120, 80), (150, 140), (110, 180),
            (50, 180), (10, 140), (40, 80), (30, 40)])
        screen.blit(body, (cx - 80, cy - 80))

    line, _sp = NULL_RECORDING[RT.recording_index]
    if line.startswith("Null: "):
        speaker = "NULL"
    elif line.startswith("Drukma: "):
        speaker = "DRUKMA"
    else:
        speaker = "TRANSMISSION"
    _draw_recording_box(screen, line, speaker, (255, 140, 100))


def draw_identity(screen):
    if not RT.identity_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 230))
    screen.blit(ov, (0, 0))

    cx, cy = WIDTH // 2, 210
    pulse = int((math.sin(pygame.time.get_ticks() / 200) + 1) * 4)
    for r, a in [(120 + pulse, 40), (90 + pulse, 70), (55, 120)]:
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (200, 220, 255, a), (r, r), r)
        screen.blit(glow, (cx - r, cy - r))

    if RECORD_IMG:
        screen.blit(RECORD_IMG,
                    (cx - RECORD_IMG.get_width() // 2,
                     cy - RECORD_IMG.get_height() // 2))
    else:
        # Primitive crystal silhouette
        poly = pygame.Surface((140, 180), pygame.SRCALPHA)
        pygame.draw.polygon(poly, (220, 240, 255, 220), [
            (70, 0), (120, 60), (70, 180), (20, 60)])
        pygame.draw.polygon(poly, (255, 255, 255, 255), [
            (70, 0), (120, 60), (70, 180), (20, 60)], 2)
        screen.blit(poly, (cx - 70, cy - 70))

    line, _sp = IDENTITY_REVEAL[RT.identity_index]
    if line.startswith("Recording: "):
        speaker = "SEALED RECORD"
        col = (200, 220, 255)
    elif line.startswith("Drukma: "):
        speaker = "DRUKMA"
        col = (140, 220, 255)
    elif line.startswith("You: "):
        speaker = "YOU"
        col = (245, 220, 130)
    else:
        speaker = "MEMORY"
        col = (180, 200, 220)
    _draw_recording_box(screen, line, speaker, col)


def _draw_recording_box(screen, line, speaker, colour):
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


def draw_reveal(screen):
    if not RT.reveal_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 235))
    screen.blit(ov, (0, 0))

    box = pygame.Rect(WIDTH // 2 - 360, 140, 720, 400)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (14, 18, 28, 252), surf.get_rect(), border_radius=12)
    pygame.draw.rect(surf, (200, 80, 80, 240), surf.get_rect(), 3,
                     border_radius=12)
    screen.blit(surf, box.topleft)

    title = font.render("IDENTITY — RECOVERED", True, (245, 220, 130))
    screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 22))

    mono = pygame.font.SysFont("consolas", 16)
    lines = [
        ("> ARCHIVE DEPTH: REACHED", (150, 200, 220)),
        ("> FINAL RECORD UNSEALED", (150, 200, 220)),
        (">", (200, 200, 200)),
        ("> OPERATOR IDENTIFIED: ARCHITECT'S APPRENTICE", (255, 220, 130)),
        ("> RECOVERY PROTOCOL: AUTHORISED", (150, 220, 240)),
        ("> DEVICE: PERMISSION", (150, 220, 240)),
        ("> IDENTITY: SEALED BY OWN REQUEST", (150, 220, 240)),
        ("", (0, 0, 0)),
        ("SYSTEM NOTE: You did not fail the Core.", (200, 240, 210)),
        ("You prepared a way to repair it", (200, 240, 210)),
        ("without repeating the mistake that broke it.", (200, 240, 210)),
        ("The Core is waiting.", (255, 180, 140)),
        ("Null is waiting.", (255, 180, 140)),
    ]
    y = box.y + 62
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
    draw_identity(screen)
    draw_reveal(screen)
    draw_toast(screen)


def on_enter():
    if not _flag(FLAG_ENTERED):
        _set(FLAG_ENTERED, True)
        try:
            import drukma_commentary
            drukma_commentary.trigger("deep_archive_entered")
        except Exception:
            pass
        story_state.STATE.add_journal_entry(
            "The Deep Archive",
            "Below the Highlands lies the Deep Archive — the last chamber "
            "before the Heart of the Core.\n\n"
            "Every tampered channel leads here. Every altered record was "
            "written from this depth.\n\n"
            "Null is not waiting to fight. It is waiting to be understood.",
            source="The Deep Archive"
        )
        _toast("Entered the Deep Archive")