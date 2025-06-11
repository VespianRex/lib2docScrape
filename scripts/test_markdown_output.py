#!/usr/bin/env python3
"""
Test Markdown Output for lib2docScrape

This script tests the complete pipeline from scraping to markdown output,
showing where scraped libraries are saved and in what format.
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


async def test_complete_pipeline():
    """Test the complete pipeline from scraping to markdown output."""
    logger.info("🧪 Testing complete pipeline: Scraping → Processing → Markdown Output")

    try:
        # Import required modules
        from src.backends.http_backend import HTTPBackend, HTTPBackendConfig
        from src.content_processor import ContentProcessor
        from src.crawler import DocumentationCrawler
        from src.organizers.doc_organizer import DocumentOrganizer, OrganizationConfig

        # Create backend and crawler
        config = HTTPBackendConfig()
        backend = HTTPBackend(config=config)
        crawler = DocumentationCrawler(backend=backend)

        # Create content processor and organizer
        content_processor = ContentProcessor()
        org_config = OrganizationConfig()
        organizer = DocumentOrganizer(config=org_config)

        # Test URL - simple and reliable
        test_url = "https://httpbin.org/html"

        logger.info(f"🎯 Testing with: {test_url}")

        # Step 1: Crawl content
        logger.info("📡 Step 1: Crawling content...")
        start_time = time.time()

        result = await crawler.crawl(
            target_url=test_url,
            depth=1,
            follow_external=False,
            content_types=["text/html"],
            exclude_patterns=[],
            required_patterns=[],
            max_pages=1,
            allowed_paths=[],
            excluded_paths=[],
        )

        crawl_duration = time.time() - start_time
        logger.info(f"✅ Crawling completed in {crawl_duration:.2f}s")
        logger.info(f"📄 Documents found: {len(result.documents)}")

        if not result.documents:
            logger.error("❌ No documents found during crawling")
            return False

        # Step 2: Process content
        logger.info("🔄 Step 2: Processing content...")
        processed_documents = []

        for doc in result.documents:
            logger.info(f"Processing document: {doc.get('url', 'Unknown URL')}")

            # Extract HTML content
            html_content = doc.get("content", "")
            if not html_content:
                logger.warning("⚠️  Document has no content")
                continue

            # Process content
            processed_content = content_processor.process(
                html_content=html_content,
                url=doc.get("url", test_url),
                title=doc.get("title", "Untitled"),
            )

            logger.info("✅ Processed content:")
            logger.info(f"   Title: {processed_content.title}")
            logger.info(f"   Content length: {len(processed_content.content)}")
            logger.info(f"   Headings: {len(processed_content.headings)}")
            logger.info(f"   Links: {len(processed_content.links)}")

            processed_documents.append(processed_content)

        # Step 3: Organize and save
        logger.info("📁 Step 3: Organizing and saving documents...")

        for processed_doc in processed_documents:
            doc_id = organizer.add_document(processed_doc)
            logger.info(f"✅ Added document to organizer with ID: {doc_id}")

        # Step 4: Export to markdown
        logger.info("📝 Step 4: Exporting to markdown...")

        # Create output directory
        output_dir = Path("scraped_docs")
        output_dir.mkdir(exist_ok=True)

        # Save each document as markdown
        for doc_id, doc_metadata in organizer.documents.items():
            if doc_metadata.versions:
                latest_version = doc_metadata.versions[-1]

                # Create markdown filename
                safe_title = "".join(
                    c for c in doc_metadata.title if c.isalnum() or c in (" ", "-", "_")
                ).rstrip()
                safe_title = safe_title.replace(" ", "_")
                markdown_filename = f"{safe_title}_{doc_id[:8]}.md"
                markdown_path = output_dir / markdown_filename

                # Get processed content from latest version
                version_data = latest_version.changes

                # Create markdown content
                markdown_content = f"""# {doc_metadata.title}

**URL:** {doc_metadata.url}
**Category:** {doc_metadata.category or "Uncategorized"}
**Last Updated:** {doc_metadata.last_updated}
**Document ID:** {doc_id}

---

{version_data.get("content", "No content available")}

---

## Metadata

- **Tags:** {", ".join(doc_metadata.tags) if doc_metadata.tags else "None"}
- **References:** {len(doc_metadata.references)} found
- **Index Terms:** {len(doc_metadata.index_terms)} terms

## Version Information

- **Version:** {latest_version.version_id}
- **Timestamp:** {latest_version.timestamp}
- **Hash:** {latest_version.hash[:16]}...

"""

                # Save markdown file
                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                logger.info(f"✅ Saved markdown: {markdown_path}")
                logger.info(f"   File size: {markdown_path.stat().st_size} bytes")

        # Step 5: Create index file
        logger.info("📋 Step 5: Creating index file...")

        index_content = f"""# Scraped Documentation Index

Generated on: {datetime.now().isoformat()}

## Documents

"""

        for doc_id, doc_metadata in organizer.documents.items():
            safe_title = "".join(
                c for c in doc_metadata.title if c.isalnum() or c in (" ", "-", "_")
            ).rstrip()
            safe_title = safe_title.replace(" ", "_")
            markdown_filename = f"{safe_title}_{doc_id[:8]}.md"

            index_content += f"""### [{doc_metadata.title}]({markdown_filename})

