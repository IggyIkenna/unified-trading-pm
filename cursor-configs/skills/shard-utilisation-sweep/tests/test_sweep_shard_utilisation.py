"""Unit tests for the shard-utilisation sweep's SAFETY guards.

Every test here exists because the naive version of the check produced a FALSE orphan
verdict on real 2026-08-20 data. The epic's constraint — "a false orphan verdict could
send someone deleting live data" — makes these the tests that matter most.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "honest-coverage-dump" / "scripts"))


@pytest.fixture
def mod():
    import sweep_shard_utilisation as m

    return m


class _Reg:
    """Stand-in for _Registries with exactly the fields the verdict helpers read."""

    def __init__(self, venues=None, dt_by_ag_itype=None, chains=None, errors=None):
        self.venue_to_asset_group = venues
        self.valid_dt_by_ag_itype = dt_by_ag_itype
        self.known_chains = chains
        self.import_errors = errors or {}


class TestVenueBareVsGluedGuard:
    def test_bare_defi_venue_matching_a_glued_key_is_consumed(self, mod) -> None:
        """AAVE_V3 carried 58 live cells while VENUE_TO_ASSET_GROUP keys only
        AAVE_V3-ETHEREUM etc. Calling that an orphan is the exact false verdict this
        tool must never emit."""
        reg = _Reg(venues={"AAVE_V3-ETHEREUM": "defi", "AAVE_V3-BASE": "defi"})
        verdict, why = mod._venue_verdict("AAVE_V3", reg)
        assert verdict == "consumed"
        assert "GLUED" in why and "cutover" in why

    def test_venue_absent_in_both_forms_is_not_consumed(self, mod) -> None:
        reg = _Reg(venues={"AAVE_V3-ETHEREUM": "defi"})
        verdict, _ = mod._venue_verdict("TOTALLY_UNKNOWN", reg)
        assert verdict == "not_consumed"

    def test_blank_venue_is_unverified_never_an_orphan(self, mod) -> None:
        reg = _Reg(venues={"X": "cefi"})
        verdict, why = mod._venue_verdict("", reg)
        assert verdict == "unverified"
        assert "writer defect" in why

    def test_missing_registry_is_unverified_never_not_consumed(self, mod) -> None:
        reg = _Reg(venues=None, errors={"venue": "ImportError: boom"})
        verdict, _ = mod._venue_verdict("ANYTHING", reg)
        assert verdict == "unverified"


class TestDisjointVocabularyGuard:
    def test_asset_group_absent_from_registry_is_unverified(self, mod) -> None:
        """DeFi has ZERO entries in VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE, yet is the
        most-captured asset_group. Absence there proves nothing."""
        reg = _Reg(dt_by_ag_itype={("cefi", "perpetual"): frozenset({"trades"})})
        verdict, why = mod._verdict_against_vocab("defi", "lst", "instrument_type", reg, {"lst", "pool"})
        assert verdict == "unverified"
        assert "NO instrument_type vocabulary" in why

    def test_largely_disjoint_vocabularies_are_unverified(self, mod) -> None:
        """Sports: registry holds odds-SHAPE types, manifest holds ~84 MARKET types, sharing
        only 'odds'. One coincidental token must not condemn the other 83."""
        reg = _Reg(
            dt_by_ag_itype={
                ("sports", "odds"): frozenset({"odds"}),
                ("sports", "prop"): frozenset({"odds"}),
            }
        )
        manifest = {"odds", "match_odds", "over_under_2_5", "asian_handicap", "soccer_epl"}
        verdict, why = mod._verdict_against_vocab("sports", "MATCH_ODDS", "instrument_type", reg, manifest)
        assert verdict == "unverified"
        assert "%" in why and "different naming systems" in why

    def test_well_covered_vocabulary_makes_absence_meaningful(self, mod) -> None:
        """cefi's registry covers 100% of what the manifest carries, so a genuinely absent
        value IS a real finding — the guard must not suppress those too."""
        reg = _Reg(
            dt_by_ag_itype={
                ("cefi", "perpetual"): frozenset({"trades"}),
                ("cefi", "spot_pair"): frozenset({"trades"}),
            }
        )
        manifest = {"perpetual", "spot_pair", "nan"}
        verdict, why = mod._verdict_against_vocab("cefi", "nan", "instrument_type", reg, manifest)
        assert verdict == "not_consumed"
        assert "meaningful" in why

    def test_value_present_in_registry_is_consumed(self, mod) -> None:
        reg = _Reg(dt_by_ag_itype={("cefi", "perpetual"): frozenset({"trades"})})
        verdict, _ = mod._verdict_against_vocab("cefi", "PERPETUAL", "instrument_type", reg, {"perpetual"})
        assert verdict == "consumed", "matching must be case-insensitive"


class TestChainVerdictNeverCondemns:
    def test_chain_outside_known_chains_is_unverified_not_orphan(self, mod) -> None:
        """10 chains carrying 46,698 manifest rows sit outside KNOWN_CHAINS. That set governs
        venue-suffix SPLITTING, which is not the same question — so this must never read as
        an orphan."""
        reg = _Reg(chains=frozenset({"ETHEREUM"}))
        verdict, why = mod._chain_verdict("STARKNET", reg)
        assert verdict == "unverified"
        assert "UAC must rule" in why

    def test_empty_chain_is_consumed_axis_inapplicable(self, mod) -> None:
        reg = _Reg(chains=frozenset({"ETHEREUM"}))
        verdict, why = mod._chain_verdict("", reg)
        assert verdict == "consumed"
        assert "inapplicable" in why


class TestReportShape:
    def test_sweep_never_emits_a_delete_suggestion(self, mod) -> None:
        payload = {
            "date": "2026-08-20",
            "by_venue_instrument_type_data_type": {
                "cefi": {"BINANCE": {"PERPETUAL": {"trades": {"captured": 1, "total": 1}}}}
            },
            "by_chain": {"cefi": {"": {"captured": 1, "total": 1}}},
        }
        report = mod.sweep(payload)
        blob = str(report).lower()
        assert "delete" not in blob or "never emits a delete" in report["safety"].lower()
        assert report["safety"].startswith("CONSUMPTION VERDICT ONLY")
        for axis in ("venue", "data_type", "instrument_type", "chain"):
            assert axis in report["axes"]
            for row in report["axes"][axis].values():
                assert row["verdict"] in {"consumed", "not_consumed", "unverified"}
