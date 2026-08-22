# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_removed_symbols.py.

Run via pytest from a venv that has pyyaml installed (the workspace
.venv-workspace satisfies this), or via the workspace-root pytest invocation
that base-service.sh wires up. These tests are pure-Python — no GCS/AWS/network.
"""

from __future__ import annotations

import textwrap
from datetime import date as _date
from pathlib import Path

import pytest
from check_removed_symbols import (  # type: ignore[import-not-found]
    Finding,
    RemovedSymbol,
    _scan_file_for_symbols,
    iter_python_files,
    load_manifest,
    scan_workspace,
)

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def get_strategy_factories_entry() -> RemovedSymbol:
    return RemovedSymbol(
        symbol="strategy_service.cli.handlers.batch_utils.get_strategy_factories",
        removed_at=_date(2026, 5, 1),
        removed_by_commit="<v1-retire>",
        successor="strategy_service.cli.handlers.batch_utils.V2BatchHarness.from_strategy_type",
        reason="V1-RETIRE Phase 2",
        status="removed",
    )


@pytest.fixture
def manifest_writer_add_entry() -> RemovedSymbol:
    return RemovedSymbol(
        symbol="unified_trading_library.manifest.ManifestWriter.add",
        removed_at=_date(2026, 5, 8),
        removed_by_commit="<writegate>",
        successor="ManifestWriter.record_captured",
        reason="writegate Phase 2.A",
        status="pending_removal",
    )


# ── Manifest loading ─────────────────────────────────────────────────────────


def test_load_manifest_valid(tmp_path: Path) -> None:
    manifest_text = textwrap.dedent(
        """
        removed_symbols:
          - symbol: "pkg.mod.thing"
            removed_at: 2026-05-01
            removed_by_commit: "abc123"
            successor: "pkg.mod.new_thing"
            reason: "test refactor"
            status: removed
        """
    ).strip()
    f = tmp_path / "manifest.yaml"
    _ = f.write_text(manifest_text)
    entries = load_manifest(f)
    assert len(entries) == 1
    assert entries[0].symbol == "pkg.mod.thing"
    assert entries[0].status == "removed"
    assert entries[0].name == "thing"
    assert entries[0].module_path == "pkg.mod"


def test_load_manifest_rejects_invalid_status(tmp_path: Path) -> None:
    manifest_text = textwrap.dedent(
        """
        removed_symbols:
          - symbol: "pkg.mod.thing"
            removed_at: 2026-05-01
            removed_by_commit: "abc"
            successor: "pkg.mod.new"
            reason: "x"
            status: not_a_real_status
        """
    ).strip()
    f = tmp_path / "manifest.yaml"
    _ = f.write_text(manifest_text)
    with pytest.raises(ValueError, match="invalid status"):
        _ = load_manifest(f)


def test_load_manifest_rejects_missing_keys(tmp_path: Path) -> None:
    manifest_text = textwrap.dedent(
        """
        removed_symbols:
          - symbol: "pkg.mod.thing"
            status: removed
        """
    ).strip()
    f = tmp_path / "manifest.yaml"
    _ = f.write_text(manifest_text)
    with pytest.raises(ValueError, match="missing required key"):
        _ = load_manifest(f)


def test_load_manifest_rejects_non_dotted_symbol(tmp_path: Path) -> None:
    manifest_text = textwrap.dedent(
        """
        removed_symbols:
          - symbol: "no_dots_here"
            removed_at: 2026-05-01
            removed_by_commit: "abc"
            successor: "x"
            reason: "y"
            status: removed
        """
    ).strip()
    f = tmp_path / "manifest.yaml"
    _ = f.write_text(manifest_text)
    with pytest.raises(ValueError, match="dotted path"):
        _ = load_manifest(f)


def test_load_manifest_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        _ = load_manifest(tmp_path / "nope.yaml")


def test_load_manifest_real_workspace_manifest() -> None:
    """The real workspace manifest must always parse cleanly."""
    here = Path(__file__).resolve().parent
    real_manifest = here / "removed_symbols_manifest.yaml"
    if not real_manifest.is_file():  # pragma: no cover — defensive
        pytest.skip("real manifest not yet shipped")
    entries = load_manifest(real_manifest)
    assert len(entries) >= 1, "real manifest unexpectedly empty"
    statuses = {e.status for e in entries}
    assert statuses.issubset({"removed", "pending_removal", "renamed"})


# ── Scanning: empty cases ────────────────────────────────────────────────────


def test_scan_empty_manifest_no_findings(tmp_path: Path) -> None:
    src = tmp_path / "x.py"
    _ = src.write_text("from os import path\nprint(path)\n")
    findings = _scan_file_for_symbols(src, [], src.read_text())
    assert findings == []


def test_scan_clean_file_no_findings(tmp_path: Path, get_strategy_factories_entry: RemovedSymbol) -> None:
    src = tmp_path / "x.py"
    _ = src.write_text("from strategy_service.cli.handlers.batch_utils import V2BatchHarness\n_ = V2BatchHarness\n")
    findings = _scan_file_for_symbols(src, [get_strategy_factories_entry], src.read_text())
    assert findings == []


# ── Scanning: positive matches ───────────────────────────────────────────────


def test_scan_detects_removed_import(tmp_path: Path, get_strategy_factories_entry: RemovedSymbol) -> None:
    src = tmp_path / "broken_consumer.py"
    _ = src.write_text(
        "from strategy_service.cli.handlers.batch_utils import get_strategy_factories\n"
        "factories = get_strategy_factories()\n"
    )
    findings = _scan_file_for_symbols(src, [get_strategy_factories_entry], src.read_text())
    assert len(findings) == 1
    f = findings[0]
    assert f.line == 1
    assert f.matched_symbol.symbol.endswith("get_strategy_factories")
    assert "get_strategy_factories" in f.snippet


def test_scan_detects_module_path_import(tmp_path: Path) -> None:
    """Removed module paths fire on `from parent import removed_module`."""
    entry = RemovedSymbol(
        symbol="unified_api_contracts.canonical.domain.client",
        removed_at=_date(2026, 5, 8),
        removed_by_commit="<option-a>",
        successor="unified_api_contracts.internal.architecture_v2.capital_allocation",
        reason="Option A revert",
        status="removed",
    )
    src = tmp_path / "broken.py"
    _ = src.write_text("from unified_api_contracts.canonical.domain import client\n_ = client\n")
    findings = _scan_file_for_symbols(src, [entry], src.read_text())
    assert len(findings) >= 1


def test_scan_detects_attribute_access_on_class_method(
    tmp_path: Path, manifest_writer_add_entry: RemovedSymbol
) -> None:
    """Receiver name matches class name (case-insensitive / snake-case tolerated)."""
    src = tmp_path / "consumer.py"
    _ = src.write_text(
        "def f(manifest_writer, ManifestWriter):\n"
        "    manifest_writer.add(processing_date=None, venue='x')\n"
        "    ManifestWriter.add(processing_date=None, venue='x')\n"
    )
    findings = _scan_file_for_symbols(src, [manifest_writer_add_entry], src.read_text())
    # Both receivers (`manifest_writer` snake-case + `ManifestWriter` exact)
    # match the second-to-last `ManifestWriter` component.
    assert len(findings) >= 2
    assert any(".add(" in f.snippet for f in findings)


def test_scan_attribute_access_does_not_fire_on_unrelated_receiver(
    tmp_path: Path, manifest_writer_add_entry: RemovedSymbol
) -> None:
    """`set.add()` / `args.client` / `list.append()` must NOT match a method removal.

    This is the false-positive class fixed 2026-05-10 after the smoke run
    surfaced ~thousands of `.add(` callsites masquerading as
    ManifestWriter.add. The attribute-access matcher requires the receiver
    name to match the entry's class name (case-insensitive / snake-case
    tolerated).
    """
    src = tmp_path / "innocent_set_add.py"
    _ = src.write_text("def f():\n    seen = set()\n    seen.add('x')\n    items = []\n    items.append(1)\n")
    findings = _scan_file_for_symbols(src, [manifest_writer_add_entry], src.read_text())
    assert findings == []


def test_scan_multiple_findings_in_same_file(tmp_path: Path, get_strategy_factories_entry: RemovedSymbol) -> None:
    src = tmp_path / "broken_consumer.py"
    _ = src.write_text(
        "from strategy_service.cli.handlers.batch_utils import get_strategy_factories\n"
        "from strategy_service.cli.handlers.batch_utils import get_strategy_factories as gsf2\n"
        "x = get_strategy_factories()\n"
        "y = gsf2()\n"
    )
    findings = _scan_file_for_symbols(src, [get_strategy_factories_entry], src.read_text())
    # Two ImportFrom hits at minimum; per-callsite attribute fires depend
    # on the dotted-path-length filter.
    assert len(findings) >= 2
    lines = sorted({f.line for f in findings})
    assert 1 in lines
    assert 2 in lines


# ── Workspace walker ─────────────────────────────────────────────────────────


def test_iter_python_files_excludes_venv(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / ".venv" / "lib").mkdir(parents=True)
    (tmp_path / "build").mkdir()
    real = tmp_path / "src" / "real.py"
    _ = real.write_text("# real\n")
    fake_venv = tmp_path / ".venv" / "lib" / "noise.py"
    _ = fake_venv.write_text("# noise\n")
    fake_build = tmp_path / "build" / "noise.py"
    _ = fake_build.write_text("# noise\n")

    found = list(iter_python_files(tmp_path))
    assert real in found
    assert fake_venv not in found
    assert fake_build not in found


def test_scan_workspace_end_to_end(tmp_path: Path, get_strategy_factories_entry: RemovedSymbol) -> None:
    (tmp_path / "consumer.py").write_text(
        "from strategy_service.cli.handlers.batch_utils import get_strategy_factories\n"
    )
    (tmp_path / "clean.py").write_text("from os import path\n")
    findings = scan_workspace(tmp_path, [get_strategy_factories_entry], max_workers=1)
    assert len(findings) == 1
    assert findings[0].file_path.name == "consumer.py"


def test_scan_workspace_empty_manifest_returns_no_findings(tmp_path: Path) -> None:
    (tmp_path / "x.py").write_text("from strategy_service.cli.handlers.batch_utils import get_strategy_factories\n")
    findings = scan_workspace(tmp_path, [], max_workers=1)
    assert findings == []


def test_scan_handles_unparseable_file(tmp_path: Path, get_strategy_factories_entry: RemovedSymbol) -> None:
    """SyntaxError in a file must NOT crash the walker."""
    (tmp_path / "broken.py").write_text("def f(:\n  pass\n")  # syntax error
    (tmp_path / "good.py").write_text("from strategy_service.cli.handlers.batch_utils import get_strategy_factories\n")
    findings = scan_workspace(tmp_path, [get_strategy_factories_entry], max_workers=1)
    # The good file's finding must still be reported.
    assert len(findings) == 1
    assert findings[0].file_path.name == "good.py"


def test_finding_dataclass_is_frozen(get_strategy_factories_entry: RemovedSymbol) -> None:
    f = Finding(
        file_path=Path("x.py"),
        line=1,
        matched_symbol=get_strategy_factories_entry,
        snippet="from x import y",
    )
    with pytest.raises(AttributeError):
        f.line = 99  # type: ignore[misc]
