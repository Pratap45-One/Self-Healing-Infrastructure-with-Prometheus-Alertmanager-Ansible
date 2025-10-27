## Self-Healing Infrastructure (demo)

This repository contains a small proof-of-concept for a self-healing workflow using Prometheus + Alertmanager to detect failures and a webhook service (Flask) to perform automated recovery actions. Recovery is attempted via an Ansible playbook (running inside WSL) and falls back to Docker CLI actions if Ansible isn't available.

The demo runs the following components (see `docker-compose.yml`):

- an `nginx` service (named `nginx_service`)
- Prometheus (scrapes targets and evaluates alert rules)
- Alertmanager (routes alerts to the webhook)

The webhook receiver is implemented in `server.py`. It listens for POSTs at `/restart` (default port 5001) and will try to run `ansible/restart_server.yml` inside WSL; if that fails it will attempt to `docker start` or `docker run` the container.

## Quick facts / contract

- Webhook endpoint: POST http://<host>:5001/restart
- Flask default port: 5001 (can be changed via PORT env var)
- Recovery target container name: `nginx_service`

## Repository layout

- `docker-compose.yml` — brings up `nginx_service`, Prometheus and Alertmanager
- `prometheus/` — Prometheus configuration and alerting rules
- `alertmanager/config.yml` — Alertmanager config (webhook receiver configured)
- `ansible/restart_server.yml` — Ansible playbook that restarts the service (used when WSL+Ansible present)
- `server.py` — Flask webhook that receives alerts and triggers recovery
- `requirements.txt` — Python dependencies for the webhook

## Prerequisites

- Docker Desktop (Windows) with WSL2 enabled (recommended)
- Python 3.8+ (for running the webhook on the host)
- (Optional) WSL2 with Ansible installed if you prefer Ansible-based recovery

If you want to use Ansible inside WSL, install WSL and Ansible (example):

1. Install WSL (PowerShell as admin):

```powershell
wsl --install -d Ubuntu-22.04
```

2. Inside the WSL distro (Ubuntu):

```bash
sudo apt update && sudo apt install -y ansible python3-pip docker.io
```

3. (Optional) Install any required Ansible collections, for example:

```bash
ansible-galaxy collection install community.docker
```

## Quickstart (Windows PowerShell)

1. In the project folder, start the containers:

```powershell
docker-compose up -d
```

2. Prepare a Python virtual environment and install dependencies:

```powershell
python -m venv venv
.\\venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

3. Run the webhook service (keeps running in the foreground):

```powershell
# run with default port 5001
python server.py
```

4. Open the UIs to inspect metrics and alerts:

- Prometheus: http://localhost:9090
- Alertmanager: http://localhost:9093

5. To simulate a failure, stop the nginx container:

```powershell
docker stop nginx_service
```

Prometheus/Alertmanager (with the included rule/config) should fire and Alertmanager will POST the alert to `http://host.docker.internal:5001/restart`. The webhook will log the payload to `server.log` and attempt recovery.

## How the webhook performs recovery

1. server.py receives the alert at `/restart` and logs the payload to `server.log`.
2. It first tries to run the Ansible playbook via WSL:
   - `wsl ansible-playbook /mnt/c/.../ansible/restart_server.yml`
3. If Ansible fails or is not available, it tries Docker commands:
   - `docker start nginx_service` — if the container exists but is stopped
   - otherwise `docker run -d --name nginx_service -p 8080:80 nginx:stable`

Return codes reflect success (HTTP 200) or failure (HTTP 500).

## Testing the webhook manually

You can POST to the webhook directly to test recovery without involving Prometheus/Alertmanager:

PowerShell example (simple JSON payload):

```powershell
$body = '{"alert":"test"}'
Invoke-RestMethod -Method Post -Uri http://localhost:5001/restart -Body $body -ContentType 'application/json'
```

Check `server.log` (in the repo folder) or the webhook console output for details.

## Troubleshooting

- If the webhook doesn't receive alerts from Alertmanager, confirm Alertmanager's `alertmanager/config.yml` uses `host.docker.internal:5001/restart` (or adjust for your environment).
- If Ansible fails, ensure WSL is installed and `ansible-playbook` works inside your WSL distro. The code converts Windows paths to WSL paths automatically.
- If Docker commands fail, ensure Docker CLI is in PATH for the user running the webhook (on Windows this is usually the case when Docker Desktop is installed).
- Inspect `server.log` for detailed stdout/stderr output captured by the webhook.

## Next steps and improvements

- Add unit tests for the webhook behavior and small integration tests that exercise the fallback paths.
- Harden the Ansible playbook (idempotency, timeouts, more robust checks).
- Secure the webhook endpoint (authentication, mTLS) before using in production.

## License & Contact

This is a small demo repo. Adapt and reuse as you like. For questions, open an issue in the repository.
# Self-Healing Infrastructure - Windows package

This package provides a ready-to-run self-healing demo using Docker Desktop on Windows.
It uses Prometheus to monitor an NGINX container, Alertmanager to route alerts, a Flask webhook to receive alerts, and Ansible (optional, via WSL) or Docker CLI to restart the service automatically.

## Prerequisites (Windows)
- Docker Desktop (with WSL2 integration enabled)
- Python 3 installed on Windows (for Flask)
- (Optional) WSL2 with Ansible installed if you want Ansible to be used:
  - Install WSL: `wsl --install -d Ubuntu-22.04`
  - Inside WSL: `sudo apt update && sudo apt install -y ansible python3-pip docker.io`
  - Install Ansible collections if needed: `ansible-galaxy collection install community.docker`

## Files included
- `docker-compose.yml` - starts nginx_service, prometheus and alertmanager
- `prometheus/` - Prometheus config and alert rules
- `alertmanager/config.yml` - routes alerts to webhook at `host.docker.internal:5001/restart`
- `ansible/restart_server.yml` - playbook to restart container (used if Ansible is available in WSL)
- `server.py` - Flask webhook that receives alerts and triggers recovery
- `requirements.txt` - Python requirements for Flask
- `README.md` - this file

## Usage (Windows)
1. Extract the ZIP to a folder, 
2. Start Docker Desktop and ensure WSL integration is enabled
3. Open PowerShell in the extracted folder
   ```powershell
   docker-compose up -d
   ```
4. Create and activate Python venv, install requirements:
   ```powershell
   python -m venv venv
   .\\venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
5. Run the Flask webhook (keep this terminal open):
   ```powershell
   python server.py
   ```
6. Open Prometheus UI: http://localhost:9090 and Alertmanager: http://localhost:9093
7. Simulate a failure (stop nginx):
   ```powershell
   docker stop nginx_service
   ```
8. Watch `server.log` or Flask console — recovery should run and `nginx_service` should be started automatically.

## Notes
- Alertmanager is configured to send webhooks to `http://host.docker.internal:5001/restart` so the containerized services reach the Flask application running on the Windows host.
- The Flask server attempts to run the Ansible playbook inside WSL first. If that fails (Ansible/WSL not available), it falls back to using the Docker CLI to start/recreate the container.

