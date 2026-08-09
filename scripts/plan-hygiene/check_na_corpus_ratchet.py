#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Shrinking-ratchet gate on the assigned_vm:NA corpus size (doc count + open-todo count).

Operator directive 2026-07-27: the `assigned_vm: NA` backlog must not grow unattended. Most NA
content is genuinely operator-gated/judgment work and correctly stays NA (see
na_docs_validity_and_ao_eligibility_audit_2026_07_26.md's own sampling: ~2/3 of reviewed NA docs
are dated, evidenced KEEP-NA calls) -- so the target is NOT "drive NA to zero". The target is that
new NA content is only ever added alongside an equal-or-greater amount of existing NA content being
reclassified or archived, so the raw backlog size trends flat-or-down, not "load-bearing content
plus an ever-growing pile nobody re-triages."

Reuses generate_na_doc_tranche_inventory.py's own classification (proper PyYAML frontmatter parse,
not a line-grep -- that script's own docstring explains why line-grepping this population is
unsound) rather than re-deriving the NA population a third time.

Usage: check_na_corpus_ratchet.py
  check_na_corpus_ratchet.py --diff-base <ref> [--quiet]
  --update-baseline   regenerate na_corpus_baseline.yaml from the CURRENT corpus state. Run this
                       ONLY after a genuine /na-eligibility-audit or manual triage pass -- never to
                       silence a run that just found the backlog grew (see the baseline file's own
                       header). If the new numbers are HIGHER than the old ones, a loud warning
                       prints (still written -- a deliberate raise is a real, visible signal, not a
                       block), so a genuine spike in new NA-worthy work stays honest in the commit
                       history rather than looking like a routine update.
Exit 0 = current NA docs/todos <= baseline + buffer on both axes. Exit 1 = either axis grew
beyond its buffer.

``--diff-base <ref>`` (2026-08-09, plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_
velocity_2026_08_09.md): diff-scoped mode, same shape + rationale as check_reference_paths.py's
own `--diff-base`. The corpus-wide baseline+buffer mode attributes ANY concurrent agent's newly
authored/edited NA doc, landing anywhere in the corpus between a worker's fix-push and the next CI
re-run, to whoever happens to be re-triggering -- on a high-churn branch this makes the check
un-convergeable serially. Diff-scoped mode compares the qualifying-doc SET (assigned_vm: NA,
status in {active, open}) at HEAD vs the set at <ref> (e.g. origin/main) on two independent axes:
a doc newly entering the population counts as a NEW-DOC violation; an existing member's open-todo
count going UP (vs its own count at <ref>) counts toward a NEW-TODOS total -- todos removed, or a
doc leaving the population, never count against either axis (shrinkage is never a violation, same
as baseline mode). Falls back safely to "no docs at base" (i.e. every current qualifying doc counts
as new) if <ref> cannot be resolved locally -- callers MUST verify the ref is fetched/resolvable
before passing --diff-base (see run_hygiene_sweep.sh's DIFF_BASE_REF guard).

Tolerance buffer (2026-08-09, operator ask): the raw corpus count moves with ordinary
day-to-day plan authoring/completion across many concurrent sessions, not just genuine
NA-eligibility drift -- a flat `current > baseline` comparison meant a normal night's
churn could trip this gate with nothing actually mis-triaged. `na_doc_buffer` /
`na_todo_buffer` in the baseline YAML set how much routine movement is tolerated before
the gate fails; --update-baseline behavior is UNCHANGED (still snaps to current, still
warns loudly on a raise) -- the buffer only widens the day-to-day tolerance band, it does
not relax "never hand-raise the baseline for a genuine, reviewed spike."

See codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 4.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]
INVENTORY_SCRIPT = Path(__file__).resolve().parent / "generate_na_doc_tranche_inventory.py"
BASELINE = Path(__file__).resolve().parent / "na_corpus_baseline.yaml"

# --diff-base mode's own doc-scope + checkbox regex, kept in sync by hand with
# generate_na_doc_tranche_inventory.py's DOC_TREES / CHECKBOX_RE -- duplicated rather than
# imported (this codebase's plan-hygiene checks are each deliberately self-contained; see
# check_reference_paths.py / check_effort_signal_ratchet.py for the same convention) so this
# checker's git-ref path never depends on that script's disk-only _iter_docs().
_NA_DOC_SUBDIRS = ("plans/active", "plans/active/issues")
_CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[ \]", re.MULTILINE)


