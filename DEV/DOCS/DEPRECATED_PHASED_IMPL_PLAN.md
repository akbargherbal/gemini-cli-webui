# GCLI Web UI: Implementation Plan

**5-Phase Roadmap | Conservative Estimates | Risk-Averse Approach**

---

## Phase 0: Environment Setup & GCLI Validation (Day 1, 1-2 hours)

### Goal

Verify GCLI installation, validate non-interactive mode capabilities, establish baseline for `@`/`/` command functionality.

### Tasks

**0.1: Verify GCLI Installation** (15 min)

```bash
# Check GCLI is installed and accessible
which gemini
gemini --version

# Expected output: version info (e.g., "1.x.x")
```

**0.2: Test Basic Non-Interactive Mode** (20 min)

```bash
# Create test directory
mkdir -p ~/test-gcli-webui
cd ~/test-gcli-webui

# Test basic non-interactive invocation
echo "What is 2+2?" | gemini --non-interactive

# Expected: Model response without entering interactive mode
```

**0.3: Test Stream-JSON Output Mode** (20 min)

```bash
# Test Stream-JSON mode (critical for web integration)
echo "Explain Python decorators" | gemini --stream-json --non-interactive

# Expected: Line-delimited JSON events
# Example output:
# {"type":"text","text":"Decorators are..."}
# {"type":"complete"}
```

**0.4: Document GCLI Capabilities** (15 min)

Create `GCLI_VALIDATION.md`:

```markdown
# GCLI Validation Results

- [x] Non-interactive mode works: YES/NO
- [x] Stream-JSON mode works: YES/NO
- [x] Output format: [describe]
- [x] Error handling: [note any issues]

## Next Steps

- If non-interactive fails: [troubleshooting steps]
- If Stream-JSON unavailable: [fallback strategy]
```

**0.5: Create Project Structure** (20 min)

```bash
mkdir -p ~/gcli-webui/{app,tests,docs,logs}
cd ~/gcli-webui

# Create initial files
touch app/__init__.py
touch app/main.py
touch requirements.txt
touch README.md
```

### Success Criteria

- ✅ GCLI responds in non-interactive mode
- ✅ Stream-JSON output format confirmed (or fallback identified)
- ✅ Project directory structure created
- ✅ Validation results documented

### Risks & Unknowns

**Risk**: Stream-JSON mode not available in installed GCLI version
- **Impact**: HIGH - affects entire streaming architecture
- **Detection**: Run `gemini --help | grep stream-json`
- **Mitigation**: Use regular non-interactive mode, parse stdout manually

**Unknown**: Exact JSON event format in Stream-JSON mode
- **Validation needed**: Capture sample output, document schema
- **Fallback**: If format unusable, switch to line-buffered stdout parsing

### Rollback Strategy

If GCLI non-interactive mode fundamentally doesn't work:
1. Document findings in `BLOCKERS.md`
2. Investigate alternative approaches (terminal emulation via `pexpect`)
3. Reassess project feasibility

### Dependencies

- GCLI installed and in PATH
- Terminal with stdout/stderr access
- Basic shell scripting capability

---

## Phase 1: Critical Validation - `@` and `/` Commands (Day 1-2, 2-3 hours)

### Goal

**CRITICAL PHASE**: Prove that `@file`, `@directory`, and `/command` preprocessing works when GCLI receives input via stdin in non-interactive mode. This validates the entire project's feasibility.

### Tasks

**1.1: Create Test Repository Structure** (15 min)

```bash
cd ~/test-gcli-webui
mkdir -p test-project/{src,docs}

# Create test files for @file references
cat > test-project/src/main.py << 'EOF'
def hello_world():
    """Simple test function"""
    print("Hello, World!")
EOF

cat > test-project/docs/README.md << 'EOF'
# Test Project
This is a test file for @file references.
EOF
```

**1.2: Test `@file` Command in Non-Interactive Mode** (30 min)

```bash
cd ~/test-gcli-webui/test-project

# Test 1: @file with relative path
echo "Explain this code: @src/main.py" | gemini --non-interactive

# Expected: Model receives file contents and explains the code
# FAILURE INDICATOR: Model says "I cannot access files" or similar

# Test 2: @file with absolute path
echo "Explain @${PWD}/src/main.py" | gemini --non-interactive

# Test 3: Multiple @file references
echo "Compare @src/main.py and @docs/README.md" | gemini --non-interactive
```

**1.3: Test `@directory` Command** (20 min)

```bash
echo "List all Python files in @src" | gemini --non-interactive

# Expected: Model receives directory contents listing
```

**1.4: Test `/` Slash Commands** (20 min)

```bash
# Test common slash commands
echo "/help" | gemini --non-interactive
echo "/model" | gemini --non-interactive

# Expected: Command output, not "unknown command"
```

**1.5: Test Combined `@` and Regular Prompts** (20 min)

```bash
# Test that @file expansion happens BEFORE model sees prompt
echo "The file @src/main.py needs error handling. Add try/except." | gemini --non-interactive

# Expected: Model response references specific code from main.py
# FAILURE: Model asks "which file?" or doesn't see code
```

**1.6: Document Findings** (30 min)

Create `PHASE1_VALIDATION.md`:

```markdown
# Phase 1: @ and / Command Validation

## Test Results

### @file Command
- ✅/❌ Single file: [works/fails - details]
- ✅/❌ Multiple files: [works/fails - details]
- ✅/❌ Absolute paths: [works/fails - details]

### @directory Command
- ✅/❌ Directory listing: [works/fails - details]

### /commands
- ✅/❌ /help: [works/fails - details]
- ✅/❌ /model: [works/fails - details]

## Critical Finding

**DO @/@ commands work in non-interactive mode?**
- Answer: YES/NO
- Evidence: [paste sample output]

## Decision Point

- ✅ Proceed to Phase 2 (all tests passed)
- ⚠️ Modify approach (partial failures - document workarounds)
- ❌ STOP (fundamental blocker - reassess project)
```

