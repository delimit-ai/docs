# Rails API Project

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
  controllers/
    api/
      v1/
        users_controller.rb    # API controllers
        base_controller.rb     # Shared API logic
  models/                      # ActiveRecord models
  serializers/                 # ActiveModel Serializers or Blueprinter
    user_serializer.rb
config/
  routes.rb                    # Route definitions
spec/                          # RSpec tests
  requests/
    api/v1/
      users_spec.rb
  factories/                   # FactoryBot factories
```

### Where Routes Are Defined
- Routes: `config/routes.rb` using `namespace`, `resources`, `scope`
- API versioning pattern:
```ruby
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      resources :users, only: [:index, :show, :create, :update, :destroy]
    end
  end
end
```
- View routes: `rails routes` or `rails routes -g users`

### Generating the OpenAPI Spec
Use `rswag` (Swagger for Rails) or `rspec-openapi`:

**rswag** (spec-driven):
```ruby
# Gemfile
gem 'rswag-api'
gem 'rswag-ui'
gem 'rswag-specs'
```
```bash
# Generate spec from RSpec integration tests
rails rswag:specs:swaggerize
# Output: swagger/v1/swagger.yaml
```

**rspec-openapi** (auto-generate from existing request specs):
```ruby
# Gemfile
gem 'rspec-openapi', group: :test
```
```bash
OPENAPI=1 rspec spec/requests/
# Output: doc/openapi.yaml
```

### Testing Commands
```bash
# Run all tests
bundle exec rspec

# Run request specs only
bundle exec rspec spec/requests/

# Run specific test
bundle exec rspec spec/requests/api/v1/users_spec.rb

# Run with coverage (SimpleCov)
COVERAGE=1 bundle exec rspec

# Regenerate API spec and lint
OPENAPI=1 bundle exec rspec spec/requests/ && npx delimit-cli lint doc/openapi.yaml
```

### Common Patterns to Watch
- Removing actions from `resources` (e.g., `only: [:index]`) removes endpoints (breaking)
- Changing `namespace` or `scope` in routes shifts URL paths (breaking)
- Modifying serializer attributes removes/renames response fields (breaking)
- Adding `before_action :authenticate!` to previously public controllers is breaking
- Changing strong parameters (`params.require().permit()`) alters accepted request bodies
- Adding API version namespace without maintaining old version is breaking

### Pre-Commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: delimit-lint
        name: Delimit API Governance
        entry: bash -c 'OPENAPI=1 bundle exec rspec spec/requests/ --format progress && npx delimit-cli lint doc/openapi.yaml'
        language: system
        pass_filenames: false
        files: 'app/controllers/api/|config/routes\.rb|app/serializers/'
```

## API Spec Location
- rswag: `swagger/v1/swagger.yaml`
- rspec-openapi: `doc/openapi.yaml`
- Swagger UI: `http://localhost:3000/api-docs` (if rswag-ui configured)
