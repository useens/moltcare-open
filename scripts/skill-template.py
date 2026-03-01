#!/usr/bin/env python3
"""
OpenClaw Skill Template Generator
提取自 Apify Agent Skills 设计模式

使用方法:
    python3 scripts/skill-template.py create <skill-name> [--type=data|api|tool]
    python3 scripts/skill-template.py validate <skill-path>
    python3 scripts/skill-template.py index [--output=agents/AGENTS.md]
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


SKILL_TEMPLATE = '''---
name: {name}
description: {description}
type: {type}
created: {date}
author: {author}
---

# {title}

{description}

## Prerequisites

<!-- 删除不适用的项 -->
- [ ] API Token/Key configured in `.env`
- [ ] CLI tool installed: `tool-name --version`
- [ ] Python package: `package>=1.0.0`
- [ ] Node.js package: `npm install -g package`

## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: {step1}
- [ ] Step 2: {step2}
- [ ] Step 3: Ask user preferences (format, scope)
- [ ] Step 4: Execute the task
- [ ] Step 5: Summarize results
```

### Step 1: {step1}

Understand what the user wants to achieve.

### Step 2: {step2}

Select the appropriate approach based on user needs:

| User Need | Approach | Best For |
|-----------|----------|----------|
| Use case 1 | Method A | Scenario X |
| Use case 2 | Method B | Scenario Y |

### Step 3: Ask User Preferences

Before executing, clarify:
1. **Output format**:
   - **Quick answer** - Display summary in chat (no file saved)
   - **Markdown** - Structured report
   - **JSON** - Machine-readable export
   - **CSV** - Tabular data
2. **Scope**: Number of items, time range, depth of analysis

### Step 4: Execute

**Quick answer (no file):**
```bash
# Command here
```

**Save to file:**
```bash
# Command with output redirection
```

### Step 5: Summarize Results

After completion, report:
- Number of items processed
- File location (if saved)
- Key findings
- Suggested follow-up actions

## Error Handling

| Error | Solution |
|-------|----------|
| `Error message 1` | How to fix |
| `Error message 2` | How to fix |

## Examples

### Example 1: Basic Usage

```bash
# Example command
```

### Example 2: Advanced Usage

```bash
# Example with more options
```
'''


def create_skill(name: str, skill_type: str = "tool", author: str = "OpenClaw") -> str:
    """Create a new skill from template."""
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    title = name.replace("-", " ").replace("_", " ").title()
    
    type_descriptions = {
        "data": f"Extract and process data from various sources using {title}.",
        "api": f"Interact with {title} API for data retrieval and operations.",
        "tool": f"Use {title} tools for automation and processing tasks.",
    }
    
    type_steps = {
        "data": ("Understand data requirements", "Select data source/method"),
        "api": ("Understand API goal", "Select endpoint/operation"),
        "tool": ("Understand task goal", "Select tool/approach"),
    }
    
    content = SKILL_TEMPLATE.format(
        name=name,
        description=type_descriptions.get(skill_type, type_descriptions["tool"]),
        type=skill_type,
        date=date_str,
        author=author,
        title=title,
        step1=type_steps.get(skill_type, type_steps["tool"])[0],
        step2=type_steps.get(skill_type, type_steps["tool"])[1],
    )
    
    return content


def validate_skill(skill_path: str) -> dict:
    """Validate a skill's SKILL.md structure."""
    
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "checks": {}
    }
    
    skill_file = Path(skill_path) / "SKILL.md"
    
    if not skill_file.exists():
        result["valid"] = False
        result["errors"].append(f"SKILL.md not found at {skill_file}")
        return result
    
    content = skill_file.read_text()
    
    # Check YAML frontmatter
    frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not frontmatter_match:
        result["errors"].append("Missing YAML frontmatter")
        result["checks"]["frontmatter"] = False
    else:
        result["checks"]["frontmatter"] = True
        frontmatter = frontmatter_match.group(1)
        
        # Required fields
        if "name:" not in frontmatter:
            result["errors"].append("Missing 'name' in frontmatter")
        if "description:" not in frontmatter:
            result["errors"].append("Missing 'description' in frontmatter")
    
    # Check sections
    required_sections = ["## Prerequisites", "## Workflow", "## Error Handling"]
    for section in required_sections:
        if section not in content:
            result["warnings"].append(f"Missing recommended section: {section}")
            result["checks"][section] = False
        else:
            result["checks"][section] = True
    
    # Check for checklist pattern
    if "- [ ]" not in content and "- [x]" not in content:
        result["warnings"].append("No progress checklist found (recommended)")
    
    # Check for examples
    if "## Examples" not in content and "### Example" not in content:
        result["warnings"].append("No examples section found (recommended)")
    
    if result["errors"]:
        result["valid"] = False
    
    return result


