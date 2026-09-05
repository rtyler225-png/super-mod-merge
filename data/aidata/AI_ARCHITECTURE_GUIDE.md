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
> [!CAUTION]
> **This table is a BUILD ORDER, not a set of proportions.** `Trigger 2316` -> `2317` -> `130` -> `133` -> `131` walks the table top-down. `Trigger 131 "Do we need more?"` bids the **first** row where `owned < target`, and then the chain **ends** - `Trigger 141` -> `Trigger 312 "build something reset multiplier"` has no `TriggerActivate`. `Trigger 129` resets the row cursor to 0 and the whole pass repeats every 1500ms.
>
> So each pass produces one bid, always for the earliest unsatisfied row, and `Trigger 149` keeps stacking bids on that same row (up to `TrnMaxNotApproved` 15 / `TrnMaxSquadBids` 35) until it is satisfied. **One row with a large count means the AI builds only that unit until it hits the count.** A consolidated 11-row table with `unsc_inf_marine_01` at 50 first made Cutter build ~50 Marines and nothing else, and because that plus the next four rows totalled 111 pop against a base cap of 120, its Scorpions were unreachable for most of the match.
>
> Counts are **cumulative totals of that squad**, so the way to get a mixed army is to list the same squad many times with a rising target and interleave the types - exactly what the shipped `CovMix_1` and `UnscRushInf_1` tables do (54 rows, counts of 1-5, types repeated). Keep increments small. **Never consolidate these rows.**
>
> Useful consequences:
> - Rows for squads the leader cannot train *yet* are skipped, not stalled (`Trigger 135` -> `206` -> `140`), and so are rows that do not fit pop (`Trigger 1017`) or lack reactors (`Trigger 1280`). Vehicle and air rows can therefore sit early in the table and simply switch on as the Vehicle Depot and Air Pad finish.
> - The **last** row for each squad governs battlefield replacement, because that is the row that goes deficient when units die. Order the final block by what you want rebuilt first.
> - Make each squad's targets strictly increasing. A repeated or decreasing target creates a row that can never be satisfied and that the walk re-checks every pass.
> - `TrainListMultiplier` scales every target (up to `TrainMaxMultiplier`, 3 on Balanced) once the table is fully satisfied, so set the 1x total slightly **above** the pop ceiling - the AI then always has something it wants and holds its cap through losses.
> - `Trigger 489` exempts the squads in `CurrentSquadCappedUnits` (`unsc_veh_warthog_01`, `unsc_inf_spartan_01`) from the multiplier entirely - their listed count is a hard ceiling.

- **Crucial Rule**: Only list squads that can actually be trained at the leader's production buildings or base! For instance, in this mod ODSTs are leader drop powers or starting units, not trainable barracks units.
- **Porting the baseline**: every squad in Cutter's `Standard` table trains at the **generic** buildings (`unsc_bldg_barracks_01`, `unsc_bldg_vehicledepot_01`, `unsc_bldg_airPad_01`). The leader-variant buildings have gaps - `unsc_bldg_vehicledepotSerina_01` has no Scorpion, `unsc_bldg_vehicledepotForge_01` has no Warthog or Wolverine, and the Anders and Serina barracks have no Sniper or Flamer. When copying this table to another UNSC leader, keep that leader's build list on the generic production protos or those rows go silently dead.
- **Universal UNSC Baseline**: The `"Standard"` baseline train list is designed to use **100% generic universal UNSC units** (Marines, Snipers, Rockets, Hellbringers, Medics, Scorpions, Warthogs, Cobras, Wolverines, Hornets, Pelicans) and omits leader-specific heroes (e.g. Jerome, Forge Warthog) so that this single baseline table can be copied cleanly across all UNSC leaders (Forge, Anders, Serina, etc.) without modification or missing squad crashes. Individual heroes or faction-unique units should be added in specialized personality tables (e.g. `ODSTRush`, `GrizzlyRoll`).

### C. TechUpgradeTable (`techs_<leader>.ai`)

> [!CAUTION]
> **Row order is strict research priority, and every tier-1 upgrade must be present.**
> The tech loop (Triggers 2269 -> 2903 -> 2278 -> 2276 -> 2277 -> 2273 -> 2271 -> 2272) walks the table from row 0 every pass and stops once it has created `AllowedNumberOfTechBids` bids - which is **1** normally, and 4 only while the AI is holding 4000+ supplies (Trigger 1950). Rows it cannot use (prereq unit absent, tech unavailable, not enough power) fall through to Trigger 2270 and the walk continues, so an unusable row does not deadlock - but the first *usable* row always wins. Anything near the bottom effectively never gets researched.
>
> Because upgrade chains are enforced by `<Prereqs><TechStatus>` in `techs.xml`, **omitting a tier-1 upgrade silently kills the whole chain**. `techs_cutter.ai` was missing `unsc_scorpion_upgrade1`, `unsc_cobra_upgrade1`, `unsc_wolverine_upgrade1` and `unsc_hornet_upgrade1` - all four are free (zero cost) and prereq only `unsc_basic` - so Cutter's entire vehicle and air line was permanently stuck at tier 1 while tiers 2 and 3 sat in the table looking correct.
>
> When porting this table to a new leader, verify with: for every row, resolve the tech's prereq chain in `techs.xml` and confirm each link is also a row in the table, at a *lower* index.

