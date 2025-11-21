from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = "supersecretkey"

# --- Flask-Login setup ---
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# In-memory user store for demo purposes
USERS = {
    "admin": {"password": "password", "is_admin": True},
    "user": {"password": "password", "is_admin": False}
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username
        self.is_admin = USERS[username]["is_admin"]

@login_manager.user_loader
def load_user(user_id):
    if user_id in USERS:
        return User(user_id)
    return None

# --- Routes ---
@app.route("/")
def index():
    return redirect(url_for("dashboard"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = USERS.get(username)
        if user and user["password"] == password:
            login_user(User(username))
            flash("Logged in successfully!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully!", "success")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    # Example: recent_meetings can be empty list for now
    recent_meetings = []
    return render_template("dashboard.html", recent_meetings=recent_meetings)

if __name__ == "__main__":
    app.run(debug=True)
