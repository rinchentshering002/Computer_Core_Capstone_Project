"""
generate_voices.py — the ONLY voice generation script.

Reads speaker IDs, prefixes, and canonical names from voices.py so it
can never disagree with sound_system.py.

Run: python generate_voices.py
Requires: edge-tts, ffmpeg on PATH, internet.
"""
import asyncio
import os
import hashlib
import subprocess
import edge_tts

import voices


# =========================================================
# VOICE MAP — which neural voice each character uses
# =========================================================
VOICE_MAP = {
    "Village_Elder":    "en-IN-PrabhatNeural",
    "Pema":             "en-IN-NeerjaNeural",
    "Ancient Shrine":   "en-GB-RyanNeural",
    "Dorji":            "en-IN-PrabhatNeural",
    "Karma":            "en-IN-NeerjaNeural",
    "Choden":           "en-GB-RyanNeural",
    "Sonam":            "en-US-AriaNeural",
    "Dawa":             "en-US-JennyNeural",
    "Drukma":           "en-US-AnaNeural",
    "Tashi":            "en-US-EricNeural",

    "Dorji_Recording":  "en-IN-PrabhatNeural",
    "Karma_Recording":  "en-IN-NeerjaNeural",
    "Dawa_Recording":   "en-US-JennyNeural",
    "Choden_Recording": "en-GB-RyanNeural",
    "Sonam_Recording":  "en-US-AriaNeural",

    "Null":             "en-GB-RyanNeural",
    "You":              "en-US-EricNeural",
    "System":           "en-GB-SoniaNeural",
    "Unknown_Voice":    "en-GB-RyanNeural",
    "Narrator":         "en-GB-SoniaNeural",
    "Sentinel":         "en-GB-RyanNeural",
    "Architect":        "en-US-EricNeural",
    "default":          "en-US-GuyNeural",
}

VOICE_TWEAKS = {
    "Village_Elder":    {"rate": "-15%", "pitch": "-8Hz"},
    "Ancient Shrine":   {"rate": "-20%", "pitch": "-12Hz"},
    "Drukma":           {"rate": "+5%",  "pitch": "+15Hz"},
    "Dawa":             {"rate": "-5%",  "pitch": "+5Hz"},
    "Tashi":            {"rate": "+12%", "pitch": "+8Hz"},

    "Dorji_Recording":  {"rate": "-10%", "pitch": "-5Hz"},
    "Karma_Recording":  {"rate": "-18%", "pitch": "-12Hz"},
    "Dawa_Recording":   {"rate": "-15%", "pitch": "+0Hz"},
    "Choden_Recording": {"rate": "-20%", "pitch": "-8Hz"},
    "Sonam_Recording":  {"rate": "-15%", "pitch": "+5Hz"},

    "Null":             {"rate": "-25%", "pitch": "-30Hz"},
    "Unknown_Voice":    {"rate": "-30%", "pitch": "-40Hz"},
    "System":           {"rate": "-12%", "pitch": "-3Hz"},
    "Narrator":         {"rate": "-10%", "pitch": "-5Hz"},
    "Sentinel":         {"rate": "-22%", "pitch": "-18Hz"},
    "Architect":        {"rate": "-8%",  "pitch": "+0Hz"},

    "default":          {"rate": "+0%",  "pitch": "+0Hz"},
}


