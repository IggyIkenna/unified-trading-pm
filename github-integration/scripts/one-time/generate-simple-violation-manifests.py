#!/usr/bin/env python3
"""
Generate CODEX_VIOLATIONS_MANIFEST.md for each service repo using ripgrep.

Directly scans for violations using the same checks as quality-gates.sh.

Usage:
    python generate-simple-violation-manifests.py [--dry-run]
"""

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
# 13 service repos for Initial Cleanup
REPOS = [
    "execution-service",
    "strategy-service",
    "instruments-service",
    "unified-trading-services",
    "market-data-processing-service",
    "ml-training-service",
    "ml-inference-service",
    "features-delta-one-service",
    "features-volatility-service",
    "features-calendar-service",
    "features-onchain-service",
    "market-tick-data-handler",
    "unified-trading-deployment-v2",
]


def run_rg(pattern: str, service_dir: Path, type_filter: str = "py", exclude_globs: list[str] = None) -> list[str]:
    """Run ripgrep and return matching lines."""
    try:
        cmd = ["rg", pattern, "--type", type_filter, "--line-number", "."]

        # Add exclusion globs (match quality-gates.sh)
        if exclude_globs:
            for glob in exclude_globs:
                cmd.extend(["--glob", glob])

        result = subprocess.run(
            cmd,
            cwd=service_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Return non-empty lines (rg returns exit code 1 if no matches)
        return [line for line in result.stdout.split("\n") if line.strip()]
    except (ConnectionError, TimeoutError, OSError, ValueError):
        return []


def check_violations(service_dir: Path, service_name: str) -> dict:
    """Check all codex violations for a service."""
    violations = {}

    # Exclusions matching quality-gates.sh
    # Quality gates exclude: tests/**, scripts/**
    exclude_globs = ["!tests/**", "!scripts/**"]

    # Check 1: print() statements (exclude tests/ and scripts/ like quality gates)
    print_matches = run_rg(r"\bprint\(", service_dir, exclude_globs=exclude_globs)
    if print_matches:
        violations["print_statements"] = print_matches

    # Check 2: os.getenv() (exclude tests/ and scripts/ like quality gates)
    getenv_matches = run_rg(r"os\.getenv\(", service_dir, exclude_globs=exclude_globs)
    if getenv_matches:
        violations["os_getenv"] = getenv_matches

    # Check 3: datetime.now() without UTC (exclude tests/ and scripts/)
    datetime_matches = run_rg(r"datetime\.now\(\)", service_dir, exclude_globs=exclude_globs)
    if datetime_matches:
        violations["datetime_now"] = datetime_matches

    # Check 4: Bare except: (exclude tests/ and scripts/)
    except_matches = run_rg(r"except\s*:", service_dir, exclude_globs=exclude_globs)
    if except_matches:
        violations["bare_except"] = except_matches

    # Check 5: requests in async code (exclude tests/ and scripts/)
    has_requests = bool(run_rg(r"import\s+requests", service_dir, exclude_globs=exclude_globs))
    has_async = bool(run_rg(r"async\s+def", service_dir, exclude_globs=exclude_globs))
    if has_requests and has_async:
        requests_matches = run_rg(r"import\s+requests", service_dir, exclude_globs=exclude_globs)
        violations["requests_in_async"] = requests_matches

    # Check 6: asyncio.run() in loops (exclude tests/ and scripts/)
    asyncio_run_matches = run_rg(r"asyncio\.run\(", service_dir, exclude_globs=exclude_globs)
    if asyncio_run_matches:
        violations["asyncio_run_in_loops"] = asyncio_run_matches

    # Check 7: time.sleep() in async (exclude tests/ and scripts/)
    time_sleep_matches = run_rg(r"time\.sleep\(", service_dir, exclude_globs=exclude_globs)
    if time_sleep_matches and has_async:
        violations["time_sleep_in_async"] = time_sleep_matches

    # Check 8: Files >1500 lines (exclude tests/ and scripts/)
    large_files = []
    for py_file in service_dir.rglob("*.py"):
        rel_path = str(py_file.relative_to(service_dir))
        if (
            "__pycache__" in rel_path
            or ".venv" in rel_path
            or rel_path.startswith("tests/")
            or rel_path.startswith("scripts/")
        ):
            continue
        try:
            line_count = len(py_file.read_text().split("\n"))
            if line_count > 1500:
                large_files.append(f"{py_file.relative_to(service_dir)} ({line_count} lines)")
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            logger.warning("Skipping item during operation: %s", e)
            continue
    if large_files:
        violations["files_too_large"] = large_files

    # Check 9: Imports inside functions (exclude tests/ and scripts/)
    import_in_func_matches = []
    for py_file in service_dir.rglob("*.py"):
        rel_path = str(py_file.relative_to(service_dir))
        if (
            "__pycache__" in rel_path
            or ".venv" in rel_path
            or rel_path.startswith("tests/")
            or rel_path.startswith("scripts/")
        ):
            continue
        try:
            content = py_file.read_text()
            lines = content.split("\n")
            in_function = False
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("def ") or stripped.startswith("async def "):
                    in_function = True
                elif in_function and (stripped.startswith("import ") or stripped.startswith("from ")):
                    # Likely an import inside a function
                    import_in_func_matches.append(f"{py_file.relative_to(service_dir)}:{i}: {stripped[:80]}")
                elif not line.startswith(" ") and not line.startswith("\t") and stripped:
                    # Back at top level
                    in_function = False
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            logger.warning("Skipping item during operation: %s", e)
            continue
    if import_in_func_matches:
        violations["imports_in_functions"] = import_in_func_matches

    return violations


def generate_manifest(service_name: str, violations: dict) -> str:
    """Generate markdown manifest from violations."""
    if not violations:
        return f"""# Codex Violations Manifest: {service_name}

✅ **No violations found!** This service is compliant with all codex standards.

## Checked Standards

- ✅ No `print()` statements (use `logger.info()`)
- ✅ No `os.getenv()` usage (use config classes)
- ✅ No `datetime.now()` without UTC
- ✅ No bare `except:` clauses
- ✅ No `requests` library in async code (use `aiohttp`)
- ✅ No `asyncio.run()` in loops
- ✅ No `time.sleep()` in async functions
- ✅ All files <1500 lines
- ✅ All imports at top of file
"""

    total_count = sum(len(v) for v in violations.values())

    lines = [
        f"# Codex Violations Manifest: {service_name}",
        "",
        f"**Total Violations**: {total_count}",
        "",
        "## Summary",
        "",
    ]

    # Summary table
    if "print_statements" in violations:
        lines.append(f"- ❌ **{len(violations['print_statements'])} print() statements** (use `logger.info()`)")
    if "os_getenv" in violations:
        lines.append(f"- ❌ **{len(violations['os_getenv'])} os.getenv() calls** (use config classes)")
    if "datetime_now" in violations:
        lines.append(f"- ❌ **{len(violations['datetime_now'])} datetime.now() calls** (use UTC)")
    if "bare_except" in violations:
        lines.append(f"- ❌ **{len(violations['bare_except'])} bare except: clauses**")
    if "requests_in_async" in violations:
        lines.append("- ❌ **requests library in async code** (use `aiohttp`)")
    if "asyncio_run_in_loops" in violations:
        lines.append(f"- ❌ **{len(violations['asyncio_run_in_loops'])} asyncio.run() in loops**")
    if "time_sleep_in_async" in violations:
        lines.append(f"- ❌ **{len(violations['time_sleep_in_async'])} time.sleep() in async**")
    if "files_too_large" in violations:
        lines.append(f"- ❌ **{len(violations['files_too_large'])} files >1500 lines**")
    if "imports_in_functions" in violations:
        lines.append(f"- ❌ **{len(violations['imports_in_functions'])} imports inside functions**")

    lines.extend(["", "---", "", "## Detailed Violations", ""])

    # Detailed sections
    if "print_statements" in violations:
        lines.extend(
            [
                "### 1. Print Statements (use logger.info())",
                "",
                "Replace `print()` with `logger.info()` or appropriate logging level.",
                "",
                "```",
            ]
        )
        for match in violations["print_statements"][:50]:  # Limit to first 50
            lines.append(match)
        if len(violations["print_statements"]) > 50:
            lines.append(f"... and {len(violations['print_statements']) - 50} more")
        lines.extend(["```", ""])

    if "os_getenv" in violations:
        lines.extend(
            [
                "### 2. os.getenv() Usage (use config classes)",
                "",
                "Replace `os.getenv()` with proper config classes extending `UnifiedCloudServicesConfig`.",
                "",
                "```",
            ]
        )
        for match in violations["os_getenv"][:50]:
            lines.append(match)
        if len(violations["os_getenv"]) > 50:
            lines.append(f"... and {len(violations['os_getenv']) - 50} more")
        lines.extend(["```", ""])

    if "datetime_now" in violations:
        lines.extend(
            [
                "### 3. datetime.now() Without UTC",
                "",
                "Replace `datetime.now()` with `datetime.now(timezone.utc)`.",
                "",
                "```",
            ]
        )
        for match in violations["datetime_now"][:50]:
            lines.append(match)
        if len(violations["datetime_now"]) > 50:
            lines.append(f"... and {len(violations['datetime_now']) - 50} more")
        lines.extend(["```", ""])

    if "bare_except" in violations:
        lines.extend(
            [
                "### 4. Bare except: Clauses",
                "",
                "Specify exception types: `except (OSError, ValueError):` or specific exceptions.",
                "",
                "```",
            ]
        )
        for match in violations["bare_except"][:50]:
            lines.append(match)
        if len(violations["bare_except"]) > 50:
            lines.append(f"... and {len(violations['bare_except']) - 50} more")
        lines.extend(["```", ""])

    if "requests_in_async" in violations:
        lines.extend(
            [
                "### 5. requests Library in Async Code",
                "",
                "Replace `requests` with `aiohttp` for async HTTP calls.",
                "",
                "```",
            ]
        )
        for match in violations["requests_in_async"]:
            lines.append(match)
        lines.extend(["```", ""])

    if "asyncio_run_in_loops" in violations:
        lines.extend(
            [
                "### 6. asyncio.run() in Loops",
                "",
                "Use `await` instead of `asyncio.run()` inside async functions.",
                "",
                "```",
            ]
        )
        for match in violations["asyncio_run_in_loops"][:50]:
            lines.append(match)
        if len(violations["asyncio_run_in_loops"]) > 50:
            lines.append(f"... and {len(violations['asyncio_run_in_loops']) - 50} more")
        lines.extend(["```", ""])

    if "time_sleep_in_async" in violations:
        lines.extend(
            [
                "### 7. time.sleep() in Async Functions",
                "",
                "Replace `time.sleep()` with `await asyncio.sleep()`.",
                "",
                "```",
            ]
        )
        for match in violations["time_sleep_in_async"][:50]:
            lines.append(match)
        if len(violations["time_sleep_in_async"]) > 50:
            lines.append(f"... and {len(violations['time_sleep_in_async']) - 50} more")
        lines.extend(["```", ""])

    if "files_too_large" in violations:
        lines.extend(
            [
                "### 8. Files >1500 Lines (COD-SIZE)",
                "",
                "Split these files into smaller modules following Single Responsibility Principle.",
                "",
            ]
        )
        for f in violations["files_too_large"]:
            lines.append(f"- {f}")
        lines.append("")

    if "imports_in_functions" in violations:
        lines.extend(
            [
                "### 9. Imports Inside Functions",
                "",
                "Move all imports to the top of the file.",
                "",
                "```",
            ]
        )
        for match in violations["imports_in_functions"][:50]:
            lines.append(match)
        if len(violations["imports_in_functions"]) > 50:
            lines.append(f"... and {len(violations['imports_in_functions']) - 50} more")
        lines.extend(["```", ""])

    lines.extend(
        [
            "---",
            "",
            "## Next Steps",
            "",
            "1. Fix violations listed above",
            "2. Run `bash scripts/quality-gates.sh` to verify",
            "3. Run `bash scripts/quickmerge.sh` to create PR",
            "",
            "Quality gates will **BLOCK** merge if violations remain.",
        ]
    )

    return "\n".join(lines)


def main():
    dry_run = "--dry-run" in sys.argv

    script_dir = Path(__file__).parent
    codex_root = script_dir.parent.parent.parent.parent
    workspace_root = codex_root.parent

    print(f"Workspace root: {workspace_root}")
    print(f"Dry run: {dry_run}")
    print()

    print("=" * 80)
    print("Generating Codex Violation Manifests (using ripgrep)")
    print("=" * 80)
    print()

    results = {}

    for service in REPOS:
        service_dir = workspace_root / service

        if not service_dir.exists():
            print(f"⚠️  SKIP: {service} (directory not found)")
            continue

        print(f"Checking {service}...", end=" ", flush=True)

        # Check violations
        violations = check_violations(service_dir, service)
        total = sum(len(v) for v in violations.values())
        results[service] = violations

        if total == 0:
            print("✅ No violations")
        else:
            print(f"❌ {total} violations")

        # Generate manifest
        manifest_md = generate_manifest(service, violations)
        manifest_path = service_dir / "CODEX_VIOLATIONS_MANIFEST.md"

        if not dry_run:
            manifest_path.write_text(manifest_md)
            print(f"  → Saved to {manifest_path.name}")
        else:
            print(f"  → Would save to {manifest_path.name}")

    # Summary
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()

    total_violations = 0
    for service, violations in results.items():
        count = sum(len(v) for v in violations.values())
        total_violations += count
        status = "✅" if count == 0 else f"❌ {count} violations"
        print(f"  {service:40s} {status}")

    print()
    print(f"Total violations across all services: {total_violations}")
    print()

    if dry_run:
        print("🔍 DRY RUN: No files written. Re-run without --dry-run to save manifests.")
    else:
        print("✅ DONE: Manifests saved to each service directory.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
