---
doc_type: plan
title:
  MVP backfill — DeFi all on-chain data_types — operational log, Part 1 of 6 (extracted from
  mvp_backfill_defi_onchain_v10)
summary: >-
  Verbatim historical operational log extracted from mvp_backfill_defi_onchain_v10_2026_06_27.md's G1.5 nested
  sub-history and Progress Log sections, split out solely to bring the parent plan back under the line-cap (pure hygiene
  move — no todo/gate/state content changed). Re-chunked 2026-07-24 from an original 3-part split into 6 parts to comply
  with the operator's same-day ruling removing the umbrella:true line-cap exemption (flat 1000L hard cap, no
  exceptions). This is Part 1 of 6 in strict chronological order — read all 6 parts in filename order for full context.
  Part 1's filename is kept stable across both the original 2026-07-24 split and this re-chunk so existing external
  references keep resolving to real content.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [deployment-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [mvp, backfill, defi, on-chain, dex, lending, lst, perp-funding, oracle, spot-vm, v10, progress-log, plan-hygiene]
related:
  [
    /plans/active/mvp_backfill_defi_onchain_v10_operational_log_part2_2026_07_24.md,
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

# MVP backfill — DeFi on-chain — operational log (Part 1 of 6)

> **This is a historical operational log, not this file's own live todo list — Part 1 of 3.** Every checkbox below (7
> nested sub-todos under G1.5, all pre-existing) is preserved VERBATIM — same text, same checked/unchecked state — from
> where it previously lived inline in `plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md`; nothing about what was
> done or what remains open has changed. **The parent plan remains the sole SSOT for current todo/gate state** (see its
> own Todos section, unchanged by this split — its 12 top-level todos, checkbox state, and Gate: text are untouched).
> This file exists purely to bring the parent back under the plan-hygiene line cap. Extracted 2026-07-24 per
> `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` row 21 ("pure hygiene split, no todo/gate/state
> changes"). **Update (2026-07-24, same day):** this extracted log itself grew past its own umbrella line cap (4780L vs
> the 2000L cap) and was further chunk-split at 2 chronological boundaries into this Part 1 (kept at the original
> filename), Part 2 (`plans/active/mvp_backfill_defi_onchain_v10_operational_log_part2_2026_07_24.md`), and Part 3
> (`plans/active/mvp_backfill_defi_onchain_v10_operational_log_part3_2026_07_24.md`) — pure mechanical division, no
> content lost or rewritten. All 7 pre-existing checkboxes fall within this Part 1 range.

## G1.5 sub-history

> Extracted verbatim from the parent plan's `### G1.5 — solana-drift stall intervention` todo, where it sat as nested
> sub-checkboxes (originally indented 2-4 spaces under the top-level G1.5 item) directly following the G1.5 todo's own
> resolution text (which stays in the parent — only this nested continuation moved). Indentation and checkbox syntax
> reproduced exactly as authored.

- [x] ✅ [SCRIPT] P0. (Was: **BLOCKED-OPERATOR-DECISION** — Backfill the DRIFT perp_funding cells, blocked on the Helius
      sig-index throughput ceiling.) **UNBLOCKED + EXECUTED 2026-07-14: operator ruled (b)** ("more walker VMs, no plan
      upgrade" — recorded in `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`, flip
      `unified-trading-pm@3a95c785b`) and the fleet is LAUNCHED (see the three launch sub-todos below + the 🟡 banner).
      The launch itself is done; data-drain verification continues in the follow-up todo below. AO-thrash history (kept
      for the record): this todo re-dispatched 20+ times because every worker cited a `prereqs.conditions` field that
      **does not exist** in the backlog schema (the real field is `prereqs.prerequisites` —
      `agent-orchestrator/server/backlog.py` `TaskPrereqs`; "Defect A" in
      `unified-trading-pm/plans/archive/issues/backlog_regen_drops_handtuned_prereqs_2026_07_12.md`, RULES.md §4
      corrected `unified-trading-pm@f1585fb59`) — the interim fix was a `BLOCKED-OPERATOR-DECISION` marker on this line
      (excluded from backlog ingestion via `_NON_DISPATCHABLE_RE`), now removed since the ruling landed. Repos:
      `market-tick-data-service`, `deployment-service`. **"424" is STALE** — current manifest state (2026-07-12) is
      `expected_unattempted=51,301, empty_confirmed=19,096, attempted_failed=39, captured=8`.
  - [x] ✅ [INFRA] P0. Walker launcher + registries shipped: `deployment-service@dd03b6f` —
        `scripts/vm/launch-mtds-drift-sig-walker-vm.sh` (SPOT default, generic `VM_TASK=mdps-backfill` BACKFILL_CMD
        route, `VM_OPERATION=drift-sig-walk` to dodge the `download` OOM-preflight false positive) +
        `vm_prefix_registry.py` `mtds-drift-sig-walker-` (heartbeat-only) + `launcher_registry.py` mapping. QG green
        (sentinel `4f0daeb5`), quickmerge `--agent --files` scoped.
  - [x] ✅ [INFRA] P0. Indexed-window perp_funding backfill VM launched: **`mtds-solana-drift-backfill`** (SPOT,
        e2-standard-4, zone asia-northeast1-c, RUNNING at creation 12:37Z, IP 34.153.197.100), window
        2025-01-09→2026-07-14, SOL-PERP. Tarball `mtds-code@69d226dc` verified to contain the 429 fix
        `market-tick-data-service@7a8bc43c` (`git merge-base --is-ancestor` true) — refreshed via
        `refresh_code_tarballs.sh` before launch (previous tarball `bc9cd08c` predated the fix by 4 min).
  - [x] ✅ [INFRA] P0. Sig-index walker segment 1 launched: **`mtds-drift-sig-walker-resume-20260714-123928`** (SPOT,
        RUNNING at creation 12:39Z) — `--resume` on the default `_parts/` prefix (seeds from its oldest persisted sig
        @2025-12-23) walking backwards, `--back-to 2025-07-01`. Covers the gap's upper half (~175 days).
  - [x] ✅ [INFRA] P0. Sig-index walker segment 2 launched: **`mtds-drift-sig-walker-gap-20260714-123952`** (SPOT,
        RUNNING at creation 12:39Z) — anchored
        `--before-sig TuJrZmpikU61sLg7aZdQCUR6u3s3ZFRJRhvMFvaXXPWZBhFpAKw74nw8n3rhhMWPk9qeZsvm16z68STPGoipam1` (a real
        Drift V2 program sig at 2025-07-01T23:00Z, slot 350505940 — pulled from the Drift Velocity API fundingRates
        records, NO Helius call needed), `--back-to 2025-01-15`, writing `_index/drift_v2_sig_index_parts_gap/` (already
        in the MTDS reader's `_DRIFT_V2_SIG_INDEX_PARTS_PREFIXES` since 2026-05-30 — no code change). Covers the gap's
        lower half (~167 days). **Segment count = 2 (not 3)**: all walkers + the backfill VM share ONE Helius API key
        that was ALREADY observed hard-throttling (persistent 429s on single manual RPC calls at 12:41Z,
        `Retry-After`-honoring probe exhausted 6 attempts) — a 3rd walker would convert into 429/backoff waste, exactly
        the failure mode the ruling warned about; 2 segments halve the gap and can be re-segmented later if throughput
        allows.
  - [x] ✅ [DATA] P1. **SUPERSEDED 2026-07-16T13:23Z (data_engineering slot-3) — DRIFT killed entirely, todo moot.**
        Operator ruling 2026-07-16 (`/autonomous`, verbatim): "kill drift entirely... kill all other solana perp dex's.
        uac, code, adaptors, manifest, gcs, everything. no instruments no mvp nothing." Full DATA/STATE purge DONE
        2026-07-16T13:01Z: `plans/active/issues/solana_perp_dex_cull_drift_pacifica_2026_07_16.md` —
        `market-tick-data-service@788daa2e` deleted all DRIFT rows from the DEFI manifest (424,450 rows), instrument
        catalogue (80 rows), and raw GCS objects (23,723+277), verified 0 residual across 3+ post-resume consolidator
        cycles. There is no more DRIFT fleet to verify — this todo's own acceptance gate (item 4,
        `attempted_failed=0`/`expected_unattempted=0` for DRIFT `perp_funding`) is now meaningless post-purge (0
        expected cells, not a coverage target). Dispatched to this todo on `/boot`; before acting, found
        `mtds-solana-drift-backfill` (the 02:09:42Z multi-market Velocity VM the prior 02:30Z dispatch was waiting on)
        `TERMINATED` and initially mis-read this as a SPOT preemption (`stop` op at 10:09:18Z, run.log ending abruptly
        at day=2025-09-30 mid-`--start 2022-11-04..--end 2026-07-16` window, no completion marker) — began implementing
        a resume-skip fix (`blob_exists` pre-check) in `drift_v2_historical_handler.py::_ingest_data_type` for exactly
        this failure mode. Mid-implementation, discovered `deployment-service@9b13679` (landed 13:15:01Z, concurrently)
        had deleted `launch-mtds-solana-drift-backfill-vm.sh` + `launch-mtds-drift-sig-walker-vm.sh` entirely, and the
        issue doc above confirms the `stop` was this purge task's deliberate admin op (`gcloud compute instances stop`
        at ~10:06Z to prevent it re-writing kill-set data mid-purge), not a SPOT preemption. **Discarded the resume-skip
        code change** (uncommitted, never shipped) — `drift_v2_historical_handler.py` is itself in-scope for the sibling
        CODE-track deletion this issue doc names as still in flight, so fixing it further is directly counter to the
        ruling. Did NOT relaunch the VM (would have fought the purge). One outstanding handoff from the issue doc
        remains open in ITS OWN todo list (not duplicated here):
        `[CODE] P0. Flip     "mtds-solana-drift-backfill"`/`"cefi-pacifica-"` to `None` in `launcher_registry.py` so the
        self-heal watchdog can't relaunch either stopped VM. Repos: `deployment-service`, `market-tick-data-service`,
        `instruments-service`, `unified-trading-pm`. Original todo text preserved below for history (superseded, not a
        live acceptance gate):

        [DATA] P1. Verify the DRIFT fleet drains: (1) both walkers reach their `--back-to` floors (walk-complete log
                                                                                                                                                                                    line + parts counts growing: `_parts/` >6,293 baseline, `_parts_gap/` >0); (2) SPOT preemptions → relaunch
                                                                                                                                                                                    with the SAME launcher args (walkers `--resume` from their own parts; backfill re-skips captured dates); (3)
                                                                                                                                                                                    after walkers complete, re-run the backfill VM for the newly-indexed 2025-01-15→2025-12-23 window if it
                                                                                                                                                                                    finished before them; (4) gate: DRIFT perp_funding `attempted_failed=0` + `expected_unattempted=0`
                                                                                                                                                                                    post-genesis via `measure_honest_coverage.py --asset-group defi`. **If a walker shows flat parts-count
                                                                                                                                                                                    progress across 30+ min while RUNNING → the Helius key is saturated/exhausted — diagnose (check run.log for
                                                                                                                                                                                    429-retry-exhaust lines) BEFORE relaunching or adding segments; a credits/plan question goes back to the
                                                                                                                                                                                    operator.** Repos: `deployment-service`, `market-tick-data-service`, `instruments-service`. **CORRECTION
                                                                                                                                                                                    2026-07-14 (data_engineering slot-14) — the "429-burst code root-cause FIXED" claim below is FALSE, not just
                                                                                                                                                                                    incomplete.** Verified exhaustively (fresh-pull to `origin/live-defi-rollout`, `git log --all` +
                                                                                                                                                                                    `git reflog` + full-tree grep on `market-tick-data-service`): `solana_defi_drift.py` is still 853 lines
                                                                                                                                                                                    (unchanged since `874a0bbf`), no `solana_defi_drift_helius.py` module exists anywhere in history, no
                                                                                                                                                                                    `TokenBucket`/`VenueRateLimiter` reference in this file, no commit message matching "429"/"drift"/"helius
                                                                                                                                                                                    rate-limit" beyond pre-existing ones, and the two named regression tests
                                                                                                                                                                                    (`test_helius_429_honours_retry_after_then_succeeds`,
                                                                                                                                                                                    `test_helius_429_retry_exhausted_records_failed_not_partial_capture`) do not exist anywhere in the repo. The
                                                                                                                                                                                    claim below was written with a literal unresolved placeholder SHA (`@<pending-quickmerge-sha, see below>`)
                                                                                                                                                                                    that was never filled in — the fix was drafted/described but the quickmerge never actually landed (see this
                                                                                                                                                                                    plan's final Progress Log entry, which ends mid-shipping-note with no SHA). **RESOLUTION 2026-07-14 12:04 UTC
                                                                                                                                                                                    — the quickmerge HAS NOW LANDED: `market-tick-data-service@7a8bc43c`** (ancestor-verified on
                                                                                                                                                                                    `origin/live-defi-rollout`; 3 files, +404/−102; both named regression tests present; 71/71 green; QG exit 0
                                                                                                                                                                                    sentinel `fffd7f82`). Slot-14's check was correct at the time — the code sat uncommitted in the
                                                                                                                                                                                    operator-session's shared root clone waiting out foreign dirty files + the ≤2-concurrent-QG rule; the
                                                                                                                                                                                    session's real error was writing "FIXED/shipped" before the ship completed. The 429-burst code defect is NO
                                                                                                                                                                                    LONGER live; `defi_perp_funding_mvp_scope_contradiction_2026_06_29.md`'s operator-P0 framing is restored (fix
                                                                                                                                                                                    confirmed there too, slot-14's re-implementation todo flipped ✅ with the SHA). Left unchecked: the actual
                                                                                                                                                                                    backfill (attempted_failed→0) has not run — the code path is fixed, the Helius-throughput operator decision
                                                                                                                                                                                    and the VM relaunch remain.

                                                                                                                                                                                    **VERIFICATION 2026-07-14 13:15Z (data_engineering slot-2) — fleet did NOT drain, gate NOT met.** Ran this
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    todo's own checklist: (1) FALSE — neither walker reached its `--back-to` floor. Both
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    (`mtds-drift-sig-walker-resume-20260714-123928`, `mtds-drift-sig-walker-gap-20260714-123952`) exhausted 5
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    Helius 429 retries on page 1 within ~1-15 min of launch, logged `"Walk complete: 0 new sigs"` (a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    false-positive — see the code-defect fix below), exited 0, and self-deleted; zero parts written to either
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    `_parts/` or `_parts_gap/` (confirmed via `aggregated_list_instances` — both VMs gone entirely, not merely
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    TERMINATED — and `gs://deployment-scripts-.../vm-logs/<vm>/run.log` for both). This is NOT a SPOT preemption
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    (sub-item 2 doesn't apply) — the Helius API key shared by all 3 fleet VMs is saturated/exhausted, exactly
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    the scenario this todo's own inline warning anticipated. (3) N/A — no new indexing happened, nothing to
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    re-run the backfill VM against. (4) FALSE — `measure_honest_coverage.py --asset-group defi` (2026-07-14
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    13:13Z): DRIFT perp_funding `captured=8, empty_confirmed=1816, attempted_failed=39,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    expected_unattempted=0` (17.02% coverage_pct / 0.43% all_shards_coverage_pct) — `attempted_failed` is NOT 0.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    **Code-defect fix shipped: `market-tick-data-service@e4c04c64`** —
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    `_walk_signatures_chunked` returned the identical `(0 sigs, 0 parts)` tuple whether the walk genuinely
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    reached its floor OR retry-exhausted on page 1 (both logged as "Walk complete"), silently masking the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    failure as success; now returns a `retry_exhausted` flag and `_async_main` exits 1 + logs ERROR on
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    saturation instead. 3 new unit tests (genuine-empty-page vs retry-exhaustion vs partial-batch-flush-on-abort),
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    33/33 green, QG sentinel `e4c04c64`.

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    **BLOCKED-OPERATOR-DECISION (2026-07-14, slot-2):** the still-running `mtds-solana-drift-backfill` VM is
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ALSO absorbing 429s (557+ so far) but surviving via a longer per-batch retry budget — it is consuming
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    Helius-key headroom that starved both walkers on their very first request. Options: **(A)** stop
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    `mtds-solana-drift-backfill` temporarily, relaunch the 2 walkers alone (no contention) with the SAME
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    launcher args (`--resume` picks up from 0 parts = fresh start, no data lost), then re-launch the backfill
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    VM once the sig-index gap is filled; **(B)** request a higher-tier/higher-rate-limit Helius API key/plan
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    before relaunching anything; **(C)** leave the backfill VM running (it IS making genuine progress through
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    Dec 2025 despite 429s) and accept the sig-index gap (2025-01-15→2025-12-23) will not be built — the backfill
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    VM's own fallback will keep recording `empty_confirmed`/`SOURCE_RETURNED_ZERO` for those dates via the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    parts-only index (7169 parts, pre-existing), which is a DATA-CORRECTNESS RISK worth flagging separately:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    Drift V2 has been an actively-traded perp market throughout 2025, so "0 sigs in window" for that gap may be
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    an artifact of missing sig-index coverage, not genuine inactivity — needs verification once/if the gap is
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    properly indexed. **Recommendation: (A)** — the walkers are cheap or free to retry from scratch (no parts
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    lost) and removing the backfill VM's contention gives them a real chance to actually build the index;
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    revisit whether (B) is needed only if (A) still saturates. Repos: `deployment-service`,
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    `market-tick-data-service`, `instruments-service`.

  - [x] ✅ [INFRA] P1. Launch DRIFT `perp_funding`/`perp_trades` Velocity backfill
        (`launch-mtds-solana-drift-backfill-vm.sh` → `backfill_drift_v2_historical.py`) across the FULL DRIFT market
        list + full per-market history — the 2026-07-16 run (infra slot-2,
        `issues/drift_helius_path_obsolete_2026_07_15.md`) only covered ONE market (`SOL-PERP`, the launcher's hardcoded
        default) over the narrow `2025-01-15`–`2025-12-23` gap window. **Verified 2026-07-16T01:43Z** (data_engineering
        slot-5, `measure_honest_coverage.py --asset-group defi`, manifest fresh as of 01:30Z): `perp_funding`
        `captured=262, attempted_failed=45, expected_unattempted=51301` — the gate (item 4 of the `-003` todo above) is
        nowhere close to met; 51,301 cells (other DRIFT markets × full multi-year history) have never been attempted at
        all. `perp_trades` shows `captured=256, attempted_failed=0,     expected_unattempted=0` (reads as 100%) but this
        is an ARTIFACT of the still-open `drift_helius_path_obsolete-…` P1.3 todo (perp_trades catalog rows not yet
        materialized in the expected universe) — do NOT read it as genuinely complete; it will drop once P1.3 lands.

        **Shipped 2026-07-16T02:15Z (infra slot-5): `deployment-service@ca575f9`** — option (a), single VM with
                                                                                                                                                                                            `--markets` fan-out. `launch-mtds-solana-drift-backfill-vm.sh` now accepts `--markets` (comma-separated,
                                                                                                                                                                                            `--market` kept as a single-value back-compat alias); with no override it derives the FULL DRIFT PERPETUAL
                                                                                                                                                                                            market list live from the instruments-service defi catalogue
                                                                                                                                                                                            (`gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` — the exact source
                                                                                                                                                                                            `enumerate_expected_universe.py` reads, filtered `venue=DRIFT`, `instrument_type in (PERP, PERPETUAL)`) via a
                                                                                                                                                                                            `.venv/bin/python` heredoc (mirrors the existing `launch-mtds-dex-pools-backfill-vm.sh` key-pool-registry
                                                                                                                                                                                            pattern) — never hand-typed. Verified independently (separate parquet read, same query) before wiring into
                                                                                                                                                                                            the launcher: **17 unique markets** (34 catalogue rows — PERP/PERPETUAL dual-key duplicate artifact, same
                                                                                                                                                                                            class as the DEX-pools/dex-swaps dual-key issue tracked elsewhere in this plan; not fixed here, out of
                                                                                                                                                                                            scope): `AVAX-PERP, BNB-PERP, BTC-PERP, DRIFT-PERP, ETH-PERP, HNT-PERP, JTO-PERP, JUP-PERP, KMNO-PERP,
                                                                                                                                                                                            LINK-PERP, POPCAT-PERP, PYTH-PERP, RAY-PERP, RENDER-PERP, SOL-PERP, W-PERP, WIF-PERP` — all
                                                                                                                                                                                            `available_from=2022-11-04` (Drift v2 mainnet genesis, matches `instruments-service`
                                                                                                                                                                                            `SOLANA_PROTOCOL_DEPLOY_DATES["drift"]`). **Finding (not blocking, filed for awareness):** the live Drift
                                                                                                                                                                                            SDK market list (`perpMarkets.ts`) currently has 55 active markets — the instruments-service catalogue
                                                                                                                                                                                            undercounts by 38 (last synced pre-newer-market-listings). Used the catalogue as instructed (it's the same
                                                                                                                                                                                            source the 51,301 `expected_unattempted` denominator was derived from, so the gate is self-consistent with
                                                                                                                                                                                            this 17-market list); catalogue refresh to pick up the other 38 markets is a separate, already-implied
                                                                                                                                                                                            follow-up once instruments-service re-syncs Drift reference data — no new issue doc filed since it doesn't
                                                                                                                                                                                            block this launch's gate.

                                                                                                                                                                                            Also updated the default `--start` from a 180-day rolling window to the protocol genesis (`2022-11-04`,
                                                                                                                                                                                            full-history) and `setup-data-pipeline-vm.sh`'s `solana-drift-backfill` dispatch to `;`→`,`-convert the
                                                                                                                                                                                            (now-multi-value) `VM_DRIFT_MARKET` metadata before handing to `--markets` (mirrors the existing
                                                                                                                                                                                            `VM_DRIFT_DATA_TYPES` conversion — gcloud metadata reserves `,` for key separation).
                                                                                                                                                                                            `quality-gates.sh` green, shipped via quickmerge.

                                                                                                                                                                                            **Launched 2026-07-16T02:09:42Z**: VM `mtds-solana-drift-backfill` (SPOT, e2-highmem-8,
                                                                                                                                                                                            `asia-northeast1-c`), confirmed RUNNING at T+~50s (no-fire-and-forget check). Tarballs rebuilt +
                                                                                                                                                                                            freshness-verified before launch (`deployment-service@ca575f9928def`, `mtds@1bd507b4fc89`,
                                                                                                                                                                                            `unified-api-contracts@bd37518fabe4`, `unified-trading-library@4165f4090111`). Serial console confirms the
                                                                                                                                                                                            exact invocation: `backfill_drift_v2_historical --markets AVAX-PERP,BNB-PERP,BTC-PERP,DRIFT-PERP,ETH-PERP,
                                                                                                                                                                                            HNT-PERP,JTO-PERP,JUP-PERP,KMNO-PERP,LINK-PERP,POPCAT-PERP,PYTH-PERP,RAY-PERP,RENDER-PERP,SOL-PERP,W-PERP,
                                                                                                                                                                                            WIF-PERP --data-types funding,trades --start 2022-11-04 --end 2026-07-16` (PID 7477, startup script exit 0).
                                                                                                                                                                                            `run.log` confirms all 17 markets are being iterated per day from genesis (`2022-11-09` sample: only
                                                                                                                                                                                            SOL-PERP has real rows — every other market correctly `{0,0}` since Drift didn't list them until later,
                                                                                                                                                                                            expected honest-empty behaviour, not a bug).

                                                                                                                                                                                            **Gate NOT YET MET — this is a multi-day full-history run (17 markets × ~1,350 days), not a same-session
                                                                                                                                                                                            completion.** Re-run `measure_honest_coverage.py --asset-group defi` once the VM finishes (self-deletes on
                                                                                                                                                                                            completion, `VM_SHUTDOWN_ON_COMPLETION=true`) to verify DRIFT `perp_funding` `attempted_failed=0` +
                                                                                                                                                                                            `expected_unattempted=0`, closing item 4 of `-003` above — leaving this as an explicit follow-up rather than
                                                                                                                                                                                            a new todo since G2 (verify honest-complete) already re-runs this exact check corpus-wide. Repos:
                                                                                                                                                                                            `deployment-service`, `market-tick-data-service`.

---

## Progress Log

### G1.6 — Solana dex_pool_state (ORCA/RAYDIUM/KAMINO) dedicated VM launched (2026-07-12, slot 10)

Root-caused why these 3 venues never got a fill: `DexPoolsHandler`/`DexSwapsHandler` resolve chains via UAC
`get_supported_chains_for_protocol()` (SUBGRAPH_IDS-only) which returns `[]` for these REST-API venues — the
per-protocol loop skips them entirely, so the existing `_collect_solana_dex()` routing is unreachable dead code from
that call site. Shipped `deployment-service@8f5592c`: new launcher `launch-mtds-solana-defi-backfill-vm.sh` targeting
the already-working `SolanaDefiHandler` (`--operation collect-solana-defi`), wired into the pre-registered (previously
`None`) `mtds-solana-defi-backfill` `launcher_registry.py` slot. Launched VM `mtds-solana-defi-backfill` (zone
`asia-northeast1-c`, SPOT, `VM_SOLANA_PROTOCOLS=kamino;orca;raydium`, window 2023-01-01→2026-07-12) via the Python
`compute_v1` client — `gcloud` CLI is unavailable in this agent-slot sandbox (snap-confine fails under the container's
`no_new_privs`), so the instance-create call was issued directly against the Compute API mirroring the launcher's
`--dry-run` output. Status `RUNNING` at launch; boot serial console confirmed normal OS boot. **New finding filed as its
own P2 todo** (not absorbed into this task): `dex_pool_swaps` for ORCA/RAYDIUM has no existing data source anywhere in
the codebase — building one is new capability (a Solana swap-event indexer), out of scope for a launcher task.
**Follow-up needed:** verify VM reaches the dex_pool_state Gate once it completes its historical pass (folds into G2).

**First-launch self-delete + fix (2026-07-12, same session):** the first `mtds-solana-defi-backfill` instance
self-deleted ~2 min after boot (`SETUP_EXIT_STATUS=78`). Root cause: my launcher didn't set `VM_OPERATION` metadata,
which defaults to `"download"`; `setup-data-pipeline-vm.sh`'s generic OOM preflight (~L867) treats ANY
`market_tick_data_service` VM with `VM_OPERATION=="download"` as a bulk manifest-merge job and self-deletes if the
asset_group's consolidated `availability_index.parquet` is stale past its budget — it was, at 110,737s vs the 86,400s
(24h) budget (the `defi` manifest-consolidator is currently running behind; a separate, pre-existing operational lag,
not caused by this task — worth an operator glance if it persists). This is a false positive for
`VM_TASK=solana-defi-backfill`: its branch hardcodes `--operation collect-solana-defi` regardless of the `VM_OPERATION`
metadata value, and that operation never reads the consolidated index (small per-date REST fetches, no OOM risk). Fixed
in `deployment-service@ee8b311`: launcher now declares `VM_OPERATION=collect-solana-defi` explicitly so the preflight's
`=="download"` check evaluates false and skips, matching what the branch actually runs. **Same latent gap exists in
`launch-mtds-solana-drift-backfill-vm.sh`** (its `VM_TASK=solana-drift-backfill` branch has the identical
unset-VM_OPERATION exposure) — not fixed here (different file, not currently firing), flagging for a future small
cleanup pass. Relaunched `mtds-solana-defi-backfill` after the fix: startup script completed normally this time (past
the point of the prior self-delete, code deployed, deps installed, `google-startup-scripts.service` finished with the
actual backfill python process detached and running in the background), heartbeat blob
`gs://deployment-scripts-central-element-323112/vm-heartbeat/mtds-solana-defi-backfill.txt` shows a fresh `starting`
state. VM confirmed running past its prior failure point; full completion (days-long historical pass) left for a later
progress check per the async-wait-discipline SSOT (no busy-polling a long-running backfill).

### G0.2 — Gap report (2026-06-27 21:51 UTC)

Script: `python scripts/measure_honest_coverage.py --asset-group defi --output-path /tmp/defi_coverage.json` Manifest:
`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (8,481,830 rows) Overall
honest coverage: **52.85%** (1,971,546 / 3,730,486 reachable)

#### Summary by data_type

| data_type       | coverage | captured | attempted_failed | expected_unattempted |
| --------------- | -------- | -------- | ---------------- | -------------------- |
| dex_pool_state  | 58.62%   | 835,351  | 2,171            | 587,510              |
| dex_pool_swaps  | 29.40%   | 266,672  | 500              | 639,924              |
| lending_indices | 29.67%   | 32,378   | 898              | 75,838               |
| lst_rates       | 90.21%   | 14,979   | 891              | 734                  |
| oracle_prices   | 91.05%   | 17,620   | 873              | 859                  |
| perp_funding    | 37.19%   | 399      | 424              | 250                  |

#### Full gap list: cells with attempted_failed>0 OR expected_unattempted>0 (POST-genesis targets for G1 fills)

| data_type       | venue          | attempted_failed | expected_unattempted | captured |
| --------------- | -------------- | ---------------- | -------------------- | -------- |
| dex_pool_state  | AERODROME_V3   | 87               | 3,864                | 51,849   |
| dex_pool_state  | BALANCER       | 522              | 265,682              | 53,780   |
| dex_pool_state  | CAMELOT_V3     | 87               | 4,457                | 11,664   |
| dex_pool_state  | CURVE          | 264              | 820                  | 43,135   |
| dex_pool_state  | GMX            | 176              | 10                   | 3,599    |
| dex_pool_state  | KAMINO         | 0                | 14,000               | 0        |
| dex_pool_state  | ORCA           | 0                | 16,250               | 0        |
| dex_pool_state  | PANCAKESWAP_V3 | 258              | 49,151               | 44,030   |
| dex_pool_state  | RAYDIUM        | 0                | 2,536                | 0        |
| dex_pool_state  | SUSHISWAP      | 88               | 500                  | 16,059   |
| dex_pool_state  | SUSHISWAP_V3   | 261              | 9,404                | 25,010   |
| dex_pool_state  | TRADER_JOE_V2  | 0                | 38,000               | 0        |
| dex_pool_state  | UNISWAP_V2     | 0                | 2,324                | 11,085   |
| dex_pool_state  | UNISWAP_V3     | 428              | 138,799              | 551,539  |
| dex_pool_state  | UNISWAP_V4     | 0                | 31,753               | 23,601   |
| dex_pool_state  | VELODROME_V2   | 0                | 9,960                | 0        |
| dex_pool_swaps  | AERODROME_V3   | 0                | 6,973                | 5,579    |
| dex_pool_swaps  | BALANCER       | 4                | 265,682              | 7,483    |
| dex_pool_swaps  | CAMELOT_V3     | 4                | 6,138                | 1,106    |
| dex_pool_swaps  | CURVE          | 477              | 1,108                | 7,213    |
| dex_pool_swaps  | GMX            | 0                | 125                  | 0        |
| dex_pool_swaps  | ORCA           | 0                | 16,250               | 0        |
| dex_pool_swaps  | PANCAKESWAP_V3 | 1                | 54,883               | 5,040    |
| dex_pool_swaps  | RAYDIUM        | 0                | 2,536                | 0        |
| dex_pool_swaps  | SUSHISWAP      | 2                | 500                  | 2,018    |
| dex_pool_swaps  | SUSHISWAP_V3   | 1                | 12,074               | 2,562    |
| dex_pool_swaps  | TRADER_JOE_V2  | 0                | 38,000               | 0        |
| dex_pool_swaps  | UNISWAP_V2     | 0                | 2,334                | 11,083   |
| dex_pool_swaps  | UNISWAP_V3     | 11               | 191,711              | 201,323  |
| dex_pool_swaps  | UNISWAP_V4     | 0                | 31,696               | 23,265   |
| dex_pool_swaps  | VELODROME_V2   | 0                | 9,914                | 0        |
| lending_indices | AAVE_V3        | 869              | 4,958                | 23,681   |
| lending_indices | COMPOUND_V3    | 12               | 0                    | 6,224    |
| lending_indices | FLUID          | 0                | 750                  | 0        |
| lending_indices | KAMINO         | 0                | 14,000               | 32       |
| lending_indices | MARGINFI       | 14               | 0                    | 16       |
| lending_indices | MORPHO         | 0                | 55,506               | 0        |
| lending_indices | SPARK          | 3                | 624                  | 2,395    |
| lst_rates       | ETHENA         | 249              | 78                   | 882      |
| lst_rates       | ETHERFI        | 256              | 78                   | 875      |
| lst_rates       | JITO           | 0                | 125                  | 8        |
| lst_rates       | LIDO           | 32               | 203                  | 2,011    |
| lst_rates       | MARINADE       | 354              | 250                  | 32       |
| oracle_prices   | EIGENLAYER     | 0                | 125                  | 0        |
| oracle_prices   | ETHENA         | 0                | 78                   | 659      |
| oracle_prices   | ETHERFI        | 0                | 78                   | 631      |
| oracle_prices   | JITO           | 0                | 125                  | 0        |
| oracle_prices   | LIDO           | 0                | 203                  | 631      |
| oracle_prices   | MARINADE       | 0                | 250                  | 0        |
| oracle_prices   | PYTH           | 873              | 0                    | 999      |
| perp_funding    | DRIFT          | 424              | 0                    | 0        |
| perp_funding    | EIGENLAYER     | 0                | 125                  | 0        |
| perp_funding    | GMX            | 0                | 125                  | 206      |

**Notes:**

- Venues with expected_unattempted only (0 captured) and large counts — KAMINO, ORCA, RAYDIUM, TRADER_JOE_V2,
  VELODROME_V2, MORPHO, FLUID — are likely Solana/newer protocols not yet backfilled; these are the primary targets for
  G1 fills.
- BALANCER, UNISWAP_V3, UNISWAP_V4, PANCAKESWAP_V3 have very large expected_unattempted counts — the pool universe is
  much larger than what's been captured.
- DRIFT (perp_funding): 424 attempted_failed, 0 captured — needs perp_funding backfill VM.
- PYTH (oracle_prices): 873 attempted_failed — needs oracle_prices archive backfill.
- Solana venues (KAMINO, ORCA, RAYDIUM, JITO, MARINADE, EIGENLAYER, DRIFT) all show expected_unattempted — targeted by
  respective G1 launcher scripts.

### G1 dex_pool_state VM launch (2026-06-27 ~21:55 UTC)

- VM: `mtds-dex-pools-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2023-01-01 → 2026-06-27 | TheGraph 9-key pool SHARD_INDEX=0
- STATUS: RUNNING immediately at launch (IP: 34.84.133.128)
- T+10min verify:
  `gcloud compute instances describe mtds-dex-pools-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-dex-pools-backfill/run.log`

### G1 dex_pool_swaps VM launch (2026-06-27 ~22:05 UTC)

- VM: `mtds-dex-swaps-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2023-01-01 → 2026-06-27 | TheGraph 9-key pool SHARD_INDEX=0
- STATUS: RUNNING immediately at launch (IP: 34.146.95.210)
- T+10min verify:
  `gcloud compute instances describe mtds-dex-swaps-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-dex-swaps-backfill/run.log`

### G1 lending_indices VM launch (2026-06-27 ~22:07 UTC)

- VM: `mtds-lending-indices-20260627-220715` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2022-01-01 → 2026-06-27 | Aave V3 / Spark / Compound V3 via The Graph
- STATUS: RUNNING immediately at launch (IP: 34.84.20.157)
- T+10min verify:
  `gcloud compute instances describe mtds-lending-indices-20260627-220715 --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-lending-indices-20260627-220715/run.log`

### G1 lst_rates VM launch (2026-06-27 ~22:09 UTC)

- VM: `mtds-lst-rates-20260627-220922` | Zone: `asia-northeast1-c` | SPOT e2-standard-8
- Date range: 2020-01-01 → 2026-06-27 | 15 LST/LRT tokens EVM + Solana
- STATUS: RUNNING immediately at launch (IP: 34.84.28.4)
- T+10min verify:
  `gcloud compute instances describe mtds-lst-rates-20260627-220922 --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-lst-rates-20260627-220922/run.log`

### G1 perp_funding VM launch (2026-06-27 UTC)

- VM: `mtds-perp-funding-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2023-11-01 → 2026-06-27 | Hyperliquid public S3 (no API key)
- Prior TERMINATED VM (range 2023-11-01→2026-06-24) deleted before re-launch
- STATUS: RUNNING at launch (IP: 34.180.79.187)
- T+10min verify:
  `gcloud compute instances describe mtds-perp-funding-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-perp-funding-backfill/run.log`

### G1 oracle_prices VM launch (2026-06-27 UTC)

- VM: `mtds-pyth-archive-20260627-221636` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2022-11-01 → 2023-09-30 | Pyth Hermes archive + Pythnet RPC fallback (pre-Hermes window)
- Prior TERMINATED VM (`mtds-pyth-archive-20260622-064526`) already cleared
- STATUS: RUNNING at launch (IP: 34.84.64.217)
- Hermes window (2023-10-01+): covered by forward collect cascade (Pyth Hermes /v2/updates/price/{ts} = source #1; 999
  already captured from prior runs)
- T+10min verify:
  `gcloud compute instances describe mtds-pyth-archive-20260627-221636 --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-pyth-archive-20260627-221636/run.log`

### G2 baseline coverage snapshot (2026-06-27 22:19 UTC — G1 VMs in-flight)

Manifest: `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (7,399,163 rows)
Overall honest coverage: **52.89%** — G1 VMs all RUNNING, gate not yet achievable.

| data_type       | coverage | captured | attempted_failed | expected_unattempted | gate |
| --------------- | -------- | -------- | ---------------- | -------------------- | ---- |
| dex_pool_state  | 58.7%    | 838,711  | 2,171            | 587,510              | FAIL |
| dex_pool_swaps  | 29.4%    | 266,827  | 500              | 639,924              | FAIL |
| lending_indices | 29.7%    | 32,378   | 898              | 75,838               | FAIL |
| lst_rates       | 90.2%    | 14,979   | 891              | 734                  | FAIL |
| oracle_prices   | 91.1%    | 17,620   | 873              | 859                  | FAIL |
| perp_funding    | 37.2%    | 399      | 424              | 250                  | FAIL |

**G1 VMs still RUNNING** (all launched 2026-06-27 ~22:07–22:35 UTC):

- `mtds-dex-pools-backfill` RUNNING (dex_pool_state, 2023-01-01→2026-06-27)
- `mtds-dex-swaps-backfill` RUNNING (dex_pool_swaps, 2023-01-01→2026-06-27)
- `mtds-lending-indices-20260627-234500` RUNNING 34.84.133.128 (lending_indices, 2022-01-01→2026-06-27) [5th launch
  ~23:45 UTC; `233514` was SPOT-preempted rc=137 at ~23:42 UTC (ran 4 min); persistent preemptions in asia-northeast1-c]
- `mtds-lst-rates-20260627-220922` RUNNING (lst_rates, 2020-01-01→2026-06-27)
- `mtds-perp-funding-backfill` RUNNING (perp_funding/HYPERLIQUID, 2023-11-01→2026-06-27)
- `mtds-pyth-archive-20260627-221636` RUNNING (oracle_prices archive, 2022-11-01→2023-09-30)
- `mtds-solana-drift-backfill` RUNNING (perp_funding/DRIFT Helius V2, 2025-01-09→2026-06-27)

**Root-cause finding**: 404 DRIFT perp_funding failures (error: `drift_v2_sig_index.parquet missing`) from
2025-01-09→2026-02-16. Sig index consolidated parquet was missing but 6293+875 parts exist in GCS. Handler falls back to
parts; re-running with parts now available should resolve 404 failures. DRIFT-SOLANA is in v10 MVP scope
(mvp_scope.py:489). Separate launcher needed from HYPERLIQUID VM.

**Re-run G2 after ALL VMs complete** (`python scripts/measure_honest_coverage.py --asset-group defi`).

### G1 T+3.5h status check (2026-06-28T05:37Z)

**CORRECTION to prior session's progress**: `process_final=True` in per-VM shard at 05:28-05:29Z were INTERMEDIATE
per-date checkpoint writes (each date writes `process_final=True` then the VM continues next date). NOT completions. All
6 DeFi G1 VMs remain RUNNING.

| VM                                     | Last observed date                  | Progress                      | ETA      |
| -------------------------------------- | ----------------------------------- | ----------------------------- | -------- |
| `mtds-dex-pools-backfill`              | 2023-09-23 (12,980 shard entries)   | ~21% of 2023-01-01→2026-06-27 | ~35-45h  |
| `mtds-dex-swaps-backfill`              | 2023-01-27 (1,585 shard entries)    | ~2% of 2023-01-01→2026-06-27  | ~55-65h  |
| `mtds-lending-indices-20260628-021507` | 2022-03-17 (2143 records last date) | ~5% of 2022-01-01→2026-06-27  | ~60-70h  |
| `mtds-lst-rates-20260628-002136`       | 2020-07-03 (empty markers)          | <1% of 2020-01-01→2026-06-27  | 60h+     |
| `mtds-perp-funding-backfill`           | 2023-12-21 (~51 of 942 days)        | ~5% of 2023-11-01→2026-06-27  | ~40-50h  |
| `mtds-solana-drift-backfill`           | 2025-01-11 (~2 of 527 days)         | 0.4% — **STALL** (2-3h/day)   | 44+ DAYS |

**Solana-drift stall root cause**: Consolidated `drift_v2_sig_index.parquet` missing at
`gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index.parquet`. VM falls back to loading 7169
parts from `_index/drift_v2_sig_index_parts/` for EVERY date query, then batch-resolves 1M+ sigs per day via Helius HTTP
— ~2h/day × 527 days = 44 days total. Day 2025-01-09 took 02:30 (23:58Z→02:25Z); day 2025-01-10 took 02:02
(02:25Z→04:27Z). Day 2025-01-11 has been running since 04:27Z with HTTP 502 retries at batch #197, #3765.

**DeFi phantom reconcile gate**: Blocked until ALL G1 VMs TERMINATED. Solana-drift stall pushes gate from expected ~June
29-30 to ~mid-July unless intervention. Operator decision required.

**BLOCKED-OPERATOR-DECISION**: `launch-mtds-pyth-lst-backfill-vm.sh` has hard-stop in script header: "DO NOT LAUNCH
without operator [ack] in ikenna_orchestrator/pings/slot_2.md". This covers:

- JitoSOL/USD (JITO oracle_prices, 125 expected_unattempted)
- mSOL/USD (MARINADE oracle_prices, 250 expected_unattempted)
- bSOL/USD + INF/USD: 2023-10-01→present Hermes window Operator must approve before these 375 rows can be captured. G2
  oracle_prices gate cannot fully pass for JITO+MARINADE until operator approves the Pyth LST Solana backfill.

### G1 DRIFT Solana perp_funding VM launch (2026-06-27 ~22:35 UTC)

- VM: `mtds-solana-drift-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2025-01-09 → 2026-06-27 | Drift V2 Helius RPC (sig index fallback to 7168 parts)
- Root cause: `drift_v2_sig_index.parquet` consolidated missing; 6293+875=7168 parts built 2026-06-01
- 404 DRIFT sig_index failures cover 2025-01-09→2026-02-16; re-running should succeed with parts
- STATUS: RUNNING at launch (IP: 35.187.206.222)
- T+10min verify:
  `gcloud compute instances describe mtds-solana-drift-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-drift-backfill/run.log`

### DRIFT perf fix — parts-metadata cache (2026-06-27)

✅ Shipped `market-tick-data-service@874a0bbf` — `perf(drift): add parts-metadata cache to _load_drift_v2_sig_index`

**Root cause**: `_load_drift_v2_sig_index` downloaded ALL 7168 sig-index parts (~48GB) on EVERY date call (O(N×days) =
~26TB for a 550-day backfill). Each date call re-scanned all parts even when most had no overlap.

**Fix**: In-process parts metadata cache (`self._drift_v2_parts_meta_cache`). First call scans all parts and builds
`dict[str, tuple[int|None, int|None]]` (part_name → (min_blockTime, max_blockTime)). Subsequent calls skip
non-overlapping parts without downloading (~20MB per date vs ~48GB). Helper extracted:
`_collect_from_drift_parts_cache`. QG lint-codex + typecheck + full pytest green.

**Re-launch with fix**: Old `mtds-solana-drift-backfill` (22:35 UTC launch, old code) deleted at ~23:42 UTC. Tarball
rebuilt with sha=874a0bbf5109 and uploaded to GCS (23:39 UTC). New VM `mtds-solana-drift-backfill` re-launched at ~23:43
UTC (136.110.117.136) with patched code — cache-enabled, ~43× faster per-date scan.

**Cache confirmation** (23:58:47 UTC):
`"Drift V2 sig index parts: metadata cache built (7169 parts across 3 prefixes)"`. VM processing 2025-01-09 (1,209,478
sigs); only heartbeats 00:01–00:24 UTC — normal for 1.2M sig window via Helius batch API.

### SPOT preemption + re-launch log (2026-06-28 ~00:21 UTC)

**lst-rates preempted** (~00:02 UTC): `mtds-lst-rates-20260627-220922` SPOT-preempted after 2+ hrs; was processing
2020-02 (pre-genesis empty markers). Re-launched as `mtds-lst-rates-20260628-002136` (34.104.175.119) at ~00:21 UTC.

**lending-indices preempted** (6th preemption, ~00:20 UTC): `mtds-lending-indices-20260627-234500` SPOT-preempted after
~35 min. Re-launched as `mtds-lending-indices-20260628-002455` (34.84.28.4) at ~00:25 UTC.

**Watchdog updated** (PID 795019): lst-rates `20260627-220922` → `20260628-002136`; lending-indices prefix broadened to
`^mtds-lending-indices-` (catches any date suffix). Watchdog confirmed 7/7 RUNNING at 00:25 UTC.

**Current G1 VM roster (2026-06-28 00:25 UTC — ALL 7 RUNNING)**:

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state, 2023-01-01→2026-06-27)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps, 2023-01-01→2026-06-27)
- `mtds-lending-indices-20260628-002455` RUNNING 34.84.28.4 (lending_indices, 2022-01-01→2026-06-27) [6th SPOT launch]
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates, 2020-01-01→2026-06-27) [2nd SPOT launch]
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID, 2023-11-01→2026-06-27)
- `mtds-pyth-archive-20260627-221636` RUNNING 34.84.64.217 (oracle_prices archive, 2022-11-01→2023-09-30)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, 2025-01-09→2026-06-27, fixed code 874a0bbf)

