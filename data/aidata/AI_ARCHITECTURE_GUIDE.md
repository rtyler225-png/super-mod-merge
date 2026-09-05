# Halo Wars: Definitive Edition — AI Architecture & Expansion Guide
**Mod**: Super Mod Merge  
**Location**: `data/aidata/AI_ARCHITECTURE_GUIDE.md`

This guide documents the skirmish AI system for `Super Mod Merge`. It provides the foundational knowledge, naming conventions, and workflows required for any human modder or AI assistant to maintain, modify, or add new leader AI personalities without breaking existing behaviors.

---

## 1. High-Level AI Architecture

Halo Wars Skirmish AI executes through a two-layer system:
1. **Master Router (`data/triggerscripts/skirmishai.triggerscript`)**:
   - Evaluates the player's selected leader at match initialization.
   - Activates the leader-specific triggerscript (e.g., `ai_cutter.triggerscript`, `ai_forge.triggerscript`, `ai_arbiter.triggerscript`).
2. **Leader Trigger Script (`data/triggerscripts/skirmishai/ai_<leader>.triggerscript`)**:
   - Manages tactical decision loops, power usage, retreat logic, and economy pacing.
   - Calls the engine effect `TableLoad(UserClassType, FileName, TableName)` to load:
     - **Build Strategy** from `data/aidata/buildlist_<leader>.ai`
     - **Train Strategy** from `data/aidata/trainlist_<leader>.ai`
     - **Tech Strategy** from `data/aidata/techs_<leader>.ai`

---

## 2. Table Schemas & Types

All AI strategy tables reside as XML files under `data/aidata/`.

### A. BuildingBuildList (`buildlist_<leader>.ai`)
- **UserClassType**: `3`
- **Root Element**: `<Table Name="..." Type="BuildingBuildList">`
- **Row Format**:
  ```xml
  <Row>
      <c>ProtoObjectName</c>       <!-- Building or upgrade proto-object -->
      <c>TargetCount</c>           <!-- Target cumulative quantity across all bases -->
      <c>BaseOrPriority</c>        <!-- Base slot / tier indicator (typically 1, 2, or 3) -->
  </Row>
  ```
- **Key ProtoObjects (UNSC)**:
  - `unsc_bldg_supplypad_01` (Supply Pad), `unsc_bldg_supplypad_02` (Heavy Supply Pad)
  - `unsc_bldg_reactor_01` (Reactor), `unsc_bldg_reactor_02` (Advanced Reactor)
  - `unsc_bldg_barracks_01` (Barracks), `unsc_bldg_vehicledepot_01` (Vehicle Depot), `unsc_bldg_airPad_01` (Air Pad)
  - `unsc_bldg_command_01` (Base Station / Expansion), `unsc_bldg_command_02` (Base Station Tier 2), `unsc_bldg_command_03` (Fortress)
  - `unsc_bldg_fieldArmory_01` (Field Armory), `unsc_bldg_turret_01` (Base Turret)

### B. SquadBuildList (`trainlist_<leader>.ai`)
- **UserClassType**: `1`
- **Root Element**: `<Table Name="..." Type="SquadBuildList">`
- **Row Format**:
  ```xml
  <Row>
      <c>ProtoSquadName</c>        <!-- Must be a valid trainable squad from squads.xml -->
      <c>DesiredCount</c>          <!-- Quantity desired in the AI's army pool -->
  </Row>
  ```
- **Crucial Rule**: Only list squads that can actually be trained at the leader's production buildings or base! For instance, in this mod ODSTs are leader drop powers or starting units, not trainable barracks units.
- **Universal UNSC Baseline**: The `"Standard"` baseline train list is designed to use **100% generic universal UNSC units** (Marines, Snipers, Rockets, Hellbringers, Medics, Scorpions, Warthogs, Cobras, Wolverines, Hornets, Pelicans) and omits leader-specific heroes (e.g. Jerome, Forge Warthog) so that this single baseline table can be copied cleanly across all UNSC leaders (Forge, Anders, Serina, etc.) without modification or missing squad crashes. Individual heroes or faction-unique units should be added in specialized personality tables (e.g. `ODSTRush`, `GrizzlyRoll`).

