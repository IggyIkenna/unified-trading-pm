# R&D Tax Credit Documentation

**Last Updated:** 2026-02-11

---

## Purpose

This directory contains tooling and documentation for R&D tax credit claims. The export script generates a CSV of all
technical work completed during a tax year, including:

- Time spent on each work item (from commit timestamps)
- Work item categorization (feature, bug, research, infrastructure)
- Data acquisition costs (e.g., market data subscriptions)
- Commit SHAs as audit trail

This data is used by accountants and tax advisors to calculate eligible R&D tax credits.

---

## What is an R&D Tax Credit?

R&D tax credits are government incentives that allow businesses to claim a credit (or deduction) for qualifying research
and development expenditures. In the US, this is typically:

- **Federal R&D Tax Credit** (IRS Form 6765): 20% of qualified research expenses above a base amount
- **State R&D Tax Credits** (varies by state): Additional credits ranging from 5-20%

### What Qualifies as R&D?

To qualify, work must meet the "Four-Part Test":

1. **Permitted Purpose:** Work must develop or improve a product, process, technique, formula, or software
2. **Technological in Nature:** Work must rely on principles of physical/biological sciences, engineering, or computer
   science
3. **Elimination of Uncertainty:** Work must attempt to discover information to eliminate technical uncertainty
4. **Process of Experimentation:** Work must evaluate alternatives (e.g., design iterations, A/B tests)

### What Work Qualifies in Our System?

**Qualified Activities:**

- Developing new trading algorithms (e.g., signal generation, position sizing)
- Designing distributed data pipelines (e.g., batch-live symmetry, sharding strategies)
- Optimizing performance (e.g., latency reduction, throughput improvements)
- Building monitoring and observability systems (e.g., 3-tier event logging)
- Researching alternative architectures (e.g., evaluating Pub/Sub vs queues for real-time data)
- Developing ML models (e.g., feature engineering, hyperparameter tuning)

**Not Qualified Activities:**

- Routine code maintenance (e.g., updating dependencies)
- Documentation that doesn't describe technical innovation
- Non-technical work (e.g., project management, business development)
- Cosmetic UI changes (unless testing usability hypotheses)

**Gray Areas (Consult Tax Advisor):**

- Bug fixes: qualify if solving complex technical problem; don't qualify if simple typo fix
- Infrastructure setup: qualify if designing/evaluating alternatives; don't qualify if following standard playbooks
- Testing: qualify if experimental (e.g., A/B testing algorithms); don't qualify if routine regression tests

---

## Export Script Usage

### Prerequisites

1. **Install gh CLI:**

   ```bash
   # macOS
   brew install gh

   # Linux
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh
   ```

2. **Authenticate gh CLI:**

   ```bash
   gh auth login
   # Follow prompts to authenticate with GitHub
   ```

3. **Clone all repos:**

   ```bash
   cd /path/to/workspace

   # Clone all repos (if not already cloned)
   gh repo clone IggyIkenna/unified-trading-deployment-v3
   gh repo clone IggyIkenna/instruments-service
   # ... etc (or use the batch clone script if available)
   ```

4. **Python 3.8+:**
   ```bash
   python3 --version
   # Should be >= 3.8
   ```

---

### Basic Usage

Export all closed issues from a single repo for 2024:

```bash
cd /path/to/unified-trading-codex/11-project-management/rd-tax-credits

python export-script.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --repo unified-trading-deployment-v3 \
  --output exports/rd-claim-2024-deployment.csv
```

Export from all repos in the workspace:

```bash
python export-script.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --all-repos \
  --workspace-root /path/to/workspace \
  --output exports/rd-claim-2024-all-repos.csv
```

Export for a different GitHub org:

```bash
python export-script.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --all-repos \
  --github-org YourGitHubOrg \
  --workspace-root /path/to/workspace \
  --output exports/rd-claim-2024.csv
```

---

### Output CSV Format

The script generates a CSV with the following columns:

| Column                  | Description                                                  | Example                                                      |
| ----------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `issue_number`          | GitHub issue number                                          | 42                                                           |
| `title`                 | Issue title                                                  | "Implement batch-live symmetry for market-tick-data-service" |
| `type`                  | Work type (feature, bug, research, infrastructure, other)    | feature                                                      |
| `area`                  | Codex area (domain, data, observability, architecture, etc.) | architecture                                                 |
| `service`               | Service/repo name                                            | market-tick-data-service                                     |
| `assignee`              | GitHub username of assignee                                  | IggyIkenna                                                   |
| `time_estimate_hours`   | Estimated hours from issue body                              | 48                                                           |
| `actual_hours`          | Calculated from commit timestamps                            | 52.5                                                         |
| `data_cost_usd`         | Data acquisition costs from issue body                       | 1250.00                                                      |
| `start_date`            | Date of first commit                                         | 2024-03-15                                                   |
| `end_date`              | Date of last commit or issue close                           | 2024-03-22                                                   |
| `commit_count`          | Number of commits referencing issue                          | 12                                                           |
| `commit_shas`           | Short commit SHAs (semicolon-separated)                      | a1b2c3d; e4f5g6h; ...                                        |
| `technical_description` | First 500 chars of issue body                                | "Design and implement batch-live symmetry pattern..."        |
| `repo`                  | Repository name                                              | market-tick-data-service                                     |

