---
title: "unified-trading-library full quality-gates.sh is RED on a pre-existing backlog"
created: 2026-06-01
author: ikenna (slot 1)
source:
  - plans/active/manifest_reader_fail_fast_on_stale_fallback_2026_05_28.md (C4 unmet — root cause)
  - plans/active/manifest_consolidator_duckdb_memory_fix_2026_05_26.md (Phase 1 shipped without full QG)
  - unified-trading-library@73209d50 (in-scope violations cleared)
locked_by: live-defi-rollout
---

# unified-trading-library full `quality-gates.sh` is RED on a pre-existing backlog

> ## ✅ ACKED + ARCHIVED 2026-06-01 — owned by a plan now
>
> This backlog (B1–B5) is now owned by
> [`plans/active/utl_full_quality_gates_green_2026_06_01.md`](../utl_full_quality_gates_green_2026_06_01.md)
> (`parent_epic: infrastructure_master`, `assigned_vm: vm-cross-cutting`). Per the issue-doc-lifecycle HARD RULE, an
> issue doc archives immediately once its work is acked into a plan — the wrapper plan is now the tracker; do not
> dual-track here. The B1–B5 detail below is retained as the source breakdown the plan's phases derive from.

## What I found

Running the **full** `bash scripts/quality-gates.sh` in `unified-trading-library` (LDR @ `73209d50`) exits **1**. This
violates the workspace HARD RULE **"Quality Gates Are A Merge Prerequisite"** — UTL has been shipping to
`live-defi-rollout` red because the dirty-dep direct-push path has no remote CI and `quickmerge` was not used.

The failures split into **(A) cleared this session** (introduced by two now-closing plans) and **(B) pre-existing
foreign/config/borderline backlog** that requires a dedicated campaign.

### (A) Cleared @ `73209d50` (in-scope — introduced by Plan 1 / Plan 2)

| Check                       | Site                                                           | Fix                                                             |
| --------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------- |
| bandit B608 ×4              | `manifest_consolidator.py` DuckDB SQL                          | `# nosec B608` (internal temp paths/schema cols, no user input) |
| STEP 5.23 deep UAC import   | `pipeline_mode_resolver.py` ×3                                 | facade `from unified_api_contracts import …`                    |
| os.environ ×3               | `manifest_consolidator.py` (`CONSOLIDATOR_*`)                  | `# noqa: qg-os-environ` (operational tunables)                  |
| empty-string fallback       | `manifest_writer.py` `MANIFEST_FAIL_ON_STALE_FALLBACK`         | `# noqa: qg-empty-fallback` (`""` = feature-off)                |
| imports-inside-functions ×3 | `manifest_consolidator.py` (duckdb/pyarrow/ThreadPoolExecutor) | `# noqa` (deliberate heavy-dep deferral)                        |

### (B) Pre-existing backlog — REMAINS RED (not from the two plans)

| #   | Check                                                                                                                                                  | Scope                                                                                                                                                                                               | Why it's not a quick fix                                                                                                                                                                                            |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B1  | **STEP 5.21** — `reportUnknownMemberType/VariableType/ParameterType/ArgumentType/LambdaType = "none"` in `pyproject.toml` (must be `error` or omitted) | repo config                                                                                                                                                                                         | Flipping to `error` surfaces **962 basedpyright errors** (untyped deps: pandas/duckdb/google-cloud/pyarrow). Needs a ~962-site annotation campaign. Deliberate downgrade (note `reportAny` IS `error`).             |
| B2  | **imports-inside-functions** ×25 (AST-detected)                                                                                                        | `instruments_catalog_reader.py`, `manifest_writer.py`, `point_in_time.py`, `legacy_reason_classifier.py`, `synthetic/cli.py`, `treasury/withdrawal_reconciler.py`, `services/client_worker_base.py` | Mostly **deliberate** deferred imports (heavy deps, circular-import avoidance). Each needs a per-line `# noqa: imports-inside-functions` (or PLC0415) — foreign files.                                              |
| B3  | **Deep unified lib imports**                                                                                                                           | `legacy_reason_classifier.py` ×7 (`unified_api_contracts.registry.*`) + others (`margin_model`, `settler`, `options_cluster_lookup`, `approval_bus`, `understat`, `footystats`)                     | Facade does NOT re-export the registry submodules (`half_day_sessions`/`venue_session_hours`/`chain_env`/`venue_launch_dates`/`generators`). Either add facade exports in UAC or `# noqa: qg-deep-import` per line. |
| B4  | **Function/class/method size**                                                                                                                         | `event_sink.py:110 GcsEventSink.write_event()` = 59L (limit 50)                                                                                                                                     | Foreign file; needs a clean helper-extract.                                                                                                                                                                         |
| B5  | **Test coverage 79.49% < 80%**                                                                                                                         | repo-wide                                                                                                                                                                                           | Borderline (≈0.5% gap); the gate early-exits the run before codex. May be flaky or need a few targeted tests.                                                                                                       |

## Why it matters

- **Blocks `manifest_reader_fail_fast_on_stale_fallback_2026_05_28.md` success criterion C4** (`quality-gates.sh` exits
  0). The plan's _feature_ shipped + is documented + has the 3-case unit test; only the repo-wide green gate is unmet —
  and no single plan owns this backlog.
- UTL is **Tier-0** (every service depends on it). A red UTL QG means none of its consumers can claim a clean cross-repo
  QG either, undermining the "QG is a merge prerequisite" invariant workspace-wide.
- B1 (STEP 5.21) is the dominant blocker: until the 962 unknown-type sites are annotated (or the downgrade is formally
  accepted with a documented exemption), UTL cannot be fully green regardless of the smaller items.

## Recommended decision

1. **Treat B1 (STEP 5.21 / 962 type errors) as its own remediation plan** under `infrastructure_master` or a UTL
   type-hardening epic — it is a multi-day annotation campaign, NOT a same-session fix. Decide explicitly: annotate to
   `error`, or codify a `BLOCKED-OPERATOR-DECISION` exemption for the untyped-dep rules with a documented rationale.
2. **B2/B3 (imports)**: bulk-apply `# noqa: imports-inside-functions` / `# noqa: qg-deep-import` to the deliberate
   deferred imports (non-functional), OR add the missing registry facade exports in UAC so B3 imports become
   facade-clean. Low-risk but touches ~8 foreign files — wants an owner.
3. **B4 (event_sink size)**: small helper-extract in a single commit.
4. **B5 (coverage)**: confirm determinism (re-run); if genuinely <80%, add targeted tests for the lowest-covered
   modules.
5. **Process fix**: route UTL changes through `quickmerge --agent` (which runs the codex gate) rather than dirty-dep
   direct-push, OR wire UTL into a remote `quality-gates-v2` check on `live-defi-rollout` so this debt can't silently
   re-accumulate.

**Until B1–B5 are closed, `manifest_reader_fail_fast`'s C4 stays open and references this issue.** The feature itself is
shipped and verified.
