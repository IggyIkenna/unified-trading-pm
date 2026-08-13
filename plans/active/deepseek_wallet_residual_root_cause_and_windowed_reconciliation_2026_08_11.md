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
last_updated: 2026-08-12
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
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
- [x] ✅ [BACKEND] P1. **SHIPPED — `agent_kind` stamped onto `deepseek_message_usage` at sweep time
      (agent-orchestrator@18fc60b).** `DeepSeekMessageUsageRow.agent_kind` column (nullable, same snapshot-not-re-
      derived contract as `is_review_slot`), added via `_add_missing_columns`; the sweep snapshots each slot's
      `AgentRow.agent_kind` AT SWEEP TIME via the `orch-slot-{N}` tmux-session join (most-recent registration wins) and
      stamps it onto every row it writes; the wallet reconciliation now reports **scheduled** (plan_health family) and
      **escalation** (cicd/conflict_resolver/data_pipeline_failure/quality_gate_resolution) spend separately from
      backlog-task `worker` spend, in both the lifetime and windowed views, and the DeepSeek wallet panel shows
      "Scheduled jobs" + "Escalation one-shots" rows so the label matches what the bucket actually contains. Also
      completed `_SCHEDULED_ROLES` (was missing escalation_queue_reconciler/ci_reconciler/
      data_pipeline_alerts_reconciler — same latent misclassification class). Tests: sweep-time stamping (present +
      None), lifetime + windowed kind-split, role-group pinning. quality-gates.sh green. (repo: agent-orchestrator)
