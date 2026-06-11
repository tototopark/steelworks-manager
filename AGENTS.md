# AGENTS.md

## Role

- This is the canonical policy document for the steelworks-manager repository.
- Read it first for planning, editing, testing, and finishing work.

## Core rules

- Plan before editing.
- Keep edits surgical.
- Update checklist.md and context-notes.md for non-trivial work.
- Test before saying done.
- Read the real error output before retrying.
- Do not touch unrelated files.
- Prefer docs-first changes when the work affects architecture, migration, or conventions.

## Project rules

- Keep code files small and focused.
- Target 300 lines or less per file when practical.
- Keep the folder structure shallow.
- Prefer at most 2 directory levels from the repository root.
- Centralize constants, environment values, and connection details in configs/app_config.py.
- Keep backend logic independent from frontend rendering.
- Design the data layer with repository patterns so SQLite can migrate to MySQL easily.
- All code modules in the backend must run as standalone scripts via __main__.

## Scope

- Shared rules belong here.
- Claude-specific compatibility belongs in CLAUDE.md.
- Hook routing belongs in HOOKS_GUIDE.md.
