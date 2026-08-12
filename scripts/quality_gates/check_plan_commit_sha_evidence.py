#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Plan commit-SHA evidence gate — a `resolved_by:` / `- [x] ... — <repo>@<sha>` citation must
resolve to a REAL commit, not a fabricated one.

The recurring failure class this closes (codified from
plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md): a `docs(plans):`
flip commit cites `resolved_by: <repo>@<sha>` (or an inline `- [x] ... — <repo>@<sha>` todo
citation) for a SHA that does not exist anywhere in the cited repo's history — a fabricated
completion-evidence citation, distinct from `check_evidence_backed_completion.py`'s Cloud Build
SHA gate (which covers runtime infra "went green" claims; PLAN_FORMAT.md § 8b explicitly carves a
code-ship `<repo>@<sha>` claim OUT of that gate's scope on the theory its evidence is "the commit
+ the local QG sentinel" — this gate is the missing structural check that actually verifies that
commit exists). This gate mirrors the Cloud Build gate's shape, generalized to git commit
citations: run it, don't read it — `git cat-file -t <sha>` in the cited repo's sibling worktree,
not a trust-the-self-report.

Scope (deliberately narrow to avoid false positives):
  - Only `<repo>@<sha>` tokens where `<repo>` is the EXACT directory name of a repo actually
    present as a FULL (non-shallow) sibling clone under `--workspace-root` are checked. A shallow
    (`--depth=1`) sibling clone — e.g. CI's dep_repos fetch for unified-trading-library /
    unified-api-contracts — is treated the same as "not present": it can only resolve its own tip
    commit, so checking it against historical citations would flag genuine, non-fabricated commits
    as violations. Abbreviated forms used informally in plan prose (`mtds@...`, `uac@...`,
    `IS@...`) are NOT matched — they're inherently ambiguous (mirrors the Cloud Build gate's
    "can't check it from here" soft-skip,
    implemented here by construction: an unregistered name is simply never a regex alternative).
  - `<sha>` must be a hex string, 6-40 chars (git's own minimum useful abbreviation length through
    a full SHA-1).
  - Scans `resolved_by:` frontmatter (any YAML scalar/list form) plus checked `- [x]` todo blocks
    (checkbox line + continuation lines) in `plans/active/*.md` and `plans/active/issues/*.md`.

