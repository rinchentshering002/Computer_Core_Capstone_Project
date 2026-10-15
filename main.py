import pygame
import sys
import math
import random
import asyncio
from setting import *

sys.modules.setdefault("main", sys.modules[__name__])
# =========================================================
# MUSIC
# =========================================================
try:
    pygame.mixer.pre_init(48000, -16, 2, 512)
except Exception:
    pass
pygame.mixer.init()
try:
    pygame.mixer.music.load("assets/music/village_theme.ogg")
    pygame.mixer.music.set_volume(0.20)
    pygame.mixer.music.play(-1)
except (pygame.error, FileNotFoundError):
    pass

# =========================================================
# CREATE WINDOW FIRST
# =========================================================
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("THE CORE - Drukora")
clock = pygame.time.Clock()

# =========================================================
# NOW IMPORT MODULES
# =========================================================
import player
import world
import drukma_chat
import save_system
import sound_system
import story_state
import tashi_quest
import drukma_commentary
import eastern_ruins
import processing_citadel
import memory_monastery
import storage_vault
import network_highlands
import deep_archive
import core_heart

world.unlock_location("CPU Dzong")
DEBUG_ALL_GUARDIANS = False

print(f"[DEBUG] broken_workshop.png: {tashi_quest.WORKSHOP_IMG is not None}")
print(f"[DEBUG] workshop parts: {tashi_quest.COMPONENT_ICONS is not None}")

# =========================================================
# DRUKMA SPRITE
# =========================================================
try:
    drukma_image = pygame.image.load("assets/sprite/drukma.png").convert_alpha()
except pygame.error:
    print("WARNING: drukma.png not found!")
    drukma_image = pygame.Surface((40, 40), pygame.SRCALPHA)
    drukma_image.fill((0, 150, 255))

# =========================================================
# TITLE SCREEN IMAGE LOADING
# =========================================================
title_landscape_img = None
title_frame_img = None

def load_title_assets():
    global title_landscape_img, title_frame_img
    try:
        img = pygame.image.load("assets/environment/backgrounds/title_landscape.png").convert()
        img_ratio = img.get_width() / img.get_height()
        screen_ratio = WIDTH / HEIGHT
        if img_ratio > screen_ratio:
            new_h = HEIGHT
            new_w = int(HEIGHT * img_ratio)
            img = pygame.transform.smoothscale(img, (new_w, new_h))
            crop_x = (new_w - WIDTH) // 2
            title_landscape_img = img.subsurface(
                pygame.Rect(crop_x, 0, WIDTH, HEIGHT)).copy()
        else:
            new_w = WIDTH
            new_h = int(WIDTH / img_ratio)
            img = pygame.transform.smoothscale(img, (new_w, new_h))
            crop_y = (new_h - HEIGHT) // 2
            title_landscape_img = img.subsurface(
                pygame.Rect(0, crop_y, WIDTH, HEIGHT)).copy()
        print("Loaded title landscape")
    except (pygame.error, FileNotFoundError):
        print("WARNING: title_landscape.png not found")
        title_landscape_img = None

    try:
        frame = pygame.image.load("assets/environment/decorations/title_frame.png").convert_alpha()
        title_frame_img = pygame.transform.smoothscale(frame, (WIDTH, HEIGHT))
        print("Loaded title frame")
    except (pygame.error, FileNotFoundError):
        print("WARNING: title_frame.png not found")
        title_frame_img = None

load_title_assets()
sound_system.init()

# =========================================================
# INTRO / TITLE SCREEN STATE
# =========================================================
game_state = "title"
intro_page = 0
intro_timer = 0

INTRO_PAGES = [
    (3.0, "The mountains have brought you here.", "But why... you do not know."),
    (3.2, "Your device stirs.", "SYSTEM: Recovery interface dormant."),
    (3.2, "A voice reaches out from the mist.", "UNKNOWN VOICE: Connection... detected."),
    (3.5, "THE CORE", "D R U K O R A"),
]
INTRO_ICONS = ["mountain", "crystal", "signal", "title"]

# =========================================================
# GAME STATE
# =========================================================
current_scene = "village"

dialogue_open = False
dialogue_name = ""
dialogue_queue = []
dialogue_index = 0
dialogue_action = None

challenge_open = False
challenge_question = ""
challenge_options = []
challenge_answer = 0
challenge_result = ""

quest_active = True
quest_completed = False
quest_title = "THE AWAKENING"
quest_objective = "Talk to the Village Elder"
quest_message = ""
quest_message_timer = 0

player_xp = 0
guardian_fragments = 0
mission_bonus_awarded = False
footstep_timer = 0
voice_blip_timer = 0
_last_voiced_line = None

paused = False
pause_selected = 0
pause_flash_text = ""
pause_flash_timer = 0

journal_open = False
journal_selected = 0

ending_pending = False
ending_page = 0
ending_timer = 0
_startup_banner_shown = False

PAUSE_MENU_ITEMS = [
    "Resume",
    "Save Game",
    "Load Game",
    "Toggle Music",
    "Quit to Title",
    "Quit to Desktop",
]

ENDING_PAGES = [
    (3.5, "The Core pulses once more.", "A warm light spreads through the Dzong."),
    (3.5, "Karma: \"You did it, young guardian.\"", "\"The kingdom will remember your name.\""),
    (3.5, "Drukma: \"I remember now.\"", "\"I was... the first guardian. The one who fell.\""),
    (3.5, "Drukma: \"But you gave me purpose again.\"", "\"Thank you, traveler.\""),
    (4.0, "The mountains stand silent.", "The Core hums softly in the distance."),
    (4.0, "THE CORE", "D R U K O R A"),
    (5.0, "TO BE CONTINUED...", "Thank you for playing"),
]

# =========================================================
# DRUKMA STATE
# =========================================================
drukma_awake = False
drukma_x = 0.0
drukma_y = 0.0
drukma_bob_phase = 0.0

drukma_speech = ""
drukma_speech_timer = 0
drukma_seen_zones = set()

DRUKMA_ZONES = [
    ("input_village",    pygame.Rect(20, 270, 220, 140),
     "Input... devices that send information INTO a system. I understand this."),
    ("cpu_dzong",        pygame.Rect(370, 270, 260, 170),
     "Processing. Instructions executed here. But... something is wrong inside."),
    ("storage_vault",    pygame.Rect(370, 510, 260, 150),
     "Storage. Records that survive even when power is gone. I know this."),
    ("output_tower",     pygame.Rect(770, 260, 200, 170),
     "Output. The results return to the world. Monitors. Speakers. Printers."),
    ("memory_monastery", pygame.Rect(370, 60, 260, 150),
     "Memory. Short and long. I... feel like I've been here before. But I don't know why."),
]

# =========================================================
# REWARD BANNER STATE
# =========================================================
reward_timer = 0
reward_title = ""
reward_subtitle = ""
reward_particles = []

# =========================================================
# GUARDIAN CHALLENGES
# =========================================================
guardian_challenges = {
    "Dorji": {
        "question": "Which device is used to enter text into a computer?",
        "options": ["Monitor", "Keyboard", "Speaker", "Printer"],
        "answer": "Keyboard",
    },
    "Karma": {
        "question": "Which part of the computer executes instructions and controls the system?",
        "options": ["Monitor", "CPU", "Keyboard", "Printer"],
        "answer": "CPU",
    },
    "Dawa": {
        "question": "Which type of memory temporarily stores data while programs run?",
        "options": ["ROM", "RAM", "Hard Drive", "USB Drive"],
        "answer": "RAM",
    },
    "Choden": {
        "question": "Which device is mainly used to store data for long-term use?",
        "options": ["Monitor", "Hard Drive", "Keyboard", "Speaker"],
        "answer": "Hard Drive",
    },
    "Sonam": {
        "question": "Which device displays the visual results produced by a computer?",
        "options": ["Monitor", "Keyboard", "Microphone", "Hard Drive"],
        "answer": "Monitor",
    },
}

tashi_hints = {
    "Investigate the Shrine":  ["There is an old shrine east of here.",
                                "Investigate it. The Core's fate may rest on what you find."],
    "Reach CPU Dzong":         ["Walk up the road to the CPU Dzong.",
                                "Karma, Guardian of Processing, waits inside.",
                                "Press E at its door to enter."],
    "Talk to Karma":           ["Karma is inside the CPU Dzong.",
                                "She will teach you about Processing."],
    "Visit Input Village":     ["Dorji, Guardian of Input, guards the village west of here."],
    "Return to Karma":         ["Return to Karma in the CPU Dzong.",
                                "Report what you learned."],
    "Visit Storage Vault":     ["Choden, Guardian of Storage, is at the vault south of the Dzong."],
    "Visit Output Tower":      ["Sonam, Guardian of Output, stands near the tower to the east."],
    "Visit Memory Monastery":  ["Dawa, Guardian of Memory, waits at the monastery to the north."],
    "Report to Karma":         ["You have met all five guardians.",
                                "Return to Karma in the CPU Dzong."],
    "Investigate the Eastern Ruins": ["The Eastern Ruins lie to the east of the village.",
                                       "Walk east past the shrine. The ruins still hold records.",
                                       "Press E at the gate to enter."],
    "Reach the Processing Citadel":  ["A signal still beats inside the Eastern Ruins.",
                                       "Follow it — press E at the SIGNAL LEAD marker.",
                                       "The Citadel lies beyond."],
    "Return to Drukora":       ["The truth is in your hands now.",
                                "Return to Drukora Village.",
                                "Press E at the Citadel exit to leave."],
    "Descend to the Memory Monastery": ["Drukma feels drawn north.",
                                         "The Memory Monastery holds two kinds of memory.",
                                         "Exit the Citadel and find the memory chamber."],
    "Descend to the Storage Vault":    ["The archives lie deeper still.",
                                         "Descend from the Memory Monastery.",
                                         "The Storage Vault keeps the kingdom's forgotten records."],
    "Ascend to the Network Highlands": ["Choden's vault showed a pattern to the tampering.",
                                         "Every relay tower in Drukora was touched.",
                                         "Ascend from the Vault and reach the Highlands."],
    "Reach the Signal Tower":          ["One tower still speaks.",
                                         "The Highlands hold the network's heart.",
                                         "Follow the signal."],
    "Descend to the Deep Archive":     ["The Highlands show the pattern.",
                                         "Every layer was tampered from the same source.",
                                         "Descend to the Deep Archive beneath the Core."],
    "Face what awaits below":          ["The truth is at the bottom of the Core.",
                                         "Null has been waiting.",
                                         "Descend."],
    "Face the Core's choice":          ["The Heart of the Core is open.",
                                         "Null is here.",
                                         "This is where it ends — or begins."],
}

# =========================================================
# HELPERS
# =========================================================
def show_message(text):
    global quest_message, quest_message_timer
    quest_message = text
    quest_message_timer = 180

def start_dialogue(speaker, lines, on_complete=None):
    global dialogue_open, dialogue_name, dialogue_queue, dialogue_index, dialogue_action
    global _last_voiced_line
    sound_system.stop_voice()
    dialogue_open = True
    dialogue_name = speaker
    dialogue_queue = list(lines)
    dialogue_index = 0
    dialogue_action = on_complete
    _last_voiced_line = None

def advance_dialogue():
    global dialogue_open, dialogue_index, dialogue_action, _last_voiced_line
    dialogue_index += 1
    if dialogue_index >= len(dialogue_queue):
        dialogue_open = False
        _last_voiced_line = None
        sound_system.stop_voice()
        action = dialogue_action
        dialogue_action = None
        if action:
            action()

def say_drukma(text, duration=200):
    global drukma_speech, drukma_speech_timer
    drukma_speech = text
    drukma_speech_timer = duration
    # Voice the commentary too — same path as dialogue, same fallback.
    if not sound_system.play_line("Drukma", text):
        sound_system.play_voice("Drukma")

drukma_commentary.set_speaker(say_drukma)

def prepare_challenge(guardian_name):
    global challenge_question, challenge_options, challenge_answer, challenge_result
    c = guardian_challenges[guardian_name]
    challenge_question = c["question"]
    choices = c["options"][:]
    random.shuffle(choices)
    challenge_options = choices
    challenge_answer = choices.index(c["answer"]) + 1
    challenge_result = ""

def award_guardian_reward(name):
    global player_xp, guardian_fragments, reward_timer, reward_title, reward_subtitle, reward_particles
    sound_system.play("reward")
    player_xp += 100
    guardian_fragments += 1
    reward_timer = 120
    reward_title = f"{name} DEFEATED!"
    reward_subtitle = "+100 XP    +1 CORE FRAGMENT"
    reward_particles = []
    for _ in range(40):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2.0, 6.0)
        reward_particles.append({
            "x": float(player.player.centerx),
            "y": float(player.player.centery),
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed - 1.5,
            "life": random.randint(40, 90),
            "size": random.randint(2, 5),
        })

    fragment_map = {
        "INPUT GUARDIAN": "fragment_dorji",
        "PROCESSING GUARDIAN": "fragment_karma",
        "STORAGE GUARDIAN": "fragment_choden",
        "OUTPUT GUARDIAN": "fragment_sonam",
        "MEMORY GUARDIAN": "fragment_dawa",
    }
    fid = fragment_map.get(name)
    if fid:
        award_fragment(fid)

