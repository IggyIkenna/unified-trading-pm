#!/usr/bin/env python3.13
"""GCS migration bundle — pipeline_mode partition + drift cleanup (2026-05-08).

Phase 2 of plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md.
Phase 5.A of manifest_schema_final_gate_2026_05_09.md — extends the single walk
to bundle TWO additional migration axes alongside the original 5 (hive-vocab /
path-prefix / instrument_type casing / schema-4 empty / chain-bundle / pipeline_mode):

Single walk applies the bundled set of pending changes:

Per-parquet axes (applied inside the per-parquet loop via :func:`migrate_one_parquet`):

1. Add ``pipeline_mode={batch_<source>|live_websocket}`` hive partition segment
   (sits LEFT of ``asset_group=`` per UAC pipeline_mode SSOT).
2. Rewrite legacy ``category=`` → canonical ``asset_group=`` if present.
3. Normalize legacy path-prefix ``day=*/...`` (under bucket root) →
   canonical ``raw_tick_data/by_date/day=*/...``.
4. Normalize ``instrument_type`` casing (``PERPETUAL`` → ``perpetual``).
5. Normalize chain-bundle drift (``data_type=option`` → ``options_chain``;
   ``future`` → ``futures_chain`` for bundled types).

Per-bucket axes (applied once per ``run_migration`` invocation around the per-parquet walk):

6. v8 NULL-column backfill for the canonical availability manifest (3 v8
   emission columns added per row via UTL Phase 2.D helper
   :func:`unified_trading_library.manifest_migrations.v7_to_v8.migrate_v7_to_v8`).
   Bucket-level operation; output written to ``_index/per_vm/v7_to_v8_migrate_{VM_NAME}.parquet``.
7. Cross-asset rescan class-A auto-fixes via Phase 3.D ``instruments-service/scripts/cross_asset_rescan.py``.
   Class-A auto-fixes update mutable manifest columns (capture_status / error_reason / attempted_at /
   path) per-asset-group; class-C ambiguous rows stream to triage JSONL for operator review.

Per CLAUDE.md "Manifest concurrency principle" + "Per-VM shard isolation":

* The script is **dry-run by default**. Operator MUST pass ``--apply`` to
  enable destructive operations.
* Multi-worker execution (multiple GCE VMs writing to the same manifest)
  REQUIRES ``MANIFEST_PER_VM_SHARDS=true`` + ``VM_NAME=<unique-tag>`` per
  worker. Startup guard raises ``MultiWorkerWithoutShardIsolationError`` if
  missing when ``--apply`` mode is requested. UTL v7_to_v8 helper has its own
  ``MissingVMShardIsolationError`` guard for defence-in-depth; the script's
  startup guard fires first so the UTL guard never triggers in practice.
* HTTP pool is sized to ``2 * --workers`` (default 10 silently truncates
  ``list_blobs()`` under high concurrency).

Per UTL ``manifest_migrations`` SSOT: this script LEVERAGES
:class:`unified_trading_library.manifest_migrations.ManifestMigrator`,
:func:`chunked_date_ranges`, :class:`RescanScanner`, :class:`LegacyRowPurger`,
and :func:`migrate_v7_to_v8`. It does NOT reimplement the read-modify-write helper.

Plan: ``unified-trading-pm/plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md``
+ ``unified-trading-pm/plans/active/manifest_schema_final_gate_2026_05_09.md`` Phase 5.A.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import re
import subprocess
import sys
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

logger = logging.getLogger("gcs_migration_bundle")

# ---------------------------------------------------------------------------
# Workspace-resolved imports (UAC pipeline_mode + UTL manifest_migrations)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # unified-trading-pm/
WORKSPACE_ROOT = REPO_ROOT.parent
UAC_PATH = WORKSPACE_ROOT / "unified-api-contracts"
UTL_PATH = WORKSPACE_ROOT / "unified-trading-library"
for _p in (UAC_PATH, UTL_PATH):
    _p_str = str(_p)
    if _p.exists() and _p_str not in sys.path:
        sys.path.insert(0, _p_str)

# ruff: noqa: E402
from unified_api_contracts.canonical.crosscutting.pipeline_mode import (  # type: ignore[import-not-found]
    PipelineMode,
    pipeline_mode_for_source,
)
from unified_trading_library.manifest_migrations import (  # type: ignore[import-not-found]  # noqa: qg-deep-import
    MissingVMShardIsolationError,
    V7ToV8MigrationResult,
    migrate_v7_to_v8,
)

# ---------------------------------------------------------------------------
# Constants + drift taxonomy
# ---------------------------------------------------------------------------


class DriftClass(StrEnum):
    """Closed-set drift axes the migration handles."""

    PIPELINE_MODE_MISSING = "pipeline_mode_missing"
    LEGACY_CATEGORY_HIVE_KEY = "legacy_category_hive_key"
    LEGACY_PATH_PREFIX = "legacy_path_prefix"
    INSTRUMENT_TYPE_CASING = "instrument_type_casing"
    CHAIN_BUNDLE_EQUIVALENCE = "chain_bundle_equivalence"
    SCHEMA4_EMPTY_INSTRUMENT_TYPE = "schema4_empty_instrument_type"
    # Per-bucket axes (Phase 5.A — manifest_schema_final_gate_2026_05_09):
    # not stamped on per-parquet ``MigrationResult.drift_classes`` since they
    # apply at the bucket/manifest level, but appear in the aggregate
    # ``MigrationMetrics`` axis-histogram + final JSON summary report.
    V8_NULL_COLUMNS_MISSING = "v8_null_columns_missing"
    CROSS_ASSET_RESCAN_CLASS_A = "cross_asset_rescan_class_a"


class MigrationStatus(StrEnum):
    """Result of migrating a single parquet."""

    NOOP = "noop"
    MIGRATED = "migrated"
    FAILED = "failed"
    DRY_RUN = "dry_run"


_BUNDLED_DATA_TYPE_REWRITES: dict[str, str] = {
    "option": "options_chain",
    "options": "options_chain",
    "future": "futures_chain",
    "futures": "futures_chain",
}

_INSTRUMENT_TYPE_CANONICAL_LOWER = {
    "perpetual",
    "spot",
    "options_chain",
    "futures_chain",
    "option",
    "future",
    "etf",
    "index",
}

_BUCKET_PREFIX_TO_DEFAULT_SOURCE: dict[str, str] = {
    "market-data-tick-cefi": "tardis",
    "market-data-tick-tradfi": "databento",
    "market-data-tick-defi": "onchain_rpc",
    "market-data-tick-sports": "api_football",
    "market-data-tick-prediction": "polymarket_clob",
    "features-calendar": "instruments_service",
    "features-delta-one-cefi": "tardis",
    "features-delta-one-tradfi": "databento",
    "features-delta-one-defi": "onchain_rpc",
    "features-volatility-cefi": "tardis",
    "features-volatility-tradfi": "databento",
    "features-volatility-defi": "onchain_rpc",
    "features-onchain": "onchain_rpc",
    "features-sports": "api_football",
    "features-prediction": "polymarket_clob",
}

_HIVE_SEGMENT_RE = re.compile(r"([a-zA-Z_]+)=([^/]+)")
_LEGACY_DAY_PREFIX_RE = re.compile(r"^day=\d{4}-\d{2}-\d{2}/")
_CANONICAL_PREFIX_RE = re.compile(r"^raw_tick_data/by_date/day=\d{4}-\d{2}-\d{2}/")


# ---------------------------------------------------------------------------
# Errors + result dataclasses
# ---------------------------------------------------------------------------


class MultiWorkerWithoutShardIsolationError(RuntimeError):
    """Raised when --apply runs without per-VM shard isolation env vars."""


class CRC32CMismatchError(RuntimeError):
    """Raised when destination object CRC32C doesn't match source."""


