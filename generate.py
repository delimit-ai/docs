#!/usr/bin/env python3
"""Generate the Delimit documentation site from templates and change type metadata."""

import os
import html

# ── Change Type Metadata ────────────────────────────────────────────────────

CHANGE_TYPES = [
    # Breaking changes (17)
    {
        "id": "endpoint-removed",
        "enum": "ENDPOINT_REMOVED",
        "value": "endpoint_removed",
        "title": "Endpoint Removed",
        "breaking": True,
        "severity": "high",
        "description": "An entire API endpoint (URL path) has been removed from the specification. All consumers calling this endpoint will receive 404 errors.",
        "why_breaking": "Any client that sends requests to the removed endpoint will immediately fail. There is no graceful fallback -- the server will return a 404 Not Found or similar error, breaking all integrations that depend on it.",
        "detection": "Delimit compares the <code>paths</code> keys between the old and new OpenAPI specs. Any path present in the old spec but absent in the new spec is flagged as <code>endpoint_removed</code>.",
        "before": '''paths:
  /users:
    get:
      summary: List users
  /users/{id}:
    get:
      summary: Get user by ID''',
        "after": '''paths:
  /users:
    get:
      summary: List users
  # /users/{id} has been removed''',
        "migration": "1. Announce the deprecation with a timeline (e.g., 90 days).\n2. Add a <code>deprecated: true</code> flag to the endpoint first.\n3. Return <code>410 Gone</code> with a body indicating the replacement.\n4. Provide a replacement endpoint or migration guide.\n5. Only remove the endpoint after the deprecation period.",
        "related": ["method-removed", "deprecated-added", "response-removed"],
        "keywords": "openapi endpoint removed breaking change api path deleted 404"
    },
    {
        "id": "method-removed",
        "enum": "METHOD_REMOVED",
        "value": "method_removed",
        "title": "Method Removed",
        "breaking": True,
        "severity": "high",
        "description": "An HTTP method (GET, POST, PUT, DELETE, PATCH, etc.) has been removed from an existing endpoint. Consumers using that method will receive 405 Method Not Allowed errors.",
        "why_breaking": "Clients explicitly choose HTTP methods for their requests. Removing a method means any consumer relying on it will fail with a 405 error, even though the endpoint path still exists.",
        "detection": "Delimit iterates over each shared path and compares the HTTP methods (get, post, put, delete, patch, head, options). Any method present in the old spec but absent in the new spec triggers this change.",
        "before": '''paths:
  /users/{id}:
    get:
      summary: Get user
    delete:
      summary: Delete user''',
        "after": '''paths:
  /users/{id}:
    get:
      summary: Get user
    # DELETE method removed''',
        "migration": "1. Mark the method as <code>deprecated: true</code> before removal.\n2. Return <code>405 Method Not Allowed</code> with an <code>Allow</code> header listing valid methods.\n3. Document the alternative approach (e.g., soft-delete via PATCH).\n4. Give consumers time to migrate before removing the method.",
        "related": ["endpoint-removed", "deprecated-added"],
        "keywords": "openapi http method removed breaking change delete put post 405"
    },
    {
        "id": "required-param-added",
        "enum": "REQUIRED_PARAM_ADDED",
        "value": "required_param_added",
        "title": "Required Parameter Added",
        "breaking": True,
        "severity": "high",
        "description": "A new required parameter has been added to an existing operation. Existing clients that do not send this parameter will receive validation errors.",
        "why_breaking": "Existing consumers do not know about the new parameter and will not include it in their requests. The server will reject these requests with a 400 Bad Request error, breaking all existing integrations.",
        "detection": "Delimit compares the <code>parameters</code> arrays for each operation. Any new parameter with <code>required: true</code> that was not present in the old spec is flagged.",
        "before": '''paths:
  /users:
    get:
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: integer''',
        "after": '''paths:
  /users:
    get:
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: integer
        - name: organization_id
          in: query
          required: true
          schema:
            type: string''',
        "migration": "1. Make the new parameter optional with a sensible default value.\n2. If the parameter must be required, version the endpoint (e.g., <code>/v2/users</code>).\n3. Communicate the change to consumers before enforcing it.\n4. Consider using a header or context-based default for backward compatibility.",
        "related": ["optional-param-added", "param-removed", "param-required-changed"],
        "keywords": "openapi required parameter added breaking change query header 400"
    },
    {
        "id": "param-removed",
        "enum": "PARAM_REMOVED",
        "value": "param_removed",
        "title": "Parameter Removed",
        "breaking": True,
        "severity": "high",
        "description": "An existing parameter has been removed from an operation. Clients sending this parameter may receive errors or experience silent behavior changes.",
        "why_breaking": "Consumers that include the removed parameter may get validation errors (strict servers) or have their parameter silently ignored (lenient servers). Either way, the intended behavior changes.",
        "detection": "Delimit identifies parameters by their <code>name</code> and <code>in</code> location (query, header, path, cookie). A parameter present in the old spec but absent in the new spec is flagged.",
        "before": '''parameters:
  - name: sort_by
    in: query
    schema:
      type: string
  - name: include_deleted
    in: query
    schema:
      type: boolean''',
        "after": '''parameters:
  - name: sort_by
    in: query
    schema:
      type: string
  # include_deleted parameter removed''',
        "migration": "1. Deprecate the parameter first by adding <code>deprecated: true</code>.\n2. Continue accepting the parameter but ignore it server-side.\n3. Log a warning when the deprecated parameter is received.\n4. Remove after a deprecation period.",
        "related": ["required-param-added", "optional-param-added"],
        "keywords": "openapi parameter removed breaking change query header path deleted"
    },
    {
        "id": "response-removed",
        "enum": "RESPONSE_REMOVED",
        "value": "response_removed",
        "title": "Response Removed",
        "breaking": True,
        "severity": "high",
        "description": "A success response (2xx) has been removed from an operation. Clients expecting this response status code will not handle the new response correctly.",
        "why_breaking": "Consumers build their error handling and response parsing around documented status codes. Removing a 2xx response means clients may not properly handle the new response, leading to incorrect application behavior.",
        "detection": "Delimit compares response status codes for each operation. Only 2xx response removals are flagged as breaking since error response changes are generally non-breaking.",
        "before": '''responses:
  "200":
    description: Success
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/User"
  "204":
    description: No content''',
        "after": '''responses:
  "200":
    description: Success
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/User"
  # 204 response removed''',
        "migration": "1. Document the new response behavior clearly.\n2. If consolidating responses, ensure the remaining response covers all use cases.\n3. Communicate the change in advance so consumers can update their response handling.\n4. Consider versioning the API if the response semantics change significantly.",
        "related": ["response-added", "endpoint-removed", "response-type-changed"],
        "keywords": "openapi response removed breaking change status code 2xx"
    },
    {
        "id": "required-field-added",
        "enum": "REQUIRED_FIELD_ADDED",
        "value": "required_field_added",
        "title": "Required Field Added",
        "breaking": True,
        "severity": "high",
        "description": "A new required field has been added to a request body schema. Existing clients that do not include this field will receive validation errors.",
        "why_breaking": "Existing consumers construct request bodies based on the current schema. A new required field means every consumer must update their code to include it, or their requests will be rejected with a 400/422 error.",
        "detection": "Delimit performs deep schema comparison on request body and response schemas. A field that appears in the <code>required</code> array of the new spec but was not present in the old spec is flagged.",
        "before": '''components:
  schemas:
    CreateUser:
      type: object
      required: [name, email]
      properties:
        name:
          type: string
        email:
          type: string''',
        "after": '''components:
  schemas:
    CreateUser:
      type: object
      required: [name, email, organization_id]
      properties:
        name:
          type: string
        email:
          type: string
        organization_id:
          type: string''',
        "migration": "1. Make the field optional with a default value instead.\n2. If it must be required, provide a migration window.\n3. Consider adding the field as optional first, then making it required in a later version.\n4. Auto-populate the field server-side for existing consumers during the transition.",
        "related": ["optional-field-added", "field-removed", "required-param-added"],
        "keywords": "openapi required field added breaking change request body schema validation"
    },
    {
        "id": "field-removed",
        "enum": "FIELD_REMOVED",
        "value": "field_removed",
        "title": "Field Removed",
        "breaking": True,
        "severity": "high",
        "description": "A field has been removed from a schema (request body, response, or component). Consumers that read or write this field will break.",
        "why_breaking": "Removing a field from a response breaks consumers that read it. Removing a field from a request body means consumers sending it will either get errors or have data silently dropped.",
        "detection": "Delimit recursively compares object properties in schemas. A property present in the old spec's <code>properties</code> but absent in the new spec is flagged, especially if it was in the <code>required</code> array.",
        "before": '''components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        legacy_role:
          type: string''',
        "after": '''components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        # legacy_role removed''',
        "migration": "1. Mark the field as <code>deprecated: true</code> before removing it.\n2. Continue returning the field with a null or default value.\n3. For response fields, add a sunset header indicating when the field will be removed.\n4. Provide a replacement field if applicable.",
        "related": ["required-field-added", "optional-field-added", "deprecated-added"],
        "keywords": "openapi field removed breaking change schema property deleted response body"
    },
    {
        "id": "type-changed",
        "enum": "TYPE_CHANGED",
        "value": "type_changed",
        "title": "Type Changed",
        "breaking": True,
        "severity": "high",
        "description": "The data type of a field, parameter, or schema has changed (e.g., from <code>string</code> to <code>integer</code>). All consumers parsing this value will break.",
        "why_breaking": "Type changes are among the most disruptive breaking changes. Every consumer that parses, validates, or stores this value based on the old type will fail. Strongly-typed clients will fail at compile time; dynamic clients will fail at runtime.",
        "detection": "Delimit compares the <code>type</code> property at every level of the schema hierarchy -- parameters, request bodies, responses, and nested objects. Any mismatch is flagged.",
        "before": '''properties:
  user_id:
    type: string
    description: User identifier''',
        "after": '''properties:
  user_id:
    type: integer
    description: User identifier''',
        "migration": "1. Never change a field's type in-place. Add a new field with the new type.\n2. Deprecate the old field and keep returning it with the original type.\n3. If you must change the type, version the API.\n4. Consider using a union type during transition if your spec supports it.",
        "related": ["param-type-changed", "response-type-changed", "format-changed"],
        "keywords": "openapi type changed breaking change string integer boolean schema property"
    },
    {
        "id": "format-changed",
        "enum": "FORMAT_CHANGED",
        "value": "format_changed",
        "title": "Format Changed",
        "breaking": True,
        "severity": "high",
        "description": "The format of a field has changed (e.g., from <code>date-time</code> to <code>date</code>, or <code>int32</code> to <code>int64</code>). Consumers parsing this value with format-specific logic will break.",
        "why_breaking": "Many consumers use format information to choose parsing strategies. Changing from <code>date-time</code> to <code>date</code> or from <code>uuid</code> to plain <code>string</code> can break validation, storage, and display logic.",
        "detection": "Delimit compares the <code>format</code> property on schema fields. A change in format value between old and new specs is flagged as breaking.",
        "before": '''properties:
  created_at:
    type: string
    format: date-time''',
        "after": '''properties:
  created_at:
    type: string
    format: date''',
        "migration": "1. Add a new field with the new format rather than changing the existing one.\n2. If the format change is widening (e.g., date to date-time), it may be safe but should still be communicated.\n3. Provide both formats during a transition period.\n4. Update all SDK code generators after the change.",
        "related": ["type-changed", "param-type-changed"],
        "keywords": "openapi format changed breaking change date-time uuid int32 int64"
    },
    {
        "id": "enum-value-removed",
        "enum": "ENUM_VALUE_REMOVED",
        "value": "enum_value_removed",
        "title": "Enum Value Removed",
        "breaking": True,
        "severity": "high",
        "description": "A value has been removed from an enum list. Consumers sending the removed value will receive validation errors; consumers parsing it will encounter unexpected behavior.",
        "why_breaking": "Consumers may be sending the removed enum value in requests (causing 400 errors) or expecting to receive it in responses (causing parsing failures). Either direction is a breaking change.",
        "detection": "Delimit compares <code>enum</code> arrays on parameters and schema properties. Values present in the old enum set but absent in the new set are flagged.",
        "before": '''properties:
  status:
    type: string
    enum: [active, inactive, pending, archived]''',
        "after": '''properties:
  status:
    type: string
    enum: [active, inactive, pending]
    # "archived" removed''',
        "migration": "1. Keep the old enum value but mark it as deprecated in the description.\n2. Map the old value to a new value server-side during a transition period.\n3. Return a warning header when the deprecated value is used.\n4. Only remove after confirming no consumers send or expect this value.",
        "related": ["enum-value-added", "type-changed"],
        "keywords": "openapi enum value removed breaking change enumeration status validation"
    },
    {
        "id": "param-type-changed",
        "enum": "PARAM_TYPE_CHANGED",
        "value": "param_type_changed",
        "title": "Parameter Type Changed",
        "breaking": True,
        "severity": "high",
        "description": "The data type of a parameter has changed (e.g., query parameter changed from <code>string</code> to <code>integer</code>). Consumers sending the old type will fail validation.",
        "why_breaking": "Consumers construct parameter values based on the documented type. Changing a query parameter from string to integer means existing string-based requests will fail server-side validation.",
        "detection": "Delimit compares the <code>schema.type</code> of parameters that exist in both old and new specs. A type mismatch triggers both <code>param_type_changed</code> and the general <code>type_changed</code> change.",
        "before": '''parameters:
  - name: user_id
    in: query
    schema:
      type: string''',
        "after": '''parameters:
  - name: user_id
    in: query
    schema:
      type: integer''',
        "migration": "1. Add a new parameter with the new type and deprecate the old one.\n2. Accept both types server-side during a transition period.\n3. If string-to-number, consider continuing to accept quoted numbers.\n4. Version the endpoint if the type change is fundamental.",
        "related": ["type-changed", "param-required-changed", "param-removed"],
        "keywords": "openapi parameter type changed breaking change query header string integer"
    },
    {
        "id": "param-required-changed",
        "enum": "PARAM_REQUIRED_CHANGED",
        "value": "param_required_changed",
        "title": "Parameter Required Changed",
        "breaking": True,
        "severity": "high",
        "description": "A parameter has changed from optional to required. Existing clients that do not send this parameter will start receiving validation errors.",
        "why_breaking": "Consumers that previously omitted this optional parameter will now receive 400 errors because the server requires it. This is functionally identical to adding a new required parameter for affected consumers.",
        "detection": "Delimit compares the <code>required</code> flag on parameters that exist in both old and new specs. A change from <code>false</code> (or absent) to <code>true</code> is flagged.",
        "before": '''parameters:
  - name: api_version
    in: header
    required: false
    schema:
      type: string''',
        "after": '''parameters:
  - name: api_version
    in: header
    required: true
    schema:
      type: string''',
        "migration": "1. Instead of making it required, add a default value so existing requests work.\n2. If it must be required, provide a migration period where the server supplies a default.\n3. Communicate the change well in advance.\n4. Consider using API versioning to introduce the requirement.",
        "related": ["required-param-added", "param-type-changed", "param-removed"],
        "keywords": "openapi parameter optional required changed breaking change validation"
    },
    {
        "id": "response-type-changed",
        "enum": "RESPONSE_TYPE_CHANGED",
        "value": "response_type_changed",
        "title": "Response Type Changed",
        "breaking": True,
        "severity": "high",
        "description": "The type of a response schema has changed (e.g., from <code>object</code> to <code>array</code>, or <code>string</code> to <code>integer</code>). All consumers parsing this response will break.",
        "why_breaking": "Response type changes are the most impactful breaking changes for consumers. Every client that deserializes the response based on the old type will fail. This causes runtime errors in production.",
        "detection": "Delimit performs deep schema comparison on response bodies. When a type mismatch is found within a response context (identified by status code in the path), it emits <code>response_type_changed</code> in addition to the general <code>type_changed</code>.",
        "before": '''responses:
  "200":
    content:
      application/json:
        schema:
          type: object
          properties:
            users:
              type: array''',
        "after": '''responses:
  "200":
    content:
      application/json:
        schema:
          type: array
          items:
            $ref: "#/components/schemas/User"''',
        "migration": "1. Never change response types in-place. Create a new endpoint version.\n2. If wrapping/unwrapping a response, keep the old format and add a new field.\n3. Use content negotiation (Accept header) to serve both formats.\n4. Provide SDK migration guides for each supported language.",
        "related": ["type-changed", "response-removed", "field-removed"],
        "keywords": "openapi response type changed breaking change object array schema deserialization"
    },
    {
        "id": "security-removed",
        "enum": "SECURITY_REMOVED",
        "value": "security_removed",
        "title": "Security Removed",
        "breaking": True,
        "severity": "high",
        "description": "A security scheme has been removed from the spec or from an operation. Consumers configured to authenticate with this scheme will need to change their authentication approach.",
        "why_breaking": "Removing a security scheme breaks consumers that are configured to use it. Their authentication tokens or credentials become invalid for the API, and they must reconfigure their authentication.",
        "detection": "Delimit compares both global security schemes (under <code>components/securitySchemes</code>) and per-operation security requirements. Schemes present in the old spec but absent in the new spec are flagged.",
        "before": '''components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
    BearerAuth:
      type: http
      scheme: bearer''',
        "after": '''components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
    # ApiKeyAuth removed''',
        "migration": "1. Announce the deprecation of the old auth scheme with a timeline.\n2. Support both authentication methods during a transition period.\n3. Provide migration documentation showing the new authentication flow.\n4. Invalidate old credentials only after the transition period ends.",
        "related": ["security-added", "security-scope-removed"],
        "keywords": "openapi security scheme removed breaking change authentication apikey bearer oauth"
    },
    {
        "id": "security-scope-removed",
        "enum": "SECURITY_SCOPE_REMOVED",
        "value": "security_scope_removed",
        "title": "Security Scope Removed",
        "breaking": True,
        "severity": "high",
        "description": "An OAuth scope has been removed from a security requirement. Consumers whose tokens include this scope may experience authorization changes.",
        "why_breaking": "Removing an OAuth scope can change authorization behavior. Consumers may have tokens that were specifically granted this scope, and removing it from the spec may indicate the server no longer recognizes it.",
        "detection": "Delimit compares the scope arrays within security requirements for each scheme. Scopes present in the old spec but absent in the new spec are flagged.",
        "before": '''security:
  - OAuth2:
    - read:users
    - write:users
    - admin:users''',
        "after": '''security:
  - OAuth2:
    - read:users
    - write:users
    # admin:users scope removed''',
        "migration": "1. Map the old scope to an equivalent new scope server-side.\n2. Continue accepting the old scope during a transition period.\n3. Notify consumers to request updated tokens.\n4. Update OAuth consent screens and documentation.",
        "related": ["security-removed", "security-added"],
        "keywords": "openapi oauth scope removed breaking change authorization token permissions"
    },
    {
        "id": "max-length-decreased",
        "enum": "MAX_LENGTH_DECREASED",
        "value": "max_length_decreased",
        "title": "Max Length Decreased",
        "breaking": True,
        "severity": "high",
        "description": "A <code>maxLength</code> or <code>maxItems</code> constraint has been decreased or newly added. Values that were previously valid may now be rejected.",
        "why_breaking": "Consumers sending values that fit within the old maximum but exceed the new maximum will have their requests rejected. This is especially problematic for stored data that was valid under the old constraint.",
        "detection": "Delimit compares <code>maxLength</code> and <code>maxItems</code> constraints. A decrease in value, or adding a max constraint where none existed, is flagged as breaking.",
        "before": '''properties:
  description:
    type: string
    maxLength: 1000''',
        "after": '''properties:
  description:
    type: string
    maxLength: 500''',
        "migration": "1. Validate existing data against the new constraint before deploying.\n2. Truncate or migrate values that exceed the new maximum.\n3. Communicate the new limit to consumers before enforcing it.\n4. Consider a warning period where over-limit values are accepted but logged.",
        "related": ["min-length-increased", "type-changed"],
        "keywords": "openapi maxLength decreased breaking change validation constraint maxItems limit"
    },
    {
        "id": "min-length-increased",
        "enum": "MIN_LENGTH_INCREASED",
        "value": "min_length_increased",
        "title": "Min Length Increased",
        "breaking": True,
        "severity": "high",
        "description": "A <code>minLength</code> or <code>minItems</code> constraint has been increased or newly added. Values that were previously valid may now be rejected.",
        "why_breaking": "Consumers sending values that met the old minimum but fall below the new minimum will have their requests rejected. This affects any consumer providing short values or empty collections.",
        "detection": "Delimit compares <code>minLength</code> and <code>minItems</code> constraints. An increase in value, or adding a min constraint where none existed (greater than 0), is flagged.",
        "before": '''properties:
  username:
    type: string
    minLength: 1''',
        "after": '''properties:
  username:
    type: string
    minLength: 3''',
        "migration": "1. Validate existing data against the new constraint before deploying.\n2. Pad or migrate values that fall below the new minimum.\n3. Apply the new constraint only to new values, grandfathering existing ones.\n4. Provide clear error messages explaining the new minimum requirement.",
        "related": ["max-length-decreased", "type-changed"],
        "keywords": "openapi minLength increased breaking change validation constraint minItems minimum"
    },
    # Non-breaking changes (10)
    {
        "id": "endpoint-added",
        "enum": "ENDPOINT_ADDED",
        "value": "endpoint_added",
        "title": "Endpoint Added",
        "breaking": False,
        "severity": "low",
        "description": "A new endpoint has been added to the API. This is purely additive and does not affect existing consumers.",
        "why_breaking": "This is a non-breaking change. New endpoints do not affect existing consumers. They can start using the new endpoint at their convenience.",
        "detection": "Delimit compares the <code>paths</code> keys between specs. Any path present in the new spec but absent in the old spec is flagged as <code>endpoint_added</code>.",
        "before": '''paths:
  /users:
    get:
      summary: List users''',
        "after": '''paths:
  /users:
    get:
      summary: List users
  /teams:
    get:
      summary: List teams''',
        "migration": "No migration needed. Document the new endpoint and notify consumers of the new capability. Update SDKs and client libraries to expose the new functionality.",
        "related": ["endpoint-removed", "method-added"],
        "keywords": "openapi endpoint added non-breaking change new api path"
    },
    {
        "id": "method-added",
        "enum": "METHOD_ADDED",
        "value": "method_added",
        "title": "Method Added",
        "breaking": False,
        "severity": "low",
        "description": "A new HTTP method has been added to an existing endpoint. This is additive and does not affect existing consumers.",
        "why_breaking": "This is a non-breaking change. Adding a new method to an existing endpoint does not affect consumers using other methods on the same endpoint.",
        "detection": "Delimit compares HTTP methods for each shared path. Methods present in the new spec but absent in the old spec are flagged as <code>method_added</code>.",
        "before": '''paths:
  /users/{id}:
    get:
      summary: Get user''',
        "after": '''paths:
  /users/{id}:
    get:
      summary: Get user
    patch:
      summary: Update user''',
        "migration": "No migration needed. Document the new method, update SDKs, and notify consumers.",
        "related": ["method-removed", "endpoint-added"],
        "keywords": "openapi http method added non-breaking change new operation"
    },
    {
        "id": "optional-param-added",
        "enum": "OPTIONAL_PARAM_ADDED",
        "value": "optional_param_added",
        "title": "Optional Parameter Added",
        "breaking": False,
        "severity": "low",
        "description": "A new optional parameter has been added to an operation. Existing clients will continue to work without changes.",
        "why_breaking": "This is a non-breaking change. Optional parameters have defaults or can be omitted. Existing consumers are unaffected and can adopt the parameter at their own pace.",
        "detection": "Delimit checks new parameters for their <code>required</code> flag. Parameters with <code>required: false</code> (or no required flag, which defaults to false) are classified as optional additions.",
        "before": '''parameters:
  - name: limit
    in: query
    required: false
    schema:
      type: integer''',
        "after": '''parameters:
  - name: limit
    in: query
    required: false
    schema:
      type: integer
  - name: cursor
    in: query
    required: false
    schema:
      type: string''',
        "migration": "No migration needed. Document the new parameter with its default behavior. Update SDKs to expose the new option.",
        "related": ["required-param-added", "param-removed"],
        "keywords": "openapi optional parameter added non-breaking change query"
    },
    {
        "id": "response-added",
        "enum": "RESPONSE_ADDED",
        "value": "response_added",
        "title": "Response Added",
        "breaking": False,
        "severity": "low",
        "description": "A new response status code has been added to an operation. This is additive and does not affect existing consumers.",
        "why_breaking": "This is a non-breaking change. Properly implemented clients should handle unexpected status codes gracefully. The new response provides additional information about the API's behavior.",
        "detection": "Delimit compares response status codes between old and new specs. New status codes are flagged as <code>response_added</code>.",
        "before": '''responses:
  "200":
    description: Success''',
        "after": '''responses:
  "200":
    description: Success
  "429":
    description: Rate limited''',
        "migration": "No migration needed. Update client error handling to take advantage of the new response code for better error messages and retry logic.",
        "related": ["response-removed", "response-type-changed"],
        "keywords": "openapi response added non-breaking change status code"
    },
    {
        "id": "optional-field-added",
        "enum": "OPTIONAL_FIELD_ADDED",
        "value": "optional_field_added",
        "title": "Optional Field Added",
        "breaking": False,
        "severity": "low",
        "description": "A new optional field has been added to a schema. Existing clients will continue to work; the new field can be adopted at their convenience.",
        "why_breaking": "This is a non-breaking change. Optional fields can be omitted in requests and may or may not appear in responses. Well-behaved clients should ignore unknown fields.",
        "detection": "Delimit checks new properties in schemas. Properties that are not in the <code>required</code> array are classified as optional field additions.",
        "before": '''components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string''',
        "after": '''components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        avatar_url:
          type: string''',
        "migration": "No migration needed. Update SDKs to include the new field. Consumers can start using it when ready.",
        "related": ["required-field-added", "field-removed"],
        "keywords": "openapi optional field added non-breaking change schema property"
    },
    {
        "id": "enum-value-added",
        "enum": "ENUM_VALUE_ADDED",
        "value": "enum_value_added",
        "title": "Enum Value Added",
        "breaking": False,
        "severity": "low",
        "description": "A new value has been added to an enum list. Existing values continue to work. Consumers should handle unknown enum values gracefully.",
        "why_breaking": "This is a non-breaking change in principle, though consumers with strict enum validation may need updates. Well-designed clients should handle unknown enum values.",
        "detection": "Delimit compares enum arrays. Values present in the new spec but absent in the old spec are flagged as <code>enum_value_added</code>.",
        "before": '''properties:
  status:
    type: string
    enum: [active, inactive]''',
        "after": '''properties:
  status:
    type: string
    enum: [active, inactive, pending]''',
        "migration": "No migration strictly needed. Consumers should ensure they handle unknown enum values gracefully. Update any client-side enum types or validation to include the new value.",
        "related": ["enum-value-removed"],
        "keywords": "openapi enum value added non-breaking change enumeration"
    },
    {
        "id": "description-changed",
        "enum": "DESCRIPTION_CHANGED",
        "value": "description_changed",
        "title": "Description Changed",
        "breaking": False,
        "severity": "low",
        "description": "A description field has been modified. This is a documentation-only change with no functional impact on consumers.",
        "why_breaking": "This is a non-breaking change. Description changes are purely cosmetic and do not affect API behavior, request/response formats, or validation.",
        "detection": "Delimit compares <code>description</code> fields on operations, parameters, schemas, and properties. Any text change is flagged as <code>description_changed</code>.",
        "before": '''paths:
  /users:
    get:
      description: Get all users''',
        "after": '''paths:
  /users:
    get:
      description: Retrieve a paginated list of all users in the organization''',
        "migration": "No migration needed. Updated descriptions improve documentation quality. Regenerate SDK documentation if auto-generated.",
        "related": ["deprecated-added"],
        "keywords": "openapi description changed non-breaking change documentation"
    },
    {
        "id": "security-added",
        "enum": "SECURITY_ADDED",
        "value": "security_added",
        "title": "Security Added",
        "breaking": False,
        "severity": "low",
        "description": "A new security scheme has been added to the spec or to an operation. Existing authentication methods continue to work.",
        "why_breaking": "This is a non-breaking change when added as an additional authentication option. Consumers can continue using existing auth methods. Note: if this replaces all existing auth, it could be breaking in practice.",
        "detection": "Delimit compares security schemes in <code>components/securitySchemes</code> and per-operation security arrays. New schemes are flagged as <code>security_added</code>.",
        "before": '''components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer''',
        "after": '''components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key''',
        "migration": "No migration needed. Document the new authentication option. Consumers can adopt it if preferred.",
        "related": ["security-removed", "security-scope-removed"],
        "keywords": "openapi security scheme added non-breaking change authentication"
    },
    {
        "id": "deprecated-added",
        "enum": "DEPRECATED_ADDED",
        "value": "deprecated_added",
        "title": "Deprecated Added",
        "breaking": False,
        "severity": "low",
        "description": "An operation or field has been marked as <code>deprecated: true</code>. This signals intent to remove but does not break existing consumers.",
        "why_breaking": "This is a non-breaking change. Deprecation is a warning, not a removal. The deprecated element continues to function. It signals that consumers should plan to migrate.",
        "detection": "Delimit compares the <code>deprecated</code> flag on operations and schema properties. A change from <code>false</code> (or absent) to <code>true</code> is flagged.",
        "before": '''paths:
  /users/search:
    get:
      summary: Search users''',
        "after": '''paths:
  /users/search:
    get:
      summary: Search users
      deprecated: true''',
        "migration": "No immediate migration needed. Plan to migrate away from the deprecated element before it is removed. Check the API changelog for the planned removal date.",
        "related": ["endpoint-removed", "method-removed", "field-removed"],
        "keywords": "openapi deprecated added non-breaking change sunset warning"
    },
    {
        "id": "default-changed",
        "enum": "DEFAULT_CHANGED",
        "value": "default_changed",
        "title": "Default Changed",
        "breaking": False,
        "severity": "low",
        "description": "The default value of a parameter or field has changed. Consumers relying on the old default behavior will see different results.",
        "why_breaking": "Classified as non-breaking because consumers explicitly setting the value are unaffected. However, consumers relying on the default (by omitting the parameter) will experience behavior changes. Review carefully.",
        "detection": "Delimit compares <code>default</code> values on parameters and schema properties. Any change in the default value is flagged as <code>default_changed</code>.",
        "before": '''parameters:
  - name: limit
    in: query
    schema:
      type: integer
      default: 20''',
        "after": '''parameters:
  - name: limit
    in: query
    schema:
      type: integer
      default: 50''',
        "migration": "1. Communicate the default value change to consumers.\n2. Consumers relying on the default should explicitly set the old value if they need the previous behavior.\n3. Update documentation to reflect the new default.\n4. Consider whether this warrants a MINOR version bump in your API.",
        "related": ["type-changed", "format-changed"],
        "keywords": "openapi default value changed non-breaking change parameter schema"
    },
]

