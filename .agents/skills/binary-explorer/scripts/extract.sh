#!/usr/bin/env bash
# Extract readable content from any desktop app for reverse-engineering.
# Usage: bash extract.sh <path-to-app-or-binary>
#
# Handles:
#   - macOS .app bundles (native or Electron)
#   - Electron app.asar archives (extracts the JS bundle)
#   - Mach-O / ELF / PE binaries (strings dump)
#   - Single-executable JS/Go bundles (strings dump — content is JS/source)
#
# Output (to stderr, human-readable):
#   A summary of what was found and where the extracted content lives.
# Output (to stdout):
#   WORKSPACE=<path>
#   key=value lines pointing at useful files (strings, bundle, frameworks, etc.)

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <path-to-app-or-binary>" >&2
    exit 1
fi

TARGET="$1"
if [[ ! -e "$TARGET" ]]; then
    echo "ERROR: Path does not exist: $TARGET" >&2
    exit 1
fi

# Normalize to absolute path
TARGET="$(cd "$(dirname "$TARGET")" 2>/dev/null && pwd)/$(basename "$TARGET")"

# Derive a stable cache key from the path (slug) + a size/mtime fingerprint
slugify() {
    echo "$1" | sed 's|^/||; s|/|_|g; s|[^a-zA-Z0-9._-]|_|g' | cut -c1-100
}

SLUG="$(slugify "$TARGET")"
FINGERPRINT="$(stat -f '%z-%m' "$TARGET" 2>/dev/null || stat -c '%s-%Y' "$TARGET" 2>/dev/null || echo "nofp")"
WORKSPACE="$HOME/.claude/cache/app-reverser/${SLUG}_${FINGERPRINT}"

mkdir -p "$WORKSPACE"

log() { echo "[app-reverser] $*" >&2; }

detect_kind() {
    local p="$1"
    if [[ -d "$p" && "$p" == *.app ]]; then
        echo "macos_app"
    elif [[ -f "$p" ]]; then
        local ft
        ft="$(file -b "$p" 2>/dev/null || echo "")"
        if [[ "$ft" == *"Mach-O"* ]]; then
            echo "macho"
        elif [[ "$ft" == *"ELF"* ]]; then
            echo "elf"
        elif [[ "$ft" == *"PE32"* || "$p" == *.exe || "$p" == *.dll ]]; then
            echo "pe"
        elif [[ "$p" == *.asar ]]; then
            echo "asar"
        else
            echo "unknown_file"
        fi
    else
        echo "unknown"
    fi
}

KIND="$(detect_kind "$TARGET")"
log "target: $TARGET"
log "kind:   $KIND"
log "workspace: $WORKSPACE"

# Start emitting stdout results
echo "WORKSPACE=$WORKSPACE"
echo "TARGET=$TARGET"
echo "KIND=$KIND"

# --- Helper: strings dump with caching ---
dump_strings() {
    local binary="$1"
    local out="$2"
    if [[ -s "$out" ]]; then
        log "strings already cached: $out ($(wc -l < "$out" | tr -d ' ') lines)"
        return
    fi
    log "dumping strings from: $binary"
    # -a: scan whole file. Default min length 4 is fine.
    strings -a "$binary" > "$out" 2>/dev/null || strings "$binary" > "$out"
    log "strings dump: $out ($(wc -l < "$out" | tr -d ' ') lines)"
}

# --- Helper: extract an asar archive ---
extract_asar() {
    local asar_path="$1"
    local out_dir="$2"
    if [[ -d "$out_dir" && -n "$(ls -A "$out_dir" 2>/dev/null)" ]]; then
        log "asar already extracted: $out_dir"
        return
    fi
    mkdir -p "$out_dir"
    log "extracting asar: $asar_path -> $out_dir"
    # Use npx to avoid forcing a global install. Suppresses the npm warnings.
    if ! npx --yes @electron/asar extract "$asar_path" "$out_dir" 2>&1 | tail -3 >&2; then
        log "WARN: @electron/asar extract may have failed; check $out_dir"
    fi
}

