#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Shard-utilisation / orphan sweep — a CONSUMPTION verdict per declared axis value.

Answers the direction the existing orphan sweeps do NOT: they walk GCS and ask "is this
stored object manifested?" (``instruments-service/scripts/migration_orphan_sweep.py``,
``market-data-processing-service/scripts/candle_orphan_sweep.py``, and MTDS's sports fork).
This asks the opposite — **"is this manifested axis value consumed by anything?"** — which
is the epic's own definition-of-done item (/plans/epics/system_readiness_master.md, the
`[SKILL] P1` "Shard utilisation / orphan sweep": *every declared data_type, instrument_type,
venue and chain consumed somewhere*).

SAFETY — this tool emits a CONSUMPTION VERDICT ONLY and NEVER a delete suggestion.
That is the epic's explicit constraint and it is not a style preference: a false orphan
verdict could send someone deleting live data. Two rules follow from it and are enforced
throughout:

1. **READ the consumer, never infer from a grep count.** Consumers here are resolved by
   IMPORTING the real registry and asking it (``VENUE_TO_ASSET_GROUP``,
   ``VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE``, ``KNOWN_CHAINS``, …). A token grep
   cannot see a runtime-resolved consumer, and this workspace has already been bitten by
   exactly that (CLAIM <= MEASUREMENT: 0 hits != missing).
2. **Print ``unverified`` when uncertain.** An axis whose consumer registry cannot be
   imported, or whose consumption is genuinely runtime-resolved, is reported ``unverified``
   — never silently downgraded to "not consumed". An absent capability and an unchecked
   one are different findings.

Enumeration reuses ``shard_universe.py`` — the SAME engine the honest-coverage and
readiness dumps share — per the epic's consistency constraint: "a third independent
enumeration would disagree on the denominator, which is worse than being slower."

Usage (needs a venv carrying BOTH unified_api_contracts and unified_trading_library —
instruments-service's, same as the sibling dumps; see SKILL.md)::

    python sweep_shard_utilisation.py                 # latest coverage.json
    python sweep_shard_utilisation.py --date 2026-08-19
    python sweep_shard_utilisation.py --json          # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Literal

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parents[1] / "honest-coverage-dump" / "scripts"))

from shard_universe import (
    DEFAULT_PROJECT_ID,
    CoverageReadError,
    iter_shard_cells,
    load_coverage,
)

Verdict = Literal["consumed", "not_consumed", "unverified"]

#: Verdict ordering for display — findings first, so a long "consumed" tail never buries
#: the two rows that actually need a human.
_VERDICT_ORDER: dict[str, int] = {"not_consumed": 0, "unverified": 1, "consumed": 2}

#: Minimum share of an asset_group's OBSERVED vocabulary the registry must cover before a
#: missing value counts as ``not_consumed`` rather than ``unverified``. Below this, the two
#: are different naming systems and absence proves nothing — see _verdict_against_vocab.
#: 0.5 is deliberately blunt: the measured populations are not near it (cefi 100%,
#: sports ~1%), so a precise threshold would be false precision.
_VOCAB_OVERLAP_MIN: float = 0.5


class _Registries:
    """The real consumer registries, imported once.

    Every attribute is either the live registry object or ``None``. ``None`` NEVER means
    "nothing consumes this" — it means "this axis could not be checked", and every value
    on that axis is reported ``unverified``.
    """

    def __init__(self) -> None:
        self.venue_to_asset_group: dict[str, str] | None = None
        self.valid_dt_by_ag_itype: dict[tuple[str, str], frozenset[str]] | None = None
        self.known_chains: frozenset[str] | None = None
        self.import_errors: dict[str, str] = {}

        try:
            from unified_api_contracts import VENUE_TO_ASSET_GROUP

            self.venue_to_asset_group = dict(VENUE_TO_ASSET_GROUP)
        except Exception as exc:  # registry genuinely unavailable in this venv
            self.import_errors["venue"] = f"{type(exc).__name__}: {exc}"

        try:
            from unified_api_contracts.registry.market_data_categories import (
                VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE,
            )

            self.valid_dt_by_ag_itype = dict(VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE)
        except Exception as exc:
            self.import_errors["data_type"] = f"{type(exc).__name__}: {exc}"
            self.import_errors["instrument_type"] = f"{type(exc).__name__}: {exc}"

        try:
            from unified_api_contracts.registry.capability_declarations._defi import KNOWN_CHAINS

            self.known_chains = frozenset(KNOWN_CHAINS)
        except Exception as exc:
            self.import_errors["chain"] = f"{type(exc).__name__}: {exc}"


