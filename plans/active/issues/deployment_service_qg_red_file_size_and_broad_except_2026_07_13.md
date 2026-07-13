---
doc_type: issue
title: deployment-service quality-gates.sh RED — pre-existing file-size + broad-except ceiling breach blocks all commits
summary:
  quality-gates.sh on deployment-service fails the codex-compliance violation ceiling on a clean live-defi-rollout HEAD
  (a01202d), unrelated to any in-flight diff — data_pipeline_monitors/cli.py is 930 lines (900-line ceiling) and
  cli/utils/manifest_reader.py has 5 undocumented `except Exception` broad-catches. Blocks every commit to this repo
  under the green-tree-before-commit HARD RULE.
status: resolved
nature: notes
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [qg-red, repo-blocker, codex-compliance, file-size, broad-except]
related: []
created: 2026-07-13
parent_epic: infrastructure_master
assigned_vm: planning
resolved_by: deployment-service@534de4b (file-size split), deployment-service@d089f24 (broad-except audit)
source: [defi_morpho_lending_indices_never_wired-002 dispatch, slot-10 infra]
priority: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

Dispatched to close the `[INFRA] P2. Close the VM-launch/GCS-publish race` todo in
`plans/active/issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`. Implemented + tested the fix in
`deployment-service` (`lc_verify_setup_script_freshness` in `scripts/vm/lib/launcher_common.sh`, wired automatically
into `lc_gcloud_create`) and a small adjacent one-line fix (a missing `CLOUD_RUN_JOBS` registry entry for
`deployment-digest`, which itself was pre-existing red but small+clear enough to fix inline). All unit tests pass (2643
passed / 1 skip-irrelevant). But `bash scripts/quality-gates.sh` fails at the codex-compliance aggregation step:

```
❌ Files exceed 900 lines:
  ./deployment_service/data_pipeline_monitors/cli.py: 930 L
⚠️  broad except Exception — document in QUALITY_GATE_BYPASS_AUDIT.md
deployment_service/cli/utils/manifest_reader.py: (5 occurrences)
❌ Codex compliance FAILED: 2 violations (max allowed: 1)
```

**Confirmed pre-existing, not caused by my diff**: stashed my 3 changed files (`scripts/vm/lib/launcher_common.sh`,
`tests/unit/test_vm_launcher_scripts.py`, plus even the 1-line `cloud_run_job_registry.py` fix), re-ran
`quality-gates.sh` — identical `2 violations (max allowed: 1)` failure, same two files (`data_pipeline_monitors/cli.py`,
`cli/utils/manifest_reader.py`) — neither of which I have ever touched. `CODEX_MAX_VIOLATIONS=1` for this repo
(`scripts/quality-gates.sh:51`) was already exhausted before this dispatch.

- `deployment_service/data_pipeline_monitors/cli.py` is 930 lines (900-line ceiling) — last touched `b3826fe`
  (2026-07-13, "fix(dp-monitors): guard find_spec() raise for absent scripts.vm") — likely pushed it over the line
  ceiling, or it was already close and a smaller nearby commit tipped it.
- `deployment_service/cli/utils/manifest_reader.py` has 5 `except Exception:` blocks with none documented in
  `QUALITY_GATE_BYPASS_AUDIT.md` — a required documentation step whenever a broad catch is intentional, not done.

## Why it matters

Per the workspace HARD RULE ("Quality gates BEFORE COMMIT — the commit is the per-repo quality boundary"), NO commit can
land on `deployment-service` right now — the gate is red independent of what changes. This blocks my own task
(`defi_morpho_lending_indices_never_wired-002`) and will block every other worker dispatched to this repo until
resolved.

## Recommended decision

- [x] [SCRIPT] P1. Split `deployment_service/data_pipeline_monitors/cli.py` (930 L) below the 900-line ceiling — likely
      extract one or more subcommand groups into a sibling module under `data_pipeline_monitors/` (follow the existing
      package's module-per-concern pattern), re-exporting via the package `__init__.py` if needed to keep the CLI's
      public entrypoints unchanged. (repo: `deployment-service`) — ✅ `deployment-service@534de4b` (cicd escalation
      agt-9d01d7): extracted the meta-sweep target/scheduler-job-name resolvers (`catalogue_targets`,
      `high_attempted_failed_targets`, `scheduler_env_prefix`, `consolidator_*_job`) into a new sibling
      `data_pipeline_monitors/meta_targets.py`; `cli.py` 930L → 810L. Also fixed an adjacent pre-existing red
      (`test_every_scheduler_tf_job_is_registered`): added the missing `CLOUD_RUN_JOBS` entry for
      `deployment_digest_scheduler.tf` (stem `deployment-digest`) — this is the same gap slot-10's dispatch had already
      diagnosed but couldn't ship (blocked by this very wall). `quality-gates.sh` now exits 0 (codex-compliance down to
      1 violation — the broad-except WARN below — within the `CODEX_MAX_VIOLATIONS=1` tolerance).
- [x] ✅ [SCRIPT] P2. Document the 5 `except Exception:` blocks in `deployment_service/cli/utils/manifest_reader.py` in
      `QUALITY_GATE_BYPASS_AUDIT.md` (follow the existing entries' format) if they are intentionally broad, or narrow
      each to the specific exception type(s) actually expected if not. (repo: `deployment-service`) — **re-scoped
      2026-07-13 (agt-9d01d7)**: the QG's broad-except check (`base-service.sh`
      `BE=$(codex_rg "except Exception:"     ... | head -5)`) scans the WHOLE repo and increments the violation counter
      ONCE regardless of occurrence count; the "5 occurrences" in this doc's original diagnosis were the first 5 lines
      of a `head -5` truncation that happen to all land in `manifest_reader.py` (alphabetically first among ~30+
      matching files across the repo, not a `manifest_reader.py`-specific count). Fixing only this file would NOT change
      the check's WARN status (another file's occurrences would just fill the `head -5` window instead) — genuinely
      closing it requires an audit-and-fix (or a sanctioned `QUALITY_GATE_BYPASS_AUDIT.md` + `BE_EXCLUDE_GLOBS` bypass)
      across every `except Exception:` site in the repo, which is out of scope for a CI-wall fix. Downgraded P1→P2 and
      demoted to informational since the gate now PASSES (1 violation ≤ `CODEX_MAX_VIOLATIONS=1`); re-prioritize if the
      ceiling is ever ratcheted to 0. **DONE 2026-07-13 (slot-8 sonnet/high)** — did the full audit-and-fix rather than
      leaving it at "tolerated": a full-repo scan (`grep -rn '^\s*except Exception:\s*$' deployment_service/`) found 31
      bare `except Exception:` sites across 8 files (not just manifest_reader.py's 5), every one the same "best-effort
      GCS/S3 read, never raise, safe-default fallback" pattern already explained per-callsite in its own docstring.
      Documented all 31 in `QUALITY_GATE_BYPASS_AUDIT.md` §§2.18-2.20 and excluded them via `BE_EXCLUDE_GLOBS` in
      `scripts/quality-gates.sh`. `quality-gates.sh` now exits 0 with the broad-except check fully GREEN (not just
      within tolerance) — `deployment-service@d089f24`.
