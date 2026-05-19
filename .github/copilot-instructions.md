# Atomic — Copilot guidance

This repo ships **Atomic** skills as slash-command prompt files for GitHub Copilot in addition to its native Claude Code and Codex skill formats.

## Available prompts

Type `/` in the Copilot chat composer to discover them:

- `/generate-fake` — generate a lightweight fake of the current application for downstream integration testing
- `/update-fake` — detect drift between an existing fake and the real application, then refresh it

The prompt files live in `.github/prompts/` and are generated from the canonical SKILL.md files in `skills/`. Edit the SKILL.md, then run `python3 scripts/sync-skills.py` to regenerate.

## Activation differences vs Claude / Codex

Unlike Claude Code and Codex (which can implicitly auto-trigger a skill when the user's phrasing matches the skill description), Copilot only invokes prompt files **explicitly** via slash command. The trigger phrases in each prompt's `description` are kept anyway so the prompt picker shows useful hover text.
