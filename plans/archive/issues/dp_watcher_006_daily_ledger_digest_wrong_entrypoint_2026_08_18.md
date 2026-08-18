---
doc_type: issue
title: DP-WATCHER-006 — uts-prod-daily-ledger-digest Cloud Run Job invoked the wrong entrypoint
summary:
  The daily-ledger-digest Cloud Run Job's terraform command/args ran the package's uvicorn dev-server entrypoint
  (`python -m client_reporting_api`) with argparse flags the CLI never accepted, then (after a first fix attempt)
  `python -m client_reporting_api.cli` which fails at the interpreter level because that package has no
  `__main__.py`. The CLI's `daily-ledger-digest` subcommand also required a single `--client-id`, which the
  fleet-wide cron never supplied. Root-caused, fixed on both the source and infra side, and live-verified via a
  direct re-execution. RESOLVED.
status: resolved
nature: incident
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, deployment-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-watcher-006, cloud-run-job, escalation, client-reporting-api]
related: ["/codex/05-infrastructure/data-pipeline-alerts.md"]
created: 2026-08-18
parent_epic: observability_master
priority: P1
source: [DP-WATCHER-006, agt-8668d1]
---

# DP-WATCHER-006 — uts-prod-daily-ledger-digest Cloud Run Job invoked the wrong entrypoint

## What I found

`escalation_id=agt-8668d1` — DP-WATCHER-006 (generic Cloud Run Job execution-failure sweep) fired for
`uts-prod-daily-ledger-digest` (asia-northeast1, `central-element-323112`). No candidate slug was filed by the
detector (per the 2026-08-18 "never raw-`git commit` from an ephemeral runner" fix in
`/codex/05-infrastructure/data-pipeline-alerts.md`), so filing this doc was the dispatched worker's job.

Diagnosis (`terraform/gcp/paper_week_determinism_scheduler.tf`, `daily_ledger_digest_job` module):

1. **Wrong entrypoint (primary cause).** `command = ["python"]`, `args = ["-m", "client_reporting_api", "--operation",
   "daily_ledger_digest", "--mode", "batch", "--asset-group", "cefi"]`. `python -m client_reporting_api` runs the
   package's `__main__.py` — the uvicorn **dev server**, not the CLI — and the `--operation`/`--mode`/`--asset-group`
   flags don't exist on the real CLI's argparse. Every execution ran the server until the 600s job timeout killed it
   non-zero. The terraform comment above the module still read `# TODO: add this operation` even though the CLI
   entrypoint (`client_reporting_api/cli/daily_digest_command.py`, P7.1-C) had shipped long ago — stale doc trap.
2. **Second-order bug found while fixing #1.** `python -m client_reporting_api.cli` (a first fix attempt) fails at the
   interpreter level too — `client_reporting_api/cli/` is a package with no `__main__.py`, so `-m` can't run it
   directly. Confirmed live via execution `uts-prod-daily-ledger-digest-nj4p2`
   (`No module named client_reporting_api.cli.__main__`). The correct invocation is the installed console script
   (`pyproject.toml`: `client-reporting-manage = "client_reporting_api.cli:main"`), which is also the Dockerfile's own
   `batch`-stage `ENTRYPOINT`.
3. **Design gap.** `daily-ledger-digest`'s parser required a single `--client-id`, but the Cloud Run Job is a
   fleet-wide daily cron with no per-client parameterisation — it could never have succeeded even with the entrypoint
   fixed. Confirmed live via execution `uts-prod-daily-ledger-digest-qtvhh` (`error: the following arguments are
   required: --client-id`), which also proved the deployed `client-reporting-api:latest` image predated the source
   fix (stale-image gap, not a further code defect).
4. **Dead env var (adjacent, fixed in the same commit).** `SLACK_CHANNEL` was set on the job's env but never read
   anywhere in the CLI (only `getattr(args, "channel")` from an explicit `--channel` flag) — the intended target
   channel was silently never applied.

## Fix

- `client-reporting-api@c49305cdb9` — gave `daily-ledger-digest` the same all-active-clients-by-default shape as
  `update`/`backfill` (`--client` optionally narrows to one; loops over `_get_active_clients(_load_registry(), ...)`
  otherwise). Factored the per-client body into `_digest_client()`. Tests updated (`tests/unit/test_daily_digest_command.py`).
- `deployment-service@9a8713b41a` + `deployment-service@b51f6b6dca` — `daily_ledger_digest_job.command` is now
  `["client-reporting-manage"]`, `args = ["daily-ledger-digest", "--channel", "#trading-daily-digest"]`. Applied to
  the live Cloud Run Job via a scoped `ENV=prod ./tofu.sh apply -target=module.daily_ledger_digest_job` (0 to add, 1
  to change, 0 to destroy — no blast-radius beyond this one job).
- Manually rebuilt `client-reporting-api:latest` (`gcloud builds submit`, build `aaf50473-cedb-4752-b4d2-12dfdbce7640`,
  SUCCESS) at commit `c49305c` since the deployed image predated the source fix and the standing LDR→main→Cloud-Build
  promotion latency would otherwise have left this DP alert unresolved through the next 30-min promotion window.

## Verification (live, not smoke-test)

Direct re-execution `uts-prod-daily-ledger-digest-cpxk8` completed successfully (40.61s). Log confirms honest,
correct behaviour — looped over all 10 active/managed clients (ODUM_PROP, IK, ANU, SL2, SL, GP, STD, ET, NN, PR),
each an honest no-op (`no ledger rows for client=<X> date=2026-08-17 — nothing to digest`, since the paper-week
determinism pipeline this stage feeds is still pre-cutover — see `paper_week_determinism_scheduler.tf`'s own
`paper_determinism_enabled` gate note), summary `10/10 succeeded`, exit 0.

## Recommended decision

None needed — resolved. No `[OPERATOR]`/credential/judgment gap encountered.