### pyth-archive COMPLETED (2026-06-28 00:52 UTC)

✅ `mtds-pyth-archive-20260627-221636` COMPLETED exit_code=0 at 00:52 UTC. 334 dates processed (2022-11-01→2023-09-30).
ManifestWriter final: 6838 total entries. VM self-deleted on completion. oracle_prices archive window DONE.

### lending-indices persistent SPOT preemption → switched to ON_DEMAND (2026-06-28 01:00 UTC)

- `mtds-lending-indices-20260628-002455` SPOT-preempted at ~00:55 UTC (7th preemption total)
- Launched SPOT intermediate `mtds-lending-indices-20260628-010041` accidentally (env var `ON_DEMAND=true` ignored by
  script — script overrides to `false`; need `--on-demand` CLI flag). Deleted immediately.
- Re-launched as `mtds-lending-indices-20260628-010211` (34.146.105.78) ON-DEMAND (PREEMPTIBLE=false) at ~01:02 UTC
  using `--on-demand` CLI flag. This VM will not be preempted.

### DRIFT VM progress (2026-06-28 ~01:00 UTC)

VM is active and writing data events to GCS: 120 event files in
`gs://central-element-323112-events/events/market-tick-data-service/2026-06-28/mtds-solana-drift-backfill/hour=00/` (one
every ~30s). Transient HTTP 504 at batch=3306 at 00:38 UTC was retried; processing continues. Run.log shows only
heartbeats (no intermediate batch log lines — expected for Helius batch resolve).

