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
  - Uses manual file injection for @file support (faster than native)
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

echo "╔═══════════════════════════════════════╗"
echo "  GCLI Web UI Launcher"
echo "╚═══════════════════════════════════════╝"
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
echo "  File Handling: Manual injection (optimized)"
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
echo "╔═══════════════════════════════════════╗"
echo "  GCLI Web UI is running!"
echo "  URL: http://localhost:$PORT"
echo "  Press Ctrl+C to stop"
echo "╚═══════════════════════════════════════╝"

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
        
        /* File info display */
        .file-info {
            font-size: 12px;
            color: #8e8ea0;
            margin-top: 8px;
            padding: 8px;
            background: #2a2b32;
            border-radius: 4px;
        }
        
        .file-info::before {
            content: "📂 ";
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
        
        // Send on Enter (Shift+Enter for new line)
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
        
        function addMessage(role, content, fileInfo = null) {
            const chatContainer = document.getElementById('chat-container');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            
            let fileInfoHtml = '';
            if (fileInfo && fileInfo.loaded_files && fileInfo.loaded_files.length > 0) {
                fileInfoHtml = `<div class="file-info">Loaded: ${fileInfo.loaded_files.join(', ')}</div>`;
            }
            
            messageDiv.innerHTML = `
                <div class="avatar">${role === 'user' ? 'U' : 'AI'}</div>
                <div class="message-content">
                    ${content}
                    ${fileInfoHtml}
                </div>
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
                    addMessage('assistant', data.response, {
                        loaded_files: data.loaded_files || [],
                        errors: data.errors || []
                    });
                    
                    // Show errors if any
                    if (data.errors && data.errors.length > 0) {
                        addSystemMessage('⚠️ Warnings: ' + data.errors.join('; '));
                    }
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
# 7. Verify: File contents processed, "Loaded: sample.py" shown
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
- ✅ `@file` and `@directory` support (manual injection)
- ✅ `/command` slash commands
- ✅ Session persistence (via GCLI checkpoints)
- ✅ Directory safety validation
- ✅ Fast file loading (no timeouts)

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

## How @file Works

This web UI uses **manual file injection** instead of GCLI's native @file support.

**Why?**
- GCLI's native @file uses tool calls in non-interactive mode
- Tool calls require multiple API roundtrips (30+ second delays)
- Manual injection is instant (<100ms file reading)

**How it works:**
```
User: "Explain @src/main.py"
  ↓
Flask reads src/main.py from disk
  ↓
Injects contents into prompt:
"Explain
```python
[actual file contents]
```
"
  ↓
Sends plain text to GCLI
  ↓
GCLI never sees @file syntax
```

**Tradeoffs:**
- ❌ Lost: Glob patterns (@src/**/*.py) - not yet implemented
- ❌ Lost: GCLI's smart context compression
- ✅ Gained: Instant file reading (no timeouts)
- ✅ Gained: Better error messages
- ✅ Gained: Full control over file handling

**Future work:**
We can implement glob patterns ourselves if needed (see Phase 5).

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
- Check Flask logs for file loading errors

**File loading errors:**
- Path traversal attempts are blocked
- Binary files are rejected
- Files over 5MB are rejected
- Check .gitignore/.geminiignore patterns

## Architecture

```
Browser
  ↕ HTTP/JSON
Flask Server (main.py)
  ↕ FilePreprocessor (manual @file injection)
  ↕ subprocess stdin/stdout
GCLI Process (--checkpoint --non-interactive)
  ↕
Gemini API
```

## Limitations

- Single user only (no multi-user support)
- No streaming in Phase 4 (shows "Thinking...")
- Session data not preserved across Flask restarts
- Glob patterns not yet implemented (coming in Phase 5)

## Development

See `ARCHITECTURE.md` for detailed system design.
See `docs/FILE_PREPROCESSING.md` for file injection implementation.
```

**4.7.1: Document File Injection Approach** (15 min)

This is already covered in the README.md section "How @file Works" above.

### Success Criteria

- ✅ `geminiwebui` command works from any directory
- ✅ Directory validation prevents system directory access
- ✅ UI matches ChatGPT aesthetic (dark theme, chat bubbles)
- ✅ Composer textarea auto-resizes
- ✅ Messages displayed in chronological order
- ✅ "Thinking..." indicator shows during processing
- ✅ Browser opens automatically
- ✅ Flask shutdown is clean (Ctrl+C)
- ✅ README clearly explains file injection approach and tradeoffs
- ✅ Loaded files displayed to user in UI
- ✅ File loading errors shown gracefully

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
- Phase 2 file preprocessor working
- Bash shell for wrapper script
- `~/bin` in PATH

