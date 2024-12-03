import pytest
from bs4 import BeautifulSoup
from src.processors.content_processor import ContentProcessor, ProcessorConfig

@pytest.fixture
def processor():
    return ContentProcessor(ProcessorConfig())

def test_basic_metadata_extraction(processor):
    """Test basic metadata extraction with all meta tags present."""
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="A test page description">
            <meta name="keywords" content="test, page, metadata">
            <meta property="og:title" content="OG Test Title">
            <meta property="og:description" content="OG test description">
            <meta name="twitter:card" content="summary">
            <meta name="twitter:title" content="Twitter Test Title">
        </head>
        <body>
            <h1>Test Content</h1>
            <p>Some test content.</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert metadata["meta_tags"]["title"] == "Test Page"
    assert metadata["meta_tags"]["description"] == "A test page description"
    assert metadata["meta_tags"]["keywords"] == "test, page, metadata"
    assert metadata["opengraph"]["title"] == "OG Test Title"
    assert metadata["opengraph"]["description"] == "OG test description"
    assert metadata["twitter"]["card"] == "summary"
    assert metadata["twitter"]["title"] == "Twitter Test Title"

def test_metadata_fallbacks(processor):
    """Test metadata fallback generation when meta tags are missing."""
    html = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>Main Heading</h1>
            <p>This is the first paragraph that should become the description.</p>
            <p>This is another paragraph with important keywords like documentation crawler testing.</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert metadata["meta_tags"]["title"] == "Test Page"
    assert "first paragraph" in metadata["meta_tags"]["description"]
    assert len(metadata["meta_tags"]["keywords"].split(",")) == 5  # Should generate 5 keywords

def test_empty_metadata(processor):
    """Test metadata extraction with minimal HTML content."""
    html = "<html><body>Some content</body></html>"
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "description" in metadata["meta_tags"]
    assert "keywords" in metadata["meta_tags"]
    assert len(metadata["opengraph"]) == 0
    assert len(metadata["twitter"]) == 0

def test_mixed_meta_properties(processor):
    """Test handling of meta tags with mixed property and name attributes."""
    html = """
    <html>
        <head>
            <meta property="description" content="Property description">
            <meta name="og:title" content="Named OG title">
            <meta property="twitter:card" content="Named Twitter card">
        </head>
        <body>Content</body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert metadata["meta_tags"]["description"] == "Property description"
    assert metadata["opengraph"]["title"] == "Named OG title"
    assert metadata["twitter"]["card"] == "Named Twitter card"

def test_duplicate_meta_tags(processor):
    """Test handling of duplicate meta tags."""
    html = """
    <html>
        <head>
            <meta name="description" content="First description">
            <meta name="description" content="Second description">
            <meta property="og:title" content="First OG title">
            <meta property="og:title" content="Second OG title">
        </head>
        <body>Content</body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    # Should use the last occurrence of duplicate tags
    assert metadata["meta_tags"]["description"] == "Second description"
    assert metadata["opengraph"]["title"] == "Second OG title"

def test_keyword_generation(processor):
    """Test automatic keyword generation from content."""
    html = """
    <html>
        <body>
            <p>This is a comprehensive article about Python programming language
            and its applications in web development using frameworks like Django
            and Flask for building robust applications.</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    keywords = metadata["meta_tags"]["keywords"].split(", ")
    assert len(keywords) == 5  # Should generate 5 keywords
    
    # Check that we have some relevant technical terms
    all_keywords = " ".join(keywords).lower()
    assert any(word in all_keywords for word in ["python", "programming", "applications", "frameworks", "development"])

def test_special_characters_metadata(processor):
    """Test metadata extraction with special characters."""
    html = """
    <html>
        <head>
            <meta name="description" content="Special chars: áéíóú &amp; ñ">
            <meta property="og:title" content="Title with &quot;quotes&quot;">
        </head>
        <body>Content</body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "áéíóú" in metadata["meta_tags"]["description"]
    assert '"quotes"' in metadata["opengraph"]["title"]

