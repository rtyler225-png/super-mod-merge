# Halo Wars: Definitive Edition — Map Management & Testing Guide

This guide explains how maps are registered, the engine mechanics behind map loading, and how to safely toggle or isolate map pools without ever causing crashes or touching files outside the mod directory.

---

## ⚠️ The Two Golden Rules of Map Editing

### 1. NEVER Comment Out `<ScenarioInfo>` Tags (Crash at `0x5BD184` / `0x40`)
When you launch the game, it reads your profile (`savegame/save.sav`) which stores the index of your last-played map for 1v1, 2v2, and 3v3.
- If maps are commented out with `<!-- ... -->`, the total scenario count drops (e.g. 125 down to 64).
- If your profile has a saved map index `>= total_count` (such as map 76), the engine's array lookup returns `nullptr`.
- The engine executes `mov edx, [rdx + 0x40]` on `nullptr`, crashing instantly with an Access Violation (`0xC0000005`) on launch.
- **Steam Cloud** syncs `save.sav` on launch, so deleting `save.sav` does not fix this.
- **Solution**: Keep all 125 `<ScenarioInfo>` entries in `data/scenariodescriptions.xml`. Use `Type="Development"` to hide maps instead of commenting them out.

### 2. Every Player Category (1v1, 2v2, 3v3) Must Have AT LEAST 1 Active Map (Crash at `0xD8614` / `0x50`)
When opening the Skirmish menu, the engine initializes default map selections for 2-player (1v1), 4-player (2v2), and 6-player (3v3) game modes (`xgameFinal.exe + 0xD84A0`).
- If ANY category has **0 active maps**, the check `if (selectedIndex >= mapCount)` tests `0 >= 0`, which is true.
- It branches to an error handler that fails to set the scenario pointer (`r8 = 0`).
- The engine then executes `mov ecx, dword ptr [r8 + 0x50]`, crashing with an **Access Violation (`0xC0000005`) reading address `0x0000000000000050`**!
- **Solution**: Whenever isolating a specific category (e.g. testing only 1v1), always leave **at least 1 active map** in 2v2 and 3v3 (e.g. Beasley's Plateau for 2v2, Exile for 3v3).

---

## How the Engine Menu Filter Works

The game engine filters maps for the lobby at `xgameFinal.exe + 0x5BA879`:
```x86asm
cmp dword ptr [map + 0x50], 1   ; 1 = "Final"
jne skip_map                    ; Skips any map that is not Final (e.g. Development = 3)
```

- **`Type="Final"` (or `Type="DLC"`)**: Displayed in the Skirmish Lobby menu.
- **`Type="Development"`**: Loaded into the engine's internal map array (preventing out-of-bounds startup crashes), but **completely hidden from the Skirmish menu**.

---

## Quick Presets

### 1. Preset: All Maps Active (Default Release)
All 63 Skirmish maps are set to `Type="Final"`.
To apply, run in PowerShell from the mod directory:
```powershell
python -c "
import re
with open('data/scenariodescriptions.xml', 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.splitlines()
head, tail = lines[:64], lines[64:]
new_tail = [re.sub(r'Type=\"Development\"', 'Type=\"Final\"', l) if '<ScenarioInfo' in l and 'Labyrinth_E3' not in l else l for l in tail]
with open('data/scenariodescriptions.xml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(head + new_tail))
print('All maps activated.')
"
```

### 2. Preset: 1v1 Focus (All 22 1v1 Maps Active + 1 Placeholder in 2v2/3v3)
All 22 1v1 maps active. 2v2 has Beasley's Plateau (1 map) and 3v3 has Exile (1 map) to satisfy Rule #2:
```powershell
python -c "
import re
with open('data/scenariodescriptions.xml', 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.splitlines()
head, tail = lines[:64], lines[64:]
new_tail = []
for l in tail:
    if '<ScenarioInfo' in l:
        m = re.search(r'MaxPlayers=\"(\d+)\"', l)
        mp = m.group(1) if m else '0'
        if mp == '2':
            l = re.sub(r'Type=\"[^\"]+\"', 'Type=\"Final\"', l)
        elif mp == '4':
            l = re.sub(r'Type=\"[^\"]+\"', 'Type=\"Final\"' if 'beasleys_plateau\\\\beasleys_plateau.scn' in l else 'Type=\"Development\"', l)
        elif mp == '6':
            l = re.sub(r'Type=\"[^\"]+\"', 'Type=\"Final\"' if 'exile\\\\exile.scn' in l else 'Type=\"Development\"', l)
    new_tail.append(l)
with open('data/scenariodescriptions.xml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(head + new_tail))
print('1v1 focus active.')
"
```

### 3. Preset: Exactly 1 Active Map per Category (Blood Gulch, Beasley's Plateau, Exile)
For minimal UI testing to avoid Scaleform list limits:
```powershell
python -c "
import re
keep = ['blood_gulch\\\\blood_gulch.scn', 'beasleys_plateau\\\\beasleys_plateau.scn', 'exile\\\\exile.scn']
with open('data/scenariodescriptions.xml', 'r', encoding='utf-8') as f:
    text = f.read()
lines = text.splitlines()
head, tail = lines[:64], lines[64:]
new_tail = []
for l in tail:
    if '<ScenarioInfo' in l:
        if any(k in l for k in keep):
            l = re.sub(r'Type=\"[^\"]+\"', 'Type=\"Final\"', l)
        else:
            l = re.sub(r'Type=\"[^\"]+\"', 'Type=\"Development\"', l)
    new_tail.append(l)
with open('data/scenariodescriptions.xml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(head + new_tail))
print('1 map per category active.')
"
```

---

## Map Inventory Overview

All **125 scenarios** registered in `data/scenariodescriptions.xml`:
- **Campaign / Dev / Tutorial Scenarios**: 61 entries
- **1v1 Skirmish Maps**: 22 entries (7 Vanilla + 15 Modded)
- **2v2 Skirmish Maps**: 21 entries (7 Vanilla + 13 Modded + 1 Dev)
- **3v3 Skirmish Maps**: 21 entries (4 Vanilla + 17 Modded)

### 1v1 Maps (2 Players)
- **Vanilla (7)**: Blood Gulch, Barrens, Blood River, Chasms, Pirth Outskirts, Release, Tundra
- **Modded (15)**: Arcadia Embassy, Arcadia Outskirts, Ascension, Black Ice, Closed Circuit, Containment, Desolation, Dome of Night, Feign River, Flash Freeze, Gateway, Graveyard, Nighttime Pass, Release Night, Whiteout

### 2v2 Maps (4 Players)
- **Vanilla (7)**: Beasley's Plateau, Crevice, Labyrinth, Memorial Basin, Repository, Terminal Moraine, The Docks
- **Modded (13)**: Arcadian Wetlands, Assembly, Badlands, Bloodbath, Castillas Retreat, District 17, Embers, Nightmare, Oceanside, Old Mombasa, Overrun, Ruins, Winter Walls

### 3v3 Maps (6 Players)
- **Vanilla (4)**: Exile, Fort Deen, Frozen Valley, Glacial Ravine
- **Modded (17)**: Anthrax Isle, Arctic Pass, Death Valley, Dig Site, Encroachment, Entanglement, Erandus, Fang Peak, Frigid Fortress, Installation 02, Plague Lands, Reclaimed, Rolling Hills, Sandstorm, The Last Bastion, Whiteout 3v3, Winter Walls 3v3