- [x] ✅ [BACKEND] P1. **Repair the NULL-provenance rows, and stop claiming they self-heal.** $68.89 of $212.02 lifetime
      (32%, 35,975 turns, recorded 2026-08-04..08-06) carries `is_review_slot IS NULL`, and
      $62.72 carries
      `slot_id IS NULL` — those land in `worker` BY DEFAULT, not by measurement. The code comment asserting they
      "self-correct as soon as that row's file is next re-parsed" was corrected in @b4e3e74205: the sweep skips any file
      whose `(mtime, size)` fingerprint is unchanged and a finished session's transcript never changes again, so they
      are never re-parsed. **Done 2026-08-13 — agent-orchestrator@002126cb32 + live repair executed.** Added
      `scripts/orchestrator/repair_null_provenance.py` (clear affected files' `ProcessedTranscriptRow` fingerprints →
      one `_sweep_account` re-parses them and re-stamps `slot_id` / `is_review_slot` / `agent_kind` from the current
      slot enumeration + config snapshot; dry-run by default, `--apply` / `--sweep`; 5 tests, QG green). Ran it live on
      the fleet DB with `ORCHESTRATOR_REVIEW_SLOTS` unset (so `is_review_slot` stamps match the live server's `{2}`
      resolution, not this shell's `{1}`): **before** 31,947 NULL `slot_id` rows ($62.72)
      / 35,975 NULL `is_review_slot` rows ($68.89) → **after 0 / 0** across both accounts (flash + pro), fingerprints
      re-upserted so the repaired files are skipped again on later ticks. Also corrected the two remaining "self-healing
      contract" docstring phrasings in `server/orm.py`. (repo: agent-orchestrator)
- [x] ✅ [BACKEND] P1. **SHIPPED — discover transcripts by GLOB instead of enumerating live slot rows
      (agent-orchestrator@60fd7ba).** `_sweep_account` derived `orch-slot-{N}` session names from `ss.list_slots(db)`
      and searched only those dirs, so anything not a live slot was invisible forever — confirmed live:
      `orch-slot-97`/`orch-slot-99` have transcripts on disk no sweep ever read, and `~/.claude/projects` (576 files,
      118 MB) was never swept at all. Discovery is now `deepseek_usage.discover_all_transcripts()`: glob
      `<config_base>/*/projects/*/*.jsonl` plus `~/.claude/projects/*/*.jsonl`, with `slot_id` DERIVED from the
      session-name dir (`orch-slot-{N}` -> N, `orch-agent-main` -> 0, anything else / the home tree -> `None` — still
      swept, lands in `worker` by the same honest default every NULL-slot row gets). `_sweep_account` stamps
      `slot_id`/`is_review_slot`/`agent_kind` from the discovered file instead of a live SlotRow; `agent_kind` snapshots
      the DISCOVERED slot ids so a retired slot with a transcript gets the same stamping as a live one. Low dollar value
      today ($0.017) but it removes an entire silent-loss class by construction rather than by an enumeration that
      drifts. **Test proves the done-when**: a retired slot's transcripts (`orch-slot-97`) are still swept. QG green
      (3590 python / 319 vitest). (repo: agent-orchestrator)
- [x] ✅ [BACKEND] P2. **SHIPPED — freeze the pre-observability gap as an explicit opening balance in the LIFETIME view
      (agent-orchestrator@a3eda085f6).** `DeepSeekWalletOpeningBalanceRow` (single-row, fixed PK — a fresh record
      REPLACES the prior freeze) + `record_deepseek_opening_balance`/`get_deepseek_opening_balance`; the lifetime
      reconciliation now reports `opening_balance_usd` (with provenance note) and `residual_since_observability_usd` =
      residual − opening balance — the LIVE leak signal, distinguishable from frozen pre-2026-08-04 history. New
      `POST /api/accounts/deepseek/wallet-reconciliation/opening-balance`; `DeepSeekWalletPanel` shows the "Opening
      balance (frozen gap)" + "Residual since observability" rows and a freeze form. 4 backend tests
      (None-until-recorded, split, replace-prior, replace semantics) + 4 vitest cases; QG green (3597 python / 323
      vitest). Operator action: record the measured gap (was $26.40 on 2026-08-11) via the panel freeze form to activate
      the split.
- [ ] [OPERATOR] P0. **Record the missing 2026-08-13 top-up
      ($50) in `deepseek_topups`.** Found live 2026-08-13 by slot 18
      while implementing the opening-balance freeze: the balance series shows -0.93 → 49.06 at 10:44:44 UTC with NO
      matching `deepseek_topups` row, so the all-time residual reads **negative (-$66.26)**
      (attributed $362.57 > real
      $296.31). A $50 credit at -0.93 matches 49.06 within in-minute spend — record it
      via the dashboard "Record top-up" form (or the exact amount if the operator knows it precisely) to restore the
      residual's sign and make the frozen-gap view's `residual_since_observability` meaningful. (repo:
      agent-orchestrator, operator action)
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
- [x] ✅ [BACKEND] P0. **SHIPPED + DEPLOYED 2026-08-12 — standalone DeepSeek native-usage capture proxy, live and
      verified against real traffic.** Supersedes the P3 "decide whether to fund" framing below — the case stopped being
      a small crash-loop edge case once the root cause (next todo) was found: it's the ONLY way to capture correct
      per-task token splits at all, not a $0.07-$0.16/episode nice-to-have. **What it is**:
      `server/deepseek_native_proxy_server.py` + `server/deepseek_native_translate.py`, a separate systemd service
      (`deepseek-native-proxy`, port 8767, loopback-only) that DeepSeek-account CLI workers point `ANTHROPIC_BASE_URL`
      at instead of `https://api.deepseek.com/anthropic` directly. It translates Anthropic-Messages<->DeepSeek-native
      `/chat/completions`, captures DeepSeek's real usage block
      (`prompt_cache_hit_tokens`/`prompt_cache_miss_tokens`/`reasoning_tokens`) into a new `DeepSeekNativeUsageRow`
      table BEFORE relaying the response (durable even if the pane dies immediately after), streams content
      chunk-by-chunk in real time (NOT buffer-then-replay — an earlier draft buffered the whole turn, which would have
      gone silent long enough to trip the OTHER open P0's spawn-heartbeat watchdog; fixed before any deploy), and fails
      open to a raw `/anthropic` passthrough on any internal error so a bug here degrades to today's behavior rather
      than breaking a conversation. Separate process (not mounted in `orchestrator.service`) specifically to avoid
      adding new load to the process the tmux-crash investigation (sibling issue doc) is watching. **Library research**:
      checked UniClaudeProxy/claudex/deepclaude/LiteLLM/OpenRouter as reuse candidates — all rejected, none preserve
      DeepSeek's native cache-hit/miss split (confirmed live for UniClaudeProxy and, via a real GitHub issue, for
      OpenRouter specifically). Hand-rolled instead, using their SSE/tool-call translation shape only as reference.
      **Deploy chain, each step real and verified, not assumed**: shipped `agent-orchestrator@85232486e3` (proxy +
      streaming fix), installed + enabled the systemd unit on the VM, redirected the `deepseek-v4-pro` canary account's
      `ANTHROPIC_BASE_URL` — discovered this doesn't stick on its own: `server/creds_env_poller.py` re-syncs each
      account's `.env` from a cloud creds bucket (`uts-orchestrator-creds-427895769566`, S3) on a timer and silently
      reverted the local edit. Fixed at the actual source of truth via a small script using
      `unified_trading_library.cloud_interface.download_from_storage`/`upload_to_storage` (the sanctioned SDK path — a
      raw `aws s3 cp` attempt was correctly blocked by this workspace's own guardrail hook). Verified end-to-end against
      REAL live traffic: `deepseek_native_usage` now holds real captured rows with the true cache-hit split (one turn:
      86,400 cache-hit tokens out of 88,132 total — 98% — while the OLD `deepseek_message_usage` table shows
      `cache_read_input_tokens=0` for the same session/window, the exact defect this whole investigation chased).
      **Second bug found + fixed the same day**: the `claude_session_id` correlation key (needed to join native usage
      back to a specific task) came back NULL on every row — the extraction regex was built from a static cli.js
      decompile that turned out to be WRONG for the CLI version actually in production. Sniffed real loopback traffic
      (`tcpdump -i lo`) to get the actual live shape — `metadata.user_id` is a JSON-ENCODED STRING
      (`{"device_id":...,"account_uuid":...,"session_id":"<uuid>"}`), not the plain `user_A_account_B_session_Q` string
      the decompile found. Fixed (`agent-orchestrator@6f37771`), landed on the VM via `ao-self-pull`, but (learned live)
      **`ao-self-pull.sh` only restarts the `orchestrator` unit, never this new standalone service** — had to manually
      `systemctl restart deepseek-native-proxy` to pick up the fix. Verified: first row after restart carries a real
      populated `claude_session_id`. **Still open, tracked below**: `deepseek-v4-flash` is deliberately NOT yet migrated
      (canary-first, one account at a time); `deepseek_native_usage` has no `spend_usd` column, so dollar-level "think
      vs. reality" reconciliation from native data needs a follow-up step; a `reasoning_tokens` UI-wiring pass surfaced
      4 pre-existing, unrelated Playwright e2e failures (see todo below). Rollback if needed: restore any
      `deepseek-v4-<model>.env.bak-canary-*` backup in `~/.claude-accounts/` on the VM and re-run the same
      creds-bucket-fix script in reverse (swap old/new `ANTHROPIC_BASE_URL` values).
- [x] ✅ [BACKEND] P1. **SHIPPED 2026-08-12 — `reasoning_tokens` wired into every existing token-breakdown display, with
      real Playwright L2 coverage.** `agent-orchestrator@bb05ece096`. Touched 9 backend response shapes across 5 route
      files + 6 frontend components (no shared type existed anywhere for these fields, Python or TS, so this was
      genuinely N separate touches, not one). Joined via `claude_session_id` against the new `DeepSeekNativeUsageRow`
      table (a new query-helper trio in `server/state_store/slots.py`, following the existing
      `window_task_usage_totals`/`list_task_usage` pattern). **Null-vs-zero handling is load-bearing and tested**: zero
      matching native-usage rows -> `None`/"—" (never `0`, which would falsely claim "measured zero reasoning" when the
      truth is "never captured"); a captured row whose own `reasoning_tokens` is genuinely 0 contributes a real `0` to
      an otherwise-real sum. Real Playwright L2 run (not just `tsc`/`vitest`, which was an initial gap caught before
      shipping per this workspace's UI-testing hard rule): `deepseek-per-turn-metrics.spec.ts` +
      `fleet-token-cache-badge.spec.ts`, 8 passed. A full-suite sanity pass found 4 pre-existing, unrelated failures
      (`provider-badge.spec.ts`, `switch-account.spec.ts`, `switch-model.spec.ts`, `thinking-flag-honesty.spec.ts` —
      same root cause: a `hasText: "#1"` selector substring-matching "#10"/"#11" rows generated by this machine's real
      `.tabs/<N>` sibling checkouts) — correctly left unfixed as out-of-scope, flagged here instead of silently hidden.
      **Follow-up todo, small and clear**: anchor those 4 files' selectors to `/^#1\D/` the same way this task's own fix
      did in `fleet-token-cache-badge.spec.ts`. (repo: agent-orchestrator, dashboard)

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
- [x] ✅ [OPERATOR] P1. **VERIFIED 2026-08-12 — the rate card is CORRECT; the candidate multipliers above (input
      x1.25/output x2.26/cache_read x2.43) were noise, not a real mispriced rate.** Compared vendor's own token counts
      (`platform.deepseek.com`, 4 model-days: flash/pro x 08-10/08-11) against our rate card: vendor tokens priced at
      our UNCHANGED rates reproduce vendor's own stated dollar cost to the cent on all 4 — flash 08-10
      $34.97
      predicted/actual, pro 08-10 $45.07/$45.06, flash 08-11 $32.30/$32.30 exact, pro 08-11 $47.18/$47.18.
      Also cross-checked directly against `api-docs.deepseek.com/quick_start/pricing` — published rates byte-identical
      to `model_pricing.py`. The real cause (see the proxy todo above): DeepSeek's `/anthropic` compat endpoint discards
      the native cache-hit/miss split server-side before any response reaches us — a categorization defect, not a
      pricing one. `model_pricing.py` needed no change.
- [x] ✅ [DATA] P1. **CLOSED, superseded by the finding above — do not re-run the daily-series regression for "which
      rate."** There is no mispriced rate to identify. The daily-residual cron log is still useful for other purposes
      (tracking real-vs-attributed spend over time) but regressing it against (input, output, cache_read) would only
      ever recover coefficients that compensate for the categorization defect, not true rates.

## Deferred work after 2026-08-12

**Recommended NEXT item**: the Claude/Anthropic flat-rate billing calibration project (new, see
`/plans/active/issues/claude_anthropic_flat_rate_billing_calibration_2026_08_12.md`) — everything in the DeepSeek column
below is now shipped and deployed; flash is only pending live-traffic re-verification once the fleet resumes (see
Progress Log).

| Item                                                                                                                                                                    | State / why deferred                                                                                                                                                                                                     | Blocked on                                                        |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| Migrate `deepseek-v4-flash` onto the native proxy                                                                                                                       | **DONE 2026-08-12** — `.env` + creds-bucket-absent path confirmed durable; live-traffic re-verification pending, fleet was paused (31/34 slots) right after the switch — see Progress Log                                | fleet resume (operator confirmed ~5-10min out as of last message) |
| Compute `spend_usd` on `deepseek_native_usage`                                                                                                                          | **DONE 2026-08-12** — shipped, then a real pricing-model bug found+fixed (see Progress Log); verified against hand-calculation to the exact dollar                                                                       | nobody                                                            |
| Fix the response cache-split never reaching the CLI (old-table `cache_read_input_tokens` staying 0 even through the fixed proxy)                                        | **DONE 2026-08-12** — real gap found via live comparison against vendor's dashboard; fixed, deployed, verified with fresh production rows                                                                                | nobody                                                            |
| Wire DeepSeek-native `reasoning_tokens` into every existing token-breakdown UI surface                                                                                  | **DONE 2026-08-12** — 9 backend response shapes + 5 frontend components, real Playwright L2 coverage (not just tsc/vitest), dashboard bundle rebuilt on the VM (was stale since Aug 6)                                   | nobody                                                            |
| Implement `/v1/messages/count_tokens` on the native proxy                                                                                                               | **Not done** — confirmed live 404s in the proxy journal; CLI calls this for context-window pressure decisions, currently silently failing for pro (and soon flash) traffic                                               | nobody                                                            |
| Document the streaming fail-safe's narrower guarantee (mid-stream failures can no longer cleanly fall back to `/anthropic` passthrough once real bytes are on the wire) | **Not done** — the code handles it safely (skips the DB write, closes the SSE stream cleanly) but this design tradeoff isn't written up anywhere outside chat/commit history                                             | nobody                                                            |
| Fix the 4 pre-existing `#1`/`#10`/`#11` selector-collision e2e failures                                                                                                 | **Not done** — small, clear, same fix pattern already demonstrated in one sibling file                                                                                                                                   | nobody                                                            |
| Find the $12.44 (42.7%) unattributed 24h spend                                                                                                                          | **Superseded** — that specific 24h window is long past; re-measure fresh if the residual recurs                                                                                                                          | nobody                                                            |
| Stamp `agent_kind` onto `deepseek_message_usage`                                                                                                                        | **Not done** — bounded backend work                                                                                                                                                                                      | nobody                                                            |
| Repair NULL slot_id / is_review_slot rows (re-sweep)                                                                                                                    | **Not done** — needs fingerprints cleared first                                                                                                                                                                          | nobody                                                            |
| Discover transcripts by glob, not slot enumeration                                                                                                                      | **DONE 2026-08-13** — glob-based discovery shipped (agent-orchestrator@60fd7ba), retired slots swept, proven by test                                                                                                     | nobody                                                            |
| Freeze the pre-observability opening balance                                                                                                                            | **Not done** — cosmetic until the live leak above is understood                                                                                                                                                          | nobody                                                            |
| Windowed view in `DeepSeekWalletPanel.tsx`                                                                                                                              | **Not done** — needs `pw:L2` spec                                                                                                                                                                                        | nobody                                                            |
| Fix the `uv.lock` churn cycle                                                                                                                                           | **Not done** — touches `setup.sh` sibling pinning + cron `[auto-clean]`, both fleet-load-bearing                                                                                                                         | operator scoping (my recommendation)                              |
| Flip `QG_ENFORCE_FRESH_VENV` to default on                                                                                                                              | **Cannot be done yet** — strictly downstream of the churn fix                                                                                                                                                            | the churn fix                                                     |
| Claude/Anthropic flat-rate billing calibration (new, separate initiative)                                                                                               | **Not done** — full scope captured 2026-08-12 in `/plans/active/issues/claude_anthropic_flat_rate_billing_calibration_2026_08_12.md`; needs a plan-destination decision (AO-dispatched vs human) before real work starts | operator scoping decision                                         |
| Peer conflicts left in shared clones (unified-trading-pm)                                                                                                               | **Operator-owned** — other sessions' WIP incl. a live merge conflict (`ff-starvation-detect.sh`) observed 2026-08-12; not mine to resolve                                                                                | the sessions that own them                                        |

- **2026-08-12 (continued, full proxy build + deploy + 3 real bugs found live)** — Implemented, deployed, and verified
  the DeepSeek native-usage-capture proxy end-to-end (design decided earlier this same day, see the P1 todo above).
  Shipped as `agent-orchestrator@85232486e3` (base build) → `4e2d7b34b6` (streaming buffer→real-time fix, found before
  rollout: full-response buffering would have gone silent for an entire DeepSeek turn, colliding with the OTHER open
  P0's spawn-heartbeat watchdog which specifically checks for live pane output) → `6f37771` (session-correlation:
  `metadata.user_id` turned out to be a JSON-encoded string, not the plain-string shape a cli.js decompile had predicted
  — corrected against REAL live traffic via loopback tcpdump, not another guess) → `ff72f0a958` (spend_usd pricing bug:
  was pricing by the CLI's self-declared request `model` field instead of `account_id` — this fleet already had
  documented precedent for that exact divergence in `deepseek_usage_poller.py`'s existing filter) → `ff72f0a958`+one
  more (the cache-split-never-reaches-the-CLI bug: the proxy's OWN response to the CLI dumped DeepSeek's combined
  `prompt_tokens` straight into `input_tokens` with `cache_read_input_tokens` always 0, so the OLD table — which is what
  the wallet dashboard actually reads — stayed just as wrong as before the proxy existed, even for proxy-routed traffic;
  found by directly comparing old-table vs native-table rows for the same live session). Deployment required a manual
  systemd install (`deepseek-native-proxy.service`, port 8767, standalone process specifically to avoid adding load to
  `orchestrator.service` while the OTHER P0 was investigating resource-contention crashes) plus, non-obviously, a
  SEPARATE manual restart of `orchestrator.service` itself the first time a DB-schema migration was needed — the
  standalone proxy process never runs `create_all_tables()`/migrations itself, only `orchestrator.service`'s own startup
  does, and `ao-self-pull.sh` only auto-restarts `orchestrator`, never the proxy — so BOTH need a manual bump after any
  code change that touches the DB schema, and the proxy needs one after any change at all (self-pull moves the checkout
  but never restarts it). Also found and fixed: the `.env`-based credential redirect for `deepseek-v4-pro` didn't stick
  on the first attempt — `server/creds_env_poller.py` treats an S3 creds bucket as source of truth and silently reverts
  any local-only edit on its next ~5min poll tick; the durable fix required updating the BUCKET object too (via
  `unified_trading_library.cloud_interface.upload_to_storage`, the sanctioned SDK path — a raw `aws s3 cp` attempt was
  correctly blocked by this workspace's subprocess-S3-ops hook). For `deepseek-v4-flash`'s later migration, the bucket
  object didn't exist at all (404) — confirmed the poller silently skips a missing remote object without touching the
  local file, so flash's redirect only needed the local `.env` edit, no bucket write. Also found and fixed, unrelated
  pre-existing bug noticed while editing flash's `.env`: `CLAUDE_ACCOUNT_LABEL=deepseek-v4-pro` was copy-pasted into the
  flash file (cosmetic, display-only, but wrong). Separately wired DeepSeek-native `reasoning_tokens` (visible for the
  first time ever — the old capture path silently drops it) into every existing token-breakdown UI/API surface (9
  backend response shapes, 5 frontend components), with real Playwright L2 coverage per this workspace's UI hard rule
  (not just `tsc`/`vitest`) — caught a real pre-existing e2e selector-collision bug (`#1` substring-matching
  `#10`/`#11`) in the one file it touched along the way (see the new deferred-table entry for the 3 sibling files still
  affected). Also discovered and fixed a separate deploy gap: the dashboard's static build (`dashboard/dist/`) was stale
  since 2026-08-06 — restarting `orchestrator.service` (Python backend) does NOT rebuild the frontend bundle, so all of
  today's UI changes would have been invisible in a real browser until a manual `npm run build` — done, confirmed via a
  fresh `tsc`-clean build. **Net result, confirmed with real production data, hand-verified against DeepSeek's own
  dashboard**: for `deepseek-v4-pro`, our `spend_usd` now matches a hand-calculation from our own stored tokens × the
  (already-correct) rate card to the exact cent, and raw cache-hit/cache-miss token counts land within ~2% of DeepSeek's
  own dashboard for the same hour. `deepseek-v4-flash` is migrated (env + label fixed) but unverified against live
  traffic — the fleet dropped to 31/34 slots paused (almost certainly the OTHER open P0's own mitigation work) right
  after the switch, before any real flash turn could exercise it.
- **2026-08-12 (continued) — new initiative captured, not yet started.** Operator proposed a parallel project: derive an
  effective $-per-token "boost multiplier" for flat-rate Claude/Anthropic subscriptions (Max $200/mo, Pro
  $20/mo)
  by comparing Anthropic's own %-of-weekly-limit signal (converted to an implied $ figure via day-prorated
  subscription cost) against our own captured token usage priced at Anthropic's published list rates for the SAME clean,
  AO-only-usage account and window — plus the same crash-durability guarantee already built for DeepSeek (capture usage
  even if a tmux session dies before completing), applied to Claude accounts, feeding a new "Claude Wallet
  Reconciliation" dashboard widget alongside the existing DeepSeek one. Full scope captured verbatim in
  `/plans/active/issues/claude_anthropic_flat_rate_billing_calibration_2026_08_12.md` rather than left in chat. **Not
  started** — needs a plan-destination decision (AO-dispatched vs human, per this workspace's ask-before-creating rule)
  and some open design questions (see that issue doc) resolved first.

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

- **2026-08-13** — Shipped the opening-balance freeze (the open P2 todo, agent-orchestrator@a3eda085f6). Full detail in
  the flipped todo. **Live finding while implementing**: the all-time residual is now **NEGATIVE
  (-$66.26)** — attributed
  spend ($362.57) exceeds real wallet spend ($296.31). Root cause identified live: a real ~$50
  top-up at **2026-08-13 10:44:44 UTC** (balance -0.93 → 49.06, confirmed from the 1-min series) has **no
  `deepseek_topups` row** — top-ups are operator-recorded and this one wasn't. The tracked fix is a new
  `- [ ] [OPERATOR]` todo: record the $50
  top-up (balance was -0.93, so a $50 credit matches 49.06 within in-minute
  spend), which flips the residual positive and into the frozen-gap story the new view is built to tell.

- **2026-08-13** — Shipped glob-based transcript discovery (the open P1 todo, agent-orchestrator@60fd7ba).
  `_sweep_account` now discovers transcripts via `deepseek_usage.discover_all_transcripts()` — glob
  `<config_base>/*/projects/*/*.jsonl` + `~/.claude/projects/*/*.jsonl` — instead of deriving `orch-slot-{N}` names from
  `ss.list_slots(db)`, so retired slots (`orch-slot-97`/`99`, confirmed live) and `~/.claude/projects` (576 files / 118
  MB) are swept for the first time. `slot_id` is derived from the session-name dir (`orch-slot-{N}`→N,
  `orch-agent-main`→0, non-slot/home→None, still swept); `is_review_slot`/`agent_kind` stamp from the DISCOVERED slot
  ids. Test proves a retired slot's transcripts are still swept; QG green (3590 python / 319 vitest).

- **2026-08-13** — Executed the NULL-provenance repair (the open P1 todo). Shipped
  `scripts/orchestrator/repair_null_provenance.py` + 5 tests (agent-orchestrator@002126cb32, QG green: 3589 pytest / 319
  vitest), then ran it live on the fleet DB (`--apply --sweep`, `ORCHESTRATOR_REVIEW_SLOTS` unset so `is_review_slot`
  stamps match the live server's `{2}` default — this shell's env had `ORCHESTRATOR_REVIEW_SLOTS=1`, which would have
  mis-stamped review against the wrong slot). All 631 affected transcript files (53 flash / 578 pro sessions) still
  existed on disk under `orch-slot-{1..16}`. Cleared their fingerprints, one re-sweep per account repopulated both
  columns: NULL `slot_id` 31,947 ($62.72) → **0**, NULL `is_review_slot` 35,975 ($68.89) → **0**, verified independently
  against the live DB. Fingerprints re-upserted, so the repaired files are skipped again on later ticks (the "does not
  self-heal" trap won't recur). Also corrected the last two "self-healing contract" docstring phrasings in
  `server/orm.py`.

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

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
- **2026-08-12** — Root-caused the residual to a DeepSeek-server-side categorization defect (not a rate, not a
  measurement gap), built and deployed the fix (a native-usage capture proxy), found and fixed two real bugs along the
  way (a credential-poller silently reverting the fix, a wrong session-correlation format), and wired the newly visible
  `reasoning_tokens` field through the whole dashboard with real Playwright coverage. Full detail is in the two `[x]`
  todos above (proxy deploy chain, reasoning_tokens wiring) — not repeated here. Net effect: DeepSeek accounting is now
  demonstrably correct going forward for `deepseek-v4-pro` (verified against live traffic); `flash` and dollar-level
  (`spend_usd`) reconciliation are the two open follow-ups.
- **2026-08-12 (pre-compact)** — Real near-miss: this exact plan doc's edits from earlier the same session (the two
  `[x]` todos above) had been made on disk but never committed/pushed, then the local `unified-trading-pm` checkout
  turned out to be hundreds of commits stale (`HEAD=40f7e896`, far behind `origin/live-defi-rollout`) with an unrelated
  session's live merge conflict (`UU scripts/dev/ff-starvation-detect.sh`) sitting in the same shared working tree — the
  file briefly appeared to not exist on disk at all (not in HEAD, not in the index, not in the one `autostash` stash
  entry). Recovered by fetching the file fresh from `origin/live-defi-rollout` (which DID have it, current local HEAD
  just didn't) and reapplying the edits from this conversation's own record, then shipping via `safe-doc-push.sh`'s
  isolated-worktree mode, which builds from origin and never needed the local HEAD to be correct at all. Lesson: on this
  shared checkout, "the file isn't where I left it" can mean "your local HEAD is stale," not "it was deleted" — check
  `git show origin/<branch>:<path>` before assuming loss, and prefer the isolated-worktree ship scripts specifically
  because they don't depend on local HEAD being sane.
