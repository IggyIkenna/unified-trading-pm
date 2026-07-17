---
doc_type: issue
title:
  Three unrelated hard failures all surfaced as the same vague "PROMOTION LAG > 60m" warning — the lag alert reports a
  symptom, never a cause
summary: |
  On 2026-07-16/17, three completely different faults — a 16h self-hosted runner-pool collapse (missing Secret Manager
  IAM grant, swallowed by `|| true`), a deliberate provenance-gate refusal, and an unsatisfiable SIT-leaf deadlock —
  ALL surfaced in Slack as the identical `PROMOTION LAG > 60m ... un-propagated` WARNING. Nothing named a cause, so
  each was mis-triaged: the provenance block was read as "the bot forgot to arm auto-merge" (the gate was then
  overridden, promoting 33 bypassed commits), and the runner collapse was read as "normal SIT latency" (it had been
  dead 16h). The lag monitor is a SYMPTOM detector being used as the fleet's only promotion alarm. Root fixes for all
  three are shipped; this doc tracks the systemic gap — a failure should page for its own cause, not leak out as lag.
status: open
resolved_by:
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, alerting, observability, promotion, self-hosted-runners, silent-failure, triage]
related:
  [
    provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md,
    ../../../codex/04-architecture/ci-alerting.md,
    ../../../codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: devops_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  - operator 2026-07-17 — "file issue then fix to fail loudly and force full pipeline to unblock now so that next time
    we get zero alerts"
  - measured during the 2026-07-16/17 ci-failures triage session
---

# One alert, three causes: promotion lag is a symptom detector

> **The pattern**: every promotion-side failure, whatever its cause, exits through the SAME door — a `branch-health`
> WARNING saying N branch-pairs are "un-propagated". The alert states the symptom (content hasn't moved) and never the
> cause. All three causes below produced a byte-identical alert shape, and two of the three were mis-triaged BECAUSE of
> it — one of those mis-triages caused real damage.

## The three faults that looked identical

| #   | Real cause                                                                                                      | What Slack said                 | How it was mis-read                                                        |
| --- | --------------------------------------------------------------------------------------------------------------- | ------------------------------- | -------------------------------------------------------------------------- |
| 1   | **Runner pool dead 16h** — `GH_TOKEN_SECRET` migration shipped without the IAM grant; `\|\| true` ate the error | `PROMOTION LAG > 60m` (WARNING) | "normal SIT latency, working as designed" — it was a total pool collapse   |
| 2   | **Provenance gate refusing** — 33 non-quickmerge commits, auto-merge deliberately NOT armed                     | `PROMOTION LAG > 60m` (WARNING) | "the bot forgot to arm auto-merge" → gate overridden, 33 commits laundered |
| 3   | **SIT-leaf deadlock** — `system-integration-tests` had `promotion_model` unset; never dispatched at all         | `PROMOTION LAG > 60m` (WARNING) | "+1 more" noise for ~4 days                                                |

Fault 1 is the sharpest: **4,159 crash-loops in a 2h window, 0 runners listening, ~37 workflows stranded — and not one
alert fired.** The only signal was a lag WARNING that reads exactly like a slow-but-healthy pipeline. A CRITICAL
infrastructure outage was invisible for 16 hours because its symptom shares a channel with routine latency.

## Root cause of the invisibility

**Silent-failure idiom.** `scripts/self-hosted-runners/glue-runner-run.sh` did:

```bash
GH_TOKEN="$(gcloud secrets versions access latest --secret="${GH_TOKEN_SECRET}" \
  ${GCP_PROJECT:+--project="${GCP_PROJECT}"} 2>/dev/null || true)"
: "${GH_TOKEN:?GH_TOKEN ... must be set via EnvironmentFile or GH_TOKEN_SECRET}"
```

`2>/dev/null || true` discards the exit code AND the reason. The real error
(`PERMISSION_DENIED: secretmanager.versions.access`) never reached the journal; operators saw only the generic "must be
set via EnvironmentFile" — which describes a _config_ problem and points away from the actual _IAM_ problem.

**Structural gap.** No detector owns "a self-hosted pool stopped accepting jobs". `promotion_lag_monitor.py` is
explicitly scoped as the SSOT for branch-pair PROPAGATION lag only — it is not, and should not be, an infra monitor. But
it is currently the only thing that fires, so it absorbs every cause by accident.

## Fixed already (do not re-file)

- **Fault 1 root** — IAM grant added (operator) + `GCP_PROJECT` pinned in `/etc/github-glue-runner.env`; pool restored,
  5/5 runners `Listening for Jobs`, 0 token crashes (was 4,159/2h), queue drained 14 → 4.
- **Fault 1 silence** — ⚠️ **ATTEMPTED AND REVERTED — still open, see the P0 below.**
- **Fault 2** — provenance block now carries a stable marker and the lag monitor reports
  `⛔ BLOCKED by the provenance gate — re-ship via quickmerge. Do NOT hand-arm auto-merge`.
- **Fault 3** — `system-integration-tests` opted into `ldr_main` (fail-OPEN SIT-leaf path, same as `e2e-testing`).

## Still open — the systemic gap

- [ ] [DEVOPS] P0. **Re-do the `|| true` fix — the first attempt BROKE PROD and was rolled back (2026-07-17).** The
      replacement block (loud gcloud error + redaction + empty-secret case) passed `bash -n` and passed three
      simulated-failure unit tests, but on the live runner it died with
      `glue-runner-run.sh: line 200: GH_TOKEN: unbound variable` — the JIT `generate-jitconfig` curl at ~L195, under the
      script's `set -euo pipefail`. All 5 runners crash-looped again (~34 restarts) until rollback; service was restored
      from `${DST}.bak-2026-07-17` within minutes and the repo copy reverted so the SSOT matches the VM. The broken
      candidate is kept at `/tmp/glue-runner-run.sh.broken-keepme` on the VM for post-mortem.

      **ROOT CAUSE FOUND (post-mortem, same day) — it was an APOSTROPHE, and the fix is one character.** The block's
          error text contained `${GCP_PROJECT:-<unset — no --project passed; relying on gcloud's ambient default>}`.
          Inside a `${VAR:-word}` expansion bash **re-parses quotes in the default word**, so the `'` in `gcloud's` opened
          a single-quoted region. In a ~200-line script full of apostrophes it silently **re-paired with a later one** —
          quotes balanced overall, so `bash -n` saw VALID syntax — while everything between them became a quoted STRING
          instead of code, swallowing the `GH_TOKEN="${_sm_out}"` assignment. Hence `line 200: GH_TOKEN: unbound variable`
          at the `generate-jitconfig` curl ~120 lines below the edited block. Verified in isolation: the same construct
          alone fails `bash -n` with ``unexpected EOF while looking for matching `'``.
          **Rule to carry forward: never put an apostrophe (or any unbalanced quote) inside a `${VAR:-...}` default word.**
          Write "gcloud" not "gcloud's", or build the message outside the expansion.

          **Why my tests missed it**: they exercised ONLY the changed block, in a SHORT file with no later apostrophe to
          re-pair against — so the toy either errored honestly or passed, and could never reproduce the swallow. `bash -n`
          validates syntax, not binding, and the syntax was genuinely valid. **Still do not retry without whole-script
          validation**: add a `--selfcheck` mode that runs everything short of exec'ing `Runner.Listener`, exercise it on a
          scratch slot, then roll ONE unit and confirm `Listening for Jobs` before the other four. (The canary was
          worthless last time because the same bad script had already been rolled to all five.)

- [ ] [DEVOPS] P1. **A self-hosted pool with 0 runners listening must page on its OWN cause.** Nothing watches runner
      liveness. Cheapest honest signal: alert when a `glue`-labelled job has been `queued` > N minutes while
      `in_progress == 0` — that is unambiguous and needs no VM access. (The `glue-writer` pool stayed healthy
      throughout, so a naive "is the host up" check would have said GREEN.)
- [ ] [DEVOPS] P1. **Ban the `|| true` credential idiom.** Grep for `2>/dev/null || true` around
      `gcloud secrets|aws secretsmanager|vault` in `scripts/`; a credential fetch must never degrade to empty-string.
      Candidate QG check — a swallowed secret fetch is a silent-outage generator by construction.
- [ ] [DEVOPS] P2. **Make the lag alert state a cause per line, or say it cannot.** It now distinguishes
      provenance-blocked; it should also distinguish (a) SIT-gated in-flight, (b) no promote PR exists, (c) promote PR
      BLOCKED/CONFLICTING, (d) cause unknown. A line that cannot name a cause should say so explicitly rather than imply
      "just slow".
- [ ] [DEVOPS] P2. **`detect_breaking_change.py` is Python-only** (`endswith(".py")` + `ast.parse`), so every TS repo
      (`deployment-ui`, `unified-trading-system-ui`) is permanently "unknown-delta" and needs a full SIT round-trip on
      EVERY promote. That is a structural promotion tax, not a fault — but it is why those two repos are always the last
      to promote and always in the lag list.
- [ ] [DEVOPS] P3. Runner units have no `StartLimitBurst`/`StartLimitIntervalSec`, so a crash-looping unit restarts
      forever at ~6s (3,014+ counted) instead of entering `failed` where `systemctl --failed` would surface it. Entering
      `failed` would have made this visible to any host check on day one.

## Lesson

Two of the three mis-triages were mine, in this session. The alert did not lie — it just answered a question nobody
asked ("has content moved?") while the real questions ("is the pool alive?", "did a gate refuse?", "is this repo even
dispatched?") had no alarm at all. **When an alert's remedy is "go investigate", it is a symptom detector.** The fix is
not a better lag threshold; it is making each cause page for itself.
