# Fidelity rubric — canned, transform, or stateful-lite?

Each surface in a fake gets exactly one fidelity choice. Bias toward the simplest option that still lets a consuming test pass meaningfully.

## The three options

### `canned` — single static response

Use when:
- The endpoint returns a fixed shape and the consumer cares about *shape*, not *content*.
- A frozen example from the spec or a recorded response is enough.
- Most read endpoints with no input-dependent variability fit here.

**Examples:**
- `GET /health` → `{"status": "ok"}`
- `GET /version` → `{"version": "1.0.0"}`
- `GET /users/{id}` → a single canned user payload regardless of the id.

### `transform` — small deterministic function of the input

Use when:
- Returning the *same* response for *every* input would confuse the consumer test (e.g. tests that check "the returned id equals the id I asked for").
- A trivial function — echo, look up in a tiny constant table, simple arithmetic, deterministic templating — captures enough of the real behaviour.

**Examples:**
- `GET /users/{id}` → return the canned shape but with the requested `id` echoed in.
- `POST /orders` → echo the request, fill in `id = "ord_" + hash(body)[:8]`, set `created_at = "2026-01-01T00:00:00Z"`, status = `"accepted"`.
- `GET /exchange-rate?from=USD&to=GBP` → look up a small constants table; fall back to `1.0` if the pair isn't in the table.
- `GET /now` → a fixed clock, or `"2026-01-01T00:00:00Z" + n_calls_seconds`.

**Rules for transforms:**
- They must be **pure** and **deterministic**. No `random()`, no real `now()`, no DB hits.
- Keep them under ~10 lines. If the transform is longer, you're recreating the real app — that's no longer a fake.
- Use a small Python/Node module per surface for clarity; don't pile transforms into one big switch.

### `stateful-lite` — in-memory read/write

Use when:
- A consumer test needs to write then read back the same resource within one test, and a `transform` would not survive the round-trip.
- Example: "POST a user, then GET the user, then assert the user exists."

**Rules:**
- State lives in an in-memory dict/map, or in `data/seed.sqlite` for richer queries.
- State is process-local and is reset on container restart (offer a `POST /__reset` admin endpoint for tests to call between cases).
- No durability, no concurrency safety beyond a single async lock if needed.
- Limit to the surfaces that *actually* need it. Every stateful endpoint is a maintenance liability.

## How to decide — flowchart

```
                    Is the response shape fixed and
                    independent of any input?
                              │
                       ┌──────┴──────┐
                       Yes           No
                       │             │
                    canned     Would a 1-line
                               echo/lookup/arith
                               be enough?
                                     │
                              ┌──────┴──────┐
                              Yes           No
                              │             │
                          transform     Does a test
                                        write-then-read
                                        within itself?
                                              │
                                       ┌──────┴──────┐
                                       Yes           No
                                       │             │
                                stateful-lite     canned
                                                  (and flag in
                                                  FRAGILITY.md)
```

## Special cases

- **Bulk endpoints (`GET /users?limit=N`).** Default to `transform`: return a slice of a canned list sized to the request. If the consumer asserts on stable ordering or pagination tokens, escalate to `stateful-lite`.
- **Search endpoints.** Default to `canned` unless the test cares about query terms; if so, `transform` with a tiny constants table mapping queries → results.
- **Auth endpoints.** Default to `transform` — accept any well-formed credential, return a deterministic token. Document this clearly in `README.md`; never ship a real auth implementation in a fake.
- **Webhook receivers.** Default to `canned` with a `204 No Content`. Optionally log to stdout so the consumer test can assert on logs.
- **gRPC streaming.** Default to `transform` — emit a small fixed sequence and close. Avoid `stateful-lite` for streams.

## What to record in the manifest

For each surface:

```yaml
fidelity: canned | transform | stateful-lite | sqlite | passthrough
cannedExample: <object>           # for canned
transform:
  description: "<plain-English description of the transform>"
  reference: "<path to a small module in the fake that implements it>"
stateLifetime: process | seed     # for stateful-lite (seed = restored from data/seed.sqlite on startup)
```
