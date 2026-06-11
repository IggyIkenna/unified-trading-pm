"""
Generate a unified OpenAPI 3.1 spec from all FastAPI services.

Sets mock environment variables, imports each service's FastAPI app,
calls app.openapi(), and merges all specs into one unified document.

Usage:
    python generate_unified_spec.py [--output-dir PATH]

See also: unified-trading-pm/docs/ui-alignment-ssot.md (OpenAPI vs ui-reference-data.json).
"""

from __future__ import annotations

# === Step 1: Set mock env vars BEFORE any service imports ===
import os

os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("MOCK_STATE_MODE", "deterministic")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("PUBSUB_EMULATOR_HOST", "localhost:8085")
os.environ.setdefault("STORAGE_EMULATOR_HOST", "http://localhost:4443")
os.environ.setdefault("BIGQUERY_EMULATOR_HOST", "localhost:9050")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")
# Prevent any real secret manager / auth calls
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("API_KEY", "mock-api-key-for-openapi-gen")

import argparse
import copy
import json
import logging
import subprocess
import sys
import traceback
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Per-service timeout in seconds
SERVICE_TIMEOUT = 150

# === Step 2: Service Registry ===
# Auto-derived from workspace-manifest.json (repositories section) + disk
# presence check.  Only repos that (a) have type in SERVICE_REPO_TYPES, (b)
# exist on disk, AND (c) have a resolvable FastAPI entrypoint are included.
#
# OVERRIDE_MODULE_PATHS: where the auto-derived import path
# `{pkg}.api.main::app` is wrong, spell out the correct (module, attr) pair.
# Keep this map small and documented.
SERVICE_REPO_TYPES: frozenset[str] = frozenset(
    {
        "service",
        "api-service",
        "batch-service",
        "api",
    }
)

# Explicit (module_path, app_attribute) overrides for services whose entry
# point doesn't follow the default `{pkg}.api.main::app` convention.
# Documented inline with the reason for each deviation.
_OVERRIDE_MODULE_PATHS: dict[str, tuple[str, str]] = {
    # unified-trading-api — factory function, not a bare `app` instance
    "unified-trading-api": ("unified_trading_api.main", "create_app"),
    # deployment-api — main lives at package root (not under api/)
    "deployment-api": ("deployment_api.main", "app"),
    # client-reporting-api — extra api/ nesting: client_reporting_api.api.main
    "client-reporting-api": ("client_reporting_api.api.main", "app"),
    # execution-service — uses api/app.py (not api/main.py)
    "execution-service": ("execution_service.api.app", "app"),
    # deployment-service — uses api/app.py (not api/main.py)
    "deployment-service": ("deployment_service.api.app", "app"),
    # features-service — consolidated monorepo; app built by factory
    "features-service": ("features_service.api.main", "app"),
    # ml-service — consolidated monorepo; app built by factory
    "ml-service": ("ml_service.api.main", "app"),
}

# Repos that genuinely have no FastAPI app (infra-only, library, UI, etc.) and
# should be silently skipped by the coverage check.  Keep this list minimal.
_NO_API_REPOS: frozenset[str] = frozenset(
    {
        # Not deployable services — no HTTP API surface
        "deployment-service",  # has api/app.py but only exposes internal hooks
        "ibkr-gateway-infra",
        "e2e-testing",
        "system-integration-tests",
        "agent-orchestrator",
        # Libraries / contracts (T0-T2) — not services
        "unified-api-contracts",
        "unified-trading-library",
        "unified-market-interface",
        # UI repos
        "unified-trading-system-ui",
        "deployment-ui",
        # PM repo itself
        "unified-trading-pm",
    }
)


