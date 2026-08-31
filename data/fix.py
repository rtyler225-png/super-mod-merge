import re
with open('squads.xml', 'r', encoding='utf-8') as f:
    s = f.read()
s = re.sub(r'(name="fld_inf_infectionForm_\d+"[\s\S]*?)<Cost ResourceType="Supplies">20</Cost>', r'\1<Cost ResourceType="Supplies">5</Cost>', s)
with open('squads.xml', 'w', encoding='utf-8') as f:
    f.write(s)
print('Done')