# ── HTML Template ────────────────────────────────────────────────────────────

BASE_URL = "https://delimit-ai.github.io/docs"

def nav_html(active=""):
    items = [
        ("Home", "/docs/"),
        ("Quick Start", "/docs/quickstart/"),
        ("CLI Reference", "/docs/cli/"),
        ("GitHub Action", "/docs/action/"),
        ("MCP Server", "/docs/mcp/"),
        ("Policies", "/docs/policies/"),
        ("Hooks", "/docs/hooks/"),
        ("Change Types", "/docs/changes/"),
        ("Integrations", "/docs/integrations/claude-code.html"),
    ]
    out = '<nav class="sidebar">\n'
    out += '  <a href="/docs/" class="logo">Delimit</a>\n'
    out += '  <ul>\n'
    for label, href in items:
        cls = ' class="active"' if label == active else ""
        out += f'    <li><a href="{href}"{cls}>{label}</a></li>\n'
    out += '  </ul>\n'
    out += '  <div class="sidebar-footer">\n'
    out += '    <a href="https://github.com/delimit-ai/delimit-action" target="_blank">GitHub</a>\n'
    out += '    <a href="https://www.npmjs.com/package/delimit-cli" target="_blank">npm</a>\n'
    out += '    <a href="https://delimit.ai" target="_blank">delimit.ai</a>\n'
    out += '  </div>\n'
    out += '</nav>\n'
    return out


