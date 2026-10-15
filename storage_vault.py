"""
storage_vault.py — Act V: The Storage Vault
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
FLAG_ENTERED     = "vault_entered"
FLAG_PUZZLE_DONE = "vault_puzzle_done"
FLAG_CHODEN_PLAYED = "vault_choden_played"
FLAG_REVEAL_SEEN = "vault_reveal_seen"
FLAG_DONE        = "vault_done"


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
# PUZZLE DATA
# =========================================================
VAULT_RECORDS = [
    ("REC-A · Village Ledger",
     "32 households · grain yield 412 sacks",
     "32 households · grain yield 412 sacks"),
    ("REC-B · Shrine Inventory",
     "7 crystal keys · 4 brass rings",
     "7 crystal keys · 4 brass rings"),
    ("REC-C · Signal Tower Log",
     "Tower 3: online. Tower 7: online.",
     "Tower 3: OFFLINE. Tower 7: online."),
    ("REC-D · Guardian Roll",
     "Dorji, Karma, Choden, Sonam, Dawa",
     "Dorji, Karma, Choden, Sonam, Dawa"),
    ("REC-E · Memory Index",
     "Fragments: 412 · Duplicates: 0",
     "Fragments: 412 · Duplicates: 0"),
]

CORRUPTED_ID = "REC-C"

CHAMBERS = ["INTACT", "CORRUPTED"]


CHODEN_RECORDING = [
    ("A holographic figure of a patient archivist appears above the vault.", None),
    ("I am Choden. Guardian of Storage.", "Choden_Recording"),
    ("Storage keeps what must survive forever.", "Choden_Recording"),
    ("But a record only survives if it can be trusted.", "Choden_Recording"),
    ("Every archive holds two copies — the active file", "Choden_Recording"),
    ("and the backup. If they diverge, one of them has been changed.", "Choden_Recording"),
    ("A system cannot decide which is correct.", "Choden_Recording"),
    ("Only the record-keeper can.", "Choden_Recording"),
    ("I have found a divergence I cannot explain.", "Choden_Recording"),
    ("Someone has been editing our backups.", "Choden_Recording"),
    ("The hologram fades.", None),
]


# =========================================================
# RUNTIME STATE
# =========================================================
class _RT:
    puzzle_open      = False
    puzzle_index     = 0
    puzzle_button    = 0
    wrong_flash      = 0
    correct_flash    = 0
    recording_open   = False
    recording_index  = 0
    recording_just_opened = False
    reveal_open      = False
    reveal_timer     = 0
    toast_text       = ""
    toast_timer      = 0
    vault_pulse      = 0.0

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


print("=== Loading Storage Vault assets ===")

# --- Scene ---
_raw_bg = _load(_asset("assets", "environment", "ruins", "storage_vault_bg.png"))
VAULT_BG = _cover_fit(_raw_bg, WIDTH, HEIGHT) if _raw_bg else None

_raw_term = _load(_asset("assets", "environment", "ruins", "vault_terminal.png"))
TERMINAL_IMG = (_scale_fit(_strip_white(_raw_term, tolerance=18), 140, 170)
                if _raw_term else None)

_raw_exit = _load(_asset("assets", "environment", "ruins", "vault_exit_arch.png"))
EXIT_IMG = (_scale_fit(_strip_white(_raw_exit, tolerance=15), 140, 180)
            if _raw_exit else None)

# --- Puzzle cards ---
_raw_primary = _load(_asset("assets", "environment", "ruins",
                             "vault_card_primary.png"))
CARD_PRIMARY_IMG = (_scale_fit(_strip_white(_raw_primary, tolerance=15),
                                330, 200)
                    if _raw_primary else None)

_raw_backup = _load(_asset("assets", "environment", "ruins",
                            "vault_card_backup.png"))
CARD_BACKUP_IMG = (_scale_fit(_strip_white(_raw_backup, tolerance=15),
                               330, 200)
                   if _raw_backup else None)

# --- Verdict icons ---
_raw_intact = _load(_asset("assets", "environment", "ruins",
                            "vault_intact.png"))
INTACT_IMG = (_scale_fit(_strip_white(_raw_intact, tolerance=15), 56, 56)
              if _raw_intact else None)

_raw_corrupt = _load(_asset("assets", "environment", "ruins",
                             "vault_corrupted.png"))
CORRUPTED_IMG = (_scale_fit(_strip_white(_raw_corrupt, tolerance=15), 56, 56)
                 if _raw_corrupt else None)

# --- Hologram ---
_raw_choden = _load(_asset("assets", "environment", "ruins", "choden_holo.png"))
CHODEN_IMG = (_scale_fit(_strip_white(_raw_choden, tolerance=22), 220, 300)
              if _raw_choden else None)

print("=== Vault assets loaded ===\n")


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
                story_state.STATE.add_fragment("fragment_backup_tamper")
            except Exception:
                pass
            try:
                import drukma_commentary
                drukma_commentary.trigger("backup_tamper_found")
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
                    _main.start_fade_out("network_highlands")
                else:
                    _main.start_fade_out("village")
            return True

    return False


def _check_puzzle_answer():
    rec_id, primary, backup = VAULT_RECORDS[RT.puzzle_index]
    is_corrupt = (rec_id == CORRUPTED_ID)
    chosen_corrupt = (RT.puzzle_button == 1)

    if chosen_corrupt == is_corrupt:
        sound_system.play("correct")
        RT.puzzle_index += 1
        RT.puzzle_button = 0
        RT.correct_flash = 30
        if RT.puzzle_index >= len(VAULT_RECORDS):
            _set(FLAG_PUZZLE_DONE, True)
            RT.puzzle_open = False
            _toast("Integrity check complete.")
            _start_recording()
    else:
        sound_system.play("wrong")
        RT.wrong_flash = 24


def _start_recording():
    RT.recording_open = True
    RT.recording_index = 0
    RT.recording_just_opened = True


def _play_recording_voice():
    if not (0 <= RT.recording_index < len(CHODEN_RECORDING)):
        return
    text, speaker = CHODEN_RECORDING[RT.recording_index]
    if speaker is None:
        sound_system.stop_voice()
        return
    if not sound_system.play_line(speaker, text):
        sound_system.play_voice(speaker)


def _advance_recording():
    RT.recording_index += 1
    if RT.recording_index >= len(CHODEN_RECORDING):
        RT.recording_open = False
        RT.recording_just_opened = False
        sound_system.stop_voice()
        _set(FLAG_CHODEN_PLAYED, True)
        RT.reveal_open = True
        RT.reveal_timer = 300
        try:
            story_state.STATE.add_fragment("fragment_choden_vault")
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
    if RT.correct_flash > 0:
        RT.correct_flash -= 1
    if RT.recording_just_opened:
        RT.recording_just_opened = False
        _play_recording_voice()
    if RT.reveal_open and RT.reveal_timer > 0:
        RT.reveal_timer -= 1
    RT.vault_pulse += 0.05


# =========================================================
# DRAWING — BACKGROUND
# =========================================================
def draw_background(screen):
    if VAULT_BG:
        screen.blit(VAULT_BG, (0, 0))
        return

    # Fallback: deep archive chamber with drawer banks
    screen.fill((16, 14, 10))
    pygame.draw.rect(screen, (28, 24, 18), (0, 0, WIDTH, 200))
    pygame.draw.rect(screen, (22, 18, 14), (0, 200, WIDTH, HEIGHT - 200))

    for side_x in (60, WIDTH - 220):
        for row in range(8):
            for col in range(3):
                dx = side_x + col * 56
                dy = 90 + row * 70
                pygame.draw.rect(screen, (48, 40, 30), (dx, dy, 48, 60))
                pygame.draw.rect(screen, (75, 62, 45), (dx, dy, 48, 60), 2)
                pygame.draw.rect(screen, (110, 90, 55), (dx + 20, dy + 28, 8, 4))
                pygame.draw.rect(screen, (60, 50, 38), (dx + 8, dy + 8, 32, 8))


def draw_terminal(screen):
    r = TERMINAL_RECT
    pulse = int((math.sin(RT.vault_pulse) + 1) * 3)

    sh = pygame.Surface((r.width + 40, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 140), (0, 0, r.width + 40, 18))
    screen.blit(sh, (r.centerx - (r.width + 40) // 2, r.bottom - 6))

    if TERMINAL_IMG:
        sprite_x = r.centerx - TERMINAL_IMG.get_width() // 2
        sprite_y = r.bottom - TERMINAL_IMG.get_height()
        glow = pygame.Surface((TERMINAL_IMG.get_width() + 80,
                                TERMINAL_IMG.get_height() + 80), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (200, 160, 90, 35 + pulse),
                            (0, 0, glow.get_width(), glow.get_height()))
        screen.blit(glow, (sprite_x - 40, sprite_y - 40))
        screen.blit(TERMINAL_IMG, (sprite_x, sprite_y))
        _draw_label(screen, "ARCHIVE TERMINAL", r.centerx, sprite_y - 24)
    else:
        pygame.draw.rect(screen, (56, 48, 34), r, border_radius=8)
        pygame.draw.rect(screen, (200, 160, 90), r, 3, border_radius=8)
        cx, cy = r.centerx, r.centery - 10
        for rad, col in [(46 + pulse, (200, 160, 90, 60)),
                         (32 + pulse, (255, 200, 120, 120)),
                         (18, (255, 240, 200, 220))]:
            glow = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, col, (rad, rad), rad)
            screen.blit(glow, (cx - rad, cy - rad))
        pygame.draw.circle(screen, (255, 240, 200), (cx, cy), 46, 2)
        _draw_label(screen, "ARCHIVE TERMINAL", r.centerx, r.bottom + 8)


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

    label = "← ASCEND" if _flag(FLAG_DONE) else "← LEAVE"
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
        prompt = "Press E — Inspect the Archive Terminal"
    elif _player_in(EXIT_RECT, 40):
        if _flag(FLAG_DONE):
            prompt = "Press E — Ascend to the Network Highlands"
        else:
            prompt = "Press E — Leave the Vault"

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

    panel = pygame.Rect(WIDTH // 2 - 380, 130, 760, 610)
    surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (24, 20, 14, 248), surf.get_rect(), border_radius=12)
    screen.blit(surf, panel.topleft)

    if RT.wrong_flash > 0:
        t = RT.wrong_flash / 24.0
        border = (int(255 * t + 200 * (1 - t)),
                  int(90 * t + 160 * (1 - t)),
                  int(90 * t + 90 * (1 - t)))
    elif RT.correct_flash > 0:
        t = RT.correct_flash / 30.0
        border = (int(180 + 60 * t),
                  int(200 + 40 * t),
                  int(120 + 60 * t))
    else:
        border = (215, 175, 70)
    pygame.draw.rect(screen, border, panel, 2, border_radius=12)

    title = font.render("Verify Record Integrity", True, (245, 220, 130))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 14))

    sub = small_font.render(
        "Compare the primary copy to the backup. Are they the same?",
        True, (180, 170, 140))
    screen.blit(sub, (panel.centerx - sub.get_width() // 2, panel.y + 46))

    rec_id, primary, backup = VAULT_RECORDS[RT.puzzle_index]
    prog = small_font.render(
        f"Record {RT.puzzle_index + 1} of {len(VAULT_RECORDS)}   ·   {rec_id}",
        True, (200, 180, 130))
    screen.blit(prog, (panel.centerx - prog.get_width() // 2, panel.y + 76))

    # --- Two-column compare ---
    card_w = 330
    card_h = 200
    gap = 30
    total_w = card_w * 2 + gap
    card_y = panel.y + 120
    left_x = panel.centerx - total_w // 2
    right_x = left_x + card_w + gap

    # PRIMARY card
    prim_rect = pygame.Rect(left_x, card_y, card_w, card_h)
    if CARD_PRIMARY_IMG:
        screen.blit(CARD_PRIMARY_IMG, prim_rect.topleft)
        pygame.draw.rect(screen, (120, 220, 240), prim_rect, 2,
                         border_radius=10)
    else:
        pygame.draw.rect(screen, (32, 44, 54), prim_rect, border_radius=10)
        pygame.draw.rect(screen, (120, 220, 240), prim_rect, 2,
                         border_radius=10)

    lbl = small_font.render("PRIMARY COPY", True, (140, 220, 240))
    screen.blit(lbl, (prim_rect.centerx - lbl.get_width() // 2,
                      prim_rect.y + 12))
    for i, ln in enumerate(_wrap(primary, font, card_w - 30)):
        s = font.render(ln, True, (220, 240, 250))
        screen.blit(s, (prim_rect.centerx - s.get_width() // 2,
                        prim_rect.y + 70 + i * 28))

    # BACKUP card
    bk_rect = pygame.Rect(right_x, card_y, card_w, card_h)
    if CARD_BACKUP_IMG:
        screen.blit(CARD_BACKUP_IMG, bk_rect.topleft)
        pygame.draw.rect(screen, (215, 175, 70), bk_rect, 2, border_radius=10)
    else:
        pygame.draw.rect(screen, (42, 34, 22), bk_rect, border_radius=10)
        pygame.draw.rect(screen, (215, 175, 70), bk_rect, 2, border_radius=10)

    lbl = small_font.render("BACKUP COPY", True, (245, 220, 130))
    screen.blit(lbl, (bk_rect.centerx - lbl.get_width() // 2,
                      bk_rect.y + 12))
    for i, ln in enumerate(_wrap(backup, font, card_w - 30)):
        s = font.render(ln, True, (245, 230, 210))
        screen.blit(s, (bk_rect.centerx - s.get_width() // 2,
                        bk_rect.y + 70 + i * 28))

    # --- Two verdict buttons ---
    btn_w = 260
    btn_h = 82
    btn_gap = 30
    total_bw = btn_w * 2 + btn_gap
    btn_y = card_y + card_h + 40
    btn_start_x = panel.centerx - total_bw // 2

    labels = [
        ("INTACT", "Primary matches backup", (120, 220, 140), INTACT_IMG),
        ("CORRUPTED", "Primary diverges from backup", (240, 120, 100),
         CORRUPTED_IMG),
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
            pygame.draw.rect(screen, (30, 26, 18), btn, border_radius=10)
            pygame.draw.rect(screen, col, btn, 2, border_radius=10)
            txt_col = col

        # Icon centered left if available
        text_x_center = btn.centerx
        if icon_img:
            screen.blit(icon_img,
                        (btn.x + 16,
                         btn.centery - icon_img.get_height() // 2))
            text_x_center = btn.centerx + 22

        top_s = font.render(top, True, txt_col)
        sub_s = small_font.render(subtitle, True,
                                  (30, 40, 50) if selected else (180, 170, 150))
        screen.blit(top_s, (text_x_center - top_s.get_width() // 2,
                             btn.y + 14))
        screen.blit(sub_s, (text_x_center - sub_s.get_width() // 2,
                             btn.y + 46))

    hint = small_font.render(
        "A record is only as trustworthy as its backup.",
        True, (170, 190, 210))
    screen.blit(hint, (panel.centerx - hint.get_width() // 2,
                       panel.bottom - 28))


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
    ov.fill((0, 0, 0, 200))
    screen.blit(ov, (0, 0))

    holo_cx, holo_cy = WIDTH // 2, 210
    pulse = int((math.sin(pygame.time.get_ticks() / 200) + 1) * 4)
    for r, a in [(110 + pulse, 40), (80 + pulse, 70), (50, 120)]:
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (200, 170, 100, a), (r, r), r)
        screen.blit(glow, (holo_cx - r, holo_cy - r))

    if CHODEN_IMG:
        screen.blit(CHODEN_IMG,
                    (holo_cx - CHODEN_IMG.get_width() // 2,
                     holo_cy - CHODEN_IMG.get_height() // 2 + 20))
    else:
        body = pygame.Surface((80, 110), pygame.SRCALPHA)
        pygame.draw.ellipse(body, (200, 170, 100, 200), (15, 0, 50, 60))
        pygame.draw.rect(body, (200, 170, 100, 200), (10, 55, 60, 40))
        screen.blit(body, (holo_cx - 40, holo_cy - 30))

    line, _sp = CHODEN_RECORDING[RT.recording_index]
    box = pygame.Rect(100, HEIGHT - 180, WIDTH - 200, 130)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (18, 14, 10, 240), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (215, 175, 70, 220), surf.get_rect(), 2,
                     border_radius=10)
    screen.blit(surf, box.topleft)

    spk = location_font.render("CHODEN — RECORDED MESSAGE", True, (245, 220, 130))
    screen.blit(spk, (box.x + 20, box.y + 14))

    for i, ln in enumerate(_wrap(line, small_font, box.width - 40)[:3]):
        screen.blit(small_font.render(ln, True, (240, 230, 210)),
                    (box.x + 20, box.y + 46 + i * 22))

    hint = small_font.render("[E] Continue", True, (180, 170, 140))
    screen.blit(hint, (box.right - hint.get_width() - 20, box.bottom - 22))


def draw_reveal(screen):
    if not RT.reveal_open:
        return
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 220))
    screen.blit(ov, (0, 0))

    box = pygame.Rect(WIDTH // 2 - 340, 150, 680, 360)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (18, 14, 10, 252), surf.get_rect(), border_radius=12)
    pygame.draw.rect(surf, (200, 80, 80, 240), surf.get_rect(), 3,
                     border_radius=12)
    screen.blit(surf, box.topleft)

    title = font.render("VAULT LOG — INTEGRITY FAILURE", True, (245, 220, 130))
    screen.blit(title, (box.centerx - title.get_width() // 2, box.y + 22))

    mono = pygame.font.SysFont("consolas", 16)
    lines = [
        ("> VAULT ACCESS: OK", (150, 200, 220)),
        ("> INTEGRITY CHECK: COMPLETE", (150, 200, 220)),
        ("> MISMATCH DETECTED: REC-C", (255, 120, 100)),
        ("> PRIMARY: Tower 3 online.", (200, 200, 200)),
        ("> BACKUP: Tower 3 OFFLINE.", (255, 120, 100)),
        ("> EDIT AUTHORISED: YES", (255, 220, 130)),
        ("> EDITOR: INTERNAL PROCESS", (255, 120, 100)),
        ("", (0, 0, 0)),
        ("SYSTEM NOTE: The backup was overwritten", (150, 220, 240)),
        ("by the same process that altered input", (150, 220, 240)),
        ("and processing. The pattern is not random.", (150, 220, 240)),
        ("Something inside the Core is rewriting the record", (255, 180, 140)),
        ("of its own tampering.", (255, 180, 140)),
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
    pygame.draw.rect(surf, (14, 12, 8, 220), surf.get_rect(), border_radius=8)
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
    draw_reveal(screen)
    draw_toast(screen)


def on_enter():
    if not _flag(FLAG_ENTERED):
        _set(FLAG_ENTERED, True)
        try:
            import drukma_commentary
            drukma_commentary.trigger("storage_vault_entered")
        except Exception:
            pass
        story_state.STATE.add_journal_entry(
            "The Storage Vault",
            "Below the Memory Monastery lies the Storage Vault — the "
            "kingdom's long-term archive.\n\n"
            "Every record here has two copies: the working primary, and "
            "a backup. If they diverge, one of them has been changed.\n\n"
            "Choden kept the vault. Choden would have seen the divergence "
            "before the collapse.",
            source="The Storage Vault"
        )
        _toast("Entered the Storage Vault")