"""
tashi_quest.py — Phase 1c with Workshop Yard + Phase 1d commentary hook.

The workshop now reads as a distinct location: bigger footprint, dirt
ground, wooden fence, giant broken gear prop, chimney smoke.
"""

import pygame
import math
import random
import story_state
import sound_system
from setting import WIDTH, HEIGHT, small_font, font, WHITE, GOLD


# =========================================================
# QUEST FLAGS
# =========================================================
FLAG_STARTED     = "tashi_quest_started"
FLAG_INSPECTED   = "tashi_workshop_inspected"
FLAG_DIAGNOSED   = "tashi_component_diagnosed"
FLAG_COIL_TAKEN  = "tashi_component_taken"
FLAG_COMPLETE    = "tashi_quest_complete"


# =========================================================
# WORLD POSITIONS  (bigger footprint — 100x70)
# =========================================================
WORKSHOP_RECT  = pygame.Rect(270, 585, 100, 70)
INSPECT_RADIUS = 65
TASHI_RECT     = pygame.Rect(240, 620, 24, 32)


# =========================================================
# THE 5 COMPONENTS
# =========================================================
COMPONENTS = [
    {"id": "input",      "name": "Brass Crank Lever",  "function": "Input",
     "desc": "Receives the operator's motion.",
     "broken": False, "hint": "It still turns smoothly."},
    {"id": "processing", "name": "Copper Gear Train",  "function": "Processing",
     "desc": "Transforms motion into useful work.",
     "broken": True,  "hint": "A tooth is cracked. Motion never reaches the lamp."},
    {"id": "output",     "name": "Lamp Crystal",       "function": "Output",
     "desc": "Shows the result of the operation.",
     "broken": False, "hint": "It would glow if the mechanism turned."},
    {"id": "memory",     "name": "Wax Memory Drum",    "function": "Memory",
     "desc": "Records the current operation.",
     "broken": False, "hint": "Its surface is clean but intact."},
    {"id": "storage",    "name": "Iron Storage Chest", "function": "Storage",
     "desc": "Preserves completed records.",
     "broken": False, "hint": "Its lock is rusted but functional."},
]


# =========================================================
# ASSET HELPERS
# =========================================================
def _strip_white(surface, tolerance=25):
    surface = surface.convert_alpha()
    w, h = surface.get_size()
    for x in range(w):
        for y in range(h):
            r, g, b, a = surface.get_at((x, y))
            if a < 20:
                continue
            if (r > 255 - tolerance and
                    g > 255 - tolerance and
                    b > 255 - tolerance):
                surface.set_at((x, y), (0, 0, 0, 0))
    return surface


def _scale_fit(surface, max_w, max_h):
    w, h = surface.get_size()
    if w == 0 or h == 0:
        return surface
    scale = min(max_w / w, max_h / h)
    return pygame.transform.smoothscale(
        surface, (max(1, int(w * scale)), max(1, int(h * scale))))


def _load_workshop():
    try:
        img = pygame.image.load(
            "assets/environment/buildings/broken_workshop.png"
        ).convert_alpha()
        img = _scale_fit(img, 180, 150)
        img = _strip_white(img, tolerance=30)
        print(f"Loaded broken_workshop.png → {img.get_size()}")
        return img
    except (pygame.error, FileNotFoundError) as e:
        print(f"WARNING: broken_workshop.png not found: {e}")
        return None


def _load_components():
    try:
        sheet = pygame.image.load(
            "assets/environment/objects/workshop_parts_sheet.png"
        ).convert_alpha()
        w, h = sheet.get_size()
        cell_w = w // 5
        icon_h = int(h * 0.72)
        icons = []
        for i in range(5):
            cell = pygame.Surface((cell_w, icon_h), pygame.SRCALPHA)
            cell.blit(sheet, (0, 0), (i * cell_w, 0, cell_w, icon_h))
            cell = _strip_white(cell, tolerance=25)
            cell = _scale_fit(cell, 48, 48)
            icons.append(cell)
        print(f"Loaded {len(icons)} workshop component icons")
        return icons
    except (pygame.error, FileNotFoundError) as e:
        print(f"WARNING: workshop_parts_sheet.png not found: {e}")
        return None


WORKSHOP_IMG     = _load_workshop()
COMPONENT_ICONS  = _load_components()


# =========================================================
# RUNTIME STATE
# =========================================================
class _RT:
    inspect_open     = False
    inspect_cursor   = 0
    wrong_attempts   = 0
    toast_text       = ""
    toast_timer      = 0
    smoke_particles  = []

