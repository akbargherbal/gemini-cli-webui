# Session Context Summary

## Project Goal
Build a web UI for Gemini CLI (GCLI) that provides ChatGPT-style interface with support for `@file` references and multi-turn conversations.

## What We Tested (Phase 0 & 1)

### ✅ Confirmed Working
- **GCLI installed**: v0.18.2
- **Non-interactive flag**: `-p` (not `--non-interactive`)
- **Basic prompts work**: `gemini -p "prompt"` returns responses
- **Stream-JSON available**: `-o stream-json` flag exists and works
- **Slash commands work**: `/help`, `/model` respond in `-p` mode
- **Working directory respected**: `cwd` parameter in subprocess correctly sets context

### ❌ Critical Failure
- **@file does NOT work in `-p` mode**: All tests timed out (30s+)
- **@directory does NOT work in `-p` mode**: Timed out
- **Root cause**: [@file preprocessing only works in interactive mode. In `-p` mode, GCLI uses tool calls (`read_file` tool) which requires multiple API roundtrips](https://github.com/google-gemini/gemini-cli/issues/3311)

## The Problem
Original plan assumed @file preprocessing happens in non-interactive mode. **This assumption is FALSE.**

## Three Options Forward

### Option 1: Manual File Injection in Flask
- Flask intercepts `@file`, reads files, injects content into prompt
- Pros: Fast, reliable, full control
- Cons: Reimplements GCLI's file logic, must handle `.geminiignore`

### Option 2: Use GCLI Tool Calls (accept slowness)
- Keep using `@file` in `-p` mode, increase timeouts to 120s+
- Pros: Native GCLI behavior
- Cons: Very slow, expensive (multiple API calls per file)

### Option 3: Interactive Mode via pexpect
- Use terminal emulation to run interactive GCLI
- Pros: Gets proper @file preprocessing
- Cons: Complex, fragile, state management harder

## Decision Required
**Which option to pursue?** Original plan is invalidated by @file limitation.

## Files Created
- `phase0_validate.py` - Environment validation (passed)
- `phase1_validate.py` - @file testing (failed)
- `docs/phase0_results.json` - Phase 0 results
- `docs/phase1_results.json` - Phase 1 results
- `test-project/` - Test directory with sample files

## Next Session
1. Choose Option 1, 2, or 3
2. If Option 1: Design file injection system
3. Update implementation plan based on chosen approach
4. Consider: Do we still need Flask or is there a simpler architecture?