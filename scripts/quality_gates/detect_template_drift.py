"""Detect drift between per-repo quality-gates.sh / .pre-commit-config.yaml and SSOT templates.

Reports repos where quality-gates.sh or .pre-commit-config.yaml has diverged from the canonical
templates.  Used by the B-014 rollout and ongoing prek rollout to catch manual edits before they
silently rot.

What is checked
---------------
For each service/api-service/library repo:

quality-gates.sh checks:
1. SSOT comment — header must reference the correct SSOT path.
2. Mandatory config vars — SERVICE_NAME, SOURCE_DIR, MIN_COVERAGE, RUN_INTEGRATION,
   PYTEST_WORKERS, LOCAL_DEPS, WORKSPACE_ROOT, source line.
3. Source path — must be `${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh`.
4. Lifecycle block — must use the canonical 3-branch pattern (fastapi_uei_lifespan /
   ServiceBootstrap / log_event loop); repos with the old bare-loop pattern are flagged.
5. No placeholder values — SERVICE_NAME and SOURCE_DIR must not be "REPLACE_ME".

.pre-commit-config.yaml checks (--prek flag):
6. SSOT comment — header must reference the pre-commit-templates/ path.
7. gitleaks hook — must be present (secret scanning).
8. ruff rev — must match SSOT template canonical version.
9. conventional-pre-commit rev — must match SSOT template.

workflow-template parity checks (--workflows flag — runs ONLY this check, not the qg/prek ones):
10. For every FLAT `.yml` template in scripts/workflow-templates/ (NOT `.yml.tmpl`, which is
    substituted per-repo so can't byte-compare), each repo's `.github/workflows/<name>` must
    byte-match the SSOT template. A present-but-different copy is an ERROR (someone hand-edited
    a per-repo copy, or it rotted after a template change without re-rollout — the SSOT hole
    that flat-copied workflows otherwise have NO guard for). A missing copy is a WARN (needs
    `rollout-workflow-templates.sh`). A repo not checked out (CI, where siblings are absent) is
    a WARN — so the guard is a no-op in CI and a hard gate locally / on a full-workspace host.

UI repos and repos without quality-gates.sh are skipped for QG checks. Workflow parity does NOT
skip by type (generic .yml templates roll out to every repo, UI included).
All repos with .pre-commit-config.yaml are checked when --prek is passed.

Usage
-----
    python3 scripts/quality_gates/detect_template_drift.py [--workspace-root PATH]
    python3 scripts/quality_gates/detect_template_drift.py --repo features-service
    python3 scripts/quality_gates/detect_template_drift.py --prek        # also check .pre-commit-config.yaml
    python3 scripts/quality_gates/detect_template_drift.py --workflows   # ONLY workflow-template parity
    python3 scripts/quality_gates/detect_template_drift.py --json        # machine-readable output
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

# Pre-commit template paths
PREK_TEMPLATE_DIR: Final[Path] = PM_ROOT / "scripts" / "pre-commit-templates"
PREK_SERVICE_TEMPLATE: Final[Path] = PREK_TEMPLATE_DIR / "python-service.pre-commit-config.yaml"
PREK_LIBRARY_TEMPLATE: Final[Path] = PREK_TEMPLATE_DIR / "python-library.pre-commit-config.yaml"
PREK_UI_TEMPLATE: Final[Path] = PREK_TEMPLATE_DIR / "ui.pre-commit-config.yaml"

# Canonical hook IDs that must be present (service repos)
PREK_MANDATORY_HOOKS: Final[tuple[str, ...]] = (
    "conventional-pre-commit",
    "ruff",
    "ruff-format",
    "gitleaks",
)
PREK_SSOT_COMMENT: Final[str] = "# Template SSOT: unified-trading-pm/scripts/pre-commit-templates/"

# Workflow-template parity: flat `.yml` templates here are cp'd verbatim into every repo's
# .github/workflows/ by rollout-workflow-templates.sh, so each copy MUST byte-match the SSOT.
# `.yml.tmpl` templates are substituted per-repo and are NOT byte-comparable (excluded by the
# `*.yml` glob).
WORKFLOW_TEMPLATE_DIR: Final[Path] = PM_ROOT / "scripts" / "workflow-templates"

# Baselined ratchet (mirrors check_credential_ask_orphans.py): the workspace already carries
# pre-existing workflow drift (templates that rotted before this guard existed). Block only NEW
# drift beyond this baseline; ratchet the baseline DOWN as repos are re-rolled-out. Each entry is
# a "<repo>/<template>.yml" key. Regenerate with `--workflows --baseline-write`.
WORKFLOW_DRIFT_BASELINE_PATH: Final[Path] = SCRIPT_DIR / "workflow_template_drift_baseline.json"


def _drift_key(repo_name: str, template_name: str) -> str:
    return f"{repo_name}/{template_name}"


def _load_workflow_drift_baseline() -> set[str]:
    if not WORKFLOW_DRIFT_BASELINE_PATH.exists():
        return set()
    with WORKFLOW_DRIFT_BASELINE_PATH.open() as f:
        raw = cast(dict[str, object], json.load(f))
    entries = raw.get("drift", [])  # noqa: qg-empty-fallback
    return set(cast(list[str], entries)) if isinstance(entries, list) else set()


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
    repos_raw = raw.get("repositories", {})  # noqa: qg-empty-fallback
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


# ── Pre-commit checks ─────────────────────────────────────────────────────────


def _check_prek(
    repo_name: str,
    repo_type: str,
    workspace_root: Path,
) -> RepoDriftReport:
    prek_path = workspace_root / repo_name / ".pre-commit-config.yaml"
    report = RepoDriftReport(repo_name=repo_name, repo_type=repo_type, qg_path=prek_path)

    if not prek_path.exists():
        report.items.append(
            DriftItem(
                "warn", "prek-missing-file", ".pre-commit-config.yaml not found — run rollout-pre-commit-configs.sh"
            )
        )
        return report

    content = prek_path.read_text()

    # 1. SSOT comment
    if PREK_SSOT_COMMENT not in content:
        report.items.append(
            DriftItem("warn", "prek-ssot-comment", f"Missing SSOT header comment. Expected: {PREK_SSOT_COMMENT!r}")
        )

    # 2. Mandatory hooks — skip ui repos (different template)
    if repo_type not in UI_REPO_TYPES:
        for hook_id in PREK_MANDATORY_HOOKS:
            if f"id: {hook_id}" not in content:
                severity = "error" if hook_id == "gitleaks" else "warn"
                report.items.append(
                    DriftItem(
                        severity, f"prek-missing-hook-{hook_id}", f"Missing hook {hook_id!r} in .pre-commit-config.yaml"
                    )
                )

    # 3. Rev version checks — parse canonical from template
    template_path = PREK_LIBRARY_TEMPLATE if repo_type in LIBRARY_REPO_TYPES else PREK_SERVICE_TEMPLATE
    if not template_path.exists():
        return report

    template_content = template_path.read_text()
    rev_pattern = re.compile(r"- repo: (https://\S+)\s.*?rev: (\S+)", re.DOTALL)
    template_revs: dict[str, str] = {m.group(1): m.group(2) for m in rev_pattern.finditer(template_content)}
    repo_revs: dict[str, str] = {m.group(1): m.group(2) for m in rev_pattern.finditer(content)}

    for repo_url, canonical_rev in template_revs.items():
        actual_rev = repo_revs.get(repo_url)
        if actual_rev is None:
            continue  # hook not present — already flagged by mandatory-hook check
        if actual_rev != canonical_rev:
            hook_short = repo_url.split("/")[-1]
            report.items.append(
                DriftItem(
                    "warn",
                    f"prek-stale-rev-{hook_short}",
                    f"{hook_short}: rev {actual_rev!r} != canonical {canonical_rev!r}",
                )
            )

    return report


# ── Workflow-template parity ───────────────────────────────────────────────────


def _check_workflows(
    repo_name: str,
    repo_type: str,
    workspace_root: Path,
) -> RepoDriftReport:
    """Assert each repo's .github/workflows/<t>.yml byte-matches the SSOT template.

    Closes the SSOT hole that flat-copied workflow templates otherwise have no guard for.
    differ -> error (true positive: a hand-edited / rotted copy). missing -> warn (needs
    rollout). repo-absent -> warn (CI degrades to no-op; runs as a hard gate locally).
    """
    gh_dir = workspace_root / repo_name / ".github" / "workflows"
    report = RepoDriftReport(repo_name=repo_name, repo_type=repo_type, qg_path=gh_dir)

    if not (workspace_root / repo_name).exists():
        report.items.append(
            DriftItem(
                "warn",
                "workflow-repo-absent",
                f"{repo_name} not checked out — workflow parity skipped (CI no-op; enforced locally)",
            )
        )
        return report

    for template in sorted(WORKFLOW_TEMPLATE_DIR.glob("*.yml")):
        name = template.name
        copy = gh_dir / name
        if not copy.exists():
            report.items.append(
                DriftItem(
                    "warn",
                    f"workflow-missing-{name}",
                    f".github/workflows/{name} missing — run "
                    f"rollout-workflow-templates.sh --repo {repo_name} --template {name}",
                )
            )
            continue
        if copy.read_bytes() != template.read_bytes():
            report.items.append(
                DriftItem(
                    "error",
                    f"workflow-drift-{name}",
                    f".github/workflows/{name} differs from SSOT scripts/workflow-templates/{name} — "
                    f"re-run rollout-workflow-templates.sh (never hand-edit the per-repo copy)",
                )
            )

    return report


# ── Main ─────────────────────────────────────────────────────────────────────


def _report_workflow_drift(
    reports: list[RepoDriftReport],
    output_json: bool,
    write_baseline: bool,
    allow_additions: bool = False,
) -> int:
    """Baselined ratchet for workflow-template parity: block only NEW drift beyond the baseline."""
    current: set[str] = {
        _drift_key(r.repo_name, it.check.removeprefix("workflow-drift-"))
        for r in reports
        for it in r.items
        if it.severity == "error" and it.check.startswith("workflow-drift-")
    }

    if write_baseline:
        # M5: --baseline-write ratchets DOWN only (removes now-clean entries); it must NOT
        # silently ADD new drift, which would bless breakage in one line (the H4 hole — a
        # hand-edited per-repo workflow getting grandfathered instead of rolled out). New
        # drift must be fixed via rollout-workflow-templates.sh; to deliberately grandfather
        # it (discouraged), pass --baseline-write-allow-additions.
        prior = _load_workflow_drift_baseline()
        if prior:
            additions = current - prior
            if additions and not allow_additions:
                print(f"REFUSED: --baseline-write would ADD {len(additions)} new drift entr(ies) (bless breakage):")
                for k in sorted(additions):
                    print(f"  + {k}")
                print(
                    "Fix via rollout-workflow-templates.sh, or re-run with"
                    " --baseline-write-allow-additions to grandfather."
                )
                return 1
            new_baseline = current if allow_additions else (current & prior)
        else:
            new_baseline = current  # bootstrap: no prior baseline → capture current
        removed = prior - new_baseline
        WORKFLOW_DRIFT_BASELINE_PATH.write_text(json.dumps({"drift": sorted(new_baseline)}, indent=2) + "\n")
        print(f"Wrote workflow-drift baseline: {len(new_baseline)} entries -> {WORKFLOW_DRIFT_BASELINE_PATH.name}")
        if removed:
            print(f"  ratcheted down: removed {len(removed)} now-clean entr(ies)")
        return 0

    baseline = _load_workflow_drift_baseline()
    new_drift = current - baseline
    ratchet_candidates = baseline - current  # baselined entries now clean — baseline can tighten

    if output_json:
        print(
            json.dumps(
                {
                    "current_drift": sorted(current),
                    "baseline": sorted(baseline),
                    "new_drift": sorted(new_drift),
                    "ratchet_candidates": sorted(ratchet_candidates),
                },
                indent=2,
            )
        )
        return 1 if new_drift else 0

    warns = sum(1 for r in reports for it in r.items if it.severity == "warn")
    print(f"\nWorkflow-template parity — {len(reports)} repos, {len(current)} drifted copy(ies), {warns} warn(s)")
    print(f"  baselined (grandfathered): {len(current & baseline)}")
    print(f"  NEW drift (blocking):      {len(new_drift)}")
    if ratchet_candidates:
        print(f"  ratchet down: {len(ratchet_candidates)} baselined entry(ies) now clean — re-run --baseline-write")
    print()
    if new_drift:
        print("❌ NEW workflow-template drift (a per-repo copy was hand-edited or rotted vs the SSOT):")
        for k in sorted(new_drift):
            print(f"  [ERROR] {k} — re-run rollout-workflow-templates.sh; never hand-edit the per-repo copy")
        print()
        return 1
    print("✅ No new workflow-template drift beyond baseline")
    return 0


def run(
    workspace_root: Path,
    filter_repo: str | None = None,
    output_json: bool = False,
    check_prek: bool = False,
    check_workflows: bool = False,
    write_baseline: bool = False,
    allow_additions: bool = False,
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
        if filter_repo and repo_name != filter_repo:
            continue

        # Workflows-only mode: generic .yml templates roll out to EVERY repo (UI included),
        # so don't apply SKIP_REPO_TYPES, and don't run the qg/prek checks.
        if check_workflows:
            reports.append(_check_workflows(repo_name, repo_type, workspace_root))
            continue

        if repo_type in SKIP_REPO_TYPES:
            continue

        report = _check_repo(repo_name, repo_type, workspace_root)
        reports.append(report)

        if check_prek:
            prek_report = _check_prek(repo_name, repo_type, workspace_root)
            if not prek_report.is_clean:
                # Merge prek items into main report under prek-prefixed checks
                for item in prek_report.items:
                    report.items.append(item)

    if check_workflows:
        return _report_workflow_drift(
            reports, output_json=output_json, write_baseline=write_baseline, allow_additions=allow_additions
        )

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
    parser.add_argument(
        "--prek", action="store_true", dest="check_prek", help="Also check .pre-commit-config.yaml drift"
    )
    parser.add_argument(
        "--workflows",
        action="store_true",
        dest="check_workflows",
        help="ONLY check .github/workflows/*.yml byte-parity vs scripts/workflow-templates/ (baselined ratchet)",
    )
    parser.add_argument(
        "--baseline-write",
        action="store_true",
        dest="write_baseline",
        help=(
            "Ratchet the workflow-drift baseline DOWN (remove now-clean entries; refuses to ADD"
            " new drift). Implies --workflows."
        ),
    )
    parser.add_argument(
        "--baseline-write-allow-additions",
        action="store_true",
        dest="allow_additions",
        help=(
            "With --baseline-write, also grandfather NEW drift (discouraged — bless breakage)."
            " Default refuses additions."
        ),
    )
    args = parser.parse_args()

    workspace_root = cast(Path, args.workspace_root)
    filter_repo = cast(str | None, args.repo)
    output_json = cast(bool, args.output_json)
    check_prek = cast(bool, args.check_prek)
    write_baseline = cast(bool, args.write_baseline)
    allow_additions = cast(bool, args.allow_additions)
    check_workflows = cast(bool, args.check_workflows) or write_baseline  # baseline-write implies workflows
    sys.exit(
        run(
            workspace_root=workspace_root,
            filter_repo=filter_repo,
            output_json=output_json,
            check_prek=check_prek,
            check_workflows=check_workflows,
            write_baseline=write_baseline,
            allow_additions=allow_additions,
        )
    )


if __name__ == "__main__":
    main()
