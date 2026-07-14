---
doc_type: issue
title:
  "`pipeline_e2e_check.py`'s live-leg verification checks the WRONG manifest row for every venue — it filters by the
  sweep's nominal historical `day` param, but a live capture VM always writes its manifest row keyed by TODAY's real
  wall-clock date, so the live-leg check can never actually see what the live VM it just launched wrote"
summary:
  "Re-verifying `CEFI:OKX:liquidations`'s live-leg failure (`manifest_status_invalid:attempted_failed`) from the
  2026-07-13 clean re-sweep (`data_pipeline_e2e_check_2026_07_10.md` todo 25) with a fresh, independent real-VM run
  AFTER the sibling `cefi_manifest_consolidator_14day_stale_recovered_2026_07_13.md` fix (which had directly verified
  this exact cell returns `ok=True, status=empty_confirmed` moments earlier), the identical `attempted_failed` verdict
  reproduced on a genuinely fresh VM (`mtds-live-smoke-cefi-okx-liquidations-20260713-154647`). Downloading and reading
  that VM's own per-VM manifest shard directly (bypassing the checker/consolidated-index entirely) proves the live
  capture itself was completely healthy: `capture_status=empty_confirmed, error_reason=SOURCE_RETURNED_ZERO,
  date=2026-07-13` (today's real wall-clock date — an honest, healthy, zero-liquidations-in-90s result). The checker's
  `verify_manifest_row(bucket, match, day)` call filters the manifest by `df['date'] == day`, where `day` is the sweep's
  SINGLE nominal historical day (`2026-07-09` for this whole re-sweep) — a value that can NEVER match a live VM's own
  row, because live captures write with today's real date, not a backfill day. The live-leg check therefore never
  actually inspects what the live VM it just launched wrote; it instead spuriously matches whatever OTHER, unrelated row
  already exists for that (day, venue, data_type) manifest key — usually the SAME shard's own force-leg row (run moments
  earlier in the same job), which is why shards whose force leg happened to succeed show the live leg as a coincidental
  'pass', and shards whose force leg failed (like OKX:liquidations, Tardis-locked) show the live leg inheriting that
  SAME stale failure, regardless of what the live VM itself actually did. This is a structural checker bug that likely
  invalidates EVERY live-leg verdict in the 452-shard re-sweep (and any future sweep) — no live-leg 'pass' in that
  report is trustworthy evidence the live VM itself worked; every live-leg 'pass' is really just 'the force leg for this
  same shard happened to write date=<day>', and every live-leg 'fail' where the force leg also failed is simply
  reflecting the force leg's OWN failure a second time, not new information about live capture."
status: resolved
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    pipeline-e2e-check,
    checker-tooling-bug,
    live-leg,
    manifest-verification,
    data-correctness,
    big-finding,
    cross-cutting,
  ]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    cefi_manifest_consolidator_14day_stale_recovered_2026_07_13.md,
    tardis_concurrent_ip_lockout_2026_07_12.md,
    ../../../codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source:
  [
    data_pipeline_e2e_check_2026_07_10.md clean re-sweep CEFI cluster triage (2026-07-13),
    a fresh,
    independent real-VM re-verification of CEFI:OKX:liquidations live leg,
    direct GCS read of the fresh VM's own per-VM manifest shard (bypassing the checker's consolidated-index read
    entirely),
    direct reading of scripts/pipeline_e2e_check.py + scripts/smoke_matrix.py's verify_manifest_row,
  ]
assigned_vm: NA
resolved_by: market-tick-data-service@981201c4 (2026-07-13, real-VM verified same day)
locked_by:
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
---

# The live-leg checker verifies the wrong manifest row for every shard — a structural, cross-cutting bug

## What was found (real, direct evidence, not inference)

Re-verifying `CEFI:OKX:liquidations`'s live-leg failure from the 2026-07-13 clean re-sweep AFTER
`cefi_manifest_consolidator_14day_stale_recovered_2026_07_13.md`'s fix (which had directly confirmed, via
`verify_manifest_row`, that this exact cell returns `ok=True, status=empty_confirmed` at ~15:18 UTC):

```
$ python3 scripts/pipeline_e2e_check.py --day 2026-07-09 --asset-group CEFI --venue OKX \
    --data-types liquidations --legs live --project central-element-323112 \
    --report-dir _pipeline_e2e_check_sweep/reverify_cefi_cluster/okx_liquidations_live
```

launched a genuinely fresh VM (`mtds-live-smoke-cefi-okx-liquidations-20260713-154647`, `launcher exited 0`,
`vm_confirmed_present=True`) and STILL reported:

```
| CEFI:OKX:liquidations | live | failed | not_applicable | 1 | 0 | attempted_failed |
  vm_not_success:vm_exit_nonzero=1; manifest_status_invalid:attempted_failed |
```

