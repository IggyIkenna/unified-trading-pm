---
doc_type: issue
title:
  deployment-api log_stream.py's real SSE generators (_vm_sse_generator/_live_cluster_sse_generator) have zero
  executable test coverage of the honest-empty-stream behavior
summary: >-
  Discovered while live-verifying data_pipeline_alert_substrate_residual_2026_07_24_finalize_2026_07_30.md's
  deployment-ui streaming-events-pane todo. GET /api/logs/stream/{ref}'s real (non-mock) generators are honest by
  code-trace AND by a direct live curl (a never-existed VM ref streams heartbeats only, zero fabricated vm_event rows) —
  but no test in the repo drains either generator and asserts this. The two existing tests for this route only check
  that stream_logs() RETURNS an EventSourceResponse object without ever iterating it, so they exercise zero GCS I/O.
  Backend/Python — out of scope for the UI-scoped todo that found it (different repo, different craft).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer]
tags: [deployment-api, testing, sse, log-stream, coverage-gap, observability]
related:
  [
    /plans/active/data_pipeline_alert_substrate_residual_2026_07_24_finalize_2026_07_30.md,
    /codex/06-coding-standards/integration-testing-layers.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
depends_on: []
locked_by:
locked_since:
source: >-
  Discovered 2026-07-30 (slot-3, ui_developer) while live-verifying
  data_pipeline_alert_substrate_residual_2026_07_24_finalize_2026_07_30.md todo 2 — traced by an Explore sub-agent
  (deployment_api/routes/log_stream.py + vm_events.py) then confirmed empirically via a direct curl against the real
  (CLOUD_MOCK_MODE=false) backend, both for a genuinely-running VM and a never-existed VM ref.
---

# deployment-api `log_stream.py` SSE generators have no executable test coverage of the honest-empty-stream behavior

## What I found

`GET /api/logs/stream/{target_ref}` (`deployment_api/routes/log_stream.py:165-185`) dispatches to one of three
generators. The two REAL (non-mock) ones — `_vm_sse_generator` (`log_stream.py:66-102`) and
`_live_cluster_sse_generator` (`log_stream.py:105-148`) — poll live GCS blobs under the `{project_id}-events` bucket and
are honest by construction: when `_collect_blob_names` (`vm_events.py:479-500`) returns `([], [])` for an
empty/nonexistent prefix, the `for` loop over new blobs runs zero times, so zero `vm_event` frames are ever yielded —
only periodic `heartbeat`/`ping` frames (every 30s, `_HEARTBEAT_INTERVAL_SECS`). Confirmed twice: by direct code trace,
and by live-curling the real backend (`restart-deployment-stack.sh --api`) against a never-existed VM ref — 35s of
stream produced only heartbeats, zero fabricated rows.

**But this is proven true only by inspection + an ad hoc manual curl, not by an executable test.** The only test file
for this route, `tests/unit/test_route_log_stream.py`:

- `TestStreamLogsLiveClusterStreams` (lines 36-59) asserts `stream_logs(...)` **returns** an `EventSourceResponse`
  instance — calling the async-generator function only creates the generator object; its body (the GCS poll loop) never
  executes until iterated. Zero GCS I/O is exercised.
- `TestMockSseGenerator` (lines 62-91) drains only the MOCK generator (`_mock_sse_generator`), which is a completely
  separate, always-fabricated 3-event code path gated on `is_mock_mode()` — irrelevant to the real generators.

No test anywhere in the repo drains `_vm_sse_generator` or `_live_cluster_sse_generator` with a fake storage client and
asserts the empty-bucket → heartbeat-only behavior. The closest analog,
`test_vm_events.py::TestRealMode:: test_empty_bucket_returns_zero_events` (lines 230-250), proves the underlying
`_collect_blob_names` primitive is honest-empty using a `_FakeStorageClient`, but it tests a _different_ endpoint
(`GET /api/vm/events`), not the SSE route itself.

## Why it matters

If a future change to `_vm_sse_generator`/`_live_cluster_sse_generator` (or the `_collect_blob_names`/
`_fetch_and_parse_event` primitives they call) accidentally started synthesizing a placeholder row on an empty prefix,
nothing in CI would catch it — the only two tests for this route don't iterate the generator at all. This is exactly the
failure mode the workspace's honest-absence rules exist to prevent (a UI pane silently showing a fabricated event for a
VM that never emitted one), and it currently depends entirely on the code staying correct by inspection, not on an
enforced regression guard.

## Recommended decision

Add a unit test mirroring the established `test_vm_events.py::test_empty_bucket_returns_zero_events` pattern (a fake
storage client returning zero blobs), but drain `_vm_sse_generator` (and ideally `_live_cluster_sse_generator`) via its
async generator protocol and assert: zero `vm_event` frames, at least one `heartbeat` frame, no `done` frame. A second
test with a fake client returning 1-2 real-shaped blobs should assert the corresponding `vm_event` frames are yielded
with the correct `VmLogLine` field mapping. Bound the generator drain (e.g. `asyncio.wait_for` / a max iteration count)
since both generators are literal `while True` loops with no natural termination.

## Todos

- [ ] [BACKEND] P3. Add `tests/unit/test_route_log_stream.py` coverage that actually drains `_vm_sse_generator` (fake
      storage client, zero blobs) and asserts heartbeat-only / zero-vm_event / no-fabricated-row, mirroring
      `test_vm_events.py::test_empty_bucket_returns_zero_events`'s `_FakeStorageClient` pattern. (repo: deployment-api)
- [ ] [BACKEND] P3. Add a second case in the same test file: a fake storage client returning 1-2 real-shaped blobs,
      asserting the drained generator yields the matching `vm_event` frames with correct `VmLogLine` field mapping
      (timestamp/event/severity/message). (repo: deployment-api)
