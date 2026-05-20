---
title: Pre-audit — ML repo consolidation (ml-training-service, ml-inference-service → ml-service)
created: 2026-05-19
author: slot-3
source:
  - plans/active/ml_repo_consolidation_2026_05_19.md
locked_by: live-defi-rollout
---

## What I found

Pre-audit inventory of stale references to archived ML repos across the workspace before consolidation.

Archived services: `ml-training-service`, `ml-inference-service`
Consolidated into: `ml-service`

## Why it matters

Phase -2 Bucket 1 cleanup — stale service names in consumer repos must be replaced before downstream
imports or service discovery fails.

## Recommended decision

Execute stale-ref sweep across all consumer repos per the ml_repo_consolidation plan (Bucket 1).
