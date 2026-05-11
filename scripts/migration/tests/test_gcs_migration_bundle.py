"""Unit tests for ``gcs_migration_bundle_2026_05_08`` (Phase 2 + Phase 5.A).

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

Phase 5.A additions (manifest_schema_final_gate_2026_05_09):

7. v8 NULL-column backfill — synthetic v7 parquet → manifest gets 3 v8 columns;
   already-v8 parquet → idempotent pass-through; UTL guard fires when env vars
   missing.
8. Cross-asset rescan class-A auto-fixes — synthetic rescan stdout → class-A
   counter increments; PHANTOM lines → class-C triage counter increments.

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
    CrossAssetRescanResult,
    DriftClass,
    MigrationMetrics,
    MigrationResult,
    MigrationStatus,
    MultiWorkerWithoutShardIsolationError,
    _parse_rescan_output,
    assert_per_vm_shard_isolation,
    iter_parquet_uris_for_slice,
    migrate_one_parquet,
    parse_gcs_uri,
    plan_target_path,
    run_cross_asset_rescan,
    run_migration,
    run_v8_column_backfill,
)
from unified_trading_library.manifest_migrations import (  # type: ignore[import-not-found]  # noqa: qg-deep-import
    V7ToV8MigrationResult,
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
        # Phase 5.A bucket-level ops short-circuited via skip-flags so this
        # legacy test stays focused on per-parquet axes only.
        skip_v8_backfill=True,
        skip_rescan=True,
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


# ---------------------------------------------------------------------------
# Phase 5.A.4 / 5.B — v8 NULL-column backfill (per-bucket axis)
# ---------------------------------------------------------------------------


def _fake_v8_result(
    *,
    rows_read: int,
    rows_migrated: int,
    rows_already_v8: int,
    bucket: str = "market-data-tick-cefi-test",
    output_path: str = "_index/per_vm/v7_to_v8_migrate_test-vm.parquet",
    dry_run: bool = False,
) -> V7ToV8MigrationResult:
    """Build a synthetic ``V7ToV8MigrationResult`` for injection."""
    return V7ToV8MigrationResult(
        bucket=bucket,
        rows_read=rows_read,
        rows_already_v8=rows_already_v8,
        rows_migrated=rows_migrated,
        output_path=output_path,
        vm_name="test-vm",
        dry_run=dry_run,
    )


def test_run_migration_invokes_v8_backfill_and_records_metrics() -> None:
    """v8 NULL-column backfill runs once per bucket + folds into metrics."""
    bucket = "market-data-tick-cefi-test"
    fake_backfill = MagicMock(return_value=_fake_v8_result(rows_read=100, rows_migrated=100, rows_already_v8=0))
    metrics, _ = run_migration(
        bucket=bucket,
        prefix_slice="raw_tick_data/by_date/",
        apply=True,
        workers=1,
        list_fn=lambda _b, _p: [],
        cp_fn=MagicMock(),
        rm_fn=MagicMock(),
        describe_fn=MagicMock(),
        v8_backfill_fn=fake_backfill,
        skip_rescan=True,
    )
    fake_backfill.assert_called_once()
    call_kwargs = fake_backfill.call_args.kwargs
    assert call_kwargs["bucket"] == bucket
    assert call_kwargs["apply"] is True
    assert metrics.v8_columns_backfilled_rows == 100
    assert metrics.v8_columns_already_present_rows == 0
    assert metrics.drift_histogram[str(DriftClass.V8_NULL_COLUMNS_MISSING)] == 100


def test_run_migration_v8_backfill_already_v8_no_drift_recorded() -> None:
    """Idempotent re-run case: every row already has 3 v8 columns."""
    fake_backfill = MagicMock(return_value=_fake_v8_result(rows_read=42, rows_migrated=0, rows_already_v8=42))
    metrics, _ = run_migration(
        bucket="market-data-tick-cefi-test",
        prefix_slice="raw_tick_data/by_date/",
        apply=True,
        workers=1,
        list_fn=lambda _b, _p: [],
        v8_backfill_fn=fake_backfill,
        skip_rescan=True,
    )
    assert metrics.v8_columns_backfilled_rows == 0
    assert metrics.v8_columns_already_present_rows == 42
    # No drift recorded when nothing was migrated.
    assert str(DriftClass.V8_NULL_COLUMNS_MISSING) not in metrics.drift_histogram


def test_run_migration_v8_backfill_dry_run_mode() -> None:
    """Dry-run mode propagates apply=False to the v8 helper."""
    fake_backfill = MagicMock(
        return_value=_fake_v8_result(
            rows_read=50,
            rows_migrated=50,
            rows_already_v8=0,
            output_path="",
            dry_run=True,
        )
    )
    metrics, _ = run_migration(
        bucket="market-data-tick-cefi-test",
        prefix_slice="raw_tick_data/by_date/",
        apply=False,
        workers=1,
        list_fn=lambda _b, _p: [],
        v8_backfill_fn=fake_backfill,
        skip_rescan=True,
    )
    fake_backfill.assert_called_once()
    assert fake_backfill.call_args.kwargs["apply"] is False
    # Even in dry-run, counts surface so the operator sees planned counts.
    assert metrics.v8_columns_backfilled_rows == 50


def test_run_v8_column_backfill_passes_kwargs_to_migrate_fn() -> None:
    """Helper forwards bucket / apply / vm_name correctly to UTL fn."""
    fake_client_factory = MagicMock(return_value=MagicMock(name="stub_client"))
    fake_migrate = MagicMock(return_value=_fake_v8_result(rows_read=10, rows_migrated=10, rows_already_v8=0))
    result = run_v8_column_backfill(
        bucket="market-data-tick-defi-test",
        apply=True,
        vm_name="test-vm-tag",
        migrate_fn=fake_migrate,
        client_factory=fake_client_factory,
    )
    fake_client_factory.assert_called_once()
    fake_migrate.assert_called_once()
    call_kwargs = fake_migrate.call_args.kwargs
    assert call_kwargs["bucket"] == "market-data-tick-defi-test"
    assert call_kwargs["vm_name"] == "test-vm-tag"
    assert call_kwargs["dry_run"] is False
    assert result.rows_migrated == 10


# ---------------------------------------------------------------------------
# Phase 5.A.5 / 5.B — cross-asset rescan class-A auto-fixes (per-asset-group axis)
# ---------------------------------------------------------------------------


def test_parse_rescan_output_counts_class_a_auto_fixes_and_class_c() -> None:
    """Stdout grep extracts class-A auto-fix + class-C triage counts."""
    stdout = "\n".join(
        [
            "starting rescan ...",
            "AUTO-FIX cefi binance 2024-01-01 capture_status=captured",
            "AUTO-FIX cefi binance 2024-01-02 error_reason=EXPECTED_PAUSED_LEAGUE",
            "PHANTOM cefi bybit data_type=trades 2024-01-01 unmatched",
            "PHANTOM defi uniswap 2024-01-02 ambiguous",
            "class-C disagreement: instrument_id drift",
            "OK end of run",
        ]
    )
    class_a, class_c = _parse_rescan_output(stdout)
    assert class_a == 2
    # PHANTOM × 2 + explicit class-C × 1 = 3 triage entries.
    assert class_c == 3


def test_parse_rescan_output_empty_stdout_yields_zero_counts() -> None:
    class_a, class_c = _parse_rescan_output("")
    assert class_a == 0
    assert class_c == 0


def test_run_migration_invokes_rescan_class_a_and_records_metrics() -> None:
    """cross_asset_rescan runs once per ``run_migration`` + folds into metrics."""
    fake_rescan = MagicMock(
        return_value=CrossAssetRescanResult(
            asset_group="cross_asset_all",
            class_a_auto_fixes=7,
            class_c_triage_count=3,
            return_code=0,
            elapsed_s=42,
        )
    )
    metrics, _ = run_migration(
        bucket="market-data-tick-cefi-test",
        prefix_slice="raw_tick_data/by_date/",
        apply=True,
        workers=1,
        list_fn=lambda _b, _p: [],
        rescan_fn=fake_rescan,
        rescan_asset_group="cross_asset_all",
        skip_v8_backfill=True,
    )
    fake_rescan.assert_called_once()
    call_kwargs = fake_rescan.call_args.kwargs
    assert call_kwargs["asset_group"] == "cross_asset_all"
    assert call_kwargs["apply"] is True
    assert metrics.rescan_class_a_auto_fixes == 7
    assert metrics.rescan_class_c_triage_count == 3
    assert metrics.drift_histogram[str(DriftClass.CROSS_ASSET_RESCAN_CLASS_A)] == 7


def test_run_migration_rescan_dry_run_no_apply_flag() -> None:
    """Dry-run propagates apply=False to rescan helper."""
    fake_rescan = MagicMock(
        return_value=CrossAssetRescanResult(
            asset_group="cefi",
            class_a_auto_fixes=0,
            class_c_triage_count=5,
            return_code=0,
            elapsed_s=20,
        )
    )
    metrics, _ = run_migration(
        bucket="market-data-tick-cefi-test",
        prefix_slice="raw_tick_data/by_date/",
        apply=False,
        workers=1,
        list_fn=lambda _b, _p: [],
        rescan_fn=fake_rescan,
        rescan_asset_group="cefi",
        skip_v8_backfill=True,
    )
    assert fake_rescan.call_args.kwargs["apply"] is False
    # No auto-fixes (dry-run counts only) → no drift histogram entry.
    assert str(DriftClass.CROSS_ASSET_RESCAN_CLASS_A) not in metrics.drift_histogram
    # Class-C triage still recorded.
    assert metrics.rescan_class_c_triage_count == 5


def test_run_cross_asset_rescan_subprocess_command_shape() -> None:
    """run_cross_asset_rescan builds the right CLI invocation."""
    captured: list[list[str]] = []

    def fake_run(cmd: list[str]) -> tuple[int, str, str]:
        captured.append(cmd)
        return 0, "AUTO-FIX cefi 2024-01-01\nPHANTOM defi 2024-01-02\n", ""

    result = run_cross_asset_rescan(
        asset_group="cefi",
        apply=True,
        rescan_script=Path("/tmp/dummy_cross_asset_rescan.py"),
        run_fn=fake_run,
    )
    assert len(captured) == 1
    cmd = captured[0]
    assert "--asset-group" in cmd
    assert "cefi" in cmd
    assert "--apply" in cmd
    assert result.class_a_auto_fixes == 1
    assert result.class_c_triage_count == 1
    assert result.return_code == 0


def test_run_cross_asset_rescan_dry_run_omits_apply_flag() -> None:
    """Dry-run mode (apply=False) does NOT pass --apply to the subprocess."""
    captured: list[list[str]] = []

    def fake_run(cmd: list[str]) -> tuple[int, str, str]:
        captured.append(cmd)
        return 0, "", ""

    run_cross_asset_rescan(
        asset_group="defi",
        apply=False,
        rescan_script=Path("/tmp/dummy_cross_asset_rescan.py"),
        run_fn=fake_run,
    )
    cmd = captured[0]
    assert "--apply" not in cmd


def test_run_cross_asset_rescan_subprocess_failure_surfaces_rc() -> None:
    """Non-zero subprocess return code surfaces in result.return_code."""
    result = run_cross_asset_rescan(
        asset_group="sports",
        apply=False,
        rescan_script=Path("/tmp/dummy_cross_asset_rescan.py"),
        run_fn=lambda _cmd: (1, "", "rescan failed: catalog missing"),
    )
    assert result.return_code == 1
    assert result.class_a_auto_fixes == 0


# ---------------------------------------------------------------------------
# Phase 5.A — combined v8 + rescan + per-parquet metrics in one run
# ---------------------------------------------------------------------------


def test_run_migration_full_bundle_combines_all_three_axis_groups() -> None:
    """Single ``run_migration`` call surfaces per-parquet + v8 + rescan metrics."""
    bucket = "market-data-tick-cefi-test"
    legacy_uris = [
        f"gs://{bucket}/day=2024-01-01/category=cefi/venue=binance/data_type=trades/a.parquet",
    ]
    fake_v8 = MagicMock(return_value=_fake_v8_result(rows_read=50, rows_migrated=50, rows_already_v8=0))
    fake_rescan = MagicMock(
        return_value=CrossAssetRescanResult(
            asset_group="cross_asset_all",
            class_a_auto_fixes=4,
            class_c_triage_count=2,
            return_code=0,
            elapsed_s=10,
        )
    )
    metrics, results = run_migration(
        bucket=bucket,
        prefix_slice="raw_tick_data/by_date/",
        apply=False,
        workers=1,
        list_fn=lambda _b, _p: legacy_uris,
        cp_fn=MagicMock(),
        rm_fn=MagicMock(),
        describe_fn=MagicMock(),
        v8_backfill_fn=fake_v8,
        rescan_fn=fake_rescan,
    )
    # Per-parquet axis fired for the 1 legacy URI.
    assert metrics.total_seen == 1
    assert metrics.total_dry_run == 1
    # v8 backfill metrics surfaced.
    assert metrics.v8_columns_backfilled_rows == 50
    # Rescan metrics surfaced.
    assert metrics.rescan_class_a_auto_fixes == 4
    assert metrics.rescan_class_c_triage_count == 2
    # All 3 axis groups visible in histogram.
    assert metrics.drift_histogram[str(DriftClass.V8_NULL_COLUMNS_MISSING)] == 50
    assert metrics.drift_histogram[str(DriftClass.CROSS_ASSET_RESCAN_CLASS_A)] == 4
    assert metrics.drift_histogram[str(DriftClass.LEGACY_CATEGORY_HIVE_KEY)] == 1
    # Results list still per-parquet only.
    assert len(results) == 1


def test_run_migration_skip_flags_short_circuit_bucket_level_ops() -> None:
    """skip_v8_backfill + skip_rescan both bypass their helpers."""
    fake_v8 = MagicMock()
    fake_rescan = MagicMock()
    metrics, _ = run_migration(
        bucket="market-data-tick-cefi-test",
        prefix_slice="raw_tick_data/by_date/",
        apply=False,
        workers=1,
        list_fn=lambda _b, _p: [],
        v8_backfill_fn=fake_v8,
        rescan_fn=fake_rescan,
        skip_v8_backfill=True,
        skip_rescan=True,
    )
    fake_v8.assert_not_called()
    fake_rescan.assert_not_called()
    assert metrics.v8_columns_backfilled_rows == 0
    assert metrics.rescan_class_a_auto_fixes == 0


# ---------------------------------------------------------------------------
# Phase 5.A — per-VM isolation guard fires BEFORE UTL helper
# ---------------------------------------------------------------------------


def test_assert_per_vm_shard_isolation_runs_before_v8_helper() -> None:
    """The script's own guard MUST fire before the UTL helper sees the call.

    This protects against the UTL ``MissingVMShardIsolationError`` being the
    error surface — the script's guard gives a more informative message about
    the bundled migration context. In practice, the startup guard in
    :func:`main` catches the missing env vars; if it didn't, we'd never get
    here.
    """
    # Script guard fires first → UTL helper never called.
    with pytest.raises(MultiWorkerWithoutShardIsolationError):
        assert_per_vm_shard_isolation(apply=True, env={})
    # Defence-in-depth — if somebody bypassed the guard and called the UTL
    # helper directly, UTL would still raise MissingVMShardIsolationError.
    # We don't test that here (it's a UTL responsibility, covered in
    # test_manifest_migrations_v7_to_v8.py); we only assert that the bundled
    # script's guard is the FIRST line of defence and uses the script's
    # error class (not UTL's).
