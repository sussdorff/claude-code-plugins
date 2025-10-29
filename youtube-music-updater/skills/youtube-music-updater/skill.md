---
name: YouTube Music Updater
description: This skill should be used when updating the YouTube Music desktop application from pear-devs GitHub releases. It handles version checking, app restart, and quarantine attribute removal.
allowed-tools: Bash(zsh:*scripts/update_youtube_music.sh*), Bash(uname:*), Bash(pgrep:*), Bash(curl:https://api.github.com/repos/pear-devs/pear-desktop/*), Bash(curl:https://github.com/pear-devs/pear-desktop/releases/download/*), Bash(jq:*), Bash(/usr/libexec/PlistBuddy:*/Applications/YouTube Music.app/*), Bash(osascript:*YouTube Music*), Bash(hdiutil:*/tmp/youtube-music-update.dmg*), Bash(hdiutil:*/Volumes/YouTubeMusicUpdate*), Bash(rm:*/Applications/YouTube Music.app*), Bash(rm:*/tmp/youtube-music-update.dmg*), Bash(cp:*/Volumes/YouTubeMusicUpdate/YouTube Music.app*), Bash(/usr/bin/xattr:*/Applications/YouTube Music.app*), Bash(open:*YouTube Music*)
---

# YouTube Music Updater

This skill automatically updates the YouTube Music desktop application from the pear-devs GitHub releases.

## Instructions

### Using the Update Script (Recommended)

For most updates, execute the bundled update script:

```zsh
zsh scripts/update_youtube_music.sh
```

The script handles the entire update process automatically, including version checking, download, installation, and app restart.

### Manual Update Process

If manual control is needed or the script requires debugging, follow these steps:

1. **Detect system architecture** using `uname -m`:
   - `arm64` → use ARM64 DMG
   - `x86_64` → use Intel DMG

2. **Fetch the latest version info** using GitHub API:
   ```zsh
   curl -sL https://api.github.com/repos/pear-devs/pear-desktop/releases/latest | jq -r '.tag_name'
   ```
   Extract the version tag (e.g., `v3.11.0`)

3. **Get the download URL** for the appropriate architecture:
   ```zsh
   curl -sL https://api.github.com/repos/pear-devs/pear-desktop/releases/latest | jq -r '.assets[] | select(.name | contains("arm64") and endswith(".dmg")) | .browser_download_url'
   ```
   For Intel (x86_64), omit the `contains("arm64")` filter

4. **Check if update is needed**:
   - Check current installed version at `/Applications/YouTube Music.app/Contents/Info.plist` using:
     ```zsh
     /usr/libexec/PlistBuddy -c "Print CFBundleShortVersionString" "/Applications/YouTube Music.app/Contents/Info.plist"
     ```
   - If versions match, inform user and exit

5. **Check if app is running**:
   ```zsh
   pgrep -x "YouTube Music" > /dev/null
   ```
   - Store result to determine if restart is needed

6. **Stop the app if running**:
   ```zsh
   osascript -e 'quit app "YouTube Music"'
   ```
   - Wait 2 seconds for graceful shutdown

7. **Download the DMG**:
   ```zsh
   curl -L -o /tmp/youtube-music-update.dmg \
     "https://github.com/pear-devs/pear-desktop/releases/download/latest/YouTube-Music-${version}-${arch}.dmg"
   ```
   - Use `arm64` suffix for ARM, no suffix for Intel

8. **Mount the DMG**:
   ```zsh
   hdiutil attach /tmp/youtube-music-update.dmg -nobrowse -mountpoint /Volumes/YouTubeMusicUpdate
   ```

9. **Replace the application**:
   ```zsh
   rm -rf "/Applications/YouTube Music.app"
   cp -R "/Volumes/YouTubeMusicUpdate/YouTube Music.app" /Applications/
   ```

10. **Unmount and cleanup**:
    ```zsh
    hdiutil detach /Volumes/YouTubeMusicUpdate
    rm /tmp/youtube-music-update.dmg
    ```

11. **Remove quarantine attributes**:
    ```zsh
    /usr/bin/xattr -cr "/Applications/YouTube Music.app"
    ```

12. **Restart the app if it was running**:
    ```zsh
    open -a "YouTube Music"
    ```

## Error Handling

- Verify download succeeded before proceeding with installation
- Check that DMG mounted successfully
- Confirm app exists in mounted volume before copying
- Handle missing `/Applications/YouTube Music.app` gracefully
- Provide clear error messages at each step

## Example Output

```
Checking for YouTube Music updates...
Current version: 3.10.0
Latest version: 3.11.0
Update available!

YouTube Music is running, stopping application...
Downloading YouTube Music 3.11.0 (arm64)...
Installing update...
Removing quarantine attributes...
Restarting YouTube Music...

Successfully updated to version 3.11.0!
```

## Notes

- Always use the base GitHub URL: `https://github.com/pear-devs/pear-desktop/releases/download/latest/`
- Intel DMG format: `YouTube-Music-{version}.dmg`
- ARM64 DMG format: `YouTube-Music-{version}-arm64.dmg`
- The skill requires network access and sudo permissions may be needed for installation
- Use ZSH for all shell commands as per user preferences