Order the table as: base upgrades -> economy (`supplypad`/`reactor`) -> the `unsc_tech_reinforcements` chain -> free tier-1 unit upgrades -> cheap upgrades that hit the largest squad counts -> the main battle line -> defence and power upgrades -> everything else. Column 2 (the prereq object) must be something that leader actually fields; a row whose prereq is a unit the leader never trains is dead weight that the loop re-checks every pass.


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
    <!-- Base 1 Turrets: 2 + 1 + 1 = the 4 perimeter sockets -->
    <Row><c>unsc_bldg_turret_01</c><c>2</c><c>1</c></Row>
    <Row><c>unsc_bldg_turretAA_01</c><c>1</c><c>1</c></Row>
    <Row><c>unsc_bldg_turretAV_01</c><c>1</c><c>1</c></Row>
    ```
  - Without turret rows in the build list, the AI will leave all perimeter turret sockets empty for the entire match.
> [!WARNING]
> **The AA/AV/AI turret counts are part of the 4, not on top of it.** `unsc_bldg_turretAA_01` and `unsc_bldg_turretAV_01` are alternative builds on the same turret socket (and `unsc_turret_upgradeAA`/`AV` convert an existing `unsc_bldg_turret_01`), so a converted turret stops counting toward `unsc_bldg_turret_01`. Asking for `turret_01` 4 + `turretAA` 2 + `turretAV` 2 requests 8 turrets for 4 sockets and leaves 4 bids permanently unfillable, burning slots in the `DiffBldMaxNotApproved` budget for the rest of the match.

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

### F. Build Priority vs. BldPermission (the scan STOPS, it does not skip)
Trigger 36 (`Get buildings of this type`) iterates `buildlist_<leader>.ai` top-down. Its conditions are, as an `And`:
1. `GetTableRow(BuildListTable, RowID, UserClassType 3)`
2. `Priority <= BldPermission`

The row cursor (`RowIDVar1`, TriggerVar 19034) is incremented **only inside `TriggerEffectsOnTrue`**, and `TriggerEffectsOnFalse` is **empty**.

> [!CAUTION]
> The moment the scan reaches a row whose priority exceeds the current `BldPermission`, **the entire build-list pass ends**. It does not skip that row and continue - every row below it is invisible until `BldPermission` rises. Put the over-priority rows at the BOTTOM of the table, never in the middle.

`BldPermission` (TriggerVar 10063) is not a fixed ceiling; it ramps during the match:

| Value | Set by | When |
| :--- | :--- | :--- |
| `1` | Trigger 411 `Default = boring`, and Trigger 1232 `Balanced` | match start / on strategy pick |
| `2` | Trigger 2492 | once the AI owns any `_ProductionBuildingNotBase` |
| `3` | Trigger 1282 | once `NumMyBases >= 2` |
| `3` | Trigger 1256 | once `StatePlayerPop > 0.7` |

> [!CAUTION]
> **The stop is the AI's build PACING, not a bug to be engineered around.** Every row at or below the current permission gets bid in the same pass, and `DiffBldMaxNotApproved` is only 30 on Normal. A priority-1 block that contains base expansions and mid-game economy opens all of it at second zero, drains the bid budget and the entire supply income into buildings, and the AI **stops training units altogether** and never buys its cheap turrets. This was tested and confirmed: growing the priority-1 block from 15 rows to 36 killed unit production outright.

- **Rule**: Priority `1` is the opening only - base 1 economy, the first Barracks / Vehicle Depot, the Field Armory, base 1 turrets. Roughly **15 rows**. Compare against the shipped tables in `unscbuildlists.ai`, which are 4-16 rows total.
- **Rule**: expansions and everything after them go at Priority `2`. This is not a delay in practice - Trigger 2492 raises `BldPermission` to 2 the moment the AI owns a single `_ProductionBuildingNotBase`, i.e. as soon as the opening Barracks finishes, and Trigger 1256 raises it to 3 as soon as `StatePlayerPop > 0.7` (which the `/30` divisor in section I makes almost immediate).
- Priority `3`+ is never reachable in skirmish.
- Interleave expansion with economy inside the priority-2 block (one `command_01` row, then production, then supply, then the base upgrade) rather than listing every `command_01` target up front. Several simultaneous base bids are very expensive and starve everything behind them.

### G. Base Expansion Requires ZERO Empty Sockets
The auto base-grab chain lives in group 14 (`Strategy:MultiBase`):

`2726 get bases` -> `2727 get sockets` -> `2728 loop` -> `2729 no empty sockets?` -> `2732 get bids` -> `2740 order new base` (`BidCreateBuilding unsc_bldg_command_01`)

> [!CAUTION]
> Trigger 2729 fires the grab **only when `EmptySockets == 0`** summed across every base the AI owns. A single unfilled interior socket anywhere blocks all further expansion, permanently.

This makes the *tail* of the build list load-bearing. If the table's cumulative targets run out before the AI's sockets do, the AI parks on empty sockets and stops expanding for the rest of the match - which reads in-game as "it just sits there doing nothing" in the late game.

- **Rule**: every `buildlist_<leader>.ai` must end with a filler tail whose targets exceed the maximum socket count the AI can reach: `LogMaxBases` (see `aidifficultysettings.xml`, 8 on Normal/Heroic) x 7 sockets at Fortress = **56**. Sum the max targets of everything that occupies an interior socket (`supplypad_01`, `_ProductionBuildingNotBase`, `reactor_01`, `fieldArmory_01`) and keep it above that.
- Turret sockets are counted separately (`EmptyTurretSockets`) and do **not** gate expansion.
- `AutoBaseGrab` (TriggerVar 23672) also gates this via Trigger 2762. Every strategy branch sets it `False` on entry and a follow-up trigger flips it back `True` (Trigger 2492 on first production building, Trigger 2530 at 5:00, Trigger 1365 / 2321 on the mid-game jump).

### H. Population Budget
- Base `Unit` pop is **120** (`data/leaders.xml`), not vanilla's 30-40.
- Each of `unsc_tech_reinforcements`, `...2`, `...3`, `...4` adds **+40** (`data/techs.xml`), for a **280** ceiling. They chain (each requires the previous) and cost 1/2/3 Power on top of supplies.
- They can only be researched at `unsc_bldg_fieldArmory_01` / `_02` (enabled by the `unsc_basic` tech). Listing them in `techs_<leader>.ai` against any other prereq building - a Barracks, for example - produces rows that can never fire.
- **Consequence**: the Field Armory is the single highest-value building in the list. Until it is up and all four techs are researched, the AI is hard-capped at 120 pop no matter how much production it has.
- Squad pop costs are on the *unit*, not the squad (`<Pop Type="Unit">` in `objects.xml`), multiplied by `<Unit count="">` in `squads.xml`. Scorpion and Pelican gunship are **6** each; a Marine squad is 4 x 0.25 = **1**. Cost the train list before assuming a low unit count means the AI is failing to produce - it is usually just pop-capped.

### I. Tactical Aggression & Waypoint Rallying
1. **Low-Pop Attack Handicap (Trigger 2164 / 2166)**:
   - Vanilla skirmish AI checks enemy human population (`totalPop > 20`). If the human player has under 20 pop (e.g. spectating or sitting idle), `HasEnoughPopToAttack` was forced to `False`, forcing the AI into 100% turtle mode.
   - Fixed by ensuring `HasEnoughPopToAttack` evaluates to `True` unconditionally so the AI fights with full aggression in all match configurations.
2. **Midpoint Rally Waypoint (Trigger 2192)**:
   - Attack missions create a midpoint waypoint in the center of the map (`MinRalliedPercent`, `MinSecureTime`).
   - If `MinSecureTime` is too long (e.g. 15s) and `MinRalliedPercent` is 0.5, continuously adding newly produced factory reserves to the mission continuously resets the rally timer, trapping the army in the center of the map.
   - Tightened `MinSecureTime` to 3s and `MinRalliedPercent` to 0.1 so the army pushes directly through to the enemy target.
3. **`StatePlayerPop` is normalised against a hardcoded 30 (KNOWN ISSUE, not yet changed)**:
   - Trigger 1255 `normalize to 1?` computes `StatePlayerPop = TotalPop / 30`, where `30` is a literal (TriggerVar 10126) left over from vanilla's 30-pop cap.
   - With this mod's 120-280 cap the value saturates far above `1.0`, so every gate keyed off it passes trivially: Trigger 1637 `Build up / force attack` (> 0.9, sets `MinimumToLaunch` to 0), Trigger 1833 `army built` (> 0.9), Trigger 1854 (> 0.8), Trigger 2838 `decider mission quota` (> `PopFor2Missions`). The mid-game brain therefore always takes the same branch.
   - The correct fix is to divide by actual `MaxPop` (TriggerVar 10109, already populated by Trigger 1254's `GetPlayerPop`) instead of the constant - i.e. change effect 4266's `SecondFloat` input from `10126` to `10109`.
   - **Do not apply this in isolation.** While the AI is production- or pop-starved it would drop `StatePlayerPop` below every threshold and make the AI *more* passive, not less. Land the build-list / Field Armory / pop-cap fixes first, confirm the AI actually reaches a full army in a test game, then make this change and re-test.

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
   - *Note on Current Baseline*: In `ai_cutter.triggerscript`, Trigger 1441's `RandomInt` roll has been disabled and hardcoded to single strategy `3` (Standard) with `SetBuildStrategy` and `SetTrainStrategy` initialized to `"Standard"` at second 0 (Triggers 2300 & 2314).
   - When you are ready to re-enable multiple personalities: replace the `CopyInt` in Trigger 1441 with a `RandomInt(1, N)` roll and route the outcomes to set:
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
