"""Unit tests for scripts/quality_gates/check_ao_dispatch_visibility.py.

SSOT: plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md

Covers the FOUR known trigger shapes of the silent-non-dispatch bug class, each from a real
incident, at both levels the gate operates on:

  1. `"was BLOCKED-CREDENTIALS, resolved"` — a resolution note restating the old marker
     (ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md: 27 todos across 21 files).
  2. `BLOCKED-PREREQUISITES` — a token absent from `_BLOCKED_TOKEN_RE`'s alternation
     (blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md).
  3. `"BLOCKED-X framing was retired"` — marker-then-resolution word order
     (defi_batch8_finalize_gate_bypass_missing_upstream_task_2026_08_02.md, archived).
  4. `"Do NOT mark this BLOCKED-CREDENTIALS"` — the sentence FORBIDDING the marker contains it
     (the sports P3 Betfair todo; fixed in unified-trading-pm@a134a45948, verified 14/15 -> 15/15).

Measured against the parser as it stands 2026-08-08, the four shapes do NOT all fail the same
way, which is the single most useful thing this suite records:

  - shape 4 is silently DROPPED — the live incident, and what finding 1 reports.
  - shapes 1 and 3 correctly DISPATCH; their escape hatches (`_STALE_MARKER_PREFIX_RE` 2026-07-29,
    `_STALE_MARKER_SUFFIX_RE` 2026-08-02) work. Pinned here so a later regex edit cannot silently
    re-break them.
  - shape 2 DISPATCHES DESPITE declaring a hold, because `BLOCKED-PREREQUISITES` is not in the
    dispatcher's vocabulary — the inverse failure, and the reason finding 3 exists. A gate that
    only inspected excluded todos would be structurally blind to it.

Two layers, deliberately:

  - `declares_hold` tests run everywhere and pin the gate's own contract: none of the four shapes
    may read as a DECLARED hold, because none of them is one. Whether the parser drops a given
    shape today is a property of AO's regex (widened four times, and it will move again); whether
    the gate calls it "declared" must not move.
  - the parser-oracle tests run the REAL `_parse_open_todos` over synthetic plan files via the
    gate's own probe, and skip loudly when `agent-orchestrator` is not cloned beside this repo.
    Their central guarantee is that the gate's view and the dispatcher's view stay identical:
    `eligible - parsed == len(excluded)`, so nothing goes unaccounted for in either direction.
"""

from __future__ import annotations

import importlib.util
import re
import sys
import types
from pathlib import Path

