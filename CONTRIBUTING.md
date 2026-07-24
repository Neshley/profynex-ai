# Contributing to Profynex AI

## Code of Conduct

Please be respectful and constructive in all interactions.

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Write tests
5. Run tests: `pytest`
6. Format code: `black . && isort .`
7. Commit: `git commit -m "Add your feature"`
8. Push: `git push origin feature/your-feature`
9. Create a Pull Request

## Development Setup

```bash
git clone https://github.com/Neshley/profynex-ai.git
cd profynex-ai
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install
npm run dev
```

## Code Style

- Follow PEP 8 for Python
- Use TypeScript for frontend code
- Use Prettier for formatting
- Use ESLint for linting

## Testing

```bash
pytest
pytest --cov
pytest tests/test_specific.py
```

## Commit Messages

Use conventional commits:
- `feat: Add new feature`
- `fix: Fix bug`
- `docs: Update documentation`
- `style: Code style changes`
- `refactor: Code refactoring`
- `test: Add tests`
- `chore: Maintenance`

## Pull Request Guidelines

1. Include a clear description
2. Reference any related issues
3. Update documentation
4. Add tests for new features
5. Ensure all tests pass
6. Keep PRs focused on a single feature

## Reporting Issues

- Use GitHub Issues
- Include clear description
- Add reproduction steps
- Include system information
- Attach screenshots if relevant

## Questions?

Open an issue or start a discussion!
