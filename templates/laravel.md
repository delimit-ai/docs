# Laravel Project

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
  Http/
    Controllers/
      Api/
        UserController.php      # API controllers
    Middleware/
    Requests/
      StoreUserRequest.php      # Form Request validation
    Resources/
      UserResource.php          # API Resources (response transformation)
      UserCollection.php
  Models/
    User.php                    # Eloquent models
routes/
  api.php                       # API route definitions (auto-prefixed /api)
tests/
  Feature/
    Api/
      UserTest.php              # Feature/integration tests
  Unit/
```

### Where Routes Are Defined
- API routes: `routes/api.php` (auto-prefixed with `/api`)
- Route definitions:
```php
Route::apiResource('users', UserController::class);
Route::get('/users/{user}/posts', [UserController::class, 'posts']);
Route::middleware('auth:sanctum')->group(function () {
    Route::post('/users', [UserController::class, 'store']);
});
```
- View all routes: `php artisan route:list --path=api`

### Generating the OpenAPI Spec
**l5-swagger** (annotation-based):
```php
/**
 * @OA\Get(
 *     path="/api/users",
 *     @OA\Response(response=200, description="Success",
 *         @OA\JsonContent(type="array", @OA\Items(ref="#/components/schemas/User"))
 *     )
 * )
 */
```
```bash
php artisan l5-swagger:generate
# Output: storage/api-docs/api-docs.json
```

**scramble** (auto-generates from code, zero annotations):
```bash
composer require dedoc/scramble
# Spec available at: /docs/api.json
```

### Testing Commands
```bash
# Run all tests
php artisan test

# Run with PHPUnit directly
./vendor/bin/phpunit

# Run feature tests only
php artisan test --testsuite=Feature

# Run specific test
php artisan test --filter=UserTest

# Run with coverage
php artisan test --coverage --min=80
```

### Common Patterns to Watch
- Adding validation rules in Form Requests makes fields required (breaking)
- Removing attributes from API Resources removes response fields (breaking)
- Changing `apiResource` to `resource` changes available endpoints
- Adding `auth:sanctum` middleware to previously public routes is breaking
- Changing route model binding keys (`getRouteKeyName()`) changes URL format
- Modifying `$hidden` or `$visible` on models changes serialized output
- Changing pagination (`paginate()` to `simplePaginate()`) alters response envelope

### Pre-Commit Hook
```bash
# Using composer scripts
composer run lint-api
# Where composer.json has:
# "lint-api": "php artisan l5-swagger:generate && npx delimit-cli lint storage/api-docs/api-docs.json"
```

## API Spec Location
- l5-swagger: `storage/api-docs/api-docs.json`
- scramble: `http://localhost:8000/docs/api.json`
- Swagger UI: `http://localhost:8000/api/documentation` (l5-swagger) or `http://localhost:8000/docs/api` (scramble)
