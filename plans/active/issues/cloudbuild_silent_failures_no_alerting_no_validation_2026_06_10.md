---
title: "Cloud Build: silent config rejection, zero failure alerting, zero pre-push validation (3 gaps, fleet-wide)"
created: 2026-06-10
author: slot-1 (operator session, Ikenna)
source:
  - "FROM-digest proof-build incident 2026-06-10 evening — two config pushes fired ZERO builds with no signal"
  - "gcloud builds list 2026-06-10: 6+ FAILURE builds (16:25, 18:34, 18:47, 19:18, 19:48, 19:49) — zero pages"
locked_by: live-defi-rollout
---

# Cloud Build: three stacked observability/validation gaps

## What I found (all proven live, same evening)

**Gap 1 — config rejection is SILENT.** A GitHub push whose `cloudbuild.yaml` fails Cloud Build's substitution
validation (e.g. an unescaped shell var — `$PIN` reads as a substitution key) produces either NO build record or a
FAILURE record with **empty substitutions** (no repo, no SHA, no trigger name — see builds
`0412980c`/`47730bcc`/`1cea6e1b`). Nothing reports to the GitHub commit (the trigger never gets far enough to create a
check), nothing reaches Slack. From the developer's side a bad config is indistinguishable from "no build configured".
The error is visible ONLY by manually running `gcloud builds triggers run …` and reading the CLI error. Tonight's
digest-aware pre-pull config was rejected TWICE this way (first for unescaped `$VAR`s, then for a bash COMMENT that
mentioned them with dollars — the validator scans the whole step arg string including comments).

**Gap 2 — failed builds don't alert AT ALL.** The webhook-triggered per-repo GCB builds run outside GitHub Actions, so
`ci-failure-watcher` (which watches GH workflow runs) never sees them; there is no Pub/Sub → Slack pipe on the
`cloud-builds` topic. Today's evidence: the first-ever digest-pinned builds failed at 18:34 + 18:47
(`bb37c7b9`/`a18c2981` — a real regression class) and sat unnoticed until an operator-prompted manual poll hours later.
Image-build failures are deploy-blocking and currently 100% silent.

**Gap 3 — no pre-push validation of cloudbuild.yaml.** Quality gates parse YAML at best; nothing checks Cloud Build
SEMANTICS. The class that bit us (unescaped `$VAR` → invalid substitution key) is mechanically detectable offline (regex
over step args: `$WORD`/`${WORD}` where WORD is neither a Cloud Build builtin, nor a `_`-prefixed user substitution, nor
`$$`-escaped). A one-off scanner written during the incident caught the second rejection before push; it must be a
permanent gate.

## Why it matters

The image-build leg is the LAST hop to deployable artifacts. A silently-rejected config means a repo quietly stops
producing images on push — discovered only when a deploy needs an image that doesn't exist. Combined with Gap 2, the
fleet can rot for days. Gap 3 means every future cloudbuild template edit re-rolls these dice across ~19 repos.

## Recommended decision (3 fixes, all PM-side, fleet-effective)

1. **Validator** (`scripts/quality_gates/check_cloudbuild_substitutions.py`): yaml-parse + the unescaped-substitution
   scan over every step arg (builtins ∪ `_*` allowed; `$$` escape honored). Wire (a) into base-service.sh as a QG step
   when `cloudbuild.yaml` exists (fleet-live via sourced base, no rollout), and (b) into `rollout-cloudbuild.py`
   post-render (a template that renders invalid must fail the ROLLOUT, not the fleet).
2. **Failure/rejection watcher** (`.github/workflows/cloud-build-failure-watcher.yml`, PM, cron \*/15): WIF auth →
   `gcloud builds list` since last tick → Slack #ci-failures for every FAILURE/ TIMEOUT/INTERNAL_ERROR, with the
   **empty-substitutions signature called out as "config REJECTED (silent class)"**. Mirrors ci-failure-watcher's Slack
   pattern.
3. **(later, optional)** event-driven upgrade: Pub/Sub `cloud-builds` topic → notifier; the \*/15 poller is sufficient
   until then.

## Todos

- [x] ✅ [SCRIPT] P1. Build + wire `check_cloudbuild_substitutions.py` (QG step in base-service.sh + post-render
      validation in rollout-cloudbuild.py). repo: unified-trading-pm. — pending commit. Checker scans step
      args/script/env values (parsed-value scan = what GCB sees, so yaml-file comments are naturally exempt while bash
      comment-lines inside arg strings ARE scanned); builtins and underscore-prefixed substitutions allowed,
      double-dollar honored as the escape, bare dollar-paren command substitution flagged. CLI: positional paths or
      --repo or --all. Wired as base-service.sh STEP 5.19 (after the 5.17 structural check; graceful echo-skip when no
      cloudbuild.yaml or checker not provisioned; bash -n OK) and rollout-cloudbuild.py post-render hard-abort (a render
      failing validation is NOT written; loud per-violation lines, exit 1; checker-unloadable also fails loud). 11 unit
      tests in `tests/unit/test_check_cloudbuild_substitutions.py` (unescaped vars, braced vars, comment-line dollars,
      bare command-substitution flagged; escaped/builtin/underscore-substitution/yaml-comment cases clean; main exit
      codes). ruff + basedpyright clean. Fleet `--all` finding 2026-06-10: 60 violations across 17 of 20 cloudbuild.yaml
      files — ALL the bare dollar-paren class, ZERO unescaped-var hits; see follow-up todo.
- [x] ✅ [SCRIPT] P1. ~~Fleet `$(` → `$$(` remediation~~ **RESOLVED-BY-SEMANTICS (same evening)**: the 60 bare-`$(`
      findings were checker over-strictness, not real risk — Cloud Build's substitution grammar only matches
      WORD-keys (`$WORD`/`${WORD}`); `$(` never parses as a substitution and reaches bash as a literal (proven by the
      17 fleet configs carrying it and building fine for weeks). Flagging it would have falsely reddened 17 repos'
      QGs (the no-redden discipline). The checker was aligned to GCB's actual grammar (bare-`$(` not a token; comment
      + test updated — `test_bare_command_substitution_is_clean`), fleet `--all` re-scan: **20/20 files clean, zero
      real violations**. No template churn needed. — pending commit.
- [x] ✅ [SCRIPT] P1. `cloud-build-failure-watcher.yml` — \*/15 poll, Slack on FAILURE classes + silent-rejection
      signature. repo: unified-trading-pm. — pending commit (`.github/workflows/cloud-build-failure-watcher.yml`:
      WIF→SA-key dual auth w/ graceful no-op when unprovisioned; 20m lookback on 15m cron (≤2 alerts/build,
      dedup-tolerant); regional + global `gcloud builds list --format=json --limit=30` deduped by id, filtered locally
      by createTime + status ∈ FAILURE/TIMEOUT/INTERNAL_ERROR/EXPIRED; empty/missing repo+sha substitutions ⇒
      ":rotating_light: CONFIG REJECTED (silent class)"; Slack via SLACK_CI_WEBHOOK_URL‖SLACK_WEBHOOK_URL jq-payload,
      8-line cap + "+N more"; ::warning summary. yaml.safe_load + actionlint clean; classifier fixture-tested incl.
      null/missing substitutions. NOTE: schedule fires from main only — live once promoted via LDR→main.)
- [ ] [INFRA] P3. Pub/Sub `cloud-builds` → notifier (event-driven; supersedes the poller's latency). repo:
      deployment-service (terraform).