def _venue_verdict(venue: str, reg: _Registries) -> tuple[Verdict, str]:
    if reg.venue_to_asset_group is None:
        return "unverified", f"VENUE_TO_ASSET_GROUP unavailable ({reg.import_errors.get('venue', '?')})"
    if not venue:
        # A blank venue is a real defect, but it is a WRITER defect, not an orphan — and
        # calling it "not consumed" would invite exactly the delete this tool forbids.
        return "unverified", "blank venue in the manifest — writer defect, not an orphan verdict"
    if venue in reg.venue_to_asset_group:
        return "consumed", "declared in VENUE_TO_ASSET_GROUP"
    # DeFi bare-vs-glued naming cutover. A bare membership test produced 95 FALSE
    # "not consumed" verdicts on the 2026-08-20 payload — including AAVE_V3, LIDO, MORPHO
    # and ETHERFI, each carrying 50+ live shard cells. Measured cause: the registry keys
    # DeFi venues in the GLUED PROTOCOL-CHAIN form (135 of its 209 entries are DeFi and
    # every one is glued, e.g. AAVE_V3-ETHEREUM) while the manifest writer emits the BARE
    # protocol in `venue` with the chain in its own column. The two sit on opposite sides
    # of the venue/chain canonicalisation cutover. A bare venue prefixing ANY glued key is
    # CONSUMED; the mismatch is its own finding, never an orphan verdict.
    glued = sorted(k for k in reg.venue_to_asset_group if k.startswith(f"{venue}-"))
    if glued:
        return "consumed", (
            f"registry keys this venue in the GLUED PROTOCOL-CHAIN form ({len(glued)} entries, "
            f"e.g. {glued[0]}) while the manifest carries the bare protocol — consumed, but "
            "registry and manifest are on opposite sides of the venue/chain canonicalisation "
            "cutover, which is its own finding"
        )
    return "not_consumed", "absent from VENUE_TO_ASSET_GROUP in either bare or glued form — no declared owner"


def _chain_verdict(chain: str, reg: _Registries) -> tuple[Verdict, str]:
    if reg.known_chains is None:
        return "unverified", f"KNOWN_CHAINS unavailable ({reg.import_errors.get('chain', '?')})"
    if not chain:
        return "consumed", "empty chain = axis inapplicable for this asset_group (cefi/tradfi/sports/prediction)"
    if chain in reg.known_chains:
        return "consumed", "in UAC KNOWN_CHAINS"
    # NOT a delete signal. KNOWN_CHAINS governs venue-suffix SPLITTING, which is not
    # necessarily the same population as "chains the manifest may legitimately carry".
    return (
        "unverified",
        "carries manifest rows but is absent from KNOWN_CHAINS — every "
        "`if chain in KNOWN_CHAINS:` consumer takes the else-branch for it. Whether that is "
        "correct depends on what KNOWN_CHAINS is meant to be (it governs venue-suffix "
        "splitting); UAC must rule before this is called an orphan",
    )


def _registry_vocab(reg: _Registries, ag: str, axis: Literal["data_type", "instrument_type"]) -> set[str]:
    """The registry's case-folded vocabulary for one (asset_group, axis)."""
    out: set[str] = set()
    if reg.valid_dt_by_ag_itype is None:
        return out
    for (reg_ag, reg_itype), dts in reg.valid_dt_by_ag_itype.items():
        if reg_ag != ag:
            continue
        if axis == "instrument_type":
            out.add(str(reg_itype).strip().casefold())
        else:
            out.update(str(d).strip().casefold() for d in dts)
    return out


