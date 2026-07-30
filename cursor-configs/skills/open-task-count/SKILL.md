---
name: open-task-count
description: >-
  Count tracked plan tasks across the active corpus and report the DEDUPED OPEN figure — open `- [ ]` checkboxes in
  `plans/active/*.md` excluding the aggregator plans (master / batch / consolidated / closeout / satellite) whose todos
  duplicate the primary plans they roll up — plus a breakdown by dispatch target (`assigned_vm: planning` =
  AO-dispatched vs `NA` = not dispatched vs missing). This is the number to quote for "how much real remaining work is
  there" (a raw checkbox grep double-counts via the roll-up plans, and counting done tasks inflates it). The
  planning-vs-NA split explains any gap versus the live AO backlog: most open work is deliberately NA (operator-gated /
  human), so the AO backlog only ever reflects the planning-assigned subset. SSOT engine:
  `scripts/plan-hygiene/count_open_tasks.py` (pure stdlib, read-only). Trigger on `/open-task-count`, "how many open
  tasks", "how many tracked tasks are left", "deduped task count", "real remaining work count", "how many tasks are
  AO-dispatched vs NA", "why is the AO backlog so light", "how many planning vs NA open todos".
---

# open-task-count

Report the honest count of remaining tracked work in the plans corpus, deduped, and split by dispatch target.

## Run it

From the `unified-trading-pm` repo root (use the repo `.venv` python or system python — pure stdlib, no deps):

```bash
python scripts/plan-hygiene/count_open_tasks.py          # human-readable
python scripts/plan-hygiene/count_open_tasks.py --json   # machine-readable
```

Pass `--pm-root <path>` if invoked from outside the PM repo.

## What it counts (and why it is deduped)

- **DEDUPED OPEN** is the headline: open `- [ ]` checkboxes in `plans/active/*.md`, EXCLUDING plans whose filename
  contains `master`, `batch`, `consolidat`, `closeout`, or `satellite`. Those are aggregator / roll-up plans that
  re-list todos owned by the primary plans, so counting them double-counts. It also excludes `INDEX.md` and `_`-prefixed
  files. Done `- [x]` tasks are reported separately, never folded into the open figure.
- **By `assigned_vm`**: `planning` = plans the agent-orchestrator dispatches; `NA` (and `missing`) = not dispatched
  (operator-gated / human / draft). This is read from each plan's frontmatter.

## Interpreting it

- The deduped-open number is the defensible "remaining work" figure to quote internally or to a client (as of 2026-07,
  ~940 deduped open vs ~1,389 raw active-plan open).
- If someone asks why the **AO backlog looks light**: it is expected. The large majority of open todos are `NA` (not
  dispatched). Only the `planning`-assigned subset reaches AO — and the deduped `planning` figure is far smaller than
  total open work. The `planning_open_incl_aggregators_active` line (which counts the batch/satellite dispatch plans the
  dedup step drops) reconciles more closely against the live AO backlog; use `/check-agent-orchestrator` for the true
  live dispatch state.
- A large `NA` share is not automatically wrong (much of it is genuinely operator-gated), but if it looks inflated, that
  is exactly the population `/na-eligibility-audit` triages for reclassification to `planning`.

## Guardrails

Read-only. Never writes plans, never mutates `backlog.yaml`, never calls cloud/network. It is a measurement, not a
reconciler — for corpus contradictions use `/plan-reconcile`, for NA-vs-AO eligibility use `/na-eligibility-audit`.