import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_ao_dispatch_visibility.py"
    spec = importlib.util.spec_from_file_location("check_ao_dispatch_visibility", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


MOD = _load_module()

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
AO_ROOT = WORKSPACE_ROOT / "agent-orchestrator"
AO_PRESENT = (AO_ROOT / "server" / "regen_backlog_from_plan.py").is_file()

requires_ao = pytest.mark.skipif(
    not AO_PRESENT,
    reason=(
        f"agent-orchestrator not cloned at {AO_ROOT} — the parser-oracle layer of this gate is "
        "unverifiable here (by design: the gate soft-skips rather than substituting a hand-rolled regex)"
    ),
)

# The real vocabulary, mirrored here ONLY so the pure-predicate tests can run without a sibling
# clone. `test_marker_vocabulary_matches_the_real_parser` asserts these stay identical to AO's,
# so this convenience copy can never silently drift into a second source of truth.
BLOCKED_RE = re.compile(
    r"BLOCKED-(CREDENTIALS|OPERATOR(-DECISION)?|BILLING|UPSTREAM-(OUTAGE|DESIGN)|PLAYWRIGHT|JURISDICTION)\b"
)
PERMANENT_RE = re.compile(r"DEFERRED-BY-DESIGN\b|_\(\s*[Ss]tretch|\b[Ss]tretch,\s*optional\b|\*\*[Ss]tretch\*\*")


# ── The four trigger shapes, as the parser sees them (checkbox text + continuation block) ─────

SHAPE_1_RESOLVED_RETAG = (
    "[DATA] P1. **Re-run the Tardis backfill for the 2025-11 window.**\n"
    "      This todo was `BLOCKED-CREDENTIALS`, resolved 2026-07-29 when the key landed — it is\n"
    "      fully actionable now."
)

SHAPE_2_UNKNOWN_TOKEN = (
    "[REVIEW] P2. BLOCKED-PREREQUISITES — final e2e gate stamp, deferred until the upstream\n      capture completes."
)

SHAPE_3_MARKER_THEN_RESOLUTION = (
    "[CODE] P1. **Wire the finalize gate's missing upstream task.**\n"
    "      The source todo's original `BLOCKED-OPERATOR-DECISION (2026-07-22)` framing was retired\n"
    "      2026-08-02; nothing gates this any more."
)

SHAPE_4_MARKER_BAN_SENTENCE = (
    "[SCRIPT] P3. **Scaffold the Betfair Exchange adapter.** Fully AO-completable with no operator\n"
    "      step, buildable credential-free against the documented REST shape. Do NOT mark this\n"
    "      `BLOCKED-CREDENTIALS` — the credential ask is a separate, already-tracked item and must\n"
    "      not gate the scaffold."
)

ALL_SHAPES = {
    "shape_1_resolved_retag": SHAPE_1_RESOLVED_RETAG,
    "shape_2_unknown_token": SHAPE_2_UNKNOWN_TOKEN,
    "shape_3_marker_then_resolution": SHAPE_3_MARKER_THEN_RESOLUTION,
    "shape_4_marker_ban_sentence": SHAPE_4_MARKER_BAN_SENTENCE,
}


# ── Layer 1: the declaration predicate (runs everywhere) ──────────────────────────────────────


@pytest.mark.unit
@pytest.mark.parametrize("name", sorted(ALL_SHAPES))
def test_four_trigger_shapes_are_never_treated_as_declared(name: str) -> None:
    """None of the four shapes may read as a declared hold — none of them is one.

    This is the gate's core guarantee. If any shape were classified "declared", the gate would
    absolve exactly the todos it exists to surface, and the corpus would go back to losing them
    silently.
    """
    assert MOD.declares_hold(ALL_SHAPES[name], BLOCKED_RE, PERMANENT_RE) is False


@pytest.mark.unit
@pytest.mark.parametrize(
    "block",
    [
        # Bracket tag beside the role tag — the dominant real form in the corpus.
        "[DATA][BLOCKED-CREDENTIALS] P1. Restore the UPBIT backfill, gated on the Tardis key.",
        # Bare marker ahead of the tags.
        "BLOCKED-UPSTREAM-DESIGN [DATA] P2. Quarantine disposition for unresolvable objects.",
        # Opening the description body, after the `[TAG] P<n>.` prefix.
        "[DATA] P3. **BLOCKED-OPERATOR — BLK-d9137d48, waiting on the scheduled maintenance window.**",
        # Permanent markers in the same leading position.
        "[SCRIPT] P1. DEFERRED-BY-DESIGN. Phase 5 canonical-groups backfill, ~24 groups remaining.",
        "[TEST] P2. **DEFERRED-BY-DESIGN** — 5 of 7 engine-running e2e DeFi tests bypass the config path.",
        # Ordinal prefix ahead of everything (the numbered-todo style).
        "12. [DATA][BLOCKED-BILLING] P2. Re-pull the Databento window once billing is restored.",
    ],
)
def test_leading_position_markers_read_as_declared(block: str) -> None:
    """A genuine hold declared in the checkbox line's leading head is honoured in every real form."""
    assert MOD.declares_hold(block, BLOCKED_RE, PERMANENT_RE) is True


@pytest.mark.unit
def test_soft_wrapped_continuation_marker_is_not_a_declaration() -> None:
    """A 120-char prose wrap that lands a marker at a continuation line's head is NOT a declaration.

    Verbatim shape from the live corpus (cefi batch10 finalize). An earlier draft of this gate
    accepted it and thereby absolved 7 soft-wrapped mid-sentence mentions, two of which were
    resolution notes saying the marker no longer applied.
    """
    block = (
        "[REVIEW] P1. **Re-check the 32 non-batchable Deferred items from batch10.** In particular:\n"
        "      (a) has the operator ruled on `issues/deribit_combo_perpetual_partition_move.md`'s\n"
        "      BLOCKED-OPERATOR-DECISION item)? (b) has the conflicting active claim shipped?"
    )
    assert MOD.declares_hold(block, BLOCKED_RE, PERMANENT_RE) is False


@pytest.mark.unit
def test_resolution_note_at_continuation_head_is_not_a_declaration() -> None:
    """The nastiest sub-case: a line-initial marker whose sentence CLEARS it."""
    block = (
        "[DATA] P1. **RETAGGED 2026-08-07 — re-run the odds-API census for the scattered gaps.**\n"
        "      `BLOCKED-CREDENTIALS` is now STALE, clearing it.** The credit top-up landed 2026-08-03."
    )
    assert MOD.declares_hold(block, BLOCKED_RE, PERMANENT_RE) is False


@pytest.mark.unit
def test_marker_just_past_the_declaration_head_is_not_a_declaration() -> None:
    """Boundary check on MARKER_HEAD_CHARS: prose that merely starts near the front is not a hold."""
    block = (
        "[CODE] P2. Execute the FINAL decided fix (retire OR scaffold-with-BLOCKED-CREDENTIALS, per\n"
        "      the operator's answer to the discriminator investigation above)."
    )
    assert MOD.declares_hold(block, BLOCKED_RE, PERMANENT_RE) is False


# ── Layer 2: the real parser as oracle (skips loudly without the sibling clone) ───────────────


def _probe(tmp_path: Path) -> dict[str, object]:
    payload = MOD._run_probe(AO_ROOT, tmp_path)
    assert payload is not None, "probe failed against the agent-orchestrator clone"
    return payload


def _write_plan(tmp_path: Path, name: str, todos: list[str], assigned_vm: str = "planning") -> None:
    active = tmp_path / "plans" / "active"
    active.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"- [ ] {todo}\n" for todo in todos)
    (active / name).write_text(
        f"---\ndoc_type: plan\nstatus: active\nassigned_vm: {assigned_vm}\n---\n\n# Test plan\n\n{body}",
        encoding="utf-8",
    )