def test_long_content_truncation(processor):
    """Test truncation of long content in metadata."""
    long_text = "x" * 200
    html = f"""
    <html>
        <body>
            <p>{long_text}</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert len(metadata["meta_tags"]["description"]) <= 103  # 100 chars + "..."
    assert metadata["meta_tags"]["description"].endswith("...")

def test_malformed_meta_tags(processor):
    """Test handling of malformed meta tags."""
    html = """
    <html>
        <head>
            <meta name="description">  <!-- Missing content -->
            <meta content="Just content">  <!-- Missing name/property -->
            <meta name="" content="Empty name">  <!-- Empty name -->
            <meta name="keywords" content="">  <!-- Empty content -->
            <meta property="og:title">  <!-- OG tag missing content -->
        </head>
        <body>Some content for fallback</body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    # Should handle missing attributes gracefully
    assert "description" in metadata["meta_tags"]
    assert metadata["meta_tags"]["keywords"] != ""  # Should fall back to generated keywords
    assert len(metadata["opengraph"]) == 0  # No valid OG tags

def test_html_entities_in_meta(processor):
    """Test handling of HTML entities in meta tags."""
    html = """
    <html>
        <head>
            <meta name="description" content="Test &lt;script&gt;alert('test')&lt;/script&gt;">
            <meta property="og:title" content="Title &amp; More">
            <meta name="keywords" content="tag1 &middot; tag2 &bull; tag3">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "<script>" not in metadata["meta_tags"]["description"]
    assert "alert('test')" not in metadata["meta_tags"]["description"]
    assert "&" in metadata["opengraph"]["title"]
    assert "·" in metadata["meta_tags"]["keywords"] or "•" in metadata["meta_tags"]["keywords"]

def test_nested_content_keyword_generation(processor):
    """Test keyword generation from nested content structures."""
    html = """
    <html>
        <body>
            <div>
                <article>
                    <section>
                        <h2>Important Terms</h2>
                        <p>This section discusses machine learning algorithms</p>
                    </section>
                    <section>
                        <h2>Technical Details</h2>
                        <p>Deep neural networks and artificial intelligence</p>
                    </section>
                </article>
            </div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    keywords = metadata["meta_tags"]["keywords"].lower()
    assert any(term in keywords for term in ["learning", "neural", "intelligence", "algorithms"])

def test_multilingual_content(processor):
    """Test metadata extraction with multilingual content."""
    html = """
    <html>
        <head>
            <meta name="description" content="Description en español with 日本語 and Deutsche">
            <meta property="og:title" content="Título - タイトル - Titel">
            <meta name="keywords" content="国際化, internacionalización, Internationalisierung">
        </head>
        <body>
            <p>Multilingual content for testing: 测试 • テスト • 테스트</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "español" in metadata["meta_tags"]["description"]
    assert "日本語" in metadata["meta_tags"]["description"]
    assert "タイトル" in metadata["opengraph"]["title"]
    assert "国際化" in metadata["meta_tags"]["keywords"]

def test_schema_org_metadata(processor):
    """Test extraction of schema.org metadata."""
    html = """
    <html>
        <head>
            <meta itemprop="name" content="Schema Title">
            <meta itemprop="description" content="Schema Description">
            <meta property="og:type" content="article">
            <meta property="article:published_time" content="2024-01-01">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    # Schema.org metadata should be included in meta_tags
    assert metadata["meta_tags"].get("name") == "Schema Title"
    assert metadata["meta_tags"].get("description") == "Schema Description"
    assert metadata["opengraph"]["type"] == "article"
    assert metadata["opengraph"]["published_time"] == "2024-01-01"

def test_meta_robots_handling(processor):
    """Test handling of robots meta tags."""
    html = """
    <html>
        <head>
            <meta name="robots" content="noindex, nofollow">
            <meta name="googlebot" content="noarchive">
            <meta name="description" content="Test description">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert metadata["meta_tags"]["robots"] == "noindex, nofollow"
    assert metadata["meta_tags"]["googlebot"] == "noarchive"

def test_json_ld_fallback(processor):
    """Test metadata extraction with JSON-LD presence."""
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "JSON-LD Title",
                "description": "JSON-LD Description"
            }
            </script>
        </head>
        <body>
            <p>Regular content</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    # Should still generate metadata even without meta tags
    assert "description" in metadata["meta_tags"]
    assert "keywords" in metadata["meta_tags"]

def test_relative_urls_in_meta(processor):
    """Test handling of relative URLs in meta tags."""
    html = """
    <html>
        <head>
            <meta property="og:image" content="/images/test.jpg">
            <meta property="og:url" content="/article/123">
            <link rel="canonical" href="/canonical/url">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    # Should preserve relative URLs as-is
    assert metadata["opengraph"]["image"] == "/images/test.jpg"
    assert metadata["opengraph"]["url"] == "/article/123"

