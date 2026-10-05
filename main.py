import pygame
import sys
import math
import random

pygame.init()

# =========================================================
# BACKGROUND MUSIC
# =========================================================

pygame.mixer.init()

try:
    pygame.mixer.music.load("assets/music/village_theme.mp3")
    pygame.mixer.music.play(-1)
except pygame.error:
    pass


# =========================================================
# WINDOW
# =========================================================

WIDTH = 1000
HEIGHT = 650

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("THE CORE - Computer System")
clock = pygame.time.Clock()


# =========================================================
# PLAYER SPRITE SHEET
# =========================================================

player_sheet = pygame.image.load("assets/sprite/player_sprite.png").convert_alpha()

SPRITE_COLS = 4
SPRITE_ROWS = 4
SPRITE_SHEET_SIZE = 1024

if player_sheet.get_size() != (SPRITE_SHEET_SIZE, SPRITE_SHEET_SIZE):
    player_sheet = pygame.transform.scale(
        player_sheet, (SPRITE_SHEET_SIZE, SPRITE_SHEET_SIZE)
    )

frame_width = player_sheet.get_width() // SPRITE_COLS
frame_height = player_sheet.get_height() // SPRITE_ROWS


# =========================================================
# PLAYER ANIMATION
# =========================================================

player_frame_index = 0
player_animation_timer = 0
PLAYER_ANIMATION_SPEED = 8

player_direction = "down"
player_moving = False


# =========================================================
# KARMA SPRITE SHEET
# =========================================================

karma_sheet = pygame.image.load("assets/sprite/karma_sprite.png").convert_alpha()

KARMA_SPRITE_COLS = 4
KARMA_SPRITE_ROWS = 4
karma_frame_width = karma_sheet.get_width() // KARMA_SPRITE_COLS
karma_frame_height = karma_sheet.get_height() // KARMA_SPRITE_ROWS

KARMA_DRAW_WIDTH = 82
KARMA_DRAW_HEIGHT = 104
karma_direction = "down"


# =========================================================
# DAWA SPRITE SHEET
# =========================================================

dawa_sheet = pygame.image.load("assets/sprite/dawa_sprite.png").convert_alpha()

DAWA_SPRITE_COLS = 4
DAWA_SPRITE_ROWS = 4
dawa_frame_width = dawa_sheet.get_width() // DAWA_SPRITE_COLS
dawa_frame_height = dawa_sheet.get_height() // DAWA_SPRITE_ROWS

DAWA_DRAW_WIDTH = 82
DAWA_DRAW_HEIGHT = 104
dawa_direction = "down"

dawa_frame_index = 0
dawa_animation_timer = 0
DAWA_ANIMATION_SPEED = 12


# =========================================================
# CHODEN - OUTPUT GUARDIAN SPRITE
# =========================================================

choden_sheet = pygame.image.load("assets/sprite/choden_sprite.png").convert_alpha()

CHODEN_SPRITE_COLS = 4
CHODEN_SPRITE_ROWS = 4
choden_frame_width = choden_sheet.get_width() // CHODEN_SPRITE_COLS
choden_frame_height = choden_sheet.get_height() // CHODEN_SPRITE_ROWS

CHODEN_DRAW_WIDTH = 82
CHODEN_DRAW_HEIGHT = 104
choden_direction = "down"


# =========================================================
# SONAM - MEMORY GUARDIAN SPRITE
# =========================================================

sonam_sheet = pygame.image.load("assets/sprite/sonam_sprite.png").convert_alpha()

SONAM_SPRITE_COLS = 4
SONAM_SPRITE_ROWS = 4
sonam_frame_width = sonam_sheet.get_width() // SONAM_SPRITE_COLS
sonam_frame_height = sonam_sheet.get_height() // SONAM_SPRITE_ROWS

SONAM_DRAW_WIDTH = 82
SONAM_DRAW_HEIGHT = 104
sonam_direction = "down"


# =========================================================
# DORJI - CPU / PROCESSING GUARDIAN SPRITE
# =========================================================

dorji_sheet = pygame.image.load("assets/sprite/dorji_sprite.png").convert_alpha()

DORJI_SPRITE_COLS = 4
DORJI_SPRITE_ROWS = 4
dorji_frame_width = dorji_sheet.get_width() // DORJI_SPRITE_COLS
dorji_frame_height = dorji_sheet.get_height() // DORJI_SPRITE_ROWS

DORJI_DRAW_WIDTH = 82
DORJI_DRAW_HEIGHT = 104
dorji_direction = "down"


# =========================================================
# ENVIRONMENT - VEGETATION
# =========================================================

vegetation_sheet = pygame.image.load(
    "assets/environment/trees/vegetation_pack.png"
).convert_alpha()


# =========================================================
# COLORS
# =========================================================

SKY = (185, 220, 235)
GRASS = (105, 155, 90)

MOUNTAIN = (105, 140, 150)
SNOW = (245, 245, 235)

ROAD = (194, 158, 108)
ROAD_EDGE = (150, 112, 72)

WOOD = (145, 88, 48)
DARK_WOOD = (105, 65, 40)

WHITE = (245, 245, 235)
BLACK = (30, 30, 30)
GOLD = (212, 175, 55)

LEAF = (45, 105, 65)
LEAF_LIGHT = (60, 125, 70)

STONE = (145, 145, 135)

PLAYER_BLUE = (65, 105, 190)
SKIN = (235, 195, 155)

INTERIOR_WALL = (65, 43, 35)
INTERIOR_WOOD = (105, 62, 38)
INTERIOR_DARK = (45, 30, 25)
INTERIOR_FLOOR = (115, 75, 48)

CORE_BLUE = (70, 150, 220)
CORE_LIGHT = (170, 225, 255)


# =========================================================
# FONTS
# =========================================================

title_font = pygame.font.SysFont("arial", 28, bold=True)
location_font = pygame.font.SysFont("arial", 18, bold=True)
font = pygame.font.SysFont("arial", 17)
small_font = pygame.font.SysFont("arial", 14)
quest_title_font = pygame.font.Font(None, 25)
quest_text_font = pygame.font.Font(None, 21)
message_font = pygame.font.Font(None, 30)


# =========================================================
# PLAYER
# =========================================================

player = pygame.Rect(485, 485, 26, 32)
player_speed = 4


# =========================================================
# SCENE
# =========================================================

current_scene = "village"


# =========================================================
# LOCATIONS
# =========================================================

locations = {
    "Memory Monastery": pygame.Rect(395, 75, 210, 95),
    "CPU Dzong": pygame.Rect(405, 270, 190, 110),
    "Input Village": pygame.Rect(80, 315, 170, 90),
    "Output Tower": pygame.Rect(750, 315, 170, 90),
    "Storage Vault": pygame.Rect(405, 520, 190, 85),
}

location_info = {
    "Memory Monastery": "Memory Monastery: RAM temporarily holds data "
    "that the computer is currently using.",
    "Input Village": "Input Village: keyboards, mice and microphones "
    "send information into the computer.",
    "Output Tower": "Output Tower: monitors, speakers and printers "
    "show the results produced by the computer.",
    "Storage Vault": "Storage Vault: hard drives, SSDs and USB drives "
    "keep data even when the power is off.",
}


# =========================================================
# DOORS
# =========================================================

cpu_dzong_entrance = pygame.Rect(470, 375, 60, 35)
cpu_dzong_exit = pygame.Rect(450, 575, 100, 50)


# =========================================================
# NORMAL NPC DATA
# =========================================================

npcs = [
    {"rect": pygame.Rect(325, 335, 24, 32), "name": "Tashi", "color": (120, 80, 150)},
    {"rect": pygame.Rect(650, 340, 24, 32), "name": "Pema", "color": (175, 90, 80)},
]


# =========================================================
# GUARDIANS
# =========================================================

input_guardian = {
    "rect": pygame.Rect(145, 350, 24, 32),
    "name": "Karma",
    "color": (70, 120, 170),
}

guardian = {
    "rect": pygame.Rect(488, 225, 24, 32),
    "name": "Dorji",
    "color": (185, 145, 55),
}

storage_guardian = {
    "rect": pygame.Rect(488, 475, 24, 32),
    "name": "Dawa",
    "color": (125, 95, 155),
}

