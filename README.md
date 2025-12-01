# GCLI Web UI

ChatGPT-style web interface for Gemini CLI.

## Status

🚧 **Under Development** - Following phased implementation plan

### Current Phase: Phase 0 - Environment Setup

## Quick Start

```bash
# Clone repository
git clone <repo-url>
cd gcli-webui

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start development server (Phase 2+)
python app/main.py
```

## Project Structure

```
gcli-webui/
├── app/                    # Flask application
│   ├── main.py            # Main application file
│   ├── session_manager.py # Session management (Phase 3)
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS assets
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   └── integration/      # Integration tests
├── docs/                  # Documentation
├── bin/                   # Shell scripts (geminiwebui wrapper)
└── logs/                  # Application logs

```

## Development Phases

- [x] **Phase 0**: Environment Setup & GCLI Validation
- [ ] **Phase 1**: Critical Validation - `@` and `/` Commands
- [ ] **Phase 2**: Minimal Flask ↔ GCLI Proof-of-Concept
- [ ] **Phase 3**: Session Management & Stateful Conversations
- [ ] **Phase 4**: Shell Wrapper & ChatGPT-Style UI
- [ ] **Phase 5**: Optional Enhancements & Stream-JSON

## Requirements

- Python 3.8+
- GCLI (Gemini CLI) installed and configured
- Flask 3.0+

## Testing

```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run with coverage
pytest --cov=app --cov-report=html
```

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Implementation Plan](docs/PHASED_PLAN.md)
- [Phase Validation](docs/PHASE_VALIDATIONS.md)

## License

MIT

## Contributing

This project follows a phased implementation approach. See `docs/PHASED_PLAN.md` for details.
