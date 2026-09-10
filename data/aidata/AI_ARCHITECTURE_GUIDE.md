# Halo Wars DE AI architecture and leader Standard

This is the current source-level baseline as of 2026-09-07. It covers the four
mainline UNSC leaders (Cutter, Forge, Anders, Serina) and the four Covenant-civ
leaders (Arbiter, Brute Chieftain, Prophet of Mercy, YapYap). Cutter was tuned
first and the other seven were ported from him. The Heretic-civ leaders
(Heretics, Blademaster), Flood, Forerunner, Militia and Rebel retain their
existing AI; those are separate factions with separate rosters and each needs
its own pass. The earlier guide mixed several abandoned experiments with current
behavior; its pre-change copy is in `scratch/cutter_standard_before/` locally.

## Runtime and table selection

`data/triggerscripts/skirmishai.triggerscript`, trigger 10, launches
`skirmishai/ai_<leader>.triggerscript`. Trigger 1441 chooses strategy 3. Build,
train, and tech files each contain exactly one table named `Standard`. Table
names are scoped by filename; the name alone is not global.

| Leader | Script | Tables | BuildingBuildList | SquadBuildList | TechUpgradeTable |
| --- | --- | --- | ---: | ---: | ---: |
| Cutter | `ai_cutter` | `*_cutter.ai` | 15 | 40 | 39 |
| Forge | `ai_forge` | `*_forge.ai` | 15 | 48 | 42 |
| Anders | `ai_anders` | `*_anders.ai` | 15 | 51 | 48 |
| Serina | `ai_serina` | `*_serina.ai` | 15 | 54 | 49 |
| Arbiter | `ai_arbiter` | `*_arbiter.ai` | 16 | 60 | 53 |
| Brute Chieftain | `ai_brute` | `*_brute.ai` | 16 | 56 | 49 |
| Prophet of Mercy | `ai_prophet` | `*_prophet.ai` | 16 | 56 | 47 |
| YapYap | `ai_gruntgeneral` | `*_grunt.ai` | 16 | 57 | 48 |

Note that YapYap's script stem and table stem differ. The eight scripts are the
same file apart from the leader-specific values listed under "Porting Standard
to another leader" below. Every fix described in this guide is present in all
eight.

The editable XML files are the AI inputs. Haruspis logs confirm its Super Mod
Merge launch selects this directory. The game's manifest outside the mod may
show another mod between launches; start this mod through Haruspis for testing.

## Why the previous baseline was unreliable

These are findings from the source, not a claim of measured match improvements.

- Train trigger 312 had an added continuation into 140 after creating a bid.
  It could walk and bid across the rest of the table without returning through
  the normal entry checks. Reaching the end also invoked multiplier growth,
  including when unavailable vehicle/air rows had merely been skipped. Counts
  therefore did not remain the fixed composition shown in the table.
- Trigger 1969 enabled the separate counter-unit plan after five minutes.
  Renaming every table Standard had not removed this second production path.
- Expansion production used `_ProductionBuildingNotBase`. Trigger 2487 picks a
  random member of that broad class, checks legality, and skips the entire row
  if the choice is illegal. It does not retry another member. This is neither a
  reliable vehicle-factory request nor a reliable combined-arms ratio in a mod
  with many factions and building variants.
- Base-upgrade filters 2735/2736 named generic UNSC bases, while Cutter's leader
  tech transforms bases into Cutter-specific prototypes.
- Multibase trigger 2729 required zero empty interior sockets across all bases.
  The secure-base mission also required more than ten reserve squads and more
  than ten blocked-site checks. Those conditions delayed expansion assistance.
- The tech table contained 287 rows, including duplicates, other factions,
  unavailable commands, and campaign grants. Its priority order also put several
  infantry upgrades ahead of the Warthog gunner upgrade.
- The population ratio divided by vanilla's constant 30, although this mod's
  normal UNSC starting cap is 240. This distorted multiple tactical decisions.
- The shared difficulty settings grant income multipliers from 4.2x to 7.35x,
  and some tiers have damage bonuses. Building around one supply pad assumed
  those bonuses would finance everything else.

## Ordinary economy and a fixed roster

Each leader's application points now explicitly use a dedicated constant of 1.0:
`SetResourceHandicap` (1112), `AISetPlayerDamageModifiers` (2506), and
`AISetPlayerBuildSpeedModifiers` (2756). The last effect is in the Deathmatch
branch; it was not a general skirmish production-speed fix.

