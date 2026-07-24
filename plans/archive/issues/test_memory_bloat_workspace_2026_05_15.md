---
doc_type: issue
title: Python test suites are 2-3 GB RSS per run — investigate + reduce module-import bloat
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, execution-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-15
author: harsh-main (audit pass)
resolved: 2026-05-15
resolution:
  STRUCTURAL-FIX-SHIPPED — 10 GB per-process RSS cap via PYTEST_WORKERS=1 + ulimit/memray instrumentation (post-OOM
  hardening). No more 79 GB runaway processes possible. Audit shows current peak ~3 GB (well within cap). Per-repo
  memray audit + UTL <1 GB RSS optimization is a NICE-TO-HAVE follow-up, NOT blocking May-23.
source:
  [
    2026-05-15 OOM incident (PM@c3cb11f6 + ca3fad47 mitigation landed),
    "Live ps audit during 6-slot concurrent QG runs (2026-05-15 23:50 UTC)",
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-15
severity: P2 — not blocking May-23; impacts dev-box concurrent-QG capacity + GHA cost-per-run
suggested_owner: ikenna-side OR opus-max-tier slot (memory-profiling + import-graph surgery is design work)
---

> **🟢 RESOLUTION VERIFIED 2026-05-20** — structural fix shipped at `unified-trading-pm@c3cb11f6` (`QG_MEM_CAP=10G`
> per-subprocess cap via systemd-run) + `unified-trading-pm@ca3fad47` (`PYTEST_WORKERS=1` default + macOS warning path).
> SSOT `/codex/06-coding-standards/quality-gates-memory-governance.md`. No more runaway >10 GB processes possible;
> current peak ~3 GB well within cap. Per-repo memray audit + UTL <1 GB optimisation is explicit NICE-TO-HAVE not
> blocking May-23 (operator-acked at issue-doc filing). Archiving.

## TL;DR

Live audit during 6 concurrent slot QGs (2026-05-15 23:50 UTC) shows individual pytest workers consistently hitting
**2.5-3 GB RSS**. UTL specifically peaks at **3 GB per worker** with `-n 2` xdist = ~6 GB for one full QG. That's high
for a Python service test suite and likely indicates eager module imports + session-scoped fixture bloat. Today's OOM
was the symptom; this is one of the root causes.

GitHub Actions runs are fine (`ubuntu-latest` = 16 GB, 5× headroom). The cost is paid on:

- **Local dev box**: 6 slots × 3 GB = 18 GB concurrent. Plus VS Code basedpyright langserver (~2 GB workspace-wide scan)
  and pyenv pytest auto-discovery (~0.5 GB × 10 repos) pushes us toward OOM under load. Today's incident hit ~25 GB
  before the kernel killed a runaway process.
- **GHA wall-clock cost**: bigger tests take longer + cost more per CI run.

## Live measurements (2026-05-15 23:50 UTC)

Snapshot during 6 slots running QG concurrently (slots 2/3/4/5/7/8):

| Slot   | Repo                    | Process             | RSS         | %CPU                  |
| ------ | ----------------------- | ------------------- | ----------- | --------------------- |
| 6      | unified-trading-library | pytest worker       | **2.95 GB** | 64%                   |
| 3      | unified-trading-library | pytest worker       | **2.75 GB** | 90%                   |
| (main) | unified-trading-library | pytest worker       | **2.62 GB** | 65%                   |
| 4      | ml-training-service     | pytest worker       | 0.99 GB     | (transient peak 874%) |
| 5      | execution-service       | pytest worker       | 0.79 GB     | low                   |
| 2      | deployment-service      | pytest workers (×2) | 0.69 GB ea. | 103% ea.              |
| 7      | deployment-api          | pytest worker       | 0.61 GB     | (transient)           |

**The top three are all UTL pytest**. UTL is the outlier — every other repo's QG runs under 1 GB per worker. UTL is 3×
heavier.

## Likely culprits (hypotheses to validate, not confirmed)

1. **Eager top-level imports in `unified_trading_library/__init__.py`** — numpy + pandas + pyarrow + boto3 +
   google-cloud-\* on every import. Each ~100-500 MB resident.
2. **Session-scoped fixtures with large fakes** — synthetic parquet files, GCS mock buckets, in-memory DataFrames held
   across the session in `conftest.py`.
3. **`-n 2` xdist worker overhead** — each xdist worker re-imports the full module graph. 1.5 GB × 2 = 3 GB matches the
   live measurement.
4. **Long-lived test collection** — VS Code pytest auto-discovery (`vscode_pytest`) keeps a separate ~0.5 GB process per
   repo alive in the background (not part of QG but visible in the same memory pool).

## Required action (Ikenna / opus-max)

This is **memory-profiling + import-graph surgery**, not a mechanical fix. Sonnet won't do this well. Suggested steps
for whoever picks it up:

1. **Baseline measure** — run a single UTL QG with `memray` or `tracemalloc` in-process. Capture which imports are
   responsible for the first 1 GB and which fixtures hold the next 1 GB.

   ```bash
   cd unified-trading-library
   memray run -o memray.bin -m pytest tests/unit/ -n 0  # single worker
   memray summary memray.bin
   memray flamegraph memray.bin
   ```

2. **Eager-import audit** — grep `unified_trading_library/__init__.py`
   - every `__init__.py` in the package tree for top-level imports of pandas / numpy / pyarrow / boto3 /
     google-cloud-\*. Move heavy deps behind `if TYPE_CHECKING:` or function-scope imports.

3. **Session-fixture audit** — every `conftest.py` `@pytest.fixture(scope="session")` that holds DataFrames / parquet
   bytes / mock GCS buckets. Convert to function-scope or use lazy generators where possible.

4. **xdist sizing decision** — `PYTEST_WORKERS=1` (today's default per PM@c3cb11f6) halves the in-process memory but
   doubles wall-clock. Audit whether key repos can drop to `-n 1` permanently. For UTL specifically, given the 3
   GB-per-worker number, **single-worker mode may be the right default for UTL** until import bloat is fixed.

5. **Per-repo memray report filed** — for each repo with QG > 1 GB peak, file a per-repo issue doc with the memray
   flamegraph + top-3 offenders listed. Track in master plan.

## Why this is P2 (not P0/P1)

- **GHA is unaffected** — `ubuntu-latest` has 16 GB, our 3 GB peak is well within limits. Single-job CI runs
  comfortable.
- **Local dev box mitigation is in place** — PM@ca3fad47 caps each subprocess at 10 GB and sets `PYTEST_WORKERS=1`
  default. The OOM-killer event today was a one-off (likely a runaway basedpyright langserver during heavy workspace
  scan, not a QG worker).
- **No May-23 critical path blocked.**

But left unaddressed:

- Concurrent-QG capacity on dev box stays at 6 slots × 3 GB = on the edge
- GHA cost per minute creeps up as more tests are added
- The next memory-related incident is just one bad import away

## Adjacent fixes already shipped today

- PM@c3cb11f6 — `QG_MEM_CAP` env (default 10G) caps each pytest/basedpyright subprocess via
  `systemd-run --user --scope -p MemoryMax`. Linux-only.
- PM@ca3fad47 — `PYTEST_WORKERS=1` default + OLD/NEW comment pattern in base-service.sh + macOS warning path. SSOT
  `/codex/06-coding-standards/quality-gates-memory-governance.md`.
- The cap **works** — today's audit shows no process near 10 GB; the 3 GB peaks are well within the cap. No more 79 GB
  runaway processes possible.

## Where the GHA runner spec lives (one-line SSOT)

`unified-trading-pm/.github/workflows/python-quality-gates.yml:32` → `runs-on: ubuntu-latest`. Every Python service
repo's `quality-gates.yml` calls this reusable workflow, so changing this one line cascades workspace-wide.

Standard GitHub-hosted Linux runner sizes (Dec-2023 onward):

- `ubuntu-latest` (default): **4-core, 16 GB RAM** — current
- `ubuntu-latest-8-cores`: 8-core, 32 GB
- `ubuntu-latest-16-cores`: 16-core, 64 GB

If a specific QG ever needs more (e.g. ml-training-service with real model training): use the bigger label per-repo via
a workflow input — don't bump the global default.

execution: owner: ikenna-main (pending ack) OR harsh-main on opus-max slot cadence: one-shot memray audit + per-repo fix
passes verifier: UTL QG peak RSS < 1 GB; total concurrent-QG peak < 6 GB across 6 slots; GHA QG wall-clock unchanged or
improved last_executed: NEVER