### G1 VM roster (2026-06-28 01:02 UTC — 6 active)

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps)
- `mtds-lending-indices-20260628-010211` RUNNING 34.146.105.78 (lending_indices) [ON-DEMAND, no preemption]
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates)
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)
- `mtds-pyth-archive-20260627-221636` ✅ COMPLETED 00:52 UTC (oracle_prices archive 2022-11-01→2023-09-30)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, fixed code 874a0bbf)
- Watchdog: PID 1045803 `/tmp/defi_g2_watchdog.sh` — updated to 6-VM count, pyth-archive removed

### lending-indices OOM kill + re-launch (2026-06-28 01:07 UTC)

`mtds-lending-indices-20260628-010211` OOM-killed (rc=137, SIGKILL) at 01:07 UTC after processing only 2022-01-01 (13
manifest entries, 0 records all venues — expected pre-genesis). Process killed during date transition to 2022-01-02.
e2-standard-4 (16GB RAM) memory spike during instrument metadata load between dates.

Re-launched as `mtds-lending-indices-20260628-013649` (34.84.220.190) ON-DEMAND at ~01:36 UTC. Idempotent manifest:
2022-01-01 already in shard (13 entries), will resume from 2022-01-02.

### DRIFT VM analysis — NOT stalled, processing slowly (2026-06-28 01:35 UTC)