@requires_ao
@pytest.mark.unit
def test_marker_vocabulary_matches_the_real_parser(tmp_path: Path) -> None:
    """The convenience regexes above must stay byte-identical to AO's real ones.

    The gate itself always compiles the patterns the probe reports, so production never drifts —
    this guards the TEST's local copy, so a vocabulary change upstream fails loudly here instead
    of quietly making the shape assertions test a fiction.
    """
    _write_plan(tmp_path, "vocab.md", ["[DATA] P1. Anything."])
    payload = _probe(tmp_path)
    assert payload["blocked_token_pattern"] == BLOCKED_RE.pattern
    assert payload["permanent_pattern"] == PERMANENT_RE.pattern


@requires_ao
@pytest.mark.unit
def test_every_parser_exclusion_is_surfaced_by_the_gate(tmp_path: Path) -> None:
    """The gate's accounting must agree with the dispatcher's exactly, over all four shapes.

    `eligible - parsed == len(excluded)` is the invariant that makes this gate trustworthy: it
    proves the reported exclusion set is the WHOLE difference between what a human reads as
    tracked and what AO will actually run, with nothing unaccounted for.
    """
    _write_plan(tmp_path, "shapes.md", list(ALL_SHAPES.values()))
    payload = _probe(tmp_path)
    docs = payload["docs"]
    assert isinstance(docs, list) and len(docs) == 1
    doc = docs[0]
    assert doc["eligible"] == len(ALL_SHAPES)
    assert doc["eligible"] - doc["parsed"] == len(doc["excluded"])


