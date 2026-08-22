---
doc_type: issue
title: Coinbase Derivatives Exchange (CDE) testnet smoke needs operator-requested UAT access
summary: >-
  COINBASE-CDE is one of the 17 CeFi venues with a real testnet answer ("YES — certification/
  UAT, not self-serve"), but has no UAC SourceCapability declaration and no publicly known
  base_url — there is nothing an agent can self-provision or attempt live. Filing the
  operator credential/access request this batch's own todo requires for a confirmed gap.
status: open
nature: issue
asset_group: [cefi]
stage: [data, execution]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [venue-readiness, smoke-test, cefi, coinbase-cde, credentials, operator-ask]
related:
  - /plans/active/cefi_venue_smoke_batch1_2026_08_20.md
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
parent_epic: security_and_cross_cutting_master
priority: P2
created: 2026-08-21
author: slot-21
assigned_vm: planning
source:
  - /plans/active/cefi_venue_smoke_batch1_2026_08_20.md
  - "execution-service/scripts/run_cefi_testnet_connectivity_smoke.py live run, 2026-08-21: COINBASE-CDE -> credential_required_no_endpoint (no attempt made — no URL to attempt)"
resolved_by:
locked_by:
context_scope:
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/_cefi.py
---

# Coinbase Derivatives Exchange (CDE) testnet smoke needs operator-requested UAT access

## What I found

`cefi_venue_smoke_batch1_2026_08_20.md`'s 2026-08-21 testnet verdict table records
COINBASE-CDE as having a real testnet answer: "YES (certification/UAT, not self-serve) —
Coinbase Derivatives Exchange provides 'a separate environment for integration, acceptance
testing and certification' — provisioned on request." That verdict was sourced from public
WebSearch, not a UAC registry entry — a full grep of
`unified_api_contracts/registry/capability_declarations/_cefi.py` confirms no
`SourceCapability` declaration exists for COINBASE-CDE at all (unlike Coinbase's spot/futures
entries, which do have sandbox URLs and were live-checked successfully this session).

This batch's todo #3 requires recording a testnet result "where credentials are available or
provisionable," and filing an operator credential request "when a credential gap is
confirmed." COINBASE-CDE is exactly that case: there is no self-serve signup, no discoverable
public base_url, and therefore nothing an agent can attempt live or provision
programmatically — the gap is confirmed, not merely unattempted.

## Why it matters

Without this, COINBASE-CDE has no measured terminal result at all for the testnet-smoke
contract — it would otherwise sit silently unaddressed rather than honestly tracked as
`credential_required_no_endpoint`, which this batch's data-correctness discipline (no
declared-absence hiding a real gap) requires.

## Recommended decision

- [ ] [OPERATOR] P2. Request Coinbase Derivatives Exchange certification/UAT environment
      access (base_url + API credentials) through Coinbase's institutional/CDE onboarding
      channel — this is a business/account action, not something self-servable
      programmatically. Once granted, register a `SourceCapability` entry for
      `coinbase_cde` in `_cefi.py` (this batch's sibling P2 registry todo already tracks the
      registration step itself) and re-run
      `execution-service/scripts/run_cefi_testnet_connectivity_smoke.py` to convert this
      venue's verdict from `credential_required_no_endpoint` to a real measured result.

## Progress Log

**2026-08-21 — slot 21.** Filed while executing `cefi_venue_smoke_batch1_2026_08_20.md` todo
#3. No live attempt was made for this venue (no URL exists to attempt) — recorded directly as
a confirmed credential/access gap per the todo's own instruction.

**2026-08-22 — direct operator confirmation (interactive session).** The human operator directly confirmed they
will personally initiate the Coinbase Derivatives Exchange (CDE) institutional/UAT onboarding request themselves
— this is a business/account action outside what any agent can self-serve (no self-serve signup, no discoverable
public `base_url`, per this doc's own findings). The `[OPERATOR] P2` todo above stays OPEN pending that
follow-through — not flipped, since the credentials/access have not actually been granted yet.
