#!/usr/bin/env python3
"""
Complete Pipeline Demo for lib2docScrape

This script demonstrates the complete pipeline from scraping to markdown output,
showing exactly where and how scraped libraries are saved.
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logger = logging.getLogger(__name__)


async def demo_complete_pipeline():
    """Demonstrate the complete pipeline with real library documentation."""
    logger.info("🚀 Starting Complete Pipeline Demo")

    try:
        # Import required modules
        from src.backends.http_backend import HTTPBackend, HTTPBackendConfig
        from src.crawler import DocumentationCrawler

        # Create backend and crawler
        config = HTTPBackendConfig()
        backend = HTTPBackend(config=config)
        crawler = DocumentationCrawler(backend=backend)

        # Test libraries - our actual dependencies
        test_libraries = {
            "requests": {
                "url": "https://requests.readthedocs.io/en/latest/",
                "description": "HTTP library for Python",
            },
            "beautifulsoup4": {
                "url": "https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
                "description": "HTML/XML parser",
            },
        }

        # Create output directory
        output_dir = Path("scraped_libraries")
        output_dir.mkdir(exist_ok=True)

        logger.info(f"📁 Output directory: {output_dir}")

        # Process each library
        for lib_name, lib_info in test_libraries.items():
            logger.info(f"\n📚 Processing {lib_name}...")
            logger.info(f"🔗 URL: {lib_info['url']}")

            try:
                # Step 1: Crawl the documentation
                start_time = time.time()

                result = await crawler.crawl(
                    target_url=lib_info["url"],
                    depth=1,
                    follow_external=False,
                    content_types=["text/html"],
                    exclude_patterns=[],
                    required_patterns=[],
                    max_pages=2,  # Keep it manageable
                    allowed_paths=[],
                    excluded_paths=[],
                )

                crawl_duration = time.time() - start_time

                logger.info(f"⏱️  Crawled in {crawl_duration:.2f}s")
                logger.info(f"📄 Documents found: {len(result.documents)}")

                if not result.documents:
                    logger.warning(f"⚠️  No documents found for {lib_name}")
                    continue

                # Step 2: Process and save each document
                for i, doc in enumerate(result.documents):
                    doc_title = doc.get("title", f"{lib_name}_doc_{i + 1}")
                    doc_url = doc.get("url", lib_info["url"])
                    doc_content = doc.get("content", "")

                    if not doc_content:
                        logger.warning(f"⚠️  Document {i + 1} has no content")
                        continue

                    # Create markdown content
                    markdown_content = f"""# {doc_title}

**Library:** {lib_name}
**Description:** {lib_info["description"]}
**Source URL:** {doc_url}
**Scraped:** {datetime.now().isoformat()}
**Content Length:** {len(doc_content)} characters

---

## Raw Content

{doc_content[:5000]}{"..." if len(doc_content) > 5000 else ""}

---

## Metadata

- **Document Index:** {i + 1} of {len(result.documents)}
- **Crawl Duration:** {crawl_duration:.2f} seconds
- **Success Rate:** {result.stats.successful_crawls}/{result.stats.successful_crawls + result.stats.failed_crawls}

## Additional Information

This documentation was automatically scraped from {lib_name}'s official documentation
using lib2docScrape. The content above represents the raw scraped data.

For the most up-to-date information, please visit the original source at:
{doc_url}
"""

                    # Save markdown file
                    safe_title = "".join(
                        c for c in doc_title if c.isalnum() or c in (" ", "-", "_")
                    ).strip()
                    safe_title = safe_title.replace(" ", "_")
                    filename = f"{lib_name}_{safe_title}_{i + 1}.md"
                    file_path = output_dir / filename

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)

                    logger.info(f"✅ Saved: {file_path}")
                    logger.info(f"   Size: {file_path.stat().st_size} bytes")

                logger.info(f"✅ Completed {lib_name}")

            except Exception as e:
                logger.error(f"❌ Failed to process {lib_name}: {e}")
                continue

        # Step 3: Create index file
        logger.info("\n📋 Creating index file...")

        index_content = f"""# Scraped Library Documentation

