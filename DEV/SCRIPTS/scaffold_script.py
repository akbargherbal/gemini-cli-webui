#!/usr/bin/env python3
"""
GCLI Web UI Project Scaffolding Script

Creates the complete directory structure and initial files
according to the phased implementation plan.

Usage:
    python scaffold.py [--dry-run]
"""

import os
import sys
from pathlib import Path
from typing import Dict, List


class ProjectScaffolder:
    """Scaffolds the GCLI Web UI project structure"""

    def __init__(self, root_dir: Path, dry_run: bool = False):
        self.root = root_dir
        self.dry_run = dry_run
        self.created_files: List[Path] = []
        self.created_dirs: List[Path] = []

    def scaffold(self):
        """Execute complete scaffolding process"""
        print("=" * 60)
        print("GCLI Web UI Project Scaffolder")
        print("=" * 60)
        print()

        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be created")
            print()

        # Create directory structure
        self._create_directories()

        # Create configuration files
        self._create_config_files()

        # Create app structure
        self._create_app_files()

        # Create test structure
        self._create_test_files()

        # Create documentation
        self._create_docs()

        # Create shell wrapper
        self._create_wrapper_script()

        # Print summary
        self._print_summary()

    def _create_directories(self):
        """Create project directory structure"""
        print("📁 Creating directory structure...")

        dirs = [
            "app",
            "app/templates",
            "app/static",
            "app/static/css",
            "app/static/js",
            "tests",
            "tests/unit",
            "tests/integration",
            "docs",
            "logs",
            "bin",
        ]

        for dir_path in dirs:
            self._mkdir(self.root / dir_path)

        print()

    def _create_config_files(self):
        """Create configuration and dependency files"""
        print("⚙️  Creating configuration files...")

        # requirements.txt
        self._write_file(
            self.root / "requirements.txt",
            """Flask==3.0.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-cov==4.1.0
pytest-flask==1.3.0
""",
        )

        # requirements-dev.txt
        self._write_file(
            self.root / "requirements-dev.txt",
            """black==23.12.1
flake8==7.0.0
mypy==1.8.0
""",
        )

        # .gitignore
        self._write_file(
            self.root / ".gitignore",
            """
# Ignore personal source code (not shared)
sources/

# Deprecated output directory (Phase 1-5)
output/

# =====================================
# Keep these (explicitly tracked)
# =====================================
!build/
!build/**/*
!snippets/
!snippets/**/*

# =====================================
# Python
# =====================================
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.py.class

# Virtual environments
.venv/
venv/
env/
ENV/
.venv*/
venv*/
env*/

# Python build/packaging (not our build/ directory)
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Unit test / coverage
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
test-results/
coverage


# Jupyter
.ipynb_checkpoints

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json
.pyre/
.pytype/

# =====================================
# Node.js (if we add JS tooling later)
# =====================================
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
package-lock.json
yarn.lock

# =====================================
# OS / Editor
# =====================================
.DS_Store
Thumbs.db
.idea/
.vscode/
*.swp
*.swo
*.log

# Windows/WSL
*Zone.Identifier*

# Temp files
*.bak
*.tmp
.tmp/
temp/

# =====================================
# Environment files
# =====================================
.env
.env.*
*.env.localrename_references.sh


# Logs
*.log
pnpm-debug.log*
""".strip(),
        )

        # .env.example
        self._write_file(
            self.root / ".env.example",
            """# GCLI Web UI Environment Variables

# GCLI Configuration
GEMINI_API_KEY=your-api-key-here
GEMINI_MODEL=gemini-2.0-flash-exp

# Flask Configuration
FLASK_SECRET_KEY=change-this-in-production
FLASK_DEBUG=1

# Web UI Configuration
GCLI_WEBUI_PORT=5000
GCLI_WEBUI_HOST=127.0.0.1

# Session Configuration
SESSION_TIMEOUT=3600

# Logging
LOG_LEVEL=INFO
""",
        )

        # pytest.ini
        self._write_file(
            self.root / "pytest.ini",
            """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=app
    --cov-report=html
    --cov-report=term-missing
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow-running tests
""",
        )

        print()

    def _create_app_files(self):
        """Create Flask application files"""
        print("🐍 Creating application files...")

        # app/__init__.py
        self._write_file(
            self.root / "app" / "__init__.py",
            '''"""
GCLI Web UI - Flask Application Package
"""

__version__ = "0.1.0"
''',
        )

        # app/main.py (Phase 2 skeleton)
        self._write_file(
            self.root / "app" / "main.py",
            '''"""
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
''',
        )

        # app/session_manager.py (Phase 3 skeleton)
        self._write_file(
            self.root / "app" / "session_manager.py",
            '''"""
Session Manager: Maintains long-lived GCLI subprocesses

Phase 3: Session Management & Stateful Conversations
TODO: Implement session management
"""

import subprocess
import threading
import queue
import uuid
from typing import Dict, Optional


class GCLISession:
    """Represents a single GCLI subprocess session"""
    
    def __init__(self, working_dir: str, model_name: str = 'gemini-2.0-flash-exp'):
        self.session_id = str(uuid.uuid4())
        self.working_dir = working_dir
        self.model_name = model_name
        self.process: Optional[subprocess.Popen] = None
        self.output_queue: queue.Queue = queue.Queue()
        self.is_alive = False
    
    def start(self):
        """Spawn GCLI subprocess with checkpointing"""
        # TODO: Implement subprocess spawning
        pass
    
    def send_prompt(self, prompt: str):
        """Send prompt to GCLI subprocess"""
        # TODO: Implement prompt sending
        pass
    
    def get_response(self, timeout: int = 60) -> str:
        """Collect response from GCLI"""
        # TODO: Implement response collection
        pass
    
    def terminate(self):
        """Clean shutdown - let GCLI checkpoint"""
        # TODO: Implement clean shutdown
        pass


class SessionManager:
    """Manages multiple GCLI sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, GCLISession] = {}
    
    def create_session(self, working_dir: str, model_name: str = 'gemini-2.0-flash-exp') -> str:
        """Create new GCLI session"""
        # TODO: Implement session creation
        pass
    
    def get_session(self, session_id: str) -> Optional[GCLISession]:
        """Retrieve existing session"""
        return self.sessions.get(session_id)
    
    def terminate_session(self, session_id: str):
        """End session gracefully"""
        # TODO: Implement session termination
        pass


# Global session manager instance
session_manager = SessionManager()
''',
        )

        # app/templates/index.html (Phase 2 minimal)
        self._write_file(
            self.root / "app" / "templates" / "index.html",
            """<!DOCTYPE html>
<html>
<head>
    <title>GCLI Web UI - Phase 2</title>
    <style>
        body { 
            font-family: monospace; 
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        #prompt { 
            width: 100%; 
            height: 100px;
            font-family: monospace;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        #response { 
            margin-top: 20px; 
            padding: 10px; 
            background: #f0f0f0;
            white-space: pre-wrap;
            border-radius: 4px;
            min-height: 100px;
        }
        #status { 
            color: blue; 
            margin-top: 10px;
        }
        button {
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background: #45a049;
        }
        input[type="text"] {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>GCLI Web UI - Phase 2 Proof of Concept</h1>
        
        <div>
            <label><strong>Working Directory:</strong></label>
            <input type="text" id="cwd" value="" style="width: 100%; margin-top: 5px;">
        </div>
        
        <div style="margin-top: 15px;">
            <label><strong>Prompt:</strong></label>
            <textarea id="prompt" placeholder="Enter prompt (try: @file or /help)"></textarea>
        </div>
        
        <button onclick="sendPrompt()">Send to GCLI</button>
        
        <div id="status"></div>
        <div id="response"></div>
    </div>
    
    <script>
        // Set default working directory
        document.getElementById('cwd').value = '';
        
        async function sendPrompt() {
            const prompt = document.getElementById('prompt').value;
            const cwd = document.getElementById('cwd').value || '.';
            const statusDiv = document.getElementById('status');
            const responseDiv = document.getElementById('response');
            
            statusDiv.textContent = 'Thinking...';
            responseDiv.textContent = '';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt, cwd})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusDiv.textContent = 'Response:';
                    responseDiv.textContent = data.response;
                } else {
                    statusDiv.textContent = 'Error:';
                    responseDiv.textContent = data.error || 'Unknown error';
                }
            } catch (error) {
                statusDiv.textContent = 'Error:';
                responseDiv.textContent = error.message;
            }
        }
    </script>
</body>
</html>
""",
        )

        print()

    def _create_test_files(self):
        """Create test structure and files"""
        print("🧪 Creating test files...")

        # tests/__init__.py
        self._write_file(self.root / "tests" / "__init__.py", "")

        # tests/conftest.py
        self._write_file(
            self.root / "tests" / "conftest.py",
            '''"""
Pytest configuration and fixtures
"""

import pytest
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def app():
    """Create Flask app for testing"""
    from app.main import app as flask_app
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    return flask_app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def safe_test_dir(tmp_path):
    """Create a safe temporary directory for testing"""
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    return test_dir
''',
        )

        # tests/unit/__init__.py
        self._write_file(self.root / "tests" / "unit" / "__init__.py", "")

        # tests/unit/test_main.py
        self._write_file(
            self.root / "tests" / "unit" / "test_main.py",
            '''"""
Unit tests for main Flask application
"""

import pytest


@pytest.mark.unit
def test_index_route(client):
    """Test that index route loads"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'GCLI Web UI' in response.data


@pytest.mark.unit
def test_is_safe_directory():
    """Test directory validation logic"""
    from app.main import is_safe_directory
    import os
    
    # Should allow home directory
    home = os.path.expanduser('~')
    assert is_safe_directory(home) is True
    
    # Should block system directories
    assert is_safe_directory('/usr') is False
    assert is_safe_directory('/etc') is False
    assert is_safe_directory('/') is False
''',
        )

        # tests/integration/__init__.py
        self._write_file(self.root / "tests" / "integration" / "__init__.py", "")

        # tests/integration/test_gcli_integration.py
        self._write_file(
            self.root / "tests" / "integration" / "test_gcli_integration.py",
            '''"""
Integration tests for GCLI subprocess integration

These tests require GCLI to be installed and configured
"""

import pytest
import subprocess


@pytest.mark.integration
def test_gcli_available():
    """Test that GCLI is installed and accessible"""
    try:
        result = subprocess.run(
            ['gemini', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0
    except FileNotFoundError:
        pytest.skip("GCLI not installed")


@pytest.mark.integration
def test_gcli_non_interactive_mode():
    """Test GCLI non-interactive mode works"""
    try:
        result = subprocess.run(
            ['gemini', '--non-interactive'],
            input='What is 2+2?',
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert len(result.stdout) > 0
    except FileNotFoundError:
        pytest.skip("GCLI not installed")
''',
        )

        print()

    def _create_docs(self):
        """Create documentation files"""
        print("📚 Creating documentation...")

        # README.md
        self._write_file(
            self.root / "README.md",
            """# GCLI Web UI

ChatGPT-style web interface for Gemini CLI.

## Status

🚧 **Under Development** - Following phased implementation plan

### Current Phase: Phase 0 - Environment Setup

## Quick Start

```bash
# Clone repository
git clone <repo-url>
cd gcli-webui

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start development server (Phase 2+)
python app/main.py
```

## Project Structure

```
gcli-webui/
├── app/                    # Flask application
│   ├── main.py            # Main application file
│   ├── session_manager.py # Session management (Phase 3)
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS assets
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/                  # Documentation
├── bin/                   # Shell scripts (geminiwebui wrapper)
└── logs/                  # Application logs

```

## Development Phases

- [x] **Phase 0**: Environment Setup & GCLI Validation
- [ ] **Phase 1**: Critical Validation - `@` and `/` Commands
- [ ] **Phase 2**: Minimal Flask ↔ GCLI Proof-of-Concept
- [ ] **Phase 3**: Session Management & Stateful Conversations
- [ ] **Phase 4**: Shell Wrapper & ChatGPT-Style UI
- [ ] **Phase 5**: Optional Enhancements & Stream-JSON

## Requirements

- Python 3.8+
- GCLI (Gemini CLI) installed and configured
- Flask 3.0+

## Testing

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run with coverage
pytest --cov=app --cov-report=html
```

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Implementation Plan](docs/PHASED_PLAN.md)
- [Phase Validation](docs/PHASE_VALIDATIONS.md)

## License

MIT

## Contributing

This project follows a phased implementation approach. See `docs/PHASED_PLAN.md` for details.
""",
        )

        # docs/ARCHITECTURE.md (placeholder)
        self._write_file(
            self.root / "docs" / "ARCHITECTURE.md",
            """# GCLI Web UI Architecture

## Overview

ChatGPT-style web interface for Gemini CLI (GCLI).

## System Architecture

```
Browser (UI)
    ↕ HTTP/JSON
Flask Server (main.py)
    ↕ subprocess stdin/stdout
GCLI Process (--checkpoint --non-interactive)
    ↕
Gemini API
```

## Components

### Flask Application (`app/main.py`)
- Handles HTTP requests
- Manages GCLI subprocess lifecycle
- Routes: `/`, `/ask`, `/start_session`, `/end_session`

### Session Manager (`app/session_manager.py`)
- Maintains long-lived GCLI subprocesses
- One subprocess per user session
- Handles conversation persistence

### Shell Wrapper (`bin/geminiwebui`)
- Directory validation
- Flask server launch
- Browser auto-open

## Data Flow

1. User enters prompt in browser
2. JavaScript sends POST to `/ask`
3. Flask forwards to GCLI subprocess
4. GCLI processes prompt (with `@file` expansion)
5. Gemini API returns response
6. Flask captures output, sends to browser
7. JavaScript updates UI

## Security

- Directory validation (blacklist system dirs)
- Subprocess timeout (60s default)
- No arbitrary code execution
- Local-only binding (127.0.0.1)

## Session Management

- Session ID stored in Flask session cookie
- GCLI subprocess persists across requests
- `--checkpoint` flag enables conversation persistence
- Clean shutdown on browser close

See `PHASED_PLAN.md` for implementation details.
""",
        )

        # docs/PHASE_VALIDATIONS.md (template)
        self._write_file(
            self.root / "docs" / "PHASE_VALIDATIONS.md",
            """# Phase Validation Results

## Phase 0: Environment Setup & GCLI Validation

### Status: In Progress

### Tasks Completed
- [ ] GCLI installation verified
- [ ] Non-interactive mode tested
- [ ] Stream-JSON mode tested
- [ ] Project structure created

### Validation Results

**GCLI Non-Interactive Mode:**
```bash
# Test command:
echo "What is 2+2?" | gemini --non-interactive

# Result:
[TO BE FILLED]
```

**Stream-JSON Mode:**
```bash
# Test command:
echo "Test" | gemini --stream-json --non-interactive

# Result:
[TO BE FILLED]
```

### Next Steps
- [ ] Complete Phase 0 validation
- [ ] Proceed to Phase 1

---

## Phase 1: Critical Validation - `@` and `/` Commands

### Status: Not Started

### Critical Questions
1. Do `@file` commands work in non-interactive mode?
2. Do `/` commands work in non-interactive mode?
3. Is Stream-JSON available?

### Test Results
[TO BE FILLED]

---

## Phase 2: Minimal Flask Integration

### Status: Not Started

[TO BE FILLED]

---

## Decision Log

| Date | Phase | Decision | Rationale |
|------|-------|----------|-----------|
| [Date] | 0 | [Decision] | [Rationale] |
""",
        )

        print()

    def _create_wrapper_script(self):
        """Create shell wrapper script"""
        print("🔧 Creating shell wrapper...")

        # bin/geminiwebui (Phase 4)
        self._write_file(
            self.root / "bin" / "geminiwebui",
            """#!/bin/bash
# geminiwebui - Launch GCLI Web UI
# Phase 4 implementation

echo "GCLI Web UI Wrapper - Not yet implemented"
echo "Run manually: python app/main.py"
exit 1
""",
        )

        # Make executable
        if not self.dry_run:
            (self.root / "bin" / "geminiwebui").chmod(0o755)

        print()

    def _mkdir(self, path: Path):
        """Create directory"""
        if self.dry_run:
            print(f"  [DRY RUN] Would create: {path}")
        else:
            path.mkdir(parents=True, exist_ok=True)
            self.created_dirs.append(path)
            print(f"  ✓ Created: {path}")

    def _write_file(self, path: Path, content: str):
        """Write file with content"""
        if self.dry_run:
            print(f"  [DRY RUN] Would write: {path} ({len(content)} bytes)")
        else:
            path.write_text(content)
            self.created_files.append(path)
            print(f"  ✓ Created: {path}")

    def _print_summary(self):
        """Print scaffolding summary"""
        print("=" * 60)
        print("✅ Scaffolding Complete!")
        print("=" * 60)
        print()

        if self.dry_run:
            print("🔍 DRY RUN - No files were actually created")
            print()
        else:
            print(f"📁 Created {len(self.created_dirs)} directories")
            print(f"📄 Created {len(self.created_files)} files")
            print()

        print("Next Steps:")
        print("  1. cd into project directory")
        print("  2. Create virtual environment:")
        print("     python -m venv .venv")
        print("     source .venv/bin/activate")
        print("  3. Install dependencies:")
        print("     pip install -r requirements.txt")
        print("  4. Copy .env.example to .env and configure")
        print("  5. Run tests:")
        print("     pytest")
        print("  6. Start Phase 0 validation:")
        print("     See docs/PHASE_VALIDATIONS.md")
        print()
        print("📚 Documentation:")
        print("  - README.md - Project overview")
        print("  - docs/ARCHITECTURE.md - System design")
        print("  - docs/PHASE_VALIDATIONS.md - Phase tracking")
        print()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Scaffold GCLI Web UI project structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without actually creating files",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)",
    )

    args = parser.parse_args()

    # Confirm if directory not empty and not dry run
    if not args.dry_run and any(args.dir.iterdir()):
        print(f"⚠️  Warning: Directory {args.dir} is not empty!")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    # Run scaffolder
    scaffolder = ProjectScaffolder(args.dir, dry_run=args.dry_run)
    scaffolder.scaffold()


if __name__ == "__main__":
    main()
