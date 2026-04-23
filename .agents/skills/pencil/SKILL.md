---
name: pencil
model: sonnet
description: Design UI screens and components in Pencil .pen files via MCP tools. Use when creating designs, editing .pen files, or working with design systems. Triggers on pencil, pen file, design system, design screen, components.pen.
---

# Pencil Design Tool

Design production-quality UIs in Pencil .pen files. Enforces correct MCP usage,
multi-file workflow, design system reuse, and visual verification.

## When to Use

- Creating or editing UI screens in .pen files
- Building reusable design system components
- Managing multi-file design projects
- Taking screenshots for visual comparison
- Generating code from Pencil designs

## Critical: MCP Quirks

### The filePath Trap

`batch_get` and `batch_design` accept a `filePath` parameter, but **it is ignored**.
All operations always target the **active document** in Pencil. Using `filePath` to
target a different file silently operates on the wrong file.

### No Auto-Save — Manual Cmd+S Required

Pencil does NOT auto-save. Changes via MCP live in memory only until the user presses
**Cmd+S** (or Ctrl+S). `open_document` does NOT auto-save the previous file.
After making changes, always remind the user to save manually.
Auto-save is planned but not yet implemented (as of Feb 2026).

### Correct Multi-File Workflow

```
1. open_document("/path/to/file.pen")   # switches active document
2. batch_get / batch_design              # operates on active document
3. → Remind user to Cmd+S before switching
4. open_document("/other/file.pen")      # switches again
```

Always call `open_document` before working on a file. Never rely on `filePath`.

### App Must Be Running

The MCP server is a bridge to the Pencil desktop app. No app = all calls fail.
**Auto-open**: If Pencil is not running, open it automatically — don't wait for the user:

```bash
# Start Pencil (idempotent — does nothing if already running)
open -a "Pencil"
sleep 5  # wait for app to initialize

# Start with a specific file
open -a "Pencil" /path/to/file.pen
sleep 5
```

### .pen = JSON Fallback

When Pencil is closed, edit files directly with `jq`:

```bash
# List screens
jq '[.children[] | select(.name | startswith("Screen/"))] | .[].name' file.pen

# Keep only components
jq '.children |= [.[] | select(.reusable == true)]' file.pen > components-only.pen
```

## File Organization

### Template-Based Multi-File Convention

```
design/
├── components.pen      # Design system: tokens + reusable components (TEMPLATE)
├── abrechnung.pen      # Feature: components + billing screens
├── dashboard.pen       # Feature: components + dashboard screens
└── patienten.pen       # Feature: components + patient screens
```

New feature: `cp design/components.pen design/new-feature.pen` — components available immediately.

## Design Rules

### Rule 1: Reuse Design System Components

**Never recreate a component that already exists.** Before inserting any element:

1. `batch_get` with `patterns: [{ reusable: true }]` to list components
2. Insert matches as `ref`: `I(parent, { type: "ref", ref: "<id>" })`
3. Customize via `descendants` in the Insert — not separate Updates

See `references/design-system-components.md` for details.

### Rule 2: Use Variables, Not Hardcoded Values

**Never hardcode colors, radius, spacing when variables exist.**

1. `get_variables` to read tokens
2. Apply as `$--variable-name` references
3. Only create raw values when no variable matches

See `references/variables-and-tokens.md` for details.

### Rule 3: Prevent Overflow

**Never allow text or children to overflow parents.**

1. Use `fill_container` for text width in auto-layout frames
2. After inserting content: `snapshot_layout` with `problemsOnly: true`
3. Fix any clipping before proceeding

See `references/layout-and-text-overflow.md` for details.

### Rule 4: Verify Visually After Each Section

**Never skip verification.** After each logical section:

1. `get_screenshot` on the section node
2. Check alignment, spacing, overflow, visual glitches
3. `snapshot_layout` with `problemsOnly: true`
4. Fix before moving to next section

See `references/visual-verification.md` for details.

### Rule 5: Reuse Existing Assets

**Never regenerate a logo/image that exists elsewhere.** Copy with `C()` operation.

See `references/asset-reuse.md` for details.

## Design Workflow

### Starting a New Design

```
1. open_document("/path/to/file.pen")         # open correct file!
2. get_editor_state                            # understand state
3. batch_get (patterns: [{reusable: true}])    # discover components
4. get_variables                               # read design tokens
5. get_guidelines (topic: relevant)            # get design rules
6. find_empty_space_on_canvas                  # find space for new screen
7. batch_design (max 25 ops per call)          # build section by section
8. get_screenshot                              # verify each section
9. snapshot_layout (problemsOnly: true)        # check for layout problems
```

### Section-by-Section Building

For each section (header, sidebar, content, footer):

1. **Plan** — identify components to reuse
2. **Build** — insert as `ref` instances, apply variables
3. **Verify** — screenshot + snapshot_layout
4. **Fix** — address issues
5. **Proceed** — next section only after verification

## MCP Tool Reference

| Tool | Purpose |
|------|---------|
| `open_document` | Switch active file (MUST call before working on a file) |
| `get_editor_state` | File state, selection, top-level nodes |
| `batch_get` | Read nodes, search components, inspect structure |
| `batch_design` | Insert/copy/update/replace/move/delete (max 25 ops) |
| `get_variables` / `set_variables` | Read/write design tokens |
| `get_screenshot` | Visual verification of any node |
| `snapshot_layout` | Detect clipping, overflow, overlap |
| `get_guidelines` | Design rules (`code`, `table`, `tailwind`, `landing-page`) |
| `find_empty_space_on_canvas` | Find space for new screens |
| `get_style_guide_tags` / `get_style_guide` | Style inspiration |

## Do NOT

- Use `filePath` parameter to target files — it is ignored, use `open_document` instead
- Call MCP tools without Pencil app running
- Use `batch_design` with > 25 operations per call
- Create nodes with explicit `id` fields — IDs are auto-generated
- Update descendants of freshly Copied nodes — use `descendants` in the Copy instead
- Read .pen files with the Read tool — use `batch_get` or `jq` on raw JSON
- Recreate components that exist in the design system
- Hardcode colors/radius/spacing when variables are defined
- Skip visual verification after building sections
- Generate new logos when one exists elsewhere in the document

## Resources

- `references/design-system-components.md` — Component reuse workflow
- `references/variables-and-tokens.md` — Design token workflow
- `references/layout-and-text-overflow.md` — Overflow prevention
- `references/visual-verification.md` — Screenshot verification workflow
- `references/asset-reuse.md` — Logo/image reuse patterns
- [Pencil Docs](https://docs.pencil.dev)
- [Pencil Prompt Gallery](https://www.pencil.dev/prompts)
