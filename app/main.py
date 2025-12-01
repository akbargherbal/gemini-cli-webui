"""
GCLI Web UI - Main Flask Application

Phase 2: Minimal Flask ↔ GCLI Proof-of-Concept
TODO: Implement routes and GCLI integration
"""

from flask import Flask, render_template, request, jsonify
import subprocess
import os
import json

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-me')


@app.route('/')
def index():
    """Serve minimal HTML form"""
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask_gcli():
    """
    Send prompt to GCLI, wait for complete response
    Phase 2: Basic implementation
    """
    # TODO: Implement GCLI subprocess integration
    return jsonify({
        'response': 'Not implemented yet',
        'success': False,
        'error': 'Phase 2 implementation pending'
    })


def is_safe_directory(path: str) -> bool:
    """
    Validate directory is safe to run GCLI in
    
    Args:
        path: Directory path to validate
    
    Returns:
        True if directory is safe, False otherwise
    """
    abs_path = os.path.abspath(path)
    
    # Blacklist system directories
    forbidden = ['/bin', '/usr', '/etc', '/var', '/sys', '/proc', '/']
    for forbidden_path in forbidden:
        if abs_path.startswith(forbidden_path):
            return False
    
    # Whitelist: Must be under home directory
    home = os.path.expanduser('~')
    return abs_path.startswith(home)


if __name__ == '__main__':
    port = int(os.environ.get('GCLI_WEBUI_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=debug
    )