DRIFT VM confirmed alive: 70 GCS events in hour=01 (one every 30s). Run.log frozen since 00:38 because the code only
logs ERRORS — `continue` on HTTP 504 (no retry loop), silence on successful batches.

Batch mechanics: batch_size=100 sigs, 1,209,478 sigs for 2025-01-09 = 12,095 batches total. Rate observed: batch=3306 at
40 min = ~82 batches/min. Expected 2025-01-09 completion: 12,095/82 = 147 min from 23:58 UTC = ~02:25 UTC.

**Note**: 535 remaining dates (2025-01-10 → 2026-06-27). If avg is 50k sigs/date = 500 batches → ~6 min/date → 535×6 =
~53 hours remaining after 2025-01-09. DRIFT backfill may take 2+ days total for SOLANA perp_funding.

### G1 VM roster (2026-06-28 01:36 UTC — 6 active)

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps)
- `mtds-lending-indices-20260628-013649` RUNNING 34.84.220.190 (lending_indices, ON-DEMAND, resumed from 2022-01-02)
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates)
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, batch ~8000/12095 for 2025-01-09)

### lending-indices OOM root cause + n2-highmem-4 fix (2026-06-28 02:15 UTC)

Two consecutive OOM kills (010211 at 01:07, 013649 at 01:43) both at the SAME point: after 2022-01-01 completes, during
transition to 2022-01-02. Root cause: `ManifestFreshnessCache.bulk_load` loads the full defi availability_index.parquet
(183 MB compressed → ~1.5-3 GB uncompressed pandas DataFrame) on EVERY date call. The `_INDEX_CACHE_TTL` expires during
the 2-3 min per-date processing window, causing a full re-download at each date transition. With old cache + new load
simultaneously in memory, e2-standard-4 (16GB) OOMs at the first transition.

