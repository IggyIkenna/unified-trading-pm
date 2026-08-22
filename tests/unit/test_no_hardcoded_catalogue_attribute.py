"""Regression guard for the query-don't-derive gate
(scripts/qg/no_hardcoded_catalogue_attribute.py).

SSOT: plans/active/instruments_catalogue_definitions_and_field_history_2026_08_17.md
§ "The query-don't-derive gate". Negative-control discipline: this file proves the
gate has real teeth (fails on a deliberately-broken fixture) as well as proving it
does NOT false-positive on the legitimate shapes already present in T2's repos
(None defaults, live-API-derived values, schema-declaration writer modules, test
fixtures) -- every one of those shapes was actually found in the live T2 codebase
during this check's construction, so this is not a hypothetical list.
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "qg" / "no_hardcoded_catalogue_attribute.py"
_spec = importlib.util.spec_from_file_location("no_hardcoded_catalogue_attribute", _SCRIPT)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["no_hardcoded_catalogue_attribute"] = _mod
_spec.loader.exec_module(_mod)

find_hardcoded_reference_literals = _mod.find_hardcoded_reference_literals
scan_file = _mod.scan_file
scan_repo = _mod.scan_repo
_is_excluded = _mod._is_excluded
DEFAULT_MUTABLE_FIELDS = _mod.DEFAULT_MUTABLE_FIELDS


def _violations(src: str, fields: frozenset[str] = DEFAULT_MUTABLE_FIELDS) -> list:
    tree = ast.parse(src)
    return find_hardcoded_reference_literals(tree, src.splitlines(), fields)


# ---------------------------------------------------------------------------
# The discriminator core — genuine violations (must be caught)
# ---------------------------------------------------------------------------


def test_module_level_hardcoded_assignment_is_a_violation():
    v = _violations("contract_size = 10.0\n")
    assert len(v) == 1
    assert v[0].field == "contract_size"


def test_annotated_hardcoded_assignment_is_a_violation():
    v = _violations("contract_size: float = 10.0\n")
    assert len(v) == 1


def test_hardcoded_lookup_table_dict_is_a_violation():
    """The MarginModel.AAVE_V3-style 'one constant regardless of input' shape,
    expressed as a hardcoded dict rather than a bare scalar."""
    v = _violations('CONTRACT_SIZE_BY_VENUE = {"contract_size": 10.0}\n')
    assert len(v) == 1


def test_equality_comparison_against_literal_is_a_violation():
    v = _violations("if position.contract_size == 10.0:\n    pass\n")
    assert len(v) == 1


def test_equality_comparison_reversed_operand_order_is_a_violation():
    v = _violations("if 10.0 == position.contract_size:\n    pass\n")
    assert len(v) == 1


def test_string_literal_hardcode_is_a_violation():
    v = _violations('contract_size = "10"\n', fields=frozenset({"contract_size"}))
    assert len(v) == 1


def test_deribit_regression_specimen_reproduces_the_real_bug():
    """The exact line the gate caught live in market-tick-data-service's
    deribit_execution.py before the fix in this same change."""
    v = _violations("def _resolve_inverse_usd_amount(self):\n    contract_size = 10.0\n    return contract_size\n")
    assert len(v) == 1
    assert v[0].snippet == "contract_size = 10.0"


# ---------------------------------------------------------------------------
# The discriminator core — legitimate shapes that must NOT false-positive
# (every one of these is a real shape found in T2's repos)
# ---------------------------------------------------------------------------


def test_none_default_is_not_a_violation():
    """DeFi AMM adapters legitimately default contract_size to None (not
    applicable to a spot pool position) — e.g.
    market-tick-data-service's lst_*_adapter.py files."""
    v = _violations("contract_size: float | None = None\n")
    assert v == []


def test_none_in_dict_literal_is_not_a_violation():
    v = _violations('{"contract_size": None}\n')
    assert v == []


def test_attribute_read_rhs_is_not_a_violation():
    """Reading a live, already-fetched value off another object — e.g.
    ccxt_adapter.py's `"contract_size": market.contractSize`."""
    v = _violations('d = {"contract_size": market.contractSize}\n')
    assert v == []


def test_call_rhs_is_not_a_violation():
    """The correct query-the-catalogue pattern itself must never self-flag."""
    v = _violations("contract_size = read_instruments_catalog_contract_size(asset_group, venue, instrument_id)\n")
    assert v == []


