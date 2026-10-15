import pygame
import re
import random

# =========================================================
# KNOWLEDGE BASE — Drukma's answers
# =========================================================
KNOWLEDGE = [
    # ---------- Greetings ----------
    {"keywords": ["hello", "hi", "hey", "greetings", "yo"],
     "response": "Hello, traveler. I am Drukma. Ask me about the Core, the Guardians, or the five forces of a computer.",
     "priority": 1},
    {"keywords": ["thanks", "thank", "cheers", "appreciate"],
     "response": "You are welcome. My memory is broken, but my purpose remains: to help you understand.",
     "priority": 1},
    {"keywords": ["bye", "goodbye", "farewell", "later"],
     "response": "Go well, young guardian. I will be here.",
     "priority": 1},
    {"keywords": ["who", "you", "drukma", "yourself", "name"],
     "response": "I am Drukma. I was bound to the Ancient Shrine. I remember concepts, but not my past. Perhaps you can help me recover it.",
     "priority": 3},

    # ---------- Help ----------
    {"keywords": ["help", "stuck", "lost", "where", "go", "objective"],
     "response": "Look at your quest tracker in the top-left. It shows your current objective. Press E to interact with people or places.",
     "priority": 2},
    {"keywords": ["controls", "keys", "movement", "move", "play"],
     "response": "Use W A S D or the arrow keys to walk. Press E to interact. Press Q to speak with me. Press ESC to quit.",
     "priority": 3},

    # ---------- World ----------
    {"keywords": ["core", "drukora", "kingdom", "heart"],
     "response": "The Core is the heart of Drukora — a great computer system that once powered everything. It has gone silent. Something reached it before us.",
     "priority": 3},
    {"keywords": ["shrine", "ancient"],
     "response": "The Ancient Shrine is where I was bound. Its crystal holds fragments of old records. Touching it awakened me.",
     "priority": 3},
    {"keywords": ["guardian", "guardians"],
     "response": "Five Guardians protect the five forces: Dorji for Input, Karma for Processing, Choden for Storage, Sonam for Output, and Dawa for Memory.",
     "priority": 2},

    # ---------- Guardians ----------
    {"keywords": ["karma"],
     "response": "Karma is the Guardian of Processing. She resides in the CPU Dzong. She is strict, but she taught every instruction Drukora ever needed.",
     "priority": 3},
    {"keywords": ["dorji"],
     "response": "Dorji guards the Input Village. He is the first guardian you will meet. He tests travelers with questions about how a system receives information.",
     "priority": 3},
    {"keywords": ["dawa"],
     "response": "Dawa waits at the Memory Monastery to the north. She teaches about RAM and ROM — the Core's present thoughts and its waking instructions.",
     "priority": 3},
    {"keywords": ["choden"],
     "response": "Choden watches over the Storage Vault south of the Dzong. She preserves records that outlive even the loss of power.",
     "priority": 3},
    {"keywords": ["sonam"],
     "response": "Sonam stands near the Output Tower to the east. She is how the Core speaks to the world — monitors, speakers, printers.",
     "priority": 3},
    {"keywords": ["village", "elder", "tashi"],
     "response": "The Village Elder was the first to send you on this journey. He has watched the Core's decline for many seasons.",
     "priority": 3},
    {"keywords": ["pema"],
     "response": "Pema keeps the village records. She knows the old stories. Her words often carry hidden truth.",
     "priority": 3},

    # ---------- INPUT ----------
    {"keywords": ["input", "keyboard", "mouse", "microphone", "scanner", "receive", "enter", "type"],
     "response": "INPUT is how a system receives information. Keyboards, mice, microphones, and scanners all send data INTO a computer. Without Input, the Core is blind and deaf.",
     "priority": 4},

    # ---------- PROCESSING ----------
    {"keywords": ["processing", "cpu", "processor", "brain", "execute", "instructions"],
     "response": "PROCESSING is where the system thinks. The CPU (Central Processing Unit) executes instructions and controls the whole system. It does not store or display — it ACTS.",
     "priority": 4},

    # ---------- STORAGE ----------
    {"keywords": ["storage", "hard", "drive", "ssd", "usb", "disk", "save"],
     "response": "STORAGE holds data for the long term. Hard drives, SSDs, and USB drives keep files even when the power is off. Unlike memory, storage survives.",
     "priority": 4},

    # ---------- OUTPUT ----------
    {"keywords": ["output", "monitor", "speaker", "printer", "display", "screen"],
     "response": "OUTPUT is how the system shows its results. Monitors display images. Speakers play sound. Printers produce pages. Without Output, we would never see the Core's work.",
     "priority": 4},

    # ---------- MEMORY ----------
    {"keywords": ["memory", "ram", "rom", "temporary"],
     "response": "MEMORY is the present, not the past. RAM temporarily stores data while programs run — fast but fleeting. ROM holds the instructions the system needs to wake up.",
     "priority": 4},

    # ---------- Quest ----------
    {"keywords": ["quiz", "question", "challenge", "test"],
     "response": "Each Guardian will ask you one question. Think carefully. The answer is always the device or component that matches their force.",
     "priority": 2},
    {"keywords": ["fragment", "fragments", "xp", "experience", "reward"],
     "response": "Every Guardian you best grants a Core Fragment and 100 XP. Collect all five, and something greater may reveal itself.",
     "priority": 3},
]

