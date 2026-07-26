---
doc_type: issue
title:
  "R1 runbook violation: the legacy no-env market-data-tick-tradfi bucket (2,008-day corpus) was permanently deleted
  2026-07-06 WITHOUT the required --also-legacy migration ever completing — the one attempt that used the flag
  (2026-06-29) OOM-crashed after copying ~1% (37k/3.8M processed_candles), and the actual completing 2026-07-06 apply's
  launcher command never passes --also-legacy at all"
summary: >-
  `data_completion_tradfi_2026_07_15.md`'s R1 runbook item (line 298) requires `migrate_tradfi_to_v9_canonical --apply`
  to include `--also-legacy` before the legacy bucket is decommissioned, so the 2,008-day no-env corpus gets copied into
  canonical form first. E7 (line 180-183) reports the legacy bucket WAS permanently deleted 2026-07-06, "DONE — apply
  2026-07-06 exit_code=0/fatal=0". Code + doc audit (2026-07-26) finds: (1) the launcher command that actually ran that
  day (`deployment-service/scripts/vm/launch-canonical-migration-vm.sh` @ commit 77cfcda, the commit live at apply time)
  builds the tradfi invocation as `--start-date $START_DATE --end-date $END_DATE --workers ${WORKERS:-24}` — NO
  `--also-legacy` anywhere, and the flag's own `argparse` default is `action="store_true"` (False) with no launcher env
  knob to inject it; (2) the ONE prior attempt that DID use `--also-legacy`
  (`canonical-migration-tradfi-20260629-053023`, per `master_data_canonicalisation_migration_catalogue_2026_06_07.md`
  line ~303) OOM-crashed at 06:02 UTC after copying only ~37k of ~3.8M planned `processed_candles` objects (~1%), was
  never resumed with the flag, and the 2026-07-06 "DONE" apply is a SEPARATE, later run using the non-also-legacy
  launcher; (3) the legacy bucket (`market-data-tick-tradfi-central-element-323112`) is confirmed permanently deleted
  (`bucket.exists() == False` via ADC, ADC has active read creds). Net: at most ~1% of the legacy corpus was ever copied
  to canonical before the bucket holding the rest was destroyed.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [tradfi, data-loss, legacy-migration, also-legacy, gcs-delete, governance, R1-runbook]
related:
  [
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26.md,
  ]
created: 2026-07-26
priority: P0
parent_epic: mtds_mdps_master
source:
  "slot 6, data_engineering, 2026-07-26, executing tradfi_satellite_ao_dispatch_batch3-002 (Audit R1/R2
  legacy-decommission safety)"
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
---

# TradFi legacy bucket deleted without the required --also-legacy migration — potential historical data loss

## What I found

**R1's requirement (line 298 of `data_completion_tradfi_2026_07_15.md`):** the v9 canonical `--apply` MUST include
`--also-legacy` to cover the 2,008-day no-env `market-data-tick-tradfi` corpus before that bucket is decommissioned —
"Without the flag, 2,008 legacy days orphan."

**E7's claim (line 180-183, same doc):** "hand C-GREEN to L6 → delete legacy `market-data-tick-tradfi` permanently...
DONE — apply 2026-07-06 exit_code=0/fatal=0."

**Evidence the flag was never actually used on the completing run:**

1. `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` at commit `77cfcda` (the version live on 2026-07-06,
   confirmed via `git log --before="2026-07-06T16:00:00" -1`) builds the tradfi invocation at line 93:
   `python -u -m market_tick_data_service.scripts.migrate_tradfi_to_v9_canonical --start-date $START_DATE --end-date $END_DATE --workers ${WORKERS:-24}`
   — no `--also-legacy` token anywhere in `_script_for`/`_launch`, and no env var in the whole script injects it.
2. `migrate_tradfi_to_v9_canonical.py`'s `--also-legacy` is `action="store_true"` — omitted means `False`, and
   `sources = [canon] + ([legacy] if args.also_legacy else [])` means the legacy bucket is SKIPPED entirely without it.
