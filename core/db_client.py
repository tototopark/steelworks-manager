"""
core/db_client.py
Encapsulates database operations, providing an abstraction layer supporting
both SQLite (for local development) and MySQL/MariaDB (for future production).
"""

import sqlite3
import os
import sys

# Set project root path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from configs import app_config

def get_connection():
    """
    Returns a database connection based on app_config.DB_TYPE.
    Halts execution immediately if the connection fails (Fail-Fast).
    """
    try:
        if app_config.DB_TYPE == "sqlite":
            # Ensure the directory exists
            db_dir = os.path.dirname(app_config.SQLITE_DB_PATH)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            conn = sqlite3.connect(app_config.SQLITE_DB_PATH)
            # Enable row factory to retrieve dictionaries
            conn.row_factory = sqlite3.Row
            return conn
        elif app_config.DB_TYPE == "mysql":
            import pymysql
            conn = pymysql.connect(
                host=app_config.MYSQL_CONFIG["host"],
                user=app_config.MYSQL_CONFIG["user"],
                password=app_config.MYSQL_CONFIG["password"],
                database=app_config.MYSQL_CONFIG["database"],
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn
        else:
            raise ValueError(f"Unknown database type: {app_config.DB_TYPE}")
    except Exception as e:
        print(f"DATABASE CONNECTION FAILURE: {str(e)}")
        sys.exit(1)

def execute_query(query, params=None):
    """
    Executes an INSERT, UPDATE, or DELETE query and returns the number of affected rows.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        return affected
    except Exception as e:
        print(f"QUERY EXECUTION FAILURE: {str(e)}\nQuery: {query}")
        sys.exit(1)
    finally:
        conn.close()

def fetch_all(query, params=None):
    """
    Executes a SELECT query and returns all matching records as a list of dictionaries.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        
        # Convert sqlite3.Row objects to standard python dictionaries
        if app_config.DB_TYPE == "sqlite":
            return [dict(row) for row in rows]
        return list(rows)
    except Exception as e:
        print(f"QUERY FETCH ALL FAILURE: {str(e)}\nQuery: {query}")
        sys.exit(1)
    finally:
        conn.close()

def fetch_one(query, params=None):
    """
    Executes a SELECT query and returns the first matching record as a dictionary,
    or None if no records are found.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        row = cursor.fetchone()
        cursor.close()
        
        if row and app_config.DB_TYPE == "sqlite":
            return dict(row)
        return row
    except Exception as e:
        print(f"QUERY FETCH ONE FAILURE: {str(e)}\nQuery: {query}")
        sys.exit(1)
    finally:
        conn.close()
