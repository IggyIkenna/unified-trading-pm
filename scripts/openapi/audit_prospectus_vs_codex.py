"""Two-sided audit: capability manifest / ARCHETYPE_CAPABILITY_REGISTRY vs codex docs.

Audits:
  (a) StrategyArchetype enum values with NO codex doc
  (b) Codex docs with no enum entry (orphan docs)
  (c) Venue-category / instrument claims in codex frontmatter that contradict
      ARCHETYPE_CAPABILITY_REGISTRY (only clear structured contradictions,
      not prose ambiguity)

Outputs:
  unified-api-contracts/openapi/prospectus/prospectus-codex-audit.md (deterministic)

Side effects:
  - Contradictions (c) → appended to
      plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md
    numbered from F15 upwards
  - Enum-without-doc + doc-without-enum → appended to
      plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md

Usage:
    python audit_prospectus_vs_codex.py [--output-dir PATH] \
        [--workspace-root PATH] [--uac-root PATH] [--no-side-effects]

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md Phase 3
"""

from __future__ import annotations

import os

os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("MOCK_STATE_MODE", "deterministic")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("PUBSUB_EMULATOR_HOST", "localhost:8085")
os.environ.setdefault("STORAGE_EMULATOR_HOST", "http://localhost:4443")
os.environ.setdefault("BIGQUERY_EMULATOR_HOST", "localhost:9050")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("API_KEY", "mock-api-key-for-openapi-gen")

import argparse
import logging
import re
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _prospectus_codex import (
    _archetype_id_to_filename,
    archetype_id_from_stem,
    list_all_codex_docs,
    load_codex_doc,
    parse_frontmatter,
)
from unified_api_contracts.internal.architecture_v2.enums import StrategyArchetype

_CAPABILITY_REGISTRY_DICT: dict = {}  # type: ignore[type-arg]
_REGISTRY_AVAILABLE = False
try:
    from unified_api_contracts.internal.architecture_v2.archetype_capability import (
        ARCHETYPE_CAPABILITY_REGISTRY as _RAW_REGISTRY,
    )

    _CAPABILITY_REGISTRY_DICT = {item.archetype_id: item for item in _RAW_REGISTRY}
    _REGISTRY_AVAILABLE = True