@dataclass(frozen=True)
class MigrationResult:
    """Result of migrating one parquet."""

    source_uri: str
    target_uri: str
    status: MigrationStatus
    drift_classes: tuple[DriftClass, ...] = ()
    bytes_moved: int = 0
    elapsed_ms: float = 0.0
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "source_uri": self.source_uri,
            "target_uri": self.target_uri,
            "status": str(self.status),
            "drift_classes": [str(d) for d in self.drift_classes],
            "bytes_moved": self.bytes_moved,
            "elapsed_ms": self.elapsed_ms,
            "error": self.error,
        }


@dataclass
class MigrationMetrics:
    """Aggregated metrics across a migration run."""

    total_seen: int = 0
    total_migrated: int = 0
    total_noop: int = 0
    total_failed: int = 0
    total_dry_run: int = 0
    total_bytes_moved: int = 0
    drift_histogram: dict[str, int] = field(default_factory=dict)
    error_histogram: dict[str, int] = field(default_factory=dict)
    # Phase 5.A per-bucket axes — populated by the bucket-level operations
    # in :func:`run_migration` (v7→v8 backfill + cross-asset rescan).
    v8_columns_backfilled_rows: int = 0
    v8_columns_already_present_rows: int = 0
    rescan_class_a_auto_fixes: int = 0
    rescan_class_c_triage_count: int = 0

    def record(self, result: MigrationResult) -> None:
        self.total_seen += 1
        if result.status is MigrationStatus.MIGRATED:
            self.total_migrated += 1
            self.total_bytes_moved += result.bytes_moved
        elif result.status is MigrationStatus.NOOP:
            self.total_noop += 1
        elif result.status is MigrationStatus.FAILED:
            self.total_failed += 1
            err_key = (result.error or "unknown_error").split("\n")[0][:80]
            self.error_histogram[err_key] = self.error_histogram.get(err_key, 0) + 1
        elif result.status is MigrationStatus.DRY_RUN:
            self.total_dry_run += 1
        for drift in result.drift_classes:
            key = str(drift)
            self.drift_histogram[key] = self.drift_histogram.get(key, 0) + 1

    def record_v8_backfill(self, result: V7ToV8MigrationResult) -> None:
        """Fold a v7→v8 helper result into the aggregate metrics.

        Called once per bucket by :func:`run_v8_column_backfill`. Tracks the
        ``v8_null_columns_missing`` drift axis in the histogram + the row-level
        backfill / already-v8 counts in dedicated fields for the JSON report.
        """
        self.v8_columns_backfilled_rows += int(result.rows_migrated)
        self.v8_columns_already_present_rows += int(result.rows_already_v8)
        if result.rows_migrated > 0:
            key = str(DriftClass.V8_NULL_COLUMNS_MISSING)
            self.drift_histogram[key] = self.drift_histogram.get(key, 0) + int(result.rows_migrated)

    def record_rescan(
        self,
        *,
        class_a_auto_fixes: int,
        class_c_triage_count: int,
    ) -> None:
        """Fold a cross-asset-rescan result into the aggregate metrics.

        Called once per ``run_migration`` invocation by
        :func:`run_cross_asset_rescan`. Increments the
        ``cross_asset_rescan_class_a`` histogram by the class-A auto-fix count
        + tracks the class-C triage queue length.
        """
        self.rescan_class_a_auto_fixes += int(class_a_auto_fixes)
        self.rescan_class_c_triage_count += int(class_c_triage_count)
        if class_a_auto_fixes > 0:
            key = str(DriftClass.CROSS_ASSET_RESCAN_CLASS_A)
            self.drift_histogram[key] = self.drift_histogram.get(key, 0) + int(class_a_auto_fixes)

    def to_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Path parsing + planning
