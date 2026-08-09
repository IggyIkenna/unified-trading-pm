#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""AO dispatch-visibility gate — a todo AO will never dispatch must SAY it is on hold.

SSOT: plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md

The failure class this closes: `_parse_open_todos`
(`agent-orchestrator/server/regen_backlog_from_plan.py`) deliberately drops any todo whose
continuation block asserts a live `BLOCKED-<TOKEN>` state or a permanent stretch/deferred
marker. That behaviour is correct on its own terms — a worker cannot work a todo that waits on
a human. The defect is that **nothing reports the drop**: the plan still renders `- [ ]`,
`regenerate_active_plan_inventory.py` still counts it, the plan's own progress fraction still
counts it, and the operator still reads it as tracked work. AO will never dispatch it and no
gate, sweep, or dashboard says so. Silent false progress at corpus scale, invisible in exactly
the direction that matters: the plan looks alive while its work is unreachable.

**This gate does not widen the exclusion regex.** Four successive widenings of
`_STALE_MARKER_PREFIX_RE`/`_STALE_MARKER_SUFFIX_RE` (2026-07-28, 07-29, 08-02, 08-08) each
closed one trigger shape and were each followed by another, because the marker's mere presence
carries no information about WHOSE state it describes — "file BLOCKED-CREDENTIALS ask docs",
"(or `BLOCKED-CREDENTIALS` if the source is unreachable)", and "Do NOT mark this
BLOCKED-CREDENTIALS" are all fully-actionable todos that merely talk ABOUT blocked-ness. No
regex over prose can separate those from a real hold. So this gate inverts the burden: it does
not try to guess intent, it requires the plan to DECLARE it.

## The three findings (deliberately separate — they need different responses)

1. **Undeclared exclusion** — a todo the real parser dropped whose block carries no explicit
   declaration. Either it is a genuine hold that must be declared, or (far more often, measured)
   it is a fully-actionable todo silently lost to a prose mention. Baselined ratchet.
2. **Zero-dispatchable doc** — an `active`, `assigned_vm: planning` doc with at least one
   parser-eligible open todo but ZERO that reach the backlog. Louder, because the doc is either
   mis-tagged or finished; it is never correct as-is. Baselined separately.
3. **Ineffective declaration** — the INVERSE failure, and the reason finding 1 alone is not
   enough: a todo whose leading head declares `BLOCKED-<SOMETHING>` in a token the dispatcher's
   vocabulary does not contain, so it dispatches anyway. The author believes it is held; AO hands
   it to a worker. This is exactly
   blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md — `BLOCKED-PREREQUISITES`
   is not in `_BLOCKED_TOKEN_RE`'s alternation, so every todo marked with it kept dispatching.
   Detected by comparing a generic `BLOCKED-<UPPERCASE>` shape against the real vocabulary the
   probe reports, so a token added upstream stops being flagged here the moment it lands.

Findings 1 and 3 are the two directions of one defect: the plan's rendered state and the
dispatcher's actual behaviour disagree, and nothing reports the disagreement.

## Declaring a hold (the convention this gate enforces)

`task_template.md` documents non-dispatchability as "a line containing `BLOCKED-<TOKEN>`" —
which is precisely the ambiguous rule that produced all four incidents. A declaration must be
**structural and positional**, somewhere prose cannot wander into. Either:

  - the marker sits in the checkbox line's leading declaration head — inside a leading bracket
    tag (`- [ ] [DATA][BLOCKED-CREDENTIALS] P1. ...`), bare before the tags
    (`- [ ] BLOCKED-UPSTREAM-DESIGN [DATA] P2. ...`), or at the very start of the description
    body after the `[TAG] P<n>.` prefix (`- [ ] [SCRIPT] P1. DEFERRED-BY-DESIGN. ...`).

A marker anywhere else — mid-sentence, or on a continuation line — is NOT a declaration. That
asymmetry is the whole point: a real hold is cheap to declare, and an accidental prose mention
cannot fake one.