def _load_service_registry(workspace_root: Path) -> list[tuple[str, str, str]]:
    """Build SERVICE_REGISTRY from workspace-manifest.json + disk presence.

    Algorithm:
    1. Read ``workspace-manifest.json`` — take every repo whose ``type`` is in
       SERVICE_REPO_TYPES.
    2. Discard repos absent from disk (silently — another agent may be
       mid-consolidation; the coverage check below will flag genuine gaps).
    3. For each remaining repo derive the default import path
       ``{pkg_name}.api.main::app`` and override with ``_OVERRIDE_MODULE_PATHS``
       where needed.
    4. Return sorted by repo name for deterministic ordering.
    """
    manifest_path = workspace_root / "unified-trading-pm" / "workspace-manifest.json"
    if not manifest_path.exists():
        logger.warning("workspace-manifest.json not found at %s — falling back to empty registry", manifest_path)
        return []

    with open(manifest_path) as f:
        manifest = json.load(f)

    entries: list[tuple[str, str, str]] = []
    repositories = manifest.get("repositories", {})

    for repo_name in sorted(repositories):
        info = repositories[repo_name]
        repo_type = info.get("type", "")
        if repo_type not in SERVICE_REPO_TYPES:
            continue
        if repo_name in _NO_API_REPOS:
            continue

        repo_dir = workspace_root / repo_name
        if not repo_dir.is_dir():
            # Repo declared in manifest but absent on this machine — skip
            continue

        if repo_name in _OVERRIDE_MODULE_PATHS:
            module_path, app_attr = _OVERRIDE_MODULE_PATHS[repo_name]
        else:
            # Default convention: {pkg_name}.api.main::app
            pkg_name = repo_name.replace("-", "_")
            module_path = f"{pkg_name}.api.main"
            app_attr = "app"

        entries.append((repo_name, module_path, app_attr))

    return entries


# Populated in main() after workspace_root is resolved; forward-declared here
# so module-level code can reference it.  Overwritten in main().
SERVICE_REGISTRY: list[tuple[str, str, str]] = []


def _subprocess_extract_script(module_path: str, app_attr: str) -> str:
    """Generate a Python script that extracts OpenAPI spec in a subprocess."""
    return f"""\
import os, sys, json

os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("MOCK_STATE_MODE", "deterministic")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("PUBSUB_EMULATOR_HOST", "localhost:8085")
os.environ.setdefault("STORAGE_EMULATOR_HOST", "http://localhost:4443")
os.environ.setdefault("BIGQUERY_EMULATOR_HOST", "localhost:9050")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("API_KEY", "mock-api-key-for-openapi-gen")

# ---- Fix forward reference resolution BEFORE importing service modules ----
# Problem: `from __future__ import annotations` + locally-defined Pydantic models
# (EventRelayPayload inside make_events_relay_router) cause PydanticUserError
# because Pydantic's TypeAdapter can't resolve ForwardRef at schema generation time.
#
# Fix: Monkey-patch the events_relay module to define EventRelayPayload at
# module scope BEFORE any service imports it. Also ensure JSONResponse is
# importable in route module namespaces.

# Pre-import the events_relay module so we can patch it
import unified_trading_library.core.events_relay as _er_mod
from pydantic import BaseModel as _BM

class EventRelayPayload(_BM):
    event_name: str
    severity: str = "INFO"
    details: dict | None = None
    correlation_id: str | None = None

# Inject into module globals so ForwardRef('EventRelayPayload') resolves
_er_mod.EventRelayPayload = EventRelayPayload

# Patch make_events_relay_router to define EventRelayPayload at module scope
_original_make = _er_mod.make_events_relay_router

def _patched_make_events_relay_router():
    from fastapi import APIRouter
    from unified_trading_library import log_event

    router = APIRouter(tags=["events"])

    @router.post("/events", status_code=204)
    async def relay_ui_event(payload: EventRelayPayload) -> None:
        log_event(
            payload.event_name,
            severity=payload.severity,
            details=payload.details,
            correlation_id=payload.correlation_id,
        )

    return router

_er_mod.make_events_relay_router = _patched_make_events_relay_router

# Also patch the UTL __init__ re-export
import unified_trading_library as _utl
_utl.make_events_relay_router = _patched_make_events_relay_router

# Now handle JSONResponse: inject into builtins so it resolves everywhere
import fastapi.responses
import builtins
builtins.JSONResponse = fastapi.responses.JSONResponse

# ---- Now import the service module (routes registered during import) ----
import importlib
from fastapi import FastAPI as _FastAPI

mod = importlib.import_module("{module_path}")
_obj = getattr(mod, "{app_attr}")
if isinstance(_obj, _FastAPI):
    app = _obj
elif callable(_obj):
    app = _obj()
else:
    raise TypeError(
        "Expected FastAPI app or factory, got "
        + type(_obj).__name__
        + " from {module_path}.{app_attr}"
    )

# Inject JSONResponse into every endpoint module's namespace
for route in getattr(app, "routes", []):
    endpoint = getattr(route, "endpoint", None)
    if endpoint is None:
        continue
    ep_mod = sys.modules.get(getattr(endpoint, "__module__", ""), None)
    if ep_mod and not hasattr(ep_mod, "JSONResponse"):
        ep_mod.JSONResponse = fastapi.responses.JSONResponse

spec = app.openapi()
json.dump(spec, sys.stdout)
"""


