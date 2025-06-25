#!/usr/bin/env python3
"""
Test Performance Analysis Script

This script runs all tests, records execution times, identifies the slowest tests,
and analyzes potential causes for slowness (setup errors, network calls, etc.).
"""

import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional


class TestPerformanceAnalyzer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.results_file = self.project_root / "test_performance_results.json"

    def run_tests_with_timing(self) -> dict:
        """Run all tests and collect detailed timing information."""
        print("🚀 Running all tests with detailed timing...")

        # Create a temporary JSON file for pytest results
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json_file = f.name

        try:
            # Run pytest with durations but no JSON reporting dependency
            cmd = [
                "uv",
                "run",
                "pytest",
                "--durations=0",  # Show all durations
                "--tb=short",  # Short traceback
                "-v",  # Verbose to get test names
                "--disable-warnings",  # Disable warnings for cleaner output
                "tests/",
            ]

            print(f"Running command: {' '.join(cmd)}")
            start_time = time.time()

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
            )

            total_time = time.time() - start_time

            # Parse durations from stdout
            durations = self._parse_durations_from_output(result.stdout)

            return {
                "total_time": total_time,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_results": {},  # No JSON results for now
                "durations": durations,
            }

        except subprocess.TimeoutExpired:
            print("❌ Tests timed out after 30 minutes!")
            return {"error": "timeout", "total_time": 1800}
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return {"error": str(e)}
        finally:
            # Clean up temp file
            if os.path.exists(json_file):
                os.unlink(json_file)

    def _parse_durations_from_output(self, output: str) -> list[tuple[str, float, str]]:
        """Parse test durations from pytest output."""
        durations = []

        # Look for duration lines like "0.12s call     tests/test_file.py::test_name"
        duration_pattern = r"(\d+\.\d+)s\s+(\w+)\s+(tests/[^:]+::[^\s]+)"

        for line in output.split("\n"):
            match = re.search(duration_pattern, line)
            if match:
                duration = float(match.group(1))
                phase = match.group(2)  # call, setup, teardown
                test_name = match.group(3)
                durations.append((test_name, duration, phase))

        return durations

    def analyze_slow_tests(self, results: dict) -> list[dict]:
        """Analyze the slowest tests and identify potential causes."""
        print("\n📊 Analyzing slow tests...")

        # Extract and sort test durations
        durations = results.get("durations", [])
        if not durations:
            print("⚠️  No duration data found")
            return []

        # Group by test name and sum all phases (setup + call + teardown)
        test_totals = {}
        for test_name, duration, phase in durations:
            if test_name not in test_totals:
                test_totals[test_name] = {"total": 0, "phases": {}}
            test_totals[test_name]["total"] += duration
            test_totals[test_name]["phases"][phase] = duration

        # Sort by total time and get top 20
        sorted_tests = sorted(
            test_totals.items(), key=lambda x: x[1]["total"], reverse=True
        )[:20]

        # Analyze each slow test
        analyzed_tests = []
        for test_name, timing_data in sorted_tests:
            analysis = self._analyze_single_test(test_name, timing_data)
            analyzed_tests.append(analysis)

        return analyzed_tests

    def _analyze_single_test(self, test_name: str, timing_data: dict) -> dict:
        """Analyze a single test to identify potential performance issues."""
        total_time = timing_data["total"]
        phases = timing_data["phases"]

        # Extract file path and test function name
        if "::" in test_name:
            file_path, test_func = test_name.rsplit("::", 1)
        else:
            file_path, test_func = test_name, "unknown"

        # Read the test file to analyze the code
        potential_issues = []
        test_code = self._read_test_code(file_path, test_func)

        if test_code:
            potential_issues = self._identify_potential_issues(test_code)

        # Categorize the slowness
        category = self._categorize_slowness(total_time, phases, potential_issues)

        return {
            "test_name": test_name,
            "file_path": file_path,
            "function_name": test_func,
            "total_time": total_time,
            "phases": phases,
            "potential_issues": potential_issues,
            "category": category,
            "code_snippet": test_code[:500] + "..."
            if test_code and len(test_code) > 500
            else test_code,
        }

    def _read_test_code(self, file_path: str, test_func: str) -> Optional[str]:
        """Read the code for a specific test function."""
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return None

            with open(full_path) as f:
                content = f.read()

            # Find the test function
            pattern = rf"(async\s+)?def\s+{re.escape(test_func)}\s*\([^)]*\):"
            match = re.search(pattern, content)
            if not match:
                return None

            # Extract the function body (simplified - just get next few lines)
            start_pos = match.start()
            lines = content[start_pos:].split("\n")

            # Get the function and its body (until next function or class)
            function_lines = [lines[0]]  # Function definition
            indent_level = None

            for line in lines[1:]:
                if line.strip() == "":
                    function_lines.append(line)
                    continue

                # Determine initial indent level
                if indent_level is None and line.strip():
                    indent_level = len(line) - len(line.lstrip())

                # If we hit a line with same or less indentation (and it's not empty),
                # we've reached the end of the function
                if line.strip() and indent_level is not None:
                    current_indent = len(line) - len(line.lstrip())
                    if current_indent <= indent_level and (
                        line.startswith("def ")
                        or line.startswith("class ")
                        or line.startswith("async def ")
                    ):
                        break

                function_lines.append(line)

                # Stop after 50 lines to avoid huge outputs
                if len(function_lines) > 50:
                    function_lines.append("    # ... (truncated)")
                    break

            return "\n".join(function_lines)

        except Exception as e:
            return f"Error reading code: {e}"

    def _identify_potential_issues(self, code: str) -> list[str]:
        """Identify potential performance issues in test code."""
        issues = []

        # Check for network-related calls
        network_patterns = [
            (r"requests\.(get|post|put|delete)", "HTTP requests"),
            (r"aiohttp\.(get|post|put|delete)", "Async HTTP requests"),
            (r"urllib\.request", "urllib HTTP requests"),
            (r"DuckDuckGoSearch|duckduckgo", "DuckDuckGo search calls"),
            (r"\.search\(", "Search operations"),
            (r"httpx\.(get|post|put|delete)", "HTTPX requests"),
        ]

        for pattern, description in network_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(description)

        # Check for sleep/delay calls
        sleep_patterns = [
            (r"time\.sleep\(", "time.sleep() calls"),
            (r"asyncio\.sleep\(", "asyncio.sleep() calls"),
            (r"await.*sleep\(", "Async sleep calls"),
            (r"\.sleep\(", "Generic sleep calls"),
        ]

        for pattern, description in sleep_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(description)

        # Check for file I/O operations
        io_patterns = [
            (r"open\(.*[\'\"]\w+[\'\"]\)", "File operations"),
            (r"with\s+open\(", "File context managers"),
            (r"\.read\(\)|\.write\(", "File read/write operations"),
        ]

        for pattern, description in io_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(description)

        # Check for database operations
        db_patterns = [
            (r"sqlite3|psycopg2|pymongo", "Database connections"),
            (r"\.execute\(.*SELECT|INSERT|UPDATE|DELETE", "SQL operations"),
        ]

        for pattern, description in db_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(description)

        # Check for browser automation
        browser_patterns = [
            (r"playwright|selenium", "Browser automation"),
            (r"\.goto\(|\.click\(|\.fill\(", "Browser interactions"),
        ]

        for pattern, description in browser_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(description)

        # Check for large data processing
        data_patterns = [
            (r"for.*in.*range\(\d{3,}", "Large loops"),
            (r"\.read_csv\(|\.to_csv\(", "CSV processing"),
            (r"json\.load.*large|json\.dump.*large", "Large JSON processing"),
        ]

        for pattern, description in data_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(description)

        # Check for subprocess calls
        subprocess_patterns = [
            (r"subprocess\.(run|call|Popen)", "Subprocess execution"),
            (r"os\.system\(", "OS system calls"),
        ]

        for pattern, description in subprocess_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(description)

        return list(set(issues))  # Remove duplicates

    def _categorize_slowness(
        self, total_time: float, phases: dict, issues: list[str]
    ) -> str:
        """Categorize the type of slowness."""
        setup_time = phases.get("setup", 0)
        call_time = phases.get("call", 0)
        teardown_time = phases.get("teardown", 0)

        # If setup/teardown takes significant time
        if setup_time > call_time * 2:
            return "SETUP_HEAVY"
        elif teardown_time > call_time * 2:
            return "TEARDOWN_HEAVY"

        # Based on identified issues
        if any("HTTP" in issue or "search" in issue.lower() for issue in issues):
            return "NETWORK_DEPENDENT"
        elif any("sleep" in issue.lower() for issue in issues):
            return "ARTIFICIAL_DELAYS"
        elif any(
            "File" in issue or "CSV" in issue or "JSON" in issue for issue in issues
        ):
            return "IO_INTENSIVE"
        elif any("Database" in issue or "SQL" in issue for issue in issues):
            return "DATABASE_DEPENDENT"
        elif any("Browser" in issue for issue in issues):
            return "BROWSER_AUTOMATION"
        elif any(
            "Subprocess" in issue or "system" in issue.lower() for issue in issues
        ):
            return "SUBPROCESS_HEAVY"
        elif total_time > 5:
            return "INHERENTLY_SLOW"
        elif total_time > 1:
            return "MODERATELY_SLOW"
        else:
            return "FAST"

    def generate_report(self, results: dict, analyzed_tests: list[dict]) -> str:
        """Generate a comprehensive performance report."""
        report = []
        report.append("=" * 80)
        report.append("🔍 TEST PERFORMANCE ANALYSIS REPORT")
        report.append("=" * 80)

        # Overall statistics
        total_time = results.get("total_time", 0)
        return_code = results.get("return_code", -1)

        report.append("\n📈 OVERALL STATISTICS:")
        report.append(f"   Total execution time: {total_time:.2f} seconds")
        report.append(f"   Return code: {return_code}")
        report.append(f"   Status: {'✅ PASSED' if return_code == 0 else '❌ FAILED'}")

        if analyzed_tests:
            report.append("\n🐌 TOP 20 SLOWEST TESTS:")
            report.append("-" * 80)

            # Group by category
            categories = {}
            for test in analyzed_tests:
                category = test["category"]
                if category not in categories:
                    categories[category] = []
                categories[category].append(test)

            # Print summary by category
            report.append("\n📊 SLOWNESS CATEGORIES:")
            for category, tests in sorted(
                categories.items(), key=lambda x: len(x[1]), reverse=True
            ):
                total_category_time = sum(t["total_time"] for t in tests)
                report.append(
                    f"   {category}: {len(tests)} tests ({total_category_time:.2f}s total)"
                )

            # Detailed test information
            report.append("\n📋 DETAILED TEST ANALYSIS:")
            report.append("-" * 80)

            for i, test in enumerate(analyzed_tests, 1):
                report.append(f"\n{i:2d}. {test['test_name']}")
                report.append(f"    ⏱️  Total time: {test['total_time']:.3f}s")
                report.append(f"    📁 File: {test['file_path']}")
                report.append(f"    🏷️  Category: {test['category']}")

                # Phase breakdown
                phases = test["phases"]
                if phases:
                    phase_info = []
                    for phase, time_val in phases.items():
                        phase_info.append(f"{phase}={time_val:.3f}s")
                    report.append(f"    🔄 Phases: {', '.join(phase_info)}")

                # Potential issues
                if test["potential_issues"]:
                    report.append(
                        f"    ⚠️  Issues: {', '.join(test['potential_issues'])}"
                    )

                # Code snippet (first few lines)
                if test.get("code_snippet"):
                    lines = test["code_snippet"].split("\n")[:3]
                    report.append(f"    💻 Code: {lines[0].strip()}")
                    if len(lines) > 1:
                        report.append(f"          {lines[1].strip()}")

                report.append("")

        # Recommendations
        report.append("\n🎯 RECOMMENDATIONS:")
        report.append("-" * 80)

        network_tests = [
            t for t in analyzed_tests if t["category"] == "NETWORK_DEPENDENT"
        ]
        if network_tests:
            report.append(f"1. 🌐 NETWORK DEPENDENT ({len(network_tests)} tests):")
            report.append("   - Mock HTTP requests and API calls")
            report.append("   - Use responses or aioresponses libraries")
            report.append("   - Disable DuckDuckGo searches in tests")

        delay_tests = [
            t for t in analyzed_tests if t["category"] == "ARTIFICIAL_DELAYS"
        ]
        if delay_tests:
            report.append(f"\n2. ⏳ ARTIFICIAL DELAYS ({len(delay_tests)} tests):")
            report.append("   - Mock asyncio.sleep() and time.sleep() calls")
            report.append("   - Use fixtures to replace delays with instant returns")
            report.append("   - Consider using freezegun for time-related tests")

        setup_tests = [
            t
            for t in analyzed_tests
            if t["category"] in ["SETUP_HEAVY", "TEARDOWN_HEAVY"]
        ]
        if setup_tests:
            report.append(f"\n3. 🔧 SETUP/TEARDOWN ISSUES ({len(setup_tests)} tests):")
            report.append("   - Use session or module-scoped fixtures")
            report.append("   - Cache expensive setup operations")
            report.append("   - Consider using pytest-benchmark for setup optimization")

        io_tests = [t for t in analyzed_tests if t["category"] == "IO_INTENSIVE"]
        if io_tests:
            report.append(f"\n4. 💾 I/O INTENSIVE ({len(io_tests)} tests):")
            report.append("   - Use in-memory databases for tests")
            report.append("   - Mock file operations with StringIO")
            report.append("   - Use temporary directories efficiently")

        return "\n".join(report)

    def save_results(self, results: dict, analyzed_tests: list[dict]):
        """Save results to JSON file for later analysis."""
        data = {
            "timestamp": time.time(),
            "results": results,
            "analyzed_tests": analyzed_tests,
        }

        with open(self.results_file, "w") as f:
            json.dump(data, f, indent=2)

        print(f"💾 Results saved to: {self.results_file}")

    def run_analysis(self):
        """Run the complete test performance analysis."""
        print("🎯 Starting comprehensive test performance analysis...")

        # Run tests and collect timing data
        results = self.run_tests_with_timing()

        if "error" in results:
            print(f"❌ Failed to run tests: {results['error']}")
            return

        # Analyze slow tests
        analyzed_tests = self.analyze_slow_tests(results)

        # Generate and display report
        report = self.generate_report(results, analyzed_tests)
        print(report)

        # Save results
        self.save_results(results, analyzed_tests)

        print(f"\n✅ Analysis complete! Check {self.results_file} for detailed data.")


if __name__ == "__main__":
    analyzer = TestPerformanceAnalyzer()
    analyzer.run_analysis()