---

### How Actual Hours are Calculated

The script calculates actual hours using commit timestamps:

1. **Find all commits** that reference the issue number (e.g., "#42", "fixes #42", "closes #42")
2. **Sort commits** by timestamp (chronological order)
3. **Calculate time span:**
   - If 1 commit: assume 2 hours minimum
   - If 2+ commits: time between first and last commit (or issue close, whichever is later)
4. **Cap at reasonable maximum:** 8 hours per day (e.g., if commits span 5 days, max 40 hours)

**Example:**

- Issue #42 has 3 commits:
  - Commit 1: 2024-03-15 10:00 AM
  - Commit 2: 2024-03-16 3:00 PM
  - Commit 3: 2024-03-17 5:00 PM
- Time span: 31 hours (10 AM March 15 → 5 PM March 17)
- Capped at: 24 hours (3 days × 8 hours)
- **Actual hours: 24.0**

**Why this method?**

- More accurate than using estimated hours (which are often wrong)
- Based on objective data (git commits)
- Provides audit trail (commit SHAs) for tax authorities

---

### How Time Estimates are Extracted

The script looks for time estimates in issue bodies using these patterns:

- `"Effort: 16 hours"` → 16 hours
- `"Time estimate: 2 days"` → 16 hours (2 days × 8 hours)
- `"Estimate: 1 week"` → 40 hours (1 week × 40 hours)
- `"16h"` → 16 hours
- `"2d"` → 16 hours
- `"1w"` → 40 hours

**If no estimate found:** Leave `time_estimate_hours` blank (accountant can use actual hours instead)

---

### How Data Costs are Extracted

The script looks for data costs in issue bodies using these patterns:

- `"Data cost: $1,250"` → 1250.00
- `"Cost: $500"` → 500.00
- `"Budget: $2,000"` → 2000.00

**Examples of data costs:**

- TARDIS market data subscription
- Databento API usage
- The Graph subgraph queries
- Cloud provider data egress fees (if significant)

**If no cost found:** Leave `data_cost_usd` blank

---

## Best Practices for Issue Tracking

To maximize R&D tax credit claims, follow these practices when creating GitHub issues:

### 1. Always Include Time Estimates

Add to issue body:

```markdown
## Effort Estimate

**Time estimate:** 16 hours

**Breakdown:**

- Design: 4 hours
- Implementation: 8 hours
- Testing: 4 hours
```

### 2. Document Data Costs

If work requires purchasing data:

```markdown
## Data Costs

**Data cost:** $1,250

**Breakdown:**

- TARDIS historical tick data for BTC-USD (Jan-Dec 2024): $1,000
- Databento options chain data: $250
```

### 3. Write Technical Descriptions

First paragraph should clearly describe the technical challenge:

```markdown
## Technical Description

Design and implement batch-live symmetry pattern for market-tick-data-service. This requires:

1. Abstracting data source (file vs WebSocket) behind adapter interface
2. Implementing reconnection logic for live mode (exponential backoff)
3. Adding mode toggle (--mode batch|live) with 90% code reuse

**Technical uncertainty:** How to handle late-arriving ticks in live mode? Evaluate sliding window vs tumbling window
approaches.
```

### 4. Reference Issues in Commits

Always include issue number in commit messages:

```bash
git commit -m "Implement batch-live symmetry adapter pattern (#42)"
```

Or use GitHub keywords to auto-close issues:

```bash
git commit -m "Add WebSocket reconnection logic

Implements exponential backoff with jitter. Fixes #42."
```

### 5. Label Issues Correctly

Use labels to categorize work:

- **Type labels:** `feature`, `bug`, `research`, `infrastructure`
- **Area labels:** `domain`, `data`, `observability`, `architecture`, etc.
- **Priority labels:** `P0`, `P1`, `P2`, `P3`

This helps the export script auto-categorize issues.

---

## Calculating Eligible Hours

Not all hours are eligible for R&D tax credits. Use this guide to filter:

### Eligible Work (Include in Claim)

- **Direct R&D:** Design, implementation, testing of technical innovations
- **Experimentation:** A/B tests, performance benchmarks, evaluating alternatives
- **Research:** Reading papers, studying algorithms, prototyping approaches
- **Debugging complex issues:** Root cause analysis of non-obvious bugs

### Not Eligible Work (Exclude from Claim)

