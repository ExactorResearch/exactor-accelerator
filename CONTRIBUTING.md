# Contributing to Exactor Accelerator

Thanks for your interest in contributing to Exactor Accelerator!

## Development Setup

```bash
git clone https://github.com/ExactorResearch/exactor-accelerator.git
cd exactor-accelerator
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your API tokens
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting & Linting

```bash
black exactor_accelerator/
ruff check exactor_accelerator/
mypy exactor_accelerator/ --ignore-missing-imports
```

## Pull Requests

1. Fork the repository
2. Create a branch for your feature (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Reporting Issues

Use [GitHub Issues](https://github.com/ExactorResearch/exactor-accelerator/issues) to report bugs or request features.

## Code of Conduct

Be respectful and constructive in all interactions.
