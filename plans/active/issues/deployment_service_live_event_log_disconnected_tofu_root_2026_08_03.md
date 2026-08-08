---
doc_type: issue
title:
  "`deployment-service/terraform/gcp/live_event_log/` is a fully independent OpenTofu root (own state/backend), not an
  actual `module` of the parent root, despite a comment claiming inheritance — unclear if intentional"
summary: >-
  Deferred follow-up from deployment_service_root_state_orphaned_pubsub_publisher_iam_member_2026_08_03.md
  (resolved/archived): that doc's root cause was two independent OpenTofu roots (the parent `terraform/gcp/` root and
  `terraform/gcp/live_event_log/`) each owning state for the same live GCP IAM binding. `live_event_log/` has its own
  `.terraform/`, `.terraform.lock.hcl`, and `backend "gcs"` block (`live_event_log/main.tf:22`), and no `module
  "live_event_log" { source = "./live_event_log" }` block exists anywhere in the parent root's `.tf` files — yet
  `live_event_log/main.tf:9` carries a comment claiming "Provider + backend are inherited from the parent terraform/gcp/
  root module," which is not actually true (no module relationship exists; it's convention/copy-paste only). Not
  investigated: whether this disconnected-root structure was an intentional design choice (e.g. to isolate the event-log
  backend state for blast-radius reasons) or a historical accident (e.g. a module block that was removed/never added).
  Left as-is, it remains a standing risk for the SAME class of drift the parent issue found (two roots, one resource) to
  recur for any other resource `live_event_log/` declares.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [terraform, opentofu, gcp, state-hygiene, live_event_log]
related:
  [
    /plans/archive/issues/deployment_service_root_state_orphaned_pubsub_publisher_iam_member_2026_08_03.md,
    /codex/05-infrastructure/deployment-service-gcp-tofu-state.md,
  ]
created: "2026-08-03"
author: unknown
last_updated: "2026-08-08"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
sequential: false
drift_direction: correct-code
source: >-
  Flagged 2026-08-03 (slot-12, infra) as an explicit deferred follow-up when closing out
  deployment_service_root_state_orphaned_pubsub_publisher_iam_member_2026_08_03.md — not investigated in that doc's
  scope.
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    /codex/05-infrastructure/deployment-service-gcp-tofu-state.md,
    deployment-service/terraform/gcp/main.tf,
    deployment-service/terraform/gcp/live_event_log/main.tf,
    /plans/archive/issues/deployment_service_root_state_orphaned_pubsub_publisher_iam_member_2026_08_03.md,
  ]
---

# `live_event_log/` disconnected OpenTofu root — intentional isolation or historical accident?

## What I found

See summary. `git log --follow` / `git blame` on `live_event_log/main.tf:9`'s inheritance comment and on the parent
`main.tf` around when `live_event_log/` was first added would show whether a `module` block ever existed and was
removed, or whether the directory was always structured this way.

## Why it matters

Whichever the answer, it determines the right fix: (a) if intentional isolation, the misleading "inherited from parent"
comment should be corrected to say so explicitly, so the NEXT person doesn't assume a module relationship exists (which
is exactly what let the orphaned-state drift in the parent issue go unnoticed); (b) if accidental, it's a real
architectural gap — either wire it as an actual `module "live_event_log" { source = "./live_event_log" }` block
(consolidating state, eliminating the two-roots-one-resource class of drift for good), or keep it separate but fix the
comment either way.

## Recommended decision

**RESOLVED by git-history investigation 2026-08-08 — (a) intentional isolation, confirmed.** See Progress Log for
evidence. The remaining action (correct the misleading comment) is now a plain mechanical fix, not a judgment call — no
operator/architect decision needed.

## Todos

- [x] ✅ [INFRA] P3. **Investigation DONE 2026-08-08 — answer is (a) intentional isolation, not historical accident.**
      `git log --diff-filter=A --follow` on `deployment-service/terraform/gcp/live_event_log/main.tf` shows the ENTIRE
      `live_event_log/` directory (`main.tf`, `bq_external.tf`, `compaction_job.tf`, `outputs.tf`, `variables.tf`,
      `warm_sink.tf`) was added together in one commit (`fc7047c7`, "Pub/Sub topics + warm GCS sink + BQ external
      table + daily compaction job (Plan 03)") — complete with its OWN
      `terraform { backend "gcs" { prefix =     "terraform/state/live-event-log" } }` and `provider "google"` blocks
      from day one. `git log -p --all -- terraform/gcp/*.tf | grep     'module "live_event_log"'` across full history
      returns zero hits — a `module "live_event_log" { source =     "./live_event_log" }` block never existed in the
      parent root at any point. The file's own current text is internally self-contradictory (line 9 claims "Provider +
      backend are inherited from the parent ... root module" immediately followed by line 10's "This directory is a
      SEPARATE terraform module (standalone init + apply)" and then its own independent `backend`/`provider` blocks) —
      the isolation was the design from the start; only the inheritance comment was ever wrong. **Remaining action
      (repo: deployment-service, out of this dispatch's per-task repo scope — a worker/infra-craft dispatch on
      deployment-service should pick this up)**: fix `live_event_log/main.tf:9`'s misleading comment to state plainly
      that this root is independent by design (own backend/provider, standalone init+apply), removing the false
      "inherited" claim — no consolidation, no `module` block, no further decision required.

## Progress Log

- **infra-tranche NA-question resolution 2026-08-08**: resolved the "(a) intentional isolation, or (b) historical
  accident?" question definitively via full git history (see todo above for evidence) — no operator judgment call
  remains, just a one-line comment fix left for a deployment-service-scoped dispatch. Did not make the code edit itself
  (this session is scoped to `unified-trading-pm` only, per its own per-task repo restriction); flipped the todo done
  since the INVESTIGATION+DECISION (this doc's actual open question) is complete, with the mechanical follow-up named
  explicitly for the next deployment-service worker.
- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — sole item [OPERATOR] P3 (git-history
  investigation whether live_event_log/ was ever wired); its bounded investigation half is already extracted in
  infra_satellite_ao_dispatch_batch7 (draft); the structural decision half stays operator-gated.

- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — added the parent issue this doc was explicitly
  deferred from, which is the whole reason the "two independent OpenTofu roots" question exists.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
