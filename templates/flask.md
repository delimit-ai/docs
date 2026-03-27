# Flask Project

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
  __init__.py          # Flask app factory (create_app)
  routes/
    __init__.py
    users.py           # Blueprint with route handlers
    auth.py
  models/
    user.py            # SQLAlchemy models
  schemas/
    user.py            # Marshmallow or Pydantic schemas
  extensions.py        # db, ma, jwt initialization
  config.py            # Configuration classes
tests/
  conftest.py          # Fixtures, test client
  test_users.py
```

### Where Routes Are Defined
- Blueprints: `app/routes/*.py` using `Blueprint`
- Route registration: `app/__init__.py` via `app.register_blueprint()`
```python
# app/routes/users.py
from flask import Blueprint, jsonify, request

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/', methods=['GET'])
def list_users():
    ...

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    ...
```

### Generating the OpenAPI Spec
**flask-smorest** (recommended, marshmallow-based):
```python
from flask_smorest import Api, Blueprint

api = Api(app)
blp = Blueprint('users', 'users', url_prefix='/api/users')

@blp.route('/')
class Users(MethodView):
    @blp.response(200, UserSchema(many=True))
    def get(self):
        ...
```
```bash
# Spec auto-generated at /api/openapi.json
curl http://localhost:5000/api/openapi.json > openapi.json
```

**apispec** (manual + marshmallow):
```python
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

spec = APISpec(title='My API', version='1.0', openapi_version='3.0',
               plugins=[MarshmallowPlugin()])
```

**flask-openapi3** (Pydantic-based, auto-generates spec):
```python
from flask_openapi3 import OpenAPI
app = OpenAPI(__name__)
```

### Testing Commands
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_users.py -v

# Run tests matching a pattern
pytest -k "test_create_user"
```

### Common Patterns to Watch
- Changing Blueprint `url_prefix` shifts all routes in that blueprint (breaking)
- Changing URL variable converters (`<int:id>` to `<string:id>`) changes the contract
- Removing route methods from `methods=[]` removes those HTTP methods (breaking)
- Making Marshmallow fields `required=True` is breaking for request schemas
- Removing fields from response schemas is breaking
- Adding `@jwt_required()` or `@login_required` to open endpoints is breaking
- Changing `jsonify()` response structure alters the contract

### Pre-Commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: delimit-lint
        name: Delimit API Governance
        entry: bash -c 'curl -s http://localhost:5000/api/openapi.json > openapi.json && npx delimit-cli lint openapi.json'
        language: system
        pass_filenames: false
        files: 'app/routes/.*\.py$'
```

## API Spec Location
- flask-smorest: `http://localhost:5000/api/openapi.json`
- Exported: `openapi.json` (project root)
- Swagger UI: `http://localhost:5000/api/docs` (flask-smorest built-in)
- ReDoc: `http://localhost:5000/api/redoc`
