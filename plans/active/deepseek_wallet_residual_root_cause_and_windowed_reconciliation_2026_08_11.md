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
- [x] ✅ [OPERATOR] P0. **MEASURED 2026-08-12 08:00 UTC — the 24h residual is NOT zero: $12.44 of $29.14 (42.7%)
      unattributed.** Window 2026-08-11T08:00:09Z → 2026-08-12T08:00:09Z. balance
      $13.40 (sampled 07:59:40Z, 29s before
      the boundary) → $44.26 (sampled 08:00:02Z, 7s before), top-ups in
      window $60.00, so real drawdown $29.14 against $16.70 attributed (worker $15.47 / orchestrator
      $0.57 / review $0.65). **Edge skew is
      ~$0.01 at these sample
      distances and explains none of it.** This CONTRADICTS the 50-minute window taken 2026-08-11 (ratio 1.045, read at
      the time as "reconciles within noise") — that window was simply too short, and its $0.26
      sat inside the old 30-minute sampler's own error bar. At 24h with 1-minute sampling the ratio is **1.745**.
      Operator states no non-AO DeepSeek usage, so this is an attribution defect, not human spend.
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

- [x] ✅ [BACKEND] P0. **ROOT-CAUSED — 82% of the "42.7% unattributed" was a PHANTOM TOP-UP, not lost spend.** Row id 6
      ($10.00, 2026-08-11 11:13Z, note "erro is previous top up sum") recorded a top-up that never happened.
      Proved twice, independently: (1) the 1-minute balance series shows the wallet going -0.90 -> 44.98 across
      2026-08-11 11:00Z (+45.88 net, ~+$50
      gross once in-hour spend is added back) — a
      $60 credit would have ended
      near 54.98; (2) DeepSeek's transactions page shows exactly ONE Success at 2026-08-11 11:10Z for $50,
      beside several Cancelled $50 attempts that explain how the mis-entry happened. The 02:xx entries (id3 $52 + id4
      $2 =
      $54) match the three real Successes ($2 + $2 +
      $50) and are CORRECT — an earlier suspicion that id4
      double-counted id3 was WRONG; do not "fix" them. Ledger corrected on the live VM to the operator-attested
      lifetime total: **$319.00
      -> $308.99**, via one -$10.01 adjustment row backdated to 11:13:11 so windowed reconciliation is right from that
      instant onward. $10.00 of it is receipt-proven; the last $0.01 reconciles to the operator's attested total
      (visible receipts sum to
      $309.00, so the cent is rounding/FX, not a missing
      top-up). Pre-change table backed up to `/home/ubuntu/deepseek_topups_backup_20260812T082841Z.json`.
      **Result: the 24h residual fell $11.82
      -> $2.09 — 42.7% -> 14.4%, ratio 1.795 -> 1.168.**
- [x] ✅ [BACKEND] P0. **Transcript loss RULED OUT as the residual's cause — capture is 99.93%.** Tested the operator's
      "fast tmux deaths lose spend" hypothesis directly, and it does not hold. Over the same 24h window, transcripts
      filtered by each turn's OWN timestamp and deduped on `message.id` hold **2,949 flash / 1,467 pro** turns against
      **2,949 / 1,464** rows in `deepseek_message_usage` — 3 turns of 4,416 (0.07%). Turns in structurally-unswept
      config dirs: **ZERO**. Since `agent_kind` and NULL-provenance only misfile spend BETWEEN buckets and cannot change
      the attributed TOTAL, and turn capture is complete, the remaining gap is necessarily a per-token PRICING question,
      not a measurement one. Confirmed by recomputing spend from the rate card: flash $4.9178 computed vs
      $4.9177
      stored, pro $6.4081 vs $6.4082 — the arithmetic is exact. Tool: `deepseek_spend_probe.py --capture`
      (agent-orchestrator@fab845c1df).
