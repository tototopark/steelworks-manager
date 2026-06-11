import re
import os

sql_path = r'F:\pe\public_html\backup-8.15.2024_19-39-32_pengelly-111\mysql\pengelly_jumbodra_DB-Dev.sql'
output_path = r'F:\pe\public_html\steelworks-manager\test\schemas.txt'

if not os.path.exists(sql_path):
    print("SQL file not found!")
    exit(1)

with open(sql_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Let's find all CREATE TABLE blocks
# A CREATE TABLE block starts with CREATE TABLE `table_name` (
# and ends with ) ENGINE=...;
matches = re.finditer(r'CREATE TABLE `(\w+)` \((.*?)\) ENGINE=.*?;', content, re.DOTALL)

os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as out:
    for m in matches:
        table_name = m.group(1)
        columns_def = m.group(2)
        out.write("="*60 + "\n")
        out.write(f"TABLE: {table_name}\n")
        out.write("="*60 + "\n")
        for line in columns_def.strip().split('\n'):
            out.write(line.strip() + "\n")
        out.write("\n")

print(f"Extraction complete! Saved to {output_path}")
