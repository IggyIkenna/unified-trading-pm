# Complete GitHub Project Structure

## Overview

**15+ GitHub Projects** organized by function, each with specific labels, filters, and automation rules.

---

## 1. Cross-Cutting Projects

### 🔄 CODs (Change of Direction) - Project #3

**Purpose:** Architectural pivots and design changes tracked separately from feature work

**Type:** Flat issue list

**Label:** `cod` (appears across ALL other projects)

**Filter:** `label:cod`

**Automation:**

- Auto-add: When `cod` label is added to any issue
- Auto-status: When issue closed → Move to 'Done'
- Auto-archive: After 30 days closed → Archive

**Repos:** All 30 repos

**Current Status:** ✅ Complete (648 CODs organized)

---

### 🐛 Bugs & Issues - Project #NEW

**Purpose:** Production failures requiring immediate attention

**Type:** Flat issue list

**Label:** `bug`

**Filter:** `label:bug is:open`

**Priority Levels:**

- P0: Blocking (prod broken)
- P1: Critical (user-facing)
- P2: Important (degraded performance)

**Automation:**

- Auto-add: When `bug` label is added
- Auto-priority: Based on severity label
- Auto-notify: Slack/email on P0/P1

**Repos:** All 30 repos

**Current Status:** ❌ To Create

---

## 2. Core Trading Projects

### 💹 Execution Services - Project #NEW

**Purpose:** Live trading execution + backtest + UI

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `execution`, `epic`, `task`, `subtask`

**Filter:** `repo:execution-service -label:cod`

**Structure:**

- **Epics:** Major features (e.g., "Multi-venue routing")
- **Tasks:** Implementation steps (e.g., "Add dYdX connector")
- **Subtasks:** Specific work items (e.g., "Implement order validation")

**Repos:**

- `execution-service` (main)

**Views:**

- Work Items (filter: `-label:cod`)
- Epics Only (filter: `label:epic -label:cod`)
- In Progress (filter: `status:in-progress -label:cod`)

**Current Status:** ❌ To Create

---

### 📈 Strategy Services - Project #NEW

**Purpose:** Strategy logic + backtest + UI + analytics

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `strategy`, `epic`, `task`, `subtask`

**Filter:** `repo:strategy-service -label:cod`

**Sub-Projects:**

- Strategy logic implementation
- **Strategy backtest engine**
- **Strategy backtest UI**
- Analytics dashboard

**Repos:**

- `strategy-service` (main)

**Current Status:** ❌ To Create

---

### ⚖️ Position Monitoring & Risk - Project #NEW

**Purpose:** Real-time P&L, risk limits, alert system

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `risk`, `epic`, `task`, `subtask`

**Filter:** `repo:position-monitoring,risk-service -label:cod`

**Features:**

- Real-time position tracking
- Risk limit monitoring
- P&L calculation
- Alert system (Slack, email)
- Drawdown tracking

**Repos:**

- `position-monitoring` (to create)
- `risk-service` (to create)

**Current Status:** ❌ To Create

---

## 3. Data Pipeline Projects

### 📊 Market Data Pipeline - Project #NEW

**Purpose:** Tick ingestion, processing, storage

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `market-data`, `epic`, `task`, `subtask`

**Filter:** `repo:market-tick-data-handler,market-data-processing-service -label:cod`

**Sub-Projects:**

- Tick data ingestion (WebSocket)
- Data processing (aggregation)
- GCS storage management
- Historical data queries

**Repos:**

- `market-tick-data-handler`
- `market-data-processing-service`

**Current Status:** ❌ To Create

---

### 🔬 Features Engineering - Project #NEW

**Purpose:** Feature calculation services

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `features`, `epic`, `task`, `subtask`

**Filter:** `repo:features-* -label:cod`

**Sub-Projects:**

- Calendar features (economic events)
- Delta-one features (futures basis)
- Onchain features (blockchain data)
- Volatility features (realized, implied)

**Repos:**

- `features-calendar-service`
- `features-delta-one-service`
- `features-onchain-service`
- `features-volatility-service`

**Current Status:** ❌ To Create

---

## 4. Machine Learning Projects

### 🤖 ML Training Services - Project #NEW

**Purpose:** Model training, hyperparameter tuning, experiment tracking

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `ml-training`, `epic`, `task`, `subtask`

