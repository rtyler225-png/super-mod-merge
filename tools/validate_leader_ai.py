"""Validate the Standard AI tables against each leader's real post-transform roster.

Each leader's `*_Leader<Name>` tech carries TransformProtoUnit effects that swap
the generic faction buildings for leader-specific variants with different TrainSquad and
Research commands. A table row naming a building, squad or tech the leader never owns
never fires, and the AI silently under-performs instead of erroring.

This script resolves those transforms and then checks, for every leader in LEADERS:

  * every build row names a prototype some socket can actually build
  * every build row whose owned form differs from the request is covered by a
    variant-counting trigger in that leader's script (otherwise the request is
    never satisfied and the row jams)
  * every train row is a squad one of the leader's own buildings can train, and
    repeated rows have strictly increasing targets
  * every tech row is researchable at one of the leader's own buildings, is not a
    duplicate, and its count gate is reachable from that leader's train list

Run from the mod directory:  python tools/validate_leader_ai.py
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
AIDATA = os.path.join(DATA, 'aidata')
SKIRMISH = os.path.join(DATA, 'triggerscripts', 'skirmishai')

# ai script stem -> (leader tech, table file stem, base prototype pattern)
LEADERS = {
    'cutter': ('unsc_LeaderCutter', 'cutter', 'unsc_bldg_command_%02d'),
    'forge': ('unsc_LeaderForge', 'forge', 'unsc_bldg_command_%02d'),
    'anders': ('unsc_LeaderAnders', 'anders', 'unsc_bldg_command_%02d'),
    'serina': ('unsc_LeaderSerina', 'serina', 'unsc_bldg_command_%02d'),
    'arbiter': ('covenant_LeaderArbiter', 'arbiter', 'cov_bldg_builder_%02d'),
    'brute': ('covenant_LeaderBrute', 'brute', 'cov_bldg_builder_%02d'),
    'prophet': ('covenant_LeaderProphet', 'prophet', 'cov_bldg_builder_%02d'),
    'gruntgeneral': ('covenant_LeaderYapYap', 'grunt', 'cov_bldg_builder_%02d'),
}


def read(path):
    with open(path, encoding='utf-8', errors='replace') as fh:
        return fh.read()


TECHS_XML = read(os.path.join(DATA, 'techs.xml'))
OBJECTS_XML = read(os.path.join(DATA, 'objects.xml'))
SQUADS_XML = read(os.path.join(DATA, 'squads.xml'))

OBJ = {}
for _m in re.finditer(r'<Object\s+name="([^"]+)"(.*?)</Object>', OBJECTS_XML, re.S):
    _c = collections.defaultdict(list)
    for _x in re.finditer(r'<Command\s+Type="([^"]+)"[^>]*>([^<]+)</Command>', _m.group(2)):
        _c[_x.group(1)].append(_x.group(2).strip())
    OBJ[_m.group(1).lower()] = _c

SQUAD_NAMES = {m.group(1).lower() for m in re.finditer(r'<Squad\s+name="([^"]+)"', SQUADS_XML)}
TECH_NAMES = {m.group(1).lower() for m in re.finditer(r'<Tech\s+name="([^"]+)"', TECHS_XML)}

# anything any socket in the game offers as a build command
SOCKET_BUILDABLE = set()
for _name, _cmds in OBJ.items():
    if 'socket' in _name:
        for _b in _cmds['BuildOther']:
            SOCKET_BUILDABLE.add(_b.lower())


def commands(proto):
    return OBJ.get(proto.lower(), collections.defaultdict(list))


def transform_map(leader_tech):
    """Apply the leader tech's TransformProtoUnit effects in order, following chains."""
    block = re.search(r'<Tech\s+name="%s"[^>]*>(.*?)</Tech>' % leader_tech, TECHS_XML, re.S)
    effects = re.findall(
        r'<Effect\s+type="TransformProtoUnit"\s+FromType="([^"]+)"\s+ToType="([^"]+)"',
        block.group(1))
    current = {}
    for src, dst in effects:
        for key, value in list(current.items()):
            if value.lower() == src.lower():
                current[key] = dst
        current[src] = dst
    return {k.lower(): v for k, v in current.items()}


def resolve(tmap, proto):
    return tmap.get(proto.lower(), proto)


def table_rows(path):
    return [re.findall(r'<c>([^<]*)</c>', row)
            for row in re.findall(r'<Row>(.*?)</Row>', read(path), re.S)]