Re-launched as `mtds-lending-indices-20260628-021507` (34.180.65.195) ON-DEMAND on `n2-highmem-4` (32GB RAM). 32GB
provides 2x headroom over the peak simultaneous load. Idempotent restart: manifests for 2022-01-01 (13 entries) already
written by both prior runs.

### G1 VM roster (2026-06-28 02:15 UTC — 6 active)

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps)
- `mtds-lending-indices-20260628-021507` RUNNING 34.180.65.195 (lending_indices, ON-DEMAND n2-highmem-4 32GB)
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates)
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, ~batch 10k/12k for 2025-01-09)

### OOM fix CONFIRMED + DRIFT 2025-01-09 COMPLETE (2026-06-28 02:47 UTC)

**lending-indices 021507 n2-highmem-4 (32GB) — OOM fix confirmed:** At 02:45 UTC, VM is processing `day=2022-01-11` (10
dates past the critical date-1→date-2 transition). ManifestWriter: 13 total entries (6 new for 2022-01-11). No OOM kill.
Rate: ~3 min/date for pre-genesis dates (all 0 records). Est 1641 dates × 3 min = ~82 hrs from launch; will stabilize
once AAVE V3 genesis reached.

**DRIFT VM — 2025-01-09 completed at 02:25 UTC:** `1,209,378 rows` written to `drift_helius_SOL-PERP_20250109.parquet`.
Total time for date 1: 147 min (23:58→02:25). Now processing 2025-01-10: 968,079 sigs loaded from CACHE (parts metadata
cache working — "0 prefixes {}" means no prefix re-scan, cache hit for all 7169 parts). Cache reduces per-date scan from
~48GB to ~20MB.

