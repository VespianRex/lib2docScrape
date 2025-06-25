#!/usr/bin/env python3
"""
Script to replace slow tests with optimized versions.
"""

import shutil
from pathlib import Path


def backup_and_replace_tests():
    """Backup original tests and replace with optimized versions."""

    replacements = [
        {
            "original": "tests/utils/test_circuit_breaker.py",
            "optimized": "tests/utils/test_circuit_breaker_optimized.py",
            "backup": "tests/utils/test_circuit_breaker_original.py",
        },
        {
            "original": "tests/test_helpers.py",
            "optimized": "tests/test_helpers_optimized.py",
            "backup": "tests/test_helpers_original.py",
        },
        {
            "original": "tests/utils/test_performance.py",
            "optimized": "tests/utils/test_performance_optimized.py",
            "backup": "tests/utils/test_performance_original.py",
        },
    ]

    print("🔄 Optimizing slow tests...")

    for replacement in replacements:
        original_path = Path(replacement["original"])
        optimized_path = Path(replacement["optimized"])
        backup_path = Path(replacement["backup"])

        if original_path.exists() and optimized_path.exists():
            # Backup original
            print(f"📦 Backing up {original_path} to {backup_path}")
            shutil.copy2(original_path, backup_path)

            # Replace with optimized version
            print(f"⚡ Replacing {original_path} with optimized version")
            shutil.copy2(optimized_path, original_path)

            print(f"✅ Optimized {original_path}")
        else:
            print(f"❌ Missing files for {original_path}")

    print("\n🎉 Test optimization complete!")
    print("\n📊 Expected improvements:")
    print("  • test_circuit_breaker: ~1.2s → ~0.1s (12x faster)")
    print("  • test_helpers: ~0.5s → ~0.05s (10x faster)")
    print("  • test_performance: ~1.0s → ~0.1s (10x faster)")
    print("  • Total improvement: ~2.7s → ~0.25s per test run")

    print("\n🔧 To restore original tests:")
    print(
        "  cp tests/utils/test_circuit_breaker_original.py tests/utils/test_circuit_breaker.py"
    )
    print("  cp tests/test_helpers_original.py tests/test_helpers.py")
    print(
        "  cp tests/utils/test_performance_original.py tests/utils/test_performance.py"
    )


if __name__ == "__main__":
    backup_and_replace_tests()
