---
doc_type: issue
title:
  Production-readiness checklist file (`deployment-service/configs/checklist.template.yaml`) does not exist — 5+ docs
  cite it, item-count 3-way disagrees
summary: >-
  `deployment-service/configs/checklist.template.yaml` is cited by name as the production-readiness checklist SSOT by at
  least 5 docs across 2 repos (deployment-service/CONTRIBUTING.md, deployment-service/audit/CURRENT_AUDIT.md,
  codex/README.md, /codex/06-coding-standards/README.md) but does not exist anywhere in the current deployment-service
  checkout under that path or any other name found. /codex/06-coding-standards/README.md's own TL;DR says "51-point",
  its dedicated "Production Readiness Checklist" section says "52-point", and its own itemized phase table (items 1-6,
  7-12, 13-18, 19-22, 23-25, 26-33, 34-37) sums to 37 — three different counts for the same checklist, none of which
  match either real checklist file found (`codex/10-audit/_checklist-template.yaml` = v1.0, 110 items, explicitly
  "preserved for reference"/superseded; `_checklist-template-enhanced.yaml` = 26 items). Found by docs-reconcile's
  internal-self-consistency hunter (2026-07-24) while checking a narrower single-doc contradiction; escalated to an
  issue doc once the cited backing file turned out to be missing entirely rather than just moved.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [docs-reconcile, checklist, production-readiness, dangling-reference, cross-repo]
related: [/codex/06-coding-standards/README.md, /codex/10-audit/README.md, /codex/README.md]
created: 2026-07-24
parent_epic: agent_operating_framework_master
priority: P2
source: >-
  docs-reconcile full-corpus run, 2026-07-24 — self-consistency hunter batch_2 flagged the 51-vs-52-vs-37 mismatch in
  /codex/06-coding-standards/README.md as an internal contradiction; investigating for a mechanical fix found the cited
  backing file itself is missing, which is a bigger and different problem than a stale prose number.
resolved_by:
locked_by:
assigned_vm: NA
code_refs: []
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# Production-readiness checklist file missing — item-count 3-way disagreement is a symptom, not the root problem

## What was found

While running docs-reconcile's internal-self-consistency hunter over codex docs touched in the last 24h, one hunter
flagged `/codex/06-coding-standards/README.md` for a self-contradiction:

- Line 13 (TL;DR): "The **51-point** production readiness checklist governs all services."
- Line 546 (dedicated section): "The **52-point** checklist in `deployment-service/configs/checklist.template.yaml`
  covers:"
- The phase table immediately below line 546 (items 1-6, 7-12, 13-18, 19-22, 23-25, 26-33, 34-37) sums to **37**.

Before fixing this as a simple "pick the right number" edit, I tried to verify against the cited backing file —
`deployment-service/configs/checklist.template.yaml` — and it **does not exist** anywhere in the current
`deployment-service` checkout (`find deployment-service -iname "*checklist*"` returns only
`docs/CLOUD_BUILD_SUCCESS_CHECKLIST.md`, an unrelated doc).

The same missing path is cited as if it exists by at least 4 other docs:

- `deployment-service/CONTRIBUTING.md:219` — "`deployment-service/configs/checklist.template.yaml` - Production
  checklist"
- `deployment-service/audit/CURRENT_AUDIT.md:74` — "Template: `configs/checklist.template.yaml`"
- `codex/README.md:137` — "**Checklist:** `deployment-service/configs/checklist.template.yaml`"
- `/codex/06-coding-standards/README.md` (this doc, both citations above)

Two OTHER checklist files do exist, but neither matches any of the 3 counts above:

- `codex/10-audit/_checklist-template.yaml` — 110 items (`/codex/10-audit/README.md:112` documents this as "v1.0 full
  110-item checklist (**preserved for reference**)" — i.e. explicitly superseded/historical, not current).
- `codex/10-audit/_checklist-template-enhanced.yaml` — 26 items.

So there are 5 different item-counts in play (51, 52, 37, 110, 26) across 6 files, and the one file every citing doc
actually points to by path is absent.

## Why I did not fix this myself

This isn't a stale-number typo with an obvious correct value — I have no way to determine from the current repo state
which number (if any) is authoritative, whether the checklist mechanism was renamed/relocated/merged into one of the
`_checklist-template*.yaml` files, or whether it needs to be recreated. Guessing a number to make the 3 in-doc mentions
internally consistent (e.g. picking 37 since that's the one value I can mechanically re-derive from the doc's own table)
risks papering over a real broken tool-chain reference with a cosmetically-consistent but still-wrong number.

## Recommended next step

- A: **[REC]** An engineer who knows the current onboarding/production-readiness tooling confirms whether
  `checklist.template.yaml` was renamed, merged into `_checklist-template-enhanced.yaml` (26 items — closest in spirit
  to "current, not historical"), or genuinely needs recreating from the 37-item phase table already documented in
  `/codex/06-coding-standards/README.md`. Once decided, fix all 5 citing locations together in one pass so they agree.
- B: If the checklist mechanism is confirmed dead/replaced by something else entirely (e.g. folded into
  `scripts/quality-gates.sh` or the AO dispatch-readiness checks), retire all 5 references and the phase table, and
  point onboarding at whatever replaced it.

## Todos

- [ ] [ENGINEER] P2. Determine the current, correct home + item-count of the production-readiness checklist (see options
      A/B above), then fix all 5 citing locations (`deployment-service/CONTRIBUTING.md`,
      `deployment-service/audit/CURRENT_AUDIT.md`, `codex/README.md`, `/codex/06-coding-standards/README.md` ×2) to
      agree with each other and with the real backing file.

## Progress Log

- 2026-07-24 — Filed by docs-reconcile self-consistency hunter follow-up. Not fixed inline (see "Why I did not fix this
  myself" above) — genuinely needs a human decision on which checklist is authoritative, not a mechanical edit.