@requires_ao
@pytest.mark.unit
def test_shape_4_marker_ban_sentence_is_dropped_by_the_real_parser(tmp_path: Path) -> None:
    """The incident that opened this issue: a todo lost to the sentence forbidding the marker.

    Asserted (not merely pinned) because there is no plausible future widening that should make
    "Do NOT mark this BLOCKED-CREDENTIALS" dispatchable via the escape hatches — the marker is
    live-tense and carries no resolution language. Its own text says it is fully AO-completable
    with no operator step, so the parser dropping it is pure loss, and the gate must report it.
    """
    _write_plan(tmp_path, "betfair.md", [SHAPE_4_MARKER_BAN_SENTENCE])
    payload = _probe(tmp_path)
    doc = payload["docs"][0]
    assert doc["parsed"] == 0
    assert len(doc["excluded"]) == 1
    assert MOD.declares_hold(doc["excluded"][0], BLOCKED_RE, PERMANENT_RE) is False


@requires_ao
@pytest.mark.unit
def test_shape_2_unknown_token_dispatches_despite_looking_held(tmp_path: Path) -> None:
    """Shape 2 fails in the OPPOSITE direction, which is why finding 3 exists.

    `BLOCKED-PREREQUISITES` is not in `_BLOCKED_TOKEN_RE`'s alternation, so the parser does not
    drop it: the author declared a hold in the leading position and AO dispatches the todo anyway.
    Finding 1 structurally cannot see this (it only inspects EXCLUDED todos), so a gate built on
    exclusions alone would have left the 2026-07-28 incident class wide open.
    """
    _write_plan(tmp_path, "prereq.md", [SHAPE_2_UNKNOWN_TOKEN])
    results = MOD.analyse(_probe(tmp_path))
    assert results[0].parsed == 1, "shape 2 is dispatched, not dropped — that is the defect"
    ineffective = MOD.ineffective_declarations(results)
    assert [i.token for i in ineffective] == ["BLOCKED-PREREQUISITES"]


@requires_ao
@pytest.mark.unit
def test_recognised_token_is_not_an_ineffective_declaration(tmp_path: Path) -> None:
    """A token the dispatcher DOES know must never appear in finding 3 — it was properly excluded."""
    _write_plan(
        tmp_path,
        "known.md",
        ["[DATA][BLOCKED-CREDENTIALS] P1. Restore the UPBIT backfill, gated on the Tardis key."],
    )
    assert MOD.ineffective_declarations(MOD.analyse(_probe(tmp_path))) == []


@requires_ao
@pytest.mark.unit
def test_blocked_on_evidence_marker_is_not_flagged(tmp_path: Path) -> None:
    """`BLOCKED-ON:<ref>` is a different family (verify.py's `/done`-time evidence closure).

    A todo carrying it is SUPPOSED to stay dispatchable, so treating it as a failed hold would
    conflate two conventions the corpus explicitly keeps apart.
    """
    _write_plan(tmp_path, "blocked_on.md", ["[SCRIPT] P2. BLOCKED-ON:cefi_content_migration_round3 (still open)."])
    results = MOD.analyse(_probe(tmp_path))
    assert results[0].parsed == 1
    assert MOD.ineffective_declarations(results) == []


@requires_ao
@pytest.mark.unit
@pytest.mark.parametrize(
    "name",
    ["shape_1_resolved_retag", "shape_3_marker_then_resolution"],
)
def test_prior_escape_hatch_fixes_still_hold(name: str, tmp_path: Path) -> None:
    """Shapes 1 and 3 must still DISPATCH — pinning the 2026-07-29 and 2026-08-02 fixes.

    Both were once silently dropped; `_STALE_MARKER_PREFIX_RE` ("was BLOCKED-X, resolved") and
    `_STALE_MARKER_SUFFIX_RE` ("BLOCKED-X framing was retired") were added to recognise the
    resolution language. Those widenings were correct for these shapes, and this gate does not
    undo them — but nothing else in the corpus guards them, so a future edit to either regex
    would silently re-break 27+ todos. It fails here first instead.
    """
    _write_plan(tmp_path, "hatch.md", [ALL_SHAPES[name]])
    results = MOD.analyse(_probe(tmp_path))
    assert results[0].parsed == 1, f"{name} regressed to silently non-dispatchable"
    assert results[0].exclusions == []


