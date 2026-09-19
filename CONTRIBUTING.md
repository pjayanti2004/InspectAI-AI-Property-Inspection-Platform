# Contributing to InspectAI

Thank you for your interest in contributing to InspectAI! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Be respectful, inclusive, and constructive.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/<your-username>/inspectai/issues) to avoid duplicates
2. Create a new issue with:
   - Clear, descriptive title
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version, OS, and dependency versions
   - Screenshots or error logs if applicable

### Suggesting Features

1. Check [existing issues](https://github.com/<your-username>/inspectai/issues) and the [Future Roadmap](README.md#future-roadmap)
2. Create a new issue with:
   - Problem statement
   - Proposed solution
   - Alternatives considered

### Pull Requests

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   # or
   git checkout -b fix/issue-123
   ```
3. **Make your changes** following the coding standards below
4. **Run tests** and ensure they pass:
   ```bash
   pytest tests/ --cov=streamlit_app
   ruff check streamlit_app/ tests/
   black --check streamlit_app/ tests/
   ```
5. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add support for drone image analysis"
   # or
   git commit -m "fix: handle empty Gemini response gracefully"
   ```
6. **Push** to your fork:
   ```bash
   git push origin feature/my-new-feature
   ```
7. **Open a Pull Request** against `main`

### PR Requirements

- [ ] All tests pass (`pytest tests/`)
- [ ] Code passes linting (`ruff check`)
- [ ] Code is formatted (`black --check`)
- [ ] New functions/classes have docstrings
- [ ] New features include tests
- [ ] `CHANGELOG.md` is updated

## Development Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/inspectai.git
cd inspectai

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black ruff mypy

# Set up environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Run tests
pytest tests/ -v

# Run the app
streamlit run streamlit_app/app.py
```

## Coding Standards

### Python Style
- **Formatter:** Black (line length 100)
- **Linter:** Ruff (replaces Flake8 + isort + more)
- **Type hints:** Required for all public functions and methods
- **Docstrings:** Google style for all public modules, classes, and functions

### Example

```python
from __future__ import annotations

from typing import Optional
import numpy as np

from streamlit_app.utils.exceptions import ValidationError
from streamlit_app.utils.logger import get_logger

logger = get_logger(__name__)


def analyze_damage_region(
    image: np.ndarray,
    region: tuple[int, int, int, int],
    *,
    min_confidence: float = 0.5,
) -> dict[str, any]:
    """Analyze a specific region for damage.

    Args:
        image:       Source image as a numpy array (H, W, 3) in RGB format.
        region:      Bounding box as (x1, y1, x2, y2) in pixel coordinates.
        min_confidence: Minimum confidence threshold for detection.

    Returns:
        Dict with keys: 'detected' (bool), 'confidence' (float),
        'damage_type' (str), 'severity' (str).

    Raises:
        ValidationError: If region coordinates are out of bounds.
    """
    x1, y1, x2, y2 = region
    h, w = image.shape[:2]

    if x1 < 0 or y1 < 0 or x2 > w or y2 > h:
        raise ValidationError(
            f"Region {region} is out of bounds for image {w}x{h}",
            field="region",
        )

    # ... implementation ...

    return {
        "detected": True,
        "confidence": 0.85,
        "damage_type": "Crack",
        "severity": "High",
    }
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

**Examples:**
```
feat(ai): add retry logic for Gemini API calls
fix(report): handle empty findings in timeline builder
docs(readme): add installation instructions
test(gemini): mock analyze_image_with_gemini for unit tests
refactor(pipeline): extract stage functions from run_inspection
```

## Project Structure

```
streamlit_app/
├── ai/                    # AI engines (Gemini, OpenCV, orchestration)
├── database/              # SQLite persistence layer
├── report/                # Report generation and rendering
├── components/            # Reusable UI components
├── pages/                 # Streamlit page modules
├── styles/                # Custom CSS
├── utils/                 # Utilities (validators, session, logging)
└── app.py                 # Entry point
```

## Testing

- Write tests for all new features and bug fixes
- Place tests in `tests/` matching the source structure
- Use `conftest.py` for shared fixtures
- Mock external APIs (Gemini) — never make real API calls in tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=streamlit_app --cov-report=html

# Run specific file
pytest tests/test_gemini_engine.py -v

# Run linting
ruff check streamlit_app/ tests/
black --check streamlit_app/ tests/
```

## Questions?

Open an issue or reach out to the maintainers. We're happy to help!
