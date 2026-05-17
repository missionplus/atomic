---
name: update-fake
description: Detect drift between an existing fake and the real application, then refresh the fake. Use when the user asks to "update the fake", "refresh the fake", "sync the fake", "check the fake for drift", "the fake is out of date", or whenever a fake's manifest is older than the application's current HEAD. The skill reads /fake/fake.manifest.yaml, runs three drift signals (spec diff, source-code diff, git history), classifies each drift item as additive / breaking / cosmetic, and proposes (or, with approval, applies) patches before updating the manifest and CHANGES.md.
---

# update-fake

You are updating an existing **fake** of the application in the current working directory. The fake was previously created by the `generate-fake` skill and recorded its inputs in `/fake/fake.manifest.yaml`. Your job is to bring it back into agreement with the real application.

> Reference reading:
> - `reference/diff-strategy.md` — how to run and interpret each drift signal
> - `reference/changelog-template.md` — how to update `CHANGES.md` and bump the manifest

## When to run this skill

- The application has changed and the fake is now stale.
- The user explicitly asks for a refresh.

If `/fake/fake.manifest.yaml` does NOT exist, stop and refer the user to `generate-fake`.

## Workflow

### 1. Load the manifest

Read `/fake/fake.manifest.yaml`. Confirm:

- `schemaVersion` is one this skill understands (current: `1`). If not, stop and ask the user; refuse to silently migrate.
- `fake.application.repoRoot` resolves. If it doesn't, ask the user where the application root is.

Print a short header: when the fake was generated, against which git SHA, in which language/framework.

### 2. Run the three drift signals

In order:

#### 2a. Spec diff

For each `specs[].path` recorded in the manifest:

1. Recompute SHA-256 of the file's current content.
2. If SHA matches recorded — no change for this spec.
3. If SHA differs — parse both versions (current and the version implied by the recorded SHA, if you can fetch it via `git show <repoHeadSha>:<path>`). Diff at the structural level: routes added/removed/changed, schemas added/removed/changed, queues added/removed/changed. Record the diff as a structured list, not as a textual patch.

If a spec referenced in the manifest no longer exists, mark as `spec_removed` (this is usually breaking).

If a spec exists in the repo but is not in the manifest, mark as `spec_added`.

#### 2b. Source code diff

For each `surfaces[].sourceFiles[].path`:

1. Recompute SHA-256.
2. If matched — no change for that source file.
3. If different — fetch the prior version via `git show <repoHeadSha>:<path>` and diff at a structural level appropriate to the file's language:
   - Routes/handlers: signature changes, new/removed endpoints, changed status codes, changed response types.
   - Schemas/models: added/removed/renamed fields, changed types, added validation.
   - Consumers/producers: changed topic, changed payload type.

If a source file is missing from the working tree, mark as `source_removed`.

#### 2c. Git history

Run `git log --name-status <repoHeadSha>..HEAD -- <every recorded sourceFiles path> <every recorded specs path>`.

Use the resulting log as a focus list — even files that ended at the same SHA but were touched along the way may have had behaviour-affecting changes you want to look at in context.

Also do `git log --diff-filter=A <repoHeadSha>..HEAD -- src/ openapi.yaml asyncapi.yaml` (or wherever specs live) to catch **newly added** routes/handlers/specs the manifest doesn't yet know about.

### 3. Classify each drift item

For every change you found, assign one of:

- **additive** — new endpoint, new optional field, new event topic, new queue subscription that doesn't break existing consumers. Safe to auto-patch.
- **breaking** — removed endpoint, removed field, renamed field, changed type, changed enum, changed status code, changed event shape. NEVER auto-apply. Always require human approval.
- **cosmetic** — comment changes, formatting, docstring edits, internal refactors that don't move the contract. Skip; record in the manifest with a fresh SHA but no behaviour change.

### 4. Present the drift report

Print a single, scannable report to the user. Group by classification:

```
DRIFT REPORT — orders-service-fake
Generated against repoHeadSha e3a17b2c → 9f12bcd1 (47 commits)

ADDITIVE (5)
  + GET /users/{id}/preferences            (openapi.yaml:142)
  + POST /orders/{id}/refund               (src/routes/orders.py:88)
  + topic orders.shipped                   (events/asyncapi.yaml:55)
  + field User.timezone (optional)         (openapi.yaml:201)
  + field Order.discount_code (optional)   (openapi.yaml:308)

BREAKING (2)
  ! removed: GET /legacy/orders            (openapi.yaml — deleted)
  ! changed: Order.status enum now [accepted, shipped, cancelled, refunded]
                                            (previously [accepted, shipped, cancelled])

COSMETIC (12)
  ~ docstring updates, formatting, comment changes — no fake change needed

OUT-OF-SCOPE OUTBOUND CHANGES (1)
  > src/payments/stripe_client.py — new method call; consumer-side concern.
```

### 5. Get approval

For **additive** items, ask: "Apply the 5 additive changes now? (yes / no / select)". If `select`, walk the user through each.

For **breaking** items, ask one by one: "`Order.status` enum changed. Apply the matching breaking change to the fake? (yes / no / skip / note)". `note` lets the user attach a comment to `CHANGES.md` without applying.

NEVER silently apply breaking changes. Per the application owner's rule and per safety, always require explicit confirmation for each breaking item.

### 6. Apply approved changes

For each approved change:

- Edit the corresponding fake file (route handler, consumer module, schema, etc.). Use the templates and conventions from `generate-fake` — same patterns, same fidelity rubric.
- Update `fake.manifest.yaml`:
  - Refresh the SHA-256 of the relevant `sourceFiles` and `specs`.
  - Add/remove/modify `surfaces` entries.
  - Set `fake.lastUpdatedAt` to the current time. Leave `fake.generatedAt` untouched — it is immutable.
  - Update `fake.application.repoHeadSha` to the new HEAD.
- Append an entry to `/fake/CHANGES.md` using `reference/changelog-template.md`.

### 7. Re-verify

- Run the fake's syntactic check (`python -m py_compile fake/app.py` / `node --check fake/app.js`).
- Smoke-test the changed surfaces (if you can run the fake locally / in a container).

### 8. Summarise

Print:

- Classification counts.
- Applied / deferred / skipped counts.
- Files touched.
- The new `repoHeadSha` recorded.
- Suggested next step: review the diff and the `CHANGES.md` entry.

## Things to avoid

- **Don't auto-apply breaking changes.** Ever.
- **Don't delete files outside `/fake/`.** Ever.
- **Don't silently rewrite the manifest schema.** If `schemaVersion` is unknown to you, stop.
- **Don't refuse to act on cosmetic-only drift.** Update the SHAs anyway so future runs aren't noisy; just don't touch behaviour.
- **Don't forget to record `notFaked` changes.** Outbound dependencies that the application now uses differently are still useful to surface to the consuming teams.
