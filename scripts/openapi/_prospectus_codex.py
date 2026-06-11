"""Codex archetype doc loader for the prospectus generator.

Maps StrategyArchetype enum values to their kebab-case codex doc filenames,
reads the doc if it exists, and extracts structured frontmatter + body text.

Filename mapping rule:
  CARRY_STAKED_BASIS          -> carry-staked-basis.md
  ARBITRAGE_MEV_JIT_LIQUIDITY -> arbitrage-mev-jit-liquidity.md
  VOL_TRADING_OPTIONS         -> vol-trading-options.md
  DEFI_LP_CONCENTRATED        -> defi-lp-concentrated.md

Unmapped (doc not found) archetypes are tracked in _UNMAPPED for the audit.

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md Phase 3
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_PM_ROOT = _SCRIPT_DIR.parent.parent
_ARCHETYPES_DIR = _PM_ROOT / "codex" / "09-strategy" / "architecture-v2" / "archetypes"


def _archetype_id_to_filename(archetype_id: str) -> str:
    """Convert CARRY_STAKED_BASIS -> carry-staked-basis.md."""
    return archetype_id.lower().replace("_", "-") + ".md"


def load_codex_doc(archetype_id: str) -> str | None:
    """Return the raw text of the codex archetype doc, or None if not found."""
    filename = _archetype_id_to_filename(archetype_id)
    path = _ARCHETYPES_DIR / filename
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def parse_frontmatter(doc_text: str) -> dict[str, str]:
    """Extract YAML-style frontmatter (between --- delimiters) into a dict.

    Only parses simple ``key: value`` lines; multi-line / list values are
    returned as raw strings.  Returns empty dict if no frontmatter found.
    """
    if not doc_text.startswith("---"):
        return {}
    lines = doc_text.splitlines()
    end = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end < 0:
        return {}
    result: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
    return result


def get_body_text(doc_text: str) -> str:
    """Return the doc body (after frontmatter), stripped of leading blank lines."""
    if not doc_text.startswith("---"):
        return doc_text
    lines = doc_text.splitlines()
    end = -1
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = i
            break
    if end < 0:
        return doc_text
    body_lines = lines[end + 1 :]
    # Drop leading blank lines
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    return "\n".join(body_lines)


def extract_section(body: str, section_heading: str) -> str | None:
    """Extract the text of a single markdown section (## or ###).

    Returns the section body (not including the heading line) or None if
    the heading is not found.  Stops at the next same-or-higher level heading.
    """
    lines = body.splitlines()
    heading_level = len(section_heading.split(" ")[0]) if section_heading.startswith("#") else 2
    target = section_heading.lstrip("#").strip().lower()
    inside = False
    result: list[str] = []
    for line in lines:
        if line.startswith("#"):
            hashes = len(line) - len(line.lstrip("#"))
            title = line.lstrip("#").strip().lower()
            if title == target:
                inside = True
                continue
            if inside and hashes <= heading_level:
                break
        if inside:
            result.append(line)
    if not result:
        return None
    return "\n".join(result).strip()


def get_codex_venue_universe(frontmatter: dict[str, str]) -> list[str]:
    """Extract the ``venue_universe`` list from frontmatter (raw string)."""
    raw = frontmatter.get("venue_universe", "")
    if not raw:
        return []
    # Strip surrounding brackets and split by comma/space
    raw = raw.strip("[]")
    # Handle multi-line (bracket on next line) — just split on comma
    venues: list[str] = [v.strip() for v in raw.replace("\n", "").split(",") if v.strip()]
    return [v for v in venues if not v.startswith("#")]


def list_all_codex_docs() -> list[str]:
    """Return all archetype doc stem names (without .md) in the archetypes dir."""
    if not _ARCHETYPES_DIR.exists():
        return []
    return sorted(p.stem for p in _ARCHETYPES_DIR.glob("*.md") if p.is_file())


def archetype_id_from_stem(stem: str) -> str:
    """Convert kebab-case stem back to UPPER_SNAKE archetype id."""
    return stem.upper().replace("-", "_")
