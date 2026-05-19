---
title: "bucket_name_ssot residual drift after 2026-05-18 workspace-wide grep audit (slot 10)"
created: 2026-05-18
author: harsh-slot-10 (R-006 backlog item)
source:
  - plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md (Done-def #6, line ~527; "2026-05-18 (slot 10) — workspace-wide grep audit" section)
  - unified-trading-pm/scripts/quality_gates/check_inline_bucket_uri.py (QG STEP 5.69)
  - unified-trading-pm/scripts/quality_gates/inline_bucket_uri_baseline.yaml
severity: P1 (Done-def #6 gate; not freeze-blocking)
locked_by: live-defi-rollout
locked_since: 2026-05-18
---

## What I found

Re-ran the workspace-wide grep audit for the `bucket_name_ssot_canonicalisation_2026_05_10.md` Done-def #6 zero-drift
verification. **Drift NOT yet at zero** across the three pattern families inspected by the plan:

### (a) Inline `gs://` / `s3://` f-string URI builders in service source (QG STEP 5.69 scope)

8 repos FAIL their `count: 0` baseline. Total **65 sites**:

| Repo                                | Sites | Notes                                                                                                                                                                                                           |
| ----------------------------------- | ----: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `deployment-api`                    |    28 | **REGRESSION vs 2026-05-11** — was lowered to 0 @`297b406`; 28 new f-string URI composers landed since                                                                                                          |
| `execution-service`                 |    16 | Down from 33 at 2026-05-11; most are multi-line f-string concatenations with `# noqa: gs-uri` marker on the gs:// continuation line (checker false-positive — AST records JoinedStr lineno at the opening line) |
| `batch-live-reconciliation-service` |     7 | All error-message URI composers in `stage0_*.py`; need `# noqa: gs-uri` markers OR full migration to `resolve_bucket_uri`                                                                                       |
| `new-sports-batting-services`       |     7 | External `footballbets` repo — NOT in workspace baseline yaml; out-of-scope                                                                                                                                     |
| `unified-trading-system-ui`         |     4 | `context/api-contracts/...` mirror (UAC AST sync target) — not edited directly                                                                                                                                  |
| `unified-trading-library`           |     1 | `bq_catalog.py:49` — multi-line DDL f-string with noqa on gs:// continuation line                                                                                                                               |
| `instruments-service`               |     1 | `sports_dependency.py:100` — ✅ FIXED 2026-05-19 (slot 10): noqa moved to opener line — instruments-service@18b5ee6                                                                                              |
| `orchastrator`                      |     1 | `server/gcs_sync.py:97` — orchestrator local-state upload; not in baseline yaml                                                                                                                                 |

Full per-site listing with file:line refs is embedded in the plan body under § "2026-05-18 (slot 10) — workspace-wide
grep audit for Done-def #6 zero-drift verification".

### (b) Inline `"bucket_template": "..."` string-template fields (L2-tail drift)

**84 hits across 9 repos** — unchanged from existing audit table; DEFERRED-AFTER code_freeze Phase 2.6 or
`BaseDependencyChecker` migration per Done-def #3.

### (c) Legacy `get_bucket_name(...)` + `BUCKET_PREFIXES` consumers (L3 drift)

**89 `get_bucket_name(` hits across 12 repos** + 9 `BUCKET_PREFIXES` hits across 6 repos — DEFERRED-AFTER code_freeze
Phase 2.6 step 2.6.4 (delegate-flip during write-pause) per Done-def #3.

## Why it matters

- The `bucket_name_ssot_canonicalisation_2026_05_10.md` `[AGENT] P1` checkbox at line ~527 cannot be flipped until all
  three patterns reach zero (or carry documented `# noqa: gs-uri` markers + ratcheted baseline counts).
- Pattern (b) + (c) are tracked DEFERRED with named successors in code_freeze Phase 2.6 — expected and on-plan.
- Pattern (a) has a **NEW finding**: deployment-api regressed from 0 → 28 since 2026-05-11. This wasn't on the existing
  PARTIAL audit table and represents drift growth between 2026-05-11 and 2026-05-18. Most of the new hits are in
  `data_status_drilldown.py` (15 sites) + `shard_detail.py` (3 sites) + `routes/*_launch.py` (6 sites); the pattern is
  URI composition from an already-resolved `bucket` var (Category B per the existing taxonomy).
- The deployment-api regression is a **process gap**, not a correctness gap — the routes use already-resolved bucket
  names so the gs:// URIs reach the right buckets at runtime; what's missing is the `# noqa: gs-uri` annotation +
  baseline ratchet hygiene.

## Recommended decision

Three follow-up items, **not freeze-gate-blocking**, suitable for slot pickup in the next 2026-05-19 / 05-20 cycles or
alongside the code_freeze Phase 2.6 sequencing umbrella:

### Follow-up #1 — deployment-api 28-site noqa hygiene (P1, sub-1-AI-day)

Owner: any slot with deployment-api context (slot 3 already actively shipping deployment-api coverage). Walk the 28
sites in `data_status_drilldown.py`, `shard_detail.py`, `data_status_hierarchical.py`, `data_query_service.py`,
`deploy_missing_launch.py`, and `routes/*_launch.py`. For each: (a) confirm the bucket var is already resolved upstream
via `resolve_bucket_name(...)` (not an inline name template); (b) add a `# noqa: gs-uri — <one-line reason>` marker on
the f-string opener line (collapse multi-line concatenations as needed). Then run
`python3 unified-trading-pm/scripts/quality_gates/check_inline_bucket_uri.py --workspace-root <ws> --update-baseline`
and commit the baseline yaml change. Verify CI green via `quickmerge.sh --agent`.

### Follow-up #2 — execution-service + UTL multi-line f-string concatenation noqa repair (P2, sub-1-AI-day)

Owner: execution-service slot. The 16 execution-service + 1 UTL hits are multi-line f-string concatenations where the
`# noqa: gs-uri` marker already exists on the line containing `gs://` but lands on a continuation line — the QG STEP
5.69 AST-walk reads the JoinedStr's `lineno` (the opener), where there is no marker. Either: (a) move/duplicate the noqa
marker onto the opener line, (b) collapse the multi-line f-string into a single-line literal, or (c) extend
`check_inline_bucket_uri.py` to scan all lines in `range(node.lineno, node.end_lineno + 1)` for the noqa marker (a small
checker enhancement that would also benefit any future multi-line f-strings). Option (c) is the cleanest fix — it
removes a class of false-positives workspace-wide. Then ratchet baselines DOWN.

### Follow-up #3 — `unified-trading-system-ui` UAC mirror + `orchastrator` baseline entries (P3, sub-1-hour)

Owner: any slot. `unified-trading-system-ui/context/api-contracts/` is a sync target of unified-api-contracts (the UAC
mirror); fixing the 4 sites by editing the mirror would just be overwritten on next sync. Either (a) extend the QG STEP
5.69 walker to skip `context/api-contracts/` and `context/internal-contracts/` (they're not service source — they're
build-time artifacts of the AST-mirror sync), or (b) fix upstream in unified-api-contracts and re-sync. `orchastrator`
and `new-sports-batting-services` are not in the baseline yaml — they're either out-of-scope for the workspace SSOT
(footballbets is an external repo with its own buckets, orchastrator is operator-tooling) or they need a baseline yaml
entry. Recommend (a) extend the walker exclusion list and (b) add explicit `count: 1` baselines for `orchastrator` if we
want the gate to catch future regressions.

### Follow-up #4 (deferred, not in scope of slot 10)

Patterns (b) + (c) stay DEFERRED-AFTER code_freeze Phase 2.6 per the existing Done-def #3 (= step 2.6.4) — that's the
Phase-2.6 owner's done-def, not a new follow-up.

## Cross-links

- Plan: `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md` § "2026-05-18 (slot 10) — workspace-wide grep
  audit" — full per-site listing
- Baseline: `unified-trading-pm/scripts/quality_gates/inline_bucket_uri_baseline.yaml` — current counts at 0 for all
  service-source repos (the gate FAILs the 8 listed above)
- Checker: `unified-trading-pm/scripts/quality_gates/check_inline_bucket_uri.py` — QG STEP 5.69 AST-walk; see
  `_count_inline_uris_regex()` v1 fallback + `_fstring_has_cloud_uri()` for the false-positive case described in
  Follow-up #2
- Sequencing umbrella: `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` (Phase 2.6 owns Done-def
  #3 + Pattern (b)/(c) flips)
