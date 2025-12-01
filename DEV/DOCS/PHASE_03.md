# Phase 3: Session Management & Stateful Conversations (Day 3-4, 3-4 hours)

## Goal

Maintain long-lived GCLI subprocess per user session to enable multi-turn conversations, leveraging GCLI's built-in `--checkpoint` flag for persistence.

**NOTE**: With manual file injection, response parsing is simpler.
We don't need to handle tool call events, just plain text output.
This makes session management easier than originally planned.

## Tasks

**3.1: Study GCLI Checkpoint Mechanism** (30 min)

⚠️ **UPDATED EXPECTATIONS**: Since we're no longer using GCLI's @file tool calls,
checkpoint testing should focus on conversation memory, not file reference persistence.

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

**Additional test - with -p flag**:
```bash
# Test if --checkpoint works with -p (our non-interactive mode)
echo "What is 2+2?" | gemini --checkpoint -p
# Does this create a session file?

# If yes - can we resume?
# If no - document that checkpointing may not work in our mode
```

Document findings in `docs/CHECKPOINT_NOTES.md`

**3.2: Modify Flask for Long-Lived Subprocess** (90 min)

**SIMPLIFIED APPROACH**: With manual file injection, the subprocess only receives
plain text prompts. This means:
- No tool call events to parse
- No complex output filtering needed
- Response completion easier to detect (no mid-stream tool executions)

The session manager can be simpler than originally designed.

Create `app/session_manager.py`:

```python
"""
Session Manager: Maintains long-lived GCLI subprocesses
One subprocess per user session

SIMPLIFIED: With manual file injection, GCLI only receives/outputs plain text.
No tool call event handling needed.
"""

import subprocess
import threading
import queue
import uuid
import time
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
            ['gemini', '-m', self.model_name, '--checkpoint', '-p'],
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
        
        Phase 3 Note: With manual file injection, GCLI only receives plain text
        and only outputs plain text. No tool call events to handle!
        
        Completion heuristic: Wait for empty line or timeout.
        Still fragile - will improve with Stream-JSON in Phase 5.
        """
        response_lines = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                msg_type, line = self.output_queue.get(timeout=1)
                if msg_type == 'error':
                    raise RuntimeError(line)
                
                response_lines.append(line)
                
                # Heuristic: Response complete when we see empty line or prompt
                # This is fragile - will improve in Phase 5
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
from flask import Flask, session as flask_session, request, jsonify, render_template
from app.session_manager import session_manager
from app.file_processor import FilePreprocessor
from pathlib import Path
import os

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'

@app.route('/')
def index():
    """Serve minimal HTML form"""
    return render_template('index.html')

@app.route('/start_session', methods=['POST'])
def start_session():
    """Initialize GCLI session for user"""
    working_dir = request.json.get('cwd', os.getcwd())
    model_name = request.json.get('model', 'gemini-2.0-flash-exp')
    
    if not is_safe_directory(working_dir):
        return jsonify({'error': 'Unsafe directory'}), 400
    
    # Expand ~ to home directory
    working_dir = os.path.expanduser(working_dir)
    
    # Create GCLI session
    session_id = session_manager.create_session(working_dir, model_name)
    
    # Store in Flask session (cookie-based)
    flask_session['gcli_session_id'] = session_id
    
    return jsonify({
        'session_id': session_id,
        'working_dir': working_dir,
        'model': model_name,
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
        
        # Preprocess @file references
        preprocessor = FilePreprocessor(Path(gcli_session.working_dir))
        modified_prompt, loaded_files, errors = preprocessor.process_prompt(prompt)
        
        # Send to GCLI subprocess
        gcli_session.send_prompt(modified_prompt)
        
        # Wait for response
        response = gcli_session.get_response(timeout=60)
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'loaded_files': loaded_files,
            'errors': errors,
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

def is_safe_directory(path):
    """Validate directory is safe to run GCLI in"""
    abs_path = os.path.abspath(os.path.expanduser(path))
    
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

**3.4: Update HTML for Session Flow** (30 min)

Modify `app/templates/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>GCLI Web UI - Phase 3</title>
    <style>
        body { font-family: monospace; padding: 20px; }
        #prompt { width: 100%; height: 100px; }
        #response { 
            margin-top: 20px; 
            padding: 10px; 
            background: #f0f0f0;
            white-space: pre-wrap;
        }
        #status { color: blue; margin: 10px 0; }
        .file-info {
            background: #e8f4f8;
            padding: 8px;
            margin: 10px 0;
            border-left: 4px solid #2196F3;
            font-size: 14px;
        }
        .error-info {
            background: #fff3cd;
            padding: 8px;
            margin: 10px 0;
            border-left: 4px solid #ffc107;
            font-size: 14px;
        }
        .session-info {
            background: #d4edda;
            padding: 8px;
            margin: 10px 0;
            border-left: 4px solid #28a745;
            font-size: 14px;
        }
        .conversation {
            border: 1px solid #ddd;
            padding: 10px;
            margin: 10px 0;
            max-height: 400px;
            overflow-y: auto;
        }
        .message {
            margin: 10px 0;
            padding: 8px;
            border-radius: 4px;
        }
        .user-message {
            background: #e3f2fd;
            text-align: right;
        }
        .assistant-message {
            background: #f5f5f5;
        }
    </style>
