# Clean Workflow Diagrams - GitHub Integration

## 1. The 5-Step Autonomous Workflow

```mermaid
flowchart LR
    subgraph Step1["1️⃣ AUTOMATED DETECTION"]
        DiffChecker["run-diff-checker.py<br/>Scans codebase for:<br/>• Import violations<br/>• Config issues<br/>• Missing tests<br/>• Code standards"]
        Output1["Detailed Issues<br/>✅ Success criteria<br/>✅ Time estimates<br/>✅ Test requirements"]

        DiffChecker --> Output1
    end

    subgraph Step2["2️⃣ GITHUB AUTO-ORGANIZATION"]
        PushIssues["Push to GitHub<br/>via API"]
        Workflows["GitHub Project Workflows<br/>Auto-organize by:<br/>• Labels (epic, task, cod)<br/>• Schemas<br/>• Priority"]
        Projects["Populate Projects<br/>✅ Right project<br/>✅ Right priority<br/>✅ Right status"]

        PushIssues --> Workflows --> Projects
    end

    subgraph Step3["3️⃣ AGENT DEPLOYMENT"]
        UI["Multi-Repo Agent UI<br/>https://multi-repo-agent-<br/>cldtjniqvq-ew.a.run.app/"]
        UserInput["User Input:<br/>• Select issue list<br/>• Choose model (Gemini, Claude)<br/>• Deploy locally or cloud"]
        Parallel["Parallel Agent Execution<br/>5-50 concurrent agents<br/>Cursor CLI or VM deployment"]

        UI --> UserInput --> Parallel
    end

    subgraph Step4["4️⃣ QUALITY GATES & OUTCOMES"]
        QualityGates["4-Phase Quality Gates<br/>1. Local auto-fix<br/>2. Local verify<br/>3. Pre-commit hooks<br/>4. CI/CD"]

        Success["4a: SUCCESS PATH<br/>✅ All gates pass<br/>✅ PR via quickmerge.sh<br/>✅ Auto-merge enabled"]
        Failure["4b: FAILURE PATH<br/>❌ Gates fail<br/>❌ Log to GCS/local<br/>❌ Create bug issue<br/>❌ Link to original"]

        QualityGates -->|Pass| Success
        QualityGates -->|Fail| Failure
    end

    subgraph Step5["5️⃣ CLOSURE OR RETRY"]
        AutoClose["Auto-Close<br/>'Fixes #XXX' in PR<br/>→ Issue closes on merge"]
        BugBlock["Bug Blocks Issue<br/>Cross-referenced<br/>Must fix bug first"]
        Retry["Retry Options:<br/>• Automatic (CODs, small tasks)<br/>• Human escalation (complex)<br/>• Better model if persist"]

        Success --> AutoClose
        Failure --> BugBlock --> Retry
        Retry --> Step3
    end

    Output1 --> PushIssues
    Projects --> UI

    style Step1 fill:#e3f2fd,stroke:#1976d2,stroke-width:3px
    style Step2 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:3px
    style Step3 fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    style Step4 fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    style Step5 fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    style Success fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
    style Failure fill:#ffcdd2,stroke:#c62828,stroke-width:3px
```

---

## 2. Complete Project Structure (15+ Projects)

