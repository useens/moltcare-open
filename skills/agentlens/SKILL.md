---
name: agentlens
description: Navigate and understand codebases using agentlens hierarchical documentation. Use when exploring new projects, finding modules, locating symbols in large files, finding TODOs/warnings, or understanding code structure.
metadata:
  short-description: Codebase navigation with agentlens
  author: agentlens
  version: "1.0"
---

# AgentLens - Codebase Navigation

# Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Understand user goal
- [ ] Step 2: Select approach
- [ ] Step 3: Ask user preferences (format, scope)
- [ ] Step 4: Execute the task
- [ ] Step 5: Summarize results
```


## Before Working on Any Codebase
Always start by reading `.agentlens/INDEX.md` for the project map.

## Navigation Hierarchy

| Level | File | Purpose |
|-------|------|---------|
| L0 | `INDEX.md` | Project overview, all modules listed |
| L1 | `modules/{slug}/MODULE.md` | Module details, file list |
| L1 | `modules/{slug}/outline.md` | Symbols in large files |
| L1 | `modules/{slug}/memory.md` | TODOs, warnings, business rules |
| L1 | `modules/{slug}/imports.md` | File dependencies |
| L2 | `files/{slug}.md` | Deep docs for complex files |

## Navigation Flow

```
INDEX.md → Find module → MODULE.md → outline.md/memory.md → Source file
```

## When To Read What

| You Need | Read This |
|----------|-----------|
| Project overview | `.agentlens/INDEX.md` |
| Find a module | INDEX.md, search module name |
| Understand a module | `modules/{slug}/MODULE.md` |
| Find function/class in large file | `modules/{slug}/outline.md` |
| Find TODOs, warnings, rules | `modules/{slug}/memory.md` |
| Understand file dependencies | `modules/{slug}/imports.md` |

## Best Practices

1. **Don't read source files directly** for large codebases - use outline.md first
2. **Check memory.md before modifying** code to see warnings and TODOs
3. **Use outline.md to locate symbols**, then read only the needed source sections
4. **Regenerate docs** with `agentlens` command if they seem stale

For detailed navigation patterns, see [references/navigation.md](references/navigation.md)
For structure explanation, see [references/structure.md](references/structure.md)


## Output Formats

| Format | Use Case | Command |
|--------|----------|---------|
| **Quick** | Preview in chat | (no flag) |
| **JSON** | Machine processing | `--format json` |
| **Markdown** | Human readable | `--format md` |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `COMMAND_NOT_FOUND` | Tool not installed | Install the required CLI tool |
| `AUTH_ERROR` | Missing/invalid token | Check `.env` file |
| `NOT_FOUND` | Resource doesn't exist | Verify ID/name |