**Filter:** `repo:ml-training-service -label:cod`

**Features:**

- Training pipeline
- Hyperparameter optimization
- Experiment tracking (Vertex AI)
- Model versioning

**Repos:**

- `ml-training-service`

**Current Status:** ❌ To Create

---

### 🧠 ML Inference Services - Project #NEW

**Purpose:** Real-time prediction, batch inference, model monitoring

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `ml-inference`, `epic`, `task`, `subtask`

**Filter:** `repo:ml-inference-service -label:cod`

**Features:**

- Real-time inference API
- Batch inference jobs
- Model monitoring
- A/B testing

**Repos:**

- `ml-inference-service`

**Current Status:** ❌ To Create

---

### 📈 ML Deployment Analytics - Project #NEW

**Purpose:** Model performance tracking, drift detection

**Type:** Flat issue list (analytics queries)

**Labels:** `ml-analytics`

**Filter:** `label:ml-analytics`

**Features:**

- Model performance metrics
- Drift detection
- A/B test analysis
- Feature importance tracking

**Repos:**

- `ml-inference-service` (queries)
- BigQuery datasets

**Current Status:** ❌ To Create

---

## 5. Operations Projects

### 🏦 Settlement & Reconciliation - Project #NEW

**Purpose:** Trade settlement, accounting integration, audit trail

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `settlement`, `epic`, `task`, `subtask`

**Filter:** `repo:settlement-service -label:cod`

**Features:**

- Trade settlement workflow
- Accounting system integration
- Reconciliation reports
- Audit trail

**Repos:**

- `settlement-service` (to create)

**Current Status:** ❌ To Create

---

### 📋 Client Reporting - Project #NEW

**Purpose:** Performance reports, analytics dashboards, custom queries

**Type:** Flat issue list (report requests)

**Labels:** `reporting`

**Filter:** `label:reporting`

**Features:**

- Performance reports (PDF, HTML)
- Analytics dashboards (Looker/Tableau)
- Custom query interface
- API for third-party tools

**Repos:**

- `client-reporting-api` (to create)

**Current Status:** ❌ To Create

---

### ⚙️ Infrastructure & Tooling - Project #NEW

**Purpose:** Cloud services, deployment automation, monitoring

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `infrastructure`, `epic`, `task`, `subtask`

**Filter:** `repo:unified-trading-services,unified-trading-deployment-v2 -label:cod`

**Sub-Projects:**

- Cloud services (GCS, BigQuery, Secret Manager)
- Deployment automation (Cloud Build, Cloud Run)
- Monitoring & alerting
- Developer tooling

**Repos:**

- `unified-trading-services`
- `unified-trading-deployment-v2`

**Current Status:** ❌ To Create

---

## 6. Documentation Projects

### 📚 Unified Trading Codex - Project #1

**Purpose:** Architecture docs, standards, checklists

**Type:** Flat issue list (documentation tasks)

**Labels:** `codex`, `documentation`

**Filter:** `repo:unified-trading-codex -label:cod`

**Features:**

- Architecture documentation (04-architecture/)
- Coding standards (06-coding-standards/)
- Checklists (10-audit/)
- Observability specs (03-observability/)

**Repos:**

- `unified-trading-codex`

**Current Status:** ✅ Exists (needs clean filter view)

---

## 7. Backtest-Specific Projects (NEW)

### 🔬 Execution Backtest & UI - Project #NEW

**Purpose:** Backtest execution strategies on historical data

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `execution-backtest`, `epic`, `task`, `subtask`

**Filter:** `repo:execution-service label:backtest -label:cod`

**Features:**

- **Execution backtest engine:** Replay historical orders
- **Execution backtest UI:** Visualize fill prices, slippage, timing
- **Performance metrics:** Fill rate, slippage, latency
- **Comparison reports:** Strategy A vs B

**Repos:**

- `execution-service` (backtest module)

**Current Status:** ❌ To Create

---

### 📊 Strategy Backtest & UI - Project #NEW

**Purpose:** Backtest trading strategies on historical data

**Type:** Epic → Task → Subtask hierarchy

**Labels:** `strategy-backtest`, `epic`, `task`, `subtask`

**Filter:** `repo:strategy-service label:backtest -label:cod`

**Features:**

