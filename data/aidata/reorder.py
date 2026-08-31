import re

with open('trainlist_flood.ai', 'r', encoding='utf-8') as f:
    text = f.read()

def process_table(match):
    table_content = match.group(0)
    
    # Extract all rows
    rows = re.findall(r'(\t\t<Row>.*?</Row>\r?\n)', table_content)
    
    infection_rows = []
    other_rows = []
    
    for row in rows:
        if 'fld_inf_infectionform_' in row:
            infection_rows.append(row)
        else:
            other_rows.append(row)
            
    # Reconstruct table
    table_start = re.search(r'(.*?<Table[^>]*>\r?\n)', table_content).group(1)
    table_end = '\t</Table>\n'
    
    new_table = table_start + ''.join(infection_rows) + ''.join(other_rows) + table_end
    return new_table

# Regex to match each Table block
new_text = re.sub(r'\t<Table[^>]*>[\s\S]*?</Table>\r?\n', process_table, text)

with open('trainlist_flood.ai', 'w', encoding='utf-8') as f:
    f.write(new_text)

print('Done')
