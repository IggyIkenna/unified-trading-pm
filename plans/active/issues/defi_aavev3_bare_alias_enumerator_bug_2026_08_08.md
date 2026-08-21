---
doc_type: issue
title: AAVEV3 bare-alias phantom venue — instruments-service pre-launch enumerator bug (root-caused + fixed)
summary: >-
  46,300 manifest rows with bare venue=AAVEV3 (no chain split, capture_status=empty_confirmed, dated
  2018-01-01..2023-01-26, single bulk written_at=2026-08-05T04:08:15Z) traced to a real code defect:
  unified-api-contracts/chain_env.py's PROTOCOL_LAUNCH_DATES carries a literal duplicate dict key ("ETHEREUM","AAVEV3")
  alongside the canonical ("ETHEREUM","AAVE_V3") entry ("alias: no-underscore form used by some callers");
  instruments-service/scripts/enumerate_expected_universe.py::_yield_v2_defi_pre_launch_rows iterated
  PROTOCOL_LAUNCH_DATES.items() with venue_label = protocol.upper() and zero alias canonicalisation, so the alias key
  seeded its own full pre-launch placeholder sweep as an independent phantom venue. Dormant historical batch artifact (0
  GCS objects backing it, not a live/growing writer — capped by the fixed 2023-01-27 launch-date window, already fully
  seeded) but the code defect was live and would re-materialise on any future re-enum, and the same class of bug (an
  un-canonicalised alias key + naive .upper() iteration) could reproduce for any other protocol given a bare-spelling
  alias in PROTOCOL_LAUNCH_DATES. Root-caused by a dispatched sub-agent (read-only investigation); code fix applied same
  session (instruments-service canonicalises venue_label via VenueMapping._canonicalise_defi_protocol_spelling + dedups
  the (chain, venue) pair before emitting, mirroring the identical fix already applied to the per-instrument v2 path in
  the same file at line ~1542).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [defi, aavev3, canonical-naming, enumerator, phantom-venue, expected-universe]
related:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-08"
author: interactive session (/autonomous)
priority: P2
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md AAVEV3 row, sub-agent root-cause dispatch, 2026-08-08",
  ]
drift_direction: advance-code
context_scope:
  [
    instruments-service/scripts/enumerate_expected_universe.py,
    unified-api-contracts/unified_api_contracts/registry/chain_env.py,
    unified-api-contracts/unified_api_contracts/registry/venue_mapping.py,
  ]
---

## Finding

