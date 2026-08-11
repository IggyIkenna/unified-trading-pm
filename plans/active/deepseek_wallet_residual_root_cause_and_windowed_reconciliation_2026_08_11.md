---
doc_type: plan
title:
  DeepSeek wallet residual — root-caused as a historical stock, and the windowed reconciliation that makes the live
  number measurable
summary: >-
  Operator suspected DeepSeek costs were "off by a factor" because the wallet reconciliation showed a persistent
  residual. Measured 2026-08-11: there is no factor error. The rate card matches DeepSeek's published prices exactly, no
  turns are double-counted, and a live 50-minute drawdown window attributed 95.7% of real spend. The $26.40 lifetime
  residual is a historical STOCK — the ledger's first priced row is 2026-08-04 on a wallet funded and running earlier,
  and those transcripts no longer exist — not a growing leak. The blocker on the operator's actual success criterion
  (24h residual to zero) was that no balance history existed anywhere, making a windowed residual not merely
  unimplemented but uncomputable. A 1-minute balance sampler plus a windowed reconciliation shipped in
  agent-orchestrator@b4e3e74205; the first true 24h measurement is available 2026-08-12. Remaining work is attribution
  fidelity (agent_kind stamping, NULL-provenance repair, glob-based transcript discovery) and freezing the
  pre-observability gap so the lifetime view stops mixing unattributable history into a live signal.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, deepseek, spend, accounting, reconciliation, wallet, cost-attribution]
related:
  [
    /plans/archive/2026_08/issues/deepseek_flash_spend_235_residual_2026_08_10.md,
    /plans/active/anthropic_per_task_actual_spend_and_account_calibration_2026_08_10.md,
    /plans/active/issues/fleet_wide_deepseek_crash_loop_undetected_2026_08_11.md,
    /plans/archive/2026_08/deepseek_flash_ab_routing_test_2026_08_05.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
  ]
created: 2026-08-11
last_updated: 2026-08-11
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
context_scope:
  [
    agent-orchestrator/server/state_store/slots.py,
    agent-orchestrator/server/deepseek_balance_poller.py,
    agent-orchestrator/server/deepseek_usage_poller.py,
    agent-orchestrator/server/model_pricing.py,
    agent-orchestrator/server/orm.py,
    agent-orchestrator/dashboard/src/DeepSeekWalletPanel.tsx,
    /plans/archive/2026_08/issues/deepseek_flash_spend_235_residual_2026_08_10.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  operator-request 2026-08-11 (interactive session — "deepseek costs are off by a factor, we are getting residual")
---

# DeepSeek wallet residual — what it actually is, and how the live number becomes measurable

## What was measured (2026-08-11, live VM, read-only via SSM)

The operator's hypothesis was a pricing factor error. It is not. Four hypotheses were killed by measurement rather than
by reasoning:

| Hypothesis                                | Verdict                                                                                                       |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Cache-read or output rate off by a factor | Rate card matches api-docs.deepseek.com exactly: pro $0.435/$0.003625/$0.87, flash $0.14/$0.0028/$0.28 per 1M |
| Replayed turns double-counted             | 0 duplicate `message_id`s across 115,589 correctly-attributed rows                                            |
| Sweep blind to some transcript dirs       | Unswept dirs hold **$0.017** of DeepSeek spend                                                                |
| Crash-loop turns billed but untranscribed | ~55 pane deaths x 1 in-flight turn x $0.0013-0.0029/turn = **$0.07-$0.16**                                    |

**The live 50-minute drawdown window** (06:57:52-07:46:46 UTC, 2,018 turns): balance $20.58 -> $14.56, no top-ups, real
drawdown $6.02 against $5.76 attributed. Ratio **1.045**. Over the same window the lifetime residual moved
$26.396 ->
$26.656 — i.e. by exactly that window's own $0.26.

**Conclusion**: the $26.40 is a STOCK, not a flow. The priced ledger's first row is 2026-08-04 while topup #1 ($105,
recorded 2026-08-06) is explicitly retroactive ground truth for earlier spend — the full-history sweep only landed
2026-08-05 and cannot recover transcripts that have since aged out. Chasing lifetime to zero means chasing deleted
files.

