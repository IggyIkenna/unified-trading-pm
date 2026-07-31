---
doc_type: issue
title:
  QG check_runbook_execution_owner.py does a full-workspace rglob that descends into every .tabs/*/.venv tree before
  post-filtering EXCLUDED_DIRS — I/O-thrashes on the shared host and hangs each quickmerge 13+ min (likely the
  sustained-git-red root cause)
summary: >-
  On 2026-07-31 main (agt-26fe12) shipped a one-file docs(issues) change via quickmerge and it sat 13+ min without even
  staging. Diagnosis: the quickmerge child `scripts/quality-gates.sh --no-fix` was blocked ~8 min inside a single gate,
  `scripts/quality_gates/check_runbook_execution_owner.py --workspace-root /home/ubuntu/unified-trading-system-repos`,
  whose python process was in kernel state D (uninterruptible I/O wait, wchan=wait_on_buffer) with an open fd deep
  inside `.tabs/6/deployment-api/.venv/.../basedpyright/dist/typeshed-fallback/...`. Root cause (code-read):
  `_iter_runbook_files` (check_runbook_execution_owner.py:86-94) walks `workspace_root.rglob("*runbook*.md")` and only
  filters `EXCLUDED_DIRS` (`.venv`, `.venv-workspace`, `node_modules`, `build/`, `dist/`, `archive/`, ...) *post-hoc* on
  the returned rel path (line 91). pathlib.rglob cannot prune — it still fully descends into every excluded directory to
  enumerate it, so the walk stats the entire slot x repo x .venv matrix (many hundreds of thousands of files across all
  `.tabs/<slot>/<repo>/.venv` trees) before discarding them. On the I/O-contended shared planning host this takes 10+
  min per invocation. Because every quickmerge runs the full gate set, this throttles the whole fleet's ship path and is
  the plausible root cause of the git_red_sustain_secs~5400 (90 min) I observed the same session (commits piling behind
  slow quickmerges).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, performance, filesystem-walk, rglob, quickmerge-throughput, shared-host-io, git-red, ship-path]
related: [plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md]
created: "2026-07-31"
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [main-orchestrator-triage-agt-26fe12, quickmerge-hang-observed]
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# What was observed

Main (`agt-26fe12`) ran `bash scripts/quickmerge.sh "docs(issues): …" --agent --files <one issue doc>` in
`unified-trading-pm`. After **13+ minutes** the file was still `??` untracked (quickmerge had not even staged it), while
_other_ agents' commits landed on the branch in the same window (so the branch itself was not blocked broadly). Process
inspection:

- `pstree`: `quickmerge.sh` → `quality-gates.sh --no-fix` → `python3 …/check_runbook_execution_owner.py`.
- The python gate had been running **~8 min alone**.
- `ps -o stat,wchan` on the gate PID: **`D` / `wait_on_buffer`** — uninterruptible **disk-I/O wait**, ~8% CPU (not a CPU
  runaway; it is I/O-bound).
- Open fd pointed **inside a `.venv`**:
  `…/.tabs/6/deployment-api/.venv/lib/python3.13/site-packages/basedpyright/dist/typeshed-fallback/stubs/pywin32/…` —
  i.e. it was actively recursing through a virtualenv's site-packages.

# Root cause (verified by code-read)

`scripts/quality_gates/check_runbook_execution_owner.py`:

```python
EXCLUDED_DIRS = ("plans/archive/", "archive/", ".venv", ".venv-workspace", "build/", "dist/", "node_modules/",
                 "context/codex/", ".extra/")

def _iter_runbook_files(workspace_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for p in workspace_root.rglob("*runbook*.md"):        # <-- walks EVERYTHING, incl. all .venv/.tabs
        rel = p.relative_to(workspace_root).as_posix()
        if any(rel.startswith(ex) or f"/{ex}" in f"/{rel}" for ex in EXCLUDED_DIRS):  # <-- post-hoc filter, too late
            continue
        candidates.append(p)
    return sorted(candidates)
```

`Path.rglob` offers no directory pruning — it recursively enumerates (and stats) **every** directory under
`workspace_root`, including each `.tabs/<slot>/<repo>/.venv/…`, `node_modules/`, `build/`, `dist/`, archived mirrors,
etc. The `EXCLUDED_DIRS` check only discards results _after_ the full walk has already paid the I/O cost. Because the
workspace root holds the whole per-slot clone matrix (N slots × M repos × a `.venv` each), that is a multi-hundred-
thousand-file walk on every invocation — and every `quickmerge`/`quality-gates.sh` run triggers it.

# Impact

- Each quickmerge on the shared host stalls 10+ min inside this one gate under I/O contention → the fleet's per-commit
  ship path is severely throttled.
- Plausible **root cause of the sustained git-red** (`git_red_sustain_secs≈5400`, 90 min, observed same session):
  commits queue behind slow quickmerges instead of landing promptly.
- Not a correctness bug (the gate's _verdict_ is right once it finishes), purely a walk-cost/latency bug — but a
  fleet-wide throughput one.

# Fix direction

Replace the `rglob` with a **pruning** walk so excluded directories are never descended into:

```python
import os
def _iter_runbook_files(workspace_root: Path) -> list[Path]:
    prune = {".venv", ".venv-workspace", "build", "dist", "node_modules", ".extra", ".git"}
    candidates: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(workspace_root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in prune]   # in-place prune -> no descent
        # keep the path-prefix excludes (plans/archive/, archive/, context/codex/) as a rel check on dirpath
        rel_dir = Path(dirpath).relative_to(workspace_root).as_posix()
        if any(rel_dir == ex.rstrip("/") or rel_dir.startswith(ex) for ex in ("plans/archive/", "archive/", "context/codex/")):
            dirnames[:] = []
            continue
        for fn in filenames:
            if "runbook" in fn and fn.endswith(".md"):
                candidates.append(Path(dirpath) / fn)
    return sorted(candidates)
```

Preserve the existing baseline/verdict semantics exactly — only the enumeration changes. Add a guard/test asserting the
walk does not descend into a `.venv` fixture (e.g. a temp tree with a `.venv/…/x-runbook.md` that must be ignored _and_
not stat-walked). Consider whether the gate even needs the whole `--workspace-root`; runbooks live under tracked doc
trees, so scoping the walk to those roots (or to `git ls-files`) would be strictly cheaper and is worth evaluating.

# Note for anyone filing a related issue

Do **not** put the literal word `runbook` in an issue-doc _filename_ under `plans/active/issues/` — the gate's
`*runbook*.md` glob matches on filename substring and that path is NOT in `EXCLUDED_DIRS`, so such a file would be
picked up and flagged as a malformed runbook. (This doc is deliberately named `qg_owner_gate_…` for that reason.)

# Triage / disposition

- **AO-scope**, `P1` (fleet ship-path throughput; likely git-red root cause), small + clear code fix in one pm-repo QG
  script + one test. Not operator-gated. Tracked follow-up below.
- Related: `boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md` (same session, unrelated
  subsystem).

# Follow-up todos

- [ ] [SCRIPT] P1. Replace the `workspace_root.rglob("*runbook*.md")` full-tree walk in
      `unified-trading-pm/scripts/quality_gates/check_runbook_execution_owner.py::_iter_runbook_files` with an
      `os.walk(topdown=True)` that prunes `EXCLUDED_DIRS` from `dirnames` in-place so
      `.venv`/`.tabs`/`node_modules`/`build`/ `dist`/archive trees are never descended into; keep the verdict + baseline
      semantics byte-identical; add a test that a `.venv/…/x-runbook.md` fixture is neither flagged nor walked. Evaluate
      scoping the walk to tracked doc roots / `git ls-files` as a further speedup. Cite
      `plans/active/issues/qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31.md` in the commit.
