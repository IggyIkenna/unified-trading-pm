"""Unit tests for scripts/quality_gates/check_no_swallowed_credential_fetch.py.

Positive (fires on the swallowed-credential-fetch idiom, incl. the real
backslash-continued shape) + negative (clean/unrelated code passes) +
baseline-ratchet semantics, per
plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md [INFRA] P1.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_no_swallowed_credential_fetch.py"
    spec = importlib.util.spec_from_file_location("check_no_swallowed_credential_fetch", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


def _write(path: Path, source: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


def _make_repo(ws: Path, repo: str) -> Path:
    repo_root = ws / repo
    (repo_root / ".git").mkdir(parents=True)
    return repo_root


# ── find_swallowed_credential_fetches (positive) ─────────────────────────────


class TestPositive:
    def test_single_line_gcloud_secrets_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "s.sh",
            'TOKEN="$(gcloud secrets versions access latest --secret=X 2>/dev/null || true)"\n',
        )
        hits = MOD.find_swallowed_credential_fetches(f)
        assert len(hits) == 1
        assert hits[0][0] == 1

    def test_backslash_continued_statement_flagged(self, tmp_path: Path) -> None:
        # The real glue-runner-run.sh shape: credential command on one physical
        # line, `2>/dev/null || true` on the next, joined by a trailing `\`.
        f = _write(
            tmp_path / "s.sh",
            'GH_TOKEN="$(gcloud secrets versions access latest --secret="${GH_TOKEN_SECRET}" \\\n'
            '  ${GCP_PROJECT:+--project="${GCP_PROJECT}"} 2>/dev/null || true)"\n',
        )
        hits = MOD.find_swallowed_credential_fetches(f)
        assert len(hits) == 1
        assert hits[0][0] == 1  # anchored to the statement's FIRST physical line

    def test_aws_secretsmanager_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "s.sh",
            'V="$(aws secretsmanager get-secret-value --secret-id X --query SecretString '
            '--output text 2>/dev/null || true)"\n',
        )
        assert len(MOD.find_swallowed_credential_fetches(f)) == 1

    def test_vault_kv_get_flagged(self, tmp_path: Path) -> None:
        f = _write(tmp_path / "s.sh", "T=$(vault kv get -field=token secret/foo 2>/dev/null || true)\n")
        assert len(MOD.find_swallowed_credential_fetches(f)) == 1

    def test_vault_read_flagged(self, tmp_path: Path) -> None:
        f = _write(tmp_path / "s.sh", "T=$(vault read -field=token secret/foo 2>/dev/null || true)\n")
        assert len(MOD.find_swallowed_credential_fetches(f)) == 1

    def test_or_colon_variant_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "s.sh",
            "T=$(gcloud secrets versions access latest --secret=X 2>/dev/null || :)\n",
        )
        assert len(MOD.find_swallowed_credential_fetches(f)) == 1


# ── find_swallowed_credential_fetches (negative) ─────────────────────────────


class TestNegative:
    def test_clean_fetch_no_swallow_not_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "s.sh",
            'TOKEN="$(gcloud secrets versions access latest --secret=X)" || { echo "FATAL" >&2; exit 1; }\n',
        )
        assert MOD.find_swallowed_credential_fetches(f) == []

    def test_swallow_without_credential_command_not_flagged(self, tmp_path: Path) -> None:
        f = _write(tmp_path / "s.sh", "rm -rf _work/* _diag/*.log 2>/dev/null || true\n")
        assert MOD.find_swallowed_credential_fetches(f) == []

    def test_secrets_list_not_a_fetch_not_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "s.sh",
            'NAMES=$(gcloud secrets list --format="value(name)" 2>/dev/null || true)\n',
        )
        assert MOD.find_swallowed_credential_fetches(f) == []

    def test_secrets_add_iam_policy_binding_not_a_fetch_not_flagged(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "s.sh",
            'gcloud secrets add-iam-policy-binding "$s" --member=X --role=Y 2>/dev/null || true\n',
        )
        assert MOD.find_swallowed_credential_fetches(f) == []

    def test_existence_check_if_then_not_flagged(self, tmp_path: Path) -> None:
        # `if cmd &>/dev/null; then` examines the exit code via `if` — it does
        # not discard it with `|| true`, so this is not the banned idiom.
        f = _write(
            tmp_path / "s.sh",
            'if gcloud secrets describe "$s" --project="$p" &>/dev/null; then\n  echo exists\nfi\n',
        )
        assert MOD.find_swallowed_credential_fetches(f) == []

    def test_noqa_marker_skipped(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "s.sh",
            "# noqa: swallowed-credential-fetch - documented dev-only fallback\n"
            "T=$(gcloud secrets versions access latest --secret=X 2>/dev/null || true)\n",
        )
        assert MOD.find_swallowed_credential_fetches(f) == []

    def test_noqa_marker_on_continued_line_skipped(self, tmp_path: Path) -> None:
        f = _write(
            tmp_path / "s.sh",
            "T=$(gcloud secrets versions access latest --secret=X \\\n"
            "  2>/dev/null || true)  # noqa: swallowed-credential-fetch\n",
        )
        assert MOD.find_swallowed_credential_fetches(f) == []


# ── scan_repo — scripts/-only scope ──────────────────────────────────────────


class TestScanRepoScope:
    def test_only_scripts_dir_scanned(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(
            repo / "scripts" / "s.sh",
            "T=$(gcloud secrets versions access latest --secret=X 2>/dev/null || true)\n",
        )
        _write(
            repo / "not-scripts" / "s.sh",
            "T=$(gcloud secrets versions access latest --secret=X 2>/dev/null || true)\n",
        )
        scan = MOD.scan_repo(repo, "repo-a")
        assert scan.count == 1

    def test_missing_scripts_dir_scores_zero(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        scan = MOD.scan_repo(repo, "repo-a")
        assert scan.count == 0

    def test_non_sh_file_not_scanned(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(
            repo / "scripts" / "s.py",
            "T = 'gcloud secrets versions access latest --secret=X 2>/dev/null || true'\n",
        )
        scan = MOD.scan_repo(repo, "repo-a")
        assert scan.count == 0


# ── baseline-ratchet semantics via main() ────────────────────────────────────

_VIOLATION_SOURCE = "T=$(gcloud secrets versions access latest --secret=X 2>/dev/null || true)\n"


class TestBaselineRatchet:
    def test_over_baseline_fails(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "scripts" / "s.sh", _VIOLATION_SOURCE)
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline)])
        assert rc == 1

    def test_at_baseline_passes(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "scripts" / "s.sh", _VIOLATION_SOURCE)
        baseline = tmp_path / "bl.yaml"
        baseline.write_text("repos:\n  repo-a:\n    count: 1\n", encoding="utf-8")
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline)])
        assert rc == 0

    def test_clean_repo_passes_at_zero_default(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "scripts" / "s.sh", "echo hello\n")
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline)])
        assert rc == 0

    def test_synthetic_new_site_fails_at_seeded_baseline(self, tmp_path: Path) -> None:
        """Done-when criterion: the checker enumerates today's hits, then fails
        the moment a NEW (synthetic) hit is introduced beyond that baseline."""
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "scripts" / "s.sh", _VIOLATION_SOURCE)
        baseline = tmp_path / "bl.yaml"
        # Seed the baseline at today's real count (1).
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline), "--update-baseline"])
        assert rc == 0
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline)])
        assert rc == 0
        # Introduce a brand-new synthetic swallow site — must now fail.
        _write(repo / "scripts" / "new.sh", _VIOLATION_SOURCE)
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline)])
        assert rc == 1

    def test_update_baseline_clamps_down_never_up(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path, "repo-a")
        _write(repo / "scripts" / "s.sh", _VIOLATION_SOURCE * 2)  # 2 sites
        baseline = tmp_path / "bl.yaml"
        baseline.write_text("repos:\n  repo-a:\n    count: 1\n", encoding="utf-8")
        rc = MOD.main(["--workspace-root", str(tmp_path), "--baseline-file", str(baseline), "--update-baseline"])
        assert rc == 0
        reloaded = MOD.load_baseline(baseline)
        assert reloaded.allowed("repo-a") == 1  # clamped to the prior baseline, not raised to 2

    def test_scope_mode_single_repo(self, tmp_path: Path) -> None:
        repo_a = _make_repo(tmp_path, "repo-a")
        _write(repo_a / "scripts" / "s.sh", _VIOLATION_SOURCE)
        repo_b = _make_repo(tmp_path, "repo-b")
        _write(repo_b / "scripts" / "s.sh", "echo hello\n")
        baseline = tmp_path / "bl.yaml"
        rc = MOD.main(["--workspace-root", str(tmp_path), "--scope", "repo-b", "--baseline-file", str(baseline)])
        assert rc == 0  # repo-a's violation is out of scope
        rc = MOD.main(["--workspace-root", str(tmp_path), "--scope", "repo-a", "--baseline-file", str(baseline)])
        assert rc == 1