output_guardian = {
    "rect": pygame.Rect(835, 420, 24, 32),
    "name": "Choden",
    "color": (60, 140, 120),
}

memory_guardian = {
    "rect": pygame.Rect(500, 205, 24, 32),
    "name": "Sonam",
    "color": (170, 110, 55),
}


# =========================================================
# DIALOGUE
# =========================================================

dialogue_open = False
dialogue_text = ""
dialogue_name = ""


# =========================================================
# GUARDIAN CHALLENGE
# =========================================================

challenge_open = False
challenge_question = ""
challenge_options = []
challenge_answer = 0
challenge_result = ""

guardian_challenges = {
    "Karma": {
        "question": "Which device is used to enter text into a computer?",
        "options": ["Monitor", "Keyboard", "Speaker", "Printer"],
        "answer": "Keyboard",
    },
    "Dorji": {
        "question": "Which part of the computer processes instructions and controls the system?",
        "options": ["Monitor", "CPU", "Keyboard", "Printer"],
        "answer": "CPU",
    },
    "Dawa": {
        "question": "Which device is mainly used to store data for long-term use?",
        "options": ["Monitor", "Hard Drive", "Keyboard", "Speaker"],
        "answer": "Hard Drive",
    },
    "Choden": {
        "question": "Which device displays the visual results produced by a computer?",
        "options": ["Monitor", "Keyboard", "Microphone", "Hard Drive"],
        "answer": "Monitor",
    },
    "Sonam": {
        "question": "Which type of memory temporarily stores data and instructions while programs are running?",
        "options": ["ROM", "RAM", "Hard Drive", "USB Drive"],
        "answer": "RAM",
    },
}


def prepare_challenge(guardian_name):
    global challenge_question
    global challenge_options
    global challenge_answer
    global challenge_result

    challenge = guardian_challenges[guardian_name]
    challenge_question = challenge["question"]
    choices = challenge["options"][:]
    random.shuffle(choices)
    challenge_options = choices
    challenge_answer = choices.index(challenge["answer"]) + 1
    challenge_result = ""


# =========================================================
# QUEST SYSTEM
# =========================================================

quest_active = False
quest_completed = False

quest_title = "THE AWAKENING"
quest_objective = "Talk to Tashi"

quest_message = ""
quest_message_timer = 0


# =========================================================
# RPG PROGRESSION
# =========================================================

player_xp = 0
guardian_fragments = 0
mission_bonus_awarded = False


# =========================================================
# GUARDIAN EFFECT
# =========================================================

guardian_effect_timer = 0
guardian_effect_name = ""
guardian_particles = []


# =========================================================
# TASHI HINTS
# =========================================================

tashi_hints = {
    "Reach CPU Dzong": "The CPU Dzong lies ahead. Walk up the road and press E at its door.",
    "Talk to Dorji": "Dorji waits for you inside the CPU Dzong.",
    "Visit Input Village": "Karma guards Input Village, to the west. Go and listen to her.",
    "Return to Dorji": "Dorji is waiting for your report in the CPU Dzong.",
    "Visit Storage Vault": "Dawa is at the Storage Vault, south of the Dzong.",
    "Visit Output Tower": "Choden is near the Output Tower, to the east.",
    "Visit Memory Monastery": "The Memory Guardian waits near the Memory Monastery.",
    "Report to Dorji": "You have met every guardian. Return to Dorji in the CPU Dzong.",
}


# =========================================================
# UI HELPERS
# =========================================================