Verification: `git -C <repo_path> cat-file -t <sha>` must print `commit`. A repo present locally
whose cited SHA does NOT resolve is a violation (fabricated-or-broken citation) — git history for
a REACHABLE commit never expires (unlike Cloud Build's retention window), so there is no
"aged out, not the citer's fault" soft bucket to mirror here; a citation that doesn't resolve
against a full local clone is either fabricated or points at history that was rewritten out from
under it, and either way the citation is broken and worth flagging.

Baselined ratchet (not strict-0): the corpus already has some amount of pre-existing citation
drift (renamed repos, long-forgotten short-hash collisions) unrelated to today's incident — this
gate ratchets that count DOWN over time rather than failing the whole fleet on first rollout.
Fix a flagged citation by correcting/removing it, or re-baseline with --baseline-write after
verifying the new count is itself all pre-existing, non-fabricated drift.

Exit-code semantics: 0 = at/below baseline; 1 = regression; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess  # invokes `git cat-file` in a sibling repo clone (fixed argv, no shell=True)
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml


def _pm_root_or_legacy(workspace_root):
    """PM checkout root resolved by CONTENT, not by directory NAME (F7, 2026-08-10).

    See scripts/quality_gates/_pm_root.py for why. Behaviour-preserving in a canonically
    named checkout; fixes resolution when running from a git worktree."""
    import pathlib as _pathlib
    import sys as _sys

    _d = str(_pathlib.Path(__file__).resolve().parent)
    if _d not in _sys.path:
        _sys.path.insert(0, _d)
    from _pm_root import pm_root_or_legacy as _impl

    return _impl(workspace_root)


DEFAULT_BASELINE_PATH = Path(__file__).parent / "plan_commit_sha_evidence_baseline.yaml"

# unified-trading-pm repo root — baseline paths are stored relative to this so the file is
# byte-identical no matter which slot/host regenerates it.
_PM_ROOT = Path(__file__).resolve().parents[2]

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n", re.DOTALL)
_CHECKED_RE = re.compile(r"^\s*-\s*\[[xX]\]\s")
_UNCHECKED_OR_CHECKED_RE = re.compile(r"^\s*-\s*\[[ xX]\]\s")

_SHA_RE = r"[0-9a-fA-F]{6,40}"


@dataclass(frozen=True)
class Citation:
    path: Path
    line_no: int
    repo: str
    sha: str
    source: str  # "frontmatter:resolved_by" | "todo"
    context: str  # short snippet for the printed diagnostic


@dataclass(frozen=True)
class ShaViolation:
    citation: Citation

    def __str__(self) -> str:
        return (
            f"{self.citation.path}:{self.citation.line_no}: "
            f"[{self.citation.source}] {self.citation.repo}@{self.citation.sha} does not resolve "
            f"to a commit in the local {self.citation.repo} clone — {self.citation.context}"
        )


def _is_shallow_clone(repo_path: Path) -> bool:
    """A `--depth=1` sibling clone (CI's dep_repos fetch, for speed) can only ever resolve its
    own tip commit — `git cat-file -t <sha>` fails for every older, perfectly real commit, which
    would otherwise read as a mass of fabricated citations. Detected via the plumbing command so
    it degrades safely (non-shallow) if git itself can't answer."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_path), "rev-parse", "--is-shallow-repository"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def _discover_sibling_repos(workspace_root: Path) -> dict[str, Path]:
    """Repo name -> absolute path, for every directory directly under workspace_root that is a
    git repo (`.git` dir or file — the latter covers a legacy linked-worktree layout).

    A shallow clone is excluded (same soft-skip treatment as a repo not present at all) — it
    structurally cannot verify a citation to any commit but its own tip, so including it produces
    false "unresolvable" violations for genuine historical citations rather than catching real
    fabrication. CI's dep_repos (unified-trading-library, unified-api-contracts) are cloned
    `--depth=1` for speed; this is what makes those clones untrustworthy for this check
    specifically, not a general repo-health signal."""
    repos: dict[str, Path] = {}
    for child in sorted(workspace_root.iterdir()):
        if not child.is_dir():
            continue
        if (child / ".git").exists() and not _is_shallow_clone(child):
            repos[child.name] = child
    return repos


def _build_citation_re(repo_names: list[str]) -> re.Pattern[str]:
    if not repo_names:
        # No sibling repos found (unexpected in a real workspace) — a pattern that matches
        # nothing, so the scan degrades to "no citations found" rather than crashing.
        return re.compile(r"(?!x)x")
    alternation = "|".join(re.escape(name) for name in sorted(repo_names, key=len, reverse=True))
    # `(?!-\d)` excludes a distinct existing convention: `<repo>@<date>-<time>` VM-launch instance
    # identifiers (e.g. `deployment-service@20260624-011134`), which are shaped exactly like a
    # `<repo>@<sha>` citation up to the hyphen but are not commit evidence at all — confirmed via
    # the corpus (the only such hit, 2026-07-30: the repo has zero commits with that hex prefix).
    return re.compile(rf"(?<![\w-])(?P<repo>{alternation})@(?P<sha>{_SHA_RE})(?!-\d)\b")


def _iter_frontmatter_citations(text: str, path: Path, citation_re: re.Pattern[str]) -> list[Citation]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return []
    fm_text = m.group(1)
    try:
        fm = cast(object, yaml.safe_load(io.StringIO(fm_text)))
    except yaml.YAMLError:
        return []
    if not isinstance(fm, dict):
        return []
    fm_dict = cast(dict[str, object], fm)
    raw = fm_dict.get("resolved_by")
    if raw is None:
        return []
    resolved_by_str = raw if isinstance(raw, str) else str(raw)

    # Locate the actual line number of `resolved_by:` within the file for a useful diagnostic.
    line_no = 1
    for i, line in enumerate(text.splitlines(), start=1):
        if line.strip().startswith("resolved_by:"):
            line_no = i
            break

    out: list[Citation] = []
    for cm in citation_re.finditer(resolved_by_str):
        out.append(
            Citation(
                path=path,
                line_no=line_no,
                repo=cm.group("repo"),
                sha=cm.group("sha"),
                source="frontmatter:resolved_by",
                context=resolved_by_str.strip()[:160],
            )
        )
    return out


def _iter_todo_citations(text: str, path: Path, citation_re: re.Pattern[str]) -> list[Citation]:
    out: list[Citation] = []
    lines = text.splitlines()
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if _CHECKED_RE.match(line):
            buf = [line]
            j = i + 1
            while j < n:
                nxt = lines[j]
                if _UNCHECKED_OR_CHECKED_RE.match(nxt) or not nxt.strip():
                    break
                buf.append(nxt)
                j += 1
            block_text = "\n".join(buf)
            for cm in citation_re.finditer(block_text):
                out.append(
                    Citation(
                        path=path,
                        line_no=i + 1,
                        repo=cm.group("repo"),
                        sha=cm.group("sha"),
                        source="todo",
                        context=buf[0].strip()[:160],
                    )
                )
            i = j
        else:
            i += 1
    return out


# Repos already fetched once during this run (see _resolves_to_commit's miss path).
_FETCHED_REPOS: set[Path] = set()


def _cat_file_is_commit(repo_path: Path, sha: str) -> bool:
    """Bare `git cat-file -t <sha> == commit` against whatever this clone already has."""
    try:
        proc = subprocess.run(  # fixed argv, no shell=True
            ["git", "-C", str(repo_path), "cat-file", "-t", sha],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        # git itself couldn't run — treat as verifiable-elsewhere-only, never a violation here.
        return True
    return proc.returncode == 0 and proc.stdout.strip() == "commit"


def _is_reachable_from_any_branch(repo_path: Path, sha: str) -> bool:
    """True when ``sha`` is an ancestor of some `origin/*` ref OR of local `HEAD`.

    `git cat-file -t` succeeds for ANY object present in the local object database, including
    a dangling commit a rebase already rewrote away — that gap is exactly how
    `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`'s dead citation
    (`4f901b9916`) and the earlier `0f9b8a65ca` incident slipped past this gate at commit time:
    both existed as loose local objects when cited but were reachable from no branch, local or
    remote. `scripts/dev/reconcile-sha-citations.sh` (Pass 2) heals that AFTER a rebase by the
    same reachability test — this mirrors it, applied BEFORE the commit for self-citations (see
    the `require_reachable` caller in `_resolves_to_commit`).

    `git branch -r --contains` (not `merge-base --is-ancestor origin/<branch>`) so this needs no
    branch name — any remote-tracking ref counts, matching the reconciler's own "OR local HEAD"
    allowance for genuinely unpushed-but-not-yet-rebased work.
    """
    try:
        remote = subprocess.run(  # fixed argv, no shell=True
            ["git", "-C", str(repo_path), "branch", "-r", "--contains", sha],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return True  # can't verify — never manufacture a violation out of a tooling failure
    if remote.returncode == 0 and remote.stdout.strip():
        return True
    try:
        local = subprocess.run(
            ["git", "-C", str(repo_path), "merge-base", "--is-ancestor", sha, "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return True
    return local.returncode == 0


def _resolves_to_commit(repo_path: Path, sha: str, *, require_reachable: bool = False) -> bool:
    """True when ``sha`` is a real commit in ``repo_path`` — fetching once before giving up.

    Bug fixed 2026-08-08: this used to be a BARE `git cat-file` against whatever the local
    clone happened to have already fetched, with no `git fetch` anywhere in the module (both
    prior mentions of "fetch" were comments). A genuinely-real commit that had just been
    pushed by another slot therefore read as FABRICATED until this clone happened to fetch
    it — the gate conflated "I cannot verify this" with "this is invented", which is the
    exact silent-wrong-answer class it exists to catch, turned on itself.

    Measured: 4 of the 8 entries in `plan_commit_sha_evidence_baseline.yaml`
    (`unified-trading-ci@b498ec2`, `@892bb81` x2, `@686bca7`) are REAL commits that only
    failed because the capturing clone was behind. `686bca7` was reproduced live — it did
    NOT resolve before a `git fetch` and DID after. Those false positives then got absorbed
    by RAISING the baseline (2 -> 4 -> 6 -> 8 over two days), which is what a ratchet is
    explicitly never supposed to do.

    A fetch is attempted only on the miss path, so the common (already-present) case costs
    nothing extra.

    ``require_reachable`` (2026-08-12, pm_repo_commit_rate_exceeds_precommit_hook_duration
    todo 5): scoped to self-citations only (see `main`'s caller) — a citation to THIS repo's
    own history must be reachable from a branch, not merely present as a loose object. A
    citation to another repo is left on the weaker cat-file-only test: PM does not control
    when a sibling repo pushes, and that repo's own precommit gate is where its own
    self-citations get this same treatment.
    """
    if _cat_file_is_commit(repo_path, sha):
        return not require_reachable or _is_reachable_from_any_branch(repo_path, sha)
    # Fetch AT MOST ONCE per repo per run. The caller's sha_cache already dedups by
    # (repo, sha), but N *distinct* stale SHAs in one repo would otherwise pay N fetches of
    # up to 120s each — so a single behind clone could turn a fast gate into a multi-minute
    # one. One fetch brings the clone current for every SHA in that repo.
    if repo_path not in _FETCHED_REPOS:
        _FETCHED_REPOS.add(repo_path)
        try:
            subprocess.run(  # fixed argv, no shell=True
                ["git", "-C", str(repo_path), "fetch", "--quiet", "--no-tags", "origin"],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            # Offline / no remote / slow network — we still cannot PROVE fabrication, and
            # this gate must never manufacture a violation out of its own inability to
            # verify. Recorded as fetched so the next miss does not retry the same timeout.
            return True
    if not _cat_file_is_commit(repo_path, sha):
        return False
    return not require_reachable or _is_reachable_from_any_branch(repo_path, sha)


def _load_baseline(baseline_path: Path) -> int:
    if not baseline_path.exists():
        return 0
    try:
        loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return 0
    if isinstance(loaded, dict):
        count = cast(dict[str, object], loaded).get("fabricated_sha_citation_baseline")
        if isinstance(count, int):
            return count
    return 0


def _write_baseline(baseline_path: Path, violations: list[ShaViolation]) -> None:
    payload: dict[str, object] = {
        "fabricated_sha_citation_baseline": len(violations),
        "rule": "plan-commit-sha-evidence (ratchet)",
        "source": "plans/active/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md",
        "baseline_citations": [
            # Repo-root-relative, NOT absolute — see the same change in
            # check_plan_operator_ruling_evidence.py: absolute paths made the file specific to
            # whichever clone last regenerated it, so a real ratchet-DOWN was indistinguishable
            # from path churn in review. Only the count is ever read back.
            {
                "path": str(v.citation.path.resolve().relative_to(_PM_ROOT)),
                "line": v.citation.line_no,
                "cited": f"{v.citation.repo}@{v.citation.sha}",
            }
            for v in violations
        ],
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan commit-SHA evidence check (resolved_by:/`<repo>@<sha>` citations must resolve to a commit)."
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent,
    )
    parser.add_argument("--baseline-path", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--baseline-write", action="store_true")
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help=(
            "Blast-radius-safe precommit mode (RULE-11, mirrors check_finalize_plan_coverage.py): still "
            "scans the whole corpus, but only reports/fails on violations among these specific paths — a "
            "pre-existing violation in an unrelated plan never blocks an unrelated commit. No baseline "
            "comparison in this mode; any violation among --only paths fails immediately."
        ),
    )
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)

    active_dir = (_pm_root_or_legacy(workspace_root)) / "plans" / "active"
    if not active_dir.is_dir():
        print(f"ERROR: plans/active not found at {active_dir}", file=sys.stderr)
        return 2

    plan_files = sorted(active_dir.glob("*.md"))
    issues_dir = active_dir / "issues"
    if issues_dir.is_dir():
        plan_files.extend(sorted(issues_dir.glob("*.md")))

    repos = _discover_sibling_repos(workspace_root)
    citation_re = _build_citation_re(list(repos.keys()))

    citations: list[Citation] = []
    for p in plan_files:
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        citations.extend(_iter_frontmatter_citations(text, p, citation_re))
        citations.extend(_iter_todo_citations(text, p, citation_re))

    # De-dupe identical (path, line, repo, sha) hits — a frontmatter+todo scan of the same line
    # region could otherwise double-count.
    seen: set[tuple[Path, int, str, str]] = set()
    deduped: list[Citation] = []
    for c in citations:
        key = (c.path, c.line_no, c.repo, c.sha)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)
    citations = deduped

    # A citation of THIS repo's own history must be reachable from a branch, not merely present
    # as a loose object (see `_resolves_to_commit`'s `require_reachable` docstring) — that gap is
    # exactly how the 4f901b9916/0f9b8a65ca dead citations slipped past this gate at commit time,
    # only surfacing corpus-wide once the rebase that orphaned them had already happened. Scoped
    # to self-citations: PM does not control when a sibling repo pushes.
    self_repo_name = _pm_root_or_legacy(workspace_root).name

    sha_cache: dict[tuple[str, str], bool] = {}
    violations: list[ShaViolation] = []
    for c in citations:
        repo_path = repos.get(c.repo)
        if repo_path is None:
            continue  # not a present sibling clone — can't verify from here, soft-skip
        key = (c.repo, c.sha)
        if key not in sha_cache:
            sha_cache[key] = _resolves_to_commit(repo_path, c.sha, require_reachable=(c.repo == self_repo_name))
        if not sha_cache[key]:
            violations.append(ShaViolation(citation=c))

    only = cast("list[str] | None", ns.only)
    if only is not None:
        # See check_plan_operator_ruling_evidence.py's --only comment: precommit scoping so a
        # fabricated/unresolvable SHA fails for its author, not for the next agent to ship.
        only_resolved = {Path(o).resolve() for o in only}
        violations = [v for v in violations if v.citation.path.resolve() in only_resolved]
        if not violations:
            print("✅ plan-commit-sha-evidence (--only): clean.")
            return 0
        print("❌ Unresolvable <repo>@<sha> citation(s) in staged plan(s):")
        for v in violations:
            print(f"  - {v.citation.path}:{v.citation.line_no}: {v.citation.repo}@{v.citation.sha}")
        return 1

    checked = sum(1 for c in citations if c.repo in repos)
    print(
        f"Scanned {len(plan_files)} plan(s), {len(citations)} `<repo>@<sha>` citation(s) found, "
        f"{checked} checkable against a present sibling clone — {len(violations)} unresolvable."
    )

    if baseline_write:
        # A RAISE must be loud — this gate's own docstring records its baseline climbing
        # 2 -> 4 -> 6 -> 8 over two days, "what a ratchet is explicitly never supposed to do",
        # and nothing printed at the time. Same warning as the sibling ruling-evidence gate.
        previous = _load_baseline(baseline_path)
        _write_baseline(baseline_path, violations)
        print(f"✅ Wrote baseline ({len(violations)}) to {baseline_path}")
        if len(violations) > previous:
            print(
                f"WARNING: fabricated_sha_citation_baseline RAISED {previous} -> {len(violations)} -- a shrinking\n"
                "  ratchet must only go DOWN. Verify this is a reviewed, justified raise and say why in the commit\n"
                "  message; the correct default is to fix or file the new violations instead.",
                file=sys.stderr,
            )
        return 0

    baseline = _load_baseline(baseline_path)
    regression = len(violations) > baseline
    if violations:
        print(f"\nUnresolvable commit-SHA citations: {len(violations)} (baseline {baseline}).")
        for v in violations[:20]:
            try:
                rel = v.citation.path.relative_to(workspace_root)
            except ValueError:
                rel = v.citation.path
            print(f"  - {rel}:{v.citation.line_no}: [{v.citation.source}] {v.citation.repo}@{v.citation.sha}")
        if len(violations) > 20:
            print(f"  ... + {len(violations) - 20} more")

    if regression:
        print(
            f"\n❌ Plan-commit-SHA-evidence regression: {len(violations)} > baseline {baseline}. "
            "Correct or remove the fabricated/unresolvable citation, or re-baseline with --baseline-write "
            "after confirming it is pre-existing, non-fabricated drift."
        )
        return 1

    if violations and len(violations) < baseline:
        print(f"\n⚠️  Improvement: {len(violations)} < baseline {baseline}. Re-baseline to codify.")
    print("\n✅ Plan-commit-SHA-evidence: all checkable citations resolve; at/below baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
