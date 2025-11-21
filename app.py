from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import models and blueprints
from models import db, User, Meeting, Race, Horse, Prediction
from auth import auth_bp, admin_required
from analyzer import process_csv_and_analyze, get_meeting_results

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # Railway Postgres URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ===== MAIN ROUTES =====
@app.route('/')
def index():
    return redirect(url_for('dashboard')) if current_user.is_authenticated else redirect(url_for('auth.login'))

@app.route('/dashboard')
@login_required
def dashboard():
    recent_meetings = Meeting.query.filter_by(user_id=current_user.id).order_by(Meeting.uploaded_at.desc()).limit(10).all()
    return render_template('dashboard.html', recent_meetings=recent_meetings)

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    file = request.files.get('csv_file')
    if not file or file.filename == '' or not file.filename.endswith('.csv'):
        flash('Please upload a valid CSV file', 'danger')
        return redirect(url_for('dashboard'))

    track_condition = request.form.get('track_condition', 'good')
    is_advanced = request.form.get('advanced_mode') == 'on'

    filename = secure_filename(file.filename)
    result = process_csv_and_analyze(file, filename, track_condition, current_user.id, is_advanced)
    flash(f'Analysis complete for {result["meeting_name"]}!', 'success')
    return redirect(url_for('view_meeting', meeting_id=result['meeting_id']))

@app.route('/meeting/<int:meeting_id>')
@login_required
def view_meeting(meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    if meeting.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view this meeting', 'danger')
        return redirect(url_for('dashboard'))
    results = get_meeting_results(meeting_id)
    return render_template('meeting.html', meeting=meeting, results=results)

@app.route('/history')
@login_required
def history():
    meetings = Meeting.query.order_by(Meeting.uploaded_at.desc()).all() if current_user.is_admin else Meeting.query.filter_by(user_id=current_user.id).order_by(Meeting.uploaded_at.desc()).all()
    return render_template('history.html', meetings=meetings)

# ===== ADMIN ROUTES =====
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.order_by(User.created_at.desc()).all()
    stats = {
        'total_users': len(users),
        'active_users': len([u for u in users if u.is_active]),
        'total_meetings': Meeting.query.count(),
        'total_analyses': Prediction.query.count()
    }
    return render_template('admin.html', users=users, stats=stats)

@app.route('/admin/create_user', methods=['POST'])
@login_required
@admin_required
def create_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    is_admin = request.form.get('is_admin') == 'on'

    if not username or not email or not password:
        flash('All fields are required', 'danger')
        return redirect(url_for('admin_panel'))

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        flash('Username or email already exists', 'danger')
        return redirect(url_for('admin_panel'))

    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f'User "{username}" created successfully!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/toggle_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot disable your own account', 'danger')
        return redirect(url_for('admin_panel'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User "{user.username}" has been {"enabled" if user.is_active else "disabled"}', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin_panel'))
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.username}" has been deleted', 'success')
    return redirect(url_for('admin_panel'))

# ===== ERROR HANDLERS =====
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ===== DATABASE INITIALIZATION =====
def init_db():
    with app.app_context():
        db.create_all()
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@theformanalyst.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'changeme123')

        admin = User.query.filter_by(username=admin_username).first()
        if not admin:
            admin = User(username=admin_username, email=admin_email, is_admin=True)
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f'Admin user created: {admin_username}')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
