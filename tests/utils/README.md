# Test Utilities

This directory contains shared utilities for test files.

## Path Setup Utility

The `test_utils.py` module provides a centralized way to set up the Python path for all test files. This ensures imports work correctly in all environments:

- **Terminal execution**: `python tests/.../test_file.py`
- **VS Code debugger**: F5 debugging with breakpoints
- **Pytest**: `pytest tests/`
- **CI/CD**: Automated testing pipelines

### Usage

#### Preferred Method (Automatic)
Simply import the module at the top of your test file:

```python
import tests.utils.test_utils  # Sets up path automatically
```

#### Direct Function Call
You can also call the function directly:

```python
from tests.utils.test_utils import setup_project_path
setup_project_path()
```

#### With Custom Starting Point
If you need to specify a starting file:

```python
from tests.utils.test_utils import setup_project_path
setup_project_path(__file__)
```

### Backward Compatibility

For backward compatibility, `setup_python_path` is an alias for `setup_project_path`:

```python
from tests.utils.test_utils import setup_python_path  # Same as setup_project_path
```

### How It Works

The utility:
1. Tries to find the project root by looking for marker files (`pyproject.toml`, `requirements.txt`, `setup.py`)
2. Checks for key package directories (`rami`, `gov`, `yad2`, `gis`, `orchestration`)
3. Adds the project root to `sys.path` if not already present
4. Also adds the current working directory if it looks like the project root

### Migration Guide

If you have old test files with duplicate path setup code, replace it with:

```python
# Old way (duplicate code):
def setup_python_path():
    # ... lots of duplicate code ...
setup_python_path()

# New way (centralized):
import tests.utils.test_utils  # noqa: F401
```

This eliminates code duplication and ensures consistent behavior across all test files.

