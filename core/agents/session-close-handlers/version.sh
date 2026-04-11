#!/usr/bin/env bash
# version.sh - Version bump: auto-detects SemVer vs CalVer from VERSION file
# Usage: version.sh [--dry-run] [major|minor|patch]
#
# SemVer: reads conventional commits to determine bump (or accepts explicit override)
# CalVer: YYYY.0M.MICRO (increments MICRO within month, resets on new month)

set -euo pipefail

DRY_RUN=false
BUMP_OVERRIDE=""
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    major|minor|patch) BUMP_OVERRIDE="$arg" ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
VERSION_FILE="$REPO_ROOT/VERSION"
NEXT_VERSION_SCRIPT="$REPO_ROOT/scripts/next-version.sh"

# Detect strategy from VERSION file
STRATEGY="calver"
if [[ -f "$VERSION_FILE" ]]; then
  CURRENT_VER=$(tr -d '[:space:]' < "$VERSION_FILE")
  MAJOR="${CURRENT_VER%%.*}"
  if [[ "$MAJOR" =~ ^[0-9]+$ ]] && (( MAJOR < 2000 )); then
    STRATEGY="semver"
  fi
fi

echo "Versioning strategy: $STRATEGY"
echo "Current VERSION: ${CURRENT_VER:-<not set>}"

# Helper: find latest tag matching current strategy
latest_tag_for_strategy() {
  local strategy="$1"
  git -C "$REPO_ROOT" tag --list "v[0-9]*.[0-9]*.[0-9]*" --sort=-v:refname 2>/dev/null | while read -r t; do
    local m="${t#v}"; m="${m%%.*}"
    if [[ "$strategy" == "semver" && "$m" =~ ^[0-9]+$ ]] && (( m < 2000 )); then
      echo "$t"; return
    elif [[ "$strategy" == "calver" && "$m" =~ ^[0-9]+$ ]] && (( m >= 2000 )); then
      echo "$t"; return
    fi
  done
}

# Show latest tag
LATEST_TAG=$(latest_tag_for_strategy "$STRATEGY")
if [ -n "$LATEST_TAG" ]; then
  echo "Latest tag: $LATEST_TAG"
else
  echo "No previous version tags found."
fi

# Determine next version
if [ -x "$NEXT_VERSION_SCRIPT" ] || [ -f "$NEXT_VERSION_SCRIPT" ]; then
  NEXT_VERSION=$(bash "$NEXT_VERSION_SCRIPT" $BUMP_OVERRIDE)
else
  if [[ "$STRATEGY" == "semver" ]]; then
    # Fallback: inline SemVer calculation
    local_ver="${CURRENT_VER:-0.0.0}"
    IFS='.' read -r sv_major sv_minor sv_patch <<< "$local_ver"
    sv_patch="${sv_patch:-0}"

    # Determine bump from conventional commits
    if [[ -n "$BUMP_OVERRIDE" ]]; then
      BUMP="$BUMP_OVERRIDE"
    else
      LAST_SV_TAG=$(latest_tag_for_strategy "semver")
      RANGE="${LAST_SV_TAG:+${LAST_SV_TAG}..HEAD}"
      RANGE="${RANGE:-HEAD}"
      LOG=$(git -C "$REPO_ROOT" log "$RANGE" --pretty=format:"%s%n%b" 2>/dev/null || true)
      if echo "$LOG" | grep -qiE "^[a-z]+(\(.+\))?!:|BREAKING[ -]CHANGE"; then
        BUMP="major"
      elif echo "$LOG" | grep -qiE "^feat(\(.+\))?:"; then
        BUMP="minor"
      else
        BUMP="patch"
      fi
    fi

    case "$BUMP" in
      major) NEXT_VERSION="$((sv_major + 1)).0.0" ;;
      minor) NEXT_VERSION="${sv_major}.$((sv_minor + 1)).0" ;;
      patch) NEXT_VERSION="${sv_major}.${sv_minor}.$((sv_patch + 1))" ;;
    esac
    echo "(SemVer $BUMP bump -- scripts/next-version.sh not found, using inline)"
  else
    # Fallback: inline CalVer calculation
    YEAR=$(date +%Y)
    MONTH=$(date +%m)
    TAG_PREFIX="v${YEAR}.${MONTH}"
    MONTH_TAG=$(git -C "$REPO_ROOT" tag --list "${TAG_PREFIX}.*" --sort=-v:refname 2>/dev/null | head -1)
    if [ -n "$MONTH_TAG" ]; then
      CURRENT_MICRO=$(echo "$MONTH_TAG" | sed "s/^${TAG_PREFIX}\\.//")
      NEXT_MICRO=$((CURRENT_MICRO + 1))
    else
      NEXT_MICRO=0
    fi
    NEXT_VERSION="${YEAR}.${MONTH}.${NEXT_MICRO}"
    echo "(CalVer -- scripts/next-version.sh not found, using inline)"
  fi
fi

NEXT_TAG="v${NEXT_VERSION}"

echo "Next version: $NEXT_VERSION"
echo "Next tag: $NEXT_TAG"

if $DRY_RUN; then
  echo ""
  echo "[DRY-RUN] Would write $NEXT_VERSION to $VERSION_FILE"
  echo "[DRY-RUN] Would create git tag $NEXT_TAG"
else
  # Write VERSION file
  echo "$NEXT_VERSION" > "$VERSION_FILE"
  echo "VERSION file updated: $NEXT_VERSION"
  git -C "$REPO_ROOT" add "$VERSION_FILE"

  # For SemVer projects: also update sushi-config.yaml if present
  SUSHI_CONFIG="$REPO_ROOT/sushi-config.yaml"
  if [[ "$STRATEGY" == "semver" && -f "$SUSHI_CONFIG" ]]; then
    sed -i '' "s/^version: .*/version: $NEXT_VERSION/" "$SUSHI_CONFIG"
    echo "sushi-config.yaml updated: $NEXT_VERSION"
    git -C "$REPO_ROOT" add "$SUSHI_CONFIG"
  fi

  # Create annotated tag
  git -C "$REPO_ROOT" tag -a "$NEXT_TAG" -m "Release $NEXT_VERSION"
  echo "Tag created: $NEXT_TAG"
fi
