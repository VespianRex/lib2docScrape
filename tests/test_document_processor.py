import pytest
from bs4 import BeautifulSoup
from src.processors.document_processor import DocumentProcessor

@pytest.fixture
def processor():
    return DocumentProcessor()

def test_basic_document_processing(processor):
    """Test basic document processing functionality."""
    html = """
    <html>
        <head>
            <title>Test Document</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Main Title</h1>
            <p>Test paragraph</p>
            <div>Test div</div>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "title" in result
    assert "content" in result
    assert "metadata" in result
    assert "links" in result

def test_empty_document(processor):
    """Test processing of empty documents."""
    empty_cases = ["", " ", "\n", None]
    for html in empty_cases:
        result = processor.process_document(html, "https://example.com")
        assert isinstance(result, dict)
        assert result["title"] == ""
        assert result["content"] == ""
        assert isinstance(result["metadata"], dict)
        assert isinstance(result["links"], list)

def test_document_with_no_title(processor):
    """Test processing document without title."""
    html = """
    <html>
        <body>
            <p>Content without title</p>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert result["title"] == ""
    assert "Content without title" in result["content"]

def test_document_with_multiple_titles(processor):
    """Test processing document with multiple title elements."""
    html = """
    <html>
        <head>
            <title>First Title</title>
            <title>Second Title</title>
        </head>
        <body>
            <h1>Heading Title</h1>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "First Title" in result["title"] or "Second Title" in result["title"]

def test_document_with_complex_content(processor):
    """Test processing document with complex content structure."""
    html = """
    <html>
        <body>
            <article>
                <h1>Article Title</h1>
                <section>
                    <h2>Section 1</h2>
                    <p>Section 1 content</p>
                </section>
                <section>
                    <h2>Section 2</h2>
                    <p>Section 2 content</p>
                </section>
            </article>
            <aside>
                <h3>Sidebar</h3>
                <p>Sidebar content</p>
            </aside>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Article Title" in result["content"]
    assert "Section 1" in result["content"]
    assert "Section 2" in result["content"]
    assert "Sidebar" in result["content"]

def test_document_with_invalid_url(processor):
    """Test processing document with invalid base URL."""
    html = "<html><body>Test content</body></html>"
    invalid_urls = [
        "",
        "not_a_url",
        "http:/example.com",
        "https://",
        "ftp://example.com",
    ]
    
    for url in invalid_urls:
        result = processor.process_document(html, url)
        assert isinstance(result, dict)
        assert isinstance(result["links"], list)
        assert "Test content" in result["content"]

def test_document_with_frames(processor):
    """Test processing document with frames and iframes."""
    html = """
    <html>
        <head>
            <title>Framed Document</title>
        </head>
        <frameset>
            <frame src="frame1.html" name="left">
            <frame src="frame2.html" name="right">
        </frameset>
        <body>
            <iframe src="iframe1.html"></iframe>
            <iframe src="iframe2.html"></iframe>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Framed Document" in result["title"]
    assert isinstance(result["links"], list)
    assert any("frame1.html" in link for link in result["links"])
    assert any("frame2.html" in link for link in result["links"])

def test_document_with_scripts(processor):
    """Test processing document with various script elements."""
    html = """
    <html>
        <head>
            <script>
                document.title = 'Dynamic Title';
                document.write('Dynamic content');
            </script>
            <script type="application/ld+json">
                {
                    "@type": "Article",
                    "headline": "JSON-LD Title"
                }
            </script>
        </head>
        <body>
            <script src="external.js"></script>
            <noscript>JavaScript is disabled</noscript>
            <p onclick="alert('test')">Test paragraph</p>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Dynamic Title" not in result["title"]
    assert "Dynamic content" not in result["content"]
    assert "Test paragraph" in result["content"]
    assert "JavaScript is disabled" in result["content"]

def test_document_with_meta_redirects(processor):
    """Test processing document with meta redirects."""
    html = """
    <html>
        <head>
            <meta http-equiv="refresh" content="0;url=https://example.com/new">
            <meta http-equiv="refresh" content="5;url=https://example.com/delayed">
            <title>Redirect Page</title>
        </head>
        <body>
            <p>Redirecting...</p>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Redirect Page" in result["title"]
    assert "Redirecting..." in result["content"]
    assert isinstance(result["metadata"], dict)
    assert "refresh" in str(result["metadata"])

def test_document_with_base_tag(processor):
    """Test processing document with base tag."""
    html = """
    <html>
        <head>
            <base href="https://different-base.com/subdir/">
            <title>Base Test</title>
        </head>
        <body>
            <a href="relative">Relative Link</a>
            <a href="/absolute">Absolute Link</a>
            <img src="image.jpg">
            <link rel="stylesheet" href="style.css">
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Base Test" in result["title"]
    assert isinstance(result["links"], list)
    assert any("different-base.com" in link for link in result["links"])

