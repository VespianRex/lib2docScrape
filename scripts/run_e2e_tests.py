#!/usr/bin/env python3
"""
Automated E2E test runner for lib2docScrape.

This script provides comprehensive end-to-end testing with:
- Site availability checking
- Performance benchmarking
- Result reporting
- CI/CD integration
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.e2e.test_sites import TEST_SITES, site_manager  # noqa: E402

logger = logging.getLogger(__name__)


class E2ETestRunner:
    """Manages end-to-end test execution and reporting."""

    def __init__(self, config: dict):
        self.config = config
        self.results = {
            "start_time": datetime.now().isoformat(),
            "config": config,
            "site_availability": {},
            "test_results": {},
            "performance_metrics": {},
            "summary": {},
        }

    async def check_site_availability(self) -> dict[str, bool]:
        """Check availability of all test sites."""
        logger.info("Checking test site availability...")
        availability = await site_manager.refresh_availability()

        self.results["site_availability"] = availability

        available_count = sum(availability.values())
        total_count = len(availability)

        logger.info(
            f"Site availability: {available_count}/{total_count} sites available"
        )

        for site_id, is_available in availability.items():
            site = TEST_SITES[site_id]
            status = "✓" if is_available else "✗"
            logger.info(f"  {status} {site.name} ({site.url})")

        return availability

    def build_pytest_args(self) -> list[str]:
        """Build pytest arguments based on configuration."""
        args = ["tests/e2e/", "-v", "--tb=short", f"--timeout={self.config['timeout']}"]

        # Add markers based on config
        markers = []

        if self.config.get("skip_slow"):
            markers.append("not slow")

        if self.config.get("performance_only"):
            markers.append("performance")
        elif self.config.get("skip_performance"):
            markers.append("not performance")

        if not self.config.get("include_real_world", True):
            markers.append("not real_world")

        if markers:
            args.extend(["-m", " and ".join(markers)])

        # Add output options
        if self.config.get("junit_xml"):
            args.extend(["--junit-xml", self.config["junit_xml"]])

        if self.config.get("html_report"):
            args.extend(["--html", self.config["html_report"]])

        # Add coverage if requested
        if self.config.get("coverage"):
            args.extend(
                ["--cov=src", "--cov-report=term-missing", "--cov-report=html:htmlcov"]
            )

        return args

    def run_tests(self) -> int:
        """Run the E2E tests using pytest."""
        logger.info("Starting E2E test execution...")

        # Set environment variables
        os.environ["E2E_TIMEOUT"] = str(self.config["timeout"])
        os.environ["E2E_MAX_CONCURRENT"] = str(self.config.get("max_concurrent", 3))

        if self.config.get("skip_real_world"):
            os.environ["SKIP_REAL_WORLD_TESTS"] = "true"

        # Build pytest arguments
        pytest_args = self.build_pytest_args()

        logger.info(f"Running: pytest {' '.join(pytest_args)}")

        # Run pytest
        start_time = time.time()
        exit_code = pytest.main(pytest_args)
        duration = time.time() - start_time

        self.results["test_execution"] = {
            "exit_code": exit_code,
            "duration": duration,
            "pytest_args": pytest_args,
        }

        logger.info(
            f"Test execution completed in {duration:.2f}s with exit code {exit_code}"
        )

        return exit_code

    def generate_report(self) -> dict:
        """Generate comprehensive test report."""
        self.results["end_time"] = datetime.now().isoformat()

        # Calculate summary statistics
        availability = self.results["site_availability"]
        available_sites = sum(availability.values())
        total_sites = len(availability)

        self.results["summary"] = {
            "total_sites": total_sites,
            "available_sites": available_sites,
            "availability_rate": available_sites / max(1, total_sites),
            "test_success": self.results.get("test_execution", {}).get("exit_code")
            == 0,
        }

        return self.results

    def save_report(self, output_file: str):
        """Save test report to file."""
        report = self.generate_report()

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Test report saved to {output_path}")


async def main():
    """Main entry point for E2E test runner."""
    parser = argparse.ArgumentParser(description="Run lib2docScrape E2E tests")

    # Test selection options
    parser.add_argument("--skip-slow", action="store_true", help="Skip slow tests")
    parser.add_argument(
        "--skip-real-world", action="store_true", help="Skip real-world tests"
    )
    parser.add_argument(
        "--performance-only", action="store_true", help="Run only performance tests"
    )
    parser.add_argument(
        "--skip-performance", action="store_true", help="Skip performance tests"
    )

    # Configuration options
    parser.add_argument(
        "--timeout", type=int, default=60, help="Test timeout in seconds"
    )
    parser.add_argument(
        "--max-concurrent", type=int, default=3, help="Max concurrent tests"
    )

    # Output options
    parser.add_argument(
        "--report", default="reports/e2e_report.json", help="Output report file"
    )
    parser.add_argument("--junit-xml", help="JUnit XML output file")
    parser.add_argument("--html-report", help="HTML report output file")
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )

    # Logging options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet logging")

    args = parser.parse_args()

    # Configure logging
    log_level = (
        logging.DEBUG
        if args.verbose
        else logging.WARNING
        if args.quiet
        else logging.INFO
    )
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Build configuration
    config = {
        "timeout": args.timeout,
        "max_concurrent": args.max_concurrent,
        "skip_slow": args.skip_slow,
        "skip_real_world": args.skip_real_world,
        "performance_only": args.performance_only,
        "skip_performance": args.skip_performance,
        "include_real_world": not args.skip_real_world,
        "junit_xml": args.junit_xml,
        "html_report": args.html_report,
        "coverage": args.coverage,
    }

    # Create test runner
    runner = E2ETestRunner(config)

    try:
        # Check site availability
        await runner.check_site_availability()

        # Run tests
        exit_code = runner.run_tests()

        # Generate and save report
        runner.save_report(args.report)

        # Print summary
        report = runner.results
        summary = report["summary"]

        print("\n" + "=" * 60)
        print("E2E TEST SUMMARY")
        print("=" * 60)
        print(
            f"Sites available: {summary['available_sites']}/{summary['total_sites']} ({summary['availability_rate']:.1%})"
        )
        print(f"Test success: {'✓' if summary['test_success'] else '✗'}")

        if "test_execution" in report:
            duration = report["test_execution"]["duration"]
            print(f"Execution time: {duration:.2f}s")

        print(f"Report saved: {args.report}")
        print("=" * 60)

        return exit_code

    except Exception as e:
        logger.error(f"E2E test runner failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
