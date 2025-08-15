from __future__ import annotations

import re
from typing import Dict, Optional, Tuple


ACT1 = "Act 1"
ACT2 = "Act 2"
ACT3 = "Act 3"
ACT4 = "Act 4"
ACT5 = "Act 5"


CODES_TO_NAME: Dict[str, str] = {
    "1.1": "Blood Moor and Den of Evil",
    "1.2": "Cold Plains and The Cave",
    "1.3": "Burial Grounds, The Crypt, and The Mausoleum",
    "1.4": "Stony Field",
    "1.5": "Dark Wood and Underground Passage",
    "1.6": "Black Marsh and The Hole",
    "1.7": "The Forgotten Tower",
    "1.8": "Jail and Barracks",
    "1.9": "Cathedral and Catacombs",
    "1.10": "The Pit",
    "1.11": "Tristram",
    "1.12": "Moo Moo Farm",
    "2.1": "Sewers",
    "2.2": "Rocky Waste and Stony Tomb",
    "2.3": "Dry Hills and Halls of the Dead",
    "2.4": "Far Oasis",
    "2.5": "Lost City, Valley of Snakes, and Claw Viper Temple",
    "2.6": "Ancient Tunnels",
    "2.7": "Arcane Sanctuary",
    "2.8": "Tal Rasha's Tombs and Tal Rasha's Chamber",
    "3.1": "Spider Forest and Spider Cavern",
    "3.2": "Great Marsh",
    "3.3": "Flayer Jungle and Flayer Dungeon",
    "3.4": "Kurast Bazaar, Ruined Temple, and Disused Fane",
    "3.5": "Travincal",
    "3.6": "Durance of Hate",
    "4.1": "Outer Steppes and Plains of Despair",
    "4.2": "River of Flame and City of the Damned",
    "4.3": "Chaos Sanctuary",
    "5.1": "Bloody Foothills, Frigid Highlands and Abaddon",
    "5.2": "Glacial Trail and Drifter Cavern",
    "5.3": "Crystalline Passage and Frozen River",
    "5.4": "Arreat Plateau and Pit of Acheron",
    "5.5": "Nihlathak's Temple, Halls of Anguish, Halls of Pain, and Halls of Vaught",
    "5.6": "Ancient's Way and Icy Cellar",
    "5.7": "Worldstone Keep, Throne of Destruction, and Worldstone Chamber",
}

def _code_key(code: str) -> Tuple[int, int]:
    a, b = code.split(".")
    return int(a), int(b)

ACT_GROUPS: Dict[str, Tuple[str, ...]] = {
    ACT1: tuple(sorted([c for c in CODES_TO_NAME if c.startswith("1.")], key=_code_key)),
    ACT2: tuple(sorted([c for c in CODES_TO_NAME if c.startswith("2.")], key=_code_key)),
    ACT3: tuple(sorted([c for c in CODES_TO_NAME if c.startswith("3.")], key=_code_key)),
    ACT4: tuple(sorted([c for c in CODES_TO_NAME if c.startswith("4.")], key=_code_key)),
    ACT5: tuple(sorted([c for c in CODES_TO_NAME if c.startswith("5.")], key=_code_key)),
}

_NON_WORDS = re.compile(r"[^\w\s]+", flags=re.UNICODE)
_MULTI_WS = re.compile(r"\s+")

def normalize_name(name: str) -> str:
    s = name.strip().lower()
    if s.startswith("the "):
        s = s[4:]
    s = s.replace("&", "and")
    s = _NON_WORDS.sub(" ", s)
    s = _MULTI_WS.sub(" ", s).strip()
    return s

EN_TO_CODE: Dict[str, str] = {}
for code, title in CODES_TO_NAME.items():
    EN_TO_CODE[normalize_name(title)] = code
    if title.lower().startswith("the "):
        EN_TO_CODE[normalize_name(title[4:])] = code

def all_codes() -> Tuple[str, ...]:
    return tuple(sorted(CODES_TO_NAME.keys(), key=_code_key))

def codes_for_act(act_title: str) -> Tuple[str, ...]:
    return ACT_GROUPS.get(act_title, ())

def name_by_code(code: str) -> str:
    return CODES_TO_NAME.get(code, code)

def code_by_name(name: str) -> Optional[str]:
    return EN_TO_CODE.get(normalize_name(name))