**1.7: Test with Stream-JSON Mode** (20 min)

If Stream-JSON available, repeat tests:

```bash
echo "Explain @src/main.py" | gemini --stream-json --non-interactive

# Verify: File contents appear in JSON events
# Check: Event structure includes context
```

### Success Criteria

- ✅ `@file` successfully loads file contents in non-interactive mode
- ✅ Model response references actual file contents (not hallucinated)
- ✅ `/` commands execute (or graceful error if unsupported)
- ✅ Working directory context is respected (GCLI operates in `test-project/`)

### Risks & Unknowns

**CRITICAL RISK**: `@`/`/` preprocessing tied to interactive UI layer
- **Likelihood**: MEDIUM (architecture doc unclear on this)
- **Impact**: CATASTROPHIC (entire project approach invalid)
- **Detection**: Test 1.2 fails - model doesn't see file contents
- **Mitigation**: If fails, investigate `--context` flag or manual file injection

**Unknown**: Does `@file` path resolution use GCLI's cwd or shell's cwd?
- **Test**: Run GCLI from different directory, reference files with relative paths
- **Impact**: Affects how Flask sets working directory

### Rollback Strategy

**If `@file` doesn't work in non-interactive mode:**

1. **Stop immediately** - document blocker
2. **Investigate workarounds:**
   - Option A: Manually read files in Flask, inject into prompt
   - Option B: Use GCLI's `--context` flag if available
   - Option C: Switch to terminal emulation (pty/pexpect)
3. **Update project scope** - if no workaround, adjust goals
4. **Document decision** in `ARCHITECTURE_DECISIONS.md`

**If `/` commands don't work:**
- Less critical - most slash commands are UI conveniences
- Can be implemented in Flask layer (intercept `/help`, etc.)

### Dependencies

- Phase 0 completed successfully
- Test project structure created
- GCLI installed with file access capabilities

---

## Phase 2: Minimal Flask ↔ GCLI Proof-of-Concept (Day 2-3, 3-4 hours)

### Goal

Create absolute minimum Flask app that sends one prompt to GCLI subprocess, receives response, displays in browser. No streaming, no UI polish—just prove the pipe works.

### Tasks

**2.1: Create Flask Application Structure** (20 min)

```bash
cd ~/gcli-webui

cat > requirements.txt << 'EOF'
Flask==3.0.0
python-dotenv==1.0.0
EOF

pip install -r requirements.txt
```

**2.2: Create Minimal Flask App** (60 min)

Create `app/main.py`:

```python
"""
Minimal GCLI Web UI - Phase 2 Proof of Concept
ONE prompt -> GCLI subprocess -> response
"""

from flask import Flask, render_template, request, jsonify
import subprocess
import os
import json

app = Flask(__name__)

@app.route('/')
def index():
    """Serve minimal HTML form"""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_gcli():
    """
    Send prompt to GCLI, wait for complete response
    NO streaming in Phase 2 - just prove it works
    """
    try:
        user_prompt = request.json.get('prompt', '')
        working_dir = request.json.get('cwd', os.getcwd())
        
        # Validate working directory (safety check)
        if not is_safe_directory(working_dir):
            return jsonify({'error': 'Unsafe directory'}), 400
        
        # Spawn GCLI subprocess
        result = subprocess.run(
            ['gemini', '--non-interactive'],
            input=user_prompt,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=60  # 1 minute timeout
        )
        
        if result.returncode != 0:
            return jsonify({
                'error': 'GCLI error',
                'stderr': result.stderr
            }), 500
        
        return jsonify({
            'response': result.stdout,
            'success': True
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'GCLI timeout'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def is_safe_directory(path):
    """
    Validate directory is safe to run GCLI in
    Phase 2: Simple whitelist approach
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
    app.run(debug=True, port=5000)
```

**2.3: Create Minimal HTML Template** (30 min)

Create `app/templates/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>GCLI Web UI - Phase 2</title>
    <style>
        body { font-family: monospace; padding: 20px; }
        #prompt { width: 100%; height: 100px; }
        #response { 
            margin-top: 20px; 
            padding: 10px; 
            background: #f0f0f0;
            white-space: pre-wrap;
        }
        #status { color: blue; }
    </style>
</head>
<body>
    <h1>GCLI Web UI - Proof of Concept</h1>
    
    <div>
        <label>Working Directory:</label>
        <input type="text" id="cwd" value="" style="width: 100%;">
    </div>
    
    <div>
        <label>Prompt:</label>
        <textarea id="prompt" placeholder="Enter prompt (try: @file or /help)"></textarea>
    </div>
    
    <button onclick="sendPrompt()">Send to GCLI</button>
    
    <div id="status"></div>
    <div id="response"></div>
    
    <script>
        // Set default working directory to current directory
        document.getElementById('cwd').value = '<%= CWD %>';  // Will be template variable
        
        async function sendPrompt() {
            const prompt = document.getElementById('prompt').value;
            const cwd = document.getElementById('cwd').value;
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
                    responseDiv.textContent = data.error;
                }
            } catch (error) {
                statusDiv.textContent = 'Error:';
                responseDiv.textContent = error.message;
            }
        }
    </script>
</body>
</html>
```

**2.4: Test Minimal Flow** (30 min)

```bash
# Terminal 1: Start Flask
cd ~/gcli-webui
python app/main.py

# Terminal 2: Test with curl
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?", "cwd": "'$(pwd)'"}'

# Expected: JSON response with GCLI output
```

**2.5: Test in Browser** (30 min)

1. Open `http://localhost:5000`
2. Enter prompt: "Explain Python decorators"
3. Click "Send to GCLI"
4. Wait for response
5. Verify response appears

**2.6: Test `@file` via Web UI** (20 min)

