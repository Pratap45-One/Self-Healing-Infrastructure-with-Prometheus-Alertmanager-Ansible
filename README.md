Self-Healing Infrastructure (Windows Demo)

This project shows how to automatically detect and fix service failures using:
- Prometheus → monitors services
- Alertmanager → sends alerts
- Flask (Python) → receives alerts
- Ansible / Docker CLI → restarts the service

What It Does:
- Runs an NGINX web server in Docker.
- Prometheus checks if it’s running.
- If NGINX stops, Alertmanager sends an alert to Flask.
- Flask triggers an Ansible playbook (or Docker command) to restart NGINX automatically.

It’s a simple demo of auto-recovery (self-healing) infrastructure.

Requirements:
- Windows with Docker Desktop (WSL2 enabled)
- Python 3.8+
- (Optional) WSL + Ansible for advanced recovery

Setup Steps:
1. Start containers:
   docker-compose up -d

2. Setup Python environment:
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt

3. Run Flask server:
   python server.py

4. Check UIs:
   Prometheus → http://localhost:9090
   Alertmanager → http://localhost:9093

Test Auto-Healing:
Stop the NGINX container:
   docker stop nginx_service
Within a few seconds, it should restart automatically — Flask logs this in server.log.

File Overview:
- docker-compose.yml → Starts NGINX, Prometheus & Alertmanager
- prometheus/ → Prometheus config & alert rules
- alertmanager/config.yml → Webhook setup for alerts
- ansible/restart_server.yml → Playbook to restart NGINX
- server.py → Flask app handling alerts
- requirements.txt → Python dependencies

Troubleshooting:
- Make sure Docker Desktop and WSL2 are running.
- Check server.log for recovery logs.
- If Flask doesn’t get alerts, update Alertmanager config to use:
  http://host.docker.internal:5001/restart

Summary:
This demo automatically detects and recovers from service failures using open-source DevOps tools.
It’s a hands-on example of self-healing systems in modern infrastructure.
