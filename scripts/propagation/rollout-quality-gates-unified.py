#!/usr/bin/env python3.13
"""
Roll out quality gates to all repositories from workspace-manifest.json.

Reads workspace-manifest.json from workspace root (parent of unified-trading-pm),
iterates over repositories, and for each repo:
- library -> library template (quality-gates-library-template.sh)
- service/api-service -> service template (quality-gates-service-template.sh)
- ui -> TypeScript template (inline)
- infrastructure/test-harness/devops -> service template

Copies scripts/quality-gates.sh, scripts/setup.sh, creates .cursorignore/.gitignore
from repo-type templates if missing, creates QUALITY_GATE_BYPASS_AUDIT.md stub
when doc_standard requires it. Skips deprecated/archived repos.

Usage:
    python3 scripts/propagation/rollout-quality-gates-unified.py [--dry-run] [--repo NAME] [--skip-missing]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import cast

type JsonDict = dict[str, object]


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jstr(val: object, default: str = "") -> str:
    return str(val) if val is not None else default


# Paths relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
CODEX_ROOT = PM_ROOT / "codex"
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"

# Template paths
SETUP_SH_SOURCE = PM_ROOT / "scripts" / "setup.sh"
QG_LIBRARY_TEMPLATE = CODEX_ROOT / "06-coding-standards" / "quality-gates-library-template.sh"
QG_SERVICE_TEMPLATE = CODEX_ROOT / "06-coding-standards" / "quality-gates-service-template.sh"
QG_UI_TEMPLATE = CODEX_ROOT / "06-coding-standards" / "quality-gates-ui-template.sh"
ESLINT_CONFIG_BASE = PM_ROOT / "scripts" / "quality-gates-base" / "eslint.config.base.js"
TEMPLATES_DIR = SCRIPT_DIR / "templates"
CURSORIGNORE_PYTHON = TEMPLATES_DIR / "cursorignore-python.txt"
CURSORIGNORE_NODE = TEMPLATES_DIR / "cursorignore-node.txt"
GITIGNORE_PYTHON = TEMPLATES_DIR / "gitignore-python.txt"
GITIGNORE_NODE = TEMPLATES_DIR / "gitignore-node.txt"
UI_API_MAPPING_PATH = SCRIPT_DIR / "ui-api-mapping.json"
UI_INTEGRATION_TEMPLATE = PM_ROOT / "scripts" / "quality-gates-base" / "ui-integration-test.template.ts"

# Doc standards that require QUALITY_GATE_BYPASS_AUDIT.md
BYPASS_AUDIT_DOC_STANDARDS = frozenset(
    {
        "service-canonical",
        "library-canonical",
        "infrastructure-canonical",
        "api-canonical",
    }
)

# Type -> template selection
TYPE_LIBRARY = "library"
TYPE_SERVICE = "service"
TYPE_API_SERVICE = "api-service"
TYPE_UI = "ui"
TYPE_INFRASTRUCTURE = "infrastructure"
TYPE_TEST_HARNESS = "test-harness"
TYPE_DEVOPS = "devops"

# Coverage floors: max(floor, actual-1) — never set below floor regardless of actual
LIBRARY_COVERAGE_FLOOR = 80
SERVICE_COVERAGE_FLOOR = 70

SKIP_STATUSES = frozenset({"deprecated", "deleted"})
# PM and Codex have their own quality-gates; do not overwrite with templates
ROLLOUT_SKIP_REPOS = frozenset({"unified-trading-pm", "unified-trading-codex"})

# Known repo-specific config patterns to preserve between LOCAL_DEPS=() and WORKSPACE_ROOT=...
# when regenerating quality-gates.sh.  These are variable assignments or array declarations
# that repos add manually and must not be wiped by rollout.
_PRESERVED_VAR_PATTERNS = re.compile(
    r"^(?:UAC_CANONICAL_EXEMPT|BROAD_EXCEPT_EXTRA_EXCLUDES|MAX_DURATION|RUN_INTEGRATION|EXTRA_RUFF_ARGS|EXTRA_PYTEST_ARGS"
    r"|PRINT_EXCLUDE_GLOBS|OS_ENV_EXCLUDE_GLOBS|IMPORT_INSIDE_EXCLUDE_GLOBS"
    r"|EMPTY_STR_EXCLUDE_GLOBS|EMPTY_DICT_LIST_EXCLUDE_GLOBS|GCP_PROJECT_ID_EXCLUDE_GLOBS"
    r"|MAX_METHOD_LINES|MAX_FUNCTION_LINES|MAX_FILE_LINES|MANIFEST_ALIGNMENT_SKIP"
    r"|FUNCTION_SIZE_EXTRA_EXCLUDES|ASYNCIO_RUN_EXCLUDE_GLOBS|SETUP_NO_SINK_EXCLUDE_GLOBS)\b"
)

# Repos where discover_source_dir() picks the wrong dir — override explicitly.
# Key: repo name, Value: SOURCE_DIR value to use in quality-gates.sh
SOURCE_DIR_OVERRIDES: dict[str, str] = {
    # Actual Python package is ibkr_gateway_client, not ibkr_gateway_infra
    "ibkr-gateway-infra": "ibkr_gateway_client",
    # Pure test harness — no source package; measure coverage against tests/ directly
    "system-integration-tests": "tests",
}

# Repos that need a lower MIN_COVERAGE floor than the type-default.
# Rollout always enforces max(floor, existing); these entries lower the floor for specific repos.
MIN_COVERAGE_OVERRIDES: dict[str, int] = {
    # ibkr-gateway-infra has limited testable surface (mostly gateway client integration code)
    "ibkr-gateway-infra": 51,
    # system-integration-tests is a pure test-harness repo — no source to measure
    "system-integration-tests": 0,
}


def get_typescript_quality_gates_script() -> str:
    """Load quality-gates.sh for TypeScript/UI repos from codex template."""
    if not QG_UI_TEMPLATE.exists():
        raise FileNotFoundError(f"UI template not found: {QG_UI_TEMPLATE}")
    return QG_UI_TEMPLATE.read_text()


def get_quality_gate_bypass_audit_stub() -> str:
    """Minimal QUALITY_GATE_BYPASS_AUDIT.md stub."""
    return """# Quality Gate Bypass Audit