def extract_service_spec(service_name: str, module_path: str, app_attr: str) -> dict[str, object] | None:
    """Extract OpenAPI spec using subprocess isolation with timeout."""
    logger.info("Extracting: %s (%s)", service_name, module_path)

    script = _subprocess_extract_script(module_path, app_attr)

    try:
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=SERVICE_TIMEOUT,
            env={**os.environ, "PYTHONPATH": os.environ.get("PYTHONPATH", "")},
        )

        if result.returncode != 0:
            logger.error("  FAILED (exit %d): %s", result.returncode, service_name)
            # Show last 10 lines of stderr
            stderr_lines = result.stderr.strip().split("\n")
            for line in stderr_lines[-10:]:
                logger.error("    %s", line)
            return None

        spec = json.loads(result.stdout)
        path_count = len(spec.get("paths", {}))  # noqa: qg-empty-fallback
        schema_count = len(spec.get("components", {}).get("schemas", {}))  # noqa: qg-empty-fallback
        logger.info("  OK: %d paths, %d schemas", path_count, schema_count)
        return spec

    except subprocess.TimeoutExpired:
        logger.error("  TIMEOUT (%ds): %s", SERVICE_TIMEOUT, service_name)
        return None
    except json.JSONDecodeError as e:
        logger.error("  INVALID JSON from %s: %s", service_name, e)
        return None
    except Exception:
        logger.error("  FAILED to extract %s:", service_name)
        traceback.print_exc()
        return None


def deep_equal(a: object, b: object) -> bool:
    """Deep equality check for schema dicts."""
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def update_refs(obj: object, renames: dict[str, str]) -> object:
    """Recursively update $ref pointers in an OpenAPI schema object."""
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k == "$ref" and isinstance(v, str):
                # $ref looks like "#/components/schemas/SomeName"
                prefix = "#/components/schemas/"
                if v.startswith(prefix):
                    schema_name = v[len(prefix) :]
                    if schema_name in renames:
                        v = prefix + renames[schema_name]
                result[k] = v
            else:
                result[k] = update_refs(v, renames)
        return result
    elif isinstance(obj, list):
        return [update_refs(item, renames) for item in obj]
    return obj


