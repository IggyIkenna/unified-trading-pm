# Epic: uac_master
# Lifecycle: permanent
# Delete-when: NA
"""API/UI coverage audit.

Compares what the unified-trading-api and client-reporting-api expose
(per the unified OpenAPI spec) vs what the UI actually consumes.

Uses subprocess `rg` (ripgrep) for scanning UI source files — never Python
`re` on file contents — to avoid catastrophic backtracking on large files.

Usage:
    python audit_api_ui_coverage.py --workspace-root PATH --output-dir PATH [--verbose]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Services whose endpoints we audit for UI coverage.
TARGET_SERVICES: set[str] = {
    "unified-trading-api",
    "client-reporting-api",
}

# Paths to skip — health/readiness probes are infrastructure, not UI.
SKIP_PATH_SUFFIXES: tuple[str, ...] = (
    "/health",
    "/readiness",
    "/openapi.json",
    "/docs",
    "/redoc",
)

# rg glob excludes applied to UI scanning.
RG_GLOB_EXCLUDES: list[str] = [
    "--glob",
    "!node_modules/**",
    "--glob",
    "!.next/**",
    "--glob",
    "!dist/**",
    "--glob",
    "!build/**",
    "--glob",
    "!*.test.*",
    "--glob",
    "!*.spec.*",
    "--glob",
    "!__tests__/**",
]

RG_TIMEOUT_SECONDS = 10


# ---------------------------------------------------------------------------
# OpenAPI spec extraction
# ---------------------------------------------------------------------------


def _extract_api_endpoints(spec_path: Path) -> dict[str, list[str]]:
    """Extract endpoint paths grouped by service from the OpenAPI spec.

    Returns mapping of service_name -> sorted list of paths.
    """
    with open(spec_path) as f:
        spec = json.load(f)

    paths_raw = spec.get("paths")
    paths: dict[str, object] = paths_raw if isinstance(paths_raw, dict) else {}
    service_paths: dict[str, list[str]] = {}

    for path in sorted(paths.keys()):
        # Determine which service this path belongs to via prefix.
        service_name = ""
        for svc in TARGET_SERVICES:
            if path.startswith(f"/{svc}/"):
                service_name = svc
                break

        if not service_name:
            continue

        # Skip infrastructure endpoints.
        if any(path.endswith(suffix) for suffix in SKIP_PATH_SUFFIXES):
            continue

        service_paths.setdefault(service_name, []).append(path)

    return service_paths


# ---------------------------------------------------------------------------
# UI scanning helpers
# ---------------------------------------------------------------------------


def _run_rg(
    pattern: str,
    search_path: Path,
    extra_args: list[str] | None = None,
) -> list[tuple[str, str]]:
    """Run ripgrep returning (file_path, matched_line) pairs."""
    cmd: list[str] = [
        "rg",
        "--no-heading",
        "--with-filename",
        "--no-messages",
    ]
    cmd.extend(RG_GLOB_EXCLUDES)
    if extra_args:
        cmd.extend(extra_args)
    cmd.append(pattern)
    cmd.append(str(search_path))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=RG_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        logger.warning("rg timed out for pattern (first 80 chars): %s", pattern[:80])
        return []
    except FileNotFoundError:
        logger.error("ripgrep (rg) not found — please install it")
        sys.exit(1)

    pairs: list[tuple[str, str]] = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        colon_idx = line.find(":")
        if colon_idx > 0:
            pairs.append((line[:colon_idx], line[colon_idx + 1 :]))
    return pairs


def _extract_gateway_path_map(typed_fetch_path: Path) -> dict[str, str]:
    """Parse GatewayPathMap from typed-fetch.ts to get UI path -> backend path mapping."""
    mapping: dict[str, str] = {}
    if not typed_fetch_path.exists():
        logger.warning("typed-fetch.ts not found at %s", typed_fetch_path)
        return mapping

    content = typed_fetch_path.read_text()
    # Match lines like: "/api/positions/active": "/unified-trading-api/positions/active";
    pattern = re.compile(r'"(/api/[^"]+)":\s*"(/[^"]+)"')
    for match in pattern.finditer(content):
        ui_path = match.group(1)
        backend_path = match.group(2)
        mapping[ui_path] = backend_path

    return mapping


def _extract_rewrite_rules(next_config_path: Path) -> dict[str, str]:
    """Extract rewrite rules from next.config.mjs.

    Returns mapping of UI source pattern -> destination pattern.
    """
    rewrites: dict[str, str] = {}
    if not next_config_path.exists():
        logger.warning("next.config.mjs not found at %s", next_config_path)
        return rewrites

    content = next_config_path.read_text()
    # Match lines like: { source: "/api/reporting/:path*", destination: `${reportingBase}/api/reporting/:path*` },
    pattern = re.compile(r'source:\s*"([^"]+)".*?destination:\s*[`"]([^`"]+)[`"]')
    for match in pattern.finditer(content):
        rewrites[match.group(1)] = match.group(2)

    return rewrites


def _scan_ui_consumed_paths(ui_root: Path) -> set[str]:
    """Scan the UI codebase for consumed API endpoint paths.

    Looks in hooks/api/, lib/api/, and components/ for patterns like:
    - "/api/..." string literals
    - fetch("/api/...")
    - useSWR("/api/...")
    - typedFetch<...>("/api/...")
    - apiFetch("/api/...")
    """
    consumed: set[str] = set()

    # Directories to scan.
    scan_dirs: list[Path] = []
    for subdir in ("hooks/api", "hooks", "lib/api", "lib", "components", "app"):
        candidate = ui_root / subdir
        if candidate.is_dir():
            scan_dirs.append(candidate)

    if not scan_dirs:
        logger.warning("No UI source directories found in %s", ui_root)
        return consumed

    # Pattern: any quoted string containing "/api/" path.
    for scan_dir in scan_dirs:
        pairs = _run_rg(
            r'["\x27`]/api/[^\s"\x27`]*',
            scan_dir,
            extra_args=["--type", "ts", "--type", "tsx", "--type-add", "tsx:*.tsx"],
        )
        for _, matched_line in pairs:
            # Extract all /api/... paths from the line.
            for m in re.finditer(r'["\x27`](/api/[^\s"\x27`,:;)}\]]+)', matched_line):
                path = m.group(1)
                # Normalise: strip trailing slashes and query params.
                path = path.split("?")[0].rstrip("/")
                # Skip paths that are clearly template literals with ${...}.
                if "${" in path:
                    continue
                # Skip paths that are just "/api" with no further segment.
                if path == "/api":
                    continue
                consumed.add(path)

    return consumed


def _normalise_api_path(path: str) -> str:
    """Strip the service prefix to get the route-relative path.

    e.g. "/unified-trading-api/positions/active" -> "/positions/active"
         "/client-reporting-api/api/reporting/trades" -> "/api/reporting/trades"
    """
    for svc in TARGET_SERVICES:
        prefix = f"/{svc}"
        if path.startswith(prefix):
            remainder = path[len(prefix) :]
            return remainder if remainder else "/"
    return path


def _strip_path_params(path: str) -> str:
    """Replace {param} segments with a wildcard for matching.

    e.g. "/api/v1/clients/{client_id}" -> "/api/v1/clients/:path*"
    """
    return re.sub(r"\{[^}]+\}", ":path*", path)


# ---------------------------------------------------------------------------
# Matching logic
# ---------------------------------------------------------------------------


def _match_endpoints(  # noqa: C901
    api_endpoints: dict[str, list[str]],
    ui_paths: set[str],
    gateway_map: dict[str, str],
    rewrite_rules: dict[str, str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Compare API endpoints against UI consumed paths.

    Returns (api_not_consumed, ui_no_backend).

    Matching strategy (API -> UI direction):
    1. Direct gateway map match (typed-fetch.ts GatewayPathMap).
    2. Exact UI path match: /api{normalised_route} in ui_paths.
    3. Path-param-tolerant match: /api{stripped_route} prefix in ui_paths.

    We deliberately do NOT use the catch-all rewrite rule (/api/:path* -> apiBase)
    to claim coverage — that would make every endpoint appear consumed. We only
    count an endpoint as consumed when the UI explicitly references its path.
    """
    # Build the set of all backend paths the UI references (via gateway map).
    ui_backend_paths: set[str] = set()
    for _ui_path, backend_path in gateway_map.items():
        ui_backend_paths.add(backend_path)

    # Flatten all API paths and build normalised lookup structures.
    all_api_paths: list[str] = []
    api_normalised_routes: set[str] = set()

    for _svc, paths in api_endpoints.items():
        for path in paths:
            all_api_paths.append(path)
            normalised = _normalise_api_path(path)
            api_normalised_routes.add(normalised)
            stripped = _strip_path_params(normalised)
            if stripped != normalised:
                api_normalised_routes.add(stripped)

    # Collect all specific rewrite prefixes (excluding the catch-all /api/:path*).
    specific_rewrite_sources: list[str] = []
    for rewrite_source in rewrite_rules:
        prefix = rewrite_source.replace(":path*", "").rstrip("/")
        # Skip the catch-all "/api" rewrite — it covers everything.
        if prefix and prefix != "/api":
            specific_rewrite_sources.append(prefix)

    # -------------------------------------------------------------------
    # Direction 1: For each API endpoint, check if the UI references it.
    # -------------------------------------------------------------------
    api_not_consumed: list[dict[str, str]] = []

    for spec_path in all_api_paths:
        matched = False
        normalised = _normalise_api_path(spec_path)

        # 1. Direct match via gateway map.
        if spec_path in ui_backend_paths:
            matched = True

        # 2. Exact UI path match: the UI uses /api/X, spec has /svc/X.
        if not matched:
            ui_equivalent = f"/api{normalised}"
            if ui_equivalent in ui_paths:
                matched = True

        # 3. Path-param-tolerant: /api/v1/clients/{client_id} matches if
        #    UI has /api/v1/clients or /api/v1/clients/someId.
        if not matched:
            stripped = _strip_path_params(normalised)
            if stripped != normalised:
                ui_stripped = f"/api{stripped}"
                # Check prefix match — UI may call /api/v1/clients/123.
                parent = "/".join(normalised.split("/")[:-1])
                ui_parent = f"/api{parent}"
                for up in ui_paths:
                    if up == ui_stripped or up.startswith(ui_parent + "/"):
                        matched = True
                        break

        # 4. Reporting paths: client-reporting-api has /api/reporting/X,
        #    UI calls /api/reporting/X (rewritten by specific rule).
        if not matched and normalised.startswith("/api/") and normalised in set(ui_paths):
            matched = True

        if not matched:
            service = ""
            for svc in TARGET_SERVICES:
                if spec_path.startswith(f"/{svc}/"):
                    service = svc
                    break
            api_not_consumed.append(
                {
                    "path": spec_path,
                    "service": service,
                }
            )

    # -------------------------------------------------------------------
    # Direction 2: For each UI path, check if there's a backend match.
    # -------------------------------------------------------------------
    # Only consider UI paths that would route to our target services.
    # Paths matching specific rewrite rules (e.g. /api/reporting/*, /api/auth/*,
    # /api/deployments/*) go to non-target services — exclude them unless the
    # rewrite destination is one of our target services.

    # Build set of rewrite prefixes that route to non-target services.
    non_target_rewrite_prefixes: list[str] = []
    for rewrite_source, rewrite_dest in rewrite_rules.items():
        prefix = rewrite_source.replace(":path*", "").rstrip("/")
        if not prefix or prefix == "/api":
            continue
        # Check if destination routes to a target service.
        routes_to_target = False
        for svc in TARGET_SERVICES:
            if svc in rewrite_dest:
                routes_to_target = True
                break
        if not routes_to_target:
            non_target_rewrite_prefixes.append(prefix)

    # Also build a flat set of all spec paths for quick lookup.
    all_spec_paths_flat: set[str] = set()
    for paths in api_endpoints.values():
        all_spec_paths_flat.update(paths)

    ui_no_backend: list[dict[str, str]] = []
    for ui_path in sorted(ui_paths):
        # Skip non-/api paths and meta paths.
        if not ui_path.startswith("/api/"):
            continue
        if ui_path in ("/api/*", "/api/..."):
            continue

        # Skip paths that route to non-target services via specific rewrites.
        routed_elsewhere = False
        for prefix in non_target_rewrite_prefixes:
            if ui_path.startswith(prefix):
                routed_elsewhere = True
                break
        if routed_elsewhere:
            continue

        matched = False

        # Check gateway map.
        if ui_path in gateway_map:
            backend = gateway_map[ui_path]
            if backend in all_spec_paths_flat:
                matched = True

        # Check if /api/X corresponds to /svc/X for any target service.
        if not matched:
            suffix = ui_path[4:]  # strip "/api"
            for svc in TARGET_SERVICES:
                candidate = f"/{svc}{suffix}"
                if candidate in all_spec_paths_flat:
                    matched = True
                    break

        # Check against normalised API routes (handles path param variations).
        if not matched:
            suffix = ui_path[4:]  # strip "/api"
            for route in api_normalised_routes:
                # Exact match.
                if suffix == route:
                    matched = True
                    break
                # The UI path might be a specific instance of a parameterised route.
                # e.g. UI has /api/v1/clients and spec has /v1/clients/{client_id}.
                route_stripped = _strip_path_params(route)
                if route_stripped != route and suffix == route_stripped:
                    matched = True
                    break
                # UI path is a parent of a parameterised spec path.
                route_parent = "/".join(route.split("/")[:-1])
                if route_parent and suffix == route_parent:
                    matched = True
                    break

        if not matched:
            target_hint = "unified-trading-api (catch-all)"
            for prefix in specific_rewrite_sources:
                if ui_path.startswith(prefix):
                    target_hint = rewrite_rules.get(
                        f"{prefix}/:path*",
                        rewrite_rules.get(f"{prefix}:path*", "unknown"),
                    )
                    break
            ui_no_backend.append(
                {
                    "path": ui_path,
                    "target_hint": target_hint,
                }
            )

    return api_not_consumed, ui_no_backend


