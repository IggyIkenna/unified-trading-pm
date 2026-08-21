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
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/04-architecture/per-client-isolation-architecture.md,
    /codex/06-coding-standards/strategy-identity-versioning.md,
    /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md,
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    strategy-service/strategy_service/client_context.py,
  ]
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

- [x] [AGENT] P0. ✅ **DECIDED 2026-08-12 — client-first.** Operator ruling quoted verbatim in § "Target state" of this
      doc (/plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md), with the provenance in
      its `source:` frontmatter. Shape: `configs/clients/{client_id}.yaml` carrying a per-archetype block. One file per
      client, so onboarding and offboarding are single-file operations, `venue_creds_kms_path` stops being restated per
      archetype, and there is finally a file that answers "what is this client configured to do?". Accepted cost:
      `StrategySupervisor` boots per (archetype, shard) and today reads only its own file, so it must now load N client
      files and filter to its own (archetype, shard) — a loader change, not an architecture change. **Second dividend,
      which turned out to decide the reload story too**: the file boundary now matches the PROCESS boundary (per-client
      isolation is one subprocess per client), so a param edit maps to exactly one client's subprocess with no diffing
      to work out whose values moved. Under archetype-first, one client's edit touches a file shared by every client on
      that archetype, giving a reload a blast radius of N clients. See § "Dynamic param updates" below.
- [x] N. ✅ [AGENT] P0. Implement the client-first layout — strategy-service@c55b586c9c74d654ffacff24c04288595585b7cf
      (`ClientConfigStore`, `configs/clients/{client_id}.yaml`, `load_client_archetype`/`load_for_archetype_shard`).
      Migration tool shipped (`client_config_migration.py` + CLI wrapper); **not independently confirmed that the two
      legacy files (`carry_staked_basis`, `arbitrage_price_dispersion`) were actually migrated in production** — verify
      before treating this as fully closed (`/plan-reconcile agent_operating_framework_master` 2026-08-19).
- [ ] [OPERATOR] P0. **Confirm which of leverage / venue selection / coin universe become per-client axes**, since each
      is a UAC schema change plus a consumer, and each has an architectural interaction: **leverage** must reconcile
      with `max_position_usd` (two overlapping notional controls invite contradiction — decide whether leverage is
      derived or independent); **venue selection** is the client-scoped case of
      [venue-eligibility RULING 3](/codex/09-strategy/architecture-v2/axes/venue-eligibility.md), so it should reuse
      that three-way split rather than inventing a second mechanism; **coin universe** interacts with the ADV-ranked
      dynamic universe — decide whether a client can narrow the resolved set, or only veto names from it.
- [x] ✅ [AGENT] P1. **Fix the `client_context.py` docstring** — it cites `max_leverage`, which exists nowhere, and
      `min_balance` for what is really `min_balance_per_venue` on the entry rather than inside `risk_limits`. Name the
      real fields, and point at `ClientsYaml` as the schema SSOT. — **DONE**, reconciled from
      `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`: `strategy-service@3146cfd068` — docstring now lists
      the real fields, notes `min_balance_per_venue` lives on `ClientsYamlEntry`, removes `max_leverage`, points at the
      UAC schema SSOT.
- [x] ✅ [AGENT] P1. **Instantiate or explicitly waive `clients.yaml` for every archetype that can run.** 2 of 60 have
      one; the absence is indistinguishable from "no clients configured" versus "surface never created". A gate
      asserting every factory-registered archetype has a `clients.yaml` (or an explicit waiver) makes the distinction
      visible. — **DONE**, reconciled from `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`:
      `deployment-service@e355c14ad3` — created `clients_waiver.yaml` for all 30 uncovered factory-registered archetypes
      (only 2 have real per-client data); `uncovered_archetypes()` now returns `[]`.
