"""
tests/import_legacy.py
Ingests legacy MariaDB SQL backup dump file and migrates records into local SQLite database.
Runs as a one-time migration utility.
"""

import os
import sys
import re
import sqlite3

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from core import db_client
from configs import app_config

def clean_sql_value(val):
    """
    Cleans SQL string values for insertion into SQLite.
    Converts 'NULL' to None, strips surrounding quotes, and unescapes quotes.
    """
    val = val.strip()
    if val.upper() == "NULL":
        return None
    
    # Strip quotes
    if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
        val = val[1:-1]
        
    # Unescape escaped single quotes \' or double quotes \"
    val = val.replace("\\'", "'").replace('\\"', '"').replace("\\r\\n", "\n").replace("\\n", "\n")
    return val

def parse_insert_values(values_str):
    """
    Parses values block: (val1, val2, ...), (val3, val4, ...)
    Respects single quoted string boundaries.
    """
    records = []
    # Regular expression to extract matches inside parentheses: (...)
    # while ignoring commas inside single quotes.
    # We step through the string to properly handle quotes and parentheses.
    in_str = False
    str_char = None
    current_record = []
    current_val = []
    
    i = 0
    length = len(values_str)
    while i < length:
        char = values_str[i]
        
        # Handle string escape characters
        if char == '\\' and i + 1 < length:
            current_val.append(values_str[i:i+2])
            i += 2
            continue
            
        if (char == "'" or char == '"') and (i == 0 or values_str[i-1] != '\\'):
            if not in_str:
                in_str = True
                str_char = char
                current_val.append(char)
            elif char == str_char:
                in_str = False
                str_char = None
                current_val.append(char)
            else:
                current_val.append(char)
        elif char == '(' and not in_str:
            current_record = []
            current_val = []
        elif char == ')' and not in_str:
            # End of a record
            val_str = "".join(current_val).strip()
            if val_str:
                current_record.append(clean_sql_value(val_str))
            records.append(current_record)
            current_record = []
            current_val = []
        elif char == ',' and not in_str:
            val_str = "".join(current_val).strip()
            current_record.append(clean_sql_value(val_str))
            current_val = []
        else:
            current_val.append(char)
        i += 1
        
    return records

def import_legacy_data():
    sql_path = app_config.LEGACY_SQL_PATH
    print(f"Reading legacy database dump from: {sql_path}")
    
    if not os.path.exists(sql_path):
        print(f"ERROR: Legacy SQL dump file not found at {sql_path}")
        sys.exit(1)
        
    # We read line by line to keep memory consumption low
    # because the SQL file could be large (up to 15MB)
    conn = db_client.get_connection()
    cursor = conn.cursor()
    
    insert_pattern = re.compile(r"^INSERT INTO `(\w+)` \((.*?)\) VALUES\s*(.*)$", re.IGNORECASE)
    
    try:
        # Disable journal and sync temporarily for rapid insertion speed
        cursor.execute("PRAGMA synchronous = OFF")
        cursor.execute("PRAGMA journal_mode = MEMORY")
        
        with open(sql_path, "r", encoding="utf-8", errors="ignore") as f:
            current_insert = []
            in_insert = False
            table_name = ""
            columns = []
            
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                
                # Check for start of INSERT statement
                match = insert_pattern.match(stripped)
                if match:
                    # If we had a previous multi-line insert, process it first
                    if in_insert and current_insert:
                        full_val_str = "".join(current_insert).rstrip(';')
                        records = parse_insert_values(full_val_str)
                        if records:
                            placeholders = ", ".join(["?"] * len(columns))
                            sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                            cursor.executemany(sql, records)
                        current_insert = []
                        
                    table_name = match.group(1)
                    cols_str = match.group(2)
                    columns = [c.replace('`', '').strip() for c in cols_str.split(',')]
                    
                    val_str = match.group(3)
                    current_insert.append(val_str)
                    in_insert = True
                    
                    # If this single line already contains the closing semicolon
                    if stripped.endswith(";"):
                        full_val_str = "".join(current_insert).rstrip(';')
                        records = parse_insert_values(full_val_str)
                        if records:
                            placeholders = ", ".join(["?"] * len(columns))
                            sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                            cursor.executemany(sql, records)
                        current_insert = []
                        in_insert = False
                elif in_insert:
                    current_insert.append(stripped)
                    if stripped.endswith(";"):
                        full_val_str = "".join(current_insert).rstrip(';')
                        records = parse_insert_values(full_val_str)
                        if records:
                            placeholders = ", ".join(["?"] * len(columns))
                            sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                            cursor.executemany(sql, records)
                        current_insert = []
                        in_insert = False
            
            # Process any final trailing block
            if in_insert and current_insert:
                full_val_str = "".join(current_insert).rstrip(';')
                records = parse_insert_values(full_val_str)
                if records:
                    placeholders = ", ".join(["?"] * len(columns))
                    sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    cursor.executemany(sql, records)
                    
        conn.commit()
        print("Legacy Data Ingested Successfully into SQLite.")
    except Exception as e:
        conn.rollback()
        print(f"DATA IMPORT FAILURE: {str(e)}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import_legacy_data()
