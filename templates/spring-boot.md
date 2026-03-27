# Spring Boot Project

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
src/main/java/com/example/myapp/
  MyAppApplication.java          # @SpringBootApplication entry point
  controller/
    UserController.java          # @RestController with @RequestMapping
  service/
    UserService.java             # Business logic
  dto/
    CreateUserRequest.java       # Request DTOs
    UserResponse.java            # Response DTOs
  model/
    User.java                    # JPA entity
  repository/
    UserRepository.java          # Spring Data JPA
  config/
    OpenApiConfig.java           # springdoc-openapi config
src/main/resources/
  application.yml                # App config
src/test/java/com/example/myapp/
  controller/
    UserControllerTest.java      # @WebMvcTest
  integration/
    UserIntegrationTest.java     # @SpringBootTest
```

### Where Routes Are Defined
- Controllers: `src/main/java/**/controller/*.java`
- Annotations: `@RestController`, `@RequestMapping("/api/v1/users")`
- Methods: `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping`
- Path variables: `@PathVariable`, query params: `@RequestParam`
- Request bodies: `@RequestBody` with DTO classes
- Validation: `@Valid`, `@NotNull`, `@Size`, etc. on DTO fields

### Generating the OpenAPI Spec
Use `springdoc-openapi`:
```xml
<!-- pom.xml -->
<dependency>
  <groupId>org.springdoc</groupId>
  <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
  <version>2.3.0</version>
</dependency>
```

```yaml
# application.yml
springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
```

Export spec:
```bash
# Export via curl (app must be running)
curl http://localhost:8080/v3/api-docs > openapi.json
```

### Testing Commands
```bash
# Run all tests (Maven)
mvn test

# Run all tests (Gradle)
./gradlew test

# Run specific test class
mvn test -Dtest=UserControllerTest

# Run with coverage (JaCoCo)
mvn test jacoco:report

# Integration tests
mvn verify
```

### Common Patterns to Watch
- Adding `@NotNull` or `@NotBlank` to DTO fields makes them required (breaking)
- Removing fields from response DTOs is breaking
- Changing `@RequestMapping` path values shifts URLs (breaking)
- Switching from `@RequestParam` to `@PathVariable` changes the contract
- Adding `@PreAuthorize` or `@Secured` to previously open endpoints is breaking
- Changing `@JsonProperty` names alters serialized field names (breaking)
- Removing enum values from request/response enums is breaking

### Pre-Commit Hook
```bash
#!/bin/sh
# .githooks/pre-commit
curl -s http://localhost:8080/v3/api-docs > openapi.json 2>/dev/null
if [ $? -eq 0 ]; then
  npx delimit-cli lint openapi.json
fi
```
```bash
git config core.hooksPath .githooks
```

## API Spec Location
- Runtime: `http://localhost:8080/v3/api-docs`
- Swagger UI: `http://localhost:8080/swagger-ui.html`