- [x] ✅ [BACKEND] P0. **DeepSeek bills on a measured 3-MINUTE LAG — and that lag is NOT the residual.**
      Cross-correlating per-minute card cost against per-minute wallet drawdown gives a single sharp peak: r = -0.11 at
      lag 0, -0.06 at 1, +0.08 at 2, **+0.74 at lag 3**, +0.42 at 4, then noise (|r| < 0.24) out to 30 min. So a turn's
      cost reaches the balance ~3 minutes after the transcript records it. This matters for any window shorter than ~1h
      and for any bucketed analysis, but it does NOT explain the level gap: LAG-ALIGNED, paired-minute totals still give
      drawdown/card = **1.1712**, essentially identical to the 24h window's 1.168. The gap is a LEVEL effect, not a
      timing one. Probe: `/tmp/lag.py` pattern, folded into `deepseek_spend_probe.py`.
- [x] ✅ [BACKEND] P0. **Which rate is wrong is NOT identifiable from the data we have — recorded so nobody re-runs
      it.** Attempted directly rather than waiting on the 7-day series: bucket the existing 1-minute balance series and
      regress real drawdown on (input, output, cache_read) tokens per model. It FAILS, for a measurable reason.
      Unaligned buckets fit noise — the 6-free-parameter solution returns NEGATIVE rates (pro.input -0.023/M at 5-min
      buckets, flash.cache_read -0.0025/M at 10-min), which are physically impossible, and the bucket ratio drifts 0.82
      -> 0.93 -> 0.94 as buckets widen from 5 -> 10 -> 15 min, which is the signature of the 3-min lag above, not of a
      rate. Aligning by the measured lag and demanding full drawdown coverage per bucket leaves only **3 buckets at 10
      min, 2 at 15, 1 at 20** — fewer observations than free parameters, so the system is underdetermined no matter
      which estimator is used. Root cause of the shortage: all usable spend sits in ONE burst (2026-08-11 07:46-09:30Z)
      with one token mix; the fleet has been idle since. **Identification needs days whose token MIX differs**, which is
      exactly what the daily cron now accumulates — it is a data-availability limit, not an analysis one.
- [ ] [OPERATOR] P1. **Verify the DeepSeek rate card against DeepSeek's own usage page — the residual is now a rate
      question.** With capture at 99.93% and the rate-card arithmetic exact, the remaining ~14% must be a per-token rate
      that does not match what DeepSeek actually bills. A SINGLE window cannot say which rate is wrong: closing the
      $2.09 gap needs input x1.25, OR output x2.26, OR cache_read x2.43 — all three fit equally well. What
      separates them is a token mix that VARIES, so this pairs with the daily-series todo below. Compare our 24h
      totals (flash 22,892,972 in / 3,046,702 out / 307,019,392 cache-read = $4.9177;
      pro 11,480,931 / 929,470 / 166,986,240 = $6.4082) against platform.deepseek.com's usage page for the same window.
      **Done when**: each published rate is confirmed or corrected in `model_pricing.py` with the source cited. (repo:
      agent-orchestrator)
- [ ] [DATA] P1. **Re-measure the 24h residual daily for a week — and regress it to identify WHICH rate is wrong.** One
      window is one datapoint, and this one ran at low volume ($14.50 real vs ~$122/24h on 2026-08-11), where a fixed
      unattributable component looks proportionally huge and a proportional one does not. Beyond that
      fixed-vs-proportional split, the series answers a sharper question: with 7 readings whose token MIX differs,
      regressing real_spend on (input, output, cache_read) tokens yields coefficients that ARE the true per-token rates
      — which is the only way to distinguish the three equally-good single-window fits above without vendor ground
      truth. Run `deepseek_spend_probe.py` (its `reconciliation` block emits every window at once). **Done when**: 7
      daily readings are recorded with volume and token mix alongside residual, and the regression either names the
      mispriced rate or shows the residual is not rate-shaped. (repo: agent-orchestrator, read-only)

## Deferred work after 2026-08-12

**Recommended NEXT item**: find where the 42.7% goes. It is the operator's stated success criterion, and every other
item here is secondary to it.

