# Atomic

**A Claude Code plugin and framework for the MISSION+ ACDC / ATOM way of working.**

Atomic is a growing collection of composable Claude Code skills that put AI agents to work across the application lifecycle — testing, legacy code understanding, refactoring, documentation, observability, and more. Each skill is *atomic*: it does one thing well and composes with the others.

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

Drop this folder into the place Claude Code looks for plugins, or install it via your team's plugin marketplace.

The skills auto-activate when the user's prompt matches the trigger phrases declared in each `SKILL.md`.

## Plugin layout

```
atomic/
├── .claude-plugin/
│   └── plugin.json
├── skills/
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
└── README.md
```

## Design principles

- **Atomic.** Each skill does one thing and composes with the others. New capabilities arrive as new skills, not as bloat in existing ones.
- **Lightweight by default.** Where Atomic produces runtime artifacts (such as fakes), they use small stacks — Python (FastAPI) or Node (Fastify) — and aim to run on a laptop in one container.
- **Specs first, code second.** Where contracts exist (OpenAPI / AsyncAPI / proto), Atomic uses them as ground truth before inferring from code.
- **The application team owns the output.** Artifacts produced by Atomic (fakes today; other things tomorrow) live in the application repo, are reviewed in PRs, and travel with the code they describe.
- **Drift is treated as a first-class problem.** Every Atomic skill that produces a long-lived artifact also produces a manifest that lets a partner skill bring it back in sync later.
- **Always ask before applying breaking changes.** Atomic skills never silently mutate contract-affecting output without confirmation.

See each skill's `SKILL.md` for the full workflow.
