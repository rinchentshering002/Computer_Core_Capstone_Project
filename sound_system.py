"""
sound_system.py — synthesized SFX + character voice playback.

Voice profiles, prefixes, and canonical names are owned by voices.py.
Do not add speakers or prefixes here — edit voices.py instead.
"""

import pygame
import math
import random
import sys
import os
import hashlib
import voices

IS_BROWSER = sys.platform == "emscripten"

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("WARNING: numpy not found — sounds disabled")

# Must match the mixer pre_init in main.py AND the re-encoded OGG files
SAMPLE_RATE = 48000


# =========================================================
# BASIC TONE GENERATORS
# =========================================================
def _envelope(samples, attack=0.01, decay=0.15, sustain=0.5, release=0.2):
    n = len(samples)
    a = int(n * attack)
    d = int(n * decay)
    r = int(n * release)
    s = max(0, n - a - d - r)
    env = np.concatenate([
        np.linspace(0, 1, a) if a > 0 else np.array([]),
        np.linspace(1, sustain, d) if d > 0 else np.array([]),
        np.full(s, sustain) if s > 0 else np.array([]),
        np.linspace(sustain, 0, r) if r > 0 else np.array([]),
    ])
    env = env[:n] if len(env) >= n else np.pad(env, (0, n - len(env)))
    return samples * env


def _sine(freq, duration, volume=0.4):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    return _envelope(np.sin(2 * math.pi * freq * t) * volume)


def _triangle(freq, duration, volume=0.25):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    wave = (2 / np.pi) * np.arcsin(np.sin(2 * math.pi * freq * t)) * volume
    return _envelope(wave, attack=0.005, decay=0.05, sustain=0.6, release=0.08)


def _square(freq, duration, volume=0.25, duty=0.5):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    wave = np.where((t * freq) % 1.0 < duty, 1.0, -1.0) * volume
    return _envelope(wave, attack=0.005, decay=0.05, sustain=0.7, release=0.05)


def _noise(duration, volume=0.2):
    n = int(SAMPLE_RATE * duration)
    wave = np.random.uniform(-1, 1, n) * volume
    return _envelope(wave, attack=0.001, decay=0.05, sustain=0.1, release=0.05)


def _chord(freqs, duration, volume=0.3):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    wave = np.zeros(n)
    for f in freqs:
        wave += np.sin(2 * math.pi * f * t)
    wave /= len(freqs)
    wave *= volume
    return _envelope(wave)


# =========================================================
# FORMANT VOWEL SYNTHESIS (the "voice" part)
# =========================================================
VOWELS = {
    "a": [(730, 90, 1.0), (1090, 110, 0.5), (2440, 140, 0.3)],
    "e": [(530, 90, 1.0), (1840, 110, 0.5), (2480, 140, 0.3)],
    "i": [(270, 70, 1.0), (2290, 110, 0.6), (3010, 140, 0.3)],
    "o": [(570, 90, 1.0), (840, 100, 0.7), (2410, 140, 0.3)],
    "u": [(300, 80, 1.0), (870, 100, 0.5), (2240, 140, 0.3)],
}


def _formant_gain(freq, formants):
    gain = 0.0
    for (f_center, bandwidth, peak) in formants:
        d = (freq - f_center) / bandwidth
        gain += peak * math.exp(-d * d)
    return gain


def _voice_vowel(f0, duration, formant_name, volume=0.5, vibrato=True):
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, False)
    formants = VOWELS.get(formant_name, VOWELS["a"])

    if vibrato:
        f0_mod = f0 * (1.0 + 0.02 * np.sin(2 * math.pi * 5.0 * t))
        phase = 2 * math.pi * np.cumsum(f0_mod) / SAMPLE_RATE
    else:
        phase = 2 * math.pi * f0 * t

    wave = np.zeros(n)
    max_harmonic = max(1, int(4000 / f0))
    for h in range(1, max_harmonic + 1):
        harmonic_freq = f0 * h
        amp = _formant_gain(harmonic_freq, formants)
        if amp > 0.01:
            wave += amp * np.sin(phase * h)

    peak = np.max(np.abs(wave))
    if peak > 1e-6:
        wave = wave / peak
    wave *= volume

    return _envelope(wave, attack=0.03, decay=0.08, sustain=0.75, release=0.25)