def page(title, description, body_html, canonical_path, active_nav="", json_ld=None):
    canonical = f"{BASE_URL}{canonical_path}"
    ld_block = ""
    if json_ld:
        import json
        ld_block = f'<script type="application/ld+json">{json.dumps(json_ld)}</script>'
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} - Delimit Docs</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{canonical}">
  <link rel="stylesheet" href="/docs/style.css">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>&#x1f6e1;</text></svg>">
  {ld_block}
</head>
<body>
  {nav_html(active_nav)}
  <main>
    {body_html}
  </main>
  <footer>
    <p>Delimit &mdash; API governance for AI coding assistants &middot;
      <a href="https://delimit.ai">delimit.ai</a> &middot;
      <a href="https://github.com/delimit-ai/delimit-action">GitHub</a> &middot;
      <a href="https://www.npmjs.com/package/delimit-cli">npm</a>
    </p>
  </footer>
</body>
</html>'''


# ── Page Generators ──────────────────────────────────────────────────────────

def generate_index():
    body = '''
    <h1>Delimit Documentation</h1>
    <p class="lead">API governance for AI coding assistants. Catch breaking changes before merge with deterministic diff analysis, policy enforcement, and semver classification.</p>

    <div class="card-grid">
      <a href="/docs/quickstart/" class="card">
        <h3>Quick Start</h3>
        <p>Get up and running in 5 minutes with the CLI or GitHub Action.</p>
      </a>
      <a href="/docs/cli/" class="card">
        <h3>CLI Reference</h3>
        <p>All commands: init, lint, diff, explain, doctor, setup, activate.</p>
      </a>
      <a href="/docs/action/" class="card">
        <h3>GitHub Action</h3>
        <p>Add API governance to your CI pipeline in one step.</p>
      </a>
      <a href="/docs/changes/" class="card">
        <h3>27 Change Types</h3>
        <p>Reference for every breaking and non-breaking change Delimit detects.</p>
      </a>
      <a href="/docs/policies/" class="card">
        <h3>Policies</h3>
        <p>Presets (strict, default, relaxed) and custom YAML policy configuration.</p>
      </a>
      <a href="/docs/mcp/" class="card">
        <h3>MCP Server</h3>
        <p>Use Delimit with Claude Code, Codex, and Gemini CLI via MCP.</p>
      </a>
    </div>

    <h2>Install</h2>
    <pre><code>npx delimit-cli setup</code></pre>
    <p>Or install globally:</p>
    <pre><code>npm install -g delimit-cli</code></pre>

    <h2>What Delimit Does</h2>
    <p>Delimit compares two versions of an OpenAPI specification and detects <strong>27 types of changes</strong> &mdash; 17 breaking and 10 non-breaking. It classifies changes by severity, recommends semver bumps, generates migration guides, and enforces custom policies.</p>

    <h2>How It Works</h2>
    <ol>
      <li><strong>Diff</strong> &mdash; Compare old and new OpenAPI specs to find all changes.</li>
      <li><strong>Classify</strong> &mdash; Each change is categorized as breaking or non-breaking with a severity level.</li>
      <li><strong>Enforce</strong> &mdash; Apply policy presets or custom YAML rules to pass/fail the change.</li>
      <li><strong>Report</strong> &mdash; Generate PR comments, CI annotations, and migration guides.</li>
    </ol>

    <h2>Integrations</h2>
    <ul>
      <li><a href="/docs/integrations/claude-code.html">Claude Code</a> &mdash; MCP integration for API governance in Claude.</li>
      <li><a href="/docs/integrations/codex.html">OpenAI Codex</a> &mdash; MCP integration for Codex CLI.</li>
      <li><a href="/docs/integrations/gemini-cli.html">Gemini CLI</a> &mdash; MCP integration for Google Gemini.</li>
    </ul>
    '''
    return page(
        "Delimit Documentation",
        "API governance for AI coding assistants. Detect 27 types of breaking changes in OpenAPI specs. CLI, GitHub Action, and MCP server.",
        body, "/",
        active_nav="Home",
        json_ld={
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "Delimit Documentation",
            "url": BASE_URL,
            "description": "API governance for AI coding assistants",
            "publisher": {
                "@type": "Organization",
                "name": "Delimit AI",
                "url": "https://delimit.ai"
            }
        }
    )


def generate_quickstart():
    body = '''
    <h1>Quick Start</h1>
    <p class="lead">Get API governance running in under 5 minutes.</p>

    <h2>Option 1: CLI (Local Development)</h2>
    <pre><code># Install
