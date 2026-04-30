---
disable-model-invocation: true
name: paperless-cli
model: haiku
description: Interact with Paperless-ngx document management via REST API. Use when searching documents, downloading PDFs, uploading scans, or querying tags. Triggers on paperless, scanned document, document archive. Not for email archiving (use piler-cli).
requires_standards: [english-only]
---

# paperless-cli

REST API client for the Paperless-ngx document archive at https://paperless.sussdorff.org.
Always access the API directly from the local machine — never SSH into the LXC.

## When to Use

- You want to search for a scanned document (invoice, contract, letter) in the archive
- You need to download a PDF from Paperless or upload a new scan for OCR processing
- You want to list or filter documents by tags, correspondents, or date
- You need to check what documents were recently added to the archive

## Authentication

Use the environment variable (set in ~/.zshrc). Fallback to 1Password if not set:

```bash
TOKEN="${PAPERLESS_TOKEN:-$(op item get "Paperless-ngx - paperless.sussdorff.org" --vault "API Keys" --format json | jq -r '.fields[] | select(.label == "API Token") | .value')}"
```

Base URL: `${PAPERLESS_URL:-https://paperless.sussdorff.org}/api/`

## Common Operations

### List Recent Documents

```bash
curl -s -H "Authorization: Token $TOKEN" \
  "https://paperless.sussdorff.org/api/documents/?ordering=-added&page_size=10" \
  | jq '.results[] | {id, title, added, original_file_name}'
```

### Search Documents

```bash
curl -s -H "Authorization: Token $TOKEN" \
  "https://paperless.sussdorff.org/api/documents/?query=searchterm" \
  | jq '.results[] | {id, title, added, original_file_name}'
```

### Get Document Details

```bash
curl -s -H "Authorization: Token $TOKEN" \
  "https://paperless.sussdorff.org/api/documents/{id}/" | jq .
```

### Download a Document

```bash
# Download original scan
curl -s -H "Authorization: Token $TOKEN" \
  "https://paperless.sussdorff.org/api/documents/{id}/download/" -o document.pdf

# Download archived (OCR'd) version
curl -s -H "Authorization: Token $TOKEN" \
  "https://paperless.sussdorff.org/api/documents/{id}/download/?original=false" -o document_ocr.pdf
```

### Upload a Document

```bash
curl -s -H "Authorization: Token $TOKEN" \
  -F "document=@/path/to/scan.pdf" \
  "https://paperless.sussdorff.org/api/documents/post_document/"
```

### List Tags and Correspondents

```bash
# Tags
curl -s -H "Authorization: Token $TOKEN" \
  "https://paperless.sussdorff.org/api/tags/" | jq '.results[] | {id, name}'

# Correspondents
curl -s -H "Authorization: Token $TOKEN" \
  "https://paperless.sussdorff.org/api/correspondents/" | jq '.results[] | {id, name}'
```

## API Endpoints Reference

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List documents | GET | `/api/documents/?ordering=-added&page_size=N` |
| Search | GET | `/api/documents/?query=term` |
| Get details | GET | `/api/documents/{id}/` |
| Download original | GET | `/api/documents/{id}/download/` |
| Download archived | GET | `/api/documents/{id}/download/?original=false` |
| Upload | POST | `/api/documents/post_document/` (multipart, field: `document`) |
| List tags | GET | `/api/tags/` |
| List correspondents | GET | `/api/correspondents/` |

## Infrastructure Context

- Instance: https://paperless.sussdorff.org
- Runs in LXC 108 on elysium (Proxmox), container: `paperless-paperless-1`
- Documents uploaded via API are processed immediately by the consume pipeline

## Do NOT

- Do NOT SSH into elysium or LXC 108 to access files directly — use the REST API only. WHY: direct filesystem access bypasses OCR pipeline and metadata indexing.
- Do NOT try to read the consume directory — documents are ingested immediately and the directory will be empty.
- Do NOT hardcode the API token in scripts — use `$PAPERLESS_TOKEN` env var (set in ~/.zshrc), with 1Password as fallback.
- Do NOT use piler-cli for document archive tasks — piler-cli is for email archives only.

## Output Format

Returns JSON from the Paperless-ngx REST API:
```
# Search results: {count, results: [{id, title, correspondent, tags, created}]}
# Document detail: {id, title, content, download_url, tags, correspondent}
```
