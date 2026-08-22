---
doc_type: codex-ssot
title: VersiFi API Docs — Local Mirror
summary: "Permanent local mirror of docs.versifi.io's 12-page developer reference (auth, order endpoints, websocket
  connection/message handling), crawled 2026-08-22 via an authenticated Playwright session so the credentialed
  portal doesn't need re-crawling for every future lookup; source for the versifi WsProtocolSpec and error-map
  entries in unified-api-contracts."
status: current
nature: record
asset_group: [cefi]
stage: [execution]
repos: [unified-api-contracts]
scope: [engineer]
tags: [versifi, cefi, websocket, api-docs, error-mapping]
related:
  [
    /plans/active/venue_websocket_resilience_and_error_code_mapping_2026_08_21.md,
    /codex/03-services/venue-capability-registry.md,
  ]
created: 2026-08-22
authoritative_for: [versifi api docs mirror]
referenced_by: [/plans/active/venue_websocket_resilience_and_error_code_mapping_2026_08_21.md]
owner: ikennaigboaka
last_reviewed: 2026-08-22
code_refs:
  [
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/cefi.py,
  ]
---

# VersiFi API Docs — Local Mirror

> **Source**: `https://docs.versifi.io/reference/*` (password-gated ReadMe.com portal; password supplied
> out-of-band by the operator 2026-08-22, NOT recorded in this file or anywhere else on disk — a fresh
> credentialed session is required to re-crawl if this mirror ever needs updating).
> **Retrieved**: 2026-08-22, via an authenticated Playwright browser session.
> **Pages crawled** (every entry in the docs sidebar nav, all captured this session):
>
> - `/reference/introduction`
> - `/reference/authentication`
> - `/reference/post_v2-orders-algo` (Create Algo Order)
> - `/reference/post_v2-orders-basic-1` (Create Basic Order)
> - `/reference/post_v2-orders-pair-2` (Create Pair Order)
> - `/reference/delete_v2-orders-id-2` (Cancel order request)
> - `/reference/get_v2-orders-id-2` (Get Order by ID)
> - `/reference/get_api-v2-orders` (Get orders with filters)
> - `/reference/delete_v2-orders-batch` (Cancel Batch order request)
> - `/reference/an-overview-of-websocket` (WebSocket Overview)
> - `/reference/get_v1-ws-3` (WebSocket Connection & Message Handling)
> - `/reference/orders-v2` (Execution Gateway API landing page — empty; no content beyond the title)
>
> This is the durable local mirror satisfying
> `plans/active/venue_websocket_resilience_and_error_code_mapping_2026_08_21.md`'s Versifi `[OPERATOR]` P2 todo
> ("supply a doc link or credentialed access") — a saved mirror IS credentialed access, permanently, so no future
> session needs to re-scrape or re-authenticate.

---

## 1. Introduction

At VersiFi, the platform is a high-throughput, low-latency trading gateway for algorithmic execution on digital
asset exchanges — execution algorithms with short-term alphas/predictive signals trained via ML to minimize
adverse selection, slippage, and market impact.

Two access modes:

- **REST** — comprehensive historical data / order management via RESTful APIs.
- **WebSocket** — instantaneous real-time data streaming (order status/fills).

### Algorithms offered

- **TWAP** (Time-Weighted Average Price) — splits a large order into equal portions executed at regular
  intervals. Params: time interval, total duration, order size, aggressiveness.
- **VWAP** (Volume-Weighted Average Price) — executes in proportion to traded volume. Params: order size,
  execution window, aggressiveness.
- **IS** (Implementation Shortfall) — minimizes slippage vs. decision-time price via aggressive front-loading.
  Params: order size, urgency level, max participation rate, aggressiveness.
- **Basis Trade** (pair order) — simultaneous long-spot / short-future(perp) to capture spot/futures spread
  convergence. Params: volume cap, order size, execution window, aggressiveness.

---

## 2. Authentication

> `https://docs.versifi.io/reference/authentication`

All REST requests require a unique per-user API key. VersiFi's team provisions the key out-of-band.

- **Header (REST, every request except WebSocket)**: `x-api-key` — request refused (unspecified status, presumably 401) if missing/invalid.
- **Headers actually used on order endpoints** (per every endpoint page crawled): `X-VERSIFI-API-KEY` +
  `X-VERSIFI-API-SIGN`, both `required`.