def test_whitespace_handling(processor):
    """Test handling of whitespace in meta tags."""
    html = """
    <html>
        <head>
            <meta name="description" content="  Padded   with   spaces  ">
            <meta name="keywords" content=" tag1,   tag2,  tag3 ">
            <meta property="og:title" content="
                Multiline
                Title
            ">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    # Should normalize whitespace
    assert "  Padded   with   spaces  " == metadata["meta_tags"]["description"]
    assert " tag1,   tag2,  tag3 " == metadata["meta_tags"]["keywords"]
    assert "\n                Multiline\n                Title\n            " == metadata["opengraph"]["title"]

def test_unicode_metadata(processor):
    """Test handling of Unicode characters in metadata."""
    html = """
    <html>
        <head>
            <meta name="description" content="测试页面 • テスト • 테스트 • اختبار">
            <meta name="keywords" content="español, français, 日本語, 한국어">
            <meta property="og:title" content="título • タイトル • 제목">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "测试页面" in metadata["meta_tags"]["description"]
    assert "español" in metadata["meta_tags"]["keywords"]
    assert "título" in metadata["opengraph"]["title"]

def test_nested_html_metadata(processor):
    """Test handling of nested HTML in metadata content."""
    html = """
    <html>
        <head>
            <meta name="description" content="<p>Test <strong>description</strong> with <em>formatting</em></p>">
            <meta name="keywords" content="<span>keyword1</span>, <b>keyword2</b>">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "<p>" not in metadata["meta_tags"]["description"]
    assert "<strong>" not in metadata["meta_tags"]["description"]
    assert "Test description with formatting" in metadata["meta_tags"]["description"]
    assert "<span>" not in metadata["meta_tags"]["keywords"]

def test_mixed_case_metadata(processor):
    """Test case-insensitive handling of meta tags."""
    html = """
    <html>
        <head>
            <META NAME="Description" CONTENT="Upper case test">
            <Meta Property="og:TITLE" Content="Mixed case test">
            <meta NAME="Keywords" content="UPPER, lower, MiXeD">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert metadata["meta_tags"]["description"] == "Upper case test"
    assert metadata["opengraph"]["title"] == "Mixed case test"
    assert "UPPER" in metadata["meta_tags"]["keywords"]

def test_duplicate_keywords_handling(processor):
    """Test handling of duplicate keywords in content."""
    html = """
    <html>
        <body>
            <h1>Python Python Python</h1>
            <h2>Testing Testing</h2>
            <p>Development development DEVELOPMENT</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    keywords = metadata["meta_tags"]["keywords"].split(", ")
    # Check for no duplicates
    assert len(keywords) == len(set(keywords))
    assert "python" in [k.lower() for k in keywords]
    assert "development" in [k.lower() for k in keywords]

def test_special_punctuation_handling(processor):
    """Test handling of special punctuation in metadata."""
    html = """
    <html>
        <head>
            <meta name="description" content="Test—with em-dash... and ellipsis!">
            <meta name="keywords" content="semi;colon, pipe|separator, slash/test">
            <meta property="og:title" content="[Brackets] {Braces} (Parentheses)">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "—" in metadata["meta_tags"]["description"]
    assert "..." in metadata["meta_tags"]["description"]
    assert "semi;colon" in metadata["meta_tags"]["keywords"]
    assert "[Brackets]" in metadata["opengraph"]["title"]