RT = _RT()


def _flag(k, d=False):
    return story_state.STATE.get_flag(k, d)

def _set(k, v=True):
    story_state.STATE.set_flag(k, v)

def _near(rect, r):
    from player import player
    return (abs(player.centerx - rect.centerx) < r and
            abs(player.centery - rect.centery) < r)


def is_blocking_input():
    return RT.inspect_open


# =========================================================
# EVENT HANDLER
# =========================================================
def handle_event(event):
    if event.type != pygame.KEYDOWN:
        return False

    if RT.inspect_open:
        if event.key in (pygame.K_UP, pygame.K_w):
            RT.inspect_cursor = (RT.inspect_cursor - 1) % len(COMPONENTS)
            sound_system.play("blip"); return True
        if event.key in (pygame.K_DOWN, pygame.K_s):
            RT.inspect_cursor = (RT.inspect_cursor + 1) % len(COMPONENTS)
            sound_system.play("blip"); return True
        if event.key in (pygame.K_e, pygame.K_RETURN):
            _diagnose(); return True
        if event.key == pygame.K_ESCAPE:
            RT.inspect_open = False
            sound_system.play("ui_close"); return True
        return True

    if event.key == pygame.K_e:
        if (_flag(FLAG_STARTED) and not _flag(FLAG_DIAGNOSED)
                and _near(WORKSHOP_RECT, INSPECT_RADIUS)):
            RT.inspect_open = True
            RT.inspect_cursor = 0
            _set(FLAG_INSPECTED, True)
            sound_system.play("ui_open")
            return True

    return False


def _diagnose():
    chosen = COMPONENTS[RT.inspect_cursor]
    if chosen["broken"]:
        _set(FLAG_DIAGNOSED, True)
        RT.inspect_open = False
        sound_system.play("correct")
        _toast("Copper Gear Train identified. Tashi needs a Resonator Coil.")

        # ← PHASE 1d: Drukma reacts to the diagnosis
        try:
            import drukma_commentary
            drukma_commentary.trigger("workshop_diagnosed")
        except Exception as e:
            print(f"[tashi_quest] commentary trigger failed: {e}")

        story_state.STATE.add_journal_entry(
            "The Workshop Diagnosis",
            "I inspected the five components of Tashi's workshop mechanism.\n\n"
            "INPUT   — Brass Crank Lever: still turns.\n"
            "PROCESSING — Copper Gear Train: A TOOTH IS CRACKED.\n"
            "OUTPUT  — Lamp Crystal: would glow if the gears turned.\n"
            "MEMORY  — Wax Memory Drum: intact.\n"
            "STORAGE — Iron Storage Chest: lock rusted but functional.\n\n"
            "The processing stage has failed. Without it, the input "
            "never reaches the output.\n\n"
            "Tashi needs a Resonator Coil to rebuild the gear train.",
            source="Broken Workshop"
        )
    else:
        RT.wrong_attempts += 1
        sound_system.play("wrong")
        _toast(f"That part looks fine. Look again. ({RT.wrong_attempts})")


def _toast(text, duration=200):
    RT.toast_text = text
    RT.toast_timer = duration


def update():
    if RT.toast_timer > 0:
        RT.toast_timer -= 1

    # --- Chimney smoke ---
    if WORKSHOP_IMG and len(RT.smoke_particles) < 12 and random.random() < 0.15:
        r = WORKSHOP_RECT
        RT.smoke_particles.append({
            "x": r.centerx + 24,
            "y": r.bottom - 120,
            "vx": random.uniform(-0.3, 0.3),
            "vy": random.uniform(-0.6, -0.3),
            "life": 60,
            "max_life": 60,
            "size": random.randint(3, 6),
        })
    for p in RT.smoke_particles:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["life"] -= 1
    RT.smoke_particles = [p for p in RT.smoke_particles if p["life"] > 0]


