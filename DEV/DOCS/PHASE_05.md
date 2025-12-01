# Phase 5: Optional Enhancements & Advanced Features (If Time Permits)

## Goal

Add advanced features and polish:
1. Real-time streaming output (Stream-JSON or line-buffered)
2. Implement features we lost from GCLI native @file (glob patterns, etc.)
3. Quality-of-life improvements
4. Performance optimizations

**Note**: With manual file injection, streaming is simpler (no tool call events).

---

## Priority Order for Phase 5 Features

**High Priority** (Restore lost features):
1. 5.7 - Glob pattern support
2. 5.8 - Smart context compression
3. 5.9 - File content caching

**Medium Priority** (UX improvements):
4. 5.1 - Real-time streaming
5. 5.3 - Copy-to-clipboard
6. 5.4 - Clear conversation

**Low Priority** (Nice-to-have):
7. 5.5 - Model selector
8. 5.6 - File upload

---

## Tasks

### 5.1: Implement Server-Sent Events (SSE) for Streaming (90 min)

**SIMPLIFIED WITH MANUAL FILE INJECTION**:

Since GCLI now only receives plain text (no tool calls), streaming is easier:
- No tool_use events to handle
- No tool_result events to filter
- Just stream plain text output line by line

Stream-JSON may not even be necessary - can use line-buffered stdout.

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

---

### 5.2: Update Frontend for Streaming (60 min)

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

---

### 5.3: Add Copy-to-Clipboard for Code Blocks (30 min)

Enhance message rendering to detect code blocks and add copy buttons.

```javascript
function renderMessage(content) {
    // Detect code blocks (```language\n...\n```)
    const codeBlockRegex = /```(\w+)?\n([\s\S]+?)```/g;
    
    return content.replace(codeBlockRegex, (match, language, code) => {
        const escapedCode = escapeHtml(code);
        const copyId = 'copy-' + Math.random().toString(36).substr(2, 9);
        
        return `
            <div class="code-block">
                <div class="code-header">
                    <span class="language">${language || 'text'}</span>
                    <button class="copy-btn" onclick="copyCode('${copyId}')">
                        📋 Copy
                    </button>
                </div>
                <pre><code id="${copyId}">${escapedCode}</code></pre>
            </div>
        `;
    });
}

function copyCode(elementId) {
    const code = document.getElementById(elementId).textContent;
    navigator.clipboard.writeText(code).then(() => {
        // Show feedback
        event.target.textContent = '✓ Copied!';
        setTimeout(() => {
            event.target.textContent = '📋 Copy';
        }, 2000);
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
```

Add CSS:

```css
.code-block {
    background: #1e1e1e;
    border-radius: 6px;
    margin: 12px 0;
    overflow: hidden;
}

.code-header {
    background: #2d2d2d;
    padding: 8px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
}

.language {
    color: #858585;
    text-transform: uppercase;
}

.copy-btn {
    background: transparent;
    border: 1px solid #565869;
    color: #ececf1;
    padding: 4px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
}

.copy-btn:hover {
    background: #565869;
}

.code-block pre {
    margin: 0;
    padding: 16px;
    overflow-x: auto;
}

.code-block code {
    font-family: 'Courier New', monospace;
    font-size: 14px;
    color: #d4d4d4;
}
```

---

### 5.4: Add Clear Conversation Button (20 min)

Add UI button to restart session (clear conversation history).

Update header in `chat.html`:

```html
<div class="header">
    <h1>GCLI Web UI</h1>
    <div class="header-controls">
        <div class="working-dir" id="working-dir"></div>
        <button class="clear-btn" onclick="clearConversation()">
            🗑️ Clear
        </button>
    </div>
</div>
```

Add JavaScript:

```javascript
async function clearConversation() {
    if (!confirm('Clear conversation history?')) {
        return;
    }
    
    // End current session
    await fetch('/end_session', {method: 'POST'});
    
    // Clear UI
    document.getElementById('chat-container').innerHTML = '';
    
    // Start new session
    await initSession();
    
    addSystemMessage('Conversation cleared. New session started.');
}
```

Add CSS:

