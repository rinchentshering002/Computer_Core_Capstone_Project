import pygame
import math
import os
from setting import *
from player import player, draw_player
import story_state
import tashi_quest

# =========================================================
# BACKGROUND REMOVAL
# =========================================================
def remove_background(surface, tolerance=60):
    surface = surface.convert_alpha()
    w, h = surface.get_size()
    for x in range(w):
        for y in range(h):
            r, g, b, a = surface.get_at((x, y))
            if a < 20:
                continue
            if r > 255 - tolerance and g > 255 - tolerance and b > 255 - tolerance:
                surface.set_at((x, y), (0, 0, 0, 0))
                continue
            if abs(r - g) < 15 and abs(g - b) < 15 and abs(r - b) < 15:
                if 165 < r < 252:
                    surface.set_at((x, y), (0, 0, 0, 0))
                    continue
            if r > 195 and g > 180 and b > 165 and abs(r - b) < 45:
                surface.set_at((x, y), (0, 0, 0, 0))
    return surface

# =========================================================
# VEGETATION SPRITE SHEET
# =========================================================
try:
    veg_sheet = pygame.image.load("assets/environment/trees/vegetation_pack.png").convert_alpha()
    SHEET_W, SHEET_H = veg_sheet.get_size()
    print(f"Loaded vegetation sheet: {SHEET_W}x{SHEET_H}")
except (pygame.error, FileNotFoundError):
    print("WARNING: vegetation_pack.png not found!")
    veg_sheet = pygame.Surface((1400, 800), pygame.SRCALPHA)
    veg_sheet.fill((50, 100, 50, 200))
    SHEET_W, SHEET_H = 1400, 800

def crop_sprite(x, y, w, h, target_w, target_h):
    x = max(0, min(x, SHEET_W - 1))
    y = max(0, min(y, SHEET_H - 1))
    w = min(w, SHEET_W - x)
    h = min(h, SHEET_H - y)
    if w <= 0 or h <= 0:
        return pygame.Surface((target_w, target_h), pygame.SRCALPHA)
    try:
        region = veg_sheet.subsurface(pygame.Rect(x, y, w, h)).copy()
        region = pygame.transform.smoothscale(region, (target_w, target_h))
        region = remove_background(region, tolerance=70)
        return region
    except ValueError:
        return pygame.Surface((target_w, target_h), pygame.SRCALPHA)

scale_x = SHEET_W / 1400.0
scale_y = SHEET_H / 800.0

def crop_scaled(sx, sy, sw, sh, tw, th):
    return crop_sprite(int(sx * scale_x), int(sy * scale_y),
                       int(sw * scale_x), int(sh * scale_y),
                       tw, th)

pine_big_sprite      = crop_scaled( 20,  20, 340, 760, 100, 220)
pavilion_tree_sprite = crop_scaled(510,  30, 290, 510,  95, 165)
small_tree_sprite    = crop_scaled(800,  50, 110, 330,  50, 145)
round_bush_sprite    = crop_scaled(995,  75, 155, 210,  55,  70)
flower_bush_sprite   = crop_scaled(1170, 50, 200, 220,  70,  75)
tall_grass_sprite    = crop_scaled(810, 460, 155, 165,  60,  65)
grass_bush_sprite    = crop_scaled(1020, 440, 135, 150,  55,  60)
small_grass_sprite   = crop_scaled(1170, 305, 145, 110,  45,  35)
flowers_1_sprite     = crop_scaled(540, 555, 220, 130,  75,  45)
flowers_2_sprite     = crop_scaled(765, 555, 175, 115,  65,  40)
flowers_3_sprite     = crop_scaled(955, 555, 130, 115,  55,  40)