- [ ] [AGENT] P2. **Move the three treasury knobs off `wallet_mapping`** (`reserve_pct`, `min_threshold_pct`,
      `max_threshold_pct`) onto whichever client-config surface the P0 above settles on. They are client policy, and
      they are the reason the operator reasonably asked whether `wallet_mapping` was the client-config home.
- [x] ✅ [AGENT] P2. **Record the resolved surface in codex** — no doc currently states which of the three surfaces owns
      what, which is why the question needed a code audit to answer. The three-surface table above is the content;
      [per-client-isolation-architecture](/codex/04-architecture/per-client-isolation-architecture.md) is the likely
      home. — **DONE**, reconciled from `cross_cutting_satellite_ao_dispatch_batch13b_2026_08_13.md`:
      `unified-trading-pm` (this batch) added a "Config surface ownership" section to
      `/codex/04-architecture/per-client-isolation-architecture.md` with the three-surface table + live-vs-not
      verdicts + the two known gaps + a pointer to the operator's 2026-08-12 ruling.

## Target state — operator ruling 2026-08-12: the `(client, archetype slot)` config governs everything

> _"client + strategy archetype slot config would govern everything. It's effectively gotta be verbose enough that
> strategy wizard could generate it (not fixed, can be a human too) and it governs exactly how everything is gonna
> operate for that client strategy slot, all the way to the execution algo selection criteria they wanna see. How they
> want PnL, analytics, risk behaviour to look — basically everything in strategy service that can be a config should be
> in there so that it can be dynamically changed per client."_

**The key is `(client_id, slot_label)`** — which is exactly the pair the event-tag 9-tuple already carries, so this
ruling is consistent with the identity standard rather than a new axis. It also settles the wallet-binding key question
in the expansion plan: the same pair.

What this ruling changes, relative to the `clients.yaml` schema measured above:

| Dimension | `clients.yaml` today                                        | Ruling target                                                                                                                                                                          |
| --------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Key       | (archetype, shard) → [client]                               | **(client_id, slot_label)** — per client-strategy-SLOT, not per archetype                                                                                                              |
| Scope     | 7 fields: creds path, per-venue balance floors, 3 risk caps | **Everything in strategy-service that can be config** — strategy params, venue + coin selection, leverage, execution-algo selection criteria, PnL treatment, analytics, risk behaviour |
| Authoring | Hand-edited YAML in a git repo                              | **Wizard-generatable, human-writable** — the capability wizard is the generator, not optional UI                                                                                       |
| Substrate | Git file, baked into a deployment                           | **GCS instance; schema + defaults in code** — the prerequisite for dynamic change                                                                                                      |

Three consequences worth stating before anyone builds it:

1. **The wizard stops being a convenience and becomes load-bearing.** A config object this complete is not comfortably
   hand-authored, which is precisely why the ruling names the wizard as its generator. `capability_manifest.py` is
   already a restriction GRAPH consuming `PARAM_SCHEMA_REGISTRY`, so the wizard is the right home — but the schema
   registry currently covers **strategy params only, for 35 of 60 archetypes**. It must grow sections for execution,
   PnL, analytics and risk before it can generate a governing object.
2. **"Execution algo selection criteria" crosses a service seam.** strategy-service config would govern an
   execution-service behaviour, and there are **no service↔service deps** by rule
   ([tier-and-import-architecture](/codex/04-architecture/tier-and-import-architecture.md)). So this travels as a
   _contract on the instruction_ (a UAC-typed selection-criteria block that execution-service interprets), never as an
   import or a shared config read. Getting this wrong is the most likely way this design picks up a dependency it is not
   allowed to have.
3. **A bigger config surface makes the determinism rule matter more, not less.** Every one of these axes becomes part of
   `config_hash`, so every change must still be a versioned event at a tick boundary (see below). The larger the object,
   the more valuable that discipline — and the more expensive a silent swap would be.

### Todos

