# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_doc_body_links.py.

Verifies the live corpus is clean against its seeded baseline (via the CLI, matching how the QG
gate actually invokes it), and that each link-shape/resolution class is caught (or correctly
excluded) on a synthetic doc tree.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from check_doc_body_links import find_broken_links  # type: ignore[import-not-found]

_PM_ROOT = _HERE.parents[1]


def test_live_corpus_has_zero_new_broken_body_links() -> None:
    """The real corpus must pass its own ratchet right now (baseline absorbs pre-existing debt)."""
    result = subprocess.run(
        [sys.executable, str(_HERE / "check_doc_body_links.py"), "--quiet"],
        cwd=_PM_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"NEW broken body links found:\n{result.stdout}\n{result.stderr}"


def test_relative_link_resolves_against_doc_dir(tmp_path: Path) -> None:
    (tmp_path / "codex" / "02-data").mkdir(parents=True)
    (tmp_path / "codex" / "02-data" / "target.md").write_text("# Target\n", encoding="utf-8")
    src = tmp_path / "codex" / "02-data" / "source.md"
    src.write_text("See [target](target.md) for detail.\n", encoding="utf-8")

    broken = find_broken_links([src], tmp_path)
    assert broken == {}


def test_dot_dot_relative_link_resolves(tmp_path: Path) -> None:
    (tmp_path / "codex" / "04-architecture").mkdir(parents=True)
    (tmp_path / "codex" / "02-data").mkdir(parents=True)
    (tmp_path / "codex" / "02-data" / "target.md").write_text("# Target\n", encoding="utf-8")
    src = tmp_path / "codex" / "04-architecture" / "source.md"
    src.write_text("See [target](../02-data/target.md).\n", encoding="utf-8")

    broken = find_broken_links([src], tmp_path)
    assert broken == {}


def test_broken_relative_link_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "codex" / "02-data").mkdir(parents=True)
    src = tmp_path / "codex" / "02-data" / "source.md"
    src.write_text("See [missing](does-not-exist.md) for detail.\n", encoding="utf-8")

    broken = find_broken_links([src], tmp_path)
    assert "codex/02-data/source.md" in broken
    assert broken["codex/02-data/source.md"] == [(1, "does-not-exist.md")]


def test_leading_slash_repo_root_relative_link_resolves(tmp_path: Path) -> None:
    """`/codex/foo.md` means "<pm_root>/codex/foo.md" in this corpus, not filesystem-absolute —
    pathlib's `Path.__truediv__` silently drops the left side on a leading-"/" right operand, which
    is the exact bug this test guards against regressing."""
    (tmp_path / "codex" / "09-strategy").mkdir(parents=True)
    (tmp_path / "codex" / "09-strategy" / "target.md").write_text("# Target\n", encoding="utf-8")
    src = tmp_path / "plans" / "epics"
    src.mkdir(parents=True)
    doc = src / "source.md"
    doc.write_text("SSOT: [target](/codex/09-strategy/target.md)\n", encoding="utf-8")

    broken = find_broken_links([doc], tmp_path)
    assert broken == {}


def test_leading_slash_broken_target_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "plans").mkdir(parents=True)
    doc = tmp_path / "plans" / "source.md"
    doc.write_text("SSOT: [target](/codex/does-not-exist.md)\n", encoding="utf-8")

    broken = find_broken_links([doc], tmp_path)
    assert broken == {"plans/source.md": [(1, "/codex/does-not-exist.md")]}


def test_archived_target_resolves_via_basename_fallback(tmp_path: Path) -> None:
    (tmp_path / "plans" / "archive" / "2026_06").mkdir(parents=True)
    (tmp_path / "plans" / "archive" / "2026_06" / "old_plan_2026_06_01.md").write_text("# Old\n", encoding="utf-8")
    (tmp_path / "plans" / "active").mkdir(parents=True)
    doc = tmp_path / "plans" / "active" / "source.md"
    doc.write_text("See [the old plan](old_plan_2026_06_01.md) for history.\n", encoding="utf-8")

    broken = find_broken_links([doc], tmp_path)
    assert broken == {}


def test_http_and_mailto_and_webview_links_are_never_checked(tmp_path: Path) -> None:
    (tmp_path / "plans").mkdir(parents=True)
    doc = tmp_path / "plans" / "source.md"
    doc.write_text(
        "External: [site](https://example.com/foo.md)\n"
        "Mail: [contact](mailto:foo@example.com)\n"
        "Editor: [pasted](vscode-webview://abc123/some/path.md)\n",
        encoding="utf-8",
    )

    broken = find_broken_links([doc], tmp_path)
    assert broken == {}


def test_anchor_only_link_is_never_checked(tmp_path: Path) -> None:
    (tmp_path / "plans").mkdir(parents=True)
    doc = tmp_path / "plans" / "source.md"
    doc.write_text("Jump to [section below](#some-heading).\n", encoding="utf-8")

    broken = find_broken_links([doc], tmp_path)
    assert broken == {}


def test_non_doc_extension_target_is_never_checked(tmp_path: Path) -> None:
    """Links to .py/.yaml/.json etc. are out of this checker's scope (mirrors validate_doc_references()
    deliberately excluding code_refs) — only .md/.mdc targets are existence-checked."""
    (tmp_path / "plans").mkdir(parents=True)
    doc = tmp_path / "plans" / "source.md"
    doc.write_text("See [the script](does_not_exist.py) for detail.\n", encoding="utf-8")

    broken = find_broken_links([doc], tmp_path)
    assert broken == {}


def test_link_inside_fenced_code_block_is_ignored(tmp_path: Path) -> None:
    """A code fence demonstrating markdown link syntax as an example is not a real reference."""
    (tmp_path / "plans").mkdir(parents=True)
    doc = tmp_path / "plans" / "source.md"
    doc.write_text(
        "Example usage:\n```markdown\n[broken](does-not-exist.md)\n```\nReal text after.\n",
        encoding="utf-8",
    )

    broken = find_broken_links([doc], tmp_path)
    assert broken == {}


def test_link_inside_frontmatter_block_is_ignored(tmp_path: Path) -> None:
    """Frontmatter path-shaped free_list fields are already covered by validate_doc_references() —
    this checker only looks at the body, so a frontmatter value that happens to look like a markdown
    link must not be double-counted (or false-flagged if it's YAML, not actually a markdown link)."""
    (tmp_path / "plans").mkdir(parents=True)
    doc = tmp_path / "plans" / "source.md"
    doc.write_text(
        "---\nrelated: [does-not-exist.md]\n---\n\n[real broken link](also-does-not-exist.md)\n",
        encoding="utf-8",
    )

    broken = find_broken_links([doc], tmp_path)
    assert broken == {"plans/source.md": [(5, "also-does-not-exist.md")]}


def test_duplicate_broken_target_in_one_doc_reported_once(tmp_path: Path) -> None:
    (tmp_path / "plans").mkdir(parents=True)
    doc = tmp_path / "plans" / "source.md"
    doc.write_text("First mention [here](missing.md) and again [here](missing.md) later.\n", encoding="utf-8")

    broken = find_broken_links([doc], tmp_path)
    assert broken == {"plans/source.md": [(1, "missing.md")]}
