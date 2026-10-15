"""make_cover.py — generates itch.io cover image (630x500)."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import math

pygame.init()
pygame.font.init()
pygame.display.set_mode((1, 1))

W, H = 630, 500

GOLD        = (212, 175, 55)
GOLD_DARK   = (150, 115, 45)
PLATE_RED   = (75, 25, 30)
DRUKORA_RED = (215, 90, 75)

screen = pygame.Surface((W, H))

def cover_fit(surface, target_w, target_h):
    sw, sh = surface.get_size()
    if sw == 0 or sh == 0:
        return pygame.Surface((target_w, target_h), pygame.SRCALPHA)
    scale = max(target_w / sw, target_h / sh)
    nw = int(sw * scale)
    nh = int(sh * scale)
    scaled = pygame.transform.smoothscale(surface, (nw, nh))
    cx = (nw - target_w) // 2
    cy = (nh - target_h) // 2
    out = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
    out.blit(scaled, (0, 0), pygame.Rect(cx, cy, target_w, target_h))
    return out

def strip_white(surface, tolerance=18):
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

def draw_endless_knot(surface, cx, cy, size, color, thickness=2):
    s = size
    for offset in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
        ox = cx + offset[0] * s * 0.35
        oy = cy + offset[1] * s * 0.35
        pygame.draw.circle(surface, color, (int(ox), int(oy)),
                           int(s * 0.4), thickness)
    pygame.draw.circle(surface, color, (cx, cy), int(s * 0.25), thickness)
    for i in range(4):
        a = math.radians(i * 90 + 45)
        x1 = cx + math.cos(a) * s * 0.55
        y1 = cy + math.sin(a) * s * 0.55
        x2 = cx - math.cos(a) * s * 0.55
        y2 = cy - math.sin(a) * s * 0.55
        pygame.draw.line(surface, color, (x1, y1), (x2, y2), thickness)

def draw_lotus(surface, cx, cy, size, color, thickness=2):
    for i in range(8):
        a = math.radians(i * 45)
        px = cx + math.cos(a) * size * 0.5
        py = cy + math.sin(a) * size * 0.5
        pygame.draw.circle(surface, color, (int(px), int(py)),
                           int(size * 0.28), thickness)
    pygame.draw.circle(surface, color, (cx, cy), int(size * 0.18), thickness)

MOUNTAIN_PATH = "assets/environment/mountains/mountain_range.png"
FLAGS_PATH    = "assets/environment/decorations/prayer_flags.png"

mountains = None
flags     = None

if os.path.isfile(MOUNTAIN_PATH):
    mountains = pygame.image.load(MOUNTAIN_PATH)
    print(f"Loaded mountain_range.png  ->  {mountains.get_size()}")
else:
    print(f"WARNING: {MOUNTAIN_PATH} not found")

if os.path.isfile(FLAGS_PATH):
    flags = pygame.image.load(FLAGS_PATH).convert_alpha()
    flags = strip_white(flags, tolerance=15)
    print(f"Loaded prayer_flags.png  ->  {flags.get_size()}")
else:
    print(f"WARNING: {FLAGS_PATH} not found")

if mountains:
    bg = cover_fit(mountains, W, H)
    screen.blit(bg, (0, 0))
else:
    for y in range(H):
        t = y / H
        r = int(24 + 180 * t)
        g = int(20 + 90 * t)
        b = int(48 + 20 * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (W, y))

shade = pygame.Surface((W, H), pygame.SRCALPHA)
for y in range(H):
    t = y / H
    alpha = int((t ** 1.6) * 150)
    pygame.draw.line(shade, (0, 0, 0, alpha), (0, y), (W, y))
screen.blit(shade, (0, 0))

top_shade = pygame.Surface((W, 130), pygame.SRCALPHA)
for y in range(130):
    t = 1.0 - (y / 130)
    alpha = int(t * 110)
    pygame.draw.line(top_shade, (0, 0, 0, alpha), (0, y), (W, y))
screen.blit(top_shade, (0, 0))

if flags:
    fw, fh = flags.get_size()
    target_w = W + 40
    scale = target_w / fw
    new_h = int(fh * scale)
    flags_scaled = pygame.transform.smoothscale(flags, (target_w, new_h))
    screen.blit(flags_scaled, (-20, 18))

plate_w, plate_h = 540, 210
plate_x = (W - plate_w) // 2
plate_y = 250
plate = pygame.Rect(plate_x, plate_y, plate_w, plate_h)

shadow = pygame.Surface((plate_w + 16, plate_h + 16), pygame.SRCALPHA)
pygame.draw.rect(shadow, (0, 0, 0, 160), (8, 8, plate_w, plate_h),
                 border_radius=10)
screen.blit(shadow, (plate.x - 8, plate.y - 8))

plate_surf = pygame.Surface((plate_w, plate_h), pygame.SRCALPHA)
pygame.draw.rect(plate_surf, (*PLATE_RED, 245), (0, 0, plate_w, plate_h),
                 border_radius=10)
screen.blit(plate_surf, plate.topleft)

pygame.draw.rect(screen, GOLD, plate, 3, border_radius=10)
pygame.draw.rect(screen, GOLD_DARK, plate.inflate(-14, -14), 1,
                 border_radius=8)

for cx, cy in [(plate.left + 12, plate.top + 12),
               (plate.right - 12, plate.top + 12),
               (plate.left + 12, plate.bottom - 12),
               (plate.right - 12, plate.bottom - 12)]:
    pygame.draw.rect(screen, GOLD, (cx - 5, cy - 5, 10, 10), 2)
    pygame.draw.circle(screen, GOLD, (cx, cy), 2)
    pygame.draw.circle(screen, PLATE_RED, (cx, cy), 1)

knot = pygame.Surface((plate_w, plate_h), pygame.SRCALPHA)
draw_endless_knot(knot, plate_w // 2, plate_h // 2, 120,
                  (*GOLD, 28), thickness=2)
screen.blit(knot, plate.topleft)

big_font = pygame.font.SysFont("georgia", 62, bold=True)
title_text = "THE CORE"

for off in [(3, 0), (-3, 0), (0, 3), (0, -3), (2, 2), (-2, -2)]:
    glow = big_font.render(title_text, True, (255, 230, 150))
    glow.set_alpha(50)
    screen.blit(glow, (plate.centerx - glow.get_width() // 2 + off[0],
                       plate.y + 22 + off[1]))

sh = big_font.render(title_text, True, (30, 8, 12))
screen.blit(sh, (plate.centerx - sh.get_width() // 2 + 2, plate.y + 24))

title_s = big_font.render(title_text, True, (245, 220, 130))
screen.blit(title_s, (plate.centerx - title_s.get_width() // 2, plate.y + 22))

div_y = plate.y + 108
pygame.draw.line(screen, GOLD,
                 (plate.centerx - 180, div_y),
                 (plate.centerx - 30, div_y), 2)
pygame.draw.line(screen, GOLD,
                 (plate.centerx + 30, div_y),
                 (plate.centerx + 180, div_y), 2)
draw_lotus(screen, plate.centerx, div_y, 18, GOLD, thickness=2)

sub_font = pygame.font.SysFont("georgia", 34, bold=True)
sub_s = sub_font.render("D R U K O R A", True, DRUKORA_RED)
screen.blit(sub_s, (plate.centerx - sub_s.get_width() // 2, plate.y + 124))

tag_font = pygame.font.SysFont("georgia", 14, italic=True)
tag_s = tag_font.render("A kingdom. A system. A mystery.",
                        True, (230, 210, 190))
screen.blit(tag_s, (plate.centerx - tag_s.get_width() // 2, plate.y + 172))

v = pygame.Surface((W, H), pygame.SRCALPHA)
for i in range(0, 70, 2):
    alpha = int((i / 70) ** 2 * 200)
    pygame.draw.rect(v, (0, 0, 0, alpha // 40),
                     (i, i, W - i * 2, H - i * 2), 4)
screen.blit(v, (0, 0))

pygame.image.save(screen, "cover.png")
print("")
print(f"Saved cover.png  ->  {screen.get_size()}")
pygame.quit()
