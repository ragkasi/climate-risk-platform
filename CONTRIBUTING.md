# Contributing to Climate Risk Lens

Thank you for your interest in contributing to Climate Risk Lens! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/climate-risk-platform.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Set up the development environment: `make setup`

## Development Environment

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Setup

```bash
# Clone the repository
git clone https://github.com/climate-risk-lens/climate-risk-platform.git
cd climate-risk-platform

# Copy environment file
cp env.example .env

# Install dependencies
make setup

# Start development environment
make dev
```

## ASCII-Only Policy

This project enforces strict ASCII-only text throughout:

- **No emojis, em dashes, en dashes, or smart quotes**
- All user-facing text, logs, and generated content must be ASCII
- Automated checks via pre-commit hooks and CI
- Sanitization middleware in backend and frontend

### ASCII Compliance Checklist

- [ ] All text files contain only ASCII characters
- [ ] No emojis in code, comments, or documentation
- [ ] No em dashes (—) or en dashes (–)
- [ ] No smart quotes ("") or apostrophes ('')
- [ ] All API responses are sanitized
- [ ] All user inputs are sanitized

## Code Style

### Python (Backend)

- Use Black for formatting
- Use Ruff for linting
- Use MyPy for type checking
- Follow PEP 8 style guide
- Use type hints for all functions

```bash
# Format code
cd backend && black .

# Lint code
cd backend && ruff check .

# Type check
cd backend && mypy .
```

### TypeScript/JavaScript (Frontend)

- Use Prettier for formatting
- Use ESLint for linting
- Use TypeScript for type safety
- Follow React best practices

```bash
# Format code
cd frontend && npm run format

# Lint code
cd frontend && npm run lint
```

## Testing

### Backend Tests

```bash
cd backend
pytest --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:e2e
```

### ASCII Compliance Tests

```bash
# Check ASCII compliance
./scripts/check_ascii.sh

# Check for blocked characters
./scripts/check_blocklist.sh
```

## Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following the code style guidelines
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Run all tests** and ensure they pass
6. **Check ASCII compliance** using the provided scripts
7. **Submit a pull request** with a clear description

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] ASCII compliance check passes

## ASCII Compliance
- [ ] No emojis added
- [ ] No em dashes or en dashes
- [ ] No smart quotes
- [ ] All text is ASCII-only

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## Commit Messages

Use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(api): add risk assessment endpoint`
- `fix(ui): resolve map rendering issue`
- `docs(readme): update installation instructions`
- `test(backend): add unit tests for risk service`

## Code Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **ASCII compliance** must be verified
3. **Code review** by at least one maintainer
4. **Testing** must be comprehensive
5. **Documentation** must be updated

## Issue Reporting

When reporting issues, please include:

1. **Environment details** (OS, Python version, Node version)
2. **Steps to reproduce** the issue
3. **Expected behavior** vs actual behavior
4. **Screenshots** if applicable
5. **Logs** if available

## Feature Requests

When requesting features, please include:

1. **Use case** and motivation
2. **Proposed solution** or approach
3. **Alternatives considered**
4. **Impact** on existing functionality

## Security

- **Report security vulnerabilities** privately to [security email]
- **Do not** create public issues for security problems
- **Follow responsible disclosure** practices

## License

By contributing to Climate Risk Lens, you agree that your contributions will be licensed under the MIT License.

## Getting Help

- **Documentation**: Check the `/docs` directory
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Email**: Contact the maintainers at [contact email]

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to Climate Risk Lens!