def test_document_with_special_content(processor):
    """Test processing document with special content types."""
    html = """
    <html>
        <head>
            <title>Special Content</title>
        </head>
        <body>
            <pre>Preformatted text
                with line breaks
                and    spaces</pre>
            <code>def test_function():
    pass</code>
            <blockquote>Quoted text</blockquote>
            <samp>Sample output</samp>
            <kbd>Ctrl + C</kbd>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Special Content" in result["title"]
    assert "Preformatted text" in result["content"]
    assert "def test_function" in result["content"]
    assert "Quoted text" in result["content"]
    assert "Sample output" in result["content"]
    assert "Ctrl + C" in result["content"]

def test_document_with_lists(processor):
    """Test processing document with various list types."""
    html = """
    <html>
        <head>
            <title>Lists Test</title>
        </head>
        <body>
            <ul>
                <li>Unordered item 1</li>
                <li>Unordered item 2
                    <ul>
                        <li>Nested item 1</li>
                        <li>Nested item 2</li>
                    </ul>
                </li>
            </ul>
            <ol>
                <li>Ordered item 1</li>
                <li>Ordered item 2</li>
            </ol>
            <dl>
                <dt>Term 1</dt>
                <dd>Definition 1</dd>
                <dt>Term 2</dt>
                <dd>Definition 2</dd>
            </dl>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Lists Test" in result["title"]
    assert "Unordered item" in result["content"]
    assert "Nested item" in result["content"]
    assert "Ordered item" in result["content"]
    assert "Term" in result["content"]
    assert "Definition" in result["content"]

def test_document_with_tables(processor):
    """Test processing document with tables."""
    html = """
    <html>
        <head>
            <title>Tables Test</title>
        </head>
        <body>
            <table>
                <caption>Test Table</caption>
                <thead>
                    <tr>
                        <th>Header 1</th>
                        <th>Header 2</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Cell 1</td>
                        <td>Cell 2</td>
                    </tr>
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="2">Footer</td>
                    </tr>
                </tfoot>
            </table>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Tables Test" in result["title"]
    assert "Test Table" in result["content"]
    assert "Header" in result["content"]
    assert "Cell" in result["content"]
    assert "Footer" in result["content"]

def test_document_with_forms(processor):
    """Test processing document with form elements."""
    html = """
    <html>
        <head>
            <title>Forms Test</title>
        </head>
        <body>
            <form action="/submit" method="post">
                <fieldset>
                    <legend>Personal Info</legend>
                    <label for="name">Name:</label>
                    <input type="text" id="name" name="name" value="John">
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" value="john@example.com">
                    <input type="hidden" name="token" value="12345">
                </fieldset>
                <textarea name="comments">Test comment</textarea>
                <select name="options">
                    <optgroup label="Group 1">
                        <option value="1">Option 1</option>
                        <option value="2">Option 2</option>
                    </optgroup>
                </select>
                <button type="submit">Submit</button>
            </form>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Forms Test" in result["title"]
    assert "Personal Info" in result["content"]
    assert "Name:" in result["content"]
    assert "Email:" in result["content"]
    assert "Test comment" in result["content"]
    assert "Option" in result["content"]
    assert "Submit" in result["content"]