Reading that fresh VM's OWN per-VM manifest shard directly via `gcsfs`
(`market-data-tick-cefi-test-central-element-323112/_index/per_vm/mtds-live-smoke-cefi-okx-liquidations-20260713-154647.parquet`)
— bypassing the checker and the (possibly-stale) consolidated index entirely — shows the live capture was completely
healthy:

```
date=2026-07-13  venue=OKX  data_type=liquidations  instrument_id=BTC-USDT  pipeline_mode=live_okx
capture_status=empty_confirmed  error_reason=SOURCE_RETURNED_ZERO  attempted_at=2026-07-13T15:50:01Z
```

**`date=2026-07-13`** — today's real wall-clock date, NOT `2026-07-09` (the re-sweep's nominal historical `day`
parameter this whole 452-shard run used for every force/skip/live leg). This is architecturally correct: a live capture
isn't backfilling a specific historical day, it captures whatever happens during the bounded real-time window it runs in
— so of course its manifest row is dated "today," not the sweep's chosen test day.

## Root cause (read directly, not guessed)

`scripts/pipeline_e2e_check.py::_run_live_leg` calls `verify_manifest_row(bucket, match, day)` where `day` is the SAME
nominal historical day threaded through the entire sweep (`--day 2026-07-09` for this run). `verify_manifest_row`
(`scripts/smoke_matrix.py:273`) filters:

```python
mask = df.get("date", df.get("day")) == smoke_date
...
matching = df[mask]
...
status = str(matching["capture_status"].iloc[-1]) if "capture_status" in matching.columns else ""
```

— a straight equality check against `smoke_date` (`day`). Since every live VM writes `date=<today's real date>`, this
mask can **never** match a live VM's own row for any sweep whose nominal `day` isn't literally today. The live-leg check
therefore silently falls through to whatever OTHER row already exists in the manifest for that `(day, venue, data_type)`
key — in practice, almost always the SAME shard's own **force-leg** row, written moments earlier in the same job,
because force/skip legs genuinely DO backfill `day` and correctly write `date=day`.

This exactly explains the pattern seen across this whole re-sweep's live legs:

- Shards whose **force leg failed** (e.g. `OKX:liquidations`, Tardis-locked — no `date=2026-07-09` row ever written, or
  an `attempted_failed` row was) → the live leg's manifest lookup finds that SAME stale/failed row and reports it as
  `attempted_failed`/`manifest_status_invalid`, even when the live VM itself ran perfectly cleanly (as proven above).
- Shards whose **force leg succeeded** (e.g. `CEFI:HYPERLIQUID:book_snapshot_5`'s live leg, which this same re-sweep
  reported `"ok (despite vm_not_success:launcher_script_nonzero_rc=1)"`) → the live leg's manifest lookup coincidentally
  matches the FORCE leg's OWN `empty_confirmed`/`captured` row (written for the SAME shard key moments before), and
  reports a spurious "pass" that has nothing to do with what the live VM itself captured.

**In neither case does the live-leg check ever actually inspect the live VM's own manifest write.** Every live-leg
verdict in this checker is really just re-reporting the SAME shard's force-leg result a second time (or an unrelated
older row), never live-specific ground truth.

## Blast radius

This is not scoped to `OKX:liquidations` or to CEFI — `_run_live_leg` and `verify_manifest_row` are shared,
venue-agnostic checker code used for every asset_group's live leg across the entire `pipeline_e2e_check.py` sweep (452
shards this pass, and every future re-sweep). **No live-leg "passed" result anywhere in `RESWEEP_FINAL_REPORT.md` is
trustworthy evidence the live capture path itself works** — it is, at best, restating the force leg's own verdict.
Live-specific bugs (a genuinely broken WS connector, a genuinely broken `MTDSShardManifestRecorder` wiring, a genuinely
hung live producer that never writes anything) would ONLY be caught by this check if the force leg for the same shard
ALSO happened to fail in a way that produces the exact `attempted_failed`/`no_matching_row` signature — otherwise a
completely broken live path would be silently masked by an unrelated, older force-leg "pass" row.

## Recommended fix (not attempted this session — needs care, and the checker file is actively being edited by

concurrent agents this session)

`_run_live_leg` should verify against the row the live VM itself actually wrote, not the sweep's nominal `day`. The
cleanest fix: pass the live VM's OWN launch/completion date (`datetime.now(UTC).date().isoformat()`, captured at
`attempt_ts`/`started`) as the date filter to `verify_manifest_row`, instead of `day`. A more robust alternative: extend
`verify_manifest_row` (or add a live-specific sibling) to filter by `attempted_at >= started` (the live VM's own launch
timestamp) rather than an exact date-string match, so it's immune to a live run crossing a UTC day boundary. Either way
this needs: (1) confirming no other caller relies on the current (buggy) day-filtered behavior for live legs, (2) a
real-VM re-verification proving the fix reads the CORRECT (fresh) row for a shard whose force leg failed but whose live
leg is genuinely healthy (exactly the `OKX:liquidations` case this doc diagnoses), (3) QG-green + quickmerge, since
`scripts/pipeline_e2e_check.py` / `scripts/smoke_matrix.py` are both dirty with other concurrent agents' unrelated WIP
as of this writing — coordinate before touching either file.