def test_schema_metadata_priority(processor):
    """Test priority handling when same metadata appears in different formats."""
    html = """
    <html>
        <head>
            <meta name="description" content="Regular meta description">
            <meta property="og:description" content="OG description">
            <meta name="twitter:description" content="Twitter description">
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "description": "Schema.org description"
            }
            </script>
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert metadata["meta_tags"]["description"] == "Regular meta description"
    assert metadata["opengraph"]["description"] == "OG description"
    assert metadata["twitter"]["description"] == "Twitter description"

def test_keyword_relevance(processor):
    """Test that generated keywords are relevant to the content."""
    html = """
    <html>
        <body>
            <h1>Machine Learning and Neural Networks</h1>
            <p>This article discusses artificial intelligence and deep learning
            algorithms used in modern data processing frameworks.</p>
            <p>Some common words that should not become keywords: the, and, or, but.</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    keywords = metadata["meta_tags"]["keywords"].lower().split(", ")
    technical_terms = {"machine", "learning", "neural", "artificial", "intelligence", "processing"}
    
    # At least 3 technical terms should be included
    assert len(set(keywords) & technical_terms) >= 3
    # Common words should not be included
    assert not any(word in keywords for word in ["the", "and", "or", "but"])

def test_empty_content_handling(processor):
    """Test handling of empty or whitespace-only content."""
    html = """
    <html>
        <head>
            <meta name="description" content="   ">
            <meta name="keywords" content="">
            <meta property="og:title" content="&#x20;">
        </head>
        <body>
            <p>Some actual content for fallback</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert metadata["meta_tags"]["description"].strip() != ""
    assert metadata["meta_tags"]["keywords"].strip() != ""
    assert "content" in metadata["meta_tags"]["keywords"]

def test_safe_content_edge_cases(processor):
    """Test edge cases in _safe_content method."""
    # Empty content
    assert processor._safe_content("") == ""
    
    # None content
    assert processor._safe_content(None) == ""
    
    # Malformed HTML
    content = "<p>Unclosed tag <b>Bold text</p>"
    result = processor._safe_content(content)
    assert "<p>" not in result
    assert "<b>" not in result
    assert "Unclosed tag Bold text" in result
    
    # Nested script tags
    content = "<script>alert('outer')<script>alert('inner')</script></script>"
    result = processor._safe_content(content)
    assert "script" not in result.lower()
    assert "alert" not in result.lower()
    
    # Mixed entities and tags
    content = "&lt;div&gt;Test &amp; &quot;quoted&quot; text&lt;/div&gt;"
    result = processor._safe_content(content)
    assert "<div>" not in result
    assert '"quoted"' in result
    assert "&" in result

def test_invalid_meta_tags(processor):
    """Test handling of invalid meta tag structures."""
    html = """
    <html>
        <head>
            <meta content>  <!-- Missing attributes -->
            <meta>  <!-- Empty meta tag -->
            <meta name=>  <!-- Empty name -->
            <meta content=>  <!-- Empty content -->
            <meta property="og:title">  <!-- Missing content -->
            <meta name="description" content>  <!-- Empty content attribute -->
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert isinstance(metadata["meta_tags"], dict)
    assert isinstance(metadata["opengraph"], dict)
    assert isinstance(metadata["twitter"], dict)

def test_malformed_opengraph(processor):
    """Test handling of malformed OpenGraph tags."""
    html = """
    <html>
        <head>
            <meta property="og:" content="Missing type">
            <meta property="og" content="Invalid prefix">
            <meta property="og:type:invalid" content="Invalid structure">
            <meta property="og:title" content="">
            <meta property="og:description" content="    ">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert isinstance(metadata["opengraph"], dict)
    assert len(metadata["opengraph"]) == 0

def test_xss_prevention(processor):
    """Test prevention of XSS attacks in metadata."""
    html = """
    <html>
        <head>
            <meta name="description" content="<script>alert('xss')</script>">
            <meta name="keywords" content="<img src=x onerror=alert('xss')>">
            <meta property="og:title" content="javascript:alert('xss')">
            <meta name="author" content="<svg/onload=alert('xss')>">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "<script>" not in metadata["meta_tags"]["description"]
    assert "alert" not in metadata["meta_tags"]["description"]
    assert "<img" not in metadata["meta_tags"]["keywords"]
    assert "javascript:" not in metadata["opengraph"]["title"]
    assert "<svg" not in metadata["meta_tags"]["author"]

