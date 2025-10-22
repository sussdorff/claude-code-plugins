#!/usr/bin/env bash
# Setup isolated workspace for reference file compaction
set -euo pipefail

REFERENCE_FILE="$1"
SKILL_DIR="$2"

# Validation
if [[ -z "$REFERENCE_FILE" ]] || [[ -z "$SKILL_DIR" ]]; then
    echo "Error: Usage: setup-workspace.sh <reference-file-path> <skill-directory>" >&2
    exit 1
fi

if [[ ! -f "$REFERENCE_FILE" ]]; then
    echo "Error: Reference file not found: $REFERENCE_FILE" >&2
    exit 1
fi

if [[ ! -f "${SKILL_DIR}/SKILL.md" ]]; then
    echo "Error: SKILL.md not found in: $SKILL_DIR" >&2
    exit 1
fi

# Generate workspace path
SKILL_NAME="$(basename "$SKILL_DIR")"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
WORKSPACE="/tmp/compaction-${SKILL_NAME}-${TIMESTAMP}"

# Create structure
mkdir -p "$WORKSPACE"/{original,artifacts,compacted,validation,metadata}

# Copy source files (read-only reference)
cp "$REFERENCE_FILE" "$WORKSPACE/original/reference.md"
cp "${SKILL_DIR}/SKILL.md" "$WORKSPACE/original/SKILL.md"

# Save metadata for finalize script
echo "$REFERENCE_FILE" > "$WORKSPACE/metadata/reference_path"
echo "$SKILL_DIR" > "$WORKSPACE/metadata/skill_dir"

# Output workspace path
echo "$WORKSPACE"
