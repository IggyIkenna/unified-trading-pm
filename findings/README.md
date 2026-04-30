# findings/

Bug reports, vendor quirks, and unresolved-issue write-ups discovered
during development. **Not** part of the codex (which is the canonical
SSOT for how the system *is* designed). Things in here describe how the
system is currently *broken* and what mitigations are in place.

## When to write a finding

- A bug that's been mitigated (band-aid in place) but the root fix is
  deferred.
- A vendor quirk that downstream consumers need to be aware of.
- An unexpected data shape in a real GCS / API response that
  contradicts what the codex says.
- An incident write-up where the fix landed but the lesson is worth
  preserving.

## When NOT to write a finding

- Quick fixes that are fully resolved in a single commit. Use the commit
  message.
- Forward-looking design questions. Those go in `plans/ai/`.
- How the system is intended to behave. That goes in `codex/`.

## Filename convention

`<topic>_<YYYY_MM_DD>.md` — same shape as `plans/ai/`. Date is when the
finding was written, not when the bug was introduced.

## Frontmatter

```yaml
---
title: <short title>
status: <open | mitigated | resolved>
severity: <low | medium | high>
created: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
owners:
  - <team or person>
related:
  - <file path or link>
---
```

`status: mitigated` means a band-aid is in place, root fix deferred.
`status: resolved` means the root fix has shipped — keep the doc as
historical context rather than deleting.