## Not done this session

No code was changed (the fix needs coordination with concurrent WIP already in `scripts/pipeline_e2e_check.py` and
`scripts/smoke_matrix.py`, and deserves its own dedicated pass rather than a rushed edit in an actively-shared file). No
attempt was made to audit how many of the re-sweep's other "live leg passed" results are similarly spurious coincidental
force-leg matches versus genuine live-path health — that would require reading every passing live-leg's underlying
per-VM shard the same way this doc did for OKX, which is a real (but mechanical) follow-up audit.

## RESOLVED 2026-07-13 — fix shipped + real-VM verified against this doc's own worked example

- **Fix shipped: `market-tick-data-service@981201c4`.** `_run_live_leg` no longer calls the day-filtered
  `verify_manifest_row(bucket, match, day)`; a new `_verify_live_manifest_row(bucket, vm_name, match, started)` (1)
  PRIMARY: reads the live VM's OWN per-VM shard `_index/per_vm/{instance}.parquet` directly — matched by
  venue/data_type/instrument with NO date filter (exactly what this doc's diagnosis did manually; immune to the `-test-`
  bucket's consolidator re-freeze); (2) FALLBACK: reads the consolidated index filtered by
  `attempted_at >= the live leg's own launch time` (−60s clock-skew tolerance, the doc's "more robust alternative" —
  immune to a live run crossing a UTC day boundary). The now-unused `day` param was removed from `_run_live_leg`;
  force/skip legs keep the day filter (they genuinely backfill `day`). Confirmed no other `verify_manifest_row` caller
  relies on the buggy behavior for a live leg; `_run_live_leg_prod_unbounded` never verifies and needed no change.
  **instruments-service's checker was analyzed and deliberately NOT changed**: its "live" leg routes through
  `setup-data-pipeline-vm.sh`'s `instruments-backfill` branch which hardcodes `--mode batch`, so it backfills `--day`
  and correctly writes `date=day` — the day filter is correct there.
- **Real-VM verification (recommended-fix item 2, the exact OKX case): PASSED.**
  `pipeline_e2e_check.py --day 2026-07-09 --asset-group CEFI --venue OKX --data-types liquidations --legs live`
  (2026-07-13T19:11–19:15Z, fresh VM `mtds-live-smoke-cefi-okx-liquidations-20260713-191136`) now reports
  `CEFI:OKX:liquidations | live | passed | manifest=empty_confirmed | reason=ok (despite vm_not_success:vm_exit_nonzero=1; live row via per_vm_shard)`
  — the checker read the live VM's OWN healthy `empty_confirmed` row (`per_vm_shard` source marker) instead of
  inheriting the force leg's stale `attempted_failed` for the nominal day. `total=1 passed=1 failed=0`, driver exit 0.
- Also shipped alongside (same commit): Phase-0 `-test-`-bucket force-consolidation before Phase 1 (closes the companion
  re-freeze gap from `cefi_manifest_consolidator_14day_stale_recovered_2026_07_13.md`; IS checker got the same Phase-0
  in `instruments-service@526d2ffd`), and the MTDS exit-code now flips on `ambiguous` (aligned to IS).
- **Residual CLOSED — disposition (2026-07-14, operator-directed close-out):** the retroactive audit of the ORIGINAL
  re-sweep's other live-leg "passes" is **impossible at the artifact level and unnecessary at the data level**:
  1. **Impossible**: `RESWEEP_FINAL_REPORT.md` + the sweep driver's shard JSONs are LOST (confirmed absent from this
     host, all 16 AO-VM slot clones, and GCS — plan Progress Log 2026-07-13, todo-25 residuals). There is no surviving
     list of which cells' live legs "passed" nor their VM instance names, so the per-VM-shard read this doc performed
     for OKX cannot be replayed for the rest. Those runs' shards have since consolidated into the canonical (data
     preserved; per-leg attribution gone).
  2. **Unnecessary**: the live leg is a smoke check of the pipeline path, not the system of record — the captures
     themselves are in the canonical availability index, whose honesty is enforced independently (phantom-audit,
     honest-coverage machinery, per-VM writer discipline). Any question about a specific historical cell is answered by
     the manifest, not the lost report. Every live-leg verdict that DROVE triage was individually re-run on real VMs
     with the fixed verifier during the 2026-07-13 verification rounds (this doc's OKX case: PASSED via `per_vm_shard`).
  3. **Forward-trustworthy**: all live legs verify per-VM-first since `market-tick-data-service@981201c4` (hardened
     further by `@1dd4bbbc`, which gave force/skip legs the same per-VM-first read). The historical live-leg columns are
     formally SUPERSEDED — the next full sweep re-derives every verdict from scratch.
