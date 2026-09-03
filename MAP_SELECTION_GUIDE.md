# Halo Wars: Definitive Edition — Map Management & Testing Guide

This guide explains how maps are registered, the engine mechanics behind map loading, and how to safely toggle or isolate map pools without ever causing crashes or touching files outside the mod directory.

---

## ⚠️ Critical Rule: NEVER Comment Out `<ScenarioInfo>` Tags

### Why Did Commenting Out Maps Crash the Game?
When you launch *Halo Wars: Definitive Edition*, the game reads your profile from `savegame/save.sav`. This file stores the index of your last-played map for **each player category separately** (1v1, 2v2, and 3v3).

1. In `data/scenariodescriptions.xml`, there are **125 total scenario entries** registered.
2. When maps were commented out using XML comment tags (`<!-- ... -->`), the XML parser completely skipped them, reducing the total map count to **64**.
3. On startup, the game engine loops through each category:
   - It reads your saved map index from `save.sav` (e.g. index **76**).
   - It checks: `if (savedIndex >= scenarioCount) return nullptr;`
   - With only 64 maps, index 76 is out of bounds (`76 >= 64`), returning a null pointer.
   - The engine immediately executes `mov edx, [rdx + 0x40]` on that null pointer, crashing with an **Access Violation (`0xC0000005`)** at `xgameFinal.exe + 0x5BD184`!

### Why Deleting `save.sav` Doesn't Work
When Steam Cloud is enabled for Halo Wars DE, deleting `save.sav` from the disk has no effect: Steam immediately re-downloads the cloud copy before launching `xgameFinal.exe`, restoring the saved map index 76.

> **RULE**: **NEVER comment out or delete `<ScenarioInfo>` lines from `scenariodescriptions.xml`.**  
> All 125 entries must remain present in the XML so that any saved index in any profile remains in-bounds.

---

## The Safe Way to Hide / Isolate Maps: Use `Type="Development"`

The engine contains a built-in lobby filter at `xgameFinal.exe + 0x5BA879`:
```x86asm
cmp dword ptr [map + 0x50], 1   ; 1 = "Final"
jne skip_map                    ; Skips any map that is not Final (e.g. Development = 3)
```

- **`Type="Final"` (or `Type="DLC"`)**: Displayed in the Skirmish Lobby menu.
- **`Type="Development"`**: Loaded into the engine's internal map array (preventing any out-of-bounds crashes), but **completely hidden from the Skirmish menu**.

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
# Set all skirmish maps (after line 64) to Final
lines = text.splitlines()
head, tail = lines[:64], lines[64:]
new_tail = [re.sub(r'Type=\"Development\"', 'Type=\"Final\"', l) if '<ScenarioInfo' in l and 'Labyrinth_E3' not in l else l for l in tail]
with open('data/scenariodescriptions.xml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(head + new_tail))
print('All maps activated.')
"
```

### 2. Preset: Only 1v1 Maps Active (Hide 2v2 & 3v3)
All 1v1 maps (22 maps) remain `Type="Final"`. All 2v2 and 3v3 maps are set to `Type="Development"`.
To apply, run in PowerShell from the mod directory:
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
        if 'MaxPlayers=\"2\"' in l:
            l = re.sub(r'Type=\"Development\"', 'Type=\"Final\"', l)
        else:
            l = re.sub(r'Type=\"(Final|DLC)\"', 'Type=\"Development\"', l)
    new_tail.append(l)
with open('data/scenariodescriptions.xml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(head + new_tail))
print('Only 1v1 maps active.')
"
```

### 3. Preset: Exactly 1 Active Map per Category (Blood Gulch, Beasley's Plateau, Exile)
For minimal UI testing to completely avoid Scaleform list limits:
To apply, run in PowerShell from the mod directory:
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
            l = re.sub(r'Type=\"Development\"', 'Type=\"Final\"', l)
        else:
            l = re.sub(r'Type=\"(Final|DLC)\"', 'Type=\"Development\"', l)
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