```mermaid
graph TD
    subgraph CrossCutting["🔄 CROSS-CUTTING"]
        COD["CODs Project<br/>Change of Direction<br/>Architectural pivots<br/>Label: 'cod' across all projects"]
        Bugs["Bugs & Issues Project<br/>Production failures<br/>Immediate fixes required<br/>Label: 'bug'"]
    end

    subgraph CoreTrading["💹 CORE TRADING"]
        Exec["Execution Services<br/>• Live trading execution<br/>• Execution backtest<br/>• Execution backtest UI<br/>Label: 'execution'"]
        Strat["Strategy Services<br/>• Strategy logic<br/>• Strategy backtest<br/>• Strategy backtest UI<br/>• Analytics dashboard<br/>Label: 'strategy'"]
        Risk["Position Monitoring & Risk<br/>• Real-time P&L<br/>• Risk limits<br/>• Alert system<br/>Label: 'risk'"]
    end

    subgraph DataPipeline["📊 DATA PIPELINE"]
        Market["Market Data Pipeline<br/>• Tick ingestion<br/>• Processing<br/>• Storage (GCS)<br/>Label: 'market-data'"]
        Features["Features Engineering<br/>• Calendar features<br/>• Delta-one features<br/>• Onchain features<br/>• Volatility features<br/>Label: 'features'"]
    end

    subgraph ML["🤖 MACHINE LEARNING"]
        MLTrain["ML Training Services<br/>• Model training<br/>• Hyperparameter tuning<br/>• Experiment tracking<br/>Label: 'ml-training'"]
        MLInfer["ML Inference Services<br/>• Real-time prediction<br/>• Batch inference<br/>• Model monitoring<br/>Label: 'ml-inference'"]
        MLAnalytics["ML Deployment Analytics<br/>• Model performance<br/>• Drift detection<br/>• A/B testing<br/>Label: 'ml-analytics'"]
    end

    subgraph Operations["⚙️ OPERATIONS"]
        Settlement["Settlement & Reconciliation<br/>• Trade settlement<br/>• Accounting integration<br/>• Audit trail<br/>Label: 'settlement'"]
        Reporting["Client Reporting<br/>• Performance reports<br/>• Analytics dashboards<br/>• Custom queries<br/>Label: 'reporting'"]
        Infra["Infrastructure & Tooling<br/>• Cloud services<br/>• Deployment automation<br/>• Monitoring<br/>Label: 'infrastructure'"]
    end

    subgraph Documentation["📚 DOCUMENTATION"]
        Codex["Unified Trading Codex<br/>• Architecture docs<br/>• Standards<br/>• Checklists (100+ items)<br/>Label: 'codex'"]
    end

    COD -.->|"Cross-cutting label"| Exec
    COD -.->|"Cross-cutting label"| Strat
    COD -.->|"Cross-cutting label"| Market
    COD -.->|"Cross-cutting label"| Features
    COD -.->|"Cross-cutting label"| MLTrain

    style COD fill:#9966ff,stroke:#6b46c1,stroke-width:3px,color:#fff
    style Bugs fill:#ff6b6b,stroke:#c92a2a,stroke-width:3px,color:#fff
```

---

## 3. Project Type Structures

```mermaid
graph TD
    subgraph TypeA["PROJECT TYPE A: Epic Hierarchy"]
        Epic1["Epic: Improve Execution Performance<br/>Label: epic<br/>Status: In Progress"]
        Task1["Task: Optimize order routing<br/>Label: task<br/>Status: In Progress"]
        Task2["Task: Add latency monitoring<br/>Label: task<br/>Status: Todo"]
        Sub1["Subtask: Implement priority queue<br/>Label: subtask<br/>Status: In Progress"]
        Sub2["Subtask: Add unit tests<br/>Label: subtask<br/>Status: Done"]
        Sub3["Subtask: Update metrics<br/>Label: subtask<br/>Status: Todo"]

        Epic1 --> Task1
        Epic1 --> Task2
        Task1 --> Sub1
        Task1 --> Sub2
        Task2 --> Sub3
    end

    subgraph TypeB["PROJECT TYPE B: Flat Issue List"]
        Issue1["Issue: Fix auth timeout<br/>Label: bug<br/>Status: Open"]
        Issue2["Issue: Update API docs<br/>Label: documentation<br/>Status: Open"]
        Issue3["Issue: Add rate limiting<br/>Label: enhancement<br/>Status: Open"]
        Issue4["Issue: Refactor config<br/>Label: cod<br/>Status: Open"]
    end

    style Epic1 fill:#4a90e2,stroke:#2e5c8a,stroke-width:3px,color:#fff
    style Task1 fill:#7cb342,stroke:#558b2f,stroke-width:2px
    style Task2 fill:#7cb342,stroke:#558b2f,stroke-width:2px
    style Sub1 fill:#ffb74d,stroke:#f57c00,stroke-width:2px
    style Sub2 fill:#81c784,stroke:#388e3c,stroke-width:2px
    style Sub3 fill:#ffb74d,stroke:#f57c00,stroke-width:2px
```

