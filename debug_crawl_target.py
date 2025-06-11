"""Debug script for CrawlTarget model."""

from src.crawler import CrawlTarget


def main():
    """Test instantiation of CrawlTarget."""
    # Try default instantiation
    print("Attempting default instantiation...")
    try:
        target = CrawlTarget()
        print(
            f"Default instantiation successful: url={target.url}, depth={target.depth}"
        )
    except Exception as e:
        print(f"Default instantiation failed: {e}")

    # Try instantiation with explicit values
    print("\nAttempting instantiation with explicit values...")
    try:
        target = CrawlTarget(url="http://example.com", depth=2)
        print(
            f"Explicit instantiation successful: url={target.url}, depth={target.depth}"
        )
    except Exception as e:
        print(f"Explicit instantiation failed: {e}")


if __name__ == "__main__":
    main()
