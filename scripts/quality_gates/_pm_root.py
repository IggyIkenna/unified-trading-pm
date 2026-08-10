"""Resolve the unified-trading-pm checkout root without assuming its DIRECTORY NAME.

WHY THIS EXISTS (2026-08-10, pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md
F7): 13 call sites across 11 scripts in this directory resolved the PM root by walking UP to
the workspace root and back DOWN by a hard-coded directory name. That only works when the
checkout directory is literally named after the repo.

It broke the one mitigation that demonstrably survives this repo's concurrency: committing
from an isolated ``git worktree``. In a worktree named anything else, the lookup lands on a
path that does not exist, and -- worse than simply failing -- the caller reports it as a
CONTENT verdict. Measured live: a doc citing no ``<repo>@<sha>`` at all was rejected with "a
staged todo cites <repo>@<sha> that does not resolve to a real commit", because
``check_plan_commit_sha_evidence.py`` could not find ``plans/active`` and fell through to its
violation path.

The round trip was never necessary: every script in this directory lives at
``<PM>/scripts/quality_gates/``, so ``Path(__file__).resolve().parents[2]`` IS the PM root of
the checkout the script was invoked from -- worktree, clone, or renamed directory alike. The
``workspace_root`` argument is still genuinely needed for SIBLING repo discovery
(``<workspace>/market-tick-data-service`` etc.); it is only PM-root resolution that must stop
going through the name.

Fallback order is deliberate: prefer the checkout this script actually lives in (correct under
a worktree), then the legacy name-based path (correct when a script is somehow run from
outside a PM checkout), then ``None`` -- which callers must treat as an INFRASTRUCTURE error,
never as a content violation.
"""

from __future__ import annotations

from pathlib import Path

_PM_DIR_NAME = "unified-trading-pm"


def _looks_like_pm_root(candidate: Path) -> bool:
    """A PM checkout is identified by its CONTENT, not its name."""
    return (candidate / "plans").is_dir() and (candidate / "scripts" / "quality_gates").is_dir()


def pm_root(workspace_root: Path | None = None, *, caller_file: str | None = None) -> Path | None:
    """Absolute path to the PM checkout root, or ``None`` if it cannot be resolved.

    ``caller_file`` should be the calling module's ``__file__``; it defaults to this module's
    own location, which resolves identically for every current caller (all live in the same
    directory).
    """
    anchor = Path(caller_file).resolve() if caller_file else Path(__file__).resolve()
    # <PM>/scripts/quality_gates/<module>.py -> parents[2] == <PM>
    if len(anchor.parents) >= 3:
        candidate = anchor.parents[2]
        if _looks_like_pm_root(candidate):
            return candidate

    if workspace_root is not None:
        legacy = Path(workspace_root) / _PM_DIR_NAME
        if _looks_like_pm_root(legacy):
            return legacy

    return None


def pm_root_or_legacy(workspace_root: Path) -> Path:
    """``pm_root`` with the legacy path as an unconditional fallback.

    Returns the legacy ``<workspace_root>/unified-trading-pm`` path even when it does not
    exist, so a caller's own "not found" handling fires exactly as it did before this module
    existed. This keeps the change behaviour-preserving in a canonically-named checkout while
    fixing the worktree case.
    """
    resolved = pm_root(workspace_root)
    return resolved if resolved is not None else Path(workspace_root) / _PM_DIR_NAME