```bash
# Setup test file
mkdir -p ~/test-webui-project
cat > ~/test-webui-project/sample.py << 'EOF'
def greet(name):
    return f"Hello, {name}!"
EOF
```

In browser:
1. Set working directory: `~/test-webui-project`
2. Enter prompt: `Explain @sample.py`
3. Send
4. **CRITICAL**: Verify response references actual code from `sample.py`

**2.7: Document Phase 2 Results** (20 min)

Create `PHASE2_RESULTS.md`:

```markdown
# Phase 2: Flask ↔ GCLI Integration

## What Works
- [ ] Flask starts without errors
- [ ] Browser loads UI
- [ ] Prompt submission triggers GCLI
- [ ] Response appears in browser
- [ ] @file commands work via web
- [ ] Working directory respected

## What Doesn't Work
- [List any failures]

## Performance
- Prompt to response time: [X seconds]
- Acceptable? YES/NO

## Blockers
- [None / List any]

## Next Steps
- ✅ Proceed to Phase 3 (add session management)
- ⚠️ Fix issues: [list]
- ❌ Fundamental problem: [describe]
```

### Success Criteria

- ✅ Flask app starts and serves HTML
- ✅ Prompt sent to GCLI subprocess successfully
- ✅ GCLI response captured and displayed in browser
- ✅ `@file` commands work when invoked via web UI
- ✅ Working directory validation prevents system directory access
- ✅ Errors handled gracefully (timeouts, GCLI failures)

### Risks & Unknowns

**Risk**: Subprocess blocking freezes Flask
- **Impact**: HIGH - UI becomes unresponsive
- **Detection**: Test with slow prompt (complex code analysis)
- **Mitigation**: Use `timeout` parameter (already in code), consider threading in Phase 3

**Risk**: Working directory validation too restrictive
- **Impact**: MEDIUM - users can't access valid projects
- **Detection**: Test with various project paths
- **Mitigation**: Make whitelist configurable

**Unknown**: GCLI output encoding issues
- **Test**: Send prompts with Unicode, emojis, special characters
- **Mitigation**: Explicit UTF-8 handling in subprocess call

### Rollback Strategy

If subprocess integration fails:
1. Document exact error in `PHASE2_RESULTS.md`
2. Test GCLI manually with same inputs (isolate Flask vs GCLI issue)
3. Options:
   - Try `shell=True` (security tradeoff)
   - Use `Popen` with explicit stdin/stdout pipes
   - Switch to `pexpect` for terminal emulation
4. **Worst case**: Revert to terminal-only GCLI usage, abandon web UI

### Dependencies

- Phase 1 completed successfully (`@file` works in non-interactive mode)
- Flask installed
- GCLI accessible from Python subprocess

---

## Phase 3: Session Management & Stateful Conversations (Day 3-4, 3-4 hours)

### Goal

Maintain long-lived GCLI subprocess per user session to enable multi-turn conversations, leveraging GCLI's built-in `--checkpoint` flag for persistence.

### Tasks

**3.1: Study GCLI Checkpoint Mechanism** (30 min)

```bash
# Test GCLI checkpoint behavior
cd ~/test-gcli-webui/test-project

# Start GCLI with checkpointing
gemini --checkpoint

# In GCLI prompt:
# 1. Ask: "What is 2+2?"
# 2. Follow-up: "What was my previous question?"
# 3. Exit GCLI
# 4. Restart with same checkpoint
# 5. Verify conversation restored

# Observe:
# - Where are checkpoint files stored? (.gemini/sessions/?)
# - What's the file format? (JSON?)
# - How are sessions identified? (UUID?)
```

Document findings in `CHECKPOINT_NOTES.md`

**3.2: Modify Flask for Long-Lived Subprocess** (90 min)

Create `app/session_manager.py`:

```python
"""
Session Manager: Maintains long-lived GCLI subprocesses
One subprocess per user session
"""

import subprocess
import threading
import queue
import uuid
from collections import defaultdict

class GCLISession:
    """Represents a single GCLI subprocess session"""
    
    def __init__(self, working_dir, model_name='gemini-2.0-flash-exp'):
        self.session_id = str(uuid.uuid4())
        self.working_dir = working_dir
        self.model_name = model_name
        self.process = None
        self.output_queue = queue.Queue()
        self.is_alive = False
        
    def start(self):
        """Spawn GCLI subprocess with checkpointing"""
        self.process = subprocess.Popen(
            ['gemini', '-m', self.model_name, '--checkpoint', '--non-interactive'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.working_dir,
            bufsize=1  # Line-buffered
        )
        self.is_alive = True
        
        # Start output reader thread
        self.reader_thread = threading.Thread(
            target=self._read_output,
            daemon=True
        )
        self.reader_thread.start()
    
    def _read_output(self):
        """Background thread: read GCLI output line by line"""
        try:
            for line in self.process.stdout:
                self.output_queue.put(('stdout', line))
        except Exception as e:
            self.output_queue.put(('error', str(e)))
        finally:
            self.is_alive = False
    
    def send_prompt(self, prompt):
        """Send prompt to GCLI subprocess"""
        if not self.is_alive:
            raise RuntimeError("GCLI subprocess not alive")
        
        self.process.stdin.write(prompt + '\n')
        self.process.stdin.flush()
    
    def get_response(self, timeout=60):
        """
        Collect response from GCLI
        Phase 3: Simple approach - wait for prompt indicator or timeout
        """
        response_lines = []
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                msg_type, line = self.output_queue.get(timeout=1)
                if msg_type == 'error':
                    raise RuntimeError(line)
                
                response_lines.append(line)
                
                # Heuristic: Response complete when we see empty line or prompt
                # This is fragile - will improve in Phase 4
                if line.strip() == '' and response_lines:
                    break
                    
            except queue.Empty:
                if response_lines:  # Got some output, likely complete
                    break
        
        return ''.join(response_lines)
    
    def terminate(self):
        """Clean shutdown - let GCLI checkpoint"""
        if self.process:
            self.process.stdin.close()
            self.process.wait(timeout=5)
            self.is_alive = False

class SessionManager:
    """Manages multiple GCLI sessions (one per user)"""
    
    def __init__(self):
        self.sessions = {}  # session_id -> GCLISession
    
    def create_session(self, working_dir, model_name='gemini-2.0-flash-exp'):
        """Create new GCLI session"""
        session = GCLISession(working_dir, model_name)
        session.start()
        self.sessions[session.session_id] = session
        return session.session_id
    
    def get_session(self, session_id):
        """Retrieve existing session"""
        return self.sessions.get(session_id)
    
    def terminate_session(self, session_id):
        """End session gracefully"""
        session = self.sessions.pop(session_id, None)
        if session:
            session.terminate()

# Global session manager instance
session_manager = SessionManager()
```

