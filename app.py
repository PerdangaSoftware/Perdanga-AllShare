import os
import shutil
import threading
from datetime import timedelta
from flask import Flask, request, render_template, send_from_directory, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Security & Session Configuration
ADMIN_PIN = os.getenv("ADMIN_PIN", "8159")
app.secret_key = os.getenv("SECRET_KEY", "perdanga-allshare-secure-salt-key-9921")
app.permanent_session_lifetime = timedelta(days=7)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
TEMP_FOLDER = os.path.join(BASE_DIR, 'temp')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

assembly_lock = threading.Lock()
completed_chunks_map = {}

def is_authenticated():
    return session.get('authenticated') is True

def is_safe_path(base_dir, target_path):
    resolved_base = os.path.abspath(base_dir)
    resolved_target = os.path.abspath(target_path)
    return os.path.commonpath([resolved_base]) == os.path.commonpath([resolved_base, resolved_target])

def get_file_size_formatted(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

@app.route('/', methods=['GET'])
def index():
    if not is_authenticated():
        return render_template('index.html', authenticated=False, files=[])

    files_info = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for filename in sorted(os.listdir(app.config['UPLOAD_FOLDER'])):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                files_info.append({
                    'name': filename,
                    'size': get_file_size_formatted(size)
                })
    return render_template('index.html', authenticated=True, files=files_info)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    submitted_pin = str(data.get('pin', '')).strip()

    if submitted_pin == ADMIN_PIN:
        session.permanent = True
        session['authenticated'] = True
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid PIN'}), 403

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('authenticated', None)
    return redirect(url_for('index'))

@app.route('/check-file', methods=['POST'])
def check_file():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    raw_filename = data.get('filename', '')
    if not raw_filename:
        return jsonify({'error': 'Filename missing'}), 400

    filename = secure_filename(raw_filename)
    target_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if os.path.exists(target_path):
        return jsonify({'exists': True, 'filename': filename})
    return jsonify({'exists': False, 'filename': filename})

@app.route('/upload-chunk', methods=['POST'])
def upload_chunk():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    file = request.files.get('file')
    raw_filename = request.form.get('filename', '')
    filename = secure_filename(raw_filename)

    try:
        chunk_index = int(request.form.get('chunkIndex', -1))
        total_chunks = int(request.form.get('totalChunks', -1))
    except ValueError:
        return jsonify({'error': 'Invalid parameters'}), 400

    if not file or not filename or chunk_index < 0 or total_chunks <= 0:
        return jsonify({'error': 'Malformed request'}), 400

    final_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if chunk_index == 0 and os.path.exists(final_path):
        return jsonify({'error': 'File already exists'}), 409

    chunk_filename = f"{filename}_part_{chunk_index}"
    chunk_file_path = os.path.join(app.config['TEMP_FOLDER'], chunk_filename)

    if not is_safe_path(app.config['TEMP_FOLDER'], chunk_file_path):
        return jsonify({'error': 'Forbidden target'}), 403

    file.save(chunk_file_path)

    with assembly_lock:
        if filename not in completed_chunks_map:
            completed_chunks_map[filename] = set()
        
        completed_chunks_map[filename].add(chunk_index)
        is_ready = (len(completed_chunks_map[filename]) == total_chunks)

    if is_ready:
        if not is_safe_path(app.config['UPLOAD_FOLDER'], final_path):
            return jsonify({'error': 'Forbidden target'}), 403

        if os.path.exists(final_path):
            return jsonify({'error': 'File already exists'}), 409

        with open(final_path, 'wb') as target_file:
            for i in range(total_chunks):
                part_path = os.path.join(app.config['TEMP_FOLDER'], f"{filename}_part_{i}")
                if os.path.exists(part_path):
                    with open(part_path, 'rb') as source_file:
                        shutil.copyfileobj(source_file, target_file, 1024 * 1024 * 16)
                    os.remove(part_path)

        with assembly_lock:
            completed_chunks_map.pop(filename, None)

        return jsonify({'completed': True})

    return jsonify({'completed': False})

@app.route('/download/<path:filename>')
def download_file(filename):
    if not is_authenticated():
        return "Unauthorized", 401

    safe_name = secure_filename(filename)
    target_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)

    if not is_safe_path(app.config['UPLOAD_FOLDER'], target_path) or not os.path.isfile(target_path):
        return "File not found or access denied", 404

    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_name, as_attachment=True)

# Delete file without PIN requirement (already protected by session)
@app.route('/delete-file', methods=['POST'])
def delete_file():
    if not is_authenticated():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    raw_filename = data.get('filename', '')

    safe_name = secure_filename(raw_filename)
    target_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)

    if not is_safe_path(app.config['UPLOAD_FOLDER'], target_path) or not os.path.isfile(target_path):
        return jsonify({'error': 'File not found'}), 404

    try:
        os.remove(target_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)