### C. TechUpgradeTable (`techs_<leader>.ai`)
- **UserClassType**: `2`
- **Root Element**: `<Table Name="..." Type="TechUpgradeTable">`
- **Row Format**:
  ```xml
  <Row>
      <c>TechName</c>              <!-- Tech identifier from techtree.xml -->
      <c>PrereqObjectType</c>      <!-- Required building or unit type present -->
      <c>Count</c>                 <!-- Required count (typically 1) -->
  </Row>
  ```


### D. Base Sockets vs. Perimeter Turrets
- **Interior Building Sockets**: A standard base provides up to 7 interior sockets (Outpost: 3 sockets, Station: 5 sockets, Fortress: 7 sockets). These host economy, tech, and production buildings (`supplypad`, `reactor`, `vehicledepot`, `barracks`, `airPad`, `fieldArmory`).
- **Perimeter Turret Sockets**: Every base has **4 dedicated perimeter turret sockets** that are completely separate from interior building sockets.
  - Turrets (`unsc_bldg_turret_01`, `cov_bldg_turret_01`) **do not consume interior sockets**!
  - To command the AI to build turrets, include entries in `buildlist_<leader>.ai`:
    ```xml
    <!-- Base 1 Turrets (4 perimeter sockets) -->
    <Row><c>unsc_bldg_turret_01</c><c>4</c><c>1</c></Row>
    <Row><c>unsc_bldg_turretAA_01</c><c>2</c><c>1</c></Row>
    <Row><c>unsc_bldg_turretAV_01</c><c>2</c><c>1</c></Row>
    ```
  - Without turret rows in the build list, the AI will leave all perimeter turret sockets empty for the entire match.

### E. Engine Production Limits & Counter-Unit Quotas
Inside `ai_<leader>.triggerscript`:
1. **Bid Limits**:
   - `TrnMaxNotApproved` (TriggerVar 3636, 6129, 6133): Caps unapproved/waiting squad bids. Default was 2 (aborting squad bidding whenever 2 bids were in flight). Increased to 15–20 to match Flood throughput.
   - `TrnMaxSquadBids` (TriggerVar 829, 6127, 6131): Hard ceiling on total active squad bids. Default was 8. Increased to 35–45 to keep dual-factories and queues saturated.
2. **Queue Limits (`BidSetQueueLimits`)**:
   - Trigger 411 default was `0 ms`, preventing buildings from queuing a 2nd unit while 1 is actively training. Set to `360000 ms` (6 minutes) to buffer factory queues.
3. **Loop Cadence**:
   - Squad loop (`Trigger 156`, Var 1018) and Building loop (`Trigger 160`, Var 1033) run on cycle timers. Lowered from 5000 ms to 1500 ms to rapidly fill empty base sockets and replenish army losses.
4. **Counter-Unit Quota (`InSuggestCapVar1`)**:
   - In Trigger 3043, when the AI scans an enemy unit type (e.g. enemy Air), it enters "COUNTER UNIT TIME" and calculates a counter (e.g. Wolverines).
   - Default cap was **20** (`InSuggestCapVar1 = 20`), which completely flooded vehicle depots and froze Scorpion production. Capped to **5** so the AI fields an anti-air detachment without starving out its main battle tanks.

---

## 3. Naming Conventions & Scoping

### The Baseline: `"Standard"`
To ensure modularity and keep the system bare and uniform across all leaders:
- Every leader's baseline build list, train list, and tech list is named simply **`"Standard"`**.
- **No Namespace Collisions**: The engine's `TableLoad` takes both `FileName` and `TableName`.
  - `TableLoad(FileName="buildlist_cutter.ai", TableName="Standard")`
  - `TableLoad(FileName="buildlist_forge.ai", TableName="Standard")`
  Because each leader specifies their own file name, tables named `"Standard"` never collide.
- Eliminates redundant prefix noise (e.g. avoid `Cutter_Standard_Build` when it is already in `buildlist_cutter.ai`).

