# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_canonical_futures_construction.py QG step."""

from __future__ import annotations

import tempfile
from pathlib import Path

from check_canonical_futures_construction import _scan_file


def _write(tmp: Path, name: str, content: str) -> Path:
    p = tmp / name
    p.write_text(content)
    return p


def test_complete_construction_no_findings():
    """All 11 required kwargs passed → no findings."""
    src = """
from unified_api_contracts.canonical.domain import CanonicalFuturesContract, FuturesContractLifecyclePhase
from datetime import date
c = CanonicalFuturesContract(
    venue="CME",
    root="ES",
    contract_symbol="ESH26",
    contract_month=3,
    contract_year=2026,
    expiry_date=date(2026, 3, 20),
    last_trading_date=date(2026, 3, 20),
    first_notice_date=date(2026, 3, 16),
    delivery_date=date(2026, 3, 20),
    settlement_date=date(2026, 3, 23),
    lifecycle_phase=FuturesContractLifecyclePhase.ACTIVE,
)
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(Path(tmp), "valid.py", src)
        findings = _scan_file(path)
    assert findings == []


def test_missing_one_kwarg_emits_error():
    """Missing `settlement_date` → error finding listing it."""
    src = """
from unified_api_contracts.canonical.domain import CanonicalFuturesContract
c = CanonicalFuturesContract(
    venue="CME",
    root="ES",
    contract_symbol="ESH26",
    contract_month=3,
    contract_year=2026,
    expiry_date=None,
    last_trading_date=None,
    first_notice_date=None,
    delivery_date=None,
    lifecycle_phase="active",
)
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(Path(tmp), "missing.py", src)
        findings = _scan_file(path)
    assert len(findings) == 1
    assert findings[0].kind == "error"
    assert "settlement_date" in findings[0].missing


def test_kwargs_spread_emits_warning():
    """`**kw` spread cannot be validated statically → warning, not error."""
    src = """
from unified_api_contracts.canonical.domain import CanonicalFuturesContract
def make(**kw):
    return CanonicalFuturesContract(**kw)
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(Path(tmp), "spread.py", src)
        findings = _scan_file(path)
    assert len(findings) == 1
    assert findings[0].kind == "warn-kwargs-spread"


def test_unrelated_class_construction_ignored():
    """Other class constructors with similar names don't trigger findings."""
    src = """
class CanonicalFuturesContractStub:
    pass

c = CanonicalFuturesContractStub()
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(Path(tmp), "unrelated.py", src)
        findings = _scan_file(path)
    assert findings == []


def test_attribute_access_construction_detected():
    """`module.CanonicalFuturesContract(...)` also detected."""
    src = """
import unified_api_contracts.canonical.domain as dom
c = dom.CanonicalFuturesContract(venue="CME")  # missing 10 of 11 required
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(Path(tmp), "attr.py", src)
        findings = _scan_file(path)
    assert len(findings) == 1
    assert findings[0].kind == "error"
    assert len(findings[0].missing) == 10


def test_syntax_error_file_skipped():
    """A file with a syntax error doesn't crash the scanner."""
    src = "def broken(:\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(Path(tmp), "broken.py", src)
        findings = _scan_file(path)
    assert findings == []


def test_pre_filter_skips_files_without_class_name():
    """Files that don't mention CanonicalFuturesContract are skipped cheaply."""
    src = "x = 1\n# nothing interesting here\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = _write(Path(tmp), "plain.py", src)
        findings = _scan_file(path)
    assert findings == []
