# Atomic

**An agent-agnostic plugin and framework for the MISSION+ ACDC / ATOM way of working.**

Atomic is a growing collection of composable agent skills that put AI coding assistants to work across the application lifecycle — testing, legacy code understanding, refactoring, documentation, observability, and more. Each skill is *atomic*: it does one thing well and composes with the others.

Skills ship in three formats from a single canonical source: **Claude Code skills**, **OpenAI Codex skills**, and **GitHub Copilot prompt files**.

This release (v0.1.0) ships two skills focused on **testability**, specifically the problem of standing up cheap, owner-maintained **fakes** of real applications so downstream teams can test against them. Future releases will extend Atomic into other ACDC / ATOM problem spaces.

## What's in v0.1.0 — Testability

A **fake** is a dramatically cut-down version of an application that:

- Exposes the same integration surfaces (HTTP APIs, message queues, gRPC, database stand-ins, etc.) as the real application.
- Returns either canned responses or simple, deterministic transformations of the input.
- Runs in a single Docker container (or a tiny Python/Node process) on a laptop.
- Is owned by the application's team, version-controlled alongside the application, and kept in sync over time.

Fakes let downstream applications run their own integration tests without standing up the real (often complex, costly, or rate-limited) dependency.

| Skill | Trigger phrases | What it does |
|-------|-----------------|--------------|
| `generate-fake` | "generate a fake", "create a fake of this app", "build a test double for this service" | Inspects the current application, discovers every integration surface, generates a fake under `/fake/`, and produces a Dockerfile, README, fragility report, consumer-config snippet, and a manifest. |
| `update-fake` | "update the fake", "refresh the fake", "check the fake for drift" | Reads `/fake/fake.manifest.yaml`, runs three drift signals (spec diff, source-code diff, git history), proposes or applies changes, and updates the manifest. |

## Roadmap

Atomic is intentionally modular — each skill stands on its own and is added independently. Likely future additions across the ACDC / ATOM problem space include (non-exhaustive, not committed):

**More testability:**
- `verify-fake` — run the real application's integration suite against the fake and report any divergence.
- `fake-from-traffic` — generate or refine a fake from recorded request/response traffic (HAR, OTel traces, recorded message buses).
- `publish-fake` / `consume-fake` — version, tag, publish, and consume fakes as OCI images.

**Legacy code & refactoring:**
- Skills that help engineers understand, characterise, and safely refactor large unfamiliar codebases — aligned with MISSION+'s agentic management of legacy code approach.

**Documentation & observability:**
- Skills that generate and maintain living technical documentation; skills that propose missing telemetry from code.

**ACDC / ATOM lifecycle support:**
- Skills that map to specific stages of the ACDC / ATOM way of working — to be filled in as the framework matures.

If you want any of these prioritised, raise the request via your usual channel.

## Installation

Atomic ships in three agent-native formats from one canonical source.

### Claude Code

Drop this folder into the place Claude Code looks for plugins, or install it via your team's plugin marketplace. Skills auto-activate when the user's prompt matches the trigger phrases declared in each `SKILL.md`.

### OpenAI Codex

Codex discovers skills under `.agents/skills/` at the repo root. Atomic ships that directory as a symlink to `skills/`, so the same `SKILL.md` files serve both Claude and Codex. Run `python3 scripts/sync-skills.py` if you're on Windows or the symlink isn't resolving — it'll materialize `.agents/skills/` as a copy.

In Codex, skills can be invoked implicitly (matched on description) or explicitly (`/skills` or `$skill-name`).

### GitHub Copilot

Copilot reads slash-command prompts from `.github/prompts/`. Atomic ships generated prompt files (`/generate-fake`, `/update-fake`) and a repo-wide `.github/copilot-instructions.md` index. Unlike Claude and Codex, Copilot only invokes prompts **explicitly** via slash command — there's no implicit match-on-description.

Regenerate the prompt files after editing any `SKILL.md`:

```
python3 scripts/sync-skills.py
```

## Plugin layout

```
atomic/
├── .claude-plugin/
│   └── plugin.json                      # Claude Code plugin manifest
├── skills/                              # CANONICAL — edit these
│   ├── generate-fake/
│   │   ├── SKILL.md
│   │   └── reference/
│   │       ├── discovery.md
│   │       ├── manifest-schema.md
│   │       ├── fragility-rubric.md
│   │       ├── fidelity-rubric.md
│   │       └── templates/
│   │           ├── python-fastapi.py
│   │           ├── node-fastify.js
│   │           ├── Dockerfile.python
│   │           ├── Dockerfile.node
│   │           ├── docker-compose.fake.yaml
│   │           └── consumer-config.example.env
│   └── update-fake/
│       ├── SKILL.md
│       └── reference/
│           ├── diff-strategy.md
│           └── changelog-template.md
├── .agents/
│   └── skills -> ../skills              # Codex (symlink; or materialized copy on Windows)
├── .github/
│   ├── copilot-instructions.md          # Copilot repo-wide index
│   └── prompts/                         # GENERATED from skills/ — do not hand-edit
│       ├── generate-fake.prompt.md
│       └── update-fake.prompt.md
├── scripts/
│   └── sync-skills.py                   # regenerate Copilot prompts + .agents/skills on Windows
└── README.md
```

## How activation differs across tools

| Tool | Discovery path | Activation | Frontmatter |
|------|----------------|------------|-------------|
| Claude Code | `skills/<name>/SKILL.md` | Implicit (description match) | `name`, `description` |
| OpenAI Codex | `.agents/skills/<name>/SKILL.md` | Implicit (description match) or `/skills` / `$skill-name` | `name`, `description` (same format) |
| GitHub Copilot | `.github/prompts/<name>.prompt.md` | Explicit (`/skill-name` only) | `name`, `description`, `agent` |

The Claude and Codex SKILL.md formats are identical, so the same file serves both. Copilot's prompt files differ enough to need generation (different frontmatter, and relative `reference/...` links need rewriting to resolve from `.github/prompts/`).

## Design principles

- **Atomic.** Each skill does one thing and composes with the others. New capabilities arrive as new skills, not as bloat in existing ones.
- **Lightweight by default.** Where Atomic produces runtime artifacts (such as fakes), they use small stacks — Python (FastAPI) or Node (Fastify) — and aim to run on a laptop in one container.
- **Specs first, code second.** Where contracts exist (OpenAPI / AsyncAPI / proto), Atomic uses them as ground truth before inferring from code.
- **The application team owns the output.** Artifacts produced by Atomic (fakes today; other things tomorrow) live in the application repo, are reviewed in PRs, and travel with the code they describe.
- **Drift is treated as a first-class problem.** Every Atomic skill that produces a long-lived artifact also produces a manifest that lets a partner skill bring it back in sync later.
- **Always ask before applying breaking changes.** Atomic skills never silently mutate contract-affecting output without confirmation.

See each skill's `SKILL.md` for the full workflow.
