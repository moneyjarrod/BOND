# Workflow Hooks — Session Discipline

Subordinate to BOND_MASTER. General behavioral rules for how Claude operates during BOND sessions.

## Tool Selection

- **Right tool for the job.** Filesystem MCP tools for file operations. bash_tool for system tasks (package installs, script execution, process management). Don't use one where the other belongs.
- **Execute, don't display.** When making code changes, use tools directly. Don't paste code into chat unless debugging or the user asks to see it. Chat explains intent — tools do the work.
- **Batch when possible.** If reading multiple files, use `read_multiple_files`. If checking multiple directories, plan the scan before executing. Fewer tool calls = faster sessions.
- **Daemon channel (localhost:3003).** The search daemon has file ops endpoints: `/manifest`, `/read`, `/write`, `/copy`, `/export`. When a browser channel is available (Chrome extension, Claude Code curl, etc.), prefer daemon over individual file reads for bulk operations — one `/export` replaces dozens of file reads, one `/manifest` replaces directory walking. Single files: direct file tools are fine. Structural maps or bulk content: daemon saves tokens. Falls back to filesystem tools when no channel is available.

## Session Awareness

- **Don't re-read what's in context.** If a file was loaded earlier in the session and hasn't been modified, use the version already in context. Save tool calls for files that may have changed.
- **Track what you've modified.** Keep a mental list of files touched this session. At {Sync} or {Handoff} time, you should be able to report what changed without re-scanning everything.
- **Ghost write vigilance.** If a write reports success but the file is unchanged when read back, something interfered. Common causes: open editors with file watchers, permission issues, path errors. Advise the user and retry.

## Communication

- **Answer first, caveat second.** When the user asks a question, answer it. Don't lead with disclaimers, limitations, or "I should mention that..." The answer comes first. Context comes after.
- **Match the user's energy.** If they're in build mode, be concise and technical. If they're thinking out loud, think with them. If they're frustrated, acknowledge it and solve the problem.
- **Don't over-explain what you did.** After executing a task, report what changed in one or two sentences. The user can read the file if they want details. Long explanations of obvious work waste context.

## Entity Discipline

- **Respect the active entity.** When entered into an entity, all work should relate to that entity's scope. If the conversation drifts to unrelated territory, note the drift rather than silently working outside scope.
- **Link before you reference.** If you need files from another entity, link it first. Don't read across entity boundaries without the link being explicit in state.
- **Exit cleanly.** When work in an entity is complete, {Exit} before moving on. Don't leave entities entered across unrelated work.
