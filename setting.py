import pygame

pygame.init()
pygame.font.init()

WIDTH = 1000
HEIGHT = 650

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