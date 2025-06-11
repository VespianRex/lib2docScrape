# bs4 package — Beautiful Soup 4.13.0 documentation

**Library:** beautifulsoup4
**Description:** HTML/XML parser
**Source URL:** https://www.crummy.com/software/BeautifulSoup/bs4/doc/api/bs4.html
**Scraped:** 2025-06-03T18:04:35.743078
**Content Length:** 316271 characters

---

## Raw Content


bs4 package — Beautiful Soup 4.13.0 documentation





# bs4 package[¶](#bs4-package "Link to this heading")

## Module contents[¶](#module-bs4 "Link to this heading")

Beautiful Soup Elixir and Tonic - "The Screen-Scraper's Friend".

<http://www.crummy.com/software/BeautifulSoup/>

Beautiful Soup uses a pluggable XML or HTML parser to parse a
(possibly invalid) document into a tree representation. Beautiful Soup
provides methods and Pythonic idioms that make it easy to navigate,
search, and modify the parse tree.

Beautiful Soup works with Python 3.7 and up. It works better if lxml
and/or html5lib is installed, but they are not required.

For more than you ever wanted to know about Beautiful Soup, see the
documentation: <http://www.crummy.com/software/BeautifulSoup/bs4/doc/>

*exception* bs4.AttributeResemblesVariableWarning[¶](#bs4.AttributeResemblesVariableWarning "Link to this definition")

Bases: [`UnusualUsageWarning`](#bs4.UnusualUsageWarning "bs4._warnings.UnusualUsageWarning"), [`SyntaxWarning`](https://docs.python.org/3/library/exceptions.html#SyntaxWarning "(in Python v3.13)")

The warning issued when Beautiful Soup suspects a provided
attribute name may actually be the misspelled name of a Beautiful
Soup variable. Generally speaking, this is only used in cases like
"\_class" where it's very unlikely the user would be referencing an
XML attribute with that name.

MESSAGE*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '%(original)r is an unusual attribute name and is a common misspelling for %(autocorrect)r.\n\nIf you meant %(autocorrect)r, change your code to use it, and this warning will go away.\n\nIf you really did mean to check the %(original)r attribute, this warning is spurious and can be filtered. To make it go away, run this code before creating your BeautifulSoup object:\n\n    from bs4 import AttributeResemblesVariableWarning\n    import warnings\n\n    warnings.filterwarnings("ignore", category=AttributeResemblesVariableWarning)\n'*[¶](#bs4.AttributeResemblesVariableWarning.MESSAGE "Link to this definition")
*class* bs4.BeautifulSoup(*markup: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [IO](https://docs.python.org/3/library/typing.html#typing.IO "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [IO](https://docs.python.org/3/library/typing.html#typing.IO "(in Python v3.13)")[[bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")] = ''*, *features: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [Sequence](https://docs.python.org/3/library/typing.html#typing.Sequence "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *builder: [TreeBuilder](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") | [Type](https://docs.python.org/3/library/typing.html#typing.Type "(in Python v3.13)")[[TreeBuilder](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *parse\_only: [SoupStrainer](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *from\_encoding: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *exclude\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *element\_classes: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[Type](https://docs.python.org/3/library/typing.html#typing.Type "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")], [Type](https://docs.python.org/3/library/typing.html#typing.Type "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")*)[¶](#bs4.BeautifulSoup "Link to this definition")

Bases: [`Tag`](#bs4.element.Tag "bs4.element.Tag")

A data structure representing a parsed HTML or XML document.

Most of the methods you'll call on a BeautifulSoup object are inherited from
PageElement or Tag.

Internally, this class defines the basic interface called by the
tree builders when converting an HTML/XML document into a d...

---

## Metadata

- **Document Index:** 2 of 2
- **Crawl Duration:** 9.10 seconds
- **Success Rate:** 2/2

## Additional Information

This documentation was automatically scraped from beautifulsoup4's official documentation
using lib2docScrape. The content above represents the raw scraped data.

For the most up-to-date information, please visit the original source at:
https://www.crummy.com/software/BeautifulSoup/bs4/doc/api/bs4.html