**Why continuation lines deliberately do NOT count**, even though annotating a marker below the
todo is a real corpus habit (blocked_marker_continuation_line_not_scanned_2026_07_26.md): plan
prose is prettier-wrapped at 120 chars, so a marker lands at the start of a continuation line
whenever the wrap happens to fall there. A first draft of this gate accepted line-initial
continuation markers and was measured against the live corpus: 7 of the 9 exclusions it thereby
absolved were soft-wraps mid-sentence ("BLOCKED-OPERATOR-DECISION item)? (b) has ..."), and two
of those were RESOLUTION notes stating the marker no longer applied ("`BLOCKED-CREDENTIALS` is
now STALE, clearing it"). Accepting that form would have silently re-created the very
false-absolution this gate exists to catch. A position a line-wrapping tool can produce by
accident is not a declaration, so the honest rule is the one prose cannot reach: the head of the
checkbox line. Complying is a ten-character edit — move the marker into the tag position.

## The parser is the oracle

This gate NEVER re-implements the exclusion regex — a second copy is a second thing to drift,
and drift here means the gate disagrees with the dispatcher about what is dispatchable, which is
worse than no gate. It imports `_parse_open_todos` and `_is_non_dispatchable` from the real
`agent-orchestrator` module in a subprocess (that clone's own interpreter, so PM's venv never has
to carry AO's dependency closure — and no banned `try/except ImportError` fallback exists
anywhere in this file). The exclusion count is derived by calling the REAL parser twice over the
same file: once normally, once with `_is_non_dispatchable` monkeypatched to a constant False.
The difference is exactly the set of todos dropped by the non-dispatchability rule — no
re-walked markdown, no second regex.

That double-call also removes a false-positive class the naive measurement in the issue doc
suffered from: a raw `^- [ ]` line count includes todos inside fenced code blocks, strikethrough
lines and frontmatter, which the parser skips for reasons that have nothing to do with being
blocked. Measured 2026-08-08: the raw disk delta was 47, but only 43 were real exclusions — and
the issue doc's single worst-listed offender (`gate_on_depends_wiring_gap_defi_dex_pool_finalize`,
"1 of 6 dispatchable") turned out to have five of its six `- [ ]` lines inside a fenced example
block, i.e. not a finding at all.

The marker vocabulary itself (`_BLOCKED_TOKEN_RE`, `_PERMANENT_NON_DISPATCHABLE_RE`) is read out
of the AO module at runtime and compiled here, so "what counts as a marker" also has exactly one
definition, upstream.

## Missing sibling clone

If `agent-orchestrator` is not cloned next to this repo, the gate prints a loud skip notice and
returns 0. It never falls back to a hand-rolled regex (that would silently re-introduce the
drift this gate exists to prevent) and never fails the fleet over a workspace-layout fact that
is not the committer's doing. Mirrors `check_plan_commit_sha_evidence.py`'s soft-skip.

Exit-code semantics: 0 = at/below baseline (or skipped); 1 = regression; 2 = arg/IO error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess  # runs the AO clone's own interpreter (fixed argv, no shell=True)
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

DEFAULT_BASELINE_PATH = Path(__file__).parent / "ao_dispatch_visibility_baseline.yaml"

AO_REPO_NAME = "agent-orchestrator"

# How far into the description body (after the leading `[TAG] P<n>.` prefix) a marker may start
# and still read as a declaration rather than prose. Sized to admit the longest real leading
# marker (`DEFERRED-BY-DESIGN`, 18 chars, sometimes preceded by `**`) plus a little slack, and to
# exclude every measured accidental case — the nearest accidental hit in the 2026-08-08 corpus
# sat 55 chars into its body ("Execute the FINAL decided fix (retire OR
# scaffold-with-BLOCKED-CREDENTIALS...").
MARKER_HEAD_CHARS = 24

# Leading structural prefix of a todo's checkbox line, per plans/PLAN_FORMAT.md's
# `- [ ] [TAG] P0. <description>` shape: an optional list ordinal, zero or more bracket role
# tags, an optional priority, and any bold/emphasis punctuation opening the description. Group
# `tags` captures the bracket-tag run so a `[BLOCKED-<TOKEN>]` tag among them counts as a
# declaration wherever it sits in that run.
_LEADING_PREFIX_RE = re.compile(r"^\s*(?:\d+\.\s*)?(?P<tags>(?:\[[A-Za-z][A-Za-z0-9_-]*\]\s*)*)(?:P\d\b\.?\s*)?[*_\s]*")