- [ ] [AGENT] P0. **Draft the full `(client_id, slot_label)` config schema** covering the six governed areas the ruling
      names: strategy params · venue + coin selection · leverage and risk behaviour · execution-algo selection criteria
      · PnL treatment · analytics. Schema + defaults in code, instance in GCS. This supersedes the narrow
      `ClientsYamlEntry` shape rather than extending it.
- [x] [AGENT] P0. ✅ **Extended `PARAM_SCHEMA_REGISTRY` with the four governing sections —
      `strategy-service@664f5b42b2`, gate green `--no-fix` (exit measured via redirect, not a pipe).** Kept at **35
      archetypes** per operator instruction ("keep at 35 since rest are stubs anyway"). 272 strategy rows + 20 governing
      rows × 35 = **972 params**, no name collisions in any archetype. Shape decisions that matter: **(a) Execution is
      HIERARCHICAL, not a flat scalar** — operator correction mid-build. `ParamSpec` gained `key_template` (e.g.
      `exec_algo.{instruction_type}.{venue}`) and `enum_source`. The correction was necessary, not cosmetic: UAC
      `ALGOS_BY_INSTRUCTION_TYPE` gives a **different valid algo set per instruction type** (`TRADE` 8, `ZERO_ALPHA` 1,
      8 types total), so a single flat enum would have been wrong for 7 of the 8. The templated row resolves live from
      UAC instead of transcribing a table that would drift. **(b) Only the 10 IMPLEMENTED algos are client-selectable**
      — UAC's `ExecutionAlgo.implemented` flag marks 6 "ghost" algos (`BENCHMARK_FILL`, `BEST_PRICE`, `KELLY_STAKE`,
      `MAX_SLIPPAGE`, `SEQUENTIAL_LEGS`, `SPREAD_ROLL`) the selector returns but nothing executes; offering one in a
      client-facing wizard would be a silent no-op. Test asserts the ghost set never leaks. **(c) Every governing row is
      `wired=False`** — a new `ParamSpec.wired` flag, defaulting `True` so the 272 existing engine-cited rows keep their
      meaning. This is the guard that stops the wizard offering a knob nothing reads; flipping a row requires a `source`
      citing its consumer, asserted by test. **(d) `get_strategy_params()` does not project unwired defaults into engine
      params** — it is explicitly "the params the engine factory consumes", and materialising 17 unread keys per
      archetype would look configured while doing nothing. An explicitly supplied value still round-trips. Enum values
      grounded in UAC, not invented: PnL cadence is `CrystallizationCadence` verbatim (asserted by test); HWM basis is
      the three bases `pnl-attribution.md` names. Analytics uses the operator's bounded list (below). **Also fixed in
      the same commit — a pre-existing cross-repo drift that blocked the green tree**: two
      `test_topology_enforcement.py` tests hardcoded `ARBITRAGE_PRICE_DISPERSION` as co_location=[] / STANDARD. That
      stopped being true at `unified-trading-pm@b2bc3c59d0`, which corrected 25 archetype docs' frontmatter to match UAC
      `ARCHETYPE_TO_DEPLOYMENT_PROFILE` (APD is `co_located_vm`). Verified the registry to confirm the DOC was the
      correct side before changing the tests, moved the standard-tier assertions onto `EVENT_DRIVEN` (genuinely
      standard/no-co-location), and noted that `test_higher_tier_satisfies_lower_requirement` had been passing
      **vacuously** since the drift — premium satisfying premium tested nothing.
- [ ] [AGENT] P1. **Wire a consumer for each governing section and flip its rows to `wired=True`.** The schema is
      declared; nothing reads it. Each section needs its reader plus a `source` citation, and the
      `test_governing_sections_are_declared_unwired` guard updated as each lands — that test is deliberately strict so
      the burn-down is visible rather than assumed.