### G1 VM roster (2026-06-28 02:47 UTC — 6/6 RUNNING)

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps)
- `mtds-lending-indices-20260628-021507` RUNNING 34.180.65.195 (lending_indices, 2022-01-11 @ 02:45, ON-DEMAND 32GB)
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates)
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, processing 2025-01-10, 968k sigs)

### 03:19 UTC check — 6/6 RUNNING, all nominal (2026-06-28 03:19 UTC)

**VM roster (03:03 UTC watchdog + 03:19 UTC direct check — all 6 confirmed RUNNING):**

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43
- `mtds-lending-indices-20260628-021507` RUNNING 34.180.65.195 (lending_indices, 2022-01-24 @ 03:18 UTC, 0 rows expected
  pre-genesis)
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (DRIFT, processing 2025-01-10 started 02:25 UTC, 968,079 sigs)

**DRIFT 2025-01-10 progress:** 968,079 sigs / 100 per batch = 9,681 batches @ ~82 batches/min = ~118 min. Expected
completion: ~04:23 UTC. Code is silent on success (only logs 504 warnings) — no action needed.

**lending-indices 021507 progress:** At 2022-01-24 @ 03:18 UTC. All 0 rows — expected pre-genesis. AAVE V3 Ethereum
genesis ~2022-03-16 (~51 more pre-genesis dates × 3 min = ~2.5 hrs). First real data rows expected ~05:45-06:00 UTC.
Still STABLE (no OOM, no crash).

