---
doc_type: issue
title: >-
  The LDR docs-gate — the CI backstop that exists BECAUSE the pre-commit frontmatter hook is fail-open — never
  completes: concurrency cancel-in-progress on a global group means every push kills the prior run, so on a hot branch
  it produces ZERO verdicts (measured: 0 of 100 runs completed over 6+ hours)
summary: >-
  Measured 2026-07-20. `ldr-docs-gate.yml` runs `check_frontmatter_schema.py` corpus-wide on every push to
  `live-defi-rollout` and is documented IN THE FILE as "the ONLY defense against broken doc frontmatter" — it was
  created 2026-07-17 as fix-direction-2 for the known fail-open pre-commit hook
  (`prek_plan_hygiene_hook_fail_open_unhooked_clone_2026_07_17.md`). Its `concurrency:` block is `{group: ldr-docs-gate,
  cancel-in-progress: true}` — a SINGLE global group with cancel-in-progress. On a branch that takes a push every 1-2
  minutes (routine for the fleet), each push cancels the still-running prior gate before it can finish, so no run ever
  reaches a verdict. Measured over the last 100 runs (window 12:07 -> 18:27 UTC, 6h20m): 99 cancelled, 1 running, **0
  completed (success|failure)**. The backstop for a known-unreliable commit-time hook is itself non-functional exactly
  when it is needed most — during the hot periods when a broken doc blocks every slot's `quality-gates.sh` fleet-wide.
  This is how a broken-frontmatter doc can sit undetected on LDR: layer-1 (pre-commit hook) is fail-open on an unhooked
  clone, and layer-2 (this gate) never completes. Both layers of the defense-in-depth are simultaneously defeated.
status: resolved
resolved_by: unified-trading-pm@078c85dc3 (+ 0349d1d15, 51ce7c394)
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, quality-gates, frontmatter, concurrency, ci-integrity, plan-hygiene, backstop, false-green]
related:
  [
    prek_plan_hygiene_hook_fail_open_unhooked_clone_2026_07_17.md,
    foreign_dirty_frontmatter_blocks_every_agents_gate_2026_07_18.md,
  ]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: devops
drift_direction: none
locked_by:
source:
  [
    "discovered 2026-07-20 while investigating (at the operator's request) how a broken-frontmatter doc reached LDR; the
    root cause turned out NOT to be the plan-health-bot autofix (which only appended valid fields) but the combination
    of a fail-open commit hook and this never-completing CI backstop",
  ]
depends_on: []
---

# The LDR docs-gate never completes — its own concurrency config cancels it before it can produce a verdict

## Evidence (measured, not inferred)

`ldr-docs-gate.yml` triggers on `push` to `live-defi-rollout` for `plans/**` + `codex/**` and runs
`check_frontmatter_schema.py --quiet` over the whole corpus. Its concurrency block:

```yaml
concurrency:
  # Newest push wins — an outdated corpus verdict is worthless.
  group: ldr-docs-gate
  cancel-in-progress: true
```

`group` is a single global constant (not keyed on the ref or the sha), and `cancel-in-progress: true`. So the newest
push always cancels the in-progress run. Over the **last 100 runs**
(`gh run list --workflow ldr-docs-gate.yml --branch live-defi-rollout --limit 100`), window `2026-07-20T12:07 -> 18:27`
UTC (6h20m):

| conclusion | count |
| ---------- | ----- |
| cancelled  | 99    |
| running    | 1     |
| success    | 0     |
| failure    | 0     |

**Zero runs completed.** The gate has never produced a verdict on this branch in the observed window. `git log` shows
LDR takes a docs push roughly every 1-2 minutes; the gate (checkout + setup + corpus parse) takes longer than that gap,
so it is cancelled 100% of the time.

## Why it matters — both layers of the defense are down at once

The frontmatter defense-in-depth is two layers, and they fail together:

1. **Layer 1 — the pre-commit `plan-hygiene` hook.** Correct when installed, but **fail-open on an unhooked clone** or
   an unresolvable sweep path — tracked in `prek_plan_hygiene_hook_fail_open_unhooked_clone_2026_07_17.md`. A clone
   without hooks direct-pushes broken frontmatter to LDR with no local block.
2. **Layer 2 — THIS gate**, created 2026-07-17 as the CI backstop precisely because layer 1 is fail-open. Its own file
   comment calls it "the ONLY defense against broken doc frontmatter." It never completes (above), so it catches nothing
   during the hot periods when it matters.

Net: a broken-frontmatter doc reaches LDR (layer 1 bypassed) and is not flagged by CI (layer 2 cancelled), so it sits
red — failing `check_frontmatter_schema` as a corpus-wide post-gate check in EVERY clone — until a human notices the
fleet-wide `quality-gates.sh` failure and repairs it by hand. That is exactly the multi-slot block described in
`foreign_dirty_frontmatter_blocks_every_agents_gate_2026_07_18.md`.