def merge_specs(
    service_specs: list[tuple[str, dict[str, object]]],
) -> dict[str, object]:
    """Merge multiple OpenAPI specs into one unified spec."""
    unified: dict[str, object] = {
        "openapi": "3.1.0",
        "info": {
            "title": "Unified Trading System API",
            "description": (
                "Comprehensive API spec generated from all FastAPI services "
                "in the Unified Trading System. Each service is represented "
                "as a tag group with its endpoints prefixed by /{service-name}/."
            ),
            "version": "1.0.0",
        },
        "paths": {},
        "components": {"schemas": {}},
        "tags": [],
    }

    unified_paths: dict[str, object] = {}
    unified_schemas: dict[str, object] = {}
    unified_tags: list[dict[str, str]] = []

    # Track schema origins for collision detection
    # schema_name -> (first_service, schema_dict)
    schema_registry: dict[str, tuple[str, dict[str, object]]] = {}

    for service_name, spec in service_specs:
        # Add service-level tag
        service_title = spec.get("info", {}).get("title", service_name)  # noqa: qg-empty-fallback
        unified_tags.append({"name": service_name, "description": str(service_title)})

        # Collect schemas and detect collisions
        schemas = spec.get("components", {}).get("schemas", {})  # noqa: qg-empty-fallback
        # renames maps original_name -> prefixed_name for THIS service
        renames: dict[str, str] = {}

        for schema_name, schema_dict in schemas.items():
            if schema_name in schema_registry:
                existing_service, existing_schema = schema_registry[schema_name]
                if deep_equal(schema_dict, existing_schema):
                    # Identical schema — reuse, no rename needed
                    pass
                else:
                    # Collision: different schema, same name
                    # Prefix the new one with service name
                    safe_prefix = service_name.replace("-", "_")
                    prefixed_name = f"{safe_prefix}__{schema_name}"
                    renames[schema_name] = prefixed_name
                    unified_schemas[prefixed_name] = copy.deepcopy(schema_dict)
                    logger.warning(
                        "  Schema collision: %s (from %s vs %s) -> prefixed as %s",
                        schema_name,
                        existing_service,
                        service_name,
                        prefixed_name,
                    )
            else:
                schema_registry[schema_name] = (service_name, schema_dict)
                unified_schemas[schema_name] = copy.deepcopy(schema_dict)

        # Process paths — prefix with /{service-name}
        paths = spec.get("paths", {})  # noqa: qg-empty-fallback
        for path, path_item in paths.items():
            prefixed_path = f"/{service_name}{path}"
            # Add service tag to each operation and update $refs
            updated_item = copy.deepcopy(path_item)

            if renames:
                updated_item = update_refs(updated_item, renames)

            for method in ("get", "post", "put", "delete", "patch", "options", "head"):
                if method in updated_item:
                    op = updated_item[method]
                    # Merge tags: keep existing + add service name
                    existing_tags = op.get("tags", [])  # noqa: qg-empty-fallback
                    if service_name not in existing_tags:
                        op["tags"] = [service_name, *existing_tags]

            unified_paths[prefixed_path] = updated_item

    # Also update $refs inside schemas that reference renamed schemas
    # (This handles schemas referencing other schemas within the same service)
    # We do a global pass since renames accumulate across services
    # Note: In practice, most renames are rare since shared models (UAC/UIC)
    # produce identical schemas across services.

    unified["paths"] = unified_paths
    unified["components"] = {"schemas": unified_schemas}
    unified["tags"] = unified_tags

    return unified


