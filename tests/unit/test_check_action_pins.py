"""Unit tests for scripts/validation/check-action-pins.py (parser; no network).

Resolution (ref_resolves / _network_ok) hits the GitHub API and is exercised in CI /
pre-rollout, not here. These tests pin the pure `uses:` extraction + dedup behaviour.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validation" / "check-action-pins.py"
    spec = importlib.util.spec_from_file_location("check_action_pins", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


def _write(tmp_path: Path, name: str, body: str) -> Path:
    f = tmp_path / name
    f.write_text(body, encoding="utf-8")
    return f


class TestExtractPins:
    def test_simple_pin(self, tmp_path: Path) -> None:
        f = _write(tmp_path, "wf.yml", "jobs:\n  x:\n    steps:\n      - uses: actions/checkout@v5\n")
        pins = MOD.extract_pins(f)
        assert pins == [("actions/checkout", "v5", "wf.yml:4")]

    def test_subpath_pin_uses_first_two_segments(self, tmp_path: Path) -> None:
        f = _write(tmp_path, "wf.yml", "      - uses: actions/cache/restore@v4\n")
        assert MOD.extract_pins(f) == [("actions/cache", "v4", "wf.yml:1")]

    def test_quoted_and_trailing_comment(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path,
            "wf.yml",
            '      - uses: "actions/setup-python@v6"\n      - uses: actions/checkout@v5  # pinned\n',
        )
        assert MOD.extract_pins(f) == [
            ("actions/setup-python", "v6", "wf.yml:1"),
            ("actions/checkout", "v5", "wf.yml:2"),
        ]

    def test_local_docker_and_dynamic_are_skipped(self, tmp_path: Path) -> None:
        body = (
            "      - uses: ./.github/actions/local-thing\n"
            "      - uses: ./.github/workflows/reusable.yml\n"
            "      - uses: docker://alpine:3.20\n"
            "      - uses: ${{ matrix.action }}@v1\n"
            "      - uses: owner/repo@${{ matrix.ref }}\n"
        )
        f = _write(tmp_path, "wf.yml", body)
        assert MOD.extract_pins(f) == []

    def test_no_at_ref_is_skipped(self, tmp_path: Path) -> None:
        f = _write(tmp_path, "wf.yml", "      - uses: ./local-action-no-version\n")
        assert MOD.extract_pins(f) == []

    def test_sha_pin_is_extracted(self, tmp_path: Path) -> None:
        sha = "11bd71901bbe5b1630ceea73d27597364c9af683"
        f = _write(tmp_path, "wf.yml", f"      - uses: actions/checkout@{sha}\n")
        assert MOD.extract_pins(f) == [("actions/checkout", sha, "wf.yml:1")]


class TestCollectPins:
    def test_dedup_across_files_aggregates_sites(self, tmp_path: Path) -> None:
        f1 = _write(tmp_path, "a.yml", "      - uses: actions/checkout@v5\n")
        f2 = _write(tmp_path, "b.yml", "      - uses: actions/checkout@v5\n")
        pins = MOD.collect_pins([f1, f2])
        assert set(pins.keys()) == {("actions/checkout", "v5")}
        assert pins[("actions/checkout", "v5")].sites == ["a.yml:1", "b.yml:1"]
