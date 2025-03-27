# Testing Framework

This directory contains all tests for the reminder backend application. The tests are organized to mirror the structure of the main application, making it easier to locate and maintain them.

## Directory Structure

- `tests/`
  - `api/` - Tests for API endpoints and request/response handling
  - `core/` - Tests for core functionality (logging, middleware, request context, etc.)
  - `models/` - Tests for data models, focusing on validation and behavior
  - `repositories/` - Tests for database interaction and query logic
  - `schemas/` - Tests for Pydantic schemas and validation
  - `services/` - Tests for business logic and service-level operations
  - `conftest.py` - Shared pytest fixtures and configuration
  - `pytest.ini` - Configuration for pytest

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests in a specific directory
pytest tests/models/

# Run a specific test file
pytest tests/api/test_auth_endpoints.py

# Run a specific test function
pytest tests/models/test_user_model.py::test_create_user
```

### Test Categories

We use pytest markers to categorize tests. You can run specific categories using:

```bash
# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run API tests only
pytest -m api

# Run a quick smoke test
pytest -m smoke
```

## Test Writing Guidelines

1. **Test Naming**: Test functions should be named with the pattern `test_<what is being tested>_<expected outcome>`.
2. **One Assertion Per Test**: When possible, keep tests focused on a single behavior.
3. **Use Fixtures**: Use fixtures to set up test data and dependencies.
4. **Mock External Dependencies**: Use mocks for external services to avoid integration complexities.
5. **Test Both Success and Failure Paths**: Ensure both valid and invalid inputs are tested.
6. **Add Comments**: Document complex test logic or setup.

## Asynchronous Testing

For testing async code, use `pytest.mark.asyncio` and `async def` for test functions. The configuration in pytest.ini is set to automatically handle asyncio tests.

## Environment Variables

Tests automatically use the testing environment configuration. You don't need to set environment variables manually when running tests, but you can override them if needed:

```bash
ENV=testing pytest
```

## Coverage

To run tests with coverage:

```bash
# Run tests with coverage
pytest --cov=app

# Generate coverage report in HTML
pytest --cov=app --cov-report=html
```

## Integration Tests

Some tests require external dependencies like databases. These are marked with `@pytest.mark.integration`. By default, they use mock interfaces, but you can run them against real dependencies by setting up the appropriate environment variables.
