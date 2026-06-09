#!/usr/bin/env python3
"""Run the codex V-counted Python sub-checkers in ONE interpreter.

base-service.sh's [5] codex block spawns a separate `python3` for each of:
  env-canon, manifest-import-alignment, schema-provenance, imports-inside-functions.
Each interpreter startup is ~0.3-0.4 s — the dominant cost of the codex "grep" phase is
process-spawn overhead, not file scanning (one rg over a 382-file tree is ~0.02 s). This
orchestrator loads each checker module by path and calls its `main()` in-process (reusing
each checker's exact logic verbatim — no logic re-implementation), turning ~4 spawns into 1.

Each checker's `main()` reads sys.argv / argparse and returns an int (0 = pass). import-patterns
is intentionally NOT merged here — it is a hard `[3.5]` gate (exit 1), kept separate so its
severity is unchanged. This orchestrator only covers the V-counted codex checkers, and prints
`__CODEX_PY_FAILURES__=<n>` for base-service to add to V (severity preserved: count, not exit).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def _run(path: Path, modname: str, argv: list[str]) -> int:
    """Invoke a checker's main() in-process with argv; return its int exit code."""
    saved = sys.argv
    sys.argv = [str(path), *argv]
    try:
        spec = importlib.util.spec_from_file_location(modname, path)
        if spec is None or spec.loader is None:
            print(f"[codex-py] {modname}: cannot load {path}")
            return 1
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # top-level only; main() is __main__-guarded so won't auto-run
        try:
            rc = mod.main()  # type: ignore[attr-defined]
            return int(rc) if rc is not None else 0
        except SystemExit as e:  # a checker that sys.exit()s inside main()
            c = e.code
            return 0 if c is None else (c if isinstance(c, int) else 1)
    except Exception as e:
        print(f"[codex-py] {modname} ERRORED: {e}")
        return 1
    finally:
        sys.argv = saved


def main() -> int:
    ap = argparse.ArgumentParser(description="Run codex V-counted python sub-checkers in one process")
    ap.add_argument("--repo-path", required=True)  # $(pwd) of the repo under test
    ap.add_argument("--service-name", required=True)
    ap.add_argument("--workspace-root", required=True)
    ap.add_argument("--source-dir", required=True)
    ap.add_argument("--pm-scripts", required=True)  # …/unified-trading-pm/scripts
    ap.add_argument("--skip-schema-provenance", action="store_true")
    ap.add_argument("--skip-manifest-alignment", action="store_true")
    ap.add_argument("--imports-inside-exclude", nargs="*", default=[])
    args = ap.parse_args()

    pm = Path(args.pm_scripts)
    checks: list[tuple[str, Path, list[str]]] = []

    ec = pm / "validation" / "check_env_canon.py"
    if ec.exists():
        checks.append(("env-canon", ec, [args.repo_path]))

    if not args.skip_manifest_alignment:
        ma = pm / "validation" / "check_manifest_import_alignment.py"
        if ma.exists():
            checks.append(
                ("manifest-alignment", ma, ["--repo", args.repo_path, "--workspace-root", args.workspace_root])
            )

    if not args.skip_schema_provenance:
        sp = pm / "validation" / "check_schema_provenance.py"
        if sp.exists():
            checks.append(
                ("schema-provenance", sp, ["--repo", args.service_name, "--workspace-root", args.workspace_root])
            )

    ii = pm / "quality_gates" / "check_imports_inside_functions.py"
    if ii.exists():
        ii_argv = ["--source-dir", args.source_dir]
        for g in args.imports_inside_exclude:
            ii_argv += ["--exclude-glob", g]
        checks.append(("imports-inside", ii, ii_argv))

    failures = 0
    for name, path, argv in checks:
        print(f"── codex-py: {name} ──")
        rc = _run(path, f"_codexpy_{name.replace('-', '_')}", argv)
        if rc != 0:
            failures += 1
            print(f"[codex-py] {name}: FAIL (rc={rc})")
        else:
            print(f"[codex-py] {name}: PASS")

    print(f"__CODEX_PY_FAILURES__={failures}")
    return 0  # always 0; base-service reads the failure count from the marker line


if __name__ == "__main__":
    sys.exit(main())