# --- Per-kind handling ---
case "$KIND" in
    macos_app)
        MACOS_DIR="$TARGET/Contents/MacOS"
        RESOURCES_DIR="$TARGET/Contents/Resources"
        FRAMEWORKS_DIR="$TARGET/Contents/Frameworks"

        # Main binary
        if [[ -d "$MACOS_DIR" ]]; then
            MAIN_BIN="$(find "$MACOS_DIR" -maxdepth 1 -type f | head -1)"
            if [[ -n "$MAIN_BIN" ]]; then
                STRINGS_OUT="$WORKSPACE/main_strings.txt"
                dump_strings "$MAIN_BIN" "$STRINGS_OUT"
                echo "MAIN_BINARY=$MAIN_BIN"
                echo "MAIN_STRINGS=$STRINGS_OUT"
            fi
        fi

        # Info.plist — copy for easy reading
        if [[ -f "$TARGET/Contents/Info.plist" ]]; then
            cp "$TARGET/Contents/Info.plist" "$WORKSPACE/Info.plist" 2>/dev/null || true
            echo "INFO_PLIST=$WORKSPACE/Info.plist"
        fi

        # Electron detection: app.asar
        if [[ -f "$RESOURCES_DIR/app.asar" ]]; then
            ASAR_OUT="$WORKSPACE/asar_extracted"
            extract_asar "$RESOURCES_DIR/app.asar" "$ASAR_OUT"
            echo "ASAR_EXTRACTED=$ASAR_OUT"
            # Index the main webpack bundles if present
            for candidate in \
                "$ASAR_OUT/.webpack/main/index.js" \
                "$ASAR_OUT/dist/main.js" \
                "$ASAR_OUT/out/main/index.js" \
                "$ASAR_OUT/build/main.js"; do
                if [[ -f "$candidate" ]]; then
                    echo "MAIN_BUNDLE=$candidate"
                    break
                fi
            done
            # package.json in extracted asar
            if [[ -f "$ASAR_OUT/package.json" ]]; then
                echo "PACKAGE_JSON=$ASAR_OUT/package.json"
            fi
        fi

        # app.asar.unpacked usually contains native modules
        if [[ -d "$RESOURCES_DIR/app.asar.unpacked" ]]; then
            echo "ASAR_UNPACKED=$RESOURCES_DIR/app.asar.unpacked"
        fi

        # Frameworks — list them, don't dump strings for all
        if [[ -d "$FRAMEWORKS_DIR" ]]; then
            echo "FRAMEWORKS_DIR=$FRAMEWORKS_DIR"
            FRAMEWORKS_LIST="$WORKSPACE/frameworks.txt"
            ls -1 "$FRAMEWORKS_DIR" > "$FRAMEWORKS_LIST" 2>/dev/null || true
            echo "FRAMEWORKS_LIST=$FRAMEWORKS_LIST"
        fi

        # Helper .app bundles (common for macOS apps with privileged features)
        HELPERS=()
        while IFS= read -r helper; do
            HELPERS+=("$helper")
        done < <(find "$TARGET/Contents" -maxdepth 4 -type d -name "*.app" 2>/dev/null)
        if [[ ${#HELPERS[@]} -gt 0 ]]; then
            HELPERS_LIST="$WORKSPACE/helper_apps.txt"
            printf '%s\n' "${HELPERS[@]}" > "$HELPERS_LIST"
            echo "HELPER_APPS=$HELPERS_LIST"
        fi
        ;;

    macho|elf|pe|unknown_file)
        STRINGS_OUT="$WORKSPACE/strings.txt"
        dump_strings "$TARGET" "$STRINGS_OUT"
        echo "MAIN_BINARY=$TARGET"
        echo "MAIN_STRINGS=$STRINGS_OUT"

        # For Mach-O, list linked libraries (otool) — handy for spotting frameworks
        if [[ "$KIND" == "macho" ]] && command -v otool >/dev/null 2>&1; then
            LIBS_OUT="$WORKSPACE/linked_libs.txt"
            otool -L "$TARGET" > "$LIBS_OUT" 2>/dev/null || true
            echo "LINKED_LIBS=$LIBS_OUT"
        fi
        # For ELF, use ldd if available
        if [[ "$KIND" == "elf" ]] && command -v ldd >/dev/null 2>&1; then
            LIBS_OUT="$WORKSPACE/linked_libs.txt"
            ldd "$TARGET" > "$LIBS_OUT" 2>/dev/null || true
            echo "LINKED_LIBS=$LIBS_OUT"
        fi
        ;;

    asar)
        ASAR_OUT="$WORKSPACE/asar_extracted"
        extract_asar "$TARGET" "$ASAR_OUT"
        echo "ASAR_EXTRACTED=$ASAR_OUT"
        if [[ -f "$ASAR_OUT/package.json" ]]; then
            echo "PACKAGE_JSON=$ASAR_OUT/package.json"
        fi
        ;;

    *)
        log "WARN: unknown artifact type; attempting strings dump as fallback"
        STRINGS_OUT="$WORKSPACE/strings.txt"
        dump_strings "$TARGET" "$STRINGS_OUT" || true
        echo "MAIN_STRINGS=$STRINGS_OUT"
        ;;
esac

log "done. Use the paths above to search."