---

## 4. The 9-Stage Maturity Progression

```mermaid
flowchart TD
    subgraph Complexity["INCREASING COMPLEXITY & CUSTOMIZATION"]
        direction LR
        Prescribed["PRESCRIBED<br/>PROMPTS"] --> Template["TEMPLATE-BASED<br/>GENERATION"] --> Interactive["INTERACTIVE<br/>ANALYSIS"] --> ClientFacing["CLIENT<br/>CUSTOMIZATION"]
    end

    subgraph Stage1_2["Stages 1-2: Foundation"]
        S1["Stage 1: COD Standards<br/>✅ COMPLETE<br/>Organize 651 CODs"]
        S2["Stage 2: File Size<br/>⏳ NEXT<br/>Enforce <1500 lines"]
        S1 --> S2
    end

    subgraph Stage3["Stage 3: Observability"]
        S3["Event Logging<br/>11 lifecycle events<br/>3-tier structure"]
    end

    subgraph Stage4_6["Stages 4-6: Production Ready"]
        S4["Stage 4: Feature Completeness<br/>100+ point checklist<br/>12 dimensions validated"]
        S5["Stage 5: New Services<br/>Scaffold from template<br/>100% compliant day 1"]
        S6["Stage 6: Hardening<br/>Dev/prod separation<br/>Safe automation"]
        S4 --> S5 --> S6
    end

    subgraph Stage7_8["Stages 7-8: Analytics & Ops"]
        S7["Stage 7: Trading Analytics<br/>BigQuery analysis<br/>Good vs bad trades<br/>Pattern detection"]
        S8["Stage 8: System Monitoring<br/>Auto-remediation<br/>Log analysis<br/>Alert management"]
        S7 --> S8
    end

    subgraph Stage9["Stage 9: Client Platform"]
        S9["Client Strategy Testing<br/>Text normalization<br/>Schema generation<br/>Backtest execution<br/>Performance reporting"]
    end

    Stage1_2 --> Stage3 --> Stage4_6 --> Stage7_8 --> Stage9

    Prescribed -.->|"Applies to"| Stage1_2
    Prescribed -.->|"Applies to"| Stage3
    Template -.->|"Applies to"| Stage4_6
    Interactive -.->|"Applies to"| Stage7_8
    ClientFacing -.->|"Applies to"| Stage9

    subgraph GCP["GOOGLE CLOUD PLATFORM INTEGRATION"]
        Run["Cloud Run<br/>Agent execution"]
        BQ["BigQuery<br/>Data warehouse"]
        GCS["GCS<br/>Storage"]
        Gemini["Gemini<br/>AI generation"]
        Vertex["Vertex AI<br/>ML platform"]
        Monitor["Cloud Monitoring<br/>Observability"]
    end

    Stage1_2 -.->|"Uses"| Run
    Stage3 -.->|"Uses"| Monitor
    Stage4_6 -.->|"Uses"| Run
    Stage4_6 -.->|"Uses"| GCS
    Stage7_8 -.->|"Uses"| BQ
    Stage7_8 -.->|"Uses"| Vertex
    Stage7_8 -.->|"Uses"| Monitor
    Stage9 -.->|"Uses"| Gemini
    Stage9 -.->|"Uses"| Run
    Stage9 -.->|"Uses"| BQ

    style Stage1_2 fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
    style Stage3 fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style Stage4_6 fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px
    style Stage7_8 fill:#b3e5fc,stroke:#0277bd,stroke-width:2px
    style Stage9 fill:#ffccbc,stroke:#d84315,stroke-width:3px
    style GCP fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
```

---

## 5. Quality Gates Detail (Simple)