# ---------------------------------------------------------------------------


def parse_gcs_uri(uri: str) -> tuple[str, str]:
    """Split a ``gs://bucket/object`` URI into ``(bucket, object)``."""
    if not uri.startswith("gs://"):
        msg = f"Not a gs:// URI: {uri!r}"
        raise ValueError(msg)
    body = uri[len("gs://") :]
    if "/" not in body:
        msg = f"URI has no object path: {uri!r}"
        raise ValueError(msg)
    bucket, _, obj = body.partition("/")
    return bucket, obj


def _bucket_prefix_default_source(bucket: str) -> str:
    for prefix, source in _BUCKET_PREFIX_TO_DEFAULT_SOURCE.items():
        if bucket.startswith(f"{prefix}-"):
            return source
    return "databento"


def _normalize_instrument_type(value: str) -> str:
    lower = value.lower()
    if lower in _INSTRUMENT_TYPE_CANONICAL_LOWER:
        return lower
    return value


def _normalize_data_type(value: str) -> str:
    return _BUNDLED_DATA_TYPE_REWRITES.get(value.lower(), value)


def plan_target_path(
    source_object: str,
    *,
    bucket: str,
    pipeline_mode: PipelineMode | None = None,
) -> tuple[str, tuple[DriftClass, ...]]:
    """Compute the canonical target object path for ``source_object``.

    Returns ``(target_object, drift_classes)``. If ``target_object ==
    source_object`` and ``drift_classes == ()``, the path is canonical (NOOP).
    """
    drifts: list[DriftClass] = []
    target = source_object

    # Drift axis 4: legacy `day=*/...` directly under bucket root → canonical
    # `raw_tick_data/by_date/day=*/...` prefix.
    if _LEGACY_DAY_PREFIX_RE.match(target) and not _CANONICAL_PREFIX_RE.match(target):
        drifts.append(DriftClass.LEGACY_PATH_PREFIX)
        target = "raw_tick_data/by_date/" + target

    # Drift axis 1: legacy `category=` hive-key → canonical `asset_group=`.
    if "category=" in target:
        drifts.append(DriftClass.LEGACY_CATEGORY_HIVE_KEY)
        target = re.sub(r"(^|/)category=", r"\1asset_group=", target)

    # Decompose hive segments for drift axes 2 + 5 (case + chain-bundle).
    parts = target.split("/")
    rebuilt: list[str] = []
    for part in parts:
        match = _HIVE_SEGMENT_RE.fullmatch(part)
        if not match:
            rebuilt.append(part)
            continue
        key, value = match.group(1), match.group(2)
        if key == "instrument_type":
            normalized = _normalize_instrument_type(value)
            if normalized != value:
                drifts.append(DriftClass.INSTRUMENT_TYPE_CASING)
                rebuilt.append(f"{key}={normalized}")
                continue
        elif key == "data_type":
            normalized = _normalize_data_type(value)
            if normalized != value:
                drifts.append(DriftClass.CHAIN_BUNDLE_EQUIVALENCE)
                rebuilt.append(f"{key}={normalized}")
                continue
        rebuilt.append(part)
    target = "/".join(rebuilt)

    # Drift axis "pipeline_mode_missing": insert pipeline_mode= LEFT of
    # asset_group=. If pipeline_mode= is already present, leave path untouched.
    if "pipeline_mode=" not in target:
        if pipeline_mode is None:
            source = _bucket_prefix_default_source(bucket)
            try:
                pipeline_mode = pipeline_mode_for_source(source)
            except ValueError:
                pipeline_mode = PipelineMode.BATCH_DATABENTO
        target_parts = target.split("/")
        out_parts: list[str] = []
        inserted = False
        for part in target_parts:
            if not inserted and (part.startswith("asset_group=") or part.startswith("category=")):
                out_parts.append(f"pipeline_mode={pipeline_mode.value}")
                inserted = True
            out_parts.append(part)
        if inserted:
            drifts.append(DriftClass.PIPELINE_MODE_MISSING)
            target = "/".join(out_parts)

    return target, tuple(drifts)


