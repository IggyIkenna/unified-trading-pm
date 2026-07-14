"""Unit tests for scripts/generate-workflow-catalog.py.

Tests cover:
- YAML `on:` block normalization (dict / YAML-1.1 True-key / list / string forms)
- Trigger, concurrency, mutation, and fires-next summarization
- Dispatch-listener index construction
- End-to-end catalog generation (main())
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate-workflow-catalog.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_workflow_catalog", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── _load_yaml / _on_block ───────────────────────────────────────────────────


def test_load_yaml_dict(tmp_path: Path) -> None:
    p = tmp_path / "wf.yml"
    p.write_text("name: foo\non:\n  push: {}\n")
    data = MOD._load_yaml(p)
    assert data["name"] == "foo"


def test_load_yaml_non_dict_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / "wf.yml"
    p.write_text("- a\n- b\n")
    assert MOD._load_yaml(p) == {}


def test_on_block_dict() -> None:
    assert MOD._on_block({"on": {"push": {}}}) == {"push": {}}


def test_on_block_yaml_true_key_coercion() -> None:
    """PyYAML(1.1) parses bare `on:` as the boolean key True."""
    assert MOD._on_block({True: {"push": {}}}) == {"push": {}}


def test_on_block_list_form() -> None:
    assert MOD._on_block({"on": ["push", "pull_request"]}) == {"push": {}, "pull_request": {}}


def test_on_block_string_form() -> None:
    assert MOD._on_block({"on": "push"}) == {"push": {}}


def test_on_block_missing() -> None:
    assert MOD._on_block({}) == {}


# ── _as_list ──────────────────────────────────────────────────────────────


def test_as_list_from_list() -> None:
    assert MOD._as_list(["a", "b"]) == ["a", "b"]


def test_as_list_from_none() -> None:
    assert MOD._as_list(None) == []


def test_as_list_from_scalar() -> None:
    assert MOD._as_list("main") == ["main"]


# ── summarize_triggers ────────────────────────────────────────────────────


def test_summarize_triggers_schedule() -> None:
    on = {"schedule": [{"cron": "*/15 * * * *"}]}
    assert MOD.summarize_triggers(on) == "schedule(*/15 * * * *)"


def test_summarize_triggers_push_with_branches() -> None:
    on = {"push": {"branches": ["main", "live-defi-rollout"]}}
    assert MOD.summarize_triggers(on) == "push[main,live-defi-rollout]"


def test_summarize_triggers_pull_request_no_branches() -> None:
    on = {"pull_request": {}}
    assert MOD.summarize_triggers(on) == "PR"


def test_summarize_triggers_workflow_run() -> None:
    on = {"workflow_run": {"workflows": ["quality-gates-v2"], "branches": ["main"]}}
    assert MOD.summarize_triggers(on) == "after:quality-gates-v2[main]"


def test_summarize_triggers_repository_dispatch() -> None:
    on = {"repository_dispatch": {"types": ["ci-failure"]}}
    assert MOD.summarize_triggers(on) == "dispatch:ci-failure"


def test_summarize_triggers_workflow_call() -> None:
    assert MOD.summarize_triggers({"workflow_call": {}}) == "callable"


def test_summarize_triggers_workflow_dispatch() -> None:
    assert MOD.summarize_triggers({"workflow_dispatch": {}}) == "manual"


def test_summarize_triggers_issue_comment() -> None:
    assert MOD.summarize_triggers({"issue_comment": {}}) == "issue_comment"


def test_summarize_triggers_combined_stable_order() -> None:
    on = {"pull_request": {}, "schedule": [{"cron": "0 0 * * *"}]}
    assert MOD.summarize_triggers(on) == "schedule(0 0 * * *) · PR"


def test_summarize_triggers_empty() -> None:
    assert MOD.summarize_triggers({}) == "—"


# ── summarize_concurrency ─────────────────────────────────────────────────


def test_summarize_concurrency_string() -> None:
    assert MOD.summarize_concurrency({"concurrency": "my-group"}) == "`my-group`"


def test_summarize_concurrency_dict_with_cancel() -> None:
    data = {"concurrency": {"group": "wf-${{ github.ref }}", "cancel-in-progress": True}}
    assert MOD.summarize_concurrency(data) == "`wf-<ref>` cancel"


def test_summarize_concurrency_dict_without_cancel() -> None:
    data = {"concurrency": {"group": "static-group"}}
    assert MOD.summarize_concurrency(data) == "`static-group`"


def test_summarize_concurrency_workflow_and_ref_vars() -> None:
    data = {"concurrency": {"group": "${{ github.workflow }}-${{ github.ref }}"}}
    assert MOD.summarize_concurrency(data) == "`<wf>-<ref>`"


def test_summarize_concurrency_other_var() -> None:
    data = {"concurrency": {"group": "${{ inputs.name }}"}}
    assert MOD.summarize_concurrency(data) == "`<var>`"


def test_summarize_concurrency_missing() -> None:
    assert MOD.summarize_concurrency({}) == "—"


# ── detect_mutations ──────────────────────────────────────────────────────


def test_detect_mutations_manifest_to_main() -> None:
    text = "run: |\n  git commit -m x workspace-manifest.json\n  git push origin main\n"
    assert "manifest→main" in MOD.detect_mutations(text)


def test_detect_mutations_main_only() -> None:
    text = "run: git push origin main\n"
    assert MOD.detect_mutations(text) == "→main"


def test_detect_mutations_ldr() -> None:
    text = "run: git push origin live-defi-rollout\n"
    assert "→LDR" in MOD.detect_mutations(text)


def test_detect_mutations_opens_pr() -> None:
    assert "opens-PR" in MOD.detect_mutations("run: gh pr create --title x\n")


def test_detect_mutations_merges_pr() -> None:
    assert "merges-PR" in MOD.detect_mutations("run: gh pr merge --squash\n")


def test_detect_mutations_firestore() -> None:
    assert "Firestore" in MOD.detect_mutations("run: python ci_status_store.py\n")


def test_detect_mutations_tags() -> None:
    assert "tags" in MOD.detect_mutations("run: git push origin --tags\n")


def test_detect_mutations_slack() -> None:
    assert "Slack" in MOD.detect_mutations("uses: ./.github/workflows/notify-slack.yml\n")


def test_detect_mutations_read_only() -> None:
    assert MOD.detect_mutations("run: echo hello\n") == "read-only"


# ── detect_fires_next ─────────────────────────────────────────────────────


def test_detect_fires_next_gh_workflow_run() -> None:
    text = "run: gh workflow run downstream-wf.yml\n"
    assert MOD.detect_fires_next(text, {}, "source-wf") == "downstream-wf"


def test_detect_fires_next_reusable_call() -> None:
    text = "uses: ./.github/workflows/shared-gate.yml\n"
    assert MOD.detect_fires_next(text, {}, "source-wf") == "shared-gate"


def test_detect_fires_next_event_dispatch() -> None:
    text = "run: gh api repos/x/y/dispatches -f event_type=my-event\n"
    listeners = {"my-event": ["listener-wf"]}
    assert MOD.detect_fires_next(text, listeners, "source-wf") == "listener-wf*"


def test_detect_fires_next_event_dispatch_escaped_json() -> None:
    text = r'run: curl -d "{\"event_type\":\"my-event\"}"'
    listeners = {"my-event": ["listener-wf"]}
    assert MOD.detect_fires_next(text, listeners, "source-wf") == "listener-wf*"


def test_detect_fires_next_excludes_self() -> None:
    text = "run: gh api dispatches -f event_type=my-event\n"
    listeners = {"my-event": ["source-wf"]}
    assert MOD.detect_fires_next(text, listeners, "source-wf") == "—"


def test_detect_fires_next_discards_noise_targets() -> None:
    text = "uses: ./.github/workflows/notify-slack.yml\n"
    assert MOD.detect_fires_next(text, {}, "source-wf") == "—"


def test_detect_fires_next_none() -> None:
    assert MOD.detect_fires_next("run: echo hi\n", {}, "source-wf") == "—"


# ── build_dispatch_listeners ──────────────────────────────────────────────


def test_build_dispatch_listeners() -> None:
    workflows = {
        "listener-a": {"on": {"repository_dispatch": {"types": ["ci-failure"]}}},
        "listener-b": {"on": {"repository_dispatch": {"types": ["ci-failure", "other"]}}},
        "no-dispatch": {"on": {"push": {}}},
    }
    listeners = MOD.build_dispatch_listeners(workflows)
    assert sorted(listeners["ci-failure"]) == ["listener-a", "listener-b"]
    assert listeners["other"] == ["listener-b"]
    assert "no-dispatch" not in listeners


def test_build_dispatch_listeners_empty() -> None:
    assert MOD.build_dispatch_listeners({}) == {}


# ── main() end-to-end ─────────────────────────────────────────────────────


def _write_workflow(wf_dir: Path, name: str, content: str) -> None:
    (wf_dir / f"{name}.yml").write_text(content)


def test_main_generates_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    out_dir = tmp_path / "docs" / "repo-management"
    out_dir.mkdir(parents=True)

    _write_workflow(
        wf_dir,
        "quality-gates-v2",
        "name: quality-gates-v2\non:\n  pull_request:\n    branches: [live-defi-rollout]\n",
    )
    _write_workflow(
        wf_dir,
        "mystery-workflow",
        "name: mystery-workflow\non:\n  workflow_dispatch: {}\n",
    )

    monkeypatch.setattr(MOD, "__file__", str(tmp_path / "scripts" / "generate-workflow-catalog.py"))
    MOD.main()

    out_path = out_dir / "CICD-WORKFLOW-CATALOG.md"
    assert out_path.exists()
    content = out_path.read_text()
    assert "quality-gates-v2" in content
    assert "Unclassified" in content

    captured = capsys.readouterr()
    assert "Wrote" in captured.out
    assert "unclassified" in captured.err
    assert "mystery-workflow" in captured.err


def test_main_no_workflows_exits_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / "docs" / "repo-management").mkdir(parents=True)
    monkeypatch.setattr(MOD, "__file__", str(tmp_path / "scripts" / "generate-workflow-catalog.py"))

    with pytest.raises(SystemExit) as exc_info:
        MOD.main()
    assert exc_info.value.code == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
