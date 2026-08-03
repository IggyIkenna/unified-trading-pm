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
asset_group:
  [ao] # retagged 2026-08-02 from [meta] (operator ruling on
  # plan_reconcile_parked_operator_decisions_2026_08_02.md na-eligibility-audit item 19, option A) — parent_epic
  # agent_operating_framework_master maps to ao; [meta] made this doc invisible to the ao tranche's own audit runs
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, performance, filesystem-walk, rglob, quickmerge-throughput, shared-host-io, git-red, ship-path]
related: [plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md]
created: "2026-07-31"
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: NA # left NA for the ao tranche's own dispatch call (per the ruling), not auto-flipped to planning here
execution_scope: local-only
drift_direction: advance-code
source: [main-orchestrator-triage-agt-26fe12, quickmerge-hang-observed]
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /codex/06-coding-standards/quality-gates.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md,
    unified-trading-pm/scripts/quality_gates/check_runbook_execution_owner.py,
  ]
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

## Progress Log

- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA — RECLASSIFY candidate assessed,
  conflict-check CLEAR, HELD as `BLOCKED-OPERATOR-DECISION`.** First verdict for this doc (no prior marker). Read
  end-to-end; `grep -cE '^- \[ \]'` = **1**, matching this verdict's item count.

  **Why it looked dispatch-ready.** The sole todo is unusually well-specified: one function (`_iter_runbook_files`) in
  one PM file, a prescribed `os.walk(topdown=True)` implementation given verbatim, an explicit invariant ("keep the
  verdict + baseline semantics byte-identical"), and a stated regression test. The doc's own triage says "AO-scope …
  small + clear code fix in one pm-repo QG script + one test. Not operator-gated." **Phase-2 conflict-check run and
  CLEAR** (protocol § 3): only three active docs mention `check_runbook_execution_owner` and **none is
  `assigned_vm: planning`** — `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29.md` (NA; its sole open todo is a
  `[REVIEW] P3` prose correction, no file overlap) and `ag_closeout_audit_infra_parked_2026_08_01.md` (NA; a narrative
  mention in finding 6), plus this doc. No sibling batch drafted this run; `infra_consolidated_closeout_2026_07_25.md`
  holds no claim on it.

  **Why it was NOT flipped — two independent reasons, each needing a human call:**
  1. **Ownership is disputed and reserved to another tranche.** Two consecutive `/ag-closeout-audit infra` runs
     (2026-08-01 finding 6, re-affirmed 2026-08-02 item 6) ruled this doc's real owning tranche is **`ao`**, not `infra`
     (`parent_epic: agent_operating_framework_master`), and that under the owning-tranche-writes-only rule only `ao` may
     write to it — an `assigned_vm` flip is a write. Flipping from the infra tranche is exactly the cross-tranche race
     that rule exists to prevent.
  2. **Blast radius is the fleet's ship path, not one repo.** This gate runs inside every `quality-gates.sh`, therefore
     inside every `quickmerge`, in every repo. "Byte-identical verdict semantics" between `Path.rglob` and a pruning
     `os.walk` is asserted by the todo, not proven by it — symlink traversal, the `archive/`-prefix substring semantics,
     and result ordering all differ subtly between the two, and a silent change to the finding set would either
     false-fail or false-pass every agent's commit. This skill's own calibration note warns against trusting a todo's
     "fully-scoped, AO-dispatchable" self-framing when the change sits on live-ship-path machinery.

  **BLOCKED-OPERATOR-DECISION — options:**
  - **A [WORKER REC]: retag `asset_group: [meta] → [ao]` first, then let the `ao` tranche make the `assigned_vm` call.**
    Settles the ownership question two prior audits already answered, and puts the flip with the tranche that owns the
    content. The caveat that makes this a decision rather than an action: **`ao` cannot currently see this doc at all**
    — tranche membership derives from `asset_group`, so the mistag is self-perpetuating (tranche-level deadlock recorded
    in `infra_consolidated_closeout_2026_07_25.md`'s 2026-08-02 marker). A works only if the retag is applied by someone
    outside the per-tranche sharding.
  - **B: authorise the infra tranche to flip `assigned_vm: NA → planning` now**, on the grounds that the WORK is PM
    repo/script-governance tooling (`unified-trading-pm/scripts/quality_gates/`), squarely infra's own Track-1/Track-3
    remit per `infra_consolidated_closeout_2026_07_25.md`'s Reachability map, even though `parent_epic` points at `ao`.
    Fastest path to fixing a live P1 throughput bug; accepts one cross-tranche write.
  - **C: keep NA and fix it by hand in an interactive session**, given the ship-path blast radius — a human runs the
    before/after via `scripts/quality_gates/profile_qg_resources.py` and diffs the finding set rather than trusting a
    worker's "byte-identical" claim.
  - Other: operator free-text.

  **Standing note for the next run**: the conflict-check is done and clear, so if the operator picks B this is a
  one-line frontmatter change plus `execution_scope: local-only → orchestrator-agent` and an `assigned_role` fill — do
  not re-derive it.

- **context-scout 2026-08-03**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — close call, preserving caution rather than
  loosening the verdict. The ownership blocker from the 2026-08-02 pass is now moot (retag `asset_group: [meta] -> [ao]`
  executed 2026-08-02, confirmed live — that's why this run sees the doc at all), but the independent blast-radius
  concern is not: the todo's own "byte-identical verdict semantics" claim is asserted, not proven, against a gate that
  runs inside every `quality-gates.sh`/quickmerge in every repo and already caused one real fleet-wide 13+min hang
  incident. No new resolving evidence since the 2026-08-02 hold (no diff-proof run, no operator pick of option A/B/C).
  Staying skeptical of a "fully-scoped, AO-dispatchable" self-framing on live-dispatch-critical -path machinery per this
  skill's own guidance, rather than re-deriving a looser verdict on unchanged evidence.
