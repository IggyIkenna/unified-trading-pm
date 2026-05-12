---
title: "Workspace QG runner foot-guns surfaced by slot worktree sweep (2026-05-12)"
created: 2026-05-12
author: ikenna-codefreeze-audit-tab (slot 3)
source:
  - unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh
  - unified-trading-pm/scripts/quality-gates-base/base-service.sh STEPs 5.67 + 5.69 + 5.70
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

> ✅ **PATCHES SHIPPED** at the same commit that creates this issue doc. Both foot-guns
> would affect ANY slot worktree QG sweep (and silently affect main-checkout STEP 5.6x
> runs too via mis-rooted relative paths). Filing to record the findings for the QG
> runner maintainer + future per-slot worktree consumers.

# Workspace QG runner foot-guns surfaced by slot worktree sweep

## What I found

Slot 3 codefreeze-audit-tab Day-4 fired the workspace QG sweep (freeze-gate item 8) by running
`bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --skip-alignment --skip-setup --skip-typecheck`
from inside the slot 3 worktree (`.tabs/3/`). Two foot-guns surfaced:

### Foot-gun #1 — `.git`-as-DIR-only check in `run_qg()`

`run-all-quality-gates.sh:156` filters which repos to QG via `[[ ! -d "$rp/.git" ]] && { echo "  [SKIP] $repo — not found"; return 0; }`. In a per-slot worktree (per CLAUDE.md "Per-Tab Worktrees — 3-tier parallel-agent isolation"), `.tabs/<N>/<repo>/.git` is a **FILE** (git-worktree link), not a directory. The `-d` check therefore returns false, and every repo gets `[SKIP] <repo> — not found`. The first run reported `OK: 34 | Failed: 0` with every repo skipped — a silent false-pass.

### Foot-gun #2 — `_PM_REPO=basename(REPO_ROOT)` / `_PM_WS=dirname(REPO_ROOT)` in STEPs 5.67 + 5.69 + 5.70

