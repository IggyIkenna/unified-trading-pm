---
doc_type: issue
title: deployment-ui may carry stale Barchart source-name labels — never checked
summary: >-
  cefi_satellite_ao_dispatch_batch11_2026_08_09.md todo 5 (Barchart code removal) scoped its repos to
  unified-api-contracts + market-tick-data-service only and explicitly flagged, but never checked, that deployment-ui's
  launch/devops console dropdowns may still carry a "Barchart" source-name label from before the retirement (CLAUDE.md:
  "VIX=VX-futures via XCBF.PITCH, Barchart RETIRED"). Migrated into a tracked todo per the 6-step archival ritual's rule
  1 ("never let a deferral evaporate with the archived plan") ahead of archiving batch11, which is otherwise fully done.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [cefi, barchart, ui, cleanup, deployment-ui]
related: [/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md]
created: "2026-08-09"
author: slot-11
assigned_vm: NA
parent_epic: cefi_master
priority: P3
locked_by:
resolved_by:
source: >-
  Flagged, not checked, in cefi_satellite_ao_dispatch_batch11_2026_08_09.md todo 5's Progress Log entry (slot-6,
  2026-08-09): "deployment-ui may have Barchart source-name labels in UI dropdowns — worth a manual spot-check... check
  before calling the todo's 'no Barchart references remain' done-when fully satisfied."
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# deployment-ui Barchart label spot-check

## What I found

Nothing yet — this doc exists solely to convert an unchecked deferral (see `source` above) into tracked work before the
plan that surfaced it archives. No investigation has been done on `deployment-ui` itself.

## Why it matters

`cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 5 deleted every live Barchart adapter/schema/registry reference
in `unified-api-contracts` and `market-tick-data-service`, but its own repo scope excluded `deployment-ui`. If a
launch-console dropdown still lists "Barchart" as a selectable source, that is a user-facing stale reference to a
retired data source — low severity (P3, cosmetic/informational, not a data-correctness issue), but real if present.

## Recommended decision

Grep `deployment-ui` for "Barchart"/"barchart" (source dropdowns, config lists, docs). If found, remove/replace
consistent with the removal already done elsewhere; if not found, close this doc with the negative-result evidence.

- [ ] [UI] P3. Grep `deployment-ui` for "Barchart"/"barchart" references in launch/devops console source dropdowns or
      config; remove if found (mirroring the removal already shipped in unified-api-contracts@fc1b4897 +
      market-tick-data-service@aea655a9), or close this doc citing the negative-result grep if none exist. Repo:
      deployment-ui.

## Progress Log

- **2026-08-09, slot 11**: filed while archiving `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` (6-step ritual rule
  1 — migrating the source doc's unchecked deferral into a real tracked todo before archival).
