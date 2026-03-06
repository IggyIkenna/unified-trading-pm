"""Loaders for service registry, checklists, and codex templates."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml
from lib.epic_models import ServiceDict

# Paths (relative to script location)
_SCRIPT_DIR = Path(__file__).resolve().parents[1]
CODEX_ROOT = _SCRIPT_DIR.parents[1]
WORKSPACE_ROOT = CODEX_ROOT.parent  # unified-trading-pm/
SERVICE_REGISTRY = CODEX_ROOT / "11-project-management" / "service-registry.yaml"
CODEX_TEMPLATES_DIR = CODEX_ROOT / "10-audit"
DEPLOYMENT_CHECKLISTS_DIR = WORKSPACE_ROOT / "unified-trading-deployment-v2" / "configs"

RegistryDict = dict[str, object]
TemplateDict = dict[str, object]
ChecklistDict = dict[str, object]


def load_service_registry() -> RegistryDict:
    """Load service registry."""
    with open(SERVICE_REGISTRY) as f:
        return cast(RegistryDict, yaml.safe_load(f))


def load_deployment_checklist(service_name: str) -> ChecklistDict | None:
    """Load deployment checklist for a service."""
    checklist_path = DEPLOYMENT_CHECKLISTS_DIR / f"checklist.{service_name}.yaml"
    if not checklist_path.exists():
        return None

    with open(checklist_path) as f:
        return cast(ChecklistDict, yaml.safe_load(f))


def load_codex_templates() -> dict[str, TemplateDict]:
    """Load all codex templates."""
    templates: dict[str, TemplateDict] = {}
    for path in CODEX_TEMPLATES_DIR.glob("_service-*.yaml"):
        with open(path) as f:
            data: TemplateDict = cast(TemplateDict, yaml.safe_load(f))
            template_name = path.stem
            templates[template_name] = data
    return templates


def get_template_for_service(service: ServiceDict, templates: dict[str, TemplateDict]) -> TemplateDict | None:
    """Get codex template for a service."""
    service_type = str(service.get("type", ""))

    # Handle nested pipeline_metadata structure
    raw_pipeline_meta = service.get("pipeline_metadata") or {}
    pipeline_meta: dict[str, object] = (
        cast(dict[str, object], raw_pipeline_meta) if isinstance(raw_pipeline_meta, dict) else {}
    )
    layer = pipeline_meta.get("layer")
    group = str(pipeline_meta.get("group", ""))

    template_key: str | None = None
    if service_type == "pipeline":
        # Map layer number + group to template
        if layer == 1 and group == "data-io":
            template_key = "_service-pipeline-data-io"
        elif layer == 2:
            template_key = "_service-pipeline-market-data"
        elif layer == 3:
            template_key = "_service-pipeline-features"
        elif layer == 4:
            template_key = "_service-pipeline-ml"
        elif layer in [5, 6]:
            template_key = "_service-pipeline-strategy-execution"
        elif layer == 7:
            template_key = "_service-pipeline-post-trade"
        else:
            print(f"Unknown pipeline layer {layer} for {service.get('service')}")
            return None
    elif service_type == "platform":
        template_key = "_service-platform"
    elif service_type == "ui":
        # Handle nested ui_metadata structure
        raw_ui_meta = service.get("ui_metadata") or {}
        ui_meta: dict[str, object] = cast(dict[str, object], raw_ui_meta) if isinstance(raw_ui_meta, dict) else {}
        ui_category = str(ui_meta.get("category", "observability"))
        template_key = f"_service-ui-{ui_category}"

    if template_key is None:
        return None
    return templates.get(template_key)


# ============================================================================
# Epic Generation Logic
# ============================================================================
