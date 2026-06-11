# CLAUDE.md

## Role

- Claude-specific compatibility note for the steelworks-manager repository.
- Follow AGENTS.md as the shared source of truth.

## Core Guidelines

1. Think before coding: Do not make arbitrary assumptions. Ask questions to clarify ambiguous requirements before modifying code.
2. Simplicity first: Avoid over-engineering (unnecessary configuration layers, unused classes, excessive exception trapping). Implement the minimum code that resolves the problem.
3. No emojis or special symbols: To prevent Unicode decoding errors, do not use emojis in code, terminal output, scripts, or markdown documentation.
4. Fail-Fast: Do not suppress exceptions. If an error occurs, halt execution immediately and propagate the error.
5. Resume functionality: If individual assets or states already exist, bypass execution steps and resume from the last valid point.
