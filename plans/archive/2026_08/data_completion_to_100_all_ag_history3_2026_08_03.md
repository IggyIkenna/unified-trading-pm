---
doc_type: plan
title:
  Data completion to 100% — all AGs — Progress Log history part 3 (the 2026-06-21/22/24 already-folded-out stub
  pointers)
summary: >-
  Line-cap remediation extraction from plans/active/data_completion_to_100_all_ag_2026_06_21.md's Progress Log — 47
  dated stub entries, each a header + a one-line "Moved to <sibling doc>" pointer left behind by the 2026-07-24 per-AG
  Progress Log fold-out (the actual narrative content already lives in
  data_completion_{cefi,defi,tradfi,sports}_2026_07_15.md and data_completion_to_100_all_ag_history2_2026_07_24.md — see
  those docs for the full text). Moved verbatim so the live plan stays under the 1000-line hard cap; no information
  lost, since each stub already only pointed elsewhere.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer]
tags: [backfill, manifest, honest-coverage, data-completion, history, line-cap-remediation]
related: [/plans/active/data_completion_to_100_all_ag_2026_06_21.md]
created: 2026-08-03
last_updated: 2026-08-03
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: script
drift_direction: none
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - "line-cap remediation split, 2026-08-03, per
    plans/active/issues/context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md"
---

# Data completion to 100% — all AGs — Progress Log history part 3

Extracted verbatim from `plans/active/data_completion_to_100_all_ag_2026_06_21.md`'s `## Progress Log` section on
2026-08-03, to bring the live plan back under the workspace's 1000-line hard cap
(`scripts/plan-hygiene/check_line_caps.sh`). No content changed — only relocated. Every entry below is itself already
just a pointer to where its real narrative lives (per the 2026-07-24 fold-out); nothing here is the primary source.

## Progress Log (historical stub entries)

### 2026-06-22 — GAP FOUND (operator): DeFi market-data has NO continuous live capture (daily batch only)

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-22 ~14:36 — Per-AG re-stamp COMPLETE (all 5 AGs, guarded) + UTL asset_group writer fix COMPLETED+SHIPPED

> **Moved to `data_completion_to_100_all_ag_history2_2026_07_24.md` § (line-cap remediation follow-up, 2026-07-24
> fold-in, verbatim).** Two dated sub-entries (14:36 per-AG re-stamp, 14:15 UTL asset_group writer fix + the deferred
> no-blank-asset_group QG ratchet todo, already `[x]`) moved together; nothing dropped or reworded.

### 2026-06-22 13:25 — SPORTS COMPLETION TARGET: ~2026-06-23/24

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-22 ~13:45 — P1 fix DRAFTED-BUT-INCOMPLETE + P0 scheduler PAUSED + P1 LIVE manifest-writer asset_group bug ROOT CAUSE PINNED

> **Moved to `data_completion_to_100_all_ag_history2_2026_07_24.md` § (line-cap remediation follow-up, 2026-07-24
> fold-in, verbatim).** Every checkbox in this entry was already `[x]`; nothing dropped or reworded.

### 2026-06-22 13:10 — TM/FS unbounded-HTTP HANG fixed; ETA + hang-detection codified

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-22 ~12:55 — ✅ TM+FootyStats UNBOUNDED-HTTP HANG fixed (uninherited path) + tarball + relaunch — instruments-service@dcf87f5

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-22 (DEFI lane, PM-driven backfill-everything dispatch) — PHASE A: enumerator IAM root-caused + fixed (expected_unattempted=0 → seeding)

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-22 — empty_confirmed-integrity fix PHASE 2 — manifest DELETE applied + canonical gas reseed (REVERSIBLE, VERIFIED)

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-22 10:55 — API-Football stopped = COMPLETED-not-stalled, BUT real 2026 gap found + now fetching

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-22 10:05 — memory fix HELD; enrichment 2nd-pass + SFI complete; one relaunch blocked on foreign WIP

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-22 06:30 — honest-cov is UNDERSTATED fleet-wide: ~1M phantom expected_unattempted (operator caught it on weather)

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-22 06:05 — wake-fix codified; 300k/day in use; TM/SFI/FootyStats OOM ROOT-CAUSED + fixed

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-22 05:40 — defi fan-out: 14 new year-sharded VMs launched (dex-pools/swaps/liquidations/lending gaps)

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-22 05:25 — overnight result: 3 sources OOM-crashed (e2-standard-2 too small); relaunched e2-standard-8

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-24 ~05:35 — DIAGNOSIS (no code bug): golden FIXTURE_LINEUPS captured flat because the running backfill uses `--force` (re-fetch already-captured cells)

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-21 ~23:00 — DEPLOYED + VERIFIED: live_databento (prod-confirmed) + equity ohlcv_1s (capturing) + MDPS batching

