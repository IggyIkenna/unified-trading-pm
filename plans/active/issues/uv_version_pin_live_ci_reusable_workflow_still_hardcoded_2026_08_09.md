---
doc_type: issue
title: UV_VERSION centralization missed the truly-live CI reusable workflow copy in unified-trading-ci
summary:
  'infra_satellite_ao_dispatch_batch9_2026_08_09.md item 1 centralized the uv `0.10.8` pin into a single canonical
  `UV_VERSION` constant and fixed all 6 sites the plan named — including
  `unified-trading-pm/scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml`. That file turned out to
  be a point-in-time snapshot (per `hosted-baseline.sh`''s own header: ''snapshot / restore / audit the PRISTINE
  GitHub-hosted form of every workflow''), not the workflow that actually fires in CI. The real, live copy — the one
  every repo''s `quality-gates-v2.yml` caller references via `uses:
  IggyIkenna/unified-trading-ci/.github/workflows/python-quality-gates-v2.yml@main` — lives in the separate
  `unified-trading-ci` repo and still has the literal `pip install "uv==0.10.8"` hardcoded at its ''Install uv'' step.
  Confirmed via diff: the two files have already diverged in other ways too (unified-trading-ci is ahead), so they are
  not kept in sync automatically. Out of scope for the batch-9 plan (its own `repos: [unified-trading-pm]` frontmatter),
  so filed here rather than expanding that plan''s scope.'
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-ci]
scope: [engineer, admin]
tags: [infra, uv, ci-cd, uv-lockfile-determinism, drift]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/infra_satellite_ao_dispatch_batch9_finalize_2026_08_09.md,
  ]
created: 2026-08-09
parent_epic: infrastructure_master
priority: P3
assigned_vm: planning
author: slot-11 (infra)
source: ["plans/active/infra_satellite_ao_dispatch_batch9_2026_08_09.md"]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

While shipping `infra_satellite_ao_dispatch_batch9_2026_08_09.md` item 1 (centralize the uv version pin), I traced the
plan's named GHA-workflow site —
`unified-trading-pm/scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml` — to confirm the fix
mechanism would actually work. Discovered it's a **snapshot**, not the live template: `hosted-baseline.sh`'s own header
documents this directory as a backup of the pristine GitHub-hosted form of every workflow, used for
`restore`/`diff`/`verify`, not the file GitHub Actions actually executes.

The real, executing copy of this reusable workflow lives in a **different repo**: `unified-trading-ci`
(`.github/workflows/python-quality-gates-v2.yml`), referenced by every service repo's caller
(`uses: IggyIkenna/unified-trading-ci/.github/workflows/python-quality-gates-v2.yml@main`, confirmed in e.g.
`alerting-service/.github/workflows/quality-gates-v2.yml`). A `diff` between the two files shows they have already
drifted apart in unrelated ways (unified-trading-ci is ahead — has newer inputs/steps the PM snapshot lacks), so fixing
the PM snapshot does NOT propagate to the live workflow.

`unified-trading-ci/.github/workflows/python-quality-gates-v2.yml`'s "Install uv" step (around line 372-378) still has:

```yaml
- name: Install uv
  ...
  run: pip install "uv==0.10.8"
```

## Why it matters

This is the actual mechanism that pins `uv` in every repo's real CI run (the plan's own fixed sites cover
local/VM-bootstrap paths: `setup.sh`, `workspace-bootstrap.sh`, `base-service.sh`/`base-library.sh`'s drift-guard). The
live CI uv-install site was never actually fixed — it still independently hardcodes `0.10.8`, so a future uv-version
bump would need a 7th edit site, not 6, and the batch-9 plan's own "Done when" grep check (scoped to
`unified-trading-pm` only) cannot catch this since the drift lives in a sibling repo.

## Recommended decision

Apply the same fix pattern used in the PM snapshot's corresponding step: fetch
`unified-trading-pm/scripts/workspace/resolve-canonical-versions.py`'s `UV_VERSION` constant directly (the dependency
self-clone step in that workflow hasn't run yet by the time "Install uv" fires, so a direct authenticated raw-content
fetch is needed, same as the PM-repo snapshot fix — see that file's "Install uv" step, committed
unified-trading-pm@e5697ac5c, for the exact working pattern to port over), then
`pip install "uv${UV_VERSION:+==$UV_VERSION}"`. Bounded, deterministic-outcome change — single step, single file, no
design judgment needed.

- [ ] [INFRA] P3. Port the `unified-trading-pm` snapshot's "Install uv" fix (unified-trading-pm@e5697ac5c,
      `scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml`) into the LIVE copy at
      `unified-trading-ci/.github/workflows/python-quality-gates-v2.yml`'s "Install uv" step — replace the hardcoded
      `pip install "uv==0.10.8"` with the same canonical-fetch-then-install pattern. Verify a real workflow run still
      installs uv successfully post-change (a green quality-gates-v2 run on any repo touching that workflow). (repo:
      unified-trading-ci)

## Progress Log

- 2026-08-09 (slot-11): Filed during batch-9 item 1 shipping. Not fixed inline — different repo than the plan's `repos:`
  scope, and touching CI-firing infra in a repo I wasn't dispatched against would be scope creep per `infra.md`'s craft
  rules.