- **Signature**: HMAC-SHA256 over a payload string, hex-digest.
  - `GET`/`DELETE`: payload = the URL-encoded query string, without the leading `?`.
  - `POST`/`PUT`: payload = the raw request body as a string.
  - Go: `hmac.New(sha256.New, []byte(apiSecret)); h.Write([]byte(payload)); hex.EncodeToString(h.Sum(nil))`
  - Python: `hmac.new(api_secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()`

No mention of a signature-expiry window, key-rotation cadence, or refresh mechanism for REST auth — the API key
itself is treated as long-lived (no keepalive/refresh call documented).

---

## 3. WebSocket — Overview

> `https://docs.versifi.io/reference/an-overview-of-websocket`

Full-duplex, single-TCP-connection protocol used for real-time order-status streaming after a REST-placed order
(clients track fills/status via the order's unique `order_id`).

### Topics

- **`execution_report`** — all status updates (executions, modifications, cancellations) for orders placed by the
  authenticated user. This is the only currently-active topic.
- **`analytics`** — **not implemented**. Planned for pre-/post-trade Transaction Cost Analysis (TCA).

### REST vs. WebSocket guidance (VersiFi's own framing)

- REST: point-in-time, audit/compliance/detailed-snapshot queries (e.g. "Get Order by ID").
- WebSocket: real-time order-status streaming, essential for high-frequency/real-time monitoring.
- The two are used complementarily, not as alternatives to each other.

---

## 4. WebSocket — Connection & Message Handling

> `https://docs.versifi.io/reference/get_v1-ws-3`

### Connection URL

Docs page and Overview table both cite a **placeholder** endpoint (`wss://example.com/v1/wss` /
`https://example.com/v1/ws`) explicitly flagged: _"This URL will be updated as it currently points to a DEV
environment."_ **No production `wss://` host is published in these docs as of this retrieval** — the real
production WS base URL was not discoverable via this crawl (honest absence; needs an operator/Versifi-team ask if
a specific production host is required downstream).

### Subscription topics table (as published)

| Subscription       | Connection URL (placeholder) | Comments                                     |
| ------------------ | ---------------------------- | -------------------------------------------- |
| `execution_report` | `wss://example.com/v1/wss`   | dev-environment placeholder, will be updated |
| `analytics`        | `wss://example.com/v1/wss`   | dev-environment placeholder, will be updated |

### Auth (WebSocket)

Must authenticate before subscribing. Client sends an `auth` op message over the open connection (this is a
per-connection application-level handshake, not a REST call):

- **Request**: `{"op": "auth", "args": [api_key, expires, signature]}`
- **Response**: `{"op": "auth", "success": true, "message": {"status": "ok"}}`
- `expires`: expiration timestamp for the auth token (client-supplied, part of the signed payload — not a
  server-dictated refresh interval).
- `signature`: HMAC-SHA256 of `payload := fmt.Sprintf("GET/realtime%d", int64(expires))`, using the same
  key-to-bytes + HMAC-SHA256 recipe as REST auth (`api_secret.encode('utf-8')` → `hmac.new(..., sha256)`).

No documented re-auth/refresh cadence beyond "the client picks its own `expires`" — there is no
listen-key-keepalive or JWT-reissue mechanism published; the auth message itself is the whole mechanism, and its
lifetime is client-chosen via `expires`.

### Subscribe

- **Request**: `{"op": "subscribe", "args": [topic]}`
- **Response**: `{"op": "subscribe", "message": "OK", "success": true}`
- Only `execution_report` is documented as currently available to subscribe to.

### Ping / Pong

- **Request**: `{"op": "ping"}`
- **Response**: `{"op": "ping", "message": <object>, "success": true}`
- This is an **application-level, client-initiated** ping/pong pair (a message op, not a websocket protocol-level
  ping frame). **No cadence/interval is published**, no pong-deadline is published, and no venue-forced
  disconnect window is published. Left `None` in the registry rather than guessed.

### Message reception — `execution_report` envelope

Every execution_report message shares the outer envelope `{"message": {...order-detail-shaped object...}, "op":
"execution_report", "success": true}`. The `message` field carries the **same schema as "Get Order by ID"**, with
extra fill-only fields nested in `child_order.trades[]` entries: `cummulative_filled_quantity`, `average_price`,
`executed_price`, `executed_quantity`.

Order-type-specific fill/cancel message shapes (Basic / Pair / Algo) were captured verbatim; all three nest a
`reject_reason: string` field at the order level (see §6 below) and at points inside `child_order`/leg objects.
A **canceled** order's message uses the identical schema with `"status": "CANCELED"`.

### Gap-recovery / resubscribe semantics — NOT documented

No sequence-number, update-id, or checksum field is published anywhere on this page (or any other page crawled)
for detecting a dropped `execution_report` message. No `resubscribe_after_reconnect` behavior (auto-restore vs.
explicit re-subscribe vs. snapshot-then-delta) is documented — a reconnecting client is only shown the same
subscribe/auth handshake used on first connect, with no stated guarantee about buffered/missed messages during a
disconnect window. Left `None`/absent in the registry rather than guessed.

### Duplicate-subscription / max-subscriptions / connection caps — NOT documented

No published limit on subscriptions per connection, connections per IP/key, or a message-rate cap on the
WebSocket transport specifically. Left `None`.

---

## 5. REST — Execution Management (order creation)

All three creation endpoints (`Create Basic Order`, `Create Algo Order`, `Create Pair Order`) require headers
`X-VERSIFI-API-KEY` + `X-VERSIFI-API-SIGN` and share the same `exchange` enum:

> **`exchange` allowed values (confirmed identically on all 3 creation-endpoint pages): `BINANCE_SPOT`,
> `BINANCE_FUTURES`, `OKX_SPOT`, `OKX_FUTURES`, `BINANCE_UNIFIED`.**
>
> **No `BYBIT*` or `DERIBIT*` value appears anywhere in the crawled docs** — every endpoint's exchange enum,
> every JSON example (`"exchange": "BINANCE"` in fill examples), and the schemas.py module docstring already in
> this repo agree: VersiFi's current live API routes only to Binance and OKX (spot + futures + the unified
> account variant). See "Integration notes" §9 below — this contradicts the operator's 2026-03-05 Telegram
> framing ("Binance/OKX/Bybit/Deribit"), which this mirror could not corroborate against the live docs.

