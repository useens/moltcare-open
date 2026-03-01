#!/usr/bin/env python3
"""
OpenClaw Dynamic Tool Discovery System
提取自 Apify Actor Schema 获取模式

提供工具/技能的动态发现和自省能力
"""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str
    description: str
    required: bool = False
    default: Any = None
    example: Optional[str] = None


@dataclass
class ToolSchema:
    """Tool schema definition."""
    name: str
    description: str
    parameters: list[ToolParameter] = field(default_factory=list)
    returns: Optional[str] = None
    examples: list[str] = field(default_factory=list)


class ToolRegistry:
    """Registry for dynamic tool discovery."""
    
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self._schemas: dict[str, ToolSchema] = {}
        self._discovered = False
    
    def discover(self) -> list[ToolSchema]:
        """Discover all available tools from skills."""
        schemas = []
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                continue
            
            schema = self._parse_skill(skill_file)
            if schema:
                schemas.append(schema)
                self._schemas[schema.name] = schema
        
        self._discovered = True
        return schemas
    
    def _parse_skill(self, skill_file: Path) -> Optional[ToolSchema]:
        """Parse SKILL.md to extract tool schema."""
        content = skill_file.read_text()
        
        # Extract frontmatter
        import re
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            return None
        
        frontmatter = frontmatter_match.group(1)
        
        # Parse fields
        name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
        desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
        
        name = name_match.group(1).strip() if name_match else skill_file.parent.name
        description = desc_match.group(1).strip() if desc_match else "No description"
        
        # Try to extract parameters from markdown
        parameters = self._extract_parameters(content)
        examples = self._extract_examples(content)
        
        return ToolSchema(
            name=name,
            description=description,
            parameters=parameters,
            examples=examples
        )
    
    def _extract_parameters(self, content: str) -> list[ToolParameter]:
        """Extract parameters from skill markdown."""
        parameters = []
        
        # Look for parameter tables or lists
        # Pattern: | Name | Type | Description | Required |
        import re
        table_pattern = r'\|[^\n]*(?:parameter|arg|option)[^\n]*\|\n\|[-:\s|]+\|\n((?:\|[^\n]+\|\n)+)'
        matches = re.findall(table_pattern, content, re.IGNORECASE)
        
        for match in matches:
            lines = match.strip().split('\n')
            for line in lines:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 3:
                    param = ToolParameter(
                        name=parts[0],
                        type=parts[1] if len(parts) > 1 else "string",
                        description=parts[2] if len(parts) > 2 else "",
                        required="required" in line.lower() or parts[3].lower() == "yes" if len(parts) > 3 else False
                    )
                    parameters.append(param)
        
        return parameters
    
    def _extract_examples(self, content: str) -> list[str]:
        """Extract examples from skill markdown."""
        examples = []
        
        import re
        # Look for code blocks after "Example"
        example_blocks = re.findall(r'(?:###?\s*Example[^\n]*\n+)?```(?:bash|shell)?\n(.*?)```', content, re.DOTALL)
        
        for block in example_blocks:
            command = block.strip()
            if command and not command.startswith('#'):
                examples.append(command)
        
        return examples[:3]  # Limit to 3 examples
    
    def get_schema(self, name: str) -> Optional[ToolSchema]:
        """Get schema for a specific tool."""
        if not self._discovered:
            self.discover()
        return self._schemas.get(name)
    
    def list_tools(self) -> list[dict]:
        """List all available tools."""
        if not self._discovered:
            self.discover()
        
        return [
            {
                "name": schema.name,
                "description": schema.description,
                "parameters": len(schema.parameters)
            }
            for schema in self._schemas.values()
        ]
    
    def search(self, query: str) -> list[ToolSchema]:
        """Search tools by keyword."""
        if not self._discovered:
            self.discover()
        
        query = query.lower()
        results = []
        
        for schema in self._schemas.values():
            if (query in schema.name.lower() or 
                query in schema.description.lower()):
                results.append(schema)
        
        return results
    
    def to_json(self) -> str:
        """Export all schemas as JSON."""
        if not self._discovered:
            self.discover()
        
        data = []
        for schema in self._schemas.values():
            data.append({
                "name": schema.name,
                "description": schema.description,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required
                    }
                    for p in schema.parameters
                ],
                "examples": schema.examples
            })
        
        return json.dumps(data, indent=2)


def main():
    """CLI for tool discovery."""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenClaw Tool Discovery")
    subparsers = parser.add_subparsers(dest="command")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all tools")
    list_parser.add_argument("--skills-dir", default="skills")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get tool schema")
    get_parser.add_argument("name", help="Tool name")
    get_parser.add_argument("--skills-dir", default="skills")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search tools")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--skills-dir", default="skills")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export all schemas as JSON")
    export_parser.add_argument("--skills-dir", default="skills")
    export_parser.add_argument("--output", help="Output file")
    
    args = parser.parse_args()
    
    registry = ToolRegistry(args.skills_dir)
    
    if args.command == "list":
        tools = registry.list_tools()
        print(f"\n🔧 Available Tools ({len(tools)}):\n")
        for tool in sorted(tools, key=lambda x: x["name"]):
            print(f"  {tool['name']}")
            print(f"    {tool['description'][:60]}...")
            print(f"    Parameters: {tool['parameters']}")
            print()
    
    elif args.command == "get":
        schema = registry.get_schema(args.name)
        if schema:
            print(f"\n📋 {schema.name}\n")
            print(f"Description: {schema.description}")
            print(f"\nParameters ({len(schema.parameters)}):")
            for param in schema.parameters:
                req = "required" if param.required else "optional"
                print(f"  - {param.name} ({param.type}, {req})")
                print(f"    {param.description}")
            if schema.examples:
                print(f"\nExamples:")
                for ex in schema.examples:
                    print(f"  $ {ex}")
        else:
            print(f"❌ Tool not found: {args.name}")
    
    elif args.command == "search":
        results = registry.search(args.query)
        print(f"\n🔍 Search results for '{args.query}' ({len(results)} found):\n")
        for schema in results:
            print(f"  {schema.name}")
            print(f"    {schema.description[:80]}...")
            print()
    
    elif args.command == "export":
        json_str = registry.to_json()
        if args.output:
            Path(args.output).write_text(json_str)
            print(f"✅ Exported to {args.output}")
        else:
            print(json_str)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
