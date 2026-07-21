---
doc_type: issue
title: >-
  DeFi contract-address citation ratchet (QG STEP 5.97) silently no-ops in every per-slot local `quality-gates.sh` run —
  `.tabs` is in its own exclusion list
summary: >-
  `unified-trading-pm/scripts/quality_gates/check_defi_address_citations.py::_is_excluded_path` checks `any(part in
  EXCLUDE_DIR_NAMES for part in path.parts)` against the file's ABSOLUTE path (in addition to the repo-relative path).
  `EXCLUDE_DIR_NAMES` includes `.tabs` (added to stop a nested worktree copy from double-counting). But every agent's
  per-slot worktree itself lives at `<workspace_root>/.tabs/<slot>/<repo>/...`, so the absolute path of EVERY file in
  EVERY slot's checkout contains `.tabs` as a path component — the exclusion fires unconditionally and `scan_repo()`
  returns 0 hits for any repo scanned from inside a slot clone, regardless of actual content. Confirmed directly:
  `_is_excluded_path(Path('/home/ubuntu/unified-trading-system-repos/.tabs/10/instruments-service/instruments_service/reference_data/adapters/defi/_dex_factory_registry.py'))`
  returns `True` even though that file has zero `# DERIVED` citations. STEP 5.97 (`base-service.sh`) prints `✅ STEP
  5.97: No new uncited DeFi contract addresses` for every local run in every slot no matter what — a rubber stamp. Only
  CI (checkout at `/home/runner/work/<repo>/<repo>`, no `.tabs` in the path) actually enforces the ratchet; that is
  where `instruments-service`'s `ldr_qg_failure` (escalation agt-3968a1, `3ffd1adf`'s 12 uncited SushiSwap/Uniswap
  factory addresses) was actually caught — never locally, by any slot, before push.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, citation-ratchet, defi, false-green, tooling-bug]
related: []
created: "2026-07-21"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.05
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "found 2026-07-21 while resolving instruments-service ldr_qg_failure escalation agt-3968a1 (cicd role, slot 11) —
    tried to locally verify a citation fix via the standalone checker and via full quality-gates.sh, both silently
    passed regardless of fix content once run from inside .tabs/<slot>/",
  ]
resolved_by:
locked_by:
---

# DeFi citation ratchet false-green under `.tabs/<slot>/` worktrees

## Root cause

`unified-trading-pm/scripts/quality_gates/check_defi_address_citations.py`:

```python
EXCLUDE_DIR_NAMES: Final[frozenset[str]] = frozenset({
    ...
    ".claude", ".tabs", "worktrees",
})

def _is_excluded_path(path: Path) -> bool:
    if any(part in EXCLUDE_DIR_NAMES for part in path.parts):
        return True
    ...

def _iter_py_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*.py"):
        if _is_excluded_path(path.relative_to(root) if path.is_relative_to(root) else path):
            continue
        if _is_excluded_path(path):   # <-- checks the ABSOLUTE path too
            continue
        yield path
```

The relative-path check is correct (it's meant to catch a _nested_ `.tabs/<N>/full-repo-clone` sitting inside a scanned
repo, which would double-count). The second `_is_excluded_path(path)` call passes the **absolute** path — and every
slot's own checkout lives under `.../.tabs/<slot>/<repo>/...`, so it always contains `.tabs` as a path component. Every
file in the currently-scanned repo gets excluded, every time, when the scan itself is invoked from inside a slot
worktree (which is 100% of local agent runs — Path-B per-slot worktrees are the standing topology).

## Impact

- `scan_repo()` returns `count=0, sites=[]` for any repo scanned locally, independent of actual uncited-address count.
- STEP 5.97 in `base-service.sh` (run by every `quality-gates.sh` / `quality-gates.sh --no-fix` invocation) always logs
  `✅ STEP 5.97: No new uncited DeFi contract addresses` — never fails locally, never even warns.
- The ratchet is effectively CI-only. New uncited addresses land on `live-defi-rollout` (or would, if quickmerge's local
  gate were the only check) and are caught only by the GitHub Actions `quality-gates-v2` run (checkout path
  `/home/runner/work/<repo>/<repo>`, no `.tabs` segment) — after push, as an `ldr_qg_failure` escalation, not before.
- Confirmed concretely: `instruments-service@3ffd1adf` added 12 uncited SushiSwap/Uniswap factory addresses to
  `_dex_factory_registry.py`. Neither the authoring slot's own `quality-gates.sh` (must have run clean per the
  Commit+Push+Flip hard rule) nor any subsequent slot re-running it locally caught this — LDR's CI did, several ships
  later, as `ldr_qg_failure` escalation `agt-3968a1`.

## Fix sketch (not applied — out of scope for the triggering escalation)

Drop the second absolute-path `_is_excluded_path(path)` call in `_iter_py_files`, or make the absolute-path check skip
`.tabs`/`.claude`/`worktrees` when they are a PREFIX of `root` itself (i.e. only exclude a _nested_ worktree found
_inside_ the scan, not the ambient slot directory the scan is running from). The relative-path check already covers the
nested-worktree case correctly on its own.

## Evidence

```
$ python3 -c "
from check_defi_address_citations import _is_excluded_path
from pathlib import Path
p = Path('/home/ubuntu/unified-trading-system-repos/.tabs/10/instruments-service/instruments_service/reference_data/adapters/defi/_dex_factory_registry.py')
print(_is_excluded_path(p))"
True
```

That file has zero `# DERIVED` markers on any of its 12 addresses at the time of this test.
