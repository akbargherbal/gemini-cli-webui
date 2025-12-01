# Phase 2: Flask with Manual File Injection (Day 2-3, 4-5 hours)

## Goal

Create Flask app that:
1. Intercepts prompts with @file references
2. Reads files from working directory (with security checks)
3. Injects file contents into prompt
4. Sends modified prompt to GCLI subprocess (no @file syntax)
5. Receives response and displays in browser

This phase implements the file preprocessor to work around GCLI's @file timeout issue in non-interactive mode.

## Tasks

**2.0: Design File Preprocessing Architecture** (20 min)

Document the preprocessing flow:

```
User Prompt: "Explain @src/main.py"
      ↓
FilePreprocessor.process_prompt()
      ↓
1. Regex find: @src/main.py
2. Read file: /working/dir/src/main.py
3. Check: .gitignore, .geminiignore, security
4. Format: Markdown code block
5. Replace: @src/main.py → file contents
      ↓
Modified Prompt: "Explain\n```python\n[file contents]\n```"
      ↓
subprocess.run(['gemini', '-p', modified_prompt])
      ↓
Response (GCLI never sees @file syntax)
```

Create `docs/FILE_PREPROCESSING.md` documenting this.

**2.1: Implement File Preprocessor Module** (90 min)

Create `app/file_processor.py`:

Key features:
- Regex pattern: `@([\w\-./]+(?:\.\w+)?)`
- Read files with security checks:
  - Path traversal protection
  - System directory blacklist
  - .gitignore/.geminiignore parsing
  - Binary file detection
  - File size limits (5MB max)
- Format file contents in markdown code blocks
- Return: (modified_prompt, loaded_files[], errors[])

See revised_plan.md for full implementation.

**Test immediately**:
```bash
python3 -c "
from app.file_processor import FilePreprocessor
from pathlib import Path

p = FilePreprocessor(Path('test-project'))
prompt, files, errors = p.process_prompt('Explain @src/main.py')
print('Loaded:', files)
print('Errors:', errors)
print('Modified prompt length:', len(prompt))
"
```

**2.2: Create Flask Application Structure** (20 min)

```bash
cd ~/gcli-webui

cat > requirements.txt << 'EOF'
Flask==3.0.0
python-dotenv==1.0.0
# No additional dependencies needed - using stdlib for file ops
EOF

pip install -r requirements.txt
```

**2.3: Create Minimal Flask App with File Injection** (60 min)

Create `app/main.py`:

**Key changes from original plan**:
1. Import FilePreprocessor
2. Process prompt BEFORE sending to GCLI
3. Send modified prompt (plain text) to subprocess
4. Return both response AND list of loaded files

```python
"""
Minimal GCLI Web UI - Phase 2 with Manual File Injection
Intercepts @file references, reads files, injects contents before GCLI
"""

from flask import Flask, render_template, request, jsonify
import subprocess
import os
from pathlib import Path
from app.file_processor import FilePreprocessor

app = Flask(__name__)

@app.route('/')
def index():
    """Serve minimal HTML form"""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_gcli():
    """
    Process @file references, inject contents, send to GCLI
    GCLI receives plain text - no @file syntax
    """
    try:
        user_prompt = request.json.get('prompt', '')
        working_dir = request.json.get('cwd', os.getcwd())
        
        # Validate working directory (safety check)
        if not is_safe_directory(working_dir):
            return jsonify({'error': 'Unsafe directory'}), 400
        
        # NEW: Preprocess @file references
        preprocessor = FilePreprocessor(Path(working_dir))
        modified_prompt, loaded_files, errors = preprocessor.process_prompt(user_prompt)
        
        # Send MODIFIED prompt to GCLI (no @file syntax)
        result = subprocess.run(
            ['gemini', '-p', modified_prompt],  # ← Plain text, not @file
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
            'loaded_files': loaded_files,  # NEW: Tell user what files loaded
            'errors': errors,               # NEW: Report file loading errors
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

See flask_app_phase2.py artifact for full implementation.

**2.4: Create Minimal HTML Template** (30 min)

**ADD to template**:
- Display loaded files list
- Show file loading errors
- Indicate when @file preprocessing happens

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
    </style>
</head>
<body>
    <h1>GCLI Web UI - Proof of Concept</h1>
    
    <div>
        <label>Working Directory:</label>
        <input type="text" id="cwd" value="" style="width: 100%;">
    </div>
    
    <div>
        <label>Prompt (use @filename to reference files):</label>
        <textarea id="prompt" placeholder="Enter prompt (try: Explain @file.py)"></textarea>
    </div>
    
    <button onclick="sendPrompt()">Send to GCLI</button>
    
    <div id="file-info" class="file-info"></div>
    <div id="status"></div>
    <div id="response"></div>
    
    <script>
        // Set default working directory to home
        document.getElementById('cwd').value = '~';
        
        async function sendPrompt() {
            const prompt = document.getElementById('prompt').value;
            const cwd = document.getElementById('cwd').value;
            const statusDiv = document.getElementById('status');
            const responseDiv = document.getElementById('response');
            const fileInfoDiv = document.getElementById('file-info');
            
            statusDiv.textContent = 'Processing @file references and thinking...';
            responseDiv.textContent = '';
            fileInfoDiv.textContent = '';
            fileInfoDiv.className = 'file-info';
            
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
                    
                    // NEW: Show loaded files
                    if (data.loaded_files && data.loaded_files.length > 0) {
                        fileInfoDiv.textContent = '📂 Loaded files: ' + data.loaded_files.join(', ');
                    }
                    
                    // NEW: Show errors
                    if (data.errors && data.errors.length > 0) {
                        const errorDiv = document.createElement('div');
                        errorDiv.className = 'error-info';
                        errorDiv.textContent = '⚠️ Warnings: ' + data.errors.join('; ');
                        fileInfoDiv.parentNode.insertBefore(errorDiv, fileInfoDiv.nextSibling);
                    }
                } else {
                    statusDiv.textContent = 'Error:';
                    responseDiv.textContent = data.error;
                    fileInfoDiv.textContent = '';
                }
            } catch (error) {
                statusDiv.textContent = 'Error:';
                responseDiv.textContent = error.message;
                fileInfoDiv.textContent = '';
            }
        }
        
        // Allow Enter to submit (for convenience)
        document.getElementById('prompt').addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                sendPrompt();
            }
        });
    </script>
</body>
</html>
```

