# IG Profile Testing (`test-profile`, `$validate`)

Test StructureDefinitions by validating example resources against them.

## Per Profile

1. Read the StructureDefinition JSON from `fsh-generated/resources/StructureDefinition-<id>.json`
2. Identify the base resource type and required/must-support elements
3. Create a **valid** example resource:
   - Fill all required and MS fields
   - Use valid codes from bound ValueSets
   - Use realistic data — query existing Aidbox data for examples:
     ```bash
     curl -s -u basic:secret "http://localhost:8080/fhir/<ResourceType>?_count=1"
     ```
4. Create an **invalid** example (missing required field, wrong code, etc.)
5. Validate both via `$validate`:

```bash
# Valid — expect no errors
curl -s -u basic:secret -X POST "http://localhost:8080/fhir/<ResourceType>/\$validate?profile=<profile-url>" \
  -H "Content-Type: application/fhir+json" \
  -d @valid-example.json

# Invalid — expect validation errors
curl -s -u basic:secret -X POST "http://localhost:8080/fhir/<ResourceType>/\$validate?profile=<profile-url>" \
  -H "Content-Type: application/fhir+json" \
  -d @invalid-example.json
```

## Testing Extensions

Extensions are not tested standalone. Instead, embed them in a parent resource and validate the parent
against a profile that uses the extension. Query existing Aidbox resources to find realistic parent
resource shapes.

## Batch: test all

Iterate over Profile StructureDefinitions (skip pure Extensions — `type != "Extension"`).
Save results to `test/Profile/<id>.http`.

## Test File Format

Save test files as `.http` (httpyac compatible):

```
test/
└── Profile/
    ├── pas-claim-de.http
    └── pas-task-de.http
```

Each `.http` file documents the test requests and expected outcomes for reproducibility.