</head>
<body>
    <h1>GCLI Web UI - Session Management (Phase 3)</h1>
    
    <div>
        <label>Working Directory:</label>
        <input type="text" id="cwd" value="~" style="width: 100%;">
    </div>
    
    <div>
        <label>Model:</label>
        <select id="model">
            <option value="gemini-2.0-flash-exp">gemini-2.0-flash-exp</option>
            <option value="gemini-1.5-pro">gemini-1.5-pro</option>
            <option value="gemini-1.5-flash">gemini-1.5-flash</option>
        </select>
    </div>
    
    <button onclick="startSession()" id="start-btn">Start Session</button>
    <button onclick="endSession()" id="end-btn" disabled>End Session</button>
    
    <div id="session-info" class="session-info" style="display: none;"></div>
    
    <div class="conversation" id="conversation">
        <p style="color: #888;">Session not started. Click "Start Session" to begin.</p>
    </div>
    
    <div>
        <label>Prompt (use @filename to reference files):</label>
        <textarea id="prompt" placeholder="Enter prompt (try: Explain @file.py)" disabled></textarea>
    </div>
    
    <button onclick="sendPrompt()" id="send-btn" disabled>Send to GCLI</button>
    
    <div id="file-info" class="file-info" style="display: none;"></div>
    <div id="status"></div>
    
    <script>
        let currentSessionId = null;
        let isSending = false;
        
        async function startSession() {
            const cwd = document.getElementById('cwd').value;
            const model = document.getElementById('model').value;
            const statusDiv = document.getElementById('status');
            
            statusDiv.textContent = 'Starting session...';
            
            try {
                const response = await fetch('/start_session', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({cwd, model})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentSessionId = data.session_id;
                    
                    document.getElementById('session-info').style.display = 'block';
                    document.getElementById('session-info').textContent = 
                        `✅ Session active: ${data.session_id.substring(0, 8)}... | Model: ${data.model} | Dir: ${data.working_dir}`;
                    
                    document.getElementById('prompt').disabled = false;
                    document.getElementById('send-btn').disabled = false;
                    document.getElementById('start-btn').disabled = true;
                    document.getElementById('end-btn').disabled = false;
                    
                    document.getElementById('conversation').innerHTML = '<p style="color: #888;">Session started. Send your first message.</p>';
                    
                    statusDiv.textContent = 'Session ready!';
                    statusDiv.style.color = 'green';
                } else {
                    statusDiv.textContent = 'Error: ' + data.error;
                    statusDiv.style.color = 'red';
                }
            } catch (error) {
                statusDiv.textContent = 'Error: ' + error.message;
                statusDiv.style.color = 'red';
            }
        }
        
        async function endSession() {
            const statusDiv = document.getElementById('status');
            
            statusDiv.textContent = 'Ending session...';
            
            try {
                await fetch('/end_session', {method: 'POST'});
                
                currentSessionId = null;
                document.getElementById('session-info').style.display = 'none';
                document.getElementById('prompt').disabled = true;
                document.getElementById('send-btn').disabled = true;
                document.getElementById('start-btn').disabled = false;
                document.getElementById('end-btn').disabled = true;
                
                document.getElementById('conversation').innerHTML = '<p style="color: #888;">Session ended. Start a new session to continue.</p>';
                
                statusDiv.textContent = 'Session ended.';
                statusDiv.style.color = 'blue';
            } catch (error) {
                statusDiv.textContent = 'Error ending session: ' + error.message;
                statusDiv.style.color = 'red';
            }
        }
        
        function addMessage(role, content) {
            const conversation = document.getElementById('conversation');
            
            if (conversation.querySelector('p[style*="color: #888"]')) {
                conversation.innerHTML = '';
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}-message`;
            messageDiv.textContent = content;
            conversation.appendChild(messageDiv);
            conversation.scrollTop = conversation.scrollHeight;
        }
        
        async function sendPrompt() {
            if (isSending || !currentSessionId) return;
            
            const prompt = document.getElementById('prompt').value.trim();
            if (!prompt) return;
            
            const statusDiv = document.getElementById('status');
            const fileInfoDiv = document.getElementById('file-info');
            
            isSending = true;
            document.getElementById('send-btn').disabled = true;
            
            // Add user message to conversation
            addMessage('user', prompt);
            
            statusDiv.textContent = 'Processing @file references and thinking...';
            statusDiv.style.color = 'blue';
            fileInfoDiv.style.display = 'none';
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Add assistant response to conversation
                    addMessage('assistant', data.response);
                    
                    // Show loaded files
                    if (data.loaded_files && data.loaded_files.length > 0) {
                        fileInfoDiv.style.display = 'block';
                        fileInfoDiv.textContent = '📂 Loaded files: ' + data.loaded_files.join(', ');
                    }
                    
                    // Show errors
                    if (data.errors && data.errors.length > 0) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'error-info';
                        errorDiv.textContent = '⚠️ Warnings: ' + data.errors.join('; ');
                        fileInfoDiv.parentNode.insertBefore(errorDiv, fileInfoDiv.nextSibling);
                    }
                    
                    statusDiv.textContent = 'Response received';
                    statusDiv.style.color = 'green';
                    
                    // Clear prompt
                    document.getElementById('prompt').value = '';
                } else {
                    statusDiv.textContent = 'Error: ' + data.error;
                    statusDiv.style.color = 'red';
                }
            } catch (error) {
                statusDiv.textContent = 'Error: ' + error.message;
                statusDiv.style.color = 'red';
            } finally {
                isSending = false;
                document.getElementById('send-btn').disabled = false;
            }
        }
        
        // Allow Ctrl+Enter to submit
        document.getElementById('prompt').addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                sendPrompt();
            }
        });
        
        // End session when browser closes
        window.addEventListener('beforeunload', async () => {
            if (currentSessionId) {
                await fetch('/end_session', {method: 'POST'});
            }
        });
    </script>
</body>
</html>
```

**3.5: Test Multi-Turn Conversation** (45 min)

Test sequence:
1. Start web UI
2. Set working dir: `~/test-webui-project`
3. Click "Start Session"
4. Send: "What is 2+2?"
5. **Verify response**
6. Send: "What was my previous question?" (tests conversation memory)
7. **CRITICAL**: Verify model references "2+2" question
8. Send: "Explain the greet function from sample.py"  # Don't use @file again
9. Send: "Add error handling to that function"
10. **Verify**: Model references `greet()` function from earlier in conversation

**Why this change in step 8-10**: Since we manually inject files, each @file creates a new
injection. Testing conversation memory doesn't require re-reading files.

**Additional tests**:
- Test multiple @file references in single prompt
- Test @file with conversation context
- Test long conversation (10+ messages)
- Test session termination and restart

**3.6: Test Session Persistence** (30 min)

1. Start conversation
2. Send 3-4 prompts
3. Click "End Session"
4. Click "Start Session" (new session)
5. **Expected**: Fresh conversation (no memory from previous session)

**Test GCLI checkpoint behavior** (if supported):
1. Start session, send prompts
2. End session via button
3. Check `~/.gemini/sessions/` for session files
4. Document whether checkpoints are created
5. If checkpoints exist, note session ID format

**3.7: Document Session Behavior** (20 min)

Create `docs/SESSION_TESTING.md`:

```markdown
# Session Management Testing

## Multi-Turn Conversation
- [ ] Model remembers previous prompts
- [ ] Context maintained across requests
- [ ] @file references work in conversation
- [ ] File injection works in multi-turn context

## Session Lifecycle
- [ ] Session starts cleanly
- [ ] Subprocess remains alive across requests
- [ ] Session terminates gracefully
- [ ] GCLI checkpoint saves on termination (if supported)

## Edge Cases
- [ ] What happens if subprocess dies mid-session?
- [ ] What happens on Flask restart?
- [ ] What happens on browser refresh?
- [ ] Multiple sessions in different browser tabs?

## Issues Found

### File Injection in Sessions
- [ ] Does @file work in multi-turn conversations?
- [ ] Should we cache file contents per session?
- [ ] Do file contents get re-read each time @file used?

### Performance
- [ ] Does file injection slow down conversation flow?
- [ ] Should we implement file content caching?
- [ ] Response latency: [X seconds per message]
- [ ] Memory usage: [observe with `top` during 20+ message conversation]

## Checkpoint Findings

**Does --checkpoint work with -p flag?**
- Answer: YES/NO
- Evidence: [check ~/.gemini/sessions/ for files]
- Session file format: [JSON/other]
- Can sessions be resumed? [YES/NO]

## Known Limitations
[Document any issues that won't be fixed in Phase 3]

## Next Steps for Phase 4
[List any improvements needed]
```

## Success Criteria

- ✅ GCLI subprocess starts and remains alive
- ✅ Multiple prompts sent to same subprocess
- ✅ Model maintains conversation context
- ✅ Session terminates cleanly on browser close
- ✅ GCLI checkpoint mechanism works (if supported)
- ✅ No memory leaks (test with 20+ prompts)
- ✅ File injection works consistently across conversation turns
- ✅ @file can be used multiple times in session without issues

## Risks & Unknowns

**MAJOR RISK RESOLVED**: Phase 1 confirmed @file timeouts.
Phase 2 proved manual file injection works.
Phase 3 just needs to integrate file injection with sessions.

**Risk**: Response completion detection is fragile
- **Impact**: HIGH - UI might show partial responses or hang
- **Current approach**: Heuristic (empty line detection)
- **Mitigation**: Phase 5 will use Stream-JSON for reliable parsing
- **Fallback**: Add timeout, show "Response may be incomplete" warning

**Risk**: Subprocess crashes mid-conversation
- **Impact**: MEDIUM - user loses session
- **Detection**: Monitor `process.poll()` status
- **Mitigation**: Auto-restart subprocess, notify user

**Unknown**: Does `--checkpoint` work with `-p` flag (our mode)?
- **Test**: Task 3.1 validation with `-p` flag specifically
- **Impact**: If fails, sessions won't persist across restarts
- **Mitigation**: Acceptable for MVP - in-memory sessions sufficient

**Unknown**: Should we cache file contents during session?
- **Scenario**: User sends "@file.py", then later "@file.py" again
- **Options**: 
  1. Re-read file each time (always fresh, but slower)
  2. Cache for session (faster, but may miss edits)
- **Decision**: Start with option 1 (always re-read), optimize later if needed

**Risk**: Threading/queue issues under load
- **Impact**: MEDIUM - race conditions, deadlocks
- **Mitigation**: Extensive testing in Task 3.5
- **Fallback**: Simplify to synchronous blocking (Phase 2 approach)

**Risk**: Multiple browser tabs create multiple sessions
- **Impact**: LOW - higher memory usage, but should work
- **Detection**: Open two tabs, start sessions in each
- **Expected**: Two separate GCLI subprocesses, two sessions

## Rollback Strategy

If long-lived subprocess approach fails:

1. **Revert to Phase 2 approach**: One subprocess per request (stateless)
2. **Document limitation**: No conversation memory
3. **Future improvement**: Implement manual conversation history in Flask (store in file/DB)

If threading causes issues:
1. **Simplify to blocking reads**: Remove output queue
2. **Tradeoff**: Flask blocks during GCLI response (acceptable for solo use)

If session management complexity too high:
1. **Simplify**: Remove session manager, use single global subprocess
2. **Limitation**: Only one user at a time (already expected)
3. **Benefit**: Much simpler code

## Dependencies

- Phase 2 completed successfully (manual file injection works)
- GCLI `--checkpoint` flag available (verify in Task 3.1)
- Python threading module (standard library)
- Python queue module (standard library)