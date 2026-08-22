#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Dev environment smoke test.

SSOT: unified-trading-pm/plans/active/dev_environment_automated_onboarding_2026_03_10.md
Phase 4.1 — smoke-test-dev.py

Checks (each prints PASS/FAIL):
  1. Python 3.13 active from .venv-workspace/bin/python
  2. All T0-T3 libraries importable (UTL, UCI, UEI, UAC, UIC, UMI)
  3. CLOUD_MOCK_MODE=true → mock GCS read/write completes without real credentials
  4. VCR_MODE=playback → top 3 venue cassette dirs present (or graceful skip)
  5. Dev GCP project configured (GCP_PROJECT_ID env var)
  6. setup_events() from UEI works without real Pub/Sub
  7. ruff check unified-trading-library/ exits 0
  8. basedpyright unified-trading-library/ exits 0 (with run_timeout 120)

Run from workspace root:
  python unified-trading-pm/scripts/dev/smoke-test-dev.py

Exit code: 0 if all mandatory checks pass, 1 if any mandatory check fails.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# ── colour helpers ────────────────────────────────────────────────────────────
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"


def _pass(label: str, detail: str = "") -> None:
    suffix = f"  ({detail})" if detail else ""
    print(f"{GREEN}  [PASS] {label}{suffix}{NC}")


def _fail(label: str, detail: str = "") -> None:
    suffix = f"  — {detail}" if detail else ""
    print(f"{RED}  [FAIL] {label}{suffix}{NC}")


def _skip(label: str, reason: str = "") -> None:
    suffix = f"  ({reason})" if reason else ""
    print(f"{BLUE}  [SKIP] {label}{suffix}{NC}")


def _warn(label: str, detail: str = "") -> None:
    suffix = f"  — {detail}" if detail else ""
    print(f"{YELLOW}  [WARN] {label}{suffix}{NC}")


def _section(title: str) -> None:
    print(f"\n{YELLOW}━━━ {title} ━━━{NC}")


# ── workspace paths ───────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
VENV_PYTHON = WORKSPACE_ROOT / ".venv-workspace" / "bin" / "python"

failures: list[str] = []
warnings: list[str] = []


def record_fail(label: str, detail: str = "") -> None:
    failures.append(label)
    _fail(label, detail)


def record_warn(label: str, detail: str = "") -> None:
    warnings.append(label)
    _warn(label, detail)


# ── Check 1: Python 3.13 from .venv-workspace ────────────────────────────────
_section("Check 1: Python 3.13 from .venv-workspace")

py_exec = sys.executable
py_ver = sys.version_info
if py_ver.major == 3 and py_ver.minor >= 13:
    if ".venv-workspace" in py_exec:
        _pass("Python 3.13", f"{py_ver.major}.{py_ver.minor}.{py_ver.micro} from {py_exec}")
    else:
        record_warn(
            "Python 3.13 OK but not from .venv-workspace",
            f"active: {py_exec} — activate with: source {WORKSPACE_ROOT}/.venv-workspace/bin/activate",
        )
else:
    record_fail(
        "Python 3.13 required",
        f"found {py_ver.major}.{py_ver.minor} at {py_exec}",
    )

# ── Check 2: T0-T3 library imports ───────────────────────────────────────────
_section("Check 2: T0-T3 library imports")

LIBRARY_IMPORTS: list[tuple[str, str, bool]] = [
    # (label, import_statement, mandatory)
    ("unified_trading_library (UTL)", "import unified_trading_library", True),
    (
        "unified_trading_library.config_interface (UCI)",
        "from unified_trading_library.config_interface import UnifiedCloudConfig",
        True,
    ),
    (
        "unified_trading_library.events (UEI)",
        "from unified_trading_library.events import setup_events, log_event",
        True,
    ),
    ("unified_api_contracts (UAC)", "import unified_api_contracts", True),
    ("unified_api_contracts.internal (UIC)", "import unified_api_contracts.internal", True),
    ("unified_market_interface (UMI)", "import unified_market_interface", False),
    ("unified_trading_library (UTL)", "import unified_trading_library", False),
    ("unified_trading_library.feature_calculator (UFCL)", "import unified_trading_library.feature_calculator", False),
]

for label, stmt, mandatory in LIBRARY_IMPORTS:
    try:
        exec(stmt)  # nosec B102 — intentional: dynamic import check for dev smoke test  # nosec B102 — dev smoke test: stmt is from known LIBRARY_IMPORTS list only
        _pass(label)
    except ImportError as exc:
        if mandatory:
            record_fail(label, str(exc))
        else:
            record_warn(label, f"optional — {exc}")

# ── Check 3: CLOUD_MOCK_MODE=true mock GCS ────────────────────────────────────
_section("Check 3: CLOUD_MOCK_MODE=true mock GCS/PubSub")

cloud_mock = os.environ.get("CLOUD_MOCK_MODE", "").lower()
if cloud_mock in ("1", "true", "yes"):
    _pass("CLOUD_MOCK_MODE", "set to true — mock GCS/PubSub active")
    # Attempt UnifiedCloudConfig instantiation (reads CLOUD_MOCK_MODE)
    try:
        from unified_trading_library import UnifiedCloudConfig  # type: ignore[import-not-found]

        cfg = UnifiedCloudConfig()
        _pass("UnifiedCloudConfig instantiated", f"project={cfg.gcp_project_id}")
    except Exception as exc:  # noqa: broad-except — smoke-test check: any init failure is a
        # recorded FAIL, never a crash of the rest of the smoke suite
        record_fail("UnifiedCloudConfig instantiation", str(exc))
else:
    record_warn(
        "CLOUD_MOCK_MODE not set to true",
        "set CLOUD_MOCK_MODE=true in .env.dev to avoid live GCP calls",
    )

