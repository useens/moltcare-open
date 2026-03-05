#!/usr/bin/env python3
"""
OpenClaw Skill Development Workflow
完整技能开发工作流 - 从构思到发布

Usage:
    # 创建新技能
    python3 scripts/skill-workflow.py create <name> --type=api|tool|data

    # 开发迭代
    python3 scripts/skill-workflow.py dev <name>  # 进入开发模式

    # 测试验证
    python3 scripts/skill-workflow.py test <name>

    # 发布
    python3 scripts/skill-workflow.py publish <name>

    # 完整流程
    python3 scripts/skill-workflow.py full <name> --type=api
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD} {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_step(step_num, total, text):
    print(f"{Colors.CYAN}[{step_num}/{total}] {Colors.BOLD}{text}{Colors.ENDC}")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


class SkillWorkflow:
    """Complete skill development workflow."""
    
    def __init__(self, workspace: str = "."):
        self.workspace = Path(workspace).resolve()
        self.skills_dir = self.workspace / "skills"
        self.scripts_dir = self.workspace / "scripts"
        self.agents_dir = self.workspace / "agents"
    
    def create(self, name: str, skill_type: str = "tool") -> bool:
        """Step 1: Create new skill from template."""
        print_step(1, 5, "Creating skill from template...")
        
        result = subprocess.run(
            [sys.executable, str(self.scripts_dir / "skill-template.py"), 
             "create", name, "--type", skill_type],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success(f"Created skill: {name}")
            skill_path = self.skills_dir / name
            print(f"  Location: {skill_path}")
            print(f"  Next: Edit {skill_path}/SKILL.md")
            return True
        else:
            print_error(f"Failed to create skill: {result.stderr}")
            return False
    
    def develop(self, name: str) -> bool:
        """Step 2: Development mode - enhance and edit."""
        print_step(2, 5, "Entering development mode...")
        
        skill_path = self.skills_dir / name
        if not skill_path.exists():
            print_error(f"Skill not found: {name}")
            return False
        
        # Apply initial enhancement
        result = subprocess.run(
            [sys.executable, str(self.scripts_dir / "skill-enhancer.py"), 
             str(skill_path), "--dry-run"],
            capture_output=True,
            text=True
        )
        
        print(f"\n{Colors.CYAN}Enhancement preview:{Colors.ENDC}")
        print(result.stdout)
        
        # Interactive development
        print(f"\n{Colors.YELLOW}Development checklist:{Colors.ENDC}")
        checklist = [
            "Fill in skill description in frontmatter",
            "Complete Step 1-5 in Workflow section", 
            "Add concrete command examples",
            "Fill Error Handling table with real errors",
            "Test commands locally",
        ]
        
        for item in checklist:
            print(f"  ☐ {item}")
        
        print(f"\n{Colors.CYAN}Edit file:{Colors.ENDC} {skill_path}/SKILL.md")
        return True
    
    def validate(self, name: str) -> bool:
        """Step 3: Validate skill structure."""
        print_step(3, 5, "Validating skill structure...")
        
        skill_path = self.skills_dir / name
        
        # Structure validation
        result = subprocess.run(
            [sys.executable, str(self.scripts_dir / "skill-template.py"), 
             "validate", str(skill_path)],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        
        if result.returncode != 0:
            print_error("Validation failed. Fix issues before publishing.")
            return False
        
        # Check SKILL.md exists and is readable
        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            print_error("SKILL.md not found")
            return False
        
        content = skill_file.read_text()
        
        # Content checks
        checks = {
            "YAML frontmatter": "---" in content[:100],
            "name field": "name:" in content[:500],
            "description field": "description:" in content[:500],
            "Workflow section": "## Workflow" in content,
            "Error Handling": "## Error Handling" in content,
            "Examples": "## Examples" in content or "```" in content,
        }
        
        print(f"\n{Colors.CYAN}Content checks:{Colors.ENDC}")
        all_passed = True
        for check, passed in checks.items():
            status = f"{Colors.GREEN}✓" if passed else f"{Colors.RED}✗"
            print(f"  {status} {check}{Colors.ENDC}")
            if not passed:
                all_passed = False
        
        return all_passed
    
    def test(self, name: str) -> bool:
        """Step 4: Test skill commands."""
        print_step(4, 5, "Testing skill commands...")
        
        skill_path = self.skills_dir / name
        skill_file = skill_path / "SKILL.md"
        
        # Extract bash commands from examples
        content = skill_file.read_text()
        import re
        
        commands = re.findall(r'```bash\n(.*?)```', content, re.DOTALL)
        
        if not commands:
            print_warning("No bash commands found to test")
            return True
        
        print(f"Found {len(commands)} command blocks to verify\n")
        
        # Note: Actually running commands could be dangerous
        # Just verify they look syntactically valid
        for i, cmd_block in enumerate(commands[:3], 1):  # Limit to first 3
            lines = cmd_block.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Basic syntax check
                    if 'python3' in line or 'bash' in line:
                        print(f"  {Colors.GREEN}✓{Colors.ENDC} Command {i}: {line[:50]}...")
        
        print(f"\n{Colors.YELLOW}Note: Commands not executed (safety).{Colors.ENDC}")
        print(f"Test manually before publishing.")
        return True
    
    def publish(self, name: str) -> bool:
        """Step 5: Publish - update index and finalize."""
        print_step(5, 5, "Publishing skill...")
        
        # Final enhancement
        skill_path = self.skills_dir / name
        result = subprocess.run(
            [sys.executable, str(self.scripts_dir / "skill-enhancer.py"), 
             str(skill_path)],
            capture_output=True,
            text=True
        )
        
        # Update AGENTS.md
        result = subprocess.run(
            [sys.executable, str(self.scripts_dir / "skill-template.py"), 
             "index", "--output", str(self.agents_dir / "AGENTS.md")],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Published successfully!")
            print(f"  Skill: {name}")
            print(f"  Indexed in: {self.agents_dir}/AGENTS.md")
            
            # Show summary
            result = subprocess.run(
                [sys.executable, str(self.scripts_dir / "skill-template.py"), 
                 "validate", str(skill_path)],
                capture_output=True,
                text=True
            )
            print(f"\n{Colors.CYAN}Final validation:{Colors.ENDC}")
            print(result.stdout)
            return True
        else:
            print_error(f"Publish failed: {result.stderr}")
            return False
    
    def full(self, name: str, skill_type: str = "tool") -> bool:
        """Run complete workflow."""
        print_header(f"SKILL DEVELOPMENT WORKFLOW: {name}")
        
        steps = [
            ("Create", lambda: self.create(name, skill_type)),
            ("Develop", lambda: self.develop(name)),
            ("Validate", lambda: self.validate(name)),
            ("Test", lambda: self.test(name)),
            ("Publish", lambda: self.publish(name)),
        ]
        
        results = []
        for step_name, step_func in steps:
            try:
                result = step_func()
                results.append((step_name, result))
                if not result:
                    print_error(f"Step '{step_name}' failed. Stopping.")
                    break
            except Exception as e:
                print_error(f"Step '{step_name}' error: {e}")
                results.append((step_name, False))
                break
        
        # Summary
        print_header("WORKFLOW SUMMARY")
        for step_name, result in results:
            status = f"{Colors.GREEN}✓ PASS" if result else f"{Colors.RED}✗ FAIL"
            print(f"  {status}{Colors.ENDC} {step_name}")
        
        all_passed = all(r for _, r in results)
        if all_passed:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 Skill '{name}' ready for use!{Colors.ENDC}")
            print(f"\nNext steps:")
            print(f"  1. Test the skill with real commands")
            print(f"  2. Add to MEMORY.md if it's a key capability")
            print(f"  3. Consider sharing on ClawHub")
        
        return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="OpenClaw Skill Development Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Complete workflow for new API skill
  python3 scripts/skill-workflow.py full my-api --type=api
  
  # Step by step
  python3 scripts/skill-workflow.py create my-tool --type=tool
  python3 scripts/skill-workflow.py dev my-tool
  python3 scripts/skill-workflow.py validate my-tool
  python3 scripts/skill-workflow.py test my-tool
  python3 scripts/skill-workflow.py publish my-tool
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Create
    create_parser = subparsers.add_parser("create", help="Create new skill")
    create_parser.add_argument("name", help="Skill name (kebab-case)")
    create_parser.add_argument("--type", choices=["api", "tool", "data"], 
                              default="tool", help="Skill type")
    
    # Develop
    dev_parser = subparsers.add_parser("dev", help="Development mode")
    dev_parser.add_argument("name", help="Skill name")
    
    # Validate
    validate_parser = subparsers.add_parser("validate", help="Validate skill")
    validate_parser.add_argument("name", help="Skill name")
    
    # Test
    test_parser = subparsers.add_parser("test", help="Test skill")
    test_parser.add_argument("name", help="Skill name")
    
    # Publish
    publish_parser = subparsers.add_parser("publish", help="Publish skill")
    publish_parser.add_argument("name", help="Skill name")
    
    # Full workflow
    full_parser = subparsers.add_parser("full", help="Complete workflow")
    full_parser.add_argument("name", help="Skill name")
    full_parser.add_argument("--type", choices=["api", "tool", "data"], 
                           default="tool", help="Skill type")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    workflow = SkillWorkflow()
    
    commands = {
        "create": lambda: workflow.create(args.name, args.type if hasattr(args, 'type') else "tool"),
        "dev": lambda: workflow.develop(args.name),
        "validate": lambda: workflow.validate(args.name),
        "test": lambda: workflow.test(args.name),
        "publish": lambda: workflow.publish(args.name),
        "full": lambda: workflow.full(args.name, args.type if hasattr(args, 'type') else "tool"),
    }
    
    success = commands[args.command]()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