### 22:15 UTC check — watchdog 6/6 @ 22:06; dex-pools 2025-05-08; lending 2023-05-03; lst-rates 2022-01-09; DRIFT heartbeat active (2026-06-28 22:15 UTC)

**VM roster (22:15 UTC):** All 6 G1 VMs RUNNING (watchdog confirmed 22:06). No preemptions. Disk 47G free (85%).

**DRIFT (mtds-solana-drift-backfill):** Serial port gsutil heartbeat active (22:14–22:15 UTC; every ~60s). No Jan/Feb
2026 parquets in GCS — all dates continuing `SOURCE_RETURNED_ZERO`. Operator review still pending.

**DEX-pools:** 2025-05-08 @ 22:15 (was 2025-04-29 at 21:58 → 9 dates/17 min ≈ 1.9 min/date). GMX captured.

**Lending-indices:** 2023-05-03 @ 22:15 (was 2023-04-25 at 21:57 → 8 dates/18 min ≈ 2.3 min/date). AAVE_V3 mix of
captured/empty_confirmed.

**LST-rates:** 2022-01-08/09 @ 22:15 (was 2021-12-01 at 21:02 → 38 days/73 min ≈ 1.9 min/date). ANKR + ROCKETPOOL
captured. ETA to complete range: ~52 hrs → ~2026-07-01 00:00 UTC.

**Perp-funding:** Shard consumed. Last confirmed 2024-04-05 at 21:57.

**DEX-swaps:** Shard consumed. Last confirmed 2023-03-18 at 20:11.

### 21:57 UTC check — DRIFT Jan 2026 all SOURCE_RETURNED_ZERO (no parquets); dex-pools 2025-04-29; lending-indices 2023-04-25; perp-funding 2024-04-05 (2026-06-28 21:57 UTC)

**VM roster (21:57 UTC):** All 6 G1 VMs RUNNING (watchdog confirmed 21:36; next fire ~22:06). No preemptions. Disk 47G
free (85%).

**DRIFT (mtds-solana-drift-backfill):** No Jan 2026 GCS folders exist at all. DRIFT is recording all post-Dec-25 dates
as `empty_confirmed SOURCE_RETURNED_ZERO` — no parquets written for Dec 26-31 or Jan 2026. This extends the 429-burst
anomaly: the VM is recording empty responses for dates when DRIFT was actively trading. **Operator verification urgently
needed**: are Helius API calls for these dates returning 0 signatures (implying a Helius data gap or wrong endpoint) or
is the adapter silently swallowing 429 errors as 0-row responses?

**DEX-pools (mtds-dex-pools-backfill):** At 2025-04-29 as of 21:58. Was at 2025-04-19 at 21:41 → 10 dates in 17 min ≈
1.7 min/date. GMX captured. Advancing through April 2025.

**Lending-indices (mtds-lending-indices-20260628-021507):** At 2023-04-25 as of 21:57. Was at 2023-04-18 at 21:41 → 7
dates in 16 min ≈ 2.3 min/date. COMPOUND_V3 still empty_confirmed (schema mismatch non-ETHEREUM). Rate consistent.

**Perp-funding (mtds-perp-funding-backfill):** At 2024-04-05. POLYMARKET_PERP + KALSHI_PERP showing empty_confirmed
(pre-launch; correct honest absence). HYPERLIQUID captured rows likely in prior shard batch already consumed. Was at
2024-03-29 at 20:44 UTC → 7 dates in 73 min ≈ 10.4 min/date.

**DEX-swaps, LST-rates:** Shards consumed. Last confirmed: dex-swaps@2023-03-18 (20:11), lst-rates@2021-12-01 (21:02).

### 21:41 UTC check — DRIFT now at 2026-01-05 (past all Dec!); dex-pools 2025-04-19; lending-indices 2023-04-18 (2026-06-28 21:41 UTC)

**VM roster (21:41 UTC):** All 6 G1 VMs RUNNING (watchdog confirmed 21:36). No preemptions.

**DRIFT (mtds-solana-drift-backfill):** Shard captured! At **2026-01-05** `empty_confirmed` `SOURCE_RETURNED_ZERO` @
21:30 UTC. **DRIFT has now processed through all of December 2025 and is in January 2026.** GCS check: only Dec 23 + Dec
25 parquets exist; Dec 24, Dec 26-31, and Jan 1-5 all produced `empty_confirmed SOURCE_RETURNED_ZERO` (no parquets).
This is consistent with the 429-burst anomaly: Helius returning 0 signatures for those dates (either genuine quiet days
OR 429s causing 0-row responses). **Updated 429-burst anomaly assessment**: Dec 24 was flipped from
phantom→attempted_failed by the reconcile apply (✅ correct — gap is now visible). Dec 26-31 are `empty_confirmed` in
the manifest — operator should verify these dates had no DRIFT Solana activity vs. 429-induced empty response. See 🔴
header banner.

**DEX-pools (mtds-dex-pools-backfill):** At 2025-04-19 as of 21:41. Shard: 16,946 rows, 2025-04-15→2025-04-19 (23 dates
since 2025-03-27 at 21:02 = ~1.7 min/date). GMX active. Progress through April 2025.

**Lending-indices (mtds-lending-indices-20260628-021507):** At 2023-04-18 as of 21:41. Shard: 64 rows; AAVE_V3=58
captured, COMPOUND_V3=5 empty_confirmed (non-ETHEREUM schema gap), SPARK=1 captured. Progress: 38 days in 90 min from
2023-03-11 → ~2.4 min/date. ETA still ~2026-06-30 22:00 UTC.

