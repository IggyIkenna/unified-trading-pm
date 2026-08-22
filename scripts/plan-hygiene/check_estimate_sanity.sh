#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Verify estimate_calibrated_ai_days ≈ estimate_baseline_ai_days × class_multiplier, AND that a plan declaring
# estimate_class also declares BOTH day-count fields (a class with one or both days blank previously passed silently
# — 2026-07-24 finding: sports_consolidated_closeout_2026_07_19.md had estimate_calibrated_ai_days set from a
# baseline×multiplier comment but an EMPTY estimate_baseline_ai_days field, invisible to this check since it only
# ever compared two numbers that were both present).
# Flags: MISSING (estimate_class set but baseline/calibrated blank) and DRIFT (calibrated doesn't match baseline ×
# multiplier by >20%).
# Soft check — exits 0 always (informational).
# Usage: bash scripts/plan-hygiene/check_estimate_sanity.sh [--quiet]

set -euo pipefail
QUIET="${1:-}"
PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

[ "$QUIET" != "--quiet" ] && echo "Estimate sanity check (calibrated ≈ baseline × multiplier, ±20%):"
[ "$QUIET" != "--quiet" ] && echo ""

QUIET_MODE="$( [ "$QUIET" = "--quiet" ] && echo 1 || echo 0 )" PM_DIR="$PM_DIR" python3 - <<'EOF'
import pathlib, re, os

PM_DIR = pathlib.Path(os.environ["PM_DIR"])

MULTIPLIERS = {
    "refactor":   0.4,
    "design":     0.6,
    "infra":      0.8,
    "brand-new":  1.0,
    "research":   1.2,
}

ACTIVE_DIR = PM_DIR / "plans" / "active"
DRIFT_THRESHOLD = 0.20

drifted = []
missing = []
checked = 0

for fp in sorted(ACTIVE_DIR.glob("*.md")):
    name = fp.name
    if name in ("INDEX.md",): continue
    if name.startswith("_"): continue
    if name.endswith(".HANDOVER.md"): continue

    text = fp.read_text()
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        continue

    fm_lines = []
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        fm_lines.append(ln)
    fm = "\n".join(fm_lines)

    mc  = re.search(r"^estimate_class:\s*(.+)", fm, re.MULTILINE)
    mb  = re.search(r"^estimate_baseline_ai_days:\s*([\d.]+)", fm, re.MULTILINE)
    mca = re.search(r"^estimate_calibrated_ai_days:\s*([\d.]+)", fm, re.MULTILINE)

    if not mc:
        continue
    cls = mc.group(1).strip()
    if cls not in MULTIPLIERS:
        continue

    if not (mb and mca):
        missing.append((name, cls, "baseline" if not mb else None, "calibrated" if not mca else None))
        continue

    baseline   = float(mb.group(1))
    calibrated = float(mca.group(1))
    expected   = round(baseline * MULTIPLIERS[cls], 4)

    if expected == 0:
        continue

    drift = abs(calibrated - expected) / expected
    checked += 1

    if drift > DRIFT_THRESHOLD:
        drifted.append((name, cls, baseline, calibrated, expected, drift))

for name, cls, missing_baseline, missing_calibrated in missing:
    which = " and ".join(f for f in (missing_baseline, missing_calibrated) if f)
    print(f"  MISSING  {name}")
    print(f"           class={cls} but {which} blank — task_template.md §2 requires both when estimate_class is set")

for name, cls, baseline, calibrated, expected, drift in sorted(drifted, key=lambda x: -x[5]):
    print(f"  DRIFT  {name}")
    print(f"         class={cls} baseline={baseline} expected={expected} calibrated={calibrated} drift={drift:.0%}")

print()
if drifted or missing:
    parts = []
    if missing: parts.append(f"{len(missing)} with a missing day-count field")
    if drifted: parts.append(f"{len(drifted)} with >20% drift")
    print(f"⚠️  check_estimate_sanity: {' + '.join(parts)} ({checked} checked, {len(missing)} skipped-as-missing)")
else:
    if os.environ.get("QUIET_MODE") != "1":
        print(f"✅ check_estimate_sanity: all {checked} plans within 20% tolerance, none missing a day-count field")
EOF
