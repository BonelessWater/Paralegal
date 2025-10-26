# Contributing to Paralegal AI

Thank you for your interest in contributing to Paralegal AI! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment. We expect all contributors to:

- Be respectful and considerate
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.10+ (3.12 recommended)
- Node.js 18+ (20 recommended)
- PostgreSQL 14+
- Git

### Setting Up Development Environment

1. **Fork and clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/Paralegal.git
cd Paralegal
```

2. **Set up Python environment**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

3. **Set up pre-commit hooks**

```bash
pip install pre-commit
pre-commit install
```

4. **Set up frontend**

```bash
cd frontend
npm install
cd ..
```

5. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration
```

6. **Set up database**

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Or install PostgreSQL locally and create database
createdb paralegal_db
```

## Development Workflow

### Branch Naming Convention

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test improvements

### Making Changes

1. **Create a new branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**

- Write clean, maintainable code
- Follow coding standards (see below)
- Add tests for new functionality
- Update documentation as needed

3. **Test your changes**

```bash
# Run backend tests
pytest backend/ -v

# Run frontend tests
cd frontend && npm test

# Run linters
pre-commit run --all-files
```

4. **Commit your changes**

```bash
git add .
git commit -m "feat: add new feature description"
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(agents): add new legal researcher agent
fix(api): resolve rate limiting issue
docs(readme): update installation instructions
```

## Coding Standards

### Python Code Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for code formatting (line length: 100)
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints for function signatures
- Write docstrings for all public functions and classes

**Example:**

```python
from typing import List, Optional

def process_task(
    task_id: str,
    content: str,
    priority: Optional[str] = "medium"
) -> Dict[str, Any]:
    """
    Process a task and return results

    Args:
        task_id: Unique task identifier
        content: Task content
        priority: Task priority (low, medium, high)

    Returns:
        Dictionary containing processing results

    Raises:
        ValueError: If task_id is invalid
    """
    # Implementation
    pass
```

### TypeScript/React Code Style

- Use TypeScript for type safety
- Follow [Airbnb React Style Guide](https://github.com/airbnb/javascript/tree/master/react)
- Use functional components with hooks
- Use Prettier for code formatting
- Write meaningful component and prop names

**Example:**

```typescript
interface TaskProps {
  id: string;
  content: string;
  status: 'pending' | 'processing' | 'completed';
  onUpdate?: (id: string) => void;
}

export const TaskCard: React.FC<TaskProps> = ({ id, content, status, onUpdate }) => {
  // Implementation
};
```

### General Guidelines

- Keep functions small and focused (single responsibility)
- Use meaningful variable and function names
- Add comments for complex logic
- Avoid hardcoded values (use constants or environment variables)
- Handle errors gracefully
- Log important events and errors

## Testing

### Backend Testing

```bash
# Run all tests
pytest backend/ -v

# Run specific test file
pytest backend/test_api.py -v

# Run with coverage
pytest backend/ --cov=backend --cov-report=html
```

### Frontend Testing

```bash
cd frontend

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

### Writing Tests

- Write unit tests for all new functions
- Write integration tests for API endpoints
- Aim for >80% code coverage
- Use descriptive test names

**Example:**

```python
def test_ingest_task_creates_task_successfully():
    """Test that ingesting a task creates it in the database"""
    # Arrange
    task_data = {"source": "email", "content": "Test task"}

    # Act
    response = client.post("/tasks/ingest", json=task_data)

    # Assert
    assert response.status_code == 200
    assert "task_id" in response.json()
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass
2. ✅ Code follows style guidelines
3. ✅ Pre-commit hooks pass
4. ✅ Documentation is updated
5. ✅ Commit messages follow convention
6. ✅ Branch is up-to-date with main

### Submitting a Pull Request

1. **Push your changes**

```bash
git push origin feature/your-feature-name
```

2. **Create Pull Request on GitHub**

- Provide a clear title and description
- Reference any related issues
- Add screenshots for UI changes
- Request review from maintainers

3. **PR Template**

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Screenshots (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

### Review Process

- Maintainers will review your PR
- Address any requested changes
- Once approved, your PR will be merged

## Reporting Issues

### Bug Reports

Include:
- Clear, descriptive title
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python/Node version, etc.)
- Error messages and logs
- Screenshots if applicable

### Feature Requests

Include:
- Clear, descriptive title
- Problem the feature solves
- Proposed solution
- Alternative solutions considered
- Any additional context

## Development Tips

### Running in Development Mode

**Backend:**
```bash
cd backend
uvicorn api_server:app --reload --port 8080
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Debugging

- Use Python debugger (`pdb`) or IDE debugger
- Check logs in `logs/` directory
- Use browser DevTools for frontend issues
- Enable DEBUG mode in `.env` for verbose logging

### Performance Testing

```bash
# Test API performance
python AMD_server/test_complete_system.py

# Load testing (if locust is installed)
locust -f tests/load_test.py
```

## Resources

- [Project Documentation](./docs/)
- [System Documentation](./SYSTEM_DOCUMENTATION.md)
- [API Documentation](http://localhost:8080/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

## Questions?

- Open an issue for questions
- Check existing issues and discussions
- Contact maintainers

---

Thank you for contributing to Paralegal AI! Your efforts help make legal technology more accessible and efficient.
