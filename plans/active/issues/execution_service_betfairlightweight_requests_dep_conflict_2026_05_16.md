---
title: "execution-service pyproject — betfairlightweight + requests version conflict blocks SIT uv sync"
created: 2026-05-16
author: ikenna-main (workspace-qg Phase B failure-mode sweep)
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

But every non-yanked release of `betfairlightweight>=2.20` requires `requests<2.33.0`. So the
intersection is empty.

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
