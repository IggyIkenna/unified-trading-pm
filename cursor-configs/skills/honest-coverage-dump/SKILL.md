---
name: honest-coverage-dump
description: >-
  Dump per-shard honest coverage straight from the already-computed daily coverage.json (SSOT:
  /codex/02-data/honest-coverage-model.md) -- this is a DUMP of data we already have, not a measurement campaign. Never
  reads GCS objects directly, never re-derives the expected universe, never recomputes a capture_status: it reuses
  instruments-service's measure_honest_coverage.py output verbatim (the same payload deployment-api's
  /api/data-status/honest-coverage route returns). Reports the 4-state capture ledger (captured, empty_confirmed
  labeled "expected-absent", attempted_failed, expected_unattempted) per shard plus a "not-expected" section for
  tuples outside the Layer-1 expected universe, with the denominator stated on every percentage (B16). Grain is
  whatever coverage.json currently carries -- (venue, data_type) today, (venue, instrument_type, data_type) once that
  axis lands -- auto-detected from the payload every run, never hardcoded, so this re-runs at the finer grain with no
  rebuild. Tuesday deliverable 2 of /plans/active/data_pipeline_completion_2026_08_21.md § "Tuesday dumps". Shares its
  shard-enumeration engine (scripts/shard_universe.py) with the readiness-state-dump skill. Trigger on
  `/honest-coverage-dump`, "dump honest coverage", "how much coverage do we have per shard", "show the four capture
  states", "what's our coverage denominator", "re-run the coverage dump at the new grain".
---

# honest-coverage-dump

Prints per-shard coverage read straight from the already-computed daily `coverage.json` -- the Tuesday deliverable 2
in `/plans/active/data_pipeline_completion_2026_08_21.md` § "Tuesday dumps". **This is a dump of data we already
have.** It never walks GCS objects, never re-derives the expected universe, and never recomputes a `capture_status` --
all of that machinery already exists (`instruments-service/scripts/measure_honest_coverage.py`, the same payload
`deployment-api`'s `/api/data-status/honest-coverage` route serves verbatim). Reimplementing any of it would violate
the task's explicit instruction and would drift from the SSOT the moment that harness changes.

## Run it

**Requires** a Python whose venv has `unified-trading-library` installed (GCS reads go through UTL's
`cloud_interface` only -- a subprocess `gcloud`/`gsutil` call is a hard workspace ban, reads included; it is also
blocked live by `scripts/hooks/block_destructive_commands.py`). `instruments-service`'s venv is the natural choice --
it owns the script that _writes_ this same `coverage.json`:

```bash
cd instruments-service && .venv/bin/python3 \
    ../unified-trading-pm/cursor-configs/skills/honest-coverage-dump/scripts/dump_coverage.py
```

```bash
python dump_coverage.py                              # latest date, all asset_groups, summary view
python dump_coverage.py --verbose                     # full per-shard table + stray/hole listings
python dump_coverage.py --date 2026-08-17
python dump_coverage.py --asset-group cefi --venue OKX-FUTURES --verbose
python dump_coverage.py --json                        # machine-readable, for a downstream consumer or a diff
python dump_coverage.py --project my-other-project     # override the default GCP project
```

## What it reports

- **The 4-state capture ledger**, per shard, in the SSOT's own vocabulary
  (`/codex/02-data/honest-coverage-model.md` § Layer 2): `captured`, `empty_confirmed`, `attempted_failed`,
  `expected_unattempted`. Displayed under labels matching the Tuesday task's own wording (B16): `captured`,
  `expected-absent` (= `empty_confirmed`), `attempted-failed`, `expected-unattempted`.
- **Why `attempted_failed` is not folded into "expected-absent"**: B16's prose names four states and its wording
  reads as if it folds a real attempted-and-failed shard into "expected-absent" by omission. This dump does not do
  that — a genuine capture failure is a distinct, actionable state from a legitimate typed absence, and collapsing
  the two would itself be the kind of measurement dishonesty this whole model exists to prevent. All four real
  `CaptureStatus` fields are reported, always.
- **"not-expected"** — B16's fourth named state: tuples entirely OUTSIDE the Layer-1 expected universe (a venue that
  cannot produce a data_type, out-of-MVP-scope, a bundle leaf rolled into its parent). These never appear as a
  manifest row under any `capture_status` and are always excluded from every denominator below, per the
  symmetric-inclusion invariant. Reported as its own section, sourced from `coverage.json`'s `layer_1.stray_tuples`.
  Real Layer-1 holes (`missing_tuples` — EXPECTED but never enumerated, a genuine gap) are reported alongside but kept
  distinct: a legitimate absence is never a Layer-1 hole, and a hole is never a legitimate absence.
- **Every percentage states its denominator** (B16): `reachable_coverage_pct = captured / (captured +
attempted_failed + expected_unattempted)` and `all_shards_coverage_pct` (which also includes `expected_unattempted` +
  `empty_confirmed`... — see the SSOT formula) are both printed with their raw denominator alongside, never bare.

## Grain — no hardcoding, no rebuild

`coverage.json`'s schema is additive (`schema_version: 2`) and already ships both `by_venue_data_type` (the
(venue, data_type) grain the registry supports today) and `by_venue_instrument_type_data_type` (the
(venue, instrument_type, data_type) grain that lands once the `instrument_type` axis is added to
`VenueCapabilityRecord` — see `/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md`). This dump
inspects which one the payload actually has non-empty data in (`shard_universe.detect_grain()`) and reads that one --
never a flag, never an assumption. **Verified live 2026-08-17: the payload already carries populated
`by_venue_instrument_type_data_type` data** (3,960 shards at that grain) — the manifest's own `instrument_type`
writer-grain column has existed for a while (see `/codex/02-data/availability-manifest-and-data-status.md`), so
Layer-2's 3-tuple projection is already real even though the _declared-capability_ side
(`VenueCapabilityRecord` gaining the axis, which drives Layer-1's EXPECTED-side matching) has not landed yet. Re-run
this dump after that lands and diff against today's output — no code change either way.

## Reuse points (what this does NOT reimplement)

- The 4-state ledger, the reachable/all-shards coverage formulas, and the Layer-1 EXPECTED-universe computation are
  all instruments-service's `measure_honest_coverage.py` output, read verbatim.
- The grain, the carve-out rules (venue-cannot-produce / out-of-MVP / bundle-rollup), and the symmetric-inclusion
  invariant are the SSOT's, not re-derived here.
- `scripts/shard_universe.py` is the single shared engine — `readiness-state-dump` imports it too (via a `sys.path`
  insertion pointing at this skill's `scripts/` directory), so both skills read `coverage.json` through the exact
  same code path and never disagree about grain or shard identity.

## Guardrails

Read-only. Never writes GCS, never mutates the manifest, never triggers a re-measurement. If `coverage.json` cannot
be read (auth, missing date, malformed JSON), it prints a clear error and exits non-zero — it never fabricates a
payload to keep going.
