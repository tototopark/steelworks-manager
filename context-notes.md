# context-notes.md

## Running Decision Log

### 2026-06-11
- **SQLite / MySQL Portability**: Decided to isolate `pymysql` inside conditional DB drivers block in `db_client.py`. This avoids library dependencies errors when running local SQLite database.
- **Task/NCR/RFI Rules**: Parsed legacy PHP behaviors where items starting with 'task', 'ncr', 'rfi' bypass standard workshop fabrication steps. They are instantly initialized as completed, and installation state becomes 'temp installed'.
- **Lot State Upgrades**: Embedded triggers inside job pipeline so that when the final fabricated item under a Lot is marked as made, the lot's install status is automatically upgraded to 'ready' to alert installers.
- **Attribution & Versioning**: Added automatic version numbering for NDT audits inside `tb_wip` increasing by 1 on every inspection edit.
- **Folder nesting restriction**: Cleanly isolated 1-time setup tools (db_init, import_legacy, mock_generator, smoke_check) into `tests/` and runtime tasks to `skills/` keeping directory nesting depth strictly to 2 levels.
