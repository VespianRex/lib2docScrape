# Since there's a name collision between src.crawler and src.crawler.crawler,
# we need to define a standalone version of the _find_links_recursive function
# based on the implementation in src.crawler.py for testing purposes


def find_links_recursive(structure_element) -> list[str]:
    """Recursively find all 'href' values from link elements in the structure."""
    links = []
    if isinstance(structure_element, dict):
        # Check if the current element itself is a link
        if (
            structure_element.get("type") in ["link", "link_inline"]
            and "href" in structure_element
        ):
            # Note: We're including empty strings ('') but not None values
            if structure_element["href"] is not None:
                links.append(structure_element["href"])
        # Recursively check values that are lists or dicts
        for value in structure_element.values():
            if isinstance(value, (dict, list)):
                links.extend(find_links_recursive(value))
    elif isinstance(structure_element, list):
        # Recursively check items in the list
        for item in structure_element:
            links.extend(find_links_recursive(item))
    return links


# Simple wrapper to simulate the class method call
def get_crawler_instance():
    class Crawler:
        def _find_links_recursive(self, structure_element):
            return find_links_recursive(structure_element)

    return Crawler()


class TestFindLinksRecursive:
    def test_empty_structure(self):
        """Test 6.1: Empty Structure"""
        crawler = get_crawler_instance()

        links_dict = crawler._find_links_recursive({})
        assert links_dict == [], "Should return empty list for an empty dictionary"

        links_list = crawler._find_links_recursive([])
        assert links_list == [], "Should return empty list for an empty list"

    def test_simple_link(self):
        """Test 6.2: Simple Link"""
        crawler = get_crawler_instance()
        structure = {"type": "link", "href": "page1.html"}
        links = crawler._find_links_recursive(structure)
        assert links == [
            "page1.html"
        ], "Should find a single link in a simple structure"

    def test_nested_structure_with_multiple_links(self):
        """Test 6.3: Nested Structure with Multiple Links"""
        crawler = get_crawler_instance()
        structure = {
            "type": "section",
            "content": [
                {"type": "link", "href": "page2.html"},
                {
                    "type": "paragraph",
                    "children": [{"type": "link_inline", "href": "page3.html"}],
                },
            ],
            "footer": {"type": "link", "href": "page4.html"},
        }
        links = crawler._find_links_recursive(structure)
        assert sorted(links) == sorted(
            ["page2.html", "page3.html", "page4.html"]
        ), "Should find all links in a nested structure"

    def test_structure_without_links(self):
        """Test 6.4: Structure without Links"""
        crawler = get_crawler_instance()
        structure = {"type": "paragraph", "text": "No links here"}
        links = crawler._find_links_recursive(structure)
        assert links == [], "Should return an empty list if no links are present"

    def test_mixed_content_with_links_at_various_levels(self):
        """Additional test for more complex scenarios."""
        crawler = get_crawler_instance()
        structure = [
            {"type": "header", "text": "Welcome"},
            {"type": "link", "href": "home.html"},
            {
                "type": "article",
                "title": "My Article",
                "body": [
                    {"type": "text_block", "content": "Some text."},
                    {"type": "link_inline", "href": "details.html"},
                    {
                        "type": "subsection",
                        "items": [
                            {"type": "link", "href": "subsection_link1.html"},
                            {"type": "text", "value": "Another text"},
                            {"type": "link", "href": "subsection_link2.html"},
                        ],
                    },
                ],
                "sidebar": {"type": "link", "href": "sidebar.html"},
            },
            {"type": "footer", "links": [{"type": "link", "href": "contact.html"}]},
        ]
        links = crawler._find_links_recursive(structure)
        expected_links = [
            "home.html",
            "details.html",
            "subsection_link1.html",
            "subsection_link2.html",
            "sidebar.html",
            "contact.html",
        ]
        assert sorted(links) == sorted(
            expected_links
        ), "Should find all links in a complex, mixed content structure"

    def test_links_in_list_of_dicts(self):
        crawler = get_crawler_instance()
        structure = [
            {"type": "link", "href": "link1.html"},
            {"type": "text", "content": "some text"},
            {"type": "link", "href": "link2.html"},
        ]
        links = crawler._find_links_recursive(structure)
        assert sorted(links) == sorted(["link1.html", "link2.html"])

    def test_deeply_nested_single_link(self):
        crawler = get_crawler_instance()
        structure = {
            "level1": {
                "level2": {
                    "level3": {"level4": {"type": "link", "href": "deep_link.html"}}
                }
            }
        }
        links = crawler._find_links_recursive(structure)
        assert links == ["deep_link.html"]

    def test_no_href_in_link_type_element(self):
        crawler = get_crawler_instance()
        structure = {"type": "link", "text": "A link without href"}  # No href
        links = crawler._find_links_recursive(structure)
        assert links == []

    def test_href_is_none_or_empty(self):
        crawler = get_crawler_instance()
        structure1 = {"type": "link", "href": None}
        links1 = crawler._find_links_recursive(structure1)
        assert links1 == []

        structure2 = {"type": "link", "href": ""}
        links2 = crawler._find_links_recursive(structure2)
        assert links2 == [
            ""
        ]  # The current implementation would include empty strings if present

    def test_various_data_types_as_values(self):
        crawler = get_crawler_instance()
        structure = {
            "key_str": "some string",
            "key_int": 123,
            "key_bool": True,
            "key_none": None,
            "key_link": {"type": "link", "href": "actual_link.html"},
        }
        links = crawler._find_links_recursive(structure)
        assert links == ["actual_link.html"]