- **URL:** {doc_metadata.url}
- **Category:** {doc_metadata.category or "Uncategorized"}
- **Last Updated:** {doc_metadata.last_updated}
- **Versions:** {len(doc_metadata.versions)}

"""

        index_path = output_dir / "README.md"
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(index_content)

        logger.info(f"✅ Created index: {index_path}")

        # Step 6: Summary
        logger.info("📊 Step 6: Summary")

        output_files = list(output_dir.glob("*.md"))
        total_size = sum(f.stat().st_size for f in output_files)

        logger.info("✅ Pipeline completed successfully!")
        logger.info(f"📁 Output directory: {output_dir}")
        logger.info(f"📄 Files created: {len(output_files)}")
        logger.info(f"💾 Total size: {total_size} bytes")

        # List all created files
        logger.info("📋 Created files:")
        for file_path in sorted(output_files):
            logger.info(f"   • {file_path.name} ({file_path.stat().st_size} bytes)")

        await backend.close()
        return True

    except Exception as e:
        logger.error(f"💥 Pipeline failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_dependency_scraping():
    """Test scraping a real dependency's documentation."""
    logger.info("🧪 Testing dependency documentation scraping...")

    try:
        # Import required modules
        from src.backends.http_backend import HTTPBackend, HTTPBackendConfig
        from src.content_processor import ContentProcessor
        from src.crawler import DocumentationCrawler
        from src.organizers.doc_organizer import DocumentOrganizer, OrganizationConfig

        # Create backend and crawler
        config = HTTPBackendConfig()
        backend = HTTPBackend(config=config)
        crawler = DocumentationCrawler(backend=backend)

        # Create content processor and organizer
        content_processor = ContentProcessor()
        org_config = OrganizationConfig()
        DocumentOrganizer(config=org_config)

        # Test with requests documentation
        test_url = "https://requests.readthedocs.io/en/latest/"

        logger.info(f"🎯 Testing with requests documentation: {test_url}")

        # Crawl content
        result = await crawler.crawl(
            target_url=test_url,
            depth=1,
            follow_external=False,
            content_types=["text/html"],
            exclude_patterns=[],
            required_patterns=[],
            max_pages=2,  # Keep it small for testing
            allowed_paths=[],
            excluded_paths=[],
        )

        logger.info(f"📄 Documents found: {len(result.documents)}")

        if result.documents:
            # Process and save first document
            doc = result.documents[0]
            html_content = doc.get("content", "")

            if html_content:
                processed_content = content_processor.process(
                    html_content=html_content,
                    url=doc.get("url", test_url),
                    title=doc.get("title", "Requests Documentation"),
                )

                # Create output directory
                output_dir = Path("scraped_libraries")
                output_dir.mkdir(exist_ok=True)

                # Save as markdown
                markdown_content = f"""# {processed_content.title}

**URL:** {processed_content.url}
**Scraped:** {datetime.now().isoformat()}

---

{processed_content.content}

---

## Links Found

"""

                for link in processed_content.links[:10]:  # First 10 links
                    markdown_content += (
                        f"- [{link.get('text', 'No text')}]({link.get('url', '#')})\n"
                    )

                # Save file
                markdown_path = output_dir / "requests_documentation.md"
                with open(markdown_path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                logger.info(f"✅ Saved requests documentation: {markdown_path}")
                logger.info(
                    f"📄 Content length: {len(processed_content.content)} characters"
                )
                logger.info(f"🔗 Links found: {len(processed_content.links)}")
                logger.info(f"📋 Headings found: {len(processed_content.headings)}")

        await backend.close()
        return True

    except Exception as e:
        logger.error(f"💥 Dependency scraping failed: {e}")
        return False


async def main():
    """Main function."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("=" * 60)
    logger.info("🎯 MARKDOWN OUTPUT TEST")
    logger.info("=" * 60)
    logger.info("Testing complete pipeline: Scraping → Processing → Markdown")
    logger.info("=" * 60)

    # Test 1: Complete pipeline
    logger.info("\n🧪 TEST 1: Complete Pipeline")
    success1 = await test_complete_pipeline()

    # Test 2: Real dependency
    logger.info("\n🧪 TEST 2: Real Dependency Documentation")
    success2 = await test_dependency_scraping()

    # Summary
    print("\n" + "=" * 60)
    print("🎯 MARKDOWN OUTPUT TEST RESULTS")
    print("=" * 60)

    if success1:
        print("✅ TEST 1: Complete Pipeline - SUCCESS")
        print("   📁 Check 'scraped_docs/' directory for markdown files")
    else:
        print("❌ TEST 1: Complete Pipeline - FAILED")

    if success2:
        print("✅ TEST 2: Real Dependency - SUCCESS")
        print("   📁 Check 'scraped_libraries/' directory for markdown files")
    else:
        print("❌ TEST 2: Real Dependency - FAILED")

    if success1 or success2:
        print("\n🎉 MARKDOWN OUTPUT IS WORKING!")
        print("📝 Scraped content is being saved as markdown files")
        print("📁 Check the output directories for your documentation")
    else:
        print("\n❌ MARKDOWN OUTPUT NEEDS INVESTIGATION")

    print("=" * 60)

    return 0 if (success1 or success2) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