**Generated:** {datetime.now().isoformat()}
**Tool:** lib2docScrape
**Purpose:** Automated documentation scraping for project dependencies

## Libraries Processed

"""

        # List all created markdown files
        markdown_files = list(output_dir.glob("*.md"))
        markdown_files = [f for f in markdown_files if f.name != "README.md"]

        for lib_name, lib_info in test_libraries.items():
            lib_files = [f for f in markdown_files if f.name.startswith(lib_name)]

            index_content += f"""### {lib_name}

**Description:** {lib_info["description"]}
**Source:** {lib_info["url"]}
**Files Generated:** {len(lib_files)}

"""

            for file_path in lib_files:
                file_size = file_path.stat().st_size
                index_content += (
                    f"- [{file_path.name}]({file_path.name}) ({file_size} bytes)\n"
                )

            index_content += "\n"

        index_content += f"""## Summary

- **Total Files:** {len(markdown_files)}
- **Total Size:** {sum(f.stat().st_size for f in markdown_files)} bytes
- **Libraries Processed:** {len(test_libraries)}

## Usage

These markdown files contain the scraped documentation for the libraries used in this project.
Each file includes:

1. **Library metadata** (name, description, source URL)
2. **Scraped content** (the actual documentation text)
3. **Processing information** (timestamps, file sizes, etc.)

## Next Steps

1. Review the generated documentation files
2. Integrate with your documentation system
3. Set up automated updates as needed

---

*Generated by lib2docScrape - Automated Documentation Scraping Tool*
"""

        index_path = output_dir / "README.md"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)

        logger.info(f"✅ Created index: {index_path}")

        # Step 4: Final summary
        all_files = list(output_dir.glob("*.md"))
        total_size = sum(f.stat().st_size for f in all_files)

        logger.info("\n🎉 Pipeline Complete!")
        logger.info(f"📁 Output Directory: {output_dir}")
        logger.info(f"📄 Files Created: {len(all_files)}")
        logger.info(f"💾 Total Size: {total_size:,} bytes")

        logger.info("\n📋 Generated Files:")
        for file_path in sorted(all_files):
            size = file_path.stat().st_size
            logger.info(f"   • {file_path.name} ({size:,} bytes)")

        await backend.close()
        return True

    except Exception as e:
        logger.error(f"💥 Pipeline failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main function."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("=" * 70)
    print("🎯 LIB2DOCSCRAPE COMPLETE PIPELINE DEMO")
    print("=" * 70)
    print("This demo shows the complete process:")
    print("1. 📡 Scrape library documentation")
    print("2. 🔄 Process content")
    print("3. 📝 Save as markdown files")
    print("4. 📋 Create organized index")
    print("=" * 70)

    success = await demo_complete_pipeline()

    print("\n" + "=" * 70)
    print("🎯 DEMO RESULTS")
    print("=" * 70)

    if success:
        print("✅ SUCCESS! Complete pipeline working perfectly!")
        print("")
        print("🎉 Your scraped libraries are now saved as markdown!")
        print("📁 Check the 'scraped_libraries/' directory")
        print("📄 Each library has its own markdown file")
        print("📋 README.md contains the complete index")
        print("")
        print("🔍 What you'll find:")
        print("   • Library documentation in markdown format")
        print("   • Organized file structure")
        print("   • Complete metadata and timestamps")
        print("   • Ready-to-use documentation files")

        # Show actual files created
        output_dir = Path("scraped_libraries")
        if output_dir.exists():
            files = list(output_dir.glob("*.md"))
            if files:
                print(f"\n📋 Files created ({len(files)} total):")
                for file_path in sorted(files):
                    size = file_path.stat().st_size
                    print(f"   • {file_path.name} ({size:,} bytes)")
    else:
        print("❌ FAILED! Something went wrong with the pipeline")
        print("Check the logs above for details")

    print("=" * 70)

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