def _verdict_against_vocab(
    ag: str,
    value: str,
    axis: Literal["data_type", "instrument_type"],
    reg: _Registries,
    manifest_vocab: set[str],
) -> tuple[Verdict, str]:
    """Verdict for one axis value, with the DISJOINT-VOCABULARY guard.

    The guard is the whole reason this function is not a one-line membership test, and it
    exists because the naive version produced a wall of FALSE orphan verdicts on the
    2026-08-19 payload — precisely the failure the epic's safety constraint names.

    Two ways a bare "absent from the registry" answer lies:

    * **The registry does not model this asset_group at all.** ``defi`` has ZERO entries in
      ``VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE``, so every DeFi value would read
      "not consumed" while DeFi is plainly the most-captured asset_group in the corpus.
    * **The registry models it under a DIFFERENT vocabulary.** ``sports`` declares 5
      odds-SHAPE types (``odds``, ``fixed_odds``, ``exchange_odds``, ``fixture``, ``prop``)
      while the manifest's sports ``instrument_type`` carries MARKET types
      (``MATCH_ODDS``, ``OVER_UNDER_2_5``, ``ASIAN_HANDICAP``) and even league/bookmaker
      names (``SOCCER_EPL``, ``ladbrokes_uk``). Those are two naming systems sharing one
      column — a real and serious finding, but NOT evidence that nothing consumes them.

    So: if the registry has no vocabulary for this asset_group, or its vocabulary is
    DISJOINT from what the manifest actually carries, every value on that axis is
    ``unverified`` and the disjointness itself is reported. Only where the two vocabularies
    demonstrably overlap does a missing value become a real ``not_consumed`` candidate.
    """
    if reg.valid_dt_by_ag_itype is None:
        return (
            "unverified",
            f"VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE unavailable ({reg.import_errors.get(axis, '?')})",
        )
    if not value:
        return "unverified", f"blank {axis} — the shard carries no value to check, not an orphan"

    vocab = _registry_vocab(reg, ag, axis)
    if not vocab:
        return "unverified", (
            f"the registry declares NO {axis} vocabulary for asset_group={ag} at all — "
            "it is not the consumer for this asset_group, so absence proves nothing"
        )

    overlap = vocab & manifest_vocab
    if value.strip().casefold() in vocab:
        return "consumed", f"declared for asset_group={ag} in VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE"

    # Overlap must be SUBSTANTIAL before absence means anything. A binary "overlap > 0"
    # test is too weak and still cried wolf: sports' registry vocabulary (5 odds-SHAPE
    # types) shares exactly ``odds`` with a manifest vocabulary of ~80 MARKET types
    # (MATCH_ODDS, OVER_UNDER_2_5, ASIAN_HANDICAP, SOCCER_EPL, ladbrokes_uk), so one
    # coincidental shared token was enough to flag the other ~80 as orphans. Requiring the
    # registry to cover a MAJORITY of what the manifest actually carries separates
    # "the registry models this asset_group, and this value is genuinely missing"
    # (cefi: 7/7 covered — absence is real) from "these are two different naming systems"
    # (sports: ~1/80 — absence proves nothing).
    ratio = len(overlap) / len(manifest_vocab) if manifest_vocab else 0.0
    if ratio < _VOCAB_OVERLAP_MIN:
        return "unverified", (
            f"registry covers only {len(overlap)}/{len(manifest_vocab)} ({ratio:.0%}) of the "
            f"{axis} values asset_group={ag} actually carries — the two vocabularies are "
            "largely different naming systems, so absence is not evidence of an orphan"
        )
    return "not_consumed", (
        f"absent from the registry's asset_group={ag} {axis} vocabulary, which covers "
        f"{len(overlap)}/{len(manifest_vocab)} ({ratio:.0%}) of what the manifest carries — "
        "so absence here is meaningful"
    )


