#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Shared shard-enumeration engine for the honest-coverage-dump and
readiness-state-dump skills (unified-trading-pm/cursor-configs/skills/).

This module owns exactly one job: read the ALREADY-COMPUTED daily
``coverage.json`` artifact (SSOT: /codex/02-data/honest-coverage-model.md)
and expose it as an iterable of per-shard cells, at WHATEVER grain the
artifact currently carries. It never recomputes captured/empty_confirmed/
attempted_failed/expected_unattempted counts, never re-derives the expected
universe, and never walks GCS objects directly -- that machinery already
exists in instruments-service's ``measure_honest_coverage.py`` (Layer 1 +
Layer 2) and this module only reads its output. "Reuse, don't reimplement."

Grain (2-tuple vs 3-tuple) is NOT hardcoded. ``coverage.json``'s schema is
additive (schema_version: 2) and already ships both ``by_venue_data_type``
(the (venue, data_type) grain the registry supports today) and
``by_venue_instrument_type_data_type`` (the (venue, instrument_type,
data_type) grain that lands once the instrument_type axis is added to
VenueCapabilityRecord -- see
/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md
"Land the instrument_type axis"). ``detect_grain()`` below picks whichever
one the payload actually has data in, so both skills re-run at the finer
grain automatically the day it lands -- no code change, no rebuild.

Reads GCS via `unified_trading_library`'s `cloud_interface` ONLY --
`get_storage_client().download_bytes()` for the object body and
`get_storage_client().list_blobs()` for date discovery. A subprocess
`gcloud storage`/`gsutil` call is a HARD BAN workspace-wide (reads
included, not just writes -- it buffers through /tmp and one such call
already OOM'd the orchestrator VM's tmpfs on 2026-08-10; SSOT:
/codex/05-infrastructure/gcs-object-operations.md, enforced live by
`scripts/hooks/block_destructive_commands.py` and at commit time by QG
STEP 5.105 `check_subprocess_gcs_object_cli.py`). This means both CLI
callers of this module need a Python whose venv has
`unified-trading-library` installed -- run them under
instruments-service's `.venv` (it owns `measure_honest_coverage.py`, the
script that WRITES this same coverage.json, so it already carries the
right dependency set). See each skill's SKILL.md for the exact invocation.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

from unified_trading_library import get_storage_client

#: Documented GCP project id for the honest-coverage bucket (see
#: /codex/02-data/honest-coverage-model.md and the "Operator verification
#: recipe" in /codex/02-data/availability-manifest-and-data-status.md, which
#: hardcodes the same id in its own recipe). Override with --project if the
#: environment differs -- this is a default, not an assumption baked into
#: the read path.
DEFAULT_PROJECT_ID = "central-element-323112"

#: The 4-state capture_status ledger, in SSOT order (honest-coverage-model.md
#: § Layer 2). This is the REAL state vocabulary the manifest writer emits;
#: kept as the canonical iteration order everywhere in both skills.
CAPTURE_STATE_FIELDS: tuple[str, ...] = (
    "captured",
    "empty_confirmed",
    "attempted_failed",
    "expected_unattempted",
)

#: Display labels matching the Tuesday-deliverable's own vocabulary
#: (data_pipeline_completion_2026_08_21.md gate B16: "captured, expected-absent,
#: expected-unattempted, not-expected"). B16's prose folds `attempted_failed`
#: into "expected-absent" implicitly by omission; this dump does NOT drop it
#: -- a real attempted-and-failed shard is a distinct, actionable state from a
#: legitimate typed absence, and hiding it would itself be the kind of
#: measurement dishonesty this whole model exists to prevent. So this dump
#: reports all four real fields under B16-recognisable labels, plus
#: "not-expected" as its own row (see NOT_EXPECTED_LABEL below) rather than
#: silently collapsing two real states into one.
DISPLAY_LABELS: dict[str, str] = {
    "captured": "captured",
    "empty_confirmed": "expected-absent",
    "attempted_failed": "attempted-failed",
    "expected_unattempted": "expected-unattempted",
}

#: B16's fourth named state -- tuples OUTSIDE the Layer-1 EXPECTED universe
#: entirely (a venue that cannot produce the data_type, out-of-MVP-scope, a
#: bundle leaf rolled into its parent). These never appear as a manifest row
#: under any capture_status; they are visible only via layer_1's
#: missing/stray bookkeeping. Reported as a separate section, never folded
#: into the 4-state counts, and always excluded from every coverage
#: denominator below (per the honest-coverage-model.md symmetric-inclusion
#: invariant).
NOT_EXPECTED_LABEL = "not-expected"

Grain = Literal["instrument_type", "venue_data_type", "league"]


