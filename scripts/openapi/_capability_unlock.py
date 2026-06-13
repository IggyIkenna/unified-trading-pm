"""Counterfactual "minimal unlock set" engine (Wave-2 #1).

For every UNAVAILABLE capability edge in the manifest, derive the smallest set
of missing prerequisites that would make it available — the *minimal unlock
set* — and an ``unlock_distance`` (count of distinct missing pieces).  This
turns the wizard into a roadmap generator: blocked edges ranked closest-to-
available first are the highest-leverage build items
("Hyperliquid perps: adapter ✓, auth ✗ — 1 edge away").

The engine is INTENTIONALLY decoupled from the registry walk (like
``generate_capability_changelog.py``): it reads the already-generated
``capability-manifest.json`` so it runs anywhere (no ``.venv-workspace``) and is
deterministic — two runs are byte-identical.

How ``unlock_distance`` is computed
-----------------------------------
A blocked edge is any edge whose status ∈ {``not_available``, ``not_registered``,
``partial``}.  Its minimal unlock set is derived by inspecting WHY it is blocked
— the ``(status, gap_type, relation, reason)`` tuple plus the presence/metadata
of the related nodes:

  * ``not_available`` + ``logical_dead_end`` → **structurally impossible** (e.g.
    options on a sports venue, no DeFi dated-future venue).  This is correct and
    expected, NOT a build gap, so it carries ``unlock_distance = None`` (a
    sentinel meaning "never a roadmap item") and the single typed piece
    ``impossible``.  Excluded from the closest-first ranking.
  * ``not_available`` (no gap_type, e.g. a venue that *rejects* a collateral
    asset) → likewise a correct negative; ``unlock_distance = None``.
  * ``not_registered`` + ``missing_registry`` → needs the named registry
    populated.  ``has_leg`` / leg-derived ``uses_algo`` edges need a
    ``needs-leg-spec``; everything else needs a ``needs-registry-entry``.
    distance 1.
  * ``not_registered`` + ``needs_code_scan`` → ``needs-code-scan`` (distance 1).
  * ``*`` + ``missing_extraction`` → ``needs-extraction`` (distance 1).
  * ``partial`` (no gap_type) → a supported-with-caveats edge; the missing piece
    is classified from the ``reason`` text into a typed category
    (``needs-auth`` / ``needs-adapter`` / ``needs-registry-entry`` /
    ``needs-leg-spec`` / ``needs-data-feed`` / ``needs-config`` / ``needs-test``
    / ``needs-docs``).  distance = count of distinct typed pieces (usually 1).

The keyword classifier is a deterministic, ordered match over the lower-cased
reason text; the FIRST matching family wins so the mapping is stable.

SSOT: ``plans/active/capability_wizard_and_manifest_2026_06_11.md`` Wave-2 #1.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

# ---------------------------------------------------------------------------
# Typed missing-piece vocabulary (closed set)
# ---------------------------------------------------------------------------

#: A venue/source adapter (code) is missing.
PIECE_ADAPTER = "needs-adapter"
#: Authentication / credentials wiring is missing.
PIECE_AUTH = "needs-auth"
#: A declarative UAC registry entry is missing.
PIECE_REGISTRY = "needs-registry-entry"
#: A per-leg structural spec (ARCHETYPE_LEG_STRUCTURES) is missing.
PIECE_LEG_SPEC = "needs-leg-spec"
#: The registry exists but the generator can't yet extract/derive the value.
PIECE_EXTRACTION = "needs-extraction"
#: The answer is only derivable by an agent-orchestrator code scan.
PIECE_CODE_SCAN = "needs-code-scan"
#: A data feed / external calendar / price-feed integration is missing.
PIECE_DATA_FEED = "needs-data-feed"
#: A runtime config / capability flag must be declared.
PIECE_CONFIG = "needs-config"
#: An integration/batch test must be written/run to lift a caveat.
PIECE_TEST = "needs-test"
#: Docs / worked-example instances are the only remaining gap.
PIECE_DOCS = "needs-docs"
#: Structurally impossible — correct negative, never a roadmap item.
PIECE_IMPOSSIBLE = "impossible"

#: Statuses that count as "blocked" (a candidate for an unlock set).
BLOCKED_STATUSES = ("not_available", "not_registered", "partial")

#: Ordered keyword → typed-piece classifier for free-text ``reason`` strings.
#: First matching family wins (deterministic).  Each entry is
#: ``(piece, [substrings])`` — substrings matched against the lower-cased reason.
_REASON_CLASSIFIER: list[tuple[str, tuple[str, ...]]] = [
    (PIECE_AUTH, ("auth", "credential", "regulatory overhead", "mm designation", "designation required")),
    (PIECE_LEG_SPEC, ("leg structure", "multileg", "multi-leg", "per-leg", "multilegordercapability")),
    (
        PIECE_DATA_FEED,
        (
            "news-feed",
            "news feed",
            "calendar",
            "price-feed",
            "price feed",
            "liquidity",
            "feed integration",
            "liquidation feed",
            "slashing",
            "unlock",
            "earnings",
        ),
    ),
    (PIECE_TEST, ("batch-test", "batch test", "not batch-tested", "test harness", "roll service", "reconciliation")),
    (PIECE_DOCS, ("docs", "example instance", "worked instance", "no codex instance", "no worked")),
    (
        PIECE_CONFIG,
        (
            "routing policy",
            "routing",
            "capability flag",
            "flag missing",
            "flag gap",
            "config path",
            "pre-declaration",
            "expression policy",
            "expression axis",
            "mapping not declared",
            "policy not declared",
            "not declared",
            "fidelity flag",
            "semantics",
            "pricing-fidelity",
        ),
    ),
    (PIECE_ADAPTER, ("adapter", "symbol universe", "symbol declaration", "fix adapter")),
    (PIECE_REGISTRY, ("registry", "uac gap", "gap #", "no supported", "missing from uac")),
]


@dataclass(frozen=True)
class UnlockEntry:
    """A single blocked edge with its derived minimal unlock set."""

    from_node_id: str
    to_node_id: str
    relation: str
    status: str
    gap_type: str | None
    reason: str
    #: None → structurally impossible (never a roadmap item); else len(missing_pieces).
    unlock_distance: int | None
    missing_pieces: tuple[str, ...] = field(default_factory=tuple)

    def edge_key(self) -> str:
        """Stable identity for an edge (independent of status)."""
        return f"{self.from_node_id}|{self.relation}|{self.to_node_id}"

    def to_dict(self) -> dict[str, object]:
        return {
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "relation": self.relation,
            "status": self.status,
            "gap_type": self.gap_type,
            "reason": self.reason,
            "unlock_distance": self.unlock_distance,
            "missing_pieces": list(self.missing_pieces),
        }


def _classify_reason(reason: str) -> tuple[str, ...]:
    """Map a free-text ``reason`` to its typed missing-piece(s).

    Deterministic: families are tested in declared order, first match wins.  An
    unclassifiable non-empty reason yields ``(PIECE_REGISTRY,)`` (the honest
    default: a caveat with no declarative source is a registry/config gap).
    """
    text = reason.lower()
    for piece, needles in _REASON_CLASSIFIER:
        if any(n in text for n in needles):
            return (piece,)
    # Non-empty but unmatched → treat as a registry/config gap (never silently empty).
    return (PIECE_REGISTRY,) if text.strip() else (PIECE_CONFIG,)


def _pieces_for_edge(status: str, gap_type: str | None, relation: str, reason: str) -> tuple[str, ...]:
    """Derive the typed minimal missing-piece set for one blocked edge.

    The ``(status, gap_type, relation)`` tuple is the primary signal; ``reason``
    refines a ``partial`` caveat into a typed family.
    """
    # Structurally-impossible negatives — correct, never a build gap.
    if gap_type == "logical_dead_end":
        return (PIECE_IMPOSSIBLE,)
    if status == "not_available" and gap_type is None:
        # e.g. a venue that explicitly *rejects* a collateral asset — correct negative.
        return (PIECE_IMPOSSIBLE,)

    if gap_type == "needs_code_scan":
        return (PIECE_CODE_SCAN,)
    if gap_type == "missing_extraction":
        return (PIECE_EXTRACTION,)
    if gap_type == "missing_registry":
        # A leg-structure gap (has_leg, or a uses_algo blocked because the
        # archetype has no leg structure) needs the leg spec specifically.
        if relation.startswith("has_leg") or "no leg structure" in reason.lower():
            return (PIECE_LEG_SPEC,)
        return (PIECE_REGISTRY,)

    # partial / no gap_type → classify from the reason caveat.
    return _classify_reason(reason)


def compute_unlock_entries(edges: list[dict[str, object]]) -> list[UnlockEntry]:
    """Build an ``UnlockEntry`` for every blocked edge.

    Deduplicates by ``edge_key`` keeping the BEST (most-available) status so a
    single available sibling never masks a blocked one and vice-versa; among
    blocked duplicates the most-available status wins (matches the changelog's
    edge-status dedup rule).  Returns entries sorted deterministically by
    ``(unlock_distance is None, unlock_distance, edge_key)``.
    """
    rank = {"available": 0, "partial": 1, "not_registered": 2, "not_available": 3}
    # First pass: best status per edge_key across ALL edges (incl. available).
    best_status: dict[str, str] = {}
    raw_by_key: dict[str, dict[str, object]] = {}
    for e in edges:
        from_node = str(e["from_node_id"])
        to_node = str(e["to_node_id"])
        relation = str(e["relation"])
        status = str(e["status"])
        key = f"{from_node}|{relation}|{to_node}"
        prev = best_status.get(key)
        if prev is None or rank.get(status, 9) < rank.get(prev, 9):
            best_status[key] = status
            raw_by_key[key] = e

    entries: list[UnlockEntry] = []
    for key, status in best_status.items():
        if status not in BLOCKED_STATUSES:
            continue
        e = raw_by_key[key]
        gap_type = cast("str | None", e.get("gap_type"))
        relation = str(e["relation"])
        reason = str(e.get("reason") or "")
        pieces = _pieces_for_edge(status, gap_type, relation, reason)
        distance: int | None = None if pieces == (PIECE_IMPOSSIBLE,) else len(pieces)
        entries.append(
            UnlockEntry(
                from_node_id=str(e["from_node_id"]),
                to_node_id=str(e["to_node_id"]),
                relation=relation,
                status=status,
                gap_type=gap_type,
                reason=reason,
                unlock_distance=distance,
                missing_pieces=pieces,
            )
        )

    entries.sort(
        key=lambda u: (
            u.unlock_distance is None,
            u.unlock_distance if u.unlock_distance is not None else 0,
            u.edge_key(),
        )
    )
    return entries


def load_manifest_edges(manifest_path: Path) -> list[dict[str, object]]:
    """Load the manifest edge list (fail-fast on a malformed manifest)."""
    raw = cast("dict[str, object]", json.loads(manifest_path.read_text()))
    return cast("list[dict[str, object]]", raw["edges"])


def build_report(manifest_commit: str, entries: list[UnlockEntry]) -> dict[str, object]:
    """Assemble the deterministic JSON report payload.

    ``demand`` is a placeholder ``0`` per blocked edge — the wizard demand
    counts are a uts-ui follow-on (documented honestly); ranking is by
    ``unlock_distance`` ASC for now (closest-to-available first).
    """
    roadmap = [u for u in entries if u.unlock_distance is not None]
    impossible = [u for u in entries if u.unlock_distance is None]

    # Per-piece counts (only over roadmap items — impossible carries no piece).
    piece_counts: dict[str, int] = {}
    for u in roadmap:
        for p in u.missing_pieces:
            piece_counts[p] = piece_counts.get(p, 0) + 1

    # Distance histogram over roadmap items.
    distance_hist: dict[str, int] = {}
    for u in roadmap:
        k = str(u.unlock_distance)
        distance_hist[k] = distance_hist.get(k, 0) + 1

    return {
        "manifest_commit": manifest_commit,
        "demand_model": "placeholder demand=0 (wizard demand counts are a uts-ui follow-on)",
        "summary": {
            "blocked_edges_total": len(entries),
            "roadmap_edges": len(roadmap),
            "impossible_edges": len(impossible),
            "missing_piece_counts": dict(sorted(piece_counts.items())),
            "unlock_distance_histogram": dict(sorted(distance_hist.items())),
        },
        # roadmap entries ranked closest-first (already sorted); each gets demand=0.
        "roadmap": [{**u.to_dict(), "demand": 0} for u in roadmap],
        "impossible": [u.to_dict() for u in impossible],
    }


def _section(title: str, lines: list[str]) -> list[str]:
    out = [f"## {title} ({len(lines)})", ""]
    out.extend(lines if lines else ["_none_"])
    out.append("")
    return out


def render_markdown(manifest_commit: str, entries: list[UnlockEntry], top_n: int = 25) -> str:
    """Render the demand-weighted gap report (deterministic markdown).

    Blocked edges ranked by ``unlock_distance`` ASC (closest-to-available first
    = highest-leverage roadmap items).  Demand is a documented placeholder (0).
    """
    roadmap = [u for u in entries if u.unlock_distance is not None]
    impossible = [u for u in entries if u.unlock_distance is None]

    piece_counts: dict[str, int] = {}
    for u in roadmap:
        for p in u.missing_pieces:
            piece_counts[p] = piece_counts.get(p, 0) + 1

    out: list[str] = [
        "# Capability unlock report — minimal unlock sets (Wave-2 #1)",
        "",
        "Counterfactual roadmap: for every blocked capability edge, the smallest set",
        "of missing prerequisites that would make it available. Regenerated by",
        "`scripts/openapi/generate_capability_unlock_report.py` from the committed",
        "`capability-manifest.json` (deterministic — two runs are byte-identical).",
        "",
        "**Ranking**: by `unlock_distance` ASC (closest-to-available first = highest-",
        "leverage build items). Demand counts from the wizard are a uts-ui follow-on;",
        "every roadmap row currently carries a documented placeholder `demand=0`.",
        "",
        "**`unlock_distance`** = the count of distinct typed missing pieces. Edges that",
        "are structurally impossible (`logical_dead_end` / explicit negatives) carry NO",
        "distance and are listed separately — they are correct negatives, not roadmap items.",
        "",
        f"Manifest commit: `{manifest_commit}`",
        "",
    ]

    summary_lines = [
        f"- blocked edges total: **{len(entries)}**",
        f"- roadmap edges (have an unlock set): **{len(roadmap)}**",
        f"- structurally-impossible edges (excluded from ranking): **{len(impossible)}**",
    ]
    out.extend(_section("Summary", summary_lines))

    piece_lines = [f"- `{p}`: {piece_counts[p]}" for p in sorted(piece_counts)]
    out.extend(_section("Missing-piece counts (across roadmap edges)", piece_lines))

    # Bullet-list (NOT a markdown table) so the generator output is
    # prettier-stable — a padded table would be re-aligned by prettier and
    # churn the committed artifact every run.
    top = roadmap[:top_n]
    top_lines: list[str] = []
    for i, u in enumerate(top, start=1):
        pieces = ", ".join(f"`{p}`" for p in u.missing_pieces)
        edge = f"`{u.from_node_id}` --{u.relation}--> `{u.to_node_id}`"
        top_lines.append(
            f"{i}. {edge} — status `{u.status}`, unlock_distance **{u.unlock_distance}**, "
            f"missing {pieces}, demand 0"
        )
    out.extend(_section(f"Closest-to-unlock — top {len(top)} (highest-leverage)", top_lines))

    impossible_lines = [
        f"- `{u.from_node_id}` --{u.relation}--> `{u.to_node_id}` — {u.reason or 'structurally impossible'}"
        for u in impossible[:top_n]
    ]
    if len(impossible) > top_n:
        impossible_lines.append(f"- … and {len(impossible) - top_n} more")
    out.extend(_section("Structurally impossible (correct negatives — not roadmap items)", impossible_lines))

    return "\n".join(out) + "\n"


def build_todo_lines(entries: list[UnlockEntry], top_n: int) -> list[str]:
    """Build canonical ``- [ ] [SCRIPT] P2.`` roadmap todo lines for the N
    closest-to-unlock edges (lowest unlock_distance first).

    Idempotent-append responsibility lives in the emitter (it dedups against
    the tracker); this only formats the lines deterministically.
    """
    roadmap = [u for u in entries if u.unlock_distance is not None]
    lines: list[str] = []
    for u in roadmap[:top_n]:
        pieces = ", ".join(u.missing_pieces)
        edge = f"{u.from_node_id} --{u.relation}--> {u.to_node_id}"
        reason = u.reason.strip() or "(no reason recorded)"
        lines.append(
            f"- [ ] [SCRIPT] P2. **unlock {edge}** (distance {u.unlock_distance}, status {u.status}) — "
            f"missing: {pieces}. Why blocked: {reason}. "
            f"(auto-emitted by generate_capability_unlock_report.py)"
        )
    return lines
