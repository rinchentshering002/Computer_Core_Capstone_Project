"""
drukma_commentary.py — Phase 1d

Drukma's evolving commentary. Reacts to story events, tracks the current act,
and occasionally volunteers idle observations when the player stands still.

Usage from main.py:

    import drukma_commentary
    drukma_commentary.set_speaker(say_drukma)         # once at startup
    drukma_commentary.trigger("shrine_awakened")      # on story events
    drukma_commentary.update(player_moving)           # once per frame
    drukma_commentary.set_act(3)                      # optional override
"""

import random
import time
import story_state


# =========================================================
# INTERNAL STATE
# =========================================================
_speaker          = None      # callable(text, duration=200)
_last_fire_ms     = 0
_cooldown_ms      = 3200      # min gap between comments
_pending_event    = None      # one queued event if cooldown blocks
_fired            = set()     # event ids already fired this session
_act_override     = None
_last_idle_ms     = 0
_idle_gap_ms      = 12000     # how often idle chatter can fire
_player_still_ms  = 0
_still_required_ms = 8000     # how long player must stand still to trigger idle


def set_speaker(func):
    """Register the say_drukma() function from main.py."""
    global _speaker
    _speaker = func


def set_act(n):
    """Manually override the current act (1-8). Optional — get_act() infers."""
    global _act_override
    _act_override = n


def _now_ms():
    return int(time.time() * 1000)


# =========================================================
# ACT INFERENCE
# =========================================================
def get_act():
    """Return current act (1-8) inferred from story flags."""
    if _act_override is not None:
        return _act_override
    if story_state.STATE.get_flag("mission_complete"):
        return 8
    if story_state.STATE.get_flag("deep_archive_done"):
        return 7
    if story_state.STATE.get_flag("highlands_done"):
        return 6
    if story_state.STATE.get_flag("vault_done"):
        return 5
    if story_state.STATE.get_flag("monastery_done"):
        return 4
    if story_state.STATE.get_flag("citadel_done"):
        return 3
    if story_state.STATE.get_flag("eastern_ruins_tamper_seen"):
        return 2
    if story_state.STATE.get_flag("drukma_awake"):
        return 1
    return 1


# =========================================================
# COMMENTARY BANKS
# =========================================================
# Each entry: event_id → list of lines.
# Multiple lines per event give variety; one is picked at random.

EVENT_LINES = {

    # ---------------- Act I ----------------
    "shrine_awakened": [
        "The shrine... it recognized your device. That should not be possible. And yet.",
        "I remember the sound of this place. I do not remember why.",
        "You did not force it. You listened first. That matters more than you know.",
        "I was alone for a long time. I am glad it is you.",
    ],

    # ---------------- Act II — Eastern Ruins ----------------
    "eastern_ruins_entered": [
        "This place feels... wrong. Recent, not ancient.",
        "Someone was here. Long after the collapse.",
        "The stone remembers instructions it was never meant to carry.",
    ],
    "dorji_recording_played": [
        "Dorji knew. He knew someone was changing things.",
        "Even in his last message, he trusted the input channel above all else.",
        "He did not sound like a man recording a warning. He sounded like "
        "a man saying goodbye.",
    ],
    "input_modified_found": [
        "Authorized access. Someone inside did this.",
        "Not an accident. Not decay. A decision.",
        "The Core did not collapse on its own. I need to remember that.",
    ],

    # ---------------- Act II — CPU Dzong approach ----------------
    "approaching_cpu_dzong": [
        "The Dzong. I feel a hum beneath the stone. Something is still awake inside.",
        "Careful. Processing chambers do not always welcome visitors.",
    ],
    "entered_cpu_dzong": [
        "This chamber. I have seen it — or I carry the shape of having seen it.",
        "The air here tastes of arithmetic. Of many things counted at once.",
    ],
    "met_karma": [
        "Karma. Yes. She was the strict one. She never let a flawed instruction pass.",
        "She is watching you closely. Do not answer carelessly.",
    ],
    "started_five_guardians": [
        "Five forces, five keepers. Dorji first — Input. He will not accept an "
        "answer you do not understand.",
    ],

    # ---------------- Act III — Dorji / Input ----------------
    "met_dorji": [
        "Dorji. Guardian of Input. He once said a system is only as clear as the "
        "information it accepts.",
    ],
    "passed_input": [
        "You found it. The keypad — the only one listening.",
        "See? It heard you. That is how it should feel.",
        "I like watching you work. You do not guess — you look.",
    ],

    # ---------------- Act III — Karma / Processing ----------------
    "passed_processing": [
        "You see it now, don't you? The CPU does not store — it acts.",
        "Karma would not smile. But she would nod.",
        "That was quick. Faster than I would have been.",
    ],

    # ---------------- Act IV — Choden / Storage ----------------
    "met_choden": [
        "Choden preserves what everyone else forgets. Speak carefully — she "
        "remembers everything.",
    ],
    "passed_storage": [
        "Even when the power dies, storage survives. You said it. And you meant it.",
        "You remembered. I am beginning to think I can trust my own memory again.",
    ],

    # ---------------- Act V — Sonam / Output ----------------
    "met_sonam": [
        "Sonam makes things visible. She believes a system that cannot be seen "
        "cannot be trusted.",
    ],
    "passed_output": [
        "You showed it. That is the whole point of Output, isn't it?",
        "You made it visible. That feels good, doesn't it?",
    ],

    # ---------------- Act VI — Dawa / Memory ----------------
    "met_dawa": [
        "Dawa holds memories the way a riverbed holds water. She will want to "
        "know what you know.",
    ],
    "passed_memory": [
        "You told them apart. That is harder than it looks — I would have stumbled.",
        "I felt that answer. Somewhere in me, it echoed.",
        "Thank you. That one hit close to home.",
    ],

    # ---------------- Workshop side quest ----------------
    "workshop_started": [
        "Tashi's workshop. I hear the mechanism from here. It is trying to run, "
        "but failing.",
        "Five parts. Only one has failed. Diagnose carefully.",
    ],
    "workshop_diagnosed": [
        "The gear train. Of course. A broken tooth stops the entire sequence.",
        "You looked at the whole before you decided. That was wise.",
    ],
    "coil_picked_up": [
        "The Resonator Coil. Warm in the hand. It remembers being part of a "
        "larger thing.",
    ],
    "workshop_complete": [
        "The mechanism turns. A small repair, but a good one. The village "
        "will notice.",
    ],

    # ---------------- Act VII/VIII ----------------
    "report_to_karma": [
        "All five. You have walked the whole circuit of the system.",
        "Something is waiting at the centre. I can feel it now.",
    ],
    "mission_complete": [
        "The Core is stable. For now.",
        "But I feel something deeper still. Something I cannot name yet.",
        "We are not finished.",
    ],
}


