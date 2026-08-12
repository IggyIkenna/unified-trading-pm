---
doc_type: issue
title:
  The per-client config surface is keyed archetype-first, and cannot express client-specific leverage, venue selection
  or coin universe
summary: >-
  Operator question 2026-08-12 ("is wallet_mapping where client specifics go? what if they want different leverage etc
  and venue selection, coins"). Measured answer: `wallet_mapping.json` is NOT the client-config surface (it is a wallet
  ADDRESS registry with zero consumers); the real surface is
  `deployment-service/configs/strategy/{archetype}/clients.yaml`, which IS live and wired (schema `ClientsYaml`,
  validated by `StrategySupervisor` at boot, passed to VMs as `VM_CLIENTS_YAML_PATH`). Two defects follow. (1) **Keying
  is archetype-first, client-second** — the path is `configs/strategy/{archetype}/clients.yaml` with clients as a list
  inside, so one client running N archetypes has its config split across N files with no client-level view, and there is
  no file you can open to answer "what is this client configured to do?". (2) **Three of the four axes the operator
  named are not expressible**: `ClientsYamlEntry` and `ClientRiskLimits` are both `extra="forbid"`, and between them
  allow only `client_id`, `shard_id`, `venue_creds_kms_path`, `min_balance_per_venue`, `max_position_usd`,
  `max_drawdown_pct`, `max_order_size_usd`. There is **no leverage field, no venue-selection field and no coin-universe
  field**, so a per-client difference in any of them is a schema change, not a config edit. Separately
  `strategy_service/client_context.py:61` documents `max_leverage` as an example `risk_limits` key and no such field
  exists in the schema or in either live file.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-api-contracts, strategy-service]
