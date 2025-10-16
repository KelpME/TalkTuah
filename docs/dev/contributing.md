# Contributing to Talk-Tuah

Thanks for your interest in contributing!

## Getting Started

1. Fork the repo
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/TalkTuah.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Test your changes: `make test`
6. Commit: `git commit -m "Add: your feature"`
7. Push: `git push origin feature/your-feature`
8. Open a Pull Request

## Development Setup

```bash
# Backend
make up

# Frontend
cd frontend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python TuivLLM.py
```

## Code Style

- Python: Follow PEP 8
- Use 4 spaces for indentation
- Max line length: 120 characters
- Add type hints where possible

## Testing

```bash
# Run all tests
make test

# Run specific test
pytest tests/test_api.py::test_name -v
```

## Pull Request Guidelines

- Keep PRs focused on a single feature/fix
- Update documentation if needed
- Add tests for new features
- Ensure all tests pass
- Follow conventional commit messages:
  - `feat:` - New feature
  - `fix:` - Bug fix
  - `docs:` - Documentation
  - `refactor:` - Code refactoring
  - `test:` - Tests

## Questions?

Open an issue or discussion on GitHub!
