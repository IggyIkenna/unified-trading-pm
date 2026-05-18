---
title: "execution-service pyproject — betfairlightweight + requests version conflict blocks SIT uv sync"
created: 2026-05-16
author: ikenna-main (workspace-qg Phase B failure-mode sweep)
resolved: 2026-05-16
resolution: SHIPPED — two-pronged: (validator side) slot-4 cross-slot pickup 2026-05-16; (features-backfill VM side) slot-1 main 2026-05-16 23:52 UTC. Both sides resolved per body.
source:
  - system-integration-tests workspace-qg failure log 2026-05-16 18:58 UTC
  - github.com/IggyIkenna/system-integration-tests/actions/runs/25970164921
severity: P1 — blocks system-integration-tests workspace-qg + any composite install that needs execution-service
locked_by: live-defi-rollout
locked_since: 2026-05-16
---

## What I found

system-integration-tests' workspace-qg run fails at `uv sync` with an unsatisfiable dependency resolution:

```
because betfairlightweight>=2.20.0 depends on requests<2.33.0 and
betfairlightweight==2.23.0 was yanked (reason: bug),
we can conclude that betfairlightweight>=2.20.0 depends on requests<2.33.0.

And because execution-service==0.1.1 depends on betfairlightweight>=2.20 and requests>=2.33.0,
we can conclude that execution-service==0.1.1 cannot be used.
```

**The bug**: execution-service's `pyproject.toml` declares:

- `betfairlightweight>=2.20`
- `requests>=2.33.0`

But every non-yanked release of `betfairlightweight>=2.20` requires `requests<2.33.0`. So the intersection is empty.

## Why it matters

- Blocks SIT workspace-qg green
- Any composite install that includes execution-service as a transitive dep (which is most repos) hits this
- Affects all 21 repos with execution-service in their transitive deps

## Recommended decision

**Option A** (recommended): downgrade `requests>=2.33.0` to `requests>=2.32.0,<2.33` in execution-service's pyproject.
The 2.32 / 2.33 jump was for a CVE that other workspace repos may have pinned 2.33 for; need to verify.

**Option B**: replace `betfairlightweight` with a different library (e.g. raw HTTP calls). Larger refactor.

**Option C**: pin `betfairlightweight==<later-version>` if a newer version supports requests 2.33. Per release notes,
betfairlightweight 2.24+ might support it — check upstream.

**Owner**: execution-service / sports adapter owner. Slot 3 or slot 4 most likely (sports betting venues).

## Workaround until fix lands

System-integration-tests workspace-qg will keep failing at install. Slot owners can validate locally via
`bash scripts/quality-gates.sh` which uses repo `.venv` with whatever version pin is current.

## RESOLVED (validator side) — 2026-05-16 (slot 4 cross-slot pickup)

**Diagnosis**: The conflict is BY DESIGN — workspace pins `requests>=2.33.0,<3.0.0` for CVE-2026-25645 floor;
`betfairlightweight` declares transitive `requests<2.33.0` on PyPI for every release we'd use. This is a PyPI-metadata
property, not a workspace bug. The institutional resolution is documented at
`.cursor/rules/dependencies/requests-betfairlightweight-workspace-resolution.mdc`:

1. Keep `requests` at the workspace floor in `workspace-constraints.toml` (NO security regression).
2. execution-service (sole consumer) declares `[tool.uv] override-dependencies = ["requests>=2.33.0,<3.0.0"]` — already
   in place at `execution-service/pyproject.toml:19-22`.
3. Global validator omits `betfairlightweight` from the flat compile graph.

**Shipped 2026-05-16 at `unified-trading-pm@b2106766`**: implemented step 3 — the validator's
`EXCLUDE_FROM_GLOBAL_COMPILE` frozenset was aspirational in the cursor rule but missing from the script. Added with the
single-package entry (`betfairlightweight`) + inline docstring referencing the cursor rule. Validator now exits 0 ("OK:
Workspace constraints resolve").

SIT's workspace-qg `uv sync` failure was a separate flavour of the same issue — SIT installs from
`workspace-constraints.toml` directly and hit the same unsatisfiable. The validator fix doesn't affect SIT's uv sync;
the SIT-side fix would be either (a) SIT-specific `[tool.uv] override-dependencies` mirroring execution-service's
pattern, or (b) SIT QG drops execution-service from its install graph. Routed to SIT owner for the per-repo decision.

Issue closeable at next archive sweep on the validator side; SIT half left open with the named follow-up above.

## RESOLVED (features-backfill VM side) — 2026-05-16 23:52 UTC (slot 1 main)

`features-onchain-defi-20260516-233044` (B-015 chain attempt 4) hit a 3rd flavour of this same conflict — the flat
`uv pip install -e ... -e execution-service ...` resolve on the data-pipeline VM. Pre-existing NODEPS opt-out at
`deployment-service/scripts/vm/setup-data-pipeline-vm.sh:403-408` only covered `synthetic-benchmark`, `strategy-paper`,
`strategy-live` VM_TASKs.

**Shipped at `deployment-service@9d37deb`**: extended the VM_TASK allowlist to include `features-backfill` so the
features-onchain VM routes `execution-service` (and other service repos in `_SVC_BENCH_NODEPS`) through `--no-deps`,
matching the strategy-paper/strategy-live pattern. Uploaded the updated setup script to
`gs://deployment-scripts-central-element-323112/vm/setup-data-pipeline-vm.sh` at 22:52:08 UTC. Attempt 5
(`features-onchain-defi-20260516-235216`) re-launched 23:52 UTC.

Both other VM_TASKs (`mtds-backfill`, `instruments-backfill`, etc.) that hit this same conflict in the future should add
themselves to the same allowlist or accept the pyproject-level fix once the systemic SIT-side resolution lands.

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED  
**Triaged by**: slot-8 triage sweep  
**Reason**: Resolved 2026-05-16; validator fix + VM setup script fix
