from flask import Flask, request, jsonify
import docker
import json
import traceback

app = Flask(__name__)

# docker client using socket (requires /var/run/docker.sock mounted)
client = docker.from_env()

def safe_restart_nginx():
    try:
        c = client.containers.get("nginx")
        print("Restarting nginx container...")
        c.restart(timeout=10)
        print("nginx restarted")
        return True, "nginx restarted"
    except Exception as e:
        print("Error restarting nginx:", e)
        return False, str(e)

def stop_stress_containers():
    stopped = []
    try:
        for c in client.containers.list():
            # common names we used: cpu-stress, stress, stress-ng
            if any(x in (c.name or "").lower() for x in ["stress", "cpu-stress"]):
                print("Stopping stress container:", c.name)
                c.stop()
                stopped.append(c.name)
        return True, stopped
    except Exception as e:
        print("Error stopping stress containers:", e)
        return False, str(e)


@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    print("==== Received alert ====")
    print(json.dumps(data, indent=2) if data else "no payload")
    acted = []

    alerts = data.get("alerts", []) if isinstance(data, dict) else []
    for a in alerts:
        labels = a.get("labels", {})
        alertname = labels.get("alertname", "")
        status = a.get("status", "")  # firing / resolved
        print("Alert:", alertname, "status:", status)

        if alertname == "NginxDown" and status == "firing":
            ok, info = safe_restart_nginx()
            acted.append({"action": "restart_nginx", "ok": ok, "info": info})

        if alertname == "HighCPUUsage" and status == "firing":
            ok, info = stop_stress_containers()
            acted.append({"action": "stop_stress", "ok": ok, "info": info})

    return jsonify({"status": "ok", "acted": acted}), 200


@app.route('/', methods=['GET'])
def index():
    return jsonify({"msg": "ansible-handler running"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