npx delimit-cli setup

# Initialize in your project
delimit init

# Compare two specs
delimit lint --old api/v1.yaml --new api/v2.yaml

# Or diff without policy enforcement
delimit diff --old api/v1.yaml --new api/v2.yaml</code></pre>

    <h2>Option 2: GitHub Action (CI/CD)</h2>
    <p>Add this to <code>.github/workflows/api-governance.yml</code>:</p>
    <pre><code>name: API Governance
on:
  pull_request:
    paths: ["openapi.yaml", "api/**"]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: delimit-ai/delimit-action@v1
        with:
          spec: openapi.yaml
          mode: advisory</code></pre>

    <p>That's it. Delimit will automatically compare your OpenAPI spec against the base branch and comment on the PR with any breaking changes.</p>

    <h2>Option 3: MCP Server (AI Assistants)</h2>
    <pre><code># Add to your MCP config
npx delimit-cli mcp</code></pre>
    <p>See the <a href="/docs/mcp/">MCP setup guide</a> for Claude Code, Codex, and Gemini CLI configuration.</p>

    <h2>What Happens Next</h2>
    <ol>
      <li>Delimit diffs your old and new OpenAPI specs.</li>
      <li>It detects up to <a href="/docs/changes/">27 types of changes</a> (17 breaking, 10 non-breaking).</li>
      <li>It applies your <a href="/docs/policies/">policy</a> (strict, default, or relaxed).</li>
      <li>In CI, it posts a PR comment with a detailed report.</li>
      <li>In enforce mode, it blocks the merge if breaking changes are found.</li>
    </ol>

    <h2>Next Steps</h2>
    <ul>
      <li><a href="/docs/cli/">CLI Reference</a> &mdash; All available commands and options</li>
      <li><a href="/docs/action/">GitHub Action</a> &mdash; Advanced CI configuration</li>
      <li><a href="/docs/policies/">Policies</a> &mdash; Customize what's allowed and what's blocked</li>
      <li><a href="/docs/changes/">Change Types</a> &mdash; Reference for all 27 detectable changes</li>
    </ul>
    '''
    return page(
        "Quick Start",
        "Get Delimit API governance running in under 5 minutes. CLI, GitHub Action, or MCP server setup.",
        body, "/quickstart/",
        active_nav="Quick Start"
    )


def generate_cli():
    body = '''
    <h1>CLI Reference</h1>
    <p class="lead">All Delimit CLI commands and options.</p>

    <h2>Installation</h2>
    <pre><code># Run without installing