def test_name_reference_rhs_is_not_a_violation():
    v = _violations("contract_size = catalog_row.contract_size\n")
    assert v == []


def test_unrelated_variable_name_is_not_a_violation():
    v = _violations("contract_size_multiplier = 1.0\n")
    assert v == []


def test_field_name_as_bare_string_in_a_list_is_not_a_violation():
    """A schema/column-name declaration list — e.g. IS's CATALOG_COLUMNS —
    is a list of strings, not a dict mapping the field to a hardcoded VALUE."""
    v = _violations('CATALOG_COLUMNS = ["instrument_id", "contract_size", "venue"]\n')
    assert v == []


def test_comparison_against_non_literal_is_not_a_violation():
    v = _violations("if position.contract_size == other.contract_size:\n    pass\n")
    assert v == []


# ---------------------------------------------------------------------------
# Path-exclusion rules
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel_path",
    [
        "instruments_service/reference_data/catalogue_field_history.py",
        "instruments_service/scripts/build_instrument_catalogue.py",
        "instruments-service/scripts/build_instrument_catalogue.py",
        "market_tick_data_service/tests/unit/test_deribit_execution.py",
        "market_data_processing_service/app/adapters/tests/test_x.py",
    ],
)
def test_owner_and_test_paths_are_excluded(rel_path):
    assert _is_excluded(rel_path) is True


@pytest.mark.parametrize(
    "rel_path",
    [
        "market_tick_data_service/market_interface/adapters/deribit_execution.py",
        "instruments_service/engine/orchestrator/sink.py",
        "market_data_processing_service/app/adapters/cefi/liquidations_adapter.py",
    ],
)
def test_consumer_paths_are_not_excluded(rel_path):
    assert _is_excluded(rel_path) is False


def test_sanction_marker_suppresses_a_reviewed_exception(tmp_path: Path):
    f = tmp_path / "adapter.py"
    f.write_text("contract_size = 10.0  # qg-allow: catalogue-attribute-hardcode reviewed 2026-08-22\n")
    assert scan_file(f, DEFAULT_MUTABLE_FIELDS) == []


# ---------------------------------------------------------------------------
# Negative control — a deliberately-broken fixture repo tree must fail the gate;
# a deliberately-clean one must pass. Proves the CLI itself has teeth, not just
# the importable walker function.
# ---------------------------------------------------------------------------


def _write_fixture_repo(root: Path, *, broken: bool) -> None:
    consumer_dir = root / "market-tick-data-service" / "market_tick_data_service" / "market_interface" / "adapters"
    consumer_dir.mkdir(parents=True)
    body = "contract_size = 10.0\n" if broken else "contract_size = fetch_live_contract_size()\n"
    (consumer_dir / "deribit_execution.py").write_text(body)

    other_repos = (
        ("instruments-service", "instruments_service"),
        ("market-data-processing-service", "market_data_processing_service"),
    )
    for repo_dir, source_dir in other_repos:
        d = root / repo_dir / source_dir
        d.mkdir(parents=True)
        (d / "__init__.py").write_text("")

    owner_dir = root / "instruments-service" / "instruments_service" / "reference_data"
    owner_dir.mkdir(parents=True)
    # The catalogue's own writer legitimately assigns the field name literally —
    # must NOT trip the gate even in the broken-fixture run.
    (owner_dir / "catalogue_field_history.py").write_text("MUTABLE_CATALOGUE_FIELDS = frozenset({'contract_size'})\n")


def test_cli_fails_on_deliberately_broken_fixture(tmp_path: Path):
    _write_fixture_repo(tmp_path, broken=True)
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--repo-root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "contract_size" in result.stdout
    assert "deribit_execution.py" in result.stdout


def test_cli_passes_on_clean_fixture(tmp_path: Path):
    _write_fixture_repo(tmp_path, broken=False)
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--repo-root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_cli_errors_when_a_t2_repo_is_missing(tmp_path: Path):
    """A silently-absent repo must fail loud, not scan an empty subset and
    report a false-clean OK."""
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--repo-root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "not found" in result.stderr


def test_scan_repo_skips_missing_source_dir_gracefully(tmp_path: Path):
    """scan_repo itself (as opposed to the CLI's up-front hard check) degrades
    to empty rather than raising when a single source dir is absent."""
    assert scan_repo(tmp_path, "instruments-service", "instruments_service", DEFAULT_MUTABLE_FIELDS) == []