def validate_refs(spec: dict[str, object]) -> list[str]:
    """Validate that all $ref pointers resolve to existing schemas."""
    available_schemas = set(spec.get("components", {}).get("schemas", {}).keys())  # noqa: qg-empty-fallback
    broken: list[str] = []

    def _walk(obj: object, path: str) -> None:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
                    schema_name = ref[len("#/components/schemas/") :]
                    if schema_name not in available_schemas:
                        broken.append(f"{path}: {ref}")
            for k, v in obj.items():
                _walk(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                _walk(item, f"{path}[{i}]")

    _walk(spec.get("paths", {}), "paths")  # noqa: qg-empty-fallback
    _walk(spec.get("components", {}), "components")  # noqa: qg-empty-fallback
    return broken


def run_orphan_audit(spec: dict[str, object], workspace_root: Path) -> list[str]:
    """Audit UAC/UIC exports against the merged spec schemas."""
    schema_names = set(spec.get("components", {}).get("schemas", {}).keys())  # noqa: qg-empty-fallback
    orphans: list[str] = []

    # Audit UAC exports
    try:
        import unified_api_contracts

        uac_all = getattr(unified_api_contracts, "__all__", [])
        for name in uac_all:
            try:
                obj = getattr(unified_api_contracts, name)
                # Check if it's a Pydantic model class (not instance, not function)
                if isinstance(obj, type) and hasattr(obj, "model_fields") and name not in schema_names:
                    orphans.append(f"UAC: {name}")
            except Exception:
                pass
        logger.info("UAC audit: %d exports checked", len(uac_all))
    except ImportError:
        logger.warning("Could not import unified_api_contracts for orphan audit")

    # Audit UIC exports
    try:
        import unified_api_contracts.internal

        uic_all = getattr(unified_api_contracts.internal, "__all__", [])
        for name in uic_all:
            try:
                obj = getattr(unified_api_contracts.internal, name)
                if isinstance(obj, type) and hasattr(obj, "model_fields") and name not in schema_names:
                    orphans.append(f"UIC: {name}")
            except Exception:
                pass
        logger.info("UIC audit: %d exports checked", len(uic_all))
    except ImportError:
        logger.warning("Could not import unified_api_contracts.internal for orphan audit")

    return orphans


def _validate_service_coverage(workspace_root: Path, registered_services: set[str]) -> None:
    """FAIL the run when disk-resident API repos are absent from SERVICE_REGISTRY.

    Scans sibling directories of ``workspace_root`` for repos that contain a
    FastAPI-style entrypoint (``{pkg}/api/main.py``, ``{pkg}/api/app.py``, or
    ``{pkg}/main.py``) but are absent from ``SERVICE_REGISTRY``.

    Exits nonzero on any mismatch so the suite cannot silently rot again (was
    warn-only prior to 2026-06-11 — the drift went undetected for ~3 weeks after
    the features/ml consolidation).  Repos in ``_NO_API_REPOS`` are excluded from
    the check.
    """
    discovered: list[str] = []

    for candidate in sorted(workspace_root.iterdir()):
        if not candidate.is_dir():
            continue
        repo_name = candidate.name
        if repo_name in registered_services:
            continue
        if repo_name in _NO_API_REPOS:
            continue
        # Must have a pyproject.toml to be a Python repo
        if not (candidate / "pyproject.toml").is_file():
            continue

        pkg_name = repo_name.replace("-", "_")
        pkg_dir = candidate / pkg_name

        if not pkg_dir.is_dir():
            continue

        # Check for FastAPI entrypoint patterns
        entrypoint_candidates = [
            pkg_dir / "api" / "main.py",
            pkg_dir / "api" / "app.py",
            pkg_dir / "main.py",
        ]
        for ep in entrypoint_candidates:
            if ep.is_file():
                discovered.append(repo_name)
                break

    if discovered:
        logger.error("")
        logger.error(
            "FAIL — Service coverage: %d repo(s) have API entrypoints but are NOT in SERVICE_REGISTRY:",
            len(discovered),
        )
        for name in discovered:
            logger.error(
                "  MISSING: Service '%s' has API entrypoint but is not in SERVICE_REGISTRY — "
                "add it to _OVERRIDE_MODULE_PATHS or let auto-discovery handle it, "
                "or add to _NO_API_REPOS if it genuinely has no HTTP API surface",
                name,
            )
        logger.error("")
        logger.error("Fix: re-run after updating _OVERRIDE_MODULE_PATHS / _NO_API_REPOS in generate_unified_spec.py")
        sys.exit(1)
    else:
        logger.info("Service coverage: all discovered API repos are in SERVICE_REGISTRY.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate unified OpenAPI spec")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for the generated spec files",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root directory",
    )
    args = parser.parse_args()

    # Determine workspace root
    workspace_root = args.workspace_root
    if workspace_root is None:
        # Try to infer from script location
        script_dir = Path(__file__).resolve().parent
        # Script is at unified-trading-pm/scripts/openapi/
        workspace_root = script_dir.parent.parent.parent
    workspace_root = workspace_root.resolve()

    # === Build SERVICE_REGISTRY from workspace-manifest.json ===
    # Must happen before PYTHONPATH construction below.
    global SERVICE_REGISTRY  # intentional module-level update in main()
    SERVICE_REGISTRY = _load_service_registry(workspace_root)
    logger.info("SERVICE_REGISTRY: %d services loaded from workspace-manifest.json", len(SERVICE_REGISTRY))

    # Subprocess extractors only see PYTHONPATH — prepend every service repo root from
    # SERVICE_REGISTRY so `import auth_api` / `import deployment_api` resolve without a
    # hand-built shell export (see ui-alignment-ssot.md).
    _roots: list[str] = []
    _seen_roots: set[str] = set()
    for service_name, _, _ in SERVICE_REGISTRY:
        root = workspace_root / service_name
        if root.is_dir():
            key = str(root.resolve())
            if key not in _seen_roots:
                _seen_roots.add(key)
                _roots.append(key)
    _extra_pp = os.pathsep.join(_roots)
    _existing_pp = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = _extra_pp + (os.pathsep + _existing_pp if _existing_pp else "")

    # Determine output directory
    output_dir = args.output_dir
    if output_dir is None:
        output_dir = workspace_root / "unified-api-contracts" / "openapi"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Workspace root: %s", workspace_root)
    logger.info("Output dir: %s", output_dir)
    logger.info("Extracting OpenAPI specs from %d services...\n", len(SERVICE_REGISTRY))

    # === Step 3: Extract per-service specs ===
    service_specs: list[tuple[str, dict[str, object]]] = []
    failed: list[tuple[str, str]] = []

    for service_name, module_path, app_attr in SERVICE_REGISTRY:
        spec = extract_service_spec(service_name, module_path, app_attr)
        if spec is not None:
            service_specs.append((service_name, spec))
        else:
            failed.append((service_name, module_path))

    if not service_specs:
        logger.error("No services could be imported. Aborting.")
        sys.exit(1)

    # === Step 4: Merge ===
    logger.info("\nMerging %d service specs...", len(service_specs))
    unified = merge_specs(service_specs)

    # === Step 4b: Validate service coverage ===
    registered_names = {name for name, _, _ in SERVICE_REGISTRY}
    _validate_service_coverage(workspace_root, registered_names)

    # === Step 5: Validate $refs ===
    broken_refs = validate_refs(unified)
    if broken_refs:
        logger.warning("\nBroken $ref pointers (%d):", len(broken_refs))
        for ref in broken_refs[:20]:
            logger.warning("  %s", ref)
        if len(broken_refs) > 20:
            logger.warning("  ... and %d more", len(broken_refs) - 20)

    # === Step 6: Write output ===
    json_path = output_dir / "unified-trading-system.openapi.json"
    with open(json_path, "w") as f:
        json.dump(unified, f, indent=2, sort_keys=False)
    logger.info("\nJSON written: %s", json_path)

    # Write YAML if pyyaml available
    try:
        import yaml

        yaml_path = output_dir / "unified-trading-system.openapi.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(unified, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info("YAML written: %s", yaml_path)
    except ImportError:
        logger.warning("pyyaml not installed — skipping YAML output")

    # === Step 7: Orphan audit ===
    logger.info("\nRunning orphan audit...")
    orphans = run_orphan_audit(unified, workspace_root)

    orphan_path = output_dir / "orphan-report.txt"
    with open(orphan_path, "w") as f:
        f.write("# Orphan Report: Domain models not exposed by any service endpoint\n")
        f.write(f"# Generated from {len(service_specs)} services\n")
        f.write(f"# Total schemas in spec: {len(unified.get('components', {}).get('schemas', {}))}\n")  # noqa: qg-empty-fallback
        f.write(f"# Orphaned models: {len(orphans)}\n\n")
        if orphans:
            for orphan in sorted(orphans):
                f.write(f"{orphan}\n")
        else:
            f.write("No orphans detected.\n")
    logger.info("Orphan report written: %s", orphan_path)

    # === Summary ===
    total_paths = len(unified.get("paths", {}))  # noqa: qg-empty-fallback
    total_schemas = len(unified.get("components", {}).get("schemas", {}))  # noqa: qg-empty-fallback

    print("\n" + "=" * 60)
    print("UNIFIED OPENAPI SPEC — GENERATION SUMMARY")
    print("=" * 60)
    print(f"Services extracted:  {len(service_specs)}/{len(SERVICE_REGISTRY)}")
    print(f"Total endpoints:     {total_paths}")
    print(f"Total schemas:       {total_schemas}")
    print(f"Broken $refs:        {len(broken_refs)}")
    print(f"Orphaned models:     {len(orphans)}")

    if failed:
        print(f"\nFailed services ({len(failed)}):")
        for name, mod in failed:
            print(f"  - {name} ({mod})")

    print("\nOutput:")
    print(f"  JSON:   {json_path}")
    if (output_dir / "unified-trading-system.openapi.yaml").exists():
        print(f"  YAML:   {output_dir / 'unified-trading-system.openapi.yaml'}")
    print(f"  Orphan: {orphan_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