def counted_variants(leader):
    """Prototypes whose owned variants the leader's script counts via the 2297 chain."""
    script = read(os.path.join(SKIRMISH, 'ai_%s.triggerscript' % leader))
    variables = {m.group(1): m.group(2)
                 for m in re.finditer(r'<TriggerVar ID="(\d+)"[^>]*>([^<]*)</TriggerVar>', script)}
    triggers = {m.group(1): m.group(0)
                for m in re.finditer(r'<Trigger ID="(\d+)".*?</Trigger>', script, re.S)}
    head = re.search(
        r'<Trigger ID="2297".*?Name="Trigger" SigID="1" Optional="false">(\d+)</Input>',
        script, re.S)
    covered = set()
    current = variables[head.group(1)]
    for _ in range(16):
        block = triggers.get(current)
        if block is None:
            break
        proto = re.search(r'SecondProtoObject" SigID="3" Optional="false">(\d+)</Input>', block)
        if proto:
            covered.add(variables.get(proto.group(1), '').lower())
        on_false = re.search(
            r'<TriggerEffectsOnFalse>.*?Name="Trigger" SigID="1" Optional="false">(\d+)</Input>',
            block, re.S)
        if not on_false:
            break
        nxt = variables.get(on_false.group(1))
        if nxt is None or nxt == current:
            break
        current = nxt
    return covered


def check(script, leader_tech, tables, base_fmt):
    tmap = transform_map(leader_tech)
    covered = counted_variants(script)
    problems = []

    build = table_rows(os.path.join(AIDATA, 'buildlist_%s.ai' % tables))
    owned = set()
    for proto, _count, _stage in build:
        got = resolve(tmap, proto)
        owned.add(got.lower())
        if proto.lower() not in SOCKET_BUILDABLE:
            problems.append('build row %s is not buildable on any socket' % proto)
        elif got.lower() != proto.lower() and proto.lower() not in covered:
            problems.append('build row %s is owned as %s but no counting trigger covers it'
                            % (proto, got))
    for tier in (1, 2, 3):
        owned.add(resolve(tmap, base_fmt % tier).lower())

    trainable, researchable = set(), set()
    for proto in list(owned):
        for tier in (proto, re.sub(r'_0\d$', '_02', proto), re.sub(r'_0\d$', '_03', proto)):
            if tier not in OBJ:
                continue
            for squad in commands(tier)['TrainSquad']:
                trainable.add(resolve(tmap, squad).lower())
            for tech in commands(tier)['Research']:
                researchable.add(tech.lower())

    train = table_rows(os.path.join(AIDATA, 'trainlist_%s.ai' % tables))
    ceiling, previous = {}, {}
    for squad, count in ((r[0], int(r[1])) for r in train):
        if squad.lower() not in SQUAD_NAMES:
            problems.append('train row %s is not a squad' % squad)
        elif squad.lower() not in trainable:
            problems.append('train row %s cannot be trained by any building this leader owns'
                            % squad)
        if squad in previous and count <= previous[squad]:
            problems.append('train row %s target %d does not increase on %d'
                            % (squad, count, previous[squad]))
        previous[squad] = count
        ceiling[squad.lower()] = max(ceiling.get(squad.lower(), 0), count)

    techs = table_rows(os.path.join(AIDATA, 'techs_%s.ai' % tables))
    seen = set()
    for tech, gate, count in ((r[0], r[1], int(r[2])) for r in techs):
        if tech.lower() not in TECH_NAMES:
            problems.append('tech row %s is not a tech' % tech)
        elif tech.lower() not in researchable:
            problems.append('tech row %s is not researchable at any building this leader owns'
                            % tech)
        if tech.lower() in seen:
            problems.append('duplicate tech row %s' % tech)
        seen.add(tech.lower())
        if gate.lower() not in owned and gate.lower() not in trainable:
            problems.append('tech row %s is gated on %s, which this leader never owns or trains'
                            % (tech, gate))
        if gate.lower() in ceiling and count > ceiling[gate.lower()]:
            problems.append('tech row %s needs %d %s but the train list only reaches %d'
                            % (tech, count, gate, ceiling[gate.lower()]))

    print('%-13s build %2d  train %2d  tech %2d  %s'
          % (script, len(build), len(train), len(techs),
             'OK' if not problems else '%d PROBLEM(S)' % len(problems)))
    for p in problems:
        print('         !! %s' % p)
    return len(problems)


def main():
    total = sum(check(script, *cfg) for script, cfg in LEADERS.items())
    print('total problems:', total)
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
