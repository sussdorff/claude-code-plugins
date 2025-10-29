#!/usr/bin/env python3
# /// script
# dependencies = [
#   "tree-sitter>=0.25.0",
#   "tree-sitter-bash>=0.25.0",
# ]
# ///
"""
Shell Function Analyzer - Tree-sitter based version
Generates extract.json for efficient function discovery in bash/zsh/shell scripts

This replaces the regex-based bash version with accurate AST parsing that handles:
- Heredocs with braces (<<EOF ... EOF)
- Complex nested structures
- Command substitutions
- All bash/zsh syntax edge cases

Works for both bash and zsh scripts (uses bash tree-sitter which handles zsh well).

Output format matches PowerShell extract.json for consistency across codebases.

Usage with uv (recommended):
    uv run analyze-shell-functions.py --path ./scripts --output extract.json

Traditional usage:
    python3 analyze-shell-functions.py --path ./scripts --output extract.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tree_sitter import Language, Parser
import tree_sitter_bash as ts_bash


class BashFunctionAnalyzer:
    """Analyzes bash/shell scripts using tree-sitter AST parsing"""

    def __init__(self):
        self.parser = Parser(Language(ts_bash.language()))
        self.bash_lang = Language(ts_bash.language())

    def analyze_file(self, file_path: Path) -> List[Dict]:
        """Analyze a single shell file and return function metadata"""
        try:
            with open(file_path, 'rb') as f:
                source_code = f.read()

            tree = self.parser.parse(source_code)
            functions = []

            # Find all function definitions in the tree
            self._walk_tree(tree.root_node, source_code, file_path, functions)

            return functions

        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}", file=sys.stderr)
            return []

    def _walk_tree(self, node, source_code: bytes, file_path: Path, functions: List[Dict]):
        """Recursively walk the AST to find function definitions"""
        if node.type == "function_definition":
            func_data = self._extract_function_metadata(node, source_code, file_path)
            if func_data:
                functions.append(func_data)

        # Recursively process children
        for child in node.children:
            self._walk_tree(child, source_code, file_path, functions)

    def _extract_function_metadata(self, node, source_code: bytes, file_path: Path) -> Optional[Dict]:
        """Extract comprehensive metadata for a function definition"""
        # Get function name
        func_name = self._get_function_name(node, source_code)
        if not func_name:
            return None

        # Get line numbers (tree-sitter uses 0-based, we need 1-based)
        start_line = node.start_point[0] + 1
        end_line = node.end_point[0] + 1
        size = end_line - start_line + 1

        # Get signature (first line)
        lines = source_code.decode('utf-8', errors='replace').split('\n')
        signature = lines[start_line - 1].strip() if start_line <= len(lines) else ""

        # Get function body for analysis
        func_body = source_code[node.start_byte:node.end_byte].decode('utf-8', errors='replace')

        # Extract metadata
        params = self._extract_parameters(node, source_code)
        purpose = self._extract_purpose(lines, start_line, func_name)
        category = self._categorize_function(func_name)
        return_type = self._infer_return_type(node, source_code)

        return {
            'name': func_name,
            'file': str(file_path.absolute()),
            'start': start_line,
            'end': end_line,
            'size': size,
            'signature': signature,
            'purpose': purpose,
            'category': category,
            'return_type': return_type,
            'params': params
        }

    def _get_function_name(self, node, source_code: bytes) -> Optional[str]:
        """Extract function name from function_definition node"""
        # Look for 'word' node which contains the function name
        for child in node.children:
            if child.type == "word":
                return source_code[child.start_byte:child.end_byte].decode('utf-8', errors='replace')
        return None

    def _extract_parameters(self, func_node, source_code: bytes) -> List[str]:
        """
        Extract parameter names from function body
        Looks for: local param=$1, local param="$1", local param="${1}", etc.
        Only scans first ~20 lines to avoid false positives
        """
        params = []
        seen_params = set()

        # Find the compound_statement (function body)
        body_node = None
        for child in func_node.children:
            if child.type == "compound_statement":
                body_node = child
                break

        if not body_node:
            return params

        # Look for declaration commands (local/declare) in first part of function
        declaration_count = 0
        max_declarations = 20  # Limit scan depth

        def scan_for_declarations(node, depth=0):
            nonlocal declaration_count
            if declaration_count >= max_declarations or depth > 5:
                return

            if node.type == "declaration_command":
                declaration_count += 1
                # Look for variable_assignment children
                for child in node.children:
                    if child.type == "variable_assignment":
                        var_name, uses_positional = self._analyze_variable_assignment(child, source_code)
                        if var_name and uses_positional and var_name not in seen_params:
                            params.append(var_name)
                            seen_params.add(var_name)

            # Only recurse into compound statements and declaration commands early in function
            if node.type in ("compound_statement", "declaration_command") and depth < 3:
                for child in node.children:
                    scan_for_declarations(child, depth + 1)

        scan_for_declarations(body_node)
        return params

    def _analyze_variable_assignment(self, node, source_code: bytes) -> Tuple[Optional[str], bool]:
        """
        Analyze a variable_assignment node to extract variable name and check if it uses positional params
        Returns: (variable_name, uses_positional_parameter)
        """
        var_name = None
        uses_positional = False

        for child in node.children:
            if child.type == "variable_name":
                var_name = source_code[child.start_byte:child.end_byte].decode('utf-8', errors='replace')
            elif var_name:  # After we found the name, check the value
                # Get the text of the value part
                value_text = source_code[child.start_byte:child.end_byte].decode('utf-8', errors='replace')
                # Check if it references a positional parameter ($1, $2, ${1}, ${1:-default}, etc.)
                if re.search(r'\$\{?\d+', value_text) and '$(' not in value_text:
                    uses_positional = True
                    break

        return var_name, uses_positional

    def _extract_purpose(self, lines: List[str], start_line: int, func_name: str) -> str:
        """
        Extract function purpose from comments above function
        Falls back to generating purpose from function name
        """
        purpose = ""
        blank_line_count = 0
        max_blank_lines = 2  # Allow max 2 blank lines between comment and function

        # Look backwards from function start for comments
        for i in range(start_line - 2, max(0, start_line - 11), -1):
            line = lines[i].strip()

            if line == "":
                blank_line_count += 1
                if blank_line_count > max_blank_lines:
                    # Too many blank lines, stop searching
                    break
                continue

            if line.startswith('#'):
                comment = line[1:].strip()
                # Skip common markers, shebangs, and empty comments
                if not comment:
                    blank_line_count = 0
                    continue
                if comment.startswith('!'):  # Shebang
                    blank_line_count = 0
                    continue
                if re.match(r'^(TODO|FIXME|NOTE|shellcheck|pylint|type:|XXX|HACK|BUG)', comment, re.IGNORECASE):
                    blank_line_count = 0
                    continue
                # Skip separator lines (###, ---, ===)
                if re.match(r'^[#\-=]{3,}$', comment):
                    blank_line_count = 0
                    continue
                # Valid comment found
                purpose = comment
                break
            else:
                # Hit non-comment, non-empty line (code from previous function/statement)
                break

        # Fallback: generate from function name
        if not purpose:
            purpose = self._generate_purpose_from_name(func_name)

        return purpose

    def _generate_purpose_from_name(self, func_name: str) -> str:
        """Generate descriptive purpose from function name"""
        patterns = [
            (r'^(get|show|display)_(.+)', lambda m: f"Gets or displays {m.group(2).replace('_', ' ')} information"),
            (r'^(set|update)_(.+)', lambda m: f"Sets or updates {m.group(2).replace('_', ' ')} configuration"),
            (r'^(test|check|validate)_(.+)', lambda m: f"Tests or checks {m.group(2).replace('_', ' ')} status"),
            (r'^(install|add)_(.+)', lambda m: f"Installs or adds {m.group(2).replace('_', ' ')}"),
            (r'^(remove|uninstall)_(.+)', lambda m: f"Removes or uninstalls {m.group(2).replace('_', ' ')}"),
        ]

        for pattern, generator in patterns:
            match = re.match(pattern, func_name)
            if match:
                return generator(match)

        return f"Performs {func_name.replace('_', ' ')} operation"

    def _categorize_function(self, func_name: str) -> str:
        """Categorize function by name patterns"""
        categories = [
            (r'^(show|display|write)_', 'display'),
            (r'^(get|set)_.*config', 'core'),
            (r'^(get|set|update|read|save)_', 'core'),
            (r'^(test|check|validate)_', 'test'),
            (r'^(export|import|backup|restore)_', 'export'),
            (r'^(install|uninstall|remove|add)_', 'install'),
            (r'^(start|stop|restart|enable|disable)_', 'service'),
        ]

        for pattern, category in categories:
            if re.match(pattern, func_name):
                return category

        return 'helper'

    def _infer_return_type(self, func_node, source_code: bytes) -> str:
        """Infer return type from function body (basic heuristics)"""
        func_text = source_code[func_node.start_byte:func_node.end_byte].decode('utf-8', errors='replace')

        # Look for explicit return statements
        if re.search(r'return\s+[0-1]', func_text):
            return 'int'
        elif 'echo' in func_text or 'printf' in func_text:
            return 'string'
        else:
            return 'void'


def build_extract_json(all_functions: List[Dict]) -> Dict:
    """Build the extract.json structure from all collected functions"""
    # Build index: function_name -> metadata
    index = {}
    for func in all_functions:
        index[func['name']] = {
            'file': func['file'],
            'start': func['start'],
            'end': func['end'],
            'size': func['size'],
            'signature': func['signature'],
            'purpose': func['purpose'],
            'return_type': func['return_type'],
            'category': func['category'],
            'params': func['params']
        }

    # Build categories: category -> [function_names]
    categories = {}
    for func in all_functions:
        cat = func['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(func['name'])

    # Sort function names within categories
    for cat in categories:
        categories[cat] = sorted(categories[cat])

    # Build quick_ref: function_name -> "filename.sh:start-end"
    quick_ref = {}
    for func in all_functions:
        filename = Path(func['file']).name
        quick_ref[func['name']] = f"{filename}:{func['start']}-{func['end']}"

    return {
        'index': index,
        'categories': categories,
        'quick_ref': quick_ref
    }


def main():
    parser = argparse.ArgumentParser(
        description='Bash Function Analyzer - Tree-sitter based version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
DESCRIPTION:
    Analyzes all shell (.sh, .bash) files in the specified directory tree and generates
    a comprehensive function index with metadata for efficient function discovery.

    Uses tree-sitter for accurate AST parsing, handling all bash syntax including:
    - Heredocs with braces
    - Complex nested structures
    - Command substitutions
    - All bash syntax edge cases

OUTPUT FORMAT (extract.json):
    {
      "index": {
        "function_name": {
          "file": "/full/path/to/file.sh",
          "start": 42, "end": 67, "size": 26,
          "purpose": "Gets or displays config information",
          "return_type": "void",
          "category": "core",
          "params": ["param1", "param2"],
          "signature": "function_name() {"
        }
      },
      "categories": {
        "display": ["show_status"], "core": ["get_config"]
      },
      "quick_ref": {
        "function_name": "filename.sh:42-67"
      }
    }

COMMON JQ QUERY PATTERNS:
    # Find functions by purpose (semantic search)
    jq '.index | to_entries[] | select(.value.purpose | test("backup"; "i")) | .key' extract.json

    # Get function location for extraction
    jq '.index."function_name" | {file_path: .file, offset: .start, limit: .size}' extract.json

    # Find functions by category
    jq '.categories.core[]' extract.json

PREREQUISITES:
    - Python 3.8+
    - tree-sitter: pip install tree-sitter
    - tree-sitter-bash: pip install tree-sitter-bash
    - jq for querying output (optional)
        """
    )

    parser.add_argument('--path', required=True, help='Directory to analyze')
    parser.add_argument('--output', required=True, help='Output extract.json file path')

    args = parser.parse_args()

    # Validate inputs
    analyze_path = Path(args.path)
    if not analyze_path.is_dir():
        print(f"Error: Path does not exist: {analyze_path}", file=sys.stderr)
        sys.exit(1)

    output_file = Path(args.output)

    # Find all shell files (bash, zsh, sh)
    print(f"Analyzing shell functions in: {analyze_path}", file=sys.stderr)
    shell_files = (
        list(analyze_path.rglob("*.sh")) +
        list(analyze_path.rglob("*.bash")) +
        list(analyze_path.rglob("*.zsh"))
    )

    if not shell_files:
        print(f"No shell files found in: {analyze_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(shell_files)} shell file(s)", file=sys.stderr)

    # Analyze all files
    analyzer = BashFunctionAnalyzer()
    all_functions = []

    for file_path in shell_files:
        print(f"  Processing: {file_path.name}...", file=sys.stderr)
        functions = analyzer.analyze_file(file_path)
        all_functions.extend(functions)

    # Build extract.json structure
    extract_data = build_extract_json(all_functions)

    # Write output
    with open(output_file, 'w') as f:
        json.dump(extract_data, f, indent=2)

    print(f"✅ Analysis complete: {len(all_functions)} function(s) found", file=sys.stderr)
    print(f"📄 Output: {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
