"""Unit tests for scripts/generate-workflow-catalog.py.

Tests cover:
- YAML loading + the `on:` block's YAML-1.1 True-key coercion tolerance
- Trigger / concurrency / mutation / fires-next summarization
- Dispatch-listener construction from repository_dispatch types
- End-to-end main() against a fixture .github/workflows/ tree
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate-workflow-catalog.py"


def _load_module():
    """Load generate-workflow-catalog.py as a module."""
    spec = importlib.util.spec_from_file_location("generate_workflow_catalog", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── _load_yaml / _on_block ───────────────────────────────────────────────────


def test_load_yaml_parses_dict(tmp_path: Path) -> None:
    p = tmp_path / "wf.yml"
    p.write_text("name: my-workflow\non:\n  push:\n    branches: [main]\n")
    data = MOD._load_yaml(p)
    assert data["name"] == "my-workflow"


def test_load_yaml_non_dict_returns_empty(tmp_path: Path) -> None:
    p = tmp_path / "wf.yml"
    p.write_text("- just\n- a\n- list\n")
    assert MOD._load_yaml(p) == {}


def test_on_block_true_key_coercion() -> None:
    # PyYAML(1.1) parses bare `on:` as the boolean key True.
    data = {True: {"push": {}}}
    assert MOD._on_block(data) == {"push": {}}


def test_on_block_string_key() -> None:
    data = {"on": {"workflow_dispatch": {}}}
    assert MOD._on_block(data) == {"workflow_dispatch": {}}


def test_on_block_list_form() -> None:
    data = {"on": ["push", "pull_request"]}
    assert MOD._on_block(data) == {"push": {}, "pull_request": {}}


def test_on_block_str_form() -> None:
    data = {"on": "push"}
    assert MOD._on_block(data) == {"push": {}}


def test_on_block_missing_returns_empty() -> None:
    assert MOD._on_block({}) == {}


# ── _as_list ─────────────────────────────────────────────────────────────────


def test_as_list_from_list() -> None:
    assert MOD._as_list(["a", "b"]) == ["a", "b"]


def test_as_list_from_none() -> None:
    assert MOD._as_list(None) == []


def test_as_list_from_scalar() -> None:
    assert MOD._as_list("main") == ["main"]


# ── summarize_triggers ───────────────────────────────────────────────────────


def test_summarize_triggers_schedule() -> None:
    on = {"schedule": [{"cron": "0 * * * *"}, {"cron": "30 5 * * *"}]}
    assert MOD.summarize_triggers(on) == "schedule(0 * * * *, 30 5 * * *)"


def test_summarize_triggers_push_with_branches() -> None:
    on = {"push": {"branches": ["live-defi-rollout"]}}
    assert MOD.summarize_triggers(on) == "push[live-defi-rollout]"


def test_summarize_triggers_pull_request_no_branches() -> None:
    on = {"pull_request": {}}
    assert MOD.summarize_triggers(on) == "PR"


def test_summarize_triggers_workflow_run() -> None:
    on = {"workflow_run": {"workflows": ["quality-gates-v2"], "branches": ["staging"]}}
    assert MOD.summarize_triggers(on) == "after:quality-gates-v2[staging]"


def test_summarize_triggers_repository_dispatch_with_types() -> None:
    on = {"repository_dispatch": {"types": ["escalate"]}}
    assert MOD.summarize_triggers(on) == "dispatch:escalate"


def test_summarize_triggers_repository_dispatch_no_types() -> None:
    on = {"repository_dispatch": {}}
    assert MOD.summarize_triggers(on) == "dispatch"


def test_summarize_triggers_workflow_call() -> None:
    assert MOD.summarize_triggers({"workflow_call": {}}) == "callable"


def test_summarize_triggers_workflow_dispatch() -> None:
    assert MOD.summarize_triggers({"workflow_dispatch": {}}) == "manual"


def test_summarize_triggers_issue_comment() -> None:
    assert MOD.summarize_triggers({"issue_comment": {}}) == "issue_comment"


def test_summarize_triggers_multiple_stable_order() -> None:
    on = {"workflow_dispatch": {}, "schedule": [{"cron": "0 0 * * *"}]}
    assert MOD.summarize_triggers(on) == "schedule(0 0 * * *) · manual"


def test_summarize_triggers_empty() -> None:
    assert MOD.summarize_triggers({}) == "—"


# ── summarize_concurrency ────────────────────────────────────────────────────


def test_summarize_concurrency_string() -> None:
    assert MOD.summarize_concurrency({"concurrency": "my-group"}) == "`my-group`"


def test_summarize_concurrency_dict_with_cancel() -> None:
    data = {"concurrency": {"group": "${{ github.workflow }}-${{ github.ref }}", "cancel-in-progress": True}}
    assert MOD.summarize_concurrency(data) == "`<wf>-<ref>` cancel"


def test_summarize_concurrency_dict_no_cancel() -> None:
    data = {"concurrency": {"group": "fixed-group"}}
    assert MOD.summarize_concurrency(data) == "`fixed-group`"


def test_summarize_concurrency_dict_other_var() -> None:
    data = {"concurrency": {"group": "${{ matrix.name }}"}}
    assert MOD.summarize_concurrency(data) == "`<var>`"


def test_summarize_concurrency_missing() -> None:
    assert MOD.summarize_concurrency({}) == "—"


# ── detect_mutations ─────────────────────────────────────────────────────────


def test_detect_mutations_manifest_to_main() -> None:
    text = "run: |\n  git commit -m x workspace-manifest.json\n  git push origin HEAD:main\n"
    assert "manifest→main" in MOD.detect_mutations(text)


def test_detect_mutations_manifest_only() -> None:
    text = "run: |\n  git commit workspace-manifest.json\n"
    assert MOD.detect_mutations(text) == "manifest"


def test_detect_mutations_to_main_only() -> None:
    text = "run: git push origin HEAD:main\n"
    assert "→main" in MOD.detect_mutations(text)


def test_detect_mutations_to_ldr() -> None:
    text = "run: git push origin push:live-defi-rollout\n"
    assert "→LDR" in MOD.detect_mutations(text)


def test_detect_mutations_opens_pr() -> None:
    assert "opens-PR" in MOD.detect_mutations("run: gh pr create --title x")


def test_detect_mutations_merges_pr() -> None:
    assert "merges-PR" in MOD.detect_mutations("run: gh pr merge --auto")


def test_detect_mutations_firestore() -> None:
    assert "Firestore" in MOD.detect_mutations("run: python ci_status_store.py")


def test_detect_mutations_tags() -> None:
    assert "tags" in MOD.detect_mutations("run: git tag v1.2.3\n")


def test_detect_mutations_slack() -> None:
    assert "Slack" in MOD.detect_mutations("uses: ./.github/workflows/notify-slack.yml")


def test_detect_mutations_read_only() -> None:
    assert MOD.detect_mutations("run: echo hello") == "read-only"


# ── detect_fires_next / build_dispatch_listeners ────────────────────────────


def test_detect_fires_next_gh_workflow_run() -> None:
    text = "run: gh workflow run quality-gates-v2.yml --ref main"
    assert MOD.detect_fires_next(text, {}, "caller") == "quality-gates-v2"


def test_detect_fires_next_reusable_call() -> None:
    text = "uses: ./.github/workflows/notify-slack.yml"
    # notify-slack is elided as a ubiquitous reusable alert
    assert MOD.detect_fires_next(text, {}, "caller") == "—"


def test_detect_fires_next_reusable_call_non_elided() -> None:
    text = "uses: ./.github/workflows/ldr-to-main-promote.yml"
    assert MOD.detect_fires_next(text, {}, "caller") == "ldr-to-main-promote"


def test_detect_fires_next_via_repository_dispatch() -> None:
    text = 'run: gh api repos/x/dispatches -f event_type=escalate'
    listeners = {"escalate": ["cicd-escalation-handler"]}
    assert MOD.detect_fires_next(text, listeners, "caller") == "cicd-escalation-handler*"


def test_detect_fires_next_self_reference_discarded() -> None:
    text = "run: gh workflow run self-name.yml"
    assert MOD.detect_fires_next(text, {}, "self-name") == "—"


def test_detect_fires_next_no_matches() -> None:
    assert MOD.detect_fires_next("run: echo hi", {}, "caller") == "—"


def test_build_dispatch_listeners() -> None:
    workflows = {
        "listener-a": {"on": {"repository_dispatch": {"types": ["escalate"]}}},
        "listener-b": {"on": {"repository_dispatch": {"types": ["escalate", "other"]}}},
        "non-listener": {"on": {"push": {}}},
    }
    listeners = MOD.build_dispatch_listeners(workflows)
    assert set(listeners["escalate"]) == {"listener-a", "listener-b"}
    assert listeners["other"] == ["listener-b"]
    assert "non-listener" not in listeners.get("escalate", [])


# ── main() end-to-end against a fixture workflow tree ───────────────────────


@pytest.fixture
def fixture_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a throwaway repo_root with its own .github/workflows/, so main()
    (which derives repo_root from `__file__`) never touches the real checked-in
    docs/repo-management/CICD-WORKFLOW-CATALOG.md."""
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    (tmp_path / "docs" / "repo-management").mkdir(parents=True)

    (wf_dir / "quality-gates-v2.yml").write_text(
        "name: quality-gates-v2\n"
        "on:\n"
        "  push:\n"
        "    branches: [live-defi-rollout]\n"
        "concurrency: qg-${{ github.ref }}\n"
        "jobs:\n"
        "  gate:\n"
        "    steps:\n"
        "      - run: echo checking\n"
    )
    (wf_dir / "ldr-to-main-promote.yml").write_text(
        "name: ldr-to-main-promote\n"
        "on:\n"
        "  schedule:\n"
        "    - cron: '*/15 * * * *'\n"
        "jobs:\n"
        "  promote:\n"
        "    steps:\n"
        "      - run: gh pr create --title promote\n"
    )
    (wf_dir / "totally-unclassified.yml").write_text(
        "name: totally-unclassified\non:\n  workflow_dispatch: {}\njobs:\n  x:\n    steps:\n      - run: echo hi\n"
    )

    # main() computes `repo_root = Path(__file__).resolve().parent.parent` — patch the
    # module's __file__ so it resolves to our throwaway tree instead of the real repo root.
    fake_script = tmp_path / "scripts" / "generate-workflow-catalog.py"
    monkeypatch.setattr(MOD, "__file__", str(fake_script))
    return tmp_path


def test_main_writes_catalog(fixture_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    MOD.main()
    out_path = fixture_repo / "docs" / "repo-management" / "CICD-WORKFLOW-CATALOG.md"
    assert out_path.exists()
    content = out_path.read_text()
    assert "`quality-gates-v2`" in content
    assert "`ldr-to-main-promote`" in content
    assert "Unclassified" in content
    captured = capsys.readouterr()
    assert "3 workflows" in captured.out
    assert "unclassified" in captured.err.lower()


def test_main_no_workflows_exits_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / "docs" / "repo-management").mkdir(parents=True)
    fake_script = tmp_path / "scripts" / "generate-workflow-catalog.py"
    monkeypatch.setattr(MOD, "__file__", str(fake_script))
    with pytest.raises(SystemExit) as exc_info:
        MOD.main()
    assert exc_info.value.code == 1


def test_module_importable_as_script() -> None:
    # Guards against the module being unimportable under `python3 scripts/generate-workflow-catalog.py`
    assert "generate_workflow_catalog" in sys.modules or MOD.__name__ == "generate_workflow_catalog"