# Any `BLOCKED-<UPPERCASE>` shape, whether or not the dispatcher recognises the token. Compared
# against the REAL vocabulary (reported by the probe) to find declarations that look authoritative
# to a human but are invisible to `_is_non_dispatchable` — finding 3.
#
# `BLOCKED-ON:<ref>` is carved out: it is a DIFFERENT, legitimate marker family — `verify.py`'s
# `_ADDED_BLOCKED_LINE_RE` (`^\+\s*-\s+\[ \]\s+.*\bBLOCKED-ON:\S+`) recognises it for `/done`-time
# evidence-only closure, and it is not an ingestion gate at all. A todo carrying it is SUPPOSED to
# stay dispatchable, so reporting it as an ineffective hold would conflate the two conventions —
# exactly what `ao_satellite_ao_dispatch_batch6_2026_08_04.md`'s open documentation todo warns
# against ("do not conflate the two"). The colon is load-bearing in that family's own regex, so it
# is required here too rather than carving out a bare `BLOCKED-ON`.
_GENERIC_BLOCKED_RE = re.compile(r"BLOCKED-(?!ON:)[A-Z][A-Z0-9-]*")

# Emitted in the AO clone's own interpreter. Returns, per `assigned_vm: planning` doc, the
# parser's real verdict plus the full block text of every todo the non-dispatchability rule
# dropped. `_is_non_dispatchable` is monkeypatched with a recording spy so the excluded blocks
# are captured EXACTLY as the real parser assembled and judged them.
_PROBE_SRC = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
from pathlib import Path
import server.regen_backlog_from_plan as R

pm_root = Path(sys.argv[2])
real = R._is_non_dispatchable
out = []

for sub in ("plans/active", "plans/active/issues"):
    d = pm_root / sub
    if not d.is_dir():
        continue
    for p in sorted(d.glob("*.md")):
        text = p.read_text(encoding="utf-8", errors="replace")
        parts = text.split("---")
        frontmatter = parts[1] if len(parts) > 2 else ""
        if "assigned_vm: planning" not in frontmatter:
            continue

        seen = []

        def spy(block, _seen=seen, _real=real):
            verdict = _real(block)
            _seen.append((block, verdict))
            return verdict

        R._is_non_dispatchable = spy
        parsed = R._parse_open_todos(p)
        R._is_non_dispatchable = real

        excluded = [block for block, verdict in seen if verdict]
        out.append({
            "doc": str(p.relative_to(pm_root)),
            "parsed": len(parsed),
            "eligible": len(seen),
            "excluded": excluded,
            "parsed_todos": [description for description, _p_tag in parsed],
        })

