---
doc_type: issue
title: PACIFICA-SOLANA canonical-rename mechanism — correcting a wrong root-cause conclusion
summary: >-
  pacifica_solana_canonical_mechanism_unconfirmed_2026_08_15.md (archived, resolved) concluded the 787-object
  PACIFICA-SOLANA canonical rename + manifest backfill was an ordinary capture/backfill CLI re-run against the
  standard canonical-by-default writer, "no new script, hence no commit in either repo". That conclusion was reached
  without knowledge of the actual migration tooling — a purpose-built, delete-safety-protocol-compliant script this
  session's operator had already dispatched and executed. This issue corrects the record with first-hand evidence.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer]
assigned_vm: NA
execution_scope: local-only
tags: [defi, canonicalization, pacifica, data-provenance, correction]
priority: P2
source: pacifica_solana_perp_reintegration_2026_08_14_pre_compact_audit_2026_08_16
parent_epic: defi_master
related:
  [
    /plans/archive/issues/pacifica_solana_canonical_mechanism_unconfirmed_2026_08_15.md,
    /plans/archive/2026_08/pacifica_solana_ao_dispatch_2026_08_15.md,
    /plans/active/pacifica_solana_perp_reintegration_2026_08_14.md,
  ]
created: 2026-08-16
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope: [/plans/active/pacifica_solana_perp_reintegration_2026_08_14.md]
---

# PACIFICA-SOLANA canonical-rename mechanism — correction

## What I found

During this session's `/pre-compact` audit (fast-forwarding `unified-trading-pm` and reviewing what other
sessions/AO workers had landed on the same plan since), I found that
`pacifica_solana_canonical_mechanism_unconfirmed_2026_08_15.md` (archived, `status: resolved`) had reached a wrong
conclusion: it attributed the 787 `PACIFICA-SOLANA` raw-tick objects' canonical rename + 787 manifest rows to "an
ordinary capture/backfill CLI re-run... issued directly against the existing, already-canonical-by-default writer (no
new script, hence no commit in either repo)". That doc's own evidence (GCS blob `last_modified` metadata clustering
into a single ~16.5-minute window, 2026-08-15T14:47:40Z-15:04:12Z, strictly monotonic in `day=` order) was measured
correctly — but the investigating worker did not know that this session had already written and executed a
purpose-built migration script for exactly this venue, because that script had not yet been committed to either repo
at the time their `git log --grep=pacifica` check ran.

## The true mechanism

This session dispatched an agent to write and execute
`market-tick-data-service/scripts/migrate_pacifica_quarantine_canonical_2026_08_15.py` — a delete-safety-protocol-
compliant migration script (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) with distinct `--copy` /
`--verify-copies` / `--backfill-manifest` / `--delete` / `--verify-post-delete` stages, each object gated by a
canonical-twin-must-resolve-first check and a fresh §3a soft-delete-retention check immediately before delete. I
personally verified this first-hand: read the script's full source, monitored its execution stage-by-stage via
`ps aux`, and independently re-confirmed the result after completion via direct GCS + manifest queries (787/787
objects canonical, 787 matching manifest rows, matching the superseded doc's own independently-measured count). The
timing signature the superseded doc measured (one sequential day-ordered rewrite run) is fully consistent with this
script's single execution — the measurement was right, only the attributed cause was wrong.

## Why the original investigation missed it

The superseded doc's `git log --since="2026-08-15 07:00" --all -i --grep=pacifica` check in both repos returned zero
commits at the time it ran. That check is accurate for what had landed in git by that point — but the migration
script itself was written and executed by this session's dispatched agent and had not yet been committed (it remained
untracked in the local `market-tick-data-service` checkout, blocked from shipping by an unrelated, live, concurrent
cross-session fleet rollout touching `.gitleaks.toml` / `.pre-commit-config.yaml` in that same repo — see this
session's Deferred work below). A commit-log check is only as good as what has actually landed; an untracked,
already-executed script is invisible to it.

## What was corrected

- `unified_api_contracts/canonical/quarantine.py`'s `QUARANTINE_REGISTRY["PACIFICA-SOLANA"]` `reason` field —
  replaced the "MECHANISM CONFIRMED" note with a "MECHANISM CORRECTED" note citing the true script and this issue
  doc. — `unified-api-contracts@<pending, see Progress Log>`.
- `market-tick-data-service/scripts/reconcile_pacifica_quarantine_2026_08_15.py`'s docstring "MECHANISM NOTE" section
  carries the same wrong claim — **not yet corrected**, blocked by the same live cross-session rollout noted above.
  Tracked as the open todo below.

- [x] ✅ [DATA] P2. Correct `unified_api_contracts/canonical/quarantine.py`'s `QUARANTINE_REGISTRY["PACIFICA-SOLANA"]`
      mechanism claim with the true root cause (repos: unified-api-contracts). See Progress Log for the shipped SHA.
- [ ] [DATA] P3. Correct `market-tick-data-service/scripts/reconcile_pacifica_quarantine_2026_08_15.py`'s docstring
      "MECHANISM NOTE (2026-08-16...)" section with the same correction, once the repo's live cross-session
      `.gitleaks.toml`/`.pre-commit-config.yaml` rollout clears (repo: market-tick-data-service).
- [ ] [SCRIPT] P3. Ship the migration script itself,
      `market-tick-data-service/scripts/migrate_pacifica_quarantine_canonical_2026_08_15.py` (currently untracked,
      already executed against prod, quality-gates.sh confirmed green before the repo went dirty) — same blocker as
      above (repo: market-tick-data-service).

## Progress Log

- **2026-08-16**: filed this correction after discovering the wrong mechanism attribution during `/pre-compact`'s
  Step-1 audit. Shipped the `quarantine.py` fix via quickmerge — see the `unified-api-contracts` repo's git log for
  the landed SHA (not restated here to avoid a stale-sha rot risk if this doc is read later; grep
  `git log --all --grep="correct PACIFICA-SOLANA mechanism attribution"` in that repo).
