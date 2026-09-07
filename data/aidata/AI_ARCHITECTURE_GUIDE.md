# Halo Wars DE AI architecture and Cutter Standard

This is the current source-level baseline as of 2026-09-06. Cutter is the only
leader covered by this overhaul. The other leaders retain their existing AI.
The earlier guide mixed several abandoned experiments with current behavior;
its pre-change copy is in `scratch/cutter_standard_before/` locally.

## Runtime and table selection

`data/triggerscripts/skirmishai.triggerscript`, trigger 10, launches
`skirmishai/ai_cutter.triggerscript` for Cutter. Cutter's trigger 1441 chooses
strategy 3. Build, train, and tech files each contain exactly one table named
`Standard`. Table names are scoped by filename; the name alone is not global.

| File | Table type | Rows |
| --- | --- | ---: |
| `buildlist_cutter.ai` | BuildingBuildList | 15 |
| `trainlist_cutter.ai` | SquadBuildList | 40 |
| `techs_cutter.ai` | TechUpgradeTable | 39 |

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

Cutter's application points now explicitly use a dedicated constant of 1.0:
`SetResourceHandicap` (1112), `AISetPlayerDamageModifiers` (2506), and
`AISetPlayerBuildSpeedModifiers` (2756). The last effect is in the Deathmatch
branch; it was not a general skirmish production-speed fix.

This is scoped to Cutter. `aidifficultysettings.xml` is unchanged, so other
leaders keep their difficulty bonuses. Difficulty still controls thinking and
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

| Squad | Final desired count |
| --- | ---: |
| Scorpion | 36 |
| Wasp | 24 |
| Cobra | 16 |
| Wolverine | 12 |
| Warthog | 12 |
| Gremlin | 4 |
| Sabre | 2 |
| Marine | 8 |
| Rocket Marine | 6 |
| Sniper squad | 2 |
| Medic squad | 2 |

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

**Build column 3 now means owned-base stage for Cutter.** Trigger 2488 copies
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

## Validation and match testing

Run from the mod directory:

```powershell
python tools/validate_cutter_ai.py
```

The regression checks parse the XML; validate added trigger references; resolve
Cutter unit and research commands; check research prerequisites; check 1x
modifiers and fixed composition; check interior capacity from one to twelve
bases; and simulate queued production through a power-0 to power-2/4 transition.
The simulation tests planning rules, not real-time engine scheduling or combat.

**In-game validation remains outstanding.** Start a fresh Standard skirmish
through Haruspis with this mod selected. Existing saves may retain old scripts
or orders. Test Normal and Heroic without economy/combat skulls, then repeat on
a second map. Record:

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

Timing targets must be calibrated from these matches. Do not label a static
check or a change in a numeric aggression setting as proof the AI feels good.
Future personalities should branch from this verified structure and preserve
ordinary costs, roster legality, and explicit production capacity.