npx delimit-cli [command]

# Install globally
npm install -g delimit-cli

# Verify installation
delimit --version</code></pre>

    <h2>Commands</h2>

    <h3><code>delimit init [--preset]</code></h3>
    <p>Initialize Delimit in your project. Creates a <code>.delimit/</code> directory with default configuration.</p>
    <pre><code># Use default preset
delimit init

# Use strict preset (all violations are errors)
delimit init --preset strict

# Use relaxed preset (all violations are warnings)
delimit init --preset relaxed</code></pre>

    <h3><code>delimit lint</code></h3>
    <p>Lint two OpenAPI specs for breaking changes and policy violations. This is the primary CI command.</p>
    <pre><code>delimit lint --old api/v1.yaml --new api/v2.yaml
delimit lint --old api/v1.yaml --new api/v2.yaml --policy .delimit/policies.yml</code></pre>

    <h3><code>delimit diff</code></h3>
    <p>Pure diff between two specs. Lists all changes without applying policy rules.</p>
    <pre><code>delimit diff --old api/v1.yaml --new api/v2.yaml</code></pre>

    <h3><code>delimit explain</code></h3>
    <p>Explain a specific change type or policy rule in detail.</p>
    <pre><code>delimit explain endpoint_removed
delimit explain no_type_changes</code></pre>

    <h3><code>delimit doctor</code></h3>
    <p>Diagnose your Delimit setup. Checks configuration, spec files, and policy validity.</p>
    <pre><code>delimit doctor</code></pre>

    <h3><code>delimit setup</code></h3>
    <p>Interactive setup wizard. Configures Delimit for your project, installs hooks, and validates your spec.</p>
    <pre><code>delimit setup</code></pre>

    <h3><code>delimit activate</code></h3>
    <p>Activate the governance layer. Installs pre-commit hooks and PATH shims for continuous governance.</p>
    <pre><code>delimit activate</code></pre>

    <h2>Global Options</h2>
    <table>
      <thead>
        <tr><th>Option</th><th>Description</th></tr>
      </thead>
      <tbody>
        <tr><td><code>--version</code></td><td>Show version number</td></tr>
        <tr><td><code>--help</code></td><td>Show help for any command</td></tr>
        <tr><td><code>--policy &lt;path&gt;</code></td><td>Path to custom policy YAML file</td></tr>
      </tbody>
    </table>

    <h2>Exit Codes</h2>
    <table>
      <thead>
        <tr><th>Code</th><th>Meaning</th></tr>
      </thead>
      <tbody>
        <tr><td><code>0</code></td><td>No violations (or advisory mode)</td></tr>
        <tr><td><code>1</code></td><td>Breaking changes detected (enforce mode)</td></tr>
        <tr><td><code>2</code></td><td>Configuration or file error</td></tr>
      </tbody>
    </table>
    '''
    return page(
        "CLI Reference",
        "Complete reference for Delimit CLI commands: init, lint, diff, explain, doctor, setup, activate. API governance from the command line.",
        body, "/cli/",
        active_nav="CLI Reference"
    )


def generate_action():
    body = '''
    <h1>GitHub Action</h1>
    <p class="lead">Add API governance to your CI pipeline with the Delimit GitHub Action.</p>

    <h2>Installation</h2>
    <p>Available on the <a href="https://github.com/marketplace/actions/delimit-api-governance" target="_blank">GitHub Marketplace</a>.</p>

    <h2>Basic Setup</h2>
    <p>Create <code>.github/workflows/api-governance.yml</code>:</p>
    <pre><code>name: API Governance
