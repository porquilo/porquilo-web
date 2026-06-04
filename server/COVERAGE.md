# Coverage

Code coverage is used to measure the effectiveness of tests in the Porquilo server. It ensures that the test suite adequately covers the application code, helping maintain code quality and reliability.

## Running coverage locally

Coverage can be run locally using pytest:

```bash
uv run pytest --cov=src --cov-report=html --cov-report=term
```

This command:
- Runs tests with coverage measurement enabled
- Reports coverage for the `src` directory
- Generates both HTML and terminal coverage reports
- Uses the current Python interpreter via `uv`

## Coverage measurement configuration

The coverage tooling is configured via `.coveragerc` in the root of the server directory:

- **Source**: `src` directory
- **Include**: All Python files under `src/*`
- **Omit**: Test files, cache directories, virtual environments, and other non-source files

The configuration excludes:
- Test files (`*/tests/*`, `*/test_*.py`)
- Python cache directories (`*/__pycache__/*`)
- pytest cache (`*/.pytest_cache/*`)
- Virtual environments (`*/venv/*`, `*/env/*`, `*/.venv/*`)
- Node modules (`*/node_modules/*`)
- Git directories (`*/.git/`)

## CI/CD usage

In CI/CD, coverage is measured and reported to ensure code quality standards are met. The GitHub Actions workflow automatically runs tests with coverage and reports results.

## Best practices

- Maintain coverage above 90%
- Write tests for all new features and code changes
- Ensure each test function covers distinct code paths
- Use `# pragma: no cover` comments for code that cannot be tested (e.g., exception handlers, platform-specific code)
- Regularly review coverage reports to identify untested code sections