FALLBACKS = [
    "My records are... unclear on that. Try asking about Input, Processing, Storage, Output, or Memory.",
    "I do not understand. Perhaps ask about the Core, the Guardians, or one of the five forces?",
    "That question is lost in my damaged memory. Ask me something else — maybe about a Guardian?",
]

# =========================================================
# CHAT STATE
# =========================================================
chat_open = False
chat_input = ""
chat_history = []
CHAT_HISTORY_MAX = 8

def open_chat():
    global chat_open, chat_input, chat_history
    chat_open = True
    chat_input = ""
    if not chat_history:
        chat_history.append(("Drukma",
            "Ask me anything, traveler. Try: 'What is a CPU?' or 'Who are the Guardians?'"))

def close_chat():
    global chat_open, chat_input
    chat_open = False
    chat_input = ""

def toggle_chat():
    if chat_open:
        close_chat()
    else:
        open_chat()

# =========================================================
# MATCHING
# =========================================================
def _match(text):
    tokens = set(re.findall(r"\w+", text.lower()))
    if not tokens:
        return random.choice(FALLBACKS)

    best_score, best_prio, best_resp = 0, 0, None
    for entry in KNOWLEDGE:
        score = len(tokens & set(entry["keywords"]))
        if score == 0:
            continue
        prio = entry.get("priority", 1)
        if score > best_score or (score == best_score and prio > best_prio):
            best_score, best_prio, best_resp = score, prio, entry["response"]

    return best_resp if best_resp else random.choice(FALLBACKS)

def submit_chat_input():
    global chat_input, chat_history
    text = chat_input.strip()
    if not text:
        return
    chat_history.append(("You", text))
    chat_history.append(("Drukma", _match(text)))
    if len(chat_history) > CHAT_HISTORY_MAX:
        chat_history[:] = chat_history[-CHAT_HISTORY_MAX:]
    chat_input = ""

# =========================================================
# KEY HANDLING
# =========================================================
def handle_chat_key(event):
    global chat_input
    if event.key == pygame.K_ESCAPE:
        close_chat()
        return True
    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        submit_chat_input()
        return True
    if event.key == pygame.K_BACKSPACE:
        chat_input = chat_input[:-1]
        return True
    if event.unicode and event.unicode.isprintable() and len(chat_input) < 80:
        if event.unicode not in ("\t", "\r", "\n"):
            chat_input += event.unicode
        return True
    return False

# =========================================================
# RENDERING
# =========================================================
def draw_chat(screen, WIDTH, HEIGHT, font, small_font):
    if not chat_open:
        return

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    screen.blit(overlay, (0, 0))

    panel_w, panel_h = 720, 380
    panel_x = (WIDTH - panel_w) // 2
    panel_y = (HEIGHT - panel_h) // 2 - 30
    panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)

    shadow = pygame.Surface((panel_w + 12, panel_h + 12), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 150), (6, 6, panel_w, panel_h), border_radius=14)
    screen.blit(shadow, (panel.x - 6, panel.y - 6))

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (18, 32, 45, 245), (0, 0, panel_w, panel_h), border_radius=14)
    pygame.draw.rect(panel_surf, (120, 220, 240, 255), (0, 0, panel_w, panel_h), 3, border_radius=14)
    screen.blit(panel_surf, panel.topleft)

    header = pygame.Rect(panel.x, panel.y, panel_w, 52)
    pygame.draw.rect(screen, (28, 48, 62), header,
                     border_top_left_radius=14, border_top_right_radius=14)
    pygame.draw.line(screen, (120, 220, 240),
                     (panel.x + 2, header.bottom), (panel.right - 2, header.bottom), 2)

    title_font = pygame.font.SysFont("georgia", 22, bold=True)
    screen.blit(title_font.render("DRUKMA", True, (180, 240, 255)),
                (panel.x + 20, panel.y + 14))

    hint = small_font.render("Type a question and press ENTER  ·  ESC to close",
                             True, (150, 190, 210))
    screen.blit(hint, (panel.right - hint.get_width() - 20, panel.y + 18))

    y = panel.y + 68
    line_h = 22
    max_width = panel_w - 40

    for speaker, text in chat_history[-6:]:
        color = (255, 220, 130) if speaker == "Drukma" else (160, 220, 255)
        prefix = "Drukma: " if speaker == "Drukma" else "You: "
        full = prefix + text

        words = full.split()
        lines, cur = [], ""
        for w in words:
            test = cur + w + " "
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur: lines.append(cur.strip())
                cur = w + " "
        if cur: lines.append(cur.strip())

        for line in lines:
            screen.blit(font.render(line, True, color), (panel.x + 20, y))
            y += line_h
        y += 4

    input_box = pygame.Rect(panel.x + 16, panel.bottom - 54, panel_w - 32, 38)
    pygame.draw.rect(screen, (10, 20, 28), input_box, border_radius=8)
    pygame.draw.rect(screen, (120, 220, 240), input_box, 2, border_radius=8)

    caret = "|" if (pygame.time.get_ticks() // 400) % 2 == 0 else ""
    screen.blit(font.render(chat_input + caret, True, (230, 245, 255)),
                (input_box.x + 10, input_box.y + 9))