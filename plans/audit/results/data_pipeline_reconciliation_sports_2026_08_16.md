---
doc_type: audit-result
title: "Sports data-pipeline reconciliation — 2026-08-16 (Tier 1 only, bounded)"
summary: "Bounded Tier-1 canonicalisation check for sports raw-tick (MTDS) + reference (IS) prod buckets — bucket
  resolution/reachability, manifest freshness, and a 60-object oracle sample. NOT a full four-surface campaign — see
  Coverage gaps."
status: pass
nature: record
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-api-contracts]
scope: [engineer]
tags: [reconciliation, canonicalisation, sports, audit]
related: [/plans/active/issues/sports_honest_coverage_gap_closure_2026_08_14.md]
created: 2026-08-16
last_updated: 2026-08-16
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
audited_scope: "sports asset_group, raw-tick layer, Tier-1 only (bucket resolution/reachability, manifest freshness, 60-object oracle sample) -- not the full four-surface campaign"
date: 2026-08-16
auditor: interactive-session
parent_epic: sports_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
---

# Sports data-pipeline reconciliation — 2026-08-16

**Scope actually run: Tier 1 only, interactive/bounded** (per `/data-pipeline-reconciliation` § 7) — not the full
`(asset_group × layer)` campaign, not Tier-2 VM-based 100% validation. This is a spot-check, not a completeness proof.
`--layer candles` was NOT run this pass.

## Bucket paths (Phase 0a/0b)

| Bucket kind        | Resolved name                                              | Reachable |
| ------------------- | ----------------------------------------------------------- | --------- |
| market-data (raw-tick) | `market-data-tick-sports-prd-central-element-323112`     | ✅ Yes |
| instruments-store (reference) | `instruments-store-sports-prd-central-element-323112` | ✅ Yes |

Both resolved via `resolve_bucket_name(...)` (UTL), never inline `gs://`.

## Manifest freshness / lock state (Phase 0d)

| Bucket | last_run_at | verdict | shards_scanned | error_reason |
| --- | --- | --- | --- | --- |
| market-data-tick-sports | 2026-08-16T19:51:33Z | `produced` | 4 | — |
| instruments-store-sports | 2026-08-16T19:51:49Z | `empty` (`no_op`) | 0 | `locked` |

**Note**: the instruments-store consolidator's most recent run bailed with `error_reason=locked` — this coincides
exactly with this session's own concurrent ad-hoc SFI CLI writes (which log
`ManifestConsolidator: clearing stale lock ... age>TTL`) hitting the same bucket. Treated as **transient, caused by
this session's own activity**, not a standing health finding — but per § 2d this makes any surface-3 count read from
the reference-bucket manifest during this window a **lower bound**, and it should be re-checked once no concurrent
writer is active.

## Phase 1 — oracle sample (Surface 1, raw-tick only)

Sampled 60 objects under `raw_tick_data/` in the market-data-tick-sports bucket, ran UAC's
`canonical_path_violations()` (the machine oracle — never re-implemented) against each:

**Result: 0/60 violations.** Every sampled raw-tick object is structurally canonical.

This is a **Tier-1 sample, not a full-corpus claim** — no Tier-2 VM campaign was launched this pass. Per the skill's
per-AG hazard table, sports raw-tick uses the standard `asset_group=sports`-keyed grammar and IS oracle-covered (unlike
the reference bucket).

## Reference bucket (instruments-store-sports) — observation, not a verdict

A shallow listing under `sports_reference/` surfaced two non-canonical-looking prefixes:

- `sports_reference/_legacy_archive/by_date/day=all/entity={teams,venues}/...`
- `sports_reference/_purge_backups/2026_07_24_league_fold*/...`

Both are self-evidently **named, dated backup/archive artifacts from a documented prior operation** (the 2026-07-24
league-fold migration), not stray orphans — but this run did **not** cross-check them against
`/codex/02-data/non-canonical-path-inventory.md` to confirm they're already registered. **Not asserting a finding
here** — flagging as an open cross-check rather than guessing either way.

This bucket's tree (`entity=` axis, no `asset_group=` key) is oracle-EXEMPT per the skill's sports hazard note — no
oracle sample was attempted against it this pass.

## Coverage gaps (explicitly declared, not omitted)

- **No Tier-2 VM-based 100% id/schema validation** run this pass (§ 7) — only the 60-object Tier-1 oracle sample above.
- **No distinct-value census** (§ 3f) run — axis vocabulary (venue/data_type/instrument_type spellings) not
  cross-checked against the canonical enum this pass.
- **`--layer candles`** not audited this pass (sports MDPS candle estate under `processed_candles/`/`processed/`).
- **Non-canonical-path-inventory cross-check** for the two `sports_reference/` prefixes above not completed.
- **Delete-suggestion sweep (Phase 2 / § 4a-4b)** not run — no deletes suggested, none evaluated.
- The **odds_api casing/backfill situation** is tracked separately and in much greater depth in
  `/plans/active/issues/sports_honest_coverage_gap_closure_2026_08_14.md` (root-caused 2026-08-16: a stale
  admission-hold, not a canonicalisation defect) — not re-derived here.

## Verdict

**Sports raw-tick (MTDS): no canonicalisation defects found in this bounded sample (0/60).** Not sufficient to claim
100% — a full campaign (Tier-2 VM pass + census + candle layer + reference-bucket register cross-check) is still
outstanding and should be scheduled as a follow-up, not assumed clean by extrapolation from this sample.

## Progress Log

- **2026-08-16 (interactive /autonomous session)**: bounded Tier-1 pass — bucket resolution, reachability, manifest
  freshness, 60-object oracle sample. No findings requiring an issue doc; coverage gaps declared above for a future
  fuller pass.
