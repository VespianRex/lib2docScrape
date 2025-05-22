#!/usr/bin/env python3
import asyncio
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
    from unittest.mock import MagicMock, patch
    print("Successfully imported MagicMock and patch")
    
    from src.utils.search import DuckDuckGoSearch, DUCKDUCKGO_AVAILABLE
    print(f"Successfully imported from src.utils.search")
    print(f"DuckDuckGo library available: {DUCKDUCKGO_AVAILABLE}")

    async def run_test():
        try:
            print("Starting test...")
            
            # Create mocks
            print("Creating mocks...")
            mock_ddgs_class = MagicMock()
            mock_ddgs_instance = MagicMock()
            
            # For basic search test
            mock_library_results = [
                {'title': 'Python Official Docs', 'href': 'https://docs.python.org', 'body': 'The official Python documentation.'},
                {'title': 'RealPython Tutorials', 'href': 'https://realpython.com', 'body': 'Practical Python tutorials.'}
            ]
            mock_ddgs_instance.text.return_value = mock_library_results
            mock_ddgs_class.return_value = mock_ddgs_instance
            print("Mocks created successfully")
            
            # Patch and test
            print("Patching DDGS...")
            with patch('src.utils.search.DDGS', mock_ddgs_class):
                print("DDGS patched successfully")
                
                # Initialize search
                print("Creating search instance...")
                search_instance = DuckDuckGoSearch(max_results=2)
                print("Search instance created")
                
                # Test 1: Basic search
                print("===== TEST 1: BASIC SEARCH =====")
                query = "python documentation"
                print(f"Searching for: {query}")
                results = await search_instance.search(query)
                print(f"Search completed, found {len(results)} results")
                
                # Check mock calls
                print(f"Mock called: {mock_ddgs_instance.text.called}")
                if mock_ddgs_instance.text.called:
                    print(f"Mock call args: {mock_ddgs_instance.text.call_args}")
                
                # Check results
                print("Results:", results)
                
                expected_formatted_results = [
                    {'title': 'Python Official Docs', 'url': 'https://docs.python.org', 'description': 'The official Python documentation.'},
                    {'title': 'RealPython Tutorials', 'url': 'https://realpython.com', 'description': 'Practical Python tutorials.'}
                ]
                if results == expected_formatted_results:
                    print("Results match expected format")
                else:
                    print("Results do NOT match expected format")
                
                # Test 2: Empty query
                print("\n===== TEST 2: EMPTY QUERY =====")
                mock_ddgs_instance.text.reset_mock()
                mock_ddgs_instance.text.return_value = []  # No results for empty query
                
                empty_results = await search_instance.search("")
                print(f"Empty query search completed, found {len(empty_results)} results")
                print(f"Mock called for empty query: {mock_ddgs_instance.text.called}")
                if mock_ddgs_instance.text.called:
                    print(f"Mock call args: {mock_ddgs_instance.text.call_args}")
                
                assert empty_results == [], "Empty query should return empty list"
                
                # Test 3: Site filter
                print("\n===== TEST 3: SITE FILTER =====")
                mock_ddgs_instance.text.reset_mock()
                site_specific_mock_results = [
                    {'title': 'Python Site Specific Page', 'href': 'https://python.org/specific', 'body': 'A specific page on python.org.'}
                ]
                mock_ddgs_instance.text.return_value = site_specific_mock_results
                
                site_query = "specifics"
                site_filter = "python.org"
                print(f"Searching for: {site_query} with site filter: {site_filter}")
                
                site_search_results = await search_instance.search(site_query, site=site_filter)
                print(f"Site filter search completed, found {len(site_search_results)} results")
                
                expected_query = f"site:{site_filter} {site_query}"
                print(f"Expected query with site filter: '{expected_query}'")
                print(f"Mock called for site filter: {mock_ddgs_instance.text.called}")
                
                if mock_ddgs_instance.text.called:
                    actual_call_args = mock_ddgs_instance.text.call_args
                    print(f"Actual call args: {actual_call_args}")
                    
                    # Check if the call arguments match expected
                    called_with_query, called_with_kwargs = actual_call_args
                    if called_with_query[0] == expected_query:
                        print("✓ Called with correct site filter query")
                    else:
                        print(f"✗ Called with INCORRECT query: '{called_with_query[0]}', expected: '{expected_query}'")
                
                # Check results
                expected_site_formatted_results = [
                    {'title': 'Python Site Specific Page', 'url': 'https://python.org/specific', 'description': 'A specific page on python.org.'}
                ]
                
                print("Site filter results:", site_search_results)
                
                if site_search_results == expected_site_formatted_results:
                    print("✓ Site filter results match expected format")
                else:
                    print("✗ Site filter results do NOT match expected format")
        
        except Exception as e:
            print(f"Error during test: {str(e)}")
            traceback.print_exc()

    if __name__ == "__main__":
        print("Starting main...")
        asyncio.run(run_test())
        print("Test complete")

except Exception as e:
    print(f"Error during import or setup: {str(e)}")
    traceback.print_exc()