**Caveat, stated rather than buried**: that
$0.26 is within the measurement's own noise floor. The balance poller was
still on its 30-minute cadence during the window, so the drawdown endpoints could be minutes stale against the ledger
boundaries; at the observed $7.60/hour
burn, three minutes of edge skew is ~$0.38 — larger than the residual being measured. The window proves there is no
FACTOR error; it does not yet resolve whether a few-percent leak exists.

## Why a 24h residual was not computable

`account_usage` is keyed by account_id and holds only the CURRENT balance; `account_usage_history` has no balance
column. With exactly one reading in existence there was no second point to difference against, so "residual over the
last 24 hours" was not unimplemented — it was structurally impossible. Fixed by the sampler below.

## Todos

- [x] ✅ [BACKEND] P0. **Balance time series + windowed reconciliation SHIPPED — agent-orchestrator@b4e3e74205.**
      `DeepSeekBalanceHistoryRow` (`account_id`, `sampled_at`), poll interval 30min -> 1min in both the poller default
      and `config.py`, `compute_deepseek_wallet_window_reconciliation(window_hours=24)`, and
      `GET /api/accounts/deepseek/wallet-reconciliation/window?window_hours=`. Mid-window top-ups are added back to
      drawdown, else a topped-up window reads as spending less than nothing. A window whose start predates the series
      returns `real_spend_usd=None`, never 0. 5 tests; `quality-gates.sh` green (3410 python, 290 dashboard). Deployed +
      verified live: series sampling at 61s intervals, `/api/healthz` ok.
- [ ] [DATA] P0. **Record the first TRUE 24h window residual — available from ~2026-08-12 07:46 UTC.** This is the
      operator's stated success criterion (24h residual to zero, no non-AO DeepSeek usage). Curl the windowed endpoint
      once the series covers a full 24h and record `real_spend_usd`, `attributed_total_usd`, `residual_usd` and BOTH
      balance sample timestamps here. At 1-minute cadence the edge skew is ~$0.13, so a residual materially above that
      is a real defect worth chasing; at or below it, the wallet reconciles and the remaining todos are fidelity work
      rather than leak-hunting. (repo: agent-orchestrator, read-only)
- [ ] [BACKEND] P1. **Stamp `agent_kind` onto `deepseek_message_usage` at sweep time.** The reconciliation's three
      buckets split on `slot_id == 0` / `is_review_slot` / everything-else, but scheduled jobs and escalation workers
      both spawn onto free NUMBERED slots via `_pick_free_slot` (`plan_health.dispatch`, `escalation.escalate`), so all
      of it lands in the bucket labelled "Worker (backlog tasks)" — a label that is simply wrong. Joining spend to kind
      through the `agents` table resolves only $8.10 of $212 (3.8%); 2,286 sessions have no surviving `agents` row.
      Stamp the kind on the usage row the same way `is_review_slot` already is. **Done when**: the reconciliation
      reports scheduled/escalation spend separately from backlog-task spend, and the panel label matches what the bucket
      actually contains. (repo: agent-orchestrator)
- [ ] [BACKEND] P1. **Repair the NULL-provenance rows, and stop claiming they self-heal.** $68.89 of $212.02 lifetime
      (32%, 35,975 turns, recorded 2026-08-04..08-06) carries `is_review_slot IS NULL`, and $62.72 carries
      `slot_id IS NULL` — those land in `worker` BY DEFAULT, not by measurement. The code comment asserting they
      "self-correct as soon as that row's file is next re-parsed" was corrected in @b4e3e74205: the sweep skips any file
      whose `(mtime, size)` fingerprint is unchanged and a finished session's transcript never changes again, so they
      are never re-parsed. **Done when**: the affected files' `ProcessedTranscriptRow` fingerprints are cleared, one
      re-sweep repopulates both columns, and the NULL counts are re-measured and recorded here. (repo:
      agent-orchestrator)
- [ ] [BACKEND] P1. **Discover transcripts by GLOB instead of enumerating live slot rows.** `_sweep_account` iterates
      `ss.list_slots(db)` and constructs `orch-slot-{N}` names, so anything not in that list is invisible forever —
      confirmed live: `orch-slot-97`/`orch-slot-99` have transcripts on disk that are never read, and
      `~/.claude/projects` (576 files, 118 MB) is never swept at all. Glob `~/.claude-configs/*/projects/*/*.jsonl` plus
      `~/.claude/projects/*/*.jsonl` and derive `slot_id` from the directory name (`None` when it is not a slot dir).
      Low dollar value today ($0.017) but it removes an entire silent-loss class by construction rather than by an
      enumeration that drifts. **Done when**: a retired slot's transcripts are still swept, proven by a test. (repo:
      agent-orchestrator)