This is scoped to the eight leaders above. `aidifficultysettings.xml` is unchanged,
so every other leader keeps its difficulty bonuses. Difficulty still controls thinking and
reaction settings. This change does not remove game-mode/skull effects or claim
to audit the engine's entire knowledge/visibility system. Site danger queries
continue to use the existing AI knowledge base; the distance tie-break does not
introduce a map-reveal command.

Every squad is purchased through the native bid system using its existing
supply cost, power requirement, population cost, and production time. The
baseline has no free grants or spawned reinforcements. It does not change player
unit statistics or population caps.

Train targets are cumulative **squad counts**, not model counts or percentages.
Repeated squads have increasing targets to interleave their production. Trigger
149 includes training squads and pending bids. Trigger 312 now ends a successful
pass; the next normal pass starts from row zero. Both the multiplier and all
writers of its maximum are fixed to 1. The separate counter list remains off.

Each leader's roster is drawn only from squads its own buildings can train, and
is scaled to roughly the same nominal population so the eight are comparable.

| Leader | Armour core | Air | Anti-air | Nominal pop |
| --- | --- | --- | --- | ---: |
| Cutter | Scorpion 36, Cobra 16 | Wasp 24, Sabre 2 | Wolverine 12 | 430 |
| Forge | Scorpion 22, Grizzly 8, Cobra 10 | Falcon 14, Vulture 2 | Falcon, Cyclops Enforcer 6 | 436 |
| Anders | Gauss Scorpion 22, Colossus 6, Rhino 4 | Hornet 18, Condor 1 | Mantis 12 | 424 |
| Serina | Cryo Scorpion 18, Colossus 6, Cobra 8 | Hornet 18, Frost Raven 6, Vulture 2 | Mantis 12 | 428 |
| Arbiter | AA Wraith 22, Spectre 14, Locust 12 | Banshee 18, Heavy Banshee 8, Seraph 2 | AA Wraith, Vampire 8, Locust | 428 |
| Brute Chieftain | Wraith 22, Prowler 16, Locust 14 | Banshee 18, Seraph 2 | Vampire 12, Locust | 418 |
| Prophet of Mercy | Wraith 22, Revenant 16, Locust 14 | Banshee 18, Seraph 2 | Vampire 12, Locust, Jackal squads | 410 |
| YapYap | Grunt Tank 28, Goblin 26, Methane Wagon 14 | Banshee 18, Seraph 2 | Goblin, Grunt Tank, Vampire 12 | 410 |

Only Cutter has a Wolverine. Forge, Anders and Serina answer air with the
Falcon, the Mantis and the Mantis respectively; those rows are not optional
flavour. Every Covenant leader gets the Vampire, which is their one cheap
dedicated anti-air aircraft and comes from the light factory all four own.
Each leader also carries a small fixed infantry tail and 2 transports where the
air building offers them. Covenant leaders additionally train exactly one hero
(Arbiter, Tartarus, Prophet, Deacon): heroes cost **Leader** population, a pool
separate from Unit population, so the hero row does not compete with the army
and is not a population exploit. The full per-row counts live in the tables.

These are ceilings for replacement requests, not a promise that the AI will
own all of them simultaneously. The nominal target exceeds the fully upgraded
400 Unit population cap, so there remains something to request without raising
the multiplier. Available population, power, money, casualties, and factories
still determine which squads can actually finish. The first unmet row wins;
vehicle rows are interleaved ahead of additional infantry. Removing the counter
list makes this a reproducible baseline, not a completed adaptive-counter AI.

## Buildings and expansion

Cutter actually owns Cutter Barracks, Cutter Air Pads, and Cutter Field Armories.
His vehicle depot stays generic. The Barracks build request still uses the generic
name exposed on `unsc_bldg_socket_01`; trigger 3197 counts the transformed Cutter
Barracks toward that request. Air Pad and Field Armory variants are directly
listed on that socket. Use the resulting buildings' `TrainSquad` and
`Research` commands when verifying a roster. Hornets and Pelican gunships are
not substitutes for Cutter's Wasp just because they are generic UNSC aircraft.

**Build column 3 now means owned-base stage.** Trigger 2488 copies
`NumMyBases` to `BldPermission` before each build scan. Trigger 36 stops at the
first row above that permission, so stages must remain sorted.

- One base: two supply pads, one depot, two reactors, one Barracks and one Air
  Pad request seven interior sockets. A separate turret request uses a perimeter
  socket. The depot is requested ahead of the Barracks.
- Two bases: totals become five pads, three depots, two reactors, one Barracks,
  two Air Pads and one Field Armory: fourteen interior sockets, plus two turrets.