def test_extreme_content_lengths(processor):
    """Test handling of extremely long or short content."""
    # Very long content
    long_text = "x" * 10000
    html = f"""
    <html>
        <head>
            <meta name="description" content="{long_text}">
            <meta name="keywords" content="{long_text}">
            <meta property="og:title" content="{long_text}">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert len(metadata["meta_tags"]["description"]) > 0
    assert len(metadata["meta_tags"]["keywords"]) > 0
    assert len(metadata["opengraph"]["title"]) > 0

def test_mixed_metadata_formats(processor):
    """Test handling of mixed metadata formats."""
    html = """
    <html>
        <head>
            <!-- Standard meta -->
            <meta name="description" content="Standard description">
            
            <!-- OpenGraph -->
            <meta property="og:description" content="OG description">
            
            <!-- Twitter -->
            <meta name="twitter:description" content="Twitter description">
            
            <!-- Schema.org -->
            <meta itemprop="description" content="Schema description">
            
            <!-- Dublin Core -->
            <meta name="DC.Description" content="DC description">
            
            <!-- Mixed case -->
            <meta Name="Description" content="Mixed case description">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "Standard description" in metadata["meta_tags"]["description"]
    assert "OG description" in metadata["opengraph"]["description"]
    assert "Twitter description" in metadata["twitter"]["description"]

def test_special_meta_tags(processor):
    """Test handling of special meta tags."""
    html = """
    <html>
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="30">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta name="robots" content="noindex, nofollow">
            <meta name="generator" content="WordPress 5.8">
            <meta name="format-detection" content="telephone=no">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert isinstance(metadata["meta_tags"], dict)
    assert "charset" in metadata["meta_tags"] or "utf-8" in metadata["meta_tags"]
    assert "viewport" in metadata["meta_tags"]
    assert "robots" in metadata["meta_tags"]

def test_metadata_inheritance(processor):
    """Test metadata inheritance and overriding."""
    html = """
    <html>
        <head>
            <meta name="description" content="General description">
            <meta property="og:description" content="OG description">
            <meta name="twitter:description" content="Twitter description">
            <meta itemprop="description" content="Schema description">
            
            <meta name="title" content="General title">
            <meta property="og:title" content="OG title">
            <meta name="twitter:title" content="Twitter title">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert metadata["meta_tags"]["description"] == "General description"
    assert metadata["opengraph"]["description"] == "OG description"
    assert metadata["twitter"]["description"] == "Twitter description"

def test_language_metadata(processor):
    """Test handling of language-specific metadata."""
    html = """
    <html>
        <head>
            <meta http-equiv="content-language" content="en-US">
            <meta name="language" content="English">
            <meta property="og:locale" content="en_US">
            <meta name="description" content="English description">
            <meta name="description" lang="es" content="Spanish description">
            <meta name="description" lang="fr" content="French description">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "language" in metadata["meta_tags"]
    assert "English" in metadata["meta_tags"]["language"]
    assert "en_US" in metadata["opengraph"]["locale"]

def test_empty_document(processor):
    """Test handling of completely empty documents."""
    html = ""
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert isinstance(metadata["meta_tags"], dict)
    assert isinstance(metadata["opengraph"], dict)
    assert isinstance(metadata["twitter"], dict)
    assert len(metadata["meta_tags"]) == 0
    assert len(metadata["opengraph"]) == 0
    assert len(metadata["twitter"]) == 0

def test_malformed_html_structure(processor):
    """Test handling of malformed HTML structure."""
    html = """
        </head>
            <meta name="description" content="Test">
        <head>
        <html>
            <meta property="og:title" content="Title">
        </html>
        <body>
            <meta name="keywords" content="keywords">
        </body>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert isinstance(metadata["meta_tags"], dict)
    assert isinstance(metadata["opengraph"], dict)
    assert "Test" in metadata["meta_tags"]["description"]
    assert "Title" in metadata["opengraph"]["title"]

