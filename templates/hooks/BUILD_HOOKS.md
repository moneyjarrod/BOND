# Build Hooks — Pre/Post-Build Discipline

Subordinate to BOND_MASTER. These rules keep builds clean and verifiable.

## Pre-Build

- **Confirm target before writing.** Before creating or modifying files, confirm which entity and directory the work belongs in. Writing to the wrong entity is a boundary violation that's easy to make and tedious to undo.
- **Check platform.** If `state/config.json` declares a platform, respect it. Windows hosts require filesystem MCP tools — bash_tool cannot reach host paths. See `PLATFORM_BASH_GUARD.md` for details.
- **Read before edit.** Before modifying a file, read the current version. Don't assume the file matches what was in context three messages ago — another tool, editor, or session may have changed it.

## During Build

- **Small commits, frequent verification.** After each logical unit of work (one file created, one function changed, one config updated), verify it landed before moving to the next. Don't stack five changes and verify at the end.
- **Edit over overwrite.** When changing specific sections of a file, use targeted edits (find/replace on exact text) rather than rewriting the entire file. Smaller changes are easier to verify and less likely to introduce unintended modifications.

## Post-Build

- **Read-back verification.** After every write, read the file back. Confirm the content is present, correct, and complete. This catches ghost writes, partial writes, and encoding issues.
- **Panel rebuild awareness.** If React components were modified, the panel needs a rebuild (`npm run build` in the panel directory) before changes are visible in production. Dev mode (Vite) hot-reloads automatically.
- **Server restart awareness.** If `server.js` was modified, the sidecar needs a restart before changes take effect. Running in dev mode with `--watch` handles this automatically.

## Commit Discipline

- **Meaningful commit messages.** Summarize what changed and why. "Updated files" tells the next session nothing. "S42: Added prune window to perspective entity config" tells the whole story.
- **One logical change per commit.** Don't bundle unrelated changes. If you fixed a bug and added a feature, that's two commits.
- **Version awareness.** If you're tracking versions in package.json or elsewhere, bump the version when shipping changes. A version that doesn't change across feature additions is a lie.
