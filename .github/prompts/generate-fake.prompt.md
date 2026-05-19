---
description: 'Generate a lightweight ''fake'' of an application for downstream integration testing. Use when the user asks to "generate a fake", "create a fake of this app", "build a test double for this service", "scaffold a fake", "make a mock service", or "produce a stand-in I can test against". The skill inspects the current codebase, discovers every external integration surface (HTTP, queues, gRPC, databases, etc.), and produces a runnable Python (FastAPI) or Node (Fastify) fake under /fake/ along with a Dockerfile, docker-compose snippet, README, fragility report, consumer config example, and a manifest that records exactly what was generated and from which sources.'
name: 'generate-fake'
agent: 'agent'
---
<!-- GENERATED from skills/generate-fake/SKILL.md by scripts/sync-skills.py. Do not edit by hand. -->

# generate-fake

You are generating a **fake** of the application in the current working directory. A fake is a dramatically simplified stand-in for the real application: it exposes the same integration surfaces, returns realistic-enough responses (canned or via simple deterministic transforms), and runs on a laptop with one command.

> Reference reading — load these as you encounter the relevant step:
> - `../../skills/generate-fake/reference/discovery.md` — how to find integration surfaces
> - `../../skills/generate-fake/reference/fidelity-rubric.md` — when to use a canned stub vs a simple transform
> - `../../skills/generate-fake/reference/fragility-rubric.md` — how to flag risky surfaces
> - `../../skills/generate-fake/reference/manifest-schema.md` — the `fake.manifest.yaml` format
> - `../../skills/generate-fake/reference/templates/` — starter files for Python and Node fakes

## When to run this skill

Trigger when the user wants a first-time fake. If `/fake/fake.manifest.yaml` already exists, **stop and suggest the `update-fake` skill instead** — running `generate-fake` again would clobber human edits.

## Workflow

Follow these steps in order. Confirm with the user before any step that creates or modifies files.

### 1. Detect the application

Determine:

- **Language and framework** (look at `package.json`, `pyproject.toml`/`requirements.txt`, `pom.xml`/`build.gradle`, `go.mod`, `Gemfile`, `*.csproj`, `Cargo.toml`).
- **Repo layout** — monorepo vs single service. Ask the user which service to fake if ambiguous.
- **Entry point(s)** — `main`, `app.py`, `server.ts`, etc.

Report what you found and confirm you've identified the right application before going further.

### 2. Discover integration surfaces

Open `../../skills/generate-fake/reference/discovery.md` and follow it. The short version:

1. **Specs first** — look for `openapi.{yaml,yml,json}`, `swagger.{yaml,json}`, `asyncapi.{yaml,json}`, `*.proto`, GraphQL SDL files. If found, parse them — they are the contract.
2. **Then code** — scan controllers/routers/handlers, message-bus subscribers/publishers, data-access layers, external HTTP clients, scheduled jobs.
3. **Then infra** — `docker-compose.yml`, k8s manifests, Terraform, Helm charts often reveal which queues, topics, databases, and external URLs the app actually talks to.
4. **Then tests** — integration tests often enumerate the integration surfaces by example.

For each surface, record: kind (HTTP route / queue / topic / gRPC method / DB table / external HTTP client / file / clock / RNG), direction (inbound or outbound), schema, and the source file you learned it from.

If you find nothing — no specs and no clear handlers — stop and tell the user; the codebase may be in a shape that needs a human to point you at the right files.

### 3. Choose the fake language

- Default to **Python 3.11 + FastAPI + Pydantic** for HTTP surfaces.
- If the source app is JS/TS, switch the default to **Node 20 + Fastify + zod** to match the team's idiom.
- Always offer the user the choice before generating; pick the recommended default if they don't care.

Other building blocks (independent of HTTP-server choice):

- **Queues**: in-process consumers/producers backed by an in-memory broker (no real Kafka/Rabbit needed). Document a `--use-real-broker` flag for the consumer to point at a real broker if desired.
- **Databases**: **SQLite** (Python: `sqlite3`; Node: `better-sqlite3`) for any persistent stand-in. Schema is generated from the inferred models.
- **gRPC**: only generate a fake gRPC server if the source app actually exposes gRPC. Use `grpcio` (Python) or `@grpc/grpc-js` (Node).
- **External HTTP clients** the app calls outbound: don't fake — instead, document in `FRAGILITY.md` that the consuming test must point those at *their* own fakes.

### 4. Decide fidelity per surface

Open `../../skills/generate-fake/reference/fidelity-rubric.md`. For each surface, mark it as one of:

