"""
configs/app_config.py
Provides global system configurations, database connections, static paths,
and constants for the steelworks-manager application.
"""

import os

# Database configurations
DB_TYPE = "sqlite"  # Options: "sqlite", "mysql"

# SQLite paths
SQLITE_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "steelworks.db"
)

# MySQL connection settings (For future migration)
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "pengelly_jumbo",
    "password": "!a>6+Bfr82iB",
    "database": "pengelly_jumbodra_DB"
}

# Legacy SQL path for migration (Relative path dynamic lookup)
LEGACY_SQL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "backup-8.15.2024_19-39-32_pengelly-111",
    "mysql",
    "pengelly_jumbodra_DB-Dev.sql"
)

# Logging configuration
LOG_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
    "pipeline.log"
)

# UI feature flags
AUTO_FILL_ENABLED = True
SHOW_DEV_HINTS = True

# Super Admin Fallback (Emergency access bypassing DB)
ENABLE_SUPER_ADMIN = True
SUPER_ADMIN_LOGIN = "admin"
SUPER_ADMIN_PASS = "12345678"
