# Diff strategy — how to compare a fake against the real application

The three drift signals (spec, source, git history) overlap on purpose. Treat them as independent voters; a change found by two is more confident than one found by only one.

## 1. Spec diff

### What you need from the manifest

For each entry in `specs`:

- `path` — relative to the application repo root.
- `sha256` — the recorded fingerprint of the spec at generation time.

### How to run it

1. Read the current file at `path`. Compute SHA-256. Compare.
2. If different, fetch the prior version via `git show <repoHeadSha>:<path>` (where `repoHeadSha` comes from the manifest).
3. Parse both versions:
   - OpenAPI / Swagger: parse YAML/JSON; iterate `paths`, `components.schemas`.
   - AsyncAPI: iterate `channels` and `components.messages`.
   - Protobuf: parse with a proto parser; iterate `services[].method[]` and `message[]`.
   - GraphQL SDL: parse with a GraphQL parser; iterate types, fields, args.
4. Produce a structured diff:

```yaml
spec: openapi.yaml
changes:
  - kind: route_added
    method: GET
    path: /users/{id}/preferences
    responseSchema: UserPreferences
    classification: additive
  - kind: route_removed
    method: GET
    path: /legacy/orders
    classification: breaking
  - kind: schema_field_added
    schema: User
    field: timezone
    optional: true
    classification: additive
  - kind: schema_field_type_changed
    schema: Order
    field: status
    from: enum[accepted,shipped,cancelled]
    to: enum[accepted,shipped,cancelled,refunded]
    classification: breaking   # enum additions can break consumers that switch exhaustively
```

### Classification heuristics for spec changes

| Change | Default classification |
|---|---|
| New optional field | additive |
| New required field | breaking |
| Field removed | breaking |
| Field type changed | breaking |
| Field renamed (no alias) | breaking |
| Enum value added | breaking (consumers may exhaustively switch) |
| Enum value removed | breaking |
| New route | additive |
| Removed route | breaking |
| Status code changed | breaking |
| Response shape changed | breaking |
| Description / example changed | cosmetic |

Erring toward `breaking` is safer than the reverse.

## 2. Source code diff

For each `surfaces[].sourceFiles[].path`:

1. Read the current content; SHA-256; compare.
2. If different, fetch prior with `git show`.
3. Run a language-appropriate structural diff:

| Language | Tool / approach |
|---|---|
| Python | `ast` module; walk function defs, class defs, decorators. Compare signatures + decorator args. |
| TypeScript / JavaScript | `@typescript-eslint/parser` or `babel/parser`; walk export declarations + decorator/route metadata. |
| Java | Read class/method signatures + Spring/JAX-RS annotation values. |
| Go | `go/ast`; walk `FuncDecl`. |
| C# | Roslyn-style read of `[HttpGet]` etc. |

Don't use plain text diff — it's noisy. Compare at the level of "did this handler's route, request type, response type, or status code change?"

### Classification heuristics for source changes

- New `@app.get(...)` / `@RestController` method → additive (new endpoint).
- Removed handler → breaking.
- Handler's response type changed → breaking unless old type is a strict supertype of new.
- Decorator path or method changed → treat as removed-old + added-new.
- Handler body changed but signature unchanged → usually cosmetic from the fake's perspective; if the original fidelity was `transform`, re-review the transform.

## 3. Git history

`git log --name-status <repoHeadSha>..HEAD -- <paths>` gives commit-level context. Use it to:

- Surface **new** routes/handlers/specs that the manifest doesn't know about (the previous two signals only check files the manifest already lists).
- Cluster changes by intent — commits with `feat:` prefix in conventional-commits are more likely to be additive; `breaking change:` or `BREAKING CHANGE:` footers should escalate classification.
- Provide commit messages and authorship in the drift report — useful when the user has to make judgment calls.

Specifically run:

```
git log --pretty="%h %s%n%b" <repoHeadSha>..HEAD -- <recorded paths>
git log --diff-filter=A --name-only <repoHeadSha>..HEAD -- src/ openapi.yaml asyncapi.yaml
```

The second invocation catches newly-added files in directories that the original generation walked.

## Combining the signals

Build one unified list of drift items keyed by surface (route, schema, topic). For each, record:

- Which signal(s) detected it (spec / source / history).
- Default classification.
- The user-facing summary line.
- The patch instructions for the fake (only used if approved).

Sort the report so **breaking** changes come first, **additive** next, **cosmetic** last.

## When to refuse

Refuse to proceed and ask the user if:

- The `schemaVersion` in the manifest is newer or older than this skill supports.
- The recorded `repoHeadSha` is no longer reachable (fetch hasn't pulled it; user has rebased history).
- The application root has moved and the manifest's `repoRoot` no longer resolves.
- More than ~25% of surfaces show breaking changes — at that volume, regenerating from scratch is probably saner than patching; suggest the user re-run `generate-fake` after backing up the existing fake.