def test_document_with_semantic_elements(processor):
    """Test processing document with semantic HTML5 elements."""
    html = """
    <html>
        <head>
            <title>Semantic HTML</title>
        </head>
        <body>
            <header>
                <nav>
                    <ul>
                        <li><a href="#home">Home</a></li>
                        <li><a href="#about">About</a></li>
                    </ul>
                </nav>
            </header>
            <main>
                <article>
                    <section>
                        <h1>Main Content</h1>
                        <p>Test paragraph</p>
                    </section>
                </article>
                <aside>
                    <h2>Sidebar</h2>
                    <p>Sidebar content</p>
                </aside>
            </main>
            <footer>
                <p>Footer content</p>
            </footer>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Semantic HTML" in result["title"]
    assert "Main Content" in result["content"]
    assert "Sidebar" in result["content"]
    assert "Footer content" in result["content"]
    assert "#home" in str(result["links"])
    assert "#about" in str(result["links"])

def test_document_with_media_elements(processor):
    """Test processing document with media elements."""
    html = """
    <html>
        <head>
            <title>Media Elements</title>
        </head>
        <body>
            <img src="test.jpg" alt="Test image">
            <audio src="test.mp3" controls>
                <source src="test.ogg" type="audio/ogg">
                Audio description
            </audio>
            <video src="test.mp4" poster="poster.jpg">
                <source src="test.webm" type="video/webm">
                <track src="captions.vtt" kind="captions">
                Video description
            </video>
            <picture>
                <source media="(min-width: 800px)" srcset="large.jpg">
                <source media="(min-width: 400px)" srcset="medium.jpg">
                <img src="small.jpg" alt="Responsive image">
            </picture>
            <figure>
                <img src="figure.jpg" alt="Figure image">
                <figcaption>Figure caption</figcaption>
            </figure>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Media Elements" in result["title"]
    assert "Test image" in result["content"]
    assert "Audio description" in result["content"]
    assert "Video description" in result["content"]
    assert "Responsive image" in result["content"]
    assert "Figure caption" in result["content"]
    assert any("test.jpg" in link for link in result["links"])

def test_document_with_interactive_elements(processor):
    """Test processing document with interactive elements."""
    html = """
    <html>
        <head>
            <title>Interactive Elements</title>
        </head>
        <body>
            <details>
                <summary>Click to expand</summary>
                Hidden content
            </details>
            <dialog open>
                Dialog content
            </dialog>
            <menu type="toolbar">
                <li><button type="button">Command 1</button></li>
                <li><button type="button">Command 2</button></li>
            </menu>
            <progress value="70" max="100">70%</progress>
            <meter value="0.6">60%</meter>
            <output name="result">Calculation result</output>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Interactive Elements" in result["title"]
    assert "Click to expand" in result["content"]
    assert "Hidden content" in result["content"]
    assert "Dialog content" in result["content"]
    assert "Command" in result["content"]
    assert "Calculation result" in result["content"]

def test_document_with_embedded_content(processor):
    """Test processing document with embedded content."""
    html = """
    <html>
        <head>
            <title>Embedded Content</title>
        </head>
        <body>
            <object data="test.swf" type="application/x-shockwave-flash">
                Flash content
            </object>
            <embed src="test.svg" type="image/svg+xml">
            <applet code="test.class">
                Java applet
            </applet>
            <iframe src="test.html">
                Iframe content
            </iframe>
            <portal src="portal.html">
                Portal content
            </portal>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Embedded Content" in result["title"]
    assert "Flash content" in result["content"]
    assert "Java applet" in result["content"]
    assert "Iframe content" in result["content"]
    assert "Portal content" in result["content"]
    assert any("test.html" in link for link in result["links"])

def test_document_with_ruby_annotations(processor):
    """Test processing document with Ruby annotations."""
    html = """
    <html>
        <head>
            <title>Ruby Annotations</title>
        </head>
        <body>
            <ruby>
                漢 <rp>(</rp><rt>かん</rt><rp>)</rp>
                字 <rp>(</rp><rt>じ</rt><rp>)</rp>
            </ruby>
            <ruby>
                明日 <rp>(</rp><rt>あした</rt><rp>)</rp>
            </ruby>
            <p>Text with <ruby>ruby<rt>annotation</rt></ruby> markup</p>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Ruby Annotations" in result["title"]
    assert "漢字" in result["content"]
    assert "明日" in result["content"]
    assert "ruby" in result["content"]
    assert "annotation" in result["content"]

def test_document_with_math_content(processor):
    """Test processing document with mathematical content."""
    html = """
    <html>
        <head>
            <title>Math Content</title>
        </head>
        <body>
            <math>
                <mi>x</mi>
                <mo>+</mo>
                <mn>1</mn>
                <mo>=</mo>
                <mn>0</mn>
            </math>
            <math display="block">
                <mrow>
                    <msup><mi>a</mi><mn>2</mn></msup>
                    <mo>+</mo>
                    <msup><mi>b</mi><mn>2</mn></msup>
                    <mo>=</mo>
                    <msup><mi>c</mi><mn>2</mn></msup>
                </mrow>
            </math>
        </body>
    </html>
    """
    result = processor.process_document(html, "https://example.com")
    assert isinstance(result, dict)
    assert "Math Content" in result["title"]
    assert "x + 1 = 0" in result["content"].replace(" ", "")
    assert "a2 + b2 = c2" in result["content"].replace(" ", "")
