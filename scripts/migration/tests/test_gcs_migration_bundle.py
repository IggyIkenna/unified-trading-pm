"""Unit tests for ``gcs_migration_bundle_2026_05_08`` (Phase 2).

Per the plan body, the test contract is:

1. Per-drift-class fixture — synthetic parquet path with ``category=``, with
   legacy day-prefix, with PERPETUAL casing, with ``data_type=option`` →
   each migrates to canonical shape.
2. NOOP detection — already-canonical path → ``MigrationStatus.NOOP``,
   no GCS operations called.
3. crc32c verification — corrupted destination triggers rollback (delete
   dest, keep source) + ``MigrationStatus.FAILED``.
4. Dry-run mode — no GCS writes; planned migration captured in result.
5. Idempotent — running migrate_one_parquet twice on the same input is safe
   (the second call sees a canonical path → NOOP).
6. Per-VM-shard isolation guard — ``--apply`` without env vars raises
   :class:`MultiWorkerWithoutShardIsolationError`.

All gcloud subprocess calls are mocked via ``unittest.mock`` — these tests
make zero network calls.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Make the script importable.
SCRIPT_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# ruff: noqa: E402
from gcs_migration_bundle_2026_05_08 import (  # type: ignore[import-not-found]
    CRC32CMismatchError,
    DriftClass,
    MigrationMetrics,
    MigrationResult,
    MigrationStatus,
    MultiWorkerWithoutShardIsolationError,
    assert_per_vm_shard_isolation,
    iter_parquet_uris_for_slice,
    migrate_one_parquet,
    parse_gcs_uri,
    plan_target_path,
    run_migration,
)

# ---------------------------------------------------------------------------
# (1) Per-drift-class planning fixtures
# ---------------------------------------------------------------------------


def test_plan_legacy_category_hive_key_rewritten_to_asset_group() -> None:
    src = "raw_tick_data/by_date/day=2024-01-01/category=cefi/venue=binance/data_type=trades/foo.parquet"
    target, drifts = plan_target_path(src, bucket="market-data-tick-cefi-test")
    assert "category=" not in target
    assert "asset_group=cefi" in target
    assert DriftClass.LEGACY_CATEGORY_HIVE_KEY in drifts
    assert DriftClass.PIPELINE_MODE_MISSING in drifts


def test_plan_legacy_path_prefix_rewritten_to_canonical() -> None:
    src = "day=2024-01-01/asset_group=cefi/venue=binance/data_type=trades/foo.parquet"
    target, drifts = plan_target_path(src, bucket="market-data-tick-cefi-test")
    assert target.startswith("raw_tick_data/by_date/day=2024-01-01/")
    assert DriftClass.LEGACY_PATH_PREFIX in drifts


def test_plan_instrument_type_casing_normalized() -> None:
    src = (  # noqa: E501 — fixture path; collapsing reduces readability of the canonical hive shape
        "raw_tick_data/by_date/day=2024-01-01/asset_group=cefi/"
        "venue=binance/data_type=trades/instrument_type=PERPETUAL/foo.parquet"
    )
    target, drifts = plan_target_path(src, bucket="market-data-tick-cefi-test")
    assert "instrument_type=perpetual" in target
    assert "PERPETUAL" not in target
    assert DriftClass.INSTRUMENT_TYPE_CASING in drifts


def test_plan_chain_bundle_data_type_rewritten() -> None:
    src = "raw_tick_data/by_date/day=2024-01-01/asset_group=cefi/venue=deribit/data_type=option/foo.parquet"
    target, drifts = plan_target_path(src, bucket="market-data-tick-cefi-test")
    assert "data_type=options_chain" in target
    assert DriftClass.CHAIN_BUNDLE_EQUIVALENCE in drifts


def test_plan_pipeline_mode_inserted_left_of_asset_group() -> None:
    src = "raw_tick_data/by_date/day=2024-01-01/asset_group=cefi/venue=binance/data_type=trades/foo.parquet"
    target, drifts = plan_target_path(src, bucket="market-data-tick-cefi-test")
    assert "pipeline_mode=batch_tardis" in target
    assert DriftClass.PIPELINE_MODE_MISSING in drifts
    # Order: pipeline_mode= MUST appear before asset_group=
    pipe_idx = target.index("pipeline_mode=")
    ag_idx = target.index("asset_group=")
    assert pipe_idx < ag_idx


def test_plan_combined_drift_axes_all_rewritten_in_one_pass() -> None:
    src = "day=2024-01-01/category=cefi/venue=deribit/data_type=option/instrument_type=PERPETUAL/foo.parquet"
    target, drifts = plan_target_path(src, bucket="market-data-tick-cefi-test")
    assert target.startswith("raw_tick_data/by_date/day=2024-01-01/")
    assert "category=" not in target
    assert "asset_group=cefi" in target
    assert "data_type=options_chain" in target
    assert "instrument_type=perpetual" in target
    assert "pipeline_mode=batch_tardis" in target
    expected_drifts = {
        DriftClass.LEGACY_PATH_PREFIX,
        DriftClass.LEGACY_CATEGORY_HIVE_KEY,
        DriftClass.CHAIN_BUNDLE_EQUIVALENCE,
        DriftClass.INSTRUMENT_TYPE_CASING,
        DriftClass.PIPELINE_MODE_MISSING,
    }
    assert expected_drifts.issubset(set(drifts))


# ---------------------------------------------------------------------------
# (2) NOOP detection — already-canonical path
# ---------------------------------------------------------------------------


def test_plan_noop_for_already_canonical_path() -> None:
    src = (
        "raw_tick_data/by_date/day=2024-01-01/pipeline_mode=batch_tardis/"
        "asset_group=cefi/venue=binance/data_type=trades/foo.parquet"
    )
    target, drifts = plan_target_path(src, bucket="market-data-tick-cefi-test")
    assert target == src
    assert drifts == ()


def test_migrate_noop_no_gcs_calls() -> None:
    canonical = (
        "raw_tick_data/by_date/day=2024-01-01/pipeline_mode=batch_tardis/"
        "asset_group=cefi/venue=binance/data_type=trades/foo.parquet"
    )
    cp_mock = MagicMock()
    rm_mock = MagicMock()
    describe_mock = MagicMock()
    result = migrate_one_parquet(
        f"gs://market-data-tick-cefi-test/{canonical}",
        apply=True,
        cp_fn=cp_mock,
        rm_fn=rm_mock,
        describe_fn=describe_mock,
    )
    assert result.status is MigrationStatus.NOOP
    assert result.drift_classes == ()
    cp_mock.assert_not_called()
    rm_mock.assert_not_called()
    describe_mock.assert_not_called()


# ---------------------------------------------------------------------------
# (3) crc32c verification — rollback on mismatch
# ---------------------------------------------------------------------------


def test_migrate_crc32c_mismatch_rolls_back_dest_and_keeps_source() -> None:
    src_uri = "gs://market-data-tick-cefi-test/day=2024-01-01/category=cefi/venue=binance/data_type=trades/foo.parquet"
    cp_mock = MagicMock()
    rm_mock = MagicMock()

    # describe_fn returns DIFFERENT crc32c for source vs dest → rollback fires.
    describe_mock = MagicMock(
        side_effect=[
            {"size": 1024, "crc32c": "src_crc"},  # initial size lookup (apply path)
            {"size": 1024, "crc32c": "src_crc"},  # source verify
            {"size": 1024, "crc32c": "dst_crc"},  # destination verify — MISMATCH
        ]
    )
    result = migrate_one_parquet(
        src_uri,
        apply=True,
        cp_fn=cp_mock,
        rm_fn=rm_mock,
        describe_fn=describe_mock,
    )
    assert result.status is MigrationStatus.FAILED
    assert "crc32c_mismatch" in (result.error or "")
    # Destination MUST have been rolled back.
    rm_mock.assert_called_once()
    # Source MUST NOT have been deleted (kept for safety).
    rm_calls = [call.args[0] for call in rm_mock.call_args_list]
    assert src_uri not in rm_calls


# ---------------------------------------------------------------------------
# (4) Dry-run mode — no GCS writes
# ---------------------------------------------------------------------------


def test_migrate_dry_run_no_gcs_writes() -> None:
    src_uri = "gs://market-data-tick-cefi-test/day=2024-01-01/category=cefi/venue=binance/data_type=trades/foo.parquet"
    cp_mock = MagicMock()
    rm_mock = MagicMock()
    describe_mock = MagicMock()
    result = migrate_one_parquet(
        src_uri,
        apply=False,  # DRY-RUN
        cp_fn=cp_mock,
        rm_fn=rm_mock,
        describe_fn=describe_mock,
    )
    assert result.status is MigrationStatus.DRY_RUN
    assert result.target_uri != src_uri  # planned migration captured
    assert DriftClass.LEGACY_CATEGORY_HIVE_KEY in result.drift_classes
    assert DriftClass.LEGACY_PATH_PREFIX in result.drift_classes
    cp_mock.assert_not_called()
    rm_mock.assert_not_called()
    describe_mock.assert_not_called()


# ---------------------------------------------------------------------------
# (5) Idempotent — second pass on canonical input is NOOP
# ---------------------------------------------------------------------------


def test_migrate_idempotent_second_pass_noop() -> None:
    src_uri = "gs://market-data-tick-cefi-test/day=2024-01-01/category=cefi/venue=binance/data_type=trades/foo.parquet"
    # First pass — dry-run captures the planned canonical target.
    first = migrate_one_parquet(
        src_uri,
        apply=False,
        cp_fn=MagicMock(),
        rm_fn=MagicMock(),
        describe_fn=MagicMock(),
    )
    assert first.status is MigrationStatus.DRY_RUN
    canonical_uri = first.target_uri
    # Second pass on the canonical target — NOOP, no migration needed.
    second = migrate_one_parquet(
        canonical_uri,
        apply=True,
        cp_fn=MagicMock(),
        rm_fn=MagicMock(),
        describe_fn=MagicMock(),
    )
    assert second.status is MigrationStatus.NOOP


# ---------------------------------------------------------------------------
# (6) Per-VM-shard isolation guard
# ---------------------------------------------------------------------------


def test_assert_per_vm_shard_isolation_dry_run_exempt() -> None:
    # Dry-run is read-only, no env var requirement.
    assert_per_vm_shard_isolation(apply=False, env={})


def test_assert_per_vm_shard_isolation_apply_requires_env_var() -> None:
    with pytest.raises(MultiWorkerWithoutShardIsolationError, match="MANIFEST_PER_VM_SHARDS"):
        assert_per_vm_shard_isolation(apply=True, env={})


def test_assert_per_vm_shard_isolation_apply_requires_unique_vm_name() -> None:
    with pytest.raises(MultiWorkerWithoutShardIsolationError, match="VM_NAME"):
        assert_per_vm_shard_isolation(
            apply=True,
            env={"MANIFEST_PER_VM_SHARDS": "true", "VM_NAME": ""},
        )


def test_assert_per_vm_shard_isolation_apply_with_full_env_passes() -> None:
    assert_per_vm_shard_isolation(
        apply=True,
        env={"MANIFEST_PER_VM_SHARDS": "true", "VM_NAME": "migration-cefi-slice01-20260508"},
    )


def test_assert_per_vm_shard_isolation_rejects_default_vm_name() -> None:
    # 'default' is reserved and not unique.
    with pytest.raises(MultiWorkerWithoutShardIsolationError, match="VM_NAME"):
        assert_per_vm_shard_isolation(
            apply=True,
            env={"MANIFEST_PER_VM_SHARDS": "true", "VM_NAME": "default"},
        )


# ---------------------------------------------------------------------------
# parse_gcs_uri + run_migration aggregate metrics
# ---------------------------------------------------------------------------


def test_parse_gcs_uri_happy_path() -> None:
    bucket, obj = parse_gcs_uri("gs://my-bucket/foo/bar.parquet")
    assert bucket == "my-bucket"
    assert obj == "foo/bar.parquet"


def test_parse_gcs_uri_rejects_non_gs_uri() -> None:
    with pytest.raises(ValueError, match="gs://"):
        parse_gcs_uri("s3://bar/baz")


def test_parse_gcs_uri_rejects_no_object_path() -> None:
    with pytest.raises(ValueError, match="no object path"):
        parse_gcs_uri("gs://bucket-only")


def test_run_migration_aggregates_metrics_across_uris() -> None:
    bucket = "market-data-tick-cefi-test"
    legacy_uris = [
        f"gs://{bucket}/day=2024-01-01/category=cefi/venue=binance/data_type=trades/a.parquet",
        f"gs://{bucket}/day=2024-01-01/category=cefi/venue=binance/data_type=option/b.parquet",
    ]
    canonical_uri = (
        f"gs://{bucket}/raw_tick_data/by_date/day=2024-01-01/pipeline_mode=batch_tardis/"
        "asset_group=cefi/venue=binance/data_type=trades/c.parquet"
    )
    metrics, results = run_migration(
        bucket=bucket,
        prefix_slice="raw_tick_data/by_date/",
        apply=False,  # dry-run — no GCS calls
        workers=1,
        list_fn=lambda _b, _p: [*legacy_uris, canonical_uri],
        cp_fn=MagicMock(),
        rm_fn=MagicMock(),
        describe_fn=MagicMock(),
    )
    assert metrics.total_seen == 3
    assert metrics.total_dry_run == 2
    assert metrics.total_noop == 1
    assert metrics.total_failed == 0
    assert metrics.drift_histogram[str(DriftClass.LEGACY_CATEGORY_HIVE_KEY)] == 2
    assert metrics.drift_histogram[str(DriftClass.PIPELINE_MODE_MISSING)] == 2
    assert metrics.drift_histogram[str(DriftClass.CHAIN_BUNDLE_EQUIVALENCE)] == 1
    # All-results length matches.
    assert len(results) == 3


def test_iter_parquet_uris_for_slice_uses_injected_list_fn() -> None:
    captured: list[tuple[str, str]] = []

    def fake_list(bucket: str, prefix: str) -> list[str]:
        captured.append((bucket, prefix))
        return [f"gs://{bucket}/{prefix}/a.parquet", f"gs://{bucket}/{prefix}/b.json"]

    uris = iter_parquet_uris_for_slice("buck", prefix_slice="day=2024-01-01", list_fn=fake_list)
    assert uris == ["gs://buck/day=2024-01-01/a.parquet", "gs://buck/day=2024-01-01/b.json"]
    assert captured == [("buck", "day=2024-01-01")]


# ---------------------------------------------------------------------------
# MigrationMetrics dataclass (basic record path)
# ---------------------------------------------------------------------------


def test_migration_metrics_record_handles_all_status_classes() -> None:
    metrics = MigrationMetrics()
    metrics.record(
        MigrationResult(source_uri="gs://b/x", target_uri="gs://b/y", status=MigrationStatus.MIGRATED, bytes_moved=100)
    )
    metrics.record(MigrationResult(source_uri="gs://b/z", target_uri="gs://b/z", status=MigrationStatus.NOOP))
    metrics.record(
        MigrationResult(
            source_uri="gs://b/q",
            target_uri="gs://b/r",
            status=MigrationStatus.FAILED,
            error="copy_failed: timeout",
        )
    )
    metrics.record(MigrationResult(source_uri="gs://b/k", target_uri="gs://b/m", status=MigrationStatus.DRY_RUN))
    assert metrics.total_seen == 4
    assert metrics.total_migrated == 1
    assert metrics.total_noop == 1
    assert metrics.total_failed == 1
    assert metrics.total_dry_run == 1
    assert metrics.total_bytes_moved == 100
    assert any("copy_failed" in k for k in metrics.error_histogram)


def test_crc32c_mismatch_error_inheritance() -> None:
    err = CRC32CMismatchError("test")
    assert isinstance(err, RuntimeError)
