---
doc_type: issue
title:
  "agent-orchestrator/dashboard resolves prettier 3.6.2 while the sanctioned prettier-autostage wrapper pins 3.9.5 — the
  two disagree on formatting, so `npm run format` and the commit hook fight each other"
summary: >-
  Measured 2026-08-06 while shipping a dashboard CSS change: `dashboard/node_modules/.bin/prettier --version` is
  **3.6.2** (devDependency `"prettier": "^3.6.2"`), but `unified-trading-pm/scripts/hooks/prettier-autostage.sh` sets
  `PRETTIER_MIN_VERSION="3.9.5"` and, finding the local binary below that floor, shells `npx -y prettier@3.9.5` instead.
  They produce DIFFERENT output: files the wrapper had just formatted were reported as needing reformatting by the local
  `npx prettier --check`, and vice versa — clean under 3.9.5, dirty under 3.6.2. Nothing is currently broken because
  `agent-orchestrator/scripts/quality-gates.sh` runs only `tsc` + `vitest` for the dashboard and never `npm run
  format:check`, so the skew is latent rather than failing — but a developer running the repo's OWN documented `npm run
  format` script produces output the sanctioned commit-time wrapper will then re-change, which is exactly the
  reformat-churn loop the wrapper exists to end. NOT simply "bump the devDependency":
  `/plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md` documents a reproducible proseWrap
  idempotency defect in prettier **3.9.5 AND 3.9.6**, so raising the floor to the wrapper's pin adopts a version with
  known badness. Which side moves is a real decision, not a mechanical bump.
status: open
nature: issue
asset_group: [ao]
scope: [engineer]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
tags: [prettier, formatting, tooling, version-skew, dashboard]
related:
  [
    /plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: 2026-08-06
author: agent
last_updated: 2026-08-06
priority: P3
parent_epic: orchestrator_master
source:
  "agent, interactive session — surfaced while formatting a dashboard CSS/TSX change for the AO context-saturation work;
  the wrapper reported success while a local `--check` reported failure on the same files, which is what exposed the
  two-version split"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/prosewrap_padding_corpus_wide_1290_space_2026_08_03.md,
    /codex/06-coding-standards/quality-gates.md,
    scripts/hooks/prettier-autostage.sh,
    agent-orchestrator/dashboard/package.json,
    agent-orchestrator/scripts/quality-gates.sh,
  ]
---

# Dashboard prettier version skew vs the autostage wrapper's pin

## Todos

- [ ] [INFRA] P3. **Decide which side moves, then align them.** Options: (a) raise the dashboard devDependency to match
      `PRETTIER_MIN_VERSION` (3.9.5) — simplest, but knowingly adopts the proseWrap idempotency defect that
      `prosewrap_padding_corpus_wide_1290_space_2026_08_03` documents for 3.9.5/3.9.6, so verify that defect does not
      affect `.ts`/`.tsx`/`.css` (it was found on markdown) before choosing it; (b) lower the wrapper's floor for
      non-markdown file types, keeping the higher pin only where the markdown mangling it guards against actually
      applies; (c) leave the split and document it, accepting that `npm run format` is not the sanctioned path for this
      repo. Whichever is chosen, make `agent-orchestrator`'s `format`/`format:check` scripts and the wrapper agree, so
      the repo's own documented command stops disagreeing with its own commit hook.

- [ ] [INFRA] P3. **Then decide whether the dashboard should gate on formatting at all.**
      `agent-orchestrator/scripts/quality-gates.sh` runs `tsc --noEmit` + `vitest` for the dashboard but never
      `format:check`, which is the only reason this skew has not failed anyone's gate. That is a gap or a deliberate
      choice; it is currently neither documented nor obvious. If formatting should be enforced, wiring `format:check` in
      is a one-line change — but do it AFTER todo 1, or the gate starts failing on the disagreement itself.

## Progress Log

### 2026-08-06 — filed

Found while shipping the context-bar staleness change: the sanctioned wrapper reported the files clean, while
`npx prettier --check` on the same files reported them dirty. Both were "right" — different binaries. Confirmed by
running `npx -y prettier@3.9.5 --check` on the identical file set, which passed. No action taken on the skew itself
during that session: the change being shipped was verified against the wrapper's pinned version (the sanctioned path)
and the gate passed, so nothing was blocked.

- **na-eligibility-audit 2026-08-07** (tranche=ao, autonomous): KEEP-NA, valid — both todos are explicit "decide which
  side moves" judgment calls (todo 1 trades off adopting a version with a known documented proseWrap defect; todo 2 is
  gated behind todo 1). Not bounded/deterministic; genuine operator/engineer tradeoff call.
- **context-scout 2026-08-07**: populated context_scope (5 entries).
