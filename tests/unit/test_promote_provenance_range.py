"""Hermetic unit tests for the since-last-promote provenance range computation.

Locks in the fix for `provenance_gate_squash_perpetual_block_2026_06_17.md`: the promote
bots must run `check_strict_quickmerge.py` over `<last-promoted-marker>..LDR`, NOT raw
`<target>..LDR` (squash-promotes make the raw range re-flag an already-drained commit
forever). The two invariants under test:
  1. marker present + usable → `<marker>..<ldr>` (only commits since the last drain).
  2. FAIL-SAFE: no marker / unusable marker → raw `<base>..<ldr>` (WIDEN, never narrow).

ALSO locks in the fix for
`provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`: a marker SHA
that still exists as a git object (`commit_reachable` true) but is NOT a true ancestor of
`ldr_ref` (e.g. orphaned by a history rewrite) must be treated as unusable — "usable" means
BOTH reachable AND an ancestor, not reachable alone.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

# Load the helper by path (scripts/ is not an importable package) — mirrors
# test_tier_c_promotion_gate.py's loader.
_MOD_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "promote_provenance_range.py"
_spec = importlib.util.spec_from_file_location("promote_provenance_range", _MOD_PATH)
assert _spec and _spec.loader
ppr = importlib.util.module_from_spec(_spec)
sys.modules["promote_provenance_range"] = ppr
_spec.loader.exec_module(ppr)


# ── resolve_range: the core marker-vs-fallback decision ──────────────────────


def test_marker_present_and_usable_uses_marker_range():
    rng, mode = ppr.resolve_range(
        "abc123", base_ref="origin/staging", ldr_ref="origin/live-defi-rollout", marker_usable=True
    )
    assert mode == "marker"
    assert rng == "abc123..origin/live-defi-rollout"


def test_marker_present_but_unusable_falls_back():
    # The unusable-marker fail-safe. `marker_usable=False` covers BOTH sub-cases the caller
    # composes it from: an unreachable object (e.g. LDR was force-synced and the marker is
    # gone) AND a reachable-but-non-ancestor object (see the `marker_usability` tests below for
    # the history-rewrite regression that specifically exercises the latter).
    rng, mode = ppr.resolve_range(
        "deadbeef", base_ref="origin/staging", ldr_ref="origin/live-defi-rollout", marker_usable=False
    )
    assert mode == "fallback"
    assert rng == "origin/staging..origin/live-defi-rollout"


def test_no_marker_falls_back():
    # First drain ever (no merged promote PR) → raw range.
    rng, mode = ppr.resolve_range(None, base_ref="origin/main", ldr_ref="origin/live-defi-rollout", marker_usable=False)
    assert mode == "fallback"
    assert rng == "origin/main..origin/live-defi-rollout"


def test_empty_marker_falls_back():
    rng, mode = ppr.resolve_range("", base_ref="origin/staging", ldr_ref="origin/live-defi-rollout", marker_usable=True)
    assert mode == "fallback"
    assert rng == "origin/staging..origin/live-defi-rollout"


def test_custom_refs_are_honored():
    rng, mode = ppr.resolve_range("sha9", base_ref="origin/main", ldr_ref="HEAD", marker_usable=True)
    assert mode == "marker"
    assert rng == "sha9..HEAD"


# ── last_promoted_marker: parse gh output / fail-safe to None ────────────────


def _patch_run(monkeypatch, rc: int, out: str):
    monkeypatch.setattr(ppr, "_run", lambda *_a, **_k: (rc, out))


def test_marker_parsed_from_gh_json(monkeypatch):
    _patch_run(
        monkeypatch,
        0,
        '[{"headRefOid":"b859a15","mergedAt":"2026-06-16T22:32:52Z",'
        '"title":"chore(promote): LDR → staging (Tier C auto-drain)"}]',
    )
    assert ppr.last_promoted_marker("IggyIkenna", "unified-trading-library", "staging") == "b859a15"


def test_marker_matches_per_sha_ref_promote_pr_by_title_not_head(monkeypatch):
    # The bug (promote_provenance_marker_stale_head_query_2026_07_13.md): the WS-L Phase-0 fleet
    # bot opens promote PRs with head `promote/<repo>/<sha>`, never literally `live-defi-rollout`.
    # The marker must resolve from the `chore(promote)` TITLE, independent of what the head-ref
    # shape is — this asserts the fix picks the PR up even though `gh pr list` here returns no
    # `headRefName` field at all (title/mergedAt/headRefOid is all the marker needs).
    _patch_run(
        monkeypatch,
        0,
        '[{"headRefOid":"9614964abc","mergedAt":"2026-07-13T10:00:00Z",'
        '"title":"chore(promote): LDR → main (Option-B direct)"}]',
    )
    assert ppr.last_promoted_marker("IggyIkenna", "market-tick-data-service", "main") == "9614964abc"


def test_marker_ignores_non_promote_prs_and_picks_latest_mergedat(monkeypatch):
    promote_title = "chore(promote): LDR → main (Option-B direct)"
    payload = json.dumps(
        [
            {"headRefOid": "stale111", "mergedAt": "2026-07-01T00:00:00Z", "title": promote_title},
            {"headRefOid": "notpromote", "mergedAt": "2026-07-12T00:00:00Z", "title": "fix: unrelated PR"},
            {"headRefOid": "latest222", "mergedAt": "2026-07-10T00:00:00Z", "title": promote_title},
        ]
    )
    _patch_run(monkeypatch, 0, payload)
    assert ppr.last_promoted_marker("IggyIkenna", "market-tick-data-service", "main") == "latest222"


def test_marker_none_on_gh_error(monkeypatch):
    _patch_run(monkeypatch, 1, "")
    assert ppr.last_promoted_marker("IggyIkenna", "r", "staging") is None


def test_marker_none_on_empty_array(monkeypatch):
    # No merged promote PR yet.
    _patch_run(monkeypatch, 0, "[]")
    assert ppr.last_promoted_marker("IggyIkenna", "r", "main") is None


def test_marker_none_on_malformed_json(monkeypatch):
    _patch_run(monkeypatch, 0, "not json{{")
    assert ppr.last_promoted_marker("IggyIkenna", "r", "staging") is None


def test_marker_none_on_missing_field(monkeypatch):
    _patch_run(monkeypatch, 0, '[{"mergedAt":"2026-06-16T22:32:52Z"}]')
    assert ppr.last_promoted_marker("IggyIkenna", "r", "staging") is None


def test_marker_none_on_blank_field(monkeypatch):
    _patch_run(monkeypatch, 0, '[{"headRefOid":"   "}]')
    assert ppr.last_promoted_marker("IggyIkenna", "r", "staging") is None


# ── commit_reachable: thin wrapper over `git cat-file -e` ────────────────────


def test_commit_reachable_true(monkeypatch):
    _patch_run(monkeypatch, 0, "")
    assert ppr.commit_reachable("abc123") is True


def test_commit_reachable_false(monkeypatch):
    _patch_run(monkeypatch, 1, "")
    assert ppr.commit_reachable("deadbeef") is False


# ── marker_is_ancestor: thin wrapper over `git merge-base --is-ancestor` ─────


def test_marker_is_ancestor_true(monkeypatch):
    _patch_run(monkeypatch, 0, "")
    assert ppr.marker_is_ancestor("abc123", "origin/live-defi-rollout") is True


def test_marker_is_ancestor_false(monkeypatch):
    _patch_run(monkeypatch, 1, "")
    assert ppr.marker_is_ancestor("abc123", "origin/live-defi-rollout") is False


# ── marker_usability: the history-rewrite regression ──────────────────────────
# `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`: after the
# 2026-08-05T11:24:53Z security-driven history rewrite, several repos' stored markers still
# resolved as git objects (GitHub kept serving the pre-rewrite SHA) while sitting on a
# disconnected history line — NOT a true ancestor of the post-rewrite `live-defi-rollout`. The
# old `commit_reachable()`-only check wrongly treated these as usable, producing a
# multi-thousand-commit spurious range (3,701 commits for instruments-service) that
# false-flagged as quickmerge-bypass content and deadlocked promotion.


def _patch_run_by_subcommand(monkeypatch, rcs: dict[str, int]):
    """Route `_run` to a different exit code per git subcommand (``cmd[1]``).

    Lets a single test drive `marker_usability`'s composed `cat-file` / `fetch` / `merge-base`
    calls independently, mirroring the real production shape (three distinct git invocations).
    """

    def _fake_run(cmd, cwd=None):
        subcmd = cmd[1] if len(cmd) > 1 else cmd[0]
        return rcs.get(subcmd, 1), ""

    monkeypatch.setattr(ppr, "_run", _fake_run)


def test_marker_usability_reachable_and_ancestor_is_usable(monkeypatch):
    _patch_run_by_subcommand(monkeypatch, {"cat-file": 0, "merge-base": 0})
    assert ppr.marker_usability("0247912d", ldr_ref="origin/live-defi-rollout") == (True, True)


def test_marker_usability_reachable_but_not_ancestor_is_unusable(monkeypatch):
    # THE REGRESSION: the marker SHA exists as a git object (`cat-file` succeeds — this is the
    # instruments-service `0247912d` case, orphaned by the history rewrite) but is NOT an
    # ancestor of `ldr_ref` (`merge-base --is-ancestor` fails). `commit_reachable` alone would
    # wrongly call this usable; `marker_usability` must require BOTH and report it unusable.
    _patch_run_by_subcommand(monkeypatch, {"cat-file": 0, "merge-base": 1})
    reachable, ancestor = ppr.marker_usability("0247912d", ldr_ref="origin/live-defi-rollout")
    assert (reachable, ancestor) == (True, False)
    # Composed into resolve_range, this must select the FALLBACK range — not the marker range
    # that would otherwise balloon to (in the live instruments-service case) 3,701 commits.
    rng, mode = ppr.resolve_range(
        "0247912d",
        base_ref="origin/main",
        ldr_ref="origin/live-defi-rollout",
        marker_usable=reachable and ancestor,
    )
    assert mode == "fallback"
    assert rng == "origin/main..origin/live-defi-rollout"


def test_marker_usability_unreachable_never_checks_ancestry(monkeypatch):
    # An absent object can never be an ancestor of anything — pins the short-circuit: no
    # merge-base call is trusted to flip this back to usable, and the flags stay (False, False)
    # rather than raising.
    _patch_run_by_subcommand(monkeypatch, {"cat-file": 1, "merge-base": 0})
    assert ppr.marker_usability("deadbeef", ldr_ref="origin/live-defi-rollout") == (False, False)


def test_marker_usability_fetches_then_rechecks_both(monkeypatch):
    # Object initially absent locally (first `cat-file` call fails) but `fetch_remote` is given
    # (production always passes one) — after the best-effort fetch, existence AND ancestry are
    # both re-checked against the now-fetched object.
    cat_file_calls = {"n": 0}

    def _fake_run(cmd, cwd=None):
        subcmd = cmd[1] if len(cmd) > 1 else cmd[0]
        if subcmd == "cat-file":
            cat_file_calls["n"] += 1
            return (0, "") if cat_file_calls["n"] > 1 else (1, "")
        if subcmd in ("fetch", "merge-base"):
            return (0, "")
        return (1, "")

    monkeypatch.setattr(ppr, "_run", _fake_run)
    reachable, ancestor = ppr.marker_usability(
        "0247912d", ldr_ref="origin/live-defi-rollout", fetch_remote="https://example.invalid/repo"
    )
    assert (reachable, ancestor) == (True, True)
    assert cat_file_calls["n"] == 2  # initial miss + post-fetch recheck
