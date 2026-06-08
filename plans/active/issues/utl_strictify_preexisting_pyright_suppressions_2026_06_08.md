---
title:
  "unified-trading-library: strict-ify the ~116 pre-existing pyright/type suppressions (out of scope of the QG-green
  plan)"
created: 2026-06-08
source:
  - plans/active/utl_full_quality_gates_green_2026_06_01.md
  - unified-trading-library (committed HEAD, pre-2026-06-08)
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

While driving `unified-trading-library` to full `quality-gates.sh` green (`utl_full_quality_gates_green_2026_06_01.md`,
shipped @9e97e01b / PR #253), I found a **pre-existing** population of type-suppressions in committed HEAD — a prior
automated pass's templated shortcut — in files this plan did not touch:

- **~52 bare `# pyright: ignore`** (no rule code) with templated rationales ("duck-typed protocol object; method
  verified at runtime by dependency injection", "type mismatch from dynamic dict or external API", "generic function
  return type cannot be statically inferred", …) — e.g. `feature_service_base/metrics.py`, `synthetic/profile.py`,
  `core/error_handling.py`, `core/health_router.py`, `manifest_freshness.py`, `feature_service_base/validity.py`,
  `streaming/parallel_per_symbol_runner.py`, `risk/rule_evaluator.py`, etc.
- **~40 broad `# type: ignore`** (no rule code) — e.g. `service_runtime.py`, `options_cluster_lookup.py`,
  `core/health_router.py`, `feature_service_base/anti_leakage.py`, `risk/family_aggregator.py`,
  `manifest_migrations/migrator.py`, etc.
- **~24 file-level `# pyright: reportX=false` blanket directives** — e.g. `service_runtime.py`,
  `instruments_write_gate.py`, `domain_client/clients/*`, `synthetic/{profile,generator,cli}.py`,
  `features_interface/adapters/{footystats,understat}.py`, `domain/{timestamp,date}_validation.py`,
  `cloud_interface/providers/protocol_impls.py`.

These pre-date the QG-green plan, are NOT required for the gate (the gate passes with them — basedpyright honors them),
and removing them repo-wide is a distinct campaign. The QG-green plan explicitly scoped them OUT (it cleared the
non-suppressed 965-error residual + added zero net-new broad/blanket suppressions).

## Why it matters

UTL is now "strict-clean modulo pre-existing per-line/-file suppressions" — not truly strict. Each blanket/bare
suppression hides whatever drifts behind it (the workspace standard bans `# type: ignore` / `# pyright: ignore` /
blanket downgrades). The honest end-state for a Tier-0 lib is zero suppressions.

## Recommended decision

File as a follow-up **wrapper plan** `utl_strictify_preexisting_pyright_suppressions_<date>.md`
(`parent_epic: plans/epics/infrastructure_master.md`), and clear the suppressions the same way the QG-green plan cleared
the residual: stubs → `cast()`/local `Protocol`s → narrow per-line exact-rule ignores ONLY for genuinely stub-limited
deps. Apply the **gcp.py Protocol pattern** to the boto3/google/fsspec/firestore boundaries; replace bare ignores with
exact-rule ones or proper typing. Ratchet `CODEX_MAX_VIOLATIONS` down to 0 once clear. NOT a blocker for the May-23
critical path — schedule behind it.
