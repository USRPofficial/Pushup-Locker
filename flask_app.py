from flask import Flask, render_template, request, jsonify
import json, os, time

app = Flask(__name__)

DATA_FILE = "data.json"
PUSHUP_GOAL = 50
EMERGENCY_SECONDS = 15 * 60


def load_state():
    if not os.path.exists(DATA_FILE):
        return {"done": 0, "emergency_until": 0}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_state(state):
    with open(DATA_FILE, "w") as f:
        json.dump(state, f)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status")
def status():
    state = load_state()
    now = time.time()
    remaining = max(PUSHUP_GOAL - state.get("done", 0), 0)
    emergency_until = state.get("emergency_until", 0)
    emergency = now < emergency_until
    time_left = int(emergency_until - now) if emergency else 0
    return jsonify({
        "remaining": remaining,
        "emergency": emergency,
        "time_left": time_left
    })


@app.route("/log_pushups", methods=["POST"])
def log_pushups():
    state = load_state()
    amount = int(request.form.get("amount", 0))
    state["done"] = state.get("done", 0) + amount
    save_state(state)
    return ("<p>Logged! <a href='/'>Back</a></p>")


@app.route("/start_emergency", methods=["POST"])
def start_emergency():
    state = load_state()
    state["emergency_until"] = time.time() + EMERGENCY_SECONDS
    save_state(state)
    return ("<p>Emergency started! <a href='/'>Back</a></p>")


PASSCODE = "1234"

@app.route("/extend_emergency", methods=["POST"])
def extend_emergency():
    code = request.form.get("code", "")
    if code != PASSCODE:
        return jsonify({"ok": False})
    state = load_state()
    state["emergency_until"] = time.time() + EMERGENCY_SECONDS
    save_state(state)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
