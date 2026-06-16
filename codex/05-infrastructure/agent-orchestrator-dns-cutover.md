---
scope: [engineer, admin]
title: agent-orchestrator — DNS cutover recipe (Phase 11)
created: 2026-05-28
last_reviewed: 2026-05-28
owner: ikenna
status: active
---

# agent-orchestrator — DNS cutover (Phase 11)

> **What this is**: the recipe for putting per-VM FQDNs in front of the AWS epic VM fleet so the central API can reach
> each backend by name (or so an operator can curl one directly for debugging) without baking volatile public IPs into
> config files.
>
> **What this is NOT**: required for normal operations. Today's deployment works fine on public IPs (see
> `agent-orchestrator/data/config/backends.json`) because the dashboard talks ONLY to the central API and the central
> API reaches the fleet via private VPC IPs (`172.31.x.x`). Per-VM FQDNs are operator convenience + debugging clarity.

## Pre-requisites

1. **Elastic IPs allocated per VM** — without stable IPs the DNS records churn every time a VM is stopped/started. Use:

   ```bash
   bash deployment-service/scripts/aws/allocate-orchestrator-eips.sh --all
   ```

   This allocates 10 EIPs (one per epic VM, tagged `agent-orch-<vm>-eip`), associates them, and prints the new stable
   public IPs. The central VM (`ikenna-vm` at `13.113.200.22`) already has its EIP allocated 2026-05-20.

2. **`backends.json` updated** — after EIPs land, replace each VM's `url` public IP with the EIP. The script writes
   results to `/tmp/eip_alloc_results.txt`; copy them into `data/config/backends.json` and commit to
   `live-defi-rollout`.

3. **DNS zone access** — `odum-research.com` is managed via Squarespace's UI (DNS records back-end is on Google Cloud
   DNS post-Squarespace's Google Domains acquisition). Operator-only credentials.

## DNS records to add

One A record per fleet VM under the `*.agent-orchestrator.odum-research.com` hierarchy. The wildcard convention keeps
the zone tidy and avoids one record per VM in the zone file — but Squarespace doesn't support wildcards on subdomains,
so we use explicit per-VM A records. TTL 300 (5 min) so cutover errors recover quickly.

| Hostname                                                 | Type | Value (replace with EIP from `allocate-orchestrator-eips.sh`) | TTL |
| -------------------------------------------------------- | ---- | ------------------------------------------------------------- | --- |
| `api.agent-orchestrator.odum-research.com`               | A    | `13.113.200.22` (central, already live)                       | 300 |
| `api-defi.agent-orchestrator.odum-research.com`          | A    | `<EIP-vm-defi>`                                               | 300 |
| `api-cefi.agent-orchestrator.odum-research.com`          | A    | `<EIP-vm-cefi>`                                               | 300 |
| `api-tradfi.agent-orchestrator.odum-research.com`        | A    | `<EIP-vm-tradfi>`                                             | 300 |
| `api-sports.agent-orchestrator.odum-research.com`        | A    | `<EIP-vm-sports>`                                             | 300 |
| `api-prediction.agent-orchestrator.odum-research.com`    | A    | `<EIP-vm-prediction>`                                         | 300 |
| `api-ml.agent-orchestrator.odum-research.com`            | A    | `<EIP-vm-ml>`                                                 | 300 |
| `api-trading-core.agent-orchestrator.odum-research.com`  | A    | `<EIP-vm-trading-core>`                                       | 300 |
| `api-operator-ops.agent-orchestrator.odum-research.com`  | A    | `<EIP-vm-operator-ops>`                                       | 300 |
| `api-cross-cutting.agent-orchestrator.odum-research.com` | A    | `<EIP-vm-cross-cutting>`                                      | 300 |
| `api-orchestrator.agent-orchestrator.odum-research.com`  | A    | `<EIP-vm-orchestrator>`                                       | 300 |

## Cutover recipe

1. Allocate EIPs:

   ```bash
   bash deployment-service/scripts/aws/allocate-orchestrator-eips.sh --all
   cat /tmp/eip_alloc_results.txt   # tab-separated: vm-id  public-ip  alloc-id
   ```

2. Update `backends.json` `url` fields with each VM's new EIP (the `private_url` fields stay unchanged — they're
   VPC-internal and not affected by EIPs).

3. Add the A records via Squarespace DNS panel (or whichever DNS provider is in front of `odum-research.com` at cutover
   time). Use TTL 300 so a typo resolves in 5 minutes.

4. Wait for propagation + verify:

   ```bash
   for v in defi cefi tradfi sports prediction ml trading-core operator-ops cross-cutting orchestrator; do
     printf '%-30s ' "api-${v}"
     dig +short "api-${v}.agent-orchestrator.odum-research.com"
   done
   ```

   Each should return its EIP.

5. Optional sanity check — curl each VM's `/health` via FQDN (TLS not yet configured per-VM, so this is HTTP):

   ```bash
   for v in defi cefi tradfi sports prediction ml trading-core operator-ops cross-cutting orchestrator; do
     printf '%-30s ' "api-${v}"
     curl -s --max-time 3 "http://api-${v}.agent-orchestrator.odum-research.com:8026/health" | head -c 80
     echo
   done
   ```

   Expect `{"status":"ok",...}` per VM.

6. Commit + push the `backends.json` update to `live-defi-rollout`.

## Optional: per-VM TLS (deferred)

If/when per-VM HTTPS is wanted (today the central API at port 443 is the only TLS-terminated endpoint; fleet VMs serve
plaintext :8026 over the private VPC):

- Either: run nginx + certbot on each VM (replicate the central VM's setup, ~5 min per VM)
- Or: front the fleet with an AWS ALB with a wildcard cert for `*.agent-orchestrator.odum-research.com`

Not currently planned — the central API's TLS is sufficient because that's the only browser-facing surface.

## What this DOES NOT change

- Dashboard SPA still talks ONLY to `api.agent-orchestrator.odum-research.com` (the central API). Per-VM FQDNs are for
  direct operator/curl access, not for the browser.
- Central API still proxies to fleet VMs via `private_url` over VPC. The per-VM public FQDNs do NOT add latency or
  change the live request path.
- Fleet VM auth + role + slot config are unchanged.

## Composes with

- [`agent-orchestrator-worker-topology.md`](agent-orchestrator-worker-topology.md) § "Deferred (post-cutover)" — the
  "EIP allocation" + "DNS" items this doc resolves
- [`agent-orchestrator-deploy.md`](agent-orchestrator-deploy.md) — central API VM nginx + TLS shape, retained
- [`../04-architecture/agent-orchestrator-overview.md`](../04-architecture/agent-orchestrator-overview.md) §
  "Connectivity model — centralized API router" — explains why per-VM TLS isn't a prerequisite for browser traffic
