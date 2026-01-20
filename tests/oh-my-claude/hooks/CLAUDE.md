# Hook Tests

pytest tests for oh-my-claude hooks.

## Framework

pytest >=8.0 with coverage via pytest-cov

## Running

```bash
cd tests/oh-my-claude/hooks
uv run --with pytest pytest . -v
```

## Structure

```python
class TestFeatureName:
    """Tests for specific feature."""

    def test_scenario_description(self, fixture):
        """Expected behavior in plain English."""
        # Arrange
        # Act
        # Assert
```

## Naming

| Element | Convention |
|---------|------------|
| Files | `test_{module_name}.py` |
| Classes | `Test{FeatureName}` |
| Methods | `test_{scenario}` |

## Fixtures (conftest.py)

| Fixture | Purpose |
|---------|---------|
| `temp_project` | Generic temp directory |
| `nodejs_project` | Creates package.json |
| `python_project` | Creates pyproject.toml |
| `sample_transcript` | Mock conversation data |
| `sample_todos` | Mock todo list |

## Mocking Patterns

**Environment variables:**
```python
def test_with_env(self, monkeypatch):
    monkeypatch.setenv("OMC_THRESHOLD", "200")
    monkeypatch.delenv("OTHER_VAR", raising=False)
```

**Function mocking:**
```python
from unittest.mock import patch

def test_with_mock(self):
    with patch("module.function", return_value="mocked"):
        result = call_code()
```

**Filesystem:**
```python
def test_file_ops(self, tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("content")
```

**Stdout capture:**
```python
def test_output(self, capsys):
    function_that_prints()
    captured = capsys.readouterr()
    assert "expected" in captured.out
```

## Coverage Focus

- Threshold boundaries (under, at, over)
- Edge cases (empty, binary, unicode, symlinks)
- Error paths (missing files, invalid JSON)
- Environment variable combinations

## Anti-Patterns

- Don't test implementation details
- Don't share mutable state between tests
- Don't mock what you can test directly
- Don't skip error path coverage
