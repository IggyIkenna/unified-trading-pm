---
doc_type: plan
title: CeFi instrument_type casing residual — re-count fresh, then apply
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 3) — re-verify the
  2,982-row instrument_type casing residual figure from cefi_consolidated_closeout_2026_07_18.md
  line 523 live before applying the canonicalization fix, given how much has landed on this
  branch since that figure was measured.
status: complete
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, canonicalization, casing]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 3, 2026-08-16"
locked_by:
locked_since:
context_scope:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    instruments-service/scripts/canonicalize_cefi_instrument_type_legacy_lowercase_2026_07_16.py,
  ]
resolved_by:
---

> **🟢 ARCHIVED 2026-08-17.** Reviewed + confirmed by [[cefi_casing_residual_ao_dispatch_2026_08_16_finalize]]:
> both cited commits (`market-tick-data-service@07861cf6`, `market-tick-data-service@c07cc70e93`) independently
> verified live on `origin/live-defi-rollout`; the follow-up issue doc's P2 VM-apply todo confirmed genuinely
> `dispatched` in the live AO backlog (not merely filed). Sole todo's done-when ("re-count live; apply if real")
> is honestly satisfied: the residual is real (39,286, not the stale 2,982), the writer regression causing it is
> fixed, and the actual `--apply` run is correctly deferred to a VM (corpus-scale: 166k+ per-VM shard objects,
> 29.9M-row consolidated index — confirmed too large for the shared host) rather than faked as complete. Remaining
> work (the VM apply itself) tracked at `issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`,
> not lost with this archival.

# CeFi instrument_type casing residual — re-count fresh, then apply

## Todos

- [x] ✅ [DATA] P2. Re-count the instrument_type casing residual live against the current catalogue (was 2,982
      non-canonical rows as of `cefi_consolidated_closeout_2026_07_18.md` line 523) — do not trust the cited figure
      without a fresh measurement. If the count still shows a real residual, execute the `--apply` casing fix.
      (repo: market-tick-data-service) — market-tick-data-service@07861cf6. Re-measured live 2026-08-17 (verified
      independently twice): residual is **39,286**, not 2,982 — grew 13x, confirming an ACTIVE writer regression, not
      stale debt. Root cause traced to `partitioned_writer.py::_resolve_instrument_type_column` (lowercases
      `instrument_type` for GCS partition-path construction; that same value leaks into the manifest
      `record_captured` row-key instead of being re-mapped to canonical uppercase for the manifest write). The
      existing `--apply` fix tooling (`scripts/normalize_instrument_type_casing.py`) had 3 separate safety defects
      (over-broad mask that would have mis-touched unrelated non-canonical categories, no collision-dedup against the
      manifest's composite row-key, no backup before the in-place PROD overwrite) — fixed all 3, shipped
      `market-tick-data-service@07861cf6`. The `--apply` run itself was NOT executed in this session: confirmed
      genuinely VM-scale (166,686 per-VM shard objects; even an index-only run against the 29.9M-row consolidated
      index OOM'd on the shared host) — dispatching it before the writer fix lands would also just decay again. Note:
      the `futures_chain`/`options_chain` values also present in `instrument_type` are NOT part of this residual —
      already investigated + ruled intentional-by-design in
      `issues/cefi_enumeration_audit_instrument_type_leakage_and_catalogue_orphans_2026_07_27.md`. Full findings +
      follow-up todos (writer-fix confirmation P1, VM-dispatched apply P2):
      `issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`.

## Progress Log

- **slot-3 2026-08-17 (review)**: independently verified both cited commits live on origin, confirmed the issue
  doc's P1 (writer fix) is done and P2 (VM apply) is genuinely dispatched (not just filed) via the live AO backlog
  — archival gate satisfied. Archived alongside `cefi_casing_residual_ao_dispatch_2026_08_16_finalize.md`. Fixed a
  duplicate `context_scope:` frontmatter key found on this doc (two conflicting entries; kept the fuller one).
  Referrer sweep: annotated the stale 2,982 citation in `cefi_consolidated_closeout_2026_07_18.md`, repointed
  `issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md`'s frontmatter, regenerated
  `INDEX.md`.
- **slot-14 2026-08-17**: re-counted live (independently twice) — residual is 39,286 (13x the cited 2,982), an
  active writer regression not stale debt. Fixed 3 safety defects in the existing `--apply` script
  (`market-tick-data-service@07861cf6`) but did NOT run `--apply` — confirmed VM-scale (166k+ per-VM shard objects,
  30M-row consolidated index OOM'd on this shared host) and the writer bug would just regrow it. Filed
  `issues/cefi_instrument_type_casing_active_writer_regression_2026_08_17.md` with the candidate root cause + 2
  follow-up todos (P1 confirm/fix the writer, P2 VM-dispatched apply). This plan's sole
  todo is done per its own done-when ("re-count live; apply if real" — re-count done, apply correctly deferred to the
  VM-scale follow-up given genuine newly-discovered blockers) — ready for archival once the issue doc's follow-ups are
  triaged/dispatched.
- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 3, operator ruling)**: extracted from
  `cefi_consolidated_closeout_2026_07_18.md`.
