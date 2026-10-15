"""
voices.py — single source of truth for every speaking character.

Every act module, every recording, every narration line should resolve
its speaker to a canonical ID here. This file owns:
  - display name (what shows in the dialogue box)
  - colour (for tinting)
  - audio profile (for the synthesized fallback)
  - voice notes (register, habits — for writers)

Do not add voice data anywhere else.
"""

# =========================================================
# CANONICAL VOICES
# =========================================================
# Each entry:
#   display   — what the dialogue box shows
#   canonical — the folder name on disk (no spaces)
#   aliases   — any speaker ID that should route here
#   prefixes  — text prefixes to strip before hashing for .ogg lookup
#   colour    — RGB for the dialogue box
#   audio     — synthesized beep profile
#   register  — writer's notes on voice
#
VOICES = {

    # ---------------------------------------------------
    # Drukma — the AI companion
    # ---------------------------------------------------
    "drukma": {
        "display":   "DRUKMA",
        "canonical": "Drukma",
        "aliases":   ["Drukma", "DRUKMA", "drukma"],
        "prefixes":  ["Drukma: ", "DRUKMA: "],
        "colour":    (150, 220, 240),
        "audio": {
            "f0": 340, "vowel": "i", "dur": 0.15, "vol": 0.44,
            "variance": 0.015, "vibrato": True,
        },
        "register": (
            "An AI companion — closer to a friend than a guide. Curious, "
            "warm, a little unsure of itself. Speaks in short, direct "
            "sentences. Uses 'you' and 'we' freely — 'you found it', "
            "'we should look closer'. Admits uncertainty out loud ('I do "
            "not know', 'I cannot remember') — never bluffs to seem "
            "wiser. Reacts to what the player DOES, not just to what is "
            "happening. Small encouragements. Small questions. Occasional "
            "dry humour. Never lectures. Never grades. Warms across the "
            "acts: guarded in I, easy by IV, protective by VIII. Never "
            "sarcastic. Never cruel."
        ),
    },

    # ---------------------------------------------------
    # Null — the antagonist
    # ---------------------------------------------------
    "null": {
        "display":   "NULL",
        "canonical": "Null",
        "aliases":   ["Null", "NULL", "null"],
        "prefixes":  ["Null: ", "NULL: "],
        "colour":    (255, 140, 100),
        "audio": {
            "f0": 88, "vowel": "u", "dur": 0.28, "vol": 0.60,
            "variance": 0.03, "vibrato": False,
        },
        "register": (
            "Cold, deliberate, courteous in a way that frightens. Never "
            "raises its voice. Speaks in complete sentences — the opposite "
            "of Drukma's clipped rhythm. Uses 'I' sparingly; prefers "
            "impersonal constructions ('the kingdom', 'the system'). "
            "Believes it is protecting, not attacking. Every line can be "
            "read twice and mean two things. Never uses contractions."
        ),
    },

    # ---------------------------------------------------
    # Player character
    # ---------------------------------------------------
    "you": {
        "display":   "YOU",
        "canonical": "You",
        "aliases":   ["You", "YOU", "Player"],
        "prefixes":  ["You: ", "YOU: "],
        "colour":    (230, 230, 230),
        "audio": {
            "f0": 175, "vowel": "a", "dur": 0.16, "vol": 0.42,
            "variance": 0.02, "vibrato": True,
        },
        "register": (
            "Direct, curious, unadorned. Short declarative sentences. "
            "Asks questions the player would ask. Never speeches. Never "
            "explains things the player hasn't learned yet. Warmth grows "
            "across the acts — from 'I cannot remember' in I to "
            "'Then this time, we build...' in VIII."
        ),
    },

    # ---------------------------------------------------
    # Village Elder — Keeper of oral history
    # ---------------------------------------------------
    "elder": {
        "display":   "VILLAGE ELDER",
        "canonical": "Village_Elder",
        "aliases":   ["Village Elder", "Elder", "elder"],
        "prefixes":  ["Village Elder: ", "Elder: "],
        "colour":    (220, 200, 160),
        "audio": {
            "f0": 102, "vowel": "o", "dur": 0.22, "vol": 0.52,
            "variance": 0.015, "vibrato": True,
        },
        "register": (
            "Slow, warm, measured. Speaks in the cadence of someone who "
            "has told this story before. Uses 'we' for the village and "
            "'they' for the Guardians — never confuses the two. Calls the "
            "player 'traveller' early, by name later. Doesn't pretend to "
            "understand technology; says so plainly."
        ),
    },

    # ---------------------------------------------------
    # Tashi — curious young mechanic
    # ---------------------------------------------------
    "tashi": {
        "display":   "TASHI",
        "canonical": "Tashi",
        "aliases":   ["Tashi", "tashi"],
        "prefixes":  ["Tashi: "],
        "colour":    (240, 210, 140),
        "audio": {
            "f0": 190, "vowel": "a", "dur": 0.15, "vol": 0.46,
            "variance": 0.025, "vibrato": True,
        },
        "register": (
            "Quick, bright, enthusiastic. Runs words together when excited. "
            "Asks more questions than they answer. Uses workshop vocabulary "
            "freely ('the gear train', 'the coil') even when the player "
            "won't understand yet. Never lectures — only wonders aloud."
        ),
    },

    # ---------------------------------------------------
    # Pema — village record keeper
    # ---------------------------------------------------
    "pema": {
        "display":   "PEMA",
        "canonical": "Pema",
        "aliases":   ["Pema", "pema"],
        "prefixes":  ["Pema: "],
        "colour":    (200, 190, 220),
        "audio": {
            "f0": 210, "vowel": "a", "dur": 0.17, "vol": 0.46,
            "variance": 0.02, "vibrato": True,
        },
        "register": (
            "Precise, careful, mildly pedantic. Distinguishes 'recorded' "
            "from 'remembered' from 'reported'. Will correct the player's "
            "imprecise language gently. Trusts documents more than people, "
            "but is learning not to. Never raises her voice."
        ),
    },

    # ---------------------------------------------------
    # Silent Sentinel — ancient system guardian
    # ---------------------------------------------------
    "sentinel": {
        "display":   "SENTINEL",
        "canonical": "Sentinel",
        "aliases":   ["Sentinel", "Silent Sentinel", "sentinel"],
        "prefixes":  ["Sentinel: ", "Silent Sentinel: "],
        "colour":    (180, 190, 200),
        "audio": {
            "f0": 92, "vowel": "u", "dur": 0.30, "vol": 0.55,
            "variance": 0.01, "vibrato": False,
        },
        "register": (
            "Formal, procedural, almost ceremonial. Speaks in conditional "
            "clauses ('Access is granted if...', 'Threat level: reduced.'). "
            "Never uses 'I' — says 'this unit' or 'the guardian'. Reports "
            "states rather than opinions. Softens only after its "
            "instruction sequence is corrected."
        ),
    },

    # ---------------------------------------------------
    # System Architect — the missing researcher
    # ---------------------------------------------------
    "architect": {
        "display":   "ARCHITECT",
        "canonical": "Architect",
        "aliases":   ["Architect", "System Architect", "architect"],
        "prefixes":  ["Architect: ", "System Architect: "],
        "colour":    (200, 220, 200),
        "audio": {
            "f0": 128, "vowel": "o", "dur": 0.20, "vol": 0.50,
            "variance": 0.015, "vibrato": True,
        },
        "register": (
            "Thoughtful, direct, unafraid of hard truths. Speaks to the "
            "player as an equal — never condescends. Uses 'we' when "
            "referring to the recovery project, 'I' when taking "
            "responsibility. Sentences end on concrete nouns, not "
            "abstractions. Sounds like someone who knew they might not "
            "survive to explain."
        ),
    },

    # ---------------------------------------------------
    # The Five Guardians — live IDs (rarely used)
    # ---------------------------------------------------
    "dorji": {
        "display":   "DORJI",
        "canonical": "Dorji",
        "aliases":   ["Dorji", "dorji"],
        "prefixes":  ["Dorji: "],
        "colour":    (200, 200, 200),
        "audio": {
            "f0": 142, "vowel": "o", "dur": 0.20, "vol": 0.50,
            "variance": 0.02, "vibrato": True,
        },
        "register": (
            "Patient, exact, faintly wry. Dorji of Input believes "
            "questions are answers in disguise. Will not accept 'I think "
            "so' — wants 'I know' or 'I don't know'. Speaks to be "
            "understood, not admired."
        ),
    },
    "karma": {
        "display":   "KARMA",
        "canonical": "Karma",
        "aliases":   ["Karma", "karma"],
        "prefixes":  ["Karma: "],
        "colour":    (220, 220, 200),
        "audio": {
            "f0": 226, "vowel": "e", "dur": 0.17, "vol": 0.48,
            "variance": 0.02, "vibrato": True,
        },
        "register": (
            "Sharp, economical, unsentimental. Karma of Processing "
            "believes a wrong result is worse than no result. Speaks in "
            "short, closed sentences. Will interrupt the player if the "
            "player is being vague. Never softens a verdict."
        ),
    },
    "choden": {
        "display":   "CHODEN",
        "canonical": "Choden",
        "aliases":   ["Choden", "choden"],
        "prefixes":  ["Choden: "],
        "colour":    (200, 210, 190),
        "audio": {
            "f0": 160, "vowel": "a", "dur": 0.20, "vol": 0.50,
            "variance": 0.015, "vibrato": True,
        },
        "register": (
            "Gentle, unhurried, quietly stubborn. Choden of Storage "
            "believes records are a form of care. Speaks in parables. "
            "Uses 'remember' as a verb with weight — not casual. Will "
            "gently correct the player if they misuse 'backup' or 'copy'."
        ),
    },
    "sonam": {
        "display":   "SONAM",
        "canonical": "Sonam",
        "aliases":   ["Sonam", "sonam"],
        "prefixes":  ["Sonam: "],
        "colour":    (240, 220, 160),
        "audio": {
            "f0": 250, "vowel": "i", "dur": 0.17, "vol": 0.48,
            "variance": 0.02, "vibrato": True,
        },
        "register": (
            "Bright, generous, impatient with opacity. Sonam of Output "
            "believes an unshared result is a lost result. Speaks in "
            "practical metaphors ('a wire', 'a window'). Uses 'we' "
            "freely — includes the player even when she barely knows them."
        ),
    },
    "dawa": {
        "display":   "DAWA",
        "canonical": "Dawa",
        "aliases":   ["Dawa", "dawa"],
        "prefixes":  ["Dawa: "],
        "colour":    (220, 210, 240),
        "audio": {
            "f0": 278, "vowel": "i", "dur": 0.19, "vol": 0.44,
            "variance": 0.02, "vibrato": True,
        },
        "register": (
            "Quiet, thoughtful, slightly haunted. Dawa of Memory knows "
            "what it costs to hold things. Speaks in questions more than "
            "statements. The only Guardian who admits she is afraid."
        ),
    },

    # ---------------------------------------------------
    # Recording variants of the Guardians
    # ---------------------------------------------------
    # Same voices, slightly lower, slightly slower. The player is
    # hearing them through a damaged recording, not in person.
    "dorji_recording": {
        "display":   "DORJI — RECORDING",
        "canonical": "Dorji_Recording",
        "aliases":   ["Dorji_Recording"],
        "prefixes":  [],
        "colour":    (170, 180, 180),
        "audio": {
            "f0": 128, "vowel": "o", "dur": 0.24, "vol": 0.48,
            "variance": 0.01, "vibrato": False,
        },
        "register": "Dorji, but formal. Recording voice, not live voice.",
    },
    "karma_recording": {
        "display":   "KARMA — RECORDING",
        "canonical": "Karma_Recording",
        "aliases":   ["Karma_Recording"],
        "prefixes":  [],
        "colour":    (190, 190, 180),
        "audio": {
            "f0": 208, "vowel": "e", "dur": 0.22, "vol": 0.44,
            "variance": 0.01, "vibrato": False,
        },
        "register": "Karma, but slower. Recording voice, not live voice.",
    },
    "choden_recording": {
        "display":   "CHODEN — RECORDING",
        "canonical": "Choden_Recording",
        "aliases":   ["Choden_Recording"],
        "prefixes":  [],
        "colour":    (180, 190, 180),
        "audio": {
            "f0": 148, "vowel": "o", "dur": 0.24, "vol": 0.46,
            "variance": 0.01, "vibrato": False,
        },
        "register": "Choden, but slower. Recording voice, not live voice.",
    },
    "sonam_recording": {
        "display":   "SONAM — RECORDING",
        "canonical": "Sonam_Recording",
        "aliases":   ["Sonam_Recording"],
        "prefixes":  [],
        "colour":    (220, 200, 150),
        "audio": {
            "f0": 232, "vowel": "i", "dur": 0.20, "vol": 0.44,
            "variance": 0.01, "vibrato": False,
        },
        "register": "Sonam, but formal. Recording voice, not live voice.",
    },
    "dawa_recording": {
        "display":   "DAWA — RECORDING",
        "canonical": "Dawa_Recording",
        "aliases":   ["Dawa_Recording"],
        "prefixes":  [],
        "colour":    (200, 195, 220),
        "audio": {
            "f0": 258, "vowel": "i", "dur": 0.22, "vol": 0.42,
            "variance": 0.01, "vibrato": False,
        },
        "register": "Dawa, but distant. Recording voice, not live voice.",
    },

    # ---------------------------------------------------
    # System / anonymous voices
    # ---------------------------------------------------
    "system": {
        "display":   "SYSTEM",
        "canonical": "System",
        "aliases":   ["System", "SYSTEM"],
        "prefixes":  ["SYSTEM: ", "System: "],
        "colour":    (180, 200, 220),
        "audio": {
            "f0": 200, "vowel": "o", "dur": 0.20, "vol": 0.42,
            "variance": 0.005, "vibrato": False,
        },
        "register": (
            "Flat, declarative, capitalised. Machine output, not speech. "
            "No contractions. No 'I'. Every line reads like a log entry."
        ),
    },
    "unknown_voice": {
        "display":   "UNKNOWN VOICE",
        "canonical": "Unknown_Voice",
        # "Ancient Shrine" is the speaker name used by main.py during the
        # shrine-activation dialogue in Act I. Those lines belong to the
        # same in-world voice as the Unknown Voice that resolves into
        # Drukma — so they route here rather than falling through to
        # the default beep.
        "aliases":   ["Unknown Voice", "UNKNOWN VOICE", "Unknown",
                      "Ancient Shrine", "Ancient_Shrine"],
        "prefixes":  ["UNKNOWN VOICE: ", "Unknown Voice: "],
        "colour":    (170, 150, 200),
        "audio": {
            "f0": 68, "vowel": "u", "dur": 0.30, "vol": 0.55,
            "variance": 0.02, "vibrato": False,
        },
        "register": (
            "Distorted, half-heard, not yet identified. Sounds like Null "
            "but isn't Null — yet. Used for the voice in Dawa's recording "
            "before the player knows whose it is."
        ),
    },
    "narrator": {
        "display":   "NARRATOR",
        "canonical": "Narrator",
        "aliases":   ["Narrator", "NARRATOR"],
        "prefixes":  ["NARRATOR: "],
        "colour":    (200, 200, 200),
        "audio": {
            "f0": 170, "vowel": "o", "dur": 0.22, "vol": 0.44,
            "variance": 0.01, "vibrato": False,
        },
        "register": (
            "Neutral, unemotional, present-tense. Describes actions the "
            "player cannot voice ('The hologram flickers.'). Never uses "
            "first person. Never editorialises."
        ),
    },

    # ---------------------------------------------------
    # Fallback — should rarely fire
    # ---------------------------------------------------
    "_default": {
        "display":   "VOICE",
        "canonical": "default",
        "aliases":   ["default"],
        "prefixes":  [],
        "colour":    (200, 200, 200),
        "audio": {
            "f0": 190, "vowel": "a", "dur": 0.18, "vol": 0.45,
            "variance": 0.0, "vibrato": False,
        },
        "register": "Unassigned speaker. If you see this, someone forgot.",
    },
}