@dataclass(frozen=True)
class ShardCell:
    """One per-shard coverage cell, at whichever grain the payload supports."""

    asset_group: str
    venue: str
    instrument_type: str | None  # None at the 2-tuple (venue, data_type) grain
    data_type: str
    counts: dict[str, int]  # keyed by CAPTURE_STATE_FIELDS (missing keys => 0)
    # None outside the "league" grain (operator's 2026-08-20 W3 fold-in ruling — see
    # instruments-service/scripts/measure_honest_coverage.py's level-5e block, which is the
    # writer of ``by_venue_instrument_type_data_type_league``, the payload key this grain reads).
    league_id: str | None = None

    def count(self, field: str) -> int:
        return int(self.counts.get(field, 0))

    def reachable_total(self) -> int:
        """Denominator for the SSOT reachable_coverage formula (empty_confirmed excluded)."""
        return self.count("captured") + self.count("attempted_failed") + self.count("expected_unattempted")

    def all_shards_total(self) -> int:
        return self.reachable_total() + self.count("empty_confirmed")


class CoverageReadError(RuntimeError):
    """Raised when coverage.json cannot be located or parsed -- never silently faked."""


def _honest_coverage_bucket(project: str) -> str:
    """Bucket name only (no ``gs://`` scheme) -- matches the literal construction in
    instruments-service/scripts/measure_honest_coverage.py's own ``_OUTPUT_BUCKET``.
    This bucket is a flat, cross-asset-group administrative bucket (a handful of
    date-partitioned objects), outside the per-asset-group `resolve_bucket_name(...)`
    taxonomy -- the same reason the SSOT script itself builds the name this way
    rather than through the resolver."""
    return f"{project}-honest-coverage"


def _client(project: str):
    """``project_id`` is passed explicitly -- the honest-coverage bucket's project
    may differ from whatever ambient GCP_PROJECT_ID the caller's shell happens to
    have set, and get_storage_client() raises if neither is present. Explicit beats
    ambient here, same reasoning as resolve_bucket_name() taking asset_group
    explicitly rather than inferring it."""
    return get_storage_client(project_id=project)


def list_available_dates(project: str = DEFAULT_PROJECT_ID) -> list[str]:
    """List YYYY-MM-DD prefixes present under the honest-coverage bucket, sorted ascending."""
    bucket = _honest_coverage_bucket(project)
    client = _client(project)
    dates: set[str] = set()
    for blob in client.list_blobs(bucket, prefix=""):
        parts = blob.name.split("/", 1)
        looks_like_date = len(parts) == 2 and len(parts[0]) == 10 and parts[0][4] == "-" and parts[0][7] == "-"
        if looks_like_date and parts[1] == "coverage.json":
            dates.add(parts[0])
    return sorted(dates)


def load_coverage(project: str = DEFAULT_PROJECT_ID, date: str | None = None) -> tuple[dict, str, str]:
    """Read coverage.json for ``date`` (latest available if None).

    Returns (payload, resolved_date, gcs_path). Raises CoverageReadError on
    any failure -- this dump reports "could not read coverage.json", it
    never fabricates a payload to keep going.
    """
    bucket = _honest_coverage_bucket(project)
    if date is None:
        dates = list_available_dates(project)
        if not dates:
            raise CoverageReadError(f"No dated coverage.json objects found under bucket {bucket!r}")
        date = dates[-1]
    blob_path = f"{date}/coverage.json"
    gcs_path = f"gs://{bucket}/{blob_path}"
    try:
        raw = _client(project).download_bytes(bucket, blob_path)
    except Exception as exc:  # storage backends raise their own provider-specific errors here
        raise CoverageReadError(f"could not download {gcs_path}: {exc}") from exc
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CoverageReadError(f"{gcs_path} is not valid JSON: {exc}") from exc
    return payload, date, gcs_path


def detect_grain(payload: dict) -> Grain:
    """Pick the finest grain the payload actually has non-empty data at.

    This is the ONLY place grain is decided, and it is decided from the data
    itself -- never from a hardcoded assumption about whether the
    instrument_type axis has landed on VenueCapabilityRecord yet.
    """
    by_vitdl = payload.get("by_venue_instrument_type_data_type_league") or {}
    for ag_block in by_vitdl.values():
        for venue_block in (ag_block or {}).values():
            if venue_block:
                return "league"
    by_vitd = payload.get("by_venue_instrument_type_data_type") or {}
    for ag_block in by_vitd.values():
        for venue_block in (ag_block or {}).values():
            if venue_block:
                return "instrument_type"
    return "venue_data_type"


def iter_shard_cells(payload: dict, grain: Grain | None = None) -> Iterator[ShardCell]:
    """Yield one ShardCell per (asset_group, venue[, instrument_type], data_type) node."""
    resolved_grain: Grain = grain if grain is not None else detect_grain(payload)
    if resolved_grain == "league":
        by_vitdl = payload.get("by_venue_instrument_type_data_type_league") or {}
        for ag, venues in by_vitdl.items():
            for venue, itypes in (venues or {}).items():
                for itype, dtypes in (itypes or {}).items():
                    for dt, leagues in (dtypes or {}).items():
                        for league_id, counts in (leagues or {}).items():
                            yield ShardCell(ag, venue, itype, dt, counts or {}, league_id)
        return

    if resolved_grain == "instrument_type":
        by_vitd = payload.get("by_venue_instrument_type_data_type") or {}
        for ag, venues in by_vitd.items():
            for venue, itypes in (venues or {}).items():
                for itype, dtypes in (itypes or {}).items():
                    for dt, counts in (dtypes or {}).items():
                        yield ShardCell(ag, venue, itype, dt, counts or {})
        return

    by_vd = payload.get("by_venue_data_type") or {}
    for ag, venues in by_vd.items():
        for venue, dtypes in (venues or {}).items():
            for dt, counts in (dtypes or {}).items():
                yield ShardCell(ag, venue, None, dt, counts or {})


