# Contributing to RxFlow

Thanks for your interest in contributing! We welcome bug reports, feature requests, and pull requests.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/rx-flow.git
   cd rx-flow
   ```
3. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Backend

```bash
cd backend
pip install -r requirements.txt

# Start PostgreSQL locally
docker run -d -e POSTGRES_PASSWORD=rxflow -p 5432:5432 postgres:15-alpine
psql -U postgres -h localhost -c "CREATE DATABASE rxflow;"
psql -U postgres -h localhost -d rxflow < app/db/schema.sql

# Set env
export DATABASE_URL=postgresql+asyncpg://postgres:rxflow@localhost:5432/rxflow
export ANTHROPIC_API_KEY=sk-...

# Run tests
pytest tests/ -v

# Start dev server
uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd client
npm install
npm start  # Runs on http://localhost:3000
```

## Code Style

- **Python**: Follow PEP 8, use type hints
- **JavaScript**: Use ESLint (run `npm run lint`)
- **SQL**: Lowercase keywords, meaningful names

## Making Changes

### For Bug Fixes
1. Describe the bug in your PR
2. Include steps to reproduce
3. Add a test case that catches the bug
4. Fix the bug
5. Ensure all tests pass

### For Features
1. Discuss the feature in an issue first (optional but recommended)
2. Implement with tests
3. Update docs if needed
4. Add examples in the README if applicable

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests (if available)
cd client
npm test
```

## Commit Messages

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add AI anomaly detection for high-value claims"
git commit -m "Fix validation logic for copay range check"

# Avoid
git commit -m "fix bug"
git commit -m "updates"
```

## Pull Request Process

1. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
2. **Open a PR** on GitHub with:
   - Clear title describing the change
   - Description of what was changed and why
   - Screenshots (if UI changes)
   - Reference to related issues
3. **Wait for review** — maintainers will provide feedback
4. **Address feedback** and push updates
5. **Merge** once approved

## Code Review

All submissions go through code review. We look for:
- ✅ Tests pass
- ✅ Code follows style guidelines
- ✅ No hardcoded credentials or secrets
- ✅ Documentation is updated
- ✅ Changes are backward compatible (when possible)

## Reporting Bugs

Use GitHub Issues with:
- **Title**: Clear description
- **Environment**: Python/Node version, OS
- **Steps to reproduce**: Exact steps
- **Expected vs actual**: What should happen vs what does
- **Logs**: Error messages, tracebacks

Example:
```
Title: Validation fails for copay=0 on refills

Environment: Python 3.12, macOS 14.4

Steps:
1. Submit claim with copay=0, refill_number=0
2. Claim should pass (copay allowed on first fill)
3. Claim is rejected

Expected: PASS
Actual: FAIL - COPAY_RANGE error
```

## Questions?

- 📖 Check [README.md](README.md)
- 📋 Check [API docs](http://localhost:8001/docs) (after running locally)
- 🐛 Search existing [Issues](https://github.com/yourusername/rx-flow/issues)
- 💬 Open a Discussion

---

**Thank you for contributing to RxFlow! 🙌**
