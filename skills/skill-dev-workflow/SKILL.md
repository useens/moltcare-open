---
name: skill-dev-workflow
description: Complete skill development workflow from concept to publication. Use when creating new skills, developing skill capabilities, or managing the skill lifecycle.
type: meta
created: 2026-03-01
---

# Skill Development Workflow

Complete workflow for creating, developing, validating, and publishing OpenClaw skills.

## Prerequisites

- [ ] OpenClaw workspace initialized
- [ ] Python >=3.10 available
- [ ] `scripts/skill-workflow.py` exists
- [ ] `scripts/skill-template.py` exists
- [ ] `scripts/skill-enhancer.py` exists

## Quick Start

### Complete Workflow (Recommended)

```bash
# Run all 5 steps automatically
python3 scripts/skill-workflow.py full my-skill --type=api
```

### Step-by-Step Workflow

```bash
# Step 1: Create from template
python3 scripts/skill-workflow.py create my-skill --type=tool

# Step 2: Development mode
python3 scripts/skill-workflow.py dev my-skill

# Step 3: Validate structure
python3 scripts/skill-workflow.py validate my-skill

# Step 4: Test commands
python3 scripts/skill-workflow.py test my-skill

# Step 5: Publish
python3 scripts/skill-workflow.py publish my-skill
```

## Workflow Details

### Step 1: Create

Generates skill from template with:
- YAML frontmatter
- 5-step workflow structure
- Error handling table
- Output format options

**Command:**
```bash
python3 scripts/skill-workflow.py create <name> --type=api|tool|data
```

### Step 2: Develop

Interactive development mode:
- Shows enhancement preview
- Provides development checklist
- Points to file to edit

**Development Checklist:**
- ☐ Fill in skill description in frontmatter
- ☐ Complete Step 1-5 in Workflow section
- ☐ Add concrete command examples
- ☐ Fill Error Handling table with real errors
- ☐ Test commands locally

**Command:**
```bash
python3 scripts/skill-workflow.py dev <name>
```

### Step 3: Validate

Checks skill structure:
- YAML frontmatter present
- Required fields (name, description)
- Required sections (Workflow, Error Handling)
- Examples present

**Command:**
```bash
python3 scripts/skill-workflow.py validate <name>
```

### Step 4: Test

Verifies skill commands:
- Extracts bash commands from examples
- Performs syntax checks
- Warns about untested commands

**Command:**
```bash
python3 scripts/skill-workflow.py test <name>
```

### Step 5: Publish

Finalizes skill:
- Applies enhancements
- Updates AGENTS.md index
- Creates backup

**Command:**
```bash
python3 scripts/skill-workflow.py publish <name>
```

## Skill Types

| Type | Use Case | Example |
|------|----------|---------|
| **api** | External API integration | GitHub API, weather API |
| **tool** | CLI tool wrapper | fd, bat, gh |
| **data** | Data extraction/processing | web scraping, CSV processing |

## Design Patterns Applied

This workflow implements patterns from Apify Agent Skills:

1. **YAML Frontmatter** - Standardized metadata
2. **5-Step Workflow** - Clear user guidance
3. **Output Formats** - Quick/JSON/CSV options
4. **Error Handling Table** - Systematic error management
5. **Dynamic Discovery** - AGENTS.md auto-generation
6. **Progress Tracking** - Checklist-based workflow

## Related Tools

| Tool | Purpose | Command |
|------|---------|---------|
| `skill-template.py` | Create/validate/index | `skill-template.py create <name>` |
| `skill-enhancer.py` | Auto-enhance existing skills | `skill-enhancer.py <path>` |
| `skill-workflow.py` | Complete development workflow | `skill-workflow.py full <name>` |
| `tool_discovery.py` | Dynamic tool discovery | `tool_discovery.py list` |

## Best Practices

1. **Start with `full` workflow** - Run complete workflow first
2. **Iterate with `dev`** - Use development mode for refinements
3. **Validate frequently** - Check structure before publishing
4. **Test manually** - Automated testing is limited, test commands yourself
5. **Keep examples real** - All examples should be tested commands

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Skill not found" | Check skill name spelling and location |
| "Validation failed" | Check missing required sections |
| "No commands to test" | Add bash code blocks with examples |
| "Publish failed" | Ensure validation passes first |

## Examples

### Example 1: Create API Skill

```bash
python3 scripts/skill-workflow.py full weather-api --type=api
# Edit SKILL.md to add:
# - API endpoint details
# - Authentication requirements
# - Example requests
```

### Example 2: Create Tool Wrapper

```bash
python3 scripts/skill-workflow.py full ffmpeg-tool --type=tool
# Edit SKILL.md to add:
# - Tool installation instructions
# - Common use cases
# - Parameter explanations
```

### Example 3: Enhance Existing Skills

```bash
# Enhance all skills at once
python3 scripts/skill-enhancer.py skills --all

# Update index
python3 scripts/skill-template.py index
```
