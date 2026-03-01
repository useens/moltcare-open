#!/usr/bin/env python3
"""
OpenClaw Skill Enhancer
自动将现有 SKILL.md 升级到 Apify 风格的最佳实践
"""

import re
import sys
from pathlib import Path
from typing import Optional


class SkillEnhancer:
    """Enhance existing skills with Apify design patterns."""
    
    def __init__(self, skill_path: str):
        self.skill_path = Path(skill_path)
        self.skill_file = self.skill_path / "SKILL.md"
        
        if not self.skill_file.exists():
            raise FileNotFoundError(f"SKILL.md not found at {skill_file}")
        
        self.content = self.skill_file.read_text()
        self.enhancements = []
    
    def check_frontmatter(self) -> bool:
        """Check if YAML frontmatter exists."""
        return bool(re.match(r'^---\s*\n', self.content))
    
    def add_workflow_section(self) -> str:
        """Add standardized workflow section if missing."""
        if "## Workflow" in self.content:
            return self.content
        
        workflow = '''
## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Understand user goal
- [ ] Step 2: Select approach
- [ ] Step 3: Ask user preferences (format, scope)
- [ ] Step 4: Execute the task
- [ ] Step 5: Summarize results
```

'''
        # Insert before first ## section
        match = re.search(r'\n##\s+', self.content)
        if match:
            pos = match.start()
            self.content = self.content[:pos] + workflow + self.content[pos:]
            self.enhancements.append("Added Workflow section")
        
        return self.content
    
    def add_error_handling_section(self) -> str:
        """Add error handling section if missing."""
        if "## Error Handling" in self.content or "## Troubleshooting" in self.content:
            return self.content
        
        error_section = '''
## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `COMMAND_NOT_FOUND` | Tool not installed | Install the required CLI tool |
| `AUTH_ERROR` | Missing/invalid token | Check `.env` file |
| `NOT_FOUND` | Resource doesn't exist | Verify ID/name |

'''
        self.content += error_section
        self.enhancements.append("Added Error Handling section")
        return self.content
    
    def add_output_formats(self) -> str:
        """Add output format guidance if applicable."""
        if "## Output" in self.content or "output format" in self.content.lower():
            return self.content
        
        # Check if skill likely produces output
        if any(kw in self.content.lower() for kw in ['file', 'save', 'export', 'generate']):
            output_section = '''
## Output Formats

| Format | Use Case | Command |
|--------|----------|---------|
| **Quick** | Preview in chat | (no flag) |
| **JSON** | Machine processing | `--format json` |
| **Markdown** | Human readable | `--format md` |

'''
            # Insert before Error Handling or at end
            if "## Error Handling" in self.content:
                pos = self.content.index("## Error Handling")
                self.content = self.content[:pos] + output_section + self.content[pos:]
            else:
                self.content += output_section
            
            self.enhancements.append("Added Output Formats section")
        
        return self.content
    
    def standardize_headings(self) -> str:
        """Standardize heading format."""
        original = self.content
        
        # Ensure main title is H1
        lines = self.content.split('\n')
        if lines and not lines[0].startswith('# '):
            # Find first H1 or H2
            for i, line in enumerate(lines):
                if line.startswith('## '):
                    lines[i] = line.replace('## ', '# ', 1)
                    break
            self.content = '\n'.join(lines)
        
        if self.content != original:
            self.enhancements.append("Standardized headings")
        
        return self.content
    
    def add_prerequisites_checklist(self) -> str:
        """Convert Prerequisites to checklist format."""
        if "## Prerequisites" not in self.content:
            return self.content
        
        # Find Prerequisites section
        prereq_match = re.search(
            r'(## Prerequisites\s*\n)(.*?)(?=\n##|\Z)',
            self.content,
            re.DOTALL
        )
        
        if prereq_match:
            prereq_content = prereq_match.group(2)
            # Convert bullet points to checklist
            new_prereq = re.sub(
                r'^[\s]*[-*][\s]+',
                '- [ ] ',
                prereq_content,
                flags=re.MULTILINE
            )
            
            if new_prereq != prereq_content:
                self.content = (
                    self.content[:prereq_match.start()] +
                    prereq_match.group(1) +
                    new_prereq +
                    self.content[prereq_match.end():]
                )
                self.enhancements.append("Converted Prerequisites to checklist")
        
        return self.content
    
    def enhance(self, dry_run: bool = False) -> dict:
        """Apply all enhancements."""
        self.add_workflow_section()
        self.add_error_handling_section()
        self.add_output_formats()
        self.standardize_headings()
        self.add_prerequisites_checklist()
        
        result = {
            "enhancements": self.enhancements,
            "modified": len(self.enhancements) > 0,
            "dry_run": dry_run
        }
        
        if not dry_run and self.enhancements:
            # Backup original
            backup_path = self.skill_file.with_suffix('.md.bak')
            backup_path.write_text(self.skill_file.read_text())
            
            # Write enhanced version
            self.skill_file.write_text(self.content)
            result["backup"] = str(backup_path)
        
        return result
    
    def get_summary(self) -> str:
        """Get enhancement summary."""
        lines = [f"\n📋 Enhancement Report for {self.skill_path.name}", ""]
        
        if self.enhancements:
            lines.append(f"Applied {len(self.enhancements)} enhancements:")
            for enhancement in self.enhancements:
                lines.append(f"  ✅ {enhancement}")
        else:
            lines.append("No enhancements needed - skill already follows best practices!")
        
        return '\n'.join(lines)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhance OpenClaw skills with Apify patterns")
    parser.add_argument("path", help="Path to skill directory")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--all", action="store_true", help="Enhance all skills in directory")
    
    args = parser.parse_args()
    
    if args.all:
        skills_dir = Path(args.path)
        results = []
        
        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            
            try:
                enhancer = SkillEnhancer(str(skill_dir))
                result = enhancer.enhance(dry_run=args.dry_run)
                results.append((skill_dir.name, result))
                print(enhancer.get_summary())
            except Exception as e:
                print(f"❌ Error processing {skill_dir.name}: {e}")
        
        print(f"\n{'='*50}")
        print(f"Enhanced {len([r for r in results if r[1]['modified']])} skills")
        
    else:
        enhancer = SkillEnhancer(args.path)
        result = enhancer.enhance(dry_run=args.dry_run)
        print(enhancer.get_summary())
        
        if result["modified"] and not args.dry_run:
            print(f"\n💾 Backup saved to: {result.get('backup', 'N/A')}")
            print(f"✨ Enhanced skill saved to: {enhancer.skill_file}")


if __name__ == "__main__":
    main()
