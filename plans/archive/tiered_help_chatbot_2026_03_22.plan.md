---

name: tiered_help_chatbot overview: > Add a tiered AI help chatbot to the Unified Trading System. Three auth-gated tiers
(public, external client, internal) each get a different knowledge scope and system prompt. Backend lives in
unified-trading-api as a new /chat router. Frontend is a persistent floating chat widget in unified-trading-system-ui,
visible on every page, minimisable. Uses Anthropic Claude API with SSE streaming. type: feature status: active priority:
P1 locked_by: live-defi-rollout locked_since: 2026-03-22

repos_modified:

- unified-trading-api
- unified-trading-system-ui
- unified-trading-pm

completion_gates: code: - C0: ruff clean on both repos - C1: basedpyright clean on unified-trading-api - C2: TypeScript
strict clean on unified-trading-system-ui - C3: unit tests pass for chat router - C4: UI component renders in all 3
tiers (public, client, internal) deployment: - D1: mock mode works locally (no API key needed for UI rendering) - D2:
real mode works with ANTHROPIC_API_KEY in Secret Manager business: - B1: public users get general answers, refused on
client-specific questions - B2: external clients can ask about their portfolio and UI navigation - B3: internal users
can ask about backend ops, runbooks, compliance

repo_gates: unified-trading-api: C3 unified-trading-system-ui: C2

todos:

- title: "Phase 1: Backend — Chat Router in unified-trading-api" items:
  - [x] [AGENT] P0. Add `anthropic` SDK to unified-trading-api pyproject.toml dependencies
  - [x] [AGENT] P0. Create `unified_trading_api/routes/chat.py` with POST /chat/message endpoint
  - [x] [AGENT] P0. Implement 3-tier system prompt selection based on EntitlementContext
  - [x] [AGENT] P0. Add SSE streaming response via StreamingResponse
  - [x] [AGENT] P0. Wire chat router into main.py create_app()
  - [x] [AGENT] P1. Add mock mode fallback (echo responses when no API key)
  - [ ] [AGENT] P2. Add unit tests for chat router (tier gating, prompt selection)

- title: "Phase 2: Frontend — Chat Widget in unified-trading-system-ui" items:
  - [x] [AGENT] P0. Create `/components/chat/chat-widget.tsx` — floating button + expandable panel
  - [x] [AGENT] P0. Create `/components/chat/chat-messages.tsx` — message list with streaming
  - [x] [AGENT] P0. Create `/components/chat/chat-input.tsx` — input with send button
  - [x] [AGENT] P0. Create `/hooks/api/use-chat.ts` — API hook for SSE streaming
  - [x] [AGENT] P0. Wire into UnifiedShell (authenticated pages) with auth context
  - [x] [AGENT] P0. Wire into public layout with public tier
  - [x] [AGENT] P1. Add Cmd+? keyboard shortcut to toggle chat
  - [x] [AGENT] P2. Add conversation history persistence (localStorage)

- title: "Phase 3: Knowledge & Content" items:
  - [ ] [HUMAN] P1. Curate public-tier knowledge doc (service descriptions, glossary)
  - [ ] [HUMAN] P1. Curate client-tier knowledge doc (UI navigation, feature guides)
  - [ ] [HUMAN] P1. Curate internal-tier knowledge doc (runbooks, compliance, backend ops)
  - [ ] [AGENT] P2. Version-tag knowledge from PM manifest at startup

notes: |

## Architecture

```
┌─────────────────────────────────┐
│  unified-trading-system-ui      │
│  ┌───────────────────────────┐  │
│  │  ChatWidget (all pages)   │  │
│  │  - floating bottom-right  │  │
│  │  - minimise/expand        │  │
│  │  - SSE streaming display  │  │
│  └──────────┬────────────────┘  │
└─────────────┼───────────────────┘
              │ POST /api/chat/message (SSE)
┌─────────────▼───────────────────┐
│  unified-trading-api :8030      │
│  ├─ auth middleware (existing)  │
│  ├─ entitlement context         │
│  └─ /chat router (NEW)         │
│     ├─ select system prompt     │
│     │  by org_type/tier         │
│     ├─ assemble context         │
│     └─ stream from Claude API   │
└─────────────┬───────────────────┘
              │
      ┌───────▼───────┐
      │  Anthropic API │
      │  (Claude)      │
      └───────────────┘
```

## Three Tiers

| Tier     | Auth               | System Prompt Scope                                  | Example Questions                   |
| -------- | ------------------ | ---------------------------------------------------- | ----------------------------------- |
| PUBLIC   | None               | General service descriptions, glossary, capabilities | "What is backtesting as a service?" |
| CLIENT   | JWT (external org) | + UI navigation, portfolio context, feature docs     | "How do I view my P&L breakdown?"   |
| INTERNAL | JWT (internal org) | + Backend ops, runbooks, compliance, architecture    | "How do we handle FCA reporting?"   |

## Key Design Decisions

1. **No RAG for v1** — Claude's context window is large enough to stuff curated docs. RAG can be added later when
   knowledge base exceeds context limits.
2. **SSE not WebSocket** — simpler, works through Next.js API rewrites, no persistent connection needed.
3. **Added to unified-trading-api** — not a new repo. Follows system-first architecture.
4. **Mock mode** — returns echo responses when ANTHROPIC_API_KEY is not set, so UI dev works without keys.
5. **Chat widget in UnifiedShell** — appears on every authenticated page. Also in public layout for tier 0.
