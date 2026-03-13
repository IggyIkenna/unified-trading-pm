# UDC Stub Completion Plan — Implement 5 NotImplementedError Stubs

**Status:** AI-generated — awaiting user review and promotion to `plans/active/` **Date:** 2026-03-13 **Scope:**
unified-domain-client **Context:** §13 audit found 5 NotImplementedError stubs. This plan implements them via UCI
(unified-cloud-interface).

---

## Summary

| Stub                                          | Location                   | Implementation                                                          |
| --------------------------------------------- | -------------------------- | ----------------------------------------------------------------------- |
| AthenaReader.read                             | readers/athena.py:23       | Use get_storage_client(provider="aws", region=...) + download_bytes     |
| AthenaReader.list_available                   | readers/athena.py:28       | Use StorageClient.list_blobs                                            |
| BigQueryExternalReader.read                   | readers/bq_external.py:22  | Use get_storage_client(provider="gcp", project_id=...) + download_bytes |
| BigQueryExternalReader.list_available         | readers/bq_external.py:27  | Use StorageClient.list_blobs                                            |
| StandardizedDomainCloudService.query_bigquery | standardized_service.py:77 | Delegate to get_analytics_client().execute_query()                      |

---

## Implementation Approach

### 1. AthenaReader & BigQueryExternalReader

Both extend BaseDataReader with `read(bucket, path)` and `list_available(bucket, prefix)`. The data lives in object
storage (S3 for Athena, GCS for BQ external). UCI provides:

- `get_storage_client(provider="aws", region=...)` for S3
- `get_storage_client(provider="gcp", project_id=...)` for GCS

Pattern: Create StorageClient in **init**, delegate read/list_available to same logic as DirectReader.

### 2. StandardizedDomainCloudService.query_bigquery

The NotImplementedError directs callers to `get_analytics_client()` in the service layer. We implement it by delegating:

- `get_analytics_client()` from UCI
- `execute_query(query, params)` returns list[dict]
- Convert to pd.DataFrame

---

## Todos

- [x] udc-athena-reader: Implement AthenaReader.read and list_available via S3 StorageClient
- [x] udc-bq-external-reader: Implement BigQueryExternalReader.read and list_available via GCS StorageClient
- [x] udc-query-bigquery: Implement StandardizedDomainCloudService.query_bigquery via get_analytics_client
- [x] udc-stub-tests: Add/update unit tests (query_bigquery mock test; lazy-init readers avoids socket in tests)
- [x] udc-quality-gates: Run quality gates — all pass; §7 in QUALITY_GATE_BYPASS_AUDIT already RESOLVED
