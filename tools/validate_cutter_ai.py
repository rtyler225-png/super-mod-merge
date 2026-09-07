"""Static and behavioral regression checks for Cutter Standard; no game engine required.
Run: python tools/validate_cutter_ai.py
These checks do not replace a fresh in-game skirmish.
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
AI = ROOT / 'data/aidata'
SCRIPT = ROOT / 'data/triggerscripts/skirmishai/ai_cutter.triggerscript'

def named(path):
    return {e.get('name', '').lower(): e for e in ET.parse(path).getroot()}

class CutterStandard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml = ET.parse(SCRIPT).getroot()
        cls.variables = {v.get('ID'): v for v in cls.xml.find('TriggerVars')}
        cls.triggers = {t.get('ID'): t for t in cls.xml.find('Triggers')}
        cls.objects = named(ROOT / 'data/objects.xml')
        cls.squads = named(ROOT / 'data/squads.xml')
        cls.techs = named(ROOT / 'data/techs.xml')
        cls.tables = {}
        for stem in ('buildlist', 'trainlist', 'techs'):
            tabs = list(ET.parse(AI / f'{stem}_cutter.ai').getroot())
            assert len(tabs) == 1 and tabs[0].get('Name') == 'Standard'
            cls.tables[stem] = [[c.text for c in r] for r in tabs[0].findall('Row')]
        cls.final = {n.lower(): int(count) for n, count in cls.tables['trainlist']}
        # Actual leaders transform the generic buildings; include the upgraded base too.
        cls.transforms = {e.get('FromType').lower(): e.get('ToType').lower()
                          for e in cls.techs['unsc_leadercutter'].findall('./Effects/Effect')
                          if e.get('type') == 'TransformProtoUnit'}
        cls.buildings = {cls.transforms.get(r[0].lower(), r[0].lower())
                         for r in cls.tables['buildlist']}
        cls.buildings |= {'unsc_bldg_commandcutter_01', 'unsc_bldg_commandcutter_02',
                          'unsc_bldg_commandcutter_03', 'unsc_bldg_supplypad_02', 'unsc_bldg_reactor_02'}
        cls.commands = {}
        for name in cls.buildings:
            for c in cls.objects[name].findall('Command'):
                if c.text:
                    cls.commands.setdefault((c.get('Type'), c.text.lower()), set()).add(name)

    def value(self, ref):
        return self.variables[ref].text

    def input(self, trigger, effect, name):
        return self.triggers[str(trigger)].find(f".//Effect[@ID='{effect}']/*[@Name='{name}']").text

    def test_new_trigger_references_and_allocator(self):
        for kind, nodes, attr in [('TriggerVar', self.variables, 'NextTriggerVarID'),
                                  ('Trigger', self.triggers, 'NextTriggerID')]:
            self.assertGreater(int(self.xml.get(attr)), max(map(int, nodes)))
        all_ids = [v.get('ID') for v in self.xml.find('TriggerVars')]
        self.assertEqual(len(all_ids), len(set(all_ids)))
        for t in self.triggers.values():
            if not t.get('Name', '').startswith('Standard:'):
                continue
            for op in list(t.iter('Effect')) + list(t.iter('Condition')):
                for param in op:
                    self.assertIn(param.text, self.variables)
                    if param.get('Name') == 'Trigger':
                        self.assertIn(self.value(param.text), self.triggers)
            group = self.xml.find(f"./TriggerGroups/Group[@ID='{t.get('GroupID')}']")
            self.assertIn(t.get('ID'), group.text.split(','))

    def test_all_requested_units_and_techs_have_cutter_commands(self):
        for squad in self.final:
            self.assertIn(squad, self.squads)
            self.assertIn(('TrainSquad', squad), self.commands, squad)
        seen = set()
        for tech, owner_gate, count in self.tables['techs']:
            tech = tech.lower()
            self.assertNotIn(tech, seen, 'duplicate research row')
            self.assertIn(tech, self.techs)
            self.assertIn(('Research', tech), self.commands, tech)
            self.assertTrue(owner_gate.lower() in self.objects, owner_gate)
            self.assertGreater(int(count), 0)
            for prereq in self.techs[tech].findall('./Prereqs/TechStatus'):
                if prereq.get('status', '').lower() == 'active':
                    self.assertTrue(prereq.text.lower() in seen or prereq.text.lower() in
                                    {'basic', 'unsc_basic', 'unsc_leadercutter'},
                                    f'{tech}: missing earlier prerequisite {prereq.text}')
            seen.add(tech)
        self.assertFalse(any(n.lower().startswith(('cpgn_', 'rebel_', 'fld_')) for n, _, _ in self.tables['techs']))

    def test_build_requests_exist_on_native_sockets(self):
        interior = {c.text.lower() for c in self.objects['unsc_bldg_socket_01'].findall('Command')
                    if c.get('Type') == 'BuildOther'}
        for name, _, _ in self.tables['buildlist']:
            if '_turret' not in name:
                self.assertIn(name.lower(), interior)
        self.assertEqual(self.transforms['unsc_bldg_barracks_01'], 'unsc_bldg_barrackscutter_01')

    def test_single_standard_and_fixed_composition(self):
        self.assertEqual(self.value('11402'), '3')
        self.assertEqual(self.value('6207'), 'False')
        self.assertEqual(self.value(self.input(1969, 6853, 'BoolSource')), 'False')
        self.assertEqual(self.value('2216'), '1')
        self.assertEqual(self.value('3651'), '1')
        for e in self.xml.iter('Effect'):
            if e.get('Type') == 'CopyInt' and any(c.tag == 'Output' and c.text == '3651' for c in e):
                self.assertEqual(self.value(e.find('Input').text), '1')
        self.assertFalse(self.triggers['312'].findall(".//Effect[@Type='TriggerActivate']"))
        previous = {}
        for squad, target in self.tables['trainlist']:
            self.assertGreater(int(target), previous.get(squad, 0))
            previous[squad] = int(target)
        self.assertLessEqual(len(self.tables['trainlist']), 54)
        self.assertEqual(self.final['unsc_inf_marine_01'], 8)
        self.assertEqual(self.final['unsc_inf_marinerocket_01'], 6)

    def test_normal_economy_damage_and_build_speed(self):
        for tid, eid, name in [(1112, 6213, 'Multiplier'), (2506, 8214, 'DamageMultiplier'),
                               (2506, 8214, 'DamageTakenMultiplier'), (2756, 8746, 'BuildSpeedMultiplier')]:
            ref = self.input(tid, eid, name)
            self.assertEqual(float(self.value(ref)), 1)
            self.assertFalse(any(c.tag == 'Output' and c.text == ref for op in self.xml.iter('Effect') for c in op))

    def test_build_capacity_across_base_counts(self):
        self.assertEqual(self.input(2488, 100000, 'IntSource'), '4029')
        self.assertEqual(self.input(2488, 100000, 'IntCopy'), '10063')
        self.assertFalse(any('_command' in n or n.startswith('_') for n, _, _ in self.tables['buildlist']))
        for bases in range(1, 13):
            totals = {}
            for name, target, stage in self.tables['buildlist']:
                stage = int(stage)
                if stage > bases:
                    break
                target = int(target) * (bases if stage >= 3 else 1)
                totals[name] = max(totals.get(name, 0), target)
            interior = sum(count for name, count in totals.items() if '_turret' not in name)
            self.assertGreaterEqual(interior, bases * 7)
            self.assertLessEqual(interior, bases * 7 + 4)
            self.assertLessEqual(totals['unsc_bldg_turret_01'], bases * 4)
        for basic, upgraded, family in [('unsc_bldg_supplypad_01', 'unsc_bldg_supplypad_02', '_UnscSupplyPad'),
                                         ('unsc_bldg_reactor_01', 'unsc_bldg_reactor_02', '_PowerLevelBuilding')]:
            for n in (basic, upgraded):
                self.assertIn(family, [e.text for e in self.objects[n].findall('ObjectType')])

    def test_vehicle_transition_with_queued_units(self):
        # Exercise the documented one-bid table walk with native-style queued counts.
        # No power: the infantry ceiling is finite even if tanks cannot be trained yet.
        queued = Counter()
        def request(power):
            for n, target in self.tables['trainlist']:
                squad = self.squads[n.lower()]
                required = max([float(c.text) for c in squad.findall('Cost')
                                if c.get('ResourceType', c.get('resourcetype', '')).lower() == 'power'] or [0])
                if required <= power and queued[n] < int(target):
                    queued[n] += 1
                    return n
            return None
        for _ in range(200):
            request(0)
        self.assertEqual(queued['unsc_inf_marine_01'], 8)
        self.assertEqual(queued['unsc_veh_scorpion_01'], 0)
        self.assertEqual(request(2), 'unsc_veh_scorpion_01')
        self.assertEqual(request(2), 'unsc_veh_wolverine_01')
        for _ in range(300):
            request(4)
        self.assertEqual(queued['unsc_inf_marine_01'], 8)
        self.assertEqual(queued['unsc_veh_scorpion_01'], 36)
        self.assertEqual(queued['unsc_air_wasp_01'], 24)
        self.assertIsNone(request(4))

    def test_expansion_and_population_gates(self):
        self.assertEqual(self.value('23388'), 'unsc_bldg_commandCutter_02')
        self.assertEqual(self.value('23275'), '1')
        self.assertEqual(self.value('23276'), 'GreaterThanOrEqualTo')
        self.assertEqual(self.input(1255, 4904, 'SecondFloat'), '10109')
        self.assertLessEqual(float(self.value('1438')), 0.3)
        self.assertLessEqual(float(self.value('18894')), 3000)
        self.assertEqual(self.value('18888'), 'True')
        self.assertFalse(any('_base_upgrade' in n for n, _, _ in self.tables['techs']))
        # Both reactors must be upgradeable; requiring TWO basic reactors would strand
        # the second upgrade after the first transforms, leaving Sabres unreachable.
        row = next(r for r in self.tables['techs'] if r[0] == 'unsc_reactor_upgrade1')
        self.assertNotEqual(row[1:], ['unsc_bldg_reactor_01', '2'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
