import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ===== Flask-Login Setup =====
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Fake user DB
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

users = {'admin': User(1, 'admin')}  # Example single user

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if str(user.id) == str(user_id):
            return user
    return None

# Fake DB for meetings
meetings = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===== Routes =====

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html', recent_meetings=reversed(meetings), current_user=current_user)

@app.route('/history')
@login_required
def history():
    return render_template('history.html', meetings=reversed(meetings), current_user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        # In real app, validate password here
        user = users.get(username)
        if user:
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.')
    return redirect(url_for('login'))

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    if 'csv_file' not in request.files:
        flash('No file part')
        return redirect(url_for('dashboard'))
    file = request.files['csv_file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('dashboard'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        track_condition = request.form.get('track_condition', 'good')
        advanced_mode = 'advanced_mode' in request.form

        # Run Node.js analysis
        try:
            cmd = ['node', 'analyze.js', filepath, track_condition]
            if advanced_mode:
                cmd.append('--advanced')
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            analysis_result = result.stdout
        except subprocess.CalledProcessError as e:
            flash(f'Analysis failed: {e.stderr}')
            return redirect(url_for('dashboard'))

        # Save meeting
        meeting = {
            'id': len(meetings) + 1,
            'meeting_name': filename,
            'uploaded_at': datetime.now(),
            'results': analysis_result,
            'user': current_user.username
        }
        meetings.append(meeting)

        return redirect(url_for('view_meeting', meeting_id=meeting['id']))
    else:
        flash('Invalid file type')
        return redirect(url_for('dashboard'))

@app.route('/meeting/<int:meeting_id>')
@login_required
def view_meeting(meeting_id):
    meeting = next((m for m in meetings if m['id'] == meeting_id), None)
    if not meeting:
        flash('Meeting not found')
        return redirect(url_for('dashboard'))
    return render_template('meeting.html', meeting=meeting, results={'races': []}, current_user=current_user)

# ===== Run App =====
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