### `POST /v2/orders/basic/` — Create Basic Order

- MARKET / LIMIT / STOP_LOSS / STOP_LOSS_LIMIT / TAKE_PROFIT / TAKE_PROFIT_LIMIT (non-algo order types; also
  accepts TWAP/VWAP/IS values but without algo params per the schema doc).
- Body: `client_order_id?`, `exchange` (enum, required), `order_type` (enum, required), `price?`, `quantity`
  (required), `quote_order_quantity?`, `side` (enum BUY/SELL, required), `start_time?` (UTC epoch microseconds),
  `stop_price?`, `symbol` (required, format `{Asset}/{Currency}`), `tif?` (enum, defaults GTC), `trailing_delta?`.
- **201 Created** response: `{client_order_id, order_id, status}`.
- **Error responses documented**: `400 Bad Request`, `401 Unauthorized`, `404 Not Found`, `409 Conflict`,
  `500 Internal Server Error`. The one expanded example body (401 page) is `{"code": 400, "message": "status bad
request"}` — confirms the malformed-message error-tier response shape is `{"code": <int>, "message": <string>}`.
  **No `transaction_id`/correlation-id field appears in any documented error response body** on this or any other
  crawled page — honest absence (the operator's "transaction id" framing was not corroborated by the live docs;
  it may exist as a response header not rendered by ReadMe.com's schema view, or the operator may be describing a
  different mechanism — flagged, not asserted).

### `POST /v2/orders/algo/` — Create Algo Order