except Exception as _exc:
    logger.warning("ARCHETYPE_CAPABILITY_REGISTRY unavailable: %s", _exc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_KNOWN_VENUE_CATEGORY_KEYWORDS = {
    "CEFI": ["cefi", "cex", "binance", "bybit", "okx", "kraken", "coinbase", "deribit", "bitmex"],
    "DEFI": ["defi", "dex", "uniswap", "curve", "aave", "compound", "lido", "jito", "drift", "jupiter"],
    "SPORTS": ["sports", "betfair", "sportradar", "smarkets", "betdaq"],
    "TRADFI": ["tradfi", "ibkr", "interactive_brokers", "nasdaq", "nyse"],
    "PREDICTION": ["prediction", "polymarket", "kalshi", "manifold"],
}


def _detect_venue_categories_from_codex(
    frontmatter: dict[str, str],
    body: str,
) -> set[str]:
    """Detect which venue categories are mentioned in codex frontmatter/body.

    Looks at venue_universe field and family field for clear structured claims.
    """
    detected: set[str] = set()
    venue_universe = frontmatter.get("venue_universe", "").lower()
    family = frontmatter.get("family", "").lower()

    text_to_check = (venue_universe + " " + family + " " + body[:2000]).lower()
    for category, keywords in _KNOWN_VENUE_CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_to_check:
                detected.add(category)
                break

    return detected


def _get_registry_venue_categories(archetype_id: str) -> set[str]:
    """Return venue categories from ARCHETYPE_CAPABILITY_REGISTRY for the archetype."""
    if not _REGISTRY_AVAILABLE:
        return set()
    capability = _CAPABILITY_REGISTRY_DICT.get(StrategyArchetype(archetype_id))
    if capability is None:
        return set()
    return {str(getattr(cell, "asset_group", "")) for cell in capability.cells}


# ---------------------------------------------------------------------------
# Audit computation
# ---------------------------------------------------------------------------

AuditResult = dict[str, object]  # type: ignore[type-arg]


def run_audit() -> dict[str, object]:  # type: ignore[type-arg]
    """Execute the two-sided audit and return structured results."""
    all_archetype_ids = [str(a) for a in sorted(StrategyArchetype)]
    all_codex_stems = list_all_codex_docs()

    # (a) Enum values with no codex doc
    enum_without_doc: list[str] = []
    for archetype_id in all_archetype_ids:
        doc = load_codex_doc(archetype_id)
        if doc is None:
            enum_without_doc.append(archetype_id)

    # (b) Codex docs with no enum entry
    enum_ids_set = {str(a) for a in StrategyArchetype}
    doc_without_enum: list[str] = []
    for stem in all_codex_stems:
        mapped_id = archetype_id_from_stem(stem)
        if mapped_id not in enum_ids_set:
            doc_without_enum.append(stem)

    # (c) Venue-category contradictions
    contradictions: list[dict[str, str]] = []  # type: ignore[type-arg]
    for archetype_id in all_archetype_ids:
        doc = load_codex_doc(archetype_id)
        if doc is None:
            continue  # (a) handles this

        frontmatter = parse_frontmatter(doc)
        body = doc[doc.find("---", 1) + 3 :].strip() if "---" in doc[1:] else doc

        codex_categories = _detect_venue_categories_from_codex(frontmatter, body)
        registry_categories = _get_registry_venue_categories(archetype_id)

        if not registry_categories:
            # Can't contradict what's not registered
            continue

        # Only flag CEFI/DEFI/SPORTS conflicts — the strongest signal
        # where codex claims a category that registry explicitly excludes
        # (must be in registry to be a contradiction, not just absence in registry)
        for cat in ["CEFI", "DEFI", "SPORTS", "TRADFI", "PREDICTION"]:
            codex_claims = cat in codex_categories
            registry_claims = cat in registry_categories

            # Only contradictions, not gaps:
            # codex says yes, registry says absolutely not (i.e. venue_universe in
            # frontmatter explicitly lists venues of that category, but registry
            # has NO cells with that category in ARCHETYPE_CAPABILITY_REGISTRY)
            venue_universe = frontmatter.get("venue_universe", "")
            # Verify codex_claims is from venue_universe (structured) not just body prose
            if (
                codex_claims
                and not registry_claims
                and venue_universe
                and any(kw in venue_universe.lower() for kw in _KNOWN_VENUE_CATEGORY_KEYWORDS.get(cat, []))
            ):
                contradictions.append(
                    {
                        "archetype_id": archetype_id,
                        "category": cat,
                        "codex_claim": f"venue_universe field references {cat} venues: {venue_universe[:100]}",
                        "registry_says": f"ARCHETYPE_CAPABILITY_REGISTRY has no {cat} capability cells",
                        "severity": "WARNING",
                    }
                )

    # With codex doc
    with_codex_doc = [a for a in all_archetype_ids if load_codex_doc(a) is not None]

    return {
        "enum_without_doc": sorted(enum_without_doc),
        "doc_without_enum": sorted(doc_without_enum),
        "contradictions": sorted(contradictions, key=lambda c: c["archetype_id"]),
        "total_archetype_ids": len(all_archetype_ids),
        "total_codex_docs": len(all_codex_stems),
        "with_codex_doc": sorted(with_codex_doc),
        "registry_available": _REGISTRY_AVAILABLE,
    }


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------


def render_audit_report(result: dict[str, object]) -> str:  # type: ignore[type-arg]
    """Render the audit report as a markdown document."""
    enum_without_doc: list[str] = result["enum_without_doc"]  # type: ignore[assignment]
    doc_without_enum: list[str] = result["doc_without_enum"]  # type: ignore[assignment]
    contradictions: list[dict[str, str]] = result["contradictions"]  # type: ignore[assignment]
    total_archetype_ids: int = result["total_archetype_ids"]  # type: ignore[assignment]
    total_codex_docs: int = result["total_codex_docs"]  # type: ignore[assignment]
    with_codex_doc: list[str] = result["with_codex_doc"]  # type: ignore[assignment]
    registry_available: bool = result["registry_available"]  # type: ignore[assignment]

    lines: list[str] = []
    lines.append("# Prospectus vs Codex Two-Sided Audit")
    lines.append("")
    lines.append(
        "_Machine-generated audit — deterministic output. Do not hand-edit; re-run `audit_prospectus_vs_codex.py`._"
    )
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|---|---|")
    lines.append(f"| StrategyArchetype enum values | {total_archetype_ids} |")
    lines.append(f"| Codex archetype docs in `archetypes/` | {total_codex_docs} |")
    lines.append(f"| Archetypes with codex doc | {len(with_codex_doc)} |")
    lines.append(f"| Archetypes WITHOUT codex doc (a) | {len(enum_without_doc)} |")
    lines.append(f"| Codex docs WITHOUT enum entry (b) | {len(doc_without_enum)} |")
    lines.append(f"| Venue-category contradictions (c) | {len(contradictions)} |")
    lines.append(
        f"| ARCHETYPE_CAPABILITY_REGISTRY available | {'yes' if registry_available else 'no — audit (c) skipped'} |"
    )
    lines.append("")

    # Section (a)
    lines.append("## (a) StrategyArchetype Enum Values WITHOUT Codex Doc")
    lines.append("")
    if enum_without_doc:
        lines.append("These archetypes exist in the enum but have no hand-authored codex doc.")
        lines.append("Prospectuses are generated machine-only for these.")
        lines.append("")
        for a in enum_without_doc:
            expected_file = _archetype_id_to_filename(a)
            lines.append(f"- `{a}` — expected file: `codex/09-strategy/architecture-v2/archetypes/{expected_file}`")
    else:
        lines.append("_All enum values have codex docs._")
    lines.append("")

    # Section (b)
    lines.append("## (b) Codex Docs WITHOUT StrategyArchetype Enum Entry (Orphan Docs)")
    lines.append("")
    if doc_without_enum:
        lines.append(
            "These files exist in the archetypes codex directory but have no corresponding "
            "StrategyArchetype enum value. They are either:"
        )
        lines.append("- Stale docs for deleted/renamed archetypes, or")
        lines.append("- New archetypes authored in codex but not yet added to the enum.")
        lines.append("")
        for stem in doc_without_enum:
            lines.append(f"- `{stem}.md` (would map to `{archetype_id_from_stem(stem)}`)")
    else:
        lines.append("_All codex docs have matching enum entries._")
    lines.append("")

    # Section (c)
    lines.append("## (c) Venue-Category / Instrument Contradictions")
    lines.append("")
    if not registry_available:
        lines.append(
            "> ARCHETYPE_CAPABILITY_REGISTRY was not importable on this host. Contradiction audit (c) was skipped."
        )
    elif contradictions:
        lines.append(
            "These are CLEAR STRUCTURED contradictions between the codex "
            "`venue_universe` frontmatter field and ARCHETYPE_CAPABILITY_REGISTRY. "
            "Prose-only ambiguity is excluded."
        )
        lines.append("")
        lines.append("| Archetype | Category | Codex Claims | Registry Says | Severity |")
        lines.append("|---|---|---|---|---|")
        for c in contradictions:
            lines.append(
                f"| `{c['archetype_id']}` | {c['category']} "
                f"| {c['codex_claim'][:80]} "
                f"| {c['registry_says'][:80]} "
                f"| {c['severity']} |"
            )
    else:
        lines.append(
            "_No clear structured venue-category contradictions found. "
            "(Codex frontmatter venue_universe aligns with ARCHETYPE_CAPABILITY_REGISTRY.)_"
        )
    lines.append("")

    # Full with-codex inventory
    lines.append("## Archetypes With Codex Doc (full inventory)")
    lines.append("")
    for a in with_codex_doc:
        lines.append(f"- `{a}`")
    lines.append("")

    # Provenance
    lines.append("## Audit Provenance")
    lines.append("")
    lines.append("- Generated by: `scripts/openapi/audit_prospectus_vs_codex.py` (unified-trading-pm)")
    lines.append("- Codex dir: `codex/09-strategy/architecture-v2/archetypes/`")
    lines.append(
        "- Registry: `unified_api_contracts.internal.architecture_v2"
        ".archetype_capability.ARCHETYPE_CAPABILITY_REGISTRY`"
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Side effects: findings + gap tracker append
# ---------------------------------------------------------------------------

_PM_ROOT = _SCRIPT_DIR.parent.parent


def _append_findings(
    findings_path: Path,
    contradictions: list[dict[str, str]],  # type: ignore[type-arg]
) -> int:
    """Append contradiction findings to findings tracker; return number of findings added."""
    if not contradictions:
        return 0
    if not findings_path.exists():
        logger.warning("Findings file not found: %s — skipping side effect", findings_path)
        return 0

    # Find current highest F-number
    text = findings_path.read_text(encoding="utf-8")
    existing = re.findall(r"F(\d+):", text)
    next_n = max((int(n) for n in existing), default=14) + 1

    new_lines: list[str] = ["\n"]
    new_lines.append("<!-- AUDIT CONTRADICTION FINDINGS (auto-appended by audit_prospectus_vs_codex.py) -->")
    new_lines.append("")

    for c in contradictions:
        new_lines.append(f"**F{next_n}:** Venue-category contradiction — `{c['archetype_id']}`")
        new_lines.append("")
        new_lines.append(f"- Codex frontmatter `venue_universe` claims: {c['codex_claim']}")
        new_lines.append(f"- ARCHETYPE_CAPABILITY_REGISTRY says: {c['registry_says']}")
        new_lines.append(
            f"- Action: Update codex frontmatter OR add capability cells to registry. Severity: {c['severity']}"
        )
        new_lines.append("")
        next_n += 1

    with open(findings_path, "a", encoding="utf-8") as f:
        f.write("\n".join(new_lines))

    return len(contradictions)


def _append_gap_tracker(
    gap_path: Path,
    enum_without_doc: list[str],
    doc_without_enum: list[str],
) -> None:
    """Append enum-without-doc and doc-without-enum entries to the gap tracker."""
    if not gap_path.exists():
        logger.warning("Gap tracker not found: %s — skipping side effect", gap_path)
        return

    new_lines: list[str] = ["\n"]
    new_lines.append("<!-- GAP ENTRIES: two-sided audit (auto-appended by audit_prospectus_vs_codex.py) -->")
    new_lines.append("")
    new_lines.append("### Archetype Doc Coverage Gaps (from two-sided audit)")
    new_lines.append("")

    if enum_without_doc:
        new_lines.append("#### Enum-without-doc (no codex archetype doc)")
        new_lines.append("")
        for a in enum_without_doc:
            fname = _archetype_id_to_filename(a)
            new_lines.append(
                f"- `{a}` | taxonomy: `missing_extraction` | expected: `archetypes/{fname}` | action: author codex doc"
            )
        new_lines.append("")

    if doc_without_enum:
        new_lines.append("#### Doc-without-enum (orphan codex docs)")
        new_lines.append("")
        for stem in doc_without_enum:
            new_lines.append(
                f"- `{stem}.md` | taxonomy: `logical_dead_end` | "
                f"would-map-to: `{archetype_id_from_stem(stem)}` | "
                "action: add enum value OR delete stale doc"
            )
        new_lines.append("")

    with open(gap_path, "a", encoding="utf-8") as f:
        f.write("\n".join(new_lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Two-sided audit: manifest/registry vs codex docs")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--workspace-root", type=Path, default=None)
    parser.add_argument("--uac-root", type=Path, default=None)
    parser.add_argument(
        "--no-side-effects",
        action="store_true",
        help="Skip appending to findings/gap tracker files",
    )
    args = parser.parse_args()

    workspace_root = args.workspace_root or _SCRIPT_DIR.parent.parent.parent
    uac_root = args.uac_root or (workspace_root / "unified-api-contracts")
    output_dir = args.output_dir or (uac_root / "openapi" / "prospectus")
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_audit()

    # Render report
    report = render_audit_report(result)
    out_path = output_dir / "prospectus-codex-audit.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("Audit report written to %s", out_path)

    # Side effects
    if not args.no_side_effects:
        findings_path = _PM_ROOT / "plans" / "active" / "issues" / "capability_wizard_analysis_findings_2026_06_11.md"
        gap_path = _PM_ROOT / "plans" / "active" / "issues" / "capability_wizard_gap_discovery_2026_06_11.md"

        contradictions: list[dict[str, str]] = result["contradictions"]  # type: ignore[assignment]
        n_added = _append_findings(findings_path, contradictions)
        if n_added:
            logger.info("Appended %d contradiction findings to %s", n_added, findings_path)

        enum_without_doc: list[str] = result["enum_without_doc"]  # type: ignore[assignment]
        doc_without_enum: list[str] = result["doc_without_enum"]  # type: ignore[assignment]
        if enum_without_doc or doc_without_enum:
            _append_gap_tracker(gap_path, enum_without_doc, doc_without_enum)
            logger.info("Gap tracker updated: %s", gap_path)

    # Print summary
    print("\n" + "=" * 60)
    print("AUDIT SUMMARY")
    print("=" * 60)
    print(f"Total archetypes (enum): {result['total_archetype_ids']}")
    print(f"Total codex docs:        {result['total_codex_docs']}")
    print(f"With codex doc:          {len(result['with_codex_doc'])}")  # type: ignore[arg-type]
    print(f"(a) Enum without doc:    {len(result['enum_without_doc'])}")  # type: ignore[arg-type]
    print(f"(b) Doc without enum:    {len(result['doc_without_enum'])}")  # type: ignore[arg-type]
    print(f"(c) Contradictions:      {len(result['contradictions'])}")  # type: ignore[arg-type]
    print(f"\nReport: {out_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