3. The completing 2026-07-06 apply ran via 2 VMs matching this launcher's naming convention:
   `canonical-migration-tradfi-20260706-145606` (2026 range, `planned=332825 moved=122703`, genuine work) and
   `canonical-migration-tradfi-20260706-152937` (historical range, `planned=1479669 moved=11` — near-total
   idempotent-skip, meaning that range's data was ALREADY canonical-shaped going in, from `canon`-source normalization,
   not from a legacy-bucket copy). Neither VM's run.log survives (rotated, >20 days old) to directly confirm
   `also_legacy=False` in the startup log line, but the launcher SOURCE at that exact commit is unambiguous.
4. **The one prior attempt that DID pass `--also-legacy`**:
   `master_data_canonicalisation_migration_catalogue_2026_06_07.md` (line ~301-303) records "Operator fires `--apply`
   (`--also-legacy` per R1)" → VM `canonical-migration-tradfi-20260629-053023` launched 05:53 UTC 2026-06-29 → "🔴
   BLOCKED 2026-06-29: ... log stalled at 06:02 (SSL `UNEXPECTED_EOF` + connection-pool-full warnings); no EXIT_STATUS
   written; ~37k/3.8M processed_candles migrated (~1%); serial console shows continuous memory pressure ... (OOM-kill
   suspected)." The same doc explicitly says "OPERATOR ACTION REQUIRED: restart TradFi migration" — I find no evidence
   anywhere in the corpus that this restart ever happened WITH `--also-legacy` re-attached; the 2026-07-06 "DONE" apply
   is a distinct, later, non-also-legacy run per (1)-(3) above.
5. **The legacy bucket is confirmed gone**:
   `google.cloud.storage.Client().bucket("market-data-tick-tradfi-central- element-323112").exists()` returns `False`
   via ADC (live credential, not the poisoned CLI active-account) — permanent deletion is real, not a stale doc claim.

**Net**: at most ~1% of the legacy corpus (the partial 2026-06-29 OOM run, IF that partial write actually landed in
canonical before the crash — unverified) was ever copied to canonical form. The remaining ~99% of the 2,008-day legacy
corpus's objects, if they held anything not otherwise captured via the canonical bucket's own independent Databento
ingestion for the same range, are now unrecoverable — the bucket itself is gone, not just the R1 migration step skipped.

## R2 audit (bundled into the same todo, unrelated verdict)

Read-only GCS listing (ADC, no deletes) of the 3 still-unconfirmed R2 DELETE-AFTER targets in the CURRENT canonical
buckets:

| Target                                                         | Bucket                             | Result                                  |
| -------------------------------------------------------------- | ---------------------------------- | --------------------------------------- |
| bare `day=*/asset_group=tradfi/` without `pipeline_mode=`      | `market-data-tick-tradfi-prd-...`  | **0 objects** — clean                   |
| old-shape `processed_candles/` (no `pipeline_mode=` partition) | `market-data-tick-tradfi-prd-...`  | **0 objects** in a 50,000-object sample |
| instruments-store E6 bare `day=` paths                         | `instruments-store-tradfi-prd-...` | **0 objects** — clean                   |