def wrap_text(text, font_obj, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = cur + w + " "
        if font_obj.size(test)[0] <= max_width:
            cur = test
        else:
            if cur: lines.append(cur.strip())
            cur = w + " "
    if cur: lines.append(cur.strip())
    return lines

# =========================================================
# MEMORY FRAGMENTS + JOURNAL
# =========================================================
def award_fragment(fragment_id):
    if story_state.STATE.add_fragment(fragment_id):
        sound_system.play("reward")

def update_fragment_popup():
    if story_state.STATE.popup_timer > 0:
        story_state.STATE.popup_timer -= 1

def draw_fragment_popup():
    if story_state.STATE.popup_timer <= 0 or story_state.STATE.pending_fragment_popup is None:
        return

    name, source = story_state.STATE.pending_fragment_popup

    t = story_state.STATE.popup_timer
    if t > 210:
        alpha = int((240 - t) * 17)
    elif t < 40:
        alpha = int(t * 6.4)
    else:
        alpha = 255
    alpha = max(0, min(255, alpha))

    banner = pygame.Rect(180, 40, 640, 100)

    sh = pygame.Surface((banner.width + 12, banner.height + 12), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, 140), (6, 6, banner.width, banner.height), border_radius=12)
    sh.set_alpha(alpha)
    screen.blit(sh, (banner.x - 6, banner.y - 6))

    bs = pygame.Surface((banner.width, banner.height), pygame.SRCALPHA)
    pygame.draw.rect(bs, (18, 32, 45, 235), (0, 0, banner.width, banner.height), border_radius=12)
    bs.set_alpha(alpha)
    screen.blit(bs, banner.topleft)

    br = pygame.Surface((banner.width, banner.height), pygame.SRCALPHA)
    pygame.draw.rect(br, (120, 220, 240, 255), (0, 0, banner.width, banner.height), 3, border_radius=12)
    br.set_alpha(alpha)
    screen.blit(br, banner.topleft)

    title_fnt = pygame.font.SysFont("georgia", 20, bold=True)
    title_surf = title_fnt.render("MEMORY FRAGMENT ACQUIRED", True, (180, 240, 255))
    title_surf.set_alpha(alpha)
    screen.blit(title_surf, (banner.centerx - title_surf.get_width() // 2, banner.y + 18))

    name_fnt = pygame.font.SysFont("georgia", 26, bold=True)
    name_surf = name_fnt.render(name, True, (255, 245, 220))
    name_surf.set_alpha(alpha)
    screen.blit(name_surf, (banner.centerx - name_surf.get_width() // 2, banner.y + 45))

    src_surf = small_font.render(f"from {source}", True, (150, 190, 210))
    src_surf.set_alpha(alpha)
    screen.blit(src_surf, (banner.centerx - src_surf.get_width() // 2, banner.y + 78))

def draw_journal():
    if not journal_open:
        return

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    panel_w, panel_h = 900, 560
    panel_x = WIDTH // 2 - panel_w // 2
    panel_y = HEIGHT // 2 - panel_h // 2
    panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

    shadow = pygame.Surface((panel_w + 16, panel_h + 16), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 160), (8, 8, panel_w, panel_h), border_radius=16)
    screen.blit(shadow, (panel.x - 8, panel.y - 8))

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (18, 32, 45, 245), (0, 0, panel_w, panel_h), border_radius=16)
    screen.blit(panel_surf, panel.topleft)

    pygame.draw.rect(screen, (120, 220, 240), panel, 3, border_radius=16)
    pygame.draw.rect(screen, (60, 130, 160), panel.inflate(-16, -16), 1, border_radius=12)

    for cx_, cy_ in [(panel.left + 18, panel.top + 18),
                     (panel.right - 18, panel.top + 18),
                     (panel.left + 18, panel.bottom - 18),
                     (panel.right - 18, panel.bottom - 18)]:
        pygame.draw.circle(screen, (120, 220, 240), (cx_, cy_), 4)
        pygame.draw.circle(screen, (60, 130, 160), (cx_, cy_), 2)

    title_fnt = pygame.font.SysFont("georgia", 34, bold=True)
    title_surf = title_fnt.render("SYSTEM JOURNAL", True, (180, 240, 255))
    screen.blit(title_surf, (panel.centerx - title_surf.get_width() // 2, panel.y + 22))

    count = story_state.STATE.fragment_count()
    total = story_state.STATE.total_fragments()
    count_surf = small_font.render(
        f"Memory Fragments: {count} / {total}",
        True, (150, 200, 220))
    screen.blit(count_surf, (panel.centerx - count_surf.get_width() // 2, panel.y + 60))

    div_y = panel.y + 90
    pygame.draw.line(screen, (120, 220, 240),
                     (panel.x + 40, div_y), (panel.centerx - 20, div_y), 2)
    pygame.draw.line(screen, (120, 220, 240),
                     (panel.centerx + 20, div_y), (panel.right - 40, div_y), 2)
    pygame.draw.circle(screen, (120, 220, 240), (panel.centerx, div_y), 5)
    pygame.draw.circle(screen, (60, 130, 160), (panel.centerx, div_y), 2)

    entries = story_state.STATE.journal_entries
    left_col = pygame.Rect(panel.x + 30, panel.y + 110, 280, panel_h - 160)
    right_col = pygame.Rect(left_col.right + 20, panel.y + 110,
                            panel.right - left_col.right - 50, panel_h - 160)

    if not entries:
        empty = font.render("No entries yet.", True, (140, 160, 180))
        screen.blit(empty, (left_col.centerx - empty.get_width() // 2, left_col.y + 20))
    else:
        for i, entry in enumerate(entries[:9]):
            y = left_col.y + i * 44
            is_selected = (i == journal_selected)
            item_rect = pygame.Rect(left_col.x, y, left_col.width, 38)
            if is_selected:
                pygame.draw.rect(screen, (35, 60, 80), item_rect, border_radius=6)
                pygame.draw.rect(screen, (120, 220, 240), item_rect, 2, border_radius=6)
            color = (220, 250, 255) if is_selected else (180, 200, 215)
            title_s = font.render(entry["title"][:26], True, color)
            screen.blit(title_s, (item_rect.x + 12, item_rect.y + 9))

    if entries and 0 <= journal_selected < len(entries):
        entry = entries[journal_selected]
        src_surf = small_font.render(f"Source: {entry['source']}", True, (120, 180, 200))
        screen.blit(src_surf, (right_col.x, right_col.y))

        body_lines = []
        for paragraph in entry["body"].split("\n\n"):
            for line in wrap_text(paragraph, font, right_col.width):
                body_lines.append(line)
            body_lines.append("")

        y_off = right_col.y + 26
        for line in body_lines[:18]:
            txt = font.render(line, True, (225, 240, 250))
            screen.blit(txt, (right_col.x, y_off))
            y_off += 20

    hint = small_font.render(
        "UP / DOWN Navigate   ·   J or ESC Close",
        True, (140, 180, 200))
    screen.blit(hint, (panel.centerx - hint.get_width() // 2, panel.bottom - 28))

# =========================================================
# PAUSE MENU
# =========================================================
def handle_pause_selection(index):
    global paused, running, game_state
    global pause_flash_text, pause_flash_timer

    action = PAUSE_MENU_ITEMS[index]

    if action == "Resume":
        paused = False

    elif action == "Save Game":
        if save_system.save_game(collect_save_state()):
            pause_flash_text = "GAME SAVED"
        else:
            pause_flash_text = "SAVE FAILED"
        pause_flash_timer = 90

    elif action == "Load Game":
        state = save_system.load_game()
        if state:
            apply_save_state(state)
            paused = False
            show_message("GAME LOADED")
        else:
            pause_flash_text = "NO SAVE FOUND"
            pause_flash_timer = 90

    elif action == "Toggle Music":
        if pygame.mixer.music.get_volume() > 0:
            pygame.mixer.music.set_volume(0.0)
            pause_flash_text = "MUSIC OFF"
        else:
            pygame.mixer.music.set_volume(0.20)
            pause_flash_text = "MUSIC ON"
        pause_flash_timer = 60

    elif action == "Quit to Title":
        save_system.save_game(collect_save_state())
        paused = False
        game_state = "title"

    elif action == "Quit to Desktop":
        save_system.save_game(collect_save_state())
        running = False

def draw_pause_menu():
    global pause_flash_timer

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    panel_w, panel_h = 460, 500
    panel_x = WIDTH // 2 - panel_w // 2
    panel_y = HEIGHT // 2 - panel_h // 2
    panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

    shadow = pygame.Surface((panel_w + 16, panel_h + 16), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 160), (8, 8, panel_w, panel_h), border_radius=16)
    screen.blit(shadow, (panel.x - 8, panel.y - 8))

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (25, 22, 35, 245), (0, 0, panel_w, panel_h), border_radius=16)
    screen.blit(panel_surf, panel.topleft)

    pygame.draw.rect(screen, (215, 175, 70), panel, 3, border_radius=16)
    pygame.draw.rect(screen, (150, 115, 45), panel.inflate(-16, -16), 1, border_radius=12)

    for cx_, cy_ in [(panel.left + 18, panel.top + 18),
                     (panel.right - 18, panel.top + 18),
                     (panel.left + 18, panel.bottom - 18),
                     (panel.right - 18, panel.bottom - 18)]:
        pygame.draw.circle(screen, (215, 175, 70), (cx_, cy_), 4)
        pygame.draw.circle(screen, (150, 115, 45), (cx_, cy_), 2)

    title_fnt = pygame.font.SysFont("georgia", 42, bold=True)
    title_surf = title_fnt.render("PAUSED", True, (245, 220, 130))
    screen.blit(title_surf, (panel.centerx - title_surf.get_width() // 2, panel.y + 28))

    div_y = panel.y + 92
    pygame.draw.line(screen, (215, 175, 70),
                     (panel.x + 40, div_y), (panel.centerx - 20, div_y), 2)
    pygame.draw.line(screen, (215, 175, 70),
                     (panel.centerx + 20, div_y), (panel.right - 40, div_y), 2)
    pygame.draw.circle(screen, (215, 175, 70), (panel.centerx, div_y), 5)
    pygame.draw.circle(screen, (150, 115, 45), (panel.centerx, div_y), 2)

    item_fnt = pygame.font.SysFont("georgia", 24, bold=True)
    item_h = 48
    start_y = panel.y + 118

    for i, item in enumerate(PAUSE_MENU_ITEMS):
        y = start_y + i * item_h
        is_selected = (i == pause_selected)

        if is_selected:
            hl = pygame.Rect(panel.x + 40, y - 4, panel_w - 80, item_h - 8)
            hl_surf = pygame.Surface((hl.width, hl.height), pygame.SRCALPHA)
            pygame.draw.rect(hl_surf, (75, 25, 30, 220),
                             (0, 0, hl.width, hl.height), border_radius=8)
            screen.blit(hl_surf, hl.topleft)
            pygame.draw.rect(screen, (215, 175, 70), hl, 2, border_radius=8)

        color = (245, 220, 130) if is_selected else (200, 195, 190)
        arrow = "> " if is_selected else "  "
        surf = item_fnt.render(arrow + item, True, color)
        screen.blit(surf, (panel.centerx - surf.get_width() // 2, y + 4))

    music_on = pygame.mixer.music.get_volume() > 0
    ind_surf = small_font.render(
        f"Music: {'ON' if music_on else 'OFF'}",
        True,
        (140, 200, 220) if music_on else (150, 120, 120))
    screen.blit(ind_surf, (panel.centerx - ind_surf.get_width() // 2,
                           panel.bottom - 68))

    if pause_flash_timer > 0:
        flash = small_font.render(pause_flash_text, True, (120, 220, 140))
        screen.blit(flash, (panel.centerx - flash.get_width() // 2,
                            panel.bottom - 46))
        pause_flash_timer -= 1

    footer = small_font.render(
        "UP/DOWN Navigate  ·  ENTER Select  ·  ESC Resume",
        True, (180, 175, 170))
    screen.blit(footer, (panel.centerx - footer.get_width() // 2,
                         panel.bottom - 24))

# =========================================================
# SAVE / LOAD STATE
# =========================================================
def collect_save_state():
    return {
        "player_xp": player_xp,
        "guardian_fragments": guardian_fragments,
        "quest_title": quest_title,
        "quest_objective": quest_objective,
        "quest_active": quest_active,
        "quest_completed": quest_completed,
        "mission_bonus_awarded": mission_bonus_awarded,
        "drukma_awake": drukma_awake,
        "shrine_activated": world.shrine_activated,
        "unlocked_locations": list(world.UNLOCKED_LOCATIONS),
        "drukma_seen_zones": list(drukma_seen_zones),
        "current_scene": current_scene,
        "player_x": player.player.x,
        "player_y": player.player.y,
        "player_direction": player.player_direction,
        "story_state": story_state.STATE.to_dict(),
    }

def apply_save_state(state):
    global player_xp, guardian_fragments, quest_title, quest_objective
    global quest_active, quest_completed, mission_bonus_awarded
    global drukma_awake, drukma_x, drukma_y, current_scene

    player_xp = state.get("player_xp", 0)
    guardian_fragments = state.get("guardian_fragments", 0)
    quest_title = state.get("quest_title", "THE AWAKENING")
    quest_objective = state.get("quest_objective", "Talk to the Village Elder")
    quest_active = state.get("quest_active", False)
    quest_completed = state.get("quest_completed", False)
    mission_bonus_awarded = state.get("mission_bonus_awarded", False)

    drukma_awake = state.get("drukma_awake", False)
    if drukma_awake:
        drukma_x = float(player.player.centerx - 45)
        drukma_y = float(player.player.centery - 45)
        story_state.STATE.set_flag("drukma_awake", True)

    world.shrine_activated = state.get("shrine_activated", False)
    world.UNLOCKED_LOCATIONS = set(state.get("unlocked_locations", ["CPU Dzong"]))

    drukma_seen_zones.clear()
    drukma_seen_zones.update(state.get("drukma_seen_zones", []))

    current_scene = state.get("current_scene", "village")
    player.player.x = state.get("player_x", 485)
    player.player.y = state.get("player_y", 485)
    player.player_direction = state.get("player_direction", "down")
    story_state.STATE.from_dict(state.get("story_state", {}))

    drukma_commentary.reset()

# =========================================================
# COLLISION HELPERS
# =========================================================
def build_village_collisions():
    rects = list(world.building_collisions)

    for npc in world.npcs:
        rects.append(npc["rect"].inflate(6, 6))

    rects.append(world.shrine_rect.inflate(6, 6))

    if world.is_unlocked("Input Village"):
        rects.append(world.input_guardian["rect"].inflate(6, 6))
    if world.is_unlocked("Storage Vault"):
        rects.append(world.storage_guardian["rect"].inflate(6, 6))
    if world.is_unlocked("Output Tower"):
        rects.append(world.output_guardian["rect"].inflate(6, 6))
    if world.is_unlocked("Memory Monastery"):
        rects.append(world.memory_guardian["rect"].inflate(6, 6))

    return rects

def build_dzong_collisions():
    return world.interior_walls + [world.guardian["rect"].inflate(6, 6)]

# =========================================================
# DRUKMA LOGIC
# =========================================================
def awaken_drukma():
    global drukma_awake, drukma_x, drukma_y, quest_active, quest_objective
    sound_system.play("shrine")
    drukma_awake = True
    story_state.STATE.set_flag("drukma_awake", True)
    drukma_x = float(world.shrine_rect.centerx)
    drukma_y = float(world.shrine_rect.y - 30)
    world.shrine_activated = True
    show_message("DRUKMA AWAKENED")

    if not quest_completed:
        quest_active = True
        quest_title = "THE AWAKENING"
        quest_objective = "Reach CPU Dzong"

    award_fragment("fragment_shrine")

    story_state.STATE.add_journal_entry(
        "The Voice in the Shrine",
        "A consciousness called itself Drukma.\n\n"
        "It said: 'I have waited a long time for someone to find me. "
        "My records are damaged.'\n\n"
        "It recognized my device. It recognized me — though I don't know why.\n\n"
        "It is coming with me. I do not know whether to trust it.",
        source="Drukma"
    )

    drukma_commentary.trigger("shrine_awakened")

def update_drukma():
    global drukma_x, drukma_y, drukma_bob_phase, drukma_speech_timer
    if not drukma_awake:
        return
    target_x = player.player.centerx - 45
    target_y = player.player.centery - 45
    drukma_x += (target_x - drukma_x) * 0.08
    drukma_y += (target_y - drukma_y) * 0.08
    drukma_bob_phase += 0.06
    if drukma_speech_timer > 0:
        drukma_speech_timer -= 1

def check_drukma_auto_comment():
    global drukma_seen_zones
    if not drukma_awake:
        return
    for zone_id, rect, line in DRUKMA_ZONES:
        if player.player.colliderect(rect.inflate(80, 80)):
            if zone_id not in drukma_seen_zones:
                drukma_seen_zones.add(zone_id)
                say_drukma(line)
            return

def draw_drukma(screen):
    if not drukma_awake:
        return
    bob = math.sin(drukma_bob_phase) * 4
    cx = int(drukma_x)
    cy = int(drukma_y + bob)

    DW, DH = 48, 48
    scaled_img = pygame.transform.scale(drukma_image, (DW, DH))

    pulse = int((math.sin(pygame.time.get_ticks() / 300) + 1) * 2)
    glow_surf = pygame.Surface((90, 90), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (120, 220, 240, 55), (45, 45), 26 + pulse)
    pygame.draw.circle(glow_surf, (180, 240, 255, 90), (45, 45), 15 + pulse)
    screen.blit(glow_surf, (cx - 45, cy - 45))

    screen.blit(scaled_img, (cx - DW // 2, cy - DH // 2))

    name = small_font.render("Drukma", True, (180, 240, 255))
    screen.blit(name, (cx - name.get_width() // 2, cy + 20))

    if drukma_speech_timer > 0 and drukma_speech:
        draw_speech_bubble(screen, cx, cy - 32, drukma_speech)

def draw_speech_bubble(screen, cx, cy, text):
    lines = wrap_text(text, small_font, 220)
    padding = 10
    line_h = 18
    w = max(small_font.size(l)[0] for l in lines) + padding * 2
    h = len(lines) * line_h + padding * 2
    box = pygame.Rect(cx - w // 2, cy - h - 8, w, h)

    bubble_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(bubble_surf, (18, 32, 45, 235), (0, 0, w, h), border_radius=10)
    pygame.draw.rect(bubble_surf, (120, 220, 240, 255), (0, 0, w, h), 2, border_radius=10)
    screen.blit(bubble_surf, box.topleft)

    pygame.draw.polygon(screen, (18, 32, 45), [
        (cx - 6, box.bottom - 1), (cx + 6, box.bottom - 1), (cx, box.bottom + 10)])
    pygame.draw.polygon(screen, (120, 220, 240), [
        (cx - 6, box.bottom - 1), (cx + 6, box.bottom - 1), (cx, box.bottom + 10)], 2)

    for i, line in enumerate(lines):
        txt = small_font.render(line, True, (220, 240, 250))
        screen.blit(txt, (box.x + padding, box.y + padding + i * line_h))

def talk_to_drukma():
    if not drukma_awake:
        return
    if dialogue_open or challenge_open:
        return
    drukma_chat.toggle_chat()

# =========================================================
# NEARBY DETECTION — CLOSEST NPC
# =========================================================
def get_nearby_npc():
    candidates = []

    checks = [
        ("Visit Input Village",    world.input_guardian),
        ("Visit Storage Vault",    world.storage_guardian),
        ("Visit Output Tower",     world.output_guardian),
        ("Visit Memory Monastery", world.memory_guardian),
    ]
    for objective, g in checks:
        if quest_active and quest_objective == objective:
            infl = g["rect"].inflate(60, 60)
            if player.player.colliderect(infl):
                dx = player.player.centerx - g["rect"].centerx
                dy = player.player.centery - g["rect"].centery
                candidates.append((dx * dx + dy * dy, {"name": g["name"]}))

    for npc in world.npcs:
        infl = npc["rect"].inflate(60, 60)
        if player.player.colliderect(infl):
            dx = player.player.centerx - npc["rect"].centerx
            dy = player.player.centery - npc["rect"].centery
            candidates.append((dx * dx + dy * dy, {"name": npc["name"]}))

    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    return candidates[0][1]

# =========================================================
# QUEST ACTIONS
# =========================================================
def start_awakening_quest():
    global quest_active, quest_objective
    sound_system.play("quest")
    quest_active = True
    if drukma_awake:
        quest_objective = "Reach CPU Dzong"
    else:
        quest_objective = "Investigate the Shrine"
    show_message("MISSION STARTED: THE AWAKENING")
    if drukma_awake:
        say_drukma("The road north leads to the CPU Dzong. Let us go together.")

    story_state.STATE.add_journal_entry(
        "The Elder's Request",
        "The village elder asked me to investigate the ancient shrine to the east.\n\n"
        "He said the Core — the system that once connected every region of Drukora — "
        "has gone silent. Signal towers failed. Records disappeared. Machines stopped working.\n\n"
        "He warned me not to trust the old systems blindly.\n\n"
        "But what else is there to do? I have to start somewhere.",
        source="Village Elder"
    )

def start_five_guardians_quest():
    global quest_title, quest_objective
    sound_system.play("quest")
    quest_title = "THE FIVE GUARDIANS"
    quest_objective = "Visit Input Village"
    show_message("MISSION STARTED: THE FIVE GUARDIANS")
    if drukma_awake:
        say_drukma("Five Guardians. Five forces. I will guide you.")
    story_state.STATE.set_flag("guardians_started", True)
    drukma_commentary.trigger("started_five_guardians")
    world.unlock_location("Input Village")

def open_input_challenge():
    global challenge_open
    challenge_open = True
    prepare_challenge("Dorji")

def open_processing_challenge():
    global challenge_open
    challenge_open = True
    prepare_challenge("Karma")

def open_storage_challenge():
    global challenge_open
    challenge_open = True
    prepare_challenge("Choden")

def open_output_challenge():
    global challenge_open
    challenge_open = True
    prepare_challenge("Sonam")

def open_memory_challenge():
    global challenge_open
    challenge_open = True
    prepare_challenge("Dawa")

open_karma_challenge      = open_processing_challenge
open_dorji_challenge      = open_input_challenge
open_dawa_challenge       = open_memory_challenge
open_choden_challenge     = open_storage_challenge
open_sonam_challenge      = open_output_challenge

def complete_mission():
    """Finish Act I — chain immediately into Act II (Broken Channel)."""
    global quest_completed, quest_active, player_xp, mission_bonus_awarded
    quest_completed = True
    quest_active = False
    if not mission_bonus_awarded:
        player_xp += 250
        mission_bonus_awarded = True
    show_message("MISSION COMPLETE  +250 XP")
    story_state.STATE.set_flag("mission_complete", True)
    drukma_commentary.trigger("mission_complete")
    start_broken_channel_quest()

def start_broken_channel_quest():
    """Act II begins — direct the player to the Eastern Ruins."""
    global quest_completed, quest_active, quest_title, quest_objective
    quest_completed = False
    quest_active = True
    quest_title = "THE BROKEN CHANNEL"
    quest_objective = "Investigate the Eastern Ruins"
    show_message("MISSION STARTED: THE BROKEN CHANNEL")
    story_state.STATE.set_flag("broken_channel_started", True)
    if drukma_awake:
        say_drukma("The Core's channels were modified. The Eastern Ruins hold records.")
    story_state.STATE.add_journal_entry(
        "The Broken Channel",
        "Karma's records show the Core's channels were altered long before the collapse.\n\n"
        "The Eastern Ruins — the old research outpost — may still hold evidence of who did it.\n\n"
        "I should investigate.",
        source="Karma"
    )

def check_act_chain():
    """Runs every frame. Watches story flags and advances the mission
    tracker between acts without needing a scene change."""
    global quest_title, quest_objective, quest_active, quest_completed

    # Act II → Act III: player just saw the INPUT CHANNEL tamper log
    if (quest_title == "THE BROKEN CHANNEL"
            and story_state.STATE.get_flag("eastern_ruins_tamper_seen")
            and not story_state.STATE.get_flag("act_three_started")):
        quest_title = "THE MODIFIED SEQUENCE"
        quest_objective = "Reach the Processing Citadel"
        show_message("NEW OBJECTIVE: PROCESSING CITADEL")
        story_state.STATE.set_flag("act_three_started", True)
        if drukma_awake:
            say_drukma("The signal leads further east. Something in the Citadel is still awake.")

    # Act III → Act IV: player finished the citadel
    if (quest_title == "THE MODIFIED SEQUENCE"
            and story_state.STATE.get_flag("citadel_done")
            and not story_state.STATE.get_flag("act_four_started")):
        quest_title = "THE FORGOTTEN ARCHIVE"
        quest_objective = "Descend to the Memory Monastery"
        show_message("NEW OBJECTIVE: MEMORY MONASTERY")
        story_state.STATE.set_flag("act_four_started", True)
        if drukma_awake:
            say_drukma("The Core remembers more than the surface. We must go deeper.")

    # One-time beat: Drukma thanks the player for bringing it along.
    if (story_state.STATE.get_flag("act_four_started")
            and not story_state.STATE.get_flag("drukma_thanked")):
        story_state.STATE.set_flag("drukma_thanked", True)
        if drukma_awake:
            say_drukma("Thank you, by the way. For bringing me with you.")

    # Act IV → Act V: player finished the monastery
    if (quest_title == "THE FORGOTTEN ARCHIVE"
            and story_state.STATE.get_flag("monastery_done")
            and not story_state.STATE.get_flag("act_five_started")):
        quest_title = "THE LOST ARCHIVES"
        quest_objective = "Descend to the Storage Vault"
        show_message("NEW OBJECTIVE: STORAGE VAULT")
        story_state.STATE.set_flag("act_five_started", True)
        if drukma_awake:
            say_drukma("The archives will hold what the monastery let go.")

    # Act V → Act VI: player finished the vault
    if (quest_title == "THE LOST ARCHIVES"
            and story_state.STATE.get_flag("vault_done")
            and not story_state.STATE.get_flag("act_six_started")):
        quest_title = "THE SHATTERED NETWORK"
        quest_objective = "Ascend to the Network Highlands"
        show_message("NEW OBJECTIVE: NETWORK HIGHLANDS")
        story_state.STATE.set_flag("act_six_started", True)
        if drukma_awake:
            say_drukma("The tampering reaches every tower. We must go higher.")

    # Act VI → Act VII: player finished the highlands
    if (quest_title == "THE SHATTERED NETWORK"
            and story_state.STATE.get_flag("highlands_done")
            and not story_state.STATE.get_flag("act_seven_started")):
        quest_title = "THE DEEP ARCHIVE"
        quest_objective = "Descend to the Deep Archive"
        show_message("NEW OBJECTIVE: DEEP ARCHIVE")
        story_state.STATE.set_flag("act_seven_started", True)
        if drukma_awake:
            say_drukma("He is below. I can feel it.")

    # Act VII → Act VIII: player finished the deep archive
    if (quest_title == "THE DEEP ARCHIVE"
            and story_state.STATE.get_flag("deep_archive_done")
            and not story_state.STATE.get_flag("act_eight_started")):
        quest_title = "THE HEART OF THE CORE"
        quest_objective = "Face the Core's choice"
        show_message("FINAL OBJECTIVE: THE HEART")
        story_state.STATE.set_flag("act_eight_started", True)
        if drukma_awake:
            say_drukma("We are here. This is the last room.")

# =========================================================
# SIDE QUEST — THE BROKEN WORKSHOP
# =========================================================
def start_tashi_quest():
    story_state.STATE.set_flag("tashi_quest_started", True)
    show_message("SIDE QUEST: THE BROKEN WORKSHOP")
    drukma_commentary.trigger("workshop_started")
    story_state.STATE.add_journal_entry(
        "The Broken Workshop",
        "Tashi the mechanic needs help. A resonator coil is missing from "
        "his workshop mechanism.\n\n"
        "He last saw it out east, past the old storage stone.",
        source="Tashi"
    )

def complete_tashi_quest():
    global player_xp
    story_state.STATE.set_flag("tashi_quest_complete", True)
    player_xp += 50
    show_message("QUEST COMPLETE: THE BROKEN WORKSHOP  +50 XP")
    sound_system.play("reward")
    drukma_commentary.trigger("workshop_complete")
    story_state.STATE.add_journal_entry(
        "The Workshop Repaired",
        "I returned the resonator coil to Tashi. He installed it and the "
        "mechanism started turning again.\n\n"
        "He thanked me — and I suspect he will be asking for help again soon.",
        source="Tashi"
    )

# =========================================================
# TALKING
# =========================================================
def talk_to_npc(name):
    global quest_active

    if name == "Village Elder":
        if quest_objective == "Talk to the Village Elder" and not quest_completed:
            start_dialogue("Village Elder", [
                "Stop there, traveler. You came from the eastern path?",
                "Few travel beyond those mountains now. Fewer still arrive with a device like that.",
                "I see the light in your hands. That was not given to you by any merchant.",
                "You do not remember, do you? The mountains took your past — I have seen it happen before.",
                "Then perhaps they brought you here for a reason.",
                "Listen. Drukora was not always silent.",
                "We once had a system that connected everything — the Core.",
                "It received information. It processed instructions. It kept our records. It delivered results.",
                "When the Core failed, every region suffered.",
                "Our signal towers stopped working. Our archives vanished. Machines we no longer understood began to fail.",
                "The old shrine east of here is our only remaining lead.",
                "Investigate it. See if anything still lives inside.",
                "And be careful. The old systems are not to be trusted blindly.",
            ], on_complete=start_awakening_quest)
        elif drukma_awake and quest_objective == "Reach CPU Dzong" and not quest_completed:
            start_dialogue("Village Elder", [
                "The shrine responded to you? Then the old systems still remember something.",
                "And you say a voice spoke from inside it — a consciousness called Drukma.",
                "I have heard that name before, but only in old stories.",
                "If Drukma truly understands the Core, then you must follow its guidance.",
                "The next step is north. The CPU Dzong — the heart of the kingdom's processing.",
                "Karma, the Guardian of Processing, once watched over it.",
                "Walk up the road. Enter through its door. Ask what happened.",
                "And traveler — do not go alone. Let Drukma accompany you.",
            ])
        elif quest_active and not quest_completed:
            lines = tashi_hints.get(quest_objective, ["Keep going, traveler. The Core needs you."])
            start_dialogue("Village Elder", lines)
        else:
            start_dialogue("Village Elder", [
                "You have done well, young guardian.",
                "The Core is safe for now. Rest.",
                "But I suspect this is only the beginning of your journey.",
            ])

    elif name == "Pema":
        start_dialogue("Pema", [
            "I am Pema, keeper of the village records.",
            "The machines around us hold many secrets.",
            "Input, Processing, Storage, Output, Memory —",
            "Learn them all, and you will understand the Core.",
        ])

    elif name == "Tashi":
        if story_state.STATE.get_flag("tashi_quest_complete"):
            start_dialogue("Tashi", [
                "You're back! The workshop is still running.",
                "Thank you again, traveler.",
            ])
        elif story_state.STATE.get_flag("tashi_component_diagnosed") and \
                not story_state.STATE.get_flag("tashi_component_taken"):
            start_dialogue("Tashi", [
                "You found the broken part? Which one?",
                "You: The Copper Gear Train. Its tooth is cracked.",
                "Tashi: Of course — the motion never reaches the lamp!",
                "Tashi: I'll need a Resonator Coil to rebuild it.",
                "Tashi: An old one was left at the eastern workshop,",
                "Tashi: past the river, on the other side of the stone.",
                "Tashi: You'll know it when you see it — a warm glow.",
            ])
        elif story_state.STATE.get_flag("tashi_quest_started"):
            start_dialogue("Tashi", [
                "Still looking? Walk up to the mechanism and press E.",
                "There are five parts. Only one has failed.",
            ])
        else:
            start_dialogue("Tashi", [
                "Oh! A traveler! I didn't see you coming.",
                "I'm Tashi. I fix things — or try to, anyway.",
                "Do you have a moment? My workshop mechanism broke down.",
                "It won't turn on. One of its five parts has failed —",
                "but I cannot tell which one.",
                "Would you inspect it with me? Walk up to the mechanism",
                "and press E when you're ready.",
            ], on_complete=start_tashi_quest)

    elif name == "Dorji":
        drukma_commentary.trigger("met_dorji")
        if quest_active and quest_objective == "Visit Input Village":
            start_dialogue("Dorji", [
                "So. The Core sent for help at last.",
                "I am Dorji, Guardian of Input.",
                "Before a system can think, it must receive.",
                "Keyboards, mice, microphones, scanners —",
                "all of them send information INTO the machine.",
                "Without Input, the Core is blind and deaf.",
                "Now prove that you understand. Answer my question.",
            ], on_complete=open_input_challenge)
        else:
            start_dialogue("Dorji", [
                "Input is how the machine listens.",
                "Remember: without input, the system hears nothing.",
            ])

    elif name == "Karma":
        if quest_active and quest_objective == "Return to Karma":
            start_dialogue("Karma", [
                "You have learned how information enters a system.",
                "Now you must understand what happens INSIDE.",
                "I am Karma, Guardian of Processing.",
                "Every instruction Drukora ever needed",
                "was executed within my Dzong.",
                "The CPU is the brain of any computer.",
                "It does not store. It does not display. It acts.",
                "Now prove that you understand Processing.",
            ], on_complete=open_processing_challenge)
        else:
            start_dialogue("Karma", [
                "Processing transforms information into results.",
                "The CPU is the heart of that transformation.",
            ])

    elif name == "Choden":
        drukma_commentary.trigger("met_choden")
        if quest_active and quest_objective == "Visit Storage Vault":
            start_dialogue("Choden", [
                "The Core does not just think — it remembers.",
                "I am Choden, Guardian of Storage.",
                "Hard drives. SSDs. USB drives.",
                "They hold data when everything else forgets.",
                "Even when the power dies, Storage survives.",
                "Now show me that you understand.",
            ], on_complete=open_storage_challenge)
        else:
            start_dialogue("Choden", [
                "Storage is memory that outlives the moment.",
                "Files, records, histories — all preserved.",
            ])

    elif name == "Sonam":
        drukma_commentary.trigger("met_sonam")
        if quest_active and quest_objective == "Visit Output Tower":
            start_dialogue("Sonam", [
                "Information means nothing unless it can be shown.",
                "I am Sonam, Guardian of Output.",
                "Monitors light up. Speakers sing. Printers write.",
                "I am how the Core speaks to the world.",
                "Now prove yourself.",
            ], on_complete=open_output_challenge)
        else:
            start_dialogue("Sonam", [
                "Output turns the machine's work into something we can see.",
            ])

    elif name == "Dawa":
        drukma_commentary.trigger("met_dawa")
        if quest_active and quest_objective == "Visit Memory Monastery":
            start_dialogue("Dawa", [
                "Storage keeps the past.",
                "But Memory holds the PRESENT.",
                "I am Dawa, Guardian of Memory.",
                "RAM is where the Core thinks while it works —",
                "fast, but fleeting.",
                "ROM holds the instructions it needs to wake up.",
                "Without Memory, the Core would forget what it was doing.",
                "Show me that you understand.",
            ], on_complete=open_memory_challenge)
        else:
            start_dialogue("Dawa", [
                "Memory helps the computer remember what it is working on.",
                "It is the present, not the past.",
            ])

# =========================================================
# KARMA — CPU Dzong interior interaction
# =========================================================
def talk_to_karma():
    if quest_objective == "Talk to Karma":
        drukma_commentary.trigger("met_karma")
        start_dialogue("Karma", [
            "You made it inside. Good.",
            "I am Karma, Guardian of Processing.",
            "The Computer Core is unstable.",
            "You must learn about the five great parts",
            "of a computer system: Input, Processing, Storage,",
            "Output, and Memory.",
            "Each is guarded by one of my kin.",
            "Visit each Guardian. Learn. Return to me.",
        ], on_complete=start_five_guardians_quest)
    elif quest_objective == "Return to Karma":
        start_dialogue("Karma", [
            "You have learned about Input. Excellent.",
            "Now prove that you understand Processing.",
        ], on_complete=open_processing_challenge)
    elif quest_objective == "Report to Karma":
        start_dialogue("Karma", [
            "You have met all five guardians.",
            "You now understand the heart of every computer.",
            "The Core is stable once more.",
            "Well done, young guardian.",
        ], on_complete=complete_mission)
    elif quest_title == "THE BROKEN CHANNEL":
        start_dialogue("Karma", [
            "The Core is stable — but only its surface.",
            "Its input and processing channels were modified before the collapse.",
            "The old research outpost to the east may still hold records.",
            "Go there. Find what was changed. And by whom.",
        ])
    elif quest_title == "THE MODIFIED SEQUENCE":
        start_dialogue("Karma", [
            "A signal still beats inside the ruins.",
            "Follow it to the Processing Citadel — my old chamber.",
            "Whatever altered the channels may still be running there.",
        ])
    elif quest_title == "THE FORGOTTEN ARCHIVE":
        start_dialogue("Karma", [
            "You saw the duplicate in the Citadel logs.",
            "Drukma carries memories that are not only its own.",
            "The Memory Monastery will show you what else the Core kept.",
        ])
    elif quest_completed:
        start_dialogue("Karma", [
            "The Core is stable for now.",
            "But something deeper still stirs beneath us...",
        ])
    else:
        start_dialogue("Karma", ["Continue your journey, young guardian."])

# =========================================================
# INTERACTION
# =========================================================
def handle_interaction():
    global current_scene, quest_objective

    if dialogue_open:
        advance_dialogue()
        return

    if current_scene == "village":
        if (story_state.STATE.get_flag("tashi_quest_started")
                and not story_state.STATE.get_flag("tashi_component_taken")
                and player.player.colliderect(world.damaged_component_rect.inflate(30, 30))):
            story_state.STATE.set_flag("tashi_component_taken", True)
            sound_system.play("correct")
            show_message("ACQUIRED: RESONATOR COIL")
            drukma_commentary.trigger("coil_picked_up")
            story_state.STATE.add_journal_entry(
                "The Resonator Coil",
                "I found the coil Tashi was looking for — a small brass "
                "device with a warm glow.\n\n"
                "I should bring it back to him.",
                source="Drukora"
            )
            return

        if not world.shrine_activated and \
                player.player.colliderect(world.shrine_rect.inflate(50, 50)):
            start_dialogue("Ancient Shrine", [
                "The shrine's crystal begins to pulse...",
                "A stream of blue light rises from the stone.",
                "UNKNOWN VOICE: Connection... established.",
                "UNKNOWN VOICE: I have waited a long time for someone to find me.",
                "You: Who are you?",
                "UNKNOWN VOICE: I... do not know.",
                "UNKNOWN VOICE: My name is Drukma. That is all I remember.",
                "UNKNOWN VOICE: But I understand the Core. I can help you.",
            ], on_complete=awaken_drukma)
            return

        nearby = get_nearby_npc()
        if nearby:
            talk_to_npc(nearby["name"])
            return

        if (quest_active or quest_completed) and \
                world.is_unlocked("CPU Dzong") and \
                player.player.colliderect(world.cpu_dzong_entrance.inflate(20, 20)):
            if not is_fading():
                start_fade_out("cpu_dzong")
            return

        if (story_state.STATE.get_flag("drukma_awake")
                and player.player.colliderect(
                    world.eastern_ruins_entrance.inflate(20, 20))):
            if not is_fading():
                start_fade_out("eastern_ruins")
            return

        for name, rect in world.locations.items():
            if world.is_unlocked(name) and player.player.colliderect(rect.inflate(50, 50)):
                info_map = {
                    "Memory Monastery": ["Memory Monastery.", "RAM temporarily holds data in use."],
                    "Input Village":    ["Input Village.", "Keyboards, mice and microphones send data in."],
                    "Output Tower":     ["Output Tower.", "Monitors and speakers show results."],
                    "Storage Vault":    ["Storage Vault.", "Hard drives keep data when power is off."],
                }
                if name in info_map:
                    start_dialogue(name, info_map[name])
                return

    elif current_scene == "cpu_dzong":
        if player.player.colliderect(world.guardian["rect"].inflate(45, 45)):
            talk_to_karma()
        elif player.player.colliderect(world.cpu_dzong_exit.inflate(20, 20)):
            if not is_fading():
                start_fade_out("village")

# =========================================================
# FADE TRANSITION SYSTEM
# =========================================================
fade_alpha = 0
fade_direction = 0
FADE_SPEED = 14
pending_scene_change = None

def start_fade_out(new_scene=None):
    global fade_direction, pending_scene_change
    fade_direction = 1
    pending_scene_change = new_scene

def start_fade_in():
    global fade_alpha, fade_direction
    fade_alpha = 255
    fade_direction = -1

def is_fading():
    return fade_direction != 0

def update_fade():
    global fade_alpha, fade_direction, pending_scene_change
    global current_scene, quest_objective

    if fade_direction == 0:
        return

    fade_alpha += fade_direction * FADE_SPEED

    if fade_direction > 0 and fade_alpha >= 255:
        fade_alpha = 255
        if pending_scene_change == "cpu_dzong":
            current_scene = "cpu_dzong"
            if quest_objective == "Reach CPU Dzong":
                quest_objective = "Talk to Karma"
            show_message("ENTERED CPU DZONG")
            player.player.x = 487
            player.player.y = 500
            drukma_commentary.trigger("entered_cpu_dzong")
        elif pending_scene_change == "village":
            current_scene = "village"
            player.player.x = 487
            player.player.y = 480
        elif pending_scene_change == "eastern_ruins":
            current_scene = "eastern_ruins"
            player.player.x = 120
            player.player.y = 500
            eastern_ruins.on_enter()
            show_message("EASTERN RUINS")
        elif pending_scene_change == "processing_citadel":
            current_scene = "processing_citadel"
            player.player.x = 480
            player.player.y = 520
            processing_citadel.on_enter()
            show_message("THE PROCESSING CITADEL")
        elif pending_scene_change == "memory_monastery":
            current_scene = "memory_monastery"
            player.player.x = 200
            player.player.y = 520
            memory_monastery.on_enter()
            show_message("THE MEMORY MONASTERY")
        elif pending_scene_change == "storage_vault":
            current_scene = "storage_vault"
            player.player.x = 200
            player.player.y = 520
            storage_vault.on_enter()
            show_message("THE STORAGE VAULT")
        elif pending_scene_change == "network_highlands":
            current_scene = "network_highlands"
            player.player.x = 200
            player.player.y = 520
            network_highlands.on_enter()
            show_message("THE NETWORK HIGHLANDS")
        elif pending_scene_change == "deep_archive":
            current_scene = "deep_archive"
            player.player.x = 200
            player.player.y = 520
            deep_archive.on_enter()
            show_message("THE DEEP ARCHIVE")
        elif pending_scene_change == "core_heart":
            current_scene = "core_heart"
            player.player.x = 480
            player.player.y = 520
            core_heart.on_enter()
            show_message("THE HEART OF THE CORE")
        elif pending_scene_change == "ending":
            start_ending()
        pending_scene_change = None
        fade_direction = -1

    elif fade_direction < 0 and fade_alpha <= 0:
        fade_alpha = 0
        fade_direction = 0

def draw_fade():
    if fade_alpha <= 0:
        return
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(int(fade_alpha))
    screen.blit(overlay, (0, 0))

# =========================================================
# VISUAL HELPERS
# =========================================================
def draw_vertical_gradient(surface, top_color, bottom_color):
    for y in range(HEIGHT):
        t = y / max(1, HEIGHT - 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (WIDTH, y))

def draw_sun(surface, cx, cy, radius, base_color=(255, 220, 150)):
    for r, a in [(radius * 3.0, 18), (radius * 2.2, 32), (radius * 1.6, 55),
                 (radius * 1.15, 90), (radius, 200), (radius * 0.7, 255)]:
        surf = pygame.Surface((int(r * 2), int(r * 2)), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*base_color, a), (int(r), int(r)), int(r))
        surface.blit(surf, (cx - r, cy - r), special_flags=pygame.BLEND_RGBA_ADD)

def draw_sun_rays(surface, cx, cy, count, length, color, alpha=60, offset_angle=0):
    ray_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for i in range(count):
        angle = math.radians(offset_angle + i * (360 / count))
        x1 = cx + math.cos(angle) * (length * 0.25)
        y1 = cy + math.sin(angle) * (length * 0.25)
        x2 = cx + math.cos(angle) * length
        y2 = cy + math.sin(angle) * length
        pygame.draw.line(ray_surf, (*color, alpha), (x1, y1), (x2, y2), 3)
    surface.blit(ray_surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

def draw_mountain_layer(surface, points, color, snow_caps=None):
    pygame.draw.polygon(surface, color, points)
    if snow_caps:
        for peak, left, right in snow_caps:
            pts = [peak, left, (peak[0] - 15, peak[1] + 25),
                   (peak[0], peak[1] + 10),
                   (peak[0] + 15, peak[1] + 25), right]
            pygame.draw.polygon(surface, (235, 240, 248), pts)

def draw_dzong(surface, x, y, scale=1.0):
    s = scale
    pygame.draw.rect(surface, (35, 28, 32), (x, y, int(120 * s), int(50 * s)))
    pygame.draw.rect(surface, (55, 40, 42), (x, y + int(5 * s), int(120 * s), int(8 * s)))
    pygame.draw.rect(surface, (30, 24, 28), (x + int(40 * s), y - int(35 * s), int(40 * s), int(50 * s)))
    pygame.draw.polygon(surface, (18, 14, 18), [
        (x + int(28 * s), y - int(30 * s)),
        (x + int(60 * s), y - int(70 * s)),
        (x + int(92 * s), y - int(30 * s))])
    pygame.draw.polygon(surface, (12, 10, 14), [
        (x + int(40 * s), y - int(65 * s)),
        (x + int(60 * s), y - int(95 * s)),
        (x + int(80 * s), y - int(65 * s))])
    pygame.draw.circle(surface, (200, 160, 60), (x + int(60 * s), y - int(98 * s)), max(1, int(3 * s)))
    for wx in [20, 55, 90]:
        pygame.draw.rect(surface, (10, 8, 10),
                         (x + int(wx * s), y + int(15 * s), int(6 * s), int(10 * s)))

def draw_prayer_flags_rope(surface, x1, y1, x2, y2, count=14, droop=35):
    colors = [(85, 130, 200), (250, 250, 245), (210, 60, 55),
              (70, 160, 85), (245, 200, 70)]
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2 + droop
    prev = (x1, y1)
    for i in range(1, 41):
        t = i / 40
        cx_ = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * mid_x + t ** 2 * x2
        cy_ = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * mid_y + t ** 2 * y2
        pygame.draw.line(surface, (90, 65, 40), prev, (cx_, cy_), 2)
        prev = (cx_, cy_)
    for i in range(count):
        t = (i + 0.5) / count
        fx = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * mid_x + t ** 2 * x2
        fy = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * mid_y + t ** 2 * y2
        color = colors[i % 5]
        sway = math.sin(pygame.time.get_ticks() / 500 + i) * 2
        top_y = fy + 2
        pts = [(fx - 14, top_y), (fx + 14, top_y), (fx + sway, top_y + 26)]
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.polygon(surface, (60, 45, 30), pts, 1)

def draw_endless_knot(surface, cx, cy, size, color, thickness=3):
    s = size
    for offset in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
        ox = cx + offset[0] * s * 0.35
        oy = cy + offset[1] * s * 0.35
        pygame.draw.circle(surface, color, (int(ox), int(oy)), int(s * 0.4), thickness)
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
        pygame.draw.circle(surface, color, (int(px), int(py)), int(size * 0.28), thickness)
    pygame.draw.circle(surface, color, (cx, cy), int(size * 0.18), thickness)

def draw_vignette(surface):
    v = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    w, h = surface.get_size()
    for i in range(0, 80, 2):
        alpha = int((i / 80) ** 2 * 220)
        pygame.draw.rect(v, (0, 0, 0, alpha // 40),
                         (i, i, w - i * 2, h - i * 2), 4)
    surface.blit(v, (0, 0))

# =========================================================
# SNOW
# =========================================================
snow_particles = []
for _ in range(90):
    snow_particles.append({
        "x": random.uniform(0, WIDTH),
        "y": random.uniform(0, HEIGHT),
        "vy": random.uniform(0.3, 1.2),
        "vx": random.uniform(-0.3, 0.3),
        "size": random.uniform(1, 2.5),
        "alpha": random.randint(80, 200),
    })

def update_and_draw_snow(surface):
    for p in snow_particles:
        p["y"] += p["vy"]
        p["x"] += p["vx"]
        if p["y"] > HEIGHT:
            p["y"] = -5
            p["x"] = random.uniform(0, WIDTH)
        if p["x"] < -5: p["x"] = WIDTH
        if p["x"] > WIDTH + 5: p["x"] = 0
        dot = pygame.Surface((int(p["size"] * 2), int(p["size"] * 2)), pygame.SRCALPHA)
        pygame.draw.circle(dot, (255, 255, 255, p["alpha"]),
                           (int(p["size"]), int(p["size"])), int(p["size"]))
        surface.blit(dot, (int(p["x"]), int(p["y"])))

# =========================================================
# TITLE SCREEN
# =========================================================
def draw_title_screen():
    if title_landscape_img is not None:
        screen.blit(title_landscape_img, (0, 0))
    else:
        draw_vertical_gradient(screen, (28, 22, 55), (180, 110, 70))
        sun_x, sun_y = WIDTH // 2, 400
        draw_sun(screen, sun_x, sun_y, 45, base_color=(255, 200, 130))
        draw_sun_rays(screen, sun_x, sun_y, 16, 700, (255, 190, 120),
                      alpha=25, offset_angle=pygame.time.get_ticks() * 0.005)
        back = [(0, 440), (100, 340), (200, 390), (300, 280), (400, 360),
                (520, 250), (640, 350), (760, 290), (880, 370), (1000, 300),
                (1000, 650), (0, 650)]
        draw_mountain_layer(screen, back, (65, 75, 105), snow_caps=[
            ((300, 280), (270, 320), (335, 325)),
            ((520, 250), (490, 300), (555, 300)),
            ((760, 290), (735, 330), (790, 335))])
        mid = [(0, 500), (140, 400), (280, 470), (420, 380), (560, 460),
               (700, 400), (840, 470), (960, 420), (1000, 460),
               (1000, 650), (0, 650)]
        draw_mountain_layer(screen, mid, (42, 48, 72))
        front = [(0, 560), (180, 470), (340, 530), (500, 460), (660, 530),
                 (820, 480), (1000, 540), (1000, 650), (0, 650)]
        draw_mountain_layer(screen, front, (22, 26, 42))
        draw_dzong(screen, 800, 480, scale=0.9)

    plate = pygame.Rect(WIDTH // 2 - 340, 395, 680, 190)
    shadow = pygame.Surface((plate.width + 20, plate.height + 20), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 120), (10, 10, plate.width, plate.height), border_radius=8)
    screen.blit(shadow, (plate.x - 10, plate.y - 10))

    plate_surf = pygame.Surface((plate.width, plate.height), pygame.SRCALPHA)
    pygame.draw.rect(plate_surf, (75, 25, 30, 235), (0, 0, plate.width, plate.height), border_radius=8)
    screen.blit(plate_surf, plate.topleft)

    pygame.draw.rect(screen, (215, 175, 70), plate, 4, border_radius=8)
    pygame.draw.rect(screen, (180, 140, 60), plate.inflate(-16, -16), 1, border_radius=6)

    for cx_, cy_ in [(plate.left + 14, plate.top + 14),
                     (plate.right - 14, plate.top + 14),
                     (plate.left + 14, plate.bottom - 14),
                     (plate.right - 14, plate.bottom - 14)]:
        pygame.draw.rect(screen, (215, 175, 70), (cx_ - 6, cy_ - 6, 12, 12), 2)
        pygame.draw.circle(screen, (215, 175, 70), (cx_, cy_), 3)
        pygame.draw.circle(screen, (75, 25, 30), (cx_, cy_), 1)

    knot_surf = pygame.Surface((plate.width, plate.height), pygame.SRCALPHA)
    draw_endless_knot(knot_surf, plate.width // 2, plate.height // 2,
                      80, (215, 175, 70, 45), thickness=2)
    screen.blit(knot_surf, plate.topleft)

    big_font = pygame.font.SysFont("georgia", 76, bold=True)
    glow_text = big_font.render("THE CORE", True, (255, 230, 150))
    for off in [(4, 0), (-4, 0), (0, 4), (0, -4), (3, 3), (-3, -3)]:
        glow_text.set_alpha(40)
        screen.blit(glow_text, (WIDTH // 2 - glow_text.get_width() // 2 + off[0], 405 + off[1]))
    shadow_text = big_font.render("THE CORE", True, (30, 10, 15))
    screen.blit(shadow_text, (WIDTH // 2 - shadow_text.get_width() // 2 + 3, 408))
    title_surf = big_font.render("THE CORE", True, (245, 220, 130))
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 405))

    div_y = 490
    pygame.draw.line(screen, (215, 175, 70),
                     (WIDTH // 2 - 220, div_y), (WIDTH // 2 - 40, div_y), 2)
    pygame.draw.line(screen, (215, 175, 70),
                     (WIDTH // 2 + 40, div_y), (WIDTH // 2 + 220, div_y), 2)
    draw_lotus(screen, WIDTH // 2, div_y, 22, (215, 175, 70))

    sub_font = pygame.font.SysFont("georgia", 36, bold=True)
    sub_surf = sub_font.render("D R U K O R A", True, (215, 90, 75))
    screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, 505))

    tag_font = pygame.font.SysFont("georgia", 18, italic=True)
    tagline = tag_font.render("A kingdom. A system. A mystery.", True, (220, 200, 180))
    screen.blit(tagline, (WIDTH // 2 - tagline.get_width() // 2, 555))

    if title_frame_img is not None:
        screen.blit(title_frame_img, (0, 0))
    else:
        draw_prayer_flags_rope(screen, 0, 55, WIDTH, 75, count=16, droop=40)

    update_and_draw_snow(screen)
    draw_vignette(screen)

    if (pygame.time.get_ticks() // 500) % 2 == 0:
        p_font = pygame.font.SysFont("georgia", 22, bold=True)
        if save_system.has_save():
            prompt = p_font.render("ENTER: New Game     ·     F9: Continue",
                                   True, (255, 245, 215))
        else:
            prompt = p_font.render("Press  ENTER  to begin", True, (255, 245, 215))
        glow = pygame.Surface((prompt.get_width() + 60, 50), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (215, 175, 70, 60),
                            (0, 0, glow.get_width(), glow.get_height()))
        screen.blit(glow, (WIDTH // 2 - glow.get_width() // 2, 610))
        screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, 618))

    footer = small_font.render("An educational RPG  ·  Computer Systems", True, (140, 130, 150))
    screen.blit(footer, (WIDTH // 2 - footer.get_width() // 2, HEIGHT - 26))

# =========================================================
# INTRO CUTSCENE
# =========================================================
def draw_intro_icon(kind, cx, cy, alpha):
    surf = pygame.Surface((300, 220), pygame.SRCALPHA)
    icx, icy = 150, 110
    if kind == "mountain":
        pygame.draw.polygon(surf, (90, 110, 140, alpha), [(20, 200), (150, 20), (280, 200)])
        pygame.draw.polygon(surf, (235, 240, 250, alpha), [(150, 20), (120, 70), (150, 55), (180, 70)])
        pygame.draw.circle(surf, (255, 210, 130, alpha), (220, 60), 18)
    elif kind == "crystal":
        for r, a in [(80, 20), (55, 40), (35, 80), (20, 140)]:
            pygame.draw.circle(surf, (100, 220, 240, int(a * alpha / 255)), (icx, icy), r)
        pygame.draw.polygon(surf, (220, 250, 255, alpha),
                            [(icx, icy - 40), (icx + 20, icy - 5), (icx, icy + 35), (icx - 20, icy - 5)])
    elif kind == "signal":
        for i, r in enumerate([25, 55, 85, 115]):
            a = int((alpha * 0.6) * (1 - i / 4))
            pygame.draw.circle(surf, (150, 210, 240, a), (icx, icy), r, 3)
        pygame.draw.circle(surf, (220, 240, 255, alpha), (icx, icy), 8)
    elif kind == "title":
        draw_endless_knot(surf, icx, icy, 70, (215, 175, 70, alpha), thickness=3)
        draw_lotus(surf, icx, icy, 40, (215, 175, 70, alpha))
    screen.blit(surf, (cx - 150, cy - 110))

def draw_intro():
    draw_vertical_gradient(screen, (12, 14, 26), (30, 25, 40))
    duration, main_text, sub_text = INTRO_PAGES[intro_page]
    icon_kind = INTRO_ICONS[intro_page % len(INTRO_ICONS)]

    t = intro_timer / 60.0
    if t < 0.6:
        alpha = int((t / 0.6) * 255)
    elif t > duration - 0.6:
        alpha = int(((duration - t) / 0.6) * 255)
    else:
        alpha = 255
    alpha = max(0, min(255, alpha))

    if title_frame_img is not None:
        frame_copy = title_frame_img.copy()
        frame_copy.set_alpha(alpha)
        screen.blit(frame_copy, (0, 0))
    else:
        flag_surf = pygame.Surface((WIDTH, 130), pygame.SRCALPHA)
        draw_prayer_flags_rope(flag_surf, 0, 40, WIDTH, 60, count=16, droop=35)
        flag_surf.set_alpha(alpha // 3)
        screen.blit(flag_surf, (0, 0))

    for p in snow_particles:
        dot = pygame.Surface((int(p["size"] * 2), int(p["size"] * 2)), pygame.SRCALPHA)
        pygame.draw.circle(dot, (255, 255, 255, int(p["alpha"] * 0.4)),
                           (int(p["size"]), int(p["size"])), int(p["size"]))
        screen.blit(dot, (int(p["x"]), int(p["y"])))
        p["y"] += p["vy"] * 0.5
        if p["y"] > HEIGHT:
            p["y"] = -5
            p["x"] = random.uniform(0, WIDTH)

    draw_intro_icon(icon_kind, WIDTH // 2, HEIGHT // 2 - 180, alpha)

    big_font = pygame.font.SysFont("georgia", 48, bold=True)
    main_surf = big_font.render(main_text, True, (245, 232, 210))
    main_surf.set_alpha(alpha)
    shadow = big_font.render(main_text, True, (0, 0, 0))
    shadow.set_alpha(alpha // 2)
    screen.blit(shadow, (WIDTH // 2 - main_surf.get_width() // 2 + 3, HEIGHT // 2 - 43))
    screen.blit(main_surf, (WIDTH // 2 - main_surf.get_width() // 2, HEIGHT // 2 - 46))

    if sub_text:
        sub_font = pygame.font.SysFont("georgia", 22, italic=True)
        sub_surf = sub_font.render(sub_text, True, (215, 180, 130))
        sub_surf.set_alpha(alpha)
        screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, HEIGHT // 2 + 25))

    div_y = HEIGHT // 2 + 80
    line_surf = pygame.Surface((WIDTH, 30), pygame.SRCALPHA)
    pygame.draw.line(line_surf, (215, 175, 70, alpha),
                     (WIDTH // 2 - 180, 15), (WIDTH // 2 - 30, 15), 2)
    pygame.draw.line(line_surf, (215, 175, 70, alpha),
                     (WIDTH // 2 + 30, 15), (WIDTH // 2 + 180, 15), 2)
    draw_lotus(line_surf, WIDTH // 2, 15, 18, (215, 175, 70, alpha))
    screen.blit(line_surf, (0, div_y))

    dot_y = HEIGHT - 60
    total = len(INTRO_PAGES)
    total_w = (12 * total) + (18 * (total - 1))
    start_x = WIDTH // 2 - total_w // 2
    for i in range(total):
        cx_ = start_x + i * 30 + 6
        if i == intro_page:
            pygame.draw.circle(screen, (215, 175, 70), (cx_, dot_y), 6)
            pygame.draw.circle(screen, (255, 220, 120), (cx_, dot_y), 3)
        else:
            pygame.draw.circle(screen, (100, 90, 80), (cx_, dot_y), 4)

    draw_vignette(screen)

    skip = small_font.render("Press ENTER to skip", True, (120, 110, 100))
    skip.set_alpha(min(alpha, 120))
    screen.blit(skip, (WIDTH - skip.get_width() - 24, HEIGHT - 26))

def update_intro():
    global intro_timer, intro_page, game_state
    intro_timer += 1
    duration = INTRO_PAGES[intro_page][0]
    if intro_timer >= duration * 60:
        intro_timer = 0
        intro_page += 1
        if intro_page >= len(INTRO_PAGES):
            game_state = "playing"
            start_fade_in()

# =========================================================
# ENDING CUTSCENE
# =========================================================
def start_ending():
    global ending_page, ending_timer, game_state
    ending_page = 0
    ending_timer = 0
    game_state = "ending"
    start_fade_in()

def update_ending():
    global ending_timer, ending_page
    ending_timer += 1
    duration = ENDING_PAGES[ending_page][0]
    if ending_timer >= duration * 60:
        if ending_page < len(ENDING_PAGES) - 1:
            ending_timer = 0
            ending_page += 1

def draw_ending():
    draw_vertical_gradient(screen, (8, 10, 20), (25, 20, 35))
    duration, main_text, sub_text = ENDING_PAGES[ending_page]

    t = ending_timer / 60.0
    if t < 0.8:
        alpha = int((t / 0.8) * 255)
    elif t > duration - 0.8:
        alpha = int(((duration - t) / 0.8) * 255)
    else:
        alpha = 255
    alpha = max(0, min(255, alpha))

    if title_frame_img is not None:
        frame_copy = title_frame_img.copy()
        frame_copy.set_alpha(alpha)
        screen.blit(frame_copy, (0, 0))
    else:
        flag_surf = pygame.Surface((WIDTH, 130), pygame.SRCALPHA)
        draw_prayer_flags_rope(flag_surf, 0, 40, WIDTH, 60, count=16, droop=35)
        flag_surf.set_alpha(alpha // 3)
        screen.blit(flag_surf, (0, 0))

    for p in snow_particles:
        dot = pygame.Surface((int(p["size"] * 2), int(p["size"] * 2)), pygame.SRCALPHA)
        pygame.draw.circle(dot, (255, 255, 255, int(p["alpha"] * 0.4)),
                           (int(p["size"]), int(p["size"])), int(p["size"]))
        screen.blit(dot, (int(p["x"]), int(p["y"])))
        p["y"] += p["vy"] * 0.5
        if p["y"] > HEIGHT:
            p["y"] = -5
            p["x"] = random.uniform(0, WIDTH)

    if ending_page not in (5, 6):
        draw_intro_icon("crystal", WIDTH // 2, HEIGHT // 2 - 180, alpha)

    if ending_page == 5:
        draw_intro_icon("title", WIDTH // 2, HEIGHT // 2 - 180, alpha)

    big_font = pygame.font.SysFont("georgia", 44, bold=True)
    main_surf = big_font.render(main_text, True, (245, 232, 210))
    main_surf.set_alpha(alpha)
    shadow = big_font.render(main_text, True, (0, 0, 0))
    shadow.set_alpha(alpha // 2)
    screen.blit(shadow, (WIDTH // 2 - main_surf.get_width() // 2 + 3, HEIGHT // 2 - 43))
    screen.blit(main_surf, (WIDTH // 2 - main_surf.get_width() // 2, HEIGHT // 2 - 46))

    if sub_text:
        sub_font = pygame.font.SysFont("georgia", 22, italic=True)
        sub_surf = sub_font.render(sub_text, True, (215, 180, 130))
        sub_surf.set_alpha(alpha)
        screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, HEIGHT // 2 + 25))

    div_y = HEIGHT // 2 + 80
    line_surf = pygame.Surface((WIDTH, 30), pygame.SRCALPHA)
    pygame.draw.line(line_surf, (215, 175, 70, alpha),
                     (WIDTH // 2 - 180, 15), (WIDTH // 2 - 30, 15), 2)
    pygame.draw.line(line_surf, (215, 175, 70, alpha),
                     (WIDTH // 2 + 30, 15), (WIDTH // 2 + 180, 15), 2)
    draw_lotus(line_surf, WIDTH // 2, 15, 18, (215, 175, 70, alpha))
    screen.blit(line_surf, (0, div_y))

    total = len(ENDING_PAGES)
    total_w = (12 * total) + (18 * (total - 1))
    start_x = WIDTH // 2 - total_w // 2
    dot_y = HEIGHT - 60
    for i in range(total):
        cx_ = start_x + i * 30 + 6
        if i == ending_page:
            pygame.draw.circle(screen, (215, 175, 70), (cx_, dot_y), 6)
            pygame.draw.circle(screen, (255, 220, 120), (cx_, dot_y), 3)
        else:
            pygame.draw.circle(screen, (100, 90, 80), (cx_, dot_y), 4)

    draw_vignette(screen)

    if ending_page == len(ENDING_PAGES) - 1 and alpha > 200:
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            p_font = pygame.font.SysFont("georgia", 22, bold=True)
            prompt = p_font.render("Press  ENTER  to return to title", True, (255, 245, 215))
            glow = pygame.Surface((prompt.get_width() + 60, 50), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (215, 175, 70, 60),
                                (0, 0, glow.get_width(), glow.get_height()))
            screen.blit(glow, (WIDTH // 2 - glow.get_width() // 2, HEIGHT - 130))
            screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 122))

# =========================================================
# UI — GAME TITLE
# =========================================================
def draw_game_title():
    panel = pygame.Rect(18, 18, 260, 76)
    shadow = pygame.Surface((panel.width + 8, panel.height + 8), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 130),
                     (4, 4, panel.width, panel.height), border_radius=10)
    screen.blit(shadow, (panel.x - 4, panel.y - 4))

    panel_surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (72, 28, 34, 245),
                     (0, 0, panel.width, panel.height), border_radius=10)
    screen.blit(panel_surf, panel.topleft)

    pygame.draw.rect(screen, (215, 175, 70), panel, 2, border_radius=10)
    pygame.draw.rect(screen, (150, 115, 45),
                     panel.inflate(-10, -10), 1, border_radius=8)

    for cx_, cy_ in [(panel.left + 10, panel.top + 10),
                     (panel.right - 10, panel.top + 10),
                     (panel.left + 10, panel.bottom - 10),
                     (panel.right - 10, panel.bottom - 10)]:
        pygame.draw.circle(screen, (215, 175, 70), (cx_, cy_), 3)
        pygame.draw.circle(screen, (150, 115, 45), (cx_, cy_), 1)

    title_fnt = pygame.font.SysFont("georgia", 26, bold=True)
    title_surf = title_fnt.render("THE CORE", True, (245, 220, 130))
    screen.blit(title_surf, (panel.centerx - title_surf.get_width() // 2,
                              panel.y + 10))

    div_y = panel.y + 40
    pygame.draw.line(screen, (215, 175, 70),
                     (panel.x + 24, div_y), (panel.centerx - 12, div_y), 1)
    pygame.draw.line(screen, (215, 175, 70),
                     (panel.centerx + 12, div_y), (panel.right - 24, div_y), 1)
    pygame.draw.circle(screen, (215, 175, 70), (panel.centerx, div_y), 3)
    pygame.draw.circle(screen, (150, 115, 45), (panel.centerx, div_y), 1)

    sub_fnt = pygame.font.SysFont("georgia", 13, bold=True)
    sub_surf = sub_fnt.render("D R U K O R A", True, (215, 90, 75))
    screen.blit(sub_surf, (panel.centerx - sub_surf.get_width() // 2,
                            panel.y + 47))

# =========================================================
# UI — RPG HUD
# =========================================================
def draw_rpg_hud():
    panel = pygame.Rect(WIDTH - 260, 20, 240, 78)
    shadow = pygame.Surface((panel.width + 8, panel.height + 8), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 130),
                     (4, 4, panel.width, panel.height), border_radius=10)
    screen.blit(shadow, (panel.x - 4, panel.y - 4))

    panel_surf = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (72, 28, 34, 245),
                     (0, 0, panel.width, panel.height), border_radius=10)
    screen.blit(panel_surf, panel.topleft)

    pygame.draw.rect(screen, (215, 175, 70), panel, 2, border_radius=10)
    pygame.draw.rect(screen, (150, 115, 45),
                     panel.inflate(-10, -10), 1, border_radius=8)

    for cx_, cy_ in [(panel.left + 10, panel.top + 10),
                     (panel.right - 10, panel.top + 10),
                     (panel.left + 10, panel.bottom - 10),
                     (panel.right - 10, panel.bottom - 10)]:
        pygame.draw.circle(screen, (215, 175, 70), (cx_, cy_), 3)
        pygame.draw.circle(screen, (150, 115, 45), (cx_, cy_), 1)

    label_font = pygame.font.SysFont("georgia", 16, bold=True)
    value_font = pygame.font.SysFont("georgia", 20, bold=True)

    diamond_cx = panel.x + 26
    diamond_cy = panel.y + 24
    pygame.draw.polygon(screen, (215, 175, 70), [
        (diamond_cx, diamond_cy - 7),
        (diamond_cx + 6, diamond_cy),
        (diamond_cx, diamond_cy + 7),
        (diamond_cx - 6, diamond_cy)])
    pygame.draw.polygon(screen, (255, 235, 150), [
        (diamond_cx, diamond_cy - 4),
        (diamond_cx + 3, diamond_cy),
        (diamond_cx, diamond_cy + 4),
        (diamond_cx - 3, diamond_cy)])

    xp_label = label_font.render("XP", True, (230, 205, 155))
    screen.blit(xp_label, (panel.x + 42, panel.y + 16))

    xp_val = value_font.render(str(player_xp), True, (255, 245, 220))
    screen.blit(xp_val, (panel.right - xp_val.get_width() - 16, panel.y + 14))

    pygame.draw.line(screen, (150, 115, 45),
                     (panel.x + 16, panel.y + 40),
                     (panel.right - 16, panel.y + 40), 1)

    crystal_cx = panel.x + 26
    crystal_cy = panel.y + 58
    pygame.draw.polygon(screen, (100, 190, 220), [
        (crystal_cx, crystal_cy - 8),
        (crystal_cx + 5, crystal_cy - 2),
        (crystal_cx, crystal_cy + 8),
        (crystal_cx - 5, crystal_cy - 2)])
    pygame.draw.polygon(screen, (220, 250, 255), [
        (crystal_cx, crystal_cy - 5),
        (crystal_cx + 2, crystal_cy - 2),
        (crystal_cx, crystal_cy + 5),
        (crystal_cx - 2, crystal_cy - 2)])

    frag_label = label_font.render("FRAGMENTS", True, (230, 205, 155))
    screen.blit(frag_label, (panel.x + 42, panel.y + 50))

    frag_val = value_font.render(f"{guardian_fragments}/5", True, (255, 245, 220))
    screen.blit(frag_val, (panel.right - frag_val.get_width() - 16, panel.y + 48))

# =========================================================
# UI — DIALOGUE
# =========================================================
def draw_dialogue():
    if not dialogue_open:
        return
    global _last_voiced_line
    current_key = (dialogue_name, dialogue_index)
    if _last_voiced_line != current_key:
        _last_voiced_line = current_key
        current_text = dialogue_queue[dialogue_index]
        if not sound_system.play_line(dialogue_name, current_text):
            sound_system.play_voice(dialogue_name)

    box = pygame.Rect(100, HEIGHT - 165, WIDTH - 200, 125)
    pygame.draw.rect(screen, (35, 30, 30), box)
    pygame.draw.rect(screen, GOLD, box, 3)

    name_surf = location_font.render(dialogue_name, True, GOLD)
    screen.blit(name_surf, (box.x + 20, box.y + 12))

    current_line = dialogue_queue[dialogue_index]

    import voices
    display_line = voices.strip_prefix(current_line)

    lines = wrap_text(display_line, font, box.width - 40)
    for i, line in enumerate(lines[:3]):
        screen.blit(font.render(line, True, WHITE), (box.x + 20, box.y + 42 + i * 22))

    page = small_font.render(f"{dialogue_index + 1} / {len(dialogue_queue)}", True, (150, 150, 150))
    screen.blit(page, (box.right - page.get_width() - 20, box.y + 12))

    hint = small_font.render("Press E to continue", True, (190, 190, 190))
    screen.blit(hint, (box.right - hint.get_width() - 20, box.bottom - 22))

# =========================================================
# UI — REWARD BANNER
# =========================================================
def update_and_draw_reward_banner():
    global reward_timer, reward_particles
    if reward_timer <= 0 and not reward_particles:
        return
    for p in reward_particles:
        p["x"] += p["vx"]; p["y"] += p["vy"]; p["vy"] += 0.15; p["life"] -= 1
    reward_particles = [p for p in reward_particles if p["life"] > 0]
    for p in reward_particles:
        pygame.draw.circle(screen, (255, 220, 100), (int(p["x"]), int(p["y"])), p["size"])

    if reward_timer > 0:
        reward_timer -= 1
    if reward_timer > 0:
        if reward_timer > 100:
            alpha = int((120 - reward_timer) * 25)
        elif reward_timer < 30:
            alpha = int(reward_timer * 8)
        else:
            alpha = 255
        alpha = max(0, min(255, alpha))
        banner = pygame.Rect(200, 165, 600, 120)
        bs = pygame.Surface((banner.width, banner.height), pygame.SRCALPHA)
        bs.fill((25, 22, 35, alpha))
        screen.blit(bs, banner.topleft)
        br = pygame.Surface((banner.width, banner.height), pygame.SRCALPHA)
        pygame.draw.rect(br, (*GOLD, alpha), (0, 0, banner.width, banner.height), 3, border_radius=12)
        screen.blit(br, banner.topleft)
        ts = title_font.render(reward_title, True, GOLD); ts.set_alpha(alpha)
        screen.blit(ts, (banner.centerx - ts.get_width() // 2, banner.y + 25))
        ss = small_font.render(reward_subtitle, True, WHITE); ss.set_alpha(alpha)
        screen.blit(ss, (banner.centerx - ss.get_width() // 2, banner.y + 75))

# =========================================================
# UI — CHALLENGE
# =========================================================
def draw_challenge():
    if not challenge_open:
        return
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175)); screen.blit(overlay, (0, 0))
    box = pygame.Rect(100, 95, 800, 465)
    pygame.draw.rect(screen, (28, 27, 38), box, border_radius=14)
    pygame.draw.rect(screen, GOLD, box, 3, border_radius=14)
    header = pygame.Rect(box.x, box.y, box.width, 62)
    pygame.draw.rect(screen, (50, 42, 58), header, border_radius=14)
    screen.blit(title_font.render("GUARDIAN CHALLENGE", True, GOLD), (box.x + 25, box.y + 16))
    instr = small_font.render("Choose an answer with keys 1 - 4", True, (205, 200, 190))
    screen.blit(instr, (box.right - instr.get_width() - 25, box.y + 24))
    y = box.y + 85
    for line in wrap_text(challenge_question, font, box.width - 70):
        screen.blit(font.render(line, True, WHITE), (box.x + 35, y)); y += 30
    y += 12
    for i, opt in enumerate(challenge_options):
        card = pygame.Rect(box.x + 35, y, box.width - 70, 47)
        pygame.draw.rect(screen, (45, 42, 55), card, border_radius=8)
        pygame.draw.rect(screen, (105, 96, 115), card, 1, border_radius=8)
        screen.blit(title_font.render(str(i + 1), True, GOLD), (card.x + 14, card.y + 7))
        screen.blit(font.render(opt, True, WHITE), (card.x + 52, card.y + 12))
        y += 55
    if challenge_result:
        screen.blit(font.render(challenge_result, True, GOLD), (box.x + 35, box.bottom - 38))

# =========================================================
# UI — QUEST TRACKER + MESSAGE
# =========================================================
def draw_quest_tracker():
    if not quest_active and not quest_completed:
        return
    panel = pygame.Rect(20, 110, 300, 95)
    pygame.draw.rect(screen, (25, 22, 35), panel, border_radius=10)
    pygame.draw.rect(screen, (180, 150, 80), panel, 2, border_radius=10)
    screen.blit(quest_title_font.render(quest_title, True, (255, 220, 130)), (35, 122))
    if quest_completed:
        obj, col = "Mission Complete!", (120, 220, 140)
    else:
        obj, col = "> " + quest_objective, (235, 235, 235)
    screen.blit(quest_text_font.render(obj, True, col), (35, 158))

def draw_quest_message():
    global quest_message_timer
    if quest_message_timer <= 0:
        return
    surf = message_font.render(quest_message, True, (255, 220, 130))
    box = pygame.Rect(WIDTH // 2 - surf.get_width() // 2 - 25, 125,
                      surf.get_width() + 50, 45)
    pygame.draw.rect(screen, (25, 22, 35), box, border_radius=8)
    pygame.draw.rect(screen, (180, 150, 80), box, 2, border_radius=8)
    screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, 137))
    quest_message_timer -= 1

# =========================================================
# MAIN LOOP (async — required for Pygbag web build)
# =========================================================
async def main():
    global running, paused, pause_selected, pause_flash_text, pause_flash_timer
    global game_state, ending_pending, ending_page, ending_timer, _startup_banner_shown
    global current_scene, quest_objective, footstep_timer
    global intro_page, intro_timer, challenge_open, challenge_result
    global journal_open, journal_selected

    running = True

    while running:
        await asyncio.sleep(0)

        update_fade()

        # ---- ENDING CUTSCENE has its own event loop ----
        if game_state == "ending":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                        if ending_page >= len(ENDING_PAGES) - 1:
                            game_state = "title"
                            ending_pending = False
                            start_fade_in()
                        else:
                            ending_page += 1
                            ending_timer = 0
            update_ending()
            if game_state == "ending":
                draw_ending()
            draw_fade()
            pygame.display.flip()
            clock.tick(60)
            continue

        # ---- Regular event loop ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if game_state == "playing":
                    save_system.save_game(collect_save_state())
                running = False

            if event.type == pygame.KEYDOWN:
                # ---- TITLE SCREEN ----
                if game_state == "title":
                    if event.key == pygame.K_RETURN:
                        game_state = "intro"; intro_page = 0; intro_timer = 0
                    elif event.key == pygame.K_F9 and save_system.has_save():
                        state = save_system.load_game()
                        if state:
                            apply_save_state(state)
                            game_state = "playing"
                            start_fade_in()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
                    continue

                # ---- INTRO CUTSCENE ----
                if game_state == "intro":
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        game_state = "playing"
                        start_fade_in()
                    continue

                # ---- PAUSE MENU ----
                if game_state == "playing" and paused:
                    if event.key == pygame.K_ESCAPE:
                        paused = False
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        pause_selected = (pause_selected - 1) % len(PAUSE_MENU_ITEMS)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        pause_selected = (pause_selected + 1) % len(PAUSE_MENU_ITEMS)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
                        handle_pause_selection(pause_selected)
                    continue

                # ---- CHAT routes first ----
                if drukma_chat.chat_open:
                    drukma_chat.handle_chat_key(event)
                    continue

                # ---- GLOBAL HOTKEYS ----
                if event.key == pygame.K_m:
                    if pygame.mixer.music.get_volume() > 0:
                        pygame.mixer.music.set_volume(0.0)
                        show_message("MUSIC OFF")
                    else:
                        pygame.mixer.music.set_volume(0.20)
                        show_message("MUSIC ON")
                    continue

                if event.key == pygame.K_F5:
                    if save_system.save_game(collect_save_state()):
                        show_message("GAME SAVED")
                    continue

                if event.key == pygame.K_F9:
                    state = save_system.load_game()
                    if state:
                        apply_save_state(state)
                        show_message("GAME LOADED")
                    continue

                # ---- JOURNAL toggles with J ----
                if event.key == pygame.K_j:
                    if game_state == "playing" and not paused:
                        journal_open = not journal_open
                        if journal_open:
                            journal_selected = 0
                        continue

                # ---- Journal navigation ----
                if journal_open:
                    if event.key == pygame.K_ESCAPE:
                        journal_open = False
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        if story_state.STATE.journal_entries:
                            journal_selected = (journal_selected - 1) % len(story_state.STATE.journal_entries)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if story_state.STATE.journal_entries:
                            journal_selected = (journal_selected + 1) % len(story_state.STATE.journal_entries)
                    continue

                if event.key == pygame.K_ESCAPE:
                    if game_state == "playing":
                        paused = True
                    continue

                if challenge_open:
                    if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                        selected = event.key - pygame.K_0
                        if selected == challenge_answer:
                            sound_system.play("correct")
                            challenge_result = "Correct! Guardian challenge passed."
                            challenge_open = False
                            if quest_objective == "Visit Input Village":
                                quest_objective = "Return to Karma"
                                award_guardian_reward("INPUT GUARDIAN")
                                drukma_commentary.trigger("passed_input")
                            elif quest_objective == "Return to Karma":
                                quest_objective = "Visit Storage Vault"
                                award_guardian_reward("PROCESSING GUARDIAN")
                                world.unlock_location("Storage Vault")
                                drukma_commentary.trigger("passed_processing")
                            elif quest_objective == "Visit Storage Vault":
                                quest_objective = "Visit Output Tower"
                                award_guardian_reward("STORAGE GUARDIAN")
                                world.unlock_location("Output Tower")
                                story_state.STATE.set_flag("storage_vault_done", True)
                                drukma_commentary.trigger("passed_storage")
                            elif quest_objective == "Visit Output Tower":
                                quest_objective = "Visit Memory Monastery"
                                award_guardian_reward("OUTPUT GUARDIAN")
                                world.unlock_location("Memory Monastery")
                                story_state.STATE.set_flag("output_tower_done", True)
                                drukma_commentary.trigger("passed_output")
                            elif quest_objective == "Visit Memory Monastery":
                                quest_objective = "Report to Karma"
                                award_guardian_reward("MEMORY GUARDIAN")
                                story_state.STATE.set_flag("memory_monastery_done", True)
                                story_state.STATE.set_flag("guardians_all_met", True)
                                drukma_commentary.trigger("passed_memory")
                        else:
                            sound_system.play("wrong")
                            challenge_result = "Not quite. Try again."
                    continue

                if tashi_quest.handle_event(event):
                    continue

                # ---- Act scene event handlers ----
                if current_scene == "eastern_ruins":
                    if eastern_ruins.handle_event(event):
                        continue
                if current_scene == "processing_citadel":
                    if processing_citadel.handle_event(event):
                        continue
                if current_scene == "memory_monastery":
                    if memory_monastery.handle_event(event):
                        continue
                if current_scene == "storage_vault":
                    if storage_vault.handle_event(event):
                        continue
                if current_scene == "network_highlands":
                    if network_highlands.handle_event(event):
                        continue
                if current_scene == "deep_archive":
                    if deep_archive.handle_event(event):
                        continue
                if current_scene == "core_heart":
                    if core_heart.handle_event(event):
                        continue

                if event.key == pygame.K_e:
                    handle_interaction()

                if event.key == pygame.K_q:
                    if drukma_awake:
                        was_open = drukma_chat.chat_open
                        drukma_chat.toggle_chat()
                        sound_system.play("ui_close" if was_open else "ui_open")
                    else:
                        talk_to_drukma()

        # =========================================================
        # RENDER
        # =========================================================
        if game_state == "title":
            draw_title_screen()
            pygame.display.flip()
            clock.tick(60)
            continue

        if game_state == "intro":
            update_intro()
            if game_state == "intro":
                draw_intro()
            draw_fade()
            pygame.display.flip()
            clock.tick(60)
            continue

        if not _startup_banner_shown and not quest_completed and not paused:
            _startup_banner_shown = True
            show_message("MISSION STARTED: THE AWAKENING")

        if paused:
            if current_scene == "village":
                world.draw_world(screen, quest_active, quest_objective, DEBUG_ALL_GUARDIANS)
                draw_drukma(screen)
            elif current_scene == "cpu_dzong":
                world.draw_cpu_dzong_interior(screen)
            elif current_scene == "eastern_ruins":
                eastern_ruins.draw_background_layer(screen)
                player.draw_player(screen)
                eastern_ruins.draw_foreground_layer(screen)
            elif current_scene == "processing_citadel":
                processing_citadel.draw_background_layer(screen)
                player.draw_player(screen)
                processing_citadel.draw_foreground_layer(screen)
            elif current_scene == "memory_monastery":
                memory_monastery.draw_background_layer(screen)
                player.draw_player(screen)
                memory_monastery.draw_foreground_layer(screen)
            elif current_scene == "storage_vault":
                storage_vault.draw_background_layer(screen)
                player.draw_player(screen)
                storage_vault.draw_foreground_layer(screen)
            elif current_scene == "network_highlands":
                network_highlands.draw_background_layer(screen)
                player.draw_player(screen)
                network_highlands.draw_foreground_layer(screen)
            elif current_scene == "deep_archive":
                deep_archive.draw_background_layer(screen)
                player.draw_player(screen)
                deep_archive.draw_foreground_layer(screen)
            elif current_scene == "core_heart":
                core_heart.draw_background_layer(screen)
                player.draw_player(screen)
                core_heart.draw_foreground_layer(screen)
            draw_game_title()
            draw_quest_tracker()
            draw_rpg_hud()
            draw_pause_menu()
            pygame.display.flip()
            clock.tick(60)
            continue

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0

        if not dialogue_open and not challenge_open and not drukma_chat.chat_open and not is_fading() and not journal_open:
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                dx -= player.player_speed; player.player_direction = "left"
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                dx += player.player_speed; player.player_direction = "right"
            if keys[pygame.K_w] or keys[pygame.K_UP]:
                dy -= player.player_speed; player.player_direction = "up"
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:
                dy += player.player_speed; player.player_direction = "down"

        player.player_moving = (dx != 0 or dy != 0)

        if player.player_moving and not is_fading():
            footstep_timer += 1
            if footstep_timer >= 20:
                footstep_timer = 0
                sound_system.play("step")
        else:
            footstep_timer = 0

        # ---- Input blocking + collision across all act scenes ----
        if (not dialogue_open and not challenge_open and not drukma_chat.chat_open
                and not is_fading() and not journal_open
                and not tashi_quest.is_blocking_input()
                and not eastern_ruins.is_blocking_input()
                and not processing_citadel.is_blocking_input()
                and not memory_monastery.is_blocking_input()
                and not storage_vault.is_blocking_input()
                and not network_highlands.is_blocking_input()
                and not deep_archive.is_blocking_input()
                and not core_heart.is_blocking_input()):
            if current_scene == "village":
                player.move_player(dx, dy, build_village_collisions())
            elif current_scene == "cpu_dzong":
                player.move_player_interior(dx, dy, build_dzong_collisions())
            elif current_scene == "eastern_ruins":
                player.move_player(dx, dy, eastern_ruins.build_collisions())
            elif current_scene == "processing_citadel":
                player.move_player(dx, dy, processing_citadel.build_collisions())
            elif current_scene == "memory_monastery":
                player.move_player(dx, dy, memory_monastery.build_collisions())
            elif current_scene == "storage_vault":
                player.move_player(dx, dy, storage_vault.build_collisions())
            elif current_scene == "network_highlands":
                player.move_player(dx, dy, network_highlands.build_collisions())
            elif current_scene == "deep_archive":
                player.move_player(dx, dy, deep_archive.build_collisions())
            elif current_scene == "core_heart":
                player.move_player(dx, dy, core_heart.build_collisions())

        if ending_pending and reward_timer <= 0 and not is_fading():
            ending_pending = False
            start_fade_out("ending")

        update_drukma()
        check_act_chain()
        tashi_quest.update()
        if current_scene == "eastern_ruins":
            eastern_ruins.update()
        if current_scene == "processing_citadel":
            processing_citadel.update()
        if current_scene == "memory_monastery":
            memory_monastery.update()
        if current_scene == "storage_vault":
            storage_vault.update()
        if current_scene == "network_highlands":
            network_highlands.update()
        if current_scene == "deep_archive":
            deep_archive.update()
        if current_scene == "core_heart":
            core_heart.update()
        if drukma_awake:
            drukma_commentary.update(player.player_moving)
        if current_scene == "village":
            check_drukma_auto_comment()

        if current_scene == "village":
            world.draw_world(screen, quest_active, quest_objective, DEBUG_ALL_GUARDIANS)
            draw_drukma(screen)
            draw_game_title()
            draw_quest_tracker()
            draw_quest_message()
            draw_rpg_hud()
            update_and_draw_reward_banner()

            if not dialogue_open and not challenge_open and not drukma_chat.chat_open:
                if (story_state.STATE.get_flag("tashi_quest_started")
                        and not story_state.STATE.get_flag("tashi_component_taken")
                        and player.player.colliderect(world.damaged_component_rect.inflate(30, 30))):
                    world.draw_prompt(screen, "Press E to pick up Resonator Coil", HEIGHT - 110)
                elif not world.shrine_activated and \
                        player.player.colliderect(world.shrine_rect.inflate(50, 50)):
                    world.draw_prompt(screen, "Press E to investigate Shrine", HEIGHT - 110)
                else:
                    nearby = get_nearby_npc()
                    if (quest_active or quest_completed) and \
                            world.is_unlocked("CPU Dzong") and \
                            player.player.colliderect(world.cpu_dzong_entrance.inflate(20, 20)):
                        world.draw_prompt(screen, "Press E to enter CPU Dzong", HEIGHT - 110)
                    elif story_state.STATE.get_flag("drukma_awake") and \
                            player.player.colliderect(world.eastern_ruins_entrance.inflate(20, 20)):
                        world.draw_prompt(screen, "Press E to enter Eastern Ruins", HEIGHT - 110)
                    elif nearby:
                        world.draw_prompt(screen, f"Press E to talk to {nearby['name']}", HEIGHT - 110)
                    else:
                        for name, rect in world.locations.items():
                            if world.is_unlocked(name) and \
                                    player.player.colliderect(rect.inflate(50, 50)):
                                world.draw_prompt(screen, f"Press E to inspect {name}", HEIGHT - 110)
                                break

                if drukma_awake:
                    q_hint = small_font.render("[Q] Chat with Drukma", True, (140, 200, 220))
                    screen.blit(q_hint, (WIDTH - q_hint.get_width() - 20, HEIGHT - 78))

        elif current_scene == "cpu_dzong":
            world.draw_cpu_dzong_interior(screen)
            draw_game_title()
            draw_quest_tracker()
            draw_quest_message()
            draw_rpg_hud()
            update_and_draw_reward_banner()

            if not dialogue_open and not challenge_open and not drukma_chat.chat_open:
                if player.player.colliderect(world.guardian["rect"].inflate(45, 45)):
                    world.draw_prompt(screen, "Press E to talk to Karma", HEIGHT - 110)
                elif player.player.colliderect(world.cpu_dzong_exit.inflate(20, 20)):
                    world.draw_prompt(screen, "Press E to exit CPU Dzong", HEIGHT - 110)

        elif current_scene == "eastern_ruins":
            eastern_ruins.draw_background_layer(screen)
            player.draw_player(screen)
            eastern_ruins.draw_foreground_layer(screen)
            draw_game_title()
            draw_quest_tracker()
            draw_quest_message()
            draw_rpg_hud()

        elif current_scene == "processing_citadel":
            processing_citadel.draw_background_layer(screen)
            player.draw_player(screen)
            processing_citadel.draw_foreground_layer(screen)
            draw_game_title()
            draw_quest_tracker()
            draw_quest_message()
            draw_rpg_hud()

        elif current_scene == "memory_monastery":
            memory_monastery.draw_background_layer(screen)
            player.draw_player(screen)
            memory_monastery.draw_foreground_layer(screen)
            draw_game_title()
            draw_quest_tracker()
            draw_quest_message()
            draw_rpg_hud()

        elif current_scene == "storage_vault":
            storage_vault.draw_background_layer(screen)
            player.draw_player(screen)
            storage_vault.draw_foreground_layer(screen)
            draw_game_title()
            draw_quest_tracker()
            draw_quest_message()
            draw_rpg_hud()

        elif current_scene == "network_highlands":
            network_highlands.draw_background_layer(screen)
            player.draw_player(screen)
            network_highlands.draw_foreground_layer(screen)
            draw_game_title()
            draw_quest_tracker()
            draw_quest_message()
            draw_rpg_hud()

        elif current_scene == "deep_archive":
            deep_archive.draw_background_layer(screen)
            player.draw_player(screen)
            deep_archive.draw_foreground_layer(screen)
            draw_game_title()
            draw_quest_tracker()
            draw_quest_message()
            draw_rpg_hud()

        elif current_scene == "core_heart":
            core_heart.draw_background_layer(screen)
            player.draw_player(screen)
            core_heart.draw_foreground_layer(screen)
            draw_game_title()
            draw_quest_tracker()
            draw_quest_message()
            draw_rpg_hud()

        draw_dialogue()
        draw_challenge()
        drukma_chat.draw_chat(screen, WIDTH, HEIGHT, font, small_font)

        update_fragment_popup()
        draw_fragment_popup()
        draw_journal()

        draw_fade()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    asyncio.run(main())