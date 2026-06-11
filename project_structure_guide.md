# project_structure_guide.md

## Goal

- Keep the repository understandable, shallow, and easy to migrate.
- Prefer small files and clear boundaries over deep folder nesting.

## Target structure

```text
steelworks-manager/
  AGENTS.md
  CLAUDE.md
  HOOKS_GUIDE.md
  README.md
  project_docs_compendium.md
  project_structure_guide.md
  configs/
    app_config.py           # Central config, variables, paths, database URI
  core/
    db_client.py            # SQLite/MySQL abstraction client (Repository base)
    pipeline_runner.py      # Sequentially runs python steps
  skills/
    010_job_pipeline.py     # Handle job-related ingestion and processing
    020_task_pipeline.py    # Handle task assignment and state changes
    030_punch_pipeline.py   # Handle timesheets and punchsheets
    040_inspect_pipeline.py # Handle WIP and third-party inspection data
  data/
    steelworks.db           # Local SQLite database file
  tests/                    # Location for database initialization, migrations, and test scripts
    db_init.py              # Init database schemas (SQLite / MySQL) - One-time execution
    import_legacy.py        # Import data from legacy SQL file into SQLite - One-time execution
    mock_data_generator.py  # Mock data insertion tool
    mock_data_cleaner.py    # Target mock data cleanup tool preserving legacy records
    db_inspector.py         # DB Viewer & Inspector tool
    extract_schemas.py      # Schema extraction utility
    schemas.txt             # Extracted legacy table schemas
  수정/                     # Session modifications and plans
```

## Rules

- Keep folder depth to 2 levels max.
- If a concern grows, split by file instead of adding deep folders.
- Keep shared constants in configs/.
- Keep backend logic independent from frontend rendering.
- Keep data access behind a small repository or gateway layer (core/db_client.py).
- All steps inside skills/ must contain a runnable `__main__` entrypoint.

## Migration rule

- Write SQL and schemas so SQLite and MySQL differences stay contained in the data layer (core/db_client.py).
- Avoid relying on SQLite-only behavior in business logic.