@requires_ao
@pytest.mark.unit
def test_zero_dispatchable_doc_is_reported_separately(tmp_path: Path) -> None:
    """A doc whose every eligible todo is excluded is the acute finding and gets its own bucket."""
    _write_plan(
        tmp_path,
        "all_blocked.md",
        [
            SHAPE_4_MARKER_BAN_SENTENCE,
            "[DATA][BLOCKED-CREDENTIALS] P1. Restore the UPBIT backfill, gated on the Tardis key.",
        ],
    )
    _write_plan(tmp_path, "healthy.md", ["[DATA] P1. A perfectly ordinary dispatchable todo."])
    results = MOD.analyse(_probe(tmp_path))
    zero_docs = {d.doc for d in MOD.zero_dispatchable_docs(results)}
    assert "plans/active/all_blocked.md" in zero_docs
    assert "plans/active/healthy.md" not in zero_docs


@requires_ao
@pytest.mark.unit
def test_finished_doc_with_no_open_todos_is_not_zero_dispatchable(tmp_path: Path) -> None:
    """`eligible >= 1` guard: a doc with only `- [x]` todos is finished, not silently blocked.

    Archival is `check_archive_candidates.sh`'s job; reporting it here would flood this gate with
    findings it has no fix for.
    """
    active = tmp_path / "plans" / "active"
    active.mkdir(parents=True, exist_ok=True)
    (active / "done.md").write_text(
        "---\ndoc_type: plan\nstatus: active\nassigned_vm: planning\n---\n\n"
        "- [x] 1. ✅ [DATA] P1. Shipped — unified-trading-pm@abc1234 + evidence\n",
        encoding="utf-8",
    )
    results = MOD.analyse(_probe(tmp_path))
    assert MOD.zero_dispatchable_docs(results) == []


@requires_ao
@pytest.mark.unit
def test_non_planning_docs_are_out_of_scope(tmp_path: Path) -> None:
    """`assigned_vm: NA` is human-owned — its todos were never going to dispatch, so a drop there
    is not the silent-false-progress failure this gate reports."""
    _write_plan(tmp_path, "human.md", [SHAPE_4_MARKER_BAN_SENTENCE], assigned_vm="NA")
    payload = _probe(tmp_path)
    assert payload["docs"] == []


@requires_ao
@pytest.mark.unit
def test_declared_hold_is_excluded_but_not_reported(tmp_path: Path) -> None:
    """The intentional case must stay quiet — otherwise the gate is noise and gets baselined away."""
    _write_plan(
        tmp_path,
        "declared.md",
        ["[DATA][BLOCKED-CREDENTIALS] P1. Restore the UPBIT backfill, gated on the Tardis key."],
    )
    results = MOD.analyse(_probe(tmp_path))
    assert sum(len(d.exclusions) for d in results) == 1
    assert MOD.undeclared_exclusions(results) == []


# ── Baseline plumbing ─────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_baseline_roundtrip(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.yaml"
    exclusions = [MOD.Exclusion(doc="plans/active/a.md", first_line="[DATA] P1. x", declared=False)]
    zero_docs = [MOD.DocResult(doc="plans/active/b.md", parsed=0, eligible=2, exclusions=[], ineffective=[])]
    ineffective = [
        MOD.IneffectiveDeclaration(doc="plans/active/c.md", first_line="[DATA] P1. y", token="BLOCKED-PREREQUISITES")
    ]
    MOD._write_baseline(baseline, exclusions, zero_docs, ineffective)
    assert MOD._load_baseline(baseline) == (1, 1, 1)


@pytest.mark.unit
def test_missing_baseline_reads_as_zero(tmp_path: Path) -> None:
    """An absent baseline must mean strict-zero, never an accidental free pass."""
    assert MOD._load_baseline(tmp_path / "nope.yaml") == (0, 0, 0)
