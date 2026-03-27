# FastAPI Project

## Delimit Governance
- On session start: call `delimit_ledger_context` and `delimit_gov_health`
- After editing API routes: call `delimit_lint` to check for breaking changes
- Before committing: call `delimit_repo_diagnose`

## MANDATORY: Tool Routing
| Operation | ALWAYS use | NEVER use |
|-----------|-----------|-----------|
| Store credentials | `delimit_secret_store` | Write to ~/.delimit/secrets/ |
| Read credentials | `delimit_secret_get` | Read from ~/.delimit/secrets/ |
| Add tasks | `delimit_ledger_add` | Write to ~/.delimit/ledger/ |
| Store memory | `delimit_memory_store` | Write to ~/.delimit/memory/ |

## Framework-Specific

### Project Structure
```
app/
  main.py          # FastAPI app instance, top-level router includes
  routers/         # APIRouter modules (one per resource)
  models/          # Pydantic request/response models
  schemas/         # Database models (SQLAlchemy/Tortoise)
  dependencies.py  # Shared Depends() callables
  config.py        # Settings via pydantic-settings
tests/
  conftest.py      # Fixtures, TestClient setup
  test_*.py        # Test modules
```

### Where Routes Are Defined
- Main app: `app/main.py` (app = FastAPI())
- Route modules: `app/routers/*.py` using `APIRouter(prefix="/resource")`
- Path operations: `@router.get()`, `@router.post()`, etc.
- Response models: `response_model=` parameter on each route

### Generating the OpenAPI Spec
FastAPI auto-generates the spec at runtime. Export it for Delimit:
```bash
python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > openapi.json
```
Or add a script:
```python
# scripts/export_openapi.py
import json
from app.main import app

with open("openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)
```

### Testing Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run a specific test file
pytest tests/test_users.py -v

# Run tests matching a pattern
pytest -k "test_create"
```

### Common Patterns to Watch
- Adding `required` fields to Pydantic models breaks existing clients
- Changing `response_model` alters the response schema (breaking)
- Removing a route path or changing its method is always breaking
- Adding `Depends()` that requires new headers/query params is breaking
- Changing `status_code` on a route changes the documented response

### Pre-Commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: delimit-lint
        name: Delimit API Governance
        entry: bash -c 'python scripts/export_openapi.py && npx delimit-cli lint openapi.json'
        language: system
        pass_filenames: false
        files: 'app/(routers|models)/.*\.py$'
```

## API Spec Location
- Runtime: `http://localhost:8000/openapi.json`
- Exported: `openapi.json` (project root)
- Docs UI: `http://localhost:8000/docs` (Swagger) or `/redoc` (ReDoc)