Sub-agent read-only investigation (full detail in the tracker doc's Progress Log, 2026-08-08 entry) confirmed:

- All 46,300 `venue=AAVEV3` manifest rows: `capture_status=empty_confirmed`, `chain=ETHEREUM`, dated
  2018-01-01→2023-01-26 (the day before AAVE_V3-ETHEREUM's registered 2023-01-27 launch), 25 `data_type` values × 1,852
  rows each, single identical `written_at=2026-08-05T04:08:15.957401+00:00` (one bulk batch write),
  `service_name=instruments-service`.
- 0 GCS objects under any `AAVEV3` path — pure manifest bookkeeping, no backing data.
- Mechanism: `unified-api-contracts/unified_api_contracts/registry/chain_env.py:199` carries
  `("ETHEREUM", "AAVEV3"): "2023-01-27"` as a literal duplicate dict key beside the canonical `("ETHEREUM", "AAVE_V3")`
  entry (line 198). `instruments-service/scripts/enumerate_expected_universe.py:: _yield_v2_defi_pre_launch_rows`
  (~line 1469) iterates `PROTOCOL_LAUNCH_DATES.items()` directly with `venue_label = protocol.upper()` — no alias
  canonicalisation — so the alias key seeded its own full pre-launch placeholder sweep as an independent phantom venue.
- Rules out both originally-framed hypotheses: not a live writer (population is capped by a fixed historical launch-date
  window, not growing) and not the `canonical-migration-defi-rebuild-20260806-223130` VM surfacing old GCS objects
  (chronologically impossible — the rebuild started 2026-08-06, a day after these rows' `written_at`, and 0 GCS objects
  exist to surface anyway).

## Fix (shipped this session)

`instruments-service/scripts/enumerate_expected_universe.py::_yield_v2_defi_pre_launch_rows`: canonicalises
`venue_label` via `VenueMapping._canonicalise_defi_protocol_spelling(protocol.upper())` — the identical fix already
applied to the per-instrument v2 path in the same file (line ~1542) — and tracks emitted `(chain, venue_label)` pairs so
the canonical and alias dict keys (which now both resolve to the same `venue_label`) don't double-emit every pre-launch
row for that venue. Regression test added:
`tests/unit/scripts/test_enumerate_expected_universe_v2.py::test_defi_v2_pre_launch_alias_key_not_duplicated`.

Deliberately NOT touched: `chain_env.py`'s `PROTOCOL_LAUNCH_DATES` dict itself — the `AAVEV3` key's own comment says
"alias: no-underscore form used by some callers," implying other consumers may do a direct dict lookup by the bare
spelling; removing the key blind risked breaking them. The enumerator-side canonicalisation fix is scoped to the actual
defect (phantom-venue emission) without touching a registry other code may depend on.

## Impact / what's still open

- **Not urgent, not paging** — the bad data is a bounded, dormant historical artifact (zero real captured rows at risk),
  and the code fix prevents it from ever re-materialising on a future re-enum.
- **Historical row purge is `[OPERATOR]`-gated, not done here** — the existing 46,300 `empty_confirmed` manifest rows
  still need a human-gated `--apply` purge (same `gcs-and-manifest-delete-safety-protocol.md` path already used for the
  gas_fees/GMX purges) once someone confirms no twin-exists collision against real `AAVE_V3` pre-launch rows for the
  same window.
- **`chain_env.py`'s alias-dict-key pattern itself is unaddressed** — the same class of bug (a bare-spelling alias key
  in `PROTOCOL_LAUNCH_DATES` + naive `.upper()` iteration elsewhere) could reproduce for any future protocol given a
  similar alias entry. A design question (should `PROTOCOL_LAUNCH_DATES` keep alias dict-keys at all, vs. resolving
  aliases inside a `get_protocol_launch_date()` accessor), not resolved here.

## Todos

- [x] [CODE] P2. Canonicalise `venue_label` + dedup emitted `(chain, venue)` pairs in `_yield_v2_defi_pre_launch_rows` —
      `instruments-service@2b2e9f124`, QG-verified + regression test added.
- [ ] [DATA] P1. **Re-run the purge script's dry-run — first attempt 2026-08-20 hit a network timeout, not a
      logic failure, no write occurred.** `instruments-service/scripts/purge_defi_aavev3_bare_alias_manifest_rows_2026_08_20.py`
      (shipped `instruments-service@<pending, see plan Progress Log for sha>` — the script itself is code-reviewed
      and safe: dry-run by default, snapshot + fresh §3a soft-delete retention check before any write, arithmetic
      gate refusing to proceed if anything but `capture_status=empty_confirmed` rows would be touched). Bucket
      `market-data-tick-defi-prd-central-element-323112` confirmed 2026-08-20 at exactly 604800s (7-day) soft-delete
      retention — QUALIFIES for the §3a agent-autonomous execution path, no operator step needed once the dry-run
      confirms the expected shape. **What happened**: `.venv/bin/python scripts/purge_defi_aavev3_bare_alias_manifest_rows_2026_08_20.py`
      timed out downloading the ~3GB `_index/availability_index.parquet` (`google.api_core.exceptions.RetryError:
      Timeout of 600.0s exceeded` — a `storage.googleapis.com` read timeout, not a script bug). No delete was
      attempted (dry-run is the default; the timeout happened during the initial read, before any gate logic ran).
      **Retried 2026-08-20 — SECOND failure, different mode: SIGKILL (exit 137), not a timeout.** The retry got
      past the first attempt's timeout point (logged "Reading defi manifest...") but was killed before ever
      logging "Loaded N manifest rows" — consistent with an OOM kill while buffering/parsing the ~3GB
      `_index/availability_index.parquet`. Two consecutive hard failures on the identical operation, in two
      different failure modes (network timeout, then OOM), both pointing at the same underlying cause: this
      class of I/O — a multi-GB whole-manifest read — should not run on the operator's laptop at all, per this
      workspace's own standing rule ("heavy I/O... NEVER runs on the operator's local machine, always a VM
      in-region", `/codex/05-infrastructure/vm-launcher-runbook.md`). **This purge script was written for local
      execution and needs a VM path instead** — either add a new category to
      `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (mirroring the existing
      `cefi-itype-casing-apply` category's pattern) or run it via the generic `setup-data-pipeline-vm.sh`
      startup script. **Not attempting a third local retry** — two failures on the identical operation is the
      retry-discipline threshold; the fix is infra placement, not another attempt with different flags.
      **UPDATE 2026-08-20 — VM path built (`deployment-service@9ae1a78e9e`), 6 launch attempts, STILL
      UNRESOLVED — see the Progress Log for the full attempt-by-attempt breakdown.** Summary: a real relative-path
      bug (fixed), a real launcher freshness-check false-negative (not a bug, retried), a genuine laptop-side
      network timeout uploading tarballs (retried after a pause), then attempts #5 and #6 BOTH self-deleted with
      **zero run.log output at all** across a full 20-minute bounded watchdog each — a distinct, reproducible
      failure mode not seen on the sibling CeFi launcher (which reliably produces logs on the same underlying
      dispatch route), so this looks specific to this script/launcher combination, not generic infra flake.
      **UPDATE 2026-08-20 (interactive session, serial-console diagnosis + 3 fleet-wide fixes shipped) — dry-run
      STILL never observed to complete; do not attempt an 8th-11th blind retry.** Full attempt-by-attempt detail
      in the Progress Log below; summary: root-caused the silent-death mechanism (NOT a boot-time failure, NOT
      SPOT preemption — confirmed via Cloud Logging that every self-delete is attributed to `uts-prd-sa`, the
      VM's own identity, not GCE's system account), shipped 3 real fixes to the shared VM infra
      (`deployment-service@74c3ad84f1`, `@3ed72199a5`, `@f63eeed04d`), but 2 further launches (attempts #9, #10)
      showed the underlying watchdog subshell's own GCS-upload reliability is itself HIGHLY VARIABLE run-to-run
      (18+ min of clean uploads on #9, zero on #10) with no code-level correlation — pointing at genuine
      intermittent network/infra instability on this project/zone today, the SAME conclusion the 2026-08-20
      laptop-side attempts (immediately above) independently reached. **Next step for the next session**: relaunch
      once (the diagnostic instrumentation from `@f63eeed04d` is now live and will surface the exact
      describe/upload error + exit code if the watchdog subshell gets even one tick this time); if it still
      doesn't run cleanly, this may need EITHER a longer external-reaper grace window for this launcher class OR
      a delivery path less dependent on a backgrounded-subshell's own GCS reliability (e.g. a Cloud Run Job
      instead of a raw VM) — an infra/design call, not a further code-guess.
      **UPDATE 2026-08-21 — attempt #11, with EVERY known code-level fix live (`@74c3ad84f1`, `@3ed72199a5`,
      `@f63eeed04d`, `@38f760e034`), failed identically (no `run.log`, ~17.5min self-delete). This is now the
      decisive data point ruling out a further code fix from this session** — see Progress Log for full detail.
      **Next step is an infra/operator judgment call, not another code guess**: either investigate this
      GCP project/zone's network path to `storage.googleapis.com` directly, or switch this launcher to a
      structurally different execution path (foreground `gcloud compute ssh` session, or a Cloud Run Job instead
      of a raw VM) that doesn't depend on a backgrounded subshell's GCS reliability at all. Not attempting a 12th
      blind relaunch.
      Twin-exists-collision precondition CONFIRMED SATISFIED 2026-08-09
      (see Progress Log) — full-population live-manifest check found 0 of the 46,300 bare cells lacking a
      correct-key `AAVE_V3`-ETHEREUM twin; "0 backing GCS objects" was independently established by the 2026-08-08
      root-cause session (see Finding section above) and cited rather than re-derived, since the population is
      capped by a fixed historical launch-date window and cannot have changed.
- [ ] [DESIGN] P3. Decide whether `chain_env.py`'s `PROTOCOL_LAUNCH_DATES` should keep alias dict-keys at all vs.
      resolving aliases inside a `get_protocol_launch_date()`-style accessor, removing the defensive- canonicalisation
      burden from every future iterator-style consumer of the raw dict.

## Progress Log

- **2026-08-08 (interactive session, `/autonomous`)**: sub-agent root-caused (see Finding); this session applied the
  code fix + regression test directly (bounded, low-risk, mirrors an already-shipped identical fix in the same file)
  rather than only filing the finding, per the operator's "finish everything" directive. Shipped
  `instruments-service@2b2e9f124` (QG-green, `test_defi_v2_pre_launch_alias_key_not_duplicated` added). Remaining work
  is genuinely open (not this session's to do): the `[OPERATOR]`-gated historical row purge, and the `[DESIGN]` question
  on `PROTOCOL_LAUNCH_DATES`'s alias-key pattern — status stays `open`, not `resolved`, until both clear.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- Root-cause + code fix already shipped
  (instruments-service@2b2e9f124). 2 remaining open items both explicitly gated: an `[OPERATOR]` human-executed
  manifest-row purge (46,300 rows, delete-safety hard-stop) and a `[DESIGN]` judgment call on alias dict-keys.
  Corroborated by sibling doc `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`. Doc stays
  `assigned_vm: NA`.
- **2026-08-09 (interactive session, twin-collision confirmation — read-only, no `--apply` run)**: dispatched to answer
  the `[OPERATOR]` todo's blocking precondition ("confirm no twin-exists collision against real `AAVE_V3`-ETHEREUM
  pre-launch rows"). **Verdict: CONFIRMED SAFE — no collision, purge is unblocked for operator go-ahead on `--apply`.**

  **Bucket correction**: the 46,300 rows do NOT live in `instruments-store-defi-prd-{pid}` (checked first, 0 hits —
  `enumerate_expected_universe.py`'s `service_name=instruments-service` attribution refers to the WRITER, not the
  bucket). The actual manifest is `market-data-tick-defi-prd-central-element-323112` — `_default_bucket_for("defi")`
  resolves `resolve_bucket_name(kind="market-data", asset_group="defi")` for the DeFi v2 pre-launch pass
  (`instruments-service/scripts/enumerate_expected_universe.py:392-419`).

  **Live re-confirmation of the 46,300 figure**: read `_index/availability_index.parquet` directly (3,003,002,411 bytes,
  generation 1786282240969913, last_modified 2026-08-09T13:30:40Z) via `gcs_describe_object` +
  `gcs_read_object_with_generation` — row-group-filtered
  `pyarrow.parquet.read_table(filters=[("venue","in", ["AAVEV3","AAVE_V3"])])`, no whole-corpus walk.
  `venue=AAVEV3, chain=ETHEREUM, capture_status=empty_confirmed` = exactly 46,300 rows, live, today — the doc's figure
  is current, not stale.

  **Twin-collision check — FULL POPULATION, not a sample** (cheap enough once the parquet was fetched: 1,208,829
  matching rows total). Built `(date, data_type)` cell sets: bare `AAVEV3` = 46,300 unique cells; correct
  `AAVE_V3`+`chain=ETHEREUM` = 53,506 unique cells (superset spanning full historical + post-launch range). **Bare cells
  lacking a correct-key twin: 0.** Every one of the 46,300 bare `(date, data_type)` cells already has a matching
  correct-key `AAVE_V3`-ETHEREUM row.

  **Content-verify (delete-safety Part 2, not just existence)**: restricting correct-key rows to exactly the bare cells'
  `(date, data_type)` set gives 48,176 rows — `capture_status=empty_confirmed`: **exactly 46,300**, a perfect 1:1 match
  against the bare rows. The remaining 1,876 are `capture_status=captured` (real data) for a subset of cells —
  specifically `data_type=lending_indices` on dates late Dec 2022/early Jan 2023, `written_at=2026-08-07*` — i.e.
  genuine early capture success shortly before the registered 2023-01-27 launch date, filed under the CORRECT key and
  entirely untouched by any purge of the wrong-key duplicates (worth a separate note that `PROTOCOL_LAUNCH_DATES`'s
  2023-01-27 AAVE_V3-ETHEREUM date may be a few weeks conservative for `lending_indices` specifically — not a
  delete-safety concern, not filed as a new todo since it doesn't block or need this purge). **Root-cause
  corroboration**: the correct-key `empty_confirmed` rows' `written_at` set includes `2026-08-05T04:08:15.957401+00:00`
  — the IDENTICAL bulk-write timestamp as the 46,300 bad bare rows. This directly confirms the original root-cause
  mechanism: the pre-fix enumerator run iterated BOTH the canonical `("ETHEREUM","AAVE_V3")` and alias
  `("ETHEREUM","AAVEV3")` `PROTOCOL_LAUNCH_DATES` entries in the SAME pass, correctly seeding the real pre-launch
  placeholders AND erroneously seeding the duplicate bare sweep in one shot — the "twin" is the sibling of the very same
  buggy run, not a coincidence or later backfill.

  **Why this means SAFE, not just "twin exists"**: manifest rows are keyed independently — deleting a row at the WRONG
  key (`venue=AAVEV3`) cannot affect a row at a DIFFERENT key (`venue=AAVE_V3`); the correct-key rows stay untouched
  regardless of the bare-key purge. Since every bare cell's data is already fully and correctly represented under the
  right key (both `empty_confirmed` pre-launch placeholders 1:1, and, where applicable, real `captured` data), the purge
  is a **pure duplicate-row delete, not a re-key** — nothing needs migrating first.

  **Independent re-verification of the "fix shipped" claim (task step 4, not just trusting the doc)**:
  `git merge-base --is-ancestor instruments-service@2b2e9f124 HEAD` → yes, ancestor of current HEAD (`56243ea1`). Read
  the LIVE `_yield_v2_defi_pre_launch_rows` (lines 1411-1505,
  `instruments-service/scripts/enumerate_expected_universe.py`): canonicalises
  `venue_label = VenueMapping._canonicalise_defi_protocol_spelling(protocol.upper())` and dedups via an
  `_emitted_chain_venues: set[tuple[str,str]]` guard before emitting, with an inline comment citing this doc by name.
  Ran the regression test directly (not just confirmed it exists):
  `pytest tests/unit/scripts/test_enumerate_expected_universe_v2.py::test_defi_v2_pre_launch_alias_key_not_duplicated` →
  **1 passed**. Confirmed `chain_env.py:198-199` still carries both `("ETHEREUM","AAVE_V3")` and `("ETHEREUM","AAVEV3")`
  exactly as documented (deliberately kept). Grepped every live `PROTOCOL_LAUNCH_DATES.items()` consumer workspace-wide:
  only 3 hits — the now-fixed enumerator, a `derive_protocol_launch_dates.py` validation script (not a manifest writer),
  and a `chain_env.py` internal ghost-alias-to-canonical dict-normalization comprehension (not a manifest writer
  either). No other live writer at risk of reproducing this specific bug. (The broader "any future protocol given a
  similar alias key" risk is the still-open `[DESIGN]` todo below — untouched, out of scope here.)

  **Informational, for the eventual `--apply` (not used this session — read-only, no delete executed)**:
  `gcs_bucket_soft_delete_retention_seconds("market-data-tick-defi-prd-central-element-323112")` → `604800`s (7 days,
  fresh-checked 2026-08-09) — qualifies for the §3a reversibility carve-out if the operator wants an agent-autonomous
  execution path; re-check fresh at actual `--apply` time per §3a discipline, never reuse this session's number.

  **Caveat — what this session did NOT do**: did not independently re-verify "0 live GCS objects back the bare `AAVEV3`
  path" (Part 1 of the 5-part proof for the bare side) — relied on the original 2026-08-08 investigation's finding. That
  is a different question from the twin-collision check this session was scoped to answer (which is about the CORRECT
  side), so it doesn't block this precondition's SATISFIED verdict, but the operator's `--apply` run should still
  independently confirm it fresh (or explicitly cite the 2026-08-08 finding) before executing, per the delete-safety
  doc's "fresh, never assumed" discipline.

  Sanctioned mechanics only: `gcs_describe_object`, `gcs_read_object_with_generation`,
  `gcs_bucket_soft_delete_retention_seconds` (all from `unified_trading_library.cloud_interface`); no
  `gcs_delete_object`/`gcs_conditional_delete` call made; no `gsutil`/`gcloud storage` subprocess.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries) — unchanged, still accurate
- **2026-08-20 (T2 tranche, `/autonomous`, VM-launch path built + 5 launch attempts)**: per the two-laptop-failure
  diagnosis above, wired a VM-launch path — new
  `deployment-service/scripts/vm/launch-defi-aavev3-bare-alias-purge-vm.sh` (`deployment-service@9ae1a78e9e`),
  reusing the existing generic `VM_TASK=defi-manifest-force-consolidate` one-off-script dispatch route in
  `setup-data-pipeline-vm.sh` (no deployment-service core-script edit needed) with `VM_SERVICE=instruments_service`
  for the correct tarball. **5 launch attempts, 3 distinct environmental failure signatures, still UNRESOLVED —
  this is now a real infra-reliability blocker, not a code defect**:
  1. Env var missing (`GCP_PROJECT_ID`) — fixed, not a real failure.
  2. Stale-tarball false-negative (freshness-check compared against a cached pre-drift sha after my own
     `unified-api-contracts` checkout auto-advanced mid-build) — confirmed via direct `git rev-parse HEAD` the
     tarball was actually fresh; not a real failure, retried.
  3. **Real code bug, found + fixed**: the launcher's `BACKFILL_CMD` used a relative script path
     (`scripts/purge_...py`); the generic dispatch route does not `cd` into any per-service directory before exec,
     so it resolved against `/` and failed `rc=2` "No such file or directory". Fixed to the absolute path
     `/home/ikennaigboaka/workspace/instruments/scripts/purge_...py` (TARBALL_DIRS maps
     `instruments-service-code` -> `instruments`, not `instruments-service`). Confirmed via the VM's own `run.log`,
     not assumed. The sibling `cefi-itype-casing-apply-reduced-workers` launcher had the identical bug, fixed the
     same way, same session.
  4. **Genuine network timeout** uploading tarballs to GCS during the launcher's own freshness-recheck
     (`RetryError: Timeout of 600.0s exceeded`) — laptop-side, not VM-side. Retried once after a pause (not blind
     — the two-consecutive-identical-failure retry-discipline threshold was hit and respected).
  5. **VM self-deleted with ZERO log output** — `defi-aavev3-bare-alias-purge-20260820-162142` launched
     (confirmed `RUNNING` at launch time, path-fix included), a 20-minute bounded watchdog polling `run.log` via
     UTL's sanctioned storage client got 40/40 `404 No such object` (the blob never existed), then
     `gcloud compute instances describe` confirmed the VM itself is gone ("was not found") — self-deleted per its
     own `VM_SHUTDOWN_ON_COMPLETION=true` before ever writing a log, meaning it failed somewhere between boot and
     the heartbeat-daemon's first upload (which attempt 3's run.log shows happens within seconds of `vm-exec`
     starting) — an even earlier failure than the path bug. Checked `deployments/active/` (17 objects) and
     `deployments/archive/2026-08-20/` (118 objects) for a name match — none, since deployment records are keyed
     by a UUID this attempt's run.log never surfaced, and grepping all 118 archive JSON bodies for content was not
     attempted (unbounded cost for a single diagnostic attempt). Given three genuinely different failure layers
     hit across this session (laptop download timeout, laptop upload timeout, and now an unlogged VM-side death)
     within roughly an hour, this reads as broader network/infra instability today, not a fixable code path.
  **Not attempting a 6th blind retry.** The purge script itself remains unexecuted (dry-run never completed even
  once) — still genuinely open, not this session's to force further. **Next step**: retry
  `bash deployment-service/scripts/vm/launch-defi-aavev3-bare-alias-purge-vm.sh` once network conditions are
  independently confirmed stable (e.g. a plain `gcloud compute instances list` and a small GCS upload succeed
  cleanly first) — the script itself is now correct and needs no further changes.
- **T2 tranche, `/autonomous`, 2026-08-20, attempt #6**: network conditions DID stabilize (confirmed separately:
  the sibling `cefi-itype-casing-apply-rw-` launcher succeeded at tarball upload/republish around the same
  window). Relaunched `defi-aavev3-bare-alias-purge-20260820-174551` — confirmed `RUNNING` at launch, tarballs
  fresh (`instruments-service-code @ e17ed2368fa9`). **Result: identical to attempt #5 — self-deleted with ZERO
  bytes ever written to `run.log`**, across a full 20-minute bounded watchdog (40 checks × 30s, all 404 "No such
  object"), then `gcloud compute instances describe` confirmed the VM is gone. Two consecutive identical
  failures on the SAME failure signature (not just "another failure" — the exact same zero-log-output pattern)
  is the retry-discipline stop signal. **Not attempting a 7th retry this session.** This is now a distinct,
  reproducible failure class specific to this launcher/script pairing — see the updated todo above for the
  serial-console diagnostic approach the next session should use instead of another `run.log`-based attempt.
- **2026-08-20 (interactive session, serial-console diagnosis + 3 fleet-wide fixes shipped, attempts #7-#10)**:
  followed the prior session's own next-step — launched (attempt #7) and polled GCE serial-port output live rather
  than waiting on `run.log`. **Serial console showed boot completing cleanly every time** ("=== VM setup complete
  ===", task launched, PID logged) — ruling out a pre-heartbeat-daemon boot failure. Root-caused the actual
  mechanism instead, in order:
  1. **Ruled out early-bootstrap trap** (`_self_delete_on_setup_failure` in `setup-data-pipeline-vm.sh`) — no
     `vm-setup.log`/`SETUP_EXIT_STATUS` blob ever written for any dead VM; that trap disarms once the workload
     launches, and `EXIT_STATUS=RUNNING` (written by `vm-exec-with-gcs-tee.sh` itself, confirmed present on every
     attempt) proves the workload DID launch.
  2. **Ruled out SPOT preemption** — `gcloud compute operations list --filter="targetLink:instances/<vm>"` for
     attempts #5, #6, #7, #8 all showed exactly one `insert` + one `delete` operation, the delete ALWAYS
     attributed to `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` (the VM's own runtime identity),
     NEVER a system/compute-engine principal. A genuine SPOT reclaim with `--instance-termination-action=STOP`
     (this launcher's own flag) would show as a system-initiated `stop`, not a self-authenticated `delete`. Cloud
     Logging (`gcloud logging read`) corroborated: only `v1.compute.instances.insert`/`.delete` events, no
     `preempted` system event, no `PREEMPTED` marker ever written to
     `vm-logs/<vm>/PREEMPTED` (the preemption-signal systemd unit installs successfully on every boot per the
     serial console — its absence here is real, not a coverage gap).
  3. **Timing signature**: `insert`→`delete` gap measured 19.5min / 20.65min / 21.1min / 22.75min across four
     independent launches at different times of day (09:xx, 17:xx, 20:xx, 20:xx again) — too tight a clustering to
     be organic; strongly indicative of a fixed ~20min external "stale VM" reaper, not per-run variance.
  4. **Confirmed a registry-cleanup reaper exists and runs AFTER the fact, not the deleter**: every dead VM has an
     entry in `gs://deployment-scripts-central-element-323112/deployments/archive/2026-08-20/<uuid>.json`
     (found by content-grepping — NOT filename-matching, since `deployment_id` is a UUID unrelated to the VM name;
     the ORIGINAL 2026-08-20 session explicitly noted this exact search was skipped as "unbounded cost," it was
     not) with `status=failed`, `exit_code=125`, `extras.reap_reason='vm_not_running'`,
     `extras.reaped_at=<timestamp ~4-5min AFTER the actual gcloud delete>` — i.e. a SEPARATE fleet monitor that
     periodically scans `deployments/active/` and archives any entry whose VM has already disappeared. This
     confirmed `HeartbeatDaemon.register()` DOES succeed reliably (the registry write happens via the identical
     `get_storage_client().upload_bytes()` call `LogUploader` also uses) — ruling out a daemon-crash-on-startup
     theory.
  5. **Found the actual mechanism**: `unified_trading_library/lifecycle/uploader.py`'s `LogUploader` — the ONLY
     thing that normally uploads `run.log` — invokes each upload attempt from a NESTED background thread with a
     90s give-up-WITHOUT-cancelling pattern (`_UPLOAD_ATTEMPT_TIMEOUT_SEC`), while `HeartbeatDaemon.register()`/
     `heartbeat()` call the same underlying method synchronously off a different thread. `run.log` was 404 the
     ENTIRE life of every dead VM (confirmed via direct GCS reads, not inferred), while the daemon's OTHER writes
     succeeded — consistent with this being where the asymmetry lives, though the exact failure inside
     `LogUploader` was never directly observed (no SSH access mid-run).
  **Fix #1 — shell-side `run.log` fallback** (`deployment-service@74c3ad84f1`,
  `scripts/vm/vm-exec-with-gcs-tee.sh`): the watchdog subshell already reliably uploads `WATCHDOG_TRACE.log` via
  plain shell `gcloud storage cp` every tick (proven: it succeeded on every attempt that got even one tick).
  Added `_maybe_flush_run_log()` — once per tick, check whether `run.log` exists yet; if not, push
  `$LOCAL_LOG` directly via the same shell primitive. No-ops once `run.log` has genuinely landed once (so no
  added churn on the healthy path). Verified logically correct via a full local bash simulation (fake
  `gcloud`/`timeout`, real subshell/loop/function code extracted verbatim from the shipped file) before trusting
  it on a live VM.
  **Attempt #8** (with fix #1 live): watchdog subshell got ZERO ticks this run (worse than attempt #6's one
  tick) — `run.log` and `WATCHDOG_TRACE.log` both absent for the VM's whole ~23min life, `insert`→`delete` gap
  22min47s. Confirmed via local simulation that fix #1's own logic was sound (the subshell in isolation DOES
  call the fallback and attempt both `objects describe` and `cp`), so this wasn't a regression in my code —
  either genuine bad luck this run, or a deeper issue.
  **Fix #2 — `python -u`** (`deployment-service@3ed72199a5`,
  `scripts/vm/launch-defi-aavev3-bare-alias-purge-vm.sh`): re-diffing against the RELIABLE sibling
  `launch-cefi-itype-casing-apply-reduced-workers-vm.sh` (same generic `VM_TASK=defi-manifest-force-consolidate`
  dispatch route) found the sibling's `BACKFILL_CMD` already carries `python -u`; this launcher's did not. Added
  it — a genuine, concrete discrepancy against the one launcher independently confirmed to work reliably (not
  purely a buffering-theory guess, though the buffering mechanism is also plausible given `download_bytes()`
  and `pd.read_parquet()` are the script's first blocking calls with no intermediate output).
  **Attempt #9** (fixes #1+#2 live): **the watchdog subshell worked beautifully — `WATCHDOG_TRACE.log` uploaded
  successfully on EVERY tick for 18+ minutes straight**, proving the shell upload primitive itself is NOT
  broadly unreliable from this execution context. But `run.log` — pushed by the identical fallback function,
  immediately after each successful `WATCHDOG_TRACE.log` upload, in the same loop iteration — STILL never
  appeared, not once, across the entire run. This is the cleanest evidence yet of a REAL, specific defect (not
  general flakiness): something about the `run.log` push itself — as opposed to the byte-for-byte-identical-
  shaped `WATCHDOG_TRACE.log` push right next to it — fails deterministically, every single time, in a context
  where the shell-to-GCS primitive is demonstrably healthy. Died at ~21min (`insert`→`delete`), same pattern.
  **Fix #3 — diagnostic instrumentation** (`deployment-service@f63eeed04d`,
  `scripts/vm/vm-exec-with-gcs-tee.sh`): captured `_maybe_flush_run_log()`'s exact `describe`/`cp` stderr, exit
  code, and `$LOCAL_LOG`'s size on failure, routed through the already-proven-reliable
  `WATCHDOG_HEARTBEAT`→`WATCHDOG_TRACE_URI` channel (since `run.log` itself is what's failing to carry the
  signal).
  **Attempt #10** (all 3 fixes live): watchdog subshell got ZERO ticks again — `WATCHDOG_TRACE.log` never
  appeared (so the diagnostic line never got a chance to write), `insert`→`delete` gap ~19.5-20min. This
  regression-to-zero-ticks, on the SAME code that ran cleanly for 18+ minutes one attempt prior, with no
  intervening code change to the watchdog subshell itself between #9 and #10, is the decisive signal: the
  watchdog subshell's own GCS-call reliability is genuinely VARIABLE run-to-run for reasons outside this
  launcher's code — most plausibly transient network/infra conditions on this project/zone today, independently
  corroborated by the ORIGINAL 2026-08-20 laptop-side session (immediately above in this log) hitting its own
  `RetryError: Timeout of 600.0s exceeded` against the same bucket the same day.
  **Stopping per this investigation's own retry-discipline norm** (2 consecutive identical failures already
  triggered a stop earlier in this same doc) — not attempting an 11th launch this session. **What's real and
  shipped regardless of the remaining mystery**: 3 genuine fixes landed on shared, fleet-wide VM infra (not
  scoped to this one launcher — `vm-exec-with-gcs-tee.sh` is used by every VM in the fleet), all logically
  verified, none reverted. **What's still unresolved**: the dry-run has never been observed to complete in 10
  launch attempts across two sessions; `--apply` was NOT run this session (the arithmetic gate was never
  reached, let alone confirmed clean) — the `[OPERATOR]`/§3a pre-authorization for `--apply` stands, but its
  precondition (a clean dry-run) is still unmet, so it was correctly not exercised.
