import re

with open('trainlist_flood.ai', 'r', encoding='utf-8') as f:
    text = f.read()

# For early game (CovMix_1, CovGeneral_1)
def fix_early(match):
    table = match.group(0)
    return re.sub(r'(<c>fld_inf_infectionform_(?:01|05|06)</c><c>)\d+(</c>)', r'\g<1>100\g<2>', table)

# For mid game (CovMix_2, CovGeneral_2)
def fix_mid(match):
    table = match.group(0)
    return re.sub(r'(<c>fld_inf_infectionform_(?:01|05|06)</c><c>)\d+(</c>)', r'\g<1>150\g<2>', table)

# For late game (CovMix_3, CovProphetElites, CovGeneral_3)
def fix_late(match):
    table = match.group(0)
    return re.sub(r'(<c>fld_inf_infectionform_(?:01|05|06)</c><c>)\d+(</c>)', r'\g<1>200\g<2>', table)

text = re.sub(r'<Table Name="CovMix_1"[\s\S]*?</Table>', fix_early, text)
text = re.sub(r'<Table Name="CovGeneral_1"[\s\S]*?</Table>', fix_early, text)

text = re.sub(r'<Table Name="CovMix_2"[\s\S]*?</Table>', fix_mid, text)
text = re.sub(r'<Table Name="CovGeneral_2"[\s\S]*?</Table>', fix_mid, text)

text = re.sub(r'<Table Name="CovMix_3"[\s\S]*?</Table>', fix_late, text)
text = re.sub(r'<Table Name="CovGeneral_3"[\s\S]*?</Table>', fix_late, text)
text = re.sub(r'<Table Name="CovProphetElites"[\s\S]*?</Table>', fix_late, text)

with open('trainlist_flood.ai', 'w', encoding='utf-8') as f:
    f.write(text)

print('Done')
