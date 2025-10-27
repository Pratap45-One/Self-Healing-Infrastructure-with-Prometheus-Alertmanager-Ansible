#!/usr/bin/env python3
from flask import Flask, request
import subprocess, logging, os, json, time

app = Flask(__name__)
logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s %(message)s')

CONTAINER_NAME = "nginx_service"
ANSIBLE_PLAYBOOK = "ansible/restart_server.yml"

def winpath_to_wsl(p):
    # Convert Windows path like C:\path\to\dir to /mnt/c/path/to/dir
    p = os.path.abspath(p)
    if os.name == 'nt':
        drive = p[0].lower()
        rest = p[2:].replace('\\', '/')
        return f"/mnt/{drive}/{rest}"
    return p

def run_ansible_playbook():
    try:
        # Try running ansible-playbook inside WSL (assumes WSL + Ansible installed)
        cwd = os.getcwd()
        wsl_playbook = winpath_to_wsl(os.path.join(cwd, ANSIBLE_PLAYBOOK))
        cmd = ["wsl", "ansible-playbook", wsl_playbook]
        logging.info("Running Ansible: %s", " ".join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        logging.info("Ansible stdout: %s", r.stdout.strip())
        logging.info("Ansible stderr: %s", r.stderr.strip())
        return r.returncode == 0
    except Exception as e:
        logging.exception("Ansible run failed: %s", e)
        return False

def docker_restart_container():
    try:
        # Try to start the container; if not present, run it
        cmd = ["docker", "start", CONTAINER_NAME]
        logging.info("Running Docker start: %s", " ".join(cmd))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            logging.info("Docker start succeeded: %s", r.stdout.strip())
            return True
        # If start failed, try run
        cmd2 = ["docker", "run", "-d", "--name", CONTAINER_NAME, "-p", "8080:80", "nginx:stable"]
        logging.info("Running Docker run: %s", " ".join(cmd2))
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=60)
        if r2.returncode == 0:
            logging.info("Docker run succeeded: %s", r2.stdout.strip())
            return True
        logging.error("Docker commands failed: %s %s", r.stdout.strip(), r2.stdout.strip())
        return False
    except Exception as e:
        logging.exception("Docker restart failed: %s", e)
        return False

@app.route('/restart', methods=['POST'])
def restart():
    payload = request.get_json(silent=True)
    logging.info("Received alert payload: %s", json.dumps(payload) if payload else "no json")
    # Try Ansible first, then docker fallback
    ok = run_ansible_playbook()
    if not ok:
        logging.info("Ansible failed or unavailable — attempting Docker restart")
        ok = docker_restart_container()
    if ok:
        msg = "Recovery action executed successfully"
        logging.info(msg)
        return msg, 200
    else:
        msg = "Recovery action failed"
        logging.error(msg)
        return msg, 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
