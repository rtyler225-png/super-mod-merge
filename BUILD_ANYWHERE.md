# Build-anywhere power balance

Build-anywhere is enabled. All original leader, faction, and campaign grant
paths are restored. As of 2026-09-10, non-Flood build-site powers cost 200 supplies,
hold one charge, and have a base 30-second cooldown
(`AutoRecharge` = 30000 milliseconds). They were briefly 500 supplies on a 60-second cooldown; that proved too expensive.
Flood retains its original cheap, fast beacon.

| Power | Supplies | Base cooldown | Radial position |
| --- | --- | --- | --- |
| `UnscBuildingDrop` | 200 | 30 seconds | 6 |
| `CovBuildingDrop` | 200 | 30 seconds | 6 |
| `SerBuildingDrop` | 200 | 30 seconds | 4 |
| `RebelBeaconDrop` | 200 | 30 seconds | 6 |
| `GruntScructureDrop` | 200 | 30 seconds | 4 |
| `FldBeaconDrop` | 10 | 1 second (unchanged) | 4 |

Existing special-mode, cheat, and skull recharge modifiers remain unchanged.
The four non-Flood `InfiniteUses` flags are replaced by `ShowLimit`, and
YapYap's `GruntScructureDrop` grant is reduced from two charges to one. All
15 non-Flood build-site grants now specify one charge. This uses the same
limited-use grant and automatic recharge setup as existing finite powers.
Flood's unlimited-use flag and original three-use grant remain unchanged.
Scripts, socket objects, squads, strings, and radial positions are preserved.
Existing direct turret-drop powers are unchanged.
Leaders that did not previously have a build-site power receive no new power.

## Future replacement

The original implementations remain intact. To introduce defensive turret
drops later, define separately named powers and replace the corresponding
`GodPower` grants in `data/techs.xml`, using the radial positions above.
Keep Flood's beacon enabled. Check inherited faction grants to avoid granting
a replacement twice.

## Validation

XML parsing and comparison confirm the five non-Flood costs and recharge values,
four unlimited-use flag replacements, and one charge-count change. All 15
previously disabled grants are active, and Flood's entire power definition and
leader tech are unchanged.

Start a new skirmish to validate the charge behavior; an existing save may retain
old grants. After waiting longer than two cooldown periods, place one build site
and confirm a second placement is unavailable until the cooldown finishes.
