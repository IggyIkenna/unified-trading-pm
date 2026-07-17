---
doc_type: codex-ssot
title: Self-hosted glue-runner security posture
summary: >-
  Security SSOT for the self-hosted GitHub Actions glue/writer runner pools on the orchestrator VM: what identity a glue
  job actually runs with (the runner user's AMBIENT cloud creds — ADC + AWS, not scoped per-job tokens), why that is
  accepted (single-tenant box, folder/venv-scope isolation), the two MEASURED credential-exposure facts that correct the
  design comments (JIT config visible in `ps` argv; the ephemeral pool DOES write single-use `.credentials` files to
  disk), the mitigation ladder (low-priv runner user + scoped SA → dedicated VM), and the workflow-author rules that
  follow (never echo ambient creds; hosted↔self-hosted moves change the auth model — see STEP 2b).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [security, github-actions, self-hosted-runners, adc, credentials, ci-cd, glue-runners]
related:
  [
    secrets-management.md,
    gha-wif-migration.md,
    ../08-workflows/ci-cd-flow.md,
    ../05-infrastructure/claude-code-settings-symlink.md,
  ]
created: 2026-07-17
authoritative_for: [self-hosted runner ambient-identity posture, glue-runner credential-exposure facts]
referenced_by: []
owner:
last_reviewed: 2026-07-17
code_refs: [unified-trading-pm/scripts/self-hosted-runners/]
---

# Self-hosted glue-runner security posture

> Provenance: `plans/active/github_actions_ci_cost_reduction_2026_07_15.md` (STEP 2 self-hosting migration, 2026-07).
> Operator directive 2026-07-16: record the posture explicitly — "important, not blocking".

## TL;DR

- A job on the glue/writer pools runs as the **`ubuntu` user on the orchestrator VM** and inherits its **ambient cloud
  identity**: the ADC file (`~/.config/gcloud/application_default_credentials.json`), gcloud CLI credentials, and the
  box's AWS identity. This is **by design** — STEP 2b drops per-job `auth` steps _because_ ambient ADC is there.
- That is a **wider blast radius than GitHub-hosted** (whose jobs get only the scoped, short-lived tokens the workflow
  passes). Accepted because the box is effectively **single-tenant** (`ubuntu` + root; the agent-orchestrator already
  runs as `ubuntu`, so a glue job gains nothing the AO doesn't have) and runner slots are isolated at
  **folder/venv/clone scope** (operator decision 2026-07-16 — NOT user-scope).
- Consequence for workflow authors: **anything runnable on a glue runner can read the VM's cloud identity.** Do not
  route untrusted code (forked PRs, third-party actions with broad permissions) to self-hosted labels; PM repos are
  private and single-org, which is what makes the current posture tenable.

## Two MEASURED facts (2026-07-16, on the box) — they correct the design comments

1. **The JIT runner config is passed as a command-line argument** (`run.sh --jitconfig <base64>`), so the blob — which
   decodes to `.credentials` including the auth URL and RSA parameters — is **visible in `ps` to any local user** while
   the runner starts. It is single-use and the runner auto-deregisters, and the box is single-tenant, so this is
   consistent with the accepted isolation scope — but it is **not** the "no credential exposure" the JIT-vs-long-lived
   framing implies.
2. **The ephemeral pool DOES write `.credentials` / `.credentials_rsaparams` / `.runner` to disk**, contradicting the
   letter of `glue-runner-run.sh`'s "No long-lived `.credentials` on disk" comment. The spirit holds — the files are
   single-use, replaced each cycle, and belong to an already-deregistered runner — but the wrapper wipes only
   `_work`/`_diag`, so a stale (useless) credential file persists between cycles. Treat any such file found on the box
   as expected residue, not an incident; wiping them in the cycle cleanup is a nice-to-have.

## Mitigation ladder (in adoption order)

1. **Now (adopted):** slot isolation at folder/venv/clone scope; runners registered per-repo (personal account — no
   org-wide runners); JIT + ephemeral registration; movers carrying secrets stay on the writer pool.
2. **Next step if posture needs tightening:** a dedicated low-privilege runner **user** + a scoped service account
   (separate from the orchestrator's), so glue jobs stop sharing the AO's identity.
3. **Operator's stated fallback if exposure ever becomes a real concern:** move the runner pools to a **dedicated VM**
   with only the runner SA on it.

## Rules that follow (workflow authors)

- **Moving a job hosted → self-hosted changes its auth model.** Hosted needs explicit `auth` steps / secrets;
  self-hosted has ambient ADC. STEP 2b's trim (drop `auth@v3` + per-run pip installs in `ci-status-update`) is the
  canonical example, and it was **probed on the box first** (`env -i` + unit PATH → python Firestore client write OK) —
  gcloud CLI credentials and the ADC file are DIFFERENT stores; always probe ADC specifically before dropping an auth
  step.
- **Moving self-hosted → hosted requires restoring the auth steps** (hosted has no ambient identity) — the reverse
  migration is NOT a plain `runs-on` flip (see also `hosted-baseline.sh`, which exists because the forward flip deleted
  hosted-only setup steps).
- The 4 CI-health watchers + `notify-slack` **stay GitHub-hosted deliberately** (failure-independence: a VM outage must
  not blind failure detection) — do not "optimize" them onto the VM.