- [ ] [AGENT] P1. **Stamp received + sent timestamps in BOTH strategy-service and execution-service** so latency is
      derivable. Operator 2026-08-12: _"both services need received and sent time so we see latencies too"_. This is a
      schema requirement on the event rows, not a config knob — `analytics_emit_latency` can be set today but there is
      nothing to compute latency FROM until both stamps exist.
- [ ] [AGENT] P1. **Assert every runtime-registered strategy slot also exists in execution-service.** Operator
      2026-08-12: _"slots registered in strategy service at runtime must be also inside execution service"_ — the link
      between the two services' config is the slot. Today nothing enforces that correspondence, so an execution-config
      block could reference a slot execution-service has never heard of.
- [x] [AGENT] P2. ✅ **Mined 2026-08-14 — see Progress Log for the full inventory + reuse recommendations.** Operator
      pointer: it _"has some cool ideas on how strategy backtests could look and we can reap the analytics from there"_.
      Read the existing views before extending the analytics section further, so the schema follows a surface that
      already works rather than inventing a parallel one.
- [ ] [AGENT] P1. **Define the execution-algo selection-criteria contract as a UAC type carried on the instruction**,
      not as a config read across the seam. Name the interpreting surface in execution-service explicitly so the seam is
      documented rather than discovered.