# ---------------------------------------------------------------------------
# Main audit logic
# ---------------------------------------------------------------------------


def run_audit(
    workspace_root: Path,
    output_dir: Path,
    verbose: bool = False,
) -> None:
    """Run the API/UI coverage audit."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    start_time = time.time()

    # 1. Read the OpenAPI spec.
    spec_path = workspace_root / "unified-api-contracts/openapi/unified-trading-system.openapi.json"
    if not spec_path.exists():
        logger.error("OpenAPI spec not found at %s", spec_path)
        sys.exit(1)

    logger.info("Reading OpenAPI spec from %s", spec_path)
    api_endpoints = _extract_api_endpoints(spec_path)

    total_api = sum(len(paths) for paths in api_endpoints.values())
    for svc, paths in sorted(api_endpoints.items()):
        logger.info("  %s: %d endpoints", svc, len(paths))

    # 2. Read the UI gateway path map.
    ui_root = workspace_root / "unified-trading-system-ui"
    typed_fetch_path = ui_root / "lib/api/typed-fetch.ts"
    logger.info("Reading GatewayPathMap from %s", typed_fetch_path)
    gateway_map = _extract_gateway_path_map(typed_fetch_path)
    logger.info("  %d gateway mappings found", len(gateway_map))

    # 3. Read rewrite rules from next.config.mjs.
    next_config_path = ui_root / "next.config.mjs"
    logger.info("Reading rewrite rules from %s", next_config_path)
    rewrite_rules = _extract_rewrite_rules(next_config_path)
    logger.info("  %d rewrite rules found", len(rewrite_rules))

    # 4. Scan UI for consumed endpoint paths.
    logger.info("Scanning UI source for consumed API paths...")
    ui_paths = _scan_ui_consumed_paths(ui_root)
    logger.info("  %d unique UI paths found", len(ui_paths))

    if verbose:
        for p in sorted(ui_paths):
            logger.debug("  UI path: %s", p)

    # 5. Match and compare.
    api_not_consumed, ui_no_backend = _match_endpoints(
        api_endpoints,
        ui_paths,
        gateway_map,
        rewrite_rules,
    )

    elapsed = time.time() - start_time

    # 6. Write JSON report.
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "_meta": {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "workspace_root": str(workspace_root),
            "spec_path": str(spec_path),
            "elapsed_seconds": round(elapsed, 1),
            "target_services": sorted(TARGET_SERVICES),
        },
        "summary": {
            "api_endpoints_total": total_api,
            "ui_consumed": total_api - len(api_not_consumed),
            "api_not_consumed": len(api_not_consumed),
            "ui_no_backend": len(ui_no_backend),
            "gateway_mappings": len(gateway_map),
            "rewrite_rules": len(rewrite_rules),
            "ui_paths_scanned": len(ui_paths),
        },
        "api_not_consumed_by_ui": sorted(api_not_consumed, key=lambda x: x["path"]),
        "ui_endpoints_no_backend": sorted(ui_no_backend, key=lambda x: x["path"]),
    }

    json_path = output_dir / "api-ui-coverage-audit.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)
    logger.info("JSON report: %s", json_path)

    # 7. Print summary.
    print()
    print(f"API/UI coverage audit complete in {elapsed:.1f}s")
    print(f"  Target services:       {', '.join(sorted(TARGET_SERVICES))}")
    print(f"  API endpoints (total): {total_api}")
    print(f"  UI consumed:           {total_api - len(api_not_consumed)}")
    print(f"  API not consumed by UI:{len(api_not_consumed):>4}")
    print(f"  UI paths w/o backend:  {len(ui_no_backend):>4}")

    if api_not_consumed:
        print()
        print("  API endpoints NOT consumed by UI:")
        for item in sorted(api_not_consumed, key=lambda x: x["path"])[:30]:
            print(f"    [{item['service']}] {item['path']}")
        if len(api_not_consumed) > 30:
            print(f"    ... and {len(api_not_consumed) - 30} more")

    if ui_no_backend:
        print()
        print("  UI paths with NO backend match:")
        for item in sorted(ui_no_backend, key=lambda x: x["path"])[:20]:
            print(f"    {item['path']}")
        if len(ui_no_backend) > 20:
            print(f"    ... and {len(ui_no_backend) - 20} more")

    print(f"\nReport written to: {json_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit API/UI coverage: compare OpenAPI spec vs UI consumption.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        required=True,
        help="Path to the multi-repo workspace root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write the JSON report.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    args = parser.parse_args()

    workspace_root: Path = args.workspace_root.resolve()
    output_dir: Path = args.output_dir.resolve()

    if not workspace_root.is_dir():
        logger.error("Workspace root does not exist: %s", workspace_root)
        sys.exit(1)

    # Verify required paths exist.
    spec_path = workspace_root / "unified-api-contracts/openapi/unified-trading-system.openapi.json"
    if not spec_path.exists():
        logger.error("OpenAPI spec not found: %s", spec_path)
        sys.exit(1)

    ui_root = workspace_root / "unified-trading-system-ui"
    if not ui_root.is_dir():
        logger.error("UI repo not found: %s", ui_root)
        sys.exit(1)

    # Verify rg is available.
    try:
        subprocess.run(["rg", "--version"], capture_output=True, timeout=5)
    except FileNotFoundError:
        logger.error("ripgrep (rg) is not installed — please install it first")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        pass  # rg exists but was slow — fine

    run_audit(workspace_root, output_dir, verbose=args.verbose)


if __name__ == "__main__":
    main()
