# GCLI Architecture - Condensed Reference for Web UI Integration

**Purpose**: Essential GCLI architecture knowledge for building Flask-based web interface  
**Audience**: This condensed doc for rapid context loading in coding sessions

---

## 1. Core Concepts

### What is GCLI?

Node.js-based CLI providing terminal-first access to Google's Gemini models. Supports:

- **Interactive mode**: Full-screen terminal UI with chat history
- **Non-interactive mode**: Scriptable, accepts stdin, outputs to stdout
- **Stream-JSON mode**: Structured JSON events for programmatic consumption

### Operational Modes (Critical for Web UI)

**Interactive Mode** (default):

```bash
gemini                    # Enters full terminal UI
gemini -m model-name      # With specific model
```

**Non-Interactive Mode** (what we'll use):

```bash
echo "prompt" | gemini --non-interactive
# Output: Plain text response to stdout
```

**Stream-JSON Mode** (ideal for web integration):

```bash
echo "prompt" | gemini --stream-json --non-interactive
# Output: Line-delimited JSON events:
# {"type":"text","text":"Response chunk..."}
# {"type":"tool_use","name":"read_file",...}
# {"type":"complete"}
```

---

## 2. File References & Commands

### `@` Commands (File/Directory Context)

**Critical Question**: Do these work in non-interactive mode? **MUST VALIDATE IN PHASE 1**

```bash
# @file - Include file contents
echo "Explain @src/main.py" | gemini --non-interactive

# @directory - Include directory listing
echo "Summarize @src" | gemini --non-interactive

# Multiple references
echo "Compare @fileA.py and @fileB.py" | gemini --non-interactive
```

**Implementation Detail**:

- Preprocessing happens **before** model sees prompt
- Uses GCLI's `cwd` (current working directory) for path resolution
- Subject to `.gitignore` and `.geminiignore` patterns

### `/` Slash Commands (CLI Commands)

Handled locally by GCLI (not sent to model):

- `/help` - Show help
- `/model` - Change model
- `/clear` - Clear conversation
- `/memory` - Manage conversation memory

**In non-interactive mode**: May not work or may behave differently. Test in Phase 1.

---

## 3. Working Directory Context

### How GCLI Determines Context

GCLI operates in the directory where it's invoked:

```bash
cd ~/my-project
gemini              # GCLI's cwd = ~/my-project
# @file references resolved relative to ~/my-project
```

### Setting cwd in Subprocess (Flask Integration)

```python
subprocess.Popen(
    ['gemini', '--non-interactive'],
    cwd='/path/to/project',  # Sets GCLI's working directory
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE
)
```

**Critical**: `@file` paths resolved relative to this `cwd`, not Flask's working directory.

---

## 4. Session Management & Checkpointing

### GCLI's Built-in Session Persistence

**Checkpoint Flag**:

```bash
gemini --checkpoint
# Saves conversation to ~/.gemini/sessions/<session-id>.json
```

**Session Files**:

- **Location**: `~/.gemini/sessions/` (or `.gemini/sessions/` in project)
- **Format**: JSON with full conversation history
- **Naming**: UUID-based session IDs
- **Retention**: Configurable via `settings.general.sessionRetention.maxAge`

**Session Resume**:

```bash
gemini --resume           # Lists recent sessions, select to resume
gemini --resume <id>      # Resume specific session
```

### Checkpoint in Non-Interactive Mode

**Unknown**: Does `--checkpoint` work with `--non-interactive`? **VALIDATE IN PHASE 3**

If yes:

```python
subprocess.Popen(['gemini', '--checkpoint', '--non-interactive'], ...)
# Conversation auto-saved on exit
```

If no:

- Implement manual conversation history in Flask (store prompts/responses)
- Pass full history to GCLI on each request (stateless per request, stateful via Flask)

---

## 5. Tool System (For Context Only)

### Built-in Tools

GCLI can execute tools during conversation:

**File Operations**:

- `read_file` - Max 20MB per file
- `write_file` - Modify/create files
- `glob` - File pattern matching
- `grep` - Search file contents (uses ripgrep)
- `ls` - Directory listing

**Execution**:

- `shell` - Execute shell commands (requires confirmation in interactive mode)

**Web**:

- `web_search` - Google search integration
- `web_fetch` - Download web content

**Confirmation Workflow**:

- Interactive mode: User must approve dangerous operations (shell, write_file)
- Non-interactive mode: **Unknown behavior** - might auto-deny or auto-approve

### Tool Output Limits

- **Character threshold**: 4MB default, dynamically adjusted to model context window
- **Line limits**: 2000 lines for text files, 1000 lines for tool results
- **File size**: 20MB max per file (won't load larger files)

---

## 6. Authentication (Not Critical for Web UI)

GCLI supports multiple auth methods:

- **Google OAuth** (best for individual developers)
- **Gemini API Key** (via `GEMINI_API_KEY` env var)
- **Vertex AI** (enterprise/GCP)

**For Web UI**: Authentication handled by GCLI subprocess, not Flask. Ensure GCLI authenticated before launching web UI:

```bash
gemini auth              # Interactive auth setup
# OR
export GEMINI_API_KEY="your-key"
gemini --non-interactive # Uses API key
```

---

## 7. Configuration System

### Configuration Hierarchy (High to Low Priority)

1. **Command-line flags**: `--model`, `--debug`, `--sandbox`
2. **Environment variables**: `GEMINI_MODEL`, `GEMINI_API_KEY`, `DEBUG`
3. **Workspace settings**: `.gemini/settings.json` (if workspace trusted)
4. **User settings**: `~/.gemini/settings.json`
5. **System defaults**

### Key Environment Variables

**Standard Prefix** (`GEMINI_*`):

- `GEMINI_API_KEY` - API authentication
- `GEMINI_MODEL` - Default model
- `GEMINI_SANDBOX` - Enable sandbox mode
- `GEMINI_TELEMETRY_ENABLED` - Telemetry opt-in

**Non-Prefixed** (compatibility):

- `DEBUG` / `DEBUG_MODE` - Debug logging
- `HTTPS_PROXY`, `HTTP_PROXY` - Proxy settings
- `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` - GCP config

### Settings File Location

```bash
~/.gemini/settings.json              # User-global
/path/to/project/.gemini/settings.json  # Project-specific
```

---

## 8. Sandbox System (macOS Only, Optional)

### Purpose

Isolates potentially untrusted operations using macOS App Sandbox.

### Invocation

```bash
gemini --sandbox
# GCLI relaunches itself with sandbox-exec
```

### Profiles (macOS `.sb` files)

Six profiles with varying restrictions:

- `permissive-open.sb` - Broad permissions, open network
- `permissive-closed.sb` - Broad permissions, no network
- `permissive-proxied.sb` - Broad permissions, proxied network
- `restrictive-open.sb` - Restricted, open network
- `restrictive-closed.sb` - Restricted, no network
- `restrictive-proxied.sb` - Restricted, proxied network

**For Web UI**: Sandbox optional, adds complexity. Skip unless security critical.

---

## 9. Stream-JSON Output Format

### Event Types

**Text Output**:

```json
{ "type": "text", "text": "Model response chunk..." }
```

**Tool Execution**:

```json
{"type":"tool_use","name":"read_file","args":{"path":"main.py"}}
{"type":"tool_result","result":"file contents..."}
```

**Completion**:

```json
{ "type": "complete" }
```

**Errors**:

```json
{ "type": "error", "message": "Error description" }
```

### Parsing Strategy (Flask Implementation)

```python
process = subprocess.Popen(['gemini', '--stream-json', '--non-interactive'], ...)

for line in process.stdout:
    event = json.loads(line)

    if event['type'] == 'text':
        # Send to browser via SSE
        yield f"data: {json.dumps(event)}\n\n"

    elif event['type'] == 'complete':
        break

    elif event['type'] == 'error':
        # Handle error
        raise RuntimeError(event['message'])
```

---

## 10. Performance Characteristics

### Startup Time

- **Cold start**: 2-5 seconds (model loading, auth validation)
- **Warm start**: <1 second (cached auth)

### Response Latency

- **Simple queries**: 1-3 seconds
- **Complex queries** (with tool calls): 5-15 seconds
- **File-heavy queries**: Depends on file size

### Memory Usage

- **Base**: ~100-200MB (Node.js process)
- **Per conversation**: ~1-10MB (depends on history length)
- **Long conversations**: Chat compression triggers at 50% of model context window

### Context Window Management

- **Compression threshold**: 50% of model token limit (configurable)
- **Preservation**: Keeps 30% of latest history uncompressed
- **Tool**: `ChatCompressionService` auto-compresses old messages

---

## 11. Error Handling

### Fatal Errors (Cause Immediate Exit)

- `FatalSandboxError` - Sandbox initialization failed
- `FatalAuthenticationError` - No valid credentials
- `FatalInputError` - Invalid input/arguments
- `FatalConfigError` - Configuration error
- `FatalToolExecutionError` - Critical tool failure

### Subprocess Error Codes

- **0**: Success
- **1**: General error
- **Non-zero**: Specific error (check stderr)

### Error Output

```bash
# stdout: Model responses, tool outputs
# stderr: Errors, warnings, debug logs
```

---

## 12. Key Files & Directories

### User Data

```
~/.gemini/
├── settings.json          # User settings
├── sessions/              # Conversation checkpoints
│   └── <uuid>.json
├── extensions/            # Installed extensions
└── trusted_folders.json   # Workspace trust settings
```

### Project-Specific

```
.gemini/
├── settings.json          # Project settings (if workspace trusted)
└── sessions/              # Project-specific sessions
```

---

## 13. Critical Unknowns for Web UI Project

### Phase 1 Validations (BLOCKING)

1. **Do `@file` commands work in `--non-interactive` mode?**

   - If NO: Major architecture change needed
   - Test: `echo "Explain @test.py" | gemini --non-interactive`

2. **Do `/` commands work in `--non-interactive` mode?**

   - If NO: Implement in Flask layer
   - Test: `echo "/help" | gemini --non-interactive`

3. **Is Stream-JSON available in installed GCLI version?**
   - Test: `gemini --help | grep stream-json`
   - If NO: Parse plain stdout (harder but doable)

### Phase 3 Validations

4. **Does `--checkpoint` work with `--non-interactive`?**

   - If NO: Implement session management in Flask
   - Test: Multi-request subprocess with checkpoint flag

5. **How to detect response completion in non-Stream-JSON mode?**
   - Heuristics: Empty line, timeout, prompt indicator
   - Fragile - Stream-JSON preferred

---

## 14. Subprocess Integration Patterns

### One-Shot (Phase 2 - Stateless)

```python
result = subprocess.run(
    ['gemini', '--non-interactive'],
    input=user_prompt,
    capture_output=True,
    text=True,
    cwd=working_dir,
    timeout=60
)

response = result.stdout
```

**Pros**: Simple, no state management  
**Cons**: No conversation memory, slower (cold start each time)

### Long-Lived (Phase 3 - Stateful)

```python
process = subprocess.Popen(
    ['gemini', '--checkpoint', '--non-interactive'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd=working_dir,
    bufsize=1  # Line-buffered
)

# Send prompts
process.stdin.write(prompt + '\n')
process.stdin.flush()

# Read responses
for line in process.stdout:
    handle_output(line)
```

**Pros**: Conversation continuity, faster (warm start)  
**Cons**: Complexity (threading, state management, error recovery)

### Stream-JSON (Phase 5 - Optimal)

```python
process = subprocess.Popen(
    ['gemini', '--stream-json', '--non-interactive'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    cwd=working_dir
)

for line in process.stdout:
    event = json.loads(line)

    if event['type'] == 'text':
        yield event['text']  # SSE to browser
    elif event['type'] == 'complete':
        break
```

**Pros**: Reliable parsing, structured events, real-time streaming  
**Cons**: Requires GCLI support for Stream-JSON

---

## 15. Safety & Validation

### Directory Validation (Flask Implementation)

```python
def is_safe_directory(path):
    abs_path = os.path.abspath(path)

    # Blacklist
    forbidden = ['/bin', '/usr', '/etc', '/var', '/sys', '/proc', '/']
    for forbidden_path in forbidden:
        if abs_path.startswith(forbidden_path):
            return False

    # Whitelist: Must be under home
    home = os.path.expanduser('~')
    return abs_path.startswith(home)
```

### Subprocess Timeouts

```python
# Hard timeout - kill subprocess
subprocess.run(..., timeout=60)

# Soft timeout - check periodically
start = time.time()
while time.time() - start < 60:
    if output_available():
        break
```

---

## 16. Debugging & Troubleshooting

### Enable Debug Logging

```bash
GEMINI_DEBUG=1 gemini --non-interactive
# OR
DEBUG=1 gemini --non-interactive
```

### Common Issues

**"Cannot find module"**:

- GCLI not in PATH
- Solution: `which gemini`, add to PATH

**"Authentication failed"**:

- No valid credentials
- Solution: `gemini auth` or set `GEMINI_API_KEY`

**"@file not found"**:

- Wrong working directory
- Relative path issues
- Solution: Use absolute paths, verify cwd

**Subprocess hangs**:

- Waiting for input that won't come
- Solution: Always use timeout, check stdin closure

**Response incomplete**:

- Fragile completion detection
- Solution: Use Stream-JSON mode, increase timeout

---

## 17. Quick Reference Commands

### Testing GCLI Modes

```bash
# Non-interactive
echo "test" | gemini --non-interactive

# Stream-JSON
echo "test" | gemini --stream-json --non-interactive

# With model
echo "test" | gemini -m gemini-flash --non-interactive

# With checkpoint
gemini --checkpoint --non-interactive < prompts.txt

# With working directory
cd /path/to/project && echo "@file.py" | gemini --non-interactive
```

### Subprocess Testing (Python)

```python
# Test 1: Basic invocation
import subprocess
result = subprocess.run(['gemini', '--version'], capture_output=True, text=True)
print(result.stdout)

# Test 2: Non-interactive prompt
result = subprocess.run(
    ['gemini', '--non-interactive'],
    input="What is 2+2?",
    capture_output=True,
    text=True,
    timeout=30
)
print(result.stdout)

# Test 3: @file in non-interactive
result = subprocess.run(
    ['gemini', '--non-interactive'],
    input="Explain @test.py",
    capture_output=True,
    text=True,
    cwd='/path/to/project'
)
print(result.stdout)
```

---

## 18. Phase-Specific Architecture Notes

### Phase 1: Validation

**Goal**: Prove `@file` and `/` work in non-interactive mode

**Critical Test**:

```bash
cd ~/test-project
echo "Explain @src/main.py" | gemini --non-interactive
```

**Success**: Response references actual file contents  
**Failure**: Response says "cannot access files" → STOP, reassess

### Phase 2: Minimal Flask Integration

**Architecture**:

```
Browser → Flask (/ask endpoint) → subprocess.run() → GCLI → Gemini API
                                        ↓
                                    Response
```

**Flow**:

1. User submits prompt via web form
2. Flask validates working directory
3. Flask spawns GCLI subprocess (`--non-interactive`)
4. Flask captures stdout, sends to browser
5. Subprocess exits

**Stateless**: Each request = new subprocess

### Phase 3: Session Management

**Architecture**:

```
Browser → Flask → Long-lived GCLI subprocess (--checkpoint)
                   ↓ stdin         ↑ stdout
                   Conversation maintained across requests
```

**Flow**:

1. Browser → `/start_session` → Flask spawns subprocess, returns session_id
2. Browser → `/ask` → Flask sends to subprocess stdin, reads stdout
3. Repeat step 2 for multi-turn conversation
4. Browser → `/end_session` → Flask terminates subprocess (GCLI checkpoints)

**Stateful**: One subprocess per session

### Phase 4: Production Wrapper

**Shell Script** (`geminiwebui`):

1. Validate current directory (safety checks)
2. Export `GCLI_WEBUI_DIR`, `GCLI_WEBUI_MODEL` env vars
3. Find available port (5000+)
4. Start Flask in background
5. Open browser
6. Wait for Ctrl+C, cleanup on exit

### Phase 5: Streaming (Optional)

**Architecture**:

```
Browser (EventSource) ← SSE ← Flask (generate) ← GCLI stdout (Stream-JSON)
```

**Flow**:

1. Flask spawns subprocess with `--stream-json`
2. Read stdout line-by-line (JSON events)
3. Forward each event to browser via SSE
4. Browser updates UI incrementally

---

## 19. Expected Limitations & Workarounds

### Limitation: No Multi-User Support

**Impact**: Only one user can use web UI at a time  
**Workaround**: Fine for personal use (project scope)

### Limitation: Sessions Lost on Flask Restart

**Impact**: Conversation history lost if Flask crashes  
**Workaround**: GCLI checkpoint saves sessions (if supported), or implement Flask-side persistence

### Limitation: No Syntax Highlighting

**Impact**: Code blocks display as plain text  
**Workaround**: Phase 5 enhancement (syntax highlighter library)

### Limitation: Response Completion Detection

**Impact**: May not detect when GCLI finished responding  
**Workaround**: Use Stream-JSON (`{"type":"complete"}` event)

---

## 20. Success Metrics

### Phase 1 Success

- ✅ `@file` loads actual file contents in non-interactive mode
- ✅ Model response references file contents (not hallucinated)
- ✅ Working directory context respected

### Phase 2 Success

- ✅ Prompt sent via web → response displayed in browser
- ✅ `@file` works through web UI
- ✅ Errors handled gracefully

### Phase 3 Success

- ✅ Multi-turn conversation maintains context
- ✅ Model remembers previous prompts
- ✅ Session terminates cleanly

### Phase 4 Success

- ✅ `geminiwebui` command works from any directory
- ✅ Directory validation prevents unsafe access
- ✅ UI matches ChatGPT aesthetic
- ✅ Browser auto-opens

### Phase 5 Success

- ✅ Real-time streaming (text appears incrementally)
- ✅ No performance degradation

---

**END OF CONDENSED ARCHITECTURE REFERENCE**

This document contains everything needed for implementing the web UI project. Reference specific sections as needed during coding sessions.