- **Strategy backtest engine:** Simulate trading strategies
- **Strategy backtest UI:** Visualize trades, P&L, drawdowns
- **Performance metrics:** Sharpe, Sortino, max drawdown
- **Optimization:** Parameter sweeps, walk-forward analysis

**Repos:**

- `strategy-service` (backtest module)

**Current Status:** ❌ To Create

---

## Summary Table

| #   | Project Name                | Type      | Status      | Repos                                                    |
| --- | --------------------------- | --------- | ----------- | -------------------------------------------------------- |
| 1   | Unified Trading Codex       | Flat      | ✅ Exists   | unified-trading-codex                                    |
| 2   | (Untitled)                  | -         | ❌ Delete   | -                                                        |
| 3   | CODs                        | Flat      | ✅ Complete | All repos (label:cod)                                    |
| 4   | Bugs & Issues               | Flat      | ❌ Create   | All repos (label:bug)                                    |
| 5   | Execution Services          | Hierarchy | ❌ Create   | execution-service                                       |
| 6   | Strategy Services           | Hierarchy | ❌ Create   | strategy-service                                         |
| 7   | Position Monitoring & Risk  | Hierarchy | ❌ Create   | position-monitoring, risk-service                        |
| 8   | Market Data Pipeline        | Hierarchy | ❌ Create   | market-tick-data-handler, market-data-processing-service |
| 9   | Features Engineering        | Hierarchy | ❌ Create   | features-\* (4 repos)                                    |
| 10  | ML Training Services        | Hierarchy | ❌ Create   | ml-training-service                                      |
| 11  | ML Inference Services       | Hierarchy | ❌ Create   | ml-inference-service                                     |
| 12  | ML Deployment Analytics     | Flat      | ❌ Create   | ml-inference-service (analytics)                         |
| 13  | Settlement & Reconciliation | Hierarchy | ❌ Create   | settlement-service                                       |
| 14  | Client Reporting            | Flat      | ❌ Create   | client-reporting-api                                 |
| 15  | Infrastructure & Tooling    | Hierarchy | ❌ Create   | unified-trading-services, unified-trading-deployment-v2  |
| 16  | Execution Backtest & UI     | Hierarchy | ❌ Create   | execution-service (backtest module)                     |
| 17  | Strategy Backtest & UI      | Hierarchy | ❌ Create   | strategy-service (backtest module)                       |

**Total:** 17 projects (2 exist, 15 to create)

---

## Automation Script

✅ **Script created:** `create-all-projects.py`

To create all 15 missing projects with correct labels, filters, and views:

```bash
cd unified-trading-codex/11-project-management/github-integration

# Dry run first (preview)
python create-all-projects.py --org IggyIkenna --dry-run

# Apply changes
python create-all-projects.py --org IggyIkenna --apply

# Or use helper script
bash manage-cods.sh create-all-projects
```

This script will:

1. ✅ Create all 15 missing projects (~45 seconds)
2. ✅ Set up labels for each project (~30 labels total)
3. 📝 Generate manual setup guides (workflows + views) - `/tmp/project-{number}-manual-setup.md`
4. ✅ Idempotent (safe to re-run)
5. ✅ Error handling & rollback

### What's Automated (95%)

- Project creation via `gh` CLI
- Label creation in target repos
- Batch operations with rate limiting

### What's Manual (5%) - ~75 minutes total

Due to GitHub API limitations:

- **Automation workflows:** 3 rules per project (auto-add, auto-status, auto-archive)
- **Filtered views:** 2-3 views per project (Work Items, Epics, In Progress)

Each project gets a detailed manual setup guide: `/tmp/project-{number}-manual-setup.md`

### Documentation

See `CREATE_ALL_PROJECTS.md` for:

- Detailed usage instructions
- Error handling & troubleshooting
- Project definitions (all 15)
- Performance metrics
- Success criteria

---

## Next Steps

1. ✅ **Script created:** `create-all-projects.py`
2. **Run dry-run:** Preview what will be created (~5 seconds)
3. **Apply changes:** Create all 15 projects (~45 seconds)
4. **Manual setup:** Follow guides in `/tmp/` (~5 min per project = 75 min total)
5. **Verify:** Create test issues with labels, check project population

Once set up, all projects will auto-populate via GitHub workflows based on labels!
