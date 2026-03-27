# NestJS Project

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
  main.ts              # Bootstrap, Swagger setup
  app.module.ts        # Root module
  users/
    users.module.ts    # Feature module
    users.controller.ts # Route handlers (@Get, @Post, etc.)
    users.service.ts   # Business logic
    dto/
      create-user.dto.ts  # Request DTOs with class-validator
      user.dto.ts         # Response DTOs
    entities/
      user.entity.ts  # TypeORM/Prisma entity
test/
  app.e2e-spec.ts      # E2E tests
  jest-e2e.json
```

### Where Routes Are Defined
- Controllers: `src/**/*.controller.ts` using decorators (`@Get()`, `@Post()`, etc.)
- DTOs: `src/**/dto/*.dto.ts` define request/response shapes
- Route prefix: set in `@Controller('users')` decorator
- Global prefix: `app.setGlobalPrefix('api')` in `main.ts`
- Swagger decorators: `@ApiTags()`, `@ApiResponse()`, `@ApiProperty()`

### Generating the OpenAPI Spec
NestJS has first-class Swagger support via `@nestjs/swagger`:
```typescript
// main.ts
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';

const config = new DocumentBuilder()
  .setTitle('My API')
  .setVersion('1.0')
  .build();
const document = SwaggerModule.createDocument(app, config);
SwaggerModule.setup('api-docs', app, document);

// Export spec to file
const fs = require('fs');
fs.writeFileSync('openapi.json', JSON.stringify(document, null, 2));
```

Export script:
```bash
# Add to package.json scripts
"export:openapi": "ts-node scripts/export-openapi.ts"
```

### Testing Commands
```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Test coverage
npm run test:cov

# Run specific test
npx jest src/users/users.controller.spec.ts

# Watch mode
npm run test -- --watch
```

### Common Patterns to Watch
- Adding `@IsNotEmpty()` or other validators to DTOs makes fields required (breaking)
- Removing `@ApiPropertyOptional()` makes a field required in the spec
- Changing `@Controller()` prefix changes all route paths (breaking)
- Adding guards (`@UseGuards(AuthGuard)`) to previously public endpoints is breaking
- Changing DTO class names with `@ApiExtraModels()` alters schema names

### Pre-Commit Hook
```json
// package.json
{
  "scripts": {
    "export:openapi": "ts-node scripts/export-openapi.ts",
    "lint:api": "npm run export:openapi && npx delimit-cli lint openapi.json"
  }
}
```
```bash
npx husky add .husky/pre-commit "npm run lint:api"
```

## API Spec Location
- Runtime: `http://localhost:3000/api-docs-json`
- Exported: `openapi.json` (project root)
- Swagger UI: `http://localhost:3000/api-docs`
