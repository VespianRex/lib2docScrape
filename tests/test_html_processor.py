import pytest
from bs4 import BeautifulSoup
from src.processors.html_processor import HTMLProcessor

@pytest.fixture
def processor():
    return HTMLProcessor()

def test_basic_html_processing(processor):
    """Test basic HTML processing functionality."""
    html = """
    <html>
        <head>
            <title>Test Page</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Main Title</h1>
            <p>Test paragraph</p>
            <div>Test div</div>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert result.title.string == "Test Page"
    assert result.find("h1").string == "Main Title"

def test_empty_html(processor):
    """Test processing of empty HTML."""
    empty_cases = ["", " ", "\n", None]
    for html in empty_cases:
        result = processor.process_html(html)
        assert isinstance(result, BeautifulSoup)
        assert result.find("body") is None

def test_malformed_html(processor):
    """Test processing of malformed HTML."""
    html = """
        </div>
        <p>Unclosed paragraph
        <div>
        <span>Unclosed span
        </p>
        <a href="test">Unclosed link
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert "Unclosed paragraph" in result.text
    assert "Unclosed span" in result.text
    assert "Unclosed link" in result.text

def test_html_encoding(processor):
    """Test handling of different HTML encodings."""
    html_cases = [
        # UTF-8 with BOM
        b'\xef\xbb\xbf<html><body>UTF-8 BOM test</body></html>',
        # UTF-16 LE
        b'\xff\xfe<\x00h\x00t\x00m\x00l\x00>\x00<\x00b\x00o\x00d\x00y\x00>\x00U\x00T\x00F\x00-\x001\x006\x00 \x00t\x00e\x00s\x00t\x00<\x00/\x00b\x00o\x00d\x00y\x00>\x00<\x00/\x00h\x00t\x00m\x00l\x00>\x00',
        # ASCII
        b'<html><body>ASCII test</body></html>',
        # Latin-1
        'á é í ó ú'.encode('latin-1'),
    ]
    
    for html in html_cases:
        result = processor.process_html(html)
        assert isinstance(result, BeautifulSoup)
        assert result.find("body") is not None

def test_html_entities(processor):
    """Test handling of HTML entities."""
    html = """
    <html>
        <body>
            <p>&lt;script&gt;alert(1)&lt;/script&gt;</p>
            <p>&amp; &quot; &apos; &gt; &lt;</p>
            <p>&#72;&#84;&#77;&#76;</p>
            <p>&#x48;&#x54;&#x4D;&#x4C;</p>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert "<script>alert(1)</script>" in result.text
    assert '& " \' > <' in result.text
    assert "HTML" in result.text

def test_doctype_handling(processor):
    """Test handling of different DOCTYPE declarations."""
    doctypes = [
        '<!DOCTYPE html>',
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">',
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">',
        '',  # No DOCTYPE
    ]
    
    for doctype in doctypes:
        html = f"{doctype}<html><body>Test</body></html>"
        result = processor.process_html(html)
        assert isinstance(result, BeautifulSoup)
        assert result.find("body").string == "Test"

def test_comment_handling(processor):
    """Test handling of HTML comments."""
    html = """
    <html>
        <body>
            <!-- Regular comment -->
            <p>Visible text</p>
            <!-- Multi-line
                 comment -->
            <div>More text</div>
            <!--[if IE]>IE specific<![endif]-->
            <!-- </script> -->
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert "Visible text" in result.text
    assert "More text" in result.text
    assert "Regular comment" not in result.text
    assert "Multi-line" not in result.text
    assert "IE specific" not in result.text

def test_script_handling(processor):
    """Test handling of script tags."""
    html = """
    <html>
        <head>
            <script>
                alert('test');
                document.write('test');
            </script>
            <script type="text/javascript">
                console.log('test');
            </script>
        </head>
        <body>
            <script>alert('test');</script>
            <noscript>JavaScript is disabled</noscript>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert "alert('test')" not in result.text
    assert "document.write('test')" not in result.text
    assert "console.log('test')" not in result.text

def test_style_handling(processor):
    """Test handling of style tags and attributes."""
    html = """
    <html>
        <head>
            <style>
                body { background: red; }
                p { color: blue; }
            </style>
        </head>
        <body>
            <p style="color: green;">Styled text</p>
            <div style="background: url('test.jpg');">Background</div>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert "background: red" not in result.text
    assert "color: blue" not in result.text
    assert "Styled text" in result.text
    assert "Background" in result.text

def test_meta_charset_handling(processor):
    """Test handling of charset meta tags."""
    html_templates = [
        '<meta charset="{}">',
        '<meta http-equiv="Content-Type" content="text/html; charset={}">',
    ]
    charsets = ['utf-8', 'UTF-8', 'iso-8859-1', 'windows-1252', 'invalid-charset']
    
    for template in html_templates:
        for charset in charsets:
            html = f"<html><head>{template.format(charset)}</head><body>Test</body></html>"
            result = processor.process_html(html)
            assert isinstance(result, BeautifulSoup)
            assert result.find("body").string == "Test"

