from flask import Flask, render_template, request, jsonify
import json, os, time
from werkzeug.security import generate_password_hash, check_password_hash

from models import User
from flask_login import LoginManager


# --- NEW IMPORTS FOR DATABASE ---
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from models import Base  # imports User + PushupLog models

# --------------------------------

app = Flask(__name__)

# --- DATABASE SETUP (Step 5) ---
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///local.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = scoped_session(sessionmaker(bind=engine))

# --- LOGIN MANAGER SETUP (Step 6B) ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # route name we'll create later

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    return db.query(User).get(int(user_id))


# Create tables if they don't exist yet
Base.metadata.create_all(engine)

@app.teardown_appcontext
def remove_session(exception=None):
    SessionLocal.remove()
# --------------------------------


# --- EXISTING JSON SYSTEM (still active for now) ---
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
# ---------------------------------------------------


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

# --- SIGNUP ROUTE ---
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        db = SessionLocal()

        # Check if username or email already exists
        if db.query(User).filter_by(username=username).first():
            return "Username already taken"
        if db.query(User).filter_by(email=email).first():
            return "Email already registered"

        # Create user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.add(new_user)
        db.commit()

        return "<p>Account created! <a href='/login'>Log in</a></p>"

    return render_template("signup.html")

# --- LOGIN ROUTE ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = SessionLocal()
        user = db.query(User).filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            return "Invalid username or password"

        from flask_login import login_user
        login_user(user)

        return "<p>Logged in! <a href='/'>Go home</a></p>"

    return render_template("login.html")




if __name__ == "__main__":
    app.run(debug=True)