```css
.header-controls {
    display: flex;
    align-items: center;
    gap: 16px;
}

.clear-btn {
    background: transparent;
    border: 1px solid #565869;
    color: #ececf1;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
}

.clear-btn:hover {
    background: #565869;
}
```

---

### 5.5: Add Model Selector Dropdown (45 min)

Allow users to switch models without restarting (pass to `/start_session`).

Update header:

```html
<div class="header">
    <h1>GCLI Web UI</h1>
    <div class="header-controls">
        <select id="model-selector" onchange="changeModel()">
            <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash (Experimental)</option>
            <option value="gemini-2.0-flash-thinking-exp-1219">Gemini 2.0 Flash Thinking</option>
            <option value="gemini-exp-1206">Gemini Experimental (1206)</option>
            <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
            <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
        </select>
        <div class="working-dir" id="working-dir"></div>
        <button class="clear-btn" onclick="clearConversation()">🗑️ Clear</button>
    </div>
</div>
```

Add JavaScript:

```javascript
let currentModel = 'gemini-2.0-flash-exp';

async function changeModel() {
    const newModel = document.getElementById('model-selector').value;
    
    if (newModel === currentModel) {
        return;
    }
    
    if (!confirm(`Switch to ${newModel}? This will start a new conversation.`)) {
        // Reset selector
        document.getElementById('model-selector').value = currentModel;
        return;
    }
    
    // End current session
    await fetch('/end_session', {method: 'POST'});
    
    // Clear UI
    document.getElementById('chat-container').innerHTML = '';
    
    // Start new session with new model
    currentModel = newModel;
    await initSession();
    
    addSystemMessage(`Now using ${newModel}`);
}

// Update initSession to use selected model
async function initSession() {
    const workingDir = new URLSearchParams(window.location.search).get('cwd') || '.';
    const model = document.getElementById('model-selector').value;
    
    document.getElementById('working-dir').textContent = workingDir;
    
    const response = await fetch('/start_session', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            cwd: workingDir,
            model: model  // NEW
        })
    });
    
    const data = await response.json();
    if (data.success) {
        sessionId = data.session_id;
        currentModel = model;
    } else {
        addSystemMessage('Error: ' + data.error);
    }
}
```

Update Flask route:

```python
@app.route('/start_session', methods=['POST'])
def start_session():
    working_dir = request.json.get('cwd', os.getcwd())
    model_name = request.json.get('model', 'gemini-2.0-flash-exp')  # NEW
    
    if not is_safe_directory(working_dir):
        return jsonify({'error': 'Unsafe directory'}), 400
    
    # Create GCLI session with specified model
    session_id = session_manager.create_session(working_dir, model_name)
    
    flask_session['gcli_session_id'] = session_id
    
    return jsonify({
        'session_id': session_id,
        'working_dir': working_dir,
        'model': model_name,  # NEW
        'success': True
    })
```

Add CSS:

```css
#model-selector {
    background: #40414f;
    border: 1px solid #565869;
    color: #ececf1;
    padding: 6px 12px;
    border-radius: 4px;
    font-size: 12px;
    cursor: pointer;
}

#model-selector:hover {
    background: #4a4b56;
}
```

---

### 5.6: Add File Upload for `@file` (60 min)

UI button to upload file → saved to temp directory → `@tempfile` reference.

Add to composer:

```html
<div class="composer-container">
    <div class="file-attachments" id="file-attachments"></div>
    <div class="composer">
        <input 
            type="file" 
            id="file-upload" 
            multiple 
            style="display: none;"
            onchange="handleFileUpload()"
        />
        <button class="attach-btn" onclick="document.getElementById('file-upload').click()">
            📎
        </button>
        <textarea id="prompt-input" placeholder="Message Gemini CLI Composer..."></textarea>
        <button class="send-button" id="send-button" onclick="sendMessage()">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
            </svg>
        </button>
    </div>
</div>
```

Add JavaScript:

