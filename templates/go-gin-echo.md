# Go (Gin/Echo) Project

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
cmd/
  server/
    main.go              # Entry point, server startup
internal/
  handler/
    user_handler.go      # HTTP handlers
  service/
    user_service.go      # Business logic
  model/
    user.go              # Domain models
  middleware/
    auth.go              # Authentication middleware
  router/
    router.go            # Route registration
api/
  openapi.yaml           # OpenAPI spec (manually maintained or generated)
docs/
  docs.go                # swag-generated docs
  swagger.json
```

### Where Routes Are Defined

**Gin:**
```go
func SetupRouter() *gin.Engine {
    r := gin.Default()
    v1 := r.Group("/api/v1")
    {
        v1.GET("/users", handler.ListUsers)
        v1.POST("/users", handler.CreateUser)
        v1.GET("/users/:id", handler.GetUser)
    }
    return r
}
```

**Echo:**
```go
e := echo.New()
v1 := e.Group("/api/v1")
v1.GET("/users", handler.ListUsers)
v1.POST("/users", handler.CreateUser)
```

### Generating the OpenAPI Spec
Use `swaggo/swag` for annotation-based generation:

```go
// ListUsers godoc
// @Summary      List users
// @Tags         users
// @Accept       json
// @Produce      json
// @Success      200  {array}   model.User
// @Router       /api/v1/users [get]
func ListUsers(c *gin.Context) { ... }
```

```bash
# Install swag
go install github.com/swaggo/swag/cmd/swag@latest

# Generate spec
swag init -g cmd/server/main.go -o docs/
# Output: docs/swagger.json
```

Alternatively, maintain `api/openapi.yaml` manually (common in Go projects).

### Testing Commands
```bash
# Run all tests
go test ./...

# Run with verbose output
go test -v ./...

# Run specific package
go test -v ./internal/handler/...

# Run with coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out

# Run with race detection
go test -race ./...
```

### Common Patterns to Watch
- Changing route group prefixes shifts all child paths (breaking)
- Changing `:id` param names or switching between path/query params is breaking
- Modifying struct tags (`json:"name"`) changes serialized field names (breaking)
- Adding required middleware to route groups affects all child routes
- Removing JSON fields from response structs is breaking
- Changing between `*string` (optional) and `string` (required) in request structs is breaking

### Pre-Commit Hook
```bash
#!/bin/sh
# .githooks/pre-commit
swag init -g cmd/server/main.go -o docs/ 2>/dev/null
npx delimit-cli lint docs/swagger.json
```
```bash
git config core.hooksPath .githooks
```

## API Spec Location
- Generated: `docs/swagger.json` (via swag)
- Manual: `api/openapi.yaml`
- Runtime: `http://localhost:8080/swagger/doc.json` (if gin-swagger configured)
