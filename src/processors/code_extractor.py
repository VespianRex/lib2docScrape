#!/usr/bin/env python3
"""
Code Example Extractor for Documentation Processing

Extracts and analyzes code examples from documentation content.
"""

import ast
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class CodeExampleExtractor:
    """Extractor for finding and analyzing code examples in documentation."""

    def __init__(self):
        """Initialize the code example extractor."""
        self.language_patterns = {
            "python": [
                r"```python\n(.*?)\n```",
                r"```py\n(.*?)\n```",
                r".. code-block:: python\n\n(.*?)(?=\n\n|\n\.\.|$)",
                r">>> (.*?)(?=\n>>>|\n\.\.\.|$)",
                r":::\s*python\n(.*?)\n:::",
            ],
            "javascript": [
                r"```javascript\n(.*?)\n```",
                r"```js\n(.*?)\n```",
                r".. code-block:: javascript\n\n(.*?)(?=\n\n|\n\.\.|$)",
                r":::\s*javascript\n(.*?)\n:::",
            ],
            "bash": [
                r"```bash\n(.*?)\n```",
                r"```shell\n(.*?)\n```",
                r"```sh\n(.*?)\n```",
                r"\$ (.*?)(?=\n\$|\n[^$]|$)",
            ],
            "generic": [
                r"```\n(.*?)\n```",
                r"`([^`\n]+)`",
                r"    (.*?)(?=\n\S|\n\n|$)",  # Indented code blocks
            ],
        }

        self.code_quality_indicators = {
            "good": [
                "import",
                "def ",
                "class ",
                "try:",
                "except:",
                "with ",
                "if __name__",
                "docstring",
                "type hint",
                "async def",
            ],
            "basic": ["print(", "input(", "= ", "for ", "while ", "if "],
        }

    def extract_examples(
        self, documentation_content: dict[str, dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Extract code examples from documentation content.

        Args:
            documentation_content: Dictionary mapping library names to their documentation

        Returns:
            Dictionary mapping library names to lists of extracted code examples
        """
        try:
            extracted_examples = {}

            for library_name, doc_data in documentation_content.items():
                logger.info(f"Extracting code examples from {library_name}")

                examples = []

                # Extract from main content
                if "content" in doc_data:
                    content_examples = self._extract_from_text(doc_data["content"])
                    examples.extend(content_examples)

                # Extract from sections
                if "sections" in doc_data:
                    for section in doc_data["sections"]:
                        if isinstance(section, dict):
                            section_content = section.get("content", "")
                            section_title = section.get("title", "Unknown Section")
                            section_examples = self._extract_from_text(
                                section_content, section_title
                            )
                            examples.extend(section_examples)
                        elif isinstance(section, str):
                            section_examples = self._extract_from_text(section)
                            examples.extend(section_examples)

                # Extract from existing code_examples field
                if "code_examples" in doc_data:
                    for example in doc_data["code_examples"]:
                        if isinstance(example, str):
                            examples.append(
                                {
                                    "code": example,
                                    "language": self._detect_language(example),
                                    "description": "Code example from documentation",
                                    "source": "code_examples_field",
                                    "quality_score": self._assess_code_quality(example),
                                }
                            )
                        elif isinstance(example, dict):
                            examples.append(
                                {
                                    "code": example.get("code", ""),
                                    "language": example.get(
                                        "language",
                                        self._detect_language(example.get("code", "")),
                                    ),
                                    "description": example.get(
                                        "description", "Code example"
                                    ),
                                    "source": "code_examples_field",
                                    "quality_score": self._assess_code_quality(
                                        example.get("code", "")
                                    ),
                                }
                            )

                # Remove duplicates and sort by quality
                unique_examples = self._deduplicate_examples(examples)
                sorted_examples = sorted(
                    unique_examples, key=lambda x: x["quality_score"], reverse=True
                )

                extracted_examples[library_name] = sorted_examples
                logger.info(
                    f"Extracted {len(sorted_examples)} code examples from {library_name}"
                )

            return extracted_examples

        except Exception as e:
            logger.error(f"Error extracting code examples: {e}")
            return {}

    def analyze_code_patterns(self, examples: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze patterns in extracted code examples.

        Args:
            examples: List of code examples

        Returns:
            Analysis of code patterns and statistics
        """
        try:
            if not examples:
                return {"error": "No examples to analyze"}

            # Language distribution
            languages = [ex["language"] for ex in examples]
            language_counts = {}
            for lang in languages:
                language_counts[lang] = language_counts.get(lang, 0) + 1

            # Quality distribution
            quality_scores = [ex["quality_score"] for ex in examples]
            avg_quality = sum(quality_scores) / len(quality_scores)

            # Common patterns
            all_code = " ".join([ex["code"] for ex in examples])
            common_imports = self._find_common_imports(examples)
            common_functions = self._find_common_functions(examples)

            # Complexity analysis
            complexity_analysis = self._analyze_complexity(examples)

            return {
                "total_examples": len(examples),
                "language_distribution": language_counts,
                "average_quality_score": round(avg_quality, 2),
                "quality_distribution": {
                    "high": len([ex for ex in examples if ex["quality_score"] > 0.7]),
                    "medium": len(
                        [ex for ex in examples if 0.3 <= ex["quality_score"] <= 0.7]
                    ),
                    "low": len([ex for ex in examples if ex["quality_score"] < 0.3]),
                },
                "common_imports": common_imports,
                "common_functions": common_functions,
                "complexity_analysis": complexity_analysis,
                "recommendations": self._generate_recommendations(examples),
            }

        except Exception as e:
            logger.error(f"Error analyzing code patterns: {e}")
            return {"error": str(e)}

    def _extract_from_text(self, text: str, context: str = "") -> list[dict[str, Any]]:
        """Extract code examples from a text string."""
        examples = []

        # Try each language pattern
        for language, patterns in self.language_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)

                for match in matches:
                    if isinstance(match, tuple):
                        code = match[0] if match else ""
                    else:
                        code = match

                    code = code.strip()
                    if len(code) > 10:  # Filter out very short snippets
                        examples.append(
                            {
                                "code": code,
                                "language": language
                                if language != "generic"
                                else self._detect_language(code),
                                "description": self._generate_description(
                                    code, context
                                ),
                                "source": f"{context} ({language} pattern)"
                                if context
                                else f"{language} pattern",
                                "quality_score": self._assess_code_quality(code),
                            }
                        )

        return examples

    def _detect_language(self, code: str) -> str:
        """Detect the programming language of a code snippet."""
        code_lower = code.lower()

        # Python indicators
        python_indicators = [
            "import ",
            "def ",
            "class ",
            "print(",
            "if __name__",
            "elif ",
            "from ",
        ]
        if any(indicator in code for indicator in python_indicators):
            return "python"

        # JavaScript indicators
        js_indicators = [
            "function ",
            "var ",
            "let ",
            "const ",
            "console.log",
            "=>",
            "require(",
        ]
        if any(indicator in code for indicator in js_indicators):
            return "javascript"

        # Bash indicators
        bash_indicators = [
            "#!/bin/bash",
            "echo ",
            "cd ",
            "ls ",
            "grep ",
            "awk ",
            "sed ",
        ]
        if any(indicator in code for indicator in bash_indicators):
            return "bash"

        # SQL indicators
        sql_indicators = ["select ", "from ", "where ", "insert ", "update ", "delete "]
        if any(indicator in code_lower for indicator in sql_indicators):
            return "sql"

        return "unknown"

    def _assess_code_quality(self, code: str) -> float:
        """Assess the quality of a code example."""
        if not code or len(code) < 10:
            return 0.0

        score = 0.0

        # Length factor (moderate length is better)
        length = len(code)
        if 50 <= length <= 500:
            score += 0.3
        elif 20 <= length <= 1000:
            score += 0.2

        # Good practices
        good_count = sum(
            1 for indicator in self.code_quality_indicators["good"] if indicator in code
        )
        score += min(good_count * 0.1, 0.4)

        # Basic functionality
        basic_count = sum(
            1
            for indicator in self.code_quality_indicators["basic"]
            if indicator in code
        )
        score += min(basic_count * 0.05, 0.2)

        # Comments and documentation
        if "#" in code or '"""' in code or "'''" in code:
            score += 0.1

        # Error handling
        if "try:" in code or "except" in code:
            score += 0.1

        # Syntax validity (for Python)
        if self._detect_language(code) == "python":
            try:
                ast.parse(code)
                score += 0.2  # Bonus for valid syntax
            except:
                score -= 0.1  # Penalty for invalid syntax

        return min(score, 1.0)

    def _generate_description(self, code: str, context: str = "") -> str:
        """Generate a description for a code example."""
        language = self._detect_language(code)

        # Basic description based on content
        if "import" in code and language == "python":
            description = "Python import and usage example"
        elif "def " in code:
            description = "Function definition example"
        elif "class " in code:
            description = "Class definition example"
        elif "print(" in code:
            description = "Basic output example"
        elif "for " in code or "while " in code:
            description = "Loop example"
        elif "if " in code:
            description = "Conditional logic example"
        else:
            description = f"{language.title()} code example"

        # Add context if available
        if context:
            description = f"{description} from {context}"

        return description

    def _deduplicate_examples(
        self, examples: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Remove duplicate code examples."""
        seen_codes = set()
        unique_examples = []

        for example in examples:
            code_normalized = re.sub(r"\s+", " ", example["code"]).strip()
            if code_normalized not in seen_codes:
                seen_codes.add(code_normalized)
                unique_examples.append(example)

        return unique_examples

    def _find_common_imports(
        self, examples: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find common import statements across examples."""
        import_counts = {}

        for example in examples:
            if example["language"] == "python":
                # Find import statements
                imports = re.findall(
                    r"(?:from\s+\S+\s+)?import\s+([^\n;]+)", example["code"]
                )
                for imp in imports:
                    imp = imp.strip()
                    import_counts[imp] = import_counts.get(imp, 0) + 1

        # Sort by frequency
        sorted_imports = sorted(import_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"import": imp, "count": count} for imp, count in sorted_imports[:10]]

    def _find_common_functions(
        self, examples: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find commonly used functions across examples."""
        function_counts = {}

        for example in examples:
            # Find function calls (simple pattern)
            functions = re.findall(r"(\w+)\s*\(", example["code"])
            for func in functions:
                if len(func) > 2:  # Filter out very short names
                    function_counts[func] = function_counts.get(func, 0) + 1

        # Sort by frequency
        sorted_functions = sorted(
            function_counts.items(), key=lambda x: x[1], reverse=True
        )
        return [
            {"function": func, "count": count} for func, count in sorted_functions[:10]
        ]

    def _analyze_complexity(self, examples: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze complexity of code examples."""
        complexity_scores = []

        for example in examples:
            code = example["code"]
            complexity = 0

            # Count complexity indicators
            complexity += len(re.findall(r"\bif\b", code))
            complexity += len(re.findall(r"\bfor\b", code))
            complexity += len(re.findall(r"\bwhile\b", code))
            complexity += len(re.findall(r"\btry\b", code))
            complexity += len(re.findall(r"\bdef\b", code))
            complexity += len(re.findall(r"\bclass\b", code))

            # Normalize by code length
            normalized_complexity = complexity / max(len(code.split("\n")), 1)
            complexity_scores.append(normalized_complexity)

        if complexity_scores:
            return {
                "average_complexity": round(
                    sum(complexity_scores) / len(complexity_scores), 2
                ),
                "max_complexity": round(max(complexity_scores), 2),
                "min_complexity": round(min(complexity_scores), 2),
                "complexity_distribution": {
                    "simple": len([s for s in complexity_scores if s < 0.5]),
                    "moderate": len([s for s in complexity_scores if 0.5 <= s < 1.5]),
                    "complex": len([s for s in complexity_scores if s >= 1.5]),
                },
            }
        else:
            return {"average_complexity": 0, "max_complexity": 0, "min_complexity": 0}

    def _generate_recommendations(self, examples: list[dict[str, Any]]) -> list[str]:
        """Generate recommendations based on code analysis."""
        recommendations = []

        if not examples:
            return ["No code examples found to analyze"]

        # Quality recommendations
        low_quality_count = len([ex for ex in examples if ex["quality_score"] < 0.3])
        if low_quality_count > len(examples) * 0.5:
            recommendations.append(
                "Consider improving code example quality with better documentation and error handling"
            )

        # Language diversity
        languages = set(ex["language"] for ex in examples)
        if len(languages) == 1:
            recommendations.append(
                "Consider adding examples in multiple programming languages"
            )

        # Complexity recommendations
        avg_quality = sum(ex["quality_score"] for ex in examples) / len(examples)
        if avg_quality < 0.5:
            recommendations.append(
                "Add more comprehensive examples with proper structure and comments"
            )

        # Coverage recommendations
        if len(examples) < 3:
            recommendations.append(
                "Add more code examples to better demonstrate usage patterns"
            )

        return recommendations