- [x] [AGENT] P2. ✅ **Analytics axes BOUNDED by operator 2026-08-12** — the list this was waiting on: strategy
      instructions · benchmark PnL _"at the price we wanna get filled which is latest price of the instrument we are
      sending"_ · the breakdown per venue / account / client / instrument / strategy slot · and on the execution side
      everything measured FROM benchmark fills — alpha PnL, latency, slippage. Implemented in
      `strategy-service@664f5b42b2` as `analytics_benchmark_price_source` (default `BENCHMARK_INSTRUCTION_SEND_LAST`,
      the operator's definition verbatim), `analytics_breakdown_dimensions`, and per-signal emit toggles. **Design
      consequence made explicit in code and test**: benchmark price has ONE definition, and alpha PnL and slippage are
      DERIVED from it rather than independently configurable — otherwise they could be set inconsistently with the
      benchmark they are measured against. PnL axis grounded in what already exists (`CrystallizationCadence`; HWM is
      TWR / Notional / PnL-recovery, never raw equity —
      [pnl-attribution](/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md)).

## Dynamic param updates — why leverage is a restart today, and why it need not be

Operator question 2026-08-12: _"strategy service is running live, we update leverage for a client, it's a restart in
this case but we want it to be dynamic right, same with api key changes (that's execution though) — I thought hot
reloader was working"_.

**The hot reloader IS working. The operator's model is correct — for credentials.** Measured:

| Surface                          | Dynamic today?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **API keys / credentials**       | **Yes, no restart.** `CredentialStore.reload()` is thread-safe under an `RLock` so the IPC listener thread can swap while the main loop reads; `ClientCredentialKmsPoller` (UTL) runs a background daemon with per-(client_id, venue) poll intervals and fires `CredentialRotatedSignal` on a version change; a `CREDENTIAL_ROTATED` bus event does an immediate reload bypassing the poll interval. execution-service has the sibling `ApiKeyReloader` pushing into the connector (HYPERLIQUID wired; Bybit explicitly cannot be served by it — a `DATA_SOURCE_TO_SECRET` registry gap noted in its own source) |
| Instrument universe              | **Yes** — `DomainConfigReloader[InstrumentDomainConfig]`, atomic module-level swap, `register_instrument_change_callback(added, removed, new_config)` gives engines a hook                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Strategy domain config           | **Yes** — `DomainConfigReloader[StrategyDomainConfig]`, same pattern                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| **Per-client params (leverage)** | **No — restart.** Two stacked reasons below                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

### Root cause: the substrate, not the reloader

**`clients.yaml` is a git-committed file in the deployment-service repo**, handed to the VM as a local path via
`VM_CLIENTS_YAML_PATH` metadata. **A git file baked into a deployment cannot hot-reload by construction** — changing
leverage means editing the repo, committing, and relaunching the VM. That is the whole reason it is a restart. It is not
that hot reload is missing; it is that this one config lives on the wrong substrate while every other hot-reloadable
config is GCS-backed.

This is exactly the operator's centralisation directive 2026-08-12: _"centralise all config with strategy-service having
the schema/defaults in config.py but not the actual config — instance is in GCS"_. **That directive and dynamic leverage
are the same change, not two.** The GCS rails already exist and are already used: `ConfigLoader.load_config()` reads
`configs/{strategy_id}.json` from `STRATEGY_BUCKET` (and `configs_grid/{grid_id}/…` for grids) through the
cloud-agnostic `storage_client`, with caching and `_validate_risk_config_blocks()` on load; `load_config_from_path()`
takes a full `gs://` path. Move the per-client instance to GCS and `DomainConfigReloader` (cloud-agnostic,
`min_reload_interval`-throttled) picks up changes with no restart.

### The second gap: a running engine cannot be told

Even with the value arriving, **`self.params` has no mutation path** — it is set once in `register_instance()` and never
rewritten; there is no setter, no `update`, and no param-change callback. The pattern to copy sits **two functions away
in the same file**: `config_reloaders.py` already exposes `register_instrument_change_callback()`. There is no
`register_param_change_callback()`. So: GCS move makes the value _arrive_; a callback + setter makes the running engine
_see_ it. Both are needed, and neither is a new subsystem.

### The constraint that decides the implementation: determinism

A naive `self.params.update()` would be dynamic **and would silently break the ε=0 proof**. `paper(W)` must equal
`batch-rerun(W)` trade-for-trade
([paper-batch-live-reconciliation](/codex/09-strategy/operational/paper-batch-live-reconciliation.md)), and a rerun
cannot reproduce a value that changed at an unrecorded moment. The design is already implied by the event tag, which
carries **both `config_hash` and `config_version`** in its 9-tuple
([strategy-identity-versioning](/codex/06-coding-standards/strategy-identity-versioning.md)): a param change must be
**an event in the log with a `config_version` bump applied at a known tick boundary**, so the rerun replays it at the
same tick. That is the difference between an implementation that works and one that quietly invalidates reconciliation.

### Todos

- [x] N. ✅ [AGENT] P0. Move the per-client config instance to GCS, schema + defaults staying in code per the
      operator's centralisation ruling — strategy-service@c55b586c9c74d654ffacff24c04288595585b7cf (`ClientConfigStore`,
      GCS-backed).
- [x] N. ✅ [AGENT] P0. Add `register_param_change_callback()` + an engine param setter, mirroring
      `register_instrument_change_callback()` — strategy-service@c55b586c9c74d654ffacff24c04288595585b7cf
      (`config_reloaders.py:152` + `orchestrator.py` `queue_param_change()`).
- [x] N. ✅ [AGENT] P0. Emit a config-change event with a `config_version` bump at a tick boundary + a reconciliation
      test that changes a param mid-window and asserts `paper(W) == batch-rerun(W)` still holds —
      strategy-service@c55b586c9c74d654ffacff24c04288595585b7cf (`orchestrator.py` `queue_param_change()`/B5,
      `test_orchestrator_param_change_determinism.py::TestMidWindowParamChangeReconciliation`).
- [ ] [OPERATOR] P1. **Confirm the tighten-vs-loosen asymmetry for risk limits.** Recommendation: **tightening** (lower
      leverage, lower caps) applies immediately as a protective action; **loosening** waits for a clean boundary or
      needs explicit authorisation. This mirrors the existing direction-and-scope-aware kill-switch philosophy
      ([autonomous-recovery-matrix](/codex/04-architecture/autonomous-recovery-matrix.md)) rather than inventing a
      second policy. Worth an explicit ruling because "hot reload" usually implies symmetry, and here symmetry is wrong.
- [x] [AGENT] P1. ✅ **PARTIALLY RESOLVED, RE-VERIFIED 2026-08-16 — the naming collision is fixed; the real
      duplication is a path-convention divergence, not a name clash.** `engine/core/strategy_config_loader.py`'s
      function was renamed `load_strategy_config_gcs()` on 2026-08-13 specifically to resolve this todo's literal
      name collision (its own docstring cites this issue doc). Four live config-loading entry points remain,
      verified against current code:
      - `config.py:361` `load_strategy_config()` — local YAML only, hardcoded "Pure Lending" fallback at line 390.
        `config.py:579` `load_config()` is a dead alias — zero callers found anywhere in the tree.
      - `engine/core/config_loader.py:310` `ConfigLoader.load_config()` / `load_config_from_path()` — GCS,
        `configs/{strategy_id}.json`, with caching + risk-block validation.
      - `engine/core/strategy_config_loader.py:44,88` `load_strategy_config_gcs()` / `load_strategy_config_by_type()`
        — GCS, but a **different path shape**: `configs/strategies/{strategy_id}.json` (extra `strategies/`
        segment), and hardcodes `asset_group="cefi"` in its bucket resolution.
      - `cli/grid_generator.py:508` `load_base_config_from_gcs(gcs_path)` — GCS, arbitrary full path, no fixed
        prefix convention at all.
      **The actual remaining duplication**: two different GCS path conventions for what's conceptually the same
      `strategy_id → config.json` lookup, no shared precedence rule between any of the four, and a dead local-YAML
      path with a hardcoded fallback that should probably be deleted rather than centralised.
      `strategy_config_loader.py:140` `get_strategy_params()` is the one place param resolution (schema defaults,
      wired-flag, wizard round-trip) is already centralized regardless of which loader produced the raw dict — a
      reasonable seam to build a single loader behind, rather than inventing a new one.

## Progress Log

- **2026-08-14 — mined `unified-trading-system-ui` backtest views for the analytics surface (P2 todo above)**: read
  every backtest-analytics view in the UI repo before the governing-schema analytics section grows further. Findings:
  - **`lib/types/backtest-analytics.ts` is already a mature, shared `BacktestAnalytics` schema** — explicitly built to
    serve BOTH the Strategies tab (signal backtests) and the Execution tab (trade backtests) from one type, which is
    itself the precedent for a single client-governing analytics schema rather than a parallel one per surface. It
    covers: a KPI bar (headline metrics), an equity curve (vs buy-and-hold, with a `drawdown_pct` per point), trade
    markers plotted on the equity chart, a bucketed P&L-distribution histogram, **per-direction performance
    (All/Long/Short)** — ~30 fields each (net/gross profit, profit factor, win rate, avg/largest win/loss, bars-in-trade
    stats, sharpe, sortino, max drawdown), capital efficiency (CAGR total/long/short, return on account size, account
    size required), run-up/drawdown stats (avg/max duration, amount, pct, recovery days), a benchmark comparison
    (buy-hold return vs strategy outperformance), and a monthly-returns heatmap.
  - **`components/cockpit/backtest-vs-operating-panel.tsx` is the direct precedent for "benchmark PnL … alpha PnL,
    latency, slippage measured FROM benchmark fills"** — the exact axis bounded in the analytics-axes todo below. It
    already renders signal-only-backtest vs operating-adjusted-simulation as two snapshots plus a **per-layer
    cost-of-reality attribution list** (execution, gas_fees, liquidation, client_flows, treasury, venue_routing, risk,
    reporting — each a signed bps delta + note). This is a layered-attribution shape, not a flat metric list — the
    `(client_id, slot_label)` governing schema's analytics section should mirror this shape (a benchmark snapshot + a
    per-layer delta breakdown) for alpha PnL/latency/slippage rather than inventing new flat fields, since it is the
    concrete "cool idea" the operator's pointer was referring to.
  - **`components/signal-broadcast/backtest-comparison-panel.tsx` is the existing UI for the "breakdown per
    venue/account/client/instrument/strategy slot" axis** — a three-way backtest-vs-paper-vs-live table keyed per
    `slot_label` (sharpe/return/signal-count/hit-rate columns per stage). This is the working precedent for
    `analytics_breakdown_dimensions` (already shipped in `strategy-service@664f5b42b2` per the analytics-axes todo
    below) — the dimension already has a UI consumer at the `slot_label` grain today.
  - **Two lighter, less analytically-rich backtest views exist** (`components/dashboards/quant/backtest-page.tsx`, a
    KPI-card + detail-panel browser; `app/(platform)/services/research/strategy/backtests/backtests-page-client.tsx`,
    the list/management view with sharpe/return/max-DD/sortino/hit-rate table columns and a DeFi-specific run-config
    form in `backtests-page-support.tsx`). These consume a narrower `BacktestRun.metrics` shape, not the full
    `BacktestAnalytics` bundle — they reinforce that `backtest-analytics.ts`'s type is the richest existing schema to
    follow, not these narrower list-view projections of it.
  - **Recommendation for the governing `(client_id, slot_label)` analytics section**: reuse `BacktestAnalytics`'s
    per-cohort stat-bundle shape (a full stats object per breakdown dimension value, as `performance_by_direction`
    already does for All/Long/Short) rather than a flat metric list, and model the benchmark/alpha/slippage fields on
    `BacktestVsOperatingPanel`'s layered-attribution pattern. No code changes made in this pass — this todo was a
    read-before-build mining pass; the schema-drafting todo above
    (`Draft the full (client_id, slot_label) config schema`) is where this gets applied.

