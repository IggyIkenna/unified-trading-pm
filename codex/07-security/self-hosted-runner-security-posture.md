---
doc_type: codex-ssot
title: Self-hosted glue-runner security posture
summary: >-
  Security SSOT for the self-hosted GitHub Actions glue/writer runner pools, now on their own dedicated VM
  (`ci-escalation-runner-vm-1`, split off the orchestrator box 2026-08-05 — see the "Dedicated VM" update below): what
  identity a glue job actually runs with (the runner user's AMBIENT cloud creds — ADC + AWS, not scoped per-job tokens),
  why that is accepted (single-tenant box, folder/venv-scope isolation), the two MEASURED credential-exposure facts that
  correct the design comments (JIT config visible in `ps` argv; the ephemeral pool DOES write single-use `.credentials`
  files to disk), the mitigation ladder (low-priv runner user + scoped SA → dedicated VM, latter now DONE), the newer
  public-repo/fork-PR threat model this posture does NOT cover on its own, and the workflow-author rules that follow
  (never echo ambient creds; hosted↔self-hosted moves change the auth model — see STEP 2b).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [security, github-actions, self-hosted-runners, adc, credentials, ci-cd, glue-runners]
related:
  [
    /codex/07-security/secrets-management.md,
    /codex/07-security/gha-wif-migration.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/claude-code-settings-symlink.md,
  ]
created: 2026-07-17
authoritative_for: [self-hosted runner ambient-identity posture, glue-runner credential-exposure facts]
referenced_by: []
owner:
last_reviewed: 2026-08-07
code_refs: [unified-trading-pm/scripts/self-hosted-runners/]
---

# Self-hosted glue-runner security posture

> Provenance: `/plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md` (STEP 2 self-hosting migration,
> 2026-07). Operator directive 2026-07-16: record the posture explicitly — "important, not blocking".

## Dedicated VM (update, 2026-08-05) — mitigation ladder step 3 is now DONE

The runner pools no longer run on the orchestrator box. They were split onto a dedicated VM, `ci-escalation-runner-vm-1`
(`i-042a6332509482556`, private IP `172-31-3-59`, `c8i.4xlarge`, SSM-only — no public IP, no SSH), separate from the
planning VM (`i-0c9b283b31d6b5ca7`, EIP `13.113.200.22`) that runs agent-orchestrator. This was primarily a capacity fix
(colocation was the root cause of a fleet-wide CI capacity crisis —
`/plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`), and it **completes the
mitigation ladder's step 3 below** (moving runner pools to their own box). **Correction (2026-08-08): this does NOT
decouple identity** — the runner VM was launched with the SAME AWS IAM instance profile (`uts-orchestrator-epic`) and
the SAME GCP service account (`unified-trading-sa`, freshly-keyed but not a distinct/scoped SA) as the orchestrator box
(`/plans/archive/2026_08/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` todo 3's evidence). A glue job's
ambient identity still doubles as the agent-orchestrator's own identity — that decoupling is step 2 below, **not yet
done**. Deploy reference: `/codex/05-infrastructure/agent-orchestrator-deploy.md` § "CI-runner fleet". Relaunch runbook:
`/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md`.

## Public-repo / fork-PR threat model (NOT covered by the posture below — track separately)

The posture below assumes **every repo routing to self-hosted labels is private, single-org** — that assumption is what
makes ambient-identity exposure tenable. It does **not** hold for a public repo: a fork PR can trigger a
self-hosted-routed workflow and run arbitrary code with this box's ambient AWS/GCP identity, a materially different (and
more severe) threat than anything the mitigation ladder below addresses. `unified-trading-pm` itself was flipped public
2026-08-06 while still routing ~8 workflows to this pool — tracked as a P0 in
`/plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md` todo 24. The durable fix is **not running
self-hosted on a public repo at all** (revert to `ubuntu-latest`, which is free/unmetered for public repos anyway);
GitHub's fork-PR approval gate is a partial mitigation only if self-hosted routing is kept for some other reason.

## TL;DR

- A job on the glue/writer pools runs as the **`ubuntu` user on the orchestrator VM** and inherits its **ambient cloud
  identity**: the ADC file (`~/.config/gcloud/application_default_credentials.json`), gcloud CLI credentials, and the
  box's AWS identity. This is **by design** — STEP 2b drops per-job `auth` steps _because_ ambient ADC is there.
- That is a **wider blast radius than GitHub-hosted** (whose jobs get only the scoped, short-lived tokens the workflow
  passes). Accepted because the box is single-tenant (only runner units run on it now) and runner slots are isolated at
  **folder/venv/clone scope** (operator decision 2026-07-16 — NOT user-scope).
- Consequence for workflow authors: **anything runnable on a glue runner can read the VM's cloud identity.** Do not
  route untrusted code (forked PRs, third-party actions with broad permissions) to self-hosted labels — and do not route
  a **public repo** to self-hosted labels at all (see the threat-model section above); this posture's
  single-org/private-repo assumption is a hard precondition, not a nice-to-have.

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
   (separate from the orchestrator's), so glue jobs stop sharing the AO's identity. Not yet done — the VM itself is now
   single-purpose (step 3), but all glue units still run as `ubuntu`/root on it.
3. **DONE 2026-08-05:** moved the runner pools to a **dedicated VM** (`ci-escalation-runner-vm-1`) with only runner
   units on it — see "Dedicated VM" above.
4. **Not covered by 1-3:** the public-repo/fork-PR threat model above. Adding a low-priv runner user does not make
   self-hosted-on-a-public-repo safe — the durable fix there is not routing a public repo to self-hosted at all.

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
