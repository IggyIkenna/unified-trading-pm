#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Check cross-doc reference FORMAT + EXISTENCE for the leading-slash, PM-repo-root-
relative convention (operator ruling 2026-07-23): /codex/... and /plans/....

Two independent counts, each its own SHRINKING ratchet (same shape as
scripts/quality_gates/check_defi_address_citations.py / no_fallback_imports_baseline.yaml
— NOT zero-tolerance from day 1, since a large pre-existing corpus can't be fixed in one
sitting, but it must never get WORSE):

1. FORMAT — every codex/... reference anywhere in plans/**.md + codex/**.md must be
   written /codex/...; every `related:` frontmatter entry must carry a full leading-slash
   path (/plans/... or /codex/...), never a bare filename. The 2026-07-23 corpus-wide
   migration (scripts/plan-hygiene/fix_reference_paths.py) brought this to book-keeping
   near-zero; the baseline count is what it could NOT safely auto-resolve (ambiguous or
   genuinely dangling bare filenames) — see reference_paths_baseline.yaml.
2. EXISTENCE — every /codex/... or /plans/... reference must resolve to a real file.
   ~1,270 pre-existing dangling refs predate this convention (docs describing planned-but-
   never-shipped codex content, references to plans since renamed/archived under a
   different name, etc.) — a real corpus-health finding, not something this migration
   caused; tracked as its own cleanup in
   plans/archive/issues/reference_path_convention_2026_07_23.md.

`depends_on` / `parent_epic` / `supersedes` / `superseded_by` / `entry_point_for` are
deliberately OUT OF SCOPE — those are machine-parsed bare-slug fields per
PLAN_FORMAT.md, not file-path references; touching their format changes backend parsing
semantics, not doc hygiene.

Usage:
  python3 scripts/plan-hygiene/check_reference_paths.py [--quiet] [--update-baseline]
  python3 scripts/plan-hygiene/check_reference_paths.py --only <path> [<path> ...]
  python3 scripts/plan-hygiene/check_reference_paths.py --diff-base <ref> [--quiet]
Exit 0 if both counts are <= their baseline. NEVER hand-raise a baseline entry — if a
count needs to go up, something regressed; fix it instead. Ratchet DOWN as the
pre-existing debt gets cleaned up: fix real violations, then re-run --update-baseline.

``--only <paths>`` (2026-08-09, precommit migration): checks ONLY the given staged files
for format/existence violations IN THEIR OWN content, no baseline math — same shape as
check_terminal_status_archived.py/check_plan_operator_ruling_evidence.py --only. This
ratchet previously had NO precommit-time presence (only the full corpus-wide baseline
mode), so a docs(plans) commit introducing a bad-format or dangling reference had zero
enforcement at commit time — root-caused after the existence-violation baseline grew
86->95 in one evening via commits that never ran this check. A staged file whose OWN
content has a badly-formatted or dangling /plans/.../codex/... reference is
unconditionally wrong regardless of the rest of the corpus's pre-existing debt.

``--diff-base <ref>`` (2026-08-09, plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_
velocity_2026_08_09.md): diff-scoped mode, same shape + rationale as
check_archive_candidates.sh's own `--diff-base` (operator ruling 2026-08-06). The
corpus-wide baseline mode attributes ANY concurrent agent's new violation, landing
anywhere in the corpus between a worker's fix-push and the next CI re-run, to whoever
happens to be re-triggering — on a high-churn branch this makes the check un-convergeable
serially (confirmed: 4+ consecutive distinct-check regressions chasing one CI wall).
Diff-scoped mode compares the violation SET at HEAD vs the violation SET at <ref> (e.g.
origin/main) and fails only on violations new to HEAD that <ref> didn't already have —
pre-existing corpus debt at <ref> is tolerated exactly like baseline mode tolerates it,
but the comparison point no longer races the corpus's live tip. Falls back safely to "no
violations at base" (i.e. every current violation counts as new) if <ref> cannot be
resolved locally — callers MUST verify the ref is fetched/resolvable before passing
--diff-base (see run_hygiene_sweep.sh's DIFF_BASE_REF guard).
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

PM_DIR = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).resolve().parent / "reference_paths_baseline.yaml"

# Anything codex-shaped WITHOUT the correct leading-slash-only prefix: bare `codex/...`
# or a relative `../codex/...` — i.e. NOT preceded by exactly one leading '/' with
# nothing else before it in the path token.
BARE_CODEX_RE = re.compile(r"(?<![\w/.-])(?:\.\./)*codex/[0-9]{2}-[a-z-]+/[A-Za-z0-9_./-]+\.md")

GOOD_REF_RE = re.compile(r"/(?:plans|codex)/[A-Za-z0-9_./-]+\.md")
BARE_MD_RE = re.compile(r"(?<![\w/.-])([A-Za-z0-9_-]+\.md)")

# D47 ruling (2026-08-21, autonomous-dispatch authority): a shell/CLI example inside a
# fenced code block that contains a literal repo-relative `codex/NN-name/...md` path is a
# COMMAND, not a cross-doc reference -- a leading slash would make the command wrong
# (commands run relative to the repo root). A BARE_CODEX_RE match whose position falls
# inside a fenced block is exempt from the FORMAT check -- removes a recurring
# false-positive class without weakening enforcement for actual prose references. See
# check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md's "Sharp edge"
# section + cross-reference-path-convention.md's "Fenced-code-block exemption" section.
_FENCE_LINE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def _fenced_code_spans(text: str) -> list[tuple[int, int]]:
    """Character spans [(start, end), ...] of fenced-code-block CONTENT in `text`
    (between an opening fence line and its matching closing fence line, exclusive of the
    fence lines themselves). Standard Markdown ``` / ~~~ fencing; a closer must use the
    same fence character and be at least as long as the opener (CommonMark's matching
    rule), so a shorter or different-character run inside the block does not close it
    early. An unterminated fence runs to end-of-text."""
    spans: list[tuple[int, int]] = []
    open_char = ""
    open_len = 0
    content_start = -1
    offset = 0
    for line in text.splitlines(keepends=True):
        m = _FENCE_LINE_RE.match(line)
        if content_start == -1:
            if m:
                fence = m.group(1)
                open_char, open_len = fence[0], len(fence)
                content_start = offset + len(line)
        elif m and m.group(1)[0] == open_char and len(m.group(1)) >= open_len:
            spans.append((content_start, offset))
            content_start = -1
        offset += len(line)
    if content_start != -1:
        spans.append((content_start, len(text)))
    return spans


@dataclass(frozen=True)
class Baseline:
    format_count: int = 0
    existence_count: int = 0
    note: str = ""


def load_baseline() -> Baseline:
    if not BASELINE_PATH.exists():
        return Baseline()
    raw = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8")) or {}
    return Baseline(
        format_count=int(raw.get("format_count", 0)),
        existence_count=int(raw.get("existence_count", 0)),
        note=str(raw.get("note") or ""),
    )


def write_baseline(format_count: int, existence_count: int, existing: Baseline) -> None:
    """Persist a new baseline. Counts are clamped DOWN — never raised above the
    existing baseline (a higher count means a NEW violation landed; fix it, don't
    bake it in)."""
    new_format = min(format_count, existing.format_count) if existing.format_count else format_count
    new_existence = min(existence_count, existing.existence_count) if existing.existence_count else existence_count
    BASELINE_PATH.write_text(
        "# Baseline for check_reference_paths.py — the /plans/... + /codex/... reference\n"
        "# path convention (operator ruling 2026-07-23).\n"
        "#\n"
        "# This is a SHRINKING ratchet. format_count/existence_count are the number of\n"
        "# pre-existing violations the gate tolerates. A live count EXCEEDING its baseline\n"
        "# fails the check — a NEW violation landed; fix the reference, don't grow the\n"
        "# number. LOWER a count (re-run --update-baseline) the moment violations are fixed.\n"
        "# NEVER hand-raise a count.\n"
        "#\n"
        "# SSOT: /codex/11-project-management/cross-reference-path-convention.md,\n"
        "# /plans/archive/issues/reference_path_convention_2026_07_23.md.\n"
        f"note: Seeded 2026-07-23 — corpus-wide migration via fix_reference_paths.py.\n"
        f"format_count: {new_format}\n"
        f"existence_count: {new_existence}\n",
        encoding="utf-8",
    )


def target_files() -> list[Path]:
    """Docs this ratchet actually audits.

    `plans/archive/` is EXCLUDED (ruled 2026-08-02,
    plan_reconcile_parked_operator_decisions_2026_08_02.md § 4) -- it sat inside this ratchet's population but
    outside every active-corpus audit's scope (plan-reconcile, ag-closeout-audit, na-eligibility-audit all only
    touch plans/active/), so a real +47 regression there could never be cleared by any run that could actually fix
    it. Archived docs' reference paths are frozen historical record, not something a live audit should chase.
    """
    files: list[Path] = []
    for top in ("plans", "codex"):
        base = PM_DIR / top
        if base.exists():
            files.extend(p for p in base.rglob("*.md") if "plans/archive/" not in p.as_posix())
    return files


def extract_related_text(text: str) -> str:
    fm_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not fm_match:
        return ""
    fm_text = fm_match.group(1)
    rel_match = re.search(r"^related:\s*(\[.*?\]|(?:\n(?:[ \t]+.*\n?)*))", fm_text, re.MULTILINE)
    return rel_match.group(1) if rel_match else ""


def _scan_text(text: str, relpath: str, exists_fn) -> tuple[list[str], list[str]]:
    """Format + existence violations for one file's own content. Shared by the
    corpus-wide scan, --only, and --diff-base so no mode can silently diverge on what
    counts as a violation. `exists_fn(rel_target) -> bool` lets each caller supply a
    cheap existence lookup (disk .is_file() for the worktree, a precomputed set for a
    git ref) instead of this function knowing how to resolve a ref itself."""
    fmt: list[str] = []
    exist: list[str] = []

    fenced_spans = _fenced_code_spans(text)
    for m in BARE_CODEX_RE.finditer(text):
        if any(start <= m.start() < end for start, end in fenced_spans):
            continue
        fmt.append(f"{relpath}: bare/relative codex ref '{m.group(0)}' — should be /codex/...")

    related_text = extract_related_text(text)
    for m in BARE_MD_RE.finditer(related_text):
        preceding = related_text[: m.start()]
        if not preceding.endswith("/"):
            fmt.append(f"{relpath}: related: entry '{m.group(1)}' has no path — should be /plans/... or /codex/...")

    for m in GOOD_REF_RE.finditer(text):
        target = m.group(0)
        if not exists_fn(target.lstrip("/")):
            exist.append(f"{relpath}: '{target}' does not resolve to a real file")

    return fmt, exist


def _disk_exists(rel_target: str) -> bool:
    return (PM_DIR / rel_target).is_file()


def _scan_file(p: Path, relpath: str) -> tuple[list[str], list[str]]:
    return _scan_text(p.read_text(encoding="utf-8"), relpath, _disk_exists)


def _tree_entries_md(ref: str) -> list[tuple[str, str]]:
    """[(relpath, blob_sha), ...] for .md files under plans/+codex/ at `ref`
    (plans/archive/ excluded, mirrors target_files()). One subprocess call regardless
    of corpus size."""
    result = subprocess.run(
        ["git", "-C", str(PM_DIR), "ls-tree", "-r", ref, "--", "plans", "codex"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    entries: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) != 3 or parts[1] != "blob":
            continue
        if path.endswith(".md") and not path.startswith("plans/archive/"):
            entries.append((path, parts[2]))
    return entries


def _existing_paths_at(ref: str) -> set[str]:
    """Every plans/+codex/ path that exists at `ref` — one subprocess call, used as an
    O(1) existence lookup for every reference found across the whole corpus instead of a
    `git cat-file -e` subprocess PER reference (was the original implementation; ~1,500
    docs x several refs each made the diff-scoped mode take 60s+ per run)."""
    result = subprocess.run(
        ["git", "-C", str(PM_DIR), "ls-tree", "-r", "--name-only", ref, "--", "plans", "codex"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return set(result.stdout.splitlines())


def _batch_read_blobs(shas: list[str]) -> dict[str, str]:
    """sha -> decoded text content, via ONE `git cat-file --batch` call for the whole
    list (vs. one `git show` subprocess per file)."""
    if not shas:
        return {}
    proc = subprocess.run(
        ["git", "-C", str(PM_DIR), "cat-file", "--batch"],
        input=("\n".join(shas) + "\n").encode("utf-8"),
        capture_output=True,
        check=False,
    )
    out = proc.stdout
    result: dict[str, str] = {}
    pos = 0
    while pos < len(out):
        nl = out.index(b"\n", pos)
        header = out[pos:nl].decode("utf-8", "replace").split()
        if len(header) != 3:
            break
        sha, _obj_type, size_s = header
        size = int(size_s)
        start = nl + 1
        result[sha] = out[start : start + size].decode("utf-8", "replace")
        pos = start + size + 1  # +1 skips the trailing newline after object data
    return result


def _violations_at(ref: str | None) -> tuple[set[str], set[str]]:
    """The full violation set (format, existence) at `ref` (None = live worktree)."""
    fmt: set[str] = set()
    exist: set[str] = set()
    if ref is None:
        for p in target_files():
            f, e = _scan_file(p, p.relative_to(PM_DIR).as_posix())
            fmt.update(f)
            exist.update(e)
        return fmt, exist

    entries = _tree_entries_md(ref)
    blobs = _batch_read_blobs([sha for _, sha in entries])
    existing = _existing_paths_at(ref)
    exists_fn = existing.__contains__
    for relpath, sha in entries:
        text = blobs.get(sha)
        if text is None:
            continue
        f, e = _scan_text(text, relpath, exists_fn)
        fmt.update(f)
        exist.update(e)
    return fmt, exist


def _run_diff_base(base_ref: str, quiet: bool) -> int:
    """Diff-scoped mode: fail only on violations new at HEAD vs `base_ref` — see the
    module docstring's --diff-base section for the race this closes."""
    head_fmt, head_exist = _violations_at(None)
    base_fmt, base_exist = _violations_at(base_ref)
    new_fmt = sorted(head_fmt - base_fmt)
    new_exist = sorted(head_exist - base_exist)
    n = len(new_fmt) + len(new_exist)

    # Evidence prints on FAILURE regardless of --quiet (see _run_only's docstring).
    if not quiet or n > 0:
        for v in new_fmt:
            print(f"  FORMAT    {v}")
        for v in new_exist:
            print(f"  DANGLING  {v}")

    print(
        f"{'✅' if n == 0 else '❌'} check_reference_paths (--diff-base {base_ref}): {n} NEW violation(s) vs {base_ref}"
    )
    return 0 if n == 0 else 1


def _run_only(paths: list[str], quiet: bool) -> int:
    """Precommit-scoped mode: check exactly the given files, no baseline math. A
    format/existence violation in a file you're actively staging is unconditionally
    wrong regardless of the rest of the corpus's pre-existing backlog.

    A path that does not resolve to a file is a caller ERROR (mistaken cwd, a
    since-deleted file still on the command line, ...), never treated the same as
    "zero violations" — that conflation previously cost seven failed safe-doc-push
    attempts on a single one-line violation (issue:
    check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12): a
    path that silently resolved to nothing reported "0 violation(s)" / exit 0, a
    clean bill of health for a file that was never actually checked.

    `plans/archive/` is skipped here too (same exclusion `target_files()` and the
    diff-base git-ls-tree filter both already apply, see `target_files()`'s
    docstring) — archived docs are frozen historical record outside every active
    audit's scope, so a staged edit to one (e.g. a frontmatter-only summary
    backfill) must not be blocked by that doc's own pre-existing, unrelated
    dangling references. Skipped paths are reported, not silently dropped, so this
    stays distinct from the unresolved-path failure mode above.
    """
    format_violations: list[str] = []
    existence_violations: list[str] = []
    unresolved: list[str] = []
    skipped_archived: list[str] = []
    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            p = Path.cwd() / p
        if "plans/archive/" in p.as_posix():
            skipped_archived.append(str(p))
            continue
        if not p.is_file():
            unresolved.append(str(p))
            continue
        try:
            relpath = p.relative_to(PM_DIR).as_posix()
        except ValueError:
            relpath = raw
        fmt, exist = _scan_file(p, relpath)
        format_violations.extend(fmt)
        existence_violations.extend(exist)

    n = len(format_violations) + len(existence_violations)
    # Evidence prints on FAILURE regardless of --quiet -- quiet suppresses noise
    # on success, never the reason for a failure (defect 2 of the issue above).
    if not quiet or n > 0 or unresolved:
        for v in format_violations:
            print(f"  FORMAT    {v}")
        for v in existence_violations:
            print(f"  DANGLING  {v}")
        for u in unresolved:
            print(f"  UNRESOLVED  --only path did not resolve to a file: {u}")
        for s in skipped_archived:
            print(f"  SKIPPED (plans/archive/, frozen historical record): {s}")

    print(f"{'✅' if n == 0 else '❌'} check_reference_paths (--only): {n} violation(s) in staged files")
    if unresolved:
        print(f"❌ check_reference_paths (--only): {len(unresolved)} unresolved path(s) — see above")
        return 1
    return 0 if n == 0 else 1


def main() -> int:
    quiet = "--quiet" in sys.argv
    update = "--update-baseline" in sys.argv

    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        return _run_only(sys.argv[idx + 1 :], quiet)

    if "--diff-base" in sys.argv:
        idx = sys.argv.index("--diff-base")
        return _run_diff_base(sys.argv[idx + 1], quiet)

    format_violations: list[str] = []
    existence_violations: list[str] = []
    files = target_files()

    for p in files:
        relpath = p.relative_to(PM_DIR).as_posix()
        fmt, exist = _scan_file(p, relpath)
        format_violations.extend(fmt)
        existence_violations.extend(exist)

    baseline = load_baseline()

    fmt_n, exist_n = len(format_violations), len(existence_violations)
    fmt_ok = fmt_n <= baseline.format_count
    exist_ok = exist_n <= baseline.existence_count

    # Evidence prints on FAILURE regardless of --quiet (defect 2 of
    # check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12):
    # quiet suppresses noise on success, never the reason for a failure.
    if not quiet or not (fmt_ok and exist_ok):
        print(f"Reference path check ({len(files)} files scanned):")
        print()
        for v in format_violations:
            print(f"  FORMAT    {v}")
        for v in existence_violations:
            print(f"  DANGLING  {v}")
        print()

    print(
        f"{'✅' if fmt_ok else '❌'} check_reference_paths (format): {fmt_n} violation(s) "
        f"(baseline {baseline.format_count})"
    )
    print(
        f"{'✅' if exist_ok else '❌'} check_reference_paths (existence): {exist_n} dangling ref(s) "
        f"(baseline {baseline.existence_count}) — see plans/archive/issues/reference_path_convention_2026_07_23.md"
    )

    if update:
        write_baseline(fmt_n, exist_n, baseline)
        print(
            f"Baseline updated: format_count={min(fmt_n, baseline.format_count or fmt_n)}, "
            f"existence_count={min(exist_n, baseline.existence_count or exist_n)}"
        )

    return 0 if (fmt_ok and exist_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
