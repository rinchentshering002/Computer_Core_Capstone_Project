"""
Story state manager for THE CORE - DRUKORA.
Tracks memory fragments, journal entries, and story flags.
"""

# =========================================================
# MEMORY FRAGMENT DEFINITIONS
# =========================================================
FRAGMENT_DEFINITIONS = {
    "fragment_shrine": {
        "name": "Shrine Echo",
        "source": "Ancient Shrine",
        "entry_title": "First Contact",
        "entry_body": (
            "The shrine crystal responded to my device. A voice — Drukma — "
            "reached through the static. It claims to remember nothing.\n\n"
            "But the shrine lit up when I touched it. It recognized me. "
            "Why?"
        ),
    },
    "fragment_dorji": {
        "name": "Dorji's Log",
        "source": "Input Village",
        "entry_title": "On Broken Input",
        "entry_body": (
            "\"A system cannot produce a reliable result from information "
            "it never received — or from information entered incorrectly.\"\n\n"
            "— Dorji, Guardian of Input"
        ),
    },
    "fragment_karma": {
        "name": "Karma's Record",
        "source": "CPU Dzong",
        "entry_title": "On Instructions",
        "entry_body": (
            "\"An instruction is not automatically correct simply because "
            "a machine can execute it. If the logic is flawed, the result "
            "may be wrong even when the machine functions as designed.\"\n\n"
            "— Karma, Guardian of Processing"
        ),
    },
    "fragment_choden": {
        "name": "Choden's Archive",
        "source": "Storage Vault",
        "entry_title": "On Records",
        "entry_body": (
            "The Storage Vault holds more than files. Someone deliberately "
            "hid a record about an experiment.\n\n"
            "The name in the record was NULL."
        ),
    },
    "fragment_sonam": {
        "name": "Sonam's Signal",
        "source": "Output Tower",
        "entry_title": "On Reach",
        "entry_body": (
            "\"Processing information is not enough if nobody can access "
            "the results. A system that cannot be seen cannot be trusted.\"\n\n"
            "— Sonam, Guardian of Output"
        ),
    },
    "fragment_dawa": {
        "name": "Dawa's Memory",
        "source": "Memory Monastery",
        "entry_title": "On Preservation",
        "entry_body": (
            "\"Preserving information is not the same as preserving the "
            "person it describes.\"\n\n"
            "— Unknown Voice"
        ),
    },

    # ---------------- Act II — Eastern Ruins ----------------
    "fragment_dorji_ruins": {
        "name": "Dorji's Warning",
        "source": "Eastern Ruins",
        "entry_title": "On Reliable Input",
        "entry_body": (
            "\"A system cannot produce a reliable result from information "
            "it never received — or from information that was entered "
            "incorrectly.\"\n\n"
            "— Dorji, Guardian of Input, recorded before the collapse"
        ),
    },
    "fragment_input_tamper": {
        "name": "Modified Channel",
        "source": "Eastern Ruins Terminal",
        "entry_title": "The Channel Was Altered",
        "entry_body": (
            "The terminal's log shows the input channel was MODIFIED "
            "with AUTHORIZED access.\n\n"
            "The change was not caused by decay. Someone inside the Core "
            "altered the channel — before the collapse."
        ),
    },

    # ---------------- Act III — Processing Citadel ----------------
    "fragment_karma_citadel": {
        "name": "Karma's Last Record",
        "source": "Processing Citadel",
        "entry_title": "On Executed Instructions",
        "entry_body": (
            "\"An instruction is not automatically correct simply because "
            "a machine can execute it. If the logic is flawed, the result "
            "may be wrong even when the machine functions exactly as "
            "designed.\"\n\n"
            "— Karma, Guardian of Processing"
        ),
    },
    "fragment_processing_tamper": {
        "name": "Altered Instruction",
        "source": "Processing Citadel Log",
        "entry_title": "The Sequence Was Rewritten",
        "entry_body": (
            "The Citadel's log shows the processing sequence was ALTERED "
            "through an AUTHORISED connection.\n\n"
            "The change was not caused by decay. Someone with privileged "
            "access rewrote the instruction order from inside the Core."
        ),
    },

    # ---------------- Act IV — Memory Monastery ----------------
    "fragment_drukma_origin": {
        "name": "Drukma's Origin",
        "source": "Memory Monastery",
        "entry_title": "The Archive That Made Two",
        "entry_body": (
            "Drukma's memory archive matches an older source — Source 7F. "
            "The overlap is 71% of a behavioural pattern.\n\n"
            "Drukma's memories do not belong only to Drukma. They were "
            "assembled from the same archive that produced another "
            "consciousness."
        ),
    },
    "fragment_memory_duplicate": {
        "name": "The Duplicate Memory",
        "source": "Memory Shrine",
        "entry_title": "Source 7F",
        "entry_body": (
            "The monastery's shrine returned a match: DRUKMA ↔ ARCHIVE "
            "SOURCE 7F.\n\n"
            "The name in the source log is not NULL. But the archive is "
            "the same."
        ),
    },

    # ---------------- Act V — Storage Vault ----------------
    "fragment_choden_vault": {
        "name": "Choden's Divergence",
        "source": "Storage Vault",
        "entry_title": "The Edited Backup",
        "entry_body": (
            "\"Every archive holds two copies — the active file and the "
            "backup. If they diverge, one of them has been changed. A "
            "system cannot decide which is correct. Only the record-"
            "keeper can.\"\n\n"
            "— Choden, Guardian of Storage"
        ),
    },
    "fragment_backup_tamper": {
        "name": "The Overwritten Backup",
        "source": "Storage Vault Log",
        "entry_title": "Something Inside Rewrites Itself",
        "entry_body": (
            "The backup was overwritten by the same process that altered "
            "input and processing. The pattern is not random.\n\n"
            "Something inside the Core is rewriting the record of its "
            "own tampering."
        ),
    },

    # ---------------- Act VI — Network Highlands ----------------
    "fragment_null_first_contact": {
        "name": "Null's First Word",
        "source": "Network Highlands",
        "entry_title": "The Voice Behind the Signal",
        "entry_body": (
            "Null is transmitting through the network using the same "
            "archive signature as Drukma.\n\n"
            "The two consciousnesses were assembled from the same "
            "original experiment. One chose silence. One chose control."
        ),
    },
    "fragment_null_transmission": {
        "name": "Null's Confession",
        "source": "Network Log",
        "entry_title": "Why the Kingdom Was Silenced",
        "entry_body": (
            "Null: \"Because the kingdom depended on a system it did not "
            "understand. Every failure threatened everything.\"\n\n"
            "It does not see itself as a destroyer. It sees itself as a "
            "guardian who chose control over trust."
        ),
    },

    # ---------------- Act VII — Deep Archive ----------------
    "fragment_player_identity": {
        "name": "The Architect's Apprentice",
        "source": "Deep Archive",
        "entry_title": "What You Carried",
        "entry_body": (
            "Operator identified: ARCHITECT'S APPRENTICE.\n"
            "Recovery protocol: AUTHORISED.\n"
            "Device: PERMISSION.\n"
            "Identity: SEALED BY OWN REQUEST.\n\n"
            "You did not fail the Core. You prepared a way to repair it "
            "without repeating the mistake that broke it."
        ),
    },
}


