---
doc_type: audit-result
title: External engineering specification — Cross-Venue Factor Repricing Platform v1.0 (verbatim reference)
summary: >-
  Verbatim text of an external CTO-level engineering specification received 2026-08-20, extracted from
  Cross_Venue_Factor_Repricing_Platform_Technical_Specification.docx. It is a CONTINUOUS-QUOTE PROFILE specification
  using BTC as its worked example — not an implementation spec for 192 venues or 60 archetypes. Held here as reference
  only; the SSOT that reconciles it against this platform is /codex/04-architecture/cross-domain-state-fabric.md.
status: pass
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, features-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: [hft, factor-state, external-reference, architecture, market-data, verbatim]
related:
  [
    /codex/04-architecture/cross-domain-state-fabric.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-20
last_updated: "2026-08-20"
date: 2026-08-20
severity: P1
parent_epic: system_readiness_master
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope: >-
  Full text of the external specification, sections 1-20 plus appendices A-E, reviewed against
  /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md sections 11-15.
auditor: >-
  Interactive session slot 6. Text extracted from the operator-supplied .docx by unzipping the OOXML package and
  stripping markup from word/document.xml; no content was summarised, reordered or edited.
---

# External specification — verbatim reference

> **This document is NOT an SSOT and MUST NOT be edited.** It is the unmodified text of an external engineering
> specification, retained because the original `.docx` exists only on the operator's laptop and every other slot, VM
> and agent in the estate would otherwise be unable to read it.
>
> **Read this for**: the continuous-quote profile mechanics — feed semantics, timestamp discipline, arbitration, the
> factor engine, the slow/fast snapshot contract, mass repricing, and its 21 external citations (§ Appendix D).
>
> **Read the SSOT instead for**: how any of this applies to this platform.
> [/codex/04-architecture/cross-domain-state-fabric.md](/codex/04-architecture/cross-domain-state-fabric.md) carries
> the two-axis model, the three semantic profiles, the StateEnvelope, and the 16 operator rulings of 2026-08-20 —
> including the three places where this document's framing was corrected.
>
> **Known scope limits of the text below** (settled 2026-08-20, do not re-derive): it assumes a colocated bare-metal
> C++ estate; it covers one risk bucket and continuous-quote venues only; it has no row for a chain reorg, for a
> market that resolves to zero, or for the absence of a cheap defensive action on-chain; and its `F_i` Taylor form is
> the continuous-quote KERNEL, not a universal valuation formula.

---

```text


ENGINEERING REFERENCE
Cross-Venue Factor Repricing Platform
Front-to-Back Technical Architecture and Implementation Specification
Document status
Architecture baseline and build specification
Version
1.0
Date
20 August 2026
Audience
CTO; Quant Research; Low-Latency Engineering; Network Infrastructure; Execution; DevOps/SRE; Risk
Scope
Crypto and listed-derivatives cross-venue price discovery, canonical factor state, and mass options repricing
Classification
Internal engineering document
Core design decision
Ingest many venue and feed representations, but publish one versioned absolute factor state per risk bucket and execution region. Ship models and factors, not thousands of instrument prices; derive quote actions locally from the current state.
Normative language
MUST/SHALL denote mandatory implementation requirements; SHOULD denotes the recommended default unless a measured exception is documented; MAY denotes an optional implementation choice.


Contents
Section
Title
1
Executive specification
2
Scope, terminology and non-goals
3
Economic and statistical model
4
End-to-end architecture
5
Feed ingestion, reconstruction and arbitration
6
Timestamp, sequence and latency semantics
7
Selecting canonical influencer instruments
8
Regional factor engine
9
Slow analytical path and fast valuation path
10
Repricing thousands of options efficiently
11
Defensive, offensive and aggressive action logic
12
Network and compute infrastructure
13
Interface, schema and configuration contracts
14
Failure handling and operational safety
15
Observability, evidence and cost accounting
16
Testing, certification and acceptance
17
Worked examples
18
Team work packages and ownership
19
Delivery roadmap
20
Normative requirement catalogue
A
Operational runbook outlines
B
Reference architecture decisions
C
Glossary
D
Sources and research basis
E
Final implementation checklist



1. Executive specification
Answer to the central pricing question: Yes: delta and gamma for a target option are applied to that target's effective underlying move after the common BTC move, venue and contract basis, quote-currency effects, funding/curve effects and other configured factors have been combined. They are not applied mechanically to a raw Binance, OKX, Upbit, Coinbase or CME price change.

This specification defines a location-aware cross-venue price-discovery and mass-repricing platform. It is designed for the case in which several economically related instruments trade on different venues and arrive through feeds with different semantics, latency, timestamp quality and failure modes. Binance may usually lead BTC, while OKX, Coinbase, Upbit, CME or a particular spot, perpetual or dated future may lead in another regime. The implementation therefore treats leadership as a measured, time-varying contribution to an unobserved factor state, not as a permanent venue priority.
The stable architecture is independent of the selected influencer set. Quantitative analysis and configuration determine which instruments and feed classes observe which factors, their expected basis, their measurement noise, their freshness limits and which actions they are allowed to support. The same runtime can therefore use Binance spot and Binance perpetual together, replace one with OKX perpetual during a regime change, include CME futures during US hours, or treat Upbit primarily as a local-premium observation without changing the fast-path code.
The platform separates four concerns that are often incorrectly combined:
Feed transport and reconstruction: turn packets, WebSocket frames, trades, BBO updates, depth changes and snapshots into valid venue-local state.
Economic inference: estimate a canonical common price and explicit basis/curve/FX/volatility factors from asynchronous observations.
Derivative valuation: apply a versioned local approximation of the slow analytical model to current factors, time and positions.
Execution action: decide whether to defend, passively reprice, quote more offensively or trade aggressively, subject to confidence, edge and venue state.
These layers communicate through versioned state. No feed handler is allowed to issue a direct '+$100 all BTC options' command. A raw observation may revise the canonical state; quote actors then derive their complete desired order state from that absolute state. This is the central protection against double reaction.
1.1 Required outcome
Outcome
Normative requirement
Primary owner
One economic reaction
The same transport packet, exchange event or cross-venue follower move MUST NOT be applied twice to fair value.
Quant + Low-latency
Location-aware nowcast
Each execution region MUST combine observations in its own actionable arrival order; it MUST NOT wait for a geographically central fair-value service.
Low-latency + Network
Mass repricing
A market event MUST be distributed as a compact factor state. Thousands of option fair values MUST be calculated locally and only changed wire orders emitted.
Low-latency
Model continuity
Slow snapshots MUST include market and position reference states and watermarks so an atomic model swap cannot omit or duplicate intervening changes.
Quant + Low-latency
Safe degradation
Feed, clock, WAN, model, position and execution faults MUST produce explicit health states and action restrictions rather than silent continued aggression.
SRE + Risk
Configurable influencers
Instrument/feed selection and measurement loadings MUST be configuration produced from analysis; they MUST NOT be embedded in venue-specific strategy code.
Quant Platform

1.2 Architectural invariants
There is one logical canonical factor state per risk bucket and execution region, even when there are redundant physical factor engines.
Raw feed messages never fan out directly to every option pricer. They terminate at venue-local adapters/arbiters and become compact canonical observations.
The hot market bus carries absolute idempotent state images with epoch and sequence, not additive price-move commands.
Sequence establishes order inside a sequenced venue feed; local monotonic receive time establishes actionable order at one listener; exchange time expresses source semantics and age. These roles are not interchangeable.
All fair-value approximations are evaluated from a reference snapshot. Fast state is current factor state minus reference factor state, current time minus reference time, and current position state minus reference position state.
Market state is latest-value/self-healing. Position, fill and order state is reliable, idempotent and auditable; it may not be silently skipped.
A low-confidence observation may support defensive action without automatically authorising offensive or aggressive action.
A late message is not rejected merely because it is late and is not applied merely because it is from a usual leader. Its conditional innovation and timestamp uncertainty determine its value.
The fast path contains no blocking RPC, database call, service discovery, allocation-dependent critical loop, global lock or distributed consensus round.
Every deployment decision - feed, machine, path, encoding, multicast group and influencer - is justified by measured marginal decision value and total cost, not nominal message rate alone.
1.3 What is fixed versus configurable
Fixed platform contract
Analysis/configuration choice
Canonical observation -> factor state -> local valuation -> order-state diff
Which venues and instruments observe each factor
Absolute state, epoch/sequence, freshness and uncertainty fields
Source weights, residual covariance and robust gates by regime
Versioned ModelSnapshot with factor/position/time references
Basis functional form, curve nodes, vol factors and approximation trust radii
Feed state machine and exact/semantic/innovation dedup barriers
Primary/backup feed class and action permissions
Location-local factor engine and local quote actors
Shard count, bucket partitioning and deployment location
Reliable position/order lane separate from lossy market lane
Dense, sparse or low-rank position adjustment representation

2. Scope, terminology and system boundaries
2.1 Scope
The initial reference bucket is BTC, but all contracts are generic over a base risk bucket. A bucket may contain spot pairs, perpetual swaps, dated futures, calendar spreads, ETFs or ETPs, options and synthetic indices whose value materially depends on the same economic underlying. The architecture also supports ETH and other assets by instantiating different factor schemas and influencer configurations.
The platform covers market-data ingress, venue-local reconstruction, timestamp capture, feed arbitration, WAN normalization, factor-state estimation, slow analytical snapshots, fast valuation, position adjustment, quote generation, execution integration, recovery, telemetry, replay, testing and deployment. It intentionally does not prescribe a single alpha model, options model, programming language, exchange connectivity vendor or physical carrier.
2.2 Normative terminology
Term
Definition
Risk bucket
The base economic state shared by a family of instruments, for example BTC, plus its configured basis/FX/curve/vol factors.
Influencer instrument
A configured measurement source whose state can update one or more bucket factors. Influence is a loading and uncertainty, not a permanent leader label.
Target instrument
An instrument being valued or quoted. A target may also be an influencer.
Source family
Observations sharing infrastructure or economic origin, such as Binance spot/depth/trade, used to avoid treating correlated messages as independent confirmation.
Canonical source state
Venue-local, feed-arbitrated state for one instrument/event plane with explicit sequence, time and health semantics.
Factor state
The regional absolute estimate of common price and configured basis/curve/FX/vol factors, including uncertainty and causal metadata.
Shock/cause ID
Identifier joining revisions that arise from the same known economic event. It is an aid to audit and semantic correlation, not the sole double-count barrier.
ModelSnapshot
Immutable slow-path generation containing reference fair values, sensitivities, credits, positions, adjustment representation, trust limits and watermarks.
Effective underlying
The target-specific underlying implied by the common state plus the basis and other factors to which the target's Greeks are defined.
Defensive
Cancel, widen or reduce exposure to avoid adverse selection or invalid state.
Offensive
Improve or move passive quotes to capture predicted fair movement while remaining maker.
Aggressive
Cross the spread or otherwise take liquidity when confidence and expected edge justify it.

2.3 Explicit non-goals
A single globally synchronous fair value. Geography makes information sets different by construction.
A universal claim that BBO, trade, MBO, MBP or aggregate trade is always fastest.
A timer-based debounce window as the primary solution to double reaction.
Full analytical repricing of every option inside the packet-receive loop.
Using Kafka, cloud Pub/Sub or a remote database as the colocated market-to-quote hop.
Silently extrapolating a Taylor model beyond its certified trust region.
Treating a local colocated feed as correct merely because it is local; local feeds can become stale, gapped or operationally delayed.
3. Economic and statistical state model
Model interpretation: The canonical price is a latent nowcast of the economic BTC state available at a specific execution location. It is not an index calculation, an average of displayed prices, or the most recent packet from a preferred venue.

3.1 Observation equation
After prices are normalized for contract multiplier, inverse/linear quotation, quote currency and unit scale, an influencer instrument k is represented as an asynchronous noisy measurement of the bucket state:
y_k(t_e) = a_k + H_k z(t_e) + epsilon_k(t_e)
For a simple BTC implementation, z may contain common log price x, USD/USDT or fiat FX factors, venue premiums, spot-perpetual basis, funding/curve nodes and selected volatility or risk factors. H_k is configured: a Binance spot and Binance perpetual can both load on x while only the perpetual loads on its funding/basis factor. A CME future can load on x, USD and the relevant maturity-curve node. An Upbit KRW instrument can load on x, KRW/USD and a local premium.
log_price[k] = intercept[k]
             + loading_common[k] * btc_common
             + loading_fx[k]     * quote_fx
             + loading_curve[k]  * curve_node[maturity(k)]
             + loading_venue[k]  * venue_basis[k]
             + residual[k]

This explicit decomposition prevents the raw $60,000 OKX versus $61,000 Binance example from generating a permanent false signal. If the calibrated expected difference is $1,000, both normalize to the same common state. Only a change in the normalized residual, or evidence that the expected basis itself has moved, creates information.
3.2 State evolution and asynchronous update
The factor engine maintains a small state and covariance. A linear state-space baseline is sufficient for the platform contract; the implementation may use a robust Kalman variant, square-root filter, information filter or another bounded deterministic estimator.
z_t^- = F(dt) z_(t-1)^+     and     P_t^- = F P_(t-1)^+ F' + Q(dt, regime)
innovation nu_k = y_k - a_k - H_k z^-  ;  K_k = P^- H_k' / (H_k P^- H_k' + R_k)
z^+ = z^- + robust_gate(nu_k) K_k nu_k
R_k is dynamic. It rises with age, spread, shallow depth, feed gaps, clock uncertainty, path degradation, venue stress, source-family correlation and residual instability. It falls only when the source has demonstrated incremental predictive value and reliable semantics. A usual leader that is two hours old receives effectively infinite measurement variance and is rejected. A local target feed suffering exchange or distribution delay is also down-weighted despite its geographic proximity.
R_k = R_base,k x age_penalty x feed_health_penalty x clock_penalty x liquidity_penalty x regime_penalty
Robust gating MUST cap the effect of outliers and crossed/invalid books without turning every unusual move into a permanent quarantine. The raw observation, pre-gate innovation, applied innovation and reason code MUST all be journaled for replay.
3.3 Permanent price discovery versus fast tactical lead
Offline price-discovery measures such as Hasbrouck information share and Gonzalo-Granger permanent/transitory decomposition are useful for identifying common trends and long-run contribution, but they do not by themselves determine the fastest actionable feed. Hasbrouck's framework explicitly addresses one security trading in multiple linked markets [R1], while the permanent/transitory approach separates common non-stationary state from stationary deviations [R2]. Crypto evidence shows that price-discovery contribution varies materially across exchanges and time, especially as markets become more or less segmented [R3, R4].
The production selection layer therefore combines three horizons:
Structural horizon: cointegration and permanent/transitory contribution establish which instruments genuinely share a common economic state.
Tactical horizon: paired-event firstness and lead-lag analysis establish which feed reveals actionable innovations first at the desired reaction horizon.
Decision horizon: out-of-sample ablation measures whether a source changes actual quoting/trading outcomes after all existing sources, fees and latency are included.
Leadership MUST be estimated conditionally by regime, time of day, venue health, spread, volatility and event class. A source can be structurally important but tactically late, or tactically first but dominated by transient venue basis.
3.4 Common movement, basis movement and target-effective movement
The output needed by a target option is not necessarily the scalar common BTC change alone. Let g_i(z) map the bucket factors into the effective underlying relative to which the target's delta and gamma were calculated:
S_eff,i(t) = g_i(z(t))
Delta S_eff,i = g_i(z_now) - g_i(z_ref)
If the option model defines delta directly to canonical BTC, venue basis remains a separate Jacobian factor. If it defines delta to a venue-specific forward or index, common price, quote FX and target basis are combined first. The definition MUST be explicit in ModelSnapshot so the fast path cannot apply a common move and then accidentally apply the same basis component again.
For a general factor vector, the price approximation is:
Delta V_i ~= J_i Delta z + 0.5 Delta z' H_i Delta z + theta_i Delta t + position_adjustment_i
For a one-dimensional effective underlying approximation this reduces to delta and gamma:
Delta V_i ~= delta_i Delta S_eff,i + 0.5 gamma_i (Delta S_eff,i)^2 + theta_i Delta t + other_factor_terms
Mandatory convention: Every Greek field MUST declare its independent variable, units, scale, sign convention, reference state and validity radius. 'Delta = 0.42' is not a sufficient interface contract without specifying whether it is versus spot, index, forward, inverse contract value or a normalized common factor.

4. End-to-end component architecture

Figure 1. Venue-local normalization limits WAN volume while every execution region maintains its own actionable factor state.
4.1 Component inventory
Component
Hot-path responsibility
Persistent/control responsibility
Venue Feed Adapter
Decode frames/packets; hardware or kernel RX timestamp; normalize identifiers and fixed-point values.
Schema certification; entitlement and connection configuration.
Book Builder
Apply sequenced updates; maintain BBO/depth/MBO planes; expose validity and sequence watermark.
Snapshot bootstrap and recovery; deterministic replay.
Feed Arbiter
Race exact duplicates; reconcile feed planes; emit canonical source state and health.
Firstness statistics, feed policy and incident evidence.
Edge Feature Extractor
Compute bounded sufficient statistics such as microprice, spread, OFI and depth slope.
Feature schema and calibration; raw archive remains separate.
WAN Replicator
Send compact absolute source states over redundant paths to execution regions.
Path inventory, encryption/private circuits, cost accounting and replay.
Regional Factor Engine
Apply observations in actionable arrival order; maintain state/covariance; publish absolute FactorState.
Fixed-lag diagnostics, source calibration, shadow comparisons.
Local State Bus
Fan the same bucket state to quote actors using shared memory or local multicast.
Group registry, recovery endpoint and schema rollout.
Slow Model Service
None in packet loop; produces immutable snapshots asynchronously.
Analytical valuation, Greeks, bases, credits, trust bounds and validation.
Position Sequencer
Publish idempotent fill/position state and watermarks.
Reconciliation against venue/account/custodian state.
Quote Actor
Evaluate local surrogate, action policy and desired wire order; suppress unchanged output.
Own instrument shard, model activation, replay and metrics.
Execution Gateway
Order-state diff, rate-limit-aware amend/cancel/new, acknowledgements and fills.
Session lifecycle, drop copy, reconciliation and kill controls.
Journal/Replay
Non-blocking append or capture tap only.
Raw packets, normalized events, factor states, models, decisions and outcomes.

4.2 Location model
Venue-local processing terminates raw feed complexity. An edge may be in an exchange colocation facility, a cloud region close to a crypto venue, or another low-latency location. It SHOULD build and validate the local book before emitting source state; forwarding raw JSON, duplicate WebSockets and full depth to every option pricer multiplies cost while exporting venue-specific failure semantics to the entire system.
Every execution colo runs a regional factor engine. It receives local target-venue state with minimal delay and remote canonical source states with unavoidable WAN delay. Because the regional engine sees the actual order in which that location could have acted, it naturally suppresses a delayed remote 'leader' that has already been reflected by the local venue. A central global factor service would erase this advantage and add a mandatory network hop.
4.3 Data-plane lanes
Lane
Semantics
Loss/backpressure policy
Recommended transport
Market source state
High-rate latest absolute state
May skip intermediate states; latest state heals. Never allow an unbounded queue.
Edge unicast/WAN relay; local shared memory or multicast
Factor state
High-rate absolute bucket state
Duplicate/reorder safe; consumer may jump to newest sequence and record skipped count.
Shared memory on host; multicast on local L2
Position/fill
Authoritative account state
No silent loss. Idempotent, ordered, replayable and reconciled.
Reliable ring or acknowledged unicast stream
Order/ack
Authoritative execution state
No silent loss; session sequence and reconciliation apply.
Venue protocol plus reliable internal IPC
Model/config
Low-rate immutable generations
Reliable delivery, validation, atomic activation and rollback.
Reliable control plane
Telemetry/archive
High-volume evidence
May sample noncritical metrics but raw incident evidence must be retained per policy.
Asynchronous journal/broker/object storage

5. Feed ingestion, reconstruction and arbitration
Design rule: There is no single 'fastest feed'. The system chooses the first valid actionable representation for each event class, preserves complementary information, and conditions every later observation on what is already known.

5.1 Feed semantic registry
Every adapter MUST register the semantics of each subscribed channel. A channel name is not enough. The registry records whether messages are event-by-event or conflated, incremental or absolute, sequenced or unsequenced, lossless or auto-culled, the timestamp meaning, expected cadence, snapshot/recovery procedure, and whether cross-channel identifiers can be joined.
Feed class
Canonical plane
Default fast-path use
Critical caveat
Raw trade
Trade/flow
Aggressor direction, executed price, signed flow and potential price innovation.
Do not assume it changed BBO; do not mutate the book unless venue semantics warrant it.
BBO/top-of-book
Fast quote overlay
Immediate defensive protection, spread/microprice and freshest displayed top.
May auto-cull or omit intermediate states; cannot reconstruct queue/depth.
Incremental MBP
Aggregated book
Canonical price levels, imbalance and depth-state transitions.
Requires snapshot bootstrap, sequence continuity and venue-specific recovery.
MBO/order-by-order
Order book/queue
Richest queue and event causality where available.
Higher byte/CPU cost; order events may span packets or one exchange event.
Aggregated depth/order
Conflated book/flow
Lower-bandwidth state and slower features.
Loses order identity and transitions that cancel within the conflation interval.
Aggregated trade
Conflated trade flow
Confirmation, rolling flow and lower-cost remote feature input.
Not assumed to be first; aggregation key and interval are venue-specific.
Rolling top-N snapshot
Absolute book overlay
Self-healing current-state fallback and defensive input if fresh.
No complete event history; may have weaker continuity semantics.
Recovery snapshot
Book bootstrap
Startup and gap recovery only.
MUST NOT be treated as a normal alpha event or replayed as a new move.

Exchange documentation confirms that nominally similar channels differ materially. Binance Spot SBE currently describes real-time trade and BBO, BBO auto-culling under load, 20 ms differential depth and 50 ms top-20 snapshots [R5]. Binance futures aggregate trades are grouped by price/taking side at a documented interval [R6]. OKX documents 10 ms BBO/tick-by-tick depth and 100 ms alternatives, with explicit sequence fields for incremental depth [R7]. Coinbase warns that some WebSocket paths can still exhibit gaps or out-of-order data despite TCP and recommends appropriate sequenced book channels [R8]. These are adapter facts, not universal platform assumptions.
5.2 Venue-feed lifecycle
State
Entry condition
Permitted output
Exit/response
UNINITIALIZED
No valid reference state
Health only
Connect and obtain required instrument definitions/snapshot.
SNAPSHOT_SYNC
Snapshot acquired; incremental bridge not yet proven
Optional defensive current-state overlay; no authoritative depth alpha
Apply buffered increments and prove continuity.
LIVE
State valid, sequence continuous, age and clock within limits
All configured observation classes
Remain until health violation.
DEGRADED
Elevated delay, loss, spread anomaly or clock uncertainty
Down-weighted observations; action permissions reduced
Recover health or progress to stale/gap.
GAP_RECOVERY
Sequence discontinuity on reconstructive feed
BBO/trade planes only if separately valid; invalid depth prohibited
Retransmit or snapshot recovery and continuity proof.
STALE
No current valid state or age beyond hard limit
No price observation; health signal only
Fresh valid state plus re-entry criteria.
QUARANTINED
Semantic violation, impossible book, persistent residual anomaly or operator action
None for pricing
Explicit automated certification or operator release.

A feed state transition MUST carry a reason code and monotonically increasing health generation. Quote and factor engines must never infer health from missing metrics alone.
5.3 Exact transport arbitration
Exact duplicate paths are the simplest case. For redundant multicast A/B feeds or duplicate sockets that share an exchange sequence/update ID, the arbiter processes the earliest valid copy and marks the key complete. Later copies update path-health statistics but do not modify economic state. CME explicitly recommends listening to both incremental A and B feeds, processing by sequence, discarding an already processed sequence and initiating recovery on a gap [R11].
on_packet(packet, path):
    rx = hardware_or_kernel_rx_timestamp(packet)
    validate_envelope(packet)
    key = (venue, channel, epoch, packet_sequence)
    if processed.contains(key):
        path_health.observe_duplicate(key, rx)
        return
    if sequence_gap(key):
        transition(GAP_RECOVERY)
        request_recovery(missing_range)
        return_or_process_only_independent_planes()
    decode_and_apply(packet)
    processed.insert(key)

The processed-key structure MUST be bounded by channel sequence/epoch and time. A weekly sequence reset, connection generation change or exchange reset MUST advance the adapter epoch so old keys cannot collide.
5.4 Semantic correlation across feed types
Trade, BBO, depth and aggregate streams often describe different consequences of one exchange event. The arbiter attempts deterministic correlation using exchange event IDs, update-ID ranges, trade IDs, sequence relationships and explicit end-of-event markers. CME's MatchEventIndicator, for example, identifies boundaries within event-based messages, and Trade Summary describes a distinct match caused by an aggressing order or market event [R13, R14].
The platform MUST NOT require a fixed microsecond waiting window to collect every representation. Waiting adds latency and fails when venue delays change. The first valid high-value representation updates its canonical plane immediately. Later messages are attached to the causal record when possible and evaluated for incremental content. An explicit venue end-of-event marker MAY allow multiple updates already present in the same receive burst to be committed together without adding an artificial timer.

Figure 2. Exact dedup, semantic correlation, conditional innovation and absolute state provide independent protection against double reaction.
5.5 Four double-reaction barriers
Barrier
Key/decision
Prevents
Does not suppress
Transport
Packet/update sequence and connection epoch
A/B or duplicate-socket copies
A genuinely different update
Semantic
Exchange event/trade/update linkage and canonical state planes
Trade/BBO/depth consequences treated as independent shocks
Extra information contained in a later plane
Economic innovation
Residual versus current/fixed-lag factor state
Follower venue or late leader re-applying an already incorporated move
A residual common or basis innovation
Consumer state
Absolute FactorState epoch and sequence
Duplicate/reordered factor packets and provisional/confirmed additive commands
A newer state revision

Critical nuance: A later message is not forced to contribute zero. If the first trade implies 60% of the common move and the subsequent BBO/depth change contains new information, the filter can apply the residual 40%. This is a conditional revision, not a double reaction. If the later message only confirms the same state, it changes uncertainty or action permission without moving the mean.

5.6 Measuring which feed is faster
Speed MUST be measured as time to the first valid actionable state transition, not raw frame arrival. For observations that can be paired to the same exchange event e, compare local receive times:
d_f,g(e) = t_rx,f(e) - t_rx,g(e)
Because both timestamps use the same local clock, this pairwise lead does not depend on the accuracy of the exchange clock. Compute distributions by symbol, event class, session, packet size, volatility regime, venue load and connection path. At minimum, retain:
Probability each feed is first valid and actionable.
p50, p90, p99 and p99.9 pairwise lead/lag; tail staleness matters more than the mean.
Probability that the revealed state survives over the intended defensive, passive and aggressive horizon.
Gap, reorder, duplicate, disconnect and invalid-state rates.
Incremental decision value after all already-selected feeds are present.
CPU, bytes, connection/license and operational cost.
The output is a conditional routing policy. It may say BBO is primary for defense, incremental depth is primary for canonical book state, raw trades update flow immediately, aggregate trade is confirmation only, and recovery snapshots are never a pricing trigger. The policy may race multiple feeds rather than selecting one permanent winner.
5.7 Snapshot and recovery rules
A reconstructive incremental book MUST start from a venue-prescribed snapshot and bridge procedure.
A snapshot carries state as of its own sequence/time. It MUST NOT be applied after later increments without the documented bridge condition.
During a depth gap, all book-derived features whose validity depends on missing updates MUST be marked invalid. Independent BBO/trade streams may remain usable if their own semantics and health are valid.
Recovery completion MUST publish a new book generation. Downstream consumers must replace the plane; they must not interpret the recovered difference as new alpha.
The raw missing range, recovery source, duration and decisions taken while degraded MUST be journaled.
CME uses sequence numbers to detect missed packets and provides snapshot and TCP recovery services [R12]. Crypto venue procedures differ and must be encoded per adapter rather than hidden in a generic reconnect loop.
6. Timestamp, sequence and latency semantics
Ordering rule: Use sequence to order one sequenced feed, local monotonic receive time to order actionable arrivals at one listener, and exchange timestamps to estimate source age and causality. Never sort cross-venue data solely by nominal exchange timestamps.

6.1 Required timestamp set
Field
Clock/owner
Meaning
Primary use
t_exchange_event_raw
Venue
Raw venue timestamp exactly as received; semantics registered per message type.
Audit and venue-relative event age
t_exchange_send_raw
Venue gateway if supplied
Venue dissemination time, distinct from matching/event time where documented.
Exchange internal/dissemination delay
t_hw_rx
NIC PHC
First timestamp at receiving network adapter.
Path/firstness measurement
t_kernel_rx
Kernel
Packet entry into host stack when hardware timestamp unavailable.
Fallback receive ordering
t_decode
CLOCK_MONOTONIC_RAW
Adapter finished validation/normalization.
Host processing latency
t_canonical_publish
CLOCK_MONOTONIC_RAW + UTC mapping
Canonical source state published.
Edge processing budget
t_wan_rx
Destination NIC/monotonic
Source state received in execution region.
WAN delay/arrival order
t_factor_publish
Regional factor engine
Absolute state committed.
Inference latency
t_quote_decision
Quote actor
Desired wire state calculated.
Repricing latency
t_order_tx / ack / fill
Execution + venue
Wire send and subsequent execution lifecycle.
End-to-end attribution

Every normalized timestamp MUST carry or imply clock domain, units, resolution, normalization method and an uncertainty bound. Raw exchange values must be retained even after normalization. Linux exposes hardware and software receive timestamping through SO_TIMESTAMPING; hardware RX timestamps are generated by the adapter when supported [R16]. IEEE 1588 PTP defines precise clock synchronization across networked devices and supports both multicast and unicast operation [R15].
6.2 Clock implementation
Use PTP hardware clocks and capable NICs/switches in colocated networks. Monitor offset, path asymmetry, grandmaster identity, servo state and holdover.
Use CLOCK_MONOTONIC_RAW or an equivalent monotonic source for durations and in-process ordering. Do not calculate latency by subtracting two potentially stepped wall clocks.
Maintain a continuously estimated mapping between the NIC PHC, host monotonic time and normalized UTC/TAI for cross-host analysis.
Store raw Unix/UTC venue timestamps plus normalization metadata because exchanges may differ in precision, generation point, leap handling and clock quality.
Prefer TAI or another non-stepping internal timeline for cross-host correlation where the estate supports it; preserve venue UTC semantics at the boundary.
If clock uncertainty exceeds the configured limit, disable claims that depend on cross-host firstness and inflate measurement variance. A clock incident is not automatically a market-feed gap.
6.3 Exchange timestamp examples
Binance futures depth messages document distinct event time E, transaction time T and update-ID ranges U/u/pu [R6]. OKX documents order-book generation time and, for its BBO channel, matching-engine book-generation semantics, plus seqId/prevSeqId for incremental continuity [R7]. CME packet headers contain a packet sequence and gateway SendingTime, while event messages may contain transaction/event fields and MatchEventIndicator [R13]. Upbit documents a trade timestamp and sequential_id but explicitly warns that sequential_id does not guarantee transaction ordering [R10]. These differences are why the semantic registry is mandatory.
6.4 Age and staleness
Where venue and local clocks are sufficiently comparable, estimated source age is:
age_k = t_local_rx_UTC - corrected(t_exchange_event_raw) +/- clock_uncertainty
Age is only one health signal. A feed can report fresh-looking exchange timestamps while queuing upstream, reuse a current timestamp for periodic snapshots, or stop sending because the market is unchanged. Health therefore combines expected heartbeat/cadence, sequence continuity, cross-feed state consistency, path-delay distribution and venue-specific semantics.
Condition
Fast-path treatment
Fresh, valid, continuous
Normal configured R and action permissions.
Age elevated but inside soft limit
Continuously inflate R; usually defense allowed, aggressive permission may be removed.
Exchange clock uncertain
Retain local arrival ordering; inflate age uncertainty; prohibit timestamp-dependent cross-host attribution.
Hard stale limit exceeded
Reject price observation; retain health event only.
Local target state fresher than remote leader
Condition remote observation on current/fixed-lag state; apply only residual information.
Sequence gap
Invalidate affected reconstructive plane regardless of apparent timestamp freshness.

6.5 Late and out-of-sequence observations
Cross-venue WAN observations are naturally delayed. The regional factor engine supports two bounded policies selected per source:
NOWCAST policy: process in receive order against current state, inflate R as a function of age and reject beyond the hard limit. This is the default for feeds whose event time is coarse or unreliable.
FIXED_LAG policy: when the source timestamp and clock uncertainty are certified, insert the measurement into a short ring of factor checkpoints at its estimated event time, replay the small factor state to the present, and publish only the resulting current absolute state.
The fixed-lag window MUST be bounded by configured time and event count. If insertion would exceed the budget, fall back to nowcast/reject rather than blocking the quote path. Quote actors never see historical intermediate rewrites; they receive one newer FactorState. Offline smoothing may reconstruct a more accurate history for research, but must not leak future information into live or backtest decisions.
7. Selecting canonical influencer instruments
Configuration principle: Spot, perpetuals, dated futures and even multiple instruments on one venue may all be influencers. The configuration decides their measurement loadings and permissions; the runtime architecture does not change.

7.1 Candidate universe
The slow analysis service builds a candidate set for each risk bucket from economically linked instruments with obtainable real-time feeds. Candidate metadata includes contract mechanics, quote currency, index composition, expiry, funding, matching-engine/source family, market hours, feed class, licence, region, spread/depth, volume, open interest and historical availability.
A source is excluded before statistical selection if its economics cannot be normalized, its feed cannot be made operationally valid, its timestamp/sequence semantics are insufficient for the proposed action, or its licence and distribution rights prohibit the intended topology.
7.2 Offline selection pipeline
Normalize every candidate into common units and remove deterministic contract, FX, multiplier, funding and maturity effects.
Verify economic linkage using cointegration/common-trend tests across suitable horizons; estimate stable and regime-varying basis components.
Estimate permanent price-discovery contribution using information-share/component-share families, with uncertainty and ordering sensitivity reported rather than hidden.
Measure paired-event firstness and short-horizon predictive lead using recorded local receive timestamps, not aligned bars alone.
Condition on the already-selected set and estimate marginal value through forward selection, regularization or constrained subset search.
Replay the actual decision engine with and without the source. Score avoided adverse selection, captured edge, false defensive exits, aggressions, turnover, fees and queue impact.
Subtract fixed feed/cross-connect/licence cost, bytes, CPU, operational burden and receiver-side cloud processing cost.
Enforce redundancy constraints so the selected set does not collapse to one venue, matching engine, network provider or quote currency.
Publish a versioned InfluencerConfig with loadings, basis model, source family, action permissions, variance model, max age and fallback behavior.
7.3 Selection objective
Choose I to maximize E[decision_loss_without_I - decision_loss_with_I] - lambda_B bytes - lambda_C cost - lambda_O operational_risk
The objective is marginal. A slow aggregate feed that merely repeats an already selected BBO may have no alpha value but still have recovery or health value. Conversely, a higher-cost CME or premium tick-by-tick feed can be justified if it uniquely leads during an economically important regime. A feed that rarely wins can remain valuable as independent redundancy.
7.4 Source-family covariance
Binance spot and Binance perpetual may both contribute, but they are not independent votes. They share venue infrastructure, participant flow and often matching/distribution behavior. The factor engine MUST model correlated measurement noise or apply source-family confirmation caps. The same applies to raw trades, BBO and depth derived from one matching event.
Independent confirmation is therefore defined by source family and economic mechanism, not message count. A Binance trade, Binance BBO and Binance aggregate trade are not three independent confirmations. Binance plus CME may be more independent, subject to session and basis state.
7.5 Influencer configuration contract
InfluencerConfig {
  config_gen; bucket_id; source_instrument_id; venue_id; source_family_id;
  eligible_feed_classes; measurement_factor_ids[]; loadings[]; intercept_model_id;
  basis_model_id; base_variance; age_penalty_curve; hard_max_age_ns;
  robust_gate; regime_table_id; required_book_state; required_clock_quality;
  allow_defensive; allow_offensive; allow_aggressive;
  cost_tag; license_scope; fallback_source_set; config_hash;
}

All actors MUST use the same instrument/reference-data generation as the configuration. Unknown IDs, factor-schema mismatches or a failed hash MUST reject activation. Config rollout is atomic at a bucket generation boundary; no event-time consensus is performed.
7.6 Online adaptation
The online filter adapts confidence through health and residual variance; it does not run unrestricted model discovery in the packet loop. Slow or nearline services update regime tables and publish new generations after validation. A fast emergency override may disable a source or action class immediately, but adding a new factor or changing Greek semantics requires a compatible model/config generation.
8. Regional factor engine
8.1 Processing contract
A factor engine is single-writer per bucket within one logical epoch. It consumes canonical source states from local and remote edges, applies health and timestamp policy, updates the factor state, records the causal decision and publishes a new absolute FactorState only when the state or action-relevant uncertainty changes.
on_source_state(s):
    require schema/config compatibility
    reject duplicate or older source sequence
    update source health and absolute source plane
    if source not eligible for pricing: journal and return
    observation = measurement_model(s, active_config)
    if FIXED_LAG eligible: update bounded history and replay to now
    else: update current nowcast with age-adjusted variance
    evaluate robust innovation and source-family covariance
    commit one new factor sequence
    publish complete absolute FactorState
    append decision record asynchronously

The factor engine MUST be deterministic for a given ordered input stream, config generation and clock-quality record. Randomized robust procedures must use explicit seeds and are discouraged in the hot path.
8.2 FactorState message
Field
Suggested type
Semantics
magic/schema_id/schema_version
u32/u16/u16
Framing and generated decoder compatibility.
bucket_id
u32
Stable risk-bucket identifier.
engine_epoch
u64
Advances on logical sequencer failover/reset; lexicographically precedes sequence.
factor_seq
u64
Strictly increasing within epoch.
config_gen/model_factor_schema
u64/u32
Configuration and ordered factor-vector interpretation.
cause_id
128-bit
Causal revision/audit identifier; zero only for heartbeat/checkpoint.
source_family_id/source_instrument_id
u32/u32
Primary observation causing this revision.
source_event_time_ns
i64
Normalized source event time, with raw value retained upstream.
source_rx_time_ns
i64
Regional or edge RX time according to schema.
publish_time_ns
i64
Factor commit/publication time.
changed_factor_mask
u64 or bitset
Fast dependency test; complete vector is still present in baseline schema.
factor_values[K]
binary64 or declared fixed point
Complete absolute ordered factor state.
diag_variance[K]
binary32/64
Compact uncertainty; full covariance remains in engine/journal if too large.
quality_flags/action_mask
u32/u16
Clock/feed/regime validity and maximum supported action class.
payload_length/crc32c
u16/u32
Datagram framing and application-level integrity.

The baseline SHOULD carry the full factor vector because K is small. This makes each market packet independently useful and allows a lagging consumer to jump directly to the newest state. If K grows beyond one datagram, split the factor schema into economically coherent sub-buckets rather than introducing IP fragmentation. All data-plane messages SHOULD fit below the smallest certified MTU; a conservative WAN profile is below approximately 1,400 bytes.
8.3 Absolute state rather than additive commands
Consumers apply FactorState using lexicographic (engine_epoch, factor_seq) ordering. A duplicate or reordered packet is ignored. A newer packet replaces current factor values and uncertainty. The consumer computes its own difference to its ModelSnapshot reference. Therefore a provisional estimate and later confirmation are revisions of state, not two commands to add a movement.
if msg.epoch < current.epoch: discard
if msg.epoch == current.epoch and msg.seq <= current.seq: discard
validate schema, config, CRC and age
current = msg                    # replacement, not += delta
reprice_owned_targets(current)

If a consumer detects skipped factor sequences, it records the gap but can continue from the newest complete state if health is valid. It MUST NOT replay stale queued market states merely to preserve every intermediate tick. Position and order lanes have different semantics and cannot use this shortcut.
8.4 Confidence and action permission
FactorState contains both the estimated mean and uncertainty/quality. A confirmation may reduce uncertainty without changing the mean. An outlier may move the defensive state while marking the state ineligible for aggressive action. This separation prevents the common failure in which one scalar fair-value change simultaneously triggers cancel, passive reprice and aggressive take regardless of evidence quality.
8.5 Logical high availability
The system exposes one logical sequencer per bucket. Physical redundancy MAY be implemented as active/standby or deterministic A/B publishers, but split-brain publications with unrelated sequence spaces are prohibited. Failover MUST advance engine_epoch. Consumers always prefer the greater epoch and reset sequence comparison. An epoch change is an explicit health event and may temporarily remove aggressive permission until the new engine proves current source and position watermarks.
9. Slow analytical path and fast valuation path

Figure 3. Slow snapshots carry market and position reference watermarks; the quote actor always evaluates against current absolute state.
9.1 Slow-path responsibilities
The slow path performs work that is analytically rich, allocation-friendly or cross-sectional and is not required for every packet. It owns full options valuation, surface/curve fitting, basis estimation, Greek and Hessian calculation, position-adjustment calibration, credit schedules, trust bounds, source-selection analysis and validation. It publishes immutable snapshots; it never mutates coefficients in place.
A snapshot can be scheduled, triggered by material state movement, triggered by expiry/time decay, or requested when a fast approximation approaches its validity boundary. Slow-path unavailability does not immediately stop the fast path: actors continue inside certified trust limits and progressively restrict action as model age grows.
9.2 ModelSnapshot header
Field
Purpose
model_gen/config_gen/schema_hash
Immutable identity and compatibility.
bucket_id/factor_schema_id
Factor-vector interpretation.
reference_time
Theta/time origin and model age.
factor_epoch0/factor_seq0/z0
Exact market state from which all factor sensitivities are measured.
position_epoch0/position_seq0/q0 or r0
Exact risk state from which position adjustment is measured.
instrument_refdata_gen
Contract multiplier, tick, expiry, quote and Greek unit compatibility.
valid_from/soft_expiry/hard_expiry
Controlled activation and degradation.
trust_region
Maximum factor/time/position displacement and error budget.
model_quality
Validation statistics and permitted action classes.
content_hash/signature
Integrity and authenticated control-plane release.

9.3 Per-instrument model row
InstrumentModelRow {
  instrument_id; target_factor_dependency_mask; pricing_convention_id;
  fair_value_0; J[K]; optional_H[packed]; theta;
  bid_credit; ask_credit; size/edge policy IDs; tick/rounding policy;
  reference_position_component; position_adjustment_row_or_factor_loading;
  delta_definition; gamma_definition; units/scales;
  factor_trust_bounds; time_trust_bound; position_trust_bound;
  next_bid_up/down_trigger; next_ask_up/down_trigger;
}

Rows are distributed only to quote actors that own the instruments. A BTC factor state is broadcast, but the 5,000 or 20,000 option rows are slow control-plane data and need not be replicated to every region or process that does not quote them.
9.4 Fast-path calculation
F_i(t) = F_i0 + J_i Delta z + 0.5 Delta z' H_i Delta z + theta_i Delta t + C_i + A_i Delta q
C_i includes bid/ask credits and other snapshot-static adjustments according to explicit convention; credits are not cumulatively added on every event. Delta z is current absolute factor state minus z0. Delta q is current reliable position state minus q0. The quote actor recalculates the complete desired fair/edge/size state from these values.
For target-specific delta/gamma, the model row may instead provide g_i and derivatives with respect to S_eff,i. The common BTC net movement has already been inferred by the factor engine; the target basis mapping then converts it to the effective movement used by the option. This is where the raw influencer and target basis are kept from being counted twice.
9.5 Atomic model activation
Receive the complete immutable snapshot and validate schema, reference data, config generation, signature/hash and numerical sanity.
Ensure the quote actor has current FactorState and PositionState at or after the snapshot's factor/position watermarks. Because states are absolute, no market replay is required to calculate the current value.
Build all data-oriented arrays, trigger indexes and position adjustment structures off the hot core.
At a safe actor boundary, atomically swap one snapshot pointer/generation.
Immediately calculate desired state from current z - z0 and q - q0; compare to existing wire state and emit only required changes.
Retain the previous generation until rollback window and in-flight decision attribution are complete.
A model snapshot MUST NOT contain 'already applied market deltas' without the corresponding factor watermark. A fill MUST NOT be embedded in q0 without its position watermark. These two rules remove the most common fast/slow hand-off race.
9.6 Position adjustment matrix
For a fill in instrument j, the reliable position sequencer emits fill_id, instrument_id, quantity delta and position sequence. Each quote shard stores the rows of A required for its owned instruments and applies A_ij Delta q_j. Network cost is constant in the number of targets; compute cost is local.
If A is dense and fill frequency makes a column update expensive, the slow path SHOULD produce a sparse plus low-rank representation:
A ~= L R + D ;  Delta r = R[:,j] Delta q_j ;  Delta F_i = L[i,:] Delta r + D[i,j] Delta q_j
The hot lane may then publish a small absolute risk-factor state r. Exact sparse local corrections remain for instruments where low-rank error exceeds tolerance. Whatever representation is chosen, fill idempotency and position reconciliation remain authoritative.
9.7 Trust-region and slow-path failure policy
Condition
Required behavior
Inside soft trust region
Normal fast approximation and configured action permissions.
Near boundary
Request refresh; increase conservative credit or reduce size according to policy.
Outside price/factor trust region
Prohibit aggressive action; perform vectorized fallback or cancel/widen until refreshed.
Model older than soft expiry
Degrade confidence/action mask; continue only if analytical error budget permits.
Model older than hard expiry
No new offensive/aggressive quotes; defensive cancel or static safe mode.
New snapshot invalid
Reject generation, retain last valid snapshot, alert and apply its age policy.
Reference-data mismatch
Reject model; trading for affected instruments prohibited.

10. Repricing thousands of options efficiently
Scaling principle: Distribute the factors that changed, keep the model rows next to the execution owner, and transmit only order states that actually change after rounding, credits, inventory and action policy.

10.1 Sharding
First partition by risk bucket so all BTC-dependent targets subscribe to the BTC common/basis factors and ETH targets do not. Within a large bucket, shard quote ownership by venue and then expiry or stable instrument hash. Each instrument has exactly one active quote owner per execution session. All owners consume the same bucket state; no central pricer emits a vector of option prices.
Avoid one multicast group per option. Recommended groups are economic lanes such as BTC common/basis, BTC volatility, BTC position state and control/recovery. If the BTC factor packet remains small, a single fixed schema is simpler and safer than excessive group partitioning.
10.2 Data-oriented local calculation
Store fair0, J, packed Hessian, theta, credits, ticks, position loadings and current wire state in structure-of-arrays form.
Pin quote actors and their memory to the local NUMA node; pre-fault pages and allocate before entering the live loop.
Use changed_factor_mask intersected with per-instrument dependency masks to avoid unrelated work.
Vectorize common price/delta/gamma operations across instruments; use scalar slow exceptions only for unusual contracts.
Place no heap allocation, logging format, dynamic schema lookup or remote cache/database access in the event loop.
Bound work per event. A newer absolute market state may supersede queued market work; position/order work may not be skipped.
10.3 Quote-boundary trigger indexes
A factor move changes every theoretical fair with nonzero delta, but it does not necessarily change every wire price. For the dominant one-dimensional factor, precompute the nearest factor values at which the rounded desired bid, ask, size tier or action state changes:
Q_i(x) = round_to_tick(F_i(x) +/- credit_i + position_adjustment_i)
Maintain upper and lower trigger structures. When x moves, pop and recompute only instruments whose boundaries were crossed, then calculate and reinsert their next boundaries. Gamma and cross-factor movement limit how long a boundary remains valid; triggers are certified only inside the model trust region.
For basis, vol or position factors that affect non-monotonic subsets, maintain factor-to-instrument dirty bitsets. A large move, model activation or trust breach triggers a vectorized full-shard scan. The optimization MUST never prevent the safe full-scan fallback.
10.4 Output suppression
After fair, credits, inventory and action policy are evaluated, compare the complete desired order state to the gateway's last acknowledged/in-flight state. Emit an intent only if price, size, side permission, cancel state or a required generation changed. Recomputing a fair is cheap; unnecessary cancel/replace traffic loses queue priority, consumes venue rate limits and increases operational cost.
desired = quote_policy(fair, uncertainty, local_book, position, limits)
if desired == actor.last_desired and no_reconciliation_required:
    return
actor.last_desired = desired
execution_gateway.apply_order_state_diff(desired)

10.5 Capacity example
For illustration, a complete 128-byte factor state at 20,000 updates per second is 2.56 MB/s of payload per receiver. Sending 5,000 instrument values at 16 bytes each at the same rate is 1.6 GB/s per receiver before transport overhead. The factor design is roughly 625 times smaller in this example, before accounting for output suppression and multicast producer savings.
naive_bytes ~= update_rate x target_count x bytes_per_target x consumers
factor_bytes ~= update_rate x factor_message_bytes x consumers
Multicast changes producer transmission from approximately C copies to one local packet, but every receiver still consumes bytes and some cloud providers bill replicated receive processing. The dominant architectural gain comes from sending K factors instead of N target values, where K is tens and N can be thousands.
10.6 Backpressure and overload
Overload
Market-state response
Authoritative-state response
Quote actor behind
Skip to newest complete FactorState, count skipped sequences and full-scan current desired state.
Continue processing every position/order event in order; if lag bound exceeded, cancel/prohibit trading.
Factor engine input burst
Bounded receive batches; coalesce only already-decoded absolute states from same source where semantics permit; never wait on a timer.
N/A
WAN queue growth
Drop superseded absolute source states by key and retain latest; health reflects loss/age.
Position/order WAN is separate reliable lane and must exert explicit backpressure/fail safe.
Execution rate limit
Continue fair state; suppress churn and prioritize risk-reducing actions.
Order actor tracks exact in-flight state and venue limits.

11. Defensive, offensive and aggressive action logic
11.1 One state, separate action thresholds
All actions derive from the same current fair and uncertainty but have separate evidence and risk thresholds. Publishing separate additive 'defensive move' and 'confirmed move' price streams would reintroduce double counting. Instead, FactorState carries quality/action flags and quote policy interprets them.
Action class
Evidence threshold
Typical action
Re-entry/continuation
Defensive
Fresh first valid observation; lower mean confidence acceptable if adverse-selection risk is material.
Cancel, widen, reduce size, disable one side.
Re-enter when state is fresh/valid, factor uncertainty falls and hysteresis criteria are met.
Offensive passive
Canonical factor mean and local book valid; expected maker edge positive after latency, queue and fee model.
Reprice or improve passive quote; change size/skew.
Continue while model trust, rate limits and inventory permit.
Aggressive
High confidence, adequate independent source-family evidence or strong single-source quality, valid target book and positive post-cost edge.
Cross spread/take liquidity or hedge immediately.
One-shot decision with post-trade position/order reconciliation.

11.2 Expected-edge calculation
expected_edge = target_fair - executable_price - fees - slippage - latency_decay - hedge_cost - risk_charge
Action confidence is not the same as factor variance alone. The policy also consumes target-book freshness, available size, own in-flight orders, inventory, hedge availability, venue status, throttles and model trust. Aggressive action MUST require the stricter of alpha and risk thresholds; a defensive cancel can be allowed when aggressive trade is prohibited.
11.3 Avoiding permanent out-of-market behavior
Defensive logic uses a state machine with hysteresis, not a fixed cool-down or a cancel on every remote packet. It records why a quote left the market and evaluates an explicit re-entry condition. Examples include factor uncertainty below threshold, local target book current, no unresolved sequence gap, fair inside model trust, and desired quote safely outside adverse executable levels.
Metrics MUST attribute out-of-market time to stale feed, clock, model, position, risk limit, venue throttle, execution reconciliation or genuine no-edge state. Without attribution, an apparently safe defensive feature can silently destroy availability.
11.4 Execution ownership and idempotency
The quote actor publishes desired order state, not imperative sequences such as cancel then add. The execution gateway owns the actual venue order lifecycle and calculates the minimal state transition using acknowledged and in-flight orders. Every intent includes quote generation, model generation, factor sequence and position sequence for attribution. Obsolete intents are discarded by generation/sequence.
A fill is first applied by the authoritative position sequencer using venue execution IDs and internal dedup keys. The resulting position state is then visible to all affected quote actors. Local speculative fill application MAY reduce latency but must reconcile to the authoritative sequence and must never be applied again when the confirmed fill arrives.
12. Network and compute infrastructure
12.1 Transport by locality
Scope
Recommended default
Reason
Same thread/process
Direct function/state update or bounded single-writer structure
No network serialization or scheduling hop.
Same host
Shared-memory SPSC rings or one-writer/many-reader latest-state slots
Lowest predictable latency; market consumers can jump to latest absolute state.
Same colo/L2, many consumers
UDP multicast, one logical sequence, redundant physical paths
One producer packet and identical fan-out without per-consumer send loops.
Same colo, few consumers
Measured choice between unicast and multicast
Unicast may be simpler when replication and recovery complexity outweigh sender savings.
Cross-region
Compact redundant unicast/point-to-point streams to one regional relay; local re-fan-out
Cloud/WAN multicast is limited, topology-dependent and not a substitute for location-local inference.
Control/recovery
Reliable unicast stream or service
Models, configs, fills and recovery ranges require integrity and explicit completion.
Archive/analytics
Asynchronous broker/object storage
Throughput and replayability matter more than packet-to-quote latency.

12.2 Multicast is a transport optimization
Local L2 multicast reduces producer serialization, system calls and NIC transmission from one copy per consumer to one packet replicated by the switching fabric. It does not deduplicate economic events, guarantee delivery, provide per-consumer backpressure or necessarily reduce provider billing. The message layer still requires epoch/sequence, application integrity and recovery/health policy.
Cloud implementations require particular caution. AWS Transit Gateway supports multicast but AWS warns that it may not be suitable for HFT/performance-sensitive applications [R18]. AWS pricing states that data processing applies to each gigabyte received by each multicast receiver [R19]. Google Cloud multicast is intra-region, does not support cross-region multicast, charges multicast infrastructure reservation and bills processing in projects where consumers receive traffic [R20]. Therefore managed cloud multicast must be benchmarked and costed as a regional fan-out service, not assumed to be a low-latency or billing shortcut.
unicast_source_bytes ~= stream_bytes x consumer_count
multicast_source_bytes ~= stream_bytes ; total_receiver_bytes ~= stream_bytes x consumer_count
12.3 Multicast group plan
FAC.BTC.<region>.FAST        absolute common/basis factor state
FAC.BTC.<region>.VOL         optional volatility factor state
POS.BTC.<region>.RELIABLE    position/risk state (reliable semantics)
CTL.BTC.<region>.MODEL       model/config generations
REC.BTC.<region>             snapshot/range-recovery endpoint
HEALTH.<region>              low-rate infrastructure state

Groups SHOULD be organized by risk bucket and semantic lane, not individual target instrument. Consumers join only the buckets they price. If traffic requires subdivision, split by factor family with an explicit dependency map; do not split a single atomic factor schema in a way that creates inconsistent partial states.
12.4 Redundant paths
Venue direct feeds SHOULD use exchange-prescribed A/B or independent connections where entitled; exact sequences are arbitrated earliest-valid.
Internal local state SHOULD have physically diverse switches/NIC queues or paths when the latency and availability case justifies it.
WAN source states SHOULD traverse independently measured carriers or tunnels where a single path failure would materially impair trading.
Redundant publishers must represent one logical epoch/sequence. Independent split-brain factor states are prohibited.
Path selection is never allowed to change economic source identity: two network copies of Binance BTC perpetual remain one source observation.
12.5 Host and CPU design
The low-latency implementation SHOULD use isolated pinned cores, NUMA-local memory, preallocated fixed-size objects, bounded rings, cache-friendly arrays and explicit NIC queue affinity. Interrupt moderation, receive-side scaling, busy polling and kernel bypass are engineering choices to benchmark on the actual host and feed. DPDK poll-mode drivers access RX/TX descriptors directly without ordinary data interrupts, but they add operational and security complexity and are not automatically superior for every crypto WebSocket path [R21].
Concern
Requirement
Core ownership
One hot actor or compatible SPSC stage per core; no contended global locks.
Memory
Pre-fault, NUMA-local, bounded and allocation-free after warm-up; explicit cache-line ownership.
NIC queues
Affinity documented per feed/path; monitor ring drops, queue imbalance and timestamp capability.
Scheduling
Isolate hot cores from noisy neighbors, background agents, log compression and control-plane jobs.
Serialization
Generated fixed-layout binary codec; no JSON or reflection on internal hot lanes.
Packet size
One application message per datagram where practical; no IP fragmentation in certified topology.
Logging
Binary non-blocking event journal; formatting and export off-core.
Garbage collection
No stop-the-world runtime on the strict hot path unless latency tails are empirically certified.

12.6 Binary encoding
Internal hot schemas SHOULD use SBE or an equivalent generated fixed-layout encoding with declared byte order, field presence and schema version. FIX Trading Community describes SBE as a high-performance binary encoding for transactions and market data and it became an ISO/IEC standard in 2025 [R17]. Exact exchange prices and quantities are decoded into signed fixed-point integers using reference-data scales; model factors may use declared IEEE-754 binary64 where the mathematical implementation requires it. No field may rely on language-native structure padding.
A datagram header SHOULD contain magic, schema ID/version, payload length, bucket/channel, epoch, sequence and CRC32C. Incompatible schema changes use a new group/port or a coordinated major version. Minor changes may append optional fields only where generated decoders certify forward/backward behavior.
12.7 Security and entitlements
Market-data subscriptions, non-display use and redistribution topology MUST comply with each venue/vendor licence. Consolidating a feed technically does not create redistribution rights.
Control-plane model/config artifacts MUST be authenticated, integrity checked and authorized by environment/bucket.
WAN observations SHOULD use private circuits or authenticated encryption according to threat model; latency exceptions require documented compensating network isolation.
Hot multicast networks MUST be isolated by VLAN/VPC, ACL and source controls. Receivers reject unknown publisher identity/epoch/schema.
Secrets are loaded before the hot loop and are never included in telemetry, packet capture or model artifacts.
Builds, schemas, configs and models are immutable/versioned and traceable to deployment approval.
13. Interface, schema and configuration contracts
13.1 Common envelope
DataPlaneEnvelope {
  u32 magic; u16 schema_id; u16 schema_version; u16 payload_length;
  u16 flags; u32 channel_or_bucket_id; u64 publisher_epoch; u64 sequence;
  i64 publish_time_ns; u32 source_id; u32 crc32c;
  bytes payload[payload_length];
}

The envelope sequence is scoped by publisher identity/channel and epoch. It is not assumed to equal an exchange sequence. Payload schemas carry exchange watermarks separately. CRC covers normalized bytes according to schema. Consumers validate length before decode and never allocate from untrusted lengths.
13.2 CanonicalSourceState
CanonicalSourceState {
  bucket_id; venue_id; instrument_id; source_family_id; feed_policy_gen;
  source_epoch; source_seq; exchange_packet_seq; exchange_event_key;
  raw_exchange_event_time; normalized_event_time_ns; event_time_uncertainty_ns;
  edge_hw_rx_time_ns; edge_publish_time_ns;
  book_generation; plane_validity_mask; feed_health_state; health_reason;
  bid_px; bid_qty; ask_px; ask_qty; last_trade_px; cumulative_trade_id;
  feature_schema_id; absolute_features[M];
}

The source message is an absolute image for current-state fields. Flow features that naturally accumulate SHOULD use cumulative counters or explicitly windowed absolute values so packet loss is detectable and later state can heal. Raw individual depth events remain in the venue-local journal unless selected downstream consumers explicitly require them.
13.3 PositionState and FillEvent
FillEvent { position_epoch; position_seq; fill_id; venue_execution_id;
            instrument_id; side; quantity; price; fee; event_time; receive_time; }

PositionState { position_epoch; position_seq; account_scope; bucket_id;
                absolute_positions_or_risk_factors[]; reconciliation_status; content_hash; }

FillEvent processing is idempotent by venue/account/execution identifiers plus an internal collision-safe key. PositionState checkpoints provide recovery and model activation. A quote actor may consume compact risk factors if the adjustment matrix is factorized, but the authoritative service retains enough detail to reconstruct instrument positions and reconcile against every venue.
13.4 QuoteIntent
QuoteIntent {
  execution_session_id; instrument_id; side; desired_action; desired_price; desired_size;
  quote_generation; model_gen; factor_epoch; factor_seq; position_epoch; position_seq;
  fair_value; edge_components; action_class; confidence; reason_mask; expiry_time_ns;
}

The execution gateway rejects expired or superseded intents and emits an OrderState result. Desired_action is state-oriented - present/amend/cancel/disabled - rather than a blind imperative. All numeric diagnostic fields can be removed from the minimum wire schema if a parallel decision journal records them without adding latency.
13.5 Configuration generations
Generation
Contents
Activation rule
ReferenceDataGen
Instrument IDs, contract definitions, scales, ticks, expiry, currencies and venue mappings.
Must precede any config/model that references it.
FeedPolicyGen
Channel semantics, exact race groups, snapshot/recovery and health thresholds.
Adapter atomic swap after connection validation.
InfluencerConfigGen
Measurement loadings, basis models, source families, age/variance and action permissions.
Factor-engine atomic bucket boundary.
FactorSchemaGen
Ordered factor IDs, units and transformation conventions.
New compatible engine/model generation; major changes require new data-plane schema.
ModelGen
Per-target valuation rows, credits, position adjustment and trust limits.
Quote-actor watermarked atomic activation.
RiskPolicyGen
Position/size/action limits and kill conditions.
Risk-authorized atomic activation; restrictive changes may apply immediately.

All generations carry content hashes and dependency IDs. A service that cannot resolve a dependency enters a conservative state; it may not silently substitute latest or default reference data.
14. Failure handling and operational safety
14.1 Failure matrix
Failure
Detection
Immediate action
Recovery proof
Exact feed packet gap
Sequence discontinuity
Invalidate affected reconstructive plane; use independent valid planes only; no aggression from invalid book.
Retransmit/snapshot bridge and new book generation.
Feed staleness/queueing
Age/cadence/path tail or cross-feed inconsistency
Inflate R, reduce action mask; hard reject after max age.
Fresh sequence/current state for configured hysteresis period.
Clock drift
PTP/PHC offset or uncertainty breach
Disable cross-host timing claims; inflate R; local receive order remains available.
Clock locked within threshold and stable hold period.
WAN partition
Heartbeat/source age
Regional engine continues from local/remaining sources with higher uncertainty; remote source rejected.
Current absolute source state and path health restored.
Factor engine failover
Process/path health
Advance epoch; temporarily restrict aggression until current inputs proven.
New epoch with source/config/position watermarks current.
Factor packet loss
Sequence gap
Jump to next complete state; record skip; full-scan local desired orders.
New state accepted; no historical replay required.
Model stale/trust breach
Age or displacement bounds
Widen/reduce/cancel; aggressive disabled; request model.
Validated fresh ModelGen activated.
Position gap/divergence
Position sequence or reconciliation mismatch
Cancel/prohibit affected bucket; never estimate through missing fills.
Authoritative checkpoint and venue reconciliation.
Execution session uncertainty
Ack timeout, sequence reset, disconnect
Stop new risk; reconcile/cancel through venue-prescribed path.
Complete open-order/position reconciliation.
Venue basis dislocation
Large persistent basis residual
Move residual to basis factor if model supports; otherwise quarantine source/offensive use.
New calibrated regime or residual normalization.
Source anomaly/spoof
Impossible price, crossed book, CRC/schema/auth failure
Reject/quarantine and alert; preserve evidence.
Validated stream or explicit operator release.

14.2 Kill hierarchy
Kills are scoped from narrowest to broadest: feed plane, influencer source, target instrument, venue session, risk bucket, execution region and global strategy. A feed fault SHOULD not unnecessarily kill unrelated buckets. A position or execution uncertainty may require a wider kill than a market-feed fault. Every kill has owner, reason, generation, trigger, permitted residual actions and release criteria.
14.3 Recovery never creates alpha
When a recovered book differs from the last local book, downstream consumers replace the canonical plane and mark the generation change. They do not interpret the entire difference as a current price innovation. The factor engine uses recovery time/sequence and other live observations to determine whether any residual information remains. This rule prevents a reconnect or snapshot from causing a mass false reprice.
15. Observability, evidence and cost accounting
15.1 Mandatory metrics
Layer
Metrics
NIC/path
Packets/bytes, RX ring drops, hardware timestamp availability, queue distribution, multicast duplicates, path p50/p99/p99.9.
Feed
Sequence gaps, out-of-order, duplicate rate, age, disconnects, snapshot/recovery time, validity state and reason.
Arbiter
Feed-firstness matrix, correlation success, exact/semantic suppressions, state-plane generation and conflicts.
Factor
Source innovations, applied gain/weight, robust rejects, state uncertainty, fixed-lag replay work, cause revisions and publish latency.
Model
Active generation, age, trust displacement, snapshot validation failure, approximation error versus analytical shadow.
Quote actor
Factor-to-decision latency, instruments dirty/evaluated/changed, trigger hits, full scans, skipped market sequences and output suppression.
Execution
Intent-to-wire, ack/fill latency, rejects, rate limits, queue churn, stale intents, order reconciliation and post-only outcomes.
Risk/availability
Position watermark lag, divergence, action masks, out-of-market time by reason, defensive exits/re-entry and kill duration.
Cost
Feed/licence/cross-connect fixed cost, WAN bytes, multicast receiver bytes, compute/core usage, cloud processing and archive volume by bucket/source.

15.2 Decision journal
For every FactorState that changes action-relevant state, the asynchronous journal records input source watermark, raw and normalized times, pre-update state, innovation, configured R and gates, post-update state, uncertainty, cause ID and action mask. For every changed QuoteIntent, it records model/factor/position generations, fair components, rounded desired state, local book and policy reasons. This evidence is required to diagnose apparent double reactions, missed moves and excessive defensive time.
Logging MUST be binary and non-blocking on hot cores. Human formatting, aggregation and export occur off-path. Sampling is acceptable for stable heartbeat detail but not for gaps, kills, model activations, fills, order state or factor revisions that changed a quote.
15.3 Cost attribution
marginal_source_value = live_or_replay_decision_value - fixed_cost - bytes_cost - compute_cost - operational_risk_charge
Cost reports distinguish producer bytes from total receiver bytes and separate local, cross-zone and cross-region traffic. Multicast may reduce sender work while provider data-processing charges still grow with receivers. Feed analysis must include market-data licensing, cross-connect/port, premium channel tier, redundant connections and staff/on-call complexity as well as cloud bills.
16. Testing, certification and acceptance
16.1 Test pyramid
Level
Required coverage
Codec/schema unit
Golden packets, endianness, fixed-point scales, malformed lengths, unknown versions, CRC, compatibility and field semantics.
Adapter/book unit
Snapshot bridge, every update action, sequence reset/wrap, crossed books, reconnects and venue-specific edge cases.
Property tests
Duplicate/reorder/loss permutations, idempotency, absolute-state convergence and watermark algebra.
Deterministic replay
Raw receive-order packet replay through adapter, arbiter, factor, quote and simulated execution with reproducible outputs.
Statistical validation
Out-of-sample source selection, residual calibration, basis stability, false reaction and action-level P&L/availability.
Latency benchmark
p50/p99/p99.9 under normal and burst traffic, CPU isolation/NUMA/NIC variants and tail regression gates.
Chaos/fault injection
Packet loss, duplication, reordering, clock drift, WAN partition, process failover, model corruption, position gaps and rate limits.
Shadow/canary
Production feeds and models with no orders, then defensive-only, limited passive and finally aggressive permission.

16.2 Mandatory double-reaction scenarios
The same CME-style A/B packet arrives B then A. One canonical update and one factor sequence result.
Binance BBO reveals a move; raw trade and depth consequences follow; aggregate trade arrives later. Price mean moves only by conditional information, while confidence/features may revise.
OKX local market moves before a delayed Binance observation reaches the execution region. The remote message contributes only its residual relative to the already current state.
A usual leader sends an exchange timestamp two hours old. It is rejected even if it is the newest packet received on that connection.
The local target feed becomes stale while remote sources remain current. Locality does not preserve its weight; action permissions reflect target-book invalidity.
A recovery snapshot produces a large state difference. The book generation replaces state without treating the whole recovered difference as a new shock.
The same FactorState is duplicated/reordered on multicast. Every quote actor's final desired state is identical and no duplicate intent is emitted.
A model activation races a factor revision and a fill. Watermarks produce the same final fair regardless of permitted processing interleaving.
A large BTC move crosses the Taylor trust region. Aggressive action stops and fallback/full repricing activates without stale continuation.
One consumer lags thousands of market states. It jumps to the latest complete state and converges; a missing fill instead triggers safe failure.
16.3 Core mathematical properties
Idempotency: applying the same source or factor message twice yields the same state as applying it once.
Permutation invariance for exact duplicates: A/B arrival order does not change economic output.
Latest-state convergence: after arbitrary market packet loss, receipt of a newer complete state converges the consumer to the publisher state.
Watermark equivalence: evaluating a new ModelSnapshot against current absolute z/q equals applying all post-reference changes exactly once.
Position conservation: authoritative fills reconcile exactly to venue/account positions; no model or market reset changes position.
Bounded approximation: fast-versus-analytical error remains within certified tolerance inside the trust region.
No-lookahead replay: decisions only use observations whose recorded receive time was available at that location.
16.4 Acceptance gates
Gate
Acceptance criterion
Correctness
Zero duplicate economic application across certified replay corpus; all model/factor/position generation races pass property tests.
Feed integrity
All prescribed gap/snapshot/reset scenarios pass per venue; invalid books cannot authorise prohibited actions.
Latency
Feed-RX to factor-publish and factor-RX to quote-intent p99.9 meet deployment budgets under certified burst load.
Capacity
Maximum configured target count and event rate fit CPU/memory/network budgets with bounded queues and no post-warm-up allocation.
Availability
Out-of-market time is attributable by reason; defensive re-entry meets approved policy without oscillation.
Risk
No trade occurs on unresolved position/order divergence; all kills and failovers have tested recovery proof.
Model
Fast approximation error, basis residuals and source gains pass out-of-sample and shadow tolerances.
Operations
Rollback, config/model compatibility, schema upgrade, monitoring, packet evidence and on-call runbooks are complete.

17. Worked examples
17.1 Raw cross-venue differential versus relative innovation
Assume Binance BTC is displayed at $61,000 and OKX BTC at $60,000. The raw $1,000 difference is not itself a signal. The slow basis model may indicate that, for the particular quote currencies/contracts/session, Binance normally trades $1,010 above OKX with a residual standard deviation of $12. The normalized observations are therefore approximately aligned; OKX being $10 rich relative to expected basis is the relevant residual, not the $1,000 raw gap.
normalized_common_from_k = transform(raw_price_k) - expected_basis_k(current factors)
If Binance then rises by $100 while its expected basis is unchanged and OKX has not moved, the observation may update common BTC. If funding or a venue-specific dislocation explains $30, the factor engine might allocate $70 to common state and $30 to Binance perpetual basis. If OKX already rose $67 before the Binance message reaches the OKX execution colo, the delayed Binance evidence revises common state only by the residual amount supported by the joint model.
17.2 Binance spot and perpetual both influence BTC
At reference time the regional state has common BTC x0 = $60,500. Binance spot, Binance perpetual, OKX spot and CME front future are configured measurements. Binance spot/perpetual share a source family; the future has a maturity basis factor.
#
Observation
Illustrative factor interpretation
Published behavior
1
Binance perpetual +$100
Initial common +$60, perp-basis +$40; medium confidence because only the perp has moved.
Absolute state x=$60,560; basis_perp=+$40; defensive/offensive policy as configured.
2
Binance spot +$72
Joint evidence revises common to +$70 and perp-basis to +$30; source-family covariance prevents double vote.
New absolute state x=$60,570; same cause revision; confirmation may reduce variance.
3
OKX local spot had already moved +$67
In an OKX-region arrival order this may have established x near +$66 before remote Binance arrived.
Delayed Binance revises to +$70 rather than adding +$100.
4
CME future +$74 after curve normalization
Independent source family supports common move; remaining difference enters curve/basis residual.
Mean may barely change; uncertainty/action permission can improve.

The numeric split is illustrative; production weights come from calibrated H, R, covariance and robust gates. The invariant is that each observation updates an explicit state and later observations are conditional on that state.
17.3 Applying delta and gamma to a target option
Suppose the final common BTC move is +$70 and the target-specific basis/FX mapping adds +$4 relative to the option's reference. The option's effective underlying move is therefore +$74. Let delta = 0.42, gamma = 0.00008 per dollar, theta over the elapsed interval = -$0.01, and position adjustment = +$0.30.
Delta V = 0.42 x 74 + 0.5 x 0.00008 x 74^2 - 0.01 + 0.30
Delta V = 31.08 + 0.219 - 0.01 + 0.30 = $31.589
The quote actor adds this to fair0, applies bid/ask credit and risk policy, rounds to the venue tick and compares with its current desired/actual order. It does not additionally apply the raw +$100 Binance move or separately add the same +$4 basis if delta was defined to S_eff. If the model instead provides a Jacobian to common and a separate basis sensitivity, both appear once in J Delta z.
17.4 One match represented by four feeds
Illustrative arrival sequence: BBO at local RX t0, raw trade at t0+30 microseconds, incremental depth at t0+80 microseconds and aggregate trade at t0+100 milliseconds. The BBO is valid for defense and produces an initial canonical quote-plane change. The trade enriches flow and only adds price innovation not already represented. The depth update completes canonical book state and may reveal additional imbalance. The aggregate trade is correlated confirmation/rolling flow, not a fourth independent price shock. No fixed 100 ms wait is introduced.
17.5 Model activation racing a fill
Model generation 41 references factor sequence 8,000 and position sequence 1,200. Before a quote actor activates it, factor state reaches 8,010 and a fill produces position sequence 1,201. The actor validates that it has absolute z at 8,010 and q/r at 1,201, atomically swaps model 41, and evaluates z(8,010)-z0(8,000) plus q(1,201)-q0(1,200). No event must be guessed as 'before' or 'after' the model; the watermarks define it exactly.
17.6 Illustrative BTC influencer configuration
bucket: BTC
factor_schema: [btc_common, usd_usdt, binance_spot_basis, binance_perp_basis,
                okx_spot_basis, okx_perp_basis, cme_front_curve, krw_usd, upbit_premium]
sources:
  - instrument: BINANCE:BTCUSDT:SPOT
    family: BINANCE_MATCHING
    feeds: [SBE_BBO, SBE_TRADE, SBE_DEPTH]
    loads_on: {btc_common: 1, usd_usdt: 1, binance_spot_basis: 1}
    actions: [defensive, offensive, aggressive_if_high_quality]
  - instrument: BINANCE:BTCUSDT:PERP
    family: BINANCE_MATCHING
    loads_on: {btc_common: 1, usd_usdt: 1, binance_perp_basis: 1}
  - instrument: OKX:BTC-USDT:SPOT
    family: OKX_MATCHING
    loads_on: {btc_common: 1, usd_usdt: 1, okx_spot_basis: 1}
  - instrument: OKX:BTC-USDT-SWAP
    family: OKX_MATCHING
    loads_on: {btc_common: 1, usd_usdt: 1, okx_perp_basis: 1}
  - instrument: CME:BTC_FRONT
    family: CME_GLOBEX
    loads_on: {btc_common: 1, cme_front_curve: 1}
  - instrument: UPBIT:KRW-BTC
    family: UPBIT_MATCHING
    loads_on: {btc_common: 1, krw_usd: 1, upbit_premium: 1}
notes: all variances, max ages, feed policies and regime tables are versioned analysis outputs

18. Team work packages and ownership
18.1 Quant Research
Define factor schemas, economic normalization, basis/curve/FX/volatility models and Greek conventions.
Build candidate-universe and influencer-selection research with permanent price discovery, firstness and decision-level ablation.
Calibrate Q/R, source-family covariance, robust gates, age penalties, regime tables and action confidence mappings.
Produce analytical option values, J/H/theta, credits, position adjustment representation and trust-region error evidence.
Own shadow error reports: raw source -> normalized observation -> factor revision -> analytical/fast fair -> outcome.
Define certification datasets and numerical tolerances with Trading/Risk.
18.2 Low-Latency / C++ Engineering
Implement venue adapters, hardware/kernel timestamp capture, book builders, exact race groups and feed state machines.
Implement canonical source schemas, semantic planes, causal ledger, WAN publisher and deterministic replay.
Implement regional factor engine, bounded fixed-lag option, absolute FactorState publisher and logical epoch failover.
Implement quote actors, watermarked ModelSnapshot activation, SoA valuation, trigger indexes and order-state diff.
Implement reliable position integration and dense/sparse/low-rank adjustment paths.
Own codec generation, hot-loop allocation/locking audits and latency benchmarks.
18.3 Network Infrastructure
Design PTP grandmaster/boundary-clock/PHC topology and clock-quality monitoring.
Provision venue feed A/B paths, cross-connects, switches, VLANs, multicast groups, ACLs and NIC queue mapping.
Design redundant WAN source-state paths and one relay per execution region; measure one-way delay/tails where clocks permit.
Benchmark unicast versus multicast per locality, including packet loss, receiver scaling, provider limits and billed bytes.
Document MTU, QoS, multicast membership, failover and packet-capture points.
Own capacity and cost model for links, ports, cloud processing and receiver growth.
18.4 DevOps / SRE
Build immutable deployment artifacts for schemas, binaries, reference data, configs and models with dependency checks.
Implement staged generation rollout, canary/shadow deployment, rollback and per-bucket kill controls.
Configure core isolation, NUMA pinning, huge pages where used, NIC ownership and safe maintenance procedures.
Operate metrics, alerts, binary journal, packet retention, replay tooling and incident evidence.
Own runbooks for feed gap, clock drift, WAN partition, factor failover, model failure, position divergence and venue disconnect.
Track SLOs, out-of-market attribution, cloud/network cost and schema/config drift.
18.5 Execution / Trading / Risk
Define defensive, offensive and aggressive thresholds, inventory limits, edge charges and hedge availability rules.
Certify order-state ownership, post-only behavior, rate-limit prioritization, kill scope and re-entry policy.
Approve model trust/error limits and what remains permitted during slow-path outage or feed degradation.
Own venue/account position reconciliation and incident release authority.
Review live shadow/canary outcomes before each action-class expansion.
18.6 Cross-team interface deliverables
Deliverable
Producer
Consumers
Exit evidence
Feed semantic registry
Low-latency + Network
Quant, SRE, Replay
Certified golden packets and recovery tests.
Factor schema and InfluencerConfig
Quant
Factor engine, Model service
Out-of-sample selection and residual report.
ModelSnapshot schema
Quant + Low-latency
Quote actors, Risk
Analytical/fast error and watermark tests.
Data-plane topology
Network
Low-latency, SRE
Packet-loss/latency/cost benchmark.
Position/order contract
Execution + Risk
Quote actors, SRE
Idempotency and reconciliation certification.
Action policy
Trading/Risk + Quant
Quote actors
Replay metrics for edge, adverse selection and availability.
Runbooks/SLOs
SRE
All teams
Chaos exercise and on-call sign-off.

19. Delivery roadmap
19.1 Phase 0 - Measurement foundation
Deliver clock infrastructure, raw packet/frame capture with local receive timestamps, venue semantic registry, instrument reference data and replayable adapters. No cross-venue trading decisions are enabled. Exit only when receive-time evidence is trustworthy enough to answer which feed was first for matched events.
19.2 Phase 1 - Canonical venue state
Implement book builders, exact A/B/duplicate arbitration, semantic planes, feed state machines, snapshot/recovery and canonical absolute source messages. Prove that duplicate/reorder/loss permutations converge correctly. Archive raw and canonical states side by side.
19.3 Phase 2 - Factor engine in shadow
Deploy location-local BTC factor engines consuming selected sources. Publish absolute state to shadow consumers only. Compare against analytical/offline reconstructions, measure source innovations, fixed-lag benefit, basis residuals and implied double-reaction rate. No execution behavior changes.
19.4 Phase 3 - Defensive integration
Allow factor quality to cancel/widen/reduce quotes while passive price remains driven by the incumbent path. Measure avoided adverse selection, false exits, re-entry latency and out-of-market attribution. This phase validates health and action separation before the platform moves prices.
19.5 Phase 4 - Passive mass repricing
Activate ModelSnapshot, local factor repricing, target-effective underlying mapping, quote-boundary triggers and output suppression for a small BTC option shard. Expand by venue/expiry only after analytical error, latency, churn and position-watermark gates pass.
19.6 Phase 5 - Aggressive actions and full scale
Enable aggressive action for narrowly certified source/regime combinations. Complete 5,000-20,000 target burst tests, logical factor failover, redundant network paths, low-rank position optimization if required, and full incident drills. Maintain independent kill switches for aggressive, offensive and defensive behavior.
19.7 Phase exit checklist
Replay corpus includes normal, volatile, outage, reconnect, gap, clock and venue-maintenance periods.
All adapter/config/model schemas and generation dependencies are frozen for the phase and backward compatibility is tested.
Latency and capacity results come from production-equivalent hardware/network, not developer laptops or average-only benchmarks.
Quant, Low-latency, Network, SRE, Execution and Risk owners sign their interface evidence.
Rollback and kill have been exercised, not merely documented.
Business value includes availability and cost, not only gross signal P&L.
20. Normative requirement catalogue
ID
Requirement
SYS-001
One logical factor state MUST exist per bucket and execution region.
SYS-002
Influencer selection MUST be configuration, not hard-coded venue logic.
SYS-003
Market, position, model and order generations MUST be independently identified and attributable.
FED-001
Every feed MUST have registered sequence, timestamp, conflation, snapshot and recovery semantics.
FED-002
Exact duplicate feeds MUST be raced by a stable exchange key where available.
FED-003
A reconstructive feed gap MUST invalidate every dependent book feature until recovery proof.
FED-004
Recovery state MUST replace state without automatically becoming a current alpha shock.
ARB-001
Different feed representations MUST be maintained in semantic planes and conditionally combined.
ARB-002
A fixed debounce timer MUST NOT be the primary duplicate-suppression mechanism.
ARB-003
Source-family correlation MUST prevent message-count confirmation.
TIM-001
Raw exchange timestamps and local RX timestamps MUST both be retained.
TIM-002
Durations MUST use a monotonic clock; cross-host UTC/TAI mapping MUST carry uncertainty.
TIM-003
Cross-venue messages MUST NOT be globally reordered solely by exchange timestamp.
TIM-004
Sequence MUST take precedence for continuity inside a sequenced feed.
FAC-001
Factor updates MUST condition observations on current or bounded fixed-lag state.
FAC-002
FactorState MUST be absolute and ordered by epoch/sequence.
FAC-003
FactorState MUST include uncertainty/quality separately from mean.
FAC-004
Late/stale source weight MUST depend on age, health and timestamp uncertainty; locality alone is insufficient.
MOD-001
ModelSnapshot MUST include z0, q0, reference time and factor/position watermarks.
MOD-002
Every Greek MUST declare independent variable, units, reference and trust radius.
MOD-003
Model activation MUST be atomic and dependency validated.
FST-001
Fast fair MUST be recomputed from current absolute state and snapshot references, not accumulated commands.
FST-002
Target options MUST use target-effective factor movement consistent with Greek definition.
FST-003
Fast path MUST provide a safe fallback when trust bounds are exceeded.
SCL-001
Factor state MUST be fanned out instead of a full vector of target prices.
SCL-002
Quote actors MUST emit only changed desired wire state.
SCL-003
Market backpressure MAY skip to the newest complete state; positions/orders MUST NOT be silently skipped.
POS-001
Fills MUST be idempotent, ordered and reconciled to venue/account state.
POS-002
Position-adjustment application MUST be traceable to position sequence and ModelSnapshot reference.
EXE-001
Execution gateway MUST own actual order lifecycle and reject stale intents.
EXE-002
Defensive, offensive and aggressive permissions MUST be independently controlled.
NET-001
Transport choice MUST follow locality and measured latency/cost; multicast is not assumed reliable or cheaper.
NET-002
Hot data-plane messages MUST fit the certified MTU and use fixed-layout versioned encoding.
NET-003
One logical sequencer MUST govern redundant factor publishers; failover advances epoch.
OPS-001
Every degradation/kill MUST include reason, scope, generation and release criteria.
OPS-002
Decision evidence MUST preserve raw observation, applied innovation, state and quote attribution.
TST-001
Duplicate/reorder/loss, model/fill races and stale-leader scenarios MUST pass deterministic replay.
TST-002
Latency certification MUST include burst and tail percentiles on production-equivalent infrastructure.

Appendix A. Operational runbook outlines
A.1 Feed gap
Confirm affected venue/channel/sequence range and whether independent BBO/trade planes remain valid.
Verify automatic state transition and action restrictions; prohibit invalid depth features.
Initiate venue-prescribed retransmit/snapshot recovery; preserve buffered increments according to bridge rules.
Publish new book generation only after continuity proof; verify factor engine did not treat recovery delta as current shock.
Review packet evidence and path-health asymmetry; open carrier/exchange incident if recurring.
A.2 Clock-quality breach
Identify PHC/host/grandmaster scope, offset magnitude, servo/holdover state and affected timestamp claims.
Inflate measurement uncertainty and remove cross-host firstness/aggressive permissions as configured; preserve local receive order.
Fail over clock source only through approved PTP procedure; avoid wall-clock steps in live duration logic.
Require stable in-threshold hold period before restoring permissions; annotate all affected replay evidence.
A.3 Position divergence
Immediately cancel/prohibit affected scope; market-data validity does not override unknown position.
Freeze speculative position paths and compare internal fill ledger, drop copy, venue positions and custodian/account state.
Resolve duplicate/missing execution IDs and establish an authoritative PositionState checkpoint.
Recalculate model adjustment from checkpoint, reconcile open orders, then release through Risk authority.
A.4 Factor-engine failover
Advance engine epoch; reject any subsequent packet from the old epoch even if its sequence is numerically higher.
Load current config and latest absolute source planes; verify clock, source and position health.
Publish an absolute factor checkpoint with failover flags; quote actors full-scan desired state.
Restore offensive/aggressive permission only after configured evidence and no split-brain publisher is present.
Appendix B. Reference architecture decisions
Decision
Selected baseline
Rejected baseline and reason
Economic output
Absolute regional factor state
Raw leader deltas: non-idempotent and location-blind.
Influencer leadership
Time-varying measurement weight and health
Hard-coded venue leader: fails during regime/outage/basis shifts.
Cross-feed duplicate control
Exact key + semantic plane + conditional innovation + absolute consumer state
Fixed-time suppression: adds latency and loses genuine residual information.
Geography
One factor engine per execution region
Central global fair: forces an extra hop and erases local arrival advantage.
Mass option update
Local surrogate rows and factor fan-out
Central per-option price stream: O(N) network and another latency hop.
Market reliability
Latest-value complete state
Lossless unbounded market queue: stale work during bursts.
Position reliability
Sequenced/idempotent reliable state
Lossy multicast-only fills: unacceptable risk.
Model transition
Watermarked immutable snapshots
In-place coefficient mutation: race and attribution ambiguity.
Local fan-out
Shared memory or measured L2 multicast
Managed cross-region multicast: limited, billed and latency-uncertain.

Appendix C. Glossary
Term
Definition
A/B feed
Two transport copies of the same sequenced exchange feed, normally carried on diverse paths.
Action mask
Maximum action classes currently authorised by data/model/risk quality.
BBO
Best bid and offer/top-of-book state.
Cause ID
Identifier relating known revisions from one economic event.
Conflation
Combining multiple source events into a periodic or aggregate update.
Effective underlying
Target-specific factor mapping to which delta/gamma are defined.
Epoch
Generation that resets sequence interpretation after restart/failover/reset.
Fixed-lag update
Bounded insertion of a delayed observation into recent state followed by replay to now.
Information share
A measure of a market's contribution to innovations in a common efficient price.
MBO / MBP
Market by order / market by price order-book representations.
Nowcast
Current best state estimate using information available at the execution location.
PHC
PTP hardware clock associated with a NIC or timing device.
PTP
Precision Time Protocol for network clock synchronization.
SBE
Simple Binary Encoding, a generated fixed-layout binary standard used in financial systems.
Source family
Economically/infrastructurally correlated observations not treated as independent votes.
Trust region
Certified displacement/time/position domain where fast approximation error is bounded.
Watermark
Sequence reference identifying exactly which market/position state is embedded in a snapshot.

Appendix D. Sources and research basis
The specification is an engineering synthesis. Exchange details and cloud limits must be re-certified against current production documentation before implementation. Academic sources support the price-discovery/common-state framing; they do not substitute for the location-specific receive-time and decision-level tests required here.
[R1] One Security, Many Markets: Determining the Contributions to Price Discovery. Joel Hasbrouck, Journal of Finance, 1995. https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1540-6261.1995.tb04054.x
[R2] Estimation of Common Long-Memory Components in Cointegrated Systems. Gonzalo and Granger, Journal of Business & Economic Statistics, 1995. https://www.tandfonline.com/doi/abs/10.1080/07350015.1995.10524576
[R3] Price Discovery in Cryptocurrency Markets. Makarov and Schoar, AEA Papers and Proceedings, 2019. https://www.aeaweb.org/articles?id=10.1257%2Fpandp.20191020
[R4] Trading and Arbitrage in Cryptocurrency Markets. Makarov and Schoar, Journal of Financial Economics, 2020. https://www.sciencedirect.com/science/article/abs/pii/S0304405X19301746
[R5] SBE Market Data Streams. Binance Developer Documentation. https://developers.binance.com/en/docs/products/spot/sbe-market-data-streams
[R6] USD-M Futures WebSocket Market Streams. Binance Developer Documentation. https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/ws-streams/public
[R7] Market Data and Order Book Channels. OKX API Documentation. https://www.okx.com/docs-v5/trick_en/
[R8] Exchange WebSocket Overview. Coinbase Developer Documentation. https://docs.cdp.coinbase.com/exchange/websocket-feed/overview
[R9] Advanced Trade WebSocket Channels. Coinbase Developer Documentation. https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-channels
[R10] Recent Trades History / timestamp and sequential_id semantics. Upbit Developer Documentation. https://global-docs.upbit.com/v1.2.2/reference/today-trades-history
[R11] MDP 3.0 Incremental Feed Arbitration. CME Group Client Systems Wiki. https://cmegroupclientsite.atlassian.net/wiki/display/EPICSANDBOX/MDP%2B3.0%2B-%2BIncremental%2BFeed%2BArbitration
[R12] MDP 3.0 Recovery Services for UDP. CME Group Client Systems Wiki. https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457325847/MDP%2B3.0%2B-%2BRecovery%2BServices%2Bfor%2BUDP
[R13] MDP Packet Structure and Event-Based Messaging. CME Group Client Systems Wiki. https://cmegroupclientsite.atlassian.net/wiki/display/EPICSANDBOX/MDP%2B3.0%2B-%2BPacket%2BStructure%2Bwith%2BEvent%2BBased%2BMessaging
[R14] MDP 3.0 Trade Summary. CME Group Client Systems Wiki. https://cmegroupclientsite.atlassian.net/wiki/spaces/EPICSANDBOX/pages/457418925/MDP%2B3.0%2B-%2BTrade%2BSummary
[R15] IEEE 1588 Precision Time Protocol. IEEE Standards Association. https://standards.ieee.org/standard/1588-2008.html
[R16] Timestamping. Linux Kernel Documentation. https://docs.kernel.org/networking/timestamping.html
[R17] Simple Binary Encoding (SBE). FIX Trading Community. https://fixtrading.org/standards/simple-binary-encoding-sbe/
[R18] Multicast in AWS Transit Gateway. Amazon Web Services Documentation. https://docs.aws.amazon.com/vpc/latest/tgw/tgw-multicast-overview.html
[R19] AWS Transit Gateway Pricing. Amazon Web Services. https://aws.amazon.com/transit-gateway/pricing/
[R20] Multicast Overview. Google Cloud Documentation. https://docs.cloud.google.com/vpc/docs/multicast/overview
[R21] Poll Mode Driver. DPDK Programmer's Guide. https://doc.dpdk.org/guides-24.03/prog_guide/poll_mode_drv.html
Appendix E. Final implementation checklist
Economic factors and every target's Greek convention are documented and versioned.
All selected feeds have certified semantics, recovery, timestamps and exact race keys.
Receive-time data proves conditional feed firstness and tail behavior by location.
Source-family covariance and basis separation prevent duplicate confidence and raw-spread errors.
FactorState is complete, absolute, fixed-layout, epoch/sequence ordered and below certified MTU.
ModelSnapshot contains z0/q0/time and watermarks; atomic activation property tests pass.
Position/fill/order lanes are authoritative, reliable and reconciled.
Quote actors use local rows, target-effective movement, trigger/dirty indexes and output suppression.
Defensive, offensive and aggressive permissions are independent and observable.
Multicast/unicast topology is measured for latency, loss, receiver scaling and billed bytes.
All major fault scenarios and rollback/kill/re-entry procedures have been exercised.
Shadow and canary evidence supports each expansion in action class and target scale.
```
