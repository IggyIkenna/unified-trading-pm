#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Verify estimate_calibrated_ai_days ≈ estimate_baseline_ai_days × class_multiplier.
# Flags plans where the drift exceeds 20%.
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

    if not (mc and mb and mca):
        continue

    cls = mc.group(1).strip()
    if cls not in MULTIPLIERS:
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

for name, cls, baseline, calibrated, expected, drift in sorted(drifted, key=lambda x: -x[5]):
    print(f"  DRIFT  {name}")
    print(f"         class={cls} baseline={baseline} expected={expected} calibrated={calibrated} drift={drift:.0%}")

print()
if drifted:
    print(f"⚠️  check_estimate_sanity: {len(drifted)} plan(s) with >20% drift ({checked} checked)")
else:
    if os.environ.get("QUIET_MODE") != "1":
        print(f"✅ check_estimate_sanity: all {checked} plans within 20% tolerance")
EOF