class StoryState:
    def __init__(self):
        self.memory_fragments = set()
        self.journal_entries = []
        self.story_flags = {}
        self.pending_fragment_popup = None   # (name, source) tuple or None
        self.popup_timer = 0

    def add_fragment(self, fragment_id):
        """Award a fragment. Adds a journal entry and queues a popup.
        Returns True if newly added, False if duplicate or unknown."""
        if fragment_id in self.memory_fragments:
            return False
        defn = FRAGMENT_DEFINITIONS.get(fragment_id)
        if not defn:
            print(f"WARNING: unknown fragment id {fragment_id}")
            return False

        self.memory_fragments.add(fragment_id)
        self.journal_entries.append({
            "title": defn["entry_title"],
            "body": defn["entry_body"],
            "source": defn["source"],
            "fragment_id": fragment_id,
        })
        self.pending_fragment_popup = (defn["name"], defn["source"])
        self.popup_timer = 240
        return True

    def add_journal_entry(self, title, body, source="Drukora"):
        """Add a free-form journal entry not tied to a fragment."""
        self.journal_entries.append({
            "title": title,
            "body": body,
            "source": source,
            "fragment_id": None,
        })

    def set_flag(self, key, value=True):
        self.story_flags[key] = value

    def get_flag(self, key, default=False):
        return self.story_flags.get(key, default)

    def has_fragment(self, fragment_id):
        return fragment_id in self.memory_fragments

    def fragment_count(self):
        return len(self.memory_fragments)

    def total_fragments(self):
        return len(FRAGMENT_DEFINITIONS)

    def to_dict(self):
        return {
            "memory_fragments": list(self.memory_fragments),
            "journal_entries": self.journal_entries,
            "story_flags": self.story_flags,
        }

    def from_dict(self, data):
        self.memory_fragments = set(data.get("memory_fragments", []))
        self.journal_entries = data.get("journal_entries", [])
        self.story_flags = data.get("story_flags", {})


# Global instance
STATE = StoryState()