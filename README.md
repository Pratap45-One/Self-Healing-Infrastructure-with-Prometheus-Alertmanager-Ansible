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
1. Extract the ZIP to a folder, e.g. `C:\Users\prata\Downloads\self_healing_infra`
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

