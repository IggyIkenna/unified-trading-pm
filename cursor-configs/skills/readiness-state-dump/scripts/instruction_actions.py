#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""InstructionActionV2 handler-coverage measurement for the `execution_instruction` leg.

Why this module exists, and what it deliberately does NOT claim
---------------------------------------------------------------
`readiness-state-dump`'s SKILL.md used to point the `execution_instruction` leg at
`execution-service/execution_service/v2/policy_resolver.py`, calling it "the real
InstructionActionV2-adaptor registry a future increment should read". Measured
2026-08-20: it is not. `policy_resolver.py` resolves an execution *algorithm* for an
instruction, keyed by `(client_id, slot_label)`, with venue appearing only as one
`applies_to` gate dimension (`venue_category`). It answers "which algo runs this
instruction for this client's slot", never "can this venue execute this action".

The only action-keyed dispatch that actually exists is
`execution_service/backtest_v2/action_handlers.py::resolve_settlement`, and it is
**venue-independent and backtest-scoped** -- it resolves a deterministic benchmark
settlement for the batch=live determinism proof, not a live per-venue execution path.

So this module measures what is really there, and the leg stays honestly `unverified`
per venue (operator ruling 2026-08-16: a leg with no real check prints `unverified`,
never a silent pass). What it adds is that the `unverified` now carries a MEASURED
denominator instead of "no check wired": how many of the enum's actions have a
settlement handler at all, and exactly which ones do not. An action with no handler
raises `UnhandledActionError` at runtime -- that is a real, reportable negative even
though it is not a per-venue one.

A per-venue instruction-path check remains genuinely blocked on execution-service
exposing one (tranche T4). The inbound request naming the exact shape needed is filed
on that tranche's plan; nothing here guesses at it. Mapping InstructionActionV2 members
onto UAC `operation_details` keys was considered and rejected as drift: measured
2026-08-20, that vocabulary is per-venue idiosyncratic (`place_order` / `create_order` /
`new_order` / `post_order` / `add_order` / `submit_order` / `buy`+`sell`) and mixed with
feed endpoints (`l2_book`, `all_mids`, `ws_trades`), so any hand-built action->operation
map would silently misread venues that spell their order verb differently.

Parsed via AST, never imported -- unified-trading-pm has no dependency on either
execution-service or unified-api-contracts, and a service-to-service import would
violate the tier rule anyway. AST is exactly as reliable for an enum member list and a
set of attribute references, which is the same reasoning check_artefact_enum_drift.py
already applies.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path

# CANCEL is not a gap: resolve_settlement's own docstring states it returns None for
# "control-plane actions that carry no fill (``CANCEL``)". Classified separately so it
# is never counted as a missing handler, and so a future control-plane action added
# here is a deliberate, reviewed edit rather than a silent reclassification.
CONTROL_PLANE_ACTIONS: frozenset[str] = frozenset({"CANCEL"})

_UAC_ENUMS_REL = Path("unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py")
_HANDLERS_REL = Path("execution-service/execution_service/backtest_v2/action_handlers.py")
_ENUM_NAME = "InstructionActionV2"
_HANDLER_FN = "resolve_settlement"


@dataclass(frozen=True)
class ActionCoverage:
    """Measured InstructionActionV2 settlement-handler coverage.

    `resolved` is False when a source file could not be read or parsed -- callers must
    surface that as `unverified`, never as zero coverage (an unreadable file is not
    evidence of a missing handler).
    """

    resolved: bool
    members: tuple[str, ...] = ()
    handled: tuple[str, ...] = ()
    control_plane: tuple[str, ...] = ()
    unhandled: tuple[str, ...] = ()
    note: str = ""
    sources: tuple[str, ...] = field(default_factory=tuple)

    @property
    def denominator(self) -> int:
        return len(self.members)

    def summary(self) -> str:
        if not self.resolved:
            return f"instruction-action coverage unresolved: {self.note}"
        covered = len(self.handled) + len(self.control_plane)
        text = (
            f"{covered}/{self.denominator} InstructionActionV2 actions have a settlement path "
            f"({len(self.handled)} handled, {len(self.control_plane)} control-plane no-fill)"
        )
        if self.unhandled:
            text += f"; {len(self.unhandled)} raise UnhandledActionError: {list(self.unhandled)}"
        return text


def _enum_members(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == _ENUM_NAME:
            return [
                s.targets[0].id
                for s in node.body
                if isinstance(s, ast.Assign) and s.targets and isinstance(s.targets[0], ast.Name)
            ]
    return []


def _handled_actions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    handled: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == _HANDLER_FN:
            for inner in ast.walk(node):
                if (
                    isinstance(inner, ast.Attribute)
                    and isinstance(inner.value, ast.Name)
                    and inner.value.id == _ENUM_NAME
                ):
                    handled.add(inner.attr)
    return handled


def measure(workspace_root: Path) -> ActionCoverage:
    """Measure handler coverage, or return an unresolved verdict explaining why."""
    enums_path = workspace_root / _UAC_ENUMS_REL
    handlers_path = workspace_root / _HANDLERS_REL
    sources = (_UAC_ENUMS_REL.as_posix(), _HANDLERS_REL.as_posix())

    missing = [p.as_posix() for p in (_UAC_ENUMS_REL, _HANDLERS_REL) if not (workspace_root / p).exists()]
    if missing:
        return ActionCoverage(resolved=False, note=f"source file(s) not present: {missing}", sources=sources)

    try:
        members = _enum_members(enums_path)
        handled = _handled_actions(handlers_path)
    except SyntaxError as exc:
        return ActionCoverage(resolved=False, note=f"AST parse failed: {exc}", sources=sources)

    if not members:
        return ActionCoverage(
            resolved=False,
            note=f"no `class {_ENUM_NAME}` member list found in {_UAC_ENUMS_REL.as_posix()}",
            sources=sources,
        )
    if not handled:
        return ActionCoverage(
            resolved=False,
            note=f"no {_ENUM_NAME} references found in {_HANDLER_FN}() -- dispatch shape changed",
            sources=sources,
        )

    member_set = set(members)
    control = sorted(member_set & CONTROL_PLANE_ACTIONS)
    unhandled = sorted(member_set - handled - set(control))
    return ActionCoverage(
        resolved=True,
        members=tuple(members),
        handled=tuple(sorted(handled & member_set)),
        control_plane=tuple(control),
        unhandled=tuple(unhandled),
        sources=sources,
    )


def main() -> int:
    root = Path(__file__).resolve().parents[5]
    cov = measure(root)
    print(f"workspace root: {root}")
    print(cov.summary())
    if cov.resolved:
        print(f"  handled       : {list(cov.handled)}")
        print(f"  control-plane : {list(cov.control_plane)}")
        print(f"  unhandled     : {list(cov.unhandled)}")
    return 0 if cov.resolved else 1


if __name__ == "__main__":
    raise SystemExit(main())