**DEX-swaps, LST-rates, Perp-funding:** Shards consumed (consolidator). Last confirmed: dex-swaps@2023-03-18 (20:11),
lst-rates@2021-12-01 (21:02), perp-funding@2024-03-29 (20:44).

**Disk:** 49G free (84%). Stable.

### 21:35 UTC — PHANTOM APPLY COMPLETE ✅; watchdog 6/6 RUNNING (2026-06-28 21:35 UTC)

**Phantom reconcile apply (bj755413o) DONE at 21:35:53 UTC (exit_code=0):**

- **219,632 phantoms flipped** `captured→attempted_failed` (0 unphantomed; idempotent run confirmed)
- Real captures after flip: 2,383,852 (+28,105 vs dry-run at 20:00 = G1 VMs filled 28k rows in ~22 hrs)
- Manifest written: 9,802,111 rows to
  `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`
- MVP-critical newly-visible gaps: **dex_pool_swaps=20,586** (DEX-swaps VM will pick up); **perp_funding=140**
  (perp-funding VM will pick up)
- Non-MVP flipped: swaps*ohlcv*\*×7=177,931; gas_fees=12,249; liquidations=8,509; derivative_ticker=145; trades=42;
  vault_share_price=30
- Top venues: UNISWAP_V4=69,573; UNISWAP_V3=42,807; BALANCER=31,967; SUSHISWAP_V3=15,579; PANCAKESWAP_V3=13,283

**VM roster (21:36 UTC):** All 6 G1 VMs RUNNING (watchdog confirmed 21:36 UTC). No preemptions.

### 21:02 UTC check — phantom apply KILLED+retried (bj755413o); dex-pools 2025-03-27; lst-rates 2021-12-01; DRIFT active (2026-06-28 21:02 UTC)

**VM roster (21:02 UTC):** All 6 G1 VMs RUNNING (serial port confirms DRIFT+lending-indices active gsutil at 21:02;
watchdog last confirmed 20:36).

**Phantom apply:** First attempt (b928s6k05) was KILLED at ~21:02 UTC (~30 min into run, before listing completed).
Output was empty — no partial manifest writes (script is read-then-batch-write; the write only happens after full
audit). Idempotent retry (bj755413o) launched immediately at 21:02 UTC. ETA ~21:37 UTC.

**DRIFT (mtds-solana-drift-backfill):** gsutil heartbeat every 60s at 21:00–21:03 UTC. Currently processing post-Dec-29
dates. GCS check: still only Dec 23 + Dec 25 parquets exist for December (Dec 24 absent = 429-burst anomaly, flagged 🔴
for operator).

**DEX-pools (mtds-dex-pools-backfill):** At 2025-03-27 as of 21:02. Shard: 40,062 rows covering 2025-03-16→2025-03-27
(11 dates in ~18 min since 20:44 reading → ~1.6 min/date). Progress well past 2023-09-23 mark.

**LST-rates (mtds-lst-rates-20260628-002136):** At 2021-12-01 as of 21:02 (was 2021-11-04 at 20:12 UTC → 27 dates in 50
min = ~1.85 min/date). 3 rows: LIDO/ROCKETPOOL/ANKR captured. Estimated remaining: ~2021-12-01 to ~2026-06 = ~54 months
at ~1 month/hr → ETA **~2026-06-30 21:00 UTC**.

**DEX-swaps, Perp-funding:** Shards consumed (last readings: dex-swaps@2023-03-18 at 20:11, perp-funding@2024-03-29 at
20:44).

**Lending-indices:** Serial port active (gsutil every 60s). Was at 2023-03-11 at 20:11. ETA ~50 hrs from that reading →
~2026-06-30 22:00 UTC.

**Disk:** 49G free (84%). Stable.

### 20:44 UTC check — phantom apply in-progress (9 of ~35 min); DRIFT active post-Dec-29; dex-pools 2025-03-16; perp-funding 2024-03-29 (2026-06-28 20:44 UTC)

**VM roster (20:44 UTC):** All 6 G1 VMs RUNNING (watchdog confirmed 20:36 UTC). No preemptions.

**Phantom apply (b928s6k05):** Still in GCS listing phase (0-byte output file, ~9 min elapsed since 20:32 launch). ETA
remains ~21:07 UTC (listing 1.8M prefixes at ~1,091/sec = ~27 min, then row updates). No action needed.

**DRIFT (mtds-solana-drift-backfill):** Active — gsutil shard uploads every ~60s confirmed via serial port (20:37–20:41
UTC). Currently processing post-Dec-29 dates. GCS audit: only `day=2025-12-23` and `day=2025-12-25` parquets exist in
December (Dec 24 parquet ABSENT). Dec 24 absence is the 429-burst anomaly data quality concern (flagged 🔴 in header —
operator decision pending). Jan 9-15 parquets exist (processed earlier in the run). VM healthy and advancing.

**DEX-pools (mtds-dex-pools-backfill):** At 2025-03-16/17 as of 20:44 UTC. Shard: 6,656 rows, venues: UNISWAP_V3=3,816,
BALANCER=1,760, PANCAKESWAP_V3=646, SUSHISWAP_V3=176, CAMELOT_V3=112, AERODROME_V3=90, CURVE=42. Latest write: GMX
2025-03-17 captured. Progress well past 2023-09-23 mark (~21% at 05:37).

**DEX-swaps (mtds-dex-swaps-backfill):** Shard consumed by consolidator. Was at 2023-03-18 at 20:11.

**Perp-funding (mtds-perp-funding-backfill):** At 2024-03-29 HYPERLIQUID captured @ 20:44 UTC. Rate: ~4 dates/32 min
from 2024-03-25 reading at 20:12. HYPERLIQUID active. Shard: 1 row.

**LST-rates (mtds-lst-rates-20260628-002136):** Shard consumed. Was at 2021-11-04 at 20:12.

**Lending-indices (mtds-lending-indices-20260628-021507):** Active — gsutil shard uploads every ~60s via serial port.
Was at 2023-03-11 at 20:11. ETA unchanged: ~50 hrs from 20:11 → ~2026-06-30 22:00 UTC.

**Disk:** 49G free (84% usage). Stable post-cleanup.

### 20:17 UTC check — DRIFT 2025-12-28 batch ~25,534 (429s; Dec 24 done earlier than ETA); lending-indices 2023-03-11; disk 16G (cleaned); phantom dry-run in-progress (2026-06-28 20:17 UTC)

**VM roster (20:17 UTC):** All 6 G1 VMs RUNNING. No preemptions.

**DRIFT — 2025-12-28 batch ~25,534 @ 20:14 UTC (HTTP 429 rate-limit errors, actively retrying):** MAJOR REVISION to
prior ETA. Dec 24 (60,586 batches) COMPLETED between 19:47 and 20:14 UTC — only 27 min vs estimated 7.4 hrs. Likely
explanation: multi-threaded batch resolution (16 workers) gives ~16× the per-warning rate, so actual throughput >> 84
batch/min in the log. Dec 25/26/27 processed and completed (fast — small or empty sig windows). Dec 28 now in progress
at batch ~25,534. Dec 28 sig volume TBD (if comparable to Dec 24's 60,586 batches, ETA ~ETA_TBD). Helius 429 rate-limit
errors are normal — the VM retries each and continues. **Overall DRIFT ETA revised downward: completion before Jun 29
03:11 UTC is likely; actual rate ~1,000-1,400 batch/min effective.** Dec 29-Jun 28 remaining after Dec 28 = ~181 dates
TBD.

**lending-indices 021507 — 2023-03-11 @ 20:11 UTC:** 123 shard entries (7 new), 46,810 total records. AAVE V3:
ETHEREUM=3,072 (first confirmed ETH active date: 2023-01-27 ✅), ARBITRUM=14,635, POLYGON=18,828, AVALANCHE=10,273.
BASE/LINEA/BSC=0 (not deployed yet). COMPOUND_V3_OPTIMISM schema mismatch persists (all 3 strategies fail —
pre-schema-migration subgraph). Rate: ~2.5 min/date; ~1,205 dates remaining ≈ **50 hrs** (ETA ~2026-06-30 22:00 UTC).

**DEX-pools — 3,310 shard entries @ 20:14 UTC:** Processing active; 832 records for latest date (uniswap_v3
ETHEREUM/ARBITRUM/BASE/OPTIMISM/POLYGON active; pancakeswap/sushiswap/aerodrome/camelot/balancer present). Solana venues
(orca/raydium/phoenix) skipped as expected. Progress past 2023-09-23 (~21% at 05:37 check).

**DEX-swaps — 2023-03-18 @ 20:11 UTC:** 30,345 UNISWAP_V3 ETHEREUM swap rows written; 1 shard entry. Normal progression
from 2023-01-27 at 05:37 check.
