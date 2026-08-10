---
doc_type: issue
title: >-
  KAMINO_LENDING venue-naming-drift root-caused + code fixed (2 handlers) — live GCS/manifest remediation NOT verified,
  the ~1GB availability_index.parquet download reproducibly stalls locally
summary: >-
  Operator/dashboard flagged `KAMINO_LENDING` as a non-canonical `venue` in the DeFi distinct-values panel (bare
  `KAMINO` is canonical, not flagged) — tracked as item 7 in
  `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`. Root-caused via direct code read (not the live panel,
  which this session could not reach — see below): `market-tick-data-service`'s `lending_indices_handler.py` and
  `risk_params_handler.py` both iterate Solana lending protocols (`SOLANA_LENDING_PROTOCOLS = {"kamino_lending",
  "solend", "marginfi"}`, `_solana_defi_fetch.py`) and pass the raw dispatch key straight through as `venue=protocol` to
  every manifest-recorder call
  (`record_captured`/`record_zero_rows`/`record_empty`/`record_catalog_unavailable`/`record_shard_failure`) AND to
  `write_defi_rows` (which drives the actual GCS partition path, `_normalize_venue()` only uppercases, does not
  canonicalise). `solend`/`marginfi`'s dispatch key already equals their UAC-registered canonical venue, so they are
  unaffected; only `kamino_lending` diverges from UAC's registered `KAMINO`/`KAMINO-SOLANA` (confirmed via
  `unified_api_contracts/registry/defi_venues.py:339` + `capability_declarations/_defi.py:789-790`) — the SAME venue
  Kamino's AMM/vault (POOL) captures already use correctly (`solana_defi_handler.py`'s own `_SOLANA_PROTOCOL_VENUES`
  dict already maps `"kamino_lending": "KAMINO"` for THAT handler — proving the project's own established correct
  pattern, which the two OLDER handlers above never picked up). Fixed going-forward: `market-tick-data-service@<fill in
  at ship time>` adds a shared `canonical_lending_venue()` resolver to `_lending_grain.py` (mirroring
  `solana_defi_handler.py`'s precedent) and routes all 11 `venue=protocol` call sites across both handlers through it.
  **What is NOT verified**: whether the LIVE manifest currently carries stale `venue=KAMINO_LENDING` rows needing a
  historical fold (the GMX-style remediation) — every attempt to read the DeFi `_index/availability_index.parquet`
  (directly, and via `read_availability_index(bucket, columns=[...], filters=[...])`, the SAME column-pruned +
  row-group-predicate-pushdown reader deployment-api's axis-value-census endpoint uses) reproducibly stalled with zero
  output past 100s+, matching the EXACT failure class `defi_gmx_venue_removal_2026_07_25.md`'s 2026-07-25 Progress Log
  already documented for this same ~1GB object on this operator's connection (a deterministic
  stall/`ChunkedEncodingError`, not flakiness — that entry's fix was running the read from a same-zone VM). Narrower,
  cheaper GCS-listing spot-checks (several representative
  `raw_tick_data/by_date/day=X/pipeline_mode=Y/asset_group=defi/venue=` prefixes) found no live
  `KAMINO`/`KAMINO_LENDING` objects under `lending_indices`, but this is inconclusive — a genuinely non-canonical row
  can exist purely as a manifest entry (`record_zero_rows`/`record_catalog_unavailable`, which both KAMINO handlers hit
  routinely, per `_collect_kamino_lending`'s own docstring: "The Kamino Finance v2 reserves API returns 404") without
  ever producing a real GCS object, so an object-listing miss does not rule out a manifest-only drift. Distinct from
  (but adjacent to) the already-RESOLVED
  `defi_kamino_solend_lending_indices_legacy_shape_fabricated_history_2026_07_28.md` migration, which fixed a DIFFERENT
  bug (fabricated timestamps on a historical population that itself used bare `venue=KAMINO`, not `KAMINO_LENDING`) in
  the same lending_indices data family.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags:
  [
    defi,
    kamino,
    solend,
    marginfi,
    venue-naming-drift,
    distinct-values,
    manifest,
    lending-indices,
    risk-params,
    data-correctness,
  ]
related:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md,
    /plans/archive/issues/defi_kamino_solend_lending_indices_legacy_shape_fabricated_history_2026_07_28.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-07"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source:
  [
    "sub-agent dispatch, 2026-08-04, item 7 of defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md
    (KAMINO_LENDING half)",
  ]
context_scope:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    market-tick-data-service/market_tick_data_service/cli/handlers/_lending_grain.py,
    market-tick-data-service/scripts/fold_legacy_composite_venue_objects_2026_07_31.py,
    /plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md,
  ]
---

# KAMINO_LENDING venue-naming-drift — code fixed, live-data remediation unverified

## Context

`unified-trading-pm/plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` item 7 asked: is
`KAMINO_LENDING` a genuine naming-drift duplicate of canonical `KAMINO`, or a legitimately-different registered entity?
Verdict: **genuine drift**, confirmed via UAC registry read (`unified_api_contracts` registers only `"KAMINO"` /
`"KAMINO-SOLANA"` — no `KAMINO_LENDING` entry anywhere) and via direct code read of both handlers that emit it.

## Root cause (confirmed by code read, not live data)

`market_tick_data_service/cli/handlers/_solana_defi_fetch.py`:

```python
SOLANA_LENDING_PROTOCOLS: frozenset[str] = frozenset({"kamino_lending", "solend", "marginfi"})
```

`"kamino_lending"` is an internal dispatch/instrument-type-resolution key (also used to select the DeFiLlama fetch
function, resolve `InstrumentType.SOLANA_LENDING` via `resolve_lending_instrument_type()`, etc.) — it was never meant to
BE the venue string. `lending_indices_handler.py` (`_collect_solana_lending` + `_collect_all_shards`, 5 call sites) and
`risk_params_handler.py` (`_handle_catalog_stale` + `_record_shard_result` + `_collect_one_shard` +
`_write_protocol_chain_rows`, 6 call sites) both passed `venue=protocol` directly to every manifest recorder AND to
`write_defi_rows` (whose own `_normalize_venue()` only uppercases — no canonicalisation). For `solend`/`marginfi` this
is harmless (their dispatch key already equals their UAC-registered venue). For `kamino_lending` it mints a SECOND,
non-canonical venue (`KAMINO_LENDING`) disjoint from the real `KAMINO` venue Kamino's AMM/vault (POOL) captures use.
`solana_defi_handler.py` (Kamino's OTHER, newer capture path) already handles this correctly — its own private
`_SOLANA_PROTOCOL_VENUES` dict maps both `"kamino"` and `"kamino_lending"` dispatch keys to venue `"KAMINO"`. The two
older handlers never picked up that pattern.

## Fix shipped (code, going-forward only)

Added `canonical_lending_venue()` to the shared `_lending_grain.py` sibling module (mirrors `solana_defi_handler.py`'s
precedent), routed all 11 `venue=protocol` call sites across `lending_indices_handler.py` + `risk_params_handler.py`
through it. No-op for every protocol except `kamino_lending` → `kamino`.
`market-tick-data-service@<fill in at ship time — see this doc's Progress Log>`.

## What is NOT resolved — the live-data verification gap

Unlike the sibling GMX finding (where the live `catalog.parquet` was read, confirmed to hold exactly 1 stale row, and
surgically fixed via `promote_catalogue(..., allow_shrink=True)`), **this session could not obtain a live read of the
DeFi availability index to determine whether `venue=KAMINO_LENDING` manifest rows currently exist and, if so, how many /
what `capture_status`.** Every attempt hit the same wall:

1. `unified_trading_library.read_availability_index(bucket, columns=[...], filters=[("venue", "==", "kamino_lending")])`
   — the SAME column-pruned, row-group-predicate-pushdown reader `deployment-api`'s `/data-status/axis-value-census`
   endpoint uses (NOT a naive full download) — ran 100s+ with zero output before being killed, both backgrounded and
   foreground.
2. This matches `defi_gmx_venue_removal_2026_07_25.md`'s 2026-07-25 Progress Log entry EXACTLY: the same ~1GB
   `_index/availability_index.parquet` object deterministically stalls/`ChunkedEncodingError`s on this operator's
   connection (confirmed there at a precise 256 MiB byte offset) — that entry's own fix was to run the read from a
   same-zone VM, not retry locally.
3. Narrower `gcloud storage ls` spot-checks (several representative recent `day=`/`pipeline_mode=` prefixes under
   `raw_tick_data/by_date/`, and `instrument_availability/by_date/` in the instruments-store bucket) found no
   `venue=KAMINO`/`venue=KAMINO_LENDING` GCS objects for the `lending_indices`/`risk_params` data_types — but this is
   INCONCLUSIVE, not a clean negative: both handlers routinely hit `record_zero_rows`/`record_catalog_unavailable` (per
   `_collect_kamino_lending`'s own docstring, the direct Kamino API 404s and the code falls back to DeFiLlama), meaning
   a manifest-only `venue=KAMINO_LENDING` row can exist with ZERO backing GCS object — an object-listing miss does not
   rule that out.

## Recommended next step (needs VM access, not a laptop retry)

Per `/codex/05-infrastructure/vm-launcher-runbook.md`'s heavy-I/O rule (this exact index read already established as one
of the documented heavy-I/O exceptions), run a bounded, column-pruned
`read_availability_index(bucket, columns=["venue","chain","data_type","instrument_type","capture_status"], filters=[("venue","==","kamino_lending")])`
(case variants too) from the same-zone VM class the GMX purge script used, or from the human-planning / AO-orchestrator
VM (both already cloud-hosted, exempt from the heavy-I/O restriction). If it returns rows: apply the SAME fold pattern
this session already validated twice this session (GMX's `promote_catalogue(..., allow_shrink=True)` for a catalogue
row; or `fold_legacy_composite_venue_objects_2026_07_31.py`'s pattern for a manifest-row-and-GCS-object venue rename,
the tool already built + proven this session for the sibling 22-composite-venue fold, item 3 of
`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`) to rewrite any found `KAMINO_LENDING` rows to `KAMINO`.
If it returns zero rows: the code fix alone was sufficient (the panel's `KAMINO_LENDING` observation was likely itself a
manifest-only artifact from a recent zero-rows/catalog-unavailable run, self-healing once the fixed code's next run
supersedes it) — close this doc.

## UPDATE 2026-08-05 (interactive session) — historical fold executed, but see 2026-08-07 re-check below

The live-data verification this doc called for DID happen, in a later session: the availability index read succeeded
(565 rows, 80 GCS objects, 2026-08-01..08-05), `relabel_kamino_lending_venue_2026_08_05.py --apply` relabeled them to
canonical `KAMINO-SOLANA`, then `retire_kamino_lending_legacy_venue_2026_08_05.py --apply` retired all 565 legacy rows.
Verified directly against the freshly-written index: **0 remaining captured `venue=KAMINO_LENDING` rows** as of
2026-08-05. Full detail: `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` item 7's Progress Log
(2026-08-05 entry). The underlying code fix shipped as `market-tick-data-service@bd153821` (this doc's summary above
still has the `<fill in at ship time>` placeholder — now filled in here).

## UPDATE 2026-08-07 (na-eligibility-audit re-check) — code fix NOT yet deployed to `main`, gap may be re-accumulating

Independently verified via `git merge-base --is-ancestor bd153821 origin/main` (market-tick-data-service): **`bd153821`
is on `live-defi-rollout` but NOT yet on `main`** — the fix has not reached production. The 2026-08-05 session's own
Progress Log entry already flagged this exact risk: _"every subsequent day will keep adding rows here until the deploy
actually lands... if the backlog persists past 2026-08-06, another day's worth of rows will need the same retire script
re-run."_ Today (2026-08-07) is past that checkpoint and the re-check was never done — this is the corpus's confirmed
"prose-only remaining work, never checkbox-ified" trap. Converted to a tracked todo below rather than left as a Progress
Log note only. Given the historical fold already shipped + the retire script already exists and is proven idempotent,
this is a genuinely bounded, worker-determinable follow-up (not a design decision) — but it stays `assigned_vm: NA` for
now since the doc otherwise reads as closed and a lone reclassified todo risks getting lost; a future audit pass should
consider extracting it into an AO-dispatch batch once `bd153821` deploys.

## Todos

- [x] ✅ [DATA] P2. **Precondition CLEARED 2026-08-09 (see Progress Log) — the fix reached `main` via `f706456a` on
      2026-08-06T08:29:26Z, not "not yet deployed" as the 2026-08-07 audit believed.** Re-run the bounded, column-pruned
      `read_availability_index(..., filters=[("venue","==","kamino_lending")])` check for any `venue=KAMINO_LENDING`
      rows captured in the now-bounded accumulation window 2026-08-05T17:42Z (last retire run) through 2026-08-06T08:29Z
      (deploy landed) — a ~15h window, not open-ended. If any exist, re-run
      `retire_kamino_lending_legacy_venue_2026_08_05.py --apply` (already-proven, idempotent) to retire them. Done when:
      the check returns zero rows (either because none accumulated, or because the re-run retired them), with the row
      count cited here. — **0 rows, verified 2026-08-09** (see Progress Log entry below).

## Codex SSOTs

- `/codex/02-data/defi-canonical-naming-ssot.md` — venue canonicalisation conventions.
- `/codex/05-infrastructure/vm-launcher-runbook.md` § heavy-I/O rule — why this read belongs on a VM.
- `/codex/02-data/availability-manifest-and-data-status.md` — manifest axis semantics.

## Progress Log

- **2026-08-04 (sub-agent dispatch)**: root-caused + code fix shipped (see summary). Live-data verification attempted,
  blocked by the documented heavy-index-read connection issue (see above) — filed as this doc rather than guess at a
  fold that could not be evidenced.
- **2026-08-05 (interactive session)**: historical fold executed + verified (565 rows, 0 remaining after retire). See
  "UPDATE 2026-08-05" section above.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA, valid (OVERRIDES this run's own Phase-1 classifier draft
  verdict of ARCHIVE). The Phase-1 read found strong evidence the historical remediation completed (cited commit shas
  - an explicit "0 remaining rows" verification + `defi_satellite_ao_dispatch_batch10_2026_08_06.md` bucketing this doc
    as `archivable_now`) and recommended archival. Independent follow-up check before archiving:
    `git merge-base --is-ancestor bd153821 origin/main` in market-tick-data-service — **the fix is NOT yet on `main`**,
    only `live-defi-rollout`. The 2026-08-05 session's own Progress Log already named this exact re-check trigger ("if
    the backlog persists past 2026-08-06...") and it was never re-run. This is a live, currently-unverified
    data-correctness gap (new `venue=KAMINO_LENDING` rows may be accumulating daily in production until the deploy
    lands), not a closed doc — archiving it now would hide real remaining work. Added "UPDATE 2026-08-07" section +
    converted the prose-only re-check note into a tracked `[DATA] P2` todo above (the corpus's confirmed
    prose-only-remaining-work trap). Also flagged: `ag_closeout_audit_defi_parked_2026_08_07.md`'s own Finding 6 on this
    same doc independently reached a more cautious "may auto-resolve, mark for re-check" verdict — my read is the first
    to confirm concretely (via git) that the risk is real and unresolved, not just a stale process artifact. Doc stays
    `assigned_vm: NA`, `status: open`.
- **context-scout 2026-08-07**: populated context_scope (6 entries).
- **stale-check-defi-tranche 2026-08-09**: correction, not a closure — the 2026-08-07 audit's "NOT yet on main" verdict
  was itself a false negative caused by the verification METHOD, not a real deploy gap.
  `git merge-base --is-ancestor bd153821 origin/main` still returns false today (2026-08-09), but that is because
  `ldr-to-main-promote` rewrites commit SHAs on promotion (Option-B direct, non-fast-forward) — checking ancestry by the
  ORIGINAL pre-promotion SHA against `origin/main` is the wrong test for this repo's promotion model. Content-based
  verification
  (`git log origin/main -S canonical_lending_venue -- market_tick_data_service/cli/handlers/_lending_grain.py`) finds
  the fix landed on `main` via `f706456a` ("chore(promote): LDR → main (Option-B direct)"), committed
  **2026-08-06T08:29:26Z** — a full day BEFORE the 2026-08-07 audit ran and concluded the deploy hadn't happened yet.
  `origin/main:market_tick_data_service/cli/handlers/_lending_grain.py` confirmed live-read to contain
  `canonical_lending_venue()` today. **Net effect**: the todo's blocking precondition ("once bd153821 reaches main") has
  been satisfied since 2026-08-06 — two days earlier than the corpus believed. The todo's SECOND half (the actual
  bounded `read_availability_index` re-check for `venue=KAMINO_LENDING` rows accumulated 2026-08-05→deploy-day, and a
  `retire_kamino_lending_legacy_venue_2026_08_05.py --apply` re-run if any are found) is still genuinely NOT done — no
  evidence of that check or script re-run anywhere in the corpus as of this pass — so the todo stays open, just
  re-scoped: the accumulation window to check is now bounded (2026-08-05 17:42 UTC → 2026-08-06 08:29 UTC, ~15h), not
  open-ended. **Process finding for the wider corpus**: any future "has fix X reached main" check in this workspace
  should verify by CONTENT (grep/`-S` pickaxe on `origin/main`) or via the `ci_status` Firestore-SSOT, never by
  `git merge-base --is-ancestor <pre-promotion-sha> origin/main` alone — that check systematically false-negatives under
  the `ldr_main` promotion model and produced this doc's incorrect blocker.
- **na-eligibility-audit 2026-08-09** (tranche=defi): **RECLASSIFY, `assigned_vm: NA -> planning`** (`execution_scope`
  corrected `local-only -> orchestrator-agent`). The sole remaining todo now clears the whole-doc RECLASSIFY bar: the
  precondition that made this ambiguous (has the code fix reached `main`) was resolved by the same-day
  "stale-check-defi-tranche 2026-08-09" entry above (content-verified landed 2026-08-06T08:29:26Z via `f706456a`), and
  what remains is a single bounded, column-pruned `read_availability_index` check over a fixed ~15h window with a stated
  done-when (zero rows, count cited) plus an already-proven idempotent conditional remediation
  (`retire_kamino_lending_legacy_venue_2026_08_05.py --apply` — verified by reading the script: it only flips
  `capture_status` on manifest index rows, snapshots a pre-write backup + `.bak` first, never deletes a GCS object — no
  `[OPERATOR]` gating needed under the delete-safety rule). Conflict-check clear: no active `assigned_vm: planning` doc
  in `parent_epic: manifest_master` claims this remediation; `defi_satellite_ao_dispatch_batch10_2026_08_06.md`'s own
  citation is a stale (2026-08-06) "archivable_now" list entry, not a dispatch;
  `ag_closeout_audit_defi_parked_2026_08_07.md` Finding 6 recommended re-check (not extraction) and is itself superseded
  by the 2026-08-09 precondition-clear above. Companion gated finalize plan authored:
  `/plans/active/defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04_finalize_2026_08_09.md`.
- **worker (slot 17) 2026-08-09**: **todo executed — 0 rows, checkbox flipped.** Ran the bounded, column-pruned
  `read_availability_index(bucket, columns=["venue","date","chain","data_type","instrument_type","capture_status", "attempted_at","written_at"], filters=[("date",">=","2026-08-05")])`
  check (memory-bounded via `run-bounded-analysis.sh --mem-cap 4G`, RSS-poll fallback — this host has no systemd --user
  instance) against `gs://market-data-tick-defi-prd-central-element-323112`. Row-group pushdown on `date>=2026-08-05`
  returned 399,456 rows total; case-insensitive `venue.upper()=="KAMINO_LENDING"` match found exactly **113 rows, all
  `date=2026-08-05`, all already `capture_status=attempted_failed`** (the 2026-08-05 retire run's own output — matches
  that run's cited 565-total/113-per-day population). **Zero rows with `date=2026-08-06`** (the only calendar day the
  15h accumulation window 2026-08-05T17:42Z→2026-08-06T08:29Z could plausibly touch, given the ~00:45 UTC daily
  collection-job cadence documented in `relabel_kamino_lending_venue_2026_08_05.py`) — confirms the writer-side fix was
  already live for that day's run, so nothing new accumulated. **Zero `capture_status=="captured"` rows anywhere in the
  `date>=2026-08-05` slice** (cross-checked precisely against both `attempted_at` and `written_at` timestamps inside the
  exact window bounds too — 0 either way). Done-when condition met (zero rows, count cited) without needing to re-run
  `retire_kamino_lending_legacy_venue_2026_08_05.py --apply` — no remediation was required. Checkbox flipped above; no
  code shipped (this was a read-only verification todo, not a code change).