**3.3: Update Flask Routes for Sessions** (45 min)

Modify `app/main.py`:

```python
from flask import Flask, session as flask_session, request, jsonify
from app.session_manager import session_manager
import os

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

@app.route('/start_session', methods=['POST'])
def start_session():
    """Initialize GCLI session for user"""
    working_dir = request.json.get('cwd', os.getcwd())
    
    if not is_safe_directory(working_dir):
        return jsonify({'error': 'Unsafe directory'}), 400
    
    # Create GCLI session
    session_id = session_manager.create_session(working_dir)
    
    # Store in Flask session (cookie-based)
    flask_session['gcli_session_id'] = session_id
    
    return jsonify({
        'session_id': session_id,
        'working_dir': working_dir,
        'success': True
    })

@app.route('/ask', methods=['POST'])
def ask_gcli():
    """Send prompt to existing GCLI session"""
    # Get session ID from cookie
    session_id = flask_session.get('gcli_session_id')
    
    if not session_id:
        return jsonify({'error': 'No active session'}), 400
    
    gcli_session = session_manager.get_session(session_id)
    if not gcli_session:
        return jsonify({'error': 'Session expired'}), 404
    
    try:
        prompt = request.json.get('prompt', '')
        
        # Send to GCLI subprocess
        gcli_session.send_prompt(prompt)
        
        # Wait for response
        response = gcli_session.get_response(timeout=60)
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'success': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/end_session', methods=['POST'])
def end_session():
    """Terminate GCLI session"""
    session_id = flask_session.get('gcli_session_id')
    
    if session_id:
        session_manager.terminate_session(session_id)
        flask_session.pop('gcli_session_id', None)
    
    return jsonify({'success': True})
```

**3.4: Update HTML for Session Flow** (30 min)

Modify `app/templates/index.html`:

```html
<script>
let currentSessionId = null;

async function startSession() {
    const cwd = document.getElementById('cwd').value;
    
    const response = await fetch('/start_session', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({cwd})
    });
    
    const data = await response.json();
    if (data.success) {
        currentSessionId = data.session_id;
        document.getElementById('status').textContent = 
            `Session started: ${data.session_id.substring(0, 8)}...`;
    }
}

async function sendPrompt() {
    // Start session if not exists
    if (!currentSessionId) {
        await startSession();
    }
    
    // ... rest of sendPrompt logic ...
}

window.addEventListener('beforeunload', async () => {
    // End session when browser closes
    if (currentSessionId) {
        await fetch('/end_session', {method: 'POST'});
    }
});
</script>
```

**3.5: Test Multi-Turn Conversation** (45 min)

Test sequence:
1. Start web UI
2. Set working dir: `~/test-webui-project`
3. Send: "What is 2+2?"
4. **Verify response**
5. Send: "What was my previous question?" (tests conversation memory)
6. **CRITICAL**: Verify model references "2+2" question
7. Send: "Explain @sample.py"
8. Send: "Add error handling to the function you just explained"
9. **Verify**: Model references `greet()` function from earlier

**3.6: Test Session Persistence** (30 min)

1. Start conversation
2. Send 3-4 prompts
3. Refresh browser (WITHOUT closing Flask)
4. Resume conversation
5. **Expected**: GCLI checkpoint should preserve history
6. **Test**: Ask "Summarize our conversation" - should reference earlier prompts

**3.7: Document Session Behavior** (20 min)

Create `SESSION_TESTING.md`:

```markdown
# Session Management Testing

## Multi-Turn Conversation
- [ ] Model remembers previous prompts
- [ ] Context maintained across requests
- [ ] @file references work in conversation

## Session Lifecycle
- [ ] Session starts cleanly
- [ ] Subprocess remains alive across requests
- [ ] Session terminates gracefully
- [ ] GCLI checkpoint saves on termination

## Edge Cases
- [ ] What happens if subprocess dies?
- [ ] What happens on Flask restart?
- [ ] What happens on browser refresh?

## Issues Found
[Document any problems]

## Performance
- Response latency: [X seconds]
- Memory usage: [observe with `top`]
```

### Success Criteria

- ✅ GCLI subprocess starts and remains alive
- ✅ Multiple prompts sent to same subprocess
- ✅ Model maintains conversation context
- ✅ Session terminates cleanly on browser close
- ✅ GCLI checkpoint mechanism works (if supported)
- ✅ No memory leaks (test with 20+ prompts)

### Risks & Unknowns

**Risk**: Response completion detection is fragile
- **Impact**: HIGH - UI might show partial responses or hang
- **Current approach**: Heuristic (empty line detection)
- **Mitigation**: Phase 4 will use Stream-JSON for reliable parsing
- **Fallback**: Add timeout, show "Response may be incomplete" warning

**Risk**: Subprocess crashes mid-conversation
- **Impact**: MEDIUM - user loses session
- **Detection**: Monitor `process.poll()` status
- **Mitigation**: Auto-restart subprocess, notify user

**Unknown**: Does `--checkpoint` work in `--non-interactive` mode?
- **Test**: Task 3.1 validation
- **If fails**: Sessions won't persist across restarts (acceptable for MVP)

