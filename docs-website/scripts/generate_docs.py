#!/usr/bin/env python3
"""
Auto-Documentation Generator for Local AI Packaged
==================================================

This script automatically generates comprehensive documentation from the codebase,
including function signatures, class definitions, docstrings, and usage examples.

Usage:
    python scripts/generate_docs.py
    python scripts/generate_docs.py --output docs-website/src/data
    python scripts/generate_docs.py --include-private --format json
"""

import os
import sys
import ast
import json
import yaml
import inspect
import importlib
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FunctionDoc:
    name: str
    signature: str
    docstring: Optional[str]
    file_path: str
    line_number: int
    parameters: List[Dict[str, Any]]
    return_type: Optional[str]
    decorators: List[str]
    is_async: bool
    examples: List[str]

@dataclass
class ClassDoc:
    name: str
    docstring: Optional[str]
    file_path: str
    line_number: int
    methods: List[FunctionDoc]
    properties: List[Dict[str, Any]]
    inheritance: List[str]
    decorators: List[str]

@dataclass
class ModuleDoc:
    name: str
    file_path: str
    docstring: Optional[str]
    functions: List[FunctionDoc]
    classes: List[ClassDoc]
    constants: List[Dict[str, Any]]
    imports: List[str]

class DocumentationGenerator:
    def __init__(self, project_root: Path, include_private: bool = False):
        self.project_root = project_root
        self.include_private = include_private
        self.modules: List[ModuleDoc] = []
        
    def analyze_file(self, file_path: Path) -> Optional[ModuleDoc]:
        """Analyze a Python file and extract documentation information."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract module docstring
            module_docstring = ast.get_docstring(tree)
            
            # Extract functions, classes, and constants
            functions = []
            classes = []
            constants = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if self.include_private or not node.name.startswith('_'):
                        func_doc = self._extract_function_doc(node, file_path)
                        functions.append(func_doc)
                
                elif isinstance(node, ast.ClassDef):
                    if self.include_private or not node.name.startswith('_'):
                        class_doc = self._extract_class_doc(node, file_path)
                        classes.append(class_doc)
                
                elif isinstance(node, ast.Assign):
                    # Extract constants (uppercase variables)
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            constants.append({
                                'name': target.id,
                                'line_number': node.lineno,
                                'value': 'See source code'  # Simplified for safety
                            })
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    else:
                        module = node.module or ''
                        for alias in node.names:
                            imports.append(f"{module}.{alias.name}")
            
            relative_path = str(file_path.relative_to(self.project_root))
            module_name = relative_path.replace('/', '.').replace('\\', '.').replace('.py', '')
            
            return ModuleDoc(
                name=module_name,
                file_path=relative_path,
                docstring=module_docstring,
                functions=functions,
                classes=classes,
                constants=constants,
                imports=imports
            )
            
        except Exception as e:
            logger.warning(f"Failed to analyze {file_path}: {e}")
            return None
    
    def _extract_function_doc(self, node: ast.FunctionDef, file_path: Path) -> FunctionDoc:
        """Extract documentation from a function definition."""
        docstring = ast.get_docstring(node)
        
        # Extract parameters
        parameters = []
        for arg in node.args.args:
            param = {
                'name': arg.arg,
                'annotation': self._safe_unparse(arg.annotation),
                'default': None
            }
            parameters.append(param)
        
        # Add defaults
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            parameters[defaults_offset + i]['default'] = self._safe_unparse(default)
        
        # Extract decorators
        decorators = [self._safe_unparse(decorator) for decorator in node.decorator_list]
        
        # Extract return type annotation
        return_type = self._safe_unparse(node.returns) if node.returns else None
        
        # Extract examples from docstring
        examples = self._extract_examples_from_docstring(docstring)
        
        return FunctionDoc(
            name=node.name,
            signature=self._get_function_signature(node),
            docstring=docstring,
            file_path=str(file_path.relative_to(self.project_root)),
            line_number=node.lineno,
            parameters=parameters,
            return_type=return_type,
            decorators=decorators,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            examples=examples
        )
    
    def _extract_class_doc(self, node: ast.ClassDef, file_path: Path) -> ClassDoc:
        """Extract documentation from a class definition."""
        docstring = ast.get_docstring(node)
        
        # Extract methods
        methods = []
        properties = []
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if self.include_private or not item.name.startswith('_'):
                    method_doc = self._extract_function_doc(item, file_path)
                    methods.append(method_doc)
        
        # Extract inheritance
        inheritance = [self._safe_unparse(base) for base in node.bases]
        
        # Extract decorators
        decorators = [self._safe_unparse(decorator) for decorator in node.decorator_list]
        
        return ClassDoc(
            name=node.name,
            docstring=docstring,
            file_path=str(file_path.relative_to(self.project_root)),
            line_number=node.lineno,
            methods=methods,
            properties=properties,
            inheritance=inheritance,
            decorators=decorators
        )
    
    def _safe_unparse(self, node) -> str:
        """Safely unparse an AST node."""
        if node is None:
            return ''
        try:
            if hasattr(ast, 'unparse'):
                return ast.unparse(node)
            else:
                # Fallback for older Python versions
                return repr(node)
        except Exception:
            return 'Unknown'
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Generate function signature string."""
        args = []
        
        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._safe_unparse(arg.annotation)}"
            args.append(arg_str)
        
        # Add defaults
        defaults_offset = len(node.args.args) - len(node.args.defaults)
        for i, default in enumerate(node.args.defaults):
            args[defaults_offset + i] += f" = {self._safe_unparse(default)}"
        
        # *args
        if node.args.vararg:
            vararg = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg += f": {self._safe_unparse(node.args.vararg.annotation)}"
            args.append(vararg)
        
        # **kwargs
        if node.args.kwarg:
            kwarg = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg += f": {self._safe_unparse(node.args.kwarg.annotation)}"
            args.append(kwarg)
        
        signature = f"{node.name}({', '.join(args)})"
        
        if node.returns:
            signature += f" -> {self._safe_unparse(node.returns)}"
        
        return signature
    
    def _extract_examples_from_docstring(self, docstring: Optional[str]) -> List[str]:
        """Extract code examples from docstring."""
        if not docstring:
            return []
        
        examples = []
        lines = docstring.split('\n')
        in_example = False
        current_example = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('>>>') or stripped.startswith('Example:') or 'example' in stripped.lower():
                if current_example:
                    examples.append('\n'.join(current_example))
                    current_example = []
                in_example = True
                current_example.append(line)
            elif in_example:
                if stripped == '' and current_example:
                    examples.append('\n'.join(current_example))
                    current_example = []
                    in_example = False
                else:
                    current_example.append(line)
        
        if current_example:
            examples.append('\n'.join(current_example))
        
        return examples
    
    def scan_project(self) -> None:
        """Scan the entire project for Python files."""
        logger.info(f"Scanning project at {self.project_root}")
        
        # Common directories to scan
        scan_dirs = [
            'scripts',
            'services', 
            'tools'
        ]
        
        python_files = []
        
        for scan_dir in scan_dirs:
            dir_path = self.project_root / scan_dir
            if dir_path.exists():
                python_files.extend(dir_path.rglob('*.py'))
        
        # Also scan root directory Python files
        python_files.extend(self.project_root.glob('*.py'))
        
        logger.info(f"Found {len(python_files)} Python files")
        
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
                
            module_doc = self.analyze_file(file_path)
            if module_doc:
                self.modules.append(module_doc)
        
        logger.info(f"Successfully analyzed {len(self.modules)} modules")
    
    def export_json(self, output_path: Path) -> None:
        """Export documentation as JSON."""
        data = {
            'modules': [asdict(module) for module in self.modules],
            'summary': {
                'total_modules': len(self.modules),
                'total_functions': sum(len(m.functions) for m in self.modules),
                'total_classes': sum(len(m.classes) for m in self.modules),
                'total_constants': sum(len(m.constants) for m in self.modules),
            }
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported JSON documentation to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate documentation from codebase")
    parser.add_argument('--output', '-o', default='src/data', 
                        help='Output directory for documentation')
    parser.add_argument('--include-private', action='store_true', 
                        help='Include private functions and classes')
    
    args = parser.parse_args()
    
    # Get the actual project root (parent of docs-website)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    output_dir = script_dir.parent / args.output
    
    generator = DocumentationGenerator(project_root, args.include_private)
    generator.scan_project()
    
    generator.export_json(output_dir / 'documentation.json')
    
    print(f"Documentation generation complete!")
    print(f"Generated docs for {len(generator.modules)} modules")
    print(f"Output: {output_dir / 'documentation.json'}")

if __name__ == '__main__':
    main()