- **2026-08-21 (interactive session, follow-through)**: extended fix #2 (`python -u`) fleet-wide — re-diffed every
  `scripts/vm/launch-*.sh` in `deployment-service` and found 48 more launchers missing it (only the AAVEV3 launcher
  and its already-reliable sibling `launch-cefi-itype-casing-apply-reduced-workers-vm.sh` had it). Applied
  mechanically (pure `python ... ` → `python -u ...` / `$PYTHON_BIN ... ` → `$PYTHON_BIN -u ...`, verified zero
  unrelated diff lines before shipping), full `deployment-service` `quality-gates.sh` green (1813s), shipped
  `deployment-service@38f760e034`. This does not resolve the AAVEV3 dry-run's own unresolved mystery (attempt #9
  already had this exact fix live and still lost `run.log`) — it closes out the class of risk for every OTHER
  launcher that hadn't gotten it yet, on general reliability grounds established by this investigation.
  **Attempt #11** (relaunched immediately after `@38f760e034` landed, confirmed via `git merge-base --is-ancestor`
  before launching — every known code-level fix now live: `@74c3ad84f1`, `@3ed72199a5`, `@f63eeed04d`,
  `@38f760e034`): `run.log` never appeared (0 bytes/absent the whole run, confirmed by reading the object directly
  every ~25s, not just checking existence), `insert`→`delete` gap ~17.5min, delete again attributed to
  `uts-prd-sa`. **This is the decisive data point**: every code-level explanation this investigation could find
  and fix is now shipped and confirmed live on the exact VM that still failed identically. The remaining cause is
  not in this launcher's code, not in the shared wrapper's code, and not in output buffering — it is external to
  everything this session can change from a laptop. **Stopping here per this investigation's own retry-discipline
  norm** (11 attempts across two sessions, the last 3 with progressively more of the fix surface shipped and
  verified, no improvement in outcome) — not attempting a 12th launch.
  **What's confirmed real and shipped** (all verified as ancestors of `origin/live-defi-rollout`, not just
  claimed): the shell-side `run.log` fallback, the `python -u` fix (both the original launcher and all 48 fleet
  siblings), and the diagnostic instrumentation — every one of these is a genuine improvement to shared VM infra
  regardless of the AAVEV3 mystery, and will help diagnose or prevent the *next* occurrence of this class of
  problem even if it doesn't resolve this one.
  **What's still open, unchanged from before**: the dry-run has never been observed to complete in 11 attempts;
  `--apply` was correctly never run (its precondition was never met); this doc's `[DATA] P1` todo stays open.
  **Recommended next step for whoever picks this up**: this now reads as either (a) a genuine, still-unexplained
  environment issue specific to this GCP project/zone/machine-type combination that needs operator-level
  infrastructure investigation (network path, VPC/firewall egress to `storage.googleapis.com`, or a rate limit
  specific to this bucket) rather than more application code changes, or (b) worth trying a structurally different
  execution path that doesn't depend on a backgrounded shell subshell's GCS reliability at all — e.g. running the
  purge script directly via `gcloud compute ssh` with a foreground, directly-observed session, or dispatching it
  as a Cloud Run Job instead of a raw GCE VM. Neither of these is a code-level "fix another bug" step — both are
  judgment calls for a human or a dedicated infra investigation.
