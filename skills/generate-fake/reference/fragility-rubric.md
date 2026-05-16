# Fragility rubric

A "fragile" integration surface is one whose real behaviour is poorly defined, poorly documented, or in tension with the goals of low-friction testing. Surfacing these is half the value of the fake.

Use this rubric to mark surfaces during discovery and to write `FRAGILITY.md`.

## Severity levels

- **high** — the fake is likely to drift from reality silently, or a consumer test built against the fake might pass against the fake but fail against the real app.
- **medium** — the fake captures current reality but the contract is implicit and may change without notice.
- **low** — stylistic or hygiene concern; not blocking.

## Patterns to flag

### Schema and contract

- **No spec for an inbound HTTP API.** Severity: high. Suggestion: introduce OpenAPI/AsyncAPI; even a generated one is better than none.
- **Spec exists but doesn't match code** (e.g. the handler accepts fields the spec doesn't list). Severity: high. Suggestion: pick one source of truth.
- **Untyped request/response.** Endpoint takes `dict` / `any` / `Map<String,Object>`. Severity: high. Suggestion: introduce DTOs/Pydantic/zod schemas.
- **Implicit polymorphism** — endpoint returns one of several shapes depending on a hidden flag. Severity: medium. Suggestion: explicit discriminator field; or split into two endpoints.

### Messaging

- **Untyped queue payloads.** Severity: high. Suggestion: schema registry or AsyncAPI.
- **Topic name overloaded** — multiple distinct event types on one topic. Severity: high. Suggestion: split topics or add a `type` field with a closed enum.
- **Ordering-dependent consumer.** The consumer assumes message order but the broker doesn't guarantee it (e.g. multi-partition Kafka without keying). Severity: high. Suggestion: key by aggregate id, or rework to be order-independent.
- **No versioning** on the event schema. Severity: medium. Suggestion: include `schemaVersion` in every event.

### Data

- **No migrations** — ORM models are the only schema source. Severity: medium. Suggestion: introduce Alembic/Flyway/Prisma migrations.
- **Hard-coded references to external IDs** (e.g. a Stripe customer id appears in a fixture). Severity: medium. Suggestion: indirection via env var or a lookup table.

### External dependencies

- **External HTTP call with no timeout.** Severity: high. Suggestion: explicit timeout, retries, and circuit-breaker.
- **External call inside a synchronous request path** that has no fallback. Severity: high. Suggestion: cache, async, or graceful degradation.
- **Multiple competing SDKs for the same provider.** Severity: low. Suggestion: standardise.
- **Hard-coded URLs** (no env-var indirection). Severity: high. Suggestion: env var, so the consuming test can point at *its* fake.

### Time, randomness, identity

- **Direct `datetime.now()` / `Math.random()` / `uuid.uuid4()` calls** inside handler logic. Severity: medium. Suggestion: inject a clock/RNG/id-generator so tests can pin them.

### Observability and shape

- **Endpoint surfaces a 500 with no schema** for the error body. Severity: low. Suggestion: standardise error envelope (RFC 7807, etc.).
- **Endpoint returns differently shaped errors depending on path.** Severity: medium. Suggestion: standard error envelope.

### Configuration

- **Required env var with no `.env.example` entry.** Severity: medium. Suggestion: keep `.env.example` complete.
- **Secret read from environment but with no rotation story.** Severity: low. Suggestion: rotation hook + indirection.

## What a finding looks like in `FRAGILITY.md`

```markdown
## H2 — POST /orders

**Severity:** high
**Surface:** `POST /orders` (`src/routes/orders.py:22`)
**Finding:** Request and response schemas are only defined in code (Pydantic), not in the OpenAPI spec. The fake will drift silently if the model is changed.
**Suggestion:** Either generate the OpenAPI from the Pydantic models at build time, or define the schema once in the spec and import it into code.
```

Be specific. "Improve the schema" is not a finding; "Add `CreateOrder` and `Order` schemas to `openapi.yaml` and regenerate this fake" is.

## What does NOT belong here

- Bugs in the application that are unrelated to the integration surface.
- Performance complaints about the real app.
- Style/lint nitpicks.
- Anything the application team can't act on.

The fragility report is *for* the application team and *about* the contract their consumers rely on.