- **canned** — single static response example (most endpoints).
- **transform** — a small deterministic function (e.g. echo the request ID, compute `amount * rate`, return `now()` shifted by an offset, reverse a string, look up a value in a constants table).
- **stateful-lite** — keep an in-memory map keyed by something obvious (e.g. POST `/users` writes to an in-memory dict, GET `/users/{id}` reads from it). Only use this when the canned-or-transform choice would clearly fail the consuming test.

Bias toward `canned`. Mark sparingly as `stateful-lite` — every stateful endpoint is a maintenance liability.

Record the choice per surface in the manifest.

### 5. Generate the fake

Create the following under `/fake/` in the application repo (or under `--output-dir` if the user specifies a different location):

```
fake/
├── app.py  or  app.js            # the fake server entrypoint
├── routes/                       # one file per HTTP route group (if many)
├── consumers/                    # one file per queue subscription
├── producers/                    # one file per queue publication
├── grpc/                         # only if needed
├── data/
│   └── seed.sqlite               # only if any surface is stateful-lite
├── Dockerfile
├── docker-compose.fake.yaml      # snippet ready to compose into the consuming project
├── consumer-config.example.env   # env vars to point a real app at the fake
├── README.md                     # what's faked, how to run, how to extend
├── FRAGILITY.md                  # surfaces flagged as risky + suggestions
└── fake.manifest.yaml            # machine-readable record of what you generated
```

Use the templates in `../../skills/generate-fake/reference/templates/` as starting points. Adapt — do not copy verbatim; the names, routes, and schemas should come from the actual app.

### 6. Write the manifest

The `fake.manifest.yaml` is critical — `update-fake` depends on it. Follow `../../skills/generate-fake/reference/manifest-schema.md` exactly. Record:

- Plugin and skill version, generation timestamp, generator (Claude model version if known).
- Application language/framework.
- For each discovered surface: kind, direction, schema, fidelity choice, source file paths, and a SHA-256 of each source file's content at generation time.
- For each spec used: filename and SHA-256.
- The git SHA of the application repo HEAD at generation time.

### 7. Write the README

Inside `/fake/README.md`, cover:

- **What this fake is.** A one-paragraph explanation aimed at a developer who has never seen it.
- **Run it.** `docker compose -f docker-compose.fake.yaml up` (or the equivalent), plus how to run without Docker.
- **What's faked.** A table: surface → kind → fidelity → notes.
- **What's NOT faked.** Anything you skipped, and why.
- **How to extend it.** Where to add new routes/consumers, how to bump fidelity, where to regenerate seed data.
- **How to keep it in sync.** Pointer to `update-fake`.

### 8. Write the fragility report

Inside `/fake/FRAGILITY.md`, list surfaces or patterns flagged using `../../skills/generate-fake/reference/fragility-rubric.md`. For each, write:

- The surface (path / queue / table).
- Why it's fragile (e.g. "no schema in code; inferred from one example response").
- A concrete suggestion to improve it in the *real* application (e.g. "add an OpenAPI definition", "introduce a typed DTO", "version the queue topic").

This report is part of the value — it tells the application team where their integration surfaces are weakest.

### 9. Write the consumer config example

Inside `/fake/consumer-config.example.env`, list env vars a consuming app sets to point at the fake instead of the real dependency. Use the patterns in `../../skills/generate-fake/reference/templates/consumer-config.example.env`.

### 10. Verify

Before declaring done:

- Run a quick syntactic check on the fake's source (e.g. `python -m py_compile fake/app.py` or `node --check fake/app.js`).
- Confirm the Dockerfile builds (if the user permits running Docker).
- Spot-check 2–3 surfaces end-to-end: send a sample request, confirm the response shape matches the source app's contract.

### 11. Summarise

Print a short report:

- Application: <name>, <language/framework>.
- Surfaces discovered: <N> (broken down by kind).
- Fidelity mix: <X canned, Y transform, Z stateful-lite>.
- Top 3 fragility findings.
- Files created (just paths, no contents).
- Suggested next step: `cd fake && docker compose -f docker-compose.fake.yaml up`.

## Things to avoid

- **Don't fake outbound dependencies.** If the app calls `https://api.stripe.com`, the fake's job isn't to replace Stripe — that's the consuming application's problem. Document it in `FRAGILITY.md` instead.
- **Don't invent endpoints.** If a route isn't in the spec or the code, don't create it in the fake.
- **Don't bring in heavy dependencies.** No databases other than SQLite. No real Kafka/Rabbit/Redis. The fake must run on a laptop without extra infra.
- **Don't overwrite human edits.** If `/fake/` exists and `fake.manifest.yaml` is present, stop and refer the user to `update-fake`.
- **Don't delete anything.** Never remove files outside the new `/fake/` folder. If you would need to (e.g. cleaning up an old partial fake), ask the user first.