def test_iframe_handling(processor):
    """Test handling of iframe elements."""
    html = """
    <html>
        <body>
            <iframe src="https://example.com"></iframe>
            <iframe srcdoc="<p>Inline frame content</p>"></iframe>
            <iframe src="javascript:alert(1)"></iframe>
            <iframe src="data:text/html,<p>Data URL content</p>"></iframe>
            <iframe></iframe>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert len(result.find_all("iframe")) > 0
    assert "javascript:alert" not in str(result)

def test_form_handling(processor):
    """Test handling of form elements."""
    html = """
    <html>
        <body>
            <form action="https://example.com/submit" method="POST">
                <input type="text" name="username" value="test">
                <input type="password" name="password" value="secret">
                <input type="hidden" name="token" value="12345">
                <textarea name="comment">Test comment</textarea>
                <select name="option">
                    <option value="1">One</option>
                    <option value="2">Two</option>
                </select>
                <button type="submit">Submit</button>
            </form>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert result.find("form") is not None
    assert "secret" not in str(result)  # Password should be sanitized
    assert "Test comment" in str(result)
    assert "Submit" in str(result)

def test_svg_handling(processor):
    """Test handling of SVG elements."""
    html = """
    <html>
        <body>
            <svg width="100" height="100">
                <circle cx="50" cy="50" r="40" stroke="black" fill="red" />
                <script>alert(1)</script>
                <text x="10" y="20">SVG Text</text>
                <a xlink:href="javascript:alert(1)">Link</a>
            </svg>
            <svg>
                <use href="external.svg#icon"></use>
            </svg>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert result.find("svg") is not None
    assert "javascript:alert" not in str(result)
    assert "SVG Text" in str(result)

def test_math_ml_handling(processor):
    """Test handling of MathML elements."""
    html = """
    <html>
        <body>
            <math>
                <mi>x</mi>
                <mo>+</mo>
                <mn>1</mn>
                <mo>=</mo>
                <mn>0</mn>
                <annotation encoding="application/x-python">x + 1 = 0</annotation>
            </math>
            <math>
                <semantics>
                    <mrow>
                        <msup><mi>a</mi><mn>2</mn></msup>
                        <mo>+</mo>
                        <msup><mi>b</mi><mn>2</mn></msup>
                    </mrow>
                </semantics>
            </math>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert result.find("math") is not None
    assert "x + 1 = 0" in str(result)

def test_custom_elements(processor):
    """Test handling of custom elements."""
    html = """
    <html>
        <body>
            <custom-element>Custom content</custom-element>
            <x-component>Component content</x-component>
            <my-widget data-value="test">Widget content</my-widget>
            <web-component>
                <shadow-root>Shadow content</shadow-root>
            </web-component>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert "Custom content" in str(result)
    assert "Component content" in str(result)
    assert "Widget content" in str(result)
    assert "Shadow content" in str(result)

def test_data_attributes(processor):
    """Test handling of data attributes."""
    html = """
    <html>
        <body>
            <div data-test="value">Test div</div>
            <p data-info='{"key": "value"}'>Test paragraph</p>
            <span data-role="button" data-action="click">Test span</span>
            <a data-tracking="analytics" data-source="test">Test link</a>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert result.find(attrs={"data-test": "value"}) is not None
    assert result.find(attrs={"data-info": '{"key": "value"}'}) is not None
    assert result.find(attrs={"data-role": "button"}) is not None

def test_conditional_comments(processor):
    """Test handling of conditional comments."""
    html = """
    <html>
        <body>
            <!--[if IE]>
            <div>IE specific content</div>
            <![endif]-->
            <!--[if gt IE 8]>
            <div>IE 9+ content</div>
            <![endif]-->
            <!--[if !IE]>-->
            <div>Non-IE content</div>
            <!--<![endif]-->
            <!-- Regular comment -->
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert "IE specific content" not in str(result)
    assert "Regular comment" not in str(result)

def test_template_handling(processor):
    """Test handling of template elements."""
    html = """
    <html>
        <body>
            <template id="my-template">
                <div>Template content</div>
                <script>alert(1)</script>
                <style>body { color: red; }</style>
            </template>
            <template>
                <slot name="content">Default content</slot>
            </template>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert result.find("template") is not None
    assert "Template content" in str(result)
    assert "alert(1)" not in str(result)

def test_picture_source_handling(processor):
    """Test handling of picture and source elements."""
    html = """
    <html>
        <body>
            <picture>
                <source srcset="large.jpg" media="(min-width: 800px)">
                <source srcset="medium.jpg" media="(min-width: 400px)">
                <source srcset="small.jpg">
                <img src="fallback.jpg" alt="Test image">
            </picture>
            <picture>
                <source srcset="image.webp" type="image/webp">
                <source srcset="image.jpg" type="image/jpeg">
                <img src="image.png" alt="Another test">
            </picture>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert result.find("picture") is not None
    assert result.find("source") is not None
    assert result.find("img") is not None
    assert "Test image" in str(result)
    assert "Another test" in str(result)

def test_unicode_handling(processor):
    """Test handling of Unicode characters and normalization."""
    html = """
    <html>
        <body>
            <p>UTF-8 Characters: </p>
            <p>Emoji: </p>
            <p>Special Characters: é è à ñ ü ö</p>
            <p>Math Symbols: ∑ ∫ ∏ √ ∂</p>
            <p>Currency Symbols: € £ ¥ ₹ ₽</p>
            <div>Mixed Content: Hello  with </div>
        </body>
    </html>
    """
    result = processor.process_html(html)
    assert isinstance(result, BeautifulSoup)
    assert "" in str(result)
    assert "" in str(result)
    assert "é è à" in str(result)
    assert "∑ ∫ ∏" in str(result)
    assert "€ £ ¥" in str(result)
