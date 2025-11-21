from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# Dummy user database
users = {
    "admin": {"password": "admin123", "is_admin": True},
    "user": {"password": "user123", "is_admin": False},
}

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

# ---- Routes ----

@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user, remember=bool(request.form.get("remember")))
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.", "danger")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("login"))

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    # Example recent meetings
    recent_meetings = [
        {"meeting_name": "Melbourne Cup", "uploaded_at": "2025-11-01 12:00", "id": 1},
        {"meeting_name": "Caulfield Stakes", "uploaded_at": "2025-11-15 14:30", "id": 2},
    ]
    return render_template("dashboard.html", recent_meetings=recent_meetings)

@app.route("/history")
@login_required
def history():
    # Example history
    recent_analyses = [
        {"meeting_name": "Melbourne Cup", "uploaded_at": "2025-11-01 12:00", "id": 1},
        {"meeting_name": "Caulfield Stakes", "uploaded_at": "2025-11-15 14:30", "id": 2},
    ]
    return render_template("history.html", recent_analyses=recent_analyses)

@app.route("/admin")
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))
    return render_template("admin.html")

@app.route("/analyze", methods=["POST"])
@login_required
def analyze():
    file = request.files.get("csv_file")
    if not file:
        flash("Please upload a CSV file.", "danger")
        return redirect(url_for("dashboard"))
    # Here you would process the CSV
    flash(f"Analyzed {file.filename} successfully!", "success")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