def generate_agents_md(skills_dir: str = "skills", output: str = "agents/AGENTS.md") -> str:
    """Generate AGENTS.md index from all skills."""
    
    skills_path = Path(skills_dir)
    output_path = Path(output)
    
    skills = []
    
    for skill_dir in skills_path.iterdir():
        if not skill_dir.is_dir():
            continue
        
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        
        content = skill_file.read_text()
        
        # Extract name and description from frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            
            name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
            desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
            
            name = name_match.group(1).strip() if name_match else skill_dir.name
            description = desc_match.group(1).strip() if desc_match else "No description"
            
            skills.append({
                "name": name,
                "description": description,
                "path": f"skills/{skill_dir.name}/SKILL.md"
            })
    
    # Sort by name
    skills.sort(key=lambda x: x["name"])
    
    # Generate AGENTS.md
    lines = [
        "<skills>",
        "",
        "You have additional SKILLs documented in directories containing a \"SKILL.md\" file.",
        "",
        "These skills are:",
    ]
    
    for skill in skills:
        lines.append(f' - {skill["name"]} -> "{skill["path"]}"')
    
    lines.extend([
        "",
        "IMPORTANT: You MUST read the SKILL.md file whenever the description of the skills matches the user intent, or may help accomplish their task.",
        "",
        "<available_skills>",
        "",
    ])
    
    for skill in skills:
        lines.append(f'{skill["name"]}: `{skill["description"]}`')
    
    lines.extend([
        "",
        "</available_skills>",
        "",
        "Paths referenced within SKILL.md files are relative to that SKILL folder.",
        "",
        "</skills>",
    ])
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
    
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="OpenClaw Skill Template Generator")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new skill from template")
    create_parser.add_argument("name", help="Skill name (kebab-case)")
    create_parser.add_argument("--type", choices=["data", "api", "tool"], default="tool",
                             help="Skill type")
    create_parser.add_argument("--author", default="OpenClaw", help="Skill author")
    create_parser.add_argument("--output", default="skills", help="Output directory")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a skill")
    validate_parser.add_argument("path", help="Path to skill directory")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Generate AGENTS.md index")
    index_parser.add_argument("--skills-dir", default="skills", help="Skills directory")
    index_parser.add_argument("--output", default="agents/AGENTS.md", help="Output file")
    
    args = parser.parse_args()
    
    if args.command == "create":
        content = create_skill(args.name, args.type, args.author)
        output_dir = Path(args.output) / args.name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        skill_file = output_dir / "SKILL.md"
        skill_file.write_text(content)
        
        print(f"✅ Created skill at: {skill_file}")
        print(f"   Type: {args.type}")
        print(f"   Next steps:")
        print(f"   1. Edit {skill_file} to customize")
        print(f"   2. Add examples and commands")
        print(f"   3. Run: python3 scripts/skill-template.py validate {output_dir}")
        
    elif args.command == "validate":
        result = validate_skill(args.path)
        
        print(f"\n🔍 Validating: {args.path}")
        print(f"   Status: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
        
        if result["errors"]:
            print(f"\n❌ Errors ({len(result['errors'])}):")
            for error in result["errors"]:
                print(f"   - {error}")
        
        if result["warnings"]:
            print(f"\n⚠️  Warnings ({len(result['warnings'])}):")
            for warning in result["warnings"]:
                print(f"   - {warning}")
        
        print(f"\n📋 Checks:")
        for check, status in result["checks"].items():
            icon = "✅" if status else "❌"
            print(f"   {icon} {check}")
        
        sys.exit(0 if result["valid"] else 1)
        
    elif args.command == "index":
        output = generate_agents_md(args.skills_dir, args.output)
        print(f"✅ Generated AGENTS.md at: {output}")
        
        # Show summary
        content = Path(output).read_text()
        skill_count = content.count(" -> ")
        print(f"   Indexed {skill_count} skills")
        
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
