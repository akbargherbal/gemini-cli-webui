# GCLI Web UI: Overall Implementation Plan

# Project Goal

The primary objective of this project is to develop **GCLI Web UI**, a robust, self-hosted web interface for the Google Gemini CLI (GCLI).

This tool aims to bridge the gap between the raw power of a terminal-based CLI and the user-friendly experience of modern AI chat interfaces like ChatGPT. It allows developers to launch a local web server from any project directory, enabling them to chat with Gemini models using their local codebase as context, without the friction of manually copying and pasting code into a browser.

**Key Objectives:**

1.  **ChatGPT-Style Experience:** Provide a polished, browser-based UI with markdown rendering, syntax highlighting, and multi-turn conversation history, superior to reading long outputs in a terminal window.
2.  **Seamless Local Context:** Enable users to instantly reference local files and directories (e.g., `Explain @src/main.py`) within their prompts.
3.  **High Performance:** Overcome the latency limitations of GCLI's native non-interactive mode by implementing a custom **Manual File Injection** system, ensuring file context is loaded instantly rather than waiting for slow API tool calls.
4.  **Zero-Config Launch:** Deliver a single command (`geminiwebui`) that validates the environment, starts the server, and opens the browser, making the tool immediately accessible for daily development workflows.

**Core Architecture:** A Flask-based web server acting as a wrapper around a long-lived GCLI subprocess.
**Key Strategy:** **Manual File Injection.** Due to performance limitations in GCLI’s native non-interactive mode, the Flask application will handle file reading (`@file`) and context management before sending plain text prompts to the model.

---

## Phase 0: Environment Setup & Baseline (Day 1)

**Goal:** Establish the development environment and verify GCLI capabilities.

This phase is purely preparatory. We must confirm that the underlying tools function as expected before building the abstraction layer.

- **0.1 Verification:** Confirm GCLI installation, version, and API connectivity.
- **0.2 Non-Interactive Testing:** Validate that `gemini --non-interactive` accepts stdin and writes to stdout.
- **0.3 Stream-JSON Check:** Determine if the installed GCLI version supports `--stream-json`. If not, we fallback to standard stdout parsing.
- **0.4 Project Skeleton:** Create the directory structure (`app/`, `tests/`, `docs/`) and `requirements.txt`.

**Deliverable:** A documented `GCLI_VALIDATION.md` confirming the toolchain is ready.

---

## Phase 1: Critical Validation & The Pivot (Day 1-2)

**Goal:** Prove the feasibility of `@file` commands and finalize the architectural approach.

**The Critical Finding:**
Native GCLI `@file` commands in non-interactive mode utilize "tool calls," which incur significant latency (30+ seconds) due to multiple API roundtrips. This is unacceptable for a web UI.

- **1.1 Test Native Features:** Attempt `echo "Explain @file.py" | gemini -p`.
- **1.2 Confirm Blocker:** Document the timeout/latency issue.
- **1.3 Architectural Decision:** Formally adopt **Manual File Injection**.
  - Instead of relying on GCLI to read files, the Flask app will parse the prompt, read the files from the disk, and inject the content into the prompt as Markdown code blocks.
  - GCLI will receive a plain-text prompt containing the file data, bypassing the slow tool-call mechanism.

**Deliverable:** `PHASE1_VALIDATION.md` documenting the decision to build a custom File Preprocessor.

---

## Phase 2: The Core Engine (Day 2-3)

**Goal:** Build the Flask application with the custom File Preprocessor.

This phase builds the "brain" of the application. We move from shell scripts to Python code that manipulates prompts.

- **2.1 File Preprocessor Module:**
  - Implement regex to detect `@filename`.
  - Implement security checks (prevent path traversal, block system directories).
  - Read file contents and format them into the prompt.
- **2.2 Minimal Flask App:**
  - Create a `/ask` endpoint.
  - Integrate the Preprocessor: `User Prompt` → `Preprocessor` → `GCLI Subprocess`.
  - Capture stdout and return it to the frontend.