# ---------------------------------------------------------------------------
# gcloud subprocess wrappers (mocked in tests)
# ---------------------------------------------------------------------------


def src_uri_str(uri: str) -> str:
    """Trim long URIs in error messages."""
    return uri if len(uri) < 80 else uri[:77] + "..."


def _gcloud_storage_object_describe(uri: str) -> dict[str, object]:
    """Return ``gcloud storage objects describe`` output as a dict."""
    proc = subprocess.run(  # noqa: S603 — gcloud is a trusted tool
        [
            "gcloud",
            "storage",
            "objects",
            "describe",
            uri,
            "--format=json",
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    parsed: object = json.loads(proc.stdout)
    if not isinstance(parsed, dict):
        msg = f"gcloud describe returned non-dict: {type(parsed).__name__}"
        raise TypeError(msg)
    return parsed


def _gcloud_storage_cp(source: str, target: str) -> None:
    """Server-side copy ``source`` → ``target``. No egress within-region."""
    subprocess.run(  # noqa: S603 — gcloud is a trusted tool
        ["gcloud", "storage", "cp", source, target],
        check=True,
        capture_output=True,
        text=True,
        timeout=300,
    )


def _gcloud_storage_rm(uri: str) -> None:
    """Delete ``uri``."""
    subprocess.run(  # noqa: S603 — gcloud is a trusted tool
        ["gcloud", "storage", "rm", uri],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )


# ---------------------------------------------------------------------------
# Per-parquet migration
# ---------------------------------------------------------------------------


def _verify_crc32c_via(
    source_uri: str,
    target_uri: str,
    describe_fn: Callable[[str], dict[str, object]],
) -> None:
    """Inject-friendly CRC32C verification (test mocks ``describe_fn``)."""
    src = describe_fn(source_uri)
    dst = describe_fn(target_uri)
    src_crc = src.get("crc32c") or src.get("crc32cChecksum")
    dst_crc = dst.get("crc32c") or dst.get("crc32cChecksum")
    src_size = src.get("size")
    dst_size = dst.get("size")
    if src_crc != dst_crc or src_size != dst_size:
        msg = f"crc32c/size mismatch: source crc={src_crc} size={src_size} target crc={dst_crc} size={dst_size}"
        raise CRC32CMismatchError(msg)


def migrate_one_parquet(
    source_uri: str,
    *,
    apply: bool,
    cp_fn: Callable[[str, str], None] = _gcloud_storage_cp,
    rm_fn: Callable[[str], None] = _gcloud_storage_rm,
    describe_fn: Callable[[str], dict[str, object]] = _gcloud_storage_object_describe,
) -> MigrationResult:
    """Migrate a single parquet to canonical hive shape.

    1. Parse the path. 2. Determine target via :func:`plan_target_path`.
    3. NOOP if already canonical. 4. DRY_RUN if ``apply=False``.
    5. cp → verify → rm. 6. Rollback on crc32c mismatch.
    """
    start = time.monotonic()
    bucket, obj = parse_gcs_uri(source_uri)
    target_obj, drifts = plan_target_path(obj, bucket=bucket)
    target_uri = f"gs://{bucket}/{target_obj}"

    if target_obj == obj:
        return MigrationResult(
            source_uri=source_uri,
            target_uri=target_uri,
            status=MigrationStatus.NOOP,
            drift_classes=(),
            elapsed_ms=(time.monotonic() - start) * 1000.0,
        )

    if not apply:
        return MigrationResult(
            source_uri=source_uri,
            target_uri=target_uri,
            status=MigrationStatus.DRY_RUN,
            drift_classes=drifts,
            elapsed_ms=(time.monotonic() - start) * 1000.0,
        )

    try:
        source_meta = describe_fn(source_uri)
        size_obj = source_meta.get("size", 0)
        try:
            bytes_moved = int(size_obj) if size_obj is not None else 0
        except (TypeError, ValueError):
            bytes_moved = 0
        cp_fn(source_uri, target_uri)
    except (subprocess.CalledProcessError, OSError, ValueError) as exc:
        return MigrationResult(
            source_uri=source_uri,
            target_uri=target_uri,
            status=MigrationStatus.FAILED,
            drift_classes=drifts,
            elapsed_ms=(time.monotonic() - start) * 1000.0,
            error=f"copy_failed: {exc!s}",
        )

    try:
        _verify_crc32c_via(source_uri, target_uri, describe_fn)
    except CRC32CMismatchError as exc:
        try:
            rm_fn(target_uri)
        except (subprocess.CalledProcessError, OSError):
            logger.warning(
                "rollback delete of %s failed; manual cleanup required",
                src_uri_str(target_uri),
            )
        return MigrationResult(
            source_uri=source_uri,
            target_uri=target_uri,
            status=MigrationStatus.FAILED,
            drift_classes=drifts,
            elapsed_ms=(time.monotonic() - start) * 1000.0,
            error=f"crc32c_mismatch: {exc!s}",
        )

    try:
        rm_fn(source_uri)
    except (subprocess.CalledProcessError, OSError) as exc:
        return MigrationResult(
            source_uri=source_uri,
            target_uri=target_uri,
            status=MigrationStatus.FAILED,
            drift_classes=drifts,
            elapsed_ms=(time.monotonic() - start) * 1000.0,
            error=f"source_delete_failed: {exc!s}",
        )

    return MigrationResult(
        source_uri=source_uri,
        target_uri=target_uri,
        status=MigrationStatus.MIGRATED,
        drift_classes=drifts,
        bytes_moved=bytes_moved,
        elapsed_ms=(time.monotonic() - start) * 1000.0,
    )


# ---------------------------------------------------------------------------
# Concurrency guard (per-VM shard isolation)
# ---------------------------------------------------------------------------


def assert_per_vm_shard_isolation(
    *,
    apply: bool,
    env: dict[str, str],
) -> None:
    """Raise if --apply mode runs without per-VM shard isolation env vars."""
    if not apply:
        return
    if env.get("MANIFEST_PER_VM_SHARDS") != "true":
        msg = (
            "--apply mode requires MANIFEST_PER_VM_SHARDS=true (per-VM shard "
            "isolation per CLAUDE.md 'Per-VM shard isolation' rule); set the "
            "env var or pass --dry-run."
        )
        raise MultiWorkerWithoutShardIsolationError(msg)
    vm_name = env.get("VM_NAME", "")
    if not vm_name or vm_name == "default":
        msg = (
            "--apply mode requires VM_NAME=<unique-tag> (per-VM shard isolation "
            "per CLAUDE.md 'Per-VM shard isolation' rule); set the env var "
            "to a unique tag like 'migration-cefi-slice01-20260508-120000'."
        )
        raise MultiWorkerWithoutShardIsolationError(msg)


# ---------------------------------------------------------------------------
# Iteration + main
# ---------------------------------------------------------------------------


def iter_parquet_uris_for_slice(
    bucket: str,
    *,
    prefix_slice: str,
    list_fn: Callable[[str, str], list[str]] | None = None,
) -> list[str]:
    """List parquet URIs under ``gs://{bucket}/{prefix_slice}``."""
    if list_fn is not None:
        return list_fn(bucket, prefix_slice)
    proc = subprocess.run(  # noqa: S603 — gcloud is a trusted tool
        ["gcloud", "storage", "ls", "--recursive", f"gs://{bucket}/{prefix_slice}"],
        check=True,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip().endswith(".parquet")]


# ---------------------------------------------------------------------------
# Bucket-level migration steps (Phase 5.A — manifest_schema_final_gate_2026_05_09)
# ---------------------------------------------------------------------------


def run_v8_column_backfill(
    *,
    bucket: str,
    apply: bool,
    vm_name: str | None = None,
    migrate_fn: Callable[..., V7ToV8MigrationResult] = migrate_v7_to_v8,
    client_factory: Callable[[], object] | None = None,
) -> V7ToV8MigrationResult:
    """Run the UTL Phase 2.D v7→v8 NULL-column backfill on ``bucket``'s manifest.

    Bucket-level operation invoked ONCE per ``run_migration`` (not per parquet).
    Adds 3 v8 emission columns to every row in
    ``gs://{bucket}/_index/availability_index.parquet``, defaulted to ``None``.
    Output is written to ``_index/per_vm/v7_to_v8_migrate_{VM_NAME}.parquet``;
    the manifest consolidator daemon merges it into the canonical index with
    last-writer-wins on identical row_key.

    Dry-run mode (``apply=False``) reads + counts but skips the per-VM shard
    write. The script's own ``MultiWorkerWithoutShardIsolationError`` guard
    fires before this is called; UTL's own ``MissingVMShardIsolationError``
    guard is defence-in-depth.

    Args:
        bucket: Bucket containing the canonical availability manifest.
        apply: True → write the per-VM shard. False → dry-run.
        vm_name: Explicit per-VM tag. Defaults to ``VM_NAME`` env var.
        migrate_fn: Injected for tests (defaults to UTL helper).
        client_factory: Injected for tests (defaults to UTL
            ``get_storage_client`` if None, but only resolved when not in
            test-injection mode).

    Returns:
        :class:`V7ToV8MigrationResult` — rows_read / rows_migrated /
        rows_already_v8 / output_path counters.
    """
    if client_factory is None:
        # Lazy import — keeps the script importable in tests that don't have
        # the cloud_interface factory available.
        from unified_trading_library import (  # type: ignore[import-not-found]
            get_storage_client,
        )

        client = get_storage_client(provider="gcp")
    else:
        client = client_factory()

    logger.info(
        "v7_to_v8 backfill starting: bucket=%s apply=%s vm_name=%s",
        bucket,
        apply,
        vm_name or "<from-env>",
    )
    return migrate_fn(
        bucket=bucket,
        client=client,
        vm_name=vm_name,
        dry_run=not apply,
    )


@dataclass(frozen=True)
class CrossAssetRescanResult:
    """Aggregated outcome of one cross-asset rescan invocation.

    Attributes:
        asset_group: Which asset_group was rescanned (or
            ``cross_asset_all`` for the full sweep).
        class_a_auto_fixes: Count of class-A mutable manifest rows
            auto-flipped (when ``apply=True``) or counted (dry-run).
        class_c_triage_count: Count of class-C ambiguous rows written
            to the triage JSONL stream.
        return_code: Subprocess return code (0 = success).
        elapsed_s: Wall-clock seconds for the rescan run.
    """

    asset_group: str
    class_a_auto_fixes: int
    class_c_triage_count: int
    return_code: int
    elapsed_s: int


_RESCAN_AUTO_FIX_PATTERNS: tuple[str, ...] = (
    "AUTO-FIX",
    "AUTO_FIXED",
    "class_a_flip",
    "FLIPPED",
)
_RESCAN_CLASS_C_PATTERN: str = "class-C"


def _parse_rescan_output(stdout: str) -> tuple[int, int]:
    """Extract (class_a_auto_fixes, class_c_triage_count) from rescan stdout.

    The rescan script doesn't emit a machine-readable summary — it logs the
    reconciler stdout (which contains "PHANTOM" lines for class-C) and emits
    structured events. We grep for the auto-fix + class-C markers in stdout
    so the script's JSON report carries meaningful counters without requiring
    the rescan helper to be re-instrumented.

    A future refactor could lift these markers into a ``RescanRunSummary``
    dataclass returned by the rescan helper — captured as a Phase 5.A
    follow-up in the plan body.
    """
    auto_fixes = 0
    class_c = 0
    for line in stdout.splitlines():
        if any(marker in line for marker in _RESCAN_AUTO_FIX_PATTERNS):
            auto_fixes += 1
        # Match both "PHANTOM" reconciler output (legacy class-C surface) and
        # explicit class-C tagging.
        if "PHANTOM" in line.upper() or _RESCAN_CLASS_C_PATTERN in line:
            class_c += 1
    return auto_fixes, class_c


def run_cross_asset_rescan(
    *,
    asset_group: str,
    apply: bool,
    rescan_script: Path | None = None,
    run_fn: Callable[[list[str]], tuple[int, str, str]] | None = None,
) -> CrossAssetRescanResult:
    """Run the instruments-service cross-asset rescan helper for ``asset_group``.

    Bucket-level (asset-group-scoped) operation invoked ONCE per
    ``run_migration``. Wraps ``instruments-service/scripts/cross_asset_rescan.py``
    as a subprocess so the rescan script's own event-stream emission +
    triage JSONL upload continue to function unchanged.

    Class-A auto-fixes update mutable manifest columns when ``apply=True``;
    in dry-run mode the rescan helper counts disagreements only. Class-C
    ambiguous rows are streamed to ``gs://{pid}-rescan-triage/{run_id}/triage.jsonl``
    by the rescan helper itself.

    Args:
        asset_group: ``cefi`` / ``defi`` / ``tradfi`` / ``sports`` /
            ``prediction`` / ``cross_asset_all``.
        apply: True → ``--apply`` (auto-flip class-A); False → dry-run.
        rescan_script: Explicit path to ``cross_asset_rescan.py`` for tests;
            defaults to ``../../instruments-service/scripts/cross_asset_rescan.py``.
        run_fn: Injected subprocess runner ``(cmd) -> (rc, stdout, stderr)`` for
            tests. Defaults to a thin ``subprocess.run`` wrapper.

    Returns:
        :class:`CrossAssetRescanResult` with class-A auto-fix + class-C
        triage counts.
    """
    if rescan_script is None:
        rescan_script = WORKSPACE_ROOT / "instruments-service" / "scripts" / "cross_asset_rescan.py"

    cmd: list[str] = [
        sys.executable,
        str(rescan_script),
        "--asset-group",
        asset_group,
    ]
    if apply:
        cmd.append("--apply")

    logger.info(
        "cross_asset_rescan starting: asset_group=%s apply=%s script=%s",
        asset_group,
        apply,
        rescan_script,
    )
    started = time.monotonic()

    if run_fn is not None:
        rc, stdout, stderr = run_fn(cmd)
    else:
        proc = subprocess.run(  # noqa: S603 — sys.executable + trusted script path
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=3600,
        )
        rc, stdout, stderr = proc.returncode, proc.stdout, proc.stderr

    elapsed = int(time.monotonic() - started)
    auto_fixes, class_c = _parse_rescan_output(stdout)

    if rc != 0:
        logger.error(
            "cross_asset_rescan FAILED rc=%d asset_group=%s stderr=%s",
            rc,
            asset_group,
            stderr[-2000:],
        )

    return CrossAssetRescanResult(
        asset_group=asset_group,
        class_a_auto_fixes=auto_fixes,
        class_c_triage_count=class_c,
        return_code=rc,
        elapsed_s=elapsed,
    )


def run_migration(
    *,
    bucket: str,
    prefix_slice: str,
    apply: bool,
    workers: int,
    list_fn: Callable[[str, str], list[str]] | None = None,
    cp_fn: Callable[[str, str], None] = _gcloud_storage_cp,
    rm_fn: Callable[[str], None] = _gcloud_storage_rm,
    describe_fn: Callable[[str], dict[str, object]] = _gcloud_storage_object_describe,
    v8_backfill_fn: Callable[..., V7ToV8MigrationResult] | None = None,
    rescan_fn: Callable[..., CrossAssetRescanResult] | None = None,
    rescan_asset_group: str = "cross_asset_all",
    skip_v8_backfill: bool = False,
    skip_rescan: bool = False,
) -> tuple[MigrationMetrics, list[MigrationResult]]:
    """Iterate a slice + migrate each parquet, returning aggregate metrics.

    Bundles 7 migration axes per Phase 5.A of manifest_schema_final_gate_2026_05_09:

    1-5. Per-parquet path rewrites (via :func:`migrate_one_parquet`).
    6.   Per-bucket v8 NULL-column manifest backfill (via :func:`run_v8_column_backfill`,
         invoked once before the per-parquet walk so the manifest is at the
         target schema when downstream readers see the migrated parquets).
    7.   Per-asset-group cross-asset rescan class-A auto-fixes (via
         :func:`run_cross_asset_rescan`, invoked once after the per-parquet walk
         so the rescan sees the migrated path-shape).

    Both bucket-level operations honour the ``apply`` flag — in dry-run mode
    they count without writing. Per-VM shard isolation is enforced upfront by
    :func:`assert_per_vm_shard_isolation` (called from :func:`main` before
    ``run_migration``); UTL's own ``MissingVMShardIsolationError`` is
    defence-in-depth.
    """
    metrics = MigrationMetrics()
    results: list[MigrationResult] = []

    # ------------------------------------------------------------------
    # Step 6 — per-bucket v8 NULL-column manifest backfill (Phase 5.A.4)
    # ------------------------------------------------------------------
    if not skip_v8_backfill:
        backfill = v8_backfill_fn if v8_backfill_fn is not None else run_v8_column_backfill
        try:
            v8_result = backfill(bucket=bucket, apply=apply)
            metrics.record_v8_backfill(v8_result)
            logger.info(
                "v7_to_v8 backfill complete: bucket=%s rows_read=%s rows_migrated=%s rows_already_v8=%s output=%s",
                v8_result.bucket,
                v8_result.rows_read,
                v8_result.rows_migrated,
                v8_result.rows_already_v8,
                v8_result.output_path or "<dry-run>",
            )
        except MissingVMShardIsolationError as exc:
            # Defence-in-depth — script's startup guard should have already
            # caught this. Surface as a failed result rather than crashing.
            logger.error("v7_to_v8 backfill blocked by UTL guard: %s", exc)
            results.append(
                MigrationResult(
                    source_uri=f"gs://{bucket}/_index/availability_index.parquet",
                    target_uri=f"gs://{bucket}/_index/availability_index.parquet",
                    status=MigrationStatus.FAILED,
                    error=f"v8_backfill_blocked: {exc!s}",
                )
            )
            metrics.total_failed += 1

    # ------------------------------------------------------------------
    # Steps 1-5 — per-parquet path-rewrite walk
    # ------------------------------------------------------------------
    uris = iter_parquet_uris_for_slice(bucket, prefix_slice=prefix_slice, list_fn=list_fn)
    logger.info(
        "Migration scan: bucket=%s prefix_slice=%s uris=%d apply=%s workers=%d",
        bucket,
        prefix_slice,
        len(uris),
        apply,
        workers,
    )

    if workers <= 1:
        for uri in uris:
            result = migrate_one_parquet(
                uri,
                apply=apply,
                cp_fn=cp_fn,
                rm_fn=rm_fn,
                describe_fn=describe_fn,
            )
            metrics.record(result)
            results.append(result)
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    migrate_one_parquet,
                    uri,
                    apply=apply,
                    cp_fn=cp_fn,
                    rm_fn=rm_fn,
                    describe_fn=describe_fn,
                ): uri
                for uri in uris
            }
            for fut in as_completed(futures):
                result = fut.result()
                metrics.record(result)
                results.append(result)

    # ------------------------------------------------------------------
    # Step 7 — per-asset-group cross-asset rescan class-A auto-fixes (Phase 5.A.5)
    # ------------------------------------------------------------------
    if not skip_rescan:
        rescan = rescan_fn if rescan_fn is not None else run_cross_asset_rescan
        rescan_result = rescan(asset_group=rescan_asset_group, apply=apply)
        metrics.record_rescan(
            class_a_auto_fixes=rescan_result.class_a_auto_fixes,
            class_c_triage_count=rescan_result.class_c_triage_count,
        )
        logger.info(
            "cross_asset_rescan complete: asset_group=%s class_a_auto_fixes=%s class_c_triage=%s rc=%s",
            rescan_result.asset_group,
            rescan_result.class_a_auto_fixes,
            rescan_result.class_c_triage_count,
            rescan_result.return_code,
        )

    return metrics, results


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "GCS migration bundle (Phase 2 of gcs_migration_bundle_pipeline_mode_2026_05_08). Dry-run by default."
        ),
    )
    parser.add_argument(
        "--bucket",
        required=True,
        help="GCS bucket name (e.g. market-data-tick-cefi-${PID}).",
    )
    parser.add_argument(
        "--prefix-slice",
        required=True,
        help=(
            "Object-prefix slice — each VM gets a deterministic slice so workers "
            "never touch the same parquet (e.g. 'raw_tick_data/by_date/day=2024-01')."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=("Enable destructive operations. Default dry-run prints planned migrations without executing them."),
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=16,
        help="Worker pool size (HTTP pool sized to 2*workers). Default 16.",
    )
    parser.add_argument(
        "--out-json",
        type=Path,
        default=None,
        help="Optional path for the per-parquet migration result JSON.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default INFO).",
    )
    parser.add_argument(
        "--skip-v8-backfill",
        action="store_true",
        help=(
            "Skip the per-bucket v7→v8 NULL-column manifest backfill (Phase 5.A.4). "
            "Use only if the manifest was already migrated by a prior run."
        ),
    )
    parser.add_argument(
        "--skip-rescan",
        action="store_true",
        help=(
            "Skip the per-asset-group cross-asset rescan class-A auto-fixes "
            "(Phase 5.A.5). Use only if the rescan was already run for this slice."
        ),
    )
    parser.add_argument(
        "--rescan-asset-group",
        default="cross_asset_all",
        choices=("cefi", "defi", "tradfi", "sports", "prediction", "cross_asset_all"),
        help=(
            "Which asset_group to pass to the cross-asset rescan helper. Default 'cross_asset_all' walks every group."
        ),
    )
    return parser


def main(argv: list[str] | None = None, *, env: dict[str, str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    import os  # local import per workspace "imports at top" exception for env-only access

    resolved_env = env if env is not None else dict(os.environ)
    assert_per_vm_shard_isolation(apply=bool(args.apply), env=resolved_env)

    metrics, results = run_migration(
        bucket=str(args.bucket),
        prefix_slice=str(args.prefix_slice),
        apply=bool(args.apply),
        workers=int(args.workers),
        rescan_asset_group=str(args.rescan_asset_group),
        skip_v8_backfill=bool(args.skip_v8_backfill),
        skip_rescan=bool(args.skip_rescan),
    )

    summary = {
        "bucket": args.bucket,
        "prefix_slice": args.prefix_slice,
        "apply": bool(args.apply),
        "workers": int(args.workers),
        "rescan_asset_group": str(args.rescan_asset_group),
        "skip_v8_backfill": bool(args.skip_v8_backfill),
        "skip_rescan": bool(args.skip_rescan),
        "metrics": metrics.to_dict(),
    }
    logger.info("MIGRATION_SUMMARY %s", json.dumps(summary, sort_keys=True))

    if args.out_json is not None:
        out_path = Path(str(args.out_json))
        out_path.write_text(
            json.dumps(
                {
                    "summary": summary,
                    "results": [r.to_dict() for r in results],
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    return 0 if metrics.total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