`base-service.sh` STEPs 5.67 (banned-NaN-placeholder) + 5.69 (inline gs:// f-string) + 5.70 (pipeline_mode-explicit) compute the AST-walk script's `--workspace-root` and `--scope` arguments from `REPO_ROOT`:

```bash
_PM_REPO=$(basename "$REPO_ROOT")    # → "3" in slot worktree; "unified-trading-system-repos" in main checkout
_PM_WS="$(dirname "$REPO_ROOT")"     # → ".tabs/" in slot worktree; "Code/" in main checkout
```

But per `scripts/quality-gates-base/qg-common.sh:48`:

```bash
REPO_ROOT="${REPO_ROOT:-$(cd "$PROJECT_ROOT/.." 2>/dev/null && pwd)}"
```

`REPO_ROOT` is set to `dirname(PROJECT_ROOT)` — i.e. it IS the workspace root (the dir CONTAINING all repo dirs), NOT a per-repo dir itself. The variable name is misleading.

So in the slot 3 worktree:
- `PROJECT_ROOT` = `.tabs/3/features-service` (the per-repo dir)
- `REPO_ROOT` = `.tabs/3` (the workspace root)
- `_PM_REPO` = `basename(.tabs/3)` = `3` ❌ (should be `features-service`)
- `_PM_WS` = `dirname(.tabs/3)` = `.tabs` ❌ (should be `.tabs/3`)

The AST-walk script's `_resolve_scopes(workspace_root, scope)` then either:
- Treats `--scope 3` as a scope-name pointing at `.tabs/3` — scans the whole slot worktree — relative-path computation yields `3/<repo>/<file>` paths that don't match baseline yaml `file:` keys (which lack the slot-number prefix).
- Returns `"no source trees to scan"` if `.tabs/3` doesn't look like a Python repo.

Net effect on slot 3 Day-4 QG sweep: the AST-walk checks flagged 6 features-service callsites as non-baselined (because the relative paths got prefixed with `3/`, breaking baseline match), failing every repo's STEP 5.70.

In the main checkout (non-worktree) — `unified-trading-system-repos/<repo>/scripts/quality-gates.sh` — the same bug exists but manifests as `_PM_REPO=unified-trading-system-repos` (a non-existent scope) which results in either an empty scan or workspace-wide paths prefixed with the repo's own name. Less visible there because most checks have empty baselines and `0 occurrences` accidentally passes.

## Why it matters

Per CLAUDE.md "Plans Run To Actual Completion" HARD RULE, `code_freeze_migrate_backfill_sequencing_2026_05_10.md` freeze-gate item 8 (Workspace QG green) requires `bash scripts/quality-gates.sh` returns 0 across every active service repo. Without these patches, the workspace QG sweep returns silently-misleading results — either false-pass (foot-gun #1) or false-fail (foot-gun #2).

Both foot-guns also impede day-to-day per-slot worktree QG usage — the per-tab-worktree model (per `plans/active/per_agent_worktrees_2026_05_10.md`) is the workspace's canonical multi-agent parallelism pattern, and these QG runners are the canonical way to validate workspace-wide state.

## Recommended decision

**✅ DONE — patches shipped 2026-05-12 by slot 3 in the same commit as this issue doc.**

- `unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh:156` — `.git`-as-DIR check extended to also accept FILE shape (`git worktree` link). Patch: `[[ ! -d "$rp/.git" && ! -f "$rp/.git" ]]`.
- `unified-trading-pm/scripts/quality-gates-base/base-service.sh` STEPs 5.67 + 5.69 + 5.70 — `_PM_REPO` derived from `PROJECT_ROOT` (not `REPO_ROOT`); `_PM_WS` set to `REPO_ROOT` (which IS the workspace-root per qg-common.sh:48). Comment block at each site cross-references this issue doc.

**Verification**: post-patch, slot 3 worktree `bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --skip-alignment --skip-setup --skip-typecheck` shows STEPs 5.65/5.67/5.69/5.70 ALL ✅ green workspace-wide. Remaining 26-repo "failures" are pre-existing workspace hygiene findings (STEP 5.61/5.62 service-only checks failing on non-services like UAC/UTL/sys-integration-tests; codex compliance violations; production readiness validators) — out of scope for slot 3 codefreeze-audit-tab; routed to per-repo / non-service-QG-template owners.

## Composes with

- `plans/active/per_agent_worktrees_2026_05_10.md` (per-slot worktree SSOT)
- `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` freeze-gate item 8 (Workspace QG green)
- CLAUDE.md "Per-Tab Worktrees — 3-tier parallel-agent isolation" + "Plans Run To Actual Completion"
- The 3 AST-walk QG STEP SSOT plans: `manifest_schema_final_gate_2026_05_09.md` Phase 4.GREP-VERIFY (STEP 5.70) + `bucket_name_ssot_canonicalisation_2026_05_10.md` § QG STEP 5.6X (STEP 5.69) + `writegate_honest_coverage_endtoend_2026_05_06.md` § STEP 5.67 (banned placeholders)

## Follow-up — non-service repo SKIP semantics for service-only checks (P1, not slot 3 scope)

26-of-26 repos fail STEP 5.61 + 5.62 (`ServiceBootstrap not found` / `No health API`) on the slot-3-worktree workspace QG sweep — but many of those repos are NOT services (UAC = library, UTL = library, sys-integration-tests = harness, deployment-ui = UI, etc.). The current `--no-fix` invocation doesn't have a way to mark non-service repos as "skip service-only checks". This is the root cause of the 26 "failures" pattern in workspace QG sweeps.

**Recommended fix (P1, separate plan)**: extend `base-service.sh` STEP 5.61 + 5.62 with `SKIP_SERVICE_LIFECYCLE_STEPS` opt-out (already exists per `base-service.sh:1300-1301` but only some non-service repos set it). Audit per-repo `quality-gates.sh` stubs and set `SKIP_SERVICE_LIFECYCLE_STEPS=true` for: UAC + UTL + sys-integration-tests + deployment-ui + UI + ibkr-gateway-infra + any other non-service repos. **Owner**: workspace QG maintainer. **Not slot 3 scope.**