# =========================================================
# INDEXES
# =========================================================
# Built once at import time. Do not edit these by hand.

# canonical id  →  full voice entry
_BY_CANONICAL = {v["canonical"]: v for v in VOICES.values()}

# every alias (and canonical)  →  full voice entry
_BY_ALIAS = {}
for _v in VOICES.values():
    _BY_ALIAS[_v["canonical"]] = _v
    for _a in _v["aliases"]:
        _BY_ALIAS[_a] = _v

# all prefixes, longest first — so "Unknown Voice: " beats "Unknown"
ALL_PREFIXES = sorted(
    (p for v in VOICES.values() for p in v["prefixes"]),
    key=len, reverse=True,
)


# =========================================================
# PUBLIC API
# =========================================================
def get(speaker_id):
    """Return the voice entry for any known speaker, or the default."""
    if speaker_id is None:
        return VOICES["_default"]
    return _BY_ALIAS.get(speaker_id, VOICES["_default"])


def canonical(speaker_id):
    """Return the on-disk folder name for a speaker."""
    return get(speaker_id)["canonical"]


def display(speaker_id):
    """Return the name to show in the dialogue box."""
    return get(speaker_id)["display"]


def colour(speaker_id):
    """Return the RGB tint for this speaker's dialogue box."""
    return get(speaker_id)["colour"]


def strip_prefix(text):
    """Remove a known speaker prefix from a dialogue line."""
    for p in ALL_PREFIXES:
        if text.startswith(p):
            return text[len(p):].strip()
    return text


def beep_styles():
    """Return the audio profile dict in the format sound_system expects."""
    out = {}
    for v in VOICES.values():
        a = v["audio"]
        out[v["canonical"]] = {
            "f0":       a["f0"],
            "dur":      a["dur"],
            "vowel":    a["vowel"],
            "vol":      a["vol"],
            "variance": a.get("variance", 0.02),
            "vibrato":  a.get("vibrato", True),
        }
    return out