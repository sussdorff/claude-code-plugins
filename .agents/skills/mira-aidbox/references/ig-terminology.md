# IG Terminology Testing (`test-cs`, `test-vs`)

Test CodeSystems and ValueSets after installing an IG into Aidbox.

## Test CodeSystems (`test-cs`)

Test that CodeSystem codes are resolvable.

**Aidbox does NOT implement `$lookup`.** Use the Aidbox-native Concept API instead:

### Per CodeSystem

1. Read the CodeSystem JSON from `fsh-generated/resources/CodeSystem-<id>.json`
2. Extract 2-3 representative codes
3. Query via Aidbox-native Concept API:

```bash
curl -s -u basic:secret "http://localhost:8080/Concept?system=<cs-url>&code=<code>"
```

4. Also test one **invalid code** — expect empty bundle:

```bash
curl -s -u basic:secret "http://localhost:8080/Concept?system=<cs-url>&code=INVALID_CODE_XYZ"
```

### Batch: test all

Iterate over all `fsh-generated/resources/CodeSystem-*.json` files.
Save results to `test/CS/<id>.http` (httpyac format) for reproducibility.

### Expected results

- Valid codes: response contains `display` and `name`
- Invalid codes: OperationOutcome with error, or empty parameter response

## Test ValueSets (`test-vs`)

Test that ValueSets expand correctly and validate codes.

### Per ValueSet

1. Read the ValueSet JSON from `fsh-generated/resources/ValueSet-<id>.json`
2. Run `$expand`:

```bash
# FHIR endpoint does NOT work in Aidbox — use native endpoint:
curl -s -u basic:secret "http://localhost:8080/ValueSet/<id>/\$expand"
```

3. Check expansion: verify the `contains` array has the expected codes
4. Run `$validate-code` for 2-3 valid codes:

```bash
curl -s -u basic:secret "http://localhost:8080/fhir/ValueSet/\$validate-code?url=<vs-url>&system=<cs-url>&code=<code>"
```

5. Run `$validate-code` for 1 invalid code — expect `result=false`:

```bash
curl -s -u basic:secret "http://localhost:8080/fhir/ValueSet/\$validate-code?url=<vs-url>&system=<cs-url>&code=INVALID_XYZ"
```

### Batch: test all

Iterate over all `fsh-generated/resources/ValueSet-*.json` files.
Save results to `test/VS/<id>.http`.

### Expected results

- `$expand`: contains array with all included codes
- Valid `$validate-code`: `"result": true`
- Invalid `$validate-code`: `"result": false`

## Test File Format

Save test files as `.http` (httpyac compatible) in the project's `test/` directory:

```
test/
├── CS/
│   ├── scheinart.http
│   └── billing-type.http
└── VS/
    ├── scheinart-vs.http
    └── billing-type-vs.http
```