on:
  pull_request:
    paths: ["openapi.yaml"]

jobs:
  delimit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: delimit-ai/delimit-action@v1
        with:
          spec: openapi.yaml</code></pre>

    <h2>Inputs</h2>
    <table>
      <thead>
        <tr><th>Input</th><th>Description</th><th>Default</th></tr>
      </thead>
      <tbody>
        <tr><td><code>spec</code></td><td>Path to OpenAPI spec. Delimit auto-fetches the base branch version.</td><td><em>auto-detect</em></td></tr>
        <tr><td><code>old_spec</code></td><td>Path to old/base spec (advanced mode).</td><td></td></tr>
        <tr><td><code>new_spec</code></td><td>Path to new/changed spec (advanced mode).</td><td></td></tr>
        <tr><td><code>mode</code></td><td><code>advisory</code> (comments only) or <code>enforce</code> (fail CI).</td><td><code>advisory</code></td></tr>
        <tr><td><code>github_token</code></td><td>Token for PR comments.</td><td><code>${{ github.token }}</code></td></tr>
        <tr><td><code>policy_file</code></td><td>Path to custom policy file.</td><td></td></tr>
      </tbody>
    </table>

    <h2>Outputs</h2>
    <table>
      <thead>
        <tr><th>Output</th><th>Description</th></tr>
      </thead>
      <tbody>
        <tr><td><code>breaking_changes_detected</code></td><td><code>true</code> or <code>false</code></td></tr>
        <tr><td><code>violations_count</code></td><td>Number of policy violations</td></tr>
        <tr><td><code>semver_bump</code></td><td><code>major</code>, <code>minor</code>, <code>patch</code>, or <code>none</code></td></tr>
        <tr><td><code>next_version</code></td><td>Computed next version string</td></tr>
        <tr><td><code>report</code></td><td>Full JSON report of all changes</td></tr>
      </tbody>
    </table>

    <h2>Advisory vs Enforce Mode</h2>
    <p><strong>Advisory mode</strong> (default): Delimit posts a PR comment with the diff report but does not block the merge. Good for initial adoption.</p>
    <p><strong>Enforce mode</strong>: Delimit blocks the merge if breaking changes are detected. Use this once your team is comfortable with the governance workflow.</p>
    <pre><code>- uses: delimit-ai/delimit-action@v1
  with:
    spec: openapi.yaml
    mode: enforce</code></pre>

    <h2>Advanced: Two-Spec Mode</h2>
    <p>For monorepos or custom setups where you manage both spec files:</p>
    <pre><code>- uses: delimit-ai/delimit-action@v1
  with:
    old_spec: specs/api-v1.yaml
    new_spec: specs/api-v2.yaml
    mode: enforce
    policy_file: .delimit/policies.yml</code></pre>

    <h2>Auto-Detection</h2>
    <p>If no spec input is provided, Delimit searches for common spec file names: <code>openapi.yaml</code>, <code>openapi.yml</code>, <code>openapi.json</code>, <code>swagger.yaml</code>, etc. in the root and common subdirectories (<code>api/</code>, <code>docs/</code>, <code>spec/</code>).</p>

    <h2>PR Comment</h2>
    <p>Delimit automatically posts (and updates) a PR comment showing:</p>
    <ul>
      <li>Breaking changes with severity levels</li>
      <li>Semver recommendation</li>
      <li>Migration guide for each breaking change</li>
      <li>Additive (non-breaking) changes</li>
    </ul>
    '''
    return page(
        "GitHub Action Setup",
        "Add Delimit API governance to your GitHub CI pipeline. Catch breaking OpenAPI changes on every pull request with advisory or enforce mode.",
        body, "/action/",
        active_nav="GitHub Action"
    )


def generate_mcp():
    body = '''
    <h1>MCP Server</h1>
    <p class="lead">Use Delimit with AI coding assistants via the Model Context Protocol (MCP).</p>

    <p>Delimit provides an MCP server that exposes API governance tools to any MCP-compatible AI assistant, including Claude Code, OpenAI Codex CLI, and Google Gemini CLI.</p>

    <h2>Quick Setup</h2>
    <pre><code>npx delimit-cli mcp</code></pre>

    <h2>Available MCP Tools</h2>
    <p>The Delimit MCP server exposes the following core tools:</p>
    <table>
      <thead>
        <tr><th>Tool</th><th>Description</th></tr>
      </thead>
      <tbody>
        <tr><td><code>delimit_lint</code></td><td>Lint two OpenAPI specs for breaking changes and policy violations.</td></tr>
        <tr><td><code>delimit_diff</code></td><td>Pure diff between two specs. Lists all changes.</td></tr>
        <tr><td><code>delimit_test_generate</code></td><td>Generate test skeletons from source code.</td></tr>
        <tr><td><code>delimit_test_coverage</code></td><td>Analyze test coverage.</td></tr>
      </tbody>
    </table>

    <h2>Integration Guides</h2>
    <ul>
      <li><a href="/docs/integrations/claude-code.html">Claude Code</a> &mdash; Full MCP setup for Claude Code</li>
      <li><a href="/docs/integrations/codex.html">OpenAI Codex CLI</a> &mdash; MCP setup for Codex</li>
      <li><a href="/docs/integrations/gemini-cli.html">Google Gemini CLI</a> &mdash; MCP setup for Gemini</li>
    </ul>

    <h2>Manual Configuration</h2>
    <p>Add to your <code>.mcp.json</code> or equivalent config:</p>
    <pre><code>{
  "mcpServers": {
    "delimit": {
      "command": "npx",
      "args": ["-y", "delimit-cli@latest", "mcp"]
    }
  }
}</code></pre>

    <h2>Usage Examples</h2>
    <p>Once connected, ask your AI assistant:</p>
    <ul>
      <li>"Lint my OpenAPI spec for breaking changes"</li>
      <li>"Compare my old and new API specs"</li>
      <li>"What breaking changes are in this PR?"</li>
      <li>"Generate tests for my API endpoints"</li>
    </ul>
    '''
    return page(
        "MCP Server Setup",
        "Use Delimit with Claude Code, Codex, and Gemini CLI via the Model Context Protocol. API governance in your AI coding assistant.",
        body, "/mcp/",
        active_nav="MCP Server"
    )


def generate_policies():
    body = '''
    <h1>Policies</h1>
    <p class="lead">Control what API changes are allowed, warned, or blocked with policy presets and custom YAML configuration.</p>

    <h2>Policy Presets</h2>
    <p>Delimit ships with three built-in presets:</p>

    <h3>Strict</h3>
    <p>All breaking changes are errors. Zero tolerance for API-breaking modifications.</p>
    <pre><code>delimit init --preset strict</code></pre>

    <h3>Default</h3>
    <p>Balanced approach. Critical changes (endpoint removal, field removal) are errors. Other breaking changes are warnings.</p>
    <pre><code>delimit init</code></pre>

    <h3>Relaxed</h3>
    <p>All breaking changes are warnings. Nothing blocks CI. Good for early-stage APIs.</p>
    <pre><code>delimit init --preset relaxed</code></pre>

    <h2>Custom Policy YAML</h2>
    <p>Create <code>.delimit/policies.yml</code> for fine-grained control:</p>
    <pre><code># .delimit/policies.yml