### Expansion Personalities
When expanding a leader outward with alternative playstyles, use clean, descriptive personality names:
- Examples: `ODSTRush`, `FortressBoom`, `ElephantFOB`, `FastHog`, `GrizzlyRoll`, `CryoLock`.
- In `buildlist_<leader>.ai`: `<Table Name="ODSTRush" Type="BuildingBuildList">`
- In `trainlist_<leader>.ai`: `<Table Name="ODSTRush" Type="SquadBuildList">`

---

## 4. How Triggerscripts Interact with Tables

Inside `ai_<leader>.triggerscript`:
1. **Build Strategy**:
   - `TriggerVar 19030` (`SetBuildStrategy`) holds the target table name string.
   - `TriggerVar 19021` (`BuildStrategyName`) holds the currently loaded table name.
   - Trigger 2299 evaluates `BuildStrategyName != SetBuildStrategy`. When unequal, it calls `TableLoad` and updates `BuildStrategyName`.
2. **Train Strategy**:
   - `TriggerVar 19221` (`SetTrainStrategy`) holds the target table name string.
   - `TriggerVar 19219` (`TrainStrategyName`) holds the currently loaded table name.
   - Trigger 2313 evaluates `TrainStrategyName != SetTrainStrategy`. When unequal, it calls `TableLoad` and updates `TrainStrategyName`.
3. **Tech Strategy**:
   - `TriggerVar 18742` holds the tech table name (default: `"Standard"`).
   - Loaded at startup via Trigger 167 with `TableLoad`.

> [!WARNING]
> If a triggerscript requests a table name that does not exist in the corresponding `.ai` file, `TableLoad` returns `-1` (Table Not Found). This stalls the AI's build queue or train queue. All table names assigned to `SetBuildStrategy` or `SetTrainStrategy` must exist in the `.ai` files.

---

## 5. Workflow: Adding a New Personality to a Leader

Follow these exact steps to add a new personality:
1. **Open the Leader's AI Files**:
   - `data/aidata/buildlist_<leader>.ai`
   - `data/aidata/trainlist_<leader>.ai`
2. **Duplicate & Tweak the `"Standard"` Table**:
   - Copy `<Table Name="Standard" ...>` to a new table with your personality name (e.g., `<Table Name="ODSTRush" ...>`).
   - Adjust building order / unit counts. Ensure all units in the train list are trainable by that leader!
3. **Wire into `ai_<leader>.triggerscript`**:
   - Locate the strategy selection trigger (e.g., Trigger 1441 / opening strategy roll).
   - Add a branch or roll condition that copies your new personality name string (e.g. `"ODSTRush"`) to:
     - `SetBuildStrategy` (TriggerVar 19030)
     - `SetTrainStrategy` (TriggerVar 19221)
4. **Validate**:
   - Verify XML well-formedness using PowerShell `[xml](Get-Content <file>)`.
   - Test in-game.

---

## 6. Leader Rollout Status

| Leader | Civ | Current Status | Active Strategy Tables |
| :--- | :--- | :--- | :--- |
| **Captain Cutter** | UNSC | **Baseline "Standard" Active** | `Standard` (Build, Train, Tech) |
| **Sergeant Forge** | UNSC | Pending Rollout | Legacy Tables |
| **Professor Anders** | UNSC | Pending Rollout | Legacy Tables |
| **Serina** | UNSC | Pending Rollout | Legacy Tables |
| **Prophet of Regret** | Covenant | Pending Rollout | Legacy Tables |
| **Arbiter** | Covenant | Pending Rollout | Legacy Tables |
| **Brute Chieftain** | Covenant | Pending Rollout | Legacy Tables |
| **Heretic Leader** | Heretic | Pending Rollout | Legacy Tables |
| **Blademaster** | Heretic | Pending Rollout | Legacy Tables |
| **Gravemind / Flood**| Flood | Pending Rollout | Legacy Tables |
| **Didact / Forerunners**| UNSC (Forerunner) | Pending Rollout | Legacy Tables |
| **Militia Leader** | UNSC | Pending Rollout | Legacy Tables |
| **Rebel Leader** | UNSC | Pending Rollout | Legacy Tables |
| **Major Vanilla** | UNSC | Pending Rollout | Legacy Tables |
