"""Capability-manifest PARAM SCHEMA exporter tests (plan
``defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17`` Phase C).

``extract_param_schema(workspace_root)`` probes the strategy-service engine SSOT
(``param_schema.build_param_schema_registry``) in that service's own ``.venv`` and
yields the per-archetype flat PARAM SCHEMA the capability manifest emits and the
wizard renders from. These tests assert the exporter emits the schema for a sample
of archetypes — CARRY_STAKED_BASIS (incl. the new ``margin_buffer_pct``),
ARBITRAGE_PRICE_DISPERSION (the F4 30/10 engine defaults, NOT the e2e-smoke 20/5),
and a VOL_* one — and that the schema lands in the serialised manifest block.

Needs the strategy-service ``.venv`` (per-service venv subprocess idiom); skipped
when absent, like the F53 service-registry test.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_SCRIPTS_OPENAPI = Path(__file__).resolve().parent.parent.parent / "scripts" / "openapi"
if str(_SCRIPTS_OPENAPI) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_OPENAPI))

os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")

from _capability_gaps import extract_param_schema
from unified_api_contracts.internal.architecture_v2.capability_manifest import (
    CapabilityManifest,
    ParamSchemaSpec,
)

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
_STRATEGY_VENV = _WORKSPACE_ROOT / "strategy-service" / ".venv" / "bin" / "python"

requires_strategy_venv = pytest.mark.skipif(
    not _STRATEGY_VENV.exists(),
    reason="strategy-service .venv not present (per-service venv probe)",
)


@pytest.fixture(scope="module")
def param_schema() -> dict[str, list[ParamSchemaSpec]]:
    schema, _nodes, _edges = extract_param_schema(_WORKSPACE_ROOT)
    return schema


def _by_name(specs: list[ParamSchemaSpec]) -> dict[str, ParamSchemaSpec]:
    return {s.name: s for s in specs}


@requires_strategy_venv
def test_sample_archetypes_emit_a_param_schema(param_schema: dict[str, list[ParamSchemaSpec]]) -> None:
    # 29 distinct engines + shared-engine archetype aliases.
    assert len(param_schema) >= 29
    for arch in ("CARRY_STAKED_BASIS", "ARBITRAGE_PRICE_DISPERSION", "VOL_CARRY"):
        assert arch in param_schema, f"{arch} absent from emitted param_schema"
        assert param_schema[arch], f"{arch} emitted with no params"


@requires_strategy_venv
def test_csb_carries_margin_buffer_pct(param_schema: dict[str, list[ParamSchemaSpec]]) -> None:
    rows = _by_name(param_schema["CARRY_STAKED_BASIS"])
    assert "margin_buffer_pct" in rows, "CSB missing the new margin_buffer_pct param"
    mb = rows["margin_buffer_pct"]
    assert mb.type == "decimal"
    assert mb.default == "0.20"  # engine _DEFAULT_MARGIN_BUFFER_PCT
    # core CSB params present + typed
    assert rows["entry_bps"].default == "200"
    assert rows["exit_bps"].default == "50"
    assert rows["start_token"].type == "enum"
    assert set(rows["start_token"].enum_values) == {"USDC", "USDT", "FDUSD"}


@requires_strategy_venv
def test_apd_uses_engine_defaults_not_smoke(param_schema: dict[str, list[ParamSchemaSpec]]) -> None:
    rows = _by_name(param_schema["ARBITRAGE_PRICE_DISPERSION"])
    # F4: engine default 30/10, NOT the e2e-smoke 20/5.
    assert rows["dispersion_bps"].default == "30"
    assert rows["cost_bps"].default == "10"
    assert rows["dispersion_type"].type == "enum"


@requires_strategy_venv
def test_vol_archetype_emits_typed_rows(param_schema: dict[str, list[ParamSchemaSpec]]) -> None:
    rows = _by_name(param_schema["VOL_CARRY"])
    assert rows["entry_vrp"].default == "0.04"
    assert rows["max_slippage_bps"].type == "int"
    assert rows["call_instrument"].required is True
    assert rows["call_instrument"].default is None


@requires_strategy_venv
def test_param_schema_round_trips_into_serialised_manifest(
    param_schema: dict[str, list[ParamSchemaSpec]],
) -> None:
    manifest = CapabilityManifest(manifest_version="1.0.0", param_schema=param_schema)
    canonical = manifest.to_canonical_dict()
    assert "param_schema" in canonical
    block = canonical["param_schema"]
    assert isinstance(block, dict)
    # archetype keys are sorted in the canonical form (determinism)
    assert list(block) == sorted(block)
    csb = {row["name"]: row for row in block["CARRY_STAKED_BASIS"]}
    assert csb["margin_buffer_pct"]["default"] == "0.20"
