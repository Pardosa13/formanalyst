from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Example users
users = {
    "admin": {"password": "password123", "is_admin": True},
    "user": {"password": "userpass", "is_admin": False},
}

# Dummy meetings data
dummy_meetings = [
    {"id": 1, "meeting_name": "Race 1", "uploaded_at": datetime.now(), "user": {"username": "admin"}},
    {"id": 2, "meeting_name": "Race 2", "uploaded_at": datetime.now(), "user": {"username": "user"}}
]

# User class
class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username
        self.is_admin = users[username]["is_admin"]

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id)
    return None

# Routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user, remember=("remember" in request.form))
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    # For simplicity, show all meetings for everyone
    recent_meetings = dummy_meetings
    return render_template("dashboard.html", recent_meetings=recent_meetings)

@app.route("/history")
@login_required
def history():
    meetings = dummy_meetings
    return render_template("history.html", meetings=meetings)

@app.route("/view_meeting/<int:meeting_id>")
@login_required
def view_meeting(meeting_id):
    meeting = next((m for m in dummy_meetings if m["id"] == meeting_id), None)
    if not meeting:
        flash("Meeting not found", "danger")
        return redirect(url_for("dashboard"))
    return f"Showing results for {meeting['meeting_name']}"  # Replace with your actual results page

if __name__ == "__main__":
    app.run(debug=True)