> **Moved to `data_completion_tradfi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-TradFi-lane; plan
> line-cap remediation).**

### 2026-06-21 22:55 — skip-fresh verified all sources; odds re-fetch FIXED; 2 follow-ups

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-21 22:40 — DISPARATE-SOURCE CONCURRENCY (operator insight): all fixture-driven sources fired in parallel

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-21 ~22:00 — tradfi `live_databento` source-stamp FIXED + 2 manifest cleanups actioned

> **Moved to `data_completion_tradfi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-TradFi-lane; plan
> line-cap remediation).**

### 2026-06-21 22:00 — "finish the current": parallelized for speed; honest completion picture

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-21 21:40 — ODDS API UPGRADED (blocker RESOLVED) + API-Football rate analysis

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-21 — SPORTS lane: enrichment OOM fix + final autonomous state

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-21 — SPORTS lane STATE SNAPSHOT (autonomous, operator away 2h) — for context-compression resume

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-21 — CEFI lane: live producer unblocked (missing lifecycle topic — fleet-wide finding)

> **Moved to `data_completion_cefi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-CeFi-lane; plan
> line-cap remediation).**

### 2026-06-21 — SPORTS lane (/autonomous, Opus): odds flowing; API-Football credential block + silent-empty bug FIXED

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-21 — DEFI lane: FULL FAN-OUT LAUNCHED + real root-cause of catalog blocker FIXED

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-21 — DEFI lane: blocker fixes IN FLIGHT — full dependency chain mapped

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-21 — SPORTS lane: RATE-LIMIT root-caused + fixed (operator: "only ~1k req/hr vs 1.2k/min — way too slow")

> **Moved to `data_completion_sports_2026_07_24.md` § Progress Log (2026-07-24 fold-in, verbatim, per-Sports-lane; plan
> line-cap remediation).**

### 2026-06-21 — DEFI lane (/autonomous, Opus): bucket bug is FLEET-WIDE across defi handlers

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-21 — CEFI lane (/autonomous, Opus): triage measured + live-path diagnosed

> **Moved to `data_completion_cefi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-CeFi-lane; plan
> line-cap remediation).**

### 2026-06-21 — DEFI lane: bucket fix SHIPPED + PROOF found 2 more blockers (gating the fan-out)

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-21 — TRADFI lane: launcher bugs diagnosed + fixed; CME-2026 canary verifying

> **Moved to `data_completion_tradfi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-TradFi-lane; plan
> line-cap remediation).**

### 2026-06-21 15:18 — TRADFI batch fan-out LIVE + PROVEN (15 VMs capturing)

> **Moved to `data_completion_tradfi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-TradFi-lane; plan
> line-cap remediation).**

### 2026-06-21 15:42 — TRADFI lane: ALL 3 dispatch items launched/done

> **Moved to `data_completion_tradfi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-TradFi-lane; plan
> line-cap remediation).**

### 2026-06-21 16:25 — ohlcv_1s added (CME+CBOE only; equities don't support it)

> **Moved to `data_completion_tradfi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-TradFi-lane; plan
> line-cap remediation).**

### 2026-06-21 16:40 — CME event contracts (binary/event markets) — IS + MTDS

> **Moved to `data_completion_tradfi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-TradFi-lane; plan
> line-cap remediation).**

### 2026-06-21 17:49 — TRADFI LIVE producer launched (live_databento; live==batch)

> **Moved to `data_completion_tradfi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-TradFi-lane; plan
> line-cap remediation).**

### 2026-06-21 — DEFI lane: RE-SEQUENCED per operator (IS→100%→rollup→MTDS) + real hang root-cause

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-21 17:55 — TRADFI live_databento: diagnosed (3 bugs + subscription unknown) — FLAGGED not stomped

> **Moved to `data_completion_tradfi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-TradFi-lane; plan
> line-cap remediation).**

### 2026-06-21 — DEFI lane: CATALOG GATE OPEN — capturing real data; full fan-out relaunched

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-21 19:40 — TRADFI honest-cov re-measured: 5.3% → 13.8% (captured TRIPLED), still climbing

> **Moved to `data_completion_tradfi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-TradFi-lane; plan
> line-cap remediation).**

### 2026-06-21 — DEFI lane: capturing works, but honest-cov BLOCKED by venue-format mismatch in expected_unattempted seeding

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-21 — DEFI honest-cov fix LANDED (root-cause in code) + codified

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-22 05:25 — DEFI status + gas-fees MANTLE BLOCKED-CREDENTIALS

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-22 07:50 — DEFI lane DONE (fetchable gap closed) + deferred follow-ups

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-22 12:40 — DEFI REGRESSION found + fixed: stale-enumerator-build re-seeded 1.44M LEGACY-venue phantoms

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**

### 2026-06-22 13:00 — DEFI 2nd defect found+fixed: 441k blank-asset_group captures (honest_cov 10.67%→18.66%)

> **Moved to `data_completion_defi_2026_07_15.md` § Progress Log (2026-07-24 fold-in, verbatim, per-DeFi-lane; plan
> line-cap remediation).**
> </content>
