#!/bin/bash
# Examples for reading credentials from the 1Password "API Keys" vault.
# Run individual lines as needed — not intended as a complete script.

# Read a single field
op read "op://API Keys/<ServiceName>/<FieldName>"

# Examples by credential type
op read "op://API Keys/Prowlarr/API Key"
op read "op://API Keys/Komga/username"
op read "op://API Keys/Komga/password"
op read "op://API Keys/Audiobookshelf/API Key"
op read "op://API Keys/Dolt Root/password"