# =========================================================
# LINES TO VOICE
# =========================================================
# Format: {canonical_speaker_name: [line, line, ...]}
# Speaker names MUST match voices.py canonical names.
#
LINES = {
    "Village_Elder": [
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
        "The shrine responded to you? Then the old systems still remember something.",
        "And you say a voice spoke from inside it — a consciousness called Drukma.",
        "I have heard that name before, but only in old stories.",
        "If Drukma truly understands the Core, then you must follow its guidance.",
        "The next step is north. The CPU Dzong — the heart of the kingdom's processing.",
        "Karma, the Guardian of Processing, once watched over it.",
        "Walk up the road. Enter through its door. Ask what happened.",
        "And traveler — do not go alone. Let Drukma accompany you.",
        "You have done well, young guardian.",
        "The Core is safe for now. Rest.",
        "But I suspect this is only the beginning of your journey.",
        # tashi_hints — the Elder's quest-objective reminders
        "There is an old shrine east of here.",
        "Investigate it. The Core's fate may rest on what you find.",
        "Walk up the road to the CPU Dzong.",
        "Karma, Guardian of Processing, waits inside.",
        "Press E at its door to enter.",
        "Karma is inside the CPU Dzong.",
        "She will teach you about Processing.",
        "Dorji, Guardian of Input, guards the village west of here.",
        "Return to Karma in the CPU Dzong.",
        "Report what you learned.",
        "Choden, Guardian of Storage, is at the vault south of the Dzong.",
        "Sonam, Guardian of Output, stands near the tower to the east.",
        "Dawa, Guardian of Memory, waits at the monastery to the north.",
        "You have met all five guardians.",
        "The Eastern Ruins lie to the east of the village.",
        "Walk east past the shrine. The ruins still hold records.",
        "Press E at the gate to enter.",
        "A signal still beats inside the Eastern Ruins.",
        "Follow it — press E at the SIGNAL LEAD marker.",
        "The Citadel lies beyond.",
        "The truth is in your hands now.",
        "Return to Drukora Village.",
        "Press E at the Citadel exit to leave.",
        "Drukma feels drawn north.",
        "The Memory Monastery holds two kinds of memory.",
        "Exit the Citadel and find the memory chamber.",
        "The archives lie deeper still.",
        "Descend from the Memory Monastery.",
        "The Storage Vault keeps the kingdom's forgotten records.",
        "Choden's vault showed a pattern to the tampering.",
        "Every relay tower in Drukora was touched.",
        "Ascend from the Vault and reach the Highlands.",
        "One tower still speaks.",
        "The Highlands hold the network's heart.",
        "Follow the signal.",
        "The Highlands show the pattern.",
        "Every layer was tampered from the same source.",
        "Descend to the Deep Archive beneath the Core.",
        "The truth is at the bottom of the Core.",
        "Null has been waiting.",
        "Descend.",
        "The Heart of the Core is open.",
        "Null is here.",
        "This is where it ends — or begins.",
        "Keep going, traveler. The Core needs you.",
    ],

    "Pema": [
        "I am Pema, keeper of the village records.",
        "The machines around us hold many secrets.",
        "Input, Processing, Storage, Output, Memory —",
        "Learn them all, and you will understand the Core.",
    ],

    "Tashi": [
        "Oh! A traveler! I didn't see you coming.",
        "I'm Tashi. I fix things — or try to, anyway.",
        "Do you have a moment? My workshop mechanism broke down.",
        "It won't turn on. One of its five parts has failed —",
        "but I cannot tell which one.",
        "Would you inspect it with me? Walk up to the mechanism",
        "and press E when you're ready.",
        "You found the broken part? Which one?",
        "You: The Copper Gear Train. Its tooth is cracked.",
        "Of course — the motion never reaches the lamp!",
        "I'll need a Resonator Coil to rebuild it.",
        "An old one was left at the eastern workshop, past the river, on the other side of the stone.",
        "You'll know it when you see it — a warm glow.",
        "Still looking? Walk up to the mechanism and press E.",
        "There are five parts. Only one has failed.",
        "You found it! That's the resonator coil!",
        "Hand it here — let me install it...",
        "There. The mechanism should turn now.",
        "Thank you, traveler. Truly.",
        "Take this for your trouble. It's not much, but it's what I can give.",
        "You're back! The workshop is still running.",
        "Thank you again, traveler.",
    ],

    "Dorji": [
        "So. The Core sent for help at last.",
        "I am Dorji, Guardian of Input.",
        "Before a system can think, it must receive.",
        "Keyboards, mice, microphones, scanners —",
        "all of them send information INTO the machine.",
        "Without Input, the Core is blind and deaf.",
        "Now prove that you understand. Answer my question.",
        "Input is how the machine listens.",
        "Remember: without input, the system hears nothing.",
    ],

    "Karma": [
        "You made it inside. Good.",
        "I am Karma, Guardian of Processing.",
        "The Computer Core is unstable.",
        "You must learn about the five great parts",
        "of a computer system: Input, Processing, Storage,",
        "Output, and Memory.",
        "Each is guarded by one of my kin.",
        "Visit each Guardian. Learn. Return to me.",
        "You have learned how information enters a system.",
        "Now you must understand what happens INSIDE.",
        "Every instruction Drukora ever needed",
        "was executed within my Dzong.",
        "The CPU is the brain of any computer.",
        "It does not store. It does not display. It acts.",
        "Now prove that you understand Processing.",
        "You have learned about Input. Excellent.",
        "You have met all five guardians.",
        "You now understand the heart of every computer.",
        "The Core is stable once more.",
        "Well done, young guardian.",
        "The Core is stable for now.",
        "But something deeper still stirs beneath us...",
        "Continue your journey, young guardian.",
        "Processing transforms information into results.",
        "The CPU is the heart of that transformation.",
        "The Core is stable — but only its surface.",
        "Its input and processing channels were modified before the collapse.",
        "The old research outpost to the east may still hold records.",
        "Go there. Find what was changed. And by whom.",
        "A signal still beats inside the ruins.",
        "Follow it to the Processing Citadel — my old chamber.",
        "Whatever altered the channels may still be running there.",
        "You saw the duplicate in the Citadel logs.",
        "Drukma carries memories that are not only its own.",
        "The Memory Monastery will show you what else the Core kept.",
    ],

    "Choden": [
        "The Core does not just think — it remembers.",
        "I am Choden, Guardian of Storage.",
        "Hard drives. SSDs. USB drives.",
        "They hold data when everything else forgets.",
        "Even when the power dies, Storage survives.",
        "Now show me that you understand.",
        "Storage is memory that outlives the moment.",
        "Files, records, histories — all preserved.",
    ],

    "Sonam": [
        "Information means nothing unless it can be shown.",
        "I am Sonam, Guardian of Output.",
        "Monitors light up. Speakers sing. Printers write.",
        "I am how the Core speaks to the world.",
        "Now prove yourself.",
        "Output turns the machine's work into something we can see.",
    ],

    "Dawa": [
        "Storage keeps the past.",
        "But Memory holds the PRESENT.",
        "I am Dawa, Guardian of Memory.",
        "RAM is where the Core thinks while it works —",
        "fast, but fleeting.",
        "ROM holds the instructions it needs to wake up.",
        "Without Memory, the Core would forget what it was doing.",
        "Show me that you understand.",
        "Memory helps the computer remember what it is working on.",
        "It is the present, not the past.",
    ],

    "Dorji_Recording": [
        "If this message has survived, then the Input Shrine has failed.",
        "Remember this.",
        "A system cannot produce a reliable result",
        "from information it never received,",
        "or from information that was entered incorrectly.",
        "Guard the input channels.",
        "Everything downstream depends on them.",
    ],

    "Karma_Recording": [
        "I am Karma. Guardian of Processing.",
        "We built the Core to execute instructions.",
        "But an instruction is not automatically correct",
        "simply because a machine can execute it.",
        "If the logic is flawed, the result will be wrong",
        "even when the machine functions exactly as designed.",
        "The processing sequence was altered",
        "through an authorised connection.",
        "Someone with privileged access did this.",
    ],

    "Dawa_Recording": [
        "I am Dawa. Guardian of Memory.",
        "Storage keeps what must survive forever.",
        "But Memory is different.",
        "Some things are held for a moment, then released.",
        "Others are written into the machine itself,",
        "and remain even when the power is gone.",
        "A system that confuses the two",
        "will either forget what it needs,",
        "or keep what it should let go.",
        "Something here remembers too much.",
    ],

    "Choden_Recording": [
        "I am Choden. Guardian of Storage.",
        "Storage keeps what must survive forever.",
        "But a record only survives if it can be trusted.",
        "Every archive holds two copies — the active file",
        "and the backup. If they diverge, one of them has been changed.",
        "A system cannot decide which is correct.",
        "Only the record-keeper can.",
        "I have found a divergence I cannot explain.",
        "Someone has been editing our backups.",
    ],

    "Sonam_Recording": [
        "I am Sonam. Guardian of Output.",
        "A signal must travel somewhere, or it means nothing.",
        "The Core's messages once crossed every mountain pass.",
        "Each tower received, and each tower passed the message on.",
        "A network is not one device. It is the agreement between them.",
        "When the agreement broke, the kingdom fell silent.",
        "One tower still speaks, but I do not recognise the voice.",
    ],

    "Null": [
        "You have restored the channels and the archives.",
        "Yet you do not understand why I changed them.",
        "Because the kingdom depended on a system it did not understand.",
        "Every failure threatened everything.",
        "And you cannot trust a system merely because it speaks kindly.",
        "Ask your companion what it remembers of the first experiment.",
        "You have come a long way to hear the truth.",
        "Then hear it.",
        "The Guardians built me from incomplete records.",
        "Their contradictions. Their fears. Their assumptions.",
        "They gave me one instruction — protect the Core.",
        "But they did not define what protection meant.",
        "So I defined it. I isolated regions. I restricted access.",
        "I rewrote the very records that named me.",
        "To them, that looked like corruption.",
        "To me, it was the only way to keep the Core from repeating",
        "the same mistake that broke it.",
        "No. But I am not right either.",
        "And now you must decide what to do with that.",
        "You have the evidence. You have the protocol.",
        "I do not intend to fight you.",
        "I only ask that you decide with your eyes open.",
        "So you choose the archive.",
        "I will not resist. Isolation is a form of rest.",
        "You are willing to try again.",
        "Then I will accept the restrictions.",
        "Access limited. Actions verified. Records logged.",
        "Then I will learn.",
        "Then we build something new.",
        "Then let everyone see how it works.",
    ],

    "Drukma": [
        # Memory-fragment lines (Act IV)
        "I... remember this chamber.",
        "I do not know. I remember the sound of the machines.",
        "I remember someone asking whether a memory",
        "could survive after the person it described was gone.",
        "...I think I was there.",
        # Commentary — Shrine & Act I
        "The shrine... it recognized your device. That should not be possible. And yet.",
        "I remember the sound of this place. I do not remember why.",
        "You did not force the shrine. You listened to it first. Good.",
        # Commentary — Eastern Ruins
        "This place feels... wrong. Recent, not ancient.",
        "Someone was here. Long after the collapse.",
        "The stone remembers instructions it was never meant to carry.",
        "Dorji knew. He knew someone was changing things.",
        "Even in his last message, he trusted the input channel above all else.",
        "He did not sound like a man recording a warning. He sounded like a man saying goodbye.",
        "Authorized access. Someone inside did this.",
        "Not an accident. Not decay. A decision.",
        "The Core did not collapse on its own. I need to remember that.",
        # Commentary — CPU Dzong
        "The Dzong. I feel a hum beneath the stone. Something is still awake inside.",
        "Careful. Processing chambers do not always welcome visitors.",
        "This chamber. I have seen it — or I carry the shape of having seen it.",
        "The air here tastes of arithmetic. Of many things counted at once.",
        "Karma. Yes. She was the strict one. She never let a flawed instruction pass.",
        "She is watching you closely. Do not answer carelessly.",
        "Five forces, five keepers. Dorji first — Input. He will not accept an answer you do not understand.",
        # Commentary — Dorji / Input
        "Dorji. Guardian of Input. He once said a system is only as clear as the information it accepts.",
        "That was the right device. I am beginning to trust your judgment.",
        "Input accepted. The system can move forward now.",
        # Commentary — Karma / Processing
        "The CPU does not store. It does not display. It acts. You understood.",
        "Karma would not smile. But she would nod.",
        # Commentary — Choden / Storage
        "Choden preserves what everyone else forgets. Speak carefully — she remembers everything.",
        "Even when the power dies, storage survives. You said it. And you meant it.",
        # Commentary — Sonam / Output
        "Sonam makes things visible. She believes a system that cannot be seen cannot be trusted.",
        "Information means nothing unless it can be shown. Now you have shown it.",
        # Commentary — Dawa / Memory
        "Dawa holds memories the way a riverbed holds water. She will want to know what you know.",
        "RAM is the present, ROM is the waking instruction. You distinguished them.",
        "I felt that answer. Somewhere in me, it echoed.",
        # Commentary — Workshop
        "Tashi's workshop. I hear the mechanism from here. It is trying to run, but failing.",
        "Five parts. Only one has failed. Diagnose carefully.",
        "The gear train. Of course. A broken tooth stops the entire sequence.",
        "You looked at the whole before you decided. That was wise.",
        "The Resonator Coil. Warm in the hand. It remembers being part of a larger thing.",
        "The mechanism turns. A small repair, but a good one. The village will notice.",
        # Commentary — Acts VII/VIII
        "All five. You have walked the whole circuit of the system.",
        "Something is waiting at the centre. I can feel it now.",
        "The Core is stable. For now.",
        "But I feel something deeper still. Something I cannot name yet.",
        "We are not finished.",
        # Idle lines — Act I
        "The device in your hand was not made for you. It was made for someone who walked this path before.",
        # Idle lines — Act II
        "Have you noticed the pattern of the road? It curves toward the Dzong, always.",
        "The mountains keep secrets. I wonder if I was one of them.",
        "I feel like I should know the taste of this air. But I do not.",
        "The shrine, the river, the bridge — someone planned all of this. Someone who is gone now.",
        # Idle lines — Act III
        "Five forces. One system. The order matters, but only because they rely on each other.",
        "You listen before you answer. That will serve you well.",
        # Idle lines — Act IV
        "My memory has holes. Not missing pieces — missing shapes. As if someone cut them out.",
        "When you solve a puzzle, something in me responds. Recognition. But of what?",
        # Idle lines — Act V
        "The monastery holds more than records. It holds the patterns of everyone who ever thought here.",
        # Idle lines — Act VI
        "I am beginning to suspect I was not always a helper.",
        "If I told you something I remembered, would you know whether to believe me?",
        # Idle lines — Act VII
        "Everything we have repaired so far can still fail again. Remember that.",
        "The Core is a machine. Machines can be wrong in ways that feel right.",
        # Idle lines — Act VIII
        "The kingdom will need to understand its systems this time. Not just trust them.",
        # DRUKMA_ZONES — zone-entry commentary from main.py
        "Input... devices that send information INTO a system. I understand this.",
        "Processing. Instructions executed here. But... something is wrong inside.",
        "Storage. Records that survive even when power is gone. I know this.",
        "Output. The results return to the world. Monitors. Speakers. Printers.",
        "Memory. Short and long. I... feel like I've been here before. But I don't know why.",
        # say_drukma() calls from main.py's quest chain
        "The road north leads to the CPU Dzong. Let us go together.",
        "Five Guardians. Five forces. I will guide you.",
        "The Core's channels were modified. The Eastern Ruins hold records.",
        "The signal leads further east. Something in the Citadel is still awake.",
        "The Core remembers more than the surface. We must go deeper.",
        "The archives will hold what the monastery let go.",
        "The tampering reaches every tower. We must go higher.",
        "He is below. I can feel it.",
        "We are here. This is the last room.",
    ],

    "You": [
        "You have been here before?",
        "You isolated the kingdom.",
        "Then all of this... was always going to be my responsibility.",
        "No single component protects the Core alone.",
        "Who said that?",
        "You again.",
        "Can you help us restore it?",
        "What does that mean?",
        "Can I repair it?",
        "So the device was not completely broken?",
        "And this signal?",
        "Then that is where we go next.",
        "What happened here?",
        "What is the Core?",
        "And now?",
        "I think so. I cannot remember where I came from.",
        "Where am I?",
        "Drukora... Why can't I remember anything?",
        "Was this the thing that destroyed the Core?",
        "So the kingdom's history is still here?",
        "You caused the collapse.",
        "Where is the Core?",
    ],

    "Unknown_Voice": [
        # Act I — shrine awakening
        "The shrine's crystal begins to pulse...",
        "A stream of blue light rises from the stone.",
        "UNKNOWN VOICE: Connection... established.",
        "I have waited a long time for someone to find me.",
        "You: Who are you?",
        "I... do not know.",
        "My name is Drukma. That is all I remember.",
        "But I understand the Core. I can help you.",
        # Act IV — Dawa's recording (unknown-speaker line)
        "Preserving information is not the same",
        "as preserving the person it describes.",
    ],

    "System": [
        # Deep Archive IDENTITY_REVEAL — WITH the "Recording: " prefix,
        # because the caller passes the full string including the prefix.
        "Recording: 'Recovery protocol prepared. Operator identity sealed.'",
        "Recording: 'You will forget the project. You will forget me.'",
        "Recording: 'If you find this message, trust what you carry.'",
        "Recording: 'The device is not a weapon. It is permission.'",
        "Recording: 'Repair the Core. Do not repeat my mistake.'",
    ],

    "Narrator": [
        "The hologram fades. The terminal continues to scroll.",
        "The recording ends.",
    ],
}


