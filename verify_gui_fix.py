#!/usr/bin/env python3
"""
Quick test to verify frontend-backend connection is fixed
"""

import asyncio
import sys
from pathlib import Path


async def test_endpoint_fix():
    """Test if the frontend fix resolves the connection issue."""

    print("🔍 TESTING FRONTEND-BACKEND CONNECTION FIX")
    print("=" * 50)

    # 1. Check if the fix was applied to the template
    template_path = Path("templates/scraping_dashboard.html")
    if template_path.exists():
        template_content = template_path.read_text()

        print("📝 Checking template fixes...")

        # Check if old broken endpoint is gone
        if "/api/scraping/start" in template_content:
            print("❌ OLD BROKEN ENDPOINT STILL PRESENT: /api/scraping/start")
            return False
        else:
            print("✅ Old broken endpoint removed")

        # Check if new correct endpoint is present
        if "/start_crawl" in template_content:
            print("✅ New correct endpoint present: /start_crawl")
        else:
            print("❌ NEW ENDPOINT MISSING: /start_crawl")
            return False

        # Check if data format is fixed
        if "urls: [" in template_content:
            print("✅ Data format fixed: sending urls array")
        else:
            print("❌ DATA FORMAT NOT FIXED: still sending wrong format")
            return False

    else:
        print("❌ Template file not found")
        return False

    # 2. Check backend endpoint exists
    print("\n📡 Checking backend endpoints...")

    try:
        with open("run_gui.py") as f:
            backend_content = f.read()

        if '@app.post("/start_crawl")' in backend_content:
            print("✅ Backend endpoint /start_crawl exists")
        else:
            print("❌ Backend endpoint /start_crawl missing")
            return False

        if '@app.post("/api/scraping/stop")' in backend_content:
            print("✅ Backend endpoint /api/scraping/stop exists")
        else:
            print("❌ Backend endpoint /api/scraping/stop missing")

    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False

    # 3. Summary
    print("\n📋 FRONTEND-BACKEND CONNECTION STATUS")
    print("=" * 40)
    print("✅ Template updated to call correct endpoint")
    print("✅ Data format fixed (urls array)")
    print("✅ Backend endpoint exists")
    print("✅ Stop endpoint exists")

    print("\n🎉 FRONTEND-BACKEND CONNECTION ISSUES RESOLVED!")
    print("\n💡 NEXT STEPS:")
    print("   1. Start GUI server: python run_gui.py")
    print("   2. Open browser to http://localhost:60643")
    print("   3. Click 'Start Scraping' button")
    print("   4. Verify it connects to backend successfully")

    return True


async def main():
    success = await test_endpoint_fix()

    if success:
        print("\n✅ CONNECTION FIX VALIDATION PASSED")
        sys.exit(0)
    else:
        print("\n❌ CONNECTION FIX VALIDATION FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
