#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Claim-ownership + marker-count gate for the client-facing presentation artefacts
under codex/14-customer-journeys/commercial-model/*.html.

This is the ACCEPTANCE TEST for the five-agent code-readiness effort
(/plans/active/code_readiness_five_agent_coordinator_2026_08_19.md). The epic sets one
invariant -- **every claim-bearing artefact section maps to a tracked item** -- and
/plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md
§ W21 records that it has already failed once, measurably. Nothing checked it. This does.

Three things are measured, because they fail independently:

  1. OWNERSHIP (shrinking ratchet). A section is *claim-bearing* when it carries a
     non-final status marker (`st-part`, `st-plan`) or a non-final evidence marker
     (`ev-check`, `ev-assumed`) -- i.e. it makes a claim the reader is being asked to
     take on trust. Such a section MUST carry an `owner:` tag binding it to tracked
     work. An untagged claim is an untracked claim: nothing closes it, and no one can
     tell whether it is one of the five allowed pending states or simply unfinished
     work nobody owns.

  2. MARKER COUNTS (shrinking ratchet). The coordinator names falling marker counts as
     "the only honest progress signal -- todo checkboxes are a proxy". The open-marker
     total (st-part + st-plan + ev-check + ev-assumed) is that signal, tracked per
     artefact so a regression names its own file.

  3. OWNER RESOLUTION (HARD, no baseline). Every owner reference must resolve to real
     tracked work. A tag pointing at something that does not exist is worse than no tag
     -- it reads as tracked and is not.

An owner tag's VISIBLE LABEL is written for a human reader and is not always a slug
(`owner: elysium-disclosure §C`, `owner: registry ground-truth P0`). The machine-readable
pointer lives in the tag's `title` attribute, which cites a repo-relative doc path. So
resolution tries, in order: a doc path cited in `title=` that exists on disk; a `W<n>`
that has a `## W<n> —` heading in the epic; a plan/epic doc slug named in the label.
Reading the label alone reports genuinely-tracked sections as dangling -- measured
2026-08-20, that mistake produced three false violations on this very corpus.

Marker vocabulary is READ FROM THE ARTEFACTS' OWN MARKUP (`class="st st-*"` /
`class="ev ev-*"`), not from a hand-copied list, so a new marker class shows up as
unknown rather than being silently ignored. Legend blocks are stripped before scanning:
the legend DEFINES the vocabulary (it contains a literal `owner: W5` as its worked
example), so counting it would both inflate marker counts and hand every artefact a free
ownership tag it has not earned.

Deliberately NO HTML parser, for the same reason check_artefact_disclosure.py gives: a
raw-text scan sees markup a DOM walker normalises away, and these files are hand-authored.

Usage:
  python3 scripts/plan-hygiene/check_artefact_claim_ownership.py [--quiet] [--json]
                                                                [--update-baseline]
Exit 0 if untagged-section count <= baseline AND open-marker count <= baseline AND every
owner reference resolves. NEVER hand-raise a baseline.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PM_DIR = Path(__file__).resolve().parents[2]
ARTEFACT_DIR = PM_DIR / "codex" / "14-customer-journeys" / "commercial-model"
EPIC_PATH = PM_DIR / "plans" / "epics" / "system_readiness_master.md"
BASELINE_PATH = Path(__file__).resolve().parent / "artefact_claim_ownership_baseline.yaml"

# Markers meaning "this claim is not finished / not independently confirmed".
OPEN_STATUS = frozenset({"st-part", "st-plan"})
OPEN_EVIDENCE = frozenset({"ev-check", "ev-assumed"})
# Markers meaning the claim is closed. Listed so an unknown class is detectable.
CLOSED_STATUS = frozenset({"st-live"})
CLOSED_EVIDENCE = frozenset({"ev-verified"})

SECTION_TOKEN_RE = re.compile(r"<section\b[^>]*>|</section>", re.IGNORECASE)
SECTION_ID_RE = re.compile(r'<section\b[^>]*\bid="([^"]+)"', re.IGNORECASE)
STATUS_RE = re.compile(r'class="st (st-[a-z0-9-]+)"')
EVIDENCE_RE = re.compile(r'class="ev (ev-[a-z0-9-]+)"')
# Whole opening tag + visible label, so the `title` attribute travels with the label.
OWNER_TAG_RE = re.compile(r"(<b\b[^>]*>)\s*owner:\s*([^<]{1,160})", re.DOTALL)
OWNER_ANY_RE = re.compile(r"owner:\s*([^<]{1,160})")
TITLE_ATTR_RE = re.compile(r'title="([^"]*)"', re.DOTALL)
DOC_PATH_RE = re.compile(r"/?((?:plans|codex)/[\w./-]+\.(?:md|html))")
OWNER_W_RE = re.compile(r"\bW\d+\b")
OWNER_SLUG_RE = re.compile(r"\b([a-z][a-z0-9_]{3,})\b")
LEGEND_RE = re.compile(r'<div class="legend">.*?</div>', re.DOTALL)
TITLE_RE = re.compile(r"<h2[^>]*>\s*([^<]{1,90})", re.IGNORECASE)
EPIC_WORKSTREAM_RE = re.compile(r"^##\s+(W\d+)\s+—", re.MULTILINE)


@dataclass(frozen=True)
class Baseline:
    untagged_sections: int = 0
    open_markers: int = 0
    note: str = ""


@dataclass
class ArtefactReport:
    name: str
    sections: int = 0
    claim_sections: int = 0
    untagged: list[tuple[str, str]] = field(default_factory=list)
    open_markers: int = 0
    closed_markers: int = 0
    marker_counts: dict[str, int] = field(default_factory=dict)
    unknown_markers: set[str] = field(default_factory=set)
    owner_workstreams: set[str] = field(default_factory=set)
    owner_docs: set[str] = field(default_factory=set)
    owner_unresolved: set[str] = field(default_factory=set)


def load_baseline() -> Baseline:
    if not BASELINE_PATH.exists():
        return Baseline()
    raw = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8")) or {}
    return Baseline(
        untagged_sections=int(raw.get("untagged_sections", 0)),
        open_markers=int(raw.get("open_markers", 0)),
        note=str(raw.get("note") or ""),
    )


def write_baseline(untagged: int, markers: int, existing: Baseline) -> tuple[int, int]:
    """Shrinking ratchet -- a baseline is only ever lowered, never raised."""
    new_untagged = min(untagged, existing.untagged_sections) if existing.untagged_sections else untagged
    new_markers = min(markers, existing.open_markers) if existing.open_markers else markers
    BASELINE_PATH.write_text(
        "# Baseline for check_artefact_claim_ownership.py -- the acceptance test for the\n"
        "# five-agent code-readiness effort. Two SHRINKING ratchets; a live count above\n"
        "# either one fails (a new untracked claim, or a marker regression).\n"
        "#\n"
        "# untagged_sections: claim-bearing sections carrying no `owner:` tag. The epic's\n"
        "#   invariant is that this reaches 0 -- every claim maps to a tracked item.\n"
        "# open_markers: st-part + st-plan + ev-check + ev-assumed across all artefacts.\n"
        "#   The coordinator names this the only honest progress signal for the effort;\n"
        "#   todo checkboxes are a proxy. Lower it as claims are closed by real state\n"
        "#   change -- NEVER by editing an artefact's markup.\n"
        "#\n"
        "# Owner resolution is a HARD check with no baseline: every `owner:` tag must\n"
        "# resolve to a doc path that exists, an epic workstream heading, or a plan slug.\n"
        "#\n"
        f"note: {existing.note or 'Seeded 2026-08-20 alongside the checker.'}\n"
        f"untagged_sections: {new_untagged}\n"
        f"open_markers: {new_markers}\n",
        encoding="utf-8",
    )
    return new_untagged, new_markers


def known_workstreams() -> set[str]:
    if not EPIC_PATH.exists():
        return set()
    return set(EPIC_WORKSTREAM_RE.findall(EPIC_PATH.read_text(encoding="utf-8")))


def known_doc_slugs() -> set[str]:
    """Plan/epic slugs an owner tag may legitimately name, e.g. `instruments_master`."""
    slugs: set[str] = set()
    for sub in ("epics", "active"):
        d = PM_DIR / "plans" / sub
        if d.exists():
            slugs.update(p.stem for p in d.glob("*.md"))
    return slugs


def _top_level_sections(text: str) -> list[tuple[int, int]]:
    """Byte ranges of top-level <section> elements, nesting-aware."""
    spans: list[tuple[int, int]] = []
    depth = 0
    start = -1
    for m in SECTION_TOKEN_RE.finditer(text):
        if m.group(0).startswith("</"):
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    spans.append((start, m.end()))
                    start = -1
        else:
            if depth == 0:
                start = m.start()
            depth += 1
    if depth > 0 and start >= 0:
        spans.append((start, len(text)))
    return spans


def _section_title(body: str, sid: str) -> str:
    m = TITLE_RE.search(body)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else sid


def _resolve_owner(
    open_tag: str,
    label: str,
    workstreams: set[str],
    slugs: set[str],
) -> tuple[set[str], set[str], bool]:
    """(workstream refs, doc refs, resolved?) for one owner tag.

    Resolution order: a doc path cited in `title=` that exists on disk, then a `W<n>`
    the epic defines, then a plan/epic slug named in the visible label.
    """
    ws = {w for w in OWNER_W_RE.findall(label) if w in workstreams}
    docs = {s for s in OWNER_SLUG_RE.findall(label) if s in slugs}

    title_m = TITLE_ATTR_RE.search(open_tag)
    if title_m:
        for rel in DOC_PATH_RE.findall(title_m.group(1)):
            if (PM_DIR / rel).exists():
                docs.add(rel)

    # A `W<n>` in the label that the epic does not define is a dangling reference even
    # if a sibling reference resolved -- report the specific broken pointer.
    bad_ws = {w for w in OWNER_W_RE.findall(label) if w not in workstreams}
    return ws | bad_ws, docs, bool((ws or docs) and not bad_ws)


def scan_file(path: Path, workstreams: set[str], slugs: set[str]) -> ArtefactReport:
    raw = path.read_text(encoding="utf-8")
    # The legend defines the vocabulary (including a literal `owner: W5` example).
    text = LEGEND_RE.sub(" ", raw)
    rep = ArtefactReport(name=path.name)

    for cls in STATUS_RE.findall(text) + EVIDENCE_RE.findall(text):
        rep.marker_counts[cls] = rep.marker_counts.get(cls, 0) + 1
        if cls in OPEN_STATUS or cls in OPEN_EVIDENCE:
            rep.open_markers += 1
        elif cls in CLOSED_STATUS or cls in CLOSED_EVIDENCE:
            rep.closed_markers += 1
        else:
            rep.unknown_markers.add(cls)

    seen_at: set[int] = set()
    for m in OWNER_TAG_RE.finditer(text):
        seen_at.add(m.start(2))
        ws, docs, ok = _resolve_owner(m.group(1), m.group(2), workstreams, slugs)
        rep.owner_workstreams.update(w for w in ws if w in workstreams)
        rep.owner_docs.update(docs)
        if not ok:
            rep.owner_unresolved.add(re.sub(r"\s+", " ", m.group(2)).strip()[:60])

    # Owner tags not wrapped in a <b> element resolve by visible label alone.
    for m in OWNER_ANY_RE.finditer(text):
        if m.start(1) in seen_at:
            continue
        ws, docs, ok = _resolve_owner("", m.group(1), workstreams, slugs)
        rep.owner_workstreams.update(w for w in ws if w in workstreams)
        rep.owner_docs.update(docs)
        if not ok:
            rep.owner_unresolved.add(re.sub(r"\s+", " ", m.group(1)).strip()[:60])

    for start, end in _top_level_sections(text):
        body = text[start:end]
        rep.sections += 1
        markers_here = STATUS_RE.findall(body) + EVIDENCE_RE.findall(body)
        if not any(c in OPEN_STATUS or c in OPEN_EVIDENCE for c in markers_here):
            continue
        rep.claim_sections += 1
        if OWNER_ANY_RE.search(body):
            continue
        sid_m = SECTION_ID_RE.search(text[start : start + 200])
        sid = sid_m.group(1) if sid_m else f"offset-{start}"
        rep.untagged.append((sid, _section_title(body, sid)))

    return rep


def main() -> int:
    quiet = "--quiet" in sys.argv
    as_json = "--json" in sys.argv
    update = "--update-baseline" in sys.argv

    if not ARTEFACT_DIR.exists():
        print(f"❌ check_artefact_claim_ownership: artefact dir missing: {ARTEFACT_DIR}")
        return 1

    workstreams = known_workstreams()
    slugs = known_doc_slugs()
    reports = [scan_file(p, workstreams, slugs) for p in sorted(ARTEFACT_DIR.glob("*.html"))]

    total_untagged = sum(len(r.untagged) for r in reports)
    total_open = sum(r.open_markers for r in reports)
    unresolved: set[str] = set()
    unknown_markers: set[str] = set()
    for r in reports:
        unresolved.update(r.owner_unresolved)
        unknown_markers.update(r.unknown_markers)

    baseline = load_baseline()

    if as_json:
        print(
            json.dumps(
                {
                    "artefacts": [
                        {
                            "name": r.name,
                            "sections": r.sections,
                            "claim_sections": r.claim_sections,
                            "untagged_sections": len(r.untagged),
                            "untagged": [{"id": s, "title": t} for s, t in r.untagged],
                            "open_markers": r.open_markers,
                            "closed_markers": r.closed_markers,
                            "markers": r.marker_counts,
                            "owner_workstreams": sorted(r.owner_workstreams),
                            "owner_docs": sorted(r.owner_docs),
                        }
                        for r in reports
                    ],
                    "totals": {"untagged_sections": total_untagged, "open_markers": total_open},
                    "baseline": {
                        "untagged_sections": baseline.untagged_sections,
                        "open_markers": baseline.open_markers,
                    },
                    "unresolved_owner_refs": sorted(unresolved),
                    "unknown_marker_classes": sorted(unknown_markers),
                },
                indent=2,
            )
        )
    elif not quiet:
        print("Artefact claim-ownership check")
        print(f"  epic workstreams resolved: {len(workstreams)} ({EPIC_PATH.relative_to(PM_DIR).as_posix()})")
        print()
        hdr = f"  {'artefact':<48} {'sect':>5} {'claim':>6} {'untag':>6} {'open':>6} {'closed':>7}"
        print(hdr)
        print("  " + "-" * (len(hdr) - 2))
        for r in reports:
            print(
                f"  {r.name:<48} {r.sections:>5} {r.claim_sections:>6} "
                f"{len(r.untagged):>6} {r.open_markers:>6} {r.closed_markers:>7}"
            )
        print(
            f"  {'TOTAL':<48} {sum(r.sections for r in reports):>5} "
            f"{sum(r.claim_sections for r in reports):>6} {total_untagged:>6} {total_open:>6} "
            f"{sum(r.closed_markers for r in reports):>7}"
        )
        print()
        for r in reports:
            if not r.untagged:
                continue
            print(f"  {r.name} — claim-bearing sections with no owner: tag")
            for sid, title in r.untagged:
                print(f"      #{sid}  {title}")
            print()
        if unresolved:
            print(f"  ❌ owner references that resolve to nothing: {', '.join(sorted(unresolved))}")
            print()
        if unknown_markers:
            unknown_list = ", ".join(sorted(unknown_markers))
            print(f"  ⚠️  unknown marker classes (not in the open/closed vocabulary): {unknown_list}")
            print()

    untagged_ok = total_untagged <= baseline.untagged_sections
    markers_ok = total_open <= baseline.open_markers
    owners_ok = not unresolved

    print(
        f"{'✅' if untagged_ok else '❌'} check_artefact_claim_ownership (ownership): "
        f"{total_untagged} claim-bearing section(s) with no owner tag (baseline {baseline.untagged_sections})"
    )
    print(
        f"{'✅' if markers_ok else '❌'} check_artefact_claim_ownership (markers): "
        f"{total_open} open marker(s) (baseline {baseline.open_markers})"
    )
    print(
        f"{'✅' if owners_ok else '❌'} check_artefact_claim_ownership (owner refs): "
        f"{len(unresolved)} reference(s) resolving to no doc, workstream or plan"
    )

    if update:
        new_untagged, new_markers = write_baseline(total_untagged, total_open, baseline)
        print(f"Baseline updated: untagged_sections={new_untagged} open_markers={new_markers}")

    return 0 if (untagged_ok and markers_ok and owners_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