def _to_sound(wave):
    wave = np.clip(wave, -1.0, 1.0)
    int_wave = (wave * 32767).astype(np.int16)
    stereo = np.column_stack([int_wave, int_wave])
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


# =========================================================
# CHARACTER VOICE PROFILES  (fallback beep bank)
# =========================================================
# Voice profiles are owned by voices.py — do not add speakers here.
# voices.beep_styles() returns {canonical_name: {f0, dur, vowel, vol,
# variance, vibrato}} for every character in the game.
VOICE_STYLES = voices.beep_styles()


# =========================================================
# SOUND REGISTRY
# =========================================================
SOUNDS = {}
ENABLED = False
_voice_channel = None


def _build_voice_variants(style):
    """Build 5 clips per character.

    Pitch and vowel are LOCKED to the character's profile. The only
    degree of freedom is a small pitch variance — a subtle breath, not
    a wobble. This is what keeps each character recognisable across
    plays."""
    variants = []
    base_f0  = style["f0"]
    dur      = style["dur"]
    vol      = style["vol"]
    vowel    = style["vowel"]       # LOCKED — no random vowel
    variance = style.get("variance", 0.02)
    use_vib  = style.get("vibrato", True)

    for i in range(5):
        pitch = base_f0 * (1.0 + (random.random() - 0.5) * 2 * variance)
        wave = _voice_vowel(pitch, dur, vowel, vol, vibrato=use_vib)
        variants.append(_to_sound(wave))
    return variants


def init():
    """Synthesize all sounds once at startup.
    In the browser, skip synthesis entirely because Pygbag doesn't support
    pygame.sndarray.make_sound() and pygame.mixer.Sound at all."""
    global ENABLED, _voice_channel

    if IS_BROWSER:
        ENABLED = True
        print("Browser mode: synthesized SFX disabled (using HTML5 Audio for voices)")
        return

    if not HAS_NUMPY:
        return
    try:
        _voice_channel = pygame.mixer.Channel(0)
        ENABLED = True

        # --- Footstep ---
        SOUNDS["step"] = _to_sound(_noise(0.06, volume=0.12))

        # --- Fallback blip ---
        SOUNDS["blip"] = _to_sound(_square(880, 0.04, volume=0.10))

        # --- Correct / Wrong ---
        SOUNDS["correct"] = _to_sound(np.concatenate([
            _sine(523, 0.10, 0.3), _sine(659, 0.10, 0.3), _sine(784, 0.20, 0.3)]))
        SOUNDS["wrong"] = _to_sound(np.concatenate([
            _square(220, 0.12, 0.20, duty=0.3), _square(150, 0.18, 0.20, duty=0.3)]))

        # --- Reward jingle ---
        SOUNDS["reward"] = _to_sound(np.concatenate([
            _sine(523, 0.08, 0.25), _sine(659, 0.08, 0.25),
            _sine(784, 0.08, 0.25), _sine(1047, 0.25, 0.25)]))

        # --- Quest fanfare ---
        SOUNDS["quest"] = _to_sound(np.concatenate([
            _chord([392, 494, 587], 0.15, 0.25),
            _chord([440, 554, 659], 0.25, 0.25)]))

        # --- UI ---
        SOUNDS["ui_open"]  = _to_sound(_sine(660, 0.08, 0.20))
        SOUNDS["ui_close"] = _to_sound(_sine(330, 0.08, 0.20))

        # --- Shrine awaken ---
        SOUNDS["shrine"] = _to_sound(np.concatenate([
            _sine(440, 0.15, 0.25), _sine(660, 0.15, 0.25), _sine(880, 0.30, 0.25)]))

        # --- Character voices (fallback beep) ---
        for name, style in VOICE_STYLES.items():
            SOUNDS[f"voice_{name}"] = _build_voice_variants(style)

        print(f"Synthesized {len(SOUNDS)} sound entries "
              f"({len(VOICE_STYLES)} character voices)")
    except Exception as e:
        print(f"Sound init failed: {e}")
        ENABLED = False