rules:
  no_endpoint_removal:
    severity: error
    message: "Endpoints must not be removed without deprecation"

  no_field_removal:
    severity: error
    message: "Response fields must not be removed"

  no_required_param_addition:
    severity: error
    message: "New required parameters break existing consumers"

  warn_type_change:
    severity: warning
    message: "Type changes should be reviewed carefully"

  no_enum_removal:
    severity: warning
    message: "Removing enum values may break consumers"</code></pre>

    <h2>Policy Rules</h2>
    <table>
      <thead>
        <tr><th>Rule</th><th>Maps to Change Type</th><th>Default Severity</th></tr>
      </thead>
      <tbody>
        <tr><td><code>no_endpoint_removal</code></td><td>endpoint_removed</td><td>error</td></tr>
        <tr><td><code>no_method_removal</code></td><td>method_removed</td><td>error</td></tr>
        <tr><td><code>no_required_param_addition</code></td><td>required_param_added</td><td>error</td></tr>
        <tr><td><code>no_field_removal</code></td><td>field_removed</td><td>error</td></tr>
        <tr><td><code>no_response_field_removal</code></td><td>field_removed (response context)</td><td>error</td></tr>
        <tr><td><code>no_type_changes</code></td><td>type_changed</td><td>error</td></tr>
        <tr><td><code>warn_type_change</code></td><td>type_changed</td><td>warning</td></tr>
        <tr><td><code>no_enum_removal</code></td><td>enum_value_removed</td><td>warning</td></tr>
      </tbody>
    </table>

    <h2>Severity Levels</h2>
    <ul>
      <li><strong>error</strong> &mdash; Blocks CI in enforce mode. Shown as red in PR comments.</li>
      <li><strong>warning</strong> &mdash; Shown in PR comments but does not block CI.</li>
      <li><strong>info</strong> &mdash; Logged for awareness only.</li>
    </ul>

    <h2>Using with GitHub Action</h2>
    <pre><code>- uses: delimit-ai/delimit-action@v1
  with:
    spec: openapi.yaml
    mode: enforce
    policy_file: .delimit/policies.yml</code></pre>

    <h2>Using with CLI</h2>
    <pre><code>delimit lint --old v1.yaml --new v2.yaml --policy .delimit/policies.yml</code></pre>
    '''
    return page(
        "Policy Configuration",
        "Configure Delimit policies with presets (strict, default, relaxed) or custom YAML rules. Control which API changes block CI.",
        body, "/policies/",
        active_nav="Policies"
    )


def generate_hooks():
    body = '''
    <h1>Cross-Model Hooks</h1>
    <p class="lead">Delimit hooks provide governance that works across all AI coding assistants.</p>

    <h2>What Are Hooks?</h2>
    <p>Delimit hooks are governance checkpoints that trigger when code changes are made, regardless of which AI assistant or IDE is being used. They ensure consistent API governance across your entire team.</p>

    <h2>Pre-Commit Hook</h2>
    <p>The pre-commit hook runs Delimit checks before every commit:</p>
    <pre><code># Install the hook
delimit activate

# Or manually add to .git/hooks/pre-commit
npx delimit-cli pre-commit-check</code></pre>

    <h2>What the Hook Checks</h2>
    <ul>
      <li>Secret detection (API keys, passwords, tokens in staged files)</li>
      <li>OpenAPI spec validation (if specs are staged)</li>
      <li>Policy compliance (if a policy file exists)</li>
      <li>Evidence recording (audit trail in <code>~/.delimit/evidence/</code>)</li>
    </ul>

    <h2>PATH Shim Integration</h2>
    <p>When activated, Delimit adds a shim layer to your PATH that provides continuous governance:</p>
    <pre><code>delimit activate
# Adds ~/.delimit/shims to PATH via shell profile</code></pre>

    <h2>Cross-Model Compatibility</h2>
    <p>Hooks work the same way regardless of whether changes are made by:</p>
    <ul>
      <li>Claude Code (via MCP or direct edits)</li>
      <li>OpenAI Codex CLI</li>
      <li>Google Gemini CLI</li>
      <li>Manual editing in VS Code, Vim, etc.</li>
    </ul>
    <p>The governance layer operates at the git level, not the editor level, ensuring universal coverage.</p>
    '''
    return page(
        "Cross-Model Hooks",
        "Delimit hooks provide API governance across all AI coding assistants. Pre-commit checks, secret detection, and audit trails.",
        body, "/hooks/",
        active_nav="Hooks"
    )


def generate_changes_index():
    breaking = [ct for ct in CHANGE_TYPES if ct["breaking"]]
    non_breaking = [ct for ct in CHANGE_TYPES if not ct["breaking"]]

    body = '''
    <h1>API Change Types</h1>
    <p class="lead">Delimit detects 27 types of API changes: 17 breaking and 10 non-breaking. Each change type has a dedicated reference page with examples, detection details, and migration guides.</p>

    <h2>Breaking Changes (17)</h2>
    <p>These changes will break existing API consumers and require a <strong>MAJOR</strong> semver bump.</p>
    <table>
      <thead>
        <tr><th>Change Type</th><th>Severity</th><th>Description</th></tr>
      </thead>
      <tbody>
'''
    for ct in breaking:
        body += f'        <tr><td><a href="/docs/changes/{ct["id"]}.html"><code>{ct["value"]}</code></a></td><td>{ct["severity"]}</td><td>{ct["description"][:80]}...</td></tr>\n'

    body += '''
      </tbody>
    </table>

    <h2>Non-Breaking Changes (10)</h2>
    <p>These changes are safe for existing consumers. They may warrant a <strong>MINOR</strong> or <strong>PATCH</strong> semver bump.</p>
    <table>
      <thead>
        <tr><th>Change Type</th><th>Severity</th><th>Description</th></tr>
      </thead>
      <tbody>