def _load_docspec():
    """Same loader as generate_na_doc_tranche_inventory.py -- PROPER YAML frontmatter parse,
    never a line-grep (that script's own module docstring documents the exact bug class a
    regex-based frontmatter parse produces: multi-line YAML values silently missed)."""
    spec = importlib.util.spec_from_file_location("docspec", PM / "scripts" / "docs" / "docspec.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/docs/docspec.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["docspec"] = mod
    spec.loader.exec_module(mod)
    return mod


ds = _load_docspec()

_BASELINE_HEADER = """\
# Shrinking-ratchet baseline for the assigned_vm:NA corpus size (check_na_corpus_ratchet.py).
#
# Tracks two numbers over the LIVE `assigned_vm: NA` + status in {active, open} population
# (plans/active/*.md + plans/active/issues/*.md) -- the same population
# generate_na_doc_tranche_inventory.py already computes and /na-eligibility-audit walks. This is
# a SHRINKING ratchet, same convention as doc_reference_baseline.yaml / doc_body_link_baseline.yaml:
# a run that finds the CURRENT corpus bigger than this baseline on EITHER axis fails. The goal is
# not "drive NA to zero" -- most NA content is genuinely operator-gated/judgment work and should
# stay NA -- the goal is that the backlog cannot grow unattended: new NA content is fine when it's
# genuinely NA-worthy, but it must be offset by /na-eligibility-audit (or manual triage)
# reclassifying/archiving existing NA content, not just accumulated net forever.
#
# NEVER hand-raise these numbers to silence a run that just found the backlog grew -- only
# --update-baseline after a genuine /na-eligibility-audit or manual triage pass. A deliberate raise
# (a real spike in legitimate new NA-worthy work) is a real signal -- make it visible with why in
# the commit message, same convention as any other ratchet exception in this corpus.
#
# na_doc_buffer / na_todo_buffer (2026-08-09, operator ask): ordinary plan-authoring churn across
# many concurrent sessions moves this count day to day without any actual NA-eligibility drift --
# the gate fails only on current > baseline + buffer. Tune the buffer here if the observed noise
# band changes; it does not relax "never hand-raise the baseline" for a genuine, reviewed spike.
#
# See codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 4 for the full
# rationale.
"""


def _current_counts() -> tuple[int, int]:
    """(doc_count, total_open_todos) over the live assigned_vm:NA + active/open population."""
    proc = subprocess.run(
        [sys.executable, str(INVENTORY_SCRIPT), "--tranche", "all", "--json"],
        capture_output=True,
        text=True,
        check=True,
        cwd=PM,
    )
    records = json.loads(proc.stdout)
    return len(records), sum(r["open_todos"] for r in records)


def _load_baseline() -> dict[str, object]:
    if not BASELINE.is_file():
        return {}
    return yaml.safe_load(BASELINE.read_text()) or {}


def _na_open_todos_from_text(text: str) -> int | None:
    """None if this doc isn't in the assigned_vm:NA + status active/open population; else
    its open-todo count. Shared by the live-worktree scan and the git-ref scan so neither
    path can silently diverge on what counts as a qualifying doc (mirrors
    generate_na_doc_tranche_inventory.py's own per-doc predicate: assigned_vm/status via a
    proper YAML frontmatter parse, never a line-grep)."""
    fm, _ = ds.parse_frontmatter(text)
    if fm is None:
        return None
    assigned_vm = fm.get("assigned_vm")
    if not (isinstance(assigned_vm, str) and assigned_vm.strip().upper() == "NA"):
        return None
    if fm.get("status") not in ("active", "open"):
        return None
    return len(_CHECKBOX_RE.findall(text))


def _counts_map_live() -> dict[str, int]:
    """relpath -> open_todos for every currently-qualifying doc on disk (live worktree)."""
    out: dict[str, int] = {}
    for sub in _NA_DOC_SUBDIRS:
        for p in sorted((PM / sub).glob("*.md")):
            text = p.read_text(encoding="utf-8", errors="replace")
            n = _na_open_todos_from_text(text)
            if n is not None:
                out[p.relative_to(PM).as_posix()] = n
    return out


def _tree_entries_na_scope(ref: str) -> list[tuple[str, str]]:
    """[(relpath, blob_sha), ...] for immediate *.md children of plans/active/ AND
    plans/active/issues/ at `ref` (non-recursive both, mirrors _NA_DOC_SUBDIRS above). Two
    `git ls-tree` calls, still O(1) in corpus size (not one subprocess per file)."""
    entries: list[tuple[str, str]] = []
    for sub in _NA_DOC_SUBDIRS:
        result = subprocess.run(
            # Trailing slash is load-bearing: `git ls-tree <ref> -- <dir>` (no slash)
            # returns the SINGLE `tree` entry for the directory itself, not its children —
            # confirmed live (0 entries returned, silently wrong) while validating this mode.
            ["git", "-C", str(PM), "ls-tree", ref, "--", f"{sub}/"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) != 3 or parts[1] != "blob":
                continue
            if path.endswith(".md"):
                entries.append((path, parts[2]))
    return entries


def _batch_read_blobs(shas: list[str]) -> dict[str, str]:
    """sha -> decoded text content, via ONE `git cat-file --batch` call for the whole list
    (mirrors check_reference_paths.py's / check_effort_signal_ratchet.py's identical
    helper — avoids one `git show` subprocess per file)."""
    if not shas:
        return {}
    proc = subprocess.run(
        ["git", "-C", str(PM), "cat-file", "--batch"],
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


def _counts_map_at(ref: str) -> dict[str, int]:
    """relpath -> open_todos for every doc qualifying at `ref` (batched git reads)."""
    entries = _tree_entries_na_scope(ref)
    blobs = _batch_read_blobs([sha for _, sha in entries])
    out: dict[str, int] = {}
    for relpath, sha in entries:
        text = blobs.get(sha)
        if text is None:
            continue
        n = _na_open_todos_from_text(text)
        if n is not None:
            out[relpath] = n
    return out


def _run_diff_base(base_ref: str, quiet: bool) -> int:
    """Diff-scoped mode — see the module docstring's --diff-base section for the race this
    closes and the two-axis (new-docs / new-todos) shape."""
    head_map = _counts_map_live()
    base_map = _counts_map_at(base_ref)

    head_docs = set(head_map)
    base_docs = set(base_map)
    new_docs = sorted(head_docs - base_docs)
    growth_docs = sorted(d for d in (head_docs & base_docs) if head_map[d] > base_map[d])

    new_todos_total = sum(head_map[d] for d in new_docs)
    new_todos_total += sum(head_map[d] - base_map[d] for d in growth_docs)

    if not quiet:
        for d in new_docs:
            print(f"  NEW-NA-DOC     {d} ({head_map[d]} open todo(s))")
        for d in growth_docs:
            print(f"  TODO-GROWTH    {d} ({base_map[d]} -> {head_map[d]})")

    problems: list[str] = []
    if new_docs:
        problems.append(f"{len(new_docs)} new NA-population doc(s)")
    if new_todos_total > 0:
        problems.append(f"{new_todos_total} new open todo(s) (new docs + growth on existing NA docs)")

    ok = not problems
    summary = "0 new NA-corpus growth" if ok else "; ".join(problems)
    print(f"{'✅' if ok else '❌'} check_na_corpus_ratchet (--diff-base {base_ref}): {summary} vs {base_ref}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    update_baseline = "--update-baseline" in args
    quiet = "--quiet" in args

    if "--diff-base" in args:
        idx = args.index("--diff-base")
        return _run_diff_base(args[idx + 1], quiet)

    docs, open_todos = _current_counts()
    baseline = _load_baseline()
    max_docs = baseline.get("max_na_docs")
    max_todos = baseline.get("max_na_open_todos")
    # Buffers default to a conservative starting tolerance until tuned from observed noise
    # (see module docstring) — a missing key (older baseline file) still defaults to 0.
    buf_docs = baseline.get("na_doc_buffer", 10)
    buf_todos = baseline.get("na_todo_buffer", 30)

    if update_baseline:
        warnings = []
        if isinstance(max_docs, int) and docs > max_docs + buf_docs:
            warnings.append(f"max_na_docs RAISED {max_docs} -> {docs}")
        if isinstance(max_todos, int) and open_todos > max_todos + buf_todos:
            warnings.append(f"max_na_open_todos RAISED {max_todos} -> {open_todos}")
        BASELINE.write_text(
            _BASELINE_HEADER
            + f"max_na_docs: {docs}\n"
            + f"na_doc_buffer: {buf_docs}\n"
            + f"max_na_open_todos: {open_todos}\n"
            + f"na_todo_buffer: {buf_todos}\n"
            + f'last_updated: "{datetime.now(UTC).date().isoformat()}"\n'
        )
        print(f"na_corpus_baseline.yaml regenerated: max_na_docs={docs}, max_na_open_todos={open_todos}")
        for w in warnings:
            print(
                f"⚠️  {w} (beyond buffer) -- verify this is a reviewed, justified raise, not a silenced failure",
                file=sys.stderr,
            )
        return 0

    problems = []
    if isinstance(max_docs, int) and docs > max_docs + buf_docs:
        problems.append(f"NA doc count grew: {docs} > baseline {max_docs} + buffer {buf_docs}")
    if isinstance(max_todos, int) and open_todos > max_todos + buf_todos:
        problems.append(f"NA open-todo count grew: {open_todos} > baseline {max_todos} + buffer {buf_todos}")

    if problems:
        print("❌ check_na_corpus_ratchet: assigned_vm:NA backlog grew beyond baseline:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        print(
            "  Remedy: run /na-eligibility-audit (or manual triage) to reclassify/archive existing NA\n"
            "  content until the backlog is back at or below baseline, then re-run this check. If this\n"
            "  growth is a reviewed, justified exception (a real spike in new NA-worthy work), re-run with\n"
            "  --update-baseline and explain why in the commit message -- never hand-edit the YAML.",
            file=sys.stderr,
        )
        return 1

    if not quiet:
        print(
            f"✅ check_na_corpus_ratchet: {docs} NA docs / {open_todos} open todos "
            f"(baseline: {max_docs}+{buf_docs} / {max_todos}+{buf_todos})"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
