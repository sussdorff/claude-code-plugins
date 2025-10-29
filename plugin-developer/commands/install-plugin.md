---
description: Install a plugin locally from plugin-developer to a target project's skills directory
argument-hint: [plugin-name] [target-project]
allowed-tools: Bash
model: claude-3-5-haiku-20241022
---

Install plugin $1 to ~/code/claude/$2/skills/:

1. Validate plugin exists: Check if plugin-developer/skills/$1 directory exists
   - If not found, list available plugins from plugin-developer/skills/
   - Exit with error if plugin doesn't exist

2. Validate target project: Check if ~/code/claude/$2 directory exists
   - If not found, list available projects in ~/code/claude/
   - Exit with error if project doesn't exist

3. Create skills directory if needed: mkdir -p ~/code/claude/$2/skills/

4. Copy plugin:
   - If $1 is a skill in plugin-developer/skills/$1/:
     - Copy: cp -r plugin-developer/skills/$1 ~/code/claude/$2/skills/
   - If $1 is a plugin in the repository root (like bash-best-practices):
     - Copy: cp -r $1/skills/$1 ~/code/claude/$2/skills/

5. Verify installation:
   - ls ~/code/claude/$2/skills/$1
   - Confirm SKILL.md exists

6. Output success message:
   ✓ Installed $1 to ~/code/claude/$2/skills/$1

   Note: Restart Claude Code in the project to discover the skill.

Error handling:
- If plugin not found, show: "Plugin '$1' not found. Available plugins: [list]"
- If target not found, show: "Project '$2' not found. Available projects: [list]"
- If copy fails, show: "Failed to copy plugin. Check permissions."