- Three or more bases: stage-3 row counts are multiplied by the current number
  of bases by trigger 3193. Supply pads target four per owned base, depots two,
  Air Pads one, turrets one. Together with the fixed early buildings this gives
  enough requests to keep expanding, without immediately bidding for a fixed
  fleet of factories intended for twelve bases.

Counts are global targets, not placement guarantees at each individual base.
Do not copy this table to another leader without copying/adapting its stage
logic. Do not interpret the small stage-3 numbers as decreasing cumulative
counts: they become larger targets after multiplication.

Triggers 3194/3195 count upgraded and basic reactors/pads as the same building
family. Their construction request still names the basic building. Upgrading a
pad must not trick the builder into filling another scarce socket to replace it.

Base claiming/upgrading stays in group 14. No base prototypes or base-upgrade
techs appear in the tables. The filters use Cutter bases, check every 15 seconds,
and allow at most one unfilled interior socket instead of requiring exactly
zero. Existing bid checks and the native purchase process remain in place.

The secure-base mission becomes eligible after four blocked-site checks with
at least four reserve squads. Its topic has less guaranteed scheduler weight,
and its waypoint can be skipped if necessary. Its existing three-second secure
time and 10% rally fraction remain. The native all-reserve assignment is still
used; escort-size allocation has not been redesigned.

Site selection first minimizes known enemy squad count. Trigger 3196 breaks
otherwise equal scores by distance from the first base. The existing 2000-unit
map search/leash remains; reducing that fixed radius could exclude all legal
expansions on some maps. This is not a pathfinding or terrain-cost calculation.

## Research and aggression

The research table contains only commands available on Cutter buildings, with
prerequisite chains in order. A free tier-1 upgrade can be gated by its factory,
so the AI need not wait for a trained squad before discovering that upgrade.

**Tech column 2 is an ownership/count gate, not the researcher.** Trigger 2278
checks that object type/count; trigger 2272 passes a null Builder to
`BidCreateTech`, letting the engine select the research building. A population
upgrade can therefore be gated on a tank count while still being researched
legally at the Field Armory. The earlier guide's claim that the row must name
its research building was too strict.

Research uses one normal pending bid, or three above 4000 supplies, to limit
unaffordable commitments in the ordinary economy. Supply-pad upgrades remain
available for every basic pad. Heavy reactor upgrades wait for three Scorpions;
they must not require two *basic* reactors, since the first upgrade would leave
only one and prevent the second. Adrenaline precedes Recruit Training.
Reinforcements progress behind tank-count gates rather than being four early
purchases before the army needs population. Base upgrades use their own manager.

The population fraction now uses actual `MaxPop`. The ordinary attack launch
threshold is reduced from 0.5 to 0.3 and its time decay doubled from 0.003 to
0.006 per second. Target scoring and affordability still apply. This permits
pressure without requiring a nearly full 240/400-pop army. Existing retreat,
scouting, enemy-readiness bypass, and attack-waypoint logic remain in place.

## Porting Standard to another leader

An `unsc_Leader<Name>` tech carries `TransformProtoUnit` effects that swap the
generic UNSC buildings for leader-specific variants with **different TrainSquad
and Research commands**. A row naming something the leader never owns simply
never fires; nothing errors. Resolve the transforms first, then write the tables
against the resulting buildings. This is what each leader actually ends up with:

### UNSC

| Role | Cutter | Forge | Anders | Serina |
| --- | --- | --- | --- | --- |
| Supply pad | `supplypad_01` | `supplypad_02` | `supplyPad_02` | `supplypad_01` |
| Reactor | `reactor_01` | `reactor_01` | `reactor_01` | `reactor_01` |
| Barracks | `barracksCutter_01` | `barracksForge_01` | `barracksAnders_01` | `barracksSerina_01` |
| Vehicle depot | `vehicledepot_01` | `vehicledepotForge_01` | `vehicledepotAnders_01` | `vehicledepotSerina_01` |
| Air pad | `airPadCutter_01` | `airpadSerina_01` | `airPadAnders_01` | `airPad_01` |
| Field armory | `fieldArmoryCutter_01` | `fieldArmoryForge_01` | `fieldArmoryAnders_01` | `fieldArmorySerina_01` |
| Base tier 1/2 | `commandCutter_02` (starts at Station) | `commandForge_01/02` | `commandAnders_01/02` | `commandSerina_01/02` |

