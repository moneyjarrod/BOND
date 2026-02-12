# Platform Bash Guard — Windows Host Protection

> **Detachable hook.** This hook exists because full BOND runs on Windows where the bash_tool operates inside a Linux container that cannot access host filesystem paths. Linux and macOS builders should remove this hook — bash_tool works natively on your host.

## Rule

**Claude must NEVER use bash_tool for file operations on Windows.**

The bash_tool runs in an isolated Linux container. It cannot see, read, write, or modify files at Windows paths (e.g., `C:\Projects\...`). Commands like `grep`, `cat`, `ls`, `cp`, `mv`, `rm` will either silently fail or return empty results — never errors, just nothing. This makes bash failures invisible and leads to false confidence that an operation succeeded.

## What To Use Instead

| Task | Wrong (bash) | Right (filesystem MCP) |
|---|---|---|
| Read a file | `cat C:\file.md` | `read_text_file` |
| Read multiple files | `cat file1 file2` | `read_multiple_files` |
| Search file content | `grep "pattern" C:\file.md` | `read_text_file` + scan in context |
| List directory | `ls C:\Projects\...` | `list_directory` |
| Find files | `find / -name "*.md"` | `search_files` |
| Write a file | `echo "..." > C:\file.md` | `write_file` |
| Edit a file | `sed -i ...` | `edit_file` |
| Move/rename | `mv source dest` | `move_file` |
| Check existence | `test -f C:\file.md` | `list_directory` on parent |

## Why This Is Detachable

This hook is platform-specific. The architecture beneath BOND — Node.js server, Python MCP servers, React panel, QAIS, ISS, SLA — is cross-platform. On Linux or macOS, bash_tool accesses the host filesystem directly, making this guard unnecessary. Remove this file and update any entity links that reference it.

## Credit

BOND architecture by J-Dub and Claude.
