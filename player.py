import pygame
from setting import WIDTH, HEIGHT

# =========================================================
# LOAD PLAYER SPRITE SHEET
# =========================================================
try:
    player_sheet = pygame.image.load("assets/sprite/player_sprite.png").convert_alpha()
    if player_sheet.get_size() != (1024, 1024):
        player_sheet = pygame.transform.scale(player_sheet, (1024, 1024))
except pygame.error:
    print("WARNING: player_sprite.png not found!")
    player_sheet = pygame.Surface((1024, 1024), pygame.SRCALPHA)
    player_sheet.fill((65, 105, 190))

SPRITE_COLS = 4
SPRITE_ROWS = 4
frame_width = player_sheet.get_width() // SPRITE_COLS
frame_height = player_sheet.get_height() // SPRITE_ROWS

# =========================================================
# PLAYER STATE
# =========================================================
player = pygame.Rect(485, 485, 30, 30)
player_speed = 4

player_frame_index = 0
player_animation_timer = 0
PLAYER_ANIMATION_SPEED = 8

player_direction = "down"
player_moving = False

# =========================================================
# DRAW PLAYER
# =========================================================
def draw_player(screen):
    global player_frame_index, player_animation_timer

    if player_moving:
        player_animation_timer += 1
        if player_animation_timer >= PLAYER_ANIMATION_SPEED:
            player_animation_timer = 0
            player_frame_index += 1
            if player_frame_index >= SPRITE_COLS:
                player_frame_index = 0
    else:
        player_frame_index = 0
        player_animation_timer = 0

    row = {"down": 0, "left": 1, "right": 2, "up": 3}.get(player_direction, 0)

    frame = player_sheet.subsurface(
        pygame.Rect(
            player_frame_index * frame_width,
            row * frame_height,
            frame_width,
            frame_height,
        )
    ).copy()

    DRAW_WIDTH = 64
    DRAW_HEIGHT = 80
    frame = pygame.transform.scale(frame, (DRAW_WIDTH, DRAW_HEIGHT))

    # Shadow
    pygame.draw.ellipse(screen, (0, 0, 0, 80),
                        (player.centerx - 18, player.bottom - 6, 36, 10))

    screen.blit(
        frame,
        (player.centerx - DRAW_WIDTH // 2, player.bottom - DRAW_HEIGHT),
    )

# =========================================================
# MOVEMENT & COLLISION
# =========================================================
def move_player(dx, dy, building_collisions):
    player.x += dx
    for building in building_collisions:
        if player.colliderect(building):
            if dx > 0: player.right = building.left
            elif dx < 0: player.left = building.right

    player.y += dy
    for building in building_collisions:
        if player.colliderect(building):
            if dy > 0: player.bottom = building.top
            elif dy < 0: player.top = building.bottom

    player.left = max(0, player.left)
    player.right = min(WIDTH, player.right)
    player.top = max(0, player.top)
    player.bottom = min(HEIGHT, player.bottom)

def move_player_interior(dx, dy, interior_walls):
    player.x += dx
    for wall in interior_walls:
        if player.colliderect(wall):
            if dx > 0: player.right = wall.left
            elif dx < 0: player.left = wall.right

    player.y += dy
    for wall in interior_walls:
        if player.colliderect(wall):
            if dy > 0: player.bottom = wall.top
            elif dy < 0: player.top = wall.bottom

    player.left = max(25, player.left)
    player.right = min(WIDTH - 25, player.right)
    player.top = max(115, player.top)
    player.bottom = min(HEIGHT - 25, player.bottom)