- **Routine coding:** Implementing well-known patterns without uncertainty
- **Documentation:** Writing READMEs, user guides (unless documenting technical innovation)
- **Meetings:** Stand-ups, planning meetings (unless specifically discussing technical approach)
- **Project management:** Creating roadmaps, tracking progress, administrative tasks
- **Ops/Maintenance:** Updating dependencies, rotating credentials, routine patches

### Gray Areas (Consult Tax Advisor)

- **Architecture design:** Eligible if evaluating alternatives; not eligible if following standard patterns
- **Testing:** Eligible if experimental (e.g., property-based testing, chaos engineering); not eligible if unit tests
- **Code review:** Eligible if providing technical guidance; not eligible if just checking style

---

## Using the CSV for Tax Filing

### Step 1: Review and Filter

Open the CSV in Excel/Google Sheets and:

1. **Filter by `type`:** Focus on `feature`, `research`, `infrastructure` (highest R&D potential)
2. **Review `technical_description`:** Does it describe technical uncertainty?
3. **Flag non-qualifying work:** Add column `exclude_reason` for items to exclude
4. **Calculate eligible hours:** Sum `actual_hours` for qualifying work

### Step 2: Calculate Total R&D Expenses

R&D expenses = Eligible hours × Effective hourly rate + Data costs

**Effective hourly rate:**

- W-2 employees: (Annual salary + benefits) / 2080 hours
- Contractors: Hourly rate
- Owners: Reasonable market rate for similar role

**Example:**

- 500 eligible hours × $75/hour = $37,500
- Data costs: $5,000
- **Total R&D expenses: $42,500**

### Step 3: Apply Credit Rates

**Federal R&D Tax Credit:**

- Regular method: 20% of qualified expenses above base amount
- Alternative Simplified Credit (ASC): 14% of current year expenses above 50% of prior 3-year average
- **Example (ASC):** If prior 3-year average is $30,000:
  - Current year expenses: $42,500
  - Base amount: $30,000 × 50% = $15,000
  - Incremental expenses: $42,500 - $15,000 = $27,500
  - **Federal credit: $27,500 × 14% = $3,850**

**State R&D Tax Credit (varies by state):**

- California: 15% of qualified expenses (no base amount for small businesses)
- Texas: No state income tax (not applicable)
- New York: 6% of qualified expenses
- **Example (California):** $42,500 × 15% = $6,375

**Total credit: $3,850 + $6,375 = $10,225**

### Step 4: Documentation for Audits

Keep these for 7 years:

1. **CSV export** from this script (audit trail)
2. **GitHub issue screenshots** (technical descriptions)
3. **Commit history** (use `git log` to generate PDF)
4. **Time tracking records** (if you use time tracking software)
5. **Receipts for data costs** (invoices from TARDIS, Databento, etc.)
6. **Payroll records** (to support hourly rate calculation)

---

## Examples

### Example 1: Single Repo, One Quarter

Export Q1 2024 work from instruments-service:

```bash
python export-script.py \
  --start-date 2024-01-01 \
  --end-date 2024-03-31 \
  --repo instruments-service \
  --output exports/rd-claim-2024-Q1-instruments.csv
```

### Example 2: All Repos, Full Year

Export 2024 work from all repos:

```bash
python export-script.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --all-repos \
  --workspace-root ~/Documents/repos/unified-trading-system-repos \
  --output exports/rd-claim-2024-all.csv
```

### Example 3: Specific Date Range

Export work done in March 2024 (e.g., for quarterly filings):

```bash
python export-script.py \
  --start-date 2024-03-01 \
  --end-date 2024-03-31 \
  --all-repos \
  --workspace-root ~/Documents/repos/unified-trading-system-repos \
  --output exports/rd-claim-2024-03-march.csv
```

---

## Troubleshooting

### "Error: gh not found"

Install gh CLI (see Prerequisites section).

### "Error: Repo not found at /path/to/repo"

The script needs local clones to analyze git commits. Options:

1. Clone missing repos: `gh repo clone IggyIkenna/repo-name`
2. Use `--workspace-root` to specify correct path
3. If repo truly doesn't exist locally, script will still export issue data (but `actual_hours` will be blank)

### "No closed issues found"

Check:

1. Date range correct? (YYYY-MM-DD format)
2. GitHub org correct? (use `--github-org` flag)
3. Repo name correct? (check `gh repo list`)
4. gh CLI authenticated? (`gh auth status`)

### "Commits not found for issue #42"

Check:

1. Did commits reference issue number? (e.g., "#42" in commit message)
2. Are commits in the repo you're scanning? (issue may be closed but work done in different repo)
3. Use `git log --all --grep "#42"` to manually verify

---

## Contact

For questions about this export script or R&D tax credit claims:

- **Technical questions:** Create issue in unified-trading-codex repo
- **Tax questions:** Consult your CPA or tax advisor

---

## Changelog

### 2026-02-11

- Initial version of export script and documentation
- Supports single repo and all-repos modes
- Calculates actual hours from commit timestamps
- Extracts time estimates and data costs from issue bodies
- Categorizes work by type and area
