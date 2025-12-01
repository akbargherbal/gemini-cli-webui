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