See flask_app_phase2.py artifact for full template.

**2.5: Test Minimal Flow** (30 min)

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

**2.6: Test in Browser** (30 min)

1. Open `http://localhost:5000`
2. Enter prompt: "Explain Python decorators"
3. Click "Send to GCLI"
4. Wait for response
5. Verify response appears

**2.7: Test `@file` via Web UI** (30 min)

**CRITICAL TEST** - This validates our Phase 1 workaround works.

Setup:
```bash
mkdir -p ~/test-webui-project
cat > ~/test-webui-project/sample.py << 'EOF'
def greet(name):
    """Example function with docstring"""
    return f"Hello, {name}!"
    
print(greet("World"))
EOF
```

In browser:
1. Set working directory: `~/test-webui-project`
2. Enter prompt: `Explain @sample.py`
3. Click "Send to GCLI"

**Expected behavior** (NEW):
- ✅ Response appears in < 5 seconds (not 30s timeout!)
- ✅ "Loaded files: sample.py" shown in UI
- ✅ Model's response references the actual code (greet function, docstring)
- ✅ No timeout errors

**What to verify**:
- Flask preprocessor detected @sample.py
- File was read successfully
- Contents injected into prompt
- GCLI received plain text (you can check Flask logs)
- Model understood the code context

**If this fails**: Phase 1 workaround didn't work - escalate immediately.

**2.8: Document Phase 2 Results** (20 min)

Create `docs/phase2_results.json`:

```json
{
  "phase": "2",
  "status": "complete",
  "approach": "manual_file_injection",
  "file_preprocessor_works": true,
  "tests": {
    "flask_starts": true,
    "browser_loads": true,
    "prompt_submission": true,
    "response_display": true,
    "file_injection_works": true,
    "working_dir_validation": true
  },
  "performance": {
    "file_injection_time_ms": "<measurement>",
    "total_response_time_seconds": "<measurement>",
    "acceptable": true
  },
  "tradeoffs": {
    "lost_features": [
      "GCLI native glob patterns (@src/**/*.py)",
      "GCLI smart context compression"
    ],
    "gained_benefits": [
      "Instant file reading (vs 30s timeout)",
      "Full control over file handling",
      "Better error messages",
      "Easier debugging"
    ]
  },
  "blockers": "none",
  "next_phase": "phase_3_session_management"
}
```

## Success Criteria

- ✅ FilePreprocessor module implemented and tested
- ✅ Regex pattern detects @file references correctly
- ✅ Files read with all security checks (path traversal, ignore patterns, etc.)
- ✅ File contents formatted and injected into prompt
- ✅ Flask app integrates preprocessor successfully
- ✅ GCLI receives plain text prompts (no @file syntax)
- ✅ Response appears in browser in < 10 seconds (vs 30s+ timeout)
- ✅ `@file` commands work via web UI
- ✅ Loaded files list displayed to user
- ✅ File loading errors reported gracefully
- ✅ Working directory validation prevents system access
- ✅ Multiple files in one prompt work (@file1.py and @file2.py)

## Risks & Unknowns

**MAJOR RISK RESOLVED**: Phase 1 confirmed @file timeouts.
We've eliminated this risk by implementing manual file injection.

**New Risks**:

**Risk**: File preprocessing takes too long (large files)
- **Impact**: MEDIUM - UI delays, but no timeout
- **Detection**: Test with 5MB file (our limit)
- **Mitigation**: File size limit already implemented (5MB max)
- **Improved from Phase 1**: Still faster than GCLI tool call timeout!

**Risk**: Working directory validation too restrictive
- **Impact**: MEDIUM - users can't access valid projects
- **Detection**: Test with various project paths
- **Mitigation**: Make whitelist configurable

**Unknown**: File encoding issues
- **Test**: Send prompts with files containing Unicode, emojis, special characters
- **Mitigation**: Explicit UTF-8 handling in file reader

**Unknown**: Binary file detection accuracy
- **Test**: Try to load .pyc, .jpg, .pdf files
- **Expected**: Should be rejected with clear error message

## Rollback Strategy

If file preprocessing fails:

1. **Isolate the issue**:
   ```python
   # Test preprocessor directly
   from app.file_processor import FilePreprocessor
   from pathlib import Path
   
   p = FilePreprocessor(Path('.'))
   result = p.process_prompt('Explain @test.py')
   print(result)
   ```

2. **Common issues**:
   - Regex not matching: Adjust pattern in file_processor.py
   - Security check too strict: Review blacklist/whitelist
   - File encoding errors: Add better error handling

3. **Worst case**: 
   - Simplify preprocessor (remove advanced features)
   - Get basic @file working first
   - Add ignore patterns later

**No need to rollback to Phase 1** - that approach was proven non-viable.

## Dependencies

- Phase 1 completed successfully (`@file` timeout confirmed, manual injection approach chosen)
- Flask installed
- GCLI accessible from Python subprocess
- Python standard library (pathlib, re, subprocess)