**Risk**: Threading/queue issues under load
- **Impact**: MEDIUM - race conditions, deadlocks
- **Mitigation**: Extensive testing in Task 3.5
- **Fallback**: Simplify to synchronous blocking (Phase 2 approach)

### Rollback Strategy

If long-lived subprocess approach fails:

1. **Revert to Phase 2 approach**: One subprocess per request (stateless)
2. **Document limitation**: No conversation memory
3. **Future improvement**: Implement manual conversation history in Flask (store in file/DB)

If threading causes issues:
1. **Simplify to blocking reads**: Remove output queue
2. **Tradeoff**: Flask blocks during GCLI response (acceptable for solo use)

### Dependencies

- Phase 2 completed successfully
- GCLI `--checkpoint` flag available (verify in Task 3.1)
- Python threading module (standard library)

---

## Phase 4: Shell Wrapper & ChatGPT-Style UI (Day 4-5, 4-5 hours)

### Goal

Create production-ready launch experience: `geminiwebui` command that validates directory, launches Flask, opens browser. Polish UI to match ChatGPT aesthetic.

### Tasks

**4.1: Create Shell Wrapper Script** (60 min)

Create `~/bin/geminiwebui`:

```bash
#!/bin/bash
# geminiwebui - Launch GCLI Web UI with safety checks

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WEBUI_APP_DIR="$HOME/gcli-webui"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- Safety Checks ---

validate_directory() {
    local dir="$1"
    local abs_dir=$(cd "$dir" && pwd)
    
    # Blacklist system directories
    local forbidden_dirs=("/" "/bin" "/usr" "/etc" "/var" "/sys" "/proc" "/boot" "/dev" "/lib" "/sbin")
    
    for forbidden in "${forbidden_dirs[@]}"; do
        if [[ "$abs_dir" == "$forbidden"* ]]; then
            echo -e "${RED}ERROR: Cannot run in system directory: $abs_dir${NC}"
            echo "GCLI should only run in user project directories."
            exit 1
        fi
    done
    
    # Warn if not in home directory
    if [[ ! "$abs_dir" == "$HOME"* ]]; then
        echo -e "${YELLOW}WARNING: Directory is outside home folder: $abs_dir${NC}"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            echo "Aborted."
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✓ Directory validated: $abs_dir${NC}"
}

# --- Parse Arguments ---

MODEL_NAME="gemini-2.0-flash-exp"  # Default model
WORKING_DIR=$(pwd)  # Current directory

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model)
            MODEL_NAME="$2"
            shift 2
            ;;
        -d|--dir)
            WORKING_DIR="$2"
            shift 2
            ;;
        -h|--help)
            cat << EOF
Usage: geminiwebui [OPTIONS]

Launch GCLI Web UI in current or specified directory.

Options:
  -m, --model MODEL    Specify Gemini model (default: gemini-2.0-flash-exp)
  -d, --dir DIR        Working directory (default: current directory)
  -h, --help           Show this help message

Examples:
  geminiwebui                          # Use current directory
  geminiwebui -m gemini-2.0-flash      # Specify model
  geminiwebui -d ~/my-project          # Specify directory
  
Safety:
  - Will not run in system directories (/, /usr, /etc, etc.)
  - Warns when running outside home directory
  - Validates directory is safe before proceeding
EOF
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# --- Main Execution ---

echo "═══════════════════════════════════════"
echo "  GCLI Web UI Launcher"
echo "═══════════════════════════════════════"
echo ""

# Validate directory
echo "Validating working directory..."
validate_directory "$WORKING_DIR"

# Export config as environment variables
export GCLI_WEBUI_DIR="$WORKING_DIR"
export GCLI_WEBUI_MODEL="$MODEL_NAME"

echo ""
echo "Configuration:"
echo "  Working Directory: $WORKING_DIR"
echo "  Model: $MODEL_NAME"
echo ""

# Check if Flask app exists
if [[ ! -d "$WEBUI_APP_DIR" ]]; then
    echo -e "${RED}ERROR: GCLI Web UI not found at $WEBUI_APP_DIR${NC}"
    echo "Please install the web UI first."
    exit 1
fi

# Find available port
PORT=5000
while lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; do
    echo "Port $PORT in use, trying next port..."
    PORT=$((PORT + 1))
done

export GCLI_WEBUI_PORT=$PORT

echo "Starting Flask server on port $PORT..."
cd "$WEBUI_APP_DIR"

# Start Flask in background
python app/main.py &
FLASK_PID=$!

# Wait for server to be ready
echo "Waiting for server to start..."
for i in {1..30}; do
    if curl -s http://localhost:$PORT/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Server ready!${NC}"
        break
    fi
    sleep 1
done

# Open browser
echo "Opening browser..."
if command -v xdg-open > /dev/null; then
    xdg-open "http://localhost:$PORT"
elif command -v open > /dev/null; then
    open "http://localhost:$PORT"
else
    echo "Please open http://localhost:$PORT in your browser"
fi

echo ""
echo "═══════════════════════════════════════"
echo "  GCLI Web UI is running!"
echo "  URL: http://localhost:$PORT"
echo "  Press Ctrl+C to stop"
echo "═══════════════════════════════════════"

# Trap Ctrl+C to cleanup
trap "echo ''; echo 'Shutting down...'; kill $FLASK_PID 2>/dev/null; exit 0" INT

# Wait for Flask process
wait $FLASK_PID
```

**4.2: Make Script Executable & Add to PATH** (15 min)

```bash
chmod +x ~/bin/geminiwebui

# Add to PATH if not already there
if ! grep -q 'export PATH="$HOME/bin:$PATH"' ~/.bashrc; then
    echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
    source ~/.bashrc
fi

# Test command available
which geminiwebui
```

**4.3: Test Wrapper Script** (30 min)

