# Efficiency Hooks — Claude Operational Optimization

These rules reduce wasted tool calls, dead-end paths, and redundant operations during BOND sessions. Rules adapt to the host environment declared in `state/config.json`.

## Environment Detection

On install, BOND writes `"platform"` to `state/config.json`:
- `"windows"` — bash_tool runs in a Linux container and CANNOT access host filesystem paths. Filesystem MCP tools are the only path to files.
- `"linux"` or `"mac"` — bash_tool CAN access host filesystem paths. Both bash and filesystem MCP tools work. Prefer whichever is more efficient for the task.

If `platform` is not set, Claude should ask the user or check path format: backslashes (`C:\`) = Windows, forward slashes (`/home/`) = Linux/Mac.

## File Operations

### Reading
- **Batch reads over sequential.** If you need 2+ files, use `read_multiple_files` in a single call. One tool call instead of five.
- **Don't re-read what's in context.** If a file was read earlier in this session and hasn't been modified since, use the version in context. Don't burn a tool call unless a {Sync} or modification occurred.
- **Spot-check over full read.** When verifying file state (version strings, section presence), use the `head` parameter to read 5-30 lines instead of the full file. Catches 90% of issues at 10% of the token cost.
- **Check before you search.** If you already know the directory layout from earlier in the session, don't re-scan it. Structures rarely change mid-session.

### Writing
- **Verify after write.** After any write or edit, read the file back to confirm it landed. The API can report success while the file remains unchanged (ghost write). One extra read prevents a cascade of errors built on a failed write.
- **Edit over overwrite.** If changing a few lines in a large file, use targeted edits (oldText/newText pairs) instead of rewriting the entire file. Smaller diffs, fewer mistakes, easier to audit.
- **Close competing editors.** If a write fails silently, file watchers from VS Code or other editors may be interfering. Advise the user to close the file before retrying.

### Platform-Specific
| Task | Windows | Linux / Mac |
|---|---|---|
| Read/write files | Filesystem MCP only | Either bash or filesystem MCP |
| Run scripts | Filesystem MCP to read, advise user to execute | bash_tool directly |
| Install packages | Advise user (npm/pip in their terminal) | bash_tool (npm/pip) |
| Directory listing | `list_directory` MCP tool | Either `ls` or `list_directory` |
| File search | `search_files` MCP tool | Either `grep`/`find` or `search_files` |

## Build Patterns

- **Fail fast.** Before building a multi-step operation, confirm the first step works. If the tool can't reach the file, the next five calls are wasted.
- **Minimal verification.** When checking if something is current, compare key indicators (version strings, function names, section headers) rather than reading entire files.
- **One task, one tool.** If a single tool call can accomplish the task, don't split it across multiple calls. If multiple calls are needed, batch what can be batched.

## Anti-Patterns

| Anti-Pattern | Cost | Instead |
|---|---|---|
| bash_tool for host paths on Windows | Dead-end + error | Filesystem MCP tools |
| Sequential single-file reads | N tool calls | `read_multiple_files` once |
| Re-reading unchanged files | Wasted context tokens | Use in-session memory |
| Full file rewrite for small change | Overwrite risk | Targeted edit |
| Full file read for version check | Token burn | `head` parameter spot check |
| Skipping post-write verification | Ghost write risk | Read-back after every write |
| Running install commands without platform check | Wrong tool for OS | Check config.json platform first |
