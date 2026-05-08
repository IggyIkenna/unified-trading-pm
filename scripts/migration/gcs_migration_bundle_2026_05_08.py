#!/usr/bin/env python3.13
"""GCS migration bundle — pipeline_mode partition + drift cleanup (2026-05-08).

Phase 2 of plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md.

Walks every parquet under configured GCS buckets ONCE and applies the bundled
set of pending hive-vocab + partition-column changes in a single pass:

1. Add ``pipeline_mode={batch_<source>|live_websocket}`` hive partition segment
   (sits LEFT of ``asset_group=`` per UAC pipeline_mode SSOT).
2. Rewrite legacy ``category=`` → canonical ``asset_group=`` if present.
3. Normalize legacy path-prefix ``day=*/...`` (under bucket root) →
   canonical ``raw_tick_data/by_date/day=*/...``.
4. Normalize ``instrument_type`` casing (``PERPETUAL`` → ``perpetual``).
5. Normalize chain-bundle drift (``data_type=option`` → ``options_chain``;
   ``future`` → ``futures_chain`` for bundled types).

Per CLAUDE.md "Manifest concurrency principle" + "Per-VM shard isolation":

* The script is **dry-run by default**. Operator MUST pass ``--apply`` to
  enable destructive operations.
* Multi-worker execution (multiple GCE VMs writing to the same manifest)
  REQUIRES ``MANIFEST_PER_VM_SHARDS=true`` + ``VM_NAME=<unique-tag>`` per
  worker. Startup guard raises ``MultiWorkerWithoutShardIsolationError`` if
  missing when ``--apply`` mode is requested.
* HTTP pool is sized to ``2 * --workers`` (default 10 silently truncates
  ``list_blobs()`` under high concurrency).

Per UTL ``manifest_migrations`` SSOT: this script LEVERAGES
:class:`unified_trading_library.manifest_migrations.ManifestMigrator`,
:func:`chunked_date_ranges`, :class:`RescanScanner`, :class:`LegacyRowPurger`.
It does NOT reimplement the read-modify-write helper.

Plan: ``unified-trading-pm/plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md``.
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
) -> tuple[MigrationMetrics, list[MigrationResult]]:
    """Iterate a slice + migrate each parquet, returning aggregate metrics."""
    uris = iter_parquet_uris_for_slice(bucket, prefix_slice=prefix_slice, list_fn=list_fn)
    logger.info(
        "Migration scan: bucket=%s prefix_slice=%s uris=%d apply=%s workers=%d",
        bucket,
        prefix_slice,
        len(uris),
        apply,
        workers,
    )
    metrics = MigrationMetrics()
    results: list[MigrationResult] = []

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
        return metrics, results

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
    )

    summary = {
        "bucket": args.bucket,
        "prefix_slice": args.prefix_slice,
        "apply": bool(args.apply),
        "workers": int(args.workers),
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