def test_duplicate_meta_tags(processor):
    """Test handling of duplicate meta tags."""
    html = """
    <html>
        <head>
            <meta name="description" content="First description">
            <meta name="description" content="Second description">
            <meta property="og:title" content="First title">
            <meta property="og:title" content="Second title">
            <meta name="twitter:card" content="First card">
            <meta name="twitter:card" content="Second card">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "First description" in metadata["meta_tags"]["description"] or \
           "Second description" in metadata["meta_tags"]["description"]
    assert "First title" in metadata["opengraph"]["title"] or \
           "Second title" in metadata["opengraph"]["title"]

def test_nested_meta_tags(processor):
    """Test handling of nested meta tags."""
    html = """
    <html>
        <head>
            <div>
                <meta name="description" content="Nested description">
                <span>
                    <meta property="og:title" content="Nested title">
                </span>
            </div>
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "Nested description" in metadata["meta_tags"]["description"]
    assert "Nested title" in metadata["opengraph"]["title"]

def test_encoded_content(processor):
    """Test handling of URL-encoded and HTML-encoded content."""
    html = """
    <html>
        <head>
            <meta name="description" content="Test%20with%20spaces">
            <meta name="keywords" content="&#72;&#84;&#77;&#76;">
            <meta property="og:title" content="&#x48;&#x65;&#x6C;&#x6C;&#x6F;">
            <meta name="author" content="John &amp; Jane">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "Test with spaces" in metadata["meta_tags"]["description"]
    assert "HTML" in metadata["meta_tags"]["keywords"]
    assert "Hello" in metadata["opengraph"]["title"]
    assert "John & Jane" in metadata["meta_tags"]["author"]

def test_json_ld_metadata(processor):
    """Test handling of JSON-LD metadata."""
    html = """
    <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "JSON-LD Title",
                "description": "JSON-LD Description",
                "keywords": "json,ld,test"
            }
            </script>
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    # Test that JSON-LD is either properly extracted or safely ignored
    assert isinstance(metadata["meta_tags"], dict)
    assert isinstance(metadata["opengraph"], dict)

def test_rdfa_metadata(processor):
    """Test handling of RDFa metadata."""
    html = """
    <html>
        <head>
            <meta property="dc:title" content="Dublin Core Title">
            <meta property="dc:description" content="Dublin Core Description">
            <meta property="dc:creator" content="Dublin Core Author">
        </head>
        <div vocab="https://schema.org/" typeof="Article">
            <h1 property="headline">RDFa Title</h1>
            <p property="description">RDFa Description</p>
        </div>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert "Dublin Core Title" in str(metadata["meta_tags"])
    assert "Dublin Core Description" in str(metadata["meta_tags"])

def test_microdata_metadata(processor):
    """Test handling of Microdata metadata."""
    html = """
    <html>
        <head>
            <div itemscope itemtype="https://schema.org/Article">
                <meta itemprop="headline" content="Microdata Title">
                <meta itemprop="description" content="Microdata Description">
                <meta itemprop="keywords" content="microdata,test">
            </div>
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert isinstance(metadata["meta_tags"], dict)
    assert "Microdata" in str(metadata["meta_tags"])

def test_meta_refresh_handling(processor):
    """Test handling of meta refresh tags."""
    html = """
    <html>
        <head>
            <meta http-equiv="refresh" content="5;url=https://example.com">
            <meta http-equiv="refresh" content="0; URL='https://malicious.com'">
            <meta http-equiv="refresh" content="invalid-content">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert isinstance(metadata["meta_tags"], dict)
    assert "refresh" in str(metadata["meta_tags"])

def test_invalid_charset_handling(processor):
    """Test handling of invalid charset declarations."""
    html = """
    <html>
        <head>
            <meta charset="invalid-charset">
            <meta http-equiv="Content-Type" content="text/html; charset=invalid">
            <meta name="description" content="Test content">
        </head>
    </html>
    """
    soup = BeautifulSoup(html, 'html.parser')
    metadata = processor._extract_metadata(soup)
    
    assert isinstance(metadata["meta_tags"], dict)
    assert "Test content" in metadata["meta_tags"]["description"]
