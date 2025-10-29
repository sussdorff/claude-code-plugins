---
description: Install a complete plugin locally by unpacking all components (skills, commands, agents, hooks) to target project
argument-hint: [plugin-name] [target-project]
allowed-tools: Bash, Read
model: claude-3-5-haiku-20241022
---

Install plugin $1 to ~/code/claude/$2/:

1. Validate plugin exists:
   - Check if $1/.claude-plugin/plugin.json exists (proper plugin)
   - If not found, list available plugins: ls -d */.claude-plugin | sed 's|/.claude-plugin||'
   - Exit with error if plugin doesn't exist

2. Validate target project:
   - Check if ~/code/claude/$2 directory exists
   - If not found, list available projects: ls ~/code/claude/
   - Exit with error if project doesn't exist

3. Read plugin structure:
   - Check which components exist in $1/:
     - skills/ directory
     - commands/ directory
     - agents/ directory
     - hooks/ directory

4. Install plugin components:

   For each component that exists:

   - **Skills**: If $1/skills/ exists:
     - mkdir -p ~/code/claude/$2/skills/
     - cp -r $1/skills/* ~/code/claude/$2/skills/
     - List installed: ls ~/code/claude/$2/skills/

   - **Commands**: If $1/commands/ exists:
     - mkdir -p ~/code/claude/$2/commands/
     - cp -r $1/commands/* ~/code/claude/$2/commands/
     - List installed: ls ~/code/claude/$2/commands/

   - **Agents**: If $1/agents/ exists:
     - mkdir -p ~/code/claude/$2/agents/
     - cp -r $1/agents/* ~/code/claude/$2/agents/
     - List installed: ls ~/code/claude/$2/agents/

   - **Hooks**: If $1/hooks/ exists:
     - mkdir -p ~/code/claude/$2/hooks/
     - cp -r $1/hooks/* ~/code/claude/$2/hooks/
     - List installed: ls ~/code/claude/$2/hooks/

5. Verify installation:
   - Read plugin.json to get plugin name and version
   - Show installed components summary

6. Output success message:
   ✓ Installed $1 (v{version}) to ~/code/claude/$2/

   Components installed:
   - Skills: {list}
   - Commands: {list}
   - Agents: {list}
   - Hooks: {list}

   Note: Restart Claude Code in the project to discover new components.

Error handling:
- If plugin not found, show: "Plugin '$1' not found. Available plugins: [list]"
- If target not found, show: "Project '$2' not found. Available projects: [list]"
- If no .claude-plugin/plugin.json, show: "'$1' is not a valid plugin (missing plugin.json)"
- If copy fails, show: "Failed to copy {component}. Check permissions."
