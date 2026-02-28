# Complete Repository Inventory

## Services (14 Python services requiring CLI standardization)

### Data Pipeline Services (4)
1. **instruments-service** - Operations: `instrument`, `corporate_actions` | Modes: batch, live
2. **market-tick-data-handler** - Operations: `fetch` | Modes: batch, live
3. **market-data-processing-service** - Operations: `process` | Modes: batch, live
4. **pnl-attribution-service** - Operations: `compute` | Modes: batch, live

### Features Services (4)
5. **features-calendar-service** - Operations: `compute` | Modes: batch, live
6. **features-delta-one-service** - Operations: `compute` | Modes: batch, live
7. **features-volatility-service** - Operations: `compute` | Modes: batch, live
8. **features-onchain-service** - Operations: `compute` | Modes: batch, live

### ML Services (2)
9. **ml-training-service** - Operations: `train_phase1`, `train_phase2`, `train_phase3` | Modes: batch, live
10. **ml-inference-service** - Operations: `infer` | Modes: batch, live

### Trading Services (3)
11. **strategy-service** - Operations: `backtest`, `live_trade` | Modes: batch (backtest only), live (trade only)
12. **execution-services** - Operations: `execute` | Modes: live only (event-driven)
13. **risk-and-exposure-service** - Operations: `compute` | Modes: batch, live

### Monitoring Services (1)
14. **position-balance-monitor-service** - Operations: `monitor` | Modes: batch, live

---

## UI Repos (9 TypeScript/React - NO CLI standardization, different quality gates)

15. **backtest-ui** - Backtest visualization
16. **batch-audit-ui** - Batch job monitoring
17. **client-reporting-ui** - Client reports
18. **live-health-monitor-ui** - Live system health
19. **logs-dashboard-ui** - Log aggregation
20. **ml-deployment-ui** - ML model deployment
21. **onboarding-ui** - Client onboarding
22. **settlement-ui** - Settlement reconciliation
23. **trading-analytics-ui** - Trading analytics

---

## Platform Libraries (6 Python - NO CLI, library-only)

24. **unified-trading-services** (UCS) - Storage, error handling, performance monitoring
25. **unified-config-interface** (UCI) - Configuration management
26. **unified-events-interface** (UEI) - Event logging, observability
27. **unified-market-interface** (UMI) - Venue configs, market categories
28. **unified-trade-execution-interface** (UOI) - Order models, execution interfaces
29. **unified-domain-client** (UDS) - Domain clients (instruments, market data, etc.)

---

## Utility Repos (5 - NO CLI standardization)

30. **unified-trading-codex** - Documentation, standards, epics
31. **unified-trading-deployment-v3** - Deployment configs, scripts (Node.js)
32. **unified-trading-deployment-v3** - Next-gen deployment (Node.js)
33. **execution-algo-library** - Execution algorithms (Python library)
34. **alerting-system** - Alerting infrastructure

---

## Special Cases (2)

35. **sports-betting-services** - Sports betting integration (separate domain)
36. **one-time-scripts** - Ad-hoc scripts (no standardization needed)

---

## Summary

- **14 Python services** → CLI standardization (`--operation`, `--mode`), engine/adapters refactoring
- **9 UI repos** → NO CLI, TypeScript quality gates (tsc, ESLint), NO engine/adapters
- **6 platform libraries** → NO CLI, library-only, NO engine/adapters
- **5 utility repos** → NO CLI standardization (docs, deployment, scripts)
- **2 special cases** → Evaluate separately

**Total requiring CLI + structure refactoring**: 14 services
**Total in workspace**: 36 active repos (excluding archive, temp, data folders)
