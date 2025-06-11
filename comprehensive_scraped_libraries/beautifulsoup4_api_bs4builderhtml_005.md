# Untitled Document

**Library:** beautifulsoup4
**Section:** api/bs4.builder.html
**Source URL:** https://www.crummy.com/software/BeautifulSoup/bs4/doc/api/bs4.builder.html
**Scraped:** 2025-06-03T18:38:23.755836

---

## Document Information

- **Content Length:** 13,762 characters
- **Links Found:** 0
- **Headings Found:** 0
- **Has Code Blocks:** False
- **Has Tables:** False

---

## Content


bs4.builder package — Beautiful Soup 4.13.0 documentation
# bs4.builder package[¶](#bs4-builder-package "Link to this heading")
## Module contents[¶](#module-bs4.builder "Link to this heading")
\*class\* bs4.builder.DetectsXMLParsedAsHTML[¶](#bs4.builder.DetectsXMLParsedAsHTML "Link to this definition")
Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")
A mixin class for any class (a TreeBuilder, or some class used by a
TreeBuilder) that's in a position to detect whether an XML
document is being incorrectly parsed as HTML, and issue an
appropriate warning.
This requires being able to observe an incoming processing
instruction that might be an XML declaration, and also able to
observe tags as they're opened. If you can't do that for a given
[`TreeBuilder`](#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder"), there's a less reliable implementation based on
examining the raw markup.
LOOKS\\_LIKE\\_HTML\*: [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]\* \*= re.compile('<[^ +]html', re.IGNORECASE)\*[¶](#bs4.builder.DetectsXMLParsedAsHTML.LOOKS\_LIKE\_HTML "Link to this definition")
Regular expression for seeing if string markup has an tag.
LOOKS\\_LIKE\\_HTML\\_B\*: [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")]\* \*= re.compile(b'<[^ +]html', re.IGNORECASE)\*[¶](#bs4.builder.DetectsXMLParsedAsHTML.LOOKS\_LIKE\_HTML\_B "Link to this definition")
Regular expression for seeing if byte markup has an tag.
XML\\_PREFIX\*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")\* \*= '\*, \*preserve\\_whitespace\\_tags: Set[str] = \*, \*store\\_line\\_numbers: bool = \*, \*string\\_containers: Dict[str\*, \*Type[NavigableString]] = \*, \*empty\\_element\\_tags: Set[str] = \*, \*attribute\\_dict\\_class: Type[AttributeDict] = \*, \*attribute\\_value\\_list\\_class: Type[AttributeValueList] = \*)[¶](#bs4.builder.HTML5TreeBuilder "Link to this definition")
Bases: [`HTMLTreeBuilder`](#bs4.builder.HTMLTreeBuilder "bs4.builder.HTMLTreeBuilder")
Use [html5lib](https://github.com/html5lib/html5lib-python) to
build a tree.
Note that [`HTML5TreeBuilder`](#bs4.builder.HTML5TreeBuilder "bs4.builder.HTML5TreeBuilder") does not support some common HTML
[`TreeBuilder`](#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") features. Some of these features could theoretically
be implemented, but at the very least it's quite difficult,
because html5lib moves the parse tree around as it's being built.
Specifically:
\* This [`TreeBuilder`](#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") doesn't use different subclasses of
[`NavigableString`](../index.html#NavigableString "NavigableString") (e.g. [`Script`](../index.html#Script "Script")) based on the name of the tag
in which the string was found.
\* You can't use a [`SoupStrainer`](../index.html#SoupStrainer "SoupStrainer") to parse only part of a document.
NAME\*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")\* \*= 'html5lib'\*[¶](#bs4.builder.HTML5TreeBuilder.NAME "Link to this definition")
TRACKS\\_LINE\\_NUMBERS\*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")\* \*= True\*[¶](#bs4.builder.HTML5TreeBuilder.TRACKS\_LINE\_NUMBERS "Link to this definition")
html5lib can tell us which line number and position in the
original file is the source of an element.
features\*: [Sequence](https://docs.python.org/3/library/typing.html#typing.Sequence "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]\* \*= ['html5lib', 'permissive', 'html5', 'html']\*[¶](#bs4.builder.HTML5TreeBuilder.features "Link to this definition")
feed(\*markup: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")\*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.builder.HTML5TreeBuilder.feed "Link to this definition")
Run some incoming markup through some parsing process,
populating the [`BeautifulSoup`](bs4.html#bs4.BeautifulSoup "bs4.BeautifulSoup") object in `HTML5TreeBuilder.soup`.
test\\_fragment\\_to\\_document(\*fragment: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")\*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.builder.HTML5TreeBuilder.test\_fragment\_to\_document "Link to this definition")
See [`TreeBuilder`](#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder").
user\\_specified\\_encoding\*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")\*[¶](#bs4.builder.HTML5TreeBuilder.user\_specified\_encoding "Link to this definition")
\*class\* bs4.builder.HTMLParserTreeBuilder(\*parser\\_args: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None\*, \*parser\\_kwargs: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None\*, \*\\*\\*kwargs: [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")\*)[¶](#bs4.builder.HTMLParserTreeBuilder "Link to this definition")
Bases: [`HTMLTreeBuilder`](#bs4.builder.HTMLTreeBuilder "bs4.builder.HTMLTreeBuilder")
A Beautiful soup [`bs4.builder.TreeBuilder`](#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") that uses the
[`html.parser.HTMLParser`](https://docs.python.org/3/library/html.parser.html#html.parser.HTMLParser "(in Python v3.13)") parser, found in the Python
standard library.
NAME\*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")\* \*= 'html.parser'\*[¶](#bs4.builder.HTMLParserTreeBuilder.NAME "Link to this definition")
TRACKS\\_LINE\\_NUMBERS\*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")\* \*= True\*[¶](#bs4.builder.HTMLParserTreeBuilder.TRACKS\_LINE\_NUMBERS "Link to this definition")
The html.parser knows which line number and position in the
original file is the source of an element.
features\*: Iterable[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]\* \*= ['html.parser', 'html', 'strict']\*[¶](#bs4.builder.HTMLParserTreeBuilder.features "Link to this definition")
feed(\*markup: \\_RawMarkup\*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.builder.HTMLParserTreeBuilder.feed "Link to this definition")
Run incoming markup through some parsing process.
is\\_xml\*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")\* \*= False\*[¶](#bs4.builder.HTMLParserTreeBuilder.is\_xml "Link to this definition")
parser\\_args\*: Tuple[Iterable[Any], Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), Any]]\*[¶](#bs4.builder.HTMLParserTreeBuilder.parser\_args "Link to this definition")
picklable\*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")\* \*= True\*[¶](#bs4.builder.HTMLParserTreeBuilder.picklable "Link to this definition")
prepare\\_markup(\*markup: \\_RawMarkup\*, \*user\\_specified\\_encoding: \\_Encoding | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None\*, \*document\\_declared\\_encoding: \\_Encoding | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None\*, \*exclude\\_encodings: \\_Encodings | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None\*) → Iterable[Tuple[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), \\_Encoding | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)"), \\_Encoding | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)"), [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]][¶](#bs4.builder.HTMLParserTreeBuilder.prepare\_markup "Link to this definition")
Run any preliminary steps necessary to make incoming markup
acceptable to the parser.
Parameters:
\* \*\*markup\*\* -- Some markup -- probably a bytestring.
\* \*\*user\\_specified\\_encoding\*\* -- The user asked to try this encoding.
\* \*\*document\\_declared\\_encoding\*\* -- The markup itself claims to be
in this encoding.
\* \*\*exclude\\_encodings\*\* -- The user asked \\_not\\_ to try any of
these encodings.
Yield:
A series of 4-tuples: (markup, encoding, declared encoding,
has undergone character replacement)
Each 4-tuple represents a strategy for parsing the document.
This TreeBuilder uses Unicode, Dammit to convert the markup
into Unicode, so the `markup` element of the tuple will
always be a string.
\*class\* bs4.builder.HTMLTreeBuilder(\*multi\\_valued\\_attributes: Dict[str\*, \*Set[str]] = \*, \*preserve\\_whitespace\\_tags: Set[str] = \*, \*store\\_line\\_numbers: bool = \*, \*string\\_containers: Dict[str\*, \*Type[NavigableString]] = \*, \*empty\\_element\\_tags: Set[str] = \*, \*attribute\\_dict\\_class: Type[AttributeDict] = \*, \*attribute\\_value\\_list\\_class: Type[AttributeValueList] = \*)[¶](#bs4.builder.HTMLTreeBuilder "Link to this definition")
Bases: [`TreeBuilder`](#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder")
This TreeBuilder knows facts about HTML, such as which tags are treated
specially by the HTML standard.
DEFAULT\\_BLOCK\\_ELEMENTS\*: Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]\* \*= {'address', 'article', 'aside', 'blockquote', 'canvas', 'dd', 'div', 'dl', 'dt', 'fieldset', 'figcaption', 'figure', 'footer', 'form', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'li', 'main', 'nav', 'noscript', 'ol', 'output', 'p', 'pre', 'section', 'table', 'tfoot', 'ul', 'video'}\*[¶](#bs4.builder.HTMLTreeBuilder.DEFAULT\_BLOCK\_ELEMENTS "Link to this definition")
The HTML standard defines these tags as block-level elements. Beautiful
Soup does not treat these elements differently from other elements,
but it may do so eventually, and this information is available if
you need to use it.
DEFAULT\\_CDATA\\_LIST\\_ATTRIBUTES\*: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]]\* \*= {'\\*': {'accesskey', 'class', 'dropzone'}, 'a': {'rel', 'rev'}, 'area': {'rel'}, 'form': {'accept-charset'}, 'icon': {'sizes'}, 'iframe': {'sandbox'}, 'link': {'rel', 'rev'}, 'object': {'archive'}, 'output': {'for'}, 'td': {'headers'}, 'th': {'headers'}}\*[¶](#bs4.builder.HTMLTreeBuilder.DEFAULT\_CDATA\_LIST\_ATTRIBUTES "Link to this definition")
The HTML standard defines these attributes as containing a
space-separated list of values, not a single value. That is,
class="foo bar" means that the 'class' attribute has two values,
'foo' and 'bar', not the single value 'foo bar'. When we
encounter one of these attributes, we will parse its value into
a list of values if possible. Upon output, the list will be
converted back into a string.
DEFAULT\\_EMPTY\\_ELEMENT\\_TAGS\*: Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]\* \*= {'area', 'base', 'basefont', 'bgsound', 'br', 'col', 'command', 'embed', 'frame', 'hr', 'image', 'img', 'input', 'isindex', 'keygen', 'link', 'menuitem', 'meta', 'nextid', 'param', 'source', 'spacer', 'track', 'wbr'}\*[¶](#bs4.builder.HTMLTreeBuilder.DEFAULT\_EMPTY\_ELEMENT\_TAGS "Link to this definition")
Some HTML tags are defined as having no contents. Beautiful Soup
treats these specially.
DEFAULT\\_PRESERVE\\_WHITESPACE\\_TAGS\*: [set](https://docs.python.org/3/library/stdtypes.html#set "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]\* \*= {'pre', 'textarea'}\*[¶](#bs4.builder.HTMLTreeBuilder.DEFAULT\_PRESERVE\_WHITESPACE\_TAGS "Link to this definition")
By default, whitespace inside these HTML tags will be
preserved rather than being collapsed.
DEFAULT\\_STRING\\_CONTAINERS\*: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), Type[[bs4.element.NavigableString](bs4.html#bs4.element.NavigableString "bs4.element.NavigableString")]]\* \*= {'rp': , 'rt': , 'script': , 'style': , 'template': }\*[¶](#bs4.builder.HTMLTreeBuilder.DEFAULT\_STRING\_CONTAINERS "Link to this definition")
These HTML tags need special treatment so they can be
represented by a string class other than [`bs4.element.NavigableString`](bs4.html#bs4.element.NavigableString "bs4.element.NavigableString").
For some of these tags, it's because the HTML standard defines
an unusual content model for them. I made this list by going
through the HTML spec
() and looking for
"metadata content" elements that can contain strings.
The Ruby tags ( and ) are here despite being normal
"phrasing content" tags, because the content they contain is
qualitatively different from other text in the document, and it
can be useful to be able to distinguish it.
TODO: Arguably 

---

## Navigation

**Part of beautifulsoup4 Documentation**
- **Main Documentation:** [https://www.crummy.com/software/BeautifulSoup/bs4/doc/](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- **This Section:** api/bs4.builder.html

---

*Generated by lib2docScrape - Comprehensive Documentation Scraping*
