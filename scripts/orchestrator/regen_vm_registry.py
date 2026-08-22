# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Regenerate orchestrator_vm_registry.yaml from plan frontmatter.

Scans plans/epics/*.md + plans/active/*master*.md + key actives for the
``assigned_vm:`` frontmatter field. Validates every referenced vm-id exists
in the registry. Bumps ``generated_at`` timestamp. Exits non-zero on errors.

Usage (run from PM repo root):
  python3 scripts/orchestrator/regen_vm_registry.py [--check]  # --check = validate only, no write
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "orchestrator_vm_registry.yaml"
PLANS_EPICS = REPO_ROOT / "plans" / "epics"
PLANS_ACTIVE = REPO_ROOT / "plans" / "active"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
# NA / na / N/A / n/a = intentionally unassigned (D3 — first-class valid value, dispatches to nobody)
_NA_VARIANTS: frozenset[str] = frozenset({"NA", "na", "N/A", "n/a"})


def _extract_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


def _scan_plans() -> dict[str, list[str]]:
    """Return {vm_id: [plan_path, ...]} from assigned_vm frontmatter."""
    vm_to_plans: dict[str, list[str]] = {}
    patterns = [
        str(PLANS_EPICS / "*.md"),
        str(PLANS_ACTIVE / "*master*.md"),
        str(PLANS_ACTIVE / "*coordination*.md"),
        str(PLANS_ACTIVE / "orchestrator_v07*.md"),
    ]
    for pattern in patterns:
        for fpath in sorted(glob.glob(pattern)):
            p = Path(fpath)
            fm = _extract_frontmatter(p)
            vm_id = fm.get("assigned_vm")
            if not isinstance(vm_id, str):
                continue
            rel = str(p.relative_to(REPO_ROOT))
            vm_to_plans.setdefault(vm_id, [])
            if rel not in vm_to_plans[vm_id]:
                vm_to_plans[vm_id].append(rel)
    return vm_to_plans


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate only; do not write")
    args = parser.parse_args()

    registry: dict[str, object] = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    known_ids: set[str] = {vm["id"] for vm in registry.get("vms", [])}  # type: ignore[index]  # noqa: qg-empty-fallback
    vm_to_plans = _scan_plans()

    errors: list[str] = []
    for vm_id, plans in vm_to_plans.items():
        if vm_id in _NA_VARIANTS:
            continue
        if vm_id not in known_ids:
            errors.append(f"  assigned_vm '{vm_id}' in plan(s) {plans} not in registry (known: {sorted(known_ids)})")

    if errors:
        print("ERRORS — vm-ids not in registry:\n" + "\n".join(errors), file=sys.stderr)
        return 1

    if args.check:
        print(f"OK — all assigned_vm values valid ({len(vm_to_plans)} vm-ids)")
        return 0

    # Update master_plans lists on each vm entry from scanned frontmatter.
    for vm in registry.get("vms", []):  # type: ignore[union-attr]  # noqa: qg-empty-fallback
        vm_id = vm["id"]  # type: ignore[index]
        scanned = vm_to_plans.get(vm_id, [])  # type: ignore[arg-type]
        # Merge: preserve manually-listed plans; add scanned ones.
        existing: list[str] = vm.get("master_plans", []) or []  # type: ignore[assignment,union-attr]  # noqa: qg-empty-fallback
        merged = list(dict.fromkeys(existing + scanned))  # deduplicate, preserve order
        vm["master_plans"] = merged  # type: ignore[index]

    registry["generated_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    REGISTRY_PATH.write_text(yaml.dump(registry, default_flow_style=False, sort_keys=False), encoding="utf-8")
    print(f"Wrote {REGISTRY_PATH} (generated_at={registry['generated_at']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
