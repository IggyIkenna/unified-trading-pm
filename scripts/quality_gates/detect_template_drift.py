"""Detect drift between per-repo quality-gates.sh files and the SSOT templates.

Reports repos where quality-gates.sh has diverged from the canonical template
(quality-gates-service-template.sh or quality-gates-library-template.sh).  Used
by the B-014 rollout to catch manual edits before they silently rot.

What is checked
---------------
For each service/api-service/library repo:

1. SSOT comment — header must reference the correct SSOT path.
2. Mandatory config vars — SERVICE_NAME, SOURCE_DIR, MIN_COVERAGE, RUN_INTEGRATION,
   PYTEST_WORKERS, LOCAL_DEPS, WORKSPACE_ROOT, source line.
3. Source path — must be `${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh`.
4. Lifecycle block — must use the canonical 3-branch pattern (fastapi_uei_lifespan /
   ServiceBootstrap / log_event loop); repos with the old bare-loop pattern are flagged.
5. No placeholder values — SERVICE_NAME and SOURCE_DIR must not be "REPLACE_ME".

UI repos and repos without quality-gates.sh are skipped.

Usage
-----
    python3 scripts/quality_gates/detect_template_drift.py [--workspace-root PATH]
    python3 scripts/quality_gates/detect_template_drift.py --repo features-service
    python3 scripts/quality_gates/detect_template_drift.py --json   # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, cast

# ── Constants ─────────────────────────────────────────────────────────────────

SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
PM_ROOT: Final[Path] = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT_DEFAULT: Final[Path] = PM_ROOT.parent
MANIFEST_PATH: Final[Path] = PM_ROOT / "workspace-manifest.json"
SERVICE_TEMPLATE_PATH: Final[Path] = PM_ROOT / "codex" / "06-coding-standards" / "quality-gates-service-template.sh"
LIBRARY_TEMPLATE_PATH: Final[Path] = PM_ROOT / "codex" / "06-coding-standards" / "quality-gates-library-template.sh"

CANONICAL_SOURCE_LINE: Final[str] = (
    'source "${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"'
)
CANONICAL_SOURCE_INDIRECT: Final[str] = "base-service.sh"  # variable-indirection pattern

CANONICAL_SSOT_COMMENT: Final[str] = (
    "# SSOT: unified-trading-pm/codex/06-coding-standards/quality-gates-service-template.sh"
)
LIBRARY_SSOT_COMMENT: Final[str] = (
    "# SSOT: unified-trading-pm/codex/06-coding-standards/quality-gates-library-template.sh"
)

# Mandatory config variables that must be set before the source line
MANDATORY_VARS: Final[tuple[str, ...]] = (
    "SERVICE_NAME",
    "SOURCE_DIR",
    "MIN_COVERAGE",
    "RUN_INTEGRATION",
    "PYTEST_WORKERS",
    "LOCAL_DEPS",
    "WORKSPACE_ROOT",
)

# Old lifecycle pattern: bare for-loop without fastapi/ServiceBootstrap check
OLD_LIFECYCLE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^for event in STARTED STOPPED FAILED", re.MULTILINE)
CANONICAL_LIFECYCLE_PATTERN: Final[re.Pattern[str]] = re.compile(r"fastapi_uei_lifespan", re.MULTILINE)

UI_REPO_TYPES: Final[frozenset[str]] = frozenset({"ui"})
SKIP_REPO_TYPES: Final[frozenset[str]] = frozenset({"ui", "devops"})
LIBRARY_REPO_TYPES: Final[frozenset[str]] = frozenset({"library"})


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass
class DriftItem:
    severity: str  # "error" | "warn" | "info"
    check: str
    message: str


@dataclass
class RepoDriftReport:
    repo_name: str
    repo_type: str
    qg_path: Path | None
    items: list[DriftItem] = field(default_factory=list[DriftItem])

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.items)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warn" for i in self.items)

    @property
    def is_clean(self) -> bool:
        return not self.items


# ── Helpers ───────────────────────────────────────────────────────────────────


def _load_manifest(manifest_path: Path) -> dict[str, dict[str, str]]:
    """Load workspace-manifest.json; returns {repo_name: {field: value}}."""
    with manifest_path.open() as f:
        text = f.read()
    raw = cast(dict[str, object], json.loads(text))
    repos_raw = raw.get("repositories", {})
    if not isinstance(repos_raw, dict):
        return {}
    return cast(dict[str, dict[str, str]], repos_raw)


def _repo_path(workspace_root: Path, repo_name: str) -> Path:
    return workspace_root / repo_name


def _qg_path(workspace_root: Path, repo_name: str) -> Path:
    return _repo_path(workspace_root, repo_name) / "scripts" / "quality-gates.sh"


# ── Per-repo checks ───────────────────────────────────────────────────────────


def _check_repo(
    repo_name: str,
    repo_type: str,
    workspace_root: Path,
) -> RepoDriftReport:
    qg = _qg_path(workspace_root, repo_name)
    report = RepoDriftReport(repo_name=repo_name, repo_type=repo_type, qg_path=qg)

    if not qg.exists():
        report.items.append(
            DriftItem("warn", "missing-file", "scripts/quality-gates.sh not found — repo may need rollout")
        )
        return report

    content = qg.read_text()

    # Library repos use a different template — only check library-specific items
    is_library = repo_type in LIBRARY_REPO_TYPES or LIBRARY_SSOT_COMMENT in content
    if is_library:
        if LIBRARY_SSOT_COMMENT not in content and CANONICAL_SSOT_COMMENT not in content:
            report.items.append(DriftItem("warn", "ssot-comment", "Missing SSOT header comment for library repo"))
        return report

    # 1. SSOT comment
    if CANONICAL_SSOT_COMMENT not in content:
        report.items.append(
            DriftItem(
                "warn",
                "ssot-comment",
                f"Missing or stale SSOT header comment. Expected: {CANONICAL_SSOT_COMMENT!r}",
            )
        )

    # 2. Mandatory config vars (before source line)
    source_line_match = content.find('source "${WORKSPACE_ROOT}')
    if source_line_match == -1:
        # Also check for variable-indirection pattern: BASE_QG_SCRIPT=...; source "${BASE_QG_SCRIPT}"
        source_line_match = content.find('source "${')
    pre_source = content[:source_line_match] if source_line_match != -1 else content
    for var in MANDATORY_VARS:
        if not re.search(rf"^{var}=", pre_source, re.MULTILINE):
            report.items.append(
                DriftItem("error", f"missing-var-{var}", f"Mandatory variable {var}= not set before source line")
            )

    # 3. Source line — accept direct or variable-indirection form
    has_direct_source = CANONICAL_SOURCE_LINE in content
    has_indirect_source = bool(
        re.search(r"BASE_QG_SCRIPT=.*base-service\.sh", content) and re.search(r"source.*BASE_QG_SCRIPT", content)
    )
    if not has_direct_source and not has_indirect_source:
        if CANONICAL_SOURCE_INDIRECT in content:
            report.items.append(
                DriftItem(
                    "warn",
                    "noncanonical-source-path",
                    f"base-service.sh referenced but not via canonical direct or BASE_QG_SCRIPT pattern. "
                    f"Canonical: {CANONICAL_SOURCE_LINE!r}",
                )
            )
        else:
            report.items.append(DriftItem("error", "missing-source-line", "No base-service.sh source line found"))

    # 4. Lifecycle block — canonical vs old
    has_canonical = bool(CANONICAL_LIFECYCLE_PATTERN.search(content))
    has_old = bool(OLD_LIFECYCLE_PATTERN.search(content))

    if has_old and not has_canonical:
        report.items.append(
            DriftItem(
                "warn",
                "stale-lifecycle-block",
                "Uses old bare-loop lifecycle pattern (missing fastapi_uei_lifespan / ServiceBootstrap check). "
                "Update to canonical 3-branch pattern from quality-gates-service-template.sh.",
            )
        )
    elif not has_canonical and not has_old:
        report.items.append(
            DriftItem(
                "warn",
                "missing-lifecycle-block",
                "No UEI lifecycle enforcement block found. Add canonical block from quality-gates-service-template.sh.",
            )
        )

    # 5. Placeholder values
    if re.search(r'^SERVICE_NAME="REPLACE_ME"', content, re.MULTILINE):
        report.items.append(DriftItem("error", "placeholder-service-name", "SERVICE_NAME is still REPLACE_ME"))
    if re.search(r'^SOURCE_DIR="REPLACE_ME"', content, re.MULTILINE):
        report.items.append(DriftItem("error", "placeholder-source-dir", "SOURCE_DIR is still REPLACE_ME"))

    return report


# ── Main ─────────────────────────────────────────────────────────────────────


def run(
    workspace_root: Path,
    filter_repo: str | None = None,
    output_json: bool = False,
) -> int:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: workspace manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest = _load_manifest(MANIFEST_PATH)

    reports: list[RepoDriftReport] = []
    for repo_name, repo_meta in manifest.items():
        repo_type = repo_meta.get("type", "service")
        archived = bool(repo_meta.get("archived_into", ""))

        if archived:
            continue
        if repo_type in SKIP_REPO_TYPES:
            continue
        if filter_repo and repo_name != filter_repo:
            continue

        report = _check_repo(repo_name, repo_type, workspace_root)
        reports.append(report)

    if output_json:
        out: list[dict[str, object]] = [
            {
                "repo": r.repo_name,
                "type": r.repo_type,
                "clean": r.is_clean,
                "items": [{"severity": i.severity, "check": i.check, "message": i.message} for i in r.items],
            }
            for r in reports
        ]
        print(json.dumps(out, indent=2))
        return 1 if any(rep.has_errors for rep in reports) else 0

    # Human-readable output
    clean_count = sum(1 for r in reports if r.is_clean)
    warn_count = sum(1 for r in reports if r.has_warnings and not r.has_errors)
    error_count = sum(1 for r in reports if r.has_errors)

    print(f"\nTemplate drift detection — {len(reports)} repos checked")
    print(f"  ✅ Clean:    {clean_count}")
    print(f"  ⚠️  Warnings: {warn_count}")
    print(f"  ❌ Errors:   {error_count}")
    print()

    for report in sorted(reports, key=lambda r: (not r.has_errors, not r.has_warnings, r.repo_name)):
        if report.is_clean:
            continue
        icon = "❌" if report.has_errors else "⚠️ "
        print(f"{icon} {report.repo_name} ({report.repo_type})")
        for item in report.items:
            prefix = "  [ERROR]" if item.severity == "error" else "  [WARN] "
            print(f"{prefix} [{item.check}] {item.message}")
        print()

    return 1 if error_count > 0 else 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace-root", type=Path, default=WORKSPACE_ROOT_DEFAULT, help="Path to workspace root")
    parser.add_argument("--repo", help="Check a single repo by name")
    parser.add_argument("--json", action="store_true", dest="output_json", help="Machine-readable JSON output")
    args = parser.parse_args()

    workspace_root = cast(Path, args.workspace_root)
    filter_repo = cast(str | None, args.repo)
    output_json = cast(bool, args.output_json)
    sys.exit(run(workspace_root=workspace_root, filter_repo=filter_repo, output_json=output_json))


if __name__ == "__main__":
    main()