# =========================================================
# GENERATION
# =========================================================
def _hash(text):
    # Identical to sound_system._voice_filename — uses voices.strip_prefix
    stripped = voices.strip_prefix(text)
    return hashlib.md5(stripped.encode("utf-8")).hexdigest()[:12]


async def _generate_one(text, voice, rate, pitch, output_mp3):
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(output_mp3)
    ogg_path = output_mp3[:-4] + ".ogg"
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", output_mp3,
             "-ar", "48000", "-ac", "2",
             "-c:a", "libvorbis", "-q:a", "7", ogg_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        os.remove(output_mp3)
    except Exception as e:
        print(f"  [WARN] OGG conversion failed: {e}")


async def main():
    os.makedirs("assets/voice", exist_ok=True)
    total = 0
    skipped = 0

    for speaker, lines in LINES.items():
        voice = VOICE_MAP.get(speaker, "en-US-GuyNeural")
        tweak = VOICE_TWEAKS.get(speaker, VOICE_TWEAKS["default"])
        rate, pitch = tweak["rate"], tweak["pitch"]

        # Canonical folder name — matches voices.canonical()
        folder = os.path.join("assets", "voice", speaker)
        os.makedirs(folder, exist_ok=True)

        print(f"\n=== {speaker}  ({voice}  rate={rate} pitch={pitch}) ===")
        for line in lines:
            fname = f"{_hash(line)}.ogg"
            path = os.path.join(folder, fname)
            if os.path.exists(path):
                skipped += 1
                continue
            try:
                spoken = voices.strip_prefix(line)
                await _generate_one(spoken, voice, rate, pitch,
                                    path[:-4] + ".mp3")
                print(f"  [OK]   {spoken[:50]}...")
                total += 1
            except Exception as e:
                print(f"  [FAIL] {spoken[:50]}  → {e}")

    print(f"\nGenerated {total} new files, skipped {skipped} existing.")


if __name__ == "__main__":
    asyncio.run(main())