- [ ] [BACKEND] P2. **Freeze the pre-observability gap as an explicit opening balance in the LIFETIME view.** Today the
      lifetime residual silently mixes unattributable pre-2026-08-04 spend with any live leak, so it can never reach
      zero and its movement is the only usable signal. Record the measured pre-ledger gap as a labelled opening balance
      so the lifetime view reports `residual since observability began` instead. **Done when**: the lifetime view
      distinguishes the frozen historical gap from live residual, and the panel says which is which.
- [ ] [UI] P2. **Surface the windowed view in `DeepSeekWalletPanel.tsx` with a 24h/7d toggle.** Must render the
      `real_spend_usd=None` case as "sampling since <ts> — 24h view available at <ts+24h>" rather than a dash that reads
      as zero, and show BOTH balance sample timestamps so the true differenced span is visible instead of assumed to
      match the request. **Done when**: the panel renders live data and a cited playwright regression spec passes;
      `[UI]` + `pw:L2 ✓` per `/codex/06-coding-standards/ui-testing-layers.md`.
- [ ] [INFRA] P2. **Pin `cleanupPeriodDays: 30` explicitly in `cursor-configs/settings.json`.** Measured 2026-08-11: the
      setting is absent from every settings file (all grep hits were Claude Code's own `cache/changelog.md`), so
      retention runs on an upstream default that the same changelog shows has already had two behaviour-changing bugs
      (`--setting-sources` without `user` silently ignoring it; `0` silently disabling persistence). Pinning costs one
      line and removes the drift risk. **Do NOT raise it to 60** without new disk: the VM is at 82% (551G/678G, 127G
      free), transcripts are 77G, and the fleet burns ~1,225 files/day at ~3.4 MB each (~4.2 GB/day) — a 30-day
      extension would consume essentially all remaining free space. **Done when**: the setting is pinned and the
      disk-headroom figures are re-checked at the time of the change. (repo: unified-trading-pm)
- [ ] [OPERATOR] P3. **Decide whether to fund request-level accounting at a proxy.** The only class the transcript
      design can NEVER see is tokens billed with no transcript line — a pane killed mid-stream, a request that errors
      after generation, a retry. Routing DeepSeek traffic through a local pass-through proxy would log every response's
      usage block when it returns, independent of whether the client survived to write the transcript. Measured cost of
      NOT doing it is currently ~$0.07-$0.16 per crash-loop episode, so this is a judgment call about observability, not
      a cost-recovery case. Revisit if the first true 24h residual is materially above the ~$0.13 skew floor.

## Codex SSOTs

- `/codex/12-agent-workflow/measurement-claims-discipline.md` — the discipline this plan's findings section follows
  (every hypothesis killed by a measurement, caveats stated rather than buried).
- `/codex/04-architecture/runtime-deployment-topology.md` § "agent-orchestrator — self-pull deploy" — the AO VM FF-pulls
  `origin/live-defi-rollout` via a 15-min root cron and restarts when HEAD moves. AO does NOT deploy from `main`; the
  LDR->main promotion pipeline is repo hygiene, not the AO deploy path.

## Progress Log

- **2026-08-11** — Investigated the operator's "off by a factor" hypothesis. Killed four candidate causes by measurement
  (see table above). Established the residual is a historical stock, not a flow, via a live 50-minute drawdown window
  (ratio 1.045). Found the real blocker on the operator's success criterion: no balance history existed anywhere, so a
  windowed residual was uncomputable. Shipped the sampler + windowed reconciliation (agent-orchestrator@b4e3e74205),
  deployed and verified live at 61-second sampling.
- **2026-08-11** — Incidental finding, fixed in the same change: the code comment claiming NULL `slot_id`/
  `is_review_slot` rows self-correct on re-parse is false, because the fingerprint cache means a finished session's
  transcript is never re-parsed.
- **2026-08-11** — Incidental finding, NOT fixed here: the `agent-orchestrator` checkout in tab 6 had fastapi 0.136.3
  installed against a `pyproject.toml` requiring `>=0.137.0` (lock pins 0.140.7), so `tests/conftest.py` could not
  import and the ENTIRE python suite was unable to run. `uv sync` repaired it. Worth a broader check that other slots
  are not silently in the same state.