| Item                                                     | State / why deferred                                                                                     | Blocked on                           |
| -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| Find the $12.44 (42.7%) unattributed 24h spend           | **Not done** — real work, nothing blocking it                                                            | nobody                               |
| Re-measure the 24h residual daily x7                     | **Cannot be done yet** — one reading per day by construction; the series is the point, not any one value | elapsed time                         |
| Stamp `agent_kind` onto `deepseek_message_usage`         | **Not done** — bounded backend work; also a prime suspect for the 42.7%                                  | nobody                               |
| Repair NULL slot_id / is_review_slot rows (re-sweep)     | **Not done** — needs fingerprints cleared first; also a prime suspect                                    | nobody                               |
| Discover transcripts by glob, not slot enumeration       | **Not done** — removes a silent-loss class by construction                                               | nobody                               |
| Freeze the pre-observability opening balance             | **Not done** — cosmetic until the live leak above is understood                                          | nobody                               |
| Windowed view in `DeepSeekWalletPanel.tsx`               | **Not done** — needs `pw:L2` spec                                                                        | nobody                               |
| Fix the `uv.lock` churn cycle                            | **Not done** — touches `setup.sh` sibling pinning + cron `[auto-clean]`, both fleet-load-bearing         | operator scoping (my recommendation) |
| Flip `QG_ENFORCE_FRESH_VENV` to default on               | **Cannot be done yet** — strictly downstream of the churn fix                                            | the churn fix                        |
| Anthropic Wallet Reconciliation (5 todos)                | **Not done** — filed in the anthropic calibration plan; AO-dispatched                                    | nobody                               |
| Request-level proxy accounting for DeepSeek              | **Operator-owned** — a cost/observability judgement, not a defect                                        | operator decision                    |
| Peer conflicts left in two shared clones (see issue doc) | **Operator-owned** — another session's WIP; not mine to resolve                                          | the sessions that own them           |

## Session lessons 2026-08-12 (carry these — each cost real time)

- **A 50-minute window cannot answer a 24-hour question.** The 2026-08-11 window read 1.045 and I called flow
  "reconciled within noise"; the 24h window reads **1.745**. The short window's $0.26 residual sat _inside_ the old
  30-minute sampler's own error bar, so it measured nothing. Do not generalise a short window to a long property — state
  the error bar and check it exceeds the signal.
- **Silence from a freshly-shipped fleet check is a RED FLAG, not success.** The shared stale-venv check was keyed on
  `REPO_ROOT`, which in this codebase is the WORKSPACE dir (`$PROJECT_ROOT/..`), not the repo — so it looked for
  `<workspace>/uv.lock`, never found one, and returned clean everywhere. It produced zero warnings across a fleet
  measured at 70-75% drift and I read that as working. **`PROJECT_ROOT` is the repo root; `REPO_ROOT` is not.**
- **`scripts/dev/slot-cron-ff-pull.sh` overwrites itself from origin every 5 minutes** via its own crontab entry
  (`git show origin/<b>:<script> | cmp -s - <script> || mv`). An in-place edit silently reverts; landing on origin is
  the only way to change it. Caught only because an extracted patch came back one file short.
- **`head -N` on a counting pipeline yields a truncated "total".** "28 stale of 60" was really 162 of 216, and the first
  fix list built from it covered only 22 repos.
- **A token grep that matches a COMMENT produces a confident wrong verdict.** Filtering `pyproject.toml` for the UTL
  string matched a pip-audit comment in `unified-trading-pm` — a repo that does not depend on UTL — and produced a false
  "12 slots BROKEN" finding.
- **`git pull` on a SHARED clone autostashes other sessions' WIP and can conflict on the pop.** Prefer the
  isolated-worktree ship scripts (they build from origin + your named files) and avoid pulling a clone you do not own.
- **uv check semantics**: `uv sync --frozen --check` fails on a MISSING LOCKFILE as well as on drift, so a `-f uv.lock`
  guard is mandatory or every lockless repo aborts. `--inexact` tolerates extra packages but still catches
  missing/wrong-version ones — it does NOT make a genuinely drifted env look clean.

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