R2 is CLEAN — nothing further to delete for these 3 targets, no operator-gated delete needed on this pass. ("the whole
legacy bucket," R2's 4th listed target, was already destroyed via E7 — see the finding above, not a clean R2 outcome.)

## Why it matters

This is the exact scenario CLAUDE.md's data-pipeline-correctness HARD RULE and the R1 runbook item were written to
prevent: an irreversible GCS delete (E7's own text calls it "⚠️ IRREVERSIBLE") ran without its stated precondition being
met. Whether this is SUBSTANTIVELY a real data-loss event (vs a procedural miss with no net loss, if the canonical
bucket's independent Databento backfill already covers the same 2020-2025ish range with equal or better fidelity) is NOT
something I can determine from the legacy bucket alone — it no longer exists to inspect. This is squarely the "big
finding" class (data-correctness, irreversible delete, governance HARD RULE) that requires operator notification, not a
todo I can close myself.

## Recommended decision

**Main's ruling on BLK-fd0758fb (2026-07-26): Option A — treat as a confirmed data-loss RISK, do NOT accept "procedural
miss, no net loss" unverified.** "Procedural miss, no net loss" is a claim that must be PROVEN with coverage evidence,
never assumed — an irreversible delete ran without its stated R1 precondition, exactly the class the
data-pipeline-correctness HARD RULE + `gcs-and-manifest-delete-safety-protocol.md` exist to catch. Split into what a
worker can do read-only now vs what is genuinely operator-gated:

- [x] ✅ [DATA] P0. **Canonical coverage-equivalence census (worker-doable, read-only, NOT a full-corpus GCS walk)** —
      DONE 2026-07-26 (worker, slot 4) — **VERDICT: NOT a clean net-loss-~0 case.** Census evidence in the new section
      below finds a real, structural uncovered slice (pre-2023 trade/tick-level + options/futures chain-snapshot tradfi
      data) that canonical's own Databento source has essentially never captured. See "2026-07-26 census evidence"
      section below for the full methodology + numbers. This does NOT resolve the parent finding — the two `[OPERATOR]`
      todos below stay open and this evidence feeds their decision. Repo: market-tick-data-service / instruments-service
      (read-only manifest census, no code changes).
- [ ] [OPERATOR] P0. **TIME-CRITICAL — GCS soft-delete / Object-Versioning recovery-window check.** Needs
      `storage.buckets.get` / `gcloud storage buckets list --soft-deleted`, which no available worker credential has.
      The bucket was deleted 2026-07-06 = 20 days ago as of this writing; GCS bucket soft-delete DEFAULT retention is 7
      days (configurable 7-90). If default, the restore window is ALREADY CLOSED; if a longer retention was configured,
      a SHRINKING window may remain. Check immediately — every day may close it permanently.
- [ ] [OPERATOR] P0. **The remediation decision itself** (restore the soft-deleted bucket if recoverable / re-run
      `migrate_tradfi_to_v9_canonical --apply --also-legacy` from a restored copy / accept the loss with the census
      evidence above) — prod-bucket-level infra, operator-only, gated on both items above.
- [x] ✅ [SCRIPT] P2. Fix `data_completion_tradfi_2026_07_15.md` lines 298/304 (R1/R2 checkboxes) — DONE (same session):
      R1 stays open pending the operator decision above; R2 flipped done citing this doc's clean 3-target inventory.
- [x] ✅ [SCRIPT] P3. Add a pre-delete GATE to `launch-canonical-migration-vm.sh` (or the runbook that invokes it) so a
      legacy-bucket-decommission step structurally CANNOT proceed without first verifying `also_legacy=True` appeared in
      a completed, non-crashed migration run for the same asset_group — this exact silent-gap class (a documented
      runbook precondition that a LATER, different invocation quietly doesn't satisfy) shouldn't require a manual
      forensic audit to catch after the fact. **RE-SCOPE NEEDED (2026-07-26, see addendum below) — do not action as
      currently worded; the addendum's Option B is the concrete replacement scope.** — DONE (slot 11, 2026-07-26) via
      the addendum's Option B, not the literal wording: `market-tick-data-service@200db96d` adds
      `scripts/one_offs/verify_legacy_bucket_decommission_precondition.py`, a standalone reusable CLI that
      operationalizes the delete-safety protocol's Part 5 twin-coverage invariant as a runnable, asset_group-agnostic
      check (manifest census, never a GCS walk) — exits non-zero with a gap report when canonical coverage is
      incomplete, 0 when complete. Unit-tested per the addendum's stated done-when (incomplete-coverage case exits
      non-zero with a clear report; fully-covered case exits 0) in
      `tests/unit/scripts/test_verify_legacy_bucket_decommission_precondition.py`. Does NOT touch
      `launch-canonical-migration-vm.sh` (confirmed dead for this purpose per the addendum) and does NOT itself gate any
      delete — the tool is the durable artifact a human decommission step is expected to run and paste output from
      first; the actual delete stays a human-only hard stop per `gcs-and-manifest-delete-safety-protocol.md` § 3.

## 2026-07-26 addendum — todo 5 investigated, needs re-scoping before it's AO-actionable

Investigated where a "pre-delete gate" could concretely attach, per this todo's own two suggested locations
(`launch-canonical-migration-vm.sh` or "the runbook that invokes it"). Neither exists in the form the todo assumes:

1. **The named tool's launcher path is gone.** `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` no
   longer invokes `migrate_tradfi_to_v9_canonical.py` at all — `_script_for()`'s `tradfi` case was REPOINTED 2026-07-19
   to the newer orphan-proof content-migration chain (`migrate_tradfi_canonical_2026_07` →
   `rebundle_tradfi_chains_2026_07` → `recover_tradfi_garbage_underlying_2026_07`, built by
   `_tradfi_content_migration_cmd()`), per the launcher's own comment: "The old day-walking
   `migrate_tradfi_to_v9_canonical` is superseded." `migrate_tradfi_to_v9_canonical.py` still exists as a file but has
   no live launcher category pointing at it — adding a gate to the launcher's tradfi path would gate a code path that
   can no longer run, giving false confidence.
2. **The actual bucket decommission is a human-only hard stop, not a script's code path.** Per
   `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3 hard stop #2 ("Any legacy-object delete after copy")
   - § 1 Part 5 (the legacy-COPIED-not-MOVED invariant, requiring 100% canonical-twin coverage before an asset_group's
     delete list executes), a legacy-bucket delete is NEVER agent-executed at any confidence level — E7's own text
     ("operator directly, interactive session") confirms the 2026-07-06 delete was a human running the delete outside
     any script's `--apply` path. There is no `--apply`/CLI invocation for THIS specific action to intercept — a code
     "gate" inside a launcher cannot structurally block a human typing a `gcloud storage buckets delete` command.
3. **No "runbook that invokes it" doc was found** as a distinct, editable target —
   `data_completion_tradfi_2026_07_15.md` states the R1 requirement in prose but isn't itself an executable gate, and no
   other runbook doc names a decommission-invoking script for the legacy tradfi bucket specifically.

**This makes the todo as literally worded not directly actionable** — it names a code location that can't enforce the
intended invariant. Recommending two options for whoever picks this up next (operator/main to choose, not decided here):

- **Option A (narrow, low-value)**: add a loud, structured warning to `migrate_tradfi_to_v9_canonical.py`'s own log
  output when `--apply` runs without `--also-legacy` (it already logs `also_legacy=%s` at the top, but that's a log
  line, not a durable artifact, and the tool isn't reachable via any current launcher — low value since nothing invokes
  it anymore).
- **Option B (general, actually closes the class this todo describes)**: build a small, STANDALONE, reusable
  pre-decommission verification CLI (e.g. `scripts/one_offs/verify_legacy_bucket_decommission_precondition.py` in
  market-tick-data-service) that operationalizes the ALREADY-DOCUMENTED Part 5 twin-coverage check from
  `gcs-and-manifest-delete-safety-protocol.md` as a runnable tool: given `--asset-group`/`--legacy-bucket`, it verifies
  canonical-twin coverage (via manifest census, not a full-corpus walk) for the legacy bucket's date range and exits
  non-zero with a clear failure report if coverage is incomplete. This becomes the "structural gate" a human
  decommission step is expected to run and paste evidence from FIRST — durable, greppable, reusable across asset_groups
  (not tradfi-specific, not dependent on which launcher/tool happens to be wired up this month). This is genuinely new
  tooling (not a location to bolt a check onto), so it deserves its own scoped follow-up plan/todo with a stated
  done-when, rather than continuing to live as this loosely-worded item.

**Recommendation: re-file this as a properly-scoped follow-up todo (Option B) in a new or existing plan, with an
explicit done-when** (e.g. "a unit test constructs a legacy bucket with a date range NOT fully covered in canonical and
asserts the tool exits non-zero with a clear report; a fully-covered case exits 0"). Declining to force either option
into this loosely-worded slot without that scoping — Option A is low-value on its own, and Option B is a real feature
that needs the same plan-authoring rigor (repo, done-when, estimate) as any other todo, not an ad-hoc implementation
under an audit-finding's addendum.

## 2026-07-26 census evidence (worker P0 todo, slot 4)

**Method**: direct read of the LIVE manifest object
`gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` (5,866,066 rows, object
`updated: 2026-07-26T03:35:45Z` — read via `blob.download_to_filename` + pandas, NOT a bucket/object walk — single
81.8MB file, satisfies the manifest-census / no-full-corpus-walk requirement). The legacy no-env bucket itself cannot be
inspected (deleted); this reads the CANONICAL bucket's own manifest to test whether its Databento-sourced content
already has equivalent fidelity for the range the legacy bucket held.

**Range bound (best-available, the deleted bucket can't be re-inspected)**: the canonical manifest's own `date` column
spans **2018-01-01 → 2026-07-26** (today), i.e. it nominally covers (and pre-dates) the migrator's own
`--start-date 2019-01-01` default and the "2,008-day" legacy-corpus figure from the 2026-06-08 drill-down
(`tradfi_manifest_canonicalisation_2026_06_01.md`). Distinct dates in canonical `<2023` = **1,826** — same order of
magnitude as the legacy bucket's 2,008 `day*` dirs, consistent with the legacy corpus being roughly the pre-2023 tradfi
history. So the DATE RANGE itself is not the gap — what's captured WITHIN that range is.

**Finding — captured_pct by year (source=databento for 5,813,461/5,866,066 = 99.1% of all rows; batch_yahoo/barchart are
the daily-only slices, immaterial here):**

| year | captured | empty_confirmed | attempted_failed | expected_unattempted | total   | captured % |
| ---- | -------- | --------------- | ---------------- | -------------------- | ------- | ---------- |
| 2018 | 0        | 27,964          | 0                | 35,316               | 63,280  | 0.0%       |
| 2019 | 585      | 24,916          | 0                | 38,372               | 63,873  | 0.9%       |
| 2020 | 5,841    | 33,690          | 29,954           | 37,034               | 106,519 | 5.5%       |
| 2021 | 6,251    | 32,566          | 29,805           | 38,602               | 107,224 | 5.8%       |
| 2022 | 6,066    | 29,695          | 29,372           | 39,762               | 104,895 | 5.8%       |
| 2023 | 202,344  | 223,855         | 29,132           | 31,247               | 486,578 | 41.6%      |
| 2024 | 305,343  | 342,042         | 29,634           | 27,172               | 704,191 | 43.4%      |

**The content-type breakdown is the decisive evidence.** Of the `captured` rows in 2018-2022 (18,743 total), the
`data_type` distribution is: `ohlcv_1s` 90,428 · `ohlcv_1m` 84,541 · `ohlcv_24h` 3,383 · **`trades` 11 · `tbbo` 2** ·
`options_chain`/`futures_chain` **0**. Contrast 2023+: `options_chain` **114,251** · `tbbo` **12,765** · `trades` 12 ·
plus the same candle families. i.e. canonical's own Databento source has genuine trade-tick and options/futures
chain-snapshot coverage starting ~2023, and **essentially none for 2018-2022** — exactly the granularity the legacy
bucket's `raw_tick_data` L-hive/L-hyphen layouts held (per `migrate_tradfi_to_v9_canonical.py`'s own docstring:
trades/tbbo/`options_chain`/`futures_chain` are first-class content there, not just candles). This lines up with the
already-documented Databento entitlement limit noted elsewhere in this corpus
(`tradfi_consolidated_closeout_2026_07_18.md`: "the billing entitlement is 1-month L3 + 1-year L1") — Databento
structurally cannot backfill tick-level history beyond its rolling entitlement window, so canonical's own source cannot
reproduce this even on a fresh re-attempt.

**Caveat (does not change the content-type verdict)**: of the 2018-2022 `attempted_failed` rows, ~87,881 (CME) carry
`error_reason=WithinBoundsTradfiSourceZero`, a KNOWN, separately-tracked, still-**UNRESOLVED** manifest
misclassification defect (`tradfi_backfill_throughput_followups_2026_07_24.md` — the NASDAQ/NYSE population of this same
defect was retired `mtds@ccbac784`; the CME/CBOE/FX population, 202,172 rows corpus-wide, remains open, out-of-scope
here). Equities (NASDAQ/NYSE) show 0 `attempted_failed` in this range but 167,093 `expected_unattempted` — i.e.
genuinely never even tried, not confirmed-absent. Neither caveat changes the captured-content finding above
(trades/tbbo/chain ≈ 0 either way for 2018-2022).

**Verdict**: this is NOT the "procedural miss, no net loss" case main's ruling asked to guard against being assumed. The
manifest census finds a real, structural uncovered slice — **pre-2023 tradfi trade-level ticks (`trades`/`tbbo`) and
options/futures chain snapshots** — that canonical's own Databento source has not captured and, per the documented
billing-entitlement window, likely cannot retroactively capture. Whether the deleted legacy bucket actually HELD real
data of this shape for 2018-2022 can no longer be verified directly (bucket gone), but its own `raw_tick_data` layout
being trades/tbbo/chain-snapshot-native makes it the most plausible holder of exactly this missing granularity. This
raises the urgency of the still-open `[OPERATOR]` soft-delete recovery-window check below — every day narrows or closes
the only remaining way to actually confirm/recover the content.

## Codex SSOTs

`/codex/02-data/data-pipeline-correctness-hard-rule.md` (the rule this may violate),
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` (the delete-safety procedure R1/E7 were supposed to follow).

## 2026-07-26 addendum — the delete DATE in this doc is wrong by 8 days (MEASURED, audit log)

**Appended by `/ag-closeout-audit tradfi` (autonomous pass, 2026-07-26). Append-only: no existing text, checkbox, or
`[OPERATOR]` item above was edited — this section records a measurement that the two open `[OPERATOR]` P0 items should
be re-read against before either is actioned.**

This doc states throughout that the legacy bucket "was permanently deleted 2026-07-06", and the TIME-CRITICAL
`[OPERATOR]` P0 above computes its recovery-window urgency from it ("deleted 2026-07-06 = 20 days ago as of this
writing"). **A Cloud Audit Log read disproves that date.** Query (read-only, run this session):

```
gcloud logging read \
  'protoPayload.resourceName:"buckets/market-data-tick-tradfi-central-element-323112" AND
   (protoPayload.methodName="storage.buckets.delete" OR protoPayload.methodName="storage.buckets.create")' \
  --project=central-element-323112 --freshness=120d --limit=10
```

Over a **120-day** window it returns **exactly ONE** event and no create:

| timestamp                        | methodName               | principal                  |
| -------------------------------- | ------------------------ | -------------------------- |
| `2026-07-14T11:03:03.648128088Z` | `storage.buckets.delete` | `ikenna@odum-research.com` |

**Three consequences for the items above:**

1. **Elapsed time is 12 days, not 20.** At the GCS default 7-day bucket soft-delete retention the window is closed
   either way, but any configured retention of 14 days or more (the setting range is 7-90) leaves it OPEN. The
   `[OPERATOR]` soft-delete check above is therefore materially more likely to succeed than this doc currently implies —
   it is worth running promptly, not writing off.
2. **The delete was not part of the 2026-07-06 v9 apply.** It landed **3 minutes before** the 2026-07-14T11:06:16Z
   consolidator pause that `/plans/active/tradfi_multisource_backfill_2026_06_22.md` records for the ICE non-24h purge —
   i.e. it was a step in that day's operator session. The reconstruction in "What I found" items (3) and (5) above
   (which infers the delete date from E7's 2026-07-06 apply) should be corrected to the audited date. It does NOT change
   the substantive finding: the completing apply's launcher still never passed `--also-legacy`, and 8 more days of
   separation between the apply and the delete does not supply the missing migration.
3. **The credential gate above is REAL, confirmed by probe, and needs no re-attempt.**
   `gcloud alpha storage buckets list --soft-deleted --project=central-element-323112` returns
   `HTTPError 403: unified-trading-sa@... does not have storage.buckets.list access`. Separately,
   `gcloud alpha storage buckets describe gs://market-data-tick-tradfi-central-element-323112 --soft-deleted` returns
   `HTTPError 400: Bucket generation is required` — a 400, not a 403, so the only missing input is the soft-deleted
   bucket's **generation**, which is obtainable solely from the 403-denied list call. A worker cannot close this loop;
   an operator (or any principal with `storage.buckets.list`) can, in one command.

Folding this correction into the doc's own summary and the `[OPERATOR]` P0's arithmetic is drafted as todo 1 of
`/plans/active/tradfi_satellite_ao_dispatch_batch4_2026_07_26.md` (`status: draft`, awaiting operator approval).
