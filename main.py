import os
import hashlib
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

def compute_hash(file_path, chunk_size=8192):
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (PermissionError, OSError):
        return None

def find_duplicates(directory):
    hashes = {}
    duplicates = {}
    if not os.path.isdir(directory):
        return duplicates

    for root, _, files in os.walk(directory):
        for file in files:
            full_path = os.path.join(root, file)
            file_hash = compute_hash(full_path)
            if not file_hash:
                continue
            if file_hash in hashes:
                if file_hash not in duplicates:
                    duplicates[file_hash] = [hashes[file_hash]]
                duplicates[file_hash].append(full_path)
            else:
                hashes[file_hash] = full_path
    return duplicates

TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Duplicate File Finder</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f6f9; margin: 0; padding: 40px; color: #333; }
        .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        h1 { margin-top: 0; color: #2c3e50; }
        form { display: flex; gap: 10px; margin-bottom: 30px; }
        input[type="text"] { flex: 1; padding: 10px 14px; border: 1px solid #ccd1d9; border-radius: 4px; font-size: 16px; }
        button { padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; font-size: 16px; cursor: pointer; }
        button:hover { background: #2980b9; }
        .duplicate-group { background: #fafbfc; border: 1px solid #e1e4e8; border-radius: 6px; padding: 15px; margin-bottom: 15px; }
        .duplicate-group h3 { margin: 0 0 10px 0; font-size: 14px; color: #e74c3c; }
        ul { margin: 0; padding-left: 20px; }
        li { margin-bottom: 5px; word-break: break-all; font-family: monospace; font-size: 13px; }
        .actions { margin-top: 8px; }
        .btn-delete { background: #e74c3c; padding: 4px 8px; font-size: 12px; border-radius: 3px; }
        .btn-delete:hover { background: #c0392b; }
        .empty { color: #7f8c8d; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Duplicate File Finder</h1>
        <form method="POST">
            <input type="text" name="directory" placeholder="Enter absolute path to scan (e.g., /path/to/folder)" value="{{ directory or '' }}" required>
            <button type="submit">Scan Directory</button>
        </form>

        {% if duplicates is not none %}
            <h2>Scan Results</h2>
            {% if duplicates %}
                <p>Found {{ duplicates|length }} group(s) of duplicate files.</p>
                {% for file_hash, paths in duplicates.items() %}
                    <div class="duplicate-group" id="group-{{ loop.index }}">
                        <h3>Hash: {{ file_hash }}</h3>
                        <ul>
                            {% for path in paths %}
                                <li id="item-{{ loop.index0 }}">
                                    {{ path }}
                                    <button class="btn-delete" onclick="deleteFile('{{ path }}', 'group-{{ loop.index }}')">Delete</button>
                                </li>
                            {% endfor %}
                        </ul>
                    </div>
                {% endfor %}
            {% else %}
                <p class="empty">No duplicate files found in the specified directory.</p>
            {% endif %}
        {% endif %}
    </div>

    <script>
        function deleteFile(path, groupId) {
            if (!confirm('Are you sure you want to delete:\n' + path)) return;
            fetch('/delete', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({path: path})
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('File deleted successfully.');
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            });
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])

def index():
    duplicates = None
    directory = None
    if request.method == 'POST':
        directory = request.form.get('directory')
        duplicates = find_duplicates(directory)
    return render_template_string(TEMPLATE, duplicates=duplicates, directory=directory)

@app.route('/delete', methods=['POST'])
def delete_file():
    data = request.get_json()
    path = data.get('path') if data else None
    if not path or not os.path.exists(path):
        return jsonify({'success': False, 'error': 'File not found.'}), 404
    try:
        os.remove(path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
