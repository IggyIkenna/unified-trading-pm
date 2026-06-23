# Ikenna's agent-orchestrator VM — onboarding

> **Status**: provisioned 2026-05-19. VM is up, workspace cloned, 12 slots ready. Backend service + DNS + TLS still need
> YOUR setup (steps below).
>
> **Authored**: Harsh + Claude, 2026-05-19. Workspace SSOT for ops procedures lives in `codex/05-infrastructure/`.

---

## TL;DR — two-Cursor workflow

You'll run **two Cursor windows side-by-side**:

1. **Local Cursor (on your Mac)** — same as today. General dev, planning, lightweight edits, reading the PM repo.
2. **Remote Cursor (SSH'd into the VM)** — for any session where you spawn the **Claude extension**. The Claude agent
   running inside that Cursor process can:
   - read/write all 27 workspace repos at `/home/ubuntu/unified-trading-system-repos/`
   - spawn workers via tmux on the VM (16 vCPU / 64 GB headroom)
   - touch any of the 12 per-slot worktrees at `.tabs/1..12/<repo>/`
   - hit the local FastAPI backend at `localhost:8765` (no auth dance over loopback)

   Your laptop fan stays quiet; the VM does the heavy lifting.

---

## What's already set up

| Resource       | Value                                                                                                                                                                     |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| EC2 instance   | `i-0c9b283b31d6b5ca7` — `m8i.4xlarge` (16 vCPU / 64 GB / Intel Granite Rapids)                                                                                            |
| Region / AZ    | `ap-northeast-1` / `ap-northeast-1c`                                                                                                                                      |
| Public IP      | `13.113.200.22`                                                                                                                                                           |
| Boot disk      | 300 GB gp3 (~4.8 GB used)                                                                                                                                                 |
| OS             | Ubuntu 24.04 LTS, kernel 6.17                                                                                                                                             |
| Pre-installed  | nginx, certbot, git, build tools, tmux, uv 0.11.15, Python 3.13.13                                                                                                        |
| Workspace root | `/home/ubuntu/unified-trading-system-repos/`                                                                                                                              |
| Repos cloned   | 27 of 28 (skipped: `new-sports-batting-services` — your PAT lacks access to that CosmicTrader repo)                                                                       |
| Slot worktrees | 12 × 27 = 324 worktrees on branches `tab/ikennaigboaka/1..12`                                                                                                             |
| AWS IAM        | account `427895769566`, `harsh-worker` creds in `~/.aws/credentials` (replace with your own — see below)                                                                  |
| SSH keypair    | EC2 keypair `agent-orchestrator-key`; private key in AWS Secrets Manager at `arn:aws:secretsmanager:ap-northeast-1:427895769566:secret:agent-orchestrator-vm-ssh-private` |
| Security group | `sg-066c852065f8cdcac` (ports 22/80/443/8765 open from 0.0.0.0/0)                                                                                                         |

**Cost**: ~$1.00/hr on-demand. With AWS credits, effectively free.

---

## 🔧 EOD 2026-05-19 pickup list — for your main agent to finish

> **Update**: more was completed tonight than the per-step section below documents. Backend systemd, nginx HTTP, uv
> sync, JWT secret, and `backends.json` wire-up are all DONE. Below is the **minimum remaining work** to make
> `https://agent-orchestrator.odum-research.com` live for you. Hand this to your main agent.

### Status snapshot

| Item                                                                    | State                                                                                                                                                                                         |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| EC2 VM `m8i.4xlarge` running                                            | ✅ done (Harsh)                                                                                                                                                                               |
| 27 workspace repos + 12 slot worktrees                                  | ✅ done (Harsh)                                                                                                                                                                               |
| All sibling repos on `live-defi-rollout` (agent-orchestrator on `main`) | ✅ done (Harsh)                                                                                                                                                                               |
| `agent-orchestrator` `uv sync` (Python deps)                            | ✅ done (Harsh)                                                                                                                                                                               |
| JWT secret generated + in `.env.local`                                  | ✅ done (Harsh) — value also backed up to AWS Secrets Manager as `agent-orchestrator-jwt-secret`                                                                                              |
| `orchestrator.service` systemd unit installed + running                 | ✅ done (Harsh) — `sudo systemctl status orchestrator` confirms                                                                                                                               |
| nginx :80 reverse proxy → 127.0.0.1:8765                                | ✅ done (Harsh) — external smoke: `curl http://13.113.200.22/api/healthz` returns 200                                                                                                         |
| `data/config/backends.json` updated with `ikenna-vm` as default         | ✅ done (Harsh) — committed to `IggyIkenna/agent-orchestrator:main@66923e7`                                                                                                                   |
| **Elastic IP** (`13.113.200.22`, was `35.78.213.80` auto-assigned)      | ✅ done (slot-1 2026-05-19) — `eipalloc-07b7bfe509d63c477` attached, IP now stable across stop/start                                                                                          |
| **DNS** `api.agent-orchestrator.odum-research.com` → `13.113.200.22`    | ✅ done (slot-1 2026-05-19) — Squarespace UI on the `.com` (not `.co.uk`) zone; propagated globally                                                                                           |
| **CAA** `letsencrypt.org` added to odum-research.com                    | ✅ done (slot-1 2026-05-19) — existing CAA was `0 issue "pki.goog"` only, blocked LE; appended `0 issue "letsencrypt.org"`                                                                    |
| **TLS** via certbot                                                     | ✅ done (slot-1 2026-05-19) — `--nginx -d api.agent-orchestrator.odum-research.com`, expires 2026-08-17, certbot.timer auto-renew scheduled                                                   |
| **GitHub auth** on VM (so agents can git push/pull)                     | ✅ done (slot-1 2026-05-19) — `~/.ssh/github_ed25519` generated; pub key added to ikenna's GitHub; `ssh -T git@github.com` returns "Hi IggyIkenna!"                                           |
| **GCP ADC** on VM (so agents can read GCS / secrets)                    | ✅ done (slot-1 2026-05-19) — `gcloud auth application-default login --no-browser` + `gcloud auth login --no-browser` (both via Mac remote-bootstrap); GH_PAT secret read smoke passes        |
| **Anthropic / Claude CLI** auth on VM                                   | ✅ done (slot-1 2026-05-19) — Node 22 + `claude` 2.1.144 installed, OAuth via Max plan; `~/.claude/.credentials.json` confirms `subscriptionType=max`, `rateLimitTier=default_claude_max_20x` |
| **Bootstrap users** on backend                                          | ✅ done (slot-1 2026-05-19) — `manage_users.py add ikenna` w/ argon2id hash; `verify` smoke passes; bash history cleared                                                                      |
| **CORS allow-list for Firebase origins**                                | ✅ done (slot-1 2026-05-19) — `IggyIkenna/agent-orchestrator:main@8daa12d` adds prod + staging + `*.web.app` origins; orchestrator systemd unit restarted to pick up; preflight returns 200   |
| **Firebase Hosting deploy** of SPA                                      | ✅ done (slot-1 2026-05-19) — `IggyIkenna/agent-orchestrator:main@dab9ac3` drops dead Cloud Run rewrites from `firebase.json`; both prod + UAT targets serving HTTP 200                       |

### Sequenced commands for your main agent

Run these in order from a Remote-SSH'd Cursor session on the VM (or your laptop where appropriate — annotated).

**1. (Mac) Add DNS record in Squarespace**

Operator-only UI action. Add A record:

```
Host:  api.agent-orchestrator
Type:  A
TTL:   3600
Value: 13.113.200.22
```

Wait + verify propagation:

```bash
dig api.agent-orchestrator.odum-research.com +short
# expect: 13.113.200.22
```

**2. (VM) GitHub SSH key**

```bash
ssh-keygen -t ed25519 -C "ikenna-agent-orchestrator-vm" -f ~/.ssh/github_ed25519 -N ""
cat ~/.ssh/github_ed25519.pub
# paste into github.com → Settings → SSH and GPG keys → New SSH key (title: "agent-orchestrator-vm")

cat >> ~/.ssh/config <<EOF

Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_ed25519
  StrictHostKeyChecking no
EOF

ssh -T git@github.com  # expect: Hi IggyIkenna! ...
```

**3. (VM) GCP ADC**

```bash
gcloud auth application-default login   # browser flow via SSH port-forward
gcloud config set project central-element-323112
gcloud secrets versions access latest --secret=GH_PAT --project=central-element-323112 | head -c 10
# expect: first 10 chars of PAT (confirms read access)
```

**4. (VM) Install Node + Claude CLI + auth — DONE 2026-05-19 (Max plan, NOT API key)**

```bash
# Node from NodeSource (Ubuntu's apt has an older version)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

sudo npm install -g @anthropic-ai/claude-code

# OAuth flow — uses your Claude Max subscription (NO ANTHROPIC_API_KEY env var must be set
# in your interactive shell; if it is, Claude Code bills per-token via API instead of Max).
# Just run `claude` for the first time — the first-run wizard walks through:
#   1. theme (pick any)
#   2. login method → select "Claude account with subscription · Pro, Max, Team, or Enterprise"
#   3. it prints an OAuth URL — open on any browser, sign in with ikenna@odum-research.com,
#      copy the verification code shown after approval, paste back into the terminal prompt
#   4. confirm `/home/ubuntu` trust prompt → done
claude        # NOT `claude login` — the first-run wizard handles auth automatically
claude --version

# Verify Max plan was used (not API):
python3 -c "import json; d=json.load(open('$HOME/.claude/.credentials.json'))['claudeAiOauth']; print('subscriptionType:', d['subscriptionType'], '| tier:', d['rateLimitTier'])"
# Expected: subscriptionType: max | tier: default_claude_max_20x
```

If you need to re-auth (e.g. after token refresh failure), run `claude /logout` then `claude` again.

**5. (VM) Bootstrap backend users**

```bash
cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator
.venv/bin/python scripts/manage_users.py add ikenna   # prompts for password
.venv/bin/python scripts/manage_users.py add harsh    # optional — if Harsh should access this backend too
.venv/bin/python scripts/manage_users.py list         # verify both rows
```

No backend restart needed — `auth.py` reads `users.json` on every login attempt.

**6. (VM) TLS via certbot** (after DNS propagates in step 1)

```bash
sudo certbot --nginx -d api.agent-orchestrator.odum-research.com \
  --email ikenna@odum-research.com --agree-tos --non-interactive --redirect

# Verify
curl -s https://api.agent-orchestrator.odum-research.com/api/healthz
# expect: {"status":"ok",...}
```

Certbot auto-edits the nginx config and sets up auto-renew via systemd timer.

**7. (Mac OR VM) First Firebase Hosting deploy of the SPA**

This is the missing piece that's making `https://agent-orchestrator.odum-research.com` show the Firebase "Site Not
Found" page. The Hosting site exists (Step P2 of your cutover plan) but no SPA bundle has been pushed yet.

```bash
# From your laptop OR VM — wherever you have firebase-tools auth
cd /path/to/agent-orchestrator   # the local clone

# Make sure you're on main with the latest backends.json
git pull origin main

# Build the dashboard
cd dashboard
npm install
npm run build     # outputs to dashboard/dist/
cd ..

# Firebase CLI
npm install -g firebase-tools  # if not already
firebase login                  # browser flow with your Google account
firebase use --add              # pick the central-element-323112 project

# Deploy to staging hosting target first (sanity check)
firebase deploy --only hosting:uat

# Verify
curl -sI https://agent-orchestrator.staging.odum-research.com | head -1
# expect: HTTP/2 200

# Then prod
firebase deploy --only hosting:prod

curl -sI https://agent-orchestrator.odum-research.com | head -1
# expect: HTTP/2 200
```

**8. (Mac, browser) End-to-end smoke**

1. Open `https://agent-orchestrator.odum-research.com` in your browser
2. The SPA loads (no more "Site Not Found")
3. Dropdown defaults to `Ikenna VM (Tokyo)`
4. Log in with the credentials you set in step 5
5. Dashboard loads showing the 12 slot worktrees as available
6. Spawn a test agent on slot 1 — should appear in `tmux ls` on the VM

If anything 401s/CORS-errors, see Troubleshooting section below.

### Optional cleanup (any time)

- **Decommission the old Cloud Run staging in europe-west4** (now redundant per D0):
  ```bash
  gcloud run services delete agent-orchestrator-staging --region europe-west4 --project central-element-323112 --quiet
  ```
- **Tear down old europe-west4 image** in Artifact Registry (if you want):
  ```bash
  gcloud artifacts repositories delete cloud-run-source-deploy --location europe-west4 --project central-element-323112 --quiet
  ```

---

## Step 1 — Fetch the SSH key

On your Mac:

```bash
# Pull the private key from AWS Secrets Manager (you already have AWS creds for account 427895769566)
aws secretsmanager get-secret-value \
  --region ap-northeast-1 \
  --secret-id agent-orchestrator-vm-ssh-private \
  --query SecretString \
  --output text > ~/.ssh/agent-orchestrator-key
chmod 600 ~/.ssh/agent-orchestrator-key

# Smoke test
ssh -i ~/.ssh/agent-orchestrator-key ubuntu@13.113.200.22 'echo ok'
```

---

## Step 2 — Configure Cursor Remote SSH

Add to your `~/.ssh/config` on the Mac:

```
Host agent-orchestrator-vm
  HostName 13.113.200.22
  User ubuntu
  IdentityFile ~/.ssh/agent-orchestrator-key
  ServerAliveInterval 60
  ServerAliveCountMax 10
```

In Cursor:

1. `Cmd+Shift+P` → **Remote-SSH: Connect to Host...** → pick `agent-orchestrator-vm`
2. New window opens; bottom-left status shows `SSH: agent-orchestrator-vm`
3. **File → Open Folder** → `/home/ubuntu/unified-trading-system-repos`
4. (Optional) `cp .tabs/1/unified-trading-system-repos.code-workspace ~/agent-orch-slot1.code-workspace` and **File →
   Open Workspace from File** for the multi-root view scoped to slot 1

---

## Step 3 — Set up GitHub auth on the VM

Currently the VM has zero GitHub auth — no token, no SSH key. Pick **one**:

**Option A — SSH key** (recommended for long-term):

```bash
ssh-keygen -t ed25519 -C "ikenna-agent-orchestrator-vm" -f ~/.ssh/github_ed25519 -N ""
cat ~/.ssh/github_ed25519.pub
# Copy the printed line into GitHub → Settings → SSH and GPG keys → New SSH key
# Title: "agent-orchestrator-vm-1"

# Wire it up
cat >> ~/.ssh/config <<'EOF'

Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/github_ed25519
  StrictHostKeyChecking no
EOF

# Verify
ssh -T git@github.com  # should say: Hi IggyIkenna! You've successfully authenticated...
```

**Option B — HTTPS + your existing PAT**:

```bash
# Your PAT is already in GCP Secret Manager
gcloud auth application-default login  # complete this first (see Step 4)
gcloud secrets versions access latest --secret=GH_PAT --project=central-element-323112 > ~/.gh-pat
chmod 600 ~/.gh-pat

git config --global credential.helper store
echo "https://x-access-token:$(cat ~/.gh-pat)@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
```

---

## Step 4 — Set up GCP ADC

```bash
gcloud auth application-default login
# Browser flow opens via SSH port-forward; pick ikenna@odum-research.com
gcloud config set project central-element-323112
```

Verify:

```bash
gcloud secrets versions access latest --secret=GH_PAT --project=central-element-323112 | head -c 20
# should print first 20 chars of PAT
```

---

## Step 5 — Replace AWS creds with your own

Your IAM user is in account `427895769566`. Generate a key for yourself + replace `harsh-worker`'s creds:

```bash
# Either: ask Ikenna's automation to provision an `ikenna-worker` IAM user (mirror harsh-worker)
# OR: use your existing AWS account creds directly

# Update ~/.aws/credentials with your access key + secret
nano ~/.aws/credentials
# Replace the [default] block with your own keys, keep region=ap-northeast-1

aws sts get-caller-identity  # should print your IAM user, not harsh-worker
```

---

## Step 6 — Install Claude CLI + Max-plan OAuth

> **Billing model**: this uses your Claude **Max subscription**, not the Anthropic API (pay-per-token). If
> `ANTHROPIC_API_KEY` is set in your shell, Claude Code uses API billing and your Max plan is bypassed. Keep the env var
> unset in your interactive shell. The orchestrator service may still set the API key in its systemd unit for
> programmatic Claude calls — that's separate and intentional.

```bash
# Node from NodeSource (Ubuntu's apt nodejs is too old for the CLI)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Claude CLI globally
sudo npm install -g @anthropic-ai/claude-code

# First-run wizard handles auth — DO NOT run `claude login` (it's not a subcommand).
claude
# Walks you through:
#   theme → "Claude account with subscription · Pro, Max, Team, or Enterprise" → OAuth URL
# Open the URL in any browser, sign in with ikenna@odum-research.com (your Max account),
# copy the verification code, paste into the terminal prompt → done.
```

Verify Max plan (not API) is the auth path:

```bash
claude --version
python3 -c "import json; d=json.load(open('$HOME/.claude/.credentials.json'))['claudeAiOauth']; print(d['subscriptionType'], d['rateLimitTier'])"
# Expected: max default_claude_max_20x
```

---

## Step 7 — Install Python deps for agent-orchestrator

```bash
cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator
uv sync   # installs deps into .venv/ (~1 min)
```

---

## Step 8 — Bootstrap users for the backend

```bash
cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator
.venv/bin/python scripts/manage_users.py add ikenna  # prompts for password
.venv/bin/python scripts/manage_users.py add harsh   # if Harsh should also access this backend
```

Users land in `data/config/users.json` (gitignored). The server reads it on every login attempt — no restart needed
after add/remove.

---

## Step 9 — Generate JWT secret + start backend

```bash
# Generate a fresh JWT signing secret (one-shot)
mkdir -p ~/.config/agent-orchestrator
openssl rand -hex 32 > ~/.config/agent-orchestrator/jwt-secret
chmod 600 ~/.config/agent-orchestrator/jwt-secret

# Quick smoke — run the backend in the foreground first to verify it boots
cd /home/ubuntu/unified-trading-system-repos/agent-orchestrator
ORCHESTRATOR_MODE=live \
ORCHESTRATOR_ALLOW_ANONYMOUS=false \
ORCHESTRATOR_USERS_JSON=$PWD/data/config/users.json \
ORCHESTRATOR_JWT_SECRET=$(cat ~/.config/agent-orchestrator/jwt-secret) \
.venv/bin/uvicorn server.server:app --host 127.0.0.1 --port 8765
```

In another SSH session:

```bash
curl -s http://127.0.0.1:8765/healthz
# should print: {"status":"ok",...}
```

Ctrl-C the foreground server when satisfied. Then wire it as a systemd service (`scripts/orchestrator.service` already
in the repo — copy to `/etc/systemd/system/`, edit paths, `systemctl enable --now orchestrator`).

---

## Step 10 — Public access (nginx + Let's Encrypt)

1. Add DNS A record in Squarespace: `api.agent-orchestrator.odum-research.com` → `13.113.200.22`
2. Wait 5-10 min for propagation (verify with `dig api.agent-orchestrator.odum-research.com +short`)
3. Configure nginx as reverse proxy:

```bash
sudo tee /etc/nginx/sites-available/agent-orchestrator <<'EOF'
server {
    listen 80;
    server_name api.agent-orchestrator.odum-research.com;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/agent-orchestrator /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# TLS
sudo certbot --nginx -d api.agent-orchestrator.odum-research.com
```

4. Add CORS allow for the SPA origin. Edit `server/server.py` middleware (or env var if one exists) to include
   `https://agent-orchestrator.odum-research.com` and `https://agent-orchestrator.staging.odum-research.com`.

---

## Step 11 — Wire the SPA dropdown to point at this VM

Edit `data/config/backends.json` (already present from earlier work):

```json
{
  "backends": [
    {
      "id": "ikenna-vm",
      "label": "Ikenna (VM)",
      "url": "https://api.agent-orchestrator.odum-research.com",
      "account_id": "ikenna-primary",
      "default": true
    },
    {
      "id": "harsh-this-box",
      "label": "Harsh (laptop)",
      "url": "https://orch.epiphanytechnologies.com",
      "account_id": "sub-a-ikenna"
    }
  ]
}
```

Then trigger a Firebase Hosting redeploy from the agent-orchestrator repo (your P4 CI wires this on push to main).

---

## How the two-Cursor workflow looks in practice

**Local Cursor**:

- Edit `unified-trading-pm/plans/...` for planning work
- Browse architecture docs
- Quick file edits where you don't need workspace-wide context

**Remote Cursor (SSH → VM)**:

- Open Cursor → Remote-SSH → `agent-orchestrator-vm`
- Open `/home/ubuntu/unified-trading-system-repos/`
- Open the Claude extension panel
- The Claude agent now has the full workspace as context, can:
  - `Bash` into any of the 12 slot worktrees and run quality gates
  - Edit any of 27 repos
  - Hit `http://127.0.0.1:8765/api/...` directly (no auth needed over loopback)
  - Spawn workers via `tmux new-session` (works because we're not on Cloud Run)
  - Run `gcloud`, `aws`, `claude`, `git` — all your auth is here on the VM

When you want to manage agents/slots via the dashboard:

- Open `https://agent-orchestrator.odum-research.com` in your browser (Firebase-hosted SPA)
- Dropdown is already pre-set to `Ikenna (VM)` (after Step 11)
- Log in with the credentials from Step 8
- Spawn/inspect/kill agents — they all run on the VM, talking to the same backend the SPA points at

---

## Known gaps / things to come back to

- **`new-sports-batting-services`** repo not cloned — your fine-grained PAT doesn't have access to this `CosmicTrader/*`
  repo. Grant access to your PAT (GitHub → Settings → PATs → edit → add repo access) then
  `cd /home/ubuntu/unified-trading-system-repos && git clone git@github.com:CosmicTrader/new-sports-batting-services.git` +
  re-run `setup-tab-worktrees.sh --add-slot 1..12`.
- **Cloud Run staging in europe-west4** (your existing P1 deployment) is now redundant. Tear down when convenient:
  `gcloud run services delete agent-orchestrator-staging --region europe-west4 --project central-element-323112`.
- **systemd unit + nginx config** above are the canonical pattern but I haven't run them — your call when to flip the
  backend from foreground-test to systemd-managed.
- **Slack notifications** wiring (your P0 successor) — `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` secret will need to flow into
  the VM systemd env file.

---

## Troubleshooting

- **SSH fails with "permission denied"**: `chmod 600 ~/.ssh/agent-orchestrator-key`, verify key matches what's in EC2
  (fingerprint `7xWw4Rd4Z2YuSF3I9CMjg47IEZWbPJyBIGUhloQiKgc=`).
- **Cursor Remote SSH hangs**: kill `~/.vscode-server/` on VM, reconnect.
- **`uv sync` fails**: ensure `~/.local/bin` is on PATH (`export PATH="$HOME/.local/bin:$PATH"` in `~/.bashrc`).
- **Backend 401 on login despite correct password**: check `ORCHESTRATOR_USERS_JSON` env var points at the file you
  bootstrapped users in.
- **VM cost concerns**: `aws ec2 stop-instances --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1` halts
  billing for compute (EBS still ~$24/mo). `start-instances` to resume — the public IP changes, so you'd update DNS too.
  For continuous use, leave it running.

---

## Quick reference

```bash
# SSH in
ssh -i ~/.ssh/agent-orchestrator-key ubuntu@13.113.200.22

# Or with config alias
ssh agent-orchestrator-vm

# View running tmux sessions (active agent slots)
tmux ls

# Tail backend logs (after systemd setup)
journalctl -u orchestrator -f

# Stop/start instance (cost control)
aws ec2 stop-instances  --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1
aws ec2 start-instances --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1
```