- `order_type` enum: `TWAP`, `VWAP`, `IS` only (narrower than Basic's type list).
- Body: `client_order_id?`, `exchange` (same enum), `order_type` (required), `params?` (algo config — duration
  required for IS), `quantity` (required), `quote_order_quantity?`, `side` (required), `symbol` (required).
- **201 Created**: `{client_order_id, lead: {leg_id, status}, order_id, secondary: {leg_id, status}, status}`.
- Error responses: `400`, `401`, `404`, `409`, `500` (adds 409 vs. Basic Order's set).

### `POST /v2/orders/pair/` — Create Pair Order (Basis Algo)

- `lead` object (required): `order_type` enum `BASIS` only, `params` (spread thresholds, legging strategy,
  drawdown/slippage caps, position/notional limits), `style` enum `SYNC`/`ASYNC`/`TWAP` (SYNC = both legs
  aggressive; ASYNC = first leg passive then aggressive on fill; TWAP = each leg independently TWAP-executed).
- `secondary` object mirrors `lead`.
- **201 Created**: same shape as Algo Order's response.
- Error responses: `400`, `401`, `404`, `409`, `500`.

---

## 6. REST — Order Management

### `DELETE /v2/orders/{id}` — Cancel order request

- Path param `id` (integer, required).
- **204 No Content** on accept; the actual cancel confirmation arrives over WebSocket (`execution_report`,
  `status: CANCELED`), not synchronously in the REST response.
- Error responses: `400`, `401`, `404`, `500` (no 409 on this endpoint).

### `DELETE /v2/orders/batch` — Cancel Batch order request

- Body: `ids: array of integers` (order IDs to cancel).
- **204 No Content**; error responses `400`, `401`, `404`, `500`.

### `GET /v2/orders/{id}` — Get Order by ID

- Returns the full order detail: `algo_order` / `basic_order` / `pair_order` (exactly one populated, matching
  `request_order_type`), `client_order_id`, `order` (raw sub-object, one of Basic/Pair/AlgoResponseV2),
  `order_id`, `reject_reason`, `request_order_type`, `status`, `timestamp` (Unix epoch **seconds**).
- **`reject_reason: string`** appears at the top level AND nested inside every `child_orders[]` entry — confirming
  the operator's claim that reject_reason is carried per-order and per-child-order (i.e. per exchange leg/fill
  attempt), available via this REST endpoint.
- Error responses: `400`, `401`, `404`, `500`.

### `GET /api/v2/orders` — Get orders with filters

- Query params: `limit` (1–1000, default 100), `offset` (≥0, default 0), `side` (enum), `symbol`, `timestamp_since`,
  `timestamp_until` (Unix timestamps). **Paginated list, no rate-limit or throttling info published on this
  page or anywhere else crawled** (honest absence — the operator's "500 transactions/second" figure is NOT
  corroborated by these docs; recorded per the operator's Telegram citation only, see §9).
- **200** response: array of order objects, each carrying `client_api_key`, `client_id`, `client_order_id`,
  `order_id`, `reject_reason`, `request_order_type`, `status`, `timestamp`, plus the same
  `algo_order`/`basic_order`/`pair_order` nesting as "Get Order by ID".
- Error responses: `400`, `401`, `500` (no 404/409 on this endpoint — it's a filter query, not a resource lookup).

---

## 7. Error-response shape observed across all endpoints

Every REST endpoint crawled documents the same coarse status-code set for the **malformed-message tier**:
`400 Bad Request`, `401 Unauthorized`, `404 Not Found` (creation/lookup/delete-by-id endpoints only),
`409 Conflict` (creation endpoints only — likely duplicate `client_order_id`), `500 Internal Server Error`. The
one expanded response-body schema seen (on Create Basic Order's `401` panel) is a flat `{code: integer, message:
string}` object — no venue-specific error taxonomy, no documented per-code enum beyond the HTTP status itself.

This matches the operator's framing: VersiFi does **not** publish its own malformed-request error-code table
beyond standard HTTP status codes — there is nothing venue-specific to transcribe into a VersiFi-owned code table
for this tier, only the HTTP status layer itself.

The **processing-time tier** (`reject_reason`) is a `string` field on every order/child-order object (§6), present
identically whether read via REST (`Get Order by ID`, `Get orders with filters`) or delivered over WebSocket
(`execution_report`, §4) — this mirror corroborates the operator's claim that the field is the same one surface
regardless of transport.

**What this mirror could NOT corroborate about `reject_reason`'s content**: the docs never show a _populated_
`reject_reason` example (every JSON example has `reject_reason` either absent or implicitly null) — so the claim
that its value is _verbatim_ the underlying exchange's own raw error JSON (not reformatted by VersiFi) is **not
independently confirmed by these docs**; it rests entirely on the operator's 2026-03-05 Telegram exchange with
Sandeep Rawal (VersiFi), cited as such in the registry entries below and already reflected in this repo's existing
`unified_api_contracts/external/versifi/schemas.py` (`parse_reject_reason` / `VersiFiRejectReason`, landed prior to
this session — see §9).

---

## 8. Rate limits

**Not documented anywhere in the crawled docs** — no rate-limits page exists in the sidebar nav, and no endpoint
page mentions a request-per-second cap, `Retry-After` header, or `429` status. The **500 transactions/second**
figure used in the registry (`incoming_message_rate_limit_per_second`) is sourced **exclusively** from the
operator's 2026-03-05 Telegram exchange with Sandeep Rawal (VersiFi's team, confirmed as sufficient throughput
alongside standard exchange + HTTP error codes) — not from these docs. Recorded with that citation, not a
doc-page citation.

---

## 9. Integration notes (for the UAC registry + reject_reason discriminator)

**Finding — the `reject_reason` compound-type discriminator already exists in this repo**, landed in a prior
session, at `unified_api_contracts/external/versifi/schemas.py`:

```python
VersiFiRejectReason = BinanceError | OKXError

def parse_reject_reason(raw: str | None) -> VersiFiRejectReason | None:
    ...  # int-shaped code -> BinanceError; else -> OKXError
```

...plus `resolve_versifi_reject_reason()` in `unified_api_contracts/external/versifi/normalize.py` (returns the
resolved `.msg`) and `normalize_versifi_error()` (HTTP-status → `CanonicalError` via `from_http_status`, i.e. the
malformed-message tier). **This mirror's exchange-enum finding (§5 — only Binance/OKX, no Bybit/Deribit) matches
the existing `BinanceError | OKXError` union exactly** — there is currently no evidence in VersiFi's own docs that
a Bybit- or Deribit-shaped `reject_reason` would ever be returned, since VersiFi's `exchange` request field has no
enum value routing to either venue. **Recommendation: do not extend the union to Bybit/Deribit speculatively** —
if VersiFi's `exchange` enum ever grows those values, extend `VersiFiRejectReason` and `parse_reject_reason`'s
discriminator at that time, keyed off whatever shape their raw error JSON actually takes (this mirror cannot
predict it).

**What still needs registry population** (this session, in `unified_api_contracts/registry/capability_declarations/
_defi.py`'s `_DEFI_WS_PROTOCOLS["versifi"]` — note: the live entry is in `_defi.py`, NOT `_cefi.py`; VersiFi is
declared as a `DEFI_CAPABILITIES` `SourceCapability` in this repo despite wrapping CeFi venues, apparently because
of how it was originally onboarded — flagging this location as a discrepancy vs. this task's brief, which named
`_cefi.py`):

- `ping_initiator="client"` (client sends `{"op":"ping"}` first) — confirmed, §4.
- `ping_interval_seconds`, `pong_deadline_seconds`, `max_connection_lifetime_seconds`: **None** — not published.
- `auth_refresh_mechanism`: best-fit is `"none"` in the sense that there's no keepalive call, but the mechanism
  is actually "client picks its own `expires` in the auth message" — recorded as a note rather than forcing it
  into one of the existing enum values, since none of `listen_key_keepalive`/`jwt_reissue`/`login_message` is an
  exact match (closest is `login_message`, used here since auth rides a one-time op message like Bybit/OKX's
  `login_message` mechanism).
- `incoming_message_rate_limit_per_second=500` — operator-Telegram citation only (§8), not doc-confirmed.
- `max_subscriptions_per_connection`, `max_connections_per_ip`, `connection_window_seconds`,
  `duplicate_subscription_allowed`, `resubscribe_after_reconnect`, `sequence_gap_detection`: **None** — not
  published anywhere in this crawl (§4).
- `rest_gap_backfill`: `{"orders": "GET /v2/orders/{id}"}` — the only REST read endpoint that could backfill a
  missed `execution_report` (there is no orderbook/trades/candles surface on this venue at all; it is an
  execution-only gateway).
- `doc_url`: this mirror file's path (the live site is password-gated) —
  `unified-trading-pm/codex/02-venues/versifi-api-docs-mirror-2026-08-22.md`.
- `doc_retrieved`: 2026-08-22.

**Errors registry** (`unified_api_contracts/canonical/crosscutting/errors/cefi.py`'s `VENUE_ERRORS_CEFI["versifi"]`):
add HTTP-status-tier entries only (400/401/404/409/500, per `ve()` pattern used by other venues for their generic
HTTP layer) with a docstring/comment stating the processing-tier (`reject_reason`) is NOT a separate
VersiFi code table — callers must resolve `reject_reason` via `parse_reject_reason()` (or
`resolve_versifi_reject_reason()`) first, then call `classify_venue_error(<binance|okx>, <resolved code>)` against
the _underlying_ exchange's own table, never `classify_venue_error("versifi", ...)` for that tier.