def sweep(payload: dict) -> dict:
    """Build the per-axis consumption verdicts from an already-computed coverage payload."""
    reg = _Registries()
    cells = list(iter_shard_cells(payload))

    # value -> (verdict, why, shard_count, asset_groups)
    axes: dict[str, dict[str, dict]] = {"venue": {}, "data_type": {}, "instrument_type": {}, "chain": {}}
    counts: dict[str, dict[str, int]] = {k: defaultdict(int) for k in axes}
    ags: dict[str, dict[str, set]] = {k: defaultdict(set) for k in axes}

    for c in cells:
        counts["venue"][c.venue] += 1
        ags["venue"][c.venue].add(c.asset_group)
        counts["data_type"][(c.asset_group, c.data_type)] += 1
        counts["instrument_type"][(c.asset_group, c.instrument_type or "")] += 1

    # chain comes from the chain-joined projection when present, else the marginal one.
    chain_src = payload.get("by_venue_instrument_type_data_type_chain") or {}
    if chain_src:
        for ag, venues in chain_src.items():
            for _v, itm in (venues or {}).items():
                for _it, dtm in (itm or {}).items():
                    for _dt, chains in (dtm or {}).items():
                        for ch in chains or {}:
                            counts["chain"][(ag, ch)] += 1
                            ags["chain"][(ag, ch)].add(ag)
    else:
        for ag, chains in (payload.get("by_chain") or {}).items():
            for ch in chains or {}:
                counts["chain"][(ag, ch)] += 1
                ags["chain"][(ag, ch)].add(ag)

    for venue, n in counts["venue"].items():
        v, why = _venue_verdict(venue, reg)
        axes["venue"][venue] = {
            "verdict": v,
            "why": why,
            "shard_cells": n,
            "asset_groups": sorted(ags["venue"][venue]),
        }
    # Per-asset_group manifest vocabularies, needed for the disjointness guard below.
    manifest_vocab: dict[tuple[str, str], set[str]] = defaultdict(set)
    for ag, dt in counts["data_type"]:
        if dt:
            manifest_vocab[(ag, "data_type")].add(dt.strip().casefold())
    for ag, it in counts["instrument_type"]:
        if it:
            manifest_vocab[(ag, "instrument_type")].add(it.strip().casefold())

    for (ag, dt), n in counts["data_type"].items():
        v, why = _verdict_against_vocab(ag, dt, "data_type", reg, manifest_vocab[(ag, "data_type")])
        axes["data_type"][f"{ag}/{dt}"] = {"verdict": v, "why": why, "shard_cells": n, "asset_groups": [ag]}
    for (ag, it), n in counts["instrument_type"].items():
        v, why = _verdict_against_vocab(ag, it, "instrument_type", reg, manifest_vocab[(ag, "instrument_type")])
        axes["instrument_type"][f"{ag}/{it}"] = {"verdict": v, "why": why, "shard_cells": n, "asset_groups": [ag]}
    for (ag, ch), n in counts["chain"].items():
        v, why = _chain_verdict(ch, reg)
        axes["chain"][f"{ag}/{ch}"] = {"verdict": v, "why": why, "shard_cells": n, "asset_groups": [ag]}

    summary = {
        axis: {
            verdict: sum(1 for r in rows.values() if r["verdict"] == verdict)
            for verdict in ("consumed", "not_consumed", "unverified")
        }
        for axis, rows in axes.items()
    }
    return {
        "generated_from": {
            "date": payload.get("date"),
            "generated_at": payload.get("generated_at"),
            "schema_version": payload.get("schema_version"),
        },
        "shard_cells_enumerated": len(cells),
        "chain_axis_source": "chain-joined projection" if chain_src else "by_chain (marginal — coarser)",
        "registry_import_errors": reg.import_errors,
        "summary": summary,
        "axes": axes,
        "safety": "CONSUMPTION VERDICT ONLY — this tool never emits a delete suggestion.",
    }


def _print_human(report: dict, gcs_path: str) -> None:
    print(f"Shard-utilisation sweep -- source: {gcs_path}")
    print(
        f"Shard cells enumerated: {report['shard_cells_enumerated']}  (chain axis from: {report['chain_axis_source']})"
    )
    if report["registry_import_errors"]:
        print("\n!! Registry imports FAILED — those axes report `unverified`, never `not_consumed`:")
        for axis, err in report["registry_import_errors"].items():
            print(f"   {axis}: {err}")
    print("\n=== Summary (findings first) ===")
    for axis, s in report["summary"].items():
        print(
            f"  {axis:<16} consumed={s['consumed']:<5} not_consumed={s['not_consumed']:<5} unverified={s['unverified']}"
        )

    for axis, rows in report["axes"].items():
        flagged = {k: v for k, v in rows.items() if v["verdict"] != "consumed"}
        if not flagged:
            print(f"\n=== {axis}: every value consumed ===")
            continue
        print(f"\n=== {axis}: {len(flagged)} value(s) needing attention ===")
        for key, r in sorted(flagged.items(), key=lambda kv: (_VERDICT_ORDER[kv[1]["verdict"]], -kv[1]["shard_cells"])):
            print(f"  [{r['verdict']:<13}] {key:<44} cells={r['shard_cells']:<6} {r['why']}")
    print(f"\n{report['safety']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Per-axis shard CONSUMPTION verdicts (never a delete suggestion).")
    ap.add_argument("--project", default=DEFAULT_PROJECT_ID)
    ap.add_argument("--date", default=None, help="coverage.json date (default: latest available)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args(argv)

    try:
        payload, _resolved, gcs_path = load_coverage(args.project, args.date)
    except CoverageReadError as exc:
        print(f"could not read coverage.json: {exc}", file=sys.stderr)
        return 2

    report = sweep(payload)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_human(report, gcs_path)
    # Exit 0 always: this is a REPORT, not a gate. A non-zero exit here would invite
    # wiring it into CI as a blocker, which the safety constraint forbids.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