## What is NOT the cause (correcting the record)

This investigation started from a WRONG premise I introduced: that `plan-health-bot` broke the
`defi_available_at_clobbered_by_wallclock_2026_07_20.md` frontmatter. It did not — `44e1fb449` appended three VALID
lines to a doc whose `summary:` was already an unquoted multi-line plain scalar (broken by the authoring commit
`273f5a9d5`). The `fix_frontmatter.py` refuse-on-unparseable + round-trip guard shipped in `2818c9648` is still worth
having (it stops the fixer from masking/misattributing a broken doc), but it does NOT address how the doc reached LDR.
THIS issue is that root cause.

## Proposed fix (design — NOT auto-applied; touches a templated fleet workflow)

The workflow is templated: the SSOT is `scripts/self-hosted-runners/hosted-baseline/ldr-docs-gate.yml`, reconciled to
the deployed `.github/workflows/ldr-docs-gate.yml` via `rehost/ldr-docs-gate.yml.patch` (runner-only delta: `glue` vs
`ubuntu-latest`; the `concurrency:` block is identical in both). A fix edits the TEMPLATE + re-runs the rollout — do not
hand-edit the deployed copy.

The intent ("newest push wins — an outdated corpus verdict is worthless") is reasonable for FAST feedback but is the
wrong contract for a GATE, whose job is to guarantee a red corpus is eventually flagged. Options, in preference order:

- **A (recommended) — keep newest-wins for push, ADD a completion-guaranteed cron.** Add a `schedule:` job (e.g. every
  15 min) running the same corpus check, in a SEPARATE concurrency group (or none) so it is never cancelled by pushes.
  Subtlety: `schedule:` fires only from the DEFAULT branch, which here is **`main`, not LDR** — so the cron job MUST
  explicitly `git fetch origin live-defi-rollout` and validate THAT ref's corpus, not the checked-out default. This
  guarantees a broken corpus is caught within one cron interval even during a push storm, while pushes still get fast
  feedback when the branch is quiet.
- **B — `cancel-in-progress: false`.** Queue runs so each completes. Simpler, but on a hot branch it builds a backlog
  and the verdict lags the head by the queue depth; a persistently-red corpus is still eventually flagged, just late.
- **C — per-sha concurrency group** (`group: ldr-docs-gate-${{ github.sha }}`). Every push's run completes (no
  cancellation), at the cost of concurrent runs. Cleanest "every commit gets a verdict," highest runner cost.

A + (B or C) composes: cron as the guaranteed safety-net, plus per-sha or queued for per-commit coverage. Whichever is
chosen, add an alert on the gate's RED verdict routed through `notify-slack.yml` (per
`codex/04-architecture/ci-alerting.md`) so a broken corpus pages instead of waiting to be noticed.

## Verification for whoever fixes this

After the template change + rollout, confirm the gate actually completes:
`gh run list --workflow ldr-docs-gate.yml --branch live-defi-rollout --limit 30 --json conclusion` should show
`success`/`failure` verdicts, not all `cancelled`. Then stage a known-broken frontmatter doc, push, and confirm the gate
(push or cron) goes RED and alerts.

## Resolution (2026-07-22, via `github_actions_ci_cost_reduction_2026_07_15.md`)

Two fix attempts were needed. First, `cancel-in-progress: false` (queue instead of cancel) — necessary but not
sufficient. The actual root cause: `runs-on: [self-hosted, Linux, X64, glue]` requires 4 labels, but
`glue-runner-run.sh` only ever registers JIT-ephemeral runners with `["self-hosted","glue"]` (2 labels) — the job could
structurally never match any runner in the pool. Fixed via `unified-trading-pm@078c85dc3`
(`runs-on: [self-hosted, glue]`, matching the other 35 workflows on this pool). **LIVE PROOF**: the next `plans/**` push
triggered run `29910893758`, which completed with a real verdict — the gate produced its first-ever result. Additionally
shipped 2026-07-22 (`unified-trading-pm@0349d1d15` + `51ce7c394`): trigger switched `push` → `schedule: "0 * * * *"` +
`workflow_dispatch` (cuts this workflow's contribution to shared glue-runner load from ~240/day to 24/day); full-corpus
scan kept deliberately (measured 2.04s for the whole corpus).

**One residual, NOT yet verified**: `schedule:` resolves against the DEFAULT branch's workflow file, which didn't carry
this fix as of 2026-07-22 session end — the hourly cron won't actually run the fixed version until the LDR→main
auto-promote cycle (`*/15`, v2-gated) lands `unified-trading-pm@51ce7c394` onto `main`. Check
`gh run list -R IggyIkenna/unified-trading-pm --workflow=ldr-docs-gate.yml` for a `schedule`-triggered run once
promotion lands; if none appears within a few hours, investigate rather than assume "still waiting."