# =========================================================
# SAFE IMAGE LOADERS
# =========================================================
def load_image(path, size=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if size:
            img = pygame.transform.smoothscale(img, size)
        return img
    except (pygame.error, FileNotFoundError):
        print(f"WARNING: {path} not found! Using placeholder.")
        w, h = size if size else (100, 100)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((200, 100, 200, 150))
        return surf

def load_sheet(path):
    try:
        img = pygame.image.load(path).convert_alpha()
        if img.get_size() != (1024, 1024):
            img = pygame.transform.scale(img, (1024, 1024))
        img = remove_background(img, tolerance=75)
        return img
    except (pygame.error, FileNotFoundError):
        print(f"WARNING: {path} not found!")
        surf = pygame.Surface((1024, 1024), pygame.SRCALPHA)
        surf.fill((200, 100, 200, 200))
        return surf

# =========================================================
# BUILDING IMAGES
# =========================================================
cpu_dzong_img        = load_image("assets/environment/buildings/cpu_dzong.png", (340, 220))
memory_monastery_img = load_image("assets/environment/buildings/memory_monastery.png", (220, 120))
input_village_img    = load_image("assets/environment/buildings/input_village.png", (180, 115))
output_tower_img     = load_image("assets/environment/buildings/output_tower.png", (150, 170))
storage_vault_img    = load_image("assets/environment/buildings/storage_vault.png", (220, 120))

# --- Resonator Coil pickup item (Broken Workshop reward) ---
try:
    resonator_coil_img = pygame.image.load(
        "assets/environment/objects/resonator_coil.png"
    ).convert_alpha()
    _cw, _ch = resonator_coil_img.get_size()
    _scale = min(44 / _cw, 44 / _ch) if _cw and _ch else 1.0
    resonator_coil_img = pygame.transform.smoothscale(
        resonator_coil_img,
        (max(1, int(_cw * _scale)), max(1, int(_ch * _scale)))
    )
    _w, _h = resonator_coil_img.get_size()
    for _x in range(_w):
        for _y in range(_h):
            _r, _g, _b, _a = resonator_coil_img.get_at((_x, _y))
            if _a < 20:
                continue
            if _r > 230 and _g > 230 and _b > 230:
                resonator_coil_img.set_at((_x, _y), (0, 0, 0, 0))
    print(f"Loaded resonator_coil.png → {resonator_coil_img.get_size()}")
except (pygame.error, FileNotFoundError) as e:
    print(f"WARNING: resonator_coil.png not found: {e}")
    resonator_coil_img = None

# =========================================================
# ENVIRONMENT OBJECTS (Cropping from AI Sheets)
# =========================================================
def load_and_crop(path, rect, size):
    """Helper to load a sheet, crop a specific part, remove bg, and scale."""
    try:
        sheet = pygame.image.load(path).convert_alpha()
        cropped = pygame.Surface(rect.size, pygame.SRCALPHA)
        cropped.blit(sheet, (0, 0), rect)
        cropped = remove_background(cropped, tolerance=60)
        return pygame.transform.smoothscale(cropped, size)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

# --- Rocks ---
rock_large_img    = load_and_crop("assets/environment/objects/rocks_sheet.png", pygame.Rect(50, 50, 400, 350), (80, 70))
rock_cluster_img  = load_and_crop("assets/environment/objects/rocks_sheet.png", pygame.Rect(1050, 500, 350, 250), (70, 50))
rock_mossy_img    = load_and_crop("assets/environment/objects/rocks_sheet.png", pygame.Rect(100, 500, 300, 200), (55, 45))
stone_lantern_img = load_and_crop("assets/environment/objects/rocks_sheet.png", pygame.Rect(830, 480, 180, 280), (50, 80))

# --- Bridges ---
bridge_wood_img   = load_and_crop("assets/environment/objects/bridges_sheet.png", pygame.Rect(880, 170, 300, 250), (100, 80))
bridge_stone_img  = load_and_crop("assets/environment/objects/bridges_sheet.png", pygame.Rect(30, 350, 350, 280), (110, 90))

# --- Water Decor ---
lily_pad_img      = load_and_crop("assets/environment/objects/water_sheet.png", pygame.Rect(220, 780, 250, 150), (55, 35))
reeds_img         = load_and_crop("assets/environment/objects/water_sheet.png", pygame.Rect(780, 780, 220, 220), (45, 45))
water_stones_img  = load_and_crop("assets/environment/objects/water_sheet.png", pygame.Rect(680, 440, 300, 100), (60, 25))

# =========================================================
# MOUNTAIN PANORAMA
# =========================================================
try:
    mountain_img_raw = pygame.image.load(
        "assets/environment/mountains/mountain_range.png"
    ).convert_alpha()
    M_W, M_H = mountain_img_raw.get_size()
    scale_factor = WIDTH / M_W
    new_w = WIDTH
    new_h = int(M_H * scale_factor)
    mountain_img = pygame.transform.smoothscale(mountain_img_raw, (new_w, new_h))
    mountain_img = remove_background(mountain_img, tolerance=30)
    MOUNTAIN_HEIGHT = new_h
    MOUNTAIN_TOP_Y = 325 - new_h
    print(f"Loaded mountain panorama at y={MOUNTAIN_TOP_Y}")
except (pygame.error, FileNotFoundError):
    print("WARNING: mountain_range.png not found")
    mountain_img = None
    MOUNTAIN_HEIGHT = 0
    MOUNTAIN_TOP_Y = 0

# =========================================================
# GUARDIAN SPRITES
# =========================================================
karma_sheet  = load_sheet("assets/sprite/karma_sprite.png")
dawa_sheet   = load_sheet("assets/sprite/dawa_sprite.png")
choden_sheet = load_sheet("assets/sprite/choden_sprite.png")
sonam_sheet  = load_sheet("assets/sprite/sonam_sprite.png")
dorji_sheet  = load_sheet("assets/sprite/dorji_sprite.png")
pema_sheet   = load_sheet("assets/sprite/pema_sprite.png")

# Tashi has his own sprite; fall back to Dorji if missing
if os.path.isfile("assets/sprite/tashi_sheet.png"):
    tashi_sheet = load_sheet("assets/sprite/tashi_sheet.png")
    print("Loaded tashi_sheet.png")
else:
    print("WARNING: tashi_sheet.png not found — using dorji_sheet placeholder")
    tashi_sheet = dorji_sheet

try:
    village_elder_sheet = pygame.image.load("assets/sprite/village_elder.png").convert_alpha()
    if village_elder_sheet.get_size() != (1024, 1024):
        village_elder_sheet = pygame.transform.scale(village_elder_sheet, (1024, 1024))
except pygame.error:
    print("WARNING: village_elder.png not found!")
    village_elder_sheet = pygame.Surface((1024, 1024), pygame.SRCALPHA)
    village_elder_sheet.fill((100, 100, 100))

SHEET_COLS = 4
SHEET_ROWS = 4

# =========================================================
# LEVEL UNLOCK SYSTEM
# =========================================================
UNLOCKED_LOCATIONS = set()

def unlock_location(name):
    UNLOCKED_LOCATIONS.add(name)
    print(f"UNLOCKED: {name}")

def is_unlocked(name):
    return name in UNLOCKED_LOCATIONS

def draw_locked_marker(screen, rect):
    cx = rect.centerx
    cy = rect.centery
    fog_w, fog_h = rect.width + 200, rect.height + 160
    fog = pygame.Surface((fog_w, fog_h), pygame.SRCALPHA)
    for offset in [(0, 0), (-30, 10), (30, 10), (-15, -20), (15, -20)]:
        for i in range(8, 0, -1):
            alpha = int((i / 8) ** 1.8 * 22)
            r = int(60 + (i * 12))
            pygame.draw.ellipse(
                fog, (230, 235, 230, alpha),
                (fog_w // 2 + offset[0] - r,
                 fog_h // 2 + offset[1] - r * 0.7,
                 r * 2, int(r * 1.4)))
    for i in range(6, 0, -1):
        alpha = int((i / 6) ** 1.5 * 30)
        r = int(30 + i * 14)
        pygame.draw.ellipse(
            fog, (200, 210, 205, alpha),
            (fog_w // 2 - r, fog_h // 2 - r * 0.8,
             r * 2, int(r * 1.6)))
    screen.blit(fog, (cx - fog_w // 2, cy - fog_h // 2))

    q_font = pygame.font.SysFont("georgia", 56, bold=True)
    q_surf = q_font.render("?", True, (250, 240, 210))
    q_shadow = q_font.render("?", True, (50, 35, 25))
    pulse = int((math.sin(pygame.time.get_ticks() / 500) + 1) * 4)
    glow = pygame.Surface((90 + pulse * 2, 90 + pulse * 2), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 220, 140, 50),
                       (glow.get_width() // 2, glow.get_height() // 2),
                       40 + pulse)

    q_y = rect.top + 8
    screen.blit(glow, (cx - glow.get_width() // 2, q_y - 12))
    screen.blit(q_shadow, (cx - q_surf.get_width() // 2 + 3, q_y + 3))
    screen.blit(q_surf, (cx - q_surf.get_width() // 2, q_y))

    lock_txt = small_font.render("LOCKED", True, (220, 210, 190))
    lock_bg = pygame.Rect(cx - lock_txt.get_width() // 2 - 10,
                          q_y + q_surf.get_height() + 4,
                          lock_txt.get_width() + 20,
                          lock_txt.get_height() + 6)
    bg_surf = pygame.Surface((lock_bg.width, lock_bg.height), pygame.SRCALPHA)
    pygame.draw.rect(bg_surf, (60, 45, 40, 200),
                     (0, 0, lock_bg.width, lock_bg.height), border_radius=6)
    pygame.draw.rect(bg_surf, (215, 175, 70, 180),
                     (0, 0, lock_bg.width, lock_bg.height), 1, border_radius=6)
    screen.blit(bg_surf, lock_bg.topleft)
    screen.blit(lock_txt, (cx - lock_txt.get_width() // 2, lock_bg.y + 3))

def draw_unlock_indicator(screen, rect):
    pulse = int((math.sin(pygame.time.get_ticks() / 400) + 1) * 5)
    glow_w = rect.width + 100
    glow_h = rect.height + 80
    glow = pygame.Surface((glow_w, glow_h), pygame.SRCALPHA)
    pygame.draw.ellipse(glow, (255, 220, 120, 40 + pulse),
                        (0, 0, glow_w, glow_h))
    pygame.draw.ellipse(glow, (255, 240, 180, 70),
                        (20, 20, glow_w - 40, glow_h - 40))
    screen.blit(glow, (rect.centerx - glow_w // 2, rect.centery - glow_h // 2))

# =========================================================
# LOCATIONS
# =========================================================
locations = {
    "Memory Monastery": pygame.Rect(390,  90, 220, 100),
    "Input Village":    pygame.Rect( 40, 290, 180, 100),
    "Output Tower":     pygame.Rect(790, 280, 160, 130),
    "CPU Dzong":        pygame.Rect(360, 275, 280, 160),
    "Storage Vault":    pygame.Rect(390, 530, 220, 110),
}

building_collisions = list(locations.values())
cpu_dzong_entrance = pygame.Rect(475, 425, 50, 25)
cpu_dzong_exit     = pygame.Rect(450, 575, 100, 50)
eastern_ruins_entrance = pygame.Rect(920, 400, 70, 130)

# ← Village-side gate sprite
try:
    village_gate_img = pygame.image.load(
        "assets/environment/ruins/gate_village_side.png"
    ).convert_alpha()
    village_gate_img = pygame.transform.smoothscale(village_gate_img, (100, 140))
    # Strip white background
    _gw, _gh = village_gate_img.get_size()
    for _gx in range(_gw):
        for _gy in range(_gh):
            _gr, _gg, _gb, _ga = village_gate_img.get_at((_gx, _gy))
            if _ga < 20:
                continue
            if _gr > 235 and _gg > 235 and _gb > 235:
                village_gate_img.set_at((_gx, _gy), (0, 0, 0, 0))
    print(f"Loaded village gate sprite → {village_gate_img.get_size()}")
except (pygame.error, FileNotFoundError):
    print("WARNING: village gate sprite not found — using primitive")
    village_gate_img = None

interior_walls = [
    pygame.Rect(0, 0, WIDTH, 115),
    pygame.Rect(0, 0, 25, HEIGHT),
    pygame.Rect(WIDTH - 25, 0, 25, HEIGHT),
    pygame.Rect(0, HEIGHT - 25, WIDTH, 25),
    pygame.Rect(335, 345, 330, 135),
]

# =========================================================
# SHRINE
# =========================================================
shrine_rect = pygame.Rect(260, 480, 80, 100)
shrine_activated = False

try:
    shrine_sheet = pygame.image.load("assets/environment/objects/shrine_sheet.png").convert_alpha()
    shrine_inactive_raw = shrine_sheet.subsurface(pygame.Rect(0, 0, 340, 380)).copy()
    shrine_inactive_img = remove_background(shrine_inactive_raw, tolerance=70)
    shrine_inactive_img = pygame.transform.smoothscale(shrine_inactive_img, (110, 120))

    shrine_active_raw = shrine_sheet.subsurface(pygame.Rect(410, 100, 600, 560)).copy()
    shrine_active_img = remove_background(shrine_active_raw, tolerance=70)
    shrine_active_img = pygame.transform.smoothscale(shrine_active_img, (110, 120))

    print("Loaded shrine sprite sheet!")
except Exception as e:
    print(f"WARNING: shrine_sheet.png not found or error cropping! {e}")
    shrine_inactive_img = None
    shrine_active_img = None

def draw_shrine(screen):
    r = shrine_rect
    if shrine_inactive_img and shrine_active_img:
        draw_soft_shadow(screen, r.centerx, r.bottom - 10, 100, 25, alpha=100)
        img = shrine_active_img if shrine_activated else shrine_inactive_img
        screen.blit(img, (r.centerx - img.get_width() // 2, r.bottom - img.get_height()))

        if not shrine_activated:
            pulse = int((math.sin(pygame.time.get_ticks() / 400) + 1) * 3)
            glow_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (150, 220, 240, 60), (60, 60), 30 + pulse)
            screen.blit(glow_surf, (r.centerx - 60, r.centery - 60))
    else:
        for i in range(3):
            alpha = 60 - i * 15
            shadow = pygame.Surface((r.width + 30, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, alpha), (0, 0, r.width + 30, 20))
            screen.blit(shadow, (r.centerx - (r.width + 30) // 2, r.bottom - 6))
        pygame.draw.rect(screen, (72, 65, 58), (r.x - 8, r.bottom - 18, r.width + 16, 18))
        pygame.draw.rect(screen, (125, 118, 105), (r.x + 12, r.y + 5, 16, r.height - 15))

    if not shrine_activated:
        label = small_font.render("Ancient Shrine", True, (245, 235, 210))
        bg_w = label.get_width() + 20
        bg_h = label.get_height() + 6
        bg_x = r.centerx - bg_w // 2
        bg_y = r.bottom + 6
        bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (0, 0, 0, 130), (0, 0, bg_w, bg_h), border_radius=6)
        screen.blit(bg_surf, (bg_x, bg_y))
        screen.blit(label, (r.centerx - label.get_width() // 2, bg_y + 3))

# =========================================================
# BROKEN WORKSHOP — DAMAGED COMPONENT
# =========================================================
damaged_component_rect = pygame.Rect(760, 630, 20, 20)

def draw_damaged_component(screen):
    """Draw the resonator coil pickup — hidden after collected or before diagnosed."""
    if story_state.STATE.get_flag("tashi_component_taken"):
        return
    if not story_state.STATE.get_flag("tashi_component_diagnosed"):
        return

    r = damaged_component_rect
    pulse = int((math.sin(pygame.time.get_ticks() / 400) + 1) * 3)

    # Glow
    glow = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 200, 100, 60), (30, 30), 20 + pulse)
    pygame.draw.circle(glow, (255, 230, 150, 90), (30, 30), 12 + pulse)
    screen.blit(glow, (r.centerx - 30, r.centery - 30))

    # Coil object — use sprite if loaded, else primitive circles
    if resonator_coil_img:
        bob = math.sin(pygame.time.get_ticks() / 500) * 2
        screen.blit(resonator_coil_img,
                    (r.centerx - resonator_coil_img.get_width() // 2,
                     r.centery - resonator_coil_img.get_height() // 2 + bob))
    else:
        pygame.draw.circle(screen, (160, 100, 50), (r.centerx, r.centery), 8)
        pygame.draw.circle(screen, (230, 170, 90), (r.centerx, r.centery), 5)
        pygame.draw.circle(screen, (255, 230, 150), (r.centerx - 1, r.centery - 1), 2)

    # Small sparks
    for i in range(3):
        a = (pygame.time.get_ticks() / 300 + i * 2.1) % (math.pi * 2)
        spark_x = r.centerx + math.cos(a) * 12
        spark_y = r.centery + math.sin(a) * 12
        spark = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(spark, (255, 240, 180, 180), (3, 3), 2)
        screen.blit(spark, (spark_x - 3, spark_y - 3))

    # Label
    label = small_font.render("Resonator Coil", True, (255, 230, 150))
    bg_w = label.get_width() + 12
    bg_h = label.get_height() + 4
    bg_x = r.centerx - bg_w // 2
    bg_y = r.bottom + 4
    bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
    pygame.draw.rect(bg_surf, (0, 0, 0, 160), (0, 0, bg_w, bg_h), border_radius=4)
    pygame.draw.rect(bg_surf, (215, 175, 70, 120), (0, 0, bg_w, bg_h), 1, border_radius=4)
    screen.blit(bg_surf, (bg_x, bg_y))
    screen.blit(label, (r.centerx - label.get_width() // 2, bg_y + 2))

# =========================================================
# NPCs & GUARDIANS
# =========================================================
npcs = [
    {"rect": pygame.Rect(75, 440, 24, 32), "name": "Village Elder"},
    {"rect": pygame.Rect(860, 510, 24, 32), "name": "Pema"},
    {"rect": pygame.Rect(240, 620, 24, 32), "name": "Tashi"},
]

input_guardian      = {"rect": pygame.Rect(155, 405, 24, 32), "name": "Dorji"}
processing_guardian = {"rect": pygame.Rect(480, 230, 24, 32), "name": "Karma"}
memory_guardian     = {"rect": pygame.Rect(640, 140, 24, 32), "name": "Dawa"}
storage_guardian    = {"rect": pygame.Rect(640, 580, 24, 32), "name": "Choden"}
output_guardian     = {"rect": pygame.Rect(865, 425, 24, 32), "name": "Sonam"}

guardian = processing_guardian

guardian_states = {
    "Karma":  {"sheet": karma_sheet,  "frame": 0, "timer": 0, "dir": "down"},
    "Dawa":   {"sheet": dawa_sheet,   "frame": 0, "timer": 0, "dir": "down"},
    "Choden": {"sheet": choden_sheet, "frame": 0, "timer": 0, "dir": "down"},
    "Sonam":  {"sheet": sonam_sheet,  "frame": 0, "timer": 0, "dir": "down"},
    "Dorji":  {"sheet": dorji_sheet,  "frame": 0, "timer": 0, "dir": "down"},
    "Pema":   {"sheet": pema_sheet,   "frame": 0, "timer": 0, "dir": "down"},
    "Village Elder": {"sheet": village_elder_sheet, "frame": 0, "timer": 0, "dir": "down"},
    "Tashi":  {"sheet": tashi_sheet,  "frame": 0, "timer": 0, "dir": "down"},
}

# =========================================================
# UI HELPERS
# =========================================================
def draw_prompt(screen, text, y, width=380):
    message = font.render(text, True, WHITE)
    box = pygame.Rect(WIDTH // 2 - width // 2, y, width, 35)
    box_surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    pygame.draw.rect(box_surf, (10, 12, 20, 220), (0, 0, box.width, box.height), border_radius=8)
    pygame.draw.rect(box_surf, (*GOLD, 180), (0, 0, box.width, box.height), 2, border_radius=8)
    screen.blit(box_surf, box.topleft)
    screen.blit(message, (box.centerx - message.get_width() // 2, box.y + 8))

def draw_label(screen, text, rect, offset):
    label = small_font.render(text, True, WHITE)
    padding = 6
    bg = pygame.Rect(rect.centerx - label.get_width() // 2 - padding,
                     rect.bottom + offset - 2,
                     label.get_width() + padding * 2,
                     label.get_height() + 4)
    bg_surf = pygame.Surface((bg.width, bg.height), pygame.SRCALPHA)
    pygame.draw.rect(bg_surf, (0, 0, 0, 165), (0, 0, bg.width, bg.height), border_radius=6)
    pygame.draw.rect(bg_surf, (215, 175, 70, 100), (0, 0, bg.width, bg.height), 1, border_radius=6)
    screen.blit(bg_surf, bg.topleft)
    screen.blit(label, (rect.centerx - label.get_width() // 2, rect.bottom + offset))

def draw_soft_shadow(screen, cx, cy, width, height, alpha=90):
    shadow = pygame.Surface((width, height), pygame.SRCALPHA)
    for i in range(3):
        a = alpha - i * 25
        sx = i * 3
        sy = i * 2
        pygame.draw.ellipse(shadow, (0, 0, 0, max(0, a)),
                            (sx, sy, width - sx * 2, height - sy * 2))
    screen.blit(shadow, (cx - width // 2, cy - height // 2))

def draw_npc(screen, npc):
    rect = npc["rect"]
    draw_soft_shadow(screen, rect.centerx, rect.bottom, 30, 10, alpha=80)
    pygame.draw.rect(screen, npc["color"], rect)
    pygame.draw.line(screen,
                     (max(0, npc["color"][0] - 40),
                      max(0, npc["color"][1] - 40),
                      max(0, npc["color"][2] - 40)),
                     (rect.right, rect.top), (rect.right, rect.bottom), 3)
    pygame.draw.circle(screen, SKIN, (rect.centerx, rect.top - 8), 12)
    pygame.draw.circle(screen, BLACK, (rect.centerx, rect.top - 16), 9)
    pygame.draw.circle(screen, BLACK, (rect.centerx - 4, rect.top - 8), 2)
    pygame.draw.circle(screen, BLACK, (rect.centerx + 4, rect.top - 8), 2)

    name = small_font.render(npc["name"], True, WHITE)
    bg = pygame.Rect(rect.centerx - name.get_width() // 2 - 5,
                     rect.bottom + 3, name.get_width() + 10, name.get_height() + 4)
    bg_surf = pygame.Surface((bg.width, bg.height), pygame.SRCALPHA)
    pygame.draw.rect(bg_surf, (0, 0, 0, 130), (0, 0, bg.width, bg.height), border_radius=4)
    screen.blit(bg_surf, bg.topleft)
    screen.blit(name, (rect.centerx - name.get_width() // 2, rect.bottom + 5))

def draw_guardian_sprite(screen, name, rect, player_rect):
    state = guardian_states[name]
    dx = player_rect.centerx - rect.centerx
    dy = player_rect.centery - rect.centery
    if abs(dx) > abs(dy):
        state["dir"] = "right" if dx > 0 else "left"
    else:
        state["dir"] = "down" if dy > 0 else "up"

    row = {"down": 0, "left": 1, "right": 2, "up": 3}[state["dir"]]
    state["timer"] += 1
    if state["timer"] >= 10:
        state["timer"] = 0
        state["frame"] = (state["frame"] + 1) % SHEET_COLS

    fw = state["sheet"].get_width() // SHEET_COLS
    fh = state["sheet"].get_height() // SHEET_ROWS
    frame = state["sheet"].subsurface(
        pygame.Rect(state["frame"] * fw, row * fh, fw, fh)).copy()
    DW, DH = 64, 80
    frame = pygame.transform.scale(frame, (DW, DH))

    draw_soft_shadow(screen, rect.centerx, rect.bottom, 45, 12, alpha=90)
    screen.blit(frame, (rect.centerx - DW // 2, rect.bottom - DH))

    name_surf = small_font.render(name, True, (255, 220, 130))
    bg = pygame.Rect(rect.centerx - name_surf.get_width() // 2 - 5,
                     rect.bottom + 4, name_surf.get_width() + 10, name_surf.get_height() + 4)
    bg_surf = pygame.Surface((bg.width, bg.height), pygame.SRCALPHA)
    pygame.draw.rect(bg_surf, (0, 0, 0, 150), (0, 0, bg.width, bg.height), border_radius=4)
    pygame.draw.rect(bg_surf, (215, 175, 70, 120), (0, 0, bg.width, bg.height), 1, border_radius=4)
    screen.blit(bg_surf, bg.topleft)
    screen.blit(name_surf, (rect.centerx - name_surf.get_width() // 2, rect.bottom + 6))

# =========================================================
# VEGETATION DRAWING
# =========================================================
def draw_pine_tree(screen, x, y, scale=1.0):
    w = int(100 * scale); h = int(220 * scale)
    img = pygame.transform.smoothscale(pine_big_sprite, (w, h))
    draw_soft_shadow(screen, x, y + 4, int(75 * scale), int(18 * scale), alpha=90)
    screen.blit(img, (x - w // 2, y - h + 8))

def draw_pavilion_tree(screen, x, y, scale=1.0):
    w = int(95 * scale); h = int(165 * scale)
    img = pygame.transform.smoothscale(pavilion_tree_sprite, (w, h))
    draw_soft_shadow(screen, x, y + 4, int(70 * scale), int(16 * scale), alpha=90)
    screen.blit(img, (x - w // 2, y - h + 6))

def draw_small_tree(screen, x, y, scale=1.0):
    w = int(50 * scale); h = int(145 * scale)
    img = pygame.transform.smoothscale(small_tree_sprite, (w, h))
    draw_soft_shadow(screen, x, y + 4, int(40 * scale), int(12 * scale), alpha=70)
    screen.blit(img, (x - w // 2, y - h + 5))

def draw_bush_v2(screen, x, y, scale=1.0):
    w = int(55 * scale); h = int(70 * scale)
    img = pygame.transform.smoothscale(round_bush_sprite, (w, h))
    draw_soft_shadow(screen, x, y + 3, int(42 * scale), int(12 * scale), alpha=70)
    screen.blit(img, (x - w // 2, y - h + 5))

def draw_flower_bush(screen, x, y, scale=1.0):
    w = int(70 * scale); h = int(75 * scale)
    img = pygame.transform.smoothscale(flower_bush_sprite, (w, h))
    draw_soft_shadow(screen, x, y + 3, int(50 * scale), int(14 * scale), alpha=70)
    screen.blit(img, (x - w // 2, y - h + 5))

def draw_tall_grass(screen, x, y, scale=1.0):
    w = int(60 * scale); h = int(65 * scale)
    img = pygame.transform.smoothscale(tall_grass_sprite, (w, h))
    screen.blit(img, (x - w // 2, y - h + 4))

def draw_grass_bush(screen, x, y, scale=1.0):
    w = int(55 * scale); h = int(60 * scale)
    img = pygame.transform.smoothscale(grass_bush_sprite, (w, h))
    screen.blit(img, (x - w // 2, y - h + 4))

def draw_grass_tuft(screen, x, y, scale=1.0):
    w = int(45 * scale); h = int(35 * scale)
    img = pygame.transform.smoothscale(small_grass_sprite, (w, h))
    screen.blit(img, (x - w // 2, y - h + 3))

def draw_flower_patch(screen, x, y, variant=1):
    if variant == 1:
        img_src, bw, bh = flowers_1_sprite, 75, 45
    elif variant == 2:
        img_src, bw, bh = flowers_2_sprite, 65, 40
    else:
        img_src, bw, bh = flowers_3_sprite, 55, 40
    screen.blit(img_src, (x - bw // 2, y - bh + 4))

def draw_rock(screen, x, y, scale=1.0):
    if rock_large_img:
        w = int(rock_large_img.get_width() * scale)
        h = int(rock_large_img.get_height() * scale)
        img = pygame.transform.smoothscale(rock_large_img, (w, h))
        draw_soft_shadow(screen, x, y + 4, int(w * 0.8), int(h * 0.3), alpha=70)
        screen.blit(img, (x - w // 2, y - h + 5))
    else:
        s = scale
        pygame.draw.polygon(screen, (72, 68, 62), [(x - 12*s, y + 4*s), (x - 8*s, y - 6*s), (x + 6*s, y - 8*s), (x + 12*s, y + 2*s), (x + 6*s, y + 6*s)])

def draw_rock_mossy(screen, x, y, scale=1.0):
    if rock_mossy_img:
        w = int(rock_mossy_img.get_width() * scale)
        h = int(rock_mossy_img.get_height() * scale)
        img = pygame.transform.smoothscale(rock_mossy_img, (w, h))
        draw_soft_shadow(screen, x, y + 3, int(w * 0.8), int(h * 0.3), alpha=60)
        screen.blit(img, (x - w // 2, y - h + 4))

def draw_log(screen, x, y):
    draw_soft_shadow(screen, x + 4, y + 6, 42, 10, alpha=70)
    pygame.draw.rect(screen, (95, 62, 38), (x - 18, y - 6, 36, 10))
    pygame.draw.rect(screen, (120, 82, 52), (x - 18, y - 6, 36, 4))
    pygame.draw.ellipse(screen, (140, 100, 62), (x + 16, y - 7, 8, 12))
    pygame.draw.ellipse(screen, (105, 72, 44), (x + 18, y - 5, 4, 8), 1)

def draw_lantern(screen, x, y):
    if stone_lantern_img:
        w, h = stone_lantern_img.get_size()
        draw_soft_shadow(screen, x, y + 4, int(w * 0.8), int(h * 0.2), alpha=90)
        screen.blit(stone_lantern_img, (x - w // 2, y - h + 8))

        glow = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 200, 100, 40), (40, 40), 30)
        screen.blit(glow, (x - 40, y - h + 10))
    else:
        pygame.draw.rect(screen, (72, 48, 32), (x - 2, y - 42, 4, 42))

# =========================================================
# ADVENTURE MAP ELEMENTS
# =========================================================
def draw_ground_patches(screen):
    patches = [
        (180, 340, 160, 50, (145, 155, 100, 55)),
        (620, 360, 180, 60, (140, 150, 95, 50)),
        (150, 620, 140, 45, (150, 155, 105, 50)),
        (700, 620, 160, 50, (145, 155, 100, 55)),
        (480, 340, 220, 45, (150, 160, 110, 40)),
        (300, 480, 160, 40, (140, 155, 100, 45)),
        (550, 480, 180, 45, (140, 155, 100, 45)),
    ]
    for x, y, w, h, color in patches:
        patch_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(patch_surf, color, (0, 0, w, h))
        screen.blit(patch_surf, (x, y))

def draw_river(screen):
    river_pts = [
        (-20, 380), (100, 400), (220, 420), (340, 445),
        (460, 460), (580, 470), (700, 470), (820, 460),
        (940, 440), (1020, 420),
    ]
    for i in range(len(river_pts) - 1):
        pygame.draw.line(screen, (45, 90, 120), river_pts[i], river_pts[i + 1], 46)
    for i in range(len(river_pts) - 1):
        pygame.draw.line(screen, (75, 130, 165), river_pts[i], river_pts[i + 1], 36)
    for i in range(len(river_pts) - 1):
        pygame.draw.line(screen, (130, 190, 220), river_pts[i], river_pts[i + 1], 4)

    for x, y in [(120, 405), (280, 435), (420, 458), (560, 470),
                 (720, 468), (880, 450)]:
        pygame.draw.line(screen, (200, 235, 250), (x - 6, y), (x + 6, y), 2)
        pygame.draw.line(screen, (200, 235, 250), (x - 3, y + 5), (x + 3, y + 5), 1)

    if lily_pad_img:
        for x, y in [(150, 420), (380, 460), (650, 480)]:
            screen.blit(lily_pad_img, (x - lily_pad_img.get_width() // 2, y))

    if reeds_img:
        for x, y in [(80, 410), (300, 440), (800, 465)]:
            screen.blit(reeds_img, (x - reeds_img.get_width() // 2, y - reeds_img.get_height() + 10))

    if water_stones_img:
        for x, y in [(200, 432), (500, 468), (750, 472)]:
            screen.blit(water_stones_img, (x - water_stones_img.get_width() // 2, y))

def draw_stone_bridge(screen, x, y):
    if bridge_stone_img:
        w, h = bridge_stone_img.get_size()
        draw_soft_shadow(screen, x, y + 4, int(w * 0.9), int(h * 0.4), alpha=90)
        screen.blit(bridge_stone_img, (x - w // 2, y - h + 8))
    else:
        pygame.draw.rect(screen, (130, 120, 105), (x - 44, y - 14, 88, 28))
        pygame.draw.rect(screen, (160, 148, 130), (x - 44, y - 14, 88, 4))

def draw_wooden_bridge(screen, x, y):
    if bridge_wood_img:
        w, h = bridge_wood_img.get_size()
        draw_soft_shadow(screen, x, y + 4, int(w * 0.9), int(h * 0.4), alpha=90)
        screen.blit(bridge_wood_img, (x - w // 2, y - h + 10))

def draw_winding_path(screen, points, width=34):
    for i in range(len(points) - 1):
        pygame.draw.line(screen, (128, 96, 62), points[i], points[i + 1], width + 6)
    for i in range(len(points) - 1):
        pygame.draw.line(screen, (172, 138, 95), points[i], points[i + 1], width)
    for i in range(len(points) - 1):
        pygame.draw.line(screen, (192, 158, 115), points[i], points[i + 1], width - 16)

def draw_ruined_wall(screen, x, y, segments=5):
    stone_colors = [(120, 112, 98), (140, 130, 115), (100, 92, 80)]
    for i in range(segments):
        bx = x + i * 24
        h = 22 + (i * 7) % 14
        color = stone_colors[i % 3]
        pygame.draw.rect(screen, color, (bx, y - h, 22, h))
        pygame.draw.rect(screen, (60, 55, 48), (bx, y - h, 22, h), 1)
        if i % 2 == 0:
            pygame.draw.polygon(screen, GRASS, [
                (bx, y - h), (bx + 8, y - h - 4),
                (bx + 22, y - h), (bx + 22, y - h + 2), (bx, y - h + 2)])
    shadow = pygame.Surface((segments * 24, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 60), (0, 0, segments * 24, 8))
    screen.blit(shadow, (x, y - 2))

def draw_signpost(screen, x, y, label):
    pygame.draw.rect(screen, (90, 60, 40), (x - 3, y - 34, 6, 34))
    pygame.draw.rect(screen, (110, 75, 50), (x - 3, y - 34, 2, 34))
    sign_w = 90
    sign_h = 22
    bx = x - sign_w // 2
    by = y - 46
    shadow = pygame.Surface((sign_w + 4, sign_h + 4), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 100), (0, 0, sign_w, sign_h), border_radius=3)
    screen.blit(shadow, (bx + 2, by + 2))
    pygame.draw.rect(screen, (150, 100, 60), (bx, by, sign_w, sign_h), border_radius=3)
    pygame.draw.rect(screen, (95, 62, 38), (bx, by, sign_w, sign_h), 2, border_radius=3)
    txt = small_font.render(label, True, (250, 240, 220))
    screen.blit(txt, (x - txt.get_width() // 2, by + (sign_h - txt.get_height()) // 2 + 1))

def draw_campfire(screen, x, y):
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        sx = x + math.cos(rad) * 18
        sy = y + math.sin(rad) * 8 + 2
        pygame.draw.circle(screen, (105, 100, 90), (int(sx), int(sy)), 4)
        pygame.draw.circle(screen, (140, 132, 118), (int(sx - 1), int(sy - 1)), 2)
    pygame.draw.line(screen, (75, 50, 35), (x - 12, y - 4), (x + 12, y + 2), 5)
    pygame.draw.line(screen, (75, 50, 35), (x - 12, y + 2), (x + 12, y - 4), 5)
    pulse = int((math.sin(pygame.time.get_ticks() / 200) + 1) * 2)
    glow = pygame.Surface((80, 80), pygame.SRCALPHA)
    pygame.draw.circle(glow, (255, 140, 60, 55), (40, 40), 30 + pulse)
    pygame.draw.circle(glow, (255, 200, 90, 90), (40, 40), 18 + pulse)
    screen.blit(glow, (x - 40, y - 40))
    flame_h = 14 + pulse
    pygame.draw.polygon(screen, (255, 120, 50), [(x - 6, y - 2), (x, y - flame_h), (x + 6, y - 2)])
    pygame.draw.polygon(screen, (255, 200, 80), [(x - 3, y - 2), (x, y - flame_h + 3), (x + 3, y - 2)])
    pygame.draw.polygon(screen, (255, 240, 160), [(x - 1, y - 2), (x, y - flame_h + 6), (x + 1, y - 2)])

# =========================================================
# MOUNTAINS
# =========================================================
def draw_mountains(screen):
    if mountain_img is not None:
        screen.blit(mountain_img, (0, MOUNTAIN_TOP_Y))
    else:
        back = [(0, 240), (100, 130), (180, 200), (280, 100),
                (400, 190), (520, 90), (620, 180),
                (740, 110), (840, 200), (1000, 130),
                (1000, 270), (0, 270)]
        pygame.draw.polygon(screen, (135, 155, 175), back)

# =========================================================
# CURRENT OBJECTIVE MAPPING
# =========================================================
OBJECTIVE_TO_LOCATION = {
    "Reach CPU Dzong":         "CPU Dzong",
    "Talk to Karma":           "CPU Dzong",
    "Visit Input Village":     "Input Village",
    "Return to Karma":         "CPU Dzong",
    "Visit Storage Vault":     "Storage Vault",
    "Visit Output Tower":      "Output Tower",
    "Visit Memory Monastery":  "Memory Monastery",
    "Report to Karma":         "CPU Dzong",
}

# =========================================================
# MEMORY MONASTERY — DISTANCE / SKY EFFECT
# =========================================================
def get_memory_monastery_scale():
    p_y = player.centery
    if p_y <= 240:
        return 1.0
    if p_y >= 460:
        return 0.55
    t = (460 - p_y) / (460 - 240)
    return 0.55 + t * 0.45

# =========================================================
# DRAW WORLD
# =========================================================
def draw_world(screen, quest_active, quest_objective, debug_all=False):
    screen.fill(GRASS)
    pygame.draw.rect(screen, SKY, (0, 0, WIDTH, 305))

    draw_mountains(screen)
    draw_ground_patches(screen)
    draw_river(screen)

    draw_winding_path(screen, [
        (0, 470), (150, 468), (300, 472), (450, 470),
        (550, 468), (700, 472), (850, 470), (1000, 470),
    ], width=32)
    draw_winding_path(screen, [
        (500, 180), (505, 220), (495, 260),
        (500, 300), (505, 340), (500, 380),
        (505, 420), (500, 465),
    ], width=26)
    draw_winding_path(screen, [
        (500, 470), (505, 510), (495, 545), (500, 575),
    ], width=26)
    draw_winding_path(screen, [
        (230, 470), (180, 462), (140, 470), (100, 465),
    ], width=22)
    draw_winding_path(screen, [
        (700, 470), (745, 462), (790, 468), (830, 465),
    ], width=22)

    draw_stone_bridge(screen, 450, 470)
    draw_wooden_bridge(screen, 300, 470)

    draw_ruined_wall(screen, 60, 550, segments=4)

    if is_unlocked("Storage Vault"):
        draw_campfire(screen, 780, 600)
        draw_log(screen, 745, 605)

    left_edge = [(15, 395, 0.70), (25, 465, 0.80), (15, 545, 0.72), (25, 615, 0.65), (30, 690, 0.60)]
    for x, y, s in left_edge:
        draw_pine_tree(screen, x, y, scale=s)
    right_edge = [(985, 400, 0.70), (975, 470, 0.80), (985, 545, 0.72), (975, 615, 0.65), (970, 690, 0.60)]
    for x, y, s in right_edge:
        draw_pine_tree(screen, x, y, scale=s)

    if is_unlocked("Input Village"):
        draw_pavilion_tree(screen, 118, 355, scale=0.75)
        draw_small_tree(screen, 195, 635, scale=0.80)
        draw_bush_v2(screen, 295, 335, scale=0.85)
        draw_bush_v2(screen, 275, 355, scale=0.70)
        draw_flower_bush(screen, 175, 590, scale=0.85)
        draw_flower_patch(screen, 290, 385, variant=1)

    if is_unlocked("Output Tower"):
        draw_pavilion_tree(screen, 882, 348, scale=0.72)
        draw_small_tree(screen, 805, 640, scale=0.78)
        draw_bush_v2(screen, 715, 350, scale=0.82)
        draw_bush_v2(screen, 735, 335, scale=0.68)
        draw_flower_bush(screen, 825, 598, scale=0.88)
        draw_flower_patch(screen, 710, 375, variant=2)

    if is_unlocked("Storage Vault"):
        draw_bush_v2(screen, 320, 630, scale=0.80)
        draw_bush_v2(screen, 340, 615, scale=0.65)
        draw_bush_v2(screen, 680, 640, scale=0.83)
        draw_bush_v2(screen, 660, 620, scale=0.68)
        draw_flower_patch(screen, 320, 605, variant=3)
        draw_flower_patch(screen, 685, 620, variant=1)

    draw_small_tree(screen, 55, 715, scale=0.65)
    draw_small_tree(screen, 945, 720, scale=0.65)

    draw_rock(screen, 135, 335, scale=0.85)
    draw_rock(screen, 145, 640, scale=0.85)
    draw_rock_mossy(screen, 175, 620, scale=1.0)

    draw_rock(screen, 865, 328, scale=0.85)
    draw_rock(screen, 855, 645, scale=0.85)
    draw_rock_mossy(screen, 830, 630, scale=1.0)

    draw_rock(screen, 60, 700, scale=0.85)
    draw_rock(screen, 940, 700, scale=0.85)

    for x, y in [(385, 630), (615, 640), (105, 405), (895, 398),
                 (465, 645), (535, 640), (155, 435), (845, 442),
                 (420, 350), (580, 355)]:
        draw_grass_tuft(screen, x, y, scale=1.0)

    for x, y in [(75, 380), (920, 390), (200, 680), (800, 680)]:
        draw_grass_bush(screen, x, y, scale=0.85)

    draw_flower_patch(screen, 550, 640, variant=2)
    draw_flower_patch(screen, 460, 605, variant=3)

    if is_unlocked("Input Village"):
        draw_signpost(screen, 175, 500, "← INPUT")
    if is_unlocked("Output Tower"):
        draw_signpost(screen, 815, 500, "OUTPUT →")
    if is_unlocked("Storage Vault"):
        draw_signpost(screen, 340, 620, "↓ STORAGE")
    if is_unlocked("Memory Monastery"):
        draw_signpost(screen, 660, 200, "↑ MEMORY")

    for x in [120, 220, 350, 550, 650, 780, 880]:
        draw_lantern(screen, x, 500)

    for name, rect in locations.items():
        if is_unlocked(name):
            if name == "Memory Monastery":
                scale = get_memory_monastery_scale()
                base_w, base_h = memory_monastery_img.get_size()
                new_w = max(20, int(base_w * scale))
                new_h = max(20, int(base_h * scale))

                sw = int(rect.width * 1.15 * scale)
                sh_h = max(4, int(26 * scale))
                shadow = pygame.Surface((sw, sh_h), pygame.SRCALPHA)
                for i in range(4):
                    a = 90 - i * 20
                    pygame.draw.ellipse(shadow, (0, 0, 0, max(0, a)),
                                        (i * 4, i * 2, sw - i * 8, sh_h - i * 4))
                screen.blit(shadow, (rect.centerx - sw // 2,
                                     rect.bottom - int(18 * scale)))

                if scale < 0.95:
                    aura_alpha = int((1.0 - scale) * 180)
                    aura = pygame.Surface((new_w + 60, new_h + 60), pygame.SRCALPHA)
                    pygame.draw.ellipse(aura, (200, 230, 255, aura_alpha // 3),
                                        (0, 0, new_w + 60, new_h + 60))
                    pygame.draw.ellipse(aura, (255, 245, 220, aura_alpha // 2),
                                        (15, 15, new_w + 30, new_h + 30))
                    screen.blit(aura, (rect.centerx - (new_w + 60) // 2,
                                       rect.bottom - new_h - 30))

                scaled_img = pygame.transform.smoothscale(
                    memory_monastery_img, (new_w, new_h))
                draw_x = rect.centerx - new_w // 2
                draw_y = rect.bottom - new_h
                screen.blit(scaled_img, (draw_x, draw_y))

                label_rect = pygame.Rect(draw_x, draw_y, new_w, new_h)
                draw_label(screen, name.upper(), label_rect, 8)
                continue

            w = int(rect.width * 1.15)
            h = 26
            shadow = pygame.Surface((w, h), pygame.SRCALPHA)
            for i in range(4):
                a = 90 - i * 20
                pygame.draw.ellipse(shadow, (0, 0, 0, max(0, a)),
                                    (i * 4, i * 2, w - i * 8, h - i * 4))
            screen.blit(shadow, (rect.centerx - w // 2, rect.bottom - 18))

            if name == "CPU Dzong":
                screen.blit(cpu_dzong_img, cpu_dzong_img.get_rect(center=rect.center))
            elif name == "Input Village":
                screen.blit(input_village_img, input_village_img.get_rect(center=rect.center))
            elif name == "Output Tower":
                screen.blit(output_tower_img, output_tower_img.get_rect(center=rect.center))
            elif name == "Storage Vault":
                screen.blit(storage_vault_img, storage_vault_img.get_rect(center=rect.center))

            draw_label(screen, name.upper(), rect, 8)
        else:
            draw_locked_marker(screen, rect)

    obj_location = OBJECTIVE_TO_LOCATION.get(quest_objective)
    if obj_location and obj_location in locations and is_unlocked(obj_location):
        draw_unlock_indicator(screen, locations[obj_location])

    # ← PHASE 2: Eastern Ruins entrance gate (unlocked after shrine)
    if story_state.STATE.get_flag("drukma_awake"):
        ent = eastern_ruins_entrance

        # Glow behind the gate
        pulse = int((math.sin(pygame.time.get_ticks() / 500) + 1) * 4)
        glow = pygame.Surface((ent.width + 40, ent.height + 40),
                              pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (90, 220, 240, 40 + pulse),
                            (0, 0, ent.width + 40, ent.height + 40))
        screen.blit(glow, (ent.centerx - (ent.width + 40) // 2,
                           ent.centery - (ent.height + 40) // 2))

        if village_gate_img:
            screen.blit(village_gate_img,
                        (ent.centerx - village_gate_img.get_width() // 2,
                         ent.bottom - village_gate_img.get_height() + 10))
        else:
            pygame.draw.rect(screen, (60, 45, 35), ent, border_radius=6)
            pygame.draw.rect(screen, (200, 170, 90), ent, 2, border_radius=6)

        # Label under gate
        txt = small_font.render("→ RUINS", True, (245, 220, 130))
        bg = pygame.Surface((txt.get_width() + 14, txt.get_height() + 6),
                            pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 0, 0, 180), bg.get_rect(), border_radius=5)
        pygame.draw.rect(bg, (215, 175, 70, 160), bg.get_rect(),
                         1, border_radius=5)
        screen.blit(bg, (ent.centerx - bg.get_width() // 2, ent.bottom + 6))
        screen.blit(txt, (ent.centerx - txt.get_width() // 2, ent.bottom + 9))

    draw_shrine(screen)
    tashi_quest.draw_background(screen)

    for npc in npcs:
        if npc["name"] == "Village Elder":
            draw_guardian_sprite(screen, "Village Elder", npc["rect"], player)
        elif npc["name"] == "Pema":
            draw_guardian_sprite(screen, "Pema", npc["rect"], player)
        elif npc["name"] == "Tashi":
            draw_guardian_sprite(screen, "Tashi", npc["rect"], player)

    draw_damaged_component(screen)

    if debug_all:
        if is_unlocked("Input Village"):
            draw_guardian_sprite(screen, "Dorji", input_guardian["rect"], player)
        if is_unlocked("Storage Vault"):
            draw_guardian_sprite(screen, "Choden", storage_guardian["rect"], player)
        if is_unlocked("Output Tower"):
            draw_guardian_sprite(screen, "Sonam", output_guardian["rect"], player)
        if is_unlocked("Memory Monastery"):
            draw_guardian_sprite(screen, "Dawa", memory_guardian["rect"], player)
    else:
        if quest_active and quest_objective == "Visit Input Village" and is_unlocked("Input Village"):
            draw_guardian_sprite(screen, "Dorji", input_guardian["rect"], player)
        if quest_active and quest_objective == "Visit Storage Vault" and is_unlocked("Storage Vault"):
            draw_guardian_sprite(screen, "Choden", storage_guardian["rect"], player)
        if quest_active and quest_objective == "Visit Output Tower" and is_unlocked("Output Tower"):
            draw_guardian_sprite(screen, "Sonam", output_guardian["rect"], player)
        if quest_active and quest_objective == "Visit Memory Monastery" and is_unlocked("Memory Monastery"):
            draw_guardian_sprite(screen, "Dawa", memory_guardian["rect"], player)

    draw_player(screen)
    tashi_quest.draw_foreground(screen)

# =========================================================
# CPU DZONG INTERIOR — Cyber-Monastery Redesign
# =========================================================
def draw_cpu_dzong_interior(screen):
    screen.fill((48, 32, 24))
    pygame.draw.rect(screen, (62, 42, 30), (0, 0, WIDTH, 400))

    plank_x = 0
    while plank_x < WIDTH:
        shade = 58 + ((plank_x // 40) % 3) * 6
        pygame.draw.rect(screen, (shade, shade - 22, shade - 38),
                         (plank_x, 0, 38, 400))
        pygame.draw.line(screen, (38, 24, 16),
                         (plank_x + 38, 0), (plank_x + 38, 400), 2)
        plank_x += 40

    pygame.draw.rect(screen, (30, 20, 14), (0, 0, WIDTH, 60))
    pygame.draw.rect(screen, (215, 175, 70), (0, 58, WIDTH, 4))
    pygame.draw.rect(screen, (140, 100, 40), (0, 62, WIDTH, 2))

    def draw_pillar(px):
        pw = 44
        pygame.draw.rect(screen, (38, 24, 18), (px - 4, 340, pw + 8, 24))
        pygame.draw.rect(screen, (72, 48, 32), (px, 340, pw, 24))
        pygame.draw.rect(screen, (215, 175, 70), (px, 344, pw, 2))
        pygame.draw.rect(screen, (85, 56, 36), (px, 55, pw, 285))
        pygame.draw.rect(screen, (62, 40, 26), (px + pw - 6, 55, 6, 285))
        pygame.draw.rect(screen, (108, 74, 48), (px, 55, 6, 285))
        knot_cx = px + pw // 2
        knot_cy = 200
        for r, col in [(16, (215, 175, 70)), (10, (140, 100, 40)), (4, (245, 220, 130))]:
            pygame.draw.circle(screen, col, (knot_cx, knot_cy), r, 2)
        for y in (110, 150, 250, 290):
            pygame.draw.rect(screen, (215, 175, 70), (px - 3, y, pw + 6, 4))
            pygame.draw.rect(screen, (140, 100, 40), (px - 3, y + 4, pw + 6, 1))
        pygame.draw.rect(screen, (72, 48, 32), (px - 6, 55, pw + 12, 16))
        pygame.draw.rect(screen, (215, 175, 70), (px - 6, 55, pw + 12, 3))

    for px in [100, 260, 696, 856]:
        draw_pillar(px)

    tap_w, tap_h = 260, 200
    tap_x = WIDTH // 2 - tap_w // 2
    tap_y = 90
    sh = pygame.Surface((tap_w + 20, tap_h + 20), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 120), (10, 10, tap_w, tap_h), border_radius=6)
    screen.blit(sh, (tap_x - 10, tap_y - 10))
    pygame.draw.rect(screen, (110, 28, 34), (tap_x, tap_y, tap_w, tap_h), border_radius=6)
    pygame.draw.rect(screen, (215, 175, 70), (tap_x, tap_y, tap_w, tap_h), 3, border_radius=6)
    pygame.draw.rect(screen, (150, 100, 40), (tap_x + 8, tap_y + 8, tap_w - 16, tap_h - 16), 1, border_radius=4)
    knot_cx = tap_x + tap_w // 2
    knot_cy = tap_y + tap_h // 2
    for i in range(4):
        a = math.radians(i * 90 + 45)
        x1 = knot_cx + math.cos(a) * 40
        y1 = knot_cy + math.sin(a) * 40
        x2 = knot_cx - math.cos(a) * 40
        y2 = knot_cy - math.sin(a) * 40
        pygame.draw.line(screen, (215, 175, 70), (x1, y1), (x2, y2), 3)
    pygame.draw.circle(screen, (215, 175, 70), (knot_cx, knot_cy), 24, 3)
    pygame.draw.circle(screen, (245, 220, 130), (knot_cx, knot_cy), 10, 2)

    flag_colors = [(85, 130, 200), (250, 250, 245), (210, 60, 55),
                   (70, 160, 85), (245, 200, 70)]
    for i in range(12):
        fx = 130 + i * 68
        fy = 68 + math.sin(i * 0.6) * 4
        color = flag_colors[i % 5]
        sway = math.sin(pygame.time.get_ticks() / 600 + i) * 2
        pts = [(fx, fy), (fx + 26, fy), (fx + 13 + sway, fy + 26)]
        pygame.draw.polygon(screen, color, pts)
        pygame.draw.polygon(screen, (50, 35, 20), pts, 1)

    def draw_hanging_lantern(lx, ly):
        pygame.draw.line(screen, (60, 45, 30), (lx, 60), (lx, ly), 2)
        pulse = int((math.sin(pygame.time.get_ticks() / 400) + 1) * 2)
        glow = pygame.Surface((90, 90), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 180, 80, 60), (45, 45), 34 + pulse)
        pygame.draw.circle(glow, (255, 210, 120, 90), (45, 45), 22 + pulse)
        screen.blit(glow, (lx - 45, ly - 20))
        pygame.draw.polygon(screen, (150, 60, 40), [
            (lx - 12, ly), (lx + 12, ly), (lx + 9, ly + 26), (lx - 9, ly + 26)])
        pygame.draw.rect(screen, (255, 220, 140), (lx - 6, ly + 6, 12, 14))
        pygame.draw.rect(screen, (60, 40, 28), (lx - 14, ly - 4, 28, 5))
        pygame.draw.rect(screen, (60, 40, 28), (lx - 12, ly + 26, 24, 4))
        pygame.draw.circle(screen, (215, 175, 70), (lx, ly + 32), 3)

    draw_hanging_lantern(200, 150)
    draw_hanging_lantern(WIDTH - 200, 150)

    pygame.draw.rect(screen, (72, 48, 30), (0, 400, WIDTH, HEIGHT - 400))
    for y in range(410, HEIGHT, 34):
        pygame.draw.line(screen, (52, 34, 20), (0, y), (WIDTH, y), 2)
        pygame.draw.line(screen, (98, 68, 44), (0, y + 2), (WIDTH, y + 2), 1)
    for row_idx, y in enumerate(range(410, HEIGHT, 34)):
        offset = (row_idx * 45) % 90
        for x in range(-45 + offset, WIDTH, 90):
            pygame.draw.line(screen, (48, 30, 18), (x, y), (x, y + 34), 2)

    cx, cy = WIDTH // 2, 500
    pulse = int((math.sin(pygame.time.get_ticks() / 500) + 1) * 4)

    for r, alpha, w in [(160 + pulse, 30, 2), (120, 50, 1), (70, 70, 1)]:
        ring = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(ring, (100, 200, 240, alpha), (r + 4, r + 4), r, w)
        screen.blit(ring, (cx - r - 4, cy - r - 4))

    for i in range(12):
        a = math.radians(i * 30 + pygame.time.get_ticks() * 0.01)
        x1 = cx + math.cos(a) * 55
        y1 = cy + math.sin(a) * 55
        x2 = cx + math.cos(a) * 155
        y2 = cy + math.sin(a) * 155
        pygame.draw.line(screen, (80, 170, 210), (x1, y1), (x2, y2), 1)

    core_cx, core_cy = WIDTH // 2, 340
    pulse2 = int((math.sin(pygame.time.get_ticks() / 300) + 1) * 6)

    pygame.draw.ellipse(screen, (30, 22, 16), (core_cx - 140, core_cy + 60, 280, 40))
    pygame.draw.rect(screen, (48, 34, 22), (core_cx - 130, core_cy + 30, 260, 50))
    pygame.draw.rect(screen, (72, 48, 32), (core_cx - 130, core_cy + 30, 260, 6))
    pygame.draw.rect(screen, (215, 175, 70), (core_cx - 130, core_cy + 76, 260, 4))

    for r, alpha in [(120 + pulse2, 25), (95 + pulse2, 40), (70, 60)]:
        glow = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(glow, (80, 160, 220, alpha), (r + 10, r + 10), r)
        screen.blit(glow, (core_cx - r - 10, core_cy - r - 10))

    for r, col in [(60, (45, 85, 115)), (48, (55, 110, 150)),
                   (36, (70, 150, 220)), (24, (170, 225, 255)), (12, (255, 255, 255))]:
        pygame.draw.circle(screen, col, (core_cx, core_cy), r)

    t = pygame.time.get_ticks() * 0.0008
    for angle_off, rx, ry in [(0, 100, 30), (60, 85, 25), (120, 115, 35)]:
        ring_surf = pygame.Surface((rx * 2 + 8, ry * 2 + 8), pygame.SRCALPHA)
        pygame.draw.ellipse(ring_surf, (215, 175, 70, 200),
                            (0, 0, rx * 2 + 4, ry * 2 + 4), 2)
        ring_surf = pygame.transform.rotate(ring_surf,
                                            math.degrees(angle_off + t * 30))
        rect = ring_surf.get_rect(center=(core_cx, core_cy))
        screen.blit(ring_surf, rect.topleft)

    core_label = location_font.render("THE COMPUTER CORE", True, (245, 220, 130))
    bg_lbl = pygame.Surface((core_label.get_width() + 24, 26), pygame.SRCALPHA)
    pygame.draw.rect(bg_lbl, (20, 14, 10, 200), (0, 0, bg_lbl.get_width(), 26), border_radius=6)
    pygame.draw.rect(bg_lbl, (215, 175, 70, 180), (0, 0, bg_lbl.get_width(), 26), 1, border_radius=6)
    screen.blit(bg_lbl, (core_cx - bg_lbl.get_width() // 2, core_cy + 90))
    screen.blit(core_label, (core_cx - core_label.get_width() // 2, core_cy + 94))

    for i in range(30):
        seed = i * 137
        dx_ = (seed * 73 + pygame.time.get_ticks() // 40) % WIDTH
        dy_ = (seed * 51 + pygame.time.get_ticks() // 30) % 400 + 100
        size = 1 + (i % 2)
        alpha = 40 + (i % 3) * 20
        dot = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(dot, (255, 230, 180, alpha), (size, size), size)
        screen.blit(dot, (dx_, dy_))

    title = title_font.render("CPU DZONG", True, (245, 220, 130))
    tshadow = title_font.render("CPU DZONG", True, (20, 12, 8))
    screen.blit(tshadow, (WIDTH // 2 - title.get_width() // 2 + 2, 27))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 25))

    subtitle = small_font.render("Chamber of the Computer Core", True, (220, 200, 170))
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 62))

    pygame.draw.rect(screen, (30, 20, 14), cpu_dzong_exit)
    pygame.draw.rect(screen, (72, 48, 32), cpu_dzong_exit.inflate(-6, -6))
    pygame.draw.rect(screen, (215, 175, 70), cpu_dzong_exit, 3)
    pygame.draw.circle(screen, (215, 175, 70), (cpu_dzong_exit.centerx, cpu_dzong_exit.top + 18), 5)
    pygame.draw.circle(screen, (245, 220, 130), (cpu_dzong_exit.centerx, cpu_dzong_exit.top + 18), 2)
    exit_label = small_font.render("EXIT", True, (245, 220, 130))
    screen.blit(exit_label,
                (cpu_dzong_exit.centerx - exit_label.get_width() // 2,
                 cpu_dzong_exit.top + 31))

    if player.bottom < guardian["rect"].bottom:
        draw_player(screen)
        draw_guardian_sprite(screen, "Karma", guardian["rect"], player)
    else:
        draw_guardian_sprite(screen, "Karma", guardian["rect"], player)
        draw_player(screen)