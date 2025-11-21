from flask import Flask, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import subprocess
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
meetings = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp3', 'wav', 'mp4'}

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        track_condition = request.form.get('track_condition', 'good')
        advanced_mode = 'advanced_mode' in request.form

        try:
            cmd = ['node', 'analyze.js', filepath, track_condition]
            if advanced_mode:
                cmd.append('--advanced')

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            analysis_result = result.stdout

        except subprocess.CalledProcessError as e:
            flash(f'Analysis failed: {e.stderr}', 'danger')
            return redirect(url_for('dashboard'))

        meeting = {
            'id': len(meetings) + 1,
            'meeting_name': filename,
            'uploaded_at': datetime.now(),
            'results': analysis_result
        }
        meetings.append(meeting)

        return redirect(url_for('view_meeting', meeting_id=meeting['id']))

    else:
        flash('Invalid file type or no file uploaded.', 'warning')
        return redirect(url_for('dashboard'))
