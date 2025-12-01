# GCLI Web UI Architecture

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