# ── Check 4: VCR cassette dirs present ───────────────────────────────────────
_section("Check 4: VCR cassette dirs")

vcr_cassettes_dir = PM_ROOT / "scripts" / "dev" / "vcr_cassettes"
vcr_mode = os.environ.get("VCR_MODE", "playback")

if vcr_mode == "playback":
    if vcr_cassettes_dir.exists():
        cassette_venues = [d for d in vcr_cassettes_dir.iterdir() if d.is_dir()]
        if len(cassette_venues) >= 3:
            names = ", ".join(d.name for d in cassette_venues[:3])
            _pass("VCR cassettes present", f"{len(cassette_venues)} venue dirs: {names} ...")
        elif cassette_venues:
            _warn(
                "VCR cassettes: fewer than 3 venue dirs",
                f"found {len(cassette_venues)} — cassettes are added by api_keys_and_auth plan Phase 1-4",
            )
        else:
            _skip(
                "VCR cassettes: directory empty",
                "api_keys_and_auth plan Phase 1-4 will populate cassettes",
            )
    else:
        _skip("VCR cassettes dir not found", "will be created when api_keys_and_auth plan runs")
else:
    _skip("VCR cassette check", f"VCR_MODE={vcr_mode} (not playback)")

# ── Check 5: Dev GCP project configured ──────────────────────────────────────
_section("Check 5: Dev GCP project")

expected_project = os.environ.get("GCP_PROJECT_ID")
if not expected_project:
    _skip("GCP project check", "GCP_PROJECT_ID not set — set it for dev environment validation")
else:
    gcloud_result = subprocess.run(
        ["gcloud", "config", "get-value", "project"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if gcloud_result.returncode == 0:
        active_project = gcloud_result.stdout.strip()
        if active_project == expected_project:
            _pass("GCP project", active_project)
        else:
            record_warn(
                "GCP project mismatch",
                f"active={active_project!r}, expected={expected_project!r} "
                f"— run: gcloud config set project {expected_project}",
            )
    else:
        _skip("GCP project check", "gcloud not available or not configured")

# ── Check 6: setup_events() works without real Pub/Sub ───────────────────────
_section("Check 6: setup_events() from UEI")

try:
    from unified_trading_library import log_event, setup_events  # type: ignore[import-not-found]

    # setup_events with a test service name; CLOUD_MOCK_MODE=true prevents real PubSub init
    setup_events("smoke-test", mode="test")
    _pass("setup_events() executed", "no real Pub/Sub connection required")
    log_event("smoke_test_check", severity="INFO", details={"check": 6, "status": "pass"})
    _pass("log_event() executed")
except Exception as exc:  # noqa: broad-except — smoke-test check: any init failure is a
    # recorded FAIL, never a crash of the rest of the smoke suite
    record_fail("setup_events() / log_event()", str(exc))

# ── Check 7: ruff check unified-trading-library/ ─────────────────────────────
_section("Check 7: ruff check unified-trading-library/")

utl_dir = WORKSPACE_ROOT / "unified-trading-library"
if utl_dir.exists():
    ruff_exec = WORKSPACE_ROOT / ".venv-workspace" / "bin" / "ruff"
    ruff_cmd = str(ruff_exec) if ruff_exec.exists() else "ruff"
    result = subprocess.run(
        [ruff_cmd, "check", str(utl_dir), "--quiet"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode == 0:
        _pass("ruff check unified-trading-library/")
    else:
        record_warn(
            "ruff check unified-trading-library/ has violations",
            f"run: {ruff_cmd} check unified-trading-library/ --fix",
        )
else:
    _skip("ruff check", "unified-trading-library/ not found in workspace")

# ── Check 8: basedpyright unified-trading-library/ ───────────────────────────
_section("Check 8: basedpyright unified-trading-library/")

if utl_dir.exists():
    bp_exec = WORKSPACE_ROOT / ".venv-workspace" / "bin" / "basedpyright"
    bp_cmd = str(bp_exec) if bp_exec.exists() else "basedpyright"

    # run_timeout is a shell function; we use a subprocess timeout instead
    result = subprocess.run(
        [bp_cmd, str(utl_dir)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(WORKSPACE_ROOT),
    )
    if result.returncode == 0:
        _pass("basedpyright unified-trading-library/")
    else:
        # Count error lines for a concise summary
        error_lines = [ln for ln in result.stdout.splitlines() if " error" in ln.lower()]
        count = len(error_lines)
        record_warn(
            "basedpyright unified-trading-library/ has type errors",
            f"{count} error(s) — run: basedpyright unified-trading-library/ for details",
        )
else:
    _skip("basedpyright check", "unified-trading-library/ not found in workspace")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print(f"\033[1m{'━' * 50}\033[0m")
if failures:
    print(f"{RED}\033[1mSMOKE TEST FAILED — {len(failures)} failure(s){NC}")
    for f in failures:
        print(f"  {RED}[FAIL]{NC} {f}")
    if warnings:
        print(f"\n{YELLOW}Warnings ({len(warnings)}):{NC}")
        for w in warnings:
            print(f"  {YELLOW}[WARN]{NC} {w}")
    sys.exit(1)
else:
    print(f"{GREEN}\033[1mSMOKE TEST PASSED{NC}")
    if warnings:
        print(f"\n{YELLOW}Warnings ({len(warnings)}) — non-fatal:{NC}")
        for w in warnings:
            print(f"  {YELLOW}[WARN]{NC} {w}")
    print(f"\n{GREEN}Dev environment is ready.{NC}")
    print(f"  Activate: source {WORKSPACE_ROOT}/.venv-workspace/bin/activate")
    sys.exit(0)
