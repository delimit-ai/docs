# Next.js API Routes Project

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

### Project Structure (App Router)
```
app/
  api/
    users/
      route.ts               # GET, POST handlers for /api/users
      [id]/
        route.ts             # GET, PUT, DELETE for /api/users/:id
    auth/
      [...nextauth]/
        route.ts             # NextAuth.js catch-all
  lib/
    db.ts                    # Database client
    validators.ts            # Zod schemas for request validation
  types/
    api.ts                   # Shared API types
```

### Project Structure (Pages Router - Legacy)
```
pages/
  api/
    users/
      index.ts               # /api/users
      [id].ts                # /api/users/:id
```

### Where Routes Are Defined

**App Router (Next.js 13+):**
- File: `app/api/[path]/route.ts`
- Export named functions: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`
```typescript
// app/api/users/route.ts
export async function GET(request: Request) {
  const users = await db.user.findMany();
  return Response.json(users);
}

export async function POST(request: Request) {
  const body = await request.json();
  const user = await db.user.create({ data: body });
  return Response.json(user, { status: 201 });
}
```

**Pages Router:**
- File: `pages/api/[path].ts`
- Default export handler function

### Generating the OpenAPI Spec
Next.js does not auto-generate specs. Options:

**next-swagger-doc:**
```bash
npm install next-swagger-doc swagger-ui-react
```
```typescript
import { createSwaggerSpec } from 'next-swagger-doc';

export const getApiDocs = () => createSwaggerSpec({
  apiFolder: 'app/api',
  definition: {
    openapi: '3.0.0',
    info: { title: 'My API', version: '1.0' },
  },
});
```

**Manual spec** (recommended for governance):
Maintain `openapi.yaml` at project root alongside route implementations.

**ts-rest** (contract-first):
```typescript
import { initContract } from '@ts-rest/core';
const c = initContract();
export const contract = c.router({ ... });
```

### Testing Commands
```bash
# Run all tests (Jest)
npm test

# Run all tests (Vitest)
npx vitest

# Run API route tests only
npx jest __tests__/api/

# Run with coverage
npx jest --coverage

# E2E tests (Playwright)
npx playwright test
```

### Common Patterns to Watch
- Renaming or moving files in `app/api/` changes route paths (breaking)
- Removing an exported HTTP method function (GET, POST) removes that endpoint (breaking)
- Changing dynamic segment names (`[id]` to `[userId]`) changes param names
- Adding middleware.ts that blocks requests to previously open routes is breaking
- Changing Response.json() shape alters the response contract
- Moving from Pages Router to App Router may change route behavior

### Pre-Commit Hook
```json
// package.json
{
  "lint-staged": {
    "app/api/**/*.ts": "npx delimit-cli lint openapi.yaml"
  }
}
```
```bash
npx husky add .husky/pre-commit "npx lint-staged"
```

## API Spec Location
- Manual: `openapi.yaml` (project root)
- Generated: via next-swagger-doc at build time
- Runtime: `http://localhost:3000/api/docs` (if Swagger UI route configured)