```bash
# Test 1: Default invocation
cd ~/test-webui-project
geminiwebui

# Expected:
# - Directory validation passes
# - Flask starts
# - Browser opens
# - UI loads

# Test 2: Custom model
geminiwebui -m gemini-flash

# Test 3: Forbidden directory (should fail)
cd /usr
geminiwebui
# Expected: Error message, script exits

# Test 4: Help
geminiwebui --help
```

**4.4: Polish HTML/CSS for ChatGPT-Style UI** (120 min)

Create `app/templates/chat.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GCLI Web UI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #343541;
            color: #ececf1;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* Header */
        .header {
            background: #202123;
            padding: 12px 20px;
            border-bottom: 1px solid #4d4d4f;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            font-size: 14px;
            font-weight: 600;
            color: #ececf1;
        }
        
        .working-dir {
            font-size: 12px;
            color: #8e8ea0;
            font-family: 'Courier New', monospace;
        }
        
        /* Chat Container */
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        
        /* Message Bubbles */
        .message {
            display: flex;
            gap: 16px;
            padding: 16px;
            max-width: 800px;
            margin: 0 auto;
            width: 100%;
        }
        
        .message.user {
            background: #343541;
        }
        
        .message.assistant {
            background: #444654;
        }
        
        .avatar {
            width: 30px;
            height: 30px;
            border-radius: 2px;
            background: #5865f2;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
            flex-shrink: 0;
        }
        
        .message.assistant .avatar {
            background: #19c37d;
        }
        
        .message-content {
            flex: 1;
            line-height: 1.6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        /* Composer */
        .composer-container {
            background: #40414f;
            border-top: 1px solid #4d4d4f;
            padding: 20px;
        }
        
        .composer {
            max-width: 800px;
            margin: 0 auto;
            background: #40414f;
            border: 1px solid #565869;
            border-radius: 8px;
            position: relative;
        }
        
        #prompt-input {
            width: 100%;
            padding: 12px 48px 12px 12px;
            background: transparent;
            border: none;
            color: #ececf1;
            font-size: 16px;
            font-family: inherit;
            resize: none;
            outline: none;
            min-height: 52px;
            max-height: 200px;
        }
        
        #prompt-input::placeholder {
            color: #8e8ea0;
        }
        
        .send-button {
            position: absolute;
            right: 12px;
            bottom: 12px;
            background: #19c37d;
            border: none;
            border-radius: 4px;
            width: 32px;
            height: 32px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }
        
        .send-button:hover {
            background: #1a8b5e;
        }
        
        .send-button:disabled {
            background: #565869;
            cursor: not-allowed;
        }
        
        /* Thinking indicator */
        .thinking {
            display: flex;
            gap: 4px;
            padding: 8px 0;
        }
        
        .thinking span {
            width: 8px;
            height: 8px;
            background: #8e8ea0;
            border-radius: 50%;
            animation: pulse 1.4s infinite;
        }
        
        .thinking span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .thinking span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes pulse {
            0%, 80%, 100% { opacity: 0.3; }
            40% { opacity: 1; }
        }
        
        /* Scrollbar styling */
        .chat-container::-webkit-scrollbar {
            width: 8px;
        }
        
        .chat-container::-webkit-scrollbar-track {
            background: #343541;
        }
        
        .chat-container::-webkit-scrollbar-thumb {
            background: #565869;
            border-radius: 4px;
        }
        
        .chat-container::-webkit-scrollbar-thumb:hover {
            background: #676778;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>GCLI Web UI</h1>
        <div class="working-dir" id="working-dir"></div>
    </div>
    
    <div class="chat-container" id="chat-container">
        <!-- Messages will be inserted here -->
    </div>
    
    <div class="composer-container">
        <div class="composer">
            <textarea 
                id="prompt-input" 
                placeholder="Message Gemini CLI Composer..."
                rows="1"
            ></textarea>
            <button class="send-button" id="send-button" onclick="sendMessage()">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
                </svg>
            </button>
        </div>
    </div>
    
    <script>
        let sessionId = null;
        let isThinking = false;
        
        // Auto-resize textarea
        const promptInput = document.getElementById('prompt-input');
        promptInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Send on Shift+Enter
        promptInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Initialize session on load
        async function initSession() {
            const workingDir = new URLSearchParams(window.location.search).get('cwd') || '.';
            document.getElementById('working-dir').textContent = workingDir;
            
            const response = await fetch('/start_session', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({cwd: workingDir})
            });
            
            const data = await response.json();
            if (data.success) {
                sessionId = data.session_id;
            } else {
                addSystemMessage('Error: ' + data.error);
            }
        }
        
        function addMessage(role, content) {
            const chatContainer = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            messageDiv.innerHTML = `
                <div class="avatar">${role === 'user' ? 'U' : 'AI'}</div>
                <div class="message-content">${content}</div>
            `;
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function addSystemMessage(content) {
            const chatContainer = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';
            messageDiv.innerHTML = `
                <div class="avatar">⚠</div>
                <div class="message-content" style="color: #ff6b6b;">${content}</div>
            `;
            chatContainer.appendChild(messageDiv);
        }
        
        function showThinking() {
            const chatContainer = document.getElementById('chat-container');
            const thinkingDiv = document.createElement('div');
            thinkingDiv.className = 'message assistant';
            thinkingDiv.id = 'thinking-indicator';
            thinkingDiv.innerHTML = `
                <div class="avatar">AI</div>
                <div class="message-content">
                    <div class="thinking">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
            chatContainer.appendChild(thinkingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function hideThinking() {
            const thinkingDiv = document.getElementById('thinking-indicator');
            if (thinkingDiv) {
                thinkingDiv.remove();
            }
        }
        
        async function sendMessage() {
            if (isThinking) return;
            
            const prompt = promptInput.value.trim();
            if (!prompt) return;
            
            // Add user message
            addMessage('user', prompt);
            promptInput.value = '';
            promptInput.style.height = 'auto';
            
            // Disable input
            isThinking = true;
            document.getElementById('send-button').disabled = true;
            
            // Show thinking indicator
            showThinking();
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt})
                });
                
                const data = await response.json();
                
                hideThinking();
                
                if (data.success) {
                    addMessage('assistant', data.response);
                } else {
                    addSystemMessage('Error: ' + data.error);
                }
            } catch (error) {
                hideThinking();
                addSystemMessage('Network error: ' + error.message);
            } finally {
                isThinking = false;
                document.getElementById('send-button').disabled = false;
                promptInput.focus();
            }
        }
        
        // Initialize on page load
        initSession();
    </script>