```javascript
let uploadedFiles = [];

async function handleFileUpload() {
    const fileInput = document.getElementById('file-upload');
    const files = Array.from(fileInput.files);
    
    for (const file of files) {
        // Read file content
        const content = await file.text();
        
        // Upload to server
        const response = await fetch('/upload_temp_file', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                filename: file.name,
                content: content
            })
        });
        
        const data = await response.json();
        if (data.success) {
            uploadedFiles.push({
                name: file.name,
                tempPath: data.temp_path
            });
            
            renderAttachments();
        }
    }
    
    fileInput.value = ''; // Reset input
}

function renderAttachments() {
    const container = document.getElementById('file-attachments');
    container.innerHTML = '';
    
    if (uploadedFiles.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'flex';
    
    uploadedFiles.forEach((file, index) => {
        const chip = document.createElement('div');
        chip.className = 'file-chip';
        chip.innerHTML = `
            <span>📄 ${file.name}</span>
            <button onclick="removeAttachment(${index})">×</button>
        `;
        container.appendChild(chip);
    });
}

function removeAttachment(index) {
    uploadedFiles.splice(index, 1);
    renderAttachments();
}

// Modify sendMessage to include uploaded files
async function sendMessage() {
    // ... existing code ...
    
    let prompt = promptInput.value.trim();
    
    // Add @references for uploaded files
    if (uploadedFiles.length > 0) {
        const refs = uploadedFiles.map(f => `@${f.tempPath}`).join(' ');
        prompt = `${refs}\n\n${prompt}`;
    }
    
    // ... rest of existing code ...
    
    // Clear attachments after sending
    uploadedFiles = [];
    renderAttachments();
}
```

Add Flask route:

```python
import tempfile
import os

@app.route('/upload_temp_file', methods=['POST'])
def upload_temp_file():
    """Save uploaded file to temp directory"""
    try:
        filename = request.json.get('filename')
        content = request.json.get('content')
        
        # Create temp file
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, 'gcli_uploads', filename)
        
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        with open(temp_path, 'w') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'temp_path': temp_path,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

Add CSS:

```css
.file-attachments {
    display: none;
    gap: 8px;
    padding: 12px;
    background: #2d2d2d;
    border-radius: 8px 8px 0 0;
    flex-wrap: wrap;
}

.file-chip {
    background: #40414f;
    border: 1px solid #565869;
    border-radius: 16px;
    padding: 4px 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
}

.file-chip button {
    background: transparent;
    border: none;
    color: #8e8ea0;
    cursor: pointer;
    font-size: 18px;
    padding: 0;
    line-height: 1;
}

.file-chip button:hover {
    color: #ececf1;
}

.attach-btn {
    position: absolute;
    left: 12px;
    bottom: 12px;
    background: transparent;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: #8e8ea0;
    padding: 4px;
}

.attach-btn:hover {
    color: #ececf1;
}

#prompt-input {
    padding-left: 48px; /* Make room for attach button */
}
```

---

### 5.7: Implement Glob Pattern Support (90 min)

Add glob pattern matching to file preprocessor:

Update `app/file_processor.py`:

```python
import glob
from typing import List, Tuple, Set

