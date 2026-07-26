"""Unit tests for scripts/quality_gates/check_dispatch_listeners.py.

Regression fixtures for the class of bug in
issues/post_cutover_silent_assumption_sweep_2026_07_23.md F1 (trading kill-switch
dispatches halt-order-flow/resume-order-flow to execution-service, which has no
listener — GitHub returns 204, read as success) + F3 (4 more orphan dispatches,
same class). Builds small synthetic fleets under tmp_path rather than depending on
the live workspace, so these stay green regardless of real-fleet drift; the live
F1+F3 reproduction + the baselined orphan count are recorded separately in
issues/post_cutover_silent_assumption_sweep_2026_07_23.md (this checker is
deliberately NOT wired into quality-gates.sh yet — see
ci_satellite_ao_dispatch_batch1_2026_07_26.md todo 2).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_dispatch_listeners.py"
    spec = importlib.util.spec_from_file_location("check_dispatch_listeners", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


def _make_repo(root: Path, name: str) -> Path:
    repo = root / name
    (repo / ".github" / "workflows").mkdir(parents=True)
    return repo


def _write_workflow(repo: Path, name: str, content: str) -> None:
    (repo / ".github" / "workflows" / name).write_text(content, encoding="utf-8")


class TestOrphanDispatch:
    def test_dispatch_with_no_listener_is_orphan(self, tmp_path: Path) -> None:
        """Mirrors F1: a dispatch to a repo with no matching listener."""
        source = _make_repo(tmp_path, "source-repo")
        target = _make_repo(tmp_path, "execution-service")
        _write_workflow(
            source,
            "kill-switch.yml",
            "on: {push: {branches: [main]}}\n"
            "jobs:\n"
            "  halt:\n"
            "    steps:\n"
            "      - run: |\n"
            '          gh api "repos/IggyIkenna/execution-service/dispatches" \\\n'
            "            -f event_type=halt-order-flow\n",
        )
        _write_workflow(
            target,
            "update-dependency-version.yml",
            "on:\n  repository_dispatch:\n    types: [dependency-update]\n",
        )

        sites = MOD.scan_dispatch_sites(tmp_path)
        listeners = MOD.scan_listeners(tmp_path)
        orphans, _ = MOD.find_orphans(sites, listeners)

        assert len(orphans) == 1
        assert orphans[0].site.event_type == "halt-order-flow"
        assert orphans[0].site.repo == "execution-service"
        assert orphans[0].reason == "no listener in execution-service"

    def test_dispatch_with_matching_listener_not_orphan(self, tmp_path: Path) -> None:
        source = _make_repo(tmp_path, "source-repo")
        target = _make_repo(tmp_path, "target-repo")
        _write_workflow(
            source,
            "notify.yml",
            "on: {push: {branches: [main]}}\n"
            "jobs:\n"
            "  n:\n"
            "    steps:\n"
            "      - run: |\n"
            '          gh api "repos/IggyIkenna/target-repo/dispatches" -f event_type=qg-passed\n',
        )
        _write_workflow(target, "listener.yml", "on:\n  repository_dispatch:\n    types: [qg-passed]\n")

        sites = MOD.scan_dispatch_sites(tmp_path)
        listeners = MOD.scan_listeners(tmp_path)
        orphans, _ = MOD.find_orphans(sites, listeners)

        assert orphans == []

    def test_wildcard_listener_covers_any_event_type(self, tmp_path: Path) -> None:
        source = _make_repo(tmp_path, "source-repo")
        target = _make_repo(tmp_path, "target-repo")
        _write_workflow(
            source,
            "notify.yml",
            "on: {push: {branches: [main]}}\n"
            "jobs:\n"
            "  n:\n"
            "    steps:\n"
            "      - run: |\n"
            '          gh api "repos/IggyIkenna/target-repo/dispatches" -f event_type=anything-at-all\n',
        )
        # No `types:` key — listens for every event_type.
        _write_workflow(target, "listener.yml", "on:\n  repository_dispatch: {}\n")

        sites = MOD.scan_dispatch_sites(tmp_path)
        listeners = MOD.scan_listeners(tmp_path)
        orphans, _ = MOD.find_orphans(sites, listeners)

        assert orphans == []

    def test_escaped_json_quotes_still_parse(self, tmp_path: Path) -> None:
        """cloudbuild.yaml / buildspec.aws.yaml embed the JSON body with escaped
        quotes (`-d "{\\"event_type\\":\\"X\\", ...}"`) — a naive ["']? match misses
        every hit there (the exact bug this test pins down)."""
        source = _make_repo(tmp_path, "source-repo")
        _make_repo(tmp_path, "deployment-service")
        (source / "cloudbuild.yaml").write_text(
            "steps:\n"
            '  - name: "gcr.io/cloud-builders/curl"\n'
            "    args:\n"
            "      - -c\n"
            "      - |\n"
            "          curl -X POST \\\n"
            "            https://api.github.com/repos/IggyIkenna/deployment-service/dispatches \\\n"
            '            -d "{\\"event_type\\":\\"service-deployed\\",\\"client_payload\\":{}}"\n',
            encoding="utf-8",
        )

        sites = MOD.scan_dispatch_sites(tmp_path)
        listeners = MOD.scan_listeners(tmp_path)
        orphans, _ = MOD.find_orphans(sites, listeners)

        assert len(orphans) == 1
        assert orphans[0].site.event_type == "service-deployed"

    def test_dynamic_target_orphan_when_zero_listeners_anywhere(self, tmp_path: Path) -> None:
        """Mirrors F3's cascade-qg-ordering.yml fan-out: the target repo is a loop
        variable (unresolvable statically), but if literally NO repo anywhere
        listens for the event_type, it is still a provable orphan."""
        source = _make_repo(tmp_path, "orchestrator-repo")
        _make_repo(tmp_path, "dependent-a")
        _write_workflow(
            source,
            "cascade.yml",
            "on: {push: {branches: [main]}}\n"
            "jobs:\n"
            "  cascade:\n"
            "    steps:\n"
            "      - run: |\n"
            '          cmd = ["gh", "api", f"repos/{OWNER}/{repo_name}/dispatches",\n'
            '                 "-f", "event_type=quality-gate-run"]\n',
        )

        sites = MOD.scan_dispatch_sites(tmp_path)
        listeners = MOD.scan_listeners(tmp_path)
        orphans, _ = MOD.find_orphans(sites, listeners)

        assert len(orphans) == 1
        assert orphans[0].reason == "no listener anywhere (dynamic target)"

    def test_dynamic_target_not_asserted_orphan_when_some_repo_listens(self, tmp_path: Path) -> None:
        """If SOME (but not necessarily the runtime-picked) repo listens for the
        dynamically-targeted event_type, statics alone cannot prove orphan OR
        clean — must not silently drop it either way (falls to `unresolved`)."""
        source = _make_repo(tmp_path, "orchestrator-repo")
        listener_repo = _make_repo(tmp_path, "dependent-a")
        _write_workflow(
            source,
            "cascade.yml",
            "on: {push: {branches: [main]}}\n"
            "jobs:\n"
            "  cascade:\n"
            "    steps:\n"
            "      - run: |\n"
            '          cmd = ["gh", "api", f"repos/{OWNER}/{repo_name}/dispatches",\n'
            '                 "-f", "event_type=quality-gate-run"]\n',
        )
        _write_workflow(listener_repo, "listener.yml", "on:\n  repository_dispatch:\n    types: [quality-gate-run]\n")

        sites = MOD.scan_dispatch_sites(tmp_path)
        listeners = MOD.scan_listeners(tmp_path)
        orphans, unresolved = MOD.find_orphans(sites, listeners)

        assert orphans == []
        assert len(unresolved) == 1

    def test_shell_wrapper_dispatch_resolves_per_call_site(self, tmp_path: Path) -> None:
        """Mirrors trading-kill-switch.sh's dispatch_event() shape exactly: a
        fixed-target shell function whose event_type comes from its OWN first
        positional arg, called twice with two different literal event_types."""
        source = _make_repo(tmp_path, "source-repo")
        _make_repo(tmp_path, "execution-service")
        script_dir = source / "scripts" / "deploy"
        script_dir.mkdir(parents=True)
        (script_dir / "kill-switch.sh").write_text(
            "#!/usr/bin/env bash\n"
            'REPO_OWNER="${3:-IggyIkenna}"\n'
            'TARGET_REPO="execution-service"\n'
            "\n"
            "dispatch_event() {\n"
            '  local event_type="$1"\n'
            '  local payload="${2:-{}}"\n'
            '  HTTP_CODE=$(curl -s -o /tmp/x -w "%{http_code}" \\\n'
            '    "https://api.github.com/repos/${REPO_OWNER}/${TARGET_REPO}/dispatches" \\\n'
            '    -d "{\\"event_type\\": \\"${event_type}\\", \\"client_payload\\": ${payload}}")\n'
            "}\n"
            "\n"
            'dispatch_event "halt-order-flow" "$payload"\n'
            'dispatch_event "resume-order-flow" "$payload"\n',
            encoding="utf-8",
        )

        sites = MOD.scan_dispatch_sites(tmp_path)
        listeners = MOD.scan_listeners(tmp_path)
        orphans, _ = MOD.find_orphans(sites, listeners)

        event_types = sorted(o.site.event_type for o in orphans)
        assert event_types == ["halt-order-flow", "resume-order-flow"]
        assert all(o.site.repo == "execution-service" for o in orphans)


class TestBaselineRatchet:
    def _fixture(self, tmp_path: Path, *, extra_orphan: bool) -> Path:
        source = _make_repo(tmp_path, "source-repo")
        _make_repo(tmp_path, "execution-service")
        lines = [
            "on: {push: {branches: [main]}}",
            "jobs:",
            "  n:",
            "    steps:",
            "      - run: |",
            '          gh api "repos/IggyIkenna/execution-service/dispatches" -f event_type=halt-order-flow',
        ]
        if extra_orphan:
            lines.append(
                '          gh api "repos/IggyIkenna/execution-service/dispatches" -f event_type=a-brand-new-orphan'
            )
        _write_workflow(source, "kill-switch.yml", "\n".join(lines) + "\n")
        return tmp_path

    @staticmethod
    def _run(monkeypatch: pytest.MonkeyPatch, workspace: Path, baseline_path: Path, *, write: bool = False) -> int:
        argv = [
            "check_dispatch_listeners.py",
            "--workspace-root",
            str(workspace),
            "--baseline-path",
            str(baseline_path),
        ]
        if write:
            argv.append("--baseline-write")
        monkeypatch.setattr(sys, "argv", argv)
        return MOD.main()

    def test_exits_zero_at_baseline(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        workspace = self._fixture(tmp_path, extra_orphan=False)
        baseline_path = tmp_path / "baseline.yaml"
        assert self._run(monkeypatch, workspace, baseline_path, write=True) == 0
        assert self._run(monkeypatch, workspace, baseline_path) == 0

    def test_exits_nonzero_on_new_orphan_beyond_baseline(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        workspace = self._fixture(tmp_path, extra_orphan=False)
        baseline_path = tmp_path / "baseline.yaml"
        assert self._run(monkeypatch, workspace, baseline_path, write=True) == 0

        # Same workspace, one NEW synthetic orphan dispatch added — must fail.
        workspace2 = self._fixture(tmp_path / "v2", extra_orphan=True)
        assert self._run(monkeypatch, workspace2, baseline_path) == 1