def draw_prompt(text, y, width=380):
    message = font.render(text, True, WHITE)
    box = pygame.Rect(WIDTH // 2 - width // 2, y, width, 35)
    pygame.draw.rect(screen, BLACK, box)
    screen.blit(message, (box.centerx - message.get_width() // 2, box.y + 8))


def draw_ground_shadow(rect, color, pad_x, pad_y_height):
    pygame.draw.ellipse(
        screen,
        color,
        (
            rect.x - pad_x,
            rect.bottom - 5,
            rect.width + pad_x * 2,
            pad_y_height,
        ),
    )


def draw_label(text, rect, offset):
    label = location_font.render(text, True, BLACK)
    screen.blit(label, (rect.centerx - label.get_width() // 2, rect.bottom + offset))


def draw_roof_outline(points):
    pygame.draw.line(screen, GOLD, points[0], points[1], 5)
    pygame.draw.line(screen, GOLD, points[1], points[2], 5)


# =========================================================
# MOUNTAINS
# =========================================================


def draw_mountains():
    pygame.draw.polygon(
        screen,
        MOUNTAIN,
        [
            (0, 240),
            (145, 80),
            (280, 240),
            (430, 55),
            (570, 240),
            (730, 90),
            (870, 240),
            (1000, 70),
            (1000, 270),
            (0, 270),
        ],
    )
    pygame.draw.polygon(screen, SNOW, [(430, 55), (395, 105), (430, 85), (460, 110)])
    pygame.draw.polygon(screen, SNOW, [(730, 90), (700, 130), (730, 115), (760, 135)])


# =========================================================
# TREE
# =========================================================


def draw_tree(x, y):
    pygame.draw.ellipse(screen, (65, 95, 60), (x - 32, y + 35, 64, 18))
    pygame.draw.rect(screen, DARK_WOOD, (x - 7, y + 8, 14, 45))
    pygame.draw.line(screen, DARK_WOOD, (x, y + 25), (x - 18, y + 8), 6)
    pygame.draw.line(screen, DARK_WOOD, (x, y + 25), (x + 18, y + 8), 6)
    pygame.draw.circle(screen, LEAF, (x, y - 5), 30)
    pygame.draw.circle(screen, LEAF, (x - 22, y + 8), 22)
    pygame.draw.circle(screen, LEAF, (x + 22, y + 8), 22)
    pygame.draw.circle(screen, LEAF_LIGHT, (x - 8, y - 22), 16)
    pygame.draw.circle(screen, LEAF_LIGHT, (x + 12, y - 15), 15)
    pygame.draw.circle(screen, LEAF_LIGHT, (x - 18, y - 3), 8)


# =========================================================
# SMALL HOUSE
# =========================================================


class SmallHouse:

    def __init__(self, rect, color, name):
        self.rect = rect
        self.color = color
        self.name = name

    def draw(self):
        rect = self.rect
        pygame.draw.ellipse(
            screen, (80, 120, 70), (rect.x - 10, rect.bottom - 6, rect.width + 20, 18)
        )
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, DARK_WOOD, rect, 4)

        pygame.draw.line(
            screen,
            DARK_WOOD,
            (rect.left + 20, rect.top),
            (rect.left + 20, rect.bottom),
            4,
        )
        pygame.draw.line(
            screen,
            DARK_WOOD,
            (rect.right - 20, rect.top),
            (rect.right - 20, rect.bottom),
            4,
        )

        roof = [
            (rect.left - 18, rect.top),
            (rect.centerx, rect.top - 38),
            (rect.right + 18, rect.top),
        ]
        pygame.draw.polygon(screen, DARK_WOOD, roof)

        inner_roof = [
            (rect.left - 10, rect.top - 2),
            (rect.centerx, rect.top - 30),
            (rect.right + 10, rect.top - 2),
        ]
        pygame.draw.polygon(screen, WOOD, inner_roof)

        for wx in [rect.left + 28, rect.right - 50]:
            window = pygame.Rect(wx, rect.top + 25, 22, 20)
            pygame.draw.rect(screen, GOLD, window)
            pygame.draw.line(
                screen,
                DARK_WOOD,
                window.center,
                (window.centerx, window.top),
                2,
            )
            pygame.draw.line(
                screen,
                DARK_WOOD,
                window.center,
                (window.centerx, window.bottom),
                2,
            )

        door = pygame.Rect(rect.centerx - 15, rect.bottom - 42, 30, 42)
        pygame.draw.rect(screen, WOOD, door)
        pygame.draw.rect(screen, DARK_WOOD, door, 3)
        pygame.draw.circle(screen, GOLD, (door.right - 7, door.centery), 3)

        draw_label(self.name, rect, 8)


houses = [
    SmallHouse(pygame.Rect(35, 310, 130, 75), WOOD, "HOUSE"),
    SmallHouse(pygame.Rect(280, 255, 130, 75), WOOD, "HOUSE"),
    SmallHouse(pygame.Rect(650, 245, 130, 75), WOOD, "HOUSE"),
    SmallHouse(pygame.Rect(825, 305, 130, 75), WOOD, "HOUSE"),
    SmallHouse(pygame.Rect(60, 500, 130, 75), WOOD, "HOUSE"),
    SmallHouse(pygame.Rect(690, 500, 130, 75), WOOD, "HOUSE"),
]


# =========================================================
# CPU DZONG
# =========================================================


def draw_cpu_dzong(rect):
    draw_ground_shadow(rect, (70, 95, 65), 25, 28)
    pygame.draw.rect(screen, (226, 205, 165), rect)

    beam_color = (92, 55, 35)
    pygame.draw.rect(screen, beam_color, (rect.left + 12, rect.top, 12, rect.height))
    pygame.draw.rect(screen, beam_color, (rect.right - 24, rect.top, 12, rect.height))

    upper = pygame.Rect(rect.left + 8, rect.top - 35, rect.width - 16, 35)
    pygame.draw.rect(screen, (188, 140, 82), upper)
    pygame.draw.rect(screen, beam_color, (upper.left, upper.top, upper.width, 7))
    pygame.draw.rect(
        screen, beam_color, (upper.left, upper.bottom - 7, upper.width, 7)
    )

    roof = [
        (rect.left - 25, rect.top - 5),
        (rect.centerx, rect.top - 65),
        (rect.right + 25, rect.top - 5),
    ]

    pygame.draw.polygon(screen, beam_color, roof)
    draw_roof_outline(roof)

    for x in (rect.left + 28, rect.right - 58):
        window = pygame.Rect(x, rect.top + 25, 30, 25)
        pygame.draw.rect(screen, (55, 90, 105), window)
        pygame.draw.rect(screen, GOLD, window, 3)
        pygame.draw.line(
            screen, GOLD, (window.centerx, window.top), (window.centerx, window.bottom), 2
        )

    door = pygame.Rect(rect.centerx - 22, rect.bottom - 60, 44, 60)
    pygame.draw.rect(screen, (75, 45, 30), door)
    pygame.draw.rect(screen, GOLD, door, 3)
    pygame.draw.circle(screen, GOLD, (door.centerx, door.top + 18), 5)

    draw_label("CPU DZONG", rect, 12)


# =========================================================
# MEMORY MONASTERY
# =========================================================


def draw_memory_monastery(rect):
    draw_ground_shadow(rect, (70, 95, 65), 25, 28)
    pygame.draw.rect(screen, (220, 205, 175), rect)
    pygame.draw.rect(screen, DARK_WOOD, rect, 5)

    upper = pygame.Rect(rect.x + 15, rect.y - 30, rect.width - 30, 30)
    pygame.draw.rect(screen, (170, 115, 65), upper)
    pygame.draw.rect(screen, DARK_WOOD, upper, 4)
    pygame.draw.line(
        screen, DARK_WOOD, (upper.left, upper.centery), (upper.right, upper.centery), 5
    )

    roof = [
        (rect.left - 30, rect.top),
        (rect.centerx, rect.top - 55),
        (rect.right + 30, rect.top),
    ]

    pygame.draw.polygon(screen, DARK_WOOD, roof)
    pygame.draw.line(screen, GOLD, roof[0], roof[1], 4)
    pygame.draw.line(screen, GOLD, roof[1], roof[2], 4)

    for x in [rect.left + 28, rect.centerx - 15, rect.right - 58]:
        window = pygame.Rect(x, rect.top + 25, 30, 25)
        pygame.draw.rect(screen, (55, 85, 100), window)
        pygame.draw.rect(screen, GOLD, window, 3)
        pygame.draw.line(
            screen, GOLD, window.center, (window.centerx, window.top), 2
        )
        pygame.draw.line(
            screen, GOLD, window.center, (window.centerx, window.bottom), 2
        )

    door = pygame.Rect(rect.centerx - 20, rect.bottom - 55, 40, 55)
    pygame.draw.rect(screen, (75, 45, 30), door)
    pygame.draw.rect(screen, GOLD, door, 3)
    pygame.draw.circle(screen, GOLD, (rect.centerx, door.top + 17), 6)

    draw_label("MEMORY MONASTERY", rect, 12)


# =========================================================
# INPUT VILLAGE
# =========================================================


def draw_input_village(rect):
    draw_ground_shadow(rect, (70, 95, 65), 20, 25)
    pygame.draw.rect(screen, (155, 120, 175), rect)
    pygame.draw.rect(screen, DARK_WOOD, rect, 5)

    roof = [
        (rect.left - 22, rect.top),
        (rect.centerx, rect.top - 48),
        (rect.right + 22, rect.top),
    ]

    pygame.draw.polygon(screen, DARK_WOOD, roof)

    inner_roof = [
        (rect.left - 12, rect.top - 2),
        (rect.centerx, rect.top - 38),
        (rect.right + 12, rect.top - 2),
    ]

    pygame.draw.polygon(screen, (110, 75, 130), inner_roof)

    box = pygame.Rect(rect.centerx - 22, rect.top + 25, 44, 32)
    pygame.draw.rect(screen, (50, 70, 75), box)
    pygame.draw.rect(screen, GOLD, box, 3)
    pygame.draw.line(
        screen, GOLD, (box.centerx - 18, box.centery), (box.centerx + 8, box.centery), 4
    )

    pygame.draw.polygon(
        screen,
        GOLD,
        [
            (box.centerx + 10, box.centery),
            (box.centerx, box.centery - 7),
            (box.centerx, box.centery + 7),
        ],
    )

    door = pygame.Rect(rect.centerx - 16, rect.bottom - 42, 32, 42)
    pygame.draw.rect(screen, WOOD, door)
    pygame.draw.rect(screen, DARK_WOOD, door, 3)

    draw_label("INPUT VILLAGE", rect, 10)


# =========================================================
# OUTPUT TOWER
# =========================================================


def draw_output_tower(rect):
    draw_ground_shadow(rect, (70, 95, 65), 20, 25)
    pygame.draw.rect(screen, (165, 125, 175), rect)
    pygame.draw.rect(screen, DARK_WOOD, rect, 5)

    for x in [rect.left + 20, rect.centerx, rect.right - 20]:
        pygame.draw.line(screen, DARK_WOOD, (x, rect.top), (x, rect.bottom), 4)

    roof = [
        (rect.left - 22, rect.top),
        (rect.centerx, rect.top - 55),
        (rect.right + 22, rect.top),
    ]

    pygame.draw.polygon(screen, DARK_WOOD, roof)
    pygame.draw.line(screen, GOLD, roof[0], roof[1], 4)
    pygame.draw.line(screen, GOLD, roof[1], roof[2], 4)

    monitor = pygame.Rect(rect.centerx - 28, rect.top + 20, 56, 38)
    pygame.draw.rect(screen, (45, 65, 70), monitor)
    pygame.draw.rect(screen, GOLD, monitor, 3)
    pygame.draw.line(
        screen,
        GOLD,
        (monitor.centerx, monitor.bottom + 3),
        (monitor.centerx, monitor.bottom + 17),
        4,
    )

    pygame.draw.polygon(
        screen,
        GOLD,
        [
            (monitor.centerx, monitor.bottom + 19),
            (monitor.centerx - 7, monitor.bottom + 10),
            (monitor.centerx + 7, monitor.bottom + 10),
        ],
    )

    door = pygame.Rect(rect.centerx - 16, rect.bottom - 42, 32, 42)
    pygame.draw.rect(screen, WOOD, door)
    pygame.draw.rect(screen, DARK_WOOD, door, 3)

    draw_label("OUTPUT TOWER", rect, 10)


# =========================================================
# STORAGE VAULT
# =========================================================


def draw_storage_vault(rect):
    draw_ground_shadow(rect, (60, 80, 60), 25, 28)
    pygame.draw.rect(screen, (105, 120, 115), rect)
    pygame.draw.rect(screen, DARK_WOOD, rect, 5)

    for y in range(rect.top + 15, rect.bottom, 22):
        pygame.draw.line(screen, (75, 90, 85), (rect.left + 5, y), (rect.right - 5, y), 2)

    roof = [
        (rect.left - 25, rect.top),
        (rect.centerx, rect.top - 45),
        (rect.right + 25, rect.top),
    ]

    pygame.draw.polygon(screen, (65, 70, 70), roof)
    pygame.draw.line(screen, GOLD, roof[0], roof[1], 4)
    pygame.draw.line(screen, GOLD, roof[1], roof[2], 4)

    door = pygame.Rect(rect.centerx - 30, rect.bottom - 62, 60, 62)
    pygame.draw.rect(screen, (45, 50, 50), door)
    pygame.draw.rect(screen, GOLD, door, 4)
    pygame.draw.circle(screen, GOLD, door.center, 19, 3)
    pygame.draw.rect(screen, GOLD, (door.centerx - 7, door.centery - 2, 14, 12), 3)

    pygame.draw.arc(
        screen,
        GOLD,
        (door.centerx - 7, door.centery - 12, 14, 15),
        math.pi,
        2 * math.pi,
        3,
    )

    for x in [rect.left + 25, rect.right - 45]:
        pygame.draw.rect(screen, (40, 55, 60), (x, rect.top + 25, 20, 20))
        pygame.draw.rect(screen, GOLD, (x, rect.top + 25, 20, 20), 2)

    draw_label("STORAGE VAULT", rect, 12)


# =========================================================
# ROADS
# =========================================================


def draw_roads():
    pygame.draw.rect(screen, ROAD_EDGE, (0, 380, WIDTH, 70))
    pygame.draw.rect(screen, ROAD, (0, 388, WIDTH, 54))

    pygame.draw.rect(screen, ROAD_EDGE, (450, 145, 100, 405))
    pygame.draw.rect(screen, ROAD, (460, 145, 80, 405))

    pygame.draw.rect(screen, ROAD, (190, 380, 270, 50))
    pygame.draw.rect(screen, ROAD, (540, 380, 270, 50))
    pygame.draw.rect(screen, ROAD, (460, 450, 80, 120))


# =========================================================
# BRIDGE
# =========================================================


def draw_bridge(x, y):
    pygame.draw.rect(screen, DARK_WOOD, (x, y, 80, 35))

    for i in range(5):
        pygame.draw.line(
            screen, WOOD, (x + i * 20, y), (x + i * 20, y + 35), 3
        )


# =========================================================
# FLAGS
# =========================================================


def draw_flag(x, y):
    pygame.draw.line(screen, DARK_WOOD, (x, y), (x, y + 55), 4)
    flag = [(x, y + 3), (x + 35, y + 12), (x, y + 25)]
    pygame.draw.polygon(screen, GOLD, flag)
    pygame.draw.line(screen, (180, 60, 45), (x + 3, y + 7), (x + 27, y + 13), 3)


# =========================================================
# GROUND DETAILS
# =========================================================


def draw_ground_details():
    grass_positions = [
        (80, 180),
        (160, 520),
        (280, 260),
        (700, 180),
        (760, 520),
        (650, 300),
        (350, 520),
    ]

    for x, y in grass_positions:
        pygame.draw.line(screen, LEAF, (x, y), (x - 4, y - 9), 2)
        pygame.draw.line(screen, LEAF, (x, y), (x + 4, y - 9), 2)

    rock_positions = [(230, 330), (610, 300), (330, 470), (720, 470)]

    for x, y in rock_positions:
        pygame.draw.ellipse(screen, STONE, (x - 7, y - 4, 14, 8))


# =========================================================
# SIGN
# =========================================================


def draw_sign(x, y, text):
    width = 130

    pygame.draw.rect(screen, DARK_WOOD, (x, y, width, 34))
    pygame.draw.rect(screen, WOOD, (x + 3, y + 3, width - 6, 28))
    pygame.draw.rect(screen, DARK_WOOD, (x + width // 2 - 4, y + 34, 8, 30))

    label = small_font.render(text, True, WHITE)
    screen.blit(label, (x + width // 2 - label.get_width() // 2, y + 9))


# =========================================================
# FENCE
# =========================================================


def draw_fence(x, y, length):
    pygame.draw.line(screen, DARK_WOOD, (x, y), (x + length, y), 5)

    for i in range(0, length + 1, 25):
        pygame.draw.line(screen, DARK_WOOD, (x + i, y - 10), (x + i, y + 10), 4)


# =========================================================
# NORMAL NPC
# =========================================================


def draw_npc(npc):
    rect = npc["rect"]

    pygame.draw.ellipse(
        screen, (65, 95, 60), (rect.x - 4, rect.bottom - 2, rect.width + 8, 9)
    )
    pygame.draw.rect(screen, npc["color"], rect)

    pygame.draw.circle(screen, SKIN, (rect.centerx, rect.top - 8), 12)
    pygame.draw.circle(screen, BLACK, (rect.centerx, rect.top - 16), 9)
    pygame.draw.circle(screen, BLACK, (rect.centerx - 4, rect.top - 8), 2)
    pygame.draw.circle(screen, BLACK, (rect.centerx + 4, rect.top - 8), 2)

    name = small_font.render(npc["name"], True, BLACK)
    screen.blit(name, (rect.centerx - name.get_width() // 2, rect.bottom + 5))


# =========================================================
# KARMA SPRITE
# =========================================================


def draw_input_guardian():
    global karma_direction

    r = input_guardian["rect"]
    dx = player.centerx - r.centerx
    dy = player.centery - r.centery

    if abs(dx) > abs(dy):
        karma_direction = "right" if dx > 0 else "left"
    else:
        karma_direction = "down" if dy > 0 else "up"

    direction_rows = {"down": 0, "left": 1, "right": 2, "up": 3}
    row = direction_rows.get(karma_direction, 0)
    frame_index = 0

    frame = karma_sheet.subsurface(
        pygame.Rect(
            frame_index * karma_frame_width,
            row * karma_frame_height,
            karma_frame_width,
            karma_frame_height,
        )
    ).copy()

    frame = pygame.transform.scale(frame, (KARMA_DRAW_WIDTH, KARMA_DRAW_HEIGHT))

    pygame.draw.ellipse(
        screen, (35, 30, 25), (r.x - 10, r.bottom - 2, r.width + 20, 9)
    )
    screen.blit(
        frame, (r.centerx - KARMA_DRAW_WIDTH // 2, r.bottom - KARMA_DRAW_HEIGHT)
    )

    name = small_font.render("Karma", True, GOLD)
    screen.blit(name, (r.centerx - name.get_width() // 2, r.bottom + 6))


# =========================================================
# DAWA SPRITE
# =========================================================


def draw_storage_guardian():
    global dawa_direction
    global dawa_frame_index
    global dawa_animation_timer

    r = storage_guardian["rect"]

    dx = player.centerx - r.centerx
    dy = player.centery - r.centery

    if abs(dx) > abs(dy):
        dawa_direction = "right" if dx > 0 else "left"
    else:
        dawa_direction = "down" if dy > 0 else "up"

    direction_rows = {"down": 0, "left": 1, "right": 2, "up": 3}
    row = direction_rows.get(dawa_direction, 0)

    dawa_animation_timer += 1
    if dawa_animation_timer >= DAWA_ANIMATION_SPEED:
        dawa_animation_timer = 0
        dawa_frame_index += 1
        if dawa_frame_index >= DAWA_SPRITE_COLS:
            dawa_frame_index = 0

    frame = dawa_sheet.subsurface(
        pygame.Rect(
            dawa_frame_index * dawa_frame_width,
            row * dawa_frame_height,
            dawa_frame_width,
            dawa_frame_height,
        )
    ).copy()

    frame = pygame.transform.scale(frame, (DAWA_DRAW_WIDTH, DAWA_DRAW_HEIGHT))

    pygame.draw.ellipse(
        screen, (35, 30, 25), (r.x - 10, r.bottom - 2, r.width + 20, 9)
    )
    screen.blit(
        frame, (r.centerx - DAWA_DRAW_WIDTH // 2, r.bottom - DAWA_DRAW_HEIGHT)
    )

    name = small_font.render("Dawa", True, GOLD)
    screen.blit(name, (r.centerx - name.get_width() // 2, r.bottom + 6))


# =========================================================
# OTHER GUARDIANS
# =========================================================


def draw_guardian():
    """Draw Dorji using the dedicated 4 x 4 RPG sprite sheet."""
    global dorji_direction

    r = guardian["rect"]

    dx = player.centerx - r.centerx
    dy = player.centery - r.centery

    if abs(dx) > abs(dy):
        dorji_direction = "right" if dx > 0 else "left"
    else:
        dorji_direction = "down" if dy > 0 else "up"

    direction_rows = {"down": 0, "left": 1, "right": 2, "up": 3}
    row = direction_rows.get(dorji_direction, 0)
    frame_index = 0

    frame = dorji_sheet.subsurface(
        pygame.Rect(
            frame_index * dorji_frame_width,
            row * dorji_frame_height,
            dorji_frame_width,
            dorji_frame_height,
        )
    ).copy()

    frame = pygame.transform.scale(frame, (DORJI_DRAW_WIDTH, DORJI_DRAW_HEIGHT))

    pygame.draw.ellipse(
        screen, (35, 30, 25), (r.x - 10, r.bottom - 2, r.width + 20, 9)
    )
    screen.blit(
        frame, (r.centerx - DORJI_DRAW_WIDTH // 2, r.bottom - DORJI_DRAW_HEIGHT)
    )

    name = small_font.render("Dorji", True, GOLD)
    screen.blit(name, (r.centerx - name.get_width() // 2, r.bottom + 6))


def draw_output_guardian():
    """Draw Choden using the dedicated 4 x 4 RPG sprite sheet."""
    global choden_direction

    r = output_guardian["rect"]

    dx = player.centerx - r.centerx
    dy = player.centery - r.centery

    if abs(dx) > abs(dy):
        choden_direction = "right" if dx > 0 else "left"
    else:
        choden_direction = "down" if dy > 0 else "up"

    direction_rows = {"down": 0, "left": 1, "right": 2, "up": 3}
    row = direction_rows.get(choden_direction, 0)
    frame_index = 0

    frame = choden_sheet.subsurface(
        pygame.Rect(
            frame_index * choden_frame_width,
            row * choden_frame_height,
            choden_frame_width,
            choden_frame_height,
        )
    ).copy()

    frame = pygame.transform.scale(frame, (CHODEN_DRAW_WIDTH, CHODEN_DRAW_HEIGHT))

    pygame.draw.ellipse(
        screen, (35, 30, 25), (r.x - 10, r.bottom - 2, r.width + 20, 9)
    )
    screen.blit(
        frame, (r.centerx - CHODEN_DRAW_WIDTH // 2, r.bottom - CHODEN_DRAW_HEIGHT)
    )

    name = small_font.render("Choden", True, GOLD)
    screen.blit(name, (r.centerx - name.get_width() // 2, r.bottom + 6))


def draw_memory_guardian():
    """Draw Sonam using the dedicated 4 x 4 RPG sprite sheet."""
    global sonam_direction

    r = memory_guardian["rect"]

    dx = player.centerx - r.centerx
    dy = player.centery - r.centery

    if abs(dx) > abs(dy):
        sonam_direction = "right" if dx > 0 else "left"
    else:
        sonam_direction = "down" if dy > 0 else "up"

    direction_rows = {"down": 0, "left": 1, "right": 2, "up": 3}
    row = direction_rows.get(sonam_direction, 0)
    frame_index = 0

    frame = sonam_sheet.subsurface(
        pygame.Rect(
            frame_index * sonam_frame_width,
            row * sonam_frame_height,
            sonam_frame_width,
            sonam_frame_height,
        )
    ).copy()

    frame = pygame.transform.scale(frame, (SONAM_DRAW_WIDTH, SONAM_DRAW_HEIGHT))

    pygame.draw.ellipse(
        screen, (35, 30, 25), (r.x - 10, r.bottom - 2, r.width + 20, 9)
    )
    screen.blit(
        frame, (r.centerx - SONAM_DRAW_WIDTH // 2, r.bottom - SONAM_DRAW_HEIGHT)
    )

    name = small_font.render("Sonam", True, GOLD)
    screen.blit(name, (r.centerx - name.get_width() // 2, r.bottom + 6))


# =========================================================
# PLAYER SPRITE
# =========================================================


def draw_player():
    global player_frame_index
    global player_animation_timer

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

    if player_direction == "down":
        row = 0
    elif player_direction == "left":
        row = 1
    elif player_direction == "right":
        row = 2
    elif player_direction == "up":
        row = 3
    else:
        row = 0

    frame = player_sheet.subsurface(
        pygame.Rect(
            player_frame_index * frame_width,
            row * frame_height,
            frame_width,
            frame_height,
        )
    ).copy()

    PLAYER_DRAW_WIDTH = 82
    PLAYER_DRAW_HEIGHT = 100

    frame = pygame.transform.scale(frame, (PLAYER_DRAW_WIDTH, PLAYER_DRAW_HEIGHT))

    screen.blit(
        frame, (player.centerx - PLAYER_DRAW_WIDTH // 2, player.bottom - PLAYER_DRAW_HEIGHT)
    )


# =========================================================
# COLLISION
# =========================================================

building_collisions = list(locations.values())


def move_player(dx, dy):
    player.x += dx
    for building in building_collisions:
        if player.colliderect(building):
            if dx > 0:
                player.right = building.left
            elif dx < 0:
                player.left = building.right

    player.y += dy
    for building in building_collisions:
        if player.colliderect(building):
            if dy > 0:
                player.bottom = building.top
            elif dy < 0:
                player.top = building.bottom

    player.left = max(0, player.left)
    player.right = min(WIDTH, player.right)
    player.top = max(0, player.top)
    player.bottom = min(HEIGHT, player.bottom)


# =========================================================
# INTERIOR MOVEMENT
# =========================================================

interior_walls = [
    pygame.Rect(0, 0, WIDTH, 115),
    pygame.Rect(0, 0, 25, HEIGHT),
    pygame.Rect(WIDTH - 25, 0, 25, HEIGHT),
    pygame.Rect(0, HEIGHT - 25, WIDTH, 25),
    pygame.Rect(335, 345, 330, 135),
]


def move_player_interior(dx, dy):
    player.x += dx
    for wall in interior_walls:
        if player.colliderect(wall):
            if dx > 0:
                player.right = wall.left
            elif dx < 0:
                player.left = wall.right

    player.y += dy
    for wall in interior_walls:
        if player.colliderect(wall):
            if dy > 0:
                player.bottom = wall.top
            elif dy < 0:
                player.top = wall.bottom

    player.left = max(25, player.left)
    player.right = min(WIDTH - 25, player.right)
    player.top = max(115, player.top)
    player.bottom = min(HEIGHT - 25, player.bottom)


# =========================================================
# NEARBY LOCATION
# =========================================================


def get_nearby_location():
    for name, rect in locations.items():
        area = rect.inflate(70, 70)
        if player.colliderect(area):
            return name
    return None


# =========================================================
# NEARBY NPC
# =========================================================


def get_nearby_npc():
    guardian_checks = [
        ("Visit Input Village", input_guardian),
        ("Visit Storage Vault", storage_guardian),
        ("Visit Output Tower", output_guardian),
        ("Visit Memory Monastery", memory_guardian),
    ]

    for objective, g in guardian_checks:
        if quest_active and quest_objective == objective:
            area = g["rect"].inflate(70, 70)
            if player.colliderect(area):
                return g

    for npc in npcs:
        area = npc["rect"].inflate(70, 70)
        if player.colliderect(area):
            return npc

    return None


# =========================================================
# DIALOGUE
# =========================================================


def draw_dialogue():
    if not dialogue_open:
        return

    box = pygame.Rect(100, HEIGHT - 165, WIDTH - 200, 125)
    pygame.draw.rect(screen, (35, 30, 30), box)
    pygame.draw.rect(screen, GOLD, box, 3)

    name_surface = location_font.render(dialogue_name, True, GOLD)
    screen.blit(name_surface, (box.x + 20, box.y + 12))

    words = dialogue_text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] < box.width - 40:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "

    if current_line:
        lines.append(current_line)

    for i, line in enumerate(lines[:3]):
        text_surface = font.render(line, True, WHITE)
        screen.blit(text_surface, (box.x + 20, box.y + 42 + i * 22))

    hint = small_font.render("Press E to close", True, (190, 190, 190))
    screen.blit(hint, (box.right - hint.get_width() - 20, box.bottom - 22))


# =========================================================
# TEXT WRAPPING
# =========================================================


def wrap_text(text, font_obj, max_width):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + word + " "
        if font_obj.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current.strip())
            current = word + " "

    if current:
        lines.append(current.strip())

    return lines


# =========================================================
# CHALLENGE
# =========================================================


def draw_challenge():
    if not challenge_open:
        return

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))

    box = pygame.Rect(100, 95, 800, 465)
    pygame.draw.rect(screen, (28, 27, 38), box, border_radius=14)
    pygame.draw.rect(screen, GOLD, box, 3, border_radius=14)

    header = pygame.Rect(box.x, box.y, box.width, 62)
    pygame.draw.rect(screen, (50, 42, 58), header, border_radius=14)

    title = title_font.render("GUARDIAN CHALLENGE", True, GOLD)
    screen.blit(title, (box.x + 25, box.y + 16))

    instruction = small_font.render(
        "Choose an answer with keys 1 - 4", True, (205, 200, 190)
    )
    screen.blit(
        instruction, (box.right - instruction.get_width() - 25, box.y + 24)
    )

    question_lines = wrap_text(challenge_question, font, box.width - 70)
    y = box.y + 85

    for line in question_lines:
        text = font.render(line, True, WHITE)
        screen.blit(text, (box.x + 35, y))
        y += 30

    y += 12

    for i, option in enumerate(challenge_options):
        card = pygame.Rect(box.x + 35, y, box.width - 70, 47)
        pygame.draw.rect(screen, (45, 42, 55), card, border_radius=8)
        pygame.draw.rect(screen, (105, 96, 115), card, 1, border_radius=8)

        number = title_font.render(str(i + 1), True, GOLD)
        screen.blit(number, (card.x + 14, card.y + 7))

        option_text = font.render(option, True, WHITE)
        screen.blit(option_text, (card.x + 52, card.y + 12))

        y += 55

    if challenge_result:
        result = font.render(challenge_result, True, GOLD)
        screen.blit(result, (box.x + 35, box.bottom - 38))


# =========================================================
# GUARDIAN EFFECT
# =========================================================


def spawn_guardian_effect(name):
    global guardian_effect_timer
    global guardian_effect_name
    global guardian_particles

    guardian_effect_timer = 100
    guardian_effect_name = name
    guardian_particles = []

    for _ in range(28):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.5, 4.5)

        guardian_particles.append({
            "x": float(player.centerx),
            "y": float(player.centery),
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": random.randint(35, 75),
            "size": random.randint(2, 5),
        })


def update_guardian_effect():
    global guardian_effect_timer
    global guardian_particles

    if guardian_effect_timer > 0:
        guardian_effect_timer -= 1

    for particle in guardian_particles:
        particle["x"] += particle["vx"]
        particle["y"] += particle["vy"]
        particle["vy"] += 0.035
        particle["life"] -= 1

    guardian_particles = [
        particle for particle in guardian_particles if particle["life"] > 0
    ]


def draw_guardian_effect():
    if guardian_effect_timer <= 0:
        return

    for particle in guardian_particles:
        pygame.draw.circle(
            screen,
            GOLD,
            (int(particle["x"]), int(particle["y"])),
            particle["size"],
        )

    if guardian_effect_timer > 55:
        banner = pygame.Rect(245, 175, 510, 90)
        pygame.draw.rect(screen, (25, 22, 35), banner, border_radius=12)
        pygame.draw.rect(screen, GOLD, banner, 3, border_radius=12)

        title = title_font.render(guardian_effect_name + " DEFEATED!", True, GOLD)
        screen.blit(title, (banner.centerx - title.get_width() // 2, banner.y + 16))

        reward = small_font.render("+100 XP    +1 CORE FRAGMENT", True, WHITE)
        screen.blit(
            reward, (banner.centerx - reward.get_width() // 2, banner.y + 55)
        )


# =========================================================
# QUEST TRACKER
# =========================================================


def draw_quest_tracker():
    if not quest_active and not quest_completed:
        return

    panel = pygame.Rect(20, 90, 300, 95)
    pygame.draw.rect(screen, (25, 22, 35), panel, border_radius=10)
    pygame.draw.rect(screen, (180, 150, 80), panel, 2, border_radius=10)

    title = quest_title_font.render(quest_title, True, (255, 220, 130))
    screen.blit(title, (35, 102))

    if quest_completed:
        objective = "Mission Complete!"
        color = (120, 220, 140)
    else:
        objective = "> " + quest_objective
        color = (235, 235, 235)

    text_surface = quest_text_font.render(objective, True, color)
    screen.blit(text_surface, (35, 138))


# =========================================================
# QUEST MESSAGE
# =========================================================


def draw_quest_message():
    global quest_message_timer

    if quest_message_timer <= 0:
        return

    text_surface = message_font.render(quest_message, True, (255, 220, 130))
    box = pygame.Rect(
        WIDTH // 2 - text_surface.get_width() // 2 - 25,
        125,
        text_surface.get_width() + 50,
        45,
    )

    pygame.draw.rect(screen, (25, 22, 35), box, border_radius=8)
    pygame.draw.rect(screen, (180, 150, 80), box, 2, border_radius=8)

    screen.blit(
        text_surface, (WIDTH // 2 - text_surface.get_width() // 2, 137)
    )

    quest_message_timer -= 1


# =========================================================
# RPG HUD
# =========================================================


def draw_rpg_hud():
    panel = pygame.Rect(770, 18, 210, 62)
    pygame.draw.rect(screen, (25, 22, 35), panel, border_radius=10)
    pygame.draw.rect(screen, (180, 150, 80), panel, 2, border_radius=10)

    xp_text = small_font.render(f"XP  {player_xp}", True, WHITE)
    fragment_text = small_font.render(
        f"CORE FRAGMENTS  {guardian_fragments}/5", True, (255, 220, 130)
    )

    screen.blit(xp_text, (785, 29))
    screen.blit(fragment_text, (785, 52))


def award_guardian_reward(guardian_name):
    global player_xp
    global guardian_fragments

    player_xp += 100
    guardian_fragments += 1

    spawn_guardian_effect(guardian_name)
    show_message(f"{guardian_name} DEFEATED  +100 XP  +1 CORE FRAGMENT")


# =========================================================
# WORLD
# =========================================================


def draw_world():
    screen.fill(GRASS)
    pygame.draw.rect(screen, SKY, (0, 0, WIDTH, 270))

    draw_mountains()
    draw_roads()
    draw_ground_details()

    for house in houses:
        house.draw()

    draw_memory_monastery(locations["Memory Monastery"])
    draw_cpu_dzong(locations["CPU Dzong"])
    draw_input_village(locations["Input Village"])
    draw_output_tower(locations["Output Tower"])
    draw_storage_vault(locations["Storage Vault"])

    draw_flag(120, 300)
    draw_flag(760, 300)

    draw_fence(20, 455, 150)
    draw_fence(830, 455, 150)

    draw_bridge(460, 455)

    tree_positions = [
        (40, 230),
        (110, 260),
        (270, 185),
        (350, 220),
        (700, 190),
        (850, 220),
        (950, 250),
        (30, 570),
        (180, 540),
        (330, 580),
        (700, 570),
        (850, 540),
        (960, 570),
    ]

    for x, y in tree_positions:
        draw_tree(x, y)

    draw_sign(270, 440, "INPUT")
    draw_sign(600, 440, "OUTPUT")
    draw_sign(430, 575, "STORAGE")

    # =====================================================
    # NORMAL NPCS
    # =====================================================

    for npc in npcs:
        draw_npc(npc)

    # =====================================================
    # QUEST GUARDIANS
    # =====================================================

    if quest_active and quest_objective == "Visit Input Village":
        draw_input_guardian()

    if quest_active and quest_objective == "Visit Storage Vault":
        draw_storage_guardian()

    if quest_active and quest_objective == "Visit Output Tower":
        draw_output_guardian()

    if quest_active and quest_objective == "Visit Memory Monastery":
        draw_memory_guardian()

    draw_player()


# =========================================================
# CPU DZONG INTERIOR
# =========================================================


def draw_cpu_dzong_interior():
    screen.fill(INTERIOR_WALL)

    # Back wall
    pygame.draw.rect(screen, (82, 55, 43), (55, 55, 890, 340))

    # Floor
    pygame.draw.rect(screen, INTERIOR_FLOOR, (0, 395, WIDTH, 255))

    # Floor boards
    for y in range(410, HEIGHT, 32):
        pygame.draw.line(screen, INTERIOR_DARK, (0, y), (WIDTH, y), 2)

    # Pillars
    for x in [90, 270, 730, 910]:
        pygame.draw.rect(screen, INTERIOR_DARK, (x, 65, 30, 330))
        pygame.draw.rect(screen, INTERIOR_WOOD, (x + 5, 65, 20, 330))
        pygame.draw.rect(screen, GOLD, (x - 5, 70, 40, 8))

    # Bhutanese wall panels
    panels = [(140, 115), (350, 115), (560, 115), (770, 115)]

    for x, y in panels:
        panel = pygame.Rect(x, y, 130, 120)
        pygame.draw.rect(screen, (125, 75, 43), panel)
        pygame.draw.rect(screen, GOLD, panel, 3)

        pygame.draw.polygon(
            screen,
            (170, 110, 55),
            [
                (x + 65, y + 15),
                (x + 105, y + 60),
                (x + 65, y + 105),
                (x + 25, y + 60),
            ],
        )

        pygame.draw.polygon(
            screen,
            (85, 55, 40),
            [
                (x + 65, y + 30),
                (x + 90, y + 60),
                (x + 65, y + 90),
                (x + 40, y + 60),
            ],
        )

    # Ceiling
    pygame.draw.rect(screen, INTERIOR_DARK, (0, 55, WIDTH, 18))

    for x in range(0, WIDTH, 125):
        pygame.draw.rect(screen, INTERIOR_WOOD, (x, 45, 22, 350))

    # Central platform
    pygame.draw.ellipse(screen, (45, 35, 30), (320, 350, 360, 80))
    pygame.draw.rect(screen, INTERIOR_DARK, (350, 340, 300, 55))
    pygame.draw.rect(screen, GOLD, (360, 340, 280, 8))

    # =====================================================
    # COMPUTER CORE
    # =====================================================

    core_x = 500
    core_y = 275

    pulse = int((math.sin(pygame.time.get_ticks() / 300) + 1) * 5)

    pygame.draw.circle(screen, (45, 85, 115), (core_x, core_y), 85 + pulse)
    pygame.draw.circle(screen, (55, 110, 150), (core_x, core_y), 68 + pulse)
    pygame.draw.circle(screen, CORE_BLUE, (core_x, core_y), 50 + pulse)
    pygame.draw.circle(screen, CORE_LIGHT, (core_x, core_y), 30)
    pygame.draw.circle(screen, WHITE, (core_x, core_y), 12)

    # Orbit rings
    pygame.draw.ellipse(screen, GOLD, (425, 250, 150, 50), 3)
    pygame.draw.ellipse(screen, GOLD, (455, 215, 90, 120), 3)

    core_label = location_font.render("THE COMPUTER CORE", True, WHITE)
    screen.blit(core_label, (core_x - core_label.get_width() // 2, 365))

    # Lamps
    for x in [170, 830]:
        pygame.draw.rect(screen, INTERIOR_WOOD, (x - 8, 215, 16, 55))
        pygame.draw.circle(screen, (230, 170, 70), (x, 205), 15)
        pygame.draw.circle(screen, (255, 220, 130), (x, 205), 7)

    # Title
    title = title_font.render("CPU DZONG", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 15))

    subtitle = small_font.render(
        "Chamber of the Computer Core", True, (220, 200, 170)
    )
    screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 48))

    # Exit
    pygame.draw.rect(screen, INTERIOR_DARK, cpu_dzong_exit)
    pygame.draw.rect(screen, GOLD, cpu_dzong_exit, 3)
    pygame.draw.circle(
        screen, GOLD, (cpu_dzong_exit.centerx, cpu_dzong_exit.top + 18), 5
    )

    exit_label = small_font.render("EXIT", True, WHITE)
    screen.blit(
        exit_label,
        (
            cpu_dzong_exit.centerx - exit_label.get_width() // 2,
            cpu_dzong_exit.top + 31,
        ),
    )

    # Dorji
    draw_guardian()

    # Player
    draw_player()


# =========================================================
# GAME ACTION HELPERS
# =========================================================


def show_message(text):
    global quest_message
    global quest_message_timer

    quest_message = text
    quest_message_timer = 180


def open_dialogue(name, text):
    global dialogue_open
    global dialogue_name
    global dialogue_text

    dialogue_open = True
    dialogue_name = name
    dialogue_text = text


# =========================================================
# NPC INTERACTION
# =========================================================


def talk_to_npc(npc):
    global quest_active
    global quest_objective

    global challenge_open
    global challenge_question
    global challenge_options
    global challenge_answer
    global challenge_result

    name = npc["name"]

    # =====================================================
    # TASHI
    # =====================================================

    if name == "Tashi":
        if not quest_active and not quest_completed:
            open_dialogue(
                "Tashi",
                "The Core has awakened. Something is wrong inside CPU Dzong.",
            )
            quest_active = True
            quest_objective = "Reach CPU Dzong"
            show_message("MISSION STARTED: THE AWAKENING")

        elif quest_active:
            open_dialogue(
                "Tashi",
                tashi_hints.get(
                    quest_objective,
                    "Keep going, traveler. The Core needs you.",
                ),
            )
        else:
            open_dialogue(
                "Tashi",
                "You have done well, traveler. The Core is safe for now.",
            )

    # =====================================================
    # PEMA
    # =====================================================

    elif name == "Pema":
        open_dialogue("Pema", "The machines around us have many secrets.")

    # =====================================================
    # KARMA
    # =====================================================

    elif name == "Karma":
        if quest_active and quest_objective == "Visit Input Village":
            open_dialogue(
                "Karma",
                "I am Karma, Guardian of Input. "
                "Input devices allow us to send "
                "information and instructions to a computer.",
            )
            challenge_open = True
            prepare_challenge("Karma")
            show_message("INPUT GUARDIAN CHALLENGE")
        else:
            open_dialogue(
                "Karma",
                "Input devices help us communicate with a computer.",
            )

    # =====================================================
    # DAWA
    # =====================================================

    elif name == "Dawa":
        if quest_active and quest_objective == "Visit Storage Vault":
            open_dialogue(
                "Dawa",
                "I am Dawa, Guardian of Storage. "
                "Storage keeps data and information "
                "so that it can be used again later. "
                "Hard drives, SSDs and USB drives "
                "are examples of storage devices.",
            )
            challenge_open = True
            prepare_challenge("Dawa")
            show_message("STORAGE GUARDIAN CHALLENGE")
        else:
            open_dialogue(
                "Dawa",
                "Storage allows information to remain available for later use.",
            )

    # =====================================================
    # CHODEN
    # =====================================================

    elif name == "Choden":
        if quest_active and quest_objective == "Visit Output Tower":
            open_dialogue(
                "Choden",
                "I am Choden, Guardian of Output. "
                "Output devices such as monitors, "
                "speakers and printers show us the "
                "results the computer has produced.",
            )
            challenge_open = True
            prepare_challenge("Choden")
            show_message("OUTPUT GUARDIAN CHALLENGE")
        else:
            open_dialogue(
                "Choden",
                "Output devices turn the computer's work into something we can see or hear.",
            )

    # =====================================================
    # MEMORY GUARDIAN
    # =====================================================

    elif name == "Sonam":
        if quest_active and quest_objective == "Visit Memory Monastery":
            open_dialogue(
                "Sonam",
                "I am Sonam, Guardian of Memory. "
                "Memory allows a computer to hold "
                "data and instructions while programs "
                "are running. RAM is temporary memory, "
                "while ROM stores important instructions.",
            )
            challenge_open = True
            prepare_challenge("Sonam")
            show_message("MEMORY GUARDIAN CHALLENGE")
        else:
            open_dialogue(
                "Sonam",
                "Memory helps the computer remember the information it needs.",
            )


# =========================================================
# DORJI INTERACTION
# =========================================================


def talk_to_dorji():
    global quest_active
    global quest_completed
    global quest_title
    global quest_objective
    global player_xp
    global mission_bonus_awarded

    global challenge_open
    global challenge_question
    global challenge_options
    global challenge_answer
    global challenge_result

    # =====================================================
    # START FIVE GUARDIANS
    # =====================================================

    if quest_objective == "Talk to Dorji":
        quest_active = True
        quest_completed = False
        quest_title = "THE FIVE GUARDIANS"
        quest_objective = "Visit Input Village"

        show_message("MISSION STARTED: THE FIVE GUARDIANS")

        open_dialogue(
            "Dorji",
            "The Computer Core is unstable. "
            "You must learn about the five great "
            "parts of a computer system.",
        )

    # =====================================================
    # RETURN AFTER INPUT
    # =====================================================

    elif quest_objective == "Return to Dorji":
        show_message("PROCESSING GUARDIAN CHALLENGE")

        open_dialogue(
            "Dorji",
            "Excellent work. You have learned about "
            "Input. Now prove that you understand "
            "Processing.",
        )

        challenge_open = True
        prepare_challenge("Dorji")

    # =====================================================
    # FINAL REPORT
    # =====================================================

    elif quest_objective == "Report to Dorji":
        quest_completed = True
        quest_active = False

        if not mission_bonus_awarded:
            player_xp += 250
            mission_bonus_awarded = True

        show_message("MISSION COMPLETE  +250 XP  THE CORE IS RESTORED")

        open_dialogue(
            "Dorji",
            "You have met the guardians of Input, "
            "Processing, Storage, Output and Memory. "
            "The Core is stable again. Well done, "
            "young guardian!",
        )

    # =====================================================
    # AFTER COMPLETION
    # =====================================================

    elif quest_completed:
        open_dialogue(
            "Dorji",
            "The Core is stable for now. But something deeper is awakening.",
        )

    else:
        open_dialogue("Dorji", "Continue your journey, young guardian.")


# =========================================================
# MAIN INTERACTION
# =========================================================


def handle_interaction():
    global dialogue_open
    global current_scene
    global quest_objective

    # =====================================================
    # CLOSE DIALOGUE
    # =====================================================

    if dialogue_open:
        dialogue_open = False
        return

    # =====================================================
    # VILLAGE
    # =====================================================

    if current_scene == "village":
        nearby_npc = get_nearby_npc()

        if nearby_npc:
            talk_to_npc(nearby_npc)

        # =================================================
        # ENTER CPU DZONG
        # =================================================

        elif (quest_active or quest_completed) and player.colliderect(
            cpu_dzong_entrance.inflate(25, 20)
        ):
            current_scene = "cpu_dzong"

            if quest_objective == "Reach CPU Dzong":
                quest_objective = "Talk to Dorji"

            show_message("ENTERED CPU DZONG")

            player.x = 487
            player.y = 500

        # =================================================
        # EXPLORE BUILDING
        # =================================================

        else:
            nearby = get_nearby_location()

            if nearby and nearby in location_info:
                open_dialogue(nearby, location_info[nearby])

    # =====================================================
    # CPU DZONG
    # =====================================================

    elif current_scene == "cpu_dzong":
        if player.colliderect(guardian["rect"].inflate(45, 45)):
            talk_to_dorji()

        elif player.colliderect(cpu_dzong_exit.inflate(25, 20)):
            current_scene = "village"

            player.x = 487
            player.y = 395


# =========================================================
# MAIN LOOP
# =========================================================

running = True

while running:
    update_guardian_effect()

    # =====================================================
    # EVENTS
    # =====================================================

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            # =================================================
            # GUARDIAN CHALLENGE
            # =================================================

            if challenge_open:
                if event.key in (
                    pygame.K_1,
                    pygame.K_2,
                    pygame.K_3,
                    pygame.K_4,
                ):
                    selected = event.key - pygame.K_0

                    if selected == challenge_answer:
                        challenge_result = "Correct! Guardian challenge passed."
                        challenge_open = False

                        # INPUT
                        if quest_objective == "Visit Input Village":
                            quest_objective = "Return to Dorji"
                            award_guardian_reward("INPUT GUARDIAN")

                        # PROCESSING
                        elif quest_objective == "Return to Dorji":
                            quest_objective = "Visit Storage Vault"
                            award_guardian_reward("PROCESSING GUARDIAN")

                        # STORAGE
                        elif quest_objective == "Visit Storage Vault":
                            quest_objective = "Visit Output Tower"
                            award_guardian_reward("STORAGE GUARDIAN")

                        # OUTPUT
                        elif quest_objective == "Visit Output Tower":
                            quest_objective = "Visit Memory Monastery"
                            award_guardian_reward("OUTPUT GUARDIAN")

                        # MEMORY
                        elif quest_objective == "Visit Memory Monastery":
                            quest_objective = "Report to Dorji"
                            award_guardian_reward("MEMORY GUARDIAN")

                    else:
                        challenge_result = "Not quite. Try again."

                continue

            # =================================================
            # INTERACTION
            # =================================================

            if event.key == pygame.K_e:
                handle_interaction()

    # =====================================================
    # KEYBOARD
    # =====================================================

    keys = pygame.key.get_pressed()

    dx = 0
    dy = 0

    # =====================================================
    # LEFT
    # =====================================================

    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        dx -= player_speed
        player_direction = "left"

    # =====================================================
    # RIGHT
    # =====================================================

    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        dx += player_speed
        player_direction = "right"

    # =====================================================
    # UP
    # =====================================================

    if keys[pygame.K_w] or keys[pygame.K_UP]:
        dy -= player_speed
        player_direction = "up"

    # =====================================================
    # DOWN
    # =====================================================

    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        dy += player_speed
        player_direction = "down"

    # =====================================================
    # MOVEMENT STATE
    # =====================================================

    player_moving = dx != 0 or dy != 0

    # =====================================================
    # MOVEMENT
    # =====================================================

    if not dialogue_open and not challenge_open:
        if current_scene == "village":
            move_player(dx, dy)
        elif current_scene == "cpu_dzong":
            move_player_interior(dx, dy)

    # =====================================================
    # DRAW VILLAGE
    # =====================================================

    if current_scene == "village":
        draw_world()
        draw_guardian_effect()
        draw_quest_tracker()
        draw_quest_message()
        draw_rpg_hud()

        # =================================================
        # TITLE
        # =================================================

        title = title_font.render("THE CORE", True, WHITE)
        screen.blit(title, (20, 18))

        subtitle = small_font.render("Computer System", True, WHITE)
        screen.blit(subtitle, (22, 50))

        # =================================================
        # INTERACTION PROMPTS
        # =================================================

        if not dialogue_open:
            nearby_npc = get_nearby_npc()

            # CPU DZONG
            if (quest_active or quest_completed) and player.colliderect(
                cpu_dzong_entrance.inflate(25, 20)
            ):
                draw_prompt("[E] Enter CPU Dzong", HEIGHT - 48)

            # BUILDINGS
            nearby = get_nearby_location()
            if nearby and nearby != "CPU Dzong" and not nearby_npc:
                draw_prompt(f"[E] Explore {nearby}", HEIGHT - 48)

            # NPC / GUARDIAN
            if nearby_npc:
                draw_prompt(
                    f"[E] Talk to {nearby_npc['name']}", HEIGHT - 90, 340
                )

        # =================================================
        # DIALOGUE
        # =================================================

        draw_dialogue()
        draw_challenge()

    # =====================================================
    # CPU DZONG
    # =====================================================

    elif current_scene == "cpu_dzong":
        draw_cpu_dzong_interior()
        draw_quest_tracker()
        draw_quest_message()
        draw_rpg_hud()

        if not dialogue_open:
            # =================================================
            # DORJI
            # =================================================

            if player.colliderect(guardian["rect"].inflate(45, 45)):
                draw_prompt("[E] Talk to Dorji", HEIGHT - 90, 340)

            # =================================================
            # EXIT
            # =================================================

            if player.colliderect(cpu_dzong_exit.inflate(25, 20)):
                draw_prompt("[E] Exit CPU Dzong", HEIGHT - 48, 340)

        # =================================================
        # DIALOGUE + CHALLENGE
        # =================================================

        draw_dialogue()
        draw_challenge()

    # =====================================================
    # DISPLAY
    # =====================================================

    pygame.display.flip()
    clock.tick(60)


# =========================================================
# EXIT
# =========================================================

pygame.quit()
sys.exit()