scope: [engineer, admin]
tags: [configuration, per-client-isolation, schema, hot-reload, client-onboarding, strategy-identity]
related:
  [
    /codex/06-coding-standards/strategy-identity-versioning.md,
    /codex/04-architecture/per-client-isolation-architecture.md,
    /codex/04-architecture/client-funds-isolation.md,
    /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md,
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-12
last_updated: 2026-08-12
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.2
assigned_role:
locked_by:
resolved_by:
source: >-
  Operator question 2026-08-12, immediately after the three blocking audits closed: "wallet_mapping is that where client
  specifics go? general client name would be logical though for client specific params like what if they want different
  leverage etc and venue selection, coins". Answering it required a cross-repo code audit because no doc states which of
  the three config surfaces owns what.
---

# Per-client config: wrong primary key, and three missing axes

## What the operator asked, and the short answer

> _"wallet_mapping is that where client specifics go? general client name would be logical though for client specific
> params like what if they want different leverage etc and venue selection, coins"_

**No — and the instinct about the key is correct.** `wallet_mapping.json` holds wallet ADDRESSES, not client policy. The
real per-client surface already exists, but it is keyed archetype-first, and it cannot express leverage, venue selection
or coin universe at all.

## The three surfaces, and which one is which

| Surface                                                        | What it actually holds                                                                                                                                              | Live?                                                                                                             |
| -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `wallet-config/{chain_env}/wallet_mapping.json`                | Wallet ADDRESSES: `custodian` → `chain_env` → `share_class` → one treasury wallet + trading wallets. Plus 3 treasury knobs (`reserve_pct`, `min/max_threshold_pct`) | **No consumers** — schema + path constant only (see the expansion plan's binding audit)                           |
| `deployment-service/configs/strategy/{archetype}/clients.yaml` | **THE per-client surface.** `client_id`, `shard_id`, `venue_creds_kms_path`, `min_balance_per_venue`, `risk_limits`                                                 | **Yes** — `ClientsYaml.model_validate_yaml()` at `StrategySupervisor` boot; launchers pass `VM_CLIENTS_YAML_PATH` |
| `strategy_service/configs/*.yaml`                              | Per-STRATEGY config (`carry_staked_basis.yaml`, `basis_trade_multi_coin.yaml`, …). No client dimension                                                              | Yes                                                                                                               |

The three treasury knobs on `wallet_mapping` are client-level POLICY sitting in a wallet registry — a smaller instance
of the same conflation the operator is pointing at, and worth moving when the surface is settled.

## Defect 1 — the primary key is inverted

Path is `configs/strategy/{archetype}/clients.yaml`, with `clients:` as a list inside. So the axis order is
**(archetype, shard) → [client]**, when the operator's mental model — and the one that matches how clients are actually
onboarded and reasoned about — is **client → [archetype]**.

Consequences, all present today:

- A client running N archetypes has its configuration spread across N files, with **no single place that answers "what
  is this client configured to do?"**. Client onboarding is therefore an N-file edit, and client offboarding an N-file
  audit.
- **Only 2 of 60 archetypes have a `clients.yaml` at all** — `carry_staked_basis` and `arbitrage_price_dispersion`.
  Every other archetype has no per-client config surface instantiated, so "add a client to archetype X" silently means
  "create the file too".
- The same two `client_id` values (`us`, `defi-client-1`) are duplicated across both files, with `venue_creds_kms_path`
  restated per archetype. Nothing enforces that a `client_id` means the same client in both.

## Defect 2 — three of the four axes the operator named cannot be expressed

`ClientsYamlEntry` and `ClientRiskLimits` are both `ConfigDict(extra="forbid")`. The complete allowed set is:

```
client_id · shard_id · venue_creds_kms_path · min_balance_per_venue
risk_limits: { max_position_usd, max_drawdown_pct, max_order_size_usd }
```

Against the operator's four axes:

| Axis the operator named | Expressible per client today?                                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------- |
| **Leverage**            | **No.** No leverage field anywhere in the schema. `max_position_usd` caps notional, which is not the same control   |
| **Venue selection**     | **No.** `min_balance_per_venue` names venues but sets a balance FLOOR — it does not select or exclude a venue       |
| **Coin universe**       | **No.** Universe is resolved per archetype (ADV-ranked for carry, hardcoded tuples elsewhere), with no client input |
| Risk envelope           | **Yes** — position / drawdown / order-size caps                                                                     |

Because `extra="forbid"`, none of these can be added as an ad-hoc YAML key: each is a UAC schema change plus a consumer.

## Defect 3 — a docstring names a field that does not exist

`strategy_service/client_context.py:61` describes `risk_limits` as "Per-client risk limit config from clients.yaml (e.g.
**max_leverage**, min_balance)". `max_leverage` is in neither `ClientRiskLimits` nor either live YAML file. An agent
reading that docstring would reasonably conclude per-client leverage is already supported — it is not. `min_balance` is
also imprecise: the real field is `min_balance_per_venue`, and it sits on the entry, not inside `risk_limits`.

## Where this lands relative to strategy identity

Per [strategy-identity-versioning](/codex/06-coding-standards/strategy-identity-versioning.md), `client_id` is
deliberately **not** part of any of the three naming forms — it is a registration attribute that appears in the
event-tag 9-tuple alongside `slot_label`, `config_hash` and `config_version`. That is the correct design and should not
change: per-client parameter values belong to **Layer 4 (Config — content hash + monotonic version)**, not to the
instance name. So two clients running the same strategy with different leverage is, correctly, _same archetype, same
slot label, different `config_hash`, different `client_id`_ — which is precisely why the config surface (not the name)
has to carry the client axis, and why it needs the three missing fields.

This also confirms the `(client_id, slot_label)` recommendation made for the wallet-binding key in the expansion plan:
the event tag already pairs exactly those two, so keying the wallet mapping the same way is consistent with the standard
rather than a new invention.

## Todos

- [ ] [OPERATOR] P0. **Decide the primary key for per-client config: client-first or archetype-first.** Recommendation:
      **client-first** — `configs/clients/{client_id}.yaml` carrying a per-archetype block, which makes onboarding and
      offboarding one file, gives a single client-level view, and stops `venue_creds_kms_path` being restated per
      archetype. This is the operator's own instinct ("general client name would be logical"). The counter-argument for
      the status quo is that `StrategySupervisor` boots per (archetype, shard) and reads only its own file; a
      client-first layout means the supervisor loads N client files and filters. That is a small loader change, not a
      blocker — but it is a real cost and the operator should see it before the decision.
- [ ] [OPERATOR] P0. **Confirm which of leverage / venue selection / coin universe become per-client axes**, since each
      is a UAC schema change plus a consumer, and each has an architectural interaction: **leverage** must reconcile
      with `max_position_usd` (two overlapping notional controls invite contradiction — decide whether leverage is
      derived or independent); **venue selection** is the client-scoped case of
      [venue-eligibility RULING 3](/codex/09-strategy/architecture-v2/axes/venue-eligibility.md), so it should reuse
      that three-way split rather than inventing a second mechanism; **coin universe** interacts with the ADV-ranked
      dynamic universe — decide whether a client can narrow the resolved set, or only veto names from it.
- [ ] [AGENT] P1. **Fix the `client_context.py` docstring** — it cites `max_leverage`, which exists nowhere, and
      `min_balance` for what is really `min_balance_per_venue` on the entry rather than inside `risk_limits`. Name the
      real fields, and point at `ClientsYaml` as the schema SSOT.
- [ ] [AGENT] P1. **Instantiate or explicitly waive `clients.yaml` for every archetype that can run.** 2 of 60 have one;
      the absence is indistinguishable from "no clients configured" versus "surface never created". A gate asserting
      every factory-registered archetype has a `clients.yaml` (or an explicit waiver) makes the distinction visible.
- [ ] [AGENT] P2. **Move the three treasury knobs off `wallet_mapping`** (`reserve_pct`, `min_threshold_pct`,
      `max_threshold_pct`) onto whichever client-config surface the P0 above settles on. They are client policy, and
      they are the reason the operator reasonably asked whether `wallet_mapping` was the client-config home.
- [ ] [AGENT] P2. **Record the resolved surface in codex** — no doc currently states which of the three surfaces owns
      what, which is why the question needed a code audit to answer. The three-surface table above is the content;
      [per-client-isolation-architecture](/codex/04-architecture/per-client-isolation-architecture.md) is the likely
      home.

## Progress Log

- **2026-08-12** — Raised from an operator question during the post-audit review. **Method note worth keeping**: the
  first probe searched only `strategy-service` for `clients.yaml`, found nothing, and was one step from reporting the
  per-client surface as entirely absent — the file lives in `deployment-service`, two repos away, and is fully wired.
  Searching every repo before writing the finding is what caught it. This is the fifth instance in two sessions of the
  absence-from-one-probe class recorded in
  [measurement-claims-discipline](/codex/12-agent-workflow/measurement-claims-discipline.md), and the first where the
  wrong verdict would have reached a written issue doc rather than only chat.
