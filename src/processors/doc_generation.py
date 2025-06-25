#!/usr/bin/env python3
"""
Dynamic Documentation Generation for Sparse GitHub Documentation

Analyzes existing documentation, identifies gaps, and generates comprehensive
documentation using AI and code analysis techniques.
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DocumentationAnalyzer:
    """Analyzer for assessing documentation completeness and identifying gaps."""

    def __init__(self):
        """Initialize the documentation analyzer."""
        self.essential_sections = [
            "installation",
            "quick_start",
            "api_reference",
            "examples",
            "configuration",
            "troubleshooting",
            "overview",
        ]

        self.section_weights = {
            "overview": 0.15,
            "installation": 0.20,
            "quick_start": 0.15,
            "api_reference": 0.25,
            "examples": 0.15,
            "configuration": 0.05,
            "troubleshooting": 0.05,
        }

    def analyze_completeness(
        self, documentation_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze documentation completeness and identify gaps.

        Args:
            documentation_data: Dictionary containing library documentation data

        Returns:
            Analysis results with completeness score and missing sections
        """
        try:
            library_name = documentation_data.get("library_name", "unknown")
            readme_content = documentation_data.get("readme_content", "")
            code_files = documentation_data.get("code_files", [])

            # Analyze existing sections
            existing_sections = self._identify_existing_sections(readme_content)

            # Calculate completeness score
            completeness_score = self._calculate_completeness_score(existing_sections)

            # Identify missing sections
            missing_sections = [
                section
                for section in self.essential_sections
                if section not in existing_sections
            ]

            # Generate recommendations
            recommendations = self._generate_recommendations(
                existing_sections, missing_sections, code_files
            )

            # Analyze code structure for API reference potential
            code_analysis = self._analyze_code_structure(code_files)

            return {
                "library_name": library_name,
                "completeness_score": completeness_score,
                "existing_sections": existing_sections,
                "missing_sections": missing_sections,
                "recommendations": recommendations,
                "code_analysis": code_analysis,
                "total_sections_found": len(existing_sections),
                "total_sections_expected": len(self.essential_sections),
            }

        except Exception as e:
            logger.error(f"Error analyzing documentation completeness: {e}")
            return {
                "completeness_score": 0.0,
                "existing_sections": [],
                "missing_sections": self.essential_sections,
                "recommendations": ["Error in analysis - manual review needed"],
                "error": str(e),
            }

    def identify_gaps(self, documentation_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Identify specific documentation gaps with priority levels.

        Args:
            documentation_data: Documentation data to analyze

        Returns:
            List of gaps with descriptions and priorities
        """
        analysis = self.analyze_completeness(documentation_data)
        gaps = []

        for missing_section in analysis["missing_sections"]:
            priority = self._get_section_priority(missing_section)
            description = self._get_gap_description(missing_section)

            gaps.append(
                {
                    "section": missing_section,
                    "priority": priority,
                    "description": description,
                    "estimated_effort": self._estimate_generation_effort(
                        missing_section
                    ),
                    "dependencies": self._get_section_dependencies(missing_section),
                }
            )

        # Sort by priority
        gaps.sort(
            key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]],
            reverse=True,
        )
        return gaps

    def extract_code_structure(
        self, code_files: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Extract code structure for API reference generation.

        Args:
            code_files: List of code file dictionaries

        Returns:
            Extracted code structure information
        """
        structure = {
            "classes": [],
            "functions": [],
            "modules": [],
            "imports": [],
            "constants": [],
        }

        for file_info in code_files:
            file_path = file_info.get("path", "")
            content = file_info.get("content", "")

            if file_path.endswith(".py"):
                file_structure = self._analyze_python_file(content, file_path)

                # Merge structures
                structure["classes"].extend(file_structure.get("classes", []))
                structure["functions"].extend(file_structure.get("functions", []))
                structure["modules"].append(
                    {
                        "name": Path(file_path).stem,
                        "path": file_path,
                        "docstring": file_structure.get("module_docstring", ""),
                        "exports": file_structure.get("exports", []),
                    }
                )
                structure["imports"].extend(file_structure.get("imports", []))
                structure["constants"].extend(file_structure.get("constants", []))

        return structure

    def _identify_existing_sections(self, content: str) -> list[str]:
        """Identify existing documentation sections in content."""
        content_lower = content.lower()
        found_sections = []

        section_patterns = {
            "overview": [r"overview", r"about", r"description", r"what is"],
            "installation": [r"install", r"setup"],
            "quick_start": [
                r"quick start",
                r"quickstart",
                r"getting started",
                r"tutorial",
            ],
            "api_reference": [
                r"api reference",
                r"api documentation",
                r"reference",
                r"methods",
                r"functions",
            ],
            "examples": [r"examples", r"example usage", r"code examples", r"demos"],
            "configuration": [r"configuration", r"config", r"settings", r"options"],
            "troubleshooting": [r"troubleshoot", r"faq", r"issues", r"problems"],
        }

        for section, patterns in section_patterns.items():
            for pattern in patterns:
                if re.search(r"\b" + pattern + r"\b", content_lower):
                    if section not in found_sections:
                        found_sections.append(section)
                    break

        return found_sections

    def _calculate_completeness_score(self, existing_sections: list[str]) -> float:
        """Calculate completeness score based on existing sections."""
        total_weight = sum(self.section_weights.values())
        achieved_weight = sum(
            self.section_weights.get(section, 0) for section in existing_sections
        )

        return min(1.0, achieved_weight / total_weight)

    def _generate_recommendations(
        self,
        existing_sections: list[str],
        missing_sections: list[str],
        code_files: list[dict[str, Any]],
    ) -> list[str]:
        """Generate recommendations for improving documentation."""
        recommendations = []

        # Priority recommendations based on missing sections
        if "installation" in missing_sections:
            recommendations.append(
                "Add installation instructions with package manager commands"
            )

        if "api_reference" in missing_sections and code_files:
            recommendations.append("Generate API reference from code structure")

        if "examples" in missing_sections:
            recommendations.append("Add code examples demonstrating key functionality")

        if "quick_start" in missing_sections:
            recommendations.append("Create a quick start guide for new users")

        # Code-based recommendations
        if code_files:
            has_classes = any(
                "class " in file_info.get("content", "") for file_info in code_files
            )
            if has_classes and "api_reference" in missing_sections:
                recommendations.append("Document class methods and properties")

        return recommendations

    def _analyze_code_structure(
        self, code_files: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze code structure for documentation potential."""
        analysis = {
            "total_files": len(code_files),
            "python_files": 0,
            "has_classes": False,
            "has_functions": False,
            "complexity_score": 0.0,
            "api_potential": 0.0,
        }

        total_complexity = 0

        for file_info in code_files:
            content = file_info.get("content", "")
            file_path = file_info.get("path", "")

            if file_path.endswith(".py"):
                analysis["python_files"] += 1

                # Check for classes and functions
                if "class " in content:
                    analysis["has_classes"] = True
                if "def " in content:
                    analysis["has_functions"] = True

                # Calculate complexity
                complexity = self._calculate_file_complexity(content)
                total_complexity += complexity

        if analysis["python_files"] > 0:
            analysis["complexity_score"] = total_complexity / analysis["python_files"]

            # Calculate API documentation potential
            api_potential = 0.0
            if analysis["has_classes"]:
                api_potential += 0.5
            if analysis["has_functions"]:
                api_potential += 0.3
            if analysis["complexity_score"] > 0.5:
                api_potential += 0.2

            analysis["api_potential"] = min(1.0, api_potential)

        return analysis

    def _analyze_python_file(self, content: str, file_path: str) -> dict[str, Any]:
        """Analyze a Python file for structure."""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "constants": [],
            "exports": [],
            "module_docstring": "",
        }

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "docstring": ast.get_docstring(node) or "",
                        "methods": [],
                        "file_path": file_path,
                        "line_number": node.lineno,
                    }

                    # Get methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                "name": item.name,
                                "docstring": ast.get_docstring(item) or "",
                                "args": [arg.arg for arg in item.args.args],
                                "is_private": item.name.startswith("_"),
                                "line_number": item.lineno,
                            }
                            class_info["methods"].append(method_info)

                    structure["classes"].append(class_info)

                elif isinstance(node, ast.FunctionDef) and not any(
                    isinstance(parent, ast.ClassDef)
                    for parent in ast.walk(tree)
                    if hasattr(parent, "body") and node in getattr(parent, "body", [])
                ):
                    # Top-level function
                    func_info = {
                        "name": node.name,
                        "docstring": ast.get_docstring(node) or "",
                        "args": [arg.arg for arg in node.args.args],
                        "is_private": node.name.startswith("_"),
                        "file_path": file_path,
                        "line_number": node.lineno,
                    }
                    structure["functions"].append(func_info)

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append(
                            {
                                "module": alias.name,
                                "alias": alias.asname,
                                "type": "import",
                            }
                        )

                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        structure["imports"].append(
                            {
                                "module": node.module,
                                "name": alias.name,
                                "alias": alias.asname,
                                "type": "from_import",
                            }
                        )

            # Get module docstring
            if (
                tree.body
                and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Str)
            ):
                structure["module_docstring"] = tree.body[0].value.s

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")

        return structure

    def _calculate_file_complexity(self, content: str) -> float:
        """Calculate complexity score for a file."""
        # Simple complexity metrics
        lines = content.split("\n")
        non_empty_lines = [line for line in lines if line.strip()]

        complexity_indicators = [
            "class ",
            "def ",
            "if ",
            "for ",
            "while ",
            "try:",
            "except:",
            "with ",
        ]

        complexity_count = sum(
            sum(1 for line in non_empty_lines if indicator in line)
            for indicator in complexity_indicators
        )

        # Normalize by file length
        if len(non_empty_lines) > 0:
            return min(1.0, complexity_count / len(non_empty_lines) * 10)

        return 0.0

    def _get_section_priority(self, section: str) -> str:
        """Get priority level for a missing section."""
        high_priority = ["installation", "quick_start", "api_reference"]
        medium_priority = ["examples", "overview"]

        if section in high_priority:
            return "high"
        elif section in medium_priority:
            return "medium"
        else:
            return "low"

    def _get_gap_description(self, section: str) -> str:
        """Get description of what's missing for a section."""
        descriptions = {
            "installation": "Missing installation instructions and setup guide",
            "quick_start": "No quick start guide for new users",
            "api_reference": "API reference documentation not available",
            "examples": "Code examples and usage demonstrations missing",
            "configuration": "Configuration options not documented",
            "troubleshooting": "Troubleshooting guide not available",
            "overview": "Project overview and description missing",
        }

        return descriptions.get(section, f"Missing {section} documentation")

    def _estimate_generation_effort(self, section: str) -> str:
        """Estimate effort required to generate a section."""
        effort_map = {
            "installation": "low",
            "overview": "low",
            "quick_start": "medium",
            "examples": "medium",
            "api_reference": "high",
            "configuration": "medium",
            "troubleshooting": "high",
        }

        return effort_map.get(section, "medium")

    def _get_section_dependencies(self, section: str) -> list[str]:
        """Get dependencies for generating a section."""
        dependencies = {
            "quick_start": ["installation"],
            "examples": ["api_reference"],
            "troubleshooting": ["api_reference", "examples"],
            "configuration": ["api_reference"],
        }

        return dependencies.get(section, [])


class CodeStructureExtractor:
    """Extractor for analyzing code structure to generate API documentation."""

    def __init__(self):
        """Initialize the code structure extractor."""
        self.supported_languages = ["python", "javascript", "typescript"]

    def extract_structure(self, code_files: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Extract code structure from a list of code files.

        Args:
            code_files: List of code file dictionaries with 'path' and 'content'

        Returns:
            Extracted code structure with classes, functions, and modules
        """
        structure = {
            "classes": [],
            "functions": [],
            "modules": [],
            "imports": [],
            "constants": [],
            "total_files": len(code_files),
            "supported_files": 0,
        }

        for file_info in code_files:
            file_path = file_info.get("path", "")
            content = file_info.get("content", "")

            if not content:
                continue

            # Determine file type and extract structure
            if file_path.endswith(".py"):
                file_structure = self._extract_python_structure(content, file_path)
                structure["supported_files"] += 1
            elif file_path.endswith((".js", ".ts")):
                file_structure = self._extract_javascript_structure(content, file_path)
                structure["supported_files"] += 1
            else:
                continue  # Skip unsupported file types

            # Merge structures
            if file_structure:
                structure["classes"].extend(file_structure.get("classes", []))
                structure["functions"].extend(file_structure.get("functions", []))
                structure["imports"].extend(file_structure.get("imports", []))
                structure["constants"].extend(file_structure.get("constants", []))

                # Add module info
                module_info = {
                    "name": Path(file_path).stem,
                    "path": file_path,
                    "docstring": file_structure.get("module_docstring", ""),
                    "exports": file_structure.get("exports", []),
                    "language": "python" if file_path.endswith(".py") else "javascript",
                }
                structure["modules"].append(module_info)

        return structure

    def _extract_python_structure(self, content: str, file_path: str) -> dict[str, Any]:
        """Extract structure from Python code."""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "constants": [],
            "exports": [],
            "module_docstring": "",
        }

        try:
            tree = ast.parse(content)

            # Get module docstring
            if (
                tree.body
                and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, (ast.Str, ast.Constant))
            ):
                if isinstance(tree.body[0].value, ast.Str):
                    structure["module_docstring"] = tree.body[0].value.s
                else:  # ast.Constant for Python 3.8+
                    structure["module_docstring"] = tree.body[0].value.value

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_info = self._extract_class_info(node, file_path)
                    structure["classes"].append(class_info)

                elif isinstance(node, ast.FunctionDef):
                    func_info = self._extract_function_info(node, file_path)
                    structure["functions"].append(func_info)

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append(
                            {
                                "module": alias.name,
                                "alias": alias.asname,
                                "type": "import",
                                "line": node.lineno,
                            }
                        )

                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        structure["imports"].append(
                            {
                                "module": node.module,
                                "name": alias.name,
                                "alias": alias.asname,
                                "type": "from_import",
                                "line": node.lineno,
                            }
                        )

                elif isinstance(node, ast.Assign):
                    # Look for constants (uppercase variables)
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            structure["constants"].append(
                                {
                                    "name": target.id,
                                    "line": node.lineno,
                                    "file_path": file_path,
                                }
                            )

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error extracting Python structure from {file_path}: {e}")

        return structure

    def _extract_class_info(self, node: ast.ClassDef, file_path: str) -> dict[str, Any]:
        """Extract information about a class."""
        class_info = {
            "name": node.name,
            "docstring": ast.get_docstring(node) or "",
            "methods": [],
            "file_path": file_path,
            "line_number": node.lineno,
            "is_public": not node.name.startswith("_"),
            "base_classes": [self._get_name(base) for base in node.bases],
        }

        # Extract methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._extract_function_info(
                    item, file_path, is_method=True
                )
                class_info["methods"].append(method_info)

        return class_info

    def _extract_function_info(
        self, node: ast.FunctionDef, file_path: str, is_method: bool = False
    ) -> dict[str, Any]:
        """Extract information about a function or method."""
        func_info = {
            "name": node.name,
            "docstring": ast.get_docstring(node) or "",
            "args": [],
            "returns": None,
            "file_path": file_path,
            "line_number": node.lineno,
            "is_public": not node.name.startswith("_"),
            "is_method": is_method,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        }

        # Extract arguments
        for arg in node.args.args:
            arg_info = {
                "name": arg.arg,
                "annotation": self._get_annotation(arg.annotation)
                if arg.annotation
                else None,
            }
            func_info["args"].append(arg_info)

        # Extract return annotation
        if node.returns:
            func_info["returns"] = self._get_annotation(node.returns)

        return func_info

    def _extract_javascript_structure(
        self, content: str, file_path: str
    ) -> dict[str, Any]:
        """Extract structure from JavaScript/TypeScript code (simplified)."""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "constants": [],
            "exports": [],
            "module_docstring": "",
        }

        lines = content.split("\n")

        for i, line in enumerate(lines):
            line = line.strip()

            # Extract classes
            if line.startswith("class "):
                class_match = re.match(r"class\s+(\w+)", line)
                if class_match:
                    structure["classes"].append(
                        {
                            "name": class_match.group(1),
                            "docstring": "",
                            "methods": [],
                            "file_path": file_path,
                            "line_number": i + 1,
                            "is_public": True,
                        }
                    )

            # Extract functions
            elif "function " in line or "=>" in line:
                func_match = re.match(r"(?:function\s+)?(\w+)\s*\(", line)
                if func_match:
                    structure["functions"].append(
                        {
                            "name": func_match.group(1),
                            "docstring": "",
                            "args": [],
                            "file_path": file_path,
                            "line_number": i + 1,
                            "is_public": True,
                        }
                    )

            # Extract imports
            elif (
                line.startswith("import ")
                or line.startswith("const ")
                and "require(" in line
            ):
                structure["imports"].append({"line": i + 1, "statement": line})

        return structure

    def _get_name(self, node) -> str:
        """Get name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)

    def _get_annotation(self, node) -> str:
        """Get type annotation as string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return str(node)


class AIDocumentationGenerator:
    """AI-powered documentation generator for creating comprehensive docs from code."""

    def __init__(self):
        """Initialize the AI documentation generator."""
        pass

    async def generate_api_reference(
        self, documentation_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Generate comprehensive API reference from code structure.

        Args:
            documentation_data: Documentation data including code files

        Returns:
            Generated API reference documentation
        """
        try:
            code_files = documentation_data.get("code_files", [])
            library_name = documentation_data.get("library_name", "Library")

            # Extract code structure
            extractor = CodeStructureExtractor()
            structure = extractor.extract_structure(code_files)

            api_reference = {}

            # Generate documentation for each class
            for class_info in structure["classes"]:
                if class_info["is_public"]:  # Only document public classes
                    class_doc = await self._generate_class_documentation(
                        class_info, library_name
                    )
                    api_reference[class_info["name"]] = class_doc

            return {
                "api_reference": api_reference,
                "total_classes": len(
                    [c for c in structure["classes"] if c["is_public"]]
                ),
                "generation_method": "ai_enhanced",
            }

        except Exception as e:
            logger.error(f"Error generating API reference: {e}")
            return {"api_reference": {}, "error": str(e)}

    async def generate_examples(
        self, documentation_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate code examples based on the library structure."""
        try:
            code_files = documentation_data.get("code_files", [])
            library_name = documentation_data.get("library_name", "library")

            # Extract structure
            extractor = CodeStructureExtractor()
            structure = extractor.extract_structure(code_files)

            examples = []

            # Generate examples for main classes
            for class_info in structure["classes"][:2]:  # Top 2 classes
                if class_info["is_public"]:
                    example = await self._generate_class_example(
                        class_info, library_name
                    )
                    examples.append(example)

            return examples

        except Exception as e:
            logger.error(f"Error generating examples: {e}")
            return []

    async def generate_tutorial(
        self, documentation_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate a step-by-step tutorial for the library."""
        try:
            library_name = documentation_data.get("library_name", "Library")
            code_files = documentation_data.get("code_files", [])

            # Extract structure for tutorial content
            extractor = CodeStructureExtractor()
            structure = extractor.extract_structure(code_files)

            tutorial = {"title": f"Getting Started with {library_name}", "sections": []}

            # Section 1: Basic Usage
            if structure["classes"]:
                main_class = structure["classes"][0]
                tutorial["sections"].append(
                    {
                        "title": "Basic Usage",
                        "content": f'Learn how to use {main_class["name"]} for basic operations',
                        "code_example": f"from {library_name.lower()} import {main_class['name']}\nobj = {main_class['name']}()\nresult = obj.do_something('test')",
                    }
                )

            # Section 2: Advanced Features
            if len(structure["classes"]) > 1:
                tutorial["sections"].append(
                    {
                        "title": "Advanced Features",
                        "content": "Explore advanced functionality",
                        "code_example": "result = obj.advanced_feature(5, 3, mode='detailed')",
                    }
                )

            return tutorial

        except Exception as e:
            logger.error(f"Error generating tutorial: {e}")
            return {
                "title": "Tutorial Generation Failed",
                "sections": [],
                "error": str(e),
            }

    async def enhance_existing_docs(
        self, documentation_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Enhance existing sparse documentation with AI-generated content."""
        try:
            original_content = documentation_data.get("readme_content", "")

            # Analyze what's missing
            analyzer = DocumentationAnalyzer()
            analysis = analyzer.analyze_completeness(documentation_data)

            enhanced_content = {"generated_sections": {}, "improvements": []}

            # Generate missing sections
            for missing_section in analysis["missing_sections"]:
                if missing_section == "api_reference":
                    api_ref = await self.generate_api_reference(documentation_data)
                    enhanced_content["generated_sections"]["api_reference"] = api_ref
                    enhanced_content["improvements"].append(
                        "Generated comprehensive API reference"
                    )

                elif missing_section == "examples":
                    examples = await self.generate_examples(documentation_data)
                    enhanced_content["generated_sections"]["examples"] = examples
                    enhanced_content["improvements"].append(
                        "Added code examples and usage patterns"
                    )

            return {
                "original_content": original_content,
                "enhanced_content": enhanced_content,
                "improvements": enhanced_content["improvements"],
            }

        except Exception as e:
            logger.error(f"Error enhancing documentation: {e}")
            return {
                "original_content": documentation_data.get("readme_content", ""),
                "enhanced_content": {},
                "improvements": [],
                "error": str(e),
            }

    async def _generate_class_documentation(
        self, class_info: dict[str, Any], library_name: str
    ) -> dict[str, Any]:
        """Generate documentation for a single class."""
        class_name = class_info["name"]

        # Generate description
        if class_info["docstring"]:
            description = class_info["docstring"]
        else:
            description = f"Main class for {library_name} operations"

        # Generate method documentation
        methods = {}
        for method in class_info["methods"]:
            if method["is_public"]:
                method_doc = {
                    "description": method["docstring"]
                    or f"Perform {method['name']} operation",
                    "parameters": {
                        arg["name"]: f"Parameter {arg['name']}"
                        for arg in method["args"]
                        if arg["name"] != "self"
                    },
                    "returns": method.get("returns", "Operation result"),
                    "examples": [f"obj.{method['name']}()"],
                }
                methods[method["name"]] = method_doc

        return {"description": description, "methods": methods}

    async def _generate_class_example(
        self, class_info: dict[str, Any], library_name: str
    ) -> dict[str, Any]:
        """Generate usage example for a class."""
        class_name = class_info["name"]

        # Create basic usage example
        example_code = f"from {library_name.lower()} import {class_name}\n\n"
        example_code += f"# Create an instance\nobj = {class_name}()\n\n"

        # Add method calls for public methods
        public_methods = [
            m
            for m in class_info["methods"]
            if m["is_public"] and m["name"] != "__init__"
        ]
        if public_methods:
            method = public_methods[0]  # Use first public method
            example_code += f"# Use the main functionality\nresult = obj.{method['name']}()\nprint(result)"

        return {
            "title": f"{class_name} Usage Example",
            "description": f"Basic usage example for the {class_name} class",
            "code": example_code,
            "language": "python",
        }

    async def _call_ai_service(
        self, prompt: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Mock AI service call for generating documentation content.
        In a real implementation, this would call an actual AI service.
        """
        # This is a mock implementation for testing
        library_name = context.get("library_name", "Library")

        if "api_reference" in prompt.lower():
            return {
                "api_reference": {
                    "AwesomeClass": {
                        "description": "Main class for performing awesome operations on data",
                        "methods": {
                            "__init__": {
                                "description": "Initialize AwesomeClass with optional configuration",
                                "parameters": {
                                    "config": "Optional dictionary for configuration settings"
                                },
                                "examples": [
                                    "obj = AwesomeClass()",
                                    "obj = AwesomeClass({'debug': True})",
                                ],
                            },
                            "do_something": {
                                "description": "Process input data and return formatted result",
                                "parameters": {
                                    "data": "Input data to process (any type)"
                                },
                                "returns": "Processed data as string",
                                "examples": [
                                    "result = obj.do_something('hello')",
                                    "result = obj.do_something([1, 2, 3])",
                                ],
                            },
                        },
                    }
                }
            }

        return {"generated_content": f"Generated content for {library_name}"}

    async def _call_ai_service(
        self, prompt: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Mock AI service call for generating documentation content.
        In a real implementation, this would call an actual AI service.
        """
        # This is a mock implementation for testing
        # In production, this would integrate with OpenAI, Claude, or other AI services

        library_name = context.get("library_name", "Library")

        if "api_reference" in prompt.lower():
            return {
                "api_reference": {
                    "AwesomeClass": {
                        "description": "Main class for performing awesome operations on data",
                        "methods": {
                            "__init__": {
                                "description": "Initialize AwesomeClass with optional configuration",
                                "parameters": {
                                    "config": "Optional dictionary for configuration settings"
                                },
                                "examples": [
                                    "obj = AwesomeClass()",
                                    "obj = AwesomeClass({'debug': True})",
                                ],
                            },
                            "do_something": {
                                "description": "Process input data and return formatted result",
                                "parameters": {
                                    "data": "Input data to process (any type)"
                                },
                                "returns": "Processed data as string",
                                "examples": [
                                    "result = obj.do_something('hello')",
                                    "result = obj.do_something([1, 2, 3])",
                                ],
                            },
                        },
                    }
                }
            }

        elif "tutorial" in prompt.lower():
            return {
                "tutorial": {
                    "title": f"Getting Started with {library_name}",
                    "sections": [
                        {
                            "title": "Basic Usage",
                            "content": f"Learn how to use {library_name} for basic operations",
                            "code_example": f"from {library_name.lower()} import AwesomeClass\nobj = AwesomeClass()\nresult = obj.do_something('test')",
                        },
                        {
                            "title": "Advanced Features",
                            "content": "Explore advanced functionality",
                            "code_example": "result = obj.advanced_feature(5, 3, mode='detailed')",
                        },
                    ],
                }
            }

        else:
            return {"generated_content": f"Generated content for {library_name}"}
