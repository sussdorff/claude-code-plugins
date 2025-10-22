#!/bin/zsh
# YouTube Music Auto-Updater Script
# Updates YouTube Music desktop app from pear-devs GitHub releases

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_PATH="/Applications/YouTube Music.app"
PLIST_PATH="${APP_PATH}/Contents/Info.plist"
TMP_DMG="/tmp/youtube-music-update.dmg"
MOUNT_POINT="/Volumes/YouTubeMusicUpdate"
GITHUB_REPO="pear-devs/pear-desktop"

echo "YouTube Music Auto-Updater"
echo "=========================="
echo

# Step 1: Detect system architecture
ARCH=$(uname -m)
echo "Detected architecture: ${ARCH}"

if [[ "${ARCH}" == "arm64" ]]; then
    ARCH_FILTER='contains("arm64")'
    ARCH_SUFFIX="-arm64"
elif [[ "${ARCH}" == "x86_64" ]]; then
    ARCH_FILTER='contains("arm64") | not'
    ARCH_SUFFIX=""
else
    echo "${RED}Error: Unsupported architecture: ${ARCH}${NC}"
    exit 1
fi

# Step 2: Fetch latest version from GitHub
echo "Fetching latest version information..."
LATEST_VERSION=$(curl -sL "https://api.github.com/repos/${GITHUB_REPO}/releases/latest" | jq -r '.tag_name')

if [[ -z "${LATEST_VERSION}" || "${LATEST_VERSION}" == "null" ]]; then
    echo "${RED}Error: Failed to fetch latest version${NC}"
    exit 1
fi

# Remove 'v' prefix if present
LATEST_VERSION_NUM="${LATEST_VERSION#v}"
echo "Latest version: ${LATEST_VERSION_NUM}"

# Step 3: Get download URL
DOWNLOAD_URL=$(curl -sL "https://api.github.com/repos/${GITHUB_REPO}/releases/latest" | \
    jq -r ".assets[] | select(.name | ${ARCH_FILTER} and endswith(\".dmg\")) | .browser_download_url" | head -1)

if [[ -z "${DOWNLOAD_URL}" ]]; then
    echo "${RED}Error: Failed to find download URL for ${ARCH}${NC}"
    exit 1
fi

echo "Download URL: ${DOWNLOAD_URL}"

# Step 4: Check current version
if [[ ! -f "${PLIST_PATH}" ]]; then
    echo "${YELLOW}Warning: YouTube Music not found at ${APP_PATH}${NC}"
    CURRENT_VERSION="not installed"
else
    CURRENT_VERSION=$(/usr/libexec/PlistBuddy -c "Print CFBundleShortVersionString" "${PLIST_PATH}" 2>/dev/null || echo "unknown")
    echo "Current version: ${CURRENT_VERSION}"
fi

# Check if update is needed
if [[ "${CURRENT_VERSION}" == "${LATEST_VERSION_NUM}" ]]; then
    echo "${GREEN}YouTube Music is already up to date!${NC}"
    exit 0
fi

echo "${YELLOW}Update available: ${CURRENT_VERSION} → ${LATEST_VERSION_NUM}${NC}"
echo

# Step 5: Check if app is running
APP_RUNNING=false
if pgrep -x "YouTube Music" > /dev/null; then
    APP_RUNNING=true
    echo "YouTube Music is running, stopping application..."

    # Step 6: Stop the app
    osascript -e 'quit app "YouTube Music"' 2>/dev/null || true
    sleep 2
fi

# Step 7: Download DMG
echo "Downloading YouTube Music ${LATEST_VERSION_NUM}..."
if ! curl -L -o "${TMP_DMG}" "${DOWNLOAD_URL}"; then
    echo "${RED}Error: Failed to download DMG${NC}"
    exit 1
fi

# Verify download
if [[ ! -f "${TMP_DMG}" ]] || [[ ! -s "${TMP_DMG}" ]]; then
    echo "${RED}Error: Downloaded DMG is missing or empty${NC}"
    rm -f "${TMP_DMG}"
    exit 1
fi

echo "Download complete!"

# Step 8: Mount DMG
echo "Mounting DMG..."
if ! hdiutil attach "${TMP_DMG}" -nobrowse -mountpoint "${MOUNT_POINT}" > /dev/null 2>&1; then
    echo "${RED}Error: Failed to mount DMG${NC}"
    rm -f "${TMP_DMG}"
    exit 1
fi

# Step 9: Replace application
echo "Installing update..."

# Verify app exists in mounted volume
if [[ ! -d "${MOUNT_POINT}/YouTube Music.app" ]]; then
    echo "${RED}Error: YouTube Music.app not found in DMG${NC}"
    hdiutil detach "${MOUNT_POINT}" > /dev/null 2>&1 || true
    rm -f "${TMP_DMG}"
    exit 1
fi

# Remove old app if it exists
if [[ -d "${APP_PATH}" ]]; then
    rm -rf "${APP_PATH}"
fi

# Copy new app
if ! cp -R "${MOUNT_POINT}/YouTube Music.app" /Applications/; then
    echo "${RED}Error: Failed to copy application${NC}"
    hdiutil detach "${MOUNT_POINT}" > /dev/null 2>&1 || true
    rm -f "${TMP_DMG}"
    exit 1
fi

# Step 10: Unmount and cleanup
echo "Cleaning up..."
hdiutil detach "${MOUNT_POINT}" > /dev/null 2>&1 || true
rm -f "${TMP_DMG}"

# Step 11: Remove quarantine attributes
echo "Removing quarantine attributes..."
/usr/bin/xattr -cr "${APP_PATH}" 2>/dev/null || true

# Step 12: Restart app if it was running
if [[ "${APP_RUNNING}" == true ]]; then
    echo "Restarting YouTube Music..."
    open -a "YouTube Music"
fi

echo
echo "${GREEN}Successfully updated to version ${LATEST_VERSION_NUM}!${NC}"