@dataclass(frozen=True)
class DedupStats:
    """Cell-count dedup + hollow-fraction stats at the instrument_type grain (FROM-T2 P0,
    code_readiness_t5_readiness_observability_presentations_2026_08_19.md).

    Measured 2026-08-19 (and re-confirmed still present 2026-08-20 -- the writer fix in
    instruments-service/scripts/measure_honest_coverage.py had not yet self-corrected the
    EXISTING artefact by the next nightly cron): a naive `len(list(iter_shard_cells(...)))`
    over-counts by ~2%, because the same shard can appear under two case-variant
    instrument_type keys (e.g. 'ODDS' and 'odds'), and a blank instrument_type key ('') and
    a literal string 'nan' both mean "no instrument_type recorded" but are never collapsed.

    This is COUNT-ONLY -- it does not merge or mutate the underlying per-cell capture-status
    counts (that would risk silently misrepresenting real data if two case-variant entries
    ever genuinely diverge). It answers "how many DISTINCT shards does this payload actually
    describe", not "what are their combined counts".
    """

    raw_cell_count: int
    distinct_cell_count: int
    hollow_instrument_type_count: int
    hollow_by_asset_group: dict[str, tuple[int, int]]  # ag -> (hollow_count, total_count)

    @property
    def duplicate_count(self) -> int:
        return self.raw_cell_count - self.distinct_cell_count

    def hollow_fraction(self, asset_group: str) -> float | None:
        entry = self.hollow_by_asset_group.get(asset_group)
        if entry is None or entry[1] == 0:
            return None
        return entry[0] / entry[1]


def compute_dedup_stats(payload: dict) -> DedupStats:
    """Only meaningful at the instrument_type grain -- the venue_data_type grain has no
    instrument_type axis to collapse or report hollowness on."""
    raw = 0
    distinct: set[tuple[str, str, str, str]] = set()
    hollow_total = 0
    by_ag_hollow: dict[str, list[int]] = {}

    for cell in iter_shard_cells(payload, "instrument_type"):
        raw += 1
        itype_raw = cell.instrument_type or ""
        # Canonical form: case-folded, and 'nan' collapsed onto blank -- both mean "no
        # instrument_type recorded", per the measured finding (26 'nan' keys sat beside 85
        # blank ones, describing the same absence, never previously unified).
        itype_canon = "" if itype_raw.strip().lower() == "nan" else itype_raw.strip().lower()
        dt_canon = cell.data_type.strip().lower()
        distinct.add((cell.asset_group, cell.venue, itype_canon, dt_canon))

        counts = by_ag_hollow.setdefault(cell.asset_group, [0, 0])
        counts[1] += 1
        if itype_canon == "":
            hollow_total += 1
            counts[0] += 1

    return DedupStats(
        raw_cell_count=raw,
        distinct_cell_count=len(distinct),
        hollow_instrument_type_count=hollow_total,
        hollow_by_asset_group={ag: (v[0], v[1]) for ag, v in by_ag_hollow.items()},
    )


def venue_asset_group_map(payload: dict, grain: Grain | None = None) -> dict[str, str]:
    """Build {venue: asset_group} straight from the payload -- no UAC import needed."""
    out: dict[str, str] = {}
    for cell in iter_shard_cells(payload, grain):
        out.setdefault(cell.venue, cell.asset_group)
    return out


def not_expected_tuples(payload: dict, asset_group: str) -> list[dict]:
    """Layer-1 stray/missing tuples for one asset_group -- the NOT_EXPECTED_LABEL section.

    ``missing_tuples`` (EXPECTED but not enumerated -- a real Layer-1 hole,
    not "not-expected") is reported separately and NOT returned here; only
    genuinely out-of-model tuples belong under "not-expected". This dump
    surfaces both, kept distinct, per the honest-coverage-model.md carve-out
    rule: a legitimate absence is never a Layer-1 hole and a Layer-1 hole is
    never a legitimate absence.
    """
    layer1 = (payload.get("layer_1") or {}).get("by_asset_group") or {}
    ag_block = layer1.get(asset_group) or {}
    return list(ag_block.get("stray_tuples") or [])


def missing_tuples(payload: dict, asset_group: str) -> list[dict]:
    layer1 = (payload.get("layer_1") or {}).get("by_asset_group") or {}
    ag_block = layer1.get(asset_group) or {}
    return list(ag_block.get("missing_tuples") or [])