## 2.1 File Size Exceptions

None.

## 2.2 Ruff Exceptions

None.

## 2.3 Basedpyright Exceptions

None.

"""


def discover_source_dir(repo_path: Path, repo_name: str) -> str:
    """Discover Python source directory. Fallback: repo name with underscores."""
    # PM and codex are not packages; Python lives in scripts/
    if repo_name in ("unified-trading-pm", "unified-trading-codex"):
        scripts = repo_path / "scripts"
        if scripts.is_dir() and any(scripts.rglob("*.py")):
            return "scripts"
    default = repo_name.replace("-", "_")  # Python package form (underscores)
    candidates = [default, "src"]  # Try underscore form, then src; not hyphen form
    for c in candidates:
        d = repo_path / c
        if d.is_dir():
            if (d / "__init__.py").exists() or list(d.rglob("__init__.py")):
                return c
            if any(d.rglob("*.py")):
                return c
    return default


def select_template_type(repo_type: str) -> str:
    """Map repo type to template: library, service, or typescript."""
    if repo_type == TYPE_LIBRARY:
        return "library"
    if repo_type in (TYPE_SERVICE, TYPE_API_SERVICE, TYPE_INFRASTRUCTURE, TYPE_TEST_HARNESS, TYPE_DEVOPS):
        return "service"
    if repo_type == TYPE_UI:
        return "typescript"
    return "service"  # default for unknown Python repos


def measure_coverage(repo_path: Path, source_dir: str) -> int | None:
    """Return TOTAL coverage % for a repo.

    Strategy (fast-path first):
    1. Parse existing coverage.xml if present (written by the last quality-gates run).
    2. Fall back to running pytest --cov if no report exists.
    """
    # Fast path: read coverage.xml produced by the last QG run
    xml_path = repo_path / "coverage.xml"
    if xml_path.exists():
        try:
            tree = ET.parse(xml_path)  # nosec B314 — local coverage.xml, not untrusted input
            root = tree.getroot()
            line_rate = root.get("line-rate")
            if line_rate is not None:
                return int(float(line_rate) * 100)
        except (ET.ParseError, ValueError):
            pass  # fall through to pytest

    # Slow path: run pytest --cov
    python = repo_path / ".venv" / "bin" / "python"
    if not python.exists():
        python = Path(sys.executable)

    tests_unit = repo_path / "tests" / "unit"
    tests_dir = tests_unit if tests_unit.exists() else repo_path / "tests"
    if not tests_dir.exists():
        return None

    try:
        result = subprocess.run(
            [
                str(python),
                "-m",
                "pytest",
                str(tests_dir),
                f"--cov={source_dir}",
                "--cov-report=term-missing",
                "--cov-report=xml:coverage.xml",
                "-q",
                "--tb=no",
                "--no-header",
                "-x",
                "--ignore=tests/integration",
                "--ignore=tests/e2e",
            ],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=180,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None

    for line in (result.stdout + result.stderr).splitlines():
        if line.startswith("TOTAL"):
            parts = line.split()
            pct_str = parts[-1].rstrip("%")
            try:
                return int(float(pct_str))
            except (ValueError, IndexError):
                pass
    return None


def _extract_preserved_lines(existing_content: str) -> list[str]:
    """Extract repo-specific config lines from an existing quality-gates.sh.

    Custom config lives between LOCAL_DEPS=() and WORKSPACE_ROOT=... .
    Lines matching _PRESERVED_VAR_PATTERNS are preserved across rollout regenerations.
    """
    preserved: list[str] = []
    in_custom_zone = False
    pending_comments: list[str] = []
    for line in existing_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("LOCAL_DEPS="):
            in_custom_zone = True
            continue
        if stripped.startswith("WORKSPACE_ROOT="):
            break
        if in_custom_zone:
            if stripped.startswith("#") or stripped == "":
                # Buffer comments — only emit if followed by a preserved variable
                pending_comments.append(line)
            elif _PRESERVED_VAR_PATTERNS.match(stripped):
                preserved.extend(pending_comments)
                pending_comments = []
                preserved.append(line)
            else:
                pending_comments = []
    return preserved


def _inject_preserved_lines(content: str, preserved: list[str]) -> str:
    """Re-inject preserved repo-specific config lines into regenerated content.

    Inserts them after the LOCAL_DEPS=() line and before the WORKSPACE_ROOT=... line.
    """
    if not preserved:
        return content
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    for line in lines:
        result.append(line)
        if line.strip().startswith("LOCAL_DEPS="):
            for p in preserved:
                result.append(p + "\n")
    return "".join(result)


def copy_quality_gates(
    repo_path: Path,
    repo_name: str,
    template_type: str,
    dry_run: bool,
    recalibrate: bool = False,
) -> bool:
    """Copy and customize quality-gates.sh. Returns True if created/updated."""
    scripts_dir = repo_path / "scripts"
    dest = scripts_dir / "quality-gates.sh"

    # Extract repo-specific config lines from existing file BEFORE overwriting
    existing_content = dest.read_text() if dest.exists() else ""
    preserved_lines = _extract_preserved_lines(existing_content)

    if template_type == "typescript":
        content = get_typescript_quality_gates_script()
    else:
        template_path = QG_LIBRARY_TEMPLATE if template_type == "library" else QG_SERVICE_TEMPLATE
        if not template_path.exists():
            print(f"  ⚠️ Template not found: {template_path}")
            return False
        content = template_path.read_text()

    source_dir = SOURCE_DIR_OVERRIDES.get(repo_name) or discover_source_dir(repo_path, repo_name)
    package_name = repo_name  # repo name for PACKAGE_NAME/SERVICE_NAME

    if template_type == "library":
        content = content.replace('PACKAGE_NAME="REPLACE_ME"', f'PACKAGE_NAME="{package_name}"')
        content = content.replace('SOURCE_DIR="REPLACE_ME"', f'SOURCE_DIR="{source_dir}"')
    elif template_type == "service":
        content = content.replace('SERVICE_NAME="REPLACE_ME"', f'SERVICE_NAME="{package_name}"')
        content = content.replace('SOURCE_DIR="REPLACE_ME"', f'SOURCE_DIR="{source_dir}"')

    # Re-inject preserved repo-specific config lines
    content = _inject_preserved_lines(content, preserved_lines)
    if preserved_lines:
        print(f"  🔒 Preserved {len(preserved_lines)} repo-specific config line(s)")

    # Compute MIN_COVERAGE = max(floor, actual-1) when recalibrating,
    # or max(floor, existing) to enforce floor without running tests.
    # Floor: library=80, service=70. Per-repo overrides in MIN_COVERAGE_OVERRIDES take precedence.
    floor = MIN_COVERAGE_OVERRIDES.get(
        repo_name, LIBRARY_COVERAGE_FLOOR if template_type == "library" else SERVICE_COVERAGE_FLOOR
    )
    existing_int: int | None = None
    if existing_content:
        m = re.search(r"^MIN_COVERAGE=(\d+)", existing_content, re.MULTILINE)
        if m:
            existing_int = int(m.group(1))

    if recalibrate:
        actual = measure_coverage(repo_path, source_dir)
        if actual is not None:
            new_coverage = max(floor, actual - 1)
            print(f"  📊 Actual coverage: {actual}% → MIN_COVERAGE={new_coverage} (floor={floor}%)")
        else:
            new_coverage = max(floor, existing_int) if existing_int is not None else floor
            print(f"  ⚠️  Could not measure coverage → MIN_COVERAGE={new_coverage} (floor fallback)")
    else:
        prev = existing_int if existing_int is not None else floor
        new_coverage = max(floor, prev)
        if prev < floor:
            print(f"  ⬆️  MIN_COVERAGE: {prev}% → {new_coverage}% (enforcing {floor}% floor)")

    content = re.sub(r"^MIN_COVERAGE=\d+", f"MIN_COVERAGE={new_coverage}", content, flags=re.MULTILINE)

    if dry_run:
        print(f"  [dry-run] Would write {dest}")
        return True

    scripts_dir.mkdir(parents=True, exist_ok=True)
    is_new = not dest.exists()
    if not is_new and dest.read_text() == content:
        print("  -- scripts/quality-gates.sh unchanged")
        return False
    dest.write_text(content)
    dest.chmod(0o755)
    print(f"  ✅ {'Created' if is_new else 'Updated'} scripts/quality-gates.sh")
    return True


def copy_setup_sh(repo_path: Path, dry_run: bool) -> bool:
    """Copy setup.sh from PM. Returns True if created/updated."""
    if not SETUP_SH_SOURCE.exists():
        print(f"  ⚠️ setup.sh not found: {SETUP_SH_SOURCE}")
        return False
    dest = repo_path / "scripts" / "setup.sh"
    new_content = SETUP_SH_SOURCE.read_text()
    if dry_run:
        print(f"  [dry-run] Would copy setup.sh to {dest}")
        return True
    scripts_dir = repo_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    is_new = not dest.exists()
    if not is_new and dest.read_text() == new_content:
        print("  -- scripts/setup.sh unchanged")
        return False
    dest.write_text(new_content)
    dest.chmod(0o755)
    print(f"  ✅ {'Created' if is_new else 'Updated'} scripts/setup.sh")
    return True


# QG sentinels are generated locally by quality-gates.sh and must never be
# committed. They were added to the templates on 2026-06-05, so any repo whose
# .gitignore was created before then never received them (this function used to
# be create-once). Re-assert them on every rollout so existing files don't drift
# and leak the sentinels (an untracked sentinel makes the worktree read dirty ->
# slot-cron-ff-pull.sh skips the repo). SSOT: CLAUDE.md "Generated artifacts + QG
# sentinels are gitignored" + scripts/propagation/templates/gitignore-python.txt.
QG_SENTINEL_PATTERNS = (".qg_last_passed_sha", ".qg_content_sentinel")
QG_SENTINEL_BLOCK = (
    "\n# QG sentinels — generated locally by quality-gates.sh, NEVER committed\n"
    '# (CLAUDE.md "Generated artifacts + QG sentinels are gitignored" + cicd_contract_hardening item H)\n'
    ".qg_last_passed_sha\n"
    ".qg_content_sentinel\n"
)


def ensure_ignore_files(repo_path: Path, template_type: str, dry_run: bool) -> bool:
    """Create .cursorignore/.gitignore from templates if missing, and re-assert
    the QG-sentinel ignore block in an existing .gitignore that predates it."""
    if template_type == "typescript":
        cursorignore_src = CURSORIGNORE_NODE
        gitignore_src = GITIGNORE_NODE
    else:
        cursorignore_src = CURSORIGNORE_PYTHON
        gitignore_src = GITIGNORE_PYTHON

    updated = False
    for name, src in [(".cursorignore", cursorignore_src), (".gitignore", gitignore_src)]:
        dest = repo_path / name
        if not dest.exists() and src.exists():
            if dry_run:
                print(f"  [dry-run] Would create {name}")
            else:
                dest.write_text(src.read_text())
                print(f"  ✅ Created {name}")
            updated = True

    # Drift-repair: ensure an existing .gitignore ignores the QG sentinels.
    gitignore_dest = repo_path / ".gitignore"
    if gitignore_dest.exists():
        text = gitignore_dest.read_text()
        if any(pat not in text for pat in QG_SENTINEL_PATTERNS):
            if dry_run:
                print("  [dry-run] Would append QG-sentinel block to .gitignore")
            else:
                if text and not text.endswith("\n"):
                    text += "\n"
                gitignore_dest.write_text(text + QG_SENTINEL_BLOCK)
                print("  ✅ Appended QG-sentinel block to .gitignore")
            updated = True
    return updated


def ensure_bypass_audit(repo_path: Path, doc_standard: str | None, dry_run: bool) -> bool:
    """Create QUALITY_GATE_BYPASS_AUDIT.md stub if doc_standard requires it."""
    if not doc_standard or doc_standard not in BYPASS_AUDIT_DOC_STANDARDS:
        return False
    dest = repo_path / "QUALITY_GATE_BYPASS_AUDIT.md"
    if dest.exists():
        return False
    if dry_run:
        print("  [dry-run] Would create QUALITY_GATE_BYPASS_AUDIT.md")
        return True
    dest.write_text(get_quality_gate_bypass_audit_stub())
    print("  ✅ Created QUALITY_GATE_BYPASS_AUDIT.md stub")
    return True


def copy_ui_integration_test(repo_path: Path, repo_name: str, dry_run: bool) -> bool:
    """Copy UI integration test from template. Returns True if created/updated."""
    if not UI_API_MAPPING_PATH.exists() or not UI_INTEGRATION_TEMPLATE.exists():
        return False
    with open(UI_API_MAPPING_PATH) as f:
        mapping = json.load(f)
    config = mapping.get(repo_name)
    if not config:
        return False
    api_name = config.get("api_name", "api")
    env_var = config.get("env_var", "INTEGRATION_TEST_API_URL")
    default_port = config.get("default_port", "8000")
    api_path = config.get("api_path", "")  # noqa: qg-empty-fallback
    endpoints = config.get("endpoints", ["/health"])
    dual_base = config.get("dual_base", False)
    endpoint_lines = []
    for ep in endpoints:
        endpoint_lines.append(
            '  it("GET ' + ep + ' returns ok or 401", async () => {\n'
            "    if (!apiAvailable) return;\n"
            '    const { ok, status } = await fetchApi("' + ep + '");\n'
            "    expect(ok || status === 401).toBe(true);\n"
            "  });"
        )
    if dual_base:
        env_var_inf = config.get("env_var_inference", "INTEGRATION_TEST_ML_INFERENCE_URL")
        default_port_inf = config.get("default_port_inference", "8003")
        for ep in config.get("endpoints_inference", ["/models"]):
            endpoint_lines.append(
                '  it("GET (inference) ' + ep + ' returns ok or 401", async () => {\n'
                "    if (!apiAvailable) return;\n"
                '    const base = (typeof process !== "undefined" && process.env.'
                + env_var_inf
                + ') || "http://localhost:'
                + default_port_inf
                + '";\n'
                '    const res = await fetch(base + "' + ep + '", { signal: AbortSignal.timeout(2000) });\n'
                "    expect(res.ok || res.status === 401).toBe(true);\n"
                "  });"
            )
    endpoint_tests = "\n\n".join(endpoint_lines)
    template = UI_INTEGRATION_TEMPLATE.read_text()
    content_out = template.replace("{{UI_NAME}}", repo_name)
    content_out = content_out.replace("{{API_NAME}}", api_name)
    content_out = content_out.replace("{{ENV_VAR}}", env_var)
    content_out = content_out.replace("{{DEFAULT_PORT}}", default_port)
    content_out = content_out.replace("{{API_PATH}}", api_path)
    content_out = content_out.replace("{{ENDPOINT_TESTS}}", endpoint_tests)
    dest = repo_path / "tests" / "integration" / "api.integration.test.ts"
    if dry_run:
        print("  [dry-run] Would write " + str(dest))
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    existed = dest.exists()
    if existed and dest.read_text() == content_out:
        return False
    dest.write_text(content_out)
    print("  ✅ " + ("Created" if not existed else "Updated") + " tests/integration/api.integration.test.ts")
    pkg_path = repo_path / "package.json"
    if pkg_path.exists():
        pkg = json.loads(pkg_path.read_text())
        scripts = pkg.get("scripts", {})  # noqa: qg-empty-fallback
        if "test:integration" not in scripts:
            scripts["test:integration"] = "vitest run tests/integration"
            pkg["scripts"] = scripts
            pkg_path.write_text(json.dumps(pkg, indent=2))
            print("  ✅ Added test:integration script to package.json")
    for vf in ["vitest.config.ts", "vite.config.ts"]:
        vitest_path = repo_path / vf
        if vitest_path.exists():
            vc = vitest_path.read_text()
            if "tests/integration" not in vc and "include" in vc:
                vc = vc.replace(
                    '"tests/unit/**/*.test.{ts,tsx}"',
                    '"tests/unit/**/*.test.{ts,tsx}", "tests/integration/**/*.integration.test.{ts,tsx}"',
                )
                vc = vc.replace(
                    '"src/**/*.test.{ts,tsx}"',
                    '"src/**/*.test.{ts,tsx}", "tests/integration/**/*.integration.test.{ts,tsx}"',
                )
                if "tests/integration" in vc:
                    vitest_path.write_text(vc)
                    print("  ✅ Updated vitest include for integration tests")
            break
    return True


def propagate_eslint_config(repo_path: Path, dry_run: bool) -> bool:
    """Propagate eslint.config.base.js from PM into a UI repo.

    Strategy: if the repo has an eslint.config.base.js already and it matches the PM SSOT,
    skip. If it differs or is absent, create/update it. Never touch a hand-crafted
    eslint.config.js or .eslintrc.cjs — those are left as-is (per-repo overrides are valid).
    Returns True if a file was created or updated.
    """
    if not ESLINT_CONFIG_BASE.exists():
        print(f"  ⚠️ eslint.config.base.js not found at {ESLINT_CONFIG_BASE} — skipping ESLint propagation")
        return False

    source_content = ESLINT_CONFIG_BASE.read_text()
    dest = repo_path / "eslint.config.base.js"

    if dest.exists() and dest.read_text() == source_content:
        return False

    if dry_run:
        print(f"  [dry-run] Would {'create' if not dest.exists() else 'update'} eslint.config.base.js")
        return True

    existed = dest.exists()
    dest.write_text(source_content)
    print(f"  ✅ {'Created' if not existed else 'Updated'} eslint.config.base.js (SSOT from PM)")
    return True


def process_repo(
    repo_name: str,
    repo_info: JsonDict,
    workspace_root: Path,
    dry_run: bool,
    recalibrate: bool = False,
    skip_missing: bool = False,
) -> bool:
    """Process a single repository. Returns True on success."""
    status = repo_info.get("status", "active")
    if status in SKIP_STATUSES:
        print(f"\n⏭️ Skipping {repo_name} (status={status})")
        return True
    if repo_name in ROLLOUT_SKIP_REPOS:
        print(f"\n⏭️ Skipping {repo_name} (has own quality-gates, not overwritten)")
        return True
    repo_type = _jstr(repo_info.get("type"), "service")
    doc_standard_raw = repo_info.get("doc_standard")
    doc_standard: str | None = None if doc_standard_raw is None else _jstr(doc_standard_raw)
    template_type = select_template_type(repo_type)
    repo_path = workspace_root / repo_name
    if not repo_path.exists():
        if skip_missing:
            print(f"\n⚠️ {repo_name}: directory not found — skipping (--skip-missing)")
            return True
        print(f"\n⚠️ {repo_name}: directory not found at {repo_path}")
        return False
    # Override: package.json + no pyproject = TypeScript (manifest may mislabel UI as library)
    has_package_json = (repo_path / "package.json").exists()
    has_pyproject = (repo_path / "pyproject.toml").exists()
    if has_package_json and not has_pyproject:
        template_type = "typescript"

    # UI repos: need package.json
    if template_type == "typescript":
        if not (repo_path / "package.json").exists():
            print(f"\n⚠️ {repo_name}: no package.json (not a UI repo?)")
            return False
    else:
        if not (repo_path / "pyproject.toml").exists():
            print(f"\n⚠️ {repo_name}: no pyproject.toml (not a Python repo?)")
            return False

    print(f"\n🔧 Processing {repo_name} (type={repo_type}, template={template_type})")

    changed = False
    changed |= copy_quality_gates(repo_path, repo_name, template_type, dry_run, recalibrate)
    changed |= copy_setup_sh(repo_path, dry_run)
    changed |= ensure_ignore_files(repo_path, template_type, dry_run)
    changed |= ensure_bypass_audit(repo_path, doc_standard, dry_run)
    if template_type == "typescript":
        changed |= copy_ui_integration_test(repo_path, repo_name, dry_run)
        changed |= propagate_eslint_config(repo_path, dry_run)

    if not changed:
        print(f"  ✅ {repo_name} already has all quality gate files")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Roll out quality gates from workspace manifest")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument("--repo", type=str, help="Process only this repository")
    parser.add_argument(
        "--recalibrate",
        action="store_true",
        help=(
            "Measure actual coverage per repo (runs pytest --cov) and set "
            "MIN_COVERAGE = max(floor, actual-1). Without this flag, enforces "
            "floor only: max(floor, existing). floor=80 library, 70 service."
        ),
    )
    parser.add_argument(
        "--skip-missing",
        action="store_true",
        help=(
            "Warn (instead of error) when a manifest repo directory is not found locally. "
            "Useful on partial checkouts or new-machine setups where not all repos are cloned yet."
        ),
    )
    parser.add_argument(
        "--ui-only",
        action="store_true",
        help="Process only TypeScript/UI repos (type=ui or package.json without pyproject.toml).",
    )
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest not found: {MANIFEST_PATH}")
        return 1

    with open(MANIFEST_PATH) as f:
        manifest = cast(JsonDict, json.load(f))

    repos_raw = _jdict(manifest.get("repositories"))
    repositories = cast(dict[str, JsonDict], repos_raw) if repos_raw else {}
    dry_run = cast(bool, args.dry_run)
    recalibrate = cast(bool, args.recalibrate)
    skip_missing = cast(bool, args.skip_missing)
    ui_only = cast(bool, args.ui_only)
    repo_filter = cast(str | None, args.repo)
    if repo_filter is not None:
        if repo_filter not in repositories:
            print(f"❌ Repository not in manifest: {repo_filter}")
            return 1
        repositories = {repo_filter: repositories[repo_filter]}

    if ui_only:
        repositories = {
            name: info for name, info in repositories.items() if _jstr(cast(JsonDict, info).get("type")) == "ui"
        }
        print(f"🎨 --ui-only: filtered to {len(repositories)} UI repos")

    print("🚀 Rolling out quality gates (unified)")
    print(f"📁 Workspace: {WORKSPACE_ROOT}")
    print(f"📋 Repositories: {len(repositories)}")
    if dry_run:
        print("🔍 Dry run — no files will be written")
    if recalibrate:
        print("📊 Recalibrate mode: measuring actual coverage per repo (runs pytest)")
    if skip_missing:
        print("⚠️  --skip-missing: missing repo directories will warn, not error")

    success = 0
    errors = 0
    for repo_name in sorted(repositories.keys()):
        try:
            if process_repo(repo_name, repositories[repo_name], WORKSPACE_ROOT, dry_run, recalibrate, skip_missing):
                success += 1
            else:
                errors += 1
        except (OSError, ValueError) as e:
            print(f"  ❌ Error: {e}")
            errors += 1

    print("\n🎉 Rollout complete!")
    print(f"  ✅ Success: {success}")
    print(f"  ❌ Errors: {errors}")

    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
