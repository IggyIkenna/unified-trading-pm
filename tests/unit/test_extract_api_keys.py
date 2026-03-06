"""Unit tests for scripts/extract_api_keys.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def _load_extract_module():
    import importlib.util

    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "extract_api_keys.py"
    spec = importlib.util.spec_from_file_location("extract_api_keys", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestParseEnvFile:
    def test_empty_file(self, tmp_path: Path) -> None:
        mod = _load_extract_module()
        p = tmp_path / ".env"
        p.write_text("")
        assert mod.parse_env_file(p) == {}

    def test_comments_and_blanks_ignored(self, tmp_path: Path) -> None:
        mod = _load_extract_module()
        p = tmp_path / ".env"
        p.write_text("# comment\n\n  \nKEY=val\n")
        assert mod.parse_env_file(p) == {"KEY": "val"}

    def test_simple_key_value(self, tmp_path: Path) -> None:
        mod = _load_extract_module()
        p = tmp_path / ".env"
        p.write_text("API_KEY=secret123\nOTHER=value\n")
        assert mod.parse_env_file(p) == {"API_KEY": "secret123", "OTHER": "value"}

    def test_quoted_value_double(self, tmp_path: Path) -> None:
        mod = _load_extract_module()
        p = tmp_path / ".env"
        p.write_text('KEY="quoted value"\n')
        assert mod.parse_env_file(p) == {"KEY": "quoted value"}

    def test_quoted_value_single(self, tmp_path: Path) -> None:
        mod = _load_extract_module()
        p = tmp_path / ".env"
        p.write_text("KEY='quoted'\n")
        assert mod.parse_env_file(p) == {"KEY": "quoted"}

    def test_empty_value_omitted(self, tmp_path: Path) -> None:
        mod = _load_extract_module()
        p = tmp_path / ".env"
        p.write_text("KEY=\nOTHER=val\n")
        assert mod.parse_env_file(p) == {"OTHER": "val"}

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        mod = _load_extract_module()
        assert mod.parse_env_file(tmp_path / "nonexistent") == {}


class TestMain:
    def test_main_writes_output(self, tmp_path: Path) -> None:
        mod = _load_extract_module()
        env_file = tmp_path / "deployment-service" / ".env"
        env_file.parent.mkdir(parents=True, exist_ok=True)
        env_file.write_text("TEST_KEY=testval\n")
        output_file = tmp_path / "api_keys"
        with (
            patch.object(mod, "WORKSPACE_ROOT", tmp_path),
            patch.object(mod, "OUTPUT_FILE", output_file),
            patch.object(mod, "ENV_PATHS", ["deployment-service/.env"]),
        ):
            mod.main()
        assert output_file.exists()
        assert "TEST_KEY=testval" in output_file.read_text()