</body>
</html>
```

**4.5: Update Flask to Serve New UI** (15 min)

Modify `app/main.py`:

```python
@app.route('/')
def index():
    """Serve ChatGPT-style UI"""
    cwd = os.environ.get('GCLI_WEBUI_DIR', os.getcwd())
    return render_template('chat.html', cwd=cwd)
```

**4.6: End-to-End Testing** (45 min)

Full workflow test:

```bash
# Test 1: Complete workflow
cd ~/test-webui-project
geminiwebui

# In browser:
# 1. Verify ChatGPT-style UI loads
# 2. Send: "What is 2+2?"
# 3. Verify: Response appears in chat bubble
# 4. Send: "What was my previous question?"
# 5. Verify: Model remembers (session continuity)
# 6. Send: "Explain @sample.py"
# 7. Verify: File contents processed
# 8. Close browser
# 9. Verify: Flask shuts down cleanly
```

**4.7: Create Usage Documentation** (30 min)

Create `~/gcli-webui/README.md`:

```markdown
# GCLI Web UI

ChatGPT-style web interface for Gemini CLI.

## Quick Start

```bash
cd ~/your-project
geminiwebui
```

Browser opens automatically at `http://localhost:5000`

## Features

- ✅ ChatGPT-style interface
- ✅ Multi-turn conversations
- ✅ `@file` and `@directory` support
- ✅ `/command` slash commands
- ✅ Session persistence (via GCLI checkpoints)
- ✅ Directory safety validation

## Usage

### Basic

```bash
# Use current directory
geminiwebui

# Specify model
geminiwebui -m gemini-flash

# Specify directory
geminiwebui -d ~/my-project
```

### In the Web UI

- Type prompts in the composer (bottom)
- Press Enter to send (Shift+Enter for new line)
- Use `@filename` to reference files
- Use `/help` for GCLI commands

### Safety

- Will not run in system directories
- Warns when running outside home folder
- Validates all paths before execution

## Troubleshooting

**Flask won't start:**
- Check if port 5000 is available
- Wrapper auto-increments to next available port

**Session not persisting:**
- Ensure GCLI `--checkpoint` flag is supported
- Check `~/.gemini/sessions/` for session files

**@file not working:**
- Verify file exists in working directory
- Check file permissions
- Ensure GCLI can access file

## Architecture

```
Browser
  ↕ HTTP/JSON
Flask Server (main.py)
  ↕ subprocess stdin/stdout
GCLI Process (--checkpoint --non-interactive)
  ↕
Gemini API
```

## Limitations

- Single user only (no multi-user support)
- No streaming in Phase 4 (shows "Thinking...")
- Session data not preserved across Flask restarts

## Development

See `ARCHITECTURE.md` for detailed system design.
```

### Success Criteria

- ✅ `geminiwebui` command works from any directory
- ✅ Directory validation prevents system directory access
- ✅ UI matches ChatGPT aesthetic (dark theme, chat bubbles)
- ✅ Composer textarea auto-resizes
- ✅ Messages displayed in chronological order
- ✅ "Thinking..." indicator shows during processing
- ✅ Browser opens automatically
- ✅ Flask shutdown is clean (Ctrl+C)

### Risks & Unknowns

**Risk**: Browser auto-open doesn't work on all systems
- **Impact**: LOW - user can manually open URL
- **Mitigation**: Display URL clearly in terminal output

**Risk**: Port conflicts if user runs multiple instances
- **Impact**: MEDIUM - second instance fails
- **Mitigation**: Wrapper auto-increments port (already implemented)

**Unknown**: CSS compatibility across browsers
- **Test**: Try Chrome, Firefox, Safari
- **Mitigation**: Use standard CSS, avoid experimental features

### Rollback Strategy

If wrapper script has issues:
1. Run Flask directly: `python app/main.py`
2. Manual browser open
3. Document wrapper bugs for later fix

If UI polish causes issues:
1. Revert to Phase 2 minimal HTML
2. Polish incrementally in future phase

### Dependencies

- Phase 3 completed (session management works)
- Bash shell for wrapper script
- `~/bin` in PATH

---

## Phase 5: Optional Enhancements & Stream-JSON (If Time Permits)

### Goal

Add real-time streaming output (replaces "Thinking..." with live text), improve error handling, add quality-of-life features.

### Tasks

**5.1: Implement Server-Sent Events (SSE) for Streaming** (90 min)

Modify `app/main.py` to add streaming endpoint:

```python
from flask import Response, stream_with_context

@app.route('/ask_stream', methods=['POST'])
def ask_gcli_stream():
    """Stream GCLI responses in real-time using SSE"""
    session_id = flask_session.get('gcli_session_id')
    gcli_session = session_manager.get_session(session_id)
    
    def generate():
        try:
            prompt = request.json.get('prompt', '')
            gcli_session.send_prompt(prompt)
            
            # Stream output line by line
            while True:
                try:
                    msg_type, line = gcli_session.output_queue.get(timeout=1)
                    
                    if msg_type == 'error':
                        yield f"data: {json.dumps({'error': line})}\n\n"
                        break
                    
                    # Send each line as SSE event
                    yield f"data: {json.dumps({'text': line})}\n\n"
                    
                    # Check for completion heuristic
                    if line.strip() == '':
                        yield "data: {\"complete\": true}\n\n"
                        break
                        
                except queue.Empty:
                    # Timeout - likely complete
                    yield "data: {\"complete\": true}\n\n"
                    break
                    
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream'
    )