print(json.dumps({
    "docs": out,
    "blocked_token_pattern": R._BLOCKED_TOKEN_RE.pattern,
    "permanent_pattern": R._PERMANENT_NON_DISPATCHABLE_RE.pattern,
}))
"""


@dataclass(frozen=True)
class Exclusion:
    doc: str
    first_line: str
    declared: bool


@dataclass(frozen=True)
class IneffectiveDeclaration:
    doc: str
    first_line: str
    token: str

    def __str__(self) -> str:
        return f"{self.doc}: `{self.token}` is not in the dispatcher's vocabulary — {self.first_line}"


@dataclass(frozen=True)
class DocResult:
    doc: str
    parsed: int
    eligible: int
    exclusions: list[Exclusion]
    ineffective: list[IneffectiveDeclaration]


def _resolve_ao_python(ao_root: Path) -> str:
    """The AO clone's own interpreter when it has a venv, else this one.

    Preferring the sibling's venv keeps PM's venv free of AO's dependency closure: the probe
    imports `server.regen_backlog_from_plan`, which pulls `config`/`role_registry`/`backlog`/
    `models`. Those happen to import cleanly under PM's venv today, but that is a coincidence of
    two dependency sets overlapping, not a contract — and when it stops being true the honest
    outcome is a loud probe failure, not a silent fallback to a hand-rolled regex.
    """
    venv_python = ao_root / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return str(venv_python)
    return sys.executable


def _run_probe(ao_root: Path, pm_root: Path) -> dict[str, object] | None:
    """Real-parser verdicts for every AO-dispatched plan doc, or None if the probe failed."""
    try:
        proc = subprocess.run(  # fixed argv, no shell=True
            [_resolve_ao_python(ao_root), "-c", _PROBE_SRC, str(ao_root), str(pm_root)],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"⚠️  AO dispatch-visibility probe could not run ({type(exc).__name__}) — SKIPPING.", file=sys.stderr)
        return None
    if proc.returncode != 0:
        print(
            "⚠️  AO dispatch-visibility probe failed against the agent-orchestrator clone — SKIPPING.\n"
            f"    stderr: {proc.stderr.strip()[:600]}",
            file=sys.stderr,
        )
        return None
    loaded = cast(object, json.loads(proc.stdout))
    if not isinstance(loaded, dict):
        print("⚠️  AO dispatch-visibility probe returned an unexpected payload — SKIPPING.", file=sys.stderr)
        return None
    return cast(dict[str, object], loaded)


def declaration_head(first_line: str) -> str:
    """The region of a checkbox line where a marker reads as a DECLARATION rather than prose.

    That is: the leading bracket-tag run (so `[DATA][BLOCKED-CREDENTIALS] P1.` counts wherever the
    marker sits among the tags), plus the first `MARKER_HEAD_CHARS` of the description body once
    the `- [ ] <ordinal> [TAG] P<n>.` structural prefix and any opening bold punctuation are
    stripped. A bare marker ahead of the tags is covered too: the prefix match simply consumes
    nothing, so the body starts at the marker.
    """
    prefix_match = _LEADING_PREFIX_RE.match(first_line)
    if prefix_match is None:
        return first_line[:MARKER_HEAD_CHARS]
    tags_region = prefix_match.group("tags")
    body_head = first_line[prefix_match.end() :][:MARKER_HEAD_CHARS]
    return f"{tags_region}\n{body_head}"


def declares_hold(block: str, blocked_re: re.Pattern[str], permanent_re: re.Pattern[str]) -> bool:
    """True when `block` DECLARES its hold structurally rather than merely mentioning a marker.

    Exactly one accepted form (see module docstring): the marker sits in the CHECKBOX LINE's
    leading declaration head. Continuation lines are deliberately not consulted; a soft-wrap can
    put a marker at the head of one by accident.
    """
    head = declaration_head(block.split("\n")[0])
    return bool(blocked_re.search(head) or permanent_re.search(head))


def analyse(payload: dict[str, object]) -> list[DocResult]:
    blocked_re = re.compile(cast(str, payload["blocked_token_pattern"]))
    permanent_re = re.compile(cast(str, payload["permanent_pattern"]))
    docs = cast(list[dict[str, object]], payload["docs"])

    results: list[DocResult] = []
    for entry in docs:
        doc = cast(str, entry["doc"])
        excluded_blocks = cast(list[str], entry["excluded"])
        exclusions = [
            Exclusion(
                doc=doc,
                first_line=block.split("\n")[0].strip()[:150],
                declared=declares_hold(block, blocked_re, permanent_re),
            )
            for block in excluded_blocks
        ]
        ineffective: list[IneffectiveDeclaration] = []
        for description in cast(list[str], entry["parsed_todos"]):
            head = declaration_head(description)
            for match in _GENERIC_BLOCKED_RE.finditer(head):
                if blocked_re.match(match.group(0)):
                    continue  # a real, recognised token — the parser will have dropped it
                ineffective.append(
                    IneffectiveDeclaration(doc=doc, first_line=description.strip()[:150], token=match.group(0))
                )

        results.append(
            DocResult(
                doc=doc,
                parsed=cast(int, entry["parsed"]),
                eligible=cast(int, entry["eligible"]),
                exclusions=exclusions,
                ineffective=ineffective,
            )
        )
    return results


def undeclared_exclusions(results: list[DocResult]) -> list[Exclusion]:
    return [exc for doc in results for exc in doc.exclusions if not exc.declared]


def ineffective_declarations(results: list[DocResult]) -> list[IneffectiveDeclaration]:
    return [item for doc in results for item in doc.ineffective]


def zero_dispatchable_docs(results: list[DocResult]) -> list[DocResult]:
    """Docs with at least one parser-eligible open todo but zero reaching the backlog.

    `eligible >= 1` matters: a doc whose every todo is already `- [x]` done is simply finished
    (archival is `check_archive_candidates.sh`'s job, not this gate's) and must not be reported
    here.
    """
    return [doc for doc in results if doc.eligible >= 1 and doc.parsed == 0]


def _load_baseline(baseline_path: Path) -> tuple[int, int, int]:
    if not baseline_path.exists():
        return (0, 0, 0)
    loaded = cast(object, yaml.safe_load(baseline_path.read_text(encoding="utf-8")))
    if not isinstance(loaded, dict):
        return (0, 0, 0)
    data = cast(dict[str, object], loaded)

    def _count(key: str) -> int:
        value = data.get(key)
        return value if isinstance(value, int) else 0

    return (
        _count("undeclared_exclusion_baseline"),
        _count("zero_dispatchable_doc_baseline"),
        _count("ineffective_declaration_baseline"),
    )


def _write_baseline(
    baseline_path: Path,
    undeclared: list[Exclusion],
    zero_docs: list[DocResult],
    ineffective: list[IneffectiveDeclaration],
) -> None:
    payload: dict[str, object] = {
        "undeclared_exclusion_baseline": len(undeclared),
        "zero_dispatchable_doc_baseline": len(zero_docs),
        "ineffective_declaration_baseline": len(ineffective),
        "rule": "ao-dispatch-visibility (ratchet — every count only goes DOWN)",
        "source": ("plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md"),
        "baseline_undeclared": [{"doc": e.doc, "todo": e.first_line} for e in undeclared],
        "baseline_zero_dispatchable": [{"doc": d.doc, "eligible": d.eligible} for d in zero_docs],
        "baseline_ineffective": [{"doc": i.doc, "token": i.token, "todo": i.first_line} for i in ineffective],
    }
    baseline_path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AO dispatch-visibility check (silently non-dispatchable todos must declare their hold)."
    )
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parents[2].parent)
    parser.add_argument("--baseline-path", type=Path, default=DEFAULT_BASELINE_PATH)
    parser.add_argument("--baseline-write", action="store_true")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print every undeclared exclusion and zero-dispatchable doc (triage mode).",
    )
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    baseline_path: Path = cast(Path, ns.baseline_path)
    baseline_write: bool = cast(bool, ns.baseline_write)
    report: bool = cast(bool, ns.report)

    pm_root = workspace_root / "unified-trading-pm"
    if not (pm_root / "plans" / "active").is_dir():
        print(f"ERROR: plans/active not found at {pm_root / 'plans' / 'active'}", file=sys.stderr)
        return 2

    ao_root = workspace_root / AO_REPO_NAME
    if not (ao_root / "server" / "regen_backlog_from_plan.py").is_file():
        print(
            f"⚠️  AO dispatch-visibility check SKIPPED — no `{AO_REPO_NAME}` sibling clone at {ao_root}.\n"
            "    This gate imports the dispatcher's REAL `_parse_open_todos` as its oracle and will not\n"
            "    substitute a hand-rolled regex for it. Clone agent-orchestrator beside this repo to enable.",
            file=sys.stderr,
        )
        return 0

    payload = _run_probe(ao_root, pm_root)
    if payload is None:
        return 0

    results = analyse(payload)
    undeclared = undeclared_exclusions(results)
    zero_docs = zero_dispatchable_docs(results)
    ineffective = ineffective_declarations(results)
    total_excluded = sum(len(d.exclusions) for d in results)
    declared = total_excluded - len(undeclared)

    print(
        f"Scanned {len(results)} AO-dispatched plan(s): "
        f"{sum(d.eligible for d in results)} parser-eligible open todo(s), "
        f"{sum(d.parsed for d in results)} dispatchable, {total_excluded} excluded "
        f"({declared} declared, {len(undeclared)} UNDECLARED); "
        f"{len(zero_docs)} zero-dispatchable doc(s); "
        f"{len(ineffective)} ineffective declaration(s)."
    )

    if baseline_write:
        _write_baseline(baseline_path, undeclared, zero_docs, ineffective)
        print(
            f"✅ Wrote baseline (undeclared={len(undeclared)}, zero-dispatchable={len(zero_docs)}, "
            f"ineffective={len(ineffective)}) to {baseline_path}"
        )
        return 0

    undeclared_baseline, zero_baseline, ineffective_baseline = _load_baseline(baseline_path)

    if undeclared and report:
        print(f"\nUndeclared exclusions ({len(undeclared)}, baseline {undeclared_baseline}):")
        for exc in undeclared:
            print(f"  - {exc.doc}\n      {exc.first_line}")
    elif undeclared:
        print(f"\nUndeclared exclusions: {len(undeclared)} (baseline {undeclared_baseline}). First 15:")
        for exc in undeclared[:15]:
            print(f"  - {exc.doc}: {exc.first_line[:110]}")
        if len(undeclared) > 15:
            print(f"  ... + {len(undeclared) - 15} more (re-run with --report for the full list)")

    if zero_docs:
        print(f"\nZero-dispatchable docs ({len(zero_docs)}, baseline {zero_baseline}) — AO will never touch these:")
        for doc in zero_docs if report else zero_docs[:15]:
            print(f"  - {doc.doc} (0 of {doc.eligible} eligible todos dispatchable)")
        if not report and len(zero_docs) > 15:
            print(f"  ... + {len(zero_docs) - 15} more (re-run with --report for the full list)")

    if ineffective:
        print(
            f"\nIneffective declarations ({len(ineffective)}, baseline {ineffective_baseline}) — "
            "these LOOK held but AO dispatches them:"
        )
        for item in ineffective if report else ineffective[:15]:
            print(f"  - {item.doc}: `{item.token}` unknown to the dispatcher\n      {item.first_line[:110]}")
        if not report and len(ineffective) > 15:
            print(f"  ... + {len(ineffective) - 15} more (re-run with --report for the full list)")

    undeclared_regressed = len(undeclared) > undeclared_baseline
    zero_regressed = len(zero_docs) > zero_baseline
    ineffective_regressed = len(ineffective) > ineffective_baseline

    if undeclared_regressed:
        print(
            f"\n❌ AO dispatch-visibility regression: {len(undeclared)} undeclared exclusion(s) > "
            f"baseline {undeclared_baseline}.\n"
            "   A todo AO will never dispatch must DECLARE the hold, in the checkbox line's LEADING position:\n"
            "   `- [ ] [DATA][BLOCKED-CREDENTIALS] P1. ...`. A marker mid-sentence or on a continuation line does\n"
            "   NOT count — a 120-char prose wrap can put one there by accident.\n"
            "   If the todo is NOT actually blocked, rephrase so no live marker token appears in its prose —\n"
            "   lowercase/hyphenated wording does not match (the vocabulary is case-SENSITIVE).",
            file=sys.stderr,
        )
    if zero_regressed:
        print(
            f"\n❌ AO dispatch-visibility regression: {len(zero_docs)} zero-dispatchable doc(s) > "
            f"baseline {zero_baseline}.\n"
            "   An `active`, `assigned_vm: planning` doc with zero dispatchable todos is either mis-tagged or\n"
            "   finished — never correct as-is. Re-tag it `assigned_vm: NA`, archive it, or declare the holds.",
            file=sys.stderr,
        )
    if ineffective_regressed:
        print(
            f"\n❌ AO dispatch-visibility regression: {len(ineffective)} ineffective declaration(s) > "
            f"baseline {ineffective_baseline}.\n"
            "   A todo declares `BLOCKED-<TOKEN>` in a token the dispatcher does not know, so it dispatches\n"
            "   anyway while reading as held. Use a token from the dispatcher's own vocabulary\n"
            "   (`_BLOCKED_TOKEN_RE` in agent-orchestrator/server/regen_backlog_from_plan.py), or add the new\n"
            "   token there FIRST — a marker AO cannot see is not a hold.",
            file=sys.stderr,
        )
    if undeclared_regressed or zero_regressed or ineffective_regressed:
        print(
            "   Re-baseline ONLY after confirming the increase is genuine declared debt:\n"
            f"   python3 {Path(__file__)} --workspace-root $WORKSPACE_ROOT --baseline-write",
            file=sys.stderr,
        )
        return 1

    if (
        len(undeclared) < undeclared_baseline
        or len(zero_docs) < zero_baseline
        or len(ineffective) < ineffective_baseline
    ):
        print(
            f"\n⚠️  Improvement (undeclared {len(undeclared)} vs {undeclared_baseline}, "
            f"zero-dispatchable {len(zero_docs)} vs {zero_baseline}, "
            f"ineffective {len(ineffective)} vs {ineffective_baseline}). Re-baseline to codify the ratchet."
        )
    print("\n✅ AO dispatch-visibility: at/below baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
