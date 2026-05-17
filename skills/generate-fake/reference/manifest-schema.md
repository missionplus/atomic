# `fake.manifest.yaml` schema

The manifest is the single source of truth that `update-fake` reads to detect drift. Write it precisely.

## Example

```yaml
schemaVersion: 1
fake:
  name: orders-service-fake
  generatedAt: 2026-05-16T11:32:00Z    # immutable — set once by generate-fake
  lastUpdatedAt: 2026-05-16T11:32:00Z  # mutable — bumped by every update-fake run
  generatorPlugin:
    name: atomic
    version: 0.1.0
    skill: generate-fake
  application:
    repoRoot: ../
    repoHeadSha: e3a17b2c8f...   # git rev-parse HEAD at generation time
    language: python
    framework: fastapi
    runtimeImage: python:3.11-slim
  fakeRuntime:
    language: python
    framework: fastapi
    image: python:3.11-slim
specs:
  - path: openapi.yaml
    sha256: 8a4f...                # SHA-256 of the file contents
  - path: events/asyncapi.yaml
    sha256: 1f9c...
surfaces:
  - id: h1
    kind: http
    direction: inbound
    method: GET
    path: /users/{id}
    requestSchema: null
    responseSchema:
      $ref: "#/components/schemas/User"
    fidelity: canned
    cannedExample:
      id: "u_123"
      email: "alice@example.com"
      created_at: "2026-01-01T00:00:00Z"
    sourceFiles:
      - path: openapi.yaml
        sha256: 8a4f...
      - path: src/routes/users.py
        sha256: c20a...
    confidence: spec
    fragility: []
  - id: h2
    kind: http
    direction: inbound
    method: POST
    path: /orders
    requestSchema: CreateOrder
    responseSchema: Order
    fidelity: transform
    transform:
      description: "Echo the request body, assign a synthetic order id, set status='accepted', set created_at=now()."
    sourceFiles:
      - path: src/routes/orders.py
        sha256: f10b...
    confidence: code
    fragility:
      - "No request schema declared in spec; inferred from Pydantic model in code."
  - id: q1
    kind: queue
    direction: inbound
    topic: payments.received
    requestSchema: PaymentReceived
    fidelity: stateful-lite
    note: "Writes to in-memory map keyed by payment_id so the read-side endpoint /payments/{id} can return it."
    sourceFiles:
      - path: events/asyncapi.yaml
        sha256: 1f9c...
      - path: src/consumers/payments.py
        sha256: 9bbe...
    confidence: spec
    fragility: []
  - id: db1
    kind: db
    direction: internal
    table: users
    fidelity: sqlite
    note: "Schema derived from SQLAlchemy model in src/models/user.py."
    sourceFiles:
      - path: src/models/user.py
        sha256: 4f33...
    confidence: code
    fragility:
      - "No migration files found; schema inferred only from ORM models."
outboundDependencies:
  # NOT faked — recorded so consumers know to provide their own fakes.
  - id: out1
    kind: external_http
    target: https://api.stripe.com
    methods:
      - POST /v1/charges
    sourceFiles:
      - path: src/payments/stripe_client.py
        sha256: 71aa...
notFaked:
  - reason: outbound_dependency
    surfaces: [out1]
  - reason: out_of_scope
    surfaces: []
fragilityFindings:
  - severity: high
    surface: h2
    finding: "Schema only present in code, not in spec."
    suggestion: "Add `CreateOrder` and `Order` schemas to openapi.yaml; regenerate this fake."
  - severity: medium
    surface: db1
    finding: "No migrations; ORM models are the only schema source."
    suggestion: "Adopt Alembic migrations so the fake's SQLite stand-in tracks the real schema."
```

## Field rules

- **`schemaVersion`** — integer. Bump whenever a breaking change is made to this schema. Current: `1`.
- **`generatedAt`** — RFC 3339 timestamp; set once by `generate-fake` and never modified afterwards.
- **`lastUpdatedAt`** — RFC 3339 timestamp; refreshed on every `update-fake` run that touches the manifest. On first generation, equal to `generatedAt`.
- **`sha256`** — lowercase hex of the SHA-256 of the file content at generation time.
- **`fidelity`** — one of `canned`, `transform`, `stateful-lite`, `sqlite` (for DB-kind surfaces), `passthrough` (rarely used; for surfaces deliberately left as no-ops).
- **`confidence`** — one of `spec`, `code`, `infer`.
- **`fragility`** — per-surface list of short strings; the aggregate is also written to `FRAGILITY.md`.
- **Paths** — always relative to the application repo root, using forward slashes.

## What `update-fake` does with this file

1. Reloads every file listed in `sourceFiles` and `specs`; computes SHA-256 anew; compares to recorded.
2. Runs `git log` for paths in `sourceFiles` since `repoHeadSha`.
3. Reports drift, classified by severity, before changing anything.

If you change the schema, `update-fake` must handle the older `schemaVersion` gracefully or refuse and ask the user to regenerate.
