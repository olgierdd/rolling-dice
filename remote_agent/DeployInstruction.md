# Deploying the Check Winning Agent to a Virtual Machine with Nginx

This guide explains how to deploy the `check_winning_agent` (A2A remote agent) on a cloud virtual machine and expose it via Nginx reverse proxy so the agent card is accessible at:

```
https://montecarlo.com/a2a/check_winning_agent/.well-known/agent-card.json
```
Assuming you have domain name **montecarlo.com**

> **Reference**: [Google ADK – Deploy Agent](https://docs.cloud.google.com/run/docs/ai/build-and-deploy-ai-agents/deploy-adk-agent)

---

## Prerequisites

| Requirement | Details |
|---|---|
| VM access | `ssh root@montecarlo.com` |
| Python | 3.12+ on the VM |
| Domain | `montecarlo.com` pointing to the VM's public IP |
| Ports | 80 and 443 open in your cloud firewall |

---

## 1. Connect to the VM

```bash
ssh root@montecarlo.com
```

---

## 2. Install System Dependencies

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx git ufw
```

### Configure Firewall

```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
```

---

## 3. Upload the Project to the VM

**from your local machine (scp):**

```bash
# Run this on your LOCAL machine, from the project root
scp -r remote_agent requirements.txt root@montecarlo.com:/opt/check_winning_agent/
```

**deployment scrip**

```bash
chmod +x deploy.sh
deploy.sh
```
The resulting directory on the VM should look like:

```
/opt/check_winning_agent/
├── dot_env
├── requirements.txt
└── remote_agent/
    ├── __init__.py          # (create if missing – see below)
    └── check_winning_agent/
        ├── __init__.py
        ├── agent.json
        └── agent.py
```

> **Important:** Make sure there is an `__init__.py` inside `remote_agent/` so ADK recognises it as a package. If it doesn't exist, create it:
>
> ```bash
> touch /opt/check_winning_agent/remote_agent/__init__.py
> ```

---

## 4. Create the Python Virtual Environment

```bash
cd /opt/check_winning_agent
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. Configure Environment Variables

```bash
cp dot_env remote_agent/.env
```

Edit the `.env` file and set your real API keys:

```bash
nano remote_agent/.env
```

```dotenv
GOOGLE_API_KEY=<your-google-api-key>
GOOGLE_MODEL=gemini-2.5-flash
OPENAI_MODEL_NAME=openai/gpt-5.4-mini
OPENAI_API_KEY=<your-openai-api-key>
```

---

## 6. Verify the Agent Starts Manually

```bash
cd /opt/check_winning_agent
source .venv/bin/activate
adk api_server --a2a --port 8001 remote_agent
```

In another terminal (or from your local machine) test the agent card:

```bash
curl -sS http://localhost:8001/a2a/check_winning_agent/.well-known/agent-card.json | python3 -m json.tool
```

You should see the agent card JSON. Press `Ctrl+C` to stop the server.

---

## 7. Create a systemd Service

This ensures the agent starts automatically and restarts on failure.

```bash
cat > /etc/systemd/system/check-winning-agent.service << 'EOF'
[Unit]
Description=Check Winning Agent (ADK A2A Server)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/check_winning_agent
Environment="PATH=/opt/check_winning_agent/.venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=/opt/check_winning_agent/remote_agent/.env
ExecStart=/opt/check_winning_agent/.venv/bin/adk api_server --a2a --port 8001 remote_agent
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```
There is configuration and scrypt file which can store logs
**check_winning_agent.service**
**start_again.sh**
Enable and start the service:

```bash
systemctl daemon-reload
systemctl enable check-winning-agent
systemctl start check-winning-agent
```

Restarting and checking services
```bash
systemctl stop check-winning-agent
systemctl daemon-reload
systemctl restart check-winning-agent
systemctl status check-winning-agent --no-pager
ls -lah /opt/.logs
tail /opt/.logs/agent_*.log
```
Verify it's running:

```bash
systemctl status check-winning-agent
journalctl -u check-winning-agent -f --no-pager
```

Test locally on the VM:

```bash
curl -sS http://127.0.0.1:8001/a2a/check_winning_agent/.well-known/agent-card.json | python3 -m json.tool
```

---

## 8. Configure Nginx as a Reverse Proxy

### 8.1 Create the Nginx site configuration

```bash
cat > /etc/nginx/sites-available/check-winning-agent << 'NGINX'
server {
    listen 80;
    server_name montecarlo.com;

    # A2A agent routes — proxy everything under /a2a/ to the ADK server
    location /a2a/ {
        proxy_pass         http://127.0.0.1:8001/a2a/;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # SSE / streaming support
        proxy_set_header   Connection        '';
        proxy_buffering    off;
        proxy_cache        off;
        chunked_transfer_encoding on;

        # Generous timeouts for long-running agent calls
        proxy_read_timeout    300s;
        proxy_connect_timeout 60s;
        proxy_send_timeout    300s;
    }
}
NGINX
```

### 8.2 Enable the site

```bash
ln -sf /etc/nginx/sites-available/check-winning-agent /etc/nginx/sites-enabled/
# Remove the default site if it conflicts
rm -f /etc/nginx/sites-enabled/default
```

### 8.3 Test and reload Nginx

```bash
nginx -t
systemctl reload nginx
```

### 8.4 Verify HTTP access

From your **local machine**:

```bash
curl -sS http://montecarlo.com/a2a/check_winning_agent/.well-known/agent-card.json | python3 -m json.tool
```

---

## 9. Enable HTTPS with Let's Encrypt (Recommended)

```bash
certbot --nginx -d montecarlo.com --non-interactive --agree-tos -m goodname@gmail.com
```

Certbot will automatically:
- Obtain an SSL certificate
- Update the Nginx configuration to listen on port 443
- Add an HTTP → HTTPS redirect

Verify auto-renewal:

```bash
certbot renew --dry-run
```

Now test with HTTPS:

```bash
curl -sS https://montecarlo.com/a2a/check_winning_agent/.well-known/agent-card.json | python3 -m json.tool
```

---

## 10. Update the Agent Card URL

After deployment, the agent is no longer on `localhost`. Update the URL in `agent.json` to reflect the production address:

```json
{
  "capabilities": {},
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["application/json"],
  "description": "Agent that handles check your luck if numbers make you winner, looser or tell probability of winning.",
  "name": "check_winning_agent",
  "skills": [
    {
      "id": "check_winning_agent",
      "name": "Check Winning Agent",
      "description": "check winning luck agent that tell if the current list of dice numbers make you winner, looser or tell probability of winning",
      "tags": ["mathematical", "computation", "numbers"]
    }
  ],
  "url": "https://montecarlo.com/a2a/check_winning_agent",
  "version": "1.0.0"
}
```

Also update the `RemoteA2aAgent` in the main agent's `agent.py` if you want the root agent to talk to the deployed remote agent:

```python
check_winning_agent = RemoteA2aAgent(
    name="check_winning_agent",
    description="Agent that handles check your luck if numbers make you winner, looser or tell probability of winning",
    agent_card=(
        f"https://montecarlo.com/a2a/check_winning_agent{AGENT_CARD_WELL_KNOWN_PATH}"
    ),
)
```

---

## 11. Test the Full A2A Flow

### Agent Card Discovery

```bash
curl -sS https://montecarlo.com/a2a/check_winning_agent/.well-known/agent-card.json | python3 -m json.tool
```


### Send an A2A Message

```bash
curl -X POST https://montecarlo.com/a2a/check_winning_agent \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Check these dice numbers: [3, 4, 5, 2]"}]
      }
    }
  }' | python3 -m json.tool
```

---

## 12. Useful Management Commands

| Action | Command |
|---|---|
| View agent logs | `journalctl -u check-winning-agent -f --no-pager` |
| Restart agent | `systemctl restart check-winning-agent` |
| Stop agent | `systemctl stop check-winning-agent` |
| Check agent status | `systemctl status check-winning-agent` |
| Reload Nginx | `systemctl reload nginx` |
| Renew SSL certificate | `certbot renew` |
| Edit environment variables | `nano /opt/check_winning_agent/remote_agent/.env && systemctl restart check-winning-agent` |

---



## Architecture Overview

```
                         Internet
                            │
                            ▼
                     ┌─────────────┐
                     │   Nginx     │  :443 (HTTPS)
                     │  (reverse   │  :80  (HTTP → redirect)
                     │   proxy)    │
                     └──────┬──────┘
                            │ proxy_pass
                            ▼
                     ┌─────────────┐
                     │  ADK A2A    │  :8001 (localhost only)
                     │  api_server │
                     │             │
                     │  check_     │
                     │  winning_   │
                     │  agent      │
                     └─────────────┘
```

**Agent Card URL:**
```
https://montecarlo.com/a2a/check_winning_agent/.well-known/agent-card.json
```

**A2A Endpoint:**
```
https://montecarlo.com/a2a/check_winning_agent
```