# =========================================================
# DRAWING — WORKSHOP YARD
# =========================================================
def draw_workshop(screen):
    """Draw the whole yard: dirt ground, building, fence, gear prop, smoke."""
    r = WORKSHOP_RECT
    cx = r.centerx

    # 1. Dirt patch under the yard
    dirt_w, dirt_h = 200, 110
    dirt = pygame.Surface((dirt_w, dirt_h), pygame.SRCALPHA)
    pygame.draw.ellipse(dirt, (135, 105, 70, 200), (0, 0, dirt_w, dirt_h))
    pygame.draw.ellipse(dirt, (155, 122, 82, 160),
                        (8, 6, dirt_w - 16, dirt_h - 12))
    pygame.draw.ellipse(dirt, (110, 82, 55, 120),
                        (18, 14, dirt_w - 36, dirt_h - 28))
    for _ in range(8):
        px = random.Random(42).randint(10, dirt_w - 10)
        py = random.Random(43).randint(10, dirt_h - 10)
        pygame.draw.circle(dirt, (95, 75, 55, 180), (px, py), 2)
    screen.blit(dirt, (cx - dirt_w // 2, r.bottom - dirt_h + 14))

    # 2. Building
    if WORKSHOP_IMG:
        img = WORKSHOP_IMG
        if _flag(FLAG_COMPLETE):
            pulse = int((math.sin(pygame.time.get_ticks() / 400) + 1) * 3)
            gw, gh = img.get_width() + 40, img.get_height() + 20
            glow = pygame.Surface((gw, gh), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 210, 120, 50), (0, 0, gw, gh))
            pygame.draw.ellipse(glow, (255, 230, 160, 90),
                                (10, 10, gw - 20, gh - 20))
            screen.blit(glow, (cx - gw // 2,
                               r.bottom - img.get_height() - 4))

        screen.blit(img, (cx - img.get_width() // 2,
                          r.bottom - img.get_height() + 8))
    else:
        pygame.draw.rect(screen, (85, 58, 38), r)
        pygame.draw.rect(screen, (110, 78, 52), (r.x, r.y, r.width, 8))
        pygame.draw.polygon(screen, (60, 40, 26), [
            (r.x - 8, r.y + 2), (cx, r.y - 18), (r.right + 8, r.y + 2)])
        door = pygame.Rect(cx - 12, r.bottom - 22, 24, 22)
        pygame.draw.rect(screen, (45, 28, 18), door)
        pygame.draw.rect(screen, (215, 175, 70), door, 2)

    # 3. Giant broken gear prop
    gear_cx = r.right - 4
    gear_cy = r.bottom - 30
    gear_r = 26
    pygame.draw.circle(screen, (95, 65, 40), (gear_cx, gear_cy), gear_r)
    pygame.draw.circle(screen, (140, 100, 60), (gear_cx, gear_cy), gear_r, 3)
    pygame.draw.circle(screen, (60, 40, 25), (gear_cx, gear_cy), 8)
    pygame.draw.circle(screen, (140, 100, 60), (gear_cx, gear_cy), 8, 2)
    for i in range(12):
        a = math.radians(i * 30)
        tx = gear_cx + math.cos(a) * (gear_r + 3)
        ty = gear_cy + math.sin(a) * (gear_r + 3)
        pygame.draw.circle(screen, (120, 88, 52), (int(tx), int(ty)), 4)
        pygame.draw.circle(screen, (60, 40, 25), (int(tx), int(ty)), 4, 1)
    a = math.radians(200)
    tx = gear_cx + math.cos(a) * (gear_r + 3)
    ty = gear_cy + math.sin(a) * (gear_r + 3)
    pygame.draw.circle(screen, (90, 60, 35), (int(tx), int(ty)), 4)
    pygame.draw.line(screen, (40, 25, 15),
                     (gear_cx - 15, gear_cy - 8),
                     (gear_cx + 12, gear_cy + 14), 2)

    # 4. Wooden fence
    fence_y = r.bottom + 18
    fence_color = (100, 68, 42)
    fence_color_top = (135, 95, 60)
    for fx in range(r.left - 10, r.right + 15, 16):
        pygame.draw.rect(screen, fence_color,
                         (fx, fence_y - 12, 5, 14))
        pygame.draw.rect(screen, fence_color_top,
                         (fx, fence_y - 12, 5, 3))
    pygame.draw.rect(screen, fence_color,
                     (r.left - 10, fence_y - 8, r.width + 30, 2))
    pygame.draw.rect(screen, fence_color,
                     (r.left - 10, fence_y - 3, r.width + 30, 2))

    # 5. Chimney smoke
    for p in RT.smoke_particles:
        t = p["life"] / p["max_life"]
        alpha = int(t * 100)
        size = p["size"] + int((1 - t) * 4)
        smoke = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(smoke, (200, 200, 210, alpha),
                           (size, size), size)
        screen.blit(smoke, (int(p["x"]) - size, int(p["y"]) - size))

    # 6. Label
    label = small_font.render("BROKEN WORKSHOP", True, WHITE)
    bg = pygame.Surface((label.get_width() + 14, label.get_height() + 6),
                        pygame.SRCALPHA)
    pygame.draw.rect(bg, (0, 0, 0, 180), bg.get_rect(), border_radius=5)
    pygame.draw.rect(bg, (215, 175, 70, 160), bg.get_rect(), 1, border_radius=5)
    screen.blit(bg, (cx - bg.get_width() // 2, fence_y + 8))
    screen.blit(label, (cx - label.get_width() // 2, fence_y + 11))


# =========================================================
# DRAWING — INTERACTION PROMPT
# =========================================================
def draw_interaction_prompt(screen):
    if RT.inspect_open:
        return
    prompt = None
    if (_flag(FLAG_STARTED) and not _flag(FLAG_DIAGNOSED)
            and _near(WORKSHOP_RECT, INSPECT_RADIUS)):
        prompt = "Press E — Inspect Workshop Mechanism"
    if prompt is None:
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
# DRAWING — INSPECTION OVERLAY
# =========================================================
def draw_inspection(screen):
    if not RT.inspect_open:
        return

    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 170))
    screen.blit(ov, (0, 0))

    panel = pygame.Rect(WIDTH // 2 - 260, 70, 520, 470)
    surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (20, 24, 34, 245), surf.get_rect(), border_radius=10)
    pygame.draw.rect(surf, (*GOLD, 220), surf.get_rect(), 2, border_radius=10)
    screen.blit(surf, panel.topleft)

    title = font.render("Inspect the Workshop Mechanism", True, (245, 220, 130))
    screen.blit(title, (panel.centerx - title.get_width() // 2, panel.y + 14))

    sub = small_font.render(
        "One of these five parts has failed.  Up/Down choose · [E] confirm · [ESC] leave",
        True, (170, 170, 170))
    screen.blit(sub, (panel.centerx - sub.get_width() // 2, panel.y + 46))

    y = panel.y + 82
    for i, c in enumerate(COMPONENTS):
        row = pygame.Rect(panel.x + 18, y, panel.width - 36, 64)
        hovered = (i == RT.inspect_cursor)
        bg = (60, 50, 34) if hovered else (32, 34, 42)
        pygame.draw.rect(screen, bg, row, border_radius=6)
        pygame.draw.rect(screen,
                         (*GOLD, 200) if hovered else (80, 80, 90),
                         row, 2, border_radius=6)

        text_x = row.x + 12

        if COMPONENT_ICONS and i < len(COMPONENT_ICONS):
            icon = COMPONENT_ICONS[i]
            slot = pygame.Rect(row.x + 8, row.y + 8, 48, 48)
            ix = slot.centerx - icon.get_width() // 2
            iy = slot.centery - icon.get_height() // 2
            screen.blit(icon, (ix, iy))
            text_x = slot.right + 10

        screen.blit(small_font.render(c["name"], True, WHITE),
                    (text_x, row.y + 10))
        screen.blit(small_font.render(f"[{c['function']}]",
                                       True, (200, 180, 120)),
                    (text_x, row.y + 34))

        desc_x = text_x + 190
        screen.blit(small_font.render(c["desc"], True, (190, 190, 190)),
                    (desc_x, row.y + 10))
        screen.blit(small_font.render(c["hint"], True, (170, 170, 170)),
                    (desc_x, row.y + 34))

        y += 68


# =========================================================
# DRAWING — TOAST
# =========================================================
def draw_toast(screen):
    if RT.toast_timer <= 0:
        return
    msg = font.render(RT.toast_text, True, (245, 220, 130))
    box = pygame.Rect(WIDTH // 2 - msg.get_width() // 2 - 20, 60,
                      msg.get_width() + 40, 40)
    surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(surf, (12, 14, 22, 220), surf.get_rect(), border_radius=8)
    pygame.draw.rect(surf, (*GOLD, 200), surf.get_rect(), 2, border_radius=8)
    screen.blit(surf, box.topleft)
    screen.blit(msg, (box.centerx - msg.get_width() // 2, box.y + 8))


# =========================================================
# PUBLIC CALLERS (used by world.py)
# =========================================================
def draw_background(screen):
    draw_workshop(screen)


def draw_foreground(screen):
    draw_interaction_prompt(screen)
    draw_inspection(screen)
    draw_toast(screen)