def play(name, volume=1.0):
    """Play a synthesized sound effect (desktop only)."""
    if not ENABLED:
        return
    if IS_BROWSER:
        return
    snd = SOUNDS.get(name)
    if snd is None:
        return
    if isinstance(snd, list):
        random.choice(snd).play()
    else:
        if volume != 1.0:
            ch = snd.play()
            if ch:
                ch.set_volume(volume)
        else:
            snd.play()


# =========================================================
# REAL VOICE LINE PLAYBACK
# =========================================================
_voice_cache = {}

# Prefixes are owned by voices.py — every prefix listed there is
# stripped before hashing. Do not add prefixes here.
SPEAKER_PREFIXES = voices.ALL_PREFIXES


def _strip_speaker_prefix(text):
    return voices.strip_prefix(text)


def _voice_filename(text):
    stripped = _strip_speaker_prefix(text)
    return hashlib.md5(stripped.encode("utf-8")).hexdigest()[:12] + ".ogg"


def _voice_path(speaker, text):
    # voices.canonical() maps every alias ("Elder", "Village Elder",
    # "village elder") to the same on-disk folder, so the same character
    # always resolves to the same voice files.
    folder = os.path.join("assets", "voice", voices.canonical(speaker))
    return os.path.join(folder, _voice_filename(text))


def stop_voice():
    """Stop whatever voice line is currently playing."""
    if IS_BROWSER:
        try:
            import platform
            platform.window.eval(
                "if (window.__lastVoice) { "
                "window.__lastVoice.pause(); "
                "window.__lastVoice.currentTime = 0; "
                "window.__lastVoice = null; }"
            )
        except Exception:
            pass
        return
    if _voice_channel is not None:
        _voice_channel.stop()


def play_voice(character_name):
    """Play the synthesized fallback beep — desktop only.
    In browser, skip because Sound objects aren't supported.

    Accepts any alias: play_voice("Village Elder") and
    play_voice("Village_Elder") resolve to the same voice."""
    if not ENABLED:
        return
    if IS_BROWSER:
        return
    canonical = voices.canonical(character_name)
    variants = SOUNDS.get(f"voice_{canonical}")
    if variants is None:
        variants = SOUNDS.get("voice_default")
    if not variants:
        return
    snd = random.choice(variants)
    try:
        if _voice_channel is not None:
            _voice_channel.stop()
            _voice_channel.play(snd)
        else:
            snd.play()
    except Exception:
        snd.play()


def play_line(speaker, text):
    """Play the recorded voice line for this (speaker, text) pair.
    Browser: HTML5 Audio via JS bridge.
    Desktop: pygame.mixer.Sound.
    Returns True if it played, False if no file was found."""
    if not ENABLED:
        print(f"[VOICE] sound_system disabled")
        return False

    path = _voice_path(speaker, text)
    if not os.path.isfile(path):
        print(f"[VOICE] missing: {path}")
        return False

    # ---- Browser path: HTML5 Audio ----
    if IS_BROWSER:
        try:
            import platform
            url = path.replace("\\", "/")
            js = (
                "(function(){"
                "if (window.__lastVoice) { window.__lastVoice.pause(); window.__lastVoice = null; }"
                f"var a = new Audio('{url}');"
                "a.volume = 0.9;"
                "a.play().catch(function(e){ console.log('audio blocked:', e); });"
                "window.__lastVoice = a;"
                "})();"
            )
            platform.window.eval(js)
            print(f"[VOICE] browser playing: {url}")
            return True
        except Exception as e:
            print(f"[VOICE] browser play failed: {e}")
            return False

    # ---- Desktop path: pygame.mixer.Sound ----
    key = (speaker, text)
    snd = _voice_cache.get(key)
    if snd is None:
        try:
            snd = pygame.mixer.Sound(path)
            _voice_cache[key] = snd
        except pygame.error as e:
            print(f"Could not load {path}: {e}")
            return False

    try:
        if _voice_channel is not None:
            _voice_channel.stop()
            _voice_channel.play(snd)
        else:
            snd.play()
        return True
    except Exception as e:
        print(f"Playback failed: {e}")
        return False