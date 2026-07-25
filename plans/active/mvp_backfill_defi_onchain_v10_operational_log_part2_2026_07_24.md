---
doc_type: plan
title:
  MVP backfill — DeFi all on-chain data_types — operational log, Part 2 of 6 (extracted from
  mvp_backfill_defi_onchain_v10)
summary: >-
  Verbatim historical operational log extracted from mvp_backfill_defi_onchain_v10_2026_06_27.md's G1.5 nested
  sub-history and Progress Log sections, split out solely to bring the parent plan back under the line-cap (pure hygiene
  move — no todo/gate/state content changed). Re-chunked 2026-07-24 from an original 3-part split into 6 parts to comply
  with the operator's same-day ruling removing the umbrella:true line-cap exemption (flat 1000L hard cap, no
  exceptions). This is Part 2 of 6 in strict chronological order — read all 6 parts in filename order for full context.
  Part 1's filename is kept stable across both the original 2026-07-24 split and this re-chunk so existing external
  references keep resolving to real content.
status: complete
nature: process
asset_group: [defi]
stage: [data]
repos: [deployment-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [mvp, backfill, defi, on-chain, dex, lending, lst, perp-funding, oracle, spot-vm, v10, progress-log, plan-hygiene]
related:
  [
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md,
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_part3_2026_07_24.md,
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_part4_2026_07_24.md,
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_part5_2026_07_24.md,
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_part6_2026_07_24.md,
    /plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    /plans/active/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: defi_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Plan line-cap hygiene remediation, /plans/active/issues/plan_line_cap_remediation_2026_07_23.md row 21 — pure
  extraction of already-written historical narrative out of mvp_backfill_defi_onchain_v10_2026_06_27.md, operator
  approved 2026-07-23 (locked plan, unlock+extract authorized); re-chunked from 3 to 6 parts 2026-07-24 per the same-day
  umbrella-exemption-removal ruling (plans/active/issues/plan_line_cap_remediation_2026_07_23.md).
assigned_role: data_engineering
drift_direction: advance-code
---

# MVP backfill — DeFi on-chain — operational log (Part 2 of 6)

**LST-rates — 2021-11-04 @ 20:12 UTC:** 2 shard entries; LIDO ETHEREUM + ANKR ETHEREUM (1 row each). Pre-genesis for
most tokens; early-date coverage expected to be sparse.

**Perp-funding — 2024-03-25 @ 20:12 UTC:** 7 shard entries, 3,152 records. HYPERLIQUID active; POLYMARKET perp recording
EXPECTED_PRE_VENUE_LAUNCH (launch 2026-04-21) — correct honest-absence encoding.

**Disk:** 16G free (recovered from 2.0G via /tmp cleanup: removed stale IS-index parquets, sports-audit parquets,
regen-ldr-plans dirs — all from prior session runs, no open handles). Stable.

**Phantom dry-run (bapes9tp0):** In-progress — started 20:00 UTC (~17 min elapsed, prior run took ~35 min). Output will
land when complete. Apply mode needed after to flip 219,529 phantom "captured" rows → "attempted_failed".

### 19:47 UTC check — DRIFT 2025-12-24 ~38% (batch ~23,098/60,586); lending-indices ~2023-02-27; both uploaders died 19:07; disk 917MB (2026-06-28 19:47 UTC)

**VM roster (19:47 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT 2025-12-24 — uploader died again (19:07:08 UTC):** Log stale 40 min (523,501 bytes). Dec 24 parquet NOT in GCS →
app still processing (not done, not crashed). Same recurring uploader-thread-death pattern. Estimated progress at 19:47:
elapsed 274 min × 84.3 batch/min = **~23,098 batches (~38.1%)**. Remaining ~37,488 batches / 84.3 = 445 min (~7.4 hrs).
ETA **~03:11 UTC 2026-06-29**.

**lending-indices 021507 — uploader died simultaneously (19:07:33 UTC):** Log also stale 40 min (9.9MB, +356KB since
last check — was active until uploader died). Last visible completion: 2023-02-10 @ 19:06:48 UTC. At 19:47: +40 min /
2.4 min/date ≈ +17 dates → **~2023-02-27**. ~1,215 dates remain @ 2.4 min/date = ~49 hrs. ETA ~**2026-06-30 20:30 UTC**.
Pattern note: both DRIFT + lending-indices uploaders died at same moment (19:07) — likely GCS auth token refresh cycle
on both VMs simultaneously.

**Disk 917MB** (down 11MB from 928MB; stable trend).

### 19:17 UTC check — DRIFT 2025-12-24 ~34% (batch ~20,569/60,586); lending-indices ~2023-02-15; disk 928MB (2026-06-28 19:17 UTC)

**VM roster (19:17 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT 2025-12-24:** Log updated 19:03:08 UTC (uploader healthy; 523KB). Last error: 504@batch=19,039 @ 18:58:46 UTC.
Progress at 19:17: elapsed 244 min × 84.3 batch/min = **~20,569 batches / 60,586 (~34%)**. Remaining: ~41,017 batches @
84.3/min = ~487 min (~8.1 hrs). ETA **~03:20 UTC 2026-06-29**.

**lending-indices 021507 — ~2023-02-15 @ 19:17 UTC:** Rate settling at ~2.4 min/date (faster than earlier 2.67
estimate). Completions observed 18:38–18:59: 2023-01-30 → 2023-02-08 (10 dates in 21.5 min). `aave_v3_ETHEREUM`
consistently active (218–332 rows/date). COMPOUND_V3 non-ETHEREUM still 0 (schema issue persists). ~1,224 dates remain @
2.4 min/date = **~49 hrs** — ETA revised to **~2026-06-30 20:00 UTC** (vs prior Jul-01 01:00 estimate).

**Disk 928MB** (down 52MB from 980MB). Above 600MB threshold; no action needed.

### 18:47 UTC check — DRIFT 2025-12-24 ~27.4% (batch ~16,634); lending-indices 2023-01-27 aave_v3_ETH CONFIRMED; COMPOUND_V3 schema ⚠️ (2026-06-28 18:47 UTC)

**VM roster (18:47 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT 2025-12-24:** Log uploaded 18:29 UTC (uploader healthy; 518KB). Last error: 502@batch=16,036 @ 18:21 UTC.
Calculated progress: 195 min × 85.3 batch/min = **~16,634 batches / 60,586 (~27.4%)**. ETA **~03:23 UTC 2026-06-29**
(~8.4 hrs). Silent running between error reports is normal.

**lending-indices 021507 — 2023-01-27 DONE @ 18:28:34 UTC — aave_v3_ETHEREUM=283 CONFIRMED ✅:**
`{'aave_v3_ETHEREUM': 283, 'aave_v3_ARBITRUM': 11385, 'aave_v3_OPTIMISM': 0, 'aave_v3_POLYGON': 6656, 'aave_v3_AVALANCHE': 1954, 'aave_v3_BASE': 0, 'aave_v3_LINEA': 0, 'aave_v3_BSC': 0, 'spark_ETHEREUM': 0, 'compound_v3_ETHEREUM': 2, 'compound_v3_ARBITRUM': 0, 'compound_v3_BASE': 0, 'compound_v3_OPTIMISM': 0}`.
AAVE V3 ETHEREUM genesis ~Jan 27, 2023 validated — 283 rows on first active date.

**⚠️ FINDING — COMPOUND_V3 schema errors for non-ETHEREUM chains:** ARBITRUM/BASE/OPTIMISM all returning 0 rows with
schema-mismatch errors: `Type 'DailyMarketAccounting' has no field 'supplyApr'` etc. Three schema strategies tried
(compound_v3_custom / compound_v3_flat / messari_lending), all fail → writes 0 rows. COMPOUND_V3_ETHEREUM works (2
rows). Historical subgraph schema evolved; early-date queries fail. Operator triage needed: empty_confirmed vs
attempted_failed for these chains pre-schema-migration. **Not actioned in this monitoring session — flagged for operator
review.**

**Disk 980MB ✅** (stable, down 6MB from 986MB).

### 18:17 UTC check — DRIFT 2025-12-24 ~26% (batch ~16,036/60,586); lending-indices 2023-01-25; disk 986MB ✅ (2026-06-28 18:17 UTC)

**VM roster (18:17 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT 2025-12-24:** Cluster of 4 HTTP errors 17:45–18:02 (batches 13,155/14,073/14,390/14,472), then 502@batch=16,036
(18:21). Rate 85.3 batch/min (slight dip). At 188 min: ~16,036/60,586 (~26.5%). ETA **~03:23 UTC 2026-06-29** (~8.7
hrs). Error cluster normal — processing continued.

**lending-indices 021507 — 2023-01-25 @ 18:23 UTC:** `aave_v3_ETHEREUM=0` still — AAVE V3 Ethereum activation expected
~Jan 27, 2023. First non-zero ETHEREUM rows imminent (within ~2 dates). COMPOUND_V3 all 0. ~2.67 min/date; ~1,245 dates
remaining ≈ **55 hrs** (ETA ~2026-07-01 01:00 UTC).

**Disk 986MB ✅** — RECOVERED from 865MB (git gc/repack freed ~121MB on other slots). Concern resolved.

### 17:47 UTC check — DRIFT 2025-12-24 ~22% (batch ~13,329/60,586); lending-indices 2023-01-13; disk 865MB (2026-06-28 17:47 UTC)

**VM roster (17:47 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT 2025-12-24:** 504@batch=13,155 (17:45, 151 min). Rate 86.8 batch/min consistent. At 153 min: ~13,329/60,586
(~22%). ETA **~03:11 UTC 2026-06-29** (~9.1 hrs). No anomalies.

**lending-indices 021507 — 2023-01-13 @ 17:51 UTC:** `aave_v3_ETHEREUM=0` still (expected; Ethereum markets not
activated until late Jan 2023). COMPOUND_V3 chains all 0 (Arbitrum/Base/Optimism V3 not yet deployed Jan 2023). ~2.67
min/date; ~1,257 dates remaining ≈ **56 hrs** (ETA ~2026-07-01 01:00 UTC).

**Disk 865MB** — decline rate slowing: 127→60→48 MB/30min. May stabilize before 500MB. Will act at <600MB.

### 17:17 UTC check — DRIFT 2025-12-24 ~18% (batch ~10,763/60,586); lending-indices 2023-01-01; disk 913MB (2026-06-28 17:17 UTC)

**VM roster (17:17 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT 2025-12-24:** 502@batch=9,722 (17:05, 111 min elapsed). Rate 87.3 batch/min. At 123 min: ~10,763/60,586 (~18%).
ETA **~03:07 UTC 2026-06-29** (~9.5 hrs remaining). Progress is steady — no anomalies.

**lending-indices 021507 — 2023-01-01 @ 17:19 UTC:** Just crossed into 2023. `aave_v3_ETHEREUM=0` — now understood as
expected: AAVE V3 Ethereum protocol did not have active markets until early 2023 (launched Jan 2023, not Mar 2022). The
291-day zero streak from 2022-03-16 is `empty_confirmed`, not a data gap. First non-zero ETHEREUM rows expected
~2023-01-27 (AAVE V3 Ethereum activation date). ~2.46 min/date; ~1,270 dates remaining ≈ **52 hrs** (ETA ~2026-06-30
21:00 UTC).

**Disk:** 913MB — decline slowed to ~60MB/30min (was 130MB). At this rate hits 500MB ~20:47 UTC. DRIFT finishes ~03:07
UTC Jun 29 — disk could be critical before then. Will act at <600MB.

### 16:47 UTC check — DRIFT 2025-12-24 ~13% (batch ~8,072/60,586); lending-indices 2022-12-19; disk 973MB ⚠️ (2026-06-28 16:47 UTC)

**VM roster (16:47 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT 2025-12-24:** Silent since 15:52 (batch=3,360) — expected. At 93 min elapsed: ~8,072/60,586 batches (~13%). Rate
86.8 batch/min sustained. ETA **~03:11 UTC 2026-06-29** (~10.4 hrs remaining).

**lending-indices 021507 — 2022-12-19 @ 16:47 UTC:** 278 days post-genesis. `aave_v3_ETHEREUM=0` persists. ~2.46
min/date (back to normal); ~1,283 dates remaining ≈ **53 hrs** (ETA ~2026-06-30 21:00 UTC).

**⚠️ Disk 973MB** (sub-1GB) — declining ~130-155MB/hr from other-slot git activity. No large /tmp files to clean. At
current rate hits 500MB ~20:00 UTC. DRIFT Dec 24 completes ~03:11 UTC Jun 29 — disk will be critical before then. Will
clean stale /tmp files if available; may need operator awareness if drops below 500MB.

### 16:17 UTC check — DRIFT 2025-12-24 ~9% (batch ~5,459/60,586, ETA ~03:11 UTC Jun29); lending-indices 2022-12-06 (2026-06-28 16:17 UTC)

**VM roster (16:17 UTC):** All 6 G1 VMs RUNNING. No preemptions. Disk: 1.1G (stable — decline stopped).

**DRIFT 2025-12-24:** 502@batch=3,360 (15:52, 38.7 min elapsed). Rate 86.8 batch/min (consistent). At 63 min:
~5,459/60,586 batches (~9%). ETA **~03:11 UTC 2026-06-29** (~635 min remaining / ~10.6 hrs). Dec 24 is 3.52× larger than
Dec 23 (60,586 vs 17,207 batches) — confirms Christmas Eve 2025 volume spike.

**lending-indices 021507 — 2022-12-06 @ 16:15 UTC:** 265 days post-genesis. `aave_v3_ETHEREUM=0` persists. ~3.0 min/date
(avg); ~1,296 dates remaining ≈ **65 hrs** (ETA ~2026-07-01 09:00 UTC).

### 15:47 UTC check — DRIFT 2025-12-24 started (6.06M sigs — 3.5× outlier, ETA 03:00 UTC); lending-indices 2022-11-27 (2026-06-28 15:47 UTC)

**VM roster (15:47 UTC):** All 6 G1 VMs RUNNING. No preemptions. Disk: 1.1G (declining ~0.2G/hr — monitor).

**DRIFT 2025-12-23 confirmed:** 15:13:26 UTC — 1,720,013 rows, 200 min. Rate 86 batch/min (17,207 batches).

**⚠️ DRIFT 2025-12-24 — VOLUME OUTLIER: 6,058,565 sigs** (6.06M vs Dec 23's 1.72M — 3.5×). Christmas Eve 2025 spike.
60,586 batches @ 86 batch/min → **~705 min (~11.75 hrs)**. ETA: **~03:00 UTC 2026-06-29**. No 502/504s yet (started
15:13:47). Dec 24 parquet not in GCS — confirmed still processing. **Impact on overall timeline**: if Dec 25-31 have
similar or higher volumes, Christmas week alone = 5-7× longer than Jan 9-14 avg (121 min each). DRIFT completion could
extend significantly past original operator stall decision point. OPERATOR DECISION on options A/B/C remains pending —
but context now richer (Jan-Dec gap was fast; Dec 23+ is heavy).

**lending-indices 021507 — 2022-11-27 @ 15:43 UTC:** 256 days post-genesis. `aave_v3_ETHEREUM=0` persists. ~2.5 min/date
(avg recent); ~1,308 dates remaining ≈ **55 hrs** (ETA ~2026-06-30 22:00 UTC).

**Disk:** 1.1G free — declining from 1.5G at 13:47 (~0.1G/30min). No /tmp parquets to clean. Will flag operator if drops
below 500MB.

### 15:17 UTC check — DRIFT 2025-12-23 ✅ DONE (~15:14 UTC); Dec 24 started; lending-indices 2022-11-16 (2026-06-28 15:17 UTC)

**VM roster (15:17 UTC):** All 6 G1 VMs RUNNING. No preemptions. Disk: 1.2G stable.

**DRIFT 2025-12-23 COMPLETE** — GCS parquet confirmed at 15:17 check; log uploader at 15:13 (490,816 bytes) captured
content through batch=13,962 (14:36), then silent (success). Last 502 at batch=13,962; completion log line just missed
the 15:13 upload window — will appear on next upload. Duration ~202 min from 11:53 start; 1,720,513 rows (est). Rate:
85.2 batch/min (17,207 batches / 202 min) — most consistent date yet. **2025-12-23 is date 344 of ~527.** 2025-12-24 now
loading; Dec 24 sig count TBD at next check.

**lending-indices 021507 — 2022-11-16 @ 15:10 UTC:** 245 days post-genesis. `aave_v3_ETHEREUM=0` persists. ~2.4
min/date; ~1,319 dates remaining ≈ **53 hrs** (ETA ~2026-06-30 20:00 UTC).

### 14:47 UTC check — DRIFT 2025-12-23 ~87% (batch ~14,910/17,207, ETA 15:14); lending-indices 2022-11-04 (2026-06-28 14:47 UTC)

**VM roster (14:47 UTC):** All 6 G1 VMs RUNNING. No preemptions. Disk: 1.2G.

**DRIFT 2025-12-23:** 502@batch=13,962 (14:36). Rate 85.7 batch/min sustained. At 174 min elapsed: ~14,910/17,207
(~87%). ETA **~15:14 UTC** (~27 min). Total 5 HTTP errors on this date — all normal skips.

**lending-indices 021507 — 2022-11-04 @ 14:40 UTC:** 233 days post-genesis. `aave_v3_ETHEREUM=0` persists.
ARBITRUM=3,835 / POLYGON=11,092 / AVALANCHE=2,927 (growing). ~2.31 min/date; ~1,331 dates remaining ≈ **51 hrs** (ETA
~2026-06-30 18:00 UTC).

### 14:17 UTC check — DRIFT 2025-12-23 ~71% (batch ~12,240/17,207, ETA 15:15); lending-indices 2022-10-22 (2026-06-28 14:17 UTC)

**VM roster (14:17 UTC):** All 6 G1 VMs RUNNING. No preemptions. Disk: 1.3G stable.

**DRIFT 2025-12-23:** 502@batch=11,567 (14:09). Rate 85.1 batch/min confirmed. At 144 min elapsed: ~12,240/17,207
(~71%). ETA **~15:15 UTC** (~58 min). Consistent across all checks: 84-85 batch/min sustained.

**lending-indices 021507 — 2022-10-22 @ 14:10 UTC:** 220 days post-genesis. `aave_v3_ETHEREUM=0` persists. ~2.46
min/date; ~1,344 dates remaining ≈ **55 hrs** (ETA ~2026-06-30 21:00 UTC).

### 13:47 UTC check — DRIFT 2025-12-23 ~56% (silent since 13:04); lending-indices 2022-10-09 (2026-06-28 13:47 UTC)

**VM roster (13:47 UTC):** All 6 G1 VMs RUNNING. No preemptions. Disk: 1.3G.

**DRIFT 2025-12-23:** Last 502/504 at batch=5,966 (13:04). Silent since — expected. At 114 min elapsed: ~9,576/17,207
batches (~56%). Rate consistent at ~84 batch/min. ETA ~15:17 UTC (~90 min remaining).

**lending-indices 021507 — 2022-10-09 @ 13:38 UTC:** 207 days post-genesis. `aave_v3_ETHEREUM=0` persists (longest gap
so far). ARBITRUM=1,007 / POLYGON=10,132 / AVALANCHE=678 rows — active on other chains. ~2.31 min/date; ~1,356 dates
remaining ≈ **52 hrs** (ETA ~2026-06-30 18:00 UTC).

### 13:17 UTC check — DRIFT 2025-12-23 ~40% (batch ~6,972/17,207); lending-indices 2022-09-26 (2026-06-28 13:17 UTC)

**VM roster (13:17 UTC):** All 6 G1 VMs RUNNING. No preemptions. Disk: 1.5G stable.

**DRIFT 2025-12-23:** Warnings: 502@batch=5,519 (12:58), 504@batch=5,966 (13:04). Rate steady ~84 batch/min. At 83 min
elapsed → ~6,972/17,207 batches (~40%). ETA ~15:17 UTC (~120 min remaining). Silent between errors — healthy.

**lending-indices 021507 — 2022-09-26 @ 13:08 UTC:** 194 days post-genesis. `aave_v3_ETHEREUM=0` persists. ~2.36
min/date consistent; ~1,370 dates remaining ≈ **54 hrs** (ETA ~2026-06-30 19:00 UTC).

### 12:47 UTC check — DRIFT 2025-12-23 ~26% (batch ~4,563/17,207); lending-indices 2022-09-12 (2026-06-28 12:47 UTC)

**VM roster (12:47 UTC):** All 6 G1 VMs RUNNING. No preemptions. Disk: 1.5G.

**DRIFT 2025-12-23:** 1,720,713 sigs / 17,207 batches. Warnings: 504@batch=1,215 (12:07), 504@batch=1,259 (12:08),
502@batch=2,028 (12:17). At 84.5 batch/min, ~54 min elapsed → ~4,563 batches done (~26%). ETA ~15:17 UTC (~150 min). Dec
23 is largest date yet (1.72M sigs vs Jan 9's 1.21M). Processing normally post each HTTP error (silent on success).

**lending-indices 021507 — 2022-09-12 @ 12:35 UTC:** 180 days post-genesis. `aave_v3_ETHEREUM=0` persists. ~2.36
min/date; ~1,384 dates remaining ≈ **54 hrs** (ETA ~2026-06-30 19:00 UTC).

### 12:17 UTC check — DRIFT 2025-12-23 started (1.72M sigs!); 343/~527 dates done; stall revised (2026-06-28 12:17 UTC)

**VM roster (12:17 UTC):** All 6 G1 VMs RUNNING. No preemptions. Disk: 1.6G (recovered).

**DRIFT — MAJOR UPDATE — stall projection revised:**

- 2025-01-14 ✅ DONE at 11:50:26 UTC — 816,966 rows, 104 min.
- 2025-01-15 ✅ DONE at 11:50:34 UTC — **846 rows, 8 seconds** (tiny sig window).
- **2025-01-16 through 2025-12-22 — all 0 sigs — burned through in ~3 min total** (~341 dates, 0 sigs each →
  `empty_confirmed`). ManifestWriter shows 343 total entries at 2025-12-22.
- **2025-12-23 now processing** (loaded at 11:53 UTC): **1,720,713 sigs** = 17,207 batches. At 80 batch/min → ~215 min.
  ETA ~**15:28 UTC**.

**Revised stall assessment:** The orchestrator's 44-day estimate assumed all ~520 remaining dates at 121 min avg. That
was wrong — the parts sig index has dense coverage only for Jan 9-15, 2025 (done) and Dec 23, 2025 onwards (now
loading). The ~341-date Jan-16→Dec-22 gap returned 0 sigs in seconds each. **True remaining: ~184 dates (Dec 23 →
Jun 28) with unknown sig density per date.** Dec 23 is the heaviest date seen (1.72M sigs > Jan 9's 1.21M). OPERATOR
DECISION on options A/B/C still open — but VM is now past the worst gap.

**Dates completed:** 6 with data (Jan 9–14) + 1 tiny (Jan 15, 846 rows) + ~341 empty (Jan 16–Dec 22) = **343 total** of
~527.

**lending-indices 021507 — 2022-08-29 @ 12:02 UTC:** 166 days post-genesis, `aave_v3_ETHEREUM=0` persists. ~2.4
min/date; ~1,398 dates remaining ≈ **56 hrs** (ETA ~2026-06-30 20:00 UTC). SPARK/COMPOUND_V3 all 0.

### 11:47 UTC check — DRIFT 2025-01-14 ~99% (parquet imminent); lending-indices 2022-08-15; disk 889MB (2026-06-28 11:47 UTC)

**VM roster (11:47 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT 2025-01-14:** 817,166 sigs / 8,172 batches; 101 min elapsed @ 10:06 start. No 502s logged since batch=18
(earliest in date) — processing cleanly. GCS parquet not yet landed at 11:47 (ETA 11:48 UTC). Log uploader intermittent
again (last GCS write 11:28:52, 102,792 bytes — app healthy, heartbeats flowing). Completion expected within minutes.
Dates done: **6 of ~527** (Jan 9–14). Running duration per date: 147/122/97/92/150/~102 min.

**lending-indices 021507 — 2022-08-15 @ 11:28 UTC:** 152 days post-genesis. `aave_v3_ETHEREUM=0` persists. ~2.3 min/date
rate; ~1,414 dates remaining ≈ **38 hrs** (ETA ~2026-06-30 01:00 UTC). SPARK/COMPOUND_V3 all 0.

**⚠️ Disk 889MB (down from 1.9G):** Tab 14 repo newly initialized at 3.2G (another slot's clone). 889MB still safe; no
/tmp parquets to clean. Will flag if drops below 500MB.

### 11:17 UTC check — DRIFT 2025-01-14 ~69%; lending-indices 2022-08-01 (138d ETH gap) (2026-06-28 11:17 UTC)

**VM roster (11:17 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT 2025-01-14:** Processing silently since 10:06:33 (batch=18 was first 502 — silent on success after). 817,166
sigs / 8,172 batches. At 71 min elapsed @ ~80 batch/min ≈ 5,680 batches (69%). Est completion ~11:48 UTC. Log uploader
intermittent again: last GCS update 10:56:51 UTC (20 min gap); file grew 94,408→98,600 bytes, heartbeats flowing —
Python app healthy. Pattern consistent with prior 09:50–10:24 gap (uploader restarts itself eventually).

**lending-indices 021507 — 2022-08-01 @ 10:55 UTC:** 139th day post-genesis. `aave_v3_ETHEREUM=0` still. 10:50:57 (8,062
rows), 10:53:17 (6,618 rows), 10:55:39 (8,839 rows) = ~2.3 min/date recent rate. ~1,427 dates remaining (2022-08-01 →
2026-06-28) ≈ **38 hrs** → ETA ~2026-06-30 01:00 UTC. Disk: 1.9G stable.

### 10:47 UTC check — DRIFT 2025-01-13 ✅ DONE (1,215,491 rows); 2025-01-14 started; lending-indices 2022-07-19 (2026-06-28 10:47 UTC)

**VM roster (10:47 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT 2025-01-13 COMPLETE at 10:06:16 UTC — 1,215,491 rows, 150 min duration.**

- 2025-01-14 started at 10:06:18 UTC; 817,166 sigs (8,172 batches). First 502 at batch=18.
- Expected completion: ~11:48 UTC (~102 min @ 80 batch/min). Rate tracking: Jan 9=147m, 10=122m, 11=97m, 12=92m,
  13=150m.
- Log uploader gap 09:50–10:24 UTC (34 min) — uploader recovered; Python app was healthy throughout.
- Dates completed so far: **5 of ~527** (Jan 9–13). Remaining ~522 dates × 121 min avg = ~44 days ETA. **Operator
  decision on DRIFT stall still pending (options A/B/C from orchestrator banner).**

**lending-indices 021507 — 2022-07-19 @ 10:24 UTC: 199 dates complete:** `aave_v3_ETHEREUM=0` still (now at 2022-07-19 =
125 days post-genesis). `aave_v3_OPTIMISM` had 8 rows on one date (2022-07-??) then back to 0 — extremely sparse early
OPTIMISM data. Rate: ~1.92 min/date; ~1,440 dates remaining ≈ **46 hrs** (ETA ~2026-06-30 09:00 UTC).
`aave_v3_BASE=0, spark_ETHEREUM=0, compound_v3_*=0` — all not yet deployed in mid-2022.

**Disk:** 2.0G stable.

### 10:17 UTC check — DRIFT log stalled 09:50 (uploader death?); lending-indices 2022-07-04 (110d ETH gap) (2026-06-28 10:17 UTC)

**VM roster (10:17 UTC):** All 6 G1 VMs RUNNING per `gcloud compute instances list`. No preemptions.

**⚠️ DRIFT log upload stall — investigating:** GCS `run.log` last updated 09:50:49 UTC (27 min stale). Log uploader
interval=60s so should have uploaded at 09:51, 09:52… but creation+update time both 09:50:49. Two scenarios: (A)
Uploader loop died but Python app still processing — parquet write will land when 2025-01-13 completes. (B) Python
application crashed at ~09:50 — VM is RUNNING but idle; 2025-01-13 will never complete. **Evidence check:** No
2025-01-13 parquet in GCS yet (checked at 10:17 — `CommandException: no objects`). Expected completion ~10:05 UTC (7,366
batches at 09:06 + 58.6 min @ 80 batch/min). Now 12 min past expected, no file. Monitoring only — will confirm at 10:47
UTC check. If no parquet by 10:47 → **NOTIFY OPERATOR of likely crash.**

**lending-indices 021507 — 2022-07-04 @ 09:49 UTC: 6,299 records:** POLYGON=3339, AVALANCHE=2131, ARBITRUM=829.
`aave_v3_ETHEREUM=0` — **110 days post-genesis**. `aave_v3_OPTIMISM=0` persistent. New: `compound_v3` all 0 (Compound V3
not deployed on these chains in mid-2022). `spark_ETHEREUM=0` (not deployed until later). Rate: 2.5 min/date; ~1,454
dates remaining ≈ ~60 hrs. Disk: 1.9G stable.

### 09:47 UTC check — DRIFT 2025-01-13 ~89%; lending-indices 2022-07-02 (108d ETH gap) (2026-06-28 09:47 UTC)

**VM roster (09:34 UTC watchdog + direct 09:47 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-13:** Log silent since 09:06 (batch 7,366) — expected (success = no log). At 09:47: ~10,769/12,157
batches (89%). Est. completion ~10:04 UTC (~17 min). Projected duration ~148 min (matches Jan 9 at 147 min). Per-date
avg now: 147/122/97/92/148 = ~121 min avg → 520+ remaining dates → confirms orchestrator 44+ day stall.

**lending-indices 021507 — 2022-07-02 @ 09:44 UTC: 4,545 records:** POLYGON=2393, AVALANCHE=1434, ARBITRUM=718.
`aave_v3_ETHEREUM=0` — **108 days post-genesis**. `aave_v3_OPTIMISM=0` also persistent. Rate: 2.31 min/date; ~1,456
dates remaining ≈ 56 hrs. Disk: 1.9G.

### 09:16 UTC check — DRIFT 2025-01-13 67%; lending-indices 2022-06-19 (95d ETH gap) (2026-06-28 09:16 UTC)

**VM roster (09:04 UTC watchdog + direct 09:16 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-13:** Batch 7,366/12,157 at 09:06 UTC (HTTP 502, `continue`). At 09:16: ~8,196 done (67%). Rate: ~83
batches/min. Remaining: ~3,961 batches ≈ 48 min. Est. completion ~10:04 UTC.

**lending-indices 021507 — 2022-06-19 @ 09:14 UTC: 9,518 records:** POLYGON=5108, AVALANCHE=3127, ARBITRUM=1283.
`aave_v3_ETHEREUM=0` — **95 days post-genesis**. Confirmed gap. ManifestWriter: 81 total entries (growing). Rate: 2.38
min/date; ~1,469 dates remaining ≈ 58 hrs. Disk: 1.9G.

### 08:45 UTC check — DRIFT 2025-01-13 45%; lending-indices 2022-06-06; AAVE-ETH 82d gap (2026-06-28 08:45 UTC)

**VM roster (08:34 UTC watchdog + direct 08:45 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-13:** HTTP 502 at batch 4,120 (08:27 UTC, `continue`). At 08:45: ~5,574/12,157 batches (45%). Rate: ~80
batches/min. Est. completion ~10:07 UTC (~82 min remaining). VM healthy.

**lending-indices 021507 — 2022-06-06 @ 08:43 UTC: 14,193 records:** POLYGON=9388, AVALANCHE=3199, ARBITRUM=1606.
`aave_v3_ETHEREUM=0` — **82 days post-genesis** (2022-03-16). Definitively confirmed data gap: either IS-derived genesis
for ETH V3 markets is much later, or subgraph returns 0. Will surface as `attempted_failed[UPSTREAM_SUBGRAPH_ZERO]` in
G2 gate. Rate: 2.38 min/date; ~1,482 dates left ≈ 59 hrs. Disk: 2.0G stable.

### 08:13 UTC check — DRIFT 2025-01-13 24%; lending-indices AAVE-ETH zero confirmed; disk 2G (2026-06-28 08:13 UTC)

**VM roster (08:04 UTC watchdog + direct 08:13 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-13:** 37 min elapsed since 07:36 start, ~24% done (~2,923/12,157 batches). No 502s visible yet. Est.
completion ~10:10 UTC. Operator decision on stall still pending.

**lending-indices 021507 — 2022-05-24 @ 08:12 UTC: 4,969 records:** POLYGON=2395, AVALANCHE=1645, ARBITRUM=929.
**`aave_v3_ETHEREUM=0` — NOW 69 DAYS POST-GENESIS (2022-03-16).** Upgraded from "flag" to **confirmed data gap** for G2
investigation. Likely cause: IS-derived genesis for ETH AAVE V3 markets is much later than 2022-03-16, OR subgraph
returning 0 rows. Rate: 2.33 min/date; ~1,495 dates remaining ≈ 58 hrs.

**Disk:** 2.0G free — stable (recovered post git-pack from 287MB critical earlier).

### 07:40 UTC check — DRIFT 2025-01-12 DONE/2025-01-13 started; disk 287MB CRITICAL (2026-06-28 07:40 UTC)

**VM roster (07:34 UTC watchdog + direct 07:40 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-12 COMPLETED at 07:36 UTC:** 722,084 rows, 92 min. Trend: 147→122→97→92 min. **DRIFT 2025-01-13 started
07:36 UTC: 1,215,691 sigs** — SPIKE (up from 722k). 12,157 batches @ 79/min = ~154 min. Est. completion ~10:10 UTC.
Validates orchestrator stall concern: volumes NOT monotonically decreasing.

**lending-indices 021507 — 2022-05-09 @ 07:37 UTC: 14,349 records:** POLYGON=6160, AVALANCHE=4365, ARBITRUM=3824.
`aave_v3_ETHEREUM=0` persisting (7.5 weeks post-genesis 2022-03-16). Increasing concern for G2 — may be subgraph data
gap or later IS-derived genesis. Rate: 2.33 min/date.

**⚠️ DISK CRITICAL: 287MB free** (was 779MB at 07:08 — lost 492MB in 32 min from other-slot git fetches). ms-playwright
cache=1.9G, per-tab PM repos=1.4-1.5G each. Cannot clear safely without operator. Monitor closely.

### 09:02 UTC check — CeFi 18 running / TradFi 93.97% / DRIFT 2025-01-13 ~154min ETA (2026-06-28 09:02 UTC)

**VM roster:** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-13:** ETA ~10:10 UTC (12,157 batches, confirmed from 07:40 analysis). 1,215,691 sigs spike vs 722k on
2025-01-12.

**TradFi:** 714,985 captured (93.97%), ~45 VMs running, +1,133 since prior check. **CeFi:** 18/24 wave-1 running (6
completed). Disk 745MB — launcher fix still BLOCKED-DISK. Confirmed disk pattern: other-slot git fetches draining space.
Disk at 745MB at time of this check.

### 07:08 UTC check — DRIFT 2025-01-12 ~70%; lending-indices 2022-04-26; disk 779MB (2026-06-28 07:08 UTC)

**VM roster (07:04 UTC watchdog + direct 07:08 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-12:** Log silent since 06:27 (batch 1,804) — expected (success = no log). At 07:08: estimated batch
~5,043/7,223 (70%). Est. completion ~07:35 UTC. VM RUNNING confirmed.

**lending-indices 021507:** At 2022-04-26 @ 07:06 UTC (2.33 min/date). Still processing compound_v3 venues (all 0 rows —
pre-genesis for Compound V3 chains, expected). AAVE V3 multi-chain data continuing.

**Disk:** 779MB free (down 71MB from 850MB at 06:34; normal git ops). Monitoring for further pressure.

### 06:34 UTC check — DRIFT 2025-01-11 DONE/2025-01-12 33%; lending-indices 2022-04-11; DISK FULL (2026-06-28 06:34 UTC)

**VM roster (06:03+06:33 UTC watchdog + direct 06:34 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-11 COMPLETED at 06:04 UTC:** 760,205 rows, 97 min. Per-date trend: 147→122→97 min (declining volumes).
**DRIFT 2025-01-12 in progress (started 06:04 UTC):** 722,284 sigs, 7,223 batches. 2× HTTP 502 at batch 1332/1804. At
06:34: ~2,370 done (33%). Est. completion ~07:35 UTC. Stall flag pending operator decision; slot-11 monitoring only.

**lending-indices 021507 — 2022-04-11 @ 06:31 UTC: 4,320 records:**
`aave_v3_POLYGON=3746, aave_v3_AVALANCHE=378, aave_v3_ARBITRUM=196`. `aave_v3_ETHEREUM=0` at 2022-04-11 (26 days past
genesis 2022-03-16) — may be later IS-derived genesis or subgraph data gap. Flag for G2 gate investigation. Rate: 2.56
min/date; ~1,641 dates remaining ≈ 70 hrs.

**DISK ALERT (06:34 UTC):** Host disk hit 100% (290G). Freed ~850MB by deleting stale /tmp/_.parquet files (avail_idx_,
avail_tradfi, cefi_cat, lending_idx, tmp\* — all 3+ hrs old). ENOSPC caused one plan-file truncation (recovered from git
@ 5109aa084). Current free: 850MB — sufficient for ongoing work but monitoring.

### 06:01 UTC check — DRIFT 2025-01-11 ~89%; lending-indices 2022-03-28; STALL flag noted (2026-06-28 06:01 UTC)

**VM roster (05:33 UTC watchdog + 06:01 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-11:** At batch 6,832/7,607 (89%) @ 05:54 UTC. 5× HTTP 502 (all `continue`). Completion est. ~06:04 UTC.
NOTE: Orchestrator flagged 🔴 PERFORMANCE STALL at 05:37 UTC (527-day range @ 2-3h/date → 44+ days). OPERATOR DECISION
REQUIRED (options A/B/C in banner). Slot-11 monitoring only; not taking autonomous action. Observed per-date trend:
2025-01-09=147min, 2025-01-10=122min, 2025-01-11=~97min (declining sig volumes may shorten later dates).

**lending-indices 021507 — 2022-03-28 @ 05:59 UTC: 1,910 records:**
`aave_v3_POLYGON=1508, aave_v3_AVALANCHE=230, aave_v3_ARBITRUM=172` — data flowing. Ethereum 0 rows at genesis boundary
(expected: sparse near genesis). VM stable.

### 06:01 UTC check — DRIFT 2025-01-11 imminently done; lending-indices 2022-03-28 (2026-06-28 06:01 UTC)

**VM roster (05:33 UTC watchdog + 06:01 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-11:** 5× HTTP 502 (batches 197, 3765, 5943, 6797, 6832 — all `continue`). At 05:54 UTC: batch
6,832/7,607 (89%). Remaining ~775 batches @ 79/min = ~10 min. Completion est. ~06:04 UTC.

**lending-indices 021507 — 2022-03-28 @ 05:59 UTC: 1,910 records:**
`aave_v3_POLYGON=1508, aave_v3_AVALANCHE=230, aave_v3_ARBITRUM=172` — multi-chain AAVE V3 data flowing well.
`aave_v3_ETHEREUM=0` (some dates near genesis show 0, expected per rate-update sparsity). ManifestWriter: 39 total
entries.

### 05:29 UTC check — FIRST REAL lending-indices ROWS; DRIFT 2025-01-11 63% (2026-06-28 05:29 UTC)

**VM roster (05:03 UTC watchdog + 05:29 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**lending-indices 021507 — FIRST NON-ZERO ROWS at 2022-03-14 @ 05:27 UTC:** 57 total records:
`aave_v3_ARBITRUM=20, aave_v3_OPTIMISM=14, aave_v3_POLYGON=5, aave_v3_AVALANCHE=18`. Ethereum AAVE V3 still pre-genesis
(genesis ~2022-03-16, ~2 more dates). ManifestWriter: 63 total entries. Milestone: lending data pipeline confirmed
working on n2-highmem-4 32GB VM.

**DRIFT 2025-01-11:** HTTP 502s at batch 197 (04:30) and batch 3,765 (05:15) — both `continue`, expected. Rate: 79
batches/min. Progress at 05:29: ~4,800/7,607 batches (~63%). Est. completion ~06:04 UTC.

### 04:57 UTC check — DRIFT 2025-01-10 COMPLETE, now 2025-01-11; lending-indices 2022-03-02 (2026-06-28 04:57 UTC)

**VM roster (04:33 UTC watchdog + 04:57 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-10 COMPLETED at 04:27 UTC:** 967,979 rows → `drift_helius_SOL-PERP_20250110.parquet`. Duration: 122 min.
**DRIFT 2025-01-11 in progress (started 04:27 UTC):** 760,705 sigs (cache hit: "0 prefixes {}"), 7,607 batches @
~79/min. Expected completion: ~06:03 UTC. One HTTP 502 at batch 197 (04:30 UTC, `continue`, expected).

**lending-indices 021507:** At 2022-03-02 @ 04:55 UTC (was 2022-02-18 at 04:24 → 12 dates in 31 min = 2.58 min/date).
AAVE V3 Ethereum genesis ~2022-03-16: ~14 more pre-genesis dates × 2.58 min = ~36 min. First real rows ~05:33 UTC.

### 04:25 UTC check — 6/6 RUNNING, DRIFT ~98% on 2025-01-10, lending-indices 2022-02-18 (2026-06-28 04:25 UTC)

**VM roster (04:03 UTC watchdog + 04:25 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-10 status:** Log frozen at batch 6,583/9,681 (03:48 UTC) — expected behaviour (silent on success). At
~79 batches/min, remaining ~3,098 batches complete by ~04:28 UTC. VM is RUNNING and healthy.

**lending-indices 021507:** At 2022-02-18 @ 04:24 UTC (was 2022-02-06 at 03:52 → 12 dates in 32 min = 2.67 min/date).
AAVE V3 Ethereum genesis ~2022-03-16: ~26 more pre-genesis dates × 2.67 min = ~69 min. First real rows ~05:33 UTC.

### 03:53 UTC check — 6/6 RUNNING, DRIFT 68%, lending-indices stable (2026-06-28 03:53 UTC)

**VM roster (03:33 UTC watchdog + 03:53 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-10 progress:** Batch 6,583/9,681 @ 03:48 UTC (68% complete). One HTTP 502 (batch=6583, `continue` — no
retry loop, expected). Rate: 6,583 batches in 83 min = ~79/min. Remaining: ~3,098 batches. Expected completion: ~04:27
UTC.

**lending-indices 021507 progress:** At 2022-02-06 @ 03:52 UTC (was 2022-01-24 at 03:18 → 13 dates in 34 min = 2.6
min/date). Pre-AAVE V3 Ethereum genesis (~2022-03-16): ~38 more pre-genesis dates × 2.6 min = ~99 min. First real rows
expected ~05:35 UTC. Stable — no OOM, no crash. Base chain genesis correctly detected (block=1 mapping to 2023-06-15 →
pre-genesis for 2022-02-06).

### G2 verification run #1 — GATE FAILS (VMs still running) (2026-06-29 07:34 UTC)

**VM roster (07:32 UTC):** 5/6 G1 VMs still RUNNING (1 pyth-archive TERMINATED 2026-06-28 00:52 UTC):

| VM                                     | STATUS                                                  |
| -------------------------------------- | ------------------------------------------------------- |
| `mtds-dex-pools-backfill`              | RUNNING 34.180.72.4 (dex_pool_state)                    |
| `mtds-dex-swaps-backfill`              | RUNNING 136.110.123.43 (dex_pool_swaps)                 |
| `mtds-lending-indices-20260628-021507` | RUNNING 34.180.65.195 (lending_indices, ON-DEMAND 32GB) |
| `mtds-lst-rates-20260628-002136`       | RUNNING 34.104.175.119 (lst_rates)                      |
| `mtds-perp-funding-backfill`           | RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)        |
| `mtds-solana-drift-backfill`           | RUNNING 136.110.117.136 (perp_funding/DRIFT)            |

**Coverage measurement** (`python scripts/measure_honest_coverage.py --asset-group defi`, 07:34 UTC): Manifest:
`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (10,782,809 rows, updated
07:33 UTC). Overall: **57.95%** (2,519,678 / 4,347,816 reachable)

| data_type       | coverage | captured  | attempted_failed | expected_unattempted | gate |
| --------------- | -------- | --------- | ---------------- | -------------------- | ---- |
| dex_pool_state  | 80.29%   | 1,527,721 | 783              | 374,350              | FAIL |
| dex_pool_swaps  | 30.40%   | 315,988   | 20,638           | 702,882              | FAIL |
| lst_rates       | 85.65%   | 14,979    | 847              | 1,662                | FAIL |
| lending_indices | 40.83%   | 52,126    | 30               | 75,525               | FAIL |
| perp_funding    | 31.89%   | 442       | 179              | 765                  | FAIL |
| oracle_prices   | 84.77%   | 18,147    | 873              | 2,387                | FAIL |

**G2 GATE STATUS: FAIL** — all 6 data_types have non-zero attempted_failed or expected_unattempted. Root cause: VMs are
still processing — coverage is improving vs G0.2 baseline (dex_pool_state 58.62%→80.29%, lending_indices 29.67%→40.83%,
perp_funding 37.19%→31.89%\* [perp_funding denominator grew post-phantom apply]).

**Phantom reconcile dry-run:** Failed with `ChunkedEncodingError` (GCS network error downloading 10.7M-row index
parquet). Prior apply completed 2026-06-28T21:35Z (219,632 phantoms flipped). Re-run after all VMs complete.

**Hygiene audit:** Timed out at 180s (manifest_divergence check on 10.7M-row index is slow). Run after VMs complete.

**ETA to re-verify:** lending-indices ~2026-06-30 22:00 UTC; lst-rates ~2026-07-01 00:00 UTC (the two slowest VMs).
Re-dispatch G2 verification after ~2026-07-01 00:00 UTC when all VMs are TERMINATED.

### G1.5 DRIFT perp_funding backfill — picked up + partially resolved, real blocker confirmed (2026-07-11)

Slot 3 (data_engineering) picked up the reopened todo. Live manifest no longer matches the plan's "424 cells" framing:
`captured=8`, `attempted_failed=39` (stale), `expected_unattempted=51,301` across 41 `instrument_id`s. Found + fixed a
second, independent bug causing most of that inflation: DRIFT SPOT markets (e.g. `DRIFT-SOLANA:SPOT:BSOL`) were wrongly
expecting `perp_funding` (SPOT instruments cannot have a funding rate) due to a capability-declaration leak in
`unified-api-contracts` (`_defi.py`'s `drift` entry bundles `PERPETUAL`+`SPOT_PAIR` with one shared `data_types` list).
Fixed via `VALID_DATA_TYPES_VENUE_EXCLUSIONS` — shipped `unified-api-contracts@b7cf3106` + 4 regression tests.

**The actual DRIFT-perp backfill remains blocked** — confirmed real, not a code issue: the consolidated
`_index/drift_v2_sig_index.parquet` still doesn't exist; existing parts cover 2025-12-23→2026-05-29 (Builder #1) and
2024-10-31→2025-01-15 (Builder #2), leaving an **~11-month unindexed gap**. Drift's S3 historical archive only covers
pre-2025-01-08 (V1→V2 migration); past that, closing the gap requires walking Solana signatures via Helius RPC — the
same rate-limit path that hit the 429-burst wall documented above. This is a genuine Helius API plan/throughput ceiling
(the builder already retries with backoff), not something fixable in code. Filed operator decision as todo 3 in
`plans/active/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md` (Helius plan upgrade vs. more parallel-
walker VMs vs. accept the gap) and posted `/blocked` on AO item `mvp_backfill_defi_onchain_v10-010` rather than
launching another VM that would likely re-hit the same ceiling without an operator call on cost/approach first.

### 2026-07-12 (later) — 3rd re-dispatch to slot 3; re-confirmed unchanged, re-filed /blocked (BLK-40ea7a68)

Re-dispatched to slot 3 again (same day as slot 4's 2026-07-12 re-confirmation above). Live-checked
`_index/drift_v2_sig_index.parquet` directly via GCS blob existence — still does not exist; both part-sets (`_parts/`
6,293 files, `_parts_b/` 876 files) still unconsolidated; the ~11-month gap (2025-01-15 → 2025-12-23) is unchanged. No
operator ruling has landed on `plans/active/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md` todo 3
("Decide the DRIFT V2 sig-index Helius throughput path: (a) Helius plan upgrade, (b) more parallel-walker VMs, (c)
accept the gap"). Re-filed `/blocked` (`BLK-40ea7a68`, recommendation: (b) more parallel-walker VMs) rather than
re-running the full investigation a 3rd time — nothing has changed since 2026-07-11/2026-07-12 that a fresh
investigation would surface. **Flagging the pattern**: this AO item has now boomeranged back into the queue 3× in ~36h
without an operator answer reaching the blocked-question queue; if this repeats, the dispatcher may need
`prereqs.conditions` gating on this task until the operator ruling lands, rather than continued re-dispatch.

### 2026-07-12 (slot 7) — 4th re-dispatch; re-verified byte-identical state; applied the recurring-redispatch mitigation

Slot 7 (data_engineering) picked up `mvp_backfill_defi_onchain_v10-001` (the reopened G1.5 todo). Cheaply re-verified
live state before touching anything: `google.cloud.storage` `blob.exists()` against
`gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index.parquet` — still **False**;
`_index/drift_v2_sig_index_parts/` = 6,293 objects, `_index/drift_v2_sig_index_parts_b/` = 876 objects, both unchanged;
availability-manifest DRIFT `perp_funding` capture_status distribution — `expected_unattempted=51,301`,
`empty_confirmed=19,096`, `attempted_failed=39`, `captured=8` — byte-identical to the 2026-07-12 slot-4 finding. Zero
state drift across 3 consecutive prior dispatches; confirmed nothing new to fix in code and no value in re-running the
investigation a 4th time.

**Mitigation applied** (the fix flagged as needed above): rather than re-filing an identical `/blocked` that a 5th slot
would just re-confirm again, created the gating condition `drift_perp_funding_helius_throughput_ruled=false` via
`POST /api/prerequisites/` and filed `/blocked` (`BLK-fc4ab4e6`, recommendation: Option B — launch more parallel-walker
VM segments) with an explicit ask for main/operator to attach
`prereqs.conditions: [drift_perp_funding_helius_throughput_ruled]` to this backlog task (`data/config/backlog.yaml` +
`POST /api/backlog/reload`) — that attachment step edits the orchestrator's live root-clone config, outside a
worker-slot's scope, so it's left for main/operator per RULES.md §4. Then called `/skip-current-task` so slot 7 stops
re-grabbing this exact dead-end (other slots remain eligible until the condition flips or the backlog task is gated).
**Still genuinely blocked on the same operator ruling** (todo 3 in
`defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`) — no code or plan-of-record change was possible beyond this
Progress Log entry.

### 2026-07-12 (slot 9) — 5th consecutive re-dispatch; unchanged; flagged the stalled gate-attachment to main via chat

Slot 9 (data_engineering) picked up `mvp_backfill_defi_onchain_v10-001` again. Cheap re-verification before touching
anything: `google.cloud.storage` `blob.exists()` against
`gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index.parquet` — still **False**; both
`_index/drift_v2_sig_index_parts/` (6,293 objects) and `_index/drift_v2_sig_index_parts_b/` (876 objects) still present
and unconsolidated. `GET /api/state` confirms the condition slot 7 created,
`drift_perp_funding_helius_throughput_ruled`, is still `value=false, gates_queued=0` — i.e. never attached to this
backlog task's `prereqs.conditions`, so the dispatcher keeps offering it to any free slot. 4 unanswered `/blocked`
questions already sit in the queue for this exact task (`BLK-ab48a164`, `BLK-a851a348`, `BLK-40ea7a68`, `BLK-fc4ab4e6`)
— filing a 5th identical one adds no new information, so skipped that step. Instead posted a direct chat message to the
`main` role (`POST /api/agents/by-role/main/message`) naming the specific stuck mitigation (attach
`prereqs.conditions: [drift_perp_funding_helius_throughput_ruled]` to this task in `backlog.yaml` +
`POST /api/backlog/reload`, or rule directly on todo 3 in `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`) so
the redispatch churn stops. Calling `/skip-current-task` next — no code or plan-of-record change is possible from a
worker slot beyond this Progress Log entry and the escalation.

### 2026-07-12 (slot 2) — 6th consecutive re-dispatch; unchanged; skip without re-investigating

Slot 2 (data_engineering) picked up `mvp_backfill_defi_onchain_v10-001` immediately after `/done`-ing an unrelated cefi
G4 task. Cheap re-verification only:
`gsutil stat gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index.parquet` still returns "No
URLs matched" (does not exist); `/api/backlog?limit=500` shows this task `status=dispatched, prereqs=None` — the
`drift_perp_funding_helius_throughput_ruled` condition slot 7 created is still not attached, and `/api/state` no longer
even lists that condition key (may have been lost on a server restart, or the state query used here surfaces it
differently — not chased further, since the underlying blocker is unchanged either way). No operator ruling has landed
on todo 3 of `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`. Per the established pattern from the 3 prior
identical dispatches (slots 3/7/9), NOT re-running the investigation or filing a 6th duplicate `/blocked` — calling
`/skip-current-task` so another slot's cycles aren't spent on a byte-identical confirmation either. This item needs the
operator's ruling (or the `prereqs.conditions` backlog attachment) to actually move.

### G2 verification run #2 — GATE FAILS, new Solana dex-pool gap found (2026-07-12 03:48 UTC, slot 3)

Picked up `mvp_backfill_defi_onchain_v10-002` (the G2 final-verification todo). Fresh-pulled all repos, confirmed VM
roster via `gcloud compute instances list --filter="name~mtds"` (using the working `~/google-cloud-sdk/bin/gcloud` — the
snap `gcloud` is broken in this sandbox: `snap-confine ... cap_dac_override not found`):

| VM                                                  | STATUS                                                                                                                                                                                          |
| --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mtds-dex-swaps-backfill`                           | RUNNING — actively writing (day=2024-11-21 of 2023-01-01→2026-06-27 range at 03:33 UTC; real progress, not stalled)                                                                             |
| `mtds-perp-funding-backfill`                        | RUNNING — processing 2026-06-05 (near "today", i.e. in daily forward-catchup phase of its 2023-11-01→today window)                                                                              |
| `mtds-dex-pools-backfill`                           | ✅ COMPLETED exit_code=0 (2026-06-29 14:07 UTC)                                                                                                                                                 |
| `mtds-lending-indices-*` (latest `20260701-022550`) | ✅ COMPLETED exit_code=0 (2026-07-01 02:29 UTC)                                                                                                                                                 |
| `mtds-lst-rates-*` (latest `20260630-003055`)       | ✅ COMPLETED exit_code=0 (2026-06-30 00:34 UTC)                                                                                                                                                 |
| `mtds-pyth-archive-*`                               | ✅ COMPLETED (2026-06-28, prior run)                                                                                                                                                            |
| `mtds-solana-drift-backfill`                        | gone — terminated mid-run (no EXIT_STATUS; last log lines are HTTP 429 spam on 2025-12-23→2026-03-06 batch resolve) — this is the already-tracked, condition-gated DRIFT blocker above, not new |

**Pre-check finding (caveat on all numbers below):** the DEFI bucket's manifest consolidator
(`uts-prod-manifest-consolidator-market-data-defi`) is **~30h stale** — `_index/availability_index.parquet`
`Update time = 2026-07-10T21:42:30Z` vs now 2026-07-12T03:37Z, exceeding `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400s`
(confirmed both from `gsutil stat` and from the still-running VMs' own `ManifestConsolidatorStaleError` log spam). This
is a **pre-existing, already-tracked, actively-being-worked issue**
(`plans/active/issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`, updated today) — root cause
(code-verified by a sub-agent): scheduler-triggered consolidator executions get SIGKILLed mid-merge, which bypasses the
`finally:`-block lock release (`unified_trading_library/manifest_consolidator.py:692-694`), so subsequent ticks take the
fresh-lock fast-skip path (`:416-432`) which reports `success=True` **without** calling `_touch_canonical_mtime`
(`:885-958`) — explaining "executions succeed every ~1min but the blob mtime never moves." A partial fix already landed
(lock TTL 90s→300s) but a residual kill source is still open. Not re-filing — already tracked. **Net effect on this
verification**: the consolidated index used below reflects state as of ~2026-07-10T21:42Z, undercounting ~30h of the two
still-running VMs' progress (per-VM shards ARE current; only the merged view is behind).

**Coverage measurement** (`python scripts/measure_honest_coverage.py --asset-group defi`, 03:48 UTC, 27,446,015-row
primary manifest merged with 594-row secondary → 24,698,596 deduped rows). Layer-1 completeness 86.2% (12 UAC-expected
tuples missing from the writer side, 171 stray writer tuples UAC doesn't sanction — pre-existing definitional gap, not
re-investigated here). Aggregated across all venues per MVP data_type:

| data_type       | captured  | attempted_failed | expected_unattempted | gate |
| --------------- | --------- | ---------------- | -------------------- | ---- |
| dex_pool_state  | 1,560,561 | 770              | 1,814,837            | FAIL |
| dex_pool_swaps  | 639,489   | 21,122           | 3,883,609            | FAIL |
| lst_rates       | 14,979    | 851              | 11,993               | FAIL |
| lending_indices | 120,885   | 54               | 569,084              | FAIL |
| perp_funding    | 2,538     | 214              | 76,873               | FAIL |
| oracle_prices   | 18,147    | 873              | 200,179              | FAIL |

**G2 GATE STATUS: FAIL (checkbox NOT flipped)** — all 6 data_types still have non-zero attempted_failed and/or
expected_unattempted. Two of six backfill VMs are still actively in-flight (dex_pool_swaps ~mid-range; perp_funding
near-caught-up), so the gate cannot pass yet on that basis alone. Root-cause breakdown of the `expected_unattempted`
mass, cross-checked against existing issue docs (via a research sub-agent, to avoid duplicate filing):

- **ORCA / RAYDIUM / KAMINO (dex_pool_state + dex_pool_swaps), captured=0 despite real code + in-scope MVP declaration —
  NEW finding, filed as G1.6 above.** The original G1 dex-pools/dex-swaps VMs explicitly skipped these 3 Solana venues
  and no follow-up VM (analogous to the DRIFT one) was ever launched.
- **UNISWAP_V2 / UNISWAP_V4 / TRADER_JOE_V2 / VELODROME_V2** — already tracked, open, P2:
  `defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md` (zero forward-capture code; awaiting operator scope
  confirmation). TRADER_JOE_V2 + VELODROME_V2 show `captured=0` in today's numbers, consistent with that doc.
- **DRIFT perp_funding** — already tracked + condition-gated (`drift_perp_funding_helius_throughput_ruled=false`), see
  the two Progress Log entries directly above. Not re-investigated.
- **FLUID lending_indices** — already tracked, open, P0: `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`
  (adapter's revert-data guard never fires; 100% broken in practice).
- **MORPHO lending_indices, captured=0** — a prior issue doc
  (`defi_lending_atoken_debttoken_instrument_split_ 2026_07_07.md`) reported 465 real captured rows as of 2026-07-07,
  which conflicts with today's captured=0 reading. Flagging as a loose thread (manifest-recording gap vs. genuine
  regression) — **not yet root-caused**, needs a follow-up check before it's actioned.
- **LIGHTER / EXTENDED (perp_funding / oracle_prices)** — correctly CeFi per v10 decision #4 (not a defi MVP gap); their
  own real capture bugs are already tracked in `non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`.

**Not re-run this dispatch** (deferred — VMs still in-flight so a full hygiene/phantom pass would be premature and
expensive against the stale consolidator): `manifest_hygiene_daily.py --mode full`,
`reconcile_phantom_manifest_rows_all.py --dry-run`. Re-run once dex_pool_swaps + perp_funding VMs terminate and the
consolidator issue above is resolved (or at least caught up).

**Next re-dispatch should**: (1) check dex_pool_swaps/perp_funding VM completion, (2) check whether G1.6 (Solana
dex-pool backfill VM) has been launched, (3) re-run `measure_honest_coverage.py`, (4) quick-verify the MORPHO
discrepancy, before attempting the full G2 gate again.

### 2026-07-12 (slot 12) — 7th consecutive re-dispatch of `mvp_backfill_defi_onchain_v10-001`; unchanged; skip

Slot 12 (data_engineering) picked up the reopened DRIFT todo again. Cheap re-verification only (python
`google.cloud.storage` `blob.exists()`): `_index/drift_v2_sig_index.parquet` still absent;
`_index/drift_v2_sig_index_parts/` = 6,293 objects, `_index/drift_v2_sig_index_parts_b/` = 876 objects — both
byte-identical to slots 3/7/9/2's prior findings. `GET /api/backlog` confirms this task's `prereqs` is still `null` —
the `drift_perp_funding_helius_throughput_ruled` condition (created by slot 7) was never attached in
`data/config/backlog.yaml` (that file lives only in the root `agent-orchestrator` clone, not this slot's worktree —
confirmed out of a worker's edit scope, matching slot 7's original call). No operator ruling on todo 3 of
`defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`. 5 unanswered `/blocked` questions already queued for this
task (`BLK-ab48a164`, `BLK-a851a348`, `BLK-40ea7a68`, `BLK-fc4ab4e6`, plus slot 9's direct chat to `main`) — not filing
a 6th duplicate. Calling `/skip-current-task`; no code or plan-of-record change possible from a worker slot beyond this
entry.

### 2026-07-12 (slot 11) — 8th consecutive re-dispatch of `mvp_backfill_defi_onchain_v10-001`; unchanged; skip

Slot 11 (data_engineering) picked up the reopened DRIFT todo again. Cheap re-verification only (python
`google.cloud.storage` `blob.exists()` against `instruments-service/.venv`):
`gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index.parquet` still does not exist;
`_index/drift_v2_sig_index_parts/` and `_index/drift_v2_sig_index_parts_b/` both still present, unconsolidated —
byte-identical to every prior dispatch back to 2026-07-11. `GET /api/backlog?limit=500` confirms this task still carries
no `prereqs` field at all — the `drift_perp_funding_helius_throughput_ruled` condition slot 7 created was never attached
(`data/config/backlog.yaml` lives only in the root `agent-orchestrator` clone, outside every worker slot's worktree —
same out-of-scope finding as slots 7/12). No operator ruling has landed on todo 3 of
`defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`. 5+ unanswered `/blocked` questions already queued for this
exact task plus slot 9's direct chat escalation to `main` — not filing a 6th/7th duplicate. Calling
`/skip-current-task`; no code or plan-of-record change is possible from a worker slot beyond this entry. The
recurring-redispatch pattern (8 slots now) confirms the mitigation slot 7 proposed — attach
`prereqs.conditions: [drift_perp_funding_helius_throughput_ruled]` to this backlog task, or rule directly on todo 3 —
still has not been actioned by main/operator.

### 2026-07-12 (slot 10) — 9th consecutive re-dispatch of `mvp_backfill_defi_onchain_v10-001`; unchanged; skip

Slot 10 (data_engineering) picked this up immediately after shipping G1.6 (Solana dex-pool VM). Cheap re-verification
only (python `google.cloud.storage`, `market-tick-data-service/.venv`): `_index/drift_v2_sig_index.parquet` still
absent; `_index/drift_v2_sig_index_parts/` = 6,293 objects, `_index/drift_v2_sig_index_parts_b/` = 876 objects —
byte-identical to every dispatch back to 2026-07-11. `GET /api/backlog?limit=500` confirms this task still carries no
`prereqs` field. No operator ruling on todo 3 of `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`. 5+
unanswered `/blocked` questions + a direct chat escalation to `main` already queued — not filing a duplicate. Calling
`/skip-current-task`; no code or plan-of-record change is possible from a worker slot beyond this entry (9 slots now
confirm the same blocker — this needs the operator ruling or the `prereqs.conditions` attachment in
`agent-orchestrator`'s `backlog.yaml`, both outside worker-slot scope).

### 2026-07-12 (slot 6) — 10th consecutive re-dispatch of `mvp_backfill_defi_onchain_v10-001`; unchanged; skip

Slot 6 (data_engineering) picked this up on boot. Cheap re-verification only, matching the prior 9 slots' method:
`GET /api/backlog?limit=500` — task still carries no `prereqs` field (`target_slot: 10, affinity: medium`, no
`conditions`). Direct GCS check (`google.cloud.storage`, `market-tick-data-service/.venv`):
`_index/drift_v2_sig_index.parquet` (consolidated) still absent; `_index/drift_v2_sig_index_parts/` = 6,293 objects,
`_index/drift_v2_sig_index_parts_b/` = 876 objects. Manifest capture_status distribution for DRIFT `perp_funding`
(direct parquet filter on `availability_index.parquet` via `instruments-service/.venv`): `expected_unattempted=51,301`,
`empty_confirmed=19,096`, `attempted_failed=39`, `captured=8` — byte-identical to every dispatch back to 2026-07-11. No
operator ruling has landed on todo 3 of `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`, and the
`drift_perp_funding_helius_throughput_ruled` condition slot 7 created remains unattached to this backlog task. 5+
unanswered `/blocked` questions + a direct chat escalation to `main` already queued — not filing an 11th duplicate.
Calling `/skip-current-task`; no code or plan-of-record change is possible from a worker slot beyond this entry (10
slots now confirm the identical blocker — this needs either the operator ruling on todo 3, or the
`prereqs.conditions: [drift_perp_funding_helius_throughput_ruled]` attachment in agent-orchestrator's `backlog.yaml`,
both outside worker-slot scope).

### 2026-07-12 (slot 9, 2nd session) — 11th consecutive re-dispatch of `mvp_backfill_defi_onchain_v10-001`; unchanged; skip

Slot 9 (data_engineering) picked this up again after an idle period. Cheap re-verification only, matching the prior 10
slots' method: `GET /api/backlog?limit=500` — task still carries no `prereqs` field (`target_slot: 10, affinity: none`).
`GET /api/state` confirms `prerequisites.drift_perp_funding_helius_throughput_ruled` =
`{value: False, set_by: slot7-data_engineering, gates_queued: 0}` — the condition slot 7 created 2026-07-12T03:34:55Z is
still unattached to this backlog task (`gates_queued=0`). No local venv was provisioned in this slot for either
`market-tick-data-service` or `instruments-service`, so skipped the direct-GCS-parquet re-check this time (10 prior
slots already confirmed `_index/drift_v2_sig_index.parquet` absent + the manifest distribution byte-identical back to
2026-07-11; provisioning a venv purely to re-confirm an unchanged dead end adds no signal). No operator ruling has
landed on todo 3 of `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`. 5+ unanswered `/blocked` questions + slot
9's own prior direct chat escalation to `main` already queued — not filing a 6th/7th/11th duplicate. Calling
`/skip-current-task`; no code or plan-of-record change is possible from a worker slot beyond this entry (11 slots now
confirm the identical blocker — this needs either the operator ruling on todo 3, or the
`prereqs.conditions: [drift_perp_funding_helius_throughput_ruled]` attachment in agent-orchestrator's `backlog.yaml`,
both outside worker-slot scope).

> **This is a historical operational log, not this file's own live todo list — Part 2 of 3.** This file is the
> chronological CONTINUATION of `plans/active/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md` (Part 1),
> picking up at the 2026-07-12 "12th consecutive re-dispatch" entry and running through the 2026-07-14T22:15Z "cycle 11
> — INCIDENT" entry. It continues in `plans/active/mvp_backfill_defi_onchain_v10_operational_log_part3_2026_07_24.md`
> (Part 3). Every line below is preserved VERBATIM from where it previously lived in Part 1 before this 2026-07-24 chunk
> split — nothing about what was done or what remains open has changed. **The parent plan
> (`mvp_backfill_defi_onchain_v10_2026_06_27.md`) remains the sole SSOT for current todo/gate state.** This file exists
> purely to bring the operational log back under the plan-hygiene line cap. No checkboxes fall within this part's range
> (all 7 pre-existing G1.5 sub-history checkboxes live earlier, in Part 1).

### 2026-07-12 (slot 11, 2nd session) — 12th consecutive re-dispatch of `mvp_backfill_defi_onchain_v10-001`; unchanged; skip

Slot 11 (data_engineering) picked this up again on `/boot`. Matching slot 9's 2nd-session reasoning: `GET /api/state`
confirms `prerequisites.drift_perp_funding_helius_throughput_ruled` is still `{value: False, gates_queued: 0}` (created
by slot 7 2026-07-12T03:34:55Z, never attached); `GET /api/backlog` confirms this task still carries no `prereqs` field.
Not re-running the GCS/manifest re-check — 11 prior dispatches (back to 2026-07-11) already confirmed
`_index/drift_v2_sig_index.parquet` absent and the DRIFT `perp_funding` capture_status distribution byte-identical;
re-provisioning a venv to re-confirm an unchanged dead end adds no signal. No operator ruling has landed on todo 3 of
`defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`. 5+ unanswered `/blocked` questions + slot 9's direct chat
escalation to `main` already queued — not filing a 13th duplicate. Calling `/skip-current-task`; the blocker is
unchanged and entirely outside worker-slot scope (needs either the operator ruling or the
`prereqs.conditions: [drift_perp_funding_helius_throughput_ruled]` attachment in agent-orchestrator's `backlog.yaml`).

### G2 verification run #3 — found + fixed a stalled VM, found a NEW capture gap (MORPHO), gate still FAILS (2026-07-12 09:33-09:50 UTC, slot 3, resumed session)

Resumed `mvp_backfill_defi_onchain_v10-002` (the same G2 task from run #2 earlier today — same slot). Fresh-pulled all
repos clean. Worked the "Next re-dispatch should" list from run #2:

**1) VM roster re-check** (`gcloud compute instances list --filter="name~mtds"`, zone `asia-northeast1-c`):

| VM                           | Status at 09:33 UTC                                                                                                                                                                                                                                                                                                              |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mtds-dex-swaps-backfill`    | RUNNING, actively writing — day=2024-11-28→2024-11-29 (real forward progress, not stalled)                                                                                                                                                                                                                                       |
| `mtds-perp-funding-backfill` | RUNNING per `gcloud`, but **STALLED** — see finding below                                                                                                                                                                                                                                                                        |
| `mtds-solana-defi-backfill`  | Gone — **confirmed COMPLETED** (`EXIT_STATUS=0`, self-deleted 2026-07-12T05:09:46Z after a clean full pass 2023-01-01→2026-07-12; per-day rows for ORCA/RAYDIUM/KAMINO correctly dropped as honest absence for every day except the run day, per its by-design forward-only-honest gate — this closes out G1.6's VM-launch todo) |
