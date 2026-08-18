---
doc_type: codex-ssot
title: Artefact sources are committed — the published page is a rendering, never the record
summary: >-
  HARD RULE from the operator, 2026-08-18 — every artefact we publish must have a committed source file in the repository,
  always. The published artifact page is a rendering of that file, not the artefact itself. This is what makes an
  artefact survivable across sessions, across accounts, and across a lost or unreachable URL — all three of which
  have now happened. Gives the rule, the measured incident that motivated it, and the recovery mechanics when a
  published page becomes unreachable.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [artifact, client-disclosure, durability, regression-prevention]
related: [/codex/12-agent-workflow/measurement-claims-discipline.md, /codex/05-infrastructure/per-tab-worktrees.md]
created: 2026-08-18
authoritative_for: [artefact source durability, artifact republish recovery, artefact SSOT location]
referenced_by: []
owner:
last_reviewed:
code_refs:
---

# Artefact sources are committed

## The rule

**Every artefact we publish has a committed source file. No exceptions, and the commit comes first.**

The published artifact page is a _rendering_ of that file. It is not the record, it is not the SSOT, and it is not
durable: a URL can become unreachable through an account switch, a permissions change, or simply a session that no
longer holds the association. The committed file is the thing that survives all three.

**Where client-facing sources live**: `codex/14-customer-journeys/commercial-model/`. A scratchpad copy is a
legitimate _render path_ — never the source of record.

## The measured incident — 2026-08-18

The operator switched accounts. Every attempt to republish `platform-external-api-walkthrough.html` refused, three
times identically:

```
publish refused: could not verify the target page is not a review page ...
this artifact is served to you as a public (non-member) reader
```

The refusal was not about the file. It was the tool trying to **read the existing published page** — owned by the
previous account — to verify it was not a review page. Nothing about the content could have fixed it.

**Nothing was lost, and only because the source was committed** (`unified-trading-pm@aa1ee152ae`, 70,268 bytes, every
measured figure verified at origin before the publish was attempted). Had the artefact existed only as a published
page, an account switch would have destroyed a document carrying live coverage measurements.

## Recovery mechanics — when a published page becomes unreachable

Publishing maps `file_path` → artifact _within a conversation_. If the prior artifact is unreadable (different
account, revoked access), republishing the same path keeps failing because the tool cannot verify the target.

**The fix is a fresh `file_path`**, which claims a new URL under the current account:

1. Confirm the committed source is current and verified at origin.
2. Copy it to a new path (the scratchpad is fine — it is a render path only).
3. Publish from that path. A new URL is issued; the old one stays with the old account.

The new URL is a cost worth paying and not worth avoiding: the artefact's identity lives in the repository, so a
changed URL is a broken link, never lost content.

## Why this is a HARD rule rather than good practice

An artefact that exists only as a published page is **undiffable, unreviewable and unrecoverable**. It cannot be
code-reviewed, its numbers cannot be traced to the measurement that produced them, and it cannot be regenerated when
the underlying figures move. Committing the source makes an artefact a normal repository artifact subject to the same
review, the same history and the same provenance rules as everything else — which is exactly what a document carrying
client-facing measurements needs.
