# Express Project

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
src/
  app.js             # Express app setup, middleware
  server.js          # HTTP server entry point
  routes/            # Route modules (one per resource)
    users.js
    products.js
  controllers/       # Request handlers
  middleware/        # Auth, validation, error handling
  models/            # Data models (Mongoose/Sequelize/Prisma)
  validators/        # Request validation schemas (Joi/Zod)
tests/
  *.test.js          # Test files
openapi.yaml         # OpenAPI spec (manually maintained or generated)
```

### Where Routes Are Defined
- Route files: `src/routes/*.js` using `express.Router()`
- Mounted in: `src/app.js` via `app.use('/api/users', usersRouter)`
- Middleware chain: defined per-route or per-router

### Generating the OpenAPI Spec
Express does not auto-generate specs. Use one of these approaches:

**swagger-jsdoc** (annotations in code):
```js
// In route files, add JSDoc annotations:
/**
 * @openapi
 * /api/users:
 *   get:
 *     summary: List users
 *     responses:
 *       200:
 *         description: Success
 */
router.get('/', listUsers);
```
```bash
# Generate spec from annotations
npx swagger-jsdoc -d src/swagger-config.js -o openapi.json
```

**Manual spec**: Maintain `openapi.yaml` alongside code and lint on change.

### Testing Commands
```bash
# Run all tests (Jest)
npm test

# Run with coverage
npm test -- --coverage

# Run a specific test
npx jest tests/users.test.js

# Run tests in watch mode
npm test -- --watch

# Supertest for integration tests
npx jest tests/integration/
```

### Common Patterns to Watch
- Changing `app.use()` mount paths shifts all child routes (breaking)
- Removing or renaming route parameters (`:id` to `:userId`) is breaking
- Adding required middleware (e.g., auth) to previously public routes is breaking
- Changing response shapes in controllers alters the API contract
- Switching validation libraries may change error response format

### Pre-Commit Hook
```bash
# Using husky
npx husky install
npx husky add .husky/pre-commit "npx swagger-jsdoc -d src/swagger-config.js -o openapi.json && npx delimit-cli lint openapi.json"
```

## API Spec Location
- File: `openapi.yaml` or `openapi.json` (project root)
- Swagger UI: `http://localhost:3000/api-docs` (if swagger-ui-express is configured)
- Generated from annotations: `npx swagger-jsdoc -d src/swagger-config.js -o openapi.json`