```mermaid
flowchart LR
    Start["Agent<br/>Completes Fix"] --> Phase1["Phase 1<br/>Local Auto-Fix<br/>ruff format<br/>ruff check --fix"]

    Phase1 --> Phase2["Phase 2<br/>Local Verify<br/>Format check<br/>Lint check<br/>Tests<br/>Imports"]

    Phase2 -->|Pass| Phase3["Phase 3<br/>Pre-Commit<br/>Hooks<br/>Same checks<br/>again"]
    Phase2 -->|Fail| Fix["Fix Root Cause<br/>(Max 3 attempts)"]
    Fix --> Phase1
    Fix -.->|"3 failures"| BugIssue["Create Bug Issue<br/>Human escalation"]

    Phase3 --> Phase4["Phase 4<br/>CI/CD<br/>GitHub Actions<br/>Cloud Build"]

    Phase4 -->|Pass| PR["Create PR<br/>Fixes #XXX<br/>Auto-merge"]
    Phase4 -->|Fail| BugIssue

    PR --> Merge["Merge to Main<br/>Issue Auto-Closes"]

    style Phase1 fill:#bbdefb,stroke:#1565c0,stroke-width:2px
    style Phase2 fill:#ffccbc,stroke:#d84315,stroke-width:2px
    style Phase3 fill:#c5e1a5,stroke:#558b2f,stroke-width:2px
    style Phase4 fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style Merge fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
    style BugIssue fill:#ffcdd2,stroke:#c62828,stroke-width:3px
    style Fix fill:#ffe082,stroke:#f57c00,stroke-width:2px
```

---

## 6. GitHub Actions Integration

```mermaid
flowchart TD
    subgraph Manual["MANUAL TRIGGER"]
        RunDiff["User runs:<br/>run-diff-checker.py<br/>OR<br/>GitHub Actions<br/>scheduled weekly"]
    end

    subgraph GHActions["GITHUB ACTIONS WORKFLOW"]
        Scan["Scan Codebase<br/>• Import violations<br/>• Config issues<br/>• Missing tests"]
        CreateIssues["Create GitHub Issues<br/>via GitHub API"]
        ApplyLabels["Apply Labels<br/>• epic / task / subtask<br/>• cod / bug<br/>• service label"]
    end

    subgraph ProjectWorkflows["GITHUB PROJECT WORKFLOWS"]
        AutoAdd["Auto-Add to Project<br/>When label matches"]
        AutoStatus["Auto-Set Status<br/>Based on issue state"]
        AutoPriority["Auto-Set Priority<br/>Based on labels"]
    end

    subgraph Projects["PROJECTS POPULATED"]
        CODProj["COD Project<br/>Filter: label:cod"]
        BugProj["Bugs Project<br/>Filter: label:bug"]
        ExecProj["Execution Project<br/>Filter: repo:execution-services<br/>-label:cod"]
        StratProj["Strategy Project<br/>Filter: repo:strategy-service<br/>-label:cod"]
    end

    RunDiff --> Scan --> CreateIssues --> ApplyLabels
    ApplyLabels --> AutoAdd --> AutoStatus --> AutoPriority
    AutoPriority --> CODProj
    AutoPriority --> BugProj
    AutoPriority --> ExecProj
    AutoPriority --> StratProj

    style GHActions fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    style ProjectWorkflows fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    style Projects fill:#e1f5fe,stroke:#01579b,stroke-width:2px
```

---

## Summary

### Key Principles:

1. **Distinct Workflows:** Each project has specific labels and automation rules
2. **Two Project Types:** Epic→Task→Subtask hierarchies AND flat issue lists
3. **Cross-Cutting CODs:** 'cod' label appears across all projects for architectural work
4. **5-Step Automation:** Detection → GitHub → Agents → Quality Gates → Close/Retry
5. **Progressive Autonomy:** 9 stages from simple (code standards) to complex (client platform)

### Google Cloud Integration:

- **Cloud Run:** Agent execution at scale
- **BigQuery:** Trading data warehouse & analytics
- **GCS:** Market data storage & logs
- **Gemini:** AI code generation & text normalization
- **Vertex AI:** ML training & deployment
- **Cloud Monitoring:** System observability

### Next Steps:

1. Automate Steps 1-2 via GitHub Actions (diff checker → issue creation)
2. Connect multi-repo UI to Cursor CLI / VM deployment
3. Implement bug→issue cross-referencing (4b failure path)
4. Scale to 5-50 parallel agents on Google Cloud Run
5. Iterate through stages 1-9 progressively