'''
    for ct in non_breaking:
        body += f'        <tr><td><a href="/docs/changes/{ct["id"]}.html"><code>{ct["value"]}</code></a></td><td>{ct["severity"]}</td><td>{ct["description"][:80]}...</td></tr>\n'

    body += '''
      </tbody>
    </table>
    '''
    return page(
        "API Change Types Reference",
        "Complete reference for all 27 API change types Delimit detects. 17 breaking changes and 10 non-breaking changes with examples and migration guides.",
        body, "/changes/",
        active_nav="Change Types"
    )


def generate_change_page(ct):
    status = "Breaking" if ct["breaking"] else "Non-Breaking"
    status_class = "breaking" if ct["breaking"] else "non-breaking"

    related_links = ""
    for r in ct["related"]:
        related_links += f'      <li><a href="/docs/changes/{r}.html"><code>{r.replace("-", "_")}</code></a></li>\n'

    body = f'''
    <div class="breadcrumb"><a href="/docs/changes/">Change Types</a> &raquo; {ct["value"]}</div>

    <h1><code>{ct["value"]}</code></h1>
    <div class="badge-row">
      <span class="badge {status_class}">{status}</span>
      <span class="badge severity-{ct["severity"]}">Severity: {ct["severity"]}</span>
    </div>

    <p class="lead">{ct["description"]}</p>

    <h2>Why Is This {"Breaking" if ct["breaking"] else "Non-Breaking"}?</h2>
    <p>{ct["why_breaking"]}</p>

    <h2>Example</h2>
    <div class="diff-container">
      <div class="diff-panel">
        <h4>Before</h4>
        <pre><code>{html.escape(ct["before"])}</code></pre>
      </div>
      <div class="diff-panel">
        <h4>After</h4>
        <pre><code>{html.escape(ct["after"])}</code></pre>
      </div>
    </div>

    <h2>How Delimit Detects It</h2>
    <p>{ct["detection"]}</p>

    <h2>Migration Guide</h2>
    <p>{ct["migration"]}</p>

    <h2>Related Change Types</h2>
    <ul>
{related_links}    </ul>

    <h2>Detect This Change</h2>
    <pre><code>npx delimit-cli lint --old old-spec.yaml --new new-spec.yaml</code></pre>
    <p>Or add the <a href="/docs/action/">GitHub Action</a> to catch this automatically on every pull request.</p>
    '''

    return page(
        f"{ct['value']} - {'Breaking' if ct['breaking'] else 'Non-Breaking'} API Change Detection",
        f"Detect {ct['value']} changes in OpenAPI specs. {ct['description'][:120]}",
        body, f"/changes/{ct['id']}.html",
        active_nav="Change Types",
        json_ld={
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": f"{ct['value']} - API Change Detection",
            "description": ct["description"],
            "url": f"{BASE_URL}/changes/{ct['id']}.html",
            "author": {"@type": "Organization", "name": "Delimit AI"},
            "publisher": {"@type": "Organization", "name": "Delimit AI", "url": "https://delimit.ai"},
            "keywords": ct["keywords"],
            "about": {
                "@type": "Thing",
                "name": ct["value"],
                "description": ct["description"]
            }
        }
    )


def generate_integration(name, title, config_example, extra_content=""):
    body = f'''
    <div class="breadcrumb"><a href="/docs/mcp/">MCP Server</a> &raquo; {title}</div>

    <h1>{title} Integration</h1>
    <p class="lead">Set up Delimit API governance in {title}.</p>

    <h2>Prerequisites</h2>
    <ul>
      <li>{title} installed and configured</li>
      <li>Node.js 18+ installed</li>
    </ul>

    <h2>Configuration</h2>
    <pre><code>{html.escape(config_example)}</code></pre>

    <h2>Usage</h2>
    <p>Once configured, you can ask {title.split()[0]} to:</p>
    <ul>
      <li>"Lint my OpenAPI spec for breaking changes"</li>
      <li>"Compare the old and new API specs in this directory"</li>
      <li>"What breaking changes are in my current changes?"</li>
      <li>"Generate tests for my source files"</li>
    </ul>

    {extra_content}

    <h2>Available Tools</h2>
    <p>The Delimit MCP server provides these tools to {title.split()[0]}:</p>
    <table>
      <thead>
        <tr><th>Tool</th><th>Description</th></tr>
      </thead>
      <tbody>
        <tr><td><code>delimit_lint</code></td><td>Lint two OpenAPI specs for breaking changes and policy violations</td></tr>
        <tr><td><code>delimit_diff</code></td><td>Diff two OpenAPI specs and list all changes</td></tr>
        <tr><td><code>delimit_test_generate</code></td><td>Generate test skeletons for source code</td></tr>
        <tr><td><code>delimit_test_coverage</code></td><td>Analyze test coverage</td></tr>
      </tbody>
    </table>

    <h2>Troubleshooting</h2>
    <ul>
      <li>Ensure <code>npx</code> is available in your PATH</li>
      <li>Check that the MCP server starts without errors: <code>npx delimit-cli mcp</code></li>
      <li>Verify your OpenAPI spec files are valid YAML or JSON</li>
    </ul>
    '''
    return page(
        f"{title} Integration",
        f"Set up Delimit API governance in {title}. MCP integration for breaking change detection in OpenAPI specs.",
        body, f"/integrations/{name}.html",
        active_nav="Integrations"
    )


# ── Generate All Pages ───────────────────────────────────────────────────────

def main():
    base = "/tmp/delimit-docs"

    # Create directories
    for d in ["", "quickstart", "cli", "action", "mcp", "policies", "hooks", "changes", "integrations", ".github/workflows"]:
        os.makedirs(os.path.join(base, d), exist_ok=True)

    # Write main pages
    pages = {
        "index.html": generate_index(),
        "quickstart/index.html": generate_quickstart(),
        "cli/index.html": generate_cli(),
        "action/index.html": generate_action(),
        "mcp/index.html": generate_mcp(),
        "policies/index.html": generate_policies(),
        "hooks/index.html": generate_hooks(),
        "changes/index.html": generate_changes_index(),
    }

    for path, content in pages.items():
        with open(os.path.join(base, path), "w") as f:
            f.write(content)
        print(f"  Generated {path}")

    # Write 27 change type pages
    for ct in CHANGE_TYPES:
        path = f"changes/{ct['id']}.html"
        with open(os.path.join(base, path), "w") as f:
            f.write(generate_change_page(ct))
        print(f"  Generated {path}")

    # Write integration pages
    integrations = {
        "claude-code": (
            "Claude Code",
            '''# Add to ~/.mcp.json or .mcp.json in your project
{
  "mcpServers": {
    "delimit": {
      "command": "npx",
      "args": ["-y", "delimit-cli@latest", "mcp"]
    }
  }
}''',
            "<h2>Claude Code Tips</h2><p>Claude Code automatically discovers MCP servers from <code>.mcp.json</code> in your project root or <code>~/.mcp.json</code> for global access. The Delimit tools will appear alongside Claude's built-in tools.</p>"
        ),
        "codex": (
            "OpenAI Codex CLI",
            '''# Add to your MCP configuration
{
  "mcpServers": {
    "delimit": {
      "command": "npx",
      "args": ["-y", "delimit-cli@latest", "mcp"]
    }
  }
}''',
            "<h2>Codex Tips</h2><p>Codex CLI supports MCP servers for extended tool access. Configure Delimit as an MCP server to give Codex the ability to lint and diff OpenAPI specifications during code reviews.</p>"
        ),
        "gemini-cli": (
            "Google Gemini CLI",
            '''# Add to your MCP configuration
{
  "mcpServers": {
    "delimit": {
      "command": "npx",
      "args": ["-y", "delimit-cli@latest", "mcp"]
    }
  }
}''',
            "<h2>Gemini CLI Tips</h2><p>Gemini CLI supports MCP servers for tool integration. Note: Avoid naming MCP tool parameters <code>type</code> as this is a reserved word in Gemini's tool schema.</p>"
        ),
    }

    for name, (title, config, extra) in integrations.items():
        path = f"integrations/{name}.html"
        with open(os.path.join(base, path), "w") as f:
            f.write(generate_integration(name, title, config, extra))
        print(f"  Generated {path}")

    print(f"\nGenerated {8 + len(CHANGE_TYPES) + len(integrations)} pages total.")


if __name__ == "__main__":
    main()