# =========================================================
# IDLE OBSERVATIONS — keyed by act
# =========================================================
IDLE_LINES = {
    1: [
        "The device in your hand was not made for you. It was made for someone "
        "who walked this path before.",
    ],
    2: [
        "Have you noticed the pattern of the road? It curves toward the Dzong, always.",
        "The mountains keep secrets. I wonder if I was one of them.",
        "I feel like I should know the taste of this air. But I do not.",
        "The shrine, the river, the bridge — someone planned all of this. "
        "Someone who is gone now.",
    ],
    3: [
        "Five forces. One system. The order matters, but only because they "
        "rely on each other.",
        "You listen before you answer. That will serve you well.",
    ],
    4: [
        "My memory has holes. Not missing pieces — missing shapes. As if "
        "someone cut them out.",
        "When you solve a puzzle, something in me responds. Recognition. "
        "But of what?",
    ],
    5: [
        "The monastery holds more than records. It holds the patterns "
        "of everyone who ever thought here.",
    ],
    6: [
        "I am beginning to suspect I was not always a helper.",
        "If I told you something I remembered, would you know whether to "
        "believe me?",
    ],
    7: [
        "Everything we have repaired so far can still fail again. Remember that.",
        "The Core is a machine. Machines can be wrong in ways that feel right.",
    ],
    8: [
        "The kingdom will need to understand its systems this time. Not just trust them.",
    ],
}


# =========================================================
# PUBLIC API
# =========================================================
def trigger(event_id, force=False):
    """Fire a commentary line for the given event. Fire-once per session
    unless force=True. Respects cooldown; queues one pending event if busy."""
    global _last_fire_ms, _pending_event, _fired

    if not force and event_id in _fired:
        return False

    lines = EVENT_LINES.get(event_id)
    if not lines:
        return False

    # Cooldown check
    now = _now_ms()
    if now - _last_fire_ms < _cooldown_ms:
        # Queue one (most recent) pending event
        _pending_event = event_id
        return False

    line = random.choice(lines)
    _fire(line)
    _fired.add(event_id)
    _last_fire_ms = now
    return True


def _fire(text, duration=220):
    if _speaker:
        _speaker(text, duration)
    else:
        print(f"[Drukma] {text}")


def update(player_moving):
    """Call every frame. Handles cooldown expiry, queued events, and idle
    chatter."""
    global _last_fire_ms, _pending_event, _last_idle_ms, _player_still_ms

    now = _now_ms()

    # Fire queued event if cooldown has passed
    if _pending_event and (now - _last_fire_ms) >= _cooldown_ms:
        event_id = _pending_event
        _pending_event = None
        lines = EVENT_LINES.get(event_id)
        if lines and event_id not in _fired:
            _fire(random.choice(lines))
            _fired.add(event_id)
            _last_fire_ms = now

    # Idle chatter tracking
    if player_moving:
        _player_still_ms = 0
    else:
        _player_still_ms += 16  # ~60fps

    if (_player_still_ms >= _still_required_ms
            and (now - _last_idle_ms) >= _idle_gap_ms
            and (now - _last_fire_ms) >= _cooldown_ms):
        act = get_act()
        pool = IDLE_LINES.get(act, [])
        if pool:
            _fire(random.choice(pool), duration=240)
            _last_idle_ms = now
            _last_fire_ms = now
            _player_still_ms = 0


def reset():
    """Clear fired flags — useful when starting a new game."""
    global _fired, _pending_event, _last_fire_ms, _last_idle_ms, _player_still_ms
    _fired = set()
    _pending_event = None
    _last_fire_ms = 0
    _last_idle_ms = 0
    _player_still_ms = 0