- **2.3 Web UI Proof-of-Concept:**
  - Create a raw HTML interface to test the flow.
  - **Critical Test:** Verify that `Explain @file.py` returns a response in <5 seconds (solving the Phase 1 blocker).

**Deliverable:** A functional Flask app where users can reference files, and the model receives the content instantly.

---

## Phase 3: Session Management (Day 3-4)

**Goal:** Enable multi-turn conversations (Memory).

We transition from "one-off" requests to stateful conversations.

- **3.1 Session Architecture:**
  - Instead of `subprocess.run` (one-shot), use `subprocess.Popen` to keep GCLI running.
  - Use GCLI's `--checkpoint` flag to handle internal state if supported, or rely on the persistent process memory.
- **3.2 Session Manager Class:**
  - Map `session_id` (cookie) to a specific GCLI subprocess.
  - Handle thread-safe reading/writing to the subprocess `stdin`/`stdout`.
- **3.3 Simplified Parsing:**
  - Because we are using Manual File Injection, we do not need to parse complex "Tool Use" events. We only need to parse plain text responses.
- **3.4 Testing:**
  - Verify the model remembers previous questions ("What was my last prompt?").
  - Ensure sessions terminate cleanly when the user leaves.

**Deliverable:** A stateful backend where users can have back-and-forth conversations.

---

## Phase 4: Production Polish (Day 4-5)

**Goal:** Create a "ChatGPT-like" user experience and a simple launcher.

This phase transforms the developer tool into a usable product.

- **4.1 The Launcher (`geminiwebui`):**
  - Write a Bash script to:
    1.  Validate the current directory (safety check).
    2.  Find an open port.
    3.  Launch Flask in the background.
    4.  Auto-open the default web browser.
- **4.2 UI Overhaul:**
  - Replace raw HTML with a polished CSS interface (Dark mode, avatars, chat bubbles).
  - Add a "Composer" area with auto-expanding text input.
  - Display "Loaded Files" metadata so users know what context was sent.
- **4.3 Documentation:**
  - Write a `README.md` explaining the `@file` injection mechanism and safety features.

**Deliverable:** A polished, installable tool that can be launched from any project directory with a single command.

---

## Phase 5: Advanced Features (Optional/Time Permitting)

**Goal:** Restore features lost in Phase 2 and add "Pro" capabilities.

Since we bypassed GCLI's native file handling, we lost some features (like glob patterns). Phase 5 rebuilds them.

- **5.1 Streaming (SSE):** Implement Server-Sent Events to show text character-by-character as it generates.
- **5.2 Glob Support:** Update the Preprocessor to handle wildcards (e.g., `@src/**/*.py`), expanding them into multiple file injections.
- **5.3 Smart Compression:** If the user loads too many files, automatically truncate or summarize them to fit the context window.
- **5.4 Caching:** Cache file contents in memory to speed up repeated queries about the same files.
- **5.5 Quality of Life:** Add "Copy Code" buttons, Model Selectors, and "Clear Chat" functionality.

**Deliverable:** A feature-rich, high-performance AI coding assistant.

---

## Summary of Trade-offs

| Feature           | Native GCLI              | GCLI Web UI (Our Approach)         |
| :---------------- | :----------------------- | :--------------------------------- |
| **@file Speed**   | Slow (Tool calls, 30s+)  | **Instant** (Text injection, <1s)  |
| **Context Logic** | Native Smart Compression | **Custom Python Logic** (Phase 5)  |
| **Glob Patterns** | Native Support           | **Custom Python Logic** (Phase 5)  |
| **Security**      | Sandbox (macOS)          | **Directory Whitelisting** (Flask) |
| **Interface**     | Terminal                 | **Web Browser**                    |

This plan prioritizes **performance and usability** over strict adherence to GCLI's native tool-use architecture, ensuring a responsive web experience.
