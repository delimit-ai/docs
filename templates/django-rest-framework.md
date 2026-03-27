# Django REST Framework Project

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
myproject/
  settings.py          # DRF config in REST_FRAMEWORK dict
  urls.py              # Root URL configuration
apps/
  users/
    urls.py            # App-level URL patterns
    views.py           # ViewSets or APIViews
    serializers.py     # Request/response serializers
    models.py          # Django ORM models
    permissions.py     # Custom permission classes
    filters.py         # django-filter FilterSets
    tests/
      test_views.py
      test_serializers.py
```

### Where Routes Are Defined
- Root URLs: `myproject/urls.py` with `include()` for app URLs
- App URLs: `apps/*/urls.py` using `router.register()` for ViewSets or `path()` for APIViews
- Router: `rest_framework.routers.DefaultRouter` auto-generates list/detail/create/update/delete
- Serializers: `apps/*/serializers.py` define request/response shapes
- ViewSets: `apps/*/views.py` with `@action()` decorator for custom endpoints

### Generating the OpenAPI Spec
Use `drf-spectacular` (recommended) or DRF's built-in schema generation:

```python
# settings.py
INSTALLED_APPS = [
    ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'My API',
    'VERSION': '1.0.0',
}
```

```bash
# Generate spec file
python manage.py spectacular --file openapi.json --format openapi-json

# Or YAML
python manage.py spectacular --file openapi.yaml --format openapi
```

### Testing Commands
```bash
# Run all tests
python manage.py test

# Run with pytest (if configured)
pytest

# Run specific app tests
python manage.py test apps.users

# Run with coverage
coverage run manage.py test && coverage report -m

# pytest with coverage
pytest --cov=apps --cov-report=term-missing
```

### Common Patterns to Watch
- Making serializer fields `required=True` (or removing `required=False`) is breaking
- Removing fields from serializers removes them from the response (breaking)
- Changing `permission_classes` from `AllowAny` to `IsAuthenticated` is breaking
- Adding `required` filter parameters changes the query contract
- Changing `lookup_field` on a ViewSet changes URL structure (breaking)
- Removing actions from a ViewSet removes endpoints (breaking)
- Pagination changes (`page_size`, pagination class) alter response envelope

### Pre-Commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: delimit-lint
        name: Delimit API Governance
        entry: bash -c 'python manage.py spectacular --file openapi.json --format openapi-json && npx delimit-cli lint openapi.json'
        language: system
        pass_filenames: false
        files: 'apps/.*(views|serializers|urls)\.py$'
```

## API Spec Location
- Generated: `python manage.py spectacular --file openapi.json --format openapi-json`
- Runtime: `http://localhost:8000/api/schema/` (if URL configured)
- Swagger UI: `http://localhost:8000/api/docs/` (with `SpectacularSwaggerView`)
- ReDoc: `http://localhost:8000/api/redoc/` (with `SpectacularRedocView`)
