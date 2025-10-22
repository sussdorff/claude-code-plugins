#!/usr/bin/env bash
# Apply compaction changes (optional) and cleanup workspace (always)
set -euo pipefail

WORKSPACE=""
APPLY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workspace=*)
            WORKSPACE="${1#*=}"
            shift
            ;;
        --apply)
            APPLY=true
            shift
            ;;
        *)
            echo "Unknown argument: $1" >&2
            echo "Usage: finalize-compaction.sh --workspace=<path> [--apply]" >&2
            exit 1
            ;;
    esac
done

if [[ -z "$WORKSPACE" ]]; then
    echo "Error: --workspace required" >&2
    echo "Usage: finalize-compaction.sh --workspace=<path> [--apply]" >&2
    exit 1
fi

if [[ ! -d "$WORKSPACE" ]]; then
    echo "Error: Workspace directory not found: $WORKSPACE" >&2
    exit 1
fi

# Read metadata from workspace
if [[ ! -f "${WORKSPACE}/metadata/reference_path" ]] || [[ ! -f "${WORKSPACE}/metadata/skill_dir" ]]; then
    echo "Error: Workspace metadata not found in: $WORKSPACE" >&2
    exit 1
fi

REFERENCE_FILE="$(<"${WORKSPACE}/metadata/reference_path")"
SKILL_DIR="$(<"${WORKSPACE}/metadata/skill_dir")"

# Apply changes if requested
if [[ "$APPLY" == "true" ]]; then
    echo "Applying changes..."

    # Verify compacted files exist
    if [[ ! -f "${WORKSPACE}/compacted/reference-COMPACTED.md" ]]; then
        echo "Error: Compacted reference file not found" >&2
        rm -rf "$WORKSPACE"
        exit 1
    fi

    if [[ ! -f "${WORKSPACE}/compacted/SKILL-updated.md" ]]; then
        echo "Error: Updated SKILL.md not found" >&2
        rm -rf "$WORKSPACE"
        exit 1
    fi

    # Atomic operations with rollback
    BACKUP_DIR="/tmp/compaction-backup-$$"
    mkdir -p "$BACKUP_DIR"

    # Backup originals
    cp "$REFERENCE_FILE" "${BACKUP_DIR}/reference.md.backup"
    cp "${SKILL_DIR}/SKILL.md" "${BACKUP_DIR}/SKILL.md.backup"

    # Apply changes
    if ! cp "${WORKSPACE}/compacted/reference-COMPACTED.md" "$REFERENCE_FILE"; then
        # Rollback on error
        cp "${BACKUP_DIR}/reference.md.backup" "$REFERENCE_FILE"
        echo "Error: Failed to apply reference changes, rolled back" >&2
        rm -rf "$BACKUP_DIR" "$WORKSPACE"
        exit 1
    fi

    if ! cp "${WORKSPACE}/compacted/SKILL-updated.md" "${SKILL_DIR}/SKILL.md"; then
        # Rollback on error
        cp "${BACKUP_DIR}/reference.md.backup" "$REFERENCE_FILE"
        cp "${BACKUP_DIR}/SKILL.md.backup" "${SKILL_DIR}/SKILL.md"
        echo "Error: Failed to apply SKILL.md changes, rolled back" >&2
        rm -rf "$BACKUP_DIR" "$WORKSPACE"
        exit 1
    fi

    # Success - remove backups
    rm -rf "$BACKUP_DIR"
    echo "✓ Changes applied successfully"
fi

# Always cleanup workspace
rm -rf "$WORKSPACE"
echo "✓ Workspace cleaned up"