- **context-scout 2026-08-14**: populated context_scope (5 entries).

- **2026-08-12** — Raised from an operator question during the post-audit review. **Method note worth keeping**: the
  first probe searched only `strategy-service` for `clients.yaml`, found nothing, and was one step from reporting the
  per-client surface as entirely absent — the file lives in `deployment-service`, two repos away, and is fully wired.
  Searching every repo before writing the finding is what caught it. This is the fifth instance in two sessions of the
  absence-from-one-probe class recorded in
  [measurement-claims-discipline](/codex/12-agent-workflow/measurement-claims-discipline.md), and the first where the
  wrong verdict would have reached a written issue doc rather than only chat.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:ee5f924d08d302cb]: KEEP-NA, valid -- Grep-verified 12 open checkboxes (lines 159,163,182,233,263,267,271,279,346,348,351,354), matching inventory_open_todos=12. Doc carries multiple explicit, dated, verbatim-quoted operator rulings (2026-08-12) throughout its own text, satisfying NEVER-RE-LITIGATE rule (a) directly. Two items are explicitly [OPERATOR]-tagged unresolved decisions (leverage/venue/coin axis scope; tighten-vs-loosen risk asymmetry). The remaining items are real cross-service design+build work (a governing config schema spanning six areas, an execution-algo selection-criteria UAC contract crossing the strategy/execution service seam under the no-service-deps rule, and determinism-critical event-log integration for dynamic param changes) -- none of these clear the bounded-outcome bar; each requires an open design call the doc itself is still working through. Noted but did not act on: todo at line 159 ('Implement the client-first layout') may partially overlap with the later, broader '(client_id, slot_label)' ruling which states it 'supersedes the narrow ClientsYamlEntry shape' -- this is a plausible staleness signal but not a clean citation (the doc doesn't explicitly say to close the earlier todo), so left as GENUINE_WORK rather than guessed into stale_items_to_close.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — 8 open checkboxes (164/183/234/264/268/272/280/357), matching Phase-0 exactly -- down from 12 at the last na-eligibility-audit pass (2026-08-17); 4 items completed since, one flipped as recently as today. (3/8 items tagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE for next-run reassessment.)
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