```

**5.2: Update Frontend for Streaming** (60 min)

Modify `chat.html` JavaScript:

```javascript
async function sendMessage() {
    // ... existing code ...
    
    const eventSource = new EventSource('/ask_stream?' + new URLSearchParams({
        prompt: prompt,
        session_id: sessionId
    }));
    
    let responseDiv = null;
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.complete) {
            eventSource.close();
            hideThinking();
            isThinking = false;
            document.getElementById('send-button').disabled = false;
            return;
        }
        
        if (data.error) {
            eventSource.close();
            hideThinking();
            addSystemMessage('Error: ' + data.error);
            isThinking = false;
            return;
        }
        
        // First chunk - create response message
        if (!responseDiv) {
            hideThinking();
            const chatContainer = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';
            messageDiv.innerHTML = `
                <div class="avatar">AI</div>
                <div class="message-content" id="streaming-response"></div>
            `;
            chatContainer.appendChild(messageDiv);
            responseDiv = document.getElementById('streaming-response');
        }
        
        // Append text chunk
        if (data.text) {
            responseDiv.textContent += data.text;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    };
    
    eventSource.onerror = () => {
        eventSource.close();
        hideThinking();
        addSystemMessage('Connection error');
        isThinking = false;
    };
}
```

**5.3: Add Copy-to-Clipboard for Code Blocks** (30 min)

Enhance message rendering to detect code blocks and add copy buttons.

**5.4: Add Clear Conversation Button** (20 min)

Add UI button to restart session (clear conversation history).

**5.5: Add Model Selector Dropdown** (45 min)

Allow users to switch models without restarting (pass to `/start_session`).

**5.6: Add File Upload for `@file`** (60 min)

UI button to upload file → saved to temp directory → `@tempfile` reference.

**5.7: Performance Testing** (30 min)

- Test with 50+ message conversation
- Check memory usage
- Test with large file `@references`

### Success Criteria

- ✅ Streaming works (text appears incrementally)
- ✅ Enhanced features improve UX
- ✅ No performance degradation

### Risks & Unknowns

**Risk**: SSE doesn't work in some browsers
- **Mitigation**: Fallback to Phase 4 approach (polling)

### Dependencies

- Phase 4 completed
- Browser supports EventSource API

---

## Post-Implementation: Maintenance & Future Work

### Adding New Features

1. **Theme Switcher** (Light/Dark mode)
2. **Conversation Export** (Save chat as Markdown/JSON)
3. **Multi-Session Support** (Tabs for multiple projects)
4. **Syntax Highlighting** (Detect code blocks, apply highlighting)

### Known Limitations

- No multi-user support (designed for single developer)
- No authentication (assumes trusted local environment)
- No mobile optimization (desktop-first design)
- Session data lost on Flask restart (unless GCLI checkpointing works)

### Upgrading GCLI

When new GCLI versions release:

1. Test non-interactive mode compatibility
2. Test `--checkpoint` flag behavior
3. Test Stream-JSON output format (if changed)
4. Update wrapper script if new flags needed

---

## Risk Mitigation Summary

| Risk                                    | Likelihood | Impact | Mitigation                                      |
| --------------------------------------- | ---------- | ------ | ----------------------------------------------- |
| @file doesn't work non-interactively    | MEDIUM     | HIGH   | Phase 1 validates - manual file injection fallback |
| Subprocess blocking freezes Flask       | LOW        | MEDIUM | Timeout + threading in Phase 3                  |
| Session subprocess crashes              | MEDIUM     | MEDIUM | Auto-restart + error notification               |
| Response completion detection fails     | HIGH       | MEDIUM | Phase 5 Stream-JSON improves reliability        |
| Directory validation too restrictive    | LOW        | LOW    | Make whitelist configurable                     |
| Port conflicts                          | LOW        | LOW    | Auto-increment port in wrapper                  |
| GCLI checkpoint not available           | MEDIUM     | LOW    | Sessions work, just not persistent across restarts |

---

## Scope Boundaries (Reminder)

### In Scope (MVP)

- ✅ ChatGPT-style web UI
- ✅ `@file` and `/command` support
- ✅ Multi-turn conversations
- ✅ Directory safety validation
- ✅ One-command launch (`geminiwebui`)
- ✅ Session management (in-memory)

### Out of Scope

- ❌ Multi-user support
- ❌ Authentication/authorization
- ❌ Database persistence
- ❌ Mobile app
- ❌ Production deployment (WSGI/Docker)
- ❌ Real-time collaboration
- ❌ Plugin system
- ❌ Syntax highlighting (Phase 5 optional)
- ❌ Extensive error recovery

---

## Session Handoff Checklist

When starting next coding session, provide:

1. ✅ This implementation plan
2. ✅ Current phase (e.g., "Starting Phase 2")
3. ✅ Previous phase results (e.g., `PHASE1_VALIDATION.md`)
4. ✅ Any errors/blockers encountered
5. ✅ **CRITICAL**: If Phase 1 fails, STOP and reassess approach

**When in doubt or need further information, always explicitly ask for files - don't make guesses or assumptions!**

---

## Critical Success Path

**Phase 1 is BLOCKING** - if `@file` doesn't work in non-interactive mode, entire approach must change.

**Fallback Architecture** (if Phase 1 fails):

```
Browser → Flask → Read files manually → Inject into prompt → GCLI
```

This works but loses GCLI's native `@file` preprocessing. Would require:
- Flask reimplements file discovery
- Manual path resolution
- Manual context assembly
- More complex, more fragile

**Prefer**: Native `@file` support (Phase 1 succeeds)  
**Fallback**: Manual file injection (Phase 1 fails)

---

**END OF IMPLEMENTATION PLAN**