import json
import os
import sys

# Detect if we're running in Pygbag (browser WASM) vs desktop
IS_BROWSER = sys.platform == "emscripten"

SAVE_PATH = "savegame.json"
STORE_KEY = "the_core_save"

DEFAULT_STATE = {
    "player_xp": 0,
    "guardian_fragments": 0,
    "quest_title": "THE AWAKENING",
    "quest_objective": "Talk to the Village Elder",
    "quest_active": True,
    "quest_completed": False,
    "mission_bonus_awarded": False,
    "drukma_awake": False,
    "shrine_activated": False,
    "unlocked_locations": ["CPU Dzong"],
    "drukma_seen_zones": [],
    "current_scene": "village",
    "player_x": 485,
    "player_y": 485,
    "player_direction": "down",
    "story_state": {},
}

# ---------------------------------------------------------
# BROWSER STORAGE (localStorage via Pygbag)
# ---------------------------------------------------------
def _browser_save(json_str):
    try:
        import platform
        platform.window.localStorage.setItem(STORE_KEY, json_str)
        return True
    except Exception as e:
        print(f"Browser save failed: {e}")
        return False

def _browser_load():
    try:
        import platform
        return platform.window.localStorage.getItem(STORE_KEY)
    except Exception as e:
        print(f"Browser load failed: {e}")
        return None

def _browser_has_save():
    try:
        import platform
        return platform.window.localStorage.getItem(STORE_KEY) is not None
    except Exception:
        return False

def _browser_delete():
    try:
        import platform
        platform.window.localStorage.removeItem(STORE_KEY)
    except Exception:
        pass

# ---------------------------------------------------------
# DESKTOP STORAGE (filesystem)
# ---------------------------------------------------------
def _desktop_save(json_str):
    try:
        with open(SAVE_PATH, "w") as f:
            f.write(json_str)
        return True
    except Exception as e:
        print(f"Save failed: {e}")
        return False

def _desktop_load():
    if not os.path.isfile(SAVE_PATH):
        return None
    try:
        with open(SAVE_PATH, "r") as f:
            return f.read()
    except Exception as e:
        print(f"Load failed: {e}")
        return None

def _desktop_has_save():
    return os.path.isfile(SAVE_PATH)

def _desktop_delete():
    if os.path.isfile(SAVE_PATH):
        try:
            os.remove(SAVE_PATH)
        except Exception:
            pass

# ---------------------------------------------------------
# PUBLIC API (auto-selects browser or desktop)
# ---------------------------------------------------------
def has_save():
    if IS_BROWSER:
        return _browser_has_save()
    return _desktop_has_save()

def save_game(state):
    text = json.dumps(state, indent=2)
    if IS_BROWSER:
        ok = _browser_save(text)
    else:
        ok = _desktop_save(text)
    if ok:
        print("Game saved")
    return ok

def load_game():
    if IS_BROWSER:
        text = _browser_load()
    else:
        text = _desktop_load()
    if not text:
        return None
    try:
        data = json.loads(text)
        merged = DEFAULT_STATE.copy()
        merged.update(data)
        return merged
    except Exception as e:
        print(f"Parse failed: {e}")
        return None

def delete_save():
    if IS_BROWSER:
        _browser_delete()
    else:
        _desktop_delete()
    print("Save deleted")