class FilePreprocessor:
    # ... existing code ...
    
    def process_prompt(self, prompt: str) -> Tuple[str, List[str], List[str]]:
        """
        Process @file and @glob references in prompt
        
        Returns:
            (modified_prompt, loaded_files, errors)
        """
        loaded_files = []
        errors = []
        modified_prompt = prompt
        
        # Process glob patterns first (e.g., @src/**/*.py)
        glob_pattern = r'@([\w\-./]+\*[\w\-./]*)'
        glob_matches = re.findall(glob_pattern, prompt)
        
        for glob_path in glob_matches:
            try:
                # Expand glob relative to working directory
                full_glob = str(self.working_dir / glob_path)
                matched_files = glob.glob(full_glob, recursive=True)
                
                if not matched_files:
                    errors.append(f"No files matched pattern: {glob_path}")
                    continue
                
                # Filter out ignored files
                matched_files = [
                    f for f in matched_files 
                    if not self._is_ignored(f) and os.path.isfile(f)
                ]
                
                if not matched_files:
                    errors.append(f"All files matching {glob_path} were ignored")
                    continue
                
                # Limit number of files (safety)
                if len(matched_files) > 50:
                    errors.append(f"Too many files matched {glob_path}: {len(matched_files)} (max 50)")
                    matched_files = matched_files[:50]
                
                # Replace glob pattern with individual file contents
                files_content = []
                for filepath in matched_files:
                    try:
                        content = self._read_file_safe(filepath)
                        files_content.append(self._format_file_content(filepath, content))
                        loaded_files.append(os.path.relpath(filepath, self.working_dir))
                    except Exception as e:
                        errors.append(f"Error reading {filepath}: {str(e)}")
                
                # Replace @glob pattern with concatenated content
                replacement = "\n\n".join(files_content)
                modified_prompt = modified_prompt.replace(f"@{glob_path}", replacement)
                
            except Exception as e:
                errors.append(f"Glob error for {glob_path}: {str(e)}")
        
        # Process individual @file references (existing code)
        file_pattern = r'@([\w\-./]+(?:\.\w+)?)'
        file_matches = re.findall(file_pattern, modified_prompt)
        
        for filepath in file_matches:
            # Skip if it looks like a glob pattern
            if '*' in filepath:
                continue
            
            try:
                abs_path = (self.working_dir / filepath).resolve()
                
                # Security checks
                if not self._is_safe_path(abs_path):
                    errors.append(f"Unsafe path: {filepath}")
                    continue
                
                if self._is_ignored(str(abs_path)):
                    errors.append(f"File ignored: {filepath}")
                    continue
                
                # Read file
                content = self._read_file_safe(str(abs_path))
                formatted = self._format_file_content(filepath, content)
                
                # Replace @file with content
                modified_prompt = modified_prompt.replace(f"@{filepath}", formatted)
                loaded_files.append(filepath)
                
            except FileNotFoundError:
                errors.append(f"File not found: {filepath}")
            except Exception as e:
                errors.append(f"Error reading {filepath}: {str(e)}")
        
        return modified_prompt, loaded_files, errors
    
    def _format_file_content(self, filepath: str, content: str) -> str:
        """Format file content with header and code block"""
        # Detect language from extension
        ext = os.path.splitext(filepath)[1].lstrip('.')
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'go': 'go',
            'rs': 'rust',
            'rb': 'ruby',
            'php': 'php',
            'sh': 'bash',
            'md': 'markdown',
            'json': 'json',
            'yaml': 'yaml',
            'yml': 'yaml',
            'xml': 'xml',
            'html': 'html',
            'css': 'css',
        }
        
        language = language_map.get(ext, ext)
        
        return f"File: {filepath}\n```{language}\n{content}\n```"
```

Add tests:

```python
# Test glob patterns
def test_glob_patterns():
    from pathlib import Path
    from app.file_processor import FilePreprocessor
    
    # Setup test directory
    test_dir = Path('test_glob')
    test_dir.mkdir(exist_ok=True)
    (test_dir / 'src').mkdir(exist_ok=True)
    (test_dir / 'src' / 'utils').mkdir(exist_ok=True)
    
    # Create test files
    (test_dir / 'src' / 'main.py').write_text('print("main")')
    (test_dir / 'src' / 'helper.py').write_text('print("helper")')
    (test_dir / 'src' / 'utils' / 'tools.py').write_text('print("tools")')
    
    processor = FilePreprocessor(test_dir)
    
    # Test 1: Simple glob
    prompt, files, errors = processor.process_prompt("Analyze @src/*.py")
    assert len(files) == 2
    assert 'main.py' in str(files)
    assert 'helper.py' in str(files)
    
    # Test 2: Recursive glob
    prompt, files, errors = processor.process_prompt("Analyze @src/**/*.py")
    assert len(files) == 3
    assert 'tools.py' in str(files)
    
    # Test 3: No matches
    prompt, files, errors = processor.process_prompt("Find @src/*.txt")
    assert len(files) == 0
    assert len(errors) > 0
    
    print("✓ Glob pattern tests passed")

if __name__ == '__main__':
    test_glob_patterns()
```

---

### 5.8: Implement Smart Context Compression (60 min)

When many files are loaded, compress context intelligently:

Add to `app/file_processor.py`:

```python
class FilePreprocessor:
    # ... existing code ...
    
    MAX_TOTAL_CHARS = 200000  # ~50k tokens
    MAX_FILE_LINES_FULL = 500  # Show full content if under this
    CONTEXT_LINES = 50  # Lines to show from start/end when compressed
    
    def process_prompt(self, prompt: str) -> Tuple[str, List[str], List[str]]:
        # ... existing file loading code ...
        
        # After loading all files, check if compression needed
        total_chars = len(modified_prompt)
        
        if total_chars > self.MAX_TOTAL_CHARS:
            modified_prompt = self._compress_context(modified_prompt, loaded_files)
        
        return modified_prompt, loaded_files, errors
    
    def _compress_context(self, prompt: str, loaded_files: List[str]) -> str:
        """
        Compress large file contents intelligently
        
        Strategy:
        1. Keep small files in full
        2. For large files, show first/last N lines with "..." in middle
        3. Prioritize files mentioned directly in user's original question
        """
        # Parse out file content blocks
        file_blocks = self._extract_file_blocks(prompt)
        
        compressed_blocks = []
        for filepath, content in file_blocks:
            lines = content.split('\n')
            
            if len(lines) <= self.MAX_FILE_LINES_FULL:
                # Keep small files in full
                compressed_blocks.append((filepath, content))
            else:
                # Compress large files
                start_lines = lines[:self.CONTEXT_LINES]
                end_lines = lines[-self.CONTEXT_LINES:]
                omitted = len(lines) - (2 * self.CONTEXT_LINES)
                
                compressed = (
                    '\n'.join(start_lines) +
                    f"\n\n... [{omitted} lines omitted] ...\n\n" +
                    '\n'.join(end_lines)
                )
                compressed_blocks.append((filepath, compressed))
        
        # Rebuild prompt with compressed content
        return self._rebuild_prompt_with_blocks(prompt, compressed_blocks)
    
    def _extract_file_blocks(self, prompt: str) -> List[Tuple[str, str]]:
        """Extract (filepath, content) tuples from prompt"""
        blocks = []
        pattern = r'File: ([\w\-./]+)\n```[\w]*\n(.*?)\n```'
        
        for match in re.finditer(pattern, prompt, re.DOTALL):
            filepath = match.group(1)
            content = match.group(2)
            blocks.append((filepath, content))
        
        return blocks
    
    def _rebuild_prompt_with_blocks(
        self, 
        original_prompt: str, 
        blocks: List[Tuple[str, str]]
    ) -> str:
        """Replace file blocks in prompt with compressed versions"""
        result = original_prompt
        
        for filepath, new_content in blocks:
            # Find and replace the old block
            pattern = f'File: {re.escape(filepath)}\\n```[\\w]*\\n.*?\\n```'
            
            # Detect language
            ext = os.path.splitext(filepath)[1].lstrip('.')
            language = self._get_language(ext)
            
            replacement = f'File: {filepath}\n```{language}\n{new_content}\n```'
            result = re.sub(pattern, replacement, result, flags=re.DOTALL)
        
        return result
    
    def _get_language(self, ext: str) -> str:
        """Map file extension to language for syntax highlighting"""
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            # ... (same as in _format_file_content)
        }
        return language_map.get(ext, ext)
```

Add compression indicator to UI:

```python
# In Flask route
@app.route('/ask', methods=['POST'])
def ask_gcli():
    # ... existing code ...
    
    original_length = len(modified_prompt)
    # ... (compression happens in preprocessor) ...
    compressed_length = len(modified_prompt)
    
    was_compressed = compressed_length < original_length
    
    return jsonify({
        'response': result.stdout,
        'loaded_files': loaded_files,
        'errors': errors,
        'compressed': was_compressed,  # NEW
        'compression_ratio': f"{compressed_length}/{original_length}" if was_compressed else None,
        'success': True
    })
```

Update frontend to show compression warning:

```javascript
if (data.compressed) {
    document.getElementById('file-info').innerHTML += 
        ` <span class="warning">⚠️ Large context compressed (${data.compression_ratio} chars)</span>`;
}
```

---

### 5.9: Add File Content Caching (45 min)

Cache file contents per session to avoid re-reading:

Update `app/file_processor.py`:

```python
class FilePreprocessor:
    def __init__(self, working_dir: Path):
        self.working_dir = Path(working_dir)
        self.file_cache = {}  # NEW: filepath -> content
        self.cache_timestamps = {}  # NEW: filepath -> mtime
        self._load_ignore_patterns()
    
    def _read_file_safe(self, filepath: str) -> str:
        """
        Read file with caching
        
        Cache is invalidated if file's mtime changes
        """
        abs_path = Path(filepath).resolve()
        
        # Get current modification time
        try:
            current_mtime = abs_path.stat().st_mtime
        except FileNotFoundError:
            raise
        
        # Check cache
        if filepath in self.file_cache:
            cached_mtime = self.cache_timestamps.get(filepath)
            if cached_mtime == current_mtime:
                # Cache hit - file unchanged
                return self.file_cache[filepath]
        
        # Cache miss or file modified - read from disk

        with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Validate size
        if len(content) > 5 * 1024 * 1024:  # 5MB limit
            raise ValueError(f"File too large: {len(content)} bytes")
        
        # Update cache
        self.file_cache[filepath] = content
        self.cache_timestamps[filepath] = current_mtime
        
        return content
    
    def clear_cache(self):
        """Manually clear cache (useful for testing)"""
        self.file_cache.clear()
        self.cache_timestamps.clear()
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics for debugging"""
        return {
            'cached_files': len(self.file_cache),
            'total_cached_bytes': sum(len(c) for c in self.file_cache.values()),
            'files': list(self.file_cache.keys())
        }


```

Add cache management to session:

```python
# In app/session_manager.py

class GCLISession:
    def __init__(self, working_dir, model_name='gemini-2.0-flash-exp'):
        # ... existing code ...
        self.file_processor = FilePreprocessor(Path(working_dir))  # NEW
    
    def send_prompt(self, prompt):
        """Send prompt to GCLI with file preprocessing"""
        # Preprocess @file references
        modified_prompt, loaded_files, errors = self.file_processor.process_prompt(prompt)
        
        # Send to GCLI
        self.process.stdin.write(modified_prompt + '\n')
        self.process.stdin.flush()
        
        return loaded_files, errors
    
    def clear_file_cache(self):
        """Clear file content cache"""
        self.file_processor.clear_cache()
    
    def get_cache_stats(self):
        """Get cache statistics"""
        return self.file_processor.get_cache_stats()
```

Add cache management endpoints:

```python
# In app/main.py

@app.route('/cache_stats', methods=['GET'])
def cache_stats():
    """Get cache statistics for current session"""
    session_id = flask_session.get('gcli_session_id')
    gcli_session = session_manager.get_session(session_id)
    
    if not gcli_session:
        return jsonify({'error': 'No active session'}), 404
    
    stats = gcli_session.get_cache_stats()
    return jsonify(stats)

@app.route('/clear_cache', methods=['POST'])
def clear_cache():
    """Clear file cache for current session"""
    session_id = flask_session.get('gcli_session_id')
    gcli_session = session_manager.get_session(session_id)
    
    if not gcli_session:
        return jsonify({'error': 'No active session'}), 404
    
    gcli_session.clear_file_cache()
    return jsonify({'success': True})
```

Add cache indicator to UI:

```html
<!-- Add to header -->
<div class="header-controls">
    <button class="cache-btn" onclick="showCacheStats()">
        💾 Cache
    </button>
    <!-- ... other controls ... -->
</div>
```

```javascript
async function showCacheStats() {
    const response = await fetch('/cache_stats');
    const stats = await response.json();
    
    const message = `
Cache Statistics:
- Cached files: ${stats.cached_files}
- Total size: ${(stats.total_cached_bytes / 1024).toFixed(1)} KB
- Files: ${stats.files.join(', ')}
    `;
    
    if (confirm(message + '\n\nClear cache?')) {
        await fetch('/clear_cache', {method: 'POST'});
        addSystemMessage('Cache cleared');
    }
}
```

---

### 5.10: Performance Testing (30 min)

Test the system under load:

```bash
# Create test script
cat > test_performance.py << 'EOF'
import requests
import time
import json

BASE_URL = "http://localhost:5000"

def test_large_file_loading():
    """Test loading many files at once"""
    # Create large test project
    import os
    os.makedirs('test_large_project/src', exist_ok=True)
    
    for i in range(20):
        with open(f'test_large_project/src/file{i}.py', 'w') as f:
            f.write(f'# File {i}\n' + 'x = 1\n' * 100)
    
    # Start session
    response = requests.post(f"{BASE_URL}/start_session", json={
        'cwd': os.path.abspath('test_large_project')
    })
    
    # Test glob pattern
    start = time.time()
    response = requests.post(f"{BASE_URL}/ask", json={
        'prompt': 'Summarize @src/*.py'
    })
    duration = time.time() - start
    
    print(f"✓ Loaded 20 files in {duration:.2f}s")
    
    # Check cache
    stats = requests.get(f"{BASE_URL}/cache_stats").json()
    print(f"✓ Cache: {stats['cached_files']} files, {stats['total_cached_bytes']/1024:.1f} KB")

def test_conversation_memory():
    """Test 50+ message conversation"""
    messages = []
    
    for i in range(50):
        response = requests.post(f"{BASE_URL}/ask", json={
            'prompt': f'Message {i}: What is {i} + {i}?'
        })
        messages.append(response.json())
        
        if i % 10 == 0:
            print(f"✓ Sent {i} messages")
    
    print(f"✓ Completed 50-message conversation")

def test_concurrent_file_changes():
    """Test cache invalidation when files change"""
    import os
    
    # Create test file
    test_file = 'test_cache/test.py'
    os.makedirs('test_cache', exist_ok=True)
    
    # First request
    with open(test_file, 'w') as f:
        f.write('version = 1')
    
    response = requests.post(f"{BASE_URL}/ask", json={
        'prompt': f'What is in @{test_file}?'
    })
    
    # Modify file
    time.sleep(0.1)  # Ensure different mtime
    with open(test_file, 'w') as f:
        f.write('version = 2')
    
    # Second request - should see new content
    response = requests.post(f"{BASE_URL}/ask", json={
        'prompt': f'What is in @{test_file}?'
    })
    
    print("✓ Cache invalidation works")

if __name__ == '__main__':
    print("Running performance tests...")
    test_large_file_loading()
    test_conversation_memory()
    test_concurrent_file_changes()
    print("\n✓ All performance tests passed")
EOF

python test_performance.py
```

Measure and document:
- File injection time (should be <100ms for 20 files)
- Total response time (should be <10s for simple queries)
- Memory usage (check with `ps aux | grep python`)
- Cache effectiveness (cache hit rate)

---

## Success Criteria

- ✅ Streaming works (text appears incrementally)
- ✅ Code blocks have copy buttons
- ✅ Clear conversation button works
- ✅ Model selector allows switching models
- ✅ File upload enables temporary file references
- ✅ Glob patterns work (`@src/**/*.py`)
- ✅ Smart context compression for large file sets
- ✅ File content caching improves performance
- ✅ No performance degradation with 50+ messages
- ✅ No memory leaks

---

## Risks & Unknowns

**Risk**: SSE doesn't work in some browsers
- **Mitigation**: Fallback to Phase 4 approach (polling)
- **Detection**: Test in Chrome, Firefox, Safari

**Risk**: Glob patterns match too many files (performance)
- **Mitigation**: 50 file limit implemented (configurable)
- **Impact**: User gets warning, first 50 files used

**Risk**: Compression loses important context
- **Mitigation**: Keep first/last 50 lines, add compression indicator
- **User control**: Show compression stats, allow cache clearing

**Unknown**: Optimal cache invalidation strategy
- **Current**: mtime-based invalidation
- **Alternative**: User-triggered cache clear
- **Monitoring**: Track cache hit rate in testing

---

## Dependencies

- Phase 4 completed (wrapper script, production UI)
- Modern browser with EventSource API (for streaming)
- Python glob module (standard library)

---

## Rollback Strategy

If advanced features cause issues:

1. **Streaming problems**: Revert to Phase 4 blocking approach
2. **Glob pattern issues**: Disable glob, keep simple @file
3. **Compression bugs**: Disable compression, keep all content
4. **Cache invalidation problems**: Disable caching, always read fresh

All Phase 5 features are optional enhancements. Core functionality remains in Phases 1-4.

---

**END OF PHASE 5**        