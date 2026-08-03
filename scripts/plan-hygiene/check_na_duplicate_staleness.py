#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: durable tooling (mechanical NA<->planning duplicate-citation staleness sweep)
# Delete-when: never
"""Find assigned_vm:NA docs whose open checkbox(es) are stale because an active
assigned_vm:planning doc already extracted the same work via a `Source: <this-doc>.md`
citation, AND that planning-side copy is now done.

Context (2026-08-03): /na-eligibility-audit's own rubric has a "KEEP-NA-STALE
(already-duplicated)" verdict for exactly this pattern, but the standard fix is a prose
citation note, not a hard mechanical gate — a future less-careful pass (or a differently
scoped audit) could still miss it. The intended closure path is the AO-side satellite/batch
plan's own paired `*_finalize` plan ("reconcile checkboxes back into the true source doc"),
but that's queue-depth-dependent and per-batch, not a corpus-wide sweep. This script is that
sweep: a repeatable, non-LLM-dependent check for the specific case where the AO-side
duplicate has ALREADY completed but the NA-side original checkbox was never reconciled.

Matching is CHECKBOX-level (2026-08-03 rewrite), not doc-level: a first version flagged
every open checkbox in a doc whenever ANY citation of that doc existed anywhere, with zero
correlation between what the checkbox said and what the citing task actually did. A
122-candidate hand-verification pass the same day found 114 of 122 (93%) were false
positives on exactly this failure mode — e.g. a doc with 20 open checkboxes and 2 done
citations had all 20 flagged, when the citations covered 2 different, already-closed items
in the same doc. This version fixes two things: (1) a checkbox already carrying a prior
audit's own "stays open"/"still open"/"na-eligibility-audit YYYY-MM-DD" disclaimer is
excluded outright (re-flagging an already-adjudicated item wastes the next verification
pass on a settled question); (2) a checkbox is only matched against a citation if their
texts share a genuinely distinctive code span (a specific file path, script, or commit sha
— see `_is_distinctive_span`, not just any backtick-quoted word) — pure doc-level citation
presence is no longer sufficient. This is still a candidate filter, not an auto-closer:
token overlap is a heuristic, not semantic understanding, so a false positive is still
possible (two causally-related but not identical todos can genuinely share a commit sha) —
but it should no longer be the DEFAULT outcome the way pure doc-level matching was.

Usage:
    python3 scripts/plan-hygiene/check_na_duplicate_staleness.py [--pm-root <path>] [--json]

Pure stdlib, read-only. No network, no cloud.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

TODO_LINE_RE = re.compile(r"^\s*-\s*\[([ xX~])\]\s*(.*)$")
BLOCK_BOUNDARY_RE = re.compile(r"^\s*-\s+\[|^\s*#")
FENCE_RE = re.compile(r"^\s*```")

# Matches `Source: X.md`, `**Source**: X.md`, backtick/paren-wrapped, with or without a
# leading `issues/`/`/plans/active/...` path prefix. Captures just the bare filename.
SOURCE_CITE_RE = re.compile(
    r"Source:\**\s*[`(]?\s*(?:/?plans/active/(?:issues/)?|issues/)?"
    r"([A-Za-z0-9_]+\.md)",
)

# A checkbox whose own text already carries a prior audit pass's verdict that it stays
# open is already-adjudicated -- re-flagging it wastes the next verification pass on a
# settled question. Patterns are drawn directly from real disclaimer text found in the
# 2026-08-03 122-candidate hand-verification pass (see module docstring).
DISCLAIMER_RE = re.compile(
    r"na-eligibility-audit\s*20\d\d-\d\d-\d\d"
    r"|ag-closeout-audit\s*20\d\d-\d\d-\d\d"
    r"|plan-reconcile\s*20\d\d-\d\d-\d\d"
    r"|CORRECTED\s*20\d\d-\d\d-\d\d"
    r"|STILL\s+OPEN"
    r"|GENUINELY\s+(?:OPEN|NOT\s+DONE)"
    r"|genuinely\s+(?:open|not\s+done|still\s+open)"
    r"|stays?\s+(?:open|unflipped)"
    r"|checkbox\s+stays"
    r"|remains?\s+(?:open|genuinely)"
    r"|not\s+(?:flipping|done\b|yet\s+(?:done|executed|implemented|shipped))",
    re.IGNORECASE,
)

# Distinctive-token overlap: a checkbox and a citing task are only considered a plausible
# match if their texts share a genuinely rare identifier -- a backtick-quoted code span
# that looks like a specific file/script/commit reference, not just any backticked word.
# Plain-word overlap was tried first and dropped: this corpus's domain vocabulary (bucket,
# manifest, backfill, canonical, shard, venue, repo:, source:, script, design...) repeats
# constantly across totally unrelated todos in dispatch/extract docs specifically BECAUSE
# they share the same tagging boilerplate, so even a 3+-shared-word bar matched on
# "repo:"/"source:"/"script" between semantically unrelated checkboxes (confirmed
# empirically 2026-08-03). Bare-backtick overlap was tried next and ALSO too loose: field/
# column names like `instrument_id`/`chain`/`captured`/`-prd` are backtick-quoted
# constantly across this pipeline's entire vocabulary, not rare at all (confirmed
# empirically the same session) -- so a code span only counts as distinctive when it
# additionally looks like a real identifier: a path (`/`), a repo@sha or bare commit sha,
# a source file (a known code-file extension), or a long SCREAMING_SNAKE_CASE constant.
_CODE_SPAN_RE = re.compile(r"`([^`]{4,})`")
_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
_FILE_EXT_RE = re.compile(r"\.(?:py|sh|md|ya?ml|json|ts|tsx|js|sql|tf)$", re.IGNORECASE)
_SCREAMING_SNAKE_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+){2,}$")
# Named, not auto-detectable: these specific paths/filenames are cited in near-every todo
# across this corpus (the QG entrypoint, the plan-authoring template, common CI configs),
# so path-shape/extension alone doesn't make them distinctive. Denylist over auto-detection
# since there's no cheap structural signal that separates "ubiquitous infra file" from
# "specific script" -- both are real paths with real extensions.
_UBIQUITOUS_REFS = {
    "quality-gates.sh",
    "task_template.md",
    "readme.md",
    "claude.md",
    "index.md",
    "cloudbuild.yaml",
    "buildspec.aws.yaml",
    "plan_format.md",
}
_MIN_PATH_LEN = 12  # filters bare "scripts/"/"docs/" while keeping real multi-segment paths


def _is_distinctive_span(tok: str) -> bool:
    low = tok.lower()
    if low in _UBIQUITOUS_REFS:
        return False
    if "/" in tok or "@" in tok:
        return len(tok) >= _MIN_PATH_LEN
    if _FILE_EXT_RE.search(tok):
        return True
    if _SHA_RE.match(tok) and not tok.isdigit():
        return True
    return bool(_SCREAMING_SNAKE_RE.match(tok))


def _code_spans(text: str) -> set[str]:
    out: set[str] = set()
    for m in _CODE_SPAN_RE.finditer(text):
        tok = m.group(1).strip()
        if tok and _is_distinctive_span(tok):
            out.add(tok.lower())
    return out


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    out: dict[str, str] = {}
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            value = re.sub(r"\s+#.*$", "", m.group(2))
            out[m.group(1)] = value.strip().strip("'\"")
    return out


@dataclass
class TodoBlock:
    line: int
    done: bool
    text: str
    source_cite: str | None


def parse_blocks(text: str) -> list[TodoBlock]:
    lines = text.splitlines()
    blocks: list[TodoBlock] = []
    in_fm = False
    in_code = False
    idx = 0
    total = len(lines)
    line_num = 0
    while idx < total:
        raw = lines[idx]
        line_num += 1
        idx += 1
        if line_num == 1 and raw.strip() == "---":
            in_fm = True
            continue
        if in_fm:
            if raw.strip() == "---":
                in_fm = False
            continue
        if FENCE_RE.match(raw):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = TODO_LINE_RE.match(raw)
        if not m:
            continue
        marker, rest = m.group(1), m.group(2)
        done = marker.lower() == "x"
        cont: list[str] = [rest]
        peek = idx
        while peek < total and not BLOCK_BOUNDARY_RE.match(lines[peek]):
            cont.append(lines[peek])
            peek += 1
        block_text = "\n".join(cont)
        cite_m = SOURCE_CITE_RE.search(block_text)
        blocks.append(
            TodoBlock(
                line=line_num,
                done=done,
                text=block_text,
                source_cite=cite_m.group(1) if cite_m else None,
            )
        )
    return blocks


@dataclass
class DocInfo:
    path: Path
    assigned_vm: str
    status: str
    blocks: list[TodoBlock]


def scan(path: Path) -> DocInfo:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    assigned_vm = (fm.get("assigned_vm") or "missing").lower()
    if assigned_vm in ("", "missing"):
        assigned_vm = "missing"
    if assigned_vm == "human-planning":
        assigned_vm = "planning"
    status = (fm.get("status") or "missing").lower()
    return DocInfo(path=path, assigned_vm=assigned_vm, status=status, blocks=parse_blocks(text))


def collect_all(pm_root: Path) -> list[DocInfo]:
    plans_dir = pm_root / "plans" / "active"
    issues_dir = plans_dir / "issues"
    files = [p for p in plans_dir.glob("*.md") if p.name != "INDEX.md" and not p.name.startswith("_")]
    if issues_dir.is_dir():
        files += list(issues_dir.glob("*.md"))
    return [scan(p) for p in sorted(files)]


def find_stale_candidates(docs: list[DocInfo]) -> list[dict]:
    # citation_index: cited basename -> list of (citing_path, citing_line, done, block_text)
    citation_index: dict[str, list[tuple[Path, int, bool, str]]] = {}
    for d in docs:
        for b in d.blocks:
            if b.source_cite:
                citation_index.setdefault(b.source_cite, []).append((d.path, b.line, b.done, b.text))

    candidates: list[dict] = []
    for d in docs:
        if d.assigned_vm != "na" or d.status not in ("active", "open"):
            continue
        cites = citation_index.get(d.path.name, [])
        done_cites = [c for c in cites if c[2]]
        if not done_cites:
            continue
        for b in d.blocks:
            if b.done:
                continue
            if DISCLAIMER_RE.search(b.text):
                continue  # already adjudicated by a prior audit pass, don't re-flag
            own_code = _code_spans(b.text)
            if not own_code:
                continue  # nothing distinctive to correlate against in this checkbox's own text
            matched = []
            for citing_path, citing_line, _done, citing_text in done_cites:
                shared = own_code & _code_spans(citing_text)
                if shared:
                    matched.append(
                        {
                            "citing_doc": str(citing_path),
                            "citing_line": citing_line,
                            "shared_tokens": sorted(shared)[:8],
                        }
                    )
            if matched:
                candidates.append(
                    {
                        "doc": str(d.path),
                        "checkbox_line": b.line,
                        "checkbox_snippet": b.text[:200],
                        "matched_citations": matched,
                    }
                )
    return candidates


def compute_genuinely_outside_ao(docs: list[DocInfo]) -> dict:
    """Conservative-bound estimate of how much NA-open work is ALREADY visible to AO in
    some form (cited by an active planning doc, done or not) vs genuinely NA-exclusive
    (never touched by AO in any form). Doc-level granularity: per NA doc, the duplicate
    count is min(distinct citing todos seen, that doc's own open-checkbox count) — never
    blanket-assigns a whole doc's open count just because it's cited once."""
    citation_index: dict[str, list[tuple[Path, int, bool]]] = {}
    for d in docs:
        for b in d.blocks:
            if b.source_cite:
                citation_index.setdefault(b.source_cite, []).append((d.path, b.line, b.done))

    total_na_open = 0
    duplicate_tracked = 0
    per_doc: list[dict] = []
    for d in docs:
        if d.assigned_vm != "na" or d.status not in ("active", "open"):
            continue
        own_open = [b for b in d.blocks if not b.done]
        if not own_open:
            continue
        total_na_open += len(own_open)
        cites = citation_index.get(d.path.name, [])
        if cites:
            n = min(len(cites), len(own_open))
            duplicate_tracked += n
            per_doc.append(
                {"doc": str(d.path), "own_open": len(own_open), "citations": len(cites), "counted_duplicate": n}
            )

    return {
        "total_na_open": total_na_open,
        "duplicate_tracked_conservative": duplicate_tracked,
        "genuinely_na_exclusive": total_na_open - duplicate_tracked,
        "per_doc_with_citations": per_doc,
    }


# Any bare `.md` filename mention, not just after `Source:` — catches "see X.md",
# "coordinate with X.md", "tracked in X.md", etc. Meta/normative docs are excluded below
# since they're referenced constantly and never indicate staleness.
ANY_MD_REF_RE = re.compile(r"([A-Za-z0-9_]{6,}_2026_\d{2}_\d{2}(?:_[A-Za-z0-9_]+)?)\.md")
_META_DOC_NAMES = {
    "task_template",
    "plan_format",
    "index",
    "active_index",
    "readme",
    "claude",
    "skill",
}


def build_resolved_doc_index(pm_root: Path) -> dict[str, str]:
    """basename (no .md, lowercase) -> 'archived' or the doc's own status field, for
    every .md under plans/ (active + archive)."""
    index: dict[str, str] = {}
    for p in (pm_root / "plans").rglob("*.md"):
        stem = p.stem.lower()
        if stem in _META_DOC_NAMES:
            continue
        is_archived = "archive" in p.relative_to(pm_root / "plans").parts
        if is_archived:
            index[stem] = "archived"
            continue
        if stem not in index:
            text = p.read_text(encoding="utf-8", errors="replace")
            fm = parse_frontmatter(text)
            index[stem] = (fm.get("status") or "").lower()
    return index


def find_plain_stale_candidates(
    docs: list[DocInfo], resolved_index: dict[str, str], dup_tracked_docs: set[str]
) -> list[dict]:
    """Among NA-open todos with NO duplicate-tracking citation, flag ones whose own text
    references another doc that is now archived/resolved/complete/superseded — a strong
    signal the referenced dependency/context has moved on since this todo was written,
    worth a manual re-check. Not a checkbox-precise match (same doc-level caveat as the
    duplicate-staleness check) — a candidate filter, not an auto-closer."""
    candidates: list[dict] = []
    for d in docs:
        if d.assigned_vm != "na" or d.status not in ("active", "open"):
            continue
        if d.path.name in dup_tracked_docs:
            continue  # already surfaced by the duplicate-staleness check above
        own_stem = d.path.stem.lower()
        hits: list[dict] = []
        for b in d.blocks:
            if b.done:
                continue
            if DISCLAIMER_RE.search(b.text):
                continue  # already adjudicated by a prior audit pass, don't re-flag
            seen_refs_this_block: set[str] = set()
            for m in ANY_MD_REF_RE.finditer(b.text):
                ref_stem = m.group(1).lower()
                if ref_stem == own_stem or ref_stem in seen_refs_this_block:
                    continue  # same doc citing itself, or the same ref repeated in one block
                seen_refs_this_block.add(ref_stem)
                ref_status = resolved_index.get(ref_stem)
                if ref_status in ("archived", "resolved", "complete", "superseded"):
                    hits.append({"line": b.line, "references": f"{ref_stem}.md", "ref_status": ref_status})
        if hits:
            candidates.append({"doc": str(d.path), "hits": hits})
    return candidates


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    default_root = Path(__file__).resolve().parents[2]
    ap.add_argument("--pm-root", type=Path, default=default_root)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not (args.pm_root / "plans" / "active").is_dir():
        print(f"error: no plans/active under {args.pm_root}", file=sys.stderr)
        return 2

    docs = collect_all(args.pm_root)
    candidates = find_stale_candidates(docs)
    overlap = compute_genuinely_outside_ao(docs)
    resolved_index = build_resolved_doc_index(args.pm_root)
    dup_tracked_docs = {Path(pd["doc"]).name for pd in overlap["per_doc_with_citations"]}
    plain_stale = find_plain_stale_candidates(docs, resolved_index, dup_tracked_docs)

    if args.json:
        payload = {"stale_candidates": candidates, "overlap": overlap, "plain_stale_candidates": plain_stale}
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Scanned {len(docs)} docs (plans + issues).\n")

    print("=== STALE-CANDIDATES (checkbox-level; token-overlap matched, disclaimer-filtered) ===")
    print(f"{len(candidates)} found\n")
    for c in candidates:
        print(f"  {c['doc']}:{c['checkbox_line']}")
        print(f"    checkbox: {c['checkbox_snippet']!r}")
        for mc in c["matched_citations"]:
            print(f"    DONE citation: {mc['citing_doc']}:{mc['citing_line']}  shared={mc['shared_tokens']}")
        print()
    if not candidates:
        print("  (none found)\n")

    dup_tracked = overlap["duplicate_tracked_conservative"]
    print("=== GENUINELY-OUTSIDE-AO ESTIMATE (conservative bound, doc-level) ===")
    print(f"  total NA open (status active/open): {overlap['total_na_open']}")
    print(f"  duplicate-tracked (also cited by an active planning doc, done or open): {dup_tracked}")
    print(f"  genuinely NA-exclusive (never touched by AO in any form): {overlap['genuinely_na_exclusive']}")
    print(f"\n  {len(overlap['per_doc_with_citations'])} NA docs carry at least one external citation:")
    for pd in overlap["per_doc_with_citations"]:
        doc, oo, ct, cd = pd["doc"], pd["own_open"], pd["citations"], pd["counted_duplicate"]
        print(f"    {doc}: own_open={oo}, citations={ct}, counted_duplicate={cd}")

    print(
        "\n=== PLAIN-STALE CANDIDATES among genuinely-NA-exclusive todos "
        "(reference another doc now archived/resolved) ==="
    )
    print(f"{len(plain_stale)} found\n")
    for c in plain_stale:
        print(f"  {c['doc']}")
        for h in c["hits"]:
            print(f"    line {h['line']}: references {h['references']} (now {h['ref_status']})")
        print()
    if not plain_stale:
        print("  (none found)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
