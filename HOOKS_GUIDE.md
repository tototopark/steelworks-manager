# HOOKS_GUIDE.md

## Purpose

- This repository keeps shared policy in AGENTS.md.
- Surface-specific guidance stays minimal and only adds compatibility notes.

## Current stance

- No extra hook routing is required right now.
- If .claude/settings.json or .codex/hooks.json is added later, keep the shared rules in AGENTS.md and place only surface-specific behavior there.

## Rule

- Do not duplicate long policy blocks across hook files.
- Keep hook messages short and purpose-specific.