Forge and Anders start with the *upgraded* supply pad, so neither has a
`unsc_supplyPad_upgrade1` row. Cutter starts at Station tier, so his tier-1 base
filter matches nothing and he only needs `unsc_base_upgrade2`.

### Covenant

The Covenant build roles are not named after the UNSC ones and one of them is
easy to get wrong. The mapping the tables use:

| UNSC role | Covenant building | Why |
| --- | --- | --- |
| Supply pad | `cov_bldg_supplyDepot_01` | family `_CovSupplyPad` covers both tiers and the Grunt variants |
| **Reactor** | **`cov_bldg_kingtemple_01`** | the KING Temple carries `_PowerLevelBuilding`; the plain Temple carries no object type at all and gives no tech level |
| Vehicle depot | `cov_bldg_heavyfactory_01` | Wraith / Prowler / Revenant / Grunt Tank |
| Air pad | `cov_bldg_lightfactory_01` | Covenant air is the Banshee and Vampire, and both come from the LIGHT factory |
| Field armory | `cov_bldg_temple_01` | hero, followers (population), turret, shield and leader-power research |
| Turret | `cov_bldg_turret_01` | perimeter socket, same as UNSC |
| — | `cov_bldg_landingpad_02` | extra Covenant building with no UNSC analogue; carries the Seraph |

| Role | Arbiter | Brute Chieftain | Prophet of Mercy | YapYap |
| --- | --- | --- | --- | --- |
| Supply depot | `supplyDepot_01` | `supplyDepot_01` | `supplyDepot_01` | `supplyDepotGrunt_01` |
| King temple | `kingtemple_01` | `kingtemple_01` | `kingtemple_01` | `kingtemple_01` |
| Heavy factory | `heavyfactoryArbiter_01` | `heavyfactoryTartarus_01` | `heavyfactoryRegret_01` | `heavyfactoryGrunt_01` |
| Light factory | `lightfactoryArbiter_01` | `lightfactory_01` | `lightfactory_01` | `lightfactory_01` |
| Barracks | `barracksArbiter_01` | `barracksTartarus_01` | `barracksRegret_01` | `barracksGrunt_01` |
| Temple | `templeArbiter_01` | `temple_01` | `temple_01` | `templeGrunt_01` |
| Base tier 1/2 | `builder_01/02` | `builderBrute_01/02` | `builderProphet_01/02` | `builderGrunt_01/02` |

Temples and King Temples have three tiers reached by `cov_temple_upgrade1/2` and
`cov_kingtemple_upgrade1/2`, which are `TransformProtoUnit` effects. All King
Temple tiers are `_PowerLevelBuilding`, so `cov_kingtemple_upgrade1` is safe to
research and is the Covenant's reactor upgrade. The plain Temple tiers have no
family, so the Temple tier upgrades are deliberately **absent** from the tech
tables, exactly as the UNSC vehicle depot and barracks upgrades are and for the
same reason: they would break the building's build-list count. The same applies
to `cov_heavyfactory_upgrade*`, `cov_summit*_upgrade1` and `cov_barracks*_upgrade1`.

The Covenant scripts also carry two values the UNSC ones do not: TriggerVars
24012 and 24019 name the leader repair power. Arbiter, Brute and Prophet ship
with `CovRepair` and YapYap with `UnscLeaderRepair`; the port preserves whichever
value each script already had rather than normalising them, because `powers.ai`
registers `UnscLeaderRepair` but not `CovRepair`. YapYap additionally carries
four supply-depot list variables (2542, 13042, 15118, 24042) that include his
Grunt depot variants; those are preserved too.

### Both factions

A build row must name a prototype that some socket lists as a `BuildOther`
command. When the leader's transform turns that prototype into a variant, the
owned building no longer matches the request, and the count that satisfies the
row must be widened or the row never completes and keeps re-bidding. Trigger
2297 sets the default filter and then walks a chain of counting triggers; the
first one whose prototype matches the current request replaces the filter:

| Leader | Counting chain after 2297 |
| --- | --- |
| Cutter | 3195 pads → 3194 reactors → 3197 barracks |
| Forge | 3195 pads → 3194 reactors → 3197 barracks → 3198 air pads |
| Anders | 3195 pads → 3194 reactors → 3197 barracks |
| Serina | 3195 pads → 3194 reactors → 3197 barracks → 3198 depots → 3199 armories |
| Arbiter | 3195 depots → 3194 king temples → 3197 barracks → 3198 heavy factories → 3199 light factories |
| Brute Chieftain | 3195 depots → 3194 king temples → 3197 barracks → 3198 heavy factories |
| Prophet of Mercy | 3195 depots → 3194 king temples → 3197 barracks → 3198 heavy factories |
| YapYap | 3195 depots → 3194 king temples → 3197 barracks (no-op) |

