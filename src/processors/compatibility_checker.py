#!/usr/bin/env python3
"""
Compatibility Checker for Multi-Library Projects

Checks version compatibility and potential conflicts between dependencies.
"""

from typing import Any


class CompatibilityChecker:
    """Checker for analyzing compatibility between library dependencies."""

    def __init__(self):
        """Initialize the compatibility checker."""
        self.known_conflicts = {
            "python": {
                ("requests", "urllib3"): {
                    "type": "version_dependency",
                    "description": "requests depends on specific urllib3 versions",
                },
                ("fastapi", "starlette"): {
                    "type": "version_dependency",
                    "description": "FastAPI depends on specific Starlette versions",
                },
                ("django", "flask"): {
                    "type": "framework_conflict",
                    "description": "Multiple web frameworks may cause conflicts",
                },
            },
            "javascript": {
                ("react", "vue"): {
                    "type": "framework_conflict",
                    "description": "Multiple frontend frameworks in same project",
                },
                ("webpack", "vite"): {
                    "type": "build_tool_conflict",
                    "description": "Multiple build tools may cause configuration conflicts",
                },
            },
        }

        self.ecosystem_rules = {
            "python": {
                "async_sync_mixing": [
                    "asyncio",
                    "aiohttp",
                    "fastapi",
                    "starlette",  # async libraries
                ],
                "web_frameworks": ["django", "flask", "fastapi", "tornado"],
                "testing_frameworks": ["pytest", "unittest", "nose"],
            },
            "javascript": {
                "frontend_frameworks": ["react", "vue", "angular", "svelte"],
                "build_tools": ["webpack", "vite", "rollup", "parcel"],
                "testing_frameworks": ["jest", "mocha", "jasmine", "vitest"],
            },
        }

    def check_compatibility(self, dependencies: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Check compatibility between a list of dependencies.

        Args:
            dependencies: List of dependency dictionaries

        Returns:
            Compatibility report with conflicts, warnings, and recommendations
        """
        report = {
            "compatible": True,
            "conflicts": [],
            "warnings": [],
            "recommendations": [],
            "version_conflicts": [],
            "ecosystem_issues": [],
        }

        # Group dependencies by ecosystem
        by_ecosystem = self._group_by_ecosystem(dependencies)

        # Check each ecosystem
        for ecosystem, deps in by_ecosystem.items():
            ecosystem_report = self._check_ecosystem_compatibility(ecosystem, deps)

            # Merge reports
            report["conflicts"].extend(ecosystem_report["conflicts"])
            report["warnings"].extend(ecosystem_report["warnings"])
            report["recommendations"].extend(ecosystem_report["recommendations"])
            report["version_conflicts"].extend(ecosystem_report["version_conflicts"])
            report["ecosystem_issues"].extend(ecosystem_report["ecosystem_issues"])

        # Check cross-ecosystem compatibility
        cross_ecosystem_issues = self._check_cross_ecosystem_compatibility(by_ecosystem)
        report["ecosystem_issues"].extend(cross_ecosystem_issues)

        # Determine overall compatibility
        report["compatible"] = (
            len(report["conflicts"]) == 0 and len(report["version_conflicts"]) == 0
        )

        return report

    def _group_by_ecosystem(
        self, dependencies: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Group dependencies by their ecosystem (python, javascript, etc.)."""
        by_ecosystem = {}

        for dep in dependencies:
            ecosystem = dep.get("type", "unknown")
            if ecosystem not in by_ecosystem:
                by_ecosystem[ecosystem] = []
            by_ecosystem[ecosystem].append(dep)

        return by_ecosystem

    def _check_ecosystem_compatibility(
        self, ecosystem: str, dependencies: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Check compatibility within a single ecosystem."""
        report = {
            "conflicts": [],
            "warnings": [],
            "recommendations": [],
            "version_conflicts": [],
            "ecosystem_issues": [],
        }

        # Check known conflicts
        conflicts = self._check_known_conflicts(ecosystem, dependencies)
        report["conflicts"].extend(conflicts)

        # Check version conflicts
        version_conflicts = self._check_version_conflicts(dependencies)
        report["version_conflicts"].extend(version_conflicts)

        # Check ecosystem-specific rules
        ecosystem_issues = self._check_ecosystem_rules(ecosystem, dependencies)
        report["ecosystem_issues"].extend(ecosystem_issues)

        return report

    def _check_known_conflicts(
        self, ecosystem: str, dependencies: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Check for known conflicts between specific libraries."""
        conflicts = []

        if ecosystem not in self.known_conflicts:
            return conflicts

        dep_names = [dep["name"] for dep in dependencies]

        for (lib1, lib2), conflict_info in self.known_conflicts[ecosystem].items():
            if lib1 in dep_names and lib2 in dep_names:
                conflicts.append(
                    {
                        "type": conflict_info["type"],
                        "libraries": [lib1, lib2],
                        "description": conflict_info["description"],
                        "severity": "high"
                        if "conflict" in conflict_info["type"]
                        else "medium",
                    }
                )

        return conflicts

    def _check_version_conflicts(
        self, dependencies: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Check for version specification conflicts."""
        conflicts = []

        # Group by library name to check for duplicate dependencies
        by_name = {}
        for dep in dependencies:
            name = dep["name"]
            if name not in by_name:
                by_name[name] = []
            by_name[name].append(dep)

        # Check for conflicting version specifications
        for name, deps in by_name.items():
            if len(deps) > 1:
                version_specs = []
                for dep in deps:
                    version_spec = dep.get("version", "")
                    if version_spec:
                        version_specs.append(version_spec)

                if len(set(version_specs)) > 1:
                    conflicts.append(
                        {
                            "type": "version_conflict",
                            "library": name,
                            "conflicting_versions": version_specs,
                            "description": f"Multiple version specifications for {name}",
                            "severity": "high",
                        }
                    )

        return conflicts

    def _check_ecosystem_rules(
        self, ecosystem: str, dependencies: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Check ecosystem-specific compatibility rules."""
        issues = []

        if ecosystem not in self.ecosystem_rules:
            return issues

        rules = self.ecosystem_rules[ecosystem]
        dep_names = [dep["name"] for dep in dependencies]

        # Check for multiple frameworks
        for rule_name, framework_list in rules.items():
            if "framework" in rule_name:
                found_frameworks = [
                    name for name in dep_names if name in framework_list
                ]
                if len(found_frameworks) > 1:
                    issues.append(
                        {
                            "type": "multiple_frameworks",
                            "category": rule_name,
                            "libraries": found_frameworks,
                            "description": f'Multiple {rule_name} detected: {", ".join(found_frameworks)}',
                            "severity": "medium",
                        }
                    )

        return issues

    def _check_cross_ecosystem_compatibility(
        self, by_ecosystem: dict[str, list[dict[str, Any]]]
    ) -> list[dict[str, Any]]:
        """Check compatibility issues across different ecosystems."""
        issues = []

        ecosystems = list(by_ecosystem.keys())

        # Check for potential integration issues
        if "python" in ecosystems and "javascript" in ecosystems:
            python_deps = [dep["name"] for dep in by_ecosystem["python"]]
            js_deps = [dep["name"] for dep in by_ecosystem["javascript"]]

            # Check for common integration patterns
            has_web_framework = any(
                fw in python_deps for fw in ["django", "flask", "fastapi"]
            )
            has_frontend_framework = any(
                fw in js_deps for fw in ["react", "vue", "angular"]
            )

            if has_web_framework and has_frontend_framework:
                issues.append(
                    {
                        "type": "integration_opportunity",
                        "ecosystems": ["python", "javascript"],
                        "description": "Backend and frontend frameworks detected - consider API integration",
                        "severity": "info",
                    }
                )

        return issues

    def get_compatibility_score(self, dependencies: list[dict[str, Any]]) -> float:
        """
        Calculate a compatibility score (0-1) for the dependency set.

        Args:
            dependencies: List of dependency dictionaries

        Returns:
            Compatibility score between 0 (incompatible) and 1 (fully compatible)
        """
        report = self.check_compatibility(dependencies)

        # Calculate score based on issues found
        score = 1.0

        # Deduct for conflicts
        score -= len(report["conflicts"]) * 0.3
        score -= len(report["version_conflicts"]) * 0.4
        score -= (
            len(
                [
                    issue
                    for issue in report["ecosystem_issues"]
                    if issue["severity"] == "high"
                ]
            )
            * 0.2
        )
        score -= (
            len(
                [
                    issue
                    for issue in report["ecosystem_issues"]
                    if issue["severity"] == "medium"
                ]
            )
            * 0.1
        )

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))

    def suggest_resolutions(
        self, compatibility_report: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        Suggest resolutions for compatibility issues.

        Args:
            compatibility_report: Report from check_compatibility()

        Returns:
            List of suggested resolutions
        """
        suggestions = []

        # Suggest resolutions for version conflicts
        for conflict in compatibility_report["version_conflicts"]:
            suggestions.append(
                {
                    "issue_type": "version_conflict",
                    "library": conflict["library"],
                    "suggestion": f'Unify version specification for {conflict["library"]}',
                    "action": "Choose a single version specification that satisfies all requirements",
                }
            )

        # Suggest resolutions for framework conflicts
        for issue in compatibility_report["ecosystem_issues"]:
            if issue["type"] == "multiple_frameworks":
                suggestions.append(
                    {
                        "issue_type": "multiple_frameworks",
                        "category": issue["category"],
                        "suggestion": f'Consider using only one {issue["category"]}',
                        "action": f'Choose between: {", ".join(issue["libraries"])}',
                    }
                )

        return suggestions
