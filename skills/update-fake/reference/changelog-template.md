# `CHANGES.md` template

After every `update-fake` run that modifies the fake, append a new entry to `/fake/CHANGES.md`. Format:

```markdown
## YYYY-MM-DD — updated against <new-repoHeadSha-short>

**Range:** `<old-repoHeadSha-short>` → `<new-repoHeadSha-short>` (`<n>` commits)

### Applied

#### Additive
- `+ GET /users/{id}/preferences` — added canned response based on `UserPreferences` schema.
- `+ field User.timezone (optional)` — added to canned response example.

#### Breaking
- `! Order.status enum` — extended to include `refunded`. Updated transform for `POST /orders` to allow that status in echo output. Reviewed by: <user>.

### Deferred (still drifted)
- `! removed: GET /legacy/orders` — left in the fake at the user's request, marked deprecated in `README.md`.

### Cosmetic (manifest SHAs refreshed only)
- 12 source files touched with no behaviour change.

### Fragility findings updated
- New: `H4` — `POST /orders/{id}/refund` accepts an untyped body. Suggestion: introduce `RefundRequest` schema.

### Manifest
- `schemaVersion`: 1 (unchanged)
- `lastUpdatedAt`: `2026-05-16T11:55:00Z`
- `application.repoHeadSha`: `9f12bcd1...`

_Run by_ Claude Code `update-fake` skill, **Atomic** plugin v0.1.0.
```

## Rules

- Newest entries go at the **top**.
- Always record both the SHA range and the commit count — it makes auditing the fake's history quick.
- Never delete previous entries.
- Don't bundle unrelated runs into one entry — each invocation = one entry.
- If the user deferred a breaking change, note it explicitly under `Deferred` so the next run knows it's still pending.
