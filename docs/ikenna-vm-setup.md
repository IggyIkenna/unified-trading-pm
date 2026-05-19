# Ikenna's agent-orchestrator VM — onboarding

> **Status**: provisioned 2026-05-19. VM is up, workspace cloned, 12 slots ready.
> Backend service + DNS + TLS still need YOUR setup (steps below).
>
> **Authored**: Harsh + Claude, 2026-05-19. Workspace SSOT for ops procedures lives in `codex/05-infrastructure/`.

---

## TL;DR — two-Cursor workflow

You'll run **two Cursor windows side-by-side**:

1. **Local Cursor (on your Mac)** — same as today. General dev, planning, lightweight edits, reading the PM repo.
2. **Remote Cursor (SSH'd into the VM)** — for any session where you spawn the **Claude extension**. The Claude
   agent running inside that Cursor process can:
   - read/write all 27 workspace repos at `/home/ubuntu/unified-trading-system-repos/`
   - spawn workers via tmux on the VM (16 vCPU / 64 GB headroom)
   - touch any of the 12 per-slot worktrees at `.tabs/1..12/<repo>/`
   - hit the local FastAPI backend at `localhost:8765` (no auth dance over loopback)

   Your laptop fan stays quiet; the VM does the heavy lifting.

---

## What's already set up

| Resource | Value |
| --- | --- |
| EC2 instance | `i-0c9b283b31d6b5ca7` — `m8i.4xlarge` (16 vCPU / 64 GB / Intel Granite Rapids) |
| Region / AZ | `ap-northeast-1` / `ap-northeast-1c` |
| Public IP | `35.78.213.80` |
| Boot disk | 300 GB gp3 (~4.8 GB used) |
| OS | Ubuntu 24.04 LTS, kernel 6.17 |
| Pre-installed | nginx, certbot, git, build tools, tmux, uv 0.11.15, Python 3.13.13 |
| Workspace root | `/home/ubuntu/unified-trading-system-repos/` |
| Repos cloned | 27 of 28 (skipped: `new-sports-batting-services` — your PAT lacks access to that CosmicTrader repo) |
| Slot worktrees | 12 × 27 = 324 worktrees on branches `tab/ikennaigboaka/1..12` |
| AWS IAM | account `427895769566`, `harsh-worker` creds in `~/.aws/credentials` (replace with your own — see below) |
| SSH keypair | EC2 keypair `agent-orchestrator-key`; private key in AWS Secrets Manager at `arn:aws:secretsmanager:ap-northeast-1:427895769566:secret:agent-orchestrator-vm-ssh-private` |
| Security group | `sg-066c852065f8cdcac` (ports 22/80/443/8765 open from 0.0.0.0/0) |

**Cost**: ~$1.00/hr on-demand. With AWS credits, effectively free.

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
ssh -i ~/.ssh/agent-orchestrator-key ubuntu@35.78.213.80 'echo ok'
```

---

## Step 2 — Configure Cursor Remote SSH

Add to your `~/.ssh/config` on the Mac:

```
Host agent-orchestrator-vm
  HostName 35.78.213.80
  User ubuntu
  IdentityFile ~/.ssh/agent-orchestrator-key
  ServerAliveInterval 60
  ServerAliveCountMax 10
```

In Cursor:

1. `Cmd+Shift+P` → **Remote-SSH: Connect to Host...** → pick `agent-orchestrator-vm`
2. New window opens; bottom-left status shows `SSH: agent-orchestrator-vm`
3. **File → Open Folder** → `/home/ubuntu/unified-trading-system-repos`
4. (Optional) `cp .tabs/1/unified-trading-system-repos.code-workspace ~/agent-orch-slot1.code-workspace` and **File → Open Workspace from File** for the multi-root view scoped to slot 1

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

## Step 6 — Install Claude CLI

```bash
# Install Node (needed for the npm-distributed CLI)
sudo apt-get install -y nodejs npm

# Install Claude CLI globally
sudo npm install -g @anthropic-ai/claude-code

# Login (this opens a browser flow)
claude login
# Use your Anthropic account (separate from Harsh's — see D15 in the dual-deployment design doc)
```

Verify:

```bash
claude --version
which claude
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

Ctrl-C the foreground server when satisfied. Then wire it as a systemd service (`scripts/orchestrator.service`
already in the repo — copy to `/etc/systemd/system/`, edit paths, `systemctl enable --now orchestrator`).

---

## Step 10 — Public access (nginx + Let's Encrypt)

1. Add DNS A record in Squarespace: `api.agent-orchestrator.odum-research.com` → `35.78.213.80`
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
      "account_id": "harsh-primary"
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

- **`new-sports-batting-services`** repo not cloned — your fine-grained PAT doesn't have access to this `CosmicTrader/*` repo. Grant access to your PAT (GitHub → Settings → PATs → edit → add repo access) then `cd /home/ubuntu/unified-trading-system-repos && git clone git@github.com:CosmicTrader/new-sports-batting-services.git` + re-run `setup-tab-worktrees.sh --add-slot 1..12`.
- **Cloud Run staging in europe-west4** (your existing P1 deployment) is now redundant. Tear down when convenient: `gcloud run services delete agent-orchestrator-staging --region europe-west4 --project central-element-323112`.
- **systemd unit + nginx config** above are the canonical pattern but I haven't run them — your call when to flip the backend from foreground-test to systemd-managed.
- **Slack notifications** wiring (your P0 successor) — `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` secret will need to flow into the VM systemd env file.

---

## Troubleshooting

- **SSH fails with "permission denied"**: `chmod 600 ~/.ssh/agent-orchestrator-key`, verify key matches what's in EC2 (fingerprint `7xWw4Rd4Z2YuSF3I9CMjg47IEZWbPJyBIGUhloQiKgc=`).
- **Cursor Remote SSH hangs**: kill `~/.vscode-server/` on VM, reconnect.
- **`uv sync` fails**: ensure `~/.local/bin` is on PATH (`export PATH="$HOME/.local/bin:$PATH"` in `~/.bashrc`).
- **Backend 401 on login despite correct password**: check `ORCHESTRATOR_USERS_JSON` env var points at the file you bootstrapped users in.
- **VM cost concerns**: `aws ec2 stop-instances --instance-ids i-0c9b283b31d6b5ca7 --region ap-northeast-1` halts billing for compute (EBS still ~$24/mo). `start-instances` to resume — the public IP changes, so you'd update DNS too. For continuous use, leave it running.

---

## Quick reference

```bash
# SSH in
ssh -i ~/.ssh/agent-orchestrator-key ubuntu@35.78.213.80

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