3195 and 3194 use an object type list (`_UnscSupplyPad` or `_CovSupplyPad`, and
`_PowerLevelBuilding`), so they also cover the upgraded tiers of each and, for
`_CovSupplyPad`, YapYap's Grunt depot. YapYap needs no variant counting at all:
his Grunt barracks, heavy factory and Temple are each listed on the socket in
their own right so they are requested directly, and his depot is caught by the
family, so his 3197 slot is pointed at his own barracks and produces a filter
identical to the default. The rest use explicit
`ProtoObjectList` variables holding the generic prototype plus the leader's
variant. New triggers are registered in group 0 (Build Manager) and the header's
`NextTriggerID` / `NextTriggerVarID` / `NextConditionID` / `NextEffectID`
counters are advanced.

Everything else in the script is leader-agnostic. Porting means copying
`ai_cutter.triggerscript` and changing only:

1. the three table filenames (TriggerVars 18741, 18842, 19023, 19075, 19224,
   19252, 20185)
2. the multibase upgrade filters (23376 tier 1, 23388 tier 2)
3. the first variant slot: request prototype 27509 and variant list 27510, plus
   the names on TriggerVar 27511 and trigger 3197
4. for a different civ, the power and supply prototypes and families (27500,
   27501, 27503, 27504)
5. any civ-specific values the leader's shipped script already carried — for the
   Covenant that is the repair power and YapYap's supply lists
6. any extra counting triggers the table above calls for

Do not skip step 6. Without it the affected build row is never satisfied, the
builder keeps bidding for a building it already has, and the leader stalls on
that stage.

## Validation and match testing

Run from the mod directory:

```powershell
python tools/validate_cutter_ai.py
python tools/validate_leader_ai.py
```

The first script is Cutter's regression suite: it parses the XML; validates
added trigger references; resolves Cutter unit and research commands; checks
research prerequisites; checks 1x modifiers and fixed composition; checks
interior capacity from one to twelve bases; and simulates queued production
through a power-0 to power-2/4 transition. The simulation tests planning rules,
not real-time engine scheduling or combat.

The second script resolves each leader's transforms and checks all eight
leaders' tables against the roster that results: build rows must be buildable on
a socket and covered by a counting trigger when they transform, train rows must
be trainable by a building the leader owns with strictly increasing targets, and
tech rows must be researchable by a building the leader owns with a count gate
the train list can actually reach. Run it after any table edit.

**In-game validation remains outstanding for every leader except Cutter.** Start
a fresh Standard skirmish through Haruspis with this mod selected. Existing saves
may retain old scripts or orders. Test Normal and Heroic without economy/combat
skulls, then repeat on a second map. Record:

1. First depot, second power level, and first Scorpion timings. Vehicles should
   enter the opening without waiting for a large infantry quota to be filled.
2. First enemy pressure and first expansion attempt; note whether a site is
   guarded. Test against both an active opponent and a passive human observer.
3. At roughly five and ten minutes: owned factories, supply stockpile, army
   composition, base count, and any unfilled sockets. A large bank with idle
   factories is a scheduling/legality symptom, not evidence more income is needed.
4. After casualties: whether tank/AA/air replacements continue and whether the
   army leaves its expansion waypoint. Losing expansions must not permanently
   prevent rebuilding.
5. For every leader except Cutter: they start at the first base tier, not the
   second, so their first three interior sockets fill with two economy buildings
   and a vehicle factory, and the Barracks and air building wait on
   `unsc_base_upgrade1` / `cov_base_upgrade1`. Confirm the base actually upgrades
   and those two buildings then appear. If a leader sits at the first tier
   forever, look at the group 14 base manager and TriggerVars 23376 and 23388
   before touching the build list.
6. For the Covenant only: confirm King Temples actually get built and Power
   rises. Covenant Power comes from the King Temple, not the Temple, and the
   Temple is the building that trains the hero. If a Covenant leader is stuck at
   Power 0 with Temples on the field, the build list is naming the wrong one.
7. For the Covenant only: confirm the leader hero is trained and stays alive.
   The hero costs Leader population, so if it never appears the Temple was never
   built rather than the army being at cap.

Timing targets must be calibrated from these matches. Do not label a static
check or a change in a numeric aggression setting as proof the AI feels good.
Future personalities should branch from this verified structure and preserve
ordinary costs, roster legality, and explicit production capacity.
