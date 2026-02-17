# Hooks — Personal Workflow Rules for BOND

Hooks are lightweight rules that attach to BOND's built-in commands and workflows. They don't change how BOND works — they add your preferences on top.

## What Hooks Are

- **Guardrails**, not gates. They remind Claude of your workflow preferences.
- **Personal**, not framework. BOND_MASTER defines protocol. Hooks define how *you* work within it.
- **Subordinate** to BOND_MASTER. A hook can never override constitutional doctrine.

## How to Use Hooks

### Option A: Library Entity (Recommended)

Create a library-class entity from the panel and copy the hook files you want into it:

1. Go to the **Library** tab in the panel
2. Click **+ New Library**
3. Name it something like `MY_HOOKS` or `WORKFLOW_RULES`
4. Copy any template files from this directory into your new entity's folder
5. Edit them to match your workflow

When you {Enter} an entity and {Link} your hooks library, Claude can search your hooks alongside whatever you're working on.

### Option B: Reference Without Entity

You can also just tell Claude about your hooks in conversation:
- "Read my hooks at `templates/hooks/`"
- Claude reads the files and follows the rules for the session

This works but doesn't persist — you'd need to remind Claude each session.

## Available Templates

| File | Purpose |
|---|---|
| `EFFICIENCY_HOOKS.md` | Reduce wasted tool calls, platform-aware file operations |
| `PLATFORM_BASH_GUARD.md` | Windows-specific: prevents bash_tool on host paths (detachable on Linux/Mac) |
| `AUDIT_HOOKS.md` | Post-build verification, entity health checks, config validation |
| `BUILD_HOOKS.md` | Pre/post-build discipline, file verification, commit hygiene |
| `WORKFLOW_HOOKS.md` | Session discipline, tool selection defaults, communication style |

## Customizing

These templates are starting points. The best hooks come from your own pain — when Claude does something you had to correct, write a hook so it doesn't happen again. A good hook is:

- **Specific.** "Verify writes landed" not "be careful."
- **Actionable.** Claude can follow it without interpretation.
- **Short.** If the rule needs a paragraph to explain, it's too complex.

## Extending

Add your own hook files to your entity. Common additions:

- **PROJECT_HOOKS.md** — Rules specific to your project (naming conventions, file structure, testing requirements)
- **STYLE_HOOKS.md** — How you want Claude to communicate (tone, formatting, verbosity)
- **DEPLOY_HOOKS.md** — Pre-deployment checks for your specific stack
