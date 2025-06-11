# bs4 package[¶](#bs4-package "Link to this heading")

**Library:** beautifulsoup4
**Section:** api/bs4.html
**Source URL:** https://www.crummy.com/software/BeautifulSoup/bs4/doc/api/bs4.html
**Scraped:** 2025-06-03T18:38:23.486703

---

## Document Information

- **Content Length:** 316,271 characters
- **Links Found:** 0
- **Headings Found:** 13
- **Has Code Blocks:** False
- **Has Tables:** False

---

## Content


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
tree builders when converting an HTML/XML document into a data
structure. The interface abstracts away the differences between
parsers. To write a new tree builder, you'll need to understand
these methods as a whole.

These methods will be called by the BeautifulSoup constructor:

* reset()
* feed(markup)

The tree builder may call these methods from its feed() implementation:

* handle\_starttag(name, attrs) # See note about return value
* handle\_endtag(name)
* handle\_data(data) # Appends to the current data node
* endData(containerClass) # Ends the current data node

No matter how complicated the underlying parser is, you should be
able to build a tree using 'start tag' events, 'end tag' events,
'data' events, and "done with data" events.

If you encounter an empty-element tag (aka a self-closing tag,
like HTML's <br> tag), call handle\_starttag and then
handle\_endtag.

ASCII\_SPACES*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= ' \n\t\x0c\r'*[¶](#bs4.BeautifulSoup.ASCII_SPACES "Link to this definition")

A string containing all ASCII whitespace characters, used in
during parsing to detect data chunks that seem 'empty'.

DEFAULT\_BUILDER\_FEATURES*: [Sequence](https://docs.python.org/3/library/typing.html#typing.Sequence "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]* *= ['html', 'fast']*[¶](#bs4.BeautifulSoup.DEFAULT_BUILDER_FEATURES "Link to this definition")

If the end-user gives no indication which tree builder they
want, look for one with these features.

ROOT\_TAG\_NAME*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '[document]'*[¶](#bs4.BeautifulSoup.ROOT_TAG_NAME "Link to this definition")

Since [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") subclasses [`Tag`](#bs4.Tag "bs4.Tag"), it's possible to treat it as
a [`Tag`](#bs4.Tag "bs4.Tag") with a [`Tag.name`](#bs4.Tag.name "bs4.Tag.name"). Hoever, this name makes it clear the
[`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") object isn't a real markup tag.

contains\_replacement\_characters*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.BeautifulSoup.contains_replacement_characters "Link to this definition")

This is True if the markup that was parsed contains
U+FFFD REPLACEMENT\_CHARACTER characters which were not present
in the original markup. These mark character sequences that
could not be represented in Unicode.

copy\_self() → [BeautifulSoup](#bs4.BeautifulSoup "bs4.BeautifulSoup")[¶](#bs4.BeautifulSoup.copy_self "Link to this definition")

Create a new BeautifulSoup object with the same TreeBuilder,
but not associated with any markup.

This is the first step of the deepcopy process.

declared\_html\_encoding*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.BeautifulSoup.declared_html_encoding "Link to this definition")

The character encoding, if any, that was explicitly defined
in the original document. This may or may not match
[`BeautifulSoup.original_encoding`](#bs4.BeautifulSoup.original_encoding "bs4.BeautifulSoup.original_encoding").

decode(*indent\_level: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *eventual\_encoding: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 'utf-8'*, *formatter: [Formatter](#bs4.formatter.Formatter "bs4.formatter.Formatter") | [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 'minimal'*, *iterator: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.BeautifulSoup.decode "Link to this definition")
Returns a string representation of the parse tree

as a full HTML or XML document.

Parameters:

* **indent\_level** -- Each line of the rendering will be
  indented this many levels. (The `formatter` decides what a
  'level' means, in terms of spaces or other characters
  output.) This is used internally in recursive calls while
  pretty-printing.
* **eventual\_encoding** -- The encoding of the final document.
  If this is None, the document will be a Unicode string.
* **formatter** -- Either a [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string naming one of
  the standard formatters.
* **iterator** -- The iterator to use when navigating over the
  parse tree. This is only used by [`Tag.decode_contents`](#bs4.Tag.decode_contents "bs4.Tag.decode_contents") and
  you probably won't need to use it.

insert\_after(*\*args: [PageElement](#bs4.element.PageElement "bs4.element.PageElement") | [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [List](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")][¶](#bs4.BeautifulSoup.insert_after "Link to this definition")

This method is part of the PageElement API, but [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") doesn't implement
it because there is nothing before or after it in the parse tree.

insert\_before(*\*args: [PageElement](#bs4.element.PageElement "bs4.element.PageElement") | [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [List](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")][¶](#bs4.BeautifulSoup.insert_before "Link to this definition")

This method is part of the PageElement API, but [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") doesn't implement
it because there is nothing before or after it in the parse tree.

is\_xml*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.BeautifulSoup.is_xml "Link to this definition")
new\_string(*s: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *subclass: [Type](https://docs.python.org/3/library/typing.html#typing.Type "(in Python v3.13)")[[NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → [NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")[¶](#bs4.BeautifulSoup.new_string "Link to this definition")

Create a new [`NavigableString`](../index.html#NavigableString "NavigableString") associated with this [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup")
object.

Parameters:

* **s** -- The string content of the [`NavigableString`](../index.html#NavigableString "NavigableString")
* **subclass** -- The subclass of [`NavigableString`](../index.html#NavigableString "NavigableString"), if any, to
  use. If a document is being processed, an appropriate
  subclass for the current location in the document will
  be determined automatically.

new\_tag(*name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespace: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *nsprefix: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *attrs: Mapping[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [NamespacedAttribute](#bs4.element.NamespacedAttribute "bs4.element.NamespacedAttribute"), \_RawAttributeValue] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *sourceline: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *sourcepos: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwattrs: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [Tag](#bs4.element.Tag "bs4.element.Tag")[¶](#bs4.BeautifulSoup.new_tag "Link to this definition")

Create a new Tag associated with this BeautifulSoup object.

Parameters:

* **name** -- The name of the new Tag.
* **namespace** -- The URI of the new Tag's XML namespace, if any.
* **prefix** -- The prefix for the new Tag's XML namespace, if any.
* **attrs** -- A dictionary of this Tag's attribute values; can
  be used instead of `kwattrs` for attributes like 'class'
  that are reserved words in Python.
* **sourceline** -- The line number where this tag was
  (purportedly) found in its source document.
* **sourcepos** -- The character position within `sourceline` where this
  tag was (purportedly) found.
* **string** -- String content for the new Tag, if any.
* **kwattrs** -- Keyword arguments for the new Tag's attribute values.

original\_encoding*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.BeautifulSoup.original_encoding "Link to this definition")

Beautiful Soup's best guess as to the character encoding of the
original document.

reset() → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.BeautifulSoup.reset "Link to this definition")

Reset this object to a state as though it had never parsed any
markup.

string\_container(*base\_class: [Type](https://docs.python.org/3/library/typing.html#typing.Type "(in Python v3.13)")[[NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → [Type](https://docs.python.org/3/library/typing.html#typing.Type "(in Python v3.13)")[[NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")][¶](#bs4.BeautifulSoup.string_container "Link to this definition")

Find the class that should be instantiated to hold a given kind of
string.

This may be a built-in Beautiful Soup class or a custom class passed
in to the BeautifulSoup constructor.

*class* bs4.CData(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.CData "Link to this definition")

Bases: [`PreformattedString`](#bs4.element.PreformattedString "bs4.element.PreformattedString")

A [CDATA section](https://dev.w3.org/html5/spec-LC/syntax.html#cdata-sections).

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<![CDATA['*[¶](#bs4.CData.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= ']]>'*[¶](#bs4.CData.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

*class* bs4.CSS(*tag: [element.Tag](#bs4.element.Tag "bs4.element.Tag")*, *api: ModuleType | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.CSS "Link to this definition")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")

A proxy object against the `soupsieve` library, to simplify its
CSS selector API.

You don't need to instantiate this class yourself; instead, use
[`element.Tag.css`](#bs4.element.Tag.css "bs4.element.Tag.css").

Parameters:

* **tag** -- All CSS selectors run by this object will use this as
  their starting point.
* **api** -- An optional drop-in replacement for the `soupsieve` module,
  intended for use in unit tests.

closest(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → [element.Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.CSS.closest "Link to this definition")

Find the [`element.Tag`](#bs4.element.Tag "bs4.element.Tag") closest to this one that matches the given selector.

This uses the Soup Sieve library. For more information, see
that library's documentation for the [soupsieve.closest()](https://facelessuser.github.io/soupsieve/api/#soupsieveclosest)
method.

Parameters:

* **selector** -- A string containing a CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will pass in the prefixes it encountered while
  parsing the document.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.closest()](https://facelessuser.github.io/soupsieve/api/#soupsieveclosest) method.
* **kwargs** --
  
  Keyword arguments to be passed into Soup Sieve's
  [soupsieve.closest()](https://facelessuser.github.io/soupsieve/api/#soupsieveclosest) method.

compile(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → SoupSieve[¶](#bs4.CSS.compile "Link to this definition")

Pre-compile a selector and return the compiled object.

Parameters:

* **selector** -- A CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will use the prefixes it encountered while
  parsing the document.
* **flags** -- Flags to be passed into Soup Sieve's
  [soupsieve.compile()](https://facelessuser.github.io/soupsieve/api/#soupsievecompile) method.
* **kwargs** --
  
  Keyword arguments to be passed into Soup Sieve's
  [soupsieve.compile()](https://facelessuser.github.io/soupsieve/api/#soupsievecompile) method.

Returns:

A precompiled selector object.

Return type:

soupsieve.SoupSieve

escape(*ident: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.CSS.escape "Link to this definition")

Escape a CSS identifier.

This is a simple wrapper around [soupsieve.escape()](https://facelessuser.github.io/soupsieve/api/#soupsieveescape). See the
documentation for that function for more information.

filter(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → [ResultSet](#bs4.ResultSet "bs4.ResultSet")[[element.Tag](#bs4.element.Tag "bs4.element.Tag")][¶](#bs4.CSS.filter "Link to this definition")

Filter this [`element.Tag`](#bs4.element.Tag "bs4.element.Tag")'s direct children based on the given CSS selector.

This uses the Soup Sieve library. It works the same way as
passing a [`element.Tag`](#bs4.element.Tag "bs4.element.Tag") into that library's [soupsieve.filter()](https://facelessuser.github.io/soupsieve/api/#soupsievefilter)
method. For more information, see the documentation for
[soupsieve.filter()](https://facelessuser.github.io/soupsieve/api/#soupsievefilter).

Parameters:

* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will pass in the prefixes it encountered while
  parsing the document.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.filter()](https://facelessuser.github.io/soupsieve/api/#soupsievefilter)
  method.
* **kwargs** --
  
  Keyword arguments to be passed into SoupSieve's
  [soupsieve.filter()](https://facelessuser.github.io/soupsieve/api/#soupsievefilter)
  method.

iselect(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → Iterator[[element.Tag](#bs4.element.Tag "bs4.element.Tag")][¶](#bs4.CSS.iselect "Link to this definition")

Perform a CSS selection operation on the current [`element.Tag`](#bs4.element.Tag "bs4.element.Tag").

This uses the Soup Sieve library. For more information, see
that library's documentation for the [soupsieve.iselect()](https://facelessuser.github.io/soupsieve/api/#soupsieveiselect)
method. It is the same as select(), but it returns a generator
instead of a list.

Parameters:

* **selector** -- A string containing a CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will pass in the prefixes it encountered while
  parsing the document.
* **limit** -- After finding this number of results, stop looking.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.iselect()](https://facelessuser.github.io/soupsieve/api/#soupsieveiselect) method.
* **kwargs** --
  
  Keyword arguments to be passed into Soup Sieve's
  [soupsieve.iselect()](https://facelessuser.github.io/soupsieve/api/#soupsieveiselect) method.

match(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.CSS.match "Link to this definition")

Check whether or not this [`element.Tag`](#bs4.element.Tag "bs4.element.Tag") matches the given CSS selector.

This uses the Soup Sieve library. For more information, see
that library's documentation for the [soupsieve.match()](https://facelessuser.github.io/soupsieve/api/#soupsievematch)
method.

Param:

a CSS selector.

Parameters:

* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will pass in the prefixes it encountered while
  parsing the document.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.match()](https://facelessuser.github.io/soupsieve/api/#soupsievematch)
  method.
* **kwargs** --
  
  Keyword arguments to be passed into SoupSieve's
  [soupsieve.match()](https://facelessuser.github.io/soupsieve/api/#soupsievematch)
  method.

select(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → [ResultSet](#bs4.ResultSet "bs4.ResultSet")[[element.Tag](#bs4.element.Tag "bs4.element.Tag")][¶](#bs4.CSS.select "Link to this definition")

Perform a CSS selection operation on the current [`element.Tag`](#bs4.element.Tag "bs4.element.Tag").

This uses the Soup Sieve library. For more information, see
that library's documentation for the [soupsieve.select()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect) method.

Parameters:

* **selector** -- A CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will pass in the prefixes it encountered while
  parsing the document.
* **limit** -- After finding this number of results, stop looking.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.select()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect) method.
* **kwargs** --
  
  Keyword arguments to be passed into Soup Sieve's
  [soupsieve.select()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect) method.

select\_one(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → [element.Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.CSS.select_one "Link to this definition")

Perform a CSS selection operation on the current Tag and return the
first result, if any.

This uses the Soup Sieve library. For more information, see
that library's documentation for the [soupsieve.select\_one()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect_one) method.

Parameters:

* **selector** -- A CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will use the prefixes it encountered while
  parsing the document.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.select\_one()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect_one) method.
* **kwargs** --
  
  Keyword arguments to be passed into Soup Sieve's
  [soupsieve.select\_one()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect_one) method.

*class* bs4.Comment(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.Comment "Link to this definition")

Bases: [`PreformattedString`](#bs4.element.PreformattedString "bs4.element.PreformattedString")

An [HTML comment](https://dev.w3.org/html5/spec-LC/syntax.html#comments) or [XML comment](https://www.w3.org/TR/REC-xml/#sec-comments).

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<!--'*[¶](#bs4.Comment.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '-->'*[¶](#bs4.Comment.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

*class* bs4.Declaration(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.Declaration "Link to this definition")

Bases: [`PreformattedString`](#bs4.element.PreformattedString "bs4.element.PreformattedString")

An [XML declaration](https://www.w3.org/TR/REC-xml/#sec-prolog-dtd).

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<?'*[¶](#bs4.Declaration.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '?>'*[¶](#bs4.Declaration.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

*class* bs4.Doctype(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.Doctype "Link to this definition")

Bases: [`PreformattedString`](#bs4.element.PreformattedString "bs4.element.PreformattedString")

A [document type declaration](https://www.w3.org/TR/REC-xml/#dt-doctype).

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<!DOCTYPE '*[¶](#bs4.Doctype.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '>\n'*[¶](#bs4.Doctype.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

*classmethod* for\_name\_and\_ids(*name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *pub\_id: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*, *system\_id: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*) → [Doctype](#bs4.element.Doctype "bs4.element.Doctype")[¶](#bs4.Doctype.for_name_and_ids "Link to this definition")

Generate an appropriate document type declaration for a given
public ID and system ID.

Parameters:

* **name** -- The name of the document's root element, e.g. 'html'.
* **pub\_id** -- The Formal Public Identifier for this document type,
  e.g. '-//W3C//DTD XHTML 1.1//EN'
* **system\_id** -- The system identifier for this document type,
  e.g. '<http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd>'

*class* bs4.ElementFilter(*match\_function: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.ElementFilter "Link to this definition")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")

[`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") encapsulates the logic necessary to decide:

1. whether a [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") (a [`Tag`](#bs4.Tag "bs4.Tag") or a [`NavigableString`](../index.html#NavigableString "NavigableString")) matches a
user-specified query.

2. whether a given sequence of markup found during initial parsing
should be turned into a [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") at all, or simply discarded.

The base class is the simplest [`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter"). By default, it
matches everything and allows all markup to become [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement")
objects. You can make it more selective by passing in a
user-defined match function, or defining a subclass.

Most users of Beautiful Soup will never need to use
[`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter"), or its more capable subclass
[`SoupStrainer`](../index.html#SoupStrainer "SoupStrainer"). Instead, they will use methods like
[`Tag.find()`](#bs4.Tag.find "bs4.Tag.find"), which will convert their arguments into
[`SoupStrainer`](../index.html#SoupStrainer "SoupStrainer") objects and run them against the tree.

However, if you find yourself wanting to treat the arguments to
Beautiful Soup's find\_\*() methods as first-class objects, those
objects will be [`SoupStrainer`](../index.html#SoupStrainer "SoupStrainer") objects. You can create them
yourself and then make use of functions like
[`ElementFilter.filter()`](#bs4.ElementFilter.filter "bs4.ElementFilter.filter").

allow\_string\_creation(*string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.ElementFilter.allow_string_creation "Link to this definition")

Based on the content of a string, see whether this
[`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") will allow a [`NavigableString`](../index.html#NavigableString "NavigableString") object based on
this string to be added to the parse tree.

By default, all strings are processed into [`NavigableString`](../index.html#NavigableString "NavigableString")
objects. To change this, subclass [`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter").

Parameters:

**str** -- The string under consideration.

allow\_tag\_creation(*nsprefix: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*, *name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *attrs: \_RawAttributeValues | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.ElementFilter.allow_tag_creation "Link to this definition")

Based on the name and attributes of a tag, see whether this
[`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") will allow a [`Tag`](#bs4.Tag "bs4.Tag") object to even be created.

By default, all tags are parsed. To change this, subclass
[`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter").

Parameters:

* **name** -- The name of the prospective tag.
* **attrs** -- The attributes of the prospective tag.

*property* excludes\_everything*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.ElementFilter.excludes_everything "Link to this definition")

Does this [`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") obviously exclude everything? If
so, Beautiful Soup will issue a warning if you try to use it
when parsing a document.

The [`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") might turn out to exclude everything even
if this returns [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.13)"), but it won't exclude everything in an
obvious way.

The base [`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") implementation excludes things based
on a match function we can't inspect, so excludes\_everything
is always false.

filter(*generator: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*) → [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement") | [Tag](#bs4.element.Tag "bs4.element.Tag") | [NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")][¶](#bs4.ElementFilter.filter "Link to this definition")

The most generic search method offered by Beautiful Soup.

Acts like Python's built-in [`filter`](#bs4.ElementFilter.filter "bs4.ElementFilter.filter"), using
[`ElementFilter.match`](#bs4.ElementFilter.match "bs4.ElementFilter.match") as the filtering function.

find(*generator: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*) → [PageElement](#bs4.element.PageElement "bs4.element.PageElement") | [Tag](#bs4.element.Tag "bs4.element.Tag") | [NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.ElementFilter.find "Link to this definition")

A lower-level equivalent of [`Tag.find()`](#bs4.Tag.find "bs4.Tag.find").

You can pass in your own generator for iterating over
[`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects. The first one that matches this
[`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") will be returned.

Parameters:

**generator** -- A way of iterating over [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement")
objects.

find\_all(*generator: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → [ResultSet](#bs4.element.ResultSet "bs4.element.ResultSet")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement") | [Tag](#bs4.element.Tag "bs4.element.Tag") | [NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")][¶](#bs4.ElementFilter.find_all "Link to this definition")

A lower-level equivalent of [`Tag.find_all()`](#bs4.Tag.find_all "bs4.Tag.find_all").

You can pass in your own generator for iterating over
[`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects. Only elements that match this
[`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") will be returned in the [`ResultSet`](#bs4.ResultSet "bs4.ResultSet").

Parameters:

* **generator** -- A way of iterating over [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement")
  objects.
* **limit** -- Stop looking after finding this many results.

*property* includes\_everything*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.ElementFilter.includes_everything "Link to this definition")

Does this [`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") obviously include everything? If so,
the filter process can be made much faster.

The [`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") might turn out to include everything even
if this returns [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.13)"), but it won't include everything in an
obvious way.

The base [`ElementFilter`](#bs4.ElementFilter "bs4.ElementFilter") implementation includes things based on
the match function, so includes\_everything is only true if
there is no match function.

match(*element: [PageElement](#bs4.element.PageElement "bs4.element.PageElement")*, *\_known\_rules: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.ElementFilter.match "Link to this definition")

Does the given PageElement match the rules set down by this
ElementFilter?

The base implementation delegates to the function passed in to
the constructor.

Parameters:

**\_known\_rules** -- Defined for compatibility with

SoupStrainer.\_match(). Used more for consistency than because
we need the performance optimization.

match\_function*: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.ElementFilter.match_function "Link to this definition")
*exception* bs4.FeatureNotFound[¶](#bs4.FeatureNotFound "Link to this definition")

Bases: [`ValueError`](https://docs.python.org/3/library/exceptions.html#ValueError "(in Python v3.13)")

Exception raised by the BeautifulSoup constructor if no parser with the
requested features is found.

*exception* bs4.GuessedAtParserWarning[¶](#bs4.GuessedAtParserWarning "Link to this definition")

Bases: [`UserWarning`](https://docs.python.org/3/library/exceptions.html#UserWarning "(in Python v3.13)")

The warning issued when BeautifulSoup has to guess what parser to
use -- probably because no parser was specified in the constructor.

MESSAGE*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= 'No parser was explicitly specified, so I\'m using the best available %(markup\_type)s parser for this system ("%(parser)s"). This usually isn\'t a problem, but if you run this code on another system, or in a different virtual environment, it may use a different parser and behave differently.\n\nThe code that caused this warning is on line %(line\_number)s of the file %(filename)s. To get rid of this warning, pass the additional argument \'features="%(parser)s"\' to the BeautifulSoup constructor.\n'*[¶](#bs4.GuessedAtParserWarning.MESSAGE "Link to this definition")
*exception* bs4.MarkupResemblesLocatorWarning[¶](#bs4.MarkupResemblesLocatorWarning "Link to this definition")

Bases: [`UnusualUsageWarning`](#bs4.UnusualUsageWarning "bs4._warnings.UnusualUsageWarning")

The warning issued when BeautifulSoup is given 'markup' that
actually looks like a resource locator -- a URL or a path to a file
on disk.

FILENAME\_MESSAGE*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= 'The input passed in on this line looks more like a filename than HTML or XML.\n\nIf you meant to use Beautiful Soup to parse the contents of a file on disk, then something has gone wrong. You should open the file first, using code like this:\n\n    filehandle = open(your filename)\n\nYou can then feed the open filehandle into Beautiful Soup instead of using the filename.\n\nHowever, if you want to parse some data that happens to look like a %(what)s, then nothing has gone wrong: you are using Beautiful Soup correctly, and this warning is spurious and can be filtered. To make this warning go away, run this code before calling the BeautifulSoup constructor:\n\n    from bs4 import MarkupResemblesLocatorWarning\n    import warnings\n\n    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)\n    '*[¶](#bs4.MarkupResemblesLocatorWarning.FILENAME_MESSAGE "Link to this definition")
URL\_MESSAGE*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= 'The input passed in on this line looks more like a URL than HTML or XML.\n\nIf you meant to use Beautiful Soup to parse the web page found at a certain URL, then something has gone wrong. You should use an Python package like \'requests\' to fetch the content behind the URL. Once you have the content as a string, you can feed that string into Beautiful Soup.\n\nHowever, if you want to parse some data that happens to look like a %(what)s, then nothing has gone wrong: you are using Beautiful Soup correctly, and this warning is spurious and can be filtered. To make this warning go away, run this code before calling the BeautifulSoup constructor:\n\n    from bs4 import MarkupResemblesLocatorWarning\n    import warnings\n\n    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)\n    '*[¶](#bs4.MarkupResemblesLocatorWarning.URL_MESSAGE "Link to this definition")
*exception* bs4.ParserRejectedMarkup(*message\_or\_exception: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [Exception](https://docs.python.org/3/library/exceptions.html#Exception "(in Python v3.13)")*)[¶](#bs4.ParserRejectedMarkup "Link to this definition")

Bases: [`Exception`](https://docs.python.org/3/library/exceptions.html#Exception "(in Python v3.13)")

An Exception to be raised when the underlying parser simply
refuses to parse the given markup.

*class* bs4.ProcessingInstruction(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.ProcessingInstruction "Link to this definition")

Bases: [`PreformattedString`](#bs4.element.PreformattedString "bs4.element.PreformattedString")

A SGML processing instruction.

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<?'*[¶](#bs4.ProcessingInstruction.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '>'*[¶](#bs4.ProcessingInstruction.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

*class* bs4.ResultSet(*source: [ElementFilter](#bs4.ElementFilter "bs4.ElementFilter") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*, *result: Iterable[\_PageElementT] = ()*)[¶](#bs4.ResultSet "Link to this definition")

Bases: [`List`](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[`_PageElementT`], [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic "(in Python v3.13)")[`_PageElementT`]

A ResultSet is a list of [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects, gathered as the result
of matching an [`ElementFilter`](../index.html#ElementFilter "ElementFilter") against a parse tree. Basically, a list of
search results.

source*: [ElementFilter](#bs4.ElementFilter "bs4.ElementFilter") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.ResultSet.source "Link to this definition")
*class* bs4.Script(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.Script "Link to this definition")

Bases: [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString")

A [`NavigableString`](../index.html#NavigableString "NavigableString") representing the contents of a [<script>
HTML tag](https://dev.w3.org/html5/spec-LC/Overview.html#the-script-element)
(probably Javascript).

Used to distinguish executable code from textual content.

*exception* bs4.StopParsing[¶](#bs4.StopParsing "Link to this definition")

Bases: [`Exception`](https://docs.python.org/3/library/exceptions.html#Exception "(in Python v3.13)")

Exception raised by a TreeBuilder if it's unable to continue parsing.

*class* bs4.Stylesheet(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.Stylesheet "Link to this definition")

Bases: [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString")

A [`NavigableString`](../index.html#NavigableString "NavigableString") representing the contents of a [<style> HTML
tag](https://dev.w3.org/html5/spec-LC/Overview.html#the-style-element)
(probably CSS).

Used to distinguish embedded stylesheets from textual content.

*class* bs4.Tag(*parser: [BeautifulSoup](#bs4.BeautifulSoup "bs4.BeautifulSoup") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *builder: [TreeBuilder](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *namespace: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *prefix: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *attrs: \_RawOrProcessedAttributeValues | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *parent: [BeautifulSoup](#bs4.BeautifulSoup "bs4.BeautifulSoup") | [Tag](#bs4.Tag "bs4.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *previous: \_AtMostOneElement = None*, *is\_xml: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *sourceline: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *sourcepos: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *can\_be\_empty\_element: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *cdata\_list\_attributes: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *preserve\_whitespace\_tags: Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *interesting\_string\_types: Set[Type[[NavigableString](../index.html#NavigableString "NavigableString")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *namespaces: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.Tag "Link to this definition")

Bases: [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement")

An HTML or XML tag that is part of a parse tree, along with its
attributes, contents, and relationships to other parts of the tree.

When Beautiful Soup parses the markup `<b>penguin</b>`, it will
create a [`Tag`](#bs4.Tag "bs4.Tag") object representing the `<b>` tag. You can
instantiate [`Tag`](#bs4.Tag "bs4.Tag") objects directly, but it's not necessary unless
you're adding entirely new markup to a parsed document. Most of
the constructor arguments are intended for use by the [`TreeBuilder`](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder")
that's parsing a document.

Parameters:

* **parser** -- A [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") object representing the parse tree this
  [`Tag`](#bs4.Tag "bs4.Tag") will be part of.
* **builder** -- The [`TreeBuilder`](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") being used to build the tree.
* **name** -- The name of the tag.
* **namespace** -- The URI of this tag's XML namespace, if any.
* **prefix** -- The prefix for this tag's XML namespace, if any.
* **attrs** -- A dictionary of attribute values.
* **parent** -- The [`Tag`](#bs4.Tag "bs4.Tag") to use as the parent of this [`Tag`](#bs4.Tag "bs4.Tag"). May be
  the [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") object itself.
* **previous** -- The [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") that was parsed immediately before
  parsing this tag.
* **is\_xml** -- If True, this is an XML tag. Otherwise, this is an
  HTML tag.
* **sourceline** -- The line number where this tag was found in its
  source document.
* **sourcepos** -- The character position within `sourceline` where this
  tag was found.
* **can\_be\_empty\_element** -- If True, this tag should be
  represented as <tag/>. If False, this tag should be represented
  as <tag></tag>.
* **cdata\_list\_attributes** -- A dictionary of attributes whose values should
  be parsed as lists of strings if they ever show up on this tag.
* **preserve\_whitespace\_tags** -- Names of tags whose contents
  should have their whitespace preserved if they are encountered inside
  this tag.
* **interesting\_string\_types** -- When iterating over this tag's
  string contents in methods like [`Tag.strings`](#bs4.Tag.strings "bs4.Tag.strings") or
  [`PageElement.get_text`](#bs4.element.PageElement.get_text "bs4.element.PageElement.get_text"), these are the types of strings that are
  interesting enough to be considered. By default,
  [`NavigableString`](../index.html#NavigableString "NavigableString") (normal strings) and [`CData`](#bs4.CData "bs4.CData") (CDATA
  sections) are the only interesting string subtypes.
* **namespaces** -- A dictionary mapping currently active
  namespace prefixes to URIs, as of the point in the parsing process when
  this tag was encountered. This can be used later to
  construct CSS selectors.

append(*tag: \_InsertableElement*) → [PageElement](#bs4.element.PageElement "bs4.element.PageElement")[¶](#bs4.Tag.append "Link to this definition")

Appends the given [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") to the contents of this [`Tag`](#bs4.Tag "bs4.Tag").

Parameters:

**tag** -- A PageElement.

:return The newly appended PageElement.

attrs*: \_AttributeValues*[¶](#bs4.Tag.attrs "Link to this definition")
can\_be\_empty\_element*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.Tag.can_be_empty_element "Link to this definition")
cdata\_list\_attributes*: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.Tag.cdata_list_attributes "Link to this definition")
*property* children*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.Tag.children "Link to this definition")

Iterate over all direct children of this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement").

clear(*decompose: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.Tag.clear "Link to this definition")
Destroy all children of this [`Tag`](#bs4.Tag "bs4.Tag") by calling

[`PageElement.extract`](#bs4.element.PageElement.extract "bs4.element.PageElement.extract") on them.

Parameters:

**decompose** -- If this is True, [`PageElement.decompose`](#bs4.element.PageElement.decompose "bs4.element.PageElement.decompose") (a
more destructive method) will be called instead of
[`PageElement.extract`](#bs4.element.PageElement.extract "bs4.element.PageElement.extract").

contents*: List[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.Tag.contents "Link to this definition")
copy\_self() → [Self](https://docs.python.org/3/library/typing.html#typing.Self "(in Python v3.13)")[¶](#bs4.Tag.copy_self "Link to this definition")

Create a new Tag just like this one, but with no
contents and unattached to any parse tree.

This is the first step in the deepcopy process, but you can
call it on its own to create a copy of a Tag without copying its
contents.

*property* css*: [CSS](#bs4.css.CSS "bs4.css.CSS")*[¶](#bs4.Tag.css "Link to this definition")

Return an interface to the CSS selector API.

decode(*indent\_level: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *eventual\_encoding: \_Encoding = 'utf-8'*, *formatter: \_FormatterOrName = 'minimal'*, *iterator: Iterator[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.Tag.decode "Link to this definition")

Render this [`Tag`](#bs4.Tag "bs4.Tag") and its contents as a Unicode string.

Parameters:

* **indent\_level** -- Each line of the rendering will be
  indented this many levels. (The `formatter` decides what a
  'level' means, in terms of spaces or other characters
  output.) This is used internally in recursive calls while
  pretty-printing.
* **encoding** -- The encoding you intend to use when
  converting the string to a bytestring. decode() is *not*
  responsible for performing that encoding. This information
  is needed so that a real encoding can be substituted in if
  the document contains an encoding declaration (e.g. in a
  <meta> tag).
* **formatter** -- Either a [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string
  naming one of the standard formatters.
* **iterator** -- The iterator to use when navigating over the
  parse tree. This is only used by [`Tag.decode_contents`](#bs4.Tag.decode_contents "bs4.Tag.decode_contents") and
  you probably won't need to use it.

decode\_contents(*indent\_level: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *eventual\_encoding: \_Encoding = 'utf-8'*, *formatter: \_FormatterOrName = 'minimal'*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.Tag.decode_contents "Link to this definition")

Renders the contents of this tag as a Unicode string.

Parameters:

* **indent\_level** -- Each line of the rendering will be
  indented this many levels. (The formatter decides what a
  'level' means in terms of spaces or other characters
  output.) Used internally in recursive calls while
  pretty-printing.
* **eventual\_encoding** -- The tag is destined to be
  encoded into this encoding. decode\_contents() is *not*
  responsible for performing that encoding. This information
  is needed so that a real encoding can be substituted in if
  the document contains an encoding declaration (e.g. in a
  <meta> tag).
* **formatter** -- A [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string naming one of
  the standard Formatters.

*property* descendants*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.Tag.descendants "Link to this definition")

Iterate over all children of this [`Tag`](#bs4.Tag "bs4.Tag") in a
breadth-first sequence.

encode(*encoding: \_Encoding = 'utf-8'*, *indent\_level: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *formatter: \_FormatterOrName = 'minimal'*, *errors: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 'xmlcharrefreplace'*) → [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")[¶](#bs4.Tag.encode "Link to this definition")

Render this [`Tag`](#bs4.Tag "bs4.Tag") and its contents as a bytestring.

Parameters:

* **encoding** -- The encoding to use when converting to
  a bytestring. This may also affect the text of the document,
  specifically any encoding declarations within the document.
* **indent\_level** -- Each line of the rendering will be
  indented this many levels. (The `formatter` decides what a
  'level' means, in terms of spaces or other characters
  output.) This is used internally in recursive calls while
  pretty-printing.
* **formatter** -- Either a [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string naming one of
  the standard formatters.
* **errors** -- An error handling strategy such as
  'xmlcharrefreplace'. This value is passed along into
  [`str.encode()`](https://docs.python.org/3/library/stdtypes.html#str.encode "(in Python v3.13)") and its value should be one of the [error
  handling constants defined by Python's codecs module](https://docs.python.org/3/library/codecs.html#error-handlers).

encode\_contents(*indent\_level: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *encoding: \_Encoding = 'utf-8'*, *formatter: \_FormatterOrName = 'minimal'*) → [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")[¶](#bs4.Tag.encode_contents "Link to this definition")

Renders the contents of this PageElement as a bytestring.

Parameters:

* **indent\_level** -- Each line of the rendering will be
  indented this many levels. (The `formatter` decides what a
  'level' means, in terms of spaces or other characters
  output.) This is used internally in recursive calls while
  pretty-printing.
* **formatter** -- Either a [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string naming one of
  the standard formatters.
* **encoding** -- The bytestring will be in this encoding.

extend(*tags: Iterable[\_InsertableElement] | [Tag](#bs4.Tag "bs4.Tag")*) → List[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")][¶](#bs4.Tag.extend "Link to this definition")

Appends one or more objects to the contents of this
[`Tag`](#bs4.Tag "bs4.Tag").

Parameters:

**tags** -- If a list of [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects is provided,
they will be appended to this tag's contents, one at a time.
If a single [`Tag`](#bs4.Tag "bs4.Tag") is provided, its [`Tag.contents`](#bs4.Tag.contents "bs4.Tag.contents") will be
used to extend this object's [`Tag.contents`](#bs4.Tag.contents "bs4.Tag.contents").

:return The list of PageElements that were appended.

find(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *recursive: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = True*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: \_StrainableAttribute*) → \_AtMostOneElement[¶](#bs4.Tag.find "Link to this definition")

Look in the children of this PageElement and find the first
PageElement that matches the given criteria.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **recursive** -- If this is True, find() will perform a
  recursive search of this Tag's children. Otherwise,
  only the direct children will be considered.
* **string** -- A filter on the [`Tag.string`](#bs4.Tag.string "bs4.Tag.string") attribute.
* **limit** -- Stop looking after finding this many results.

Kwargs:

Additional filters on attribute values.

find\_all(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *recursive: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = True*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\_stacklevel: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 2*, *\*\*kwargs: \_StrainableAttribute*) → \_QueryResults[¶](#bs4.Tag.find_all "Link to this definition")

Look in the children of this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") and find all
[`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects that match the given criteria.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **recursive** -- If this is True, find\_all() will perform a
  recursive search of this PageElement's children. Otherwise,
  only the direct children will be considered.
* **limit** -- Stop looking after finding this many results.
* **\_stacklevel** -- Used internally to improve warning messages.

Kwargs:

Additional filters on attribute values.

get(*key: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *default: \_AttributeValue | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → \_AttributeValue | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.Tag.get "Link to this definition")

Returns the value of the 'key' attribute for the tag, or
the value given for 'default' if it doesn't have that
attribute.

Parameters:

* **key** -- The attribute to look for.
* **default** -- Use this value if the attribute is not present
  on this [`Tag`](#bs4.Tag "bs4.Tag").

get\_attribute\_list(*key: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *default: [AttributeValueList](#bs4.element.AttributeValueList "bs4.element.AttributeValueList") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → [AttributeValueList](#bs4.element.AttributeValueList "bs4.element.AttributeValueList")[¶](#bs4.Tag.get_attribute_list "Link to this definition")

The same as get(), but always returns a (possibly empty) list.

Parameters:

* **key** -- The attribute to look for.
* **default** -- Use this value if the attribute is not present
  on this [`Tag`](#bs4.Tag "bs4.Tag").

Returns:

A list of strings, usually empty or containing only a single
value.

has\_attr(*key: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.Tag.has_attr "Link to this definition")

Does this [`Tag`](#bs4.Tag "bs4.Tag") have an attribute with the given name?

index(*element: [PageElement](#bs4.element.PageElement "bs4.element.PageElement")*) → [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)")[¶](#bs4.Tag.index "Link to this definition")

Find the index of a child of this [`Tag`](#bs4.Tag "bs4.Tag") (by identity, not value).

Doing this by identity avoids issues when a [`Tag`](#bs4.Tag "bs4.Tag") contains two
children that have string equality.

Parameters:

**element** -- Look for this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") in this object's contents.

insert(*position: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)")*, *\*new\_children: \_InsertableElement*) → List[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")][¶](#bs4.Tag.insert "Link to this definition")

Insert one or more new PageElements as a child of this [`Tag`](#bs4.Tag "bs4.Tag").

This works similarly to `list.insert()`, except you can insert
multiple elements at once.

Parameters:

* **position** -- The numeric position that should be occupied
  in this Tag's [`Tag.children`](#bs4.Tag.children "bs4.Tag.children") by the first new [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement").
* **new\_children** -- The PageElements to insert.

:return The newly inserted PageElements.

interesting\_string\_types*: Set[Type[[NavigableString](../index.html#NavigableString "NavigableString")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.Tag.interesting_string_types "Link to this definition")
isSelfClosing() → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.Tag.isSelfClosing "Link to this definition")

: :meta private:

*property* is\_empty\_element*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.Tag.is_empty_element "Link to this definition")

Is this tag an empty-element tag? (aka a self-closing tag)

A tag that has contents is never an empty-element tag.

A tag that has no contents may or may not be an empty-element
tag. It depends on the [`TreeBuilder`](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") used to create the
tag. If the builder has a designated list of empty-element
tags, then only a tag whose name shows up in that list is
considered an empty-element tag. This is usually the case
for HTML documents.

If the builder has no designated list of empty-element, then
any tag with no contents is an empty-element tag. This is usually
the case for XML documents.

name*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*[¶](#bs4.Tag.name "Link to this definition")
namespace*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.Tag.namespace "Link to this definition")
parser\_class*: [type](https://docs.python.org/3/library/functions.html#type "(in Python v3.13)")[[BeautifulSoup](#bs4.BeautifulSoup "bs4.BeautifulSoup")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.Tag.parser_class "Link to this definition")
prefix*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.Tag.prefix "Link to this definition")
preserve\_whitespace\_tags*: Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.Tag.preserve_whitespace_tags "Link to this definition")
prettify(*encoding: \_Encoding | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *formatter: \_FormatterOrName = 'minimal'*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")[¶](#bs4.Tag.prettify "Link to this definition")

Pretty-print this [`Tag`](#bs4.Tag "bs4.Tag") as a string or bytestring.

Parameters:

* **encoding** -- The encoding of the bytestring, or None if you want Unicode.
* **formatter** -- A Formatter object, or a string naming one of
  the standard formatters.

Returns:

A string (if no `encoding` is provided) or a bytestring
(otherwise).

replaceWithChildren() → \_OneElement[¶](#bs4.Tag.replaceWithChildren "Link to this definition")

: :meta private:

replace\_with\_children() → [Self](https://docs.python.org/3/library/typing.html#typing.Self "(in Python v3.13)")[¶](#bs4.Tag.replace_with_children "Link to this definition")

Replace this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") with its contents.

Returns:

This object, no longer part of the tree.

select(*selector: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")*) → [ResultSet](#bs4.element.ResultSet "bs4.element.ResultSet")[[Tag](#bs4.element.Tag "bs4.element.Tag")][¶](#bs4.Tag.select "Link to this definition")

Perform a CSS selection operation on the current element.

This uses the SoupSieve library.

Parameters:

* **selector** -- A string containing a CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will use the prefixes it encountered while
  parsing the document.
* **limit** -- After finding this number of results, stop looking.
* **kwargs** -- Keyword arguments to be passed into SoupSieve's
  soupsieve.select() method.

select\_one(*selector: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")*) → [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.Tag.select_one "Link to this definition")

Perform a CSS selection operation on the current element.

Parameters:

* **selector** -- A CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will use the prefixes it encountered while
  parsing the document.
* **kwargs** -- Keyword arguments to be passed into Soup Sieve's
  soupsieve.select() method.

*property* self\_and\_descendants*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.Tag.self_and_descendants "Link to this definition")

Iterate over this [`Tag`](#bs4.Tag "bs4.Tag") and its children in a
breadth-first sequence.

smooth() → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.Tag.smooth "Link to this definition")

Smooth out the children of this [`Tag`](#bs4.Tag "bs4.Tag") by consolidating consecutive
strings.

If you perform a lot of operations that modify the tree,
calling this method afterwards can make pretty-printed output
look more natural.

sourceline*: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.Tag.sourceline "Link to this definition")
sourcepos*: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.Tag.sourcepos "Link to this definition")
*property* string*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.Tag.string "Link to this definition")

Convenience property to get the single string within this
[`Tag`](#bs4.Tag "bs4.Tag"), assuming there is just one.

Returns:

If this [`Tag`](#bs4.Tag "bs4.Tag") has a single child that's a
[`NavigableString`](../index.html#NavigableString "NavigableString"), the return value is that string. If this
element has one child [`Tag`](#bs4.Tag "bs4.Tag"), the return value is that child's
[`Tag.string`](#bs4.Tag.string "bs4.Tag.string"), recursively. If this [`Tag`](#bs4.Tag "bs4.Tag") has no children,
or has more than one child, the return value is `None`.

If this property is unexpectedly returning `None` for you,
it's probably because your [`Tag`](#bs4.Tag "bs4.Tag") has more than one thing
inside it.

*property* strings*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.Tag.strings "Link to this definition")

Yield all strings of certain classes, possibly stripping them.

Parameters:

* **strip** -- If True, all strings will be stripped before being
  yielded.
* **types** -- A tuple of NavigableString subclasses. Any strings of
  a subclass not found in this list will be ignored. By
  default, the subclasses considered are the ones found in
  self.interesting\_string\_types. If that's not specified,
  only NavigableString and CData objects will be
  considered. That means no comments, processing
  instructions, etc.

unwrap() → [Self](https://docs.python.org/3/library/typing.html#typing.Self "(in Python v3.13)")[¶](#bs4.Tag.unwrap "Link to this definition")

Replace this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") with its contents.

Returns:

This object, no longer part of the tree.

*class* bs4.TemplateString(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.TemplateString "Link to this definition")

Bases: [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString")

A [`NavigableString`](../index.html#NavigableString "NavigableString") representing a string found inside an [HTML
<template> tag](https://html.spec.whatwg.org/multipage/scripting.html#the-template-element)
embedded in a larger document.

Used to distinguish such strings from the main body of the document.

*class* bs4.UnicodeDammit(*markup: [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*, *known\_definite\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = []*, *smart\_quotes\_to: [Literal](https://docs.python.org/3/library/typing.html#typing.Literal "(in Python v3.13)")['ascii', 'xml', 'html'] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *is\_html: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*, *exclude\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = []*, *user\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *override\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.UnicodeDammit "Link to this definition")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")

A class for detecting the encoding of a bytestring containing an
HTML or XML document, and decoding it to Unicode. If the source
encoding is windows-1252, [`UnicodeDammit`](#bs4.UnicodeDammit "bs4.UnicodeDammit") can also replace
Microsoft smart quotes with their HTML or XML equivalents.

Parameters:

* **markup** -- HTML or XML markup in an unknown encoding.
* **known\_definite\_encodings** -- When determining the encoding
  of `markup`, these encodings will be tried first, in
  order. In HTML terms, this corresponds to the "known
  definite encoding" step defined in [section 13.2.3.1 of the HTML standard](https://html.spec.whatwg.org/multipage/parsing.html#parsing-with-a-known-character-encoding).
* **user\_encodings** -- These encodings will be tried after the
  `known_definite_encodings` have been tried and failed, and
  after an attempt to sniff the encoding by looking at a
  byte order mark has failed. In HTML terms, this
  corresponds to the step "user has explicitly instructed
  the user agent to override the document's character
  encoding", defined in [section 13.2.3.2 of the HTML standard](https://html.spec.whatwg.org/multipage/parsing.html#determining-the-character-encoding).
* **override\_encodings** -- A **deprecated** alias for
  `known_definite_encodings`. Any encodings here will be tried
  immediately after the encodings in
  `known_definite_encodings`.
* **smart\_quotes\_to** -- By default, Microsoft smart quotes will,
  like all other characters, be converted to Unicode
  characters. Setting this to `ascii` will convert them to ASCII
  quotes instead. Setting it to `xml` will convert them to XML
  entity references, and setting it to `html` will convert them
  to HTML entity references.
* **is\_html** -- If True, `markup` is treated as an HTML
  document. Otherwise it's treated as an XML document.
* **exclude\_encodings** -- These encodings will not be considered,
  even if the sniffing code thinks they might make sense.

CHARSET\_ALIASES*: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.UnicodeDammit.CHARSET_ALIASES "Link to this definition")

This dictionary maps commonly seen values for "charset" in HTML
meta tags to the corresponding Python codec names. It only covers
values that aren't in Python's aliases and can't be determined
by the heuristics in [`find_codec`](#bs4.UnicodeDammit.find_codec "bs4.UnicodeDammit.find_codec").

ENCODINGS\_WITH\_SMART\_QUOTES*: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.UnicodeDammit.ENCODINGS_WITH_SMART_QUOTES "Link to this definition")

A list of encodings that tend to contain Microsoft smart quotes.

MS\_CHARS*: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [Tuple](https://docs.python.org/3/library/typing.html#typing.Tuple "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]]*[¶](#bs4.UnicodeDammit.MS_CHARS "Link to this definition")

A partial mapping of ISO-Latin-1 to HTML entities/XML numeric entities.

WINDOWS\_1252\_TO\_UTF8*: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)"), [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")]*[¶](#bs4.UnicodeDammit.WINDOWS_1252_TO_UTF8 "Link to this definition")

A map used when removing rogue Windows-1252/ISO-8859-1
characters in otherwise UTF-8 documents.

Note that \x81, \x8d, \x8f, \x90, and \x9d are undefined in
Windows-1252.

contains\_replacement\_characters*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.UnicodeDammit.contains_replacement_characters "Link to this definition")

This is True if [`UnicodeDammit.unicode_markup`](#bs4.UnicodeDammit.unicode_markup "bs4.UnicodeDammit.unicode_markup") contains
U+FFFD REPLACEMENT\_CHARACTER characters which were not present
in [`UnicodeDammit.markup`](#bs4.UnicodeDammit.markup "bs4.UnicodeDammit.markup"). These mark character sequences that
could not be represented in Unicode.

*property* declared\_html\_encoding*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.UnicodeDammit.declared_html_encoding "Link to this definition")

If the markup is an HTML document, returns the encoding, if any,
declared *inside* the document.

*classmethod* detwingle(*in\_bytes: [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*, *main\_encoding: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 'utf8'*, *embedded\_encoding: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 'windows-1252'*) → [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")[¶](#bs4.UnicodeDammit.detwingle "Link to this definition")

Fix characters from one encoding embedded in some other encoding.

Currently the only situation supported is Windows-1252 (or its
subset ISO-8859-1), embedded in UTF-8.

Parameters:

* **in\_bytes** -- A bytestring that you suspect contains
  characters from multiple encodings. Note that this *must*
  be a bytestring. If you've already converted the document
  to Unicode, you're too late.
* **main\_encoding** -- The primary encoding of `in_bytes`.
* **embedded\_encoding** -- The encoding that was used to embed characters
  in the main document.

Returns:

A bytestring similar to `in_bytes`, in which
`embedded_encoding` characters have been converted to
their `main_encoding` equivalents.

find\_codec(*charset: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.UnicodeDammit.find_codec "Link to this definition")

Look up the Python codec corresponding to a given character set.

Parameters:

**charset** -- The name of a character set.

Returns:

The name of a Python codec.

markup*: [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*[¶](#bs4.UnicodeDammit.markup "Link to this definition")

The original markup, before it was converted to Unicode.
This is not necessarily the same as what was passed in to the
constructor, since any byte-order mark will be stripped.

original\_encoding*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.UnicodeDammit.original_encoding "Link to this definition")

Unicode, Dammit's best guess as to the original character
encoding of [`UnicodeDammit.markup`](#bs4.UnicodeDammit.markup "bs4.UnicodeDammit.markup").

smart\_quotes\_to*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.UnicodeDammit.smart_quotes_to "Link to this definition")

The strategy used to handle Microsoft smart quotes.

tried\_encodings*: [List](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[[Tuple](https://docs.python.org/3/library/typing.html#typing.Tuple "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]]*[¶](#bs4.UnicodeDammit.tried_encodings "Link to this definition")

The (encoding, error handling strategy) 2-tuples that were used to
try and convert the markup to Unicode.

unicode\_markup*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.UnicodeDammit.unicode_markup "Link to this definition")

The Unicode version of the markup, following conversion. This
is set to None if there was simply no way to convert the
bytestring to Unicode (as with binary data).

*exception* bs4.UnusualUsageWarning[¶](#bs4.UnusualUsageWarning "Link to this definition")

Bases: [`UserWarning`](https://docs.python.org/3/library/exceptions.html#UserWarning "(in Python v3.13)")

A superclass for warnings issued when Beautiful Soup sees
something that is typically the result of a mistake in the calling
code, but might be intentional on the part of the user. If it is
in fact intentional, you can filter the individual warning class
to get rid of the warning. If you don't like Beautiful Soup
second-guessing what you are doing, you can filter the
UnusualUsageWarningclass itself and get rid of these entirely.

*exception* bs4.XMLParsedAsHTMLWarning[¶](#bs4.XMLParsedAsHTMLWarning "Link to this definition")

Bases: [`UnusualUsageWarning`](#bs4.UnusualUsageWarning "bs4._warnings.UnusualUsageWarning")

The warning issued when an HTML parser is used to parse
XML that is not (as far as we can tell) XHTML.

MESSAGE*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= 'It looks like you\'re using an HTML parser to parse an XML document.\n\nAssuming this really is an XML document, what you\'re doing might work, but you should know that using an XML parser will be more reliable. To parse this document as XML, make sure you have the Python package \'lxml\' installed, and pass the keyword argument `features="xml"` into the BeautifulSoup constructor.\n\nIf you want or need to use an HTML parser on this document, you can make this warning go away by filtering it. To do that, run this code before calling the BeautifulSoup constructor:\n\n    from bs4 import XMLParsedAsHTMLWarning\n    import warnings\n\n    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)\n'*[¶](#bs4.XMLParsedAsHTMLWarning.MESSAGE "Link to this definition")

## Subpackages[¶](#subpackages "Link to this heading")

* [bs4.builder package](bs4.builder.html)


## Submodules[¶](#submodules "Link to this heading")


## bs4.css module[¶](#module-bs4.css "Link to this heading")

Integration code for CSS selectors using [Soup Sieve](https://facelessuser.github.io/soupsieve/) (pypi: `soupsieve`).

Acquire a [`CSS`](#bs4.css.CSS "bs4.css.CSS") object through the [`element.Tag.css`](#bs4.element.Tag.css "bs4.element.Tag.css") attribute of
the starting point of your CSS selector, or (if you want to run a
selector against the entire document) of the [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") object
itself.

The main advantage of doing this instead of using `soupsieve`
functions is that you don't need to keep passing the [`element.Tag`](#bs4.element.Tag "bs4.element.Tag") to be
selected against, since the [`CSS`](#bs4.css.CSS "bs4.css.CSS") object is permanently scoped to that
[`element.Tag`](#bs4.element.Tag "bs4.element.Tag").

*class* bs4.css.CSS(*tag: [element.Tag](#bs4.element.Tag "bs4.element.Tag")*, *api: ModuleType | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.css.CSS "Link to this definition")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")

A proxy object against the `soupsieve` library, to simplify its
CSS selector API.

You don't need to instantiate this class yourself; instead, use
[`element.Tag.css`](#bs4.element.Tag.css "bs4.element.Tag.css").

Parameters:

* **tag** -- All CSS selectors run by this object will use this as
  their starting point.
* **api** -- An optional drop-in replacement for the `soupsieve` module,
  intended for use in unit tests.

closest(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → [element.Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.css.CSS.closest "Link to this definition")

Find the [`element.Tag`](#bs4.element.Tag "bs4.element.Tag") closest to this one that matches the given selector.

This uses the Soup Sieve library. For more information, see
that library's documentation for the [soupsieve.closest()](https://facelessuser.github.io/soupsieve/api/#soupsieveclosest)
method.

Parameters:

* **selector** -- A string containing a CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will pass in the prefixes it encountered while
  parsing the document.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.closest()](https://facelessuser.github.io/soupsieve/api/#soupsieveclosest) method.
* **kwargs** --
  
  Keyword arguments to be passed into Soup Sieve's
  [soupsieve.closest()](https://facelessuser.github.io/soupsieve/api/#soupsieveclosest) method.

compile(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → SoupSieve[¶](#bs4.css.CSS.compile "Link to this definition")

Pre-compile a selector and return the compiled object.

Parameters:

* **selector** -- A CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will use the prefixes it encountered while
  parsing the document.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.compile()](https://facelessuser.github.io/soupsieve/api/#soupsievecompile) method.
* **kwargs** --
  
  Keyword arguments to be passed into Soup Sieve's
  [soupsieve.compile()](https://facelessuser.github.io/soupsieve/api/#soupsievecompile) method.

Returns:

A precompiled selector object.

Return type:

soupsieve.SoupSieve

escape(*ident: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.css.CSS.escape "Link to this definition")

Escape a CSS identifier.

This is a simple wrapper around [soupsieve.escape()](https://facelessuser.github.io/soupsieve/api/#soupsieveescape). See the
documentation for that function for more information.

filter(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → [ResultSet](#bs4.ResultSet "bs4.ResultSet")[[element.Tag](#bs4.element.Tag "bs4.element.Tag")][¶](#bs4.css.CSS.filter "Link to this definition")

Filter this [`element.Tag`](#bs4.element.Tag "bs4.element.Tag")'s direct children based on the given CSS selector.

This uses the Soup Sieve library. It works the same way as
passing a [`element.Tag`](#bs4.element.Tag "bs4.element.Tag") into that library's [soupsieve.filter()](https://facelessuser.github.io/soupsieve/api/#soupsievefilter)
method. For more information, see the documentation for
[soupsieve.filter()](https://facelessuser.github.io/soupsieve/api/#soupsievefilter).

Parameters:

* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will pass in the prefixes it encountered while
  parsing the document.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.filter()](https://facelessuser.github.io/soupsieve/api/#soupsievefilter)
  method.
* **kwargs** --
  
  Keyword arguments to be passed into SoupSieve's
  [soupsieve.filter()](https://facelessuser.github.io/soupsieve/api/#soupsievefilter)
  method.

iselect(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → Iterator[[element.Tag](#bs4.element.Tag "bs4.element.Tag")][¶](#bs4.css.CSS.iselect "Link to this definition")

Perform a CSS selection operation on the current [`element.Tag`](#bs4.element.Tag "bs4.element.Tag").

This uses the Soup Sieve library. For more information, see
that library's documentation for the [soupsieve.iselect()](https://facelessuser.github.io/soupsieve/api/#soupsieveiselect)
method. It is the same as select(), but it returns a generator
instead of a list.

Parameters:

* **selector** -- A string containing a CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will pass in the prefixes it encountered while
  parsing the document.
* **limit** -- After finding this number of results, stop looking.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.iselect()](https://facelessuser.github.io/soupsieve/api/#soupsieveiselect) method.
* **kwargs** --
  
  Keyword arguments to be passed into Soup Sieve's
  [soupsieve.iselect()](https://facelessuser.github.io/soupsieve/api/#soupsieveiselect) method.

match(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.css.CSS.match "Link to this definition")

Check whether or not this [`element.Tag`](#bs4.element.Tag "bs4.element.Tag") matches the given CSS selector.

This uses the Soup Sieve library. For more information, see
that library's documentation for the [soupsieve.match()](https://facelessuser.github.io/soupsieve/api/#soupsievematch)
method.

Param:

a CSS selector.

Parameters:

* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will pass in the prefixes it encountered while
  parsing the document.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.match()](https://facelessuser.github.io/soupsieve/api/#soupsievematch)
  method.
* **kwargs** --
  
  Keyword arguments to be passed into SoupSieve's
  [soupsieve.match()](https://facelessuser.github.io/soupsieve/api/#soupsievematch)
  method.

select(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → [ResultSet](#bs4.ResultSet "bs4.ResultSet")[[element.Tag](#bs4.element.Tag "bs4.element.Tag")][¶](#bs4.css.CSS.select "Link to this definition")

Perform a CSS selection operation on the current [`element.Tag`](#bs4.element.Tag "bs4.element.Tag").

This uses the Soup Sieve library. For more information, see
that library's documentation for the [soupsieve.select()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect) method.

Parameters:

* **selector** -- A CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will pass in the prefixes it encountered while
  parsing the document.
* **limit** -- After finding this number of results, stop looking.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.select()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect) method.
* **kwargs** --
  
  Keyword arguments to be passed into Soup Sieve's
  [soupsieve.select()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect) method.

select\_one(*select: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: \_NamespaceMapping | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *flags: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: Any*) → [element.Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.css.CSS.select_one "Link to this definition")

Perform a CSS selection operation on the current Tag and return the
first result, if any.

This uses the Soup Sieve library. For more information, see
that library's documentation for the [soupsieve.select\_one()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect_one) method.

Parameters:

* **selector** -- A CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will use the prefixes it encountered while
  parsing the document.
* **flags** --
  
  Flags to be passed into Soup Sieve's
  [soupsieve.select\_one()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect_one) method.
* **kwargs** --
  
  Keyword arguments to be passed into Soup Sieve's
  [soupsieve.select\_one()](https://facelessuser.github.io/soupsieve/api/#soupsieveselect_one) method.

## bs4.dammit module[¶](#module-bs4.dammit "Link to this heading")

Beautiful Soup bonus library: Unicode, Dammit

This library converts a bytestream to Unicode through any means
necessary. It is heavily based on code from Mark Pilgrim's [Universal
Feed Parser](https://pypi.org/project/feedparser/), now maintained
by Kurt McKee. It does not rewrite the body of an XML or HTML document
to reflect a new encoding; that's the job of [`TreeBuilder`](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder").

*class* bs4.dammit.EncodingDetector(*markup: [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*, *known\_definite\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *is\_html: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = False*, *exclude\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *user\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *override\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.dammit.EncodingDetector "Link to this definition")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")

This class is capable of guessing a number of possible encodings
for a bytestring.

Order of precedence:

1. Encodings you specifically tell EncodingDetector to try first
   (the `known_definite_encodings` argument to the constructor).
2. An encoding determined by sniffing the document's byte-order mark.
3. Encodings you specifically tell EncodingDetector to try if
   byte-order mark sniffing fails (the `user_encodings` argument to the
   constructor).
4. An encoding declared within the bytestring itself, either in an
   XML declaration (if the bytestring is to be interpreted as an XML
   document), or in a <meta> tag (if the bytestring is to be
   interpreted as an HTML document.)
5. An encoding detected through textual analysis by chardet,
   cchardet, or a similar external library.
6. UTF-8.
7. Windows-1252.

Parameters:

* **markup** -- Some markup in an unknown encoding.
* **known\_definite\_encodings** --
  
  When determining the encoding
  of `markup`, these encodings will be tried first, in
  order. In HTML terms, this corresponds to the "known
  definite encoding" step defined in [section 13.2.3.1 of the HTML standard](https://html.spec.whatwg.org/multipage/parsing.html#parsing-with-a-known-character-encoding).
* **user\_encodings** --
  
  These encodings will be tried after the
  `known_definite_encodings` have been tried and failed, and
  after an attempt to sniff the encoding by looking at a
  byte order mark has failed. In HTML terms, this
  corresponds to the step "user has explicitly instructed
  the user agent to override the document's character
  encoding", defined in [section 13.2.3.2 of the HTML standard](https://html.spec.whatwg.org/multipage/parsing.html#determining-the-character-encoding).
* **override\_encodings** -- A **deprecated** alias for
  `known_definite_encodings`. Any encodings here will be tried
  immediately after the encodings in
  `known_definite_encodings`.
* **is\_html** -- If True, this markup is considered to be
  HTML. Otherwise it's assumed to be XML.
* **exclude\_encodings** -- These encodings will not be tried,
  even if they otherwise would be.

chardet\_encoding*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.dammit.EncodingDetector.chardet_encoding "Link to this definition")
declared\_encoding*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.dammit.EncodingDetector.declared_encoding "Link to this definition")
*property* encodings*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EncodingDetector.encodings "Link to this definition")

Yield a number of encodings that might work for this markup.

Yield:

A sequence of strings. Each is the name of an encoding
that *might* work to convert a bytestring into Unicode.

exclude\_encodings*: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EncodingDetector.exclude_encodings "Link to this definition")
*classmethod* find\_declared\_encoding(*markup: [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *is\_html: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*, *search\_entire\_document: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.dammit.EncodingDetector.find_declared_encoding "Link to this definition")

Given a document, tries to find an encoding declared within the
text of the document itself.

An XML encoding is declared at the beginning of the document.

An HTML encoding is declared in a <meta> tag, hopefully near the
beginning of the document.

Parameters:

* **markup** -- Some markup.
* **is\_html** -- If True, this markup is considered to be HTML. Otherwise
  it's assumed to be XML.
* **search\_entire\_document** -- Since an encoding is supposed
  to declared near the beginning of the document, most of
  the time it's only necessary to search a few kilobytes of
  data. Set this to True to force this method to search the
  entire document.

Returns:

The declared encoding, if one is found.

is\_html*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.dammit.EncodingDetector.is_html "Link to this definition")
known\_definite\_encodings*: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EncodingDetector.known_definite_encodings "Link to this definition")
markup*: [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*[¶](#bs4.dammit.EncodingDetector.markup "Link to this definition")
sniffed\_encoding*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.dammit.EncodingDetector.sniffed_encoding "Link to this definition")
*classmethod* strip\_byte\_order\_mark(*data: [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*) → [Tuple](https://docs.python.org/3/library/typing.html#typing.Tuple "(in Python v3.13)")[[bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")][¶](#bs4.dammit.EncodingDetector.strip_byte_order_mark "Link to this definition")

If a byte-order mark is present, strip it and return the encoding it implies.

Parameters:

**data** -- A bytestring that may or may not begin with a
byte-order mark.

Returns:

A 2-tuple (data stripped of byte-order mark, encoding implied by byte-order mark)

user\_encodings*: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EncodingDetector.user_encodings "Link to this definition")
*class* bs4.dammit.EntitySubstitution[¶](#bs4.dammit.EntitySubstitution "Link to this definition")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")

The ability to substitute XML or HTML entities for certain characters.

AMPERSAND\_OR\_BRACKET*: [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EntitySubstitution.AMPERSAND_OR_BRACKET "Link to this definition")

A regular expression matching an angle bracket or an ampersand.

ANY\_ENTITY\_RE *= re.compile('&(#\\d+|#x[0-9a-fA-F]+|\\w+);', re.IGNORECASE)*[¶](#bs4.dammit.EntitySubstitution.ANY_ENTITY_RE "Link to this definition")
BARE\_AMPERSAND\_OR\_BRACKET*: [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EntitySubstitution.BARE_AMPERSAND_OR_BRACKET "Link to this definition")

A regular expression matching an angle bracket or an ampersand that
is not part of an XML or HTML entity.

CHARACTER\_TO\_HTML\_ENTITY*: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EntitySubstitution.CHARACTER_TO_HTML_ENTITY "Link to this definition")

A map of Unicode strings to the corresponding named HTML entities;
the inverse of HTML\_ENTITY\_TO\_CHARACTER.

CHARACTER\_TO\_HTML\_ENTITY\_RE*: [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EntitySubstitution.CHARACTER_TO_HTML_ENTITY_RE "Link to this definition")

A regular expression that matches any character (or, in rare
cases, pair of characters) that can be replaced with a named
HTML entity.

CHARACTER\_TO\_HTML\_ENTITY\_WITH\_AMPERSAND\_RE*: [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EntitySubstitution.CHARACTER_TO_HTML_ENTITY_WITH_AMPERSAND_RE "Link to this definition")

A very similar regular expression to
CHARACTER\_TO\_HTML\_ENTITY\_RE, but which also matches unescaped
ampersands. This is used by the 'html' formatted to provide
backwards-compatibility, even though the HTML5 spec allows most
ampersands to go unescaped.

CHARACTER\_TO\_XML\_ENTITY*: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EntitySubstitution.CHARACTER_TO_XML_ENTITY "Link to this definition")

A map of Unicode strings to the corresponding named XML entities.

HTML\_ENTITY\_TO\_CHARACTER*: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.EntitySubstitution.HTML_ENTITY_TO_CHARACTER "Link to this definition")

A map of named HTML entities to the corresponding Unicode string.

*classmethod* quoted\_attribute\_value(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.dammit.EntitySubstitution.quoted_attribute_value "Link to this definition")

Make a value into a quoted XML attribute, possibly escaping it.

> Most strings will be quoted using double quotes.
> 
> > Bob's Bar -> "Bob's Bar"
> 
> If a string contains double quotes, it will be quoted using
> single quotes.
> 
> > Welcome to "my bar" -> 'Welcome to "my bar"'
> 
> If a string contains both single and double quotes, the
> double quotes will be escaped, and the string will be quoted
> using double quotes.
> 
> > Welcome to "Bob's Bar" -> Welcome to &quot;Bob's bar&quot;

Parameters:

**value** -- The XML attribute value to quote

Returns:

The quoted value

*classmethod* substitute\_html(*s: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.dammit.EntitySubstitution.substitute_html "Link to this definition")

Replace certain Unicode characters with named HTML entities.

This differs from `data.encode(encoding, 'xmlcharrefreplace')`
in that the goal is to make the result more readable (to those
with ASCII displays) rather than to recover from
errors. There's absolutely nothing wrong with a UTF-8 string
containg a LATIN SMALL LETTER E WITH ACUTE, but replacing that
character with "&eacute;" will make it more readable to some
people.

Parameters:

**s** -- The string to be modified.

Returns:

The string with some Unicode characters replaced with
HTML entities.

*classmethod* substitute\_html5(*s: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.dammit.EntitySubstitution.substitute_html5 "Link to this definition")

Replace certain Unicode characters with named HTML entities
using HTML5 rules.

Specifically, this method is much less aggressive about
escaping ampersands than substitute\_html. Only ambiguous
ampersands are escaped, per the HTML5 standard:

"An ambiguous ampersand is a U+0026 AMPERSAND character (&)
that is followed by one or more ASCII alphanumerics, followed
by a U+003B SEMICOLON character (;), where these characters do
not match any of the names given in the named character
references section."

Unlike substitute\_html5\_raw, this method assumes HTML entities
were converted to Unicode characters on the way in, as
Beautiful Soup does. By the time Beautiful Soup does its work,
the only ambiguous ampersands that need to be escaped are the
ones that were escaped in the original markup when mentioning
HTML entities.

Parameters:

**s** -- The string to be modified.

Returns:

The string with some Unicode characters replaced with
HTML entities.

*classmethod* substitute\_html5\_raw(*s: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.dammit.EntitySubstitution.substitute_html5_raw "Link to this definition")

Replace certain Unicode characters with named HTML entities
using HTML5 rules.

substitute\_html5\_raw is similar to substitute\_html5 but it is
designed for standalone use (whereas substitute\_html5 is
designed for use with Beautiful Soup).

Parameters:

**s** -- The string to be modified.

Returns:

The string with some Unicode characters replaced with
HTML entities.

*classmethod* substitute\_xml(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *make\_quoted\_attribute: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.dammit.EntitySubstitution.substitute_xml "Link to this definition")

Replace special XML characters with named XML entities.

The less-than sign will become &lt;, the greater-than sign
will become &gt;, and any ampersands will become &amp;. If you
want ampersands that seem to be part of an entity definition
to be left alone, use [`substitute_xml_containing_entities`](#bs4.dammit.EntitySubstitution.substitute_xml_containing_entities "bs4.dammit.EntitySubstitution.substitute_xml_containing_entities")
instead.

Parameters:

* **value** -- A string to be substituted.
* **make\_quoted\_attribute** -- If True, then the string will be
  quoted, as befits an attribute value.

Returns:

A version of `value` with special characters replaced
with named entities.

*classmethod* substitute\_xml\_containing\_entities(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *make\_quoted\_attribute: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.dammit.EntitySubstitution.substitute_xml_containing_entities "Link to this definition")

Substitute XML entities for special XML characters.

Parameters:

* **value** -- A string to be substituted. The less-than sign will
  become &lt;, the greater-than sign will become &gt;, and any
  ampersands that are not part of an entity defition will
  become &amp;.
* **make\_quoted\_attribute** -- If True, then the string will be
  quoted, as befits an attribute value.

*class* bs4.dammit.UnicodeDammit(*markup: [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*, *known\_definite\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = []*, *smart\_quotes\_to: [Literal](https://docs.python.org/3/library/typing.html#typing.Literal "(in Python v3.13)")['ascii', 'xml', 'html'] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *is\_html: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*, *exclude\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = []*, *user\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *override\_encodings: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.dammit.UnicodeDammit "Link to this definition")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")

A class for detecting the encoding of a bytestring containing an
HTML or XML document, and decoding it to Unicode. If the source
encoding is windows-1252, [`UnicodeDammit`](#bs4.dammit.UnicodeDammit "bs4.dammit.UnicodeDammit") can also replace
Microsoft smart quotes with their HTML or XML equivalents.

Parameters:

* **markup** -- HTML or XML markup in an unknown encoding.
* **known\_definite\_encodings** --
  
  When determining the encoding
  of `markup`, these encodings will be tried first, in
  order. In HTML terms, this corresponds to the "known
  definite encoding" step defined in [section 13.2.3.1 of the HTML standard](https://html.spec.whatwg.org/multipage/parsing.html#parsing-with-a-known-character-encoding).
* **user\_encodings** --
  
  These encodings will be tried after the
  `known_definite_encodings` have been tried and failed, and
  after an attempt to sniff the encoding by looking at a
  byte order mark has failed. In HTML terms, this
  corresponds to the step "user has explicitly instructed
  the user agent to override the document's character
  encoding", defined in [section 13.2.3.2 of the HTML standard](https://html.spec.whatwg.org/multipage/parsing.html#determining-the-character-encoding).
* **override\_encodings** -- A **deprecated** alias for
  `known_definite_encodings`. Any encodings here will be tried
  immediately after the encodings in
  `known_definite_encodings`.
* **smart\_quotes\_to** -- By default, Microsoft smart quotes will,
  like all other characters, be converted to Unicode
  characters. Setting this to `ascii` will convert them to ASCII
  quotes instead. Setting it to `xml` will convert them to XML
  entity references, and setting it to `html` will convert them
  to HTML entity references.
* **is\_html** -- If True, `markup` is treated as an HTML
  document. Otherwise it's treated as an XML document.
* **exclude\_encodings** -- These encodings will not be considered,
  even if the sniffing code thinks they might make sense.

CHARSET\_ALIASES*: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.UnicodeDammit.CHARSET_ALIASES "Link to this definition")

This dictionary maps commonly seen values for "charset" in HTML
meta tags to the corresponding Python codec names. It only covers
values that aren't in Python's aliases and can't be determined
by the heuristics in [`find_codec`](#bs4.dammit.UnicodeDammit.find_codec "bs4.dammit.UnicodeDammit.find_codec").

ENCODINGS\_WITH\_SMART\_QUOTES*: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.dammit.UnicodeDammit.ENCODINGS_WITH_SMART_QUOTES "Link to this definition")

A list of encodings that tend to contain Microsoft smart quotes.

MS\_CHARS*: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [Tuple](https://docs.python.org/3/library/typing.html#typing.Tuple "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]]*[¶](#bs4.dammit.UnicodeDammit.MS_CHARS "Link to this definition")

A partial mapping of ISO-Latin-1 to HTML entities/XML numeric entities.

WINDOWS\_1252\_TO\_UTF8*: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)"), [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")]*[¶](#bs4.dammit.UnicodeDammit.WINDOWS_1252_TO_UTF8 "Link to this definition")

A map used when removing rogue Windows-1252/ISO-8859-1
characters in otherwise UTF-8 documents.

Note that \x81, \x8d, \x8f, \x90, and \x9d are undefined in
Windows-1252.

contains\_replacement\_characters*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.dammit.UnicodeDammit.contains_replacement_characters "Link to this definition")

This is True if [`UnicodeDammit.unicode_markup`](#bs4.dammit.UnicodeDammit.unicode_markup "bs4.dammit.UnicodeDammit.unicode_markup") contains
U+FFFD REPLACEMENT\_CHARACTER characters which were not present
in [`UnicodeDammit.markup`](#bs4.dammit.UnicodeDammit.markup "bs4.dammit.UnicodeDammit.markup"). These mark character sequences that
could not be represented in Unicode.

*property* declared\_html\_encoding*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.dammit.UnicodeDammit.declared_html_encoding "Link to this definition")

If the markup is an HTML document, returns the encoding, if any,
declared *inside* the document.

*classmethod* detwingle(*in\_bytes: [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*, *main\_encoding: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 'utf8'*, *embedded\_encoding: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 'windows-1252'*) → [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")[¶](#bs4.dammit.UnicodeDammit.detwingle "Link to this definition")

Fix characters from one encoding embedded in some other encoding.

Currently the only situation supported is Windows-1252 (or its
subset ISO-8859-1), embedded in UTF-8.

Parameters:

* **in\_bytes** -- A bytestring that you suspect contains
  characters from multiple encodings. Note that this *must*
  be a bytestring. If you've already converted the document
  to Unicode, you're too late.
* **main\_encoding** -- The primary encoding of `in_bytes`.
* **embedded\_encoding** -- The encoding that was used to embed characters
  in the main document.

Returns:

A bytestring similar to `in_bytes`, in which
`embedded_encoding` characters have been converted to
their `main_encoding` equivalents.

find\_codec(*charset: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.dammit.UnicodeDammit.find_codec "Link to this definition")

Look up the Python codec corresponding to a given character set.

Parameters:

**charset** -- The name of a character set.

Returns:

The name of a Python codec.

markup*: [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*[¶](#bs4.dammit.UnicodeDammit.markup "Link to this definition")

The original markup, before it was converted to Unicode.
This is not necessarily the same as what was passed in to the
constructor, since any byte-order mark will be stripped.

original\_encoding*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.dammit.UnicodeDammit.original_encoding "Link to this definition")

Unicode, Dammit's best guess as to the original character
encoding of [`UnicodeDammit.markup`](#bs4.dammit.UnicodeDammit.markup "bs4.dammit.UnicodeDammit.markup").

smart\_quotes\_to*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.dammit.UnicodeDammit.smart_quotes_to "Link to this definition")

The strategy used to handle Microsoft smart quotes.

tried\_encodings*: [List](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[[Tuple](https://docs.python.org/3/library/typing.html#typing.Tuple "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]]*[¶](#bs4.dammit.UnicodeDammit.tried_encodings "Link to this definition")

The (encoding, error handling strategy) 2-tuples that were used to
try and convert the markup to Unicode.

unicode\_markup*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.dammit.UnicodeDammit.unicode_markup "Link to this definition")

The Unicode version of the markup, following conversion. This
is set to None if there was simply no way to convert the
bytestring to Unicode (as with binary data).


## bs4.element module[¶](#module-bs4.element "Link to this heading")

*class* bs4.element.AttributeDict[¶](#bs4.element.AttributeDict "Link to this definition")

Bases: [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[`Any`](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)"), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")]

Superclass for the dictionary used to hold a tag's
attributes. You can use this, but it's just a regular dict with no
special logic.

*class* bs4.element.AttributeValueList(*iterable=()*, */*)[¶](#bs4.element.AttributeValueList "Link to this definition")

Bases: [`List`](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]

Class for the list used to hold the values of attributes which
have multiple values (such as HTML's 'class'). It's just a regular
list, but you can subclass it and pass it in to the TreeBuilder
constructor as attribute\_value\_list\_class, to have your subclass
instantiated instead.

*class* bs4.element.AttributeValueWithCharsetSubstitution[¶](#bs4.element.AttributeValueWithCharsetSubstitution "Link to this definition")

Bases: [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")

An abstract class standing in for a character encoding specified
inside an HTML `<meta>` tag.

Subclasses exist for each place such a character encoding might be
found: either inside the `charset` attribute
([`CharsetMetaAttributeValue`](#bs4.element.CharsetMetaAttributeValue "bs4.element.CharsetMetaAttributeValue")) or inside the `content` attribute
([`ContentMetaAttributeValue`](#bs4.element.ContentMetaAttributeValue "bs4.element.ContentMetaAttributeValue"))

This allows Beautiful Soup to replace that part of the HTML file
with a different encoding when ouputting a tree as a string.

substitute\_encoding(*eventual\_encoding: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.element.AttributeValueWithCharsetSubstitution.substitute_encoding "Link to this definition")

Do whatever's necessary in this implementation-specific
portion an HTML document to substitute in a specific encoding.

*class* bs4.element.CData(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.CData "Link to this definition")

Bases: [`PreformattedString`](#bs4.element.PreformattedString "bs4.element.PreformattedString")

A [CDATA section](https://dev.w3.org/html5/spec-LC/syntax.html#cdata-sections).

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<![CDATA['*[¶](#bs4.element.CData.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= ']]>'*[¶](#bs4.element.CData.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

next\_element*: \_AtMostOneElement*[¶](#bs4.element.CData.next_element "Link to this definition")
next\_sibling*: \_AtMostOneElement*[¶](#bs4.element.CData.next_sibling "Link to this definition")
parent*: [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.CData.parent "Link to this definition")
previous\_element*: \_AtMostOneElement*[¶](#bs4.element.CData.previous_element "Link to this definition")
previous\_sibling*: \_AtMostOneElement*[¶](#bs4.element.CData.previous_sibling "Link to this definition")
*class* bs4.element.CharsetMetaAttributeValue(*original\_value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*)[¶](#bs4.element.CharsetMetaAttributeValue "Link to this definition")

Bases: [`AttributeValueWithCharsetSubstitution`](#bs4.element.AttributeValueWithCharsetSubstitution "bs4.element.AttributeValueWithCharsetSubstitution")

A generic stand-in for the value of a `<meta>` tag's `charset`
attribute.

When Beautiful Soup parses the markup `<meta charset="utf8">`, the
value of the `charset` attribute will become one of these objects.

If the document is later encoded to an encoding other than UTF-8, its
`<meta>` tag will mention the new encoding instead of `utf8`.

substitute\_encoding(*eventual\_encoding: \_Encoding = 'utf-8'*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.element.CharsetMetaAttributeValue.substitute_encoding "Link to this definition")

When an HTML document is being encoded to a given encoding, the
value of a `<meta>` tag's `charset` becomes the name of
the encoding.

*class* bs4.element.Comment(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.Comment "Link to this definition")

Bases: [`PreformattedString`](#bs4.element.PreformattedString "bs4.element.PreformattedString")

An [HTML comment](https://dev.w3.org/html5/spec-LC/syntax.html#comments) or [XML comment](https://www.w3.org/TR/REC-xml/#sec-comments).

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<!--'*[¶](#bs4.element.Comment.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '-->'*[¶](#bs4.element.Comment.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

next\_element*: \_AtMostOneElement*[¶](#bs4.element.Comment.next_element "Link to this definition")
next\_sibling*: \_AtMostOneElement*[¶](#bs4.element.Comment.next_sibling "Link to this definition")
parent*: [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Comment.parent "Link to this definition")
previous\_element*: \_AtMostOneElement*[¶](#bs4.element.Comment.previous_element "Link to this definition")
previous\_sibling*: \_AtMostOneElement*[¶](#bs4.element.Comment.previous_sibling "Link to this definition")
*class* bs4.element.ContentMetaAttributeValue(*original\_value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*)[¶](#bs4.element.ContentMetaAttributeValue "Link to this definition")

Bases: [`AttributeValueWithCharsetSubstitution`](#bs4.element.AttributeValueWithCharsetSubstitution "bs4.element.AttributeValueWithCharsetSubstitution")

A generic stand-in for the value of a `<meta>` tag's `content`
attribute.

When Beautiful Soup parses the markup:

`<meta http-equiv="content-type" content="text/html; charset=utf8">`

The value of the `content` attribute will become one of these objects.

If the document is later encoded to an encoding other than UTF-8, its
`<meta>` tag will mention the new encoding instead of `utf8`.

CHARSET\_RE*: [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]* *= re.compile('((^|;)\\s\*charset=)([^;]\*)', re.MULTILINE)*[¶](#bs4.element.ContentMetaAttributeValue.CHARSET_RE "Link to this definition")

Match the 'charset' argument inside the 'content' attribute
of a <meta> tag.
:meta private:

substitute\_encoding(*eventual\_encoding: \_Encoding = 'utf-8'*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.element.ContentMetaAttributeValue.substitute_encoding "Link to this definition")

When an HTML document is being encoded to a given encoding, the
value of the `charset=` in a `<meta>` tag's `content` becomes
the name of the encoding.

bs4.element.DEFAULT\_OUTPUT\_ENCODING*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= 'utf-8'*[¶](#bs4.element.DEFAULT_OUTPUT_ENCODING "Link to this definition")

Documents output by Beautiful Soup will be encoded with
this encoding unless you specify otherwise.

*class* bs4.element.Declaration(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.Declaration "Link to this definition")

Bases: [`PreformattedString`](#bs4.element.PreformattedString "bs4.element.PreformattedString")

An [XML declaration](https://www.w3.org/TR/REC-xml/#sec-prolog-dtd).

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<?'*[¶](#bs4.element.Declaration.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '?>'*[¶](#bs4.element.Declaration.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

next\_element*: \_AtMostOneElement*[¶](#bs4.element.Declaration.next_element "Link to this definition")
next\_sibling*: \_AtMostOneElement*[¶](#bs4.element.Declaration.next_sibling "Link to this definition")
parent*: [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Declaration.parent "Link to this definition")
previous\_element*: \_AtMostOneElement*[¶](#bs4.element.Declaration.previous_element "Link to this definition")
previous\_sibling*: \_AtMostOneElement*[¶](#bs4.element.Declaration.previous_sibling "Link to this definition")
*class* bs4.element.Doctype(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.Doctype "Link to this definition")

Bases: [`PreformattedString`](#bs4.element.PreformattedString "bs4.element.PreformattedString")

A [document type declaration](https://www.w3.org/TR/REC-xml/#dt-doctype).

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<!DOCTYPE '*[¶](#bs4.element.Doctype.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '>\n'*[¶](#bs4.element.Doctype.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

*classmethod* for\_name\_and\_ids(*name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *pub\_id: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*, *system\_id: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*) → [Doctype](#bs4.element.Doctype "bs4.element.Doctype")[¶](#bs4.element.Doctype.for_name_and_ids "Link to this definition")

Generate an appropriate document type declaration for a given
public ID and system ID.

Parameters:

* **name** -- The name of the document's root element, e.g. 'html'.
* **pub\_id** -- The Formal Public Identifier for this document type,
  e.g. '-//W3C//DTD XHTML 1.1//EN'
* **system\_id** -- The system identifier for this document type,
  e.g. '<http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd>'

next\_element*: \_AtMostOneElement*[¶](#bs4.element.Doctype.next_element "Link to this definition")
next\_sibling*: \_AtMostOneElement*[¶](#bs4.element.Doctype.next_sibling "Link to this definition")
parent*: [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Doctype.parent "Link to this definition")
previous\_element*: \_AtMostOneElement*[¶](#bs4.element.Doctype.previous_element "Link to this definition")
previous\_sibling*: \_AtMostOneElement*[¶](#bs4.element.Doctype.previous_sibling "Link to this definition")
*class* bs4.element.HTMLAttributeDict[¶](#bs4.element.HTMLAttributeDict "Link to this definition")

Bases: [`AttributeDict`](#bs4.element.AttributeDict "bs4.element.AttributeDict")

A dictionary for holding a Tag's attributes, which processes
incoming values for consistency with the HTML spec, which says
'Attribute values are a mixture of text and character
references...'

Basically, this means converting common non-string values into
strings, like XMLAttributeDict, though HTML also has some rules
around boolean attributes that XML doesn't have.

*class* bs4.element.NamespacedAttribute(*prefix: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*, *name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *namespace: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.element.NamespacedAttribute "Link to this definition")

Bases: [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")

A namespaced attribute (e.g. the 'xml:lang' in 'xml:lang="en"')
which remembers the namespace prefix ('xml') and the name ('lang')
that were used to create it.

name*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.NamespacedAttribute.name "Link to this definition")
namespace*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.NamespacedAttribute.namespace "Link to this definition")
prefix*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.NamespacedAttribute.prefix "Link to this definition")
*class* bs4.element.NavigableString(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.NavigableString "Link to this definition")

Bases: [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement")

A Python string that is part of a parse tree.

When Beautiful Soup parses the markup `<b>penguin</b>`, it will
create a [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") for the string "penguin".

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= ''*[¶](#bs4.element.NavigableString.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= ''*[¶](#bs4.element.NavigableString.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

output\_ready(*formatter: \_FormatterOrName = 'minimal'*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.element.NavigableString.output_ready "Link to this definition")

Run the string through the provided formatter, making it
ready for output as part of an HTML or XML document.

Parameters:

**formatter** -- A [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string naming one
of the standard formatters.

*property* strings*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.element.NavigableString.strings "Link to this definition")

Yield this string, but only if it is interesting.

This is defined the way it is for compatibility with
[`Tag.strings`](#bs4.element.Tag.strings "bs4.element.Tag.strings"). See [`Tag`](#bs4.element.Tag "bs4.element.Tag") for information on which strings are
interesting in a given context.

Yield:

A sequence that either contains this string, or is empty.

bs4.element.PYTHON\_SPECIFIC\_ENCODINGS*: Set[\_Encoding]* *= {'idna', 'mbcs', 'oem', 'palmos', 'punycode', 'raw-unicode-escape', 'raw\_unicode\_escape', 'string-escape', 'string\_escape', 'undefined', 'unicode-escape', 'unicode\_escape'}*[¶](#bs4.element.PYTHON_SPECIFIC_ENCODINGS "Link to this definition")

These encodings are recognized by Python (so [`Tag.encode`](#bs4.element.Tag.encode "bs4.element.Tag.encode")
could theoretically support them) but XML and HTML don't recognize
them (so they should not show up in an XML or HTML document as that
document's encoding).

If an XML document is encoded in one of these encodings, no encoding
will be mentioned in the XML declaration. If an HTML document is
encoded in one of these encodings, and the HTML document has a
<meta> tag that mentions an encoding, the encoding will be given as
the empty string.

Source:
Python documentation, [Python Specific Encodings](https://docs.python.org/3/library/codecs.html#python-specific-encodings)

*class* bs4.element.PageElement[¶](#bs4.element.PageElement "Link to this definition")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")

An abstract class representing a single element in the parse tree.

[`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString"), [`Tag`](#bs4.element.Tag "bs4.element.Tag"), etc. are all subclasses of
[`PageElement`](#bs4.element.PageElement "bs4.element.PageElement"). For this reason you'll see a lot of methods that
return [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement"), but you'll never see an actual [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement")
object. For the most part you can think of [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") as
meaning "a [`Tag`](#bs4.element.Tag "bs4.element.Tag") or a [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString")."

decompose() → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.element.PageElement.decompose "Link to this definition")

Recursively destroys this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") and its children.

The element will be removed from the tree and wiped out; so
will everything beneath it.

The behavior of a decomposed [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") is undefined and you
should never use one for anything, but if you need to *check*
whether an element has been decomposed, you can use the
[`PageElement.decomposed`](#bs4.element.PageElement.decomposed "bs4.element.PageElement.decomposed") property.

*property* decomposed*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.element.PageElement.decomposed "Link to this definition")

Check whether a PageElement has been decomposed.

extract(*\_self\_index: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → [Self](https://docs.python.org/3/library/typing.html#typing.Self "(in Python v3.13)")[¶](#bs4.element.PageElement.extract "Link to this definition")

Destructively rips this element out of the tree.

Parameters:

**\_self\_index** -- The location of this element in its parent's
.contents, if known. Passing this in allows for a performance
optimization.

Returns:

this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement"), no longer part of the tree.

find\_all\_next(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\_stacklevel: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 2*, *\*\*kwargs: \_StrainableAttribute*) → \_QueryResults[¶](#bs4.element.PageElement.find_all_next "Link to this definition")

Find all [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects that match the given criteria and
appear later in the document than this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement").

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **string** -- A filter for a NavigableString with specific text.
* **limit** -- Stop looking after finding this many results.
* **\_stacklevel** -- Used internally to improve warning messages.

Kwargs:

Additional filters on attribute values.

find\_all\_previous(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\_stacklevel: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 2*, *\*\*kwargs: \_StrainableAttribute*) → \_QueryResults[¶](#bs4.element.PageElement.find_all_previous "Link to this definition")

Look backwards in the document from this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") and find all
[`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") that match the given criteria.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **string** -- A filter for a [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") with specific text.
* **limit** -- Stop looking after finding this many results.
* **\_stacklevel** -- Used internally to improve warning messages.

Kwargs:

Additional filters on attribute values.

find\_next(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: \_StrainableAttribute*) → \_AtMostOneElement[¶](#bs4.element.PageElement.find_next "Link to this definition")

Find the first PageElement that matches the given criteria and
appears later in the document than this PageElement.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **string** -- A filter for a NavigableString with specific text.

Kwargs:

Additional filters on attribute values.

find\_next\_sibling(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: \_StrainableAttribute*) → \_AtMostOneElement[¶](#bs4.element.PageElement.find_next_sibling "Link to this definition")

Find the closest sibling to this PageElement that matches the
given criteria and appears later in the document.

All find\_\* methods take a common set of arguments. See the
online documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **string** -- A filter for a [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") with specific text.

Kwargs:

Additional filters on attribute values.

find\_next\_siblings(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\_stacklevel: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 2*, *\*\*kwargs: \_StrainableAttribute*) → \_QueryResults[¶](#bs4.element.PageElement.find_next_siblings "Link to this definition")

Find all siblings of this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") that match the given criteria
and appear later in the document.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **string** -- A filter for a [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") with specific text.
* **limit** -- Stop looking after finding this many results.
* **\_stacklevel** -- Used internally to improve warning messages.

Kwargs:

Additional filters on attribute values.

find\_parent(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *\*\*kwargs: \_StrainableAttribute*) → \_AtMostOneElement[¶](#bs4.element.PageElement.find_parent "Link to this definition")

Find the closest parent of this PageElement that matches the given
criteria.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **self** -- Whether the PageElement itself should be considered
  as one of its 'parents'.

Kwargs:

Additional filters on attribute values.

find\_parents(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\_stacklevel: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 2*, *\*\*kwargs: \_StrainableAttribute*) → \_QueryResults[¶](#bs4.element.PageElement.find_parents "Link to this definition")

Find all parents of this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") that match the given criteria.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **limit** -- Stop looking after finding this many results.
* **\_stacklevel** -- Used internally to improve warning messages.

Kwargs:

Additional filters on attribute values.

find\_previous(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: \_StrainableAttribute*) → \_AtMostOneElement[¶](#bs4.element.PageElement.find_previous "Link to this definition")

Look backwards in the document from this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") and find the
first [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") that matches the given criteria.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **string** -- A filter for a [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") with specific text.

Kwargs:

Additional filters on attribute values.

find\_previous\_sibling(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: \_StrainableAttribute*) → \_AtMostOneElement[¶](#bs4.element.PageElement.find_previous_sibling "Link to this definition")

Returns the closest sibling to this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") that matches the
given criteria and appears earlier in the document.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **string** -- A filter for a [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") with specific text.

Kwargs:

Additional filters on attribute values.

find\_previous\_siblings(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\_stacklevel: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 2*, *\*\*kwargs: \_StrainableAttribute*) → \_QueryResults[¶](#bs4.element.PageElement.find_previous_siblings "Link to this definition")

Returns all siblings to this PageElement that match the
given criteria and appear earlier in the document.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **string** -- A filter for a NavigableString with specific text.
* **limit** -- Stop looking after finding this many results.
* **\_stacklevel** -- Used internally to improve warning messages.

Kwargs:

Additional filters on attribute values.

format\_string(*s: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *formatter: \_FormatterOrName | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.element.PageElement.format_string "Link to this definition")

Format the given string using the given formatter.

Parameters:

* **s** -- A string.
* **formatter** -- A Formatter object, or a string naming one of the standard formatters.

formatter\_for\_name(*formatter\_name: \_FormatterOrName | \_EntitySubstitutionFunction*) → [Formatter](#bs4.formatter.Formatter "bs4.formatter.Formatter")[¶](#bs4.element.PageElement.formatter_for_name "Link to this definition")

Look up or create a Formatter for the given identifier,
if necessary.

Parameters:

**formatter** -- Can be a [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object (used as-is), a
function (used as the entity substitution hook for an
[`bs4.formatter.XMLFormatter`](#bs4.formatter.XMLFormatter "bs4.formatter.XMLFormatter") or
[`bs4.formatter.HTMLFormatter`](#bs4.formatter.HTMLFormatter "bs4.formatter.HTMLFormatter")), or a string (used to look
up an [`bs4.formatter.XMLFormatter`](#bs4.formatter.XMLFormatter "bs4.formatter.XMLFormatter") or
[`bs4.formatter.HTMLFormatter`](#bs4.formatter.HTMLFormatter "bs4.formatter.HTMLFormatter") in the appropriate registry.

getText(*separator: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = ''*, *strip: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*, *types: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[Type](https://docs.python.org/3/library/typing.html#typing.Type "(in Python v3.13)")[[NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")]] = ()*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.element.PageElement.getText "Link to this definition")

Get all child strings of this PageElement, concatenated using the
given separator.

Parameters:

* **separator** -- Strings will be concatenated using this separator.
* **strip** -- If True, strings will be stripped before being
  concatenated.
* **types** -- A tuple of NavigableString subclasses. Any
  strings of a subclass not found in this list will be
  ignored. Although there are exceptions, the default
  behavior in most cases is to consider only NavigableString
  and CData objects. That means no comments, processing
  instructions, etc.

Returns:

A string.

get\_text(*separator: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = ''*, *strip: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*, *types: [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[Type](https://docs.python.org/3/library/typing.html#typing.Type "(in Python v3.13)")[[NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")]] = ()*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.element.PageElement.get_text "Link to this definition")

Get all child strings of this PageElement, concatenated using the
given separator.

Parameters:

* **separator** -- Strings will be concatenated using this separator.
* **strip** -- If True, strings will be stripped before being
  concatenated.
* **types** -- A tuple of NavigableString subclasses. Any
  strings of a subclass not found in this list will be
  ignored. Although there are exceptions, the default
  behavior in most cases is to consider only NavigableString
  and CData objects. That means no comments, processing
  instructions, etc.

Returns:

A string.

hidden*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")* *= False*[¶](#bs4.element.PageElement.hidden "Link to this definition")

Whether or not this element is hidden from generated output.
Only the [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") object itself is hidden.

insert\_after(*\*args: \_InsertableElement*) → List[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")][¶](#bs4.element.PageElement.insert_after "Link to this definition")

Makes the given element(s) the immediate successor of this one.

The elements will have the same [`PageElement.parent`](#bs4.element.PageElement.parent "bs4.element.PageElement.parent") as this
one, and the given elements will occur immediately after this
one.

Parameters:

**args** -- One or more PageElements.

:return The list of PageElements that were inserted.

insert\_before(*\*args: \_InsertableElement*) → List[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")][¶](#bs4.element.PageElement.insert_before "Link to this definition")

Makes the given element(s) the immediate predecessor of this one.

All the elements will have the same [`PageElement.parent`](#bs4.element.PageElement.parent "bs4.element.PageElement.parent") as
this one, and the given elements will occur immediately before
this one.

Parameters:

**args** -- One or more PageElements.

:return The list of PageElements that were inserted.

known\_xml*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")* *= None*[¶](#bs4.element.PageElement.known_xml "Link to this definition")

In general, we can't tell just by looking at an element whether
it's contained in an XML document or an HTML document. But for
[`Tag`](#bs4.element.Tag "bs4.element.Tag") objects (q.v.) we can store this information at parse time.
:meta private:

*property* next*: \_AtMostOneElement*[¶](#bs4.element.PageElement.next "Link to this definition")

The [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement"), if any, that was parsed just after this one.

next\_element*: \_AtMostOneElement*[¶](#bs4.element.PageElement.next_element "Link to this definition")
*property* next\_elements*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.PageElement.next_elements "Link to this definition")

All PageElements that were parsed after this one.

next\_sibling*: \_AtMostOneElement*[¶](#bs4.element.PageElement.next_sibling "Link to this definition")
*property* next\_siblings*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.PageElement.next_siblings "Link to this definition")

All PageElements that are siblings of this one but were parsed
later.

parent*: [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.PageElement.parent "Link to this definition")
*property* parents*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[Tag](#bs4.element.Tag "bs4.element.Tag")]*[¶](#bs4.element.PageElement.parents "Link to this definition")

All elements that are parents of this PageElement.

Yield:

A sequence of Tags, ending with a BeautifulSoup object.

*property* previous*: \_AtMostOneElement*[¶](#bs4.element.PageElement.previous "Link to this definition")

The [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement"), if any, that was parsed just before this one.

previous\_element*: \_AtMostOneElement*[¶](#bs4.element.PageElement.previous_element "Link to this definition")
*property* previous\_elements*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.PageElement.previous_elements "Link to this definition")

All PageElements that were parsed before this one.

Yield:

A sequence of PageElements.

previous\_sibling*: \_AtMostOneElement*[¶](#bs4.element.PageElement.previous_sibling "Link to this definition")
*property* previous\_siblings*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.PageElement.previous_siblings "Link to this definition")

All PageElements that are siblings of this one but were parsed
earlier.

Yield:

A sequence of PageElements.

replace\_with(*\*args: [PageElement](#bs4.element.PageElement "bs4.element.PageElement")*) → [Self](https://docs.python.org/3/library/typing.html#typing.Self "(in Python v3.13)")[¶](#bs4.element.PageElement.replace_with "Link to this definition")

Replace this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") with one or more other [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement"),
objects, keeping the rest of the tree the same.

Returns:

This [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement"), no longer part of the tree.

*property* self\_and\_next\_elements*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.PageElement.self_and_next_elements "Link to this definition")

This PageElement, then all PageElements that were parsed after it.

*property* self\_and\_next\_siblings*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.PageElement.self_and_next_siblings "Link to this definition")

This PageElement, then all of its siblings.

*property* self\_and\_parents*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.PageElement.self_and_parents "Link to this definition")

This element, then all of its parents.

Yield:

A sequence of PageElements, ending with a BeautifulSoup object.

*property* self\_and\_previous\_elements*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.PageElement.self_and_previous_elements "Link to this definition")

This PageElement, then all elements that were parsed
earlier.

*property* self\_and\_previous\_siblings*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.PageElement.self_and_previous_siblings "Link to this definition")

This PageElement, then all of its siblings that were parsed
earlier.

setup(*parent: [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *previous\_element: \_AtMostOneElement = None*, *next\_element: \_AtMostOneElement = None*, *previous\_sibling: \_AtMostOneElement = None*, *next\_sibling: \_AtMostOneElement = None*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.element.PageElement.setup "Link to this definition")

Sets up the initial relations between this element and
other elements.

Parameters:

* **parent** -- The parent of this element.
* **previous\_element** -- The element parsed immediately before
  this one.
* **next\_element** -- The element parsed immediately before
  this one.
* **previous\_sibling** -- The most recently encountered element
  on the same level of the parse tree as this one.
* **previous\_sibling** -- The next element to be encountered
  on the same level of the parse tree as this one.

*property* stripped\_strings*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.element.PageElement.stripped_strings "Link to this definition")

Yield all interesting strings in this PageElement, stripping them
first.

See [`Tag`](#bs4.element.Tag "bs4.element.Tag") for information on which strings are considered
interesting in a given context.

*property* text*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*[¶](#bs4.element.PageElement.text "Link to this definition")

Get all child strings of this PageElement, concatenated using the
given separator.

Parameters:

* **separator** -- Strings will be concatenated using this separator.
* **strip** -- If True, strings will be stripped before being
  concatenated.
* **types** -- A tuple of NavigableString subclasses. Any
  strings of a subclass not found in this list will be
  ignored. Although there are exceptions, the default
  behavior in most cases is to consider only NavigableString
  and CData objects. That means no comments, processing
  instructions, etc.

Returns:

A string.

wrap(*wrap\_inside: [Tag](#bs4.element.Tag "bs4.element.Tag")*) → [Tag](#bs4.element.Tag "bs4.element.Tag")[¶](#bs4.element.PageElement.wrap "Link to this definition")

Wrap this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") inside a [`Tag`](#bs4.element.Tag "bs4.element.Tag").

Returns:

`wrap_inside`, occupying the position in the tree that used
to be occupied by this object, and with this object now inside it.

*class* bs4.element.PreformattedString(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.PreformattedString "Link to this definition")

Bases: [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString")

A [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") not subject to the normal formatting rules.

This is an abstract class used for special kinds of strings such
as comments ([`Comment`](#bs4.element.Comment "bs4.element.Comment")) and CDATA blocks ([`CData`](#bs4.element.CData "bs4.element.CData")).

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= ''*[¶](#bs4.element.PreformattedString.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= ''*[¶](#bs4.element.PreformattedString.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

output\_ready(*formatter: \_FormatterOrName | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.element.PreformattedString.output_ready "Link to this definition")
Make this string ready for output by adding any subclass-specific

prefix or suffix.

Parameters:

**formatter** -- A [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string naming one
of the standard formatters. The string will be passed into the
[`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter"), but only to trigger any side effects: the return
value is ignored.

Returns:

The string, with any subclass-specific prefix and
suffix added on.

*class* bs4.element.ProcessingInstruction(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.ProcessingInstruction "Link to this definition")

Bases: [`PreformattedString`](#bs4.element.PreformattedString "bs4.element.PreformattedString")

A SGML processing instruction.

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<?'*[¶](#bs4.element.ProcessingInstruction.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '>'*[¶](#bs4.element.ProcessingInstruction.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

next\_element*: \_AtMostOneElement*[¶](#bs4.element.ProcessingInstruction.next_element "Link to this definition")
next\_sibling*: \_AtMostOneElement*[¶](#bs4.element.ProcessingInstruction.next_sibling "Link to this definition")
parent*: [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.ProcessingInstruction.parent "Link to this definition")
previous\_element*: \_AtMostOneElement*[¶](#bs4.element.ProcessingInstruction.previous_element "Link to this definition")
previous\_sibling*: \_AtMostOneElement*[¶](#bs4.element.ProcessingInstruction.previous_sibling "Link to this definition")
*class* bs4.element.ResultSet(*source: [ElementFilter](../index.html#ElementFilter "ElementFilter") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*, *result: Iterable[\_PageElementT] = ()*)[¶](#bs4.element.ResultSet "Link to this definition")

Bases: [`List`](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[`_PageElementT`], [`Generic`](https://docs.python.org/3/library/typing.html#typing.Generic "(in Python v3.13)")[`_PageElementT`]

A ResultSet is a list of [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects, gathered as the result
of matching an [`ElementFilter`](../index.html#ElementFilter "ElementFilter") against a parse tree. Basically, a list of
search results.

source*: [ElementFilter](../index.html#ElementFilter "ElementFilter") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.ResultSet.source "Link to this definition")
*class* bs4.element.RubyParenthesisString(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.RubyParenthesisString "Link to this definition")

Bases: [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString")

A NavigableString representing the contents of an [<rp> HTML
tag](https://dev.w3.org/html5/spec-LC/text-level-semantics.html#the-rp-element).

*class* bs4.element.RubyTextString(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.RubyTextString "Link to this definition")

Bases: [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString")

A NavigableString representing the contents of an [<rt> HTML
tag](https://dev.w3.org/html5/spec-LC/text-level-semantics.html#the-rt-element).

Can be used to distinguish such strings from the strings they're
annotating.

*class* bs4.element.Script(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.Script "Link to this definition")

Bases: [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString")

A [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") representing the contents of a [<script>
HTML tag](https://dev.w3.org/html5/spec-LC/Overview.html#the-script-element)
(probably Javascript).

Used to distinguish executable code from textual content.

*class* bs4.element.Stylesheet(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.Stylesheet "Link to this definition")

Bases: [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString")

A [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") representing the contents of a [<style> HTML
tag](https://dev.w3.org/html5/spec-LC/Overview.html#the-style-element)
(probably CSS).

Used to distinguish embedded stylesheets from textual content.

*class* bs4.element.Tag(*parser: [BeautifulSoup](#bs4.BeautifulSoup "bs4.BeautifulSoup") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *builder: [TreeBuilder](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *namespace: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *prefix: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *attrs: \_RawOrProcessedAttributeValues | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *parent: [BeautifulSoup](#bs4.BeautifulSoup "bs4.BeautifulSoup") | [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *previous: \_AtMostOneElement = None*, *is\_xml: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *sourceline: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *sourcepos: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *can\_be\_empty\_element: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *cdata\_list\_attributes: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *preserve\_whitespace\_tags: Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *interesting\_string\_types: Set[Type[[NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *namespaces: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.element.Tag "Link to this definition")

Bases: [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement")

An HTML or XML tag that is part of a parse tree, along with its
attributes, contents, and relationships to other parts of the tree.

When Beautiful Soup parses the markup `<b>penguin</b>`, it will
create a [`Tag`](#bs4.element.Tag "bs4.element.Tag") object representing the `<b>` tag. You can
instantiate [`Tag`](#bs4.element.Tag "bs4.element.Tag") objects directly, but it's not necessary unless
you're adding entirely new markup to a parsed document. Most of
the constructor arguments are intended for use by the [`TreeBuilder`](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder")
that's parsing a document.

Parameters:

* **parser** -- A [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") object representing the parse tree this
  [`Tag`](#bs4.element.Tag "bs4.element.Tag") will be part of.
* **builder** -- The [`TreeBuilder`](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") being used to build the tree.
* **name** -- The name of the tag.
* **namespace** -- The URI of this tag's XML namespace, if any.
* **prefix** -- The prefix for this tag's XML namespace, if any.
* **attrs** -- A dictionary of attribute values.
* **parent** -- The [`Tag`](#bs4.element.Tag "bs4.element.Tag") to use as the parent of this [`Tag`](#bs4.element.Tag "bs4.element.Tag"). May be
  the [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") object itself.
* **previous** -- The [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") that was parsed immediately before
  parsing this tag.
* **is\_xml** -- If True, this is an XML tag. Otherwise, this is an
  HTML tag.
* **sourceline** -- The line number where this tag was found in its
  source document.
* **sourcepos** -- The character position within `sourceline` where this
  tag was found.
* **can\_be\_empty\_element** -- If True, this tag should be
  represented as <tag/>. If False, this tag should be represented
  as <tag></tag>.
* **cdata\_list\_attributes** -- A dictionary of attributes whose values should
  be parsed as lists of strings if they ever show up on this tag.
* **preserve\_whitespace\_tags** -- Names of tags whose contents
  should have their whitespace preserved if they are encountered inside
  this tag.
* **interesting\_string\_types** -- When iterating over this tag's
  string contents in methods like [`Tag.strings`](#bs4.element.Tag.strings "bs4.element.Tag.strings") or
  [`PageElement.get_text`](#bs4.element.PageElement.get_text "bs4.element.PageElement.get_text"), these are the types of strings that are
  interesting enough to be considered. By default,
  [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") (normal strings) and [`CData`](#bs4.element.CData "bs4.element.CData") (CDATA
  sections) are the only interesting string subtypes.
* **namespaces** -- A dictionary mapping currently active
  namespace prefixes to URIs, as of the point in the parsing process when
  this tag was encountered. This can be used later to
  construct CSS selectors.

append(*tag: \_InsertableElement*) → [PageElement](#bs4.element.PageElement "bs4.element.PageElement")[¶](#bs4.element.Tag.append "Link to this definition")

Appends the given [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") to the contents of this [`Tag`](#bs4.element.Tag "bs4.element.Tag").

Parameters:

**tag** -- A PageElement.

:return The newly appended PageElement.

attrs*: \_AttributeValues*[¶](#bs4.element.Tag.attrs "Link to this definition")
can\_be\_empty\_element*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.can_be_empty_element "Link to this definition")
cdata\_list\_attributes*: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.cdata_list_attributes "Link to this definition")
*property* children*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.Tag.children "Link to this definition")

Iterate over all direct children of this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement").

clear(*decompose: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.element.Tag.clear "Link to this definition")
Destroy all children of this [`Tag`](#bs4.element.Tag "bs4.element.Tag") by calling

[`PageElement.extract`](#bs4.element.PageElement.extract "bs4.element.PageElement.extract") on them.

Parameters:

**decompose** -- If this is True, [`PageElement.decompose`](#bs4.element.PageElement.decompose "bs4.element.PageElement.decompose") (a
more destructive method) will be called instead of
[`PageElement.extract`](#bs4.element.PageElement.extract "bs4.element.PageElement.extract").

contents*: List[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.Tag.contents "Link to this definition")
copy\_self() → [Self](https://docs.python.org/3/library/typing.html#typing.Self "(in Python v3.13)")[¶](#bs4.element.Tag.copy_self "Link to this definition")

Create a new Tag just like this one, but with no
contents and unattached to any parse tree.

This is the first step in the deepcopy process, but you can
call it on its own to create a copy of a Tag without copying its
contents.

*property* css*: [CSS](#bs4.css.CSS "bs4.css.CSS")*[¶](#bs4.element.Tag.css "Link to this definition")

Return an interface to the CSS selector API.

decode(*indent\_level: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *eventual\_encoding: \_Encoding = 'utf-8'*, *formatter: \_FormatterOrName = 'minimal'*, *iterator: Iterator[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.element.Tag.decode "Link to this definition")

Render this [`Tag`](#bs4.element.Tag "bs4.element.Tag") and its contents as a Unicode string.

Parameters:

* **indent\_level** -- Each line of the rendering will be
  indented this many levels. (The `formatter` decides what a
  'level' means, in terms of spaces or other characters
  output.) This is used internally in recursive calls while
  pretty-printing.
* **encoding** -- The encoding you intend to use when
  converting the string to a bytestring. decode() is *not*
  responsible for performing that encoding. This information
  is needed so that a real encoding can be substituted in if
  the document contains an encoding declaration (e.g. in a
  <meta> tag).
* **formatter** -- Either a [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string
  naming one of the standard formatters.
* **iterator** -- The iterator to use when navigating over the
  parse tree. This is only used by [`Tag.decode_contents`](#bs4.element.Tag.decode_contents "bs4.element.Tag.decode_contents") and
  you probably won't need to use it.

decode\_contents(*indent\_level: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *eventual\_encoding: \_Encoding = 'utf-8'*, *formatter: \_FormatterOrName = 'minimal'*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.element.Tag.decode_contents "Link to this definition")

Renders the contents of this tag as a Unicode string.

Parameters:

* **indent\_level** -- Each line of the rendering will be
  indented this many levels. (The formatter decides what a
  'level' means in terms of spaces or other characters
  output.) Used internally in recursive calls while
  pretty-printing.
* **eventual\_encoding** -- The tag is destined to be
  encoded into this encoding. decode\_contents() is *not*
  responsible for performing that encoding. This information
  is needed so that a real encoding can be substituted in if
  the document contains an encoding declaration (e.g. in a
  <meta> tag).
* **formatter** -- A [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string naming one of
  the standard Formatters.

*property* descendants*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.Tag.descendants "Link to this definition")

Iterate over all children of this [`Tag`](#bs4.element.Tag "bs4.element.Tag") in a
breadth-first sequence.

encode(*encoding: \_Encoding = 'utf-8'*, *indent\_level: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *formatter: \_FormatterOrName = 'minimal'*, *errors: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 'xmlcharrefreplace'*) → [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")[¶](#bs4.element.Tag.encode "Link to this definition")

Render this [`Tag`](#bs4.element.Tag "bs4.element.Tag") and its contents as a bytestring.

Parameters:

* **encoding** -- The encoding to use when converting to
  a bytestring. This may also affect the text of the document,
  specifically any encoding declarations within the document.
* **indent\_level** -- Each line of the rendering will be
  indented this many levels. (The `formatter` decides what a
  'level' means, in terms of spaces or other characters
  output.) This is used internally in recursive calls while
  pretty-printing.
* **formatter** -- Either a [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string naming one of
  the standard formatters.
* **errors** --
  
  An error handling strategy such as
  'xmlcharrefreplace'. This value is passed along into
  [`str.encode()`](https://docs.python.org/3/library/stdtypes.html#str.encode "(in Python v3.13)") and its value should be one of the [error
  handling constants defined by Python's codecs module](https://docs.python.org/3/library/codecs.html#error-handlers).

encode\_contents(*indent\_level: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *encoding: \_Encoding = 'utf-8'*, *formatter: \_FormatterOrName = 'minimal'*) → [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")[¶](#bs4.element.Tag.encode_contents "Link to this definition")

Renders the contents of this PageElement as a bytestring.

Parameters:

* **indent\_level** -- Each line of the rendering will be
  indented this many levels. (The `formatter` decides what a
  'level' means, in terms of spaces or other characters
  output.) This is used internally in recursive calls while
  pretty-printing.
* **formatter** -- Either a [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter") object, or a string naming one of
  the standard formatters.
* **encoding** -- The bytestring will be in this encoding.

extend(*tags: Iterable[\_InsertableElement] | [Tag](#bs4.element.Tag "bs4.element.Tag")*) → List[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")][¶](#bs4.element.Tag.extend "Link to this definition")

Appends one or more objects to the contents of this
[`Tag`](#bs4.element.Tag "bs4.element.Tag").

Parameters:

**tags** -- If a list of [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects is provided,
they will be appended to this tag's contents, one at a time.
If a single [`Tag`](#bs4.element.Tag "bs4.element.Tag") is provided, its [`Tag.contents`](#bs4.element.Tag.contents "bs4.element.Tag.contents") will be
used to extend this object's [`Tag.contents`](#bs4.element.Tag.contents "bs4.element.Tag.contents").

:return The list of PageElements that were appended.

find(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *recursive: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = True*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: \_StrainableAttribute*) → \_AtMostOneElement[¶](#bs4.element.Tag.find "Link to this definition")

Look in the children of this PageElement and find the first
PageElement that matches the given criteria.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **recursive** -- If this is True, find() will perform a
  recursive search of this Tag's children. Otherwise,
  only the direct children will be considered.
* **string** -- A filter on the [`Tag.string`](#bs4.element.Tag.string "bs4.element.Tag.string") attribute.
* **limit** -- Stop looking after finding this many results.

Kwargs:

Additional filters on attribute values.

find\_all(*name: \_FindMethodName = None*, *attrs: \_StrainableAttributes = {}*, *recursive: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = True*, *string: \_StrainableString | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\_stacklevel: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 2*, *\*\*kwargs: \_StrainableAttribute*) → \_QueryResults[¶](#bs4.element.Tag.find_all "Link to this definition")

Look in the children of this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") and find all
[`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects that match the given criteria.

All find\_\* methods take a common set of arguments. See the online
documentation for detailed explanations.

Parameters:

* **name** -- A filter on tag name.
* **attrs** -- Additional filters on attribute values.
* **recursive** -- If this is True, find\_all() will perform a
  recursive search of this PageElement's children. Otherwise,
  only the direct children will be considered.
* **limit** -- Stop looking after finding this many results.
* **\_stacklevel** -- Used internally to improve warning messages.

Kwargs:

Additional filters on attribute values.

get(*key: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *default: \_AttributeValue | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → \_AttributeValue | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.element.Tag.get "Link to this definition")

Returns the value of the 'key' attribute for the tag, or
the value given for 'default' if it doesn't have that
attribute.

Parameters:

* **key** -- The attribute to look for.
* **default** -- Use this value if the attribute is not present
  on this [`Tag`](#bs4.element.Tag "bs4.element.Tag").

get\_attribute\_list(*key: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *default: [AttributeValueList](#bs4.element.AttributeValueList "bs4.element.AttributeValueList") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → [AttributeValueList](#bs4.element.AttributeValueList "bs4.element.AttributeValueList")[¶](#bs4.element.Tag.get_attribute_list "Link to this definition")

The same as get(), but always returns a (possibly empty) list.

Parameters:

* **key** -- The attribute to look for.
* **default** -- Use this value if the attribute is not present
  on this [`Tag`](#bs4.element.Tag "bs4.element.Tag").

Returns:

A list of strings, usually empty or containing only a single
value.

has\_attr(*key: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.element.Tag.has_attr "Link to this definition")

Does this [`Tag`](#bs4.element.Tag "bs4.element.Tag") have an attribute with the given name?

index(*element: [PageElement](#bs4.element.PageElement "bs4.element.PageElement")*) → [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)")[¶](#bs4.element.Tag.index "Link to this definition")

Find the index of a child of this [`Tag`](#bs4.element.Tag "bs4.element.Tag") (by identity, not value).

Doing this by identity avoids issues when a [`Tag`](#bs4.element.Tag "bs4.element.Tag") contains two
children that have string equality.

Parameters:

**element** -- Look for this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") in this object's contents.

insert(*position: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)")*, *\*new\_children: \_InsertableElement*) → List[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")][¶](#bs4.element.Tag.insert "Link to this definition")

Insert one or more new PageElements as a child of this [`Tag`](#bs4.element.Tag "bs4.element.Tag").

This works similarly to `list.insert()`, except you can insert
multiple elements at once.

Parameters:

* **position** -- The numeric position that should be occupied
  in this Tag's [`Tag.children`](#bs4.element.Tag.children "bs4.element.Tag.children") by the first new [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement").
* **new\_children** -- The PageElements to insert.

:return The newly inserted PageElements.

interesting\_string\_types*: Set[Type[[NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.interesting_string_types "Link to this definition")
isSelfClosing() → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.element.Tag.isSelfClosing "Link to this definition")

: :meta private:

*property* is\_empty\_element*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.element.Tag.is_empty_element "Link to this definition")

Is this tag an empty-element tag? (aka a self-closing tag)

A tag that has contents is never an empty-element tag.

A tag that has no contents may or may not be an empty-element
tag. It depends on the [`TreeBuilder`](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") used to create the
tag. If the builder has a designated list of empty-element
tags, then only a tag whose name shows up in that list is
considered an empty-element tag. This is usually the case
for HTML documents.

If the builder has no designated list of empty-element, then
any tag with no contents is an empty-element tag. This is usually
the case for XML documents.

name*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*[¶](#bs4.element.Tag.name "Link to this definition")
namespace*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.namespace "Link to this definition")
next\_element*: \_AtMostOneElement*[¶](#bs4.element.Tag.next_element "Link to this definition")
next\_sibling*: \_AtMostOneElement*[¶](#bs4.element.Tag.next_sibling "Link to this definition")
parent*: [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.parent "Link to this definition")
parser\_class*: [type](https://docs.python.org/3/library/functions.html#type "(in Python v3.13)")[[BeautifulSoup](#bs4.BeautifulSoup "bs4.BeautifulSoup")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.parser_class "Link to this definition")
prefix*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.prefix "Link to this definition")
preserve\_whitespace\_tags*: Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.preserve_whitespace_tags "Link to this definition")
prettify(*encoding: \_Encoding | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *formatter: \_FormatterOrName = 'minimal'*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")[¶](#bs4.element.Tag.prettify "Link to this definition")

Pretty-print this [`Tag`](#bs4.element.Tag "bs4.element.Tag") as a string or bytestring.

Parameters:

* **encoding** -- The encoding of the bytestring, or None if you want Unicode.
* **formatter** -- A Formatter object, or a string naming one of
  the standard formatters.

Returns:

A string (if no `encoding` is provided) or a bytestring
(otherwise).

previous\_element*: \_AtMostOneElement*[¶](#bs4.element.Tag.previous_element "Link to this definition")
previous\_sibling*: \_AtMostOneElement*[¶](#bs4.element.Tag.previous_sibling "Link to this definition")
replaceWithChildren() → \_OneElement[¶](#bs4.element.Tag.replaceWithChildren "Link to this definition")

: :meta private:

replace\_with\_children() → [Self](https://docs.python.org/3/library/typing.html#typing.Self "(in Python v3.13)")[¶](#bs4.element.Tag.replace_with_children "Link to this definition")

Replace this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") with its contents.

Returns:

This object, no longer part of the tree.

select(*selector: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 0*, *\*\*kwargs: [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")*) → [ResultSet](#bs4.element.ResultSet "bs4.element.ResultSet")[[Tag](#bs4.element.Tag "bs4.element.Tag")][¶](#bs4.element.Tag.select "Link to this definition")

Perform a CSS selection operation on the current element.

This uses the SoupSieve library.

Parameters:

* **selector** -- A string containing a CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will use the prefixes it encountered while
  parsing the document.
* **limit** -- After finding this number of results, stop looking.
* **kwargs** -- Keyword arguments to be passed into SoupSieve's
  soupsieve.select() method.

select\_one(*selector: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *namespaces: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")*) → [Tag](#bs4.element.Tag "bs4.element.Tag") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.element.Tag.select_one "Link to this definition")

Perform a CSS selection operation on the current element.

Parameters:

* **selector** -- A CSS selector.
* **namespaces** -- A dictionary mapping namespace prefixes
  used in the CSS selector to namespace URIs. By default,
  Beautiful Soup will use the prefixes it encountered while
  parsing the document.
* **kwargs** -- Keyword arguments to be passed into Soup Sieve's
  soupsieve.select() method.

*property* self\_and\_descendants*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*[¶](#bs4.element.Tag.self_and_descendants "Link to this definition")

Iterate over this [`Tag`](#bs4.element.Tag "bs4.element.Tag") and its children in a
breadth-first sequence.

smooth() → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.element.Tag.smooth "Link to this definition")

Smooth out the children of this [`Tag`](#bs4.element.Tag "bs4.element.Tag") by consolidating consecutive
strings.

If you perform a lot of operations that modify the tree,
calling this method afterwards can make pretty-printed output
look more natural.

sourceline*: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.sourceline "Link to this definition")
sourcepos*: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.sourcepos "Link to this definition")
*property* string*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.element.Tag.string "Link to this definition")

Convenience property to get the single string within this
[`Tag`](#bs4.element.Tag "bs4.element.Tag"), assuming there is just one.

Returns:

If this [`Tag`](#bs4.element.Tag "bs4.element.Tag") has a single child that's a
[`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString"), the return value is that string. If this
element has one child [`Tag`](#bs4.element.Tag "bs4.element.Tag"), the return value is that child's
[`Tag.string`](#bs4.element.Tag.string "bs4.element.Tag.string"), recursively. If this [`Tag`](#bs4.element.Tag "bs4.element.Tag") has no children,
or has more than one child, the return value is `None`.

If this property is unexpectedly returning `None` for you,
it's probably because your [`Tag`](#bs4.element.Tag "bs4.element.Tag") has more than one thing
inside it.

*property* strings*: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]*[¶](#bs4.element.Tag.strings "Link to this definition")

Yield all strings of certain classes, possibly stripping them.

Parameters:

* **strip** -- If True, all strings will be stripped before being
  yielded.
* **types** -- A tuple of NavigableString subclasses. Any strings of
  a subclass not found in this list will be ignored. By
  default, the subclasses considered are the ones found in
  self.interesting\_string\_types. If that's not specified,
  only NavigableString and CData objects will be
  considered. That means no comments, processing
  instructions, etc.

unwrap() → [Self](https://docs.python.org/3/library/typing.html#typing.Self "(in Python v3.13)")[¶](#bs4.element.Tag.unwrap "Link to this definition")

Replace this [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") with its contents.

Returns:

This object, no longer part of the tree.

*class* bs4.element.TemplateString(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.TemplateString "Link to this definition")

Bases: [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString")

A [`NavigableString`](#bs4.element.NavigableString "bs4.element.NavigableString") representing a string found inside an [HTML
<template> tag](https://html.spec.whatwg.org/multipage/scripting.html#the-template-element)
embedded in a larger document.

Used to distinguish such strings from the main body of the document.

*class* bs4.element.XMLAttributeDict[¶](#bs4.element.XMLAttributeDict "Link to this definition")

Bases: [`AttributeDict`](#bs4.element.AttributeDict "bs4.element.AttributeDict")

A dictionary for holding a Tag's attributes, which processes
incoming values for consistency with the HTML spec.

*class* bs4.element.XMLProcessingInstruction(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")*)[¶](#bs4.element.XMLProcessingInstruction "Link to this definition")

Bases: [`ProcessingInstruction`](#bs4.element.ProcessingInstruction "bs4.element.ProcessingInstruction")

An [XML processing instruction](https://www.w3.org/TR/REC-xml/#sec-pi).

PREFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '<?'*[¶](#bs4.element.XMLProcessingInstruction.PREFIX "Link to this definition")

A string prepended to the body of the 'real' string
when formatting it as part of a document, such as the '<!--'
in an HTML comment.

SUFFIX*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= '?>'*[¶](#bs4.element.XMLProcessingInstruction.SUFFIX "Link to this definition")

A string appended to the body of the 'real' string
when formatting it as part of a document, such as the '-->'
in an HTML comment.

bs4.element.nonwhitespace\_re*: Pattern[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]* *= re.compile('\\S+')*[¶](#bs4.element.nonwhitespace_re "Link to this definition")

A regular expression that can be used to split on whitespace.


## bs4.filter module[¶](#module-bs4.filter "Link to this heading")

*class* bs4.filter.AttributeValueMatchRule(*string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *pattern: [\_RegularExpressionProtocol](#bs4._typing._RegularExpressionProtocol "bs4._typing._RegularExpressionProtocol") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *function: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *present: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *exclude\_everything: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.filter.AttributeValueMatchRule "Link to this definition")

Bases: [`MatchRule`](#bs4.filter.MatchRule "bs4.filter.MatchRule")

A MatchRule implementing the rules for matches against attribute value.

function*: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.filter.AttributeValueMatchRule.function "Link to this definition")
*class* bs4.filter.ElementFilter(*match\_function: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.filter.ElementFilter "Link to this definition")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")

[`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") encapsulates the logic necessary to decide:

1. whether a [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") (a [`Tag`](../index.html#Tag "Tag") or a [`NavigableString`](../index.html#NavigableString "NavigableString")) matches a
user-specified query.

2. whether a given sequence of markup found during initial parsing
should be turned into a [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") at all, or simply discarded.

The base class is the simplest [`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter"). By default, it
matches everything and allows all markup to become [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement")
objects. You can make it more selective by passing in a
user-defined match function, or defining a subclass.

Most users of Beautiful Soup will never need to use
[`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter"), or its more capable subclass
[`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer"). Instead, they will use methods like
`Tag.find()`, which will convert their arguments into
[`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") objects and run them against the tree.

However, if you find yourself wanting to treat the arguments to
Beautiful Soup's find\_\*() methods as first-class objects, those
objects will be [`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") objects. You can create them
yourself and then make use of functions like
[`ElementFilter.filter()`](#bs4.filter.ElementFilter.filter "bs4.filter.ElementFilter.filter").

allow\_string\_creation(*string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.ElementFilter.allow_string_creation "Link to this definition")

Based on the content of a string, see whether this
[`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") will allow a [`NavigableString`](../index.html#NavigableString "NavigableString") object based on
this string to be added to the parse tree.

By default, all strings are processed into [`NavigableString`](../index.html#NavigableString "NavigableString")
objects. To change this, subclass [`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter").

Parameters:

**str** -- The string under consideration.

allow\_tag\_creation(*nsprefix: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*, *name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *attrs: \_RawAttributeValues | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.ElementFilter.allow_tag_creation "Link to this definition")

Based on the name and attributes of a tag, see whether this
[`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") will allow a [`Tag`](../index.html#Tag "Tag") object to even be created.

By default, all tags are parsed. To change this, subclass
[`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter").

Parameters:

* **name** -- The name of the prospective tag.
* **attrs** -- The attributes of the prospective tag.

*property* excludes\_everything*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.filter.ElementFilter.excludes_everything "Link to this definition")

Does this [`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") obviously exclude everything? If
so, Beautiful Soup will issue a warning if you try to use it
when parsing a document.

The [`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") might turn out to exclude everything even
if this returns [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.13)"), but it won't exclude everything in an
obvious way.

The base [`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") implementation excludes things based
on a match function we can't inspect, so excludes\_everything
is always false.

filter(*generator: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*) → [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement") | [Tag](#bs4.element.Tag "bs4.element.Tag") | [NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")][¶](#bs4.filter.ElementFilter.filter "Link to this definition")

The most generic search method offered by Beautiful Soup.

Acts like Python's built-in [`filter`](#bs4.filter.ElementFilter.filter "bs4.filter.ElementFilter.filter"), using
[`ElementFilter.match`](#bs4.filter.ElementFilter.match "bs4.filter.ElementFilter.match") as the filtering function.

find(*generator: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*) → [PageElement](#bs4.element.PageElement "bs4.element.PageElement") | [Tag](#bs4.element.Tag "bs4.element.Tag") | [NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.filter.ElementFilter.find "Link to this definition")

A lower-level equivalent of `Tag.find()`.

You can pass in your own generator for iterating over
[`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects. The first one that matches this
[`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") will be returned.

Parameters:

**generator** -- A way of iterating over [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement")
objects.

find\_all(*generator: [Iterator](https://docs.python.org/3/library/typing.html#typing.Iterator "(in Python v3.13)")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")]*, *limit: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*) → [ResultSet](#bs4.element.ResultSet "bs4.element.ResultSet")[[PageElement](#bs4.element.PageElement "bs4.element.PageElement") | [Tag](#bs4.element.Tag "bs4.element.Tag") | [NavigableString](#bs4.element.NavigableString "bs4.element.NavigableString")][¶](#bs4.filter.ElementFilter.find_all "Link to this definition")

A lower-level equivalent of `Tag.find_all()`.

You can pass in your own generator for iterating over
[`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") objects. Only elements that match this
[`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") will be returned in the `ResultSet`.

Parameters:

* **generator** -- A way of iterating over [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement")
  objects.
* **limit** -- Stop looking after finding this many results.

*property* includes\_everything*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.filter.ElementFilter.includes_everything "Link to this definition")

Does this [`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") obviously include everything? If so,
the filter process can be made much faster.

The [`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") might turn out to include everything even
if this returns [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.13)"), but it won't include everything in an
obvious way.

The base [`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") implementation includes things based on
the match function, so includes\_everything is only true if
there is no match function.

match(*element: [PageElement](#bs4.element.PageElement "bs4.element.PageElement")*, *\_known\_rules: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.ElementFilter.match "Link to this definition")

Does the given PageElement match the rules set down by this
ElementFilter?

The base implementation delegates to the function passed in to
the constructor.

Parameters:

**\_known\_rules** -- Defined for compatibility with

SoupStrainer.\_match(). Used more for consistency than because
we need the performance optimization.

match\_function*: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[PageElement](#bs4.element.PageElement "bs4.element.PageElement")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.filter.ElementFilter.match_function "Link to this definition")
*class* bs4.filter.MatchRule(*string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *pattern: [\_RegularExpressionProtocol](#bs4._typing._RegularExpressionProtocol "bs4._typing._RegularExpressionProtocol") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *function: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *present: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *exclude\_everything: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.filter.MatchRule "Link to this definition")

Bases: [`object`](https://docs.python.org/3/library/functions.html#object "(in Python v3.13)")

Each MatchRule encapsulates the logic behind a single argument
passed in to one of the Beautiful Soup find\* methods.

exclude\_everything*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.filter.MatchRule.exclude_everything "Link to this definition")
matches\_string(*string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.MatchRule.matches_string "Link to this definition")
pattern*: [\_RegularExpressionProtocol](#bs4._typing._RegularExpressionProtocol "bs4._typing._RegularExpressionProtocol") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.filter.MatchRule.pattern "Link to this definition")
present*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.filter.MatchRule.present "Link to this definition")
string*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.filter.MatchRule.string "Link to this definition")
*class* bs4.filter.SoupStrainer(*name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[Tag](#bs4.element.Tag "bs4.element.Tag")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[Tag](#bs4.element.Tag "bs4.element.Tag")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *attrs: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]]] = {}*, *string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *\*\*kwargs: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [Iterable](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [Pattern](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]]*)[¶](#bs4.filter.SoupStrainer "Link to this definition")

Bases: [`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter")

The [`ElementFilter`](#bs4.filter.ElementFilter "bs4.filter.ElementFilter") subclass used internally by Beautiful Soup.

A [`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") encapsulates the logic necessary to perform the
kind of matches supported by methods such as
`Tag.find()`. [`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") objects are primarily created
internally, but you can create one yourself and pass it in as
`parse_only` to the [`BeautifulSoup`](#bs4.BeautifulSoup "bs4.BeautifulSoup") constructor, to parse a
subset of a large document.

Internally, [`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") objects work by converting the
constructor arguments into [`MatchRule`](#bs4.filter.MatchRule "bs4.filter.MatchRule") objects. Incoming
tags/markup are matched against those rules.

Parameters:

* **name** -- One or more restrictions on the tags found in a document.
* **attrs** -- A dictionary that maps attribute names to
  restrictions on tags that use those attributes.
* **string** -- One or more restrictions on the strings found in a
  document.
* **kwargs** -- A dictionary that maps attribute names to restrictions
  on tags that use those attributes. These restrictions are additive to
  any specified in `attrs`.

allow\_string\_creation(*string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.SoupStrainer.allow_string_creation "Link to this definition")

Based on the content of a markup string, see whether this
[`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") will allow it to be instantiated as a
[`NavigableString`](../index.html#NavigableString "NavigableString") object, or whether it should be ignored.

allow\_tag\_creation(*nsprefix: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*, *name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *attrs: \_RawAttributeValues | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.SoupStrainer.allow_tag_creation "Link to this definition")

Based on the name and attributes of a tag, see whether this
[`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") will allow a [`Tag`](../index.html#Tag "Tag") object to even be created.

Parameters:

* **name** -- The name of the prospective tag.
* **attrs** -- The attributes of the prospective tag.

attribute\_rules*: [Dict](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [List](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[[AttributeValueMatchRule](#bs4.filter.AttributeValueMatchRule "bs4.filter.AttributeValueMatchRule")]]*[¶](#bs4.filter.SoupStrainer.attribute_rules "Link to this definition")
*property* excludes\_everything*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.filter.SoupStrainer.excludes_everything "Link to this definition")

Check whether the provided rules will obviously exclude
everything. (They might exclude everything even if this returns [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.13)"),
but not in an obvious way.)

*property* includes\_everything*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.filter.SoupStrainer.includes_everything "Link to this definition")

Check whether the provided rules will obviously include
everything. (They might include everything even if this returns [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.13)"),
but not in an obvious way.)

match(*element: [PageElement](#bs4.element.PageElement "bs4.element.PageElement")*, *\_known\_rules: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.SoupStrainer.match "Link to this definition")

Does the given [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") match the rules set down by this
[`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer")?

The find\_\* methods rely heavily on this method to find matches.

Parameters:

* **element** -- A [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement").
* **\_known\_rules** -- Set to true in the common case where
  we already checked and found at least one rule in this SoupStrainer
  that might exclude a PageElement. Without this, we need
  to check .includes\_everything every time, just to be safe.

Returns:

[`True`](https://docs.python.org/3/library/constants.html#True "(in Python v3.13)") if the element matches this [`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer")'s rules; [`False`](https://docs.python.org/3/library/constants.html#False "(in Python v3.13)") otherwise.

matches\_any\_string\_rule(*string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.SoupStrainer.matches_any_string_rule "Link to this definition")

See whether the content of a string matches any of
this [`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer")'s string rules.

matches\_tag(*tag: [Tag](#bs4.element.Tag "bs4.element.Tag")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.SoupStrainer.matches_tag "Link to this definition")

Do the rules of this [`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") trigger a match against the
given [`Tag`](../index.html#Tag "Tag")?

If the [`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") has any [`TagNameMatchRule`](#bs4.filter.TagNameMatchRule "bs4.filter.TagNameMatchRule"), at least one
must match the [`Tag`](../index.html#Tag "Tag") or its [`Tag.name`](../index.html#Tag.name "Tag.name").

If there are any [`AttributeValueMatchRule`](#bs4.filter.AttributeValueMatchRule "bs4.filter.AttributeValueMatchRule") for a given
attribute, at least one of them must match the attribute
value.

If there are any [`StringMatchRule`](#bs4.filter.StringMatchRule "bs4.filter.StringMatchRule"), at least one must match,
but a [`SoupStrainer`](#bs4.filter.SoupStrainer "bs4.filter.SoupStrainer") that *only* contains [`StringMatchRule`](#bs4.filter.StringMatchRule "bs4.filter.StringMatchRule")
cannot match a [`Tag`](../index.html#Tag "Tag"), only a [`NavigableString`](../index.html#NavigableString "NavigableString").

name\_rules*: [List](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[[TagNameMatchRule](#bs4.filter.TagNameMatchRule "bs4.filter.TagNameMatchRule")]*[¶](#bs4.filter.SoupStrainer.name_rules "Link to this definition")
search\_tag(*name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *attrs: \_RawAttributeValues | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.SoupStrainer.search_tag "Link to this definition")

A less elegant version of [`allow_tag_creation`](#bs4.filter.SoupStrainer.allow_tag_creation "bs4.filter.SoupStrainer.allow_tag_creation"). Deprecated as of 4.13.0

string\_rules*: [List](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[[StringMatchRule](#bs4.filter.StringMatchRule "bs4.filter.StringMatchRule")]*[¶](#bs4.filter.SoupStrainer.string_rules "Link to this definition")
*class* bs4.filter.StringMatchRule(*string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *pattern: [\_RegularExpressionProtocol](#bs4._typing._RegularExpressionProtocol "bs4._typing._RegularExpressionProtocol") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *function: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *present: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *exclude\_everything: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.filter.StringMatchRule "Link to this definition")

Bases: [`MatchRule`](#bs4.filter.MatchRule "bs4.filter.MatchRule")

A MatchRule implementing the rules for matches against a NavigableString.

function*: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.filter.StringMatchRule.function "Link to this definition")
*class* bs4.filter.TagNameMatchRule(*string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [bytes](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *pattern: [\_RegularExpressionProtocol](#bs4._typing._RegularExpressionProtocol "bs4._typing._RegularExpressionProtocol") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *function: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *present: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *exclude\_everything: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*)[¶](#bs4.filter.TagNameMatchRule "Link to this definition")

Bases: [`MatchRule`](#bs4.filter.MatchRule "bs4.filter.MatchRule")

A MatchRule implementing the rules for matches against tag name.

function*: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[Tag](#bs4.element.Tag "bs4.element.Tag")], [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")*[¶](#bs4.filter.TagNameMatchRule.function "Link to this definition")
matches\_tag(*tag: [Tag](#bs4.element.Tag "bs4.element.Tag")*) → [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")[¶](#bs4.filter.TagNameMatchRule.matches_tag "Link to this definition")

## bs4.formatter module[¶](#module-bs4.formatter "Link to this heading")

*class* bs4.formatter.Formatter(*language: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *entity\_substitution: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *void\_element\_close\_prefix: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = '/'*, *cdata\_containing\_tags: [Set](https://docs.python.org/3/library/typing.html#typing.Set "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *empty\_attributes\_are\_booleans: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*, *indent: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 1*)[¶](#bs4.formatter.Formatter "Link to this definition")

Bases: [`EntitySubstitution`](#bs4.dammit.EntitySubstitution "bs4.dammit.EntitySubstitution")

Describes a strategy to use when outputting a parse tree to a string.

Some parts of this strategy come from the distinction between
HTML4, HTML5, and XML. Others are configurable by the user.

Formatters are passed in as the [`formatter`](#module-bs4.formatter "bs4.formatter") argument to methods
like [`bs4.element.Tag.encode`](#bs4.element.Tag.encode "bs4.element.Tag.encode"). Most people won't need to
think about formatters, and most people who need to think about
them can pass in one of these predefined strings as [`formatter`](#module-bs4.formatter "bs4.formatter")
rather than making a new Formatter object:

For HTML documents:

* 'html' - HTML entity substitution for generic HTML documents. (default)
* 'html5' - HTML entity substitution for HTML5 documents, as
  
  well as some optimizations in the way tags are rendered.
* 'html5-4.12.0' - The version of the 'html5' formatter used prior to
  
  Beautiful Soup 4.13.0.
* 'minimal' - Only make the substitutions necessary to guarantee
  
  valid HTML.
* None - Do not perform any substitution. This will be faster
  
  but may result in invalid markup.

For XML documents:

* 'html' - Entity substitution for XHTML documents.
* 'minimal' - Only make the substitutions necessary to guarantee
  
  valid XML. (default)
* None - Do not perform any substitution. This will be faster
  
  but may result in invalid markup.

HTML*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= 'html'*[¶](#bs4.formatter.Formatter.HTML "Link to this definition")

Constant name denoting HTML markup

HTML\_DEFAULTS*: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), Set[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]]* *= {'cdata\_containing\_tags': {'script', 'style'}}*[¶](#bs4.formatter.Formatter.HTML_DEFAULTS "Link to this definition")

Default values for the various constructor options when the
markup language is HTML.

XML*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")* *= 'xml'*[¶](#bs4.formatter.Formatter.XML "Link to this definition")

Constant name denoting XML markup

attribute\_value(*value: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.formatter.Formatter.attribute_value "Link to this definition")

Process the value of an attribute.

Parameters:

**ns** -- A string.

Returns:

A string with certain characters replaced by named
or numeric entities.

attributes(*tag: [bs4.element.Tag](#bs4.element.Tag "bs4.element.Tag")*) → Iterable[Tuple[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), \_AttributeValue | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")]][¶](#bs4.formatter.Formatter.attributes "Link to this definition")

Reorder a tag's attributes however you want.

By default, attributes are sorted alphabetically. This makes
behavior consistent between Python 2 and Python 3, and preserves
backwards compatibility with older versions of Beautiful Soup.

If [`empty_attributes_are_booleans`](#bs4.formatter.Formatter.empty_attributes_are_booleans "bs4.formatter.Formatter.empty_attributes_are_booleans") is True, then
attributes whose values are set to the empty string will be
treated as boolean attributes.

empty\_attributes\_are\_booleans*: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")*[¶](#bs4.formatter.Formatter.empty_attributes_are_booleans "Link to this definition")

If this is set to true by the constructor, then attributes whose
values are sent to the empty string will be treated as HTML
boolean attributes. (Attributes whose value is None are always
rendered this way.)

substitute(*ns: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")[¶](#bs4.formatter.Formatter.substitute "Link to this definition")

Process a string that needs to undergo entity substitution.
This may be a string encountered in an attribute value or as
text.

Parameters:

**ns** -- A string.

Returns:

The same string but with certain characters replaced by named
or numeric entities.

*class* bs4.formatter.HTMLFormatter(*entity\_substitution: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *void\_element\_close\_prefix: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = '/'*, *cdata\_containing\_tags: [Set](https://docs.python.org/3/library/typing.html#typing.Set "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *empty\_attributes\_are\_booleans: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*, *indent: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 1*)[¶](#bs4.formatter.HTMLFormatter "Link to this definition")

Bases: [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter")

A generic Formatter for HTML.

REGISTRY*: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)"), [HTMLFormatter](#bs4.formatter.HTMLFormatter "bs4.formatter.HTMLFormatter")]* *= {'html': <bs4.formatter.HTMLFormatter object>, 'html5': <bs4.formatter.HTMLFormatter object>, 'html5-4.12': <bs4.formatter.HTMLFormatter object>, 'minimal': <bs4.formatter.HTMLFormatter object>, None: <bs4.formatter.HTMLFormatter object>}*[¶](#bs4.formatter.HTMLFormatter.REGISTRY "Link to this definition")
*class* bs4.formatter.XMLFormatter(*entity\_substitution: [Callable](https://docs.python.org/3/library/typing.html#typing.Callable "(in Python v3.13)")[[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *void\_element\_close\_prefix: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = '/'*, *cdata\_containing\_tags: [Set](https://docs.python.org/3/library/typing.html#typing.Set "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")] | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)") = None*, *empty\_attributes\_are\_booleans: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = False*, *indent: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") | [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 1*)[¶](#bs4.formatter.XMLFormatter "Link to this definition")

Bases: [`Formatter`](#bs4.formatter.Formatter "bs4.formatter.Formatter")

A generic Formatter for XML.

REGISTRY*: Dict[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)"), [XMLFormatter](#bs4.formatter.XMLFormatter "bs4.formatter.XMLFormatter")]* *= {'html': <bs4.formatter.XMLFormatter object>, 'minimal': <bs4.formatter.XMLFormatter object>, None: <bs4.formatter.XMLFormatter object>}*[¶](#bs4.formatter.XMLFormatter.REGISTRY "Link to this definition")

## bs4.\_typing module[¶](#module-bs4._typing "Link to this heading")

bs4.\_typing.\_AttributeValues[¶](#bs4._typing._AttributeValues "Link to this definition")

A dictionary of names to `_AttributeValue` objects. This is what
a tag's attributes look like after processing.

alias of [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), `AttributeValueList`]]

bs4.\_typing.\_BaseStrainable[¶](#bs4._typing._BaseStrainable "Link to this definition")

Either a tag name, an attribute value or a string can be matched
against a string, bytestring, regular expression, or a boolean.

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]

bs4.\_typing.\_BaseStrainableAttribute[¶](#bs4._typing._BaseStrainableAttribute "Link to this definition")

A tag's attribute vgalue can be matched either with the
[`_BaseStrainable`](#bs4._typing._BaseStrainable "bs4._typing._BaseStrainable") options, or using a function that takes that
value as its sole argument.

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)"), `Callable`[[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]]

bs4.\_typing.\_BaseStrainableElement[¶](#bs4._typing._BaseStrainableElement "Link to this definition")

A tag can be matched either with the [`_BaseStrainable`](#bs4._typing._BaseStrainable "bs4._typing._BaseStrainable") options, or
using a function that takes the [`Tag`](../index.html#Tag "Tag") as its sole argument.

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)"), `Callable`[[[`Tag`](../index.html#Tag "Tag")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]]

bs4.\_typing.\_Encoding[¶](#bs4._typing._Encoding "Link to this definition")

A data encoding.

bs4.\_typing.\_Encodings[¶](#bs4._typing._Encodings "Link to this definition")

One or more data encodings.

alias of [`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]

bs4.\_typing.\_IncomingMarkup[¶](#bs4._typing._IncomingMarkup "Link to this definition")

The rawest form of markup: either a string, bytestring, or an open filehandle.

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`IO`](https://docs.python.org/3/library/typing.html#typing.IO "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`IO`](https://docs.python.org/3/library/typing.html#typing.IO "(in Python v3.13)")[[`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")]]

bs4.\_typing.\_InsertableElement[¶](#bs4._typing._InsertableElement "Link to this definition")

A number of tree manipulation methods can take either a [`PageElement`](#bs4.element.PageElement "bs4.element.PageElement") or a
normal Python string (which will be converted to a [`NavigableString`](../index.html#NavigableString "NavigableString")).

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[`PageElement`, [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]

bs4.\_typing.\_InvertedNamespaceMapping[¶](#bs4._typing._InvertedNamespaceMapping "Link to this definition")

A mapping of namespace URLs to prefixes

alias of [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]

bs4.\_typing.\_NamespaceMapping[¶](#bs4._typing._NamespaceMapping "Link to this definition")

A mapping of prefixes to namespace URLs.

alias of [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")]

bs4.\_typing.\_NamespacePrefix[¶](#bs4._typing._NamespacePrefix "Link to this definition")

The prefix for an XML namespace.

bs4.\_typing.\_NamespaceURL[¶](#bs4._typing._NamespaceURL "Link to this definition")

The URL of an XML namespace

bs4.\_typing.\_OneElement[¶](#bs4._typing._OneElement "Link to this definition")

Many Beautiful soup methods return a PageElement or an ResultSet of
PageElements. A PageElement is either a Tag or a NavigableString.
These convenience aliases make it easier for IDE users to see which methods
are available on the objects they're dealing with.

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[`PageElement`, [`Tag`](../index.html#Tag "Tag"), [`NavigableString`](../index.html#NavigableString "NavigableString")]

bs4.\_typing.\_PageElementMatchFunction[¶](#bs4._typing._PageElementMatchFunction "Link to this definition")

A function that takes a PageElement and returns a yes-or-no answer.

alias of `Callable`[[`PageElement`], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]

bs4.\_typing.\_RawAttributeValue[¶](#bs4._typing._RawAttributeValue "Link to this definition")

The value associated with an HTML or XML attribute. This is the
relatively unprocessed value Beautiful Soup expects to come from a
[`TreeBuilder`](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder").

bs4.\_typing.\_RawAttributeValues*: [TypeAlias](https://docs.python.org/3/library/typing.html#typing.TypeAlias "(in Python v3.13)")* *= 'Mapping[Union[str, NamespacedAttribute], \_RawAttributeValue]'*[¶](#bs4._typing._RawAttributeValues "Link to this definition")

A dictionary of names to [`_RawAttributeValue`](#bs4._typing._RawAttributeValue "bs4._typing._RawAttributeValue") objects. This is how
Beautiful Soup expects a [`TreeBuilder`](bs4.builder.html#bs4.builder.TreeBuilder "bs4.builder.TreeBuilder") to represent a tag's
attribute values.

bs4.\_typing.\_RawMarkup[¶](#bs4._typing._RawMarkup "Link to this definition")

Markup that is in memory but has (potentially) yet to be converted
to Unicode.

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)")]

bs4.\_typing.\_RawOrProcessedAttributeValues[¶](#bs4._typing._RawOrProcessedAttributeValues "Link to this definition")

The methods that deal with turning [`_RawAttributeValue`](#bs4._typing._RawAttributeValue "bs4._typing._RawAttributeValue") into
`_AttributeValue` may be called several times, even after the values
are already processed (e.g. when cloning a tag), so they need to
be able to acommodate both possibilities.

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[`Mapping[Union[str, NamespacedAttribute], _RawAttributeValue]`, [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), `AttributeValueList`]]]

*class* bs4.\_typing.\_RegularExpressionProtocol(*\*args*, *\*\*kwargs*)[¶](#bs4._typing._RegularExpressionProtocol "Link to this definition")

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol "(in Python v3.13)")

A protocol object which can accept either Python's built-in
[`re.Pattern`](https://docs.python.org/3/library/re.html#re.Pattern "(in Python v3.13)") objects, or the similar `Regex` objects defined by the
third-party `regex` package.

\_abc\_impl *= <\_abc.\_abc\_data object>*[¶](#bs4._typing._RegularExpressionProtocol._abc_impl "Link to this definition")
\_is\_protocol *= True*[¶](#bs4._typing._RegularExpressionProtocol._is_protocol "Link to this definition")
\_is\_runtime\_protocol *= True*[¶](#bs4._typing._RegularExpressionProtocol._is_runtime_protocol "Link to this definition")
*property* pattern*: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*[¶](#bs4._typing._RegularExpressionProtocol.pattern "Link to this definition")
search(*string: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *pos: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = Ellipsis*, *endpos: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = Ellipsis*) → [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4._typing._RegularExpressionProtocol.search "Link to this definition")
bs4.\_typing.\_StrainableAttribute[¶](#bs4._typing._StrainableAttribute "Link to this definition")

An attribute value can be matched using either a single criterion
or a list of criteria.

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)"), `Callable`[[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")], [`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)"), `Callable`[[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]]]]

bs4.\_typing.\_StrainableAttributes[¶](#bs4._typing._StrainableAttributes "Link to this definition")

A dictionary may be used to match against multiple attribute vlaues at once.

alias of [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)"), `Callable`[[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")], [`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)"), `Callable`[[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]]]]]

bs4.\_typing.\_StrainableElement[¶](#bs4._typing._StrainableElement "Link to this definition")

A tag can be matched using either a single criterion or a list of
criteria.

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)"), `Callable`[[[`Tag`](../index.html#Tag "Tag")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")], [`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)"), `Callable`[[[`Tag`](../index.html#Tag "Tag")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]]]]

bs4.\_typing.\_StrainableString[¶](#bs4._typing._StrainableString "Link to this definition")

An string can be matched using the same techniques as
an attribute value.

alias of [`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)"), `Callable`[[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")], [`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable "(in Python v3.13)")[[`Union`](https://docs.python.org/3/library/typing.html#typing.Union "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [`bytes`](https://docs.python.org/3/library/stdtypes.html#bytes "(in Python v3.13)"), [`Pattern`](https://docs.python.org/3/library/typing.html#typing.Pattern "(in Python v3.13)")[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)"), `Callable`[[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]]]]

bs4.\_typing.\_StringMatchFunction[¶](#bs4._typing._StringMatchFunction "Link to this definition")

A function that takes a single string and returns a yes-or-no
answer. An [`AttributeValueMatchRule`](#bs4.filter.AttributeValueMatchRule "bs4.filter.AttributeValueMatchRule") expects this kind of function, if
you're going to pass it a function. So does a [`StringMatchRule`](#bs4.filter.StringMatchRule "bs4.filter.StringMatchRule").

alias of `Callable`[[[`str`](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]

bs4.\_typing.\_TagMatchFunction[¶](#bs4._typing._TagMatchFunction "Link to this definition")

A function that takes a [`Tag`](../index.html#Tag "Tag") and returns a yes-or-no answer.
A [`TagNameMatchRule`](#bs4.filter.TagNameMatchRule "bs4.filter.TagNameMatchRule") expects this kind of function, if you're
going to pass it a function.

alias of `Callable`[[[`Tag`](../index.html#Tag "Tag")], [`bool`](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)")]


## bs4.diagnose module[¶](#module-bs4.diagnose "Link to this heading")

Diagnostic functions, mainly for use when doing tech support.

*class* bs4.diagnose.AnnouncingParser(*\**, *convert\_charrefs=True*)[¶](#bs4.diagnose.AnnouncingParser "Link to this definition")

Bases: [`HTMLParser`](https://docs.python.org/3/library/html.parser.html#html.parser.HTMLParser "(in Python v3.13)")

Subclass of HTMLParser that announces parse events, without doing
anything else.

You can use this to get a picture of how html.parser sees a given
document. The easiest way to do this is to call [`htmlparser_trace`](#bs4.diagnose.htmlparser_trace "bs4.diagnose.htmlparser_trace").

handle\_charref(*name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.AnnouncingParser.handle_charref "Link to this definition")
handle\_comment(*data: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.AnnouncingParser.handle_comment "Link to this definition")
handle\_data(*data: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.AnnouncingParser.handle_data "Link to this definition")
handle\_decl(*data: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.AnnouncingParser.handle_decl "Link to this definition")
handle\_endtag(*name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *check\_already\_closed: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = True*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.AnnouncingParser.handle_endtag "Link to this definition")
handle\_entityref(*name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.AnnouncingParser.handle_entityref "Link to this definition")
handle\_pi(*data: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.AnnouncingParser.handle_pi "Link to this definition")
handle\_starttag(*name: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*, *attrs: [List](https://docs.python.org/3/library/typing.html#typing.List "(in Python v3.13)")[[Tuple](https://docs.python.org/3/library/typing.html#typing.Tuple "(in Python v3.13)")[[str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)"), [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") | [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")]]*, *handle\_empty\_element: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = True*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.AnnouncingParser.handle_starttag "Link to this definition")
unknown\_decl(*data: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.AnnouncingParser.unknown_decl "Link to this definition")
bs4.diagnose.benchmark\_parsers(*num\_elements: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 100000*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.benchmark_parsers "Link to this definition")

Very basic head-to-head performance benchmark.

bs4.diagnose.diagnose(*data: \_IncomingMarkup*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.diagnose "Link to this definition")

Diagnostic suite for isolating common problems.

Parameters:

**data** -- Some markup that needs to be explained.

Returns:

None; diagnostics are printed to standard output.

bs4.diagnose.htmlparser\_trace(*data: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)")*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.htmlparser_trace "Link to this definition")

Print out the HTMLParser events that occur during parsing.

This lets you see how HTMLParser parses a document when no
Beautiful Soup code is running.

Parameters:

**data** -- Some markup.

bs4.diagnose.lxml\_trace(*data: \_IncomingMarkup*, *html: [bool](https://docs.python.org/3/library/functions.html#bool "(in Python v3.13)") = True*, *\*\*kwargs: [Any](https://docs.python.org/3/library/typing.html#typing.Any "(in Python v3.13)")*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.lxml_trace "Link to this definition")

Print out the lxml events that occur during parsing.

This lets you see how lxml parses a document when no Beautiful
Soup code is running. You can use this to determine whether
an lxml-specific problem is in Beautiful Soup's lxml tree builders
or in lxml itself.

Parameters:

* **data** -- Some markup.
* **html** -- If True, markup will be parsed with lxml's HTML parser.
  if False, lxml's XML parser will be used.

bs4.diagnose.profile(*num\_elements: [int](https://docs.python.org/3/library/functions.html#int "(in Python v3.13)") = 100000*, *parser: [str](https://docs.python.org/3/library/stdtypes.html#str "(in Python v3.13)") = 'lxml'*) → [None](https://docs.python.org/3/library/constants.html#None "(in Python v3.13)")[¶](#bs4.diagnose.profile "Link to this definition")

Use Python's profiler on a randomly generated document.






### [Table of Contents](../index.html)

* [bs4 package](#)
  + [Module contents](#module-bs4)
    - [`AttributeResemblesVariableWarning`](#bs4.AttributeResemblesVariableWarning)
      * [`AttributeResemblesVariableWarning.MESSAGE`](#bs4.AttributeResemblesVariableWarning.MESSAGE)
    - [`BeautifulSoup`](#bs4.BeautifulSoup)
      * [`BeautifulSoup.ASCII_SPACES`](#bs4.BeautifulSoup.ASCII_SPACES)
      * [`BeautifulSoup.DEFAULT_BUILDER_FEATURES`](#bs4.BeautifulSoup.DEFAULT_BUILDER_FEATURES)
      * [`BeautifulSoup.ROOT_TAG_NAME`](#bs4.BeautifulSoup.ROOT_TAG_NAME)
      * [`BeautifulSoup.contains_replacement_characters`](#bs4.BeautifulSoup.contains_replacement_characters)
      * [`BeautifulSoup.copy_self()`](#bs4.BeautifulSoup.copy_self)
      * [`BeautifulSoup.declared_html_encoding`](#bs4.BeautifulSoup.declared_html_encoding)
      * [`BeautifulSoup.decode()`](#bs4.BeautifulSoup.decode)
      * [`BeautifulSoup.insert_after()`](#bs4.BeautifulSoup.insert_after)
      * [`BeautifulSoup.insert_before()`](#bs4.BeautifulSoup.insert_before)
      * [`BeautifulSoup.is_xml`](#bs4.BeautifulSoup.is_xml)
      * [`BeautifulSoup.new_string()`](#bs4.BeautifulSoup.new_string)
      * [`BeautifulSoup.new_tag()`](#bs4.BeautifulSoup.new_tag)
      * [`BeautifulSoup.original_encoding`](#bs4.BeautifulSoup.original_encoding)
      * [`BeautifulSoup.reset()`](#bs4.BeautifulSoup.reset)
      * [`BeautifulSoup.string_container()`](#bs4.BeautifulSoup.string_container)
    - [`CData`](#bs4.CData)
      * [`CData.PREFIX`](#bs4.CData.PREFIX)
      * [`CData.SUFFIX`](#bs4.CData.SUFFIX)
    - [`CSS`](#bs4.CSS)
      * [`CSS.closest()`](#bs4.CSS.closest)
      * [`CSS.compile()`](#bs4.CSS.compile)
      * [`CSS.escape()`](#bs4.CSS.escape)
      * [`CSS.filter()`](#bs4.CSS.filter)
      * [`CSS.iselect()`](#bs4.CSS.iselect)
      * [`CSS.match()`](#bs4.CSS.match)
      * [`CSS.select()`](#bs4.CSS.select)
      * [`CSS.select_one()`](#bs4.CSS.select_one)
    - [`Comment`](#bs4.Comment)
      * [`Comment.PREFIX`](#bs4.Comment.PREFIX)
      * [`Comment.SUFFIX`](#bs4.Comment.SUFFIX)
    - [`Declaration`](#bs4.Declaration)
      * [`Declaration.PREFIX`](#bs4.Declaration.PREFIX)
      * [`Declaration.SUFFIX`](#bs4.Declaration.SUFFIX)
    - [`Doctype`](#bs4.Doctype)
      * [`Doctype.PREFIX`](#bs4.Doctype.PREFIX)
      * [`Doctype.SUFFIX`](#bs4.Doctype.SUFFIX)
      * [`Doctype.for_name_and_ids()`](#bs4.Doctype.for_name_and_ids)
    - [`ElementFilter`](#bs4.ElementFilter)
      * [`ElementFilter.allow_string_creation()`](#bs4.ElementFilter.allow_string_creation)
      * [`ElementFilter.allow_tag_creation()`](#bs4.ElementFilter.allow_tag_creation)
      * [`ElementFilter.excludes_everything`](#bs4.ElementFilter.excludes_everything)
      * [`ElementFilter.filter()`](#bs4.ElementFilter.filter)
      * [`ElementFilter.find()`](#bs4.ElementFilter.find)
      * [`ElementFilter.find_all()`](#bs4.ElementFilter.find_all)
      * [`ElementFilter.includes_everything`](#bs4.ElementFilter.includes_everything)
      * [`ElementFilter.match()`](#bs4.ElementFilter.match)
      * [`ElementFilter.match_function`](#bs4.ElementFilter.match_function)
    - [`FeatureNotFound`](#bs4.FeatureNotFound)
    - [`GuessedAtParserWarning`](#bs4.GuessedAtParserWarning)
      * [`GuessedAtParserWarning.MESSAGE`](#bs4.GuessedAtParserWarning.MESSAGE)
    - [`MarkupResemblesLocatorWarning`](#bs4.MarkupResemblesLocatorWarning)
      * [`MarkupResemblesLocatorWarning.FILENAME_MESSAGE`](#bs4.MarkupResemblesLocatorWarning.FILENAME_MESSAGE)
      * [`MarkupResemblesLocatorWarning.URL_MESSAGE`](#bs4.MarkupResemblesLocatorWarning.URL_MESSAGE)
    - [`ParserRejectedMarkup`](#bs4.ParserRejectedMarkup)
    - [`ProcessingInstruction`](#bs4.ProcessingInstruction)
      * [`ProcessingInstruction.PREFIX`](#bs4.ProcessingInstruction.PREFIX)
      * [`ProcessingInstruction.SUFFIX`](#bs4.ProcessingInstruction.SUFFIX)
    - [`ResultSet`](#bs4.ResultSet)
      * [`ResultSet.source`](#bs4.ResultSet.source)
    - [`Script`](#bs4.Script)
    - [`StopParsing`](#bs4.StopParsing)
    - [`Stylesheet`](#bs4.Stylesheet)
    - [`Tag`](#bs4.Tag)
      * [`Tag.append()`](#bs4.Tag.append)
      * [`Tag.attrs`](#bs4.Tag.attrs)
      * [`Tag.can_be_empty_element`](#bs4.Tag.can_be_empty_element)
      * [`Tag.cdata_list_attributes`](#bs4.Tag.cdata_list_attributes)
      * [`Tag.children`](#bs4.Tag.children)
      * [`Tag.clear()`](#bs4.Tag.clear)
      * [`Tag.contents`](#bs4.Tag.contents)
      * [`Tag.copy_self()`](#bs4.Tag.copy_self)
      * [`Tag.css`](#bs4.Tag.css)
      * [`Tag.decode()`](#bs4.Tag.decode)
      * [`Tag.decode_contents()`](#bs4.Tag.decode_contents)
      * [`Tag.descendants`](#bs4.Tag.descendants)
      * [`Tag.encode()`](#bs4.Tag.encode)
      * [`Tag.encode_contents()`](#bs4.Tag.encode_contents)
      * [`Tag.extend()`](#bs4.Tag.extend)
      * [`Tag.find()`](#bs4.Tag.find)
      * [`Tag.find_all()`](#bs4.Tag.find_all)
      * [`Tag.get()`](#bs4.Tag.get)
      * [`Tag.get_attribute_list()`](#bs4.Tag.get_attribute_list)
      * [`Tag.has_attr()`](#bs4.Tag.has_attr)
      * [`Tag.index()`](#bs4.Tag.index)
      * [`Tag.insert()`](#bs4.Tag.insert)
      * [`Tag.interesting_string_types`](#bs4.Tag.interesting_string_types)
      * [`Tag.isSelfClosing()`](#bs4.Tag.isSelfClosing)
      * [`Tag.is_empty_element`](#bs4.Tag.is_empty_element)
      * [`Tag.name`](#bs4.Tag.name)
      * [`Tag.namespace`](#bs4.Tag.namespace)
      * [`Tag.parser_class`](#bs4.Tag.parser_class)
      * [`Tag.prefix`](#bs4.Tag.prefix)
      * [`Tag.preserve_whitespace_tags`](#bs4.Tag.preserve_whitespace_tags)
      * [`Tag.prettify()`](#bs4.Tag.prettify)
      * [`Tag.replaceWithChildren()`](#bs4.Tag.replaceWithChildren)
      * [`Tag.replace_with_children()`](#bs4.Tag.replace_with_children)
      * [`Tag.select()`](#bs4.Tag.select)
      * [`Tag.select_one()`](#bs4.Tag.select_one)
      * [`Tag.self_and_descendants`](#bs4.Tag.self_and_descendants)
      * [`Tag.smooth()`](#bs4.Tag.smooth)
      * [`Tag.sourceline`](#bs4.Tag.sourceline)
      * [`Tag.sourcepos`](#bs4.Tag.sourcepos)
      * [`Tag.string`](#bs4.Tag.string)
      * [`Tag.strings`](#bs4.Tag.strings)
      * [`Tag.unwrap()`](#bs4.Tag.unwrap)
    - [`TemplateString`](#bs4.TemplateString)
    - [`UnicodeDammit`](#bs4.UnicodeDammit)
      * [`UnicodeDammit.CHARSET_ALIASES`](#bs4.UnicodeDammit.CHARSET_ALIASES)
      * [`UnicodeDammit.ENCODINGS_WITH_SMART_QUOTES`](#bs4.UnicodeDammit.ENCODINGS_WITH_SMART_QUOTES)
      * [`UnicodeDammit.MS_CHARS`](#bs4.UnicodeDammit.MS_CHARS)
      * [`UnicodeDammit.WINDOWS_1252_TO_UTF8`](#bs4.UnicodeDammit.WINDOWS_1252_TO_UTF8)
      * [`UnicodeDammit.contains_replacement_characters`](#bs4.UnicodeDammit.contains_replacement_characters)
      * [`UnicodeDammit.declared_html_encoding`](#bs4.UnicodeDammit.declared_html_encoding)
      * [`UnicodeDammit.detwingle()`](#bs4.UnicodeDammit.detwingle)
      * [`UnicodeDammit.find_codec()`](#bs4.UnicodeDammit.find_codec)
      * [`UnicodeDammit.markup`](#bs4.UnicodeDammit.markup)
      * [`UnicodeDammit.original_encoding`](#bs4.UnicodeDammit.original_encoding)
      * [`UnicodeDammit.smart_quotes_to`](#bs4.UnicodeDammit.smart_quotes_to)
      * [`UnicodeDammit.tried_encodings`](#bs4.UnicodeDammit.tried_encodings)
      * [`UnicodeDammit.unicode_markup`](#bs4.UnicodeDammit.unicode_markup)
    - [`UnusualUsageWarning`](#bs4.UnusualUsageWarning)
    - [`XMLParsedAsHTMLWarning`](#bs4.XMLParsedAsHTMLWarning)
      * [`XMLParsedAsHTMLWarning.MESSAGE`](#bs4.XMLParsedAsHTMLWarning.MESSAGE)
  + [Subpackages](#subpackages)
  + [Submodules](#submodules)
  + [bs4.css module](#module-bs4.css)
    - [`CSS`](#bs4.css.CSS)
      * [`CSS.closest()`](#bs4.css.CSS.closest)
      * [`CSS.compile()`](#bs4.css.CSS.compile)
      * [`CSS.escape()`](#bs4.css.CSS.escape)
      * [`CSS.filter()`](#bs4.css.CSS.filter)
      * [`CSS.iselect()`](#bs4.css.CSS.iselect)
      * [`CSS.match()`](#bs4.css.CSS.match)
      * [`CSS.select()`](#bs4.css.CSS.select)
      * [`CSS.select_one()`](#bs4.css.CSS.select_one)
  + [bs4.dammit module](#module-bs4.dammit)
    - [`EncodingDetector`](#bs4.dammit.EncodingDetector)
      * [`EncodingDetector.chardet_encoding`](#bs4.dammit.EncodingDetector.chardet_encoding)
      * [`EncodingDetector.declared_encoding`](#bs4.dammit.EncodingDetector.declared_encoding)
      * [`EncodingDetector.encodings`](#bs4.dammit.EncodingDetector.encodings)
      * [`EncodingDetector.exclude_encodings`](#bs4.dammit.EncodingDetector.exclude_encodings)
      * [`EncodingDetector.find_declared_encoding()`](#bs4.dammit.EncodingDetector.find_declared_encoding)
      * [`EncodingDetector.is_html`](#bs4.dammit.EncodingDetector.is_html)
      * [`EncodingDetector.known_definite_encodings`](#bs4.dammit.EncodingDetector.known_definite_encodings)
      * [`EncodingDetector.markup`](#bs4.dammit.EncodingDetector.markup)
      * [`EncodingDetector.sniffed_encoding`](#bs4.dammit.EncodingDetector.sniffed_encoding)
      * [`EncodingDetector.strip_byte_order_mark()`](#bs4.dammit.EncodingDetector.strip_byte_order_mark)
      * [`EncodingDetector.user_encodings`](#bs4.dammit.EncodingDetector.user_encodings)
    - [`EntitySubstitution`](#bs4.dammit.EntitySubstitution)
      * [`EntitySubstitution.AMPERSAND_OR_BRACKET`](#bs4.dammit.EntitySubstitution.AMPERSAND_OR_BRACKET)
      * [`EntitySubstitution.ANY_ENTITY_RE`](#bs4.dammit.EntitySubstitution.ANY_ENTITY_RE)
      * [`EntitySubstitution.BARE_AMPERSAND_OR_BRACKET`](#bs4.dammit.EntitySubstitution.BARE_AMPERSAND_OR_BRACKET)
      * [`EntitySubstitution.CHARACTER_TO_HTML_ENTITY`](#bs4.dammit.EntitySubstitution.CHARACTER_TO_HTML_ENTITY)
      * [`EntitySubstitution.CHARACTER_TO_HTML_ENTITY_RE`](#bs4.dammit.EntitySubstitution.CHARACTER_TO_HTML_ENTITY_RE)
      * [`EntitySubstitution.CHARACTER_TO_HTML_ENTITY_WITH_AMPERSAND_RE`](#bs4.dammit.EntitySubstitution.CHARACTER_TO_HTML_ENTITY_WITH_AMPERSAND_RE)
      * [`EntitySubstitution.CHARACTER_TO_XML_ENTITY`](#bs4.dammit.EntitySubstitution.CHARACTER_TO_XML_ENTITY)
      * [`EntitySubstitution.HTML_ENTITY_TO_CHARACTER`](#bs4.dammit.EntitySubstitution.HTML_ENTITY_TO_CHARACTER)
      * [`EntitySubstitution.quoted_attribute_value()`](#bs4.dammit.EntitySubstitution.quoted_attribute_value)
      * [`EntitySubstitution.substitute_html()`](#bs4.dammit.EntitySubstitution.substitute_html)
      * [`EntitySubstitution.substitute_html5()`](#bs4.dammit.EntitySubstitution.substitute_html5)
      * [`EntitySubstitution.substitute_html5_raw()`](#bs4.dammit.EntitySubstitution.substitute_html5_raw)
      * [`EntitySubstitution.substitute_xml()`](#bs4.dammit.EntitySubstitution.substitute_xml)
      * [`EntitySubstitution.substitute_xml_containing_entities()`](#bs4.dammit.EntitySubstitution.substitute_xml_containing_entities)
    - [`UnicodeDammit`](#bs4.dammit.UnicodeDammit)
      * [`UnicodeDammit.CHARSET_ALIASES`](#bs4.dammit.UnicodeDammit.CHARSET_ALIASES)
      * [`UnicodeDammit.ENCODINGS_WITH_SMART_QUOTES`](#bs4.dammit.UnicodeDammit.ENCODINGS_WITH_SMART_QUOTES)
      * [`UnicodeDammit.MS_CHARS`](#bs4.dammit.UnicodeDammit.MS_CHARS)
      * [`UnicodeDammit.WINDOWS_1252_TO_UTF8`](#bs4.dammit.UnicodeDammit.WINDOWS_1252_TO_UTF8)
      * [`UnicodeDammit.contains_replacement_characters`](#bs4.dammit.UnicodeDammit.contains_replacement_characters)
      * [`UnicodeDammit.declared_html_encoding`](#bs4.dammit.UnicodeDammit.declared_html_encoding)
      * [`UnicodeDammit.detwingle()`](#bs4.dammit.UnicodeDammit.detwingle)
      * [`UnicodeDammit.find_codec()`](#bs4.dammit.UnicodeDammit.find_codec)
      * [`UnicodeDammit.markup`](#bs4.dammit.UnicodeDammit.markup)
      * [`UnicodeDammit.original_encoding`](#bs4.dammit.UnicodeDammit.original_encoding)
      * [`UnicodeDammit.smart_quotes_to`](#bs4.dammit.UnicodeDammit.smart_quotes_to)
      * [`UnicodeDammit.tried_encodings`](#bs4.dammit.UnicodeDammit.tried_encodings)
      * [`UnicodeDammit.unicode_markup`](#bs4.dammit.UnicodeDammit.unicode_markup)
  + [bs4.element module](#module-bs4.element)
    - [`AttributeDict`](#bs4.element.AttributeDict)
    - [`AttributeValueList`](#bs4.element.AttributeValueList)
    - [`AttributeValueWithCharsetSubstitution`](#bs4.element.AttributeValueWithCharsetSubstitution)
      * [`AttributeValueWithCharsetSubstitution.substitute_encoding()`](#bs4.element.AttributeValueWithCharsetSubstitution.substitute_encoding)
    - [`CData`](#bs4.element.CData)
      * [`CData.PREFIX`](#bs4.element.CData.PREFIX)
      * [`CData.SUFFIX`](#bs4.element.CData.SUFFIX)
      * [`CData.next_element`](#bs4.element.CData.next_element)
      * [`CData.next_sibling`](#bs4.element.CData.next_sibling)
      * [`CData.parent`](#bs4.element.CData.parent)
      * [`CData.previous_element`](#bs4.element.CData.previous_element)
      * [`CData.previous_sibling`](#bs4.element.CData.previous_sibling)
    - [`CharsetMetaAttributeValue`](#bs4.element.CharsetMetaAttributeValue)
      * [`CharsetMetaAttributeValue.substitute_encoding()`](#bs4.element.CharsetMetaAttributeValue.substitute_encoding)
    - [`Comment`](#bs4.element.Comment)
      * [`Comment.PREFIX`](#bs4.element.Comment.PREFIX)
      * [`Comment.SUFFIX`](#bs4.element.Comment.SUFFIX)
      * [`Comment.next_element`](#bs4.element.Comment.next_element)
      * [`Comment.next_sibling`](#bs4.element.Comment.next_sibling)
      * [`Comment.parent`](#bs4.element.Comment.parent)
      * [`Comment.previous_element`](#bs4.element.Comment.previous_element)
      * [`Comment.previous_sibling`](#bs4.element.Comment.previous_sibling)
    - [`ContentMetaAttributeValue`](#bs4.element.ContentMetaAttributeValue)
      * [`ContentMetaAttributeValue.CHARSET_RE`](#bs4.element.ContentMetaAttributeValue.CHARSET_RE)
      * [`ContentMetaAttributeValue.substitute_encoding()`](#bs4.element.ContentMetaAttributeValue.substitute_encoding)
    - [`DEFAULT_OUTPUT_ENCODING`](#bs4.element.DEFAULT_OUTPUT_ENCODING)
    - [`Declaration`](#bs4.element.Declaration)
      * [`Declaration.PREFIX`](#bs4.element.Declaration.PREFIX)
      * [`Declaration.SUFFIX`](#bs4.element.Declaration.SUFFIX)
      * [`Declaration.next_element`](#bs4.element.Declaration.next_element)
      * [`Declaration.next_sibling`](#bs4.element.Declaration.next_sibling)
      * [`Declaration.parent`](#bs4.element.Declaration.parent)
      * [`Declaration.previous_element`](#bs4.element.Declaration.previous_element)
      * [`Declaration.previous_sibling`](#bs4.element.Declaration.previous_sibling)
    - [`Doctype`](#bs4.element.Doctype)
      * [`Doctype.PREFIX`](#bs4.element.Doctype.PREFIX)
      * [`Doctype.SUFFIX`](#bs4.element.Doctype.SUFFIX)
      * [`Doctype.for_name_and_ids()`](#bs4.element.Doctype.for_name_and_ids)
      * [`Doctype.next_element`](#bs4.element.Doctype.next_element)
      * [`Doctype.next_sibling`](#bs4.element.Doctype.next_sibling)
      * [`Doctype.parent`](#bs4.element.Doctype.parent)
      * [`Doctype.previous_element`](#bs4.element.Doctype.previous_element)
      * [`Doctype.previous_sibling`](#bs4.element.Doctype.previous_sibling)
    - [`HTMLAttributeDict`](#bs4.element.HTMLAttributeDict)
    - [`NamespacedAttribute`](#bs4.element.NamespacedAttribute)
      * [`NamespacedAttribute.name`](#bs4.element.NamespacedAttribute.name)
      * [`NamespacedAttribute.namespace`](#bs4.element.NamespacedAttribute.namespace)
      * [`NamespacedAttribute.prefix`](#bs4.element.NamespacedAttribute.prefix)
    - [`NavigableString`](#bs4.element.NavigableString)
      * [`NavigableString.PREFIX`](#bs4.element.NavigableString.PREFIX)
      * [`NavigableString.SUFFIX`](#bs4.element.NavigableString.SUFFIX)
      * [`NavigableString.output_ready()`](#bs4.element.NavigableString.output_ready)
      * [`NavigableString.strings`](#bs4.element.NavigableString.strings)
    - [`PYTHON_SPECIFIC_ENCODINGS`](#bs4.element.PYTHON_SPECIFIC_ENCODINGS)
    - [`PageElement`](#bs4.element.PageElement)
      * [`PageElement.decompose()`](#bs4.element.PageElement.decompose)
      * [`PageElement.decomposed`](#bs4.element.PageElement.decomposed)
      * [`PageElement.extract()`](#bs4.element.PageElement.extract)
      * [`PageElement.find_all_next()`](#bs4.element.PageElement.find_all_next)
      * [`PageElement.find_all_previous()`](#bs4.element.PageElement.find_all_previous)
      * [`PageElement.find_next()`](#bs4.element.PageElement.find_next)
      * [`PageElement.find_next_sibling()`](#bs4.element.PageElement.find_next_sibling)
      * [`PageElement.find_next_siblings()`](#bs4.element.PageElement.find_next_siblings)
      * [`PageElement.find_parent()`](#bs4.element.PageElement.find_parent)
      * [`PageElement.find_parents()`](#bs4.element.PageElement.find_parents)
      * [`PageElement.find_previous()`](#bs4.element.PageElement.find_previous)
      * [`PageElement.find_previous_sibling()`](#bs4.element.PageElement.find_previous_sibling)
      * [`PageElement.find_previous_siblings()`](#bs4.element.PageElement.find_previous_siblings)
      * [`PageElement.format_string()`](#bs4.element.PageElement.format_string)
      * [`PageElement.formatter_for_name()`](#bs4.element.PageElement.formatter_for_name)
      * [`PageElement.getText()`](#bs4.element.PageElement.getText)
      * [`PageElement.get_text()`](#bs4.element.PageElement.get_text)
      * [`PageElement.hidden`](#bs4.element.PageElement.hidden)
      * [`PageElement.insert_after()`](#bs4.element.PageElement.insert_after)
      * [`PageElement.insert_before()`](#bs4.element.PageElement.insert_before)
      * [`PageElement.known_xml`](#bs4.element.PageElement.known_xml)
      * [`PageElement.next`](#bs4.element.PageElement.next)
      * [`PageElement.next_element`](#bs4.element.PageElement.next_element)
      * [`PageElement.next_elements`](#bs4.element.PageElement.next_elements)
      * [`PageElement.next_sibling`](#bs4.element.PageElement.next_sibling)
      * [`PageElement.next_siblings`](#bs4.element.PageElement.next_siblings)
      * [`PageElement.parent`](#bs4.element.PageElement.parent)
      * [`PageElement.parents`](#bs4.element.PageElement.parents)
      * [`PageElement.previous`](#bs4.element.PageElement.previous)
      * [`PageElement.previous_element`](#bs4.element.PageElement.previous_element)
      * [`PageElement.previous_elements`](#bs4.element.PageElement.previous_elements)
      * [`PageElement.previous_sibling`](#bs4.element.PageElement.previous_sibling)
      * [`PageElement.previous_siblings`](#bs4.element.PageElement.previous_siblings)
      * [`PageElement.replace_with()`](#bs4.element.PageElement.replace_with)
      * [`PageElement.self_and_next_elements`](#bs4.element.PageElement.self_and_next_elements)
      * [`PageElement.self_and_next_siblings`](#bs4.element.PageElement.self_and_next_siblings)
      * [`PageElement.self_and_parents`](#bs4.element.PageElement.self_and_parents)
      * [`PageElement.self_and_previous_elements`](#bs4.element.PageElement.self_and_previous_elements)
      * [`PageElement.self_and_previous_siblings`](#bs4.element.PageElement.self_and_previous_siblings)
      * [`PageElement.setup()`](#bs4.element.PageElement.setup)
      * [`PageElement.stripped_strings`](#bs4.element.PageElement.stripped_strings)
      * [`PageElement.text`](#bs4.element.PageElement.text)
      * [`PageElement.wrap()`](#bs4.element.PageElement.wrap)
    - [`PreformattedString`](#bs4.element.PreformattedString)
      * [`PreformattedString.PREFIX`](#bs4.element.PreformattedString.PREFIX)
      * [`PreformattedString.SUFFIX`](#bs4.element.PreformattedString.SUFFIX)
      * [`PreformattedString.output_ready()`](#bs4.element.PreformattedString.output_ready)
    - [`ProcessingInstruction`](#bs4.element.ProcessingInstruction)
      * [`ProcessingInstruction.PREFIX`](#bs4.element.ProcessingInstruction.PREFIX)
      * [`ProcessingInstruction.SUFFIX`](#bs4.element.ProcessingInstruction.SUFFIX)
      * [`ProcessingInstruction.next_element`](#bs4.element.ProcessingInstruction.next_element)
      * [`ProcessingInstruction.next_sibling`](#bs4.element.ProcessingInstruction.next_sibling)
      * [`ProcessingInstruction.parent`](#bs4.element.ProcessingInstruction.parent)
      * [`ProcessingInstruction.previous_element`](#bs4.element.ProcessingInstruction.previous_element)
      * [`ProcessingInstruction.previous_sibling`](#bs4.element.ProcessingInstruction.previous_sibling)
    - [`ResultSet`](#bs4.element.ResultSet)
      * [`ResultSet.source`](#bs4.element.ResultSet.source)
    - [`RubyParenthesisString`](#bs4.element.RubyParenthesisString)
    - [`RubyTextString`](#bs4.element.RubyTextString)
    - [`Script`](#bs4.element.Script)
    - [`Stylesheet`](#bs4.element.Stylesheet)
    - [`Tag`](#bs4.element.Tag)
      * [`Tag.append()`](#bs4.element.Tag.append)
      * [`Tag.attrs`](#bs4.element.Tag.attrs)
      * [`Tag.can_be_empty_element`](#bs4.element.Tag.can_be_empty_element)
      * [`Tag.cdata_list_attributes`](#bs4.element.Tag.cdata_list_attributes)
      * [`Tag.children`](#bs4.element.Tag.children)
      * [`Tag.clear()`](#bs4.element.Tag.clear)
      * [`Tag.contents`](#bs4.element.Tag.contents)
      * [`Tag.copy_self()`](#bs4.element.Tag.copy_self)
      * [`Tag.css`](#bs4.element.Tag.css)
      * [`Tag.decode()`](#bs4.element.Tag.decode)
      * [`Tag.decode_contents()`](#bs4.element.Tag.decode_contents)
      * [`Tag.descendants`](#bs4.element.Tag.descendants)
      * [`Tag.encode()`](#bs4.element.Tag.encode)
      * [`Tag.encode_contents()`](#bs4.element.Tag.encode_contents)
      * [`Tag.extend()`](#bs4.element.Tag.extend)
      * [`Tag.find()`](#bs4.element.Tag.find)
      * [`Tag.find_all()`](#bs4.element.Tag.find_all)
      * [`Tag.get()`](#bs4.element.Tag.get)
      * [`Tag.get_attribute_list()`](#bs4.element.Tag.get_attribute_list)
      * [`Tag.has_attr()`](#bs4.element.Tag.has_attr)
      * [`Tag.index()`](#bs4.element.Tag.index)
      * [`Tag.insert()`](#bs4.element.Tag.insert)
      * [`Tag.interesting_string_types`](#bs4.element.Tag.interesting_string_types)
      * [`Tag.isSelfClosing()`](#bs4.element.Tag.isSelfClosing)
      * [`Tag.is_empty_element`](#bs4.element.Tag.is_empty_element)
      * [`Tag.name`](#bs4.element.Tag.name)
      * [`Tag.namespace`](#bs4.element.Tag.namespace)
      * [`Tag.next_element`](#bs4.element.Tag.next_element)
      * [`Tag.next_sibling`](#bs4.element.Tag.next_sibling)
      * [`Tag.parent`](#bs4.element.Tag.parent)
      * [`Tag.parser_class`](#bs4.element.Tag.parser_class)
      * [`Tag.prefix`](#bs4.element.Tag.prefix)
      * [`Tag.preserve_whitespace_tags`](#bs4.element.Tag.preserve_whitespace_tags)
      * [`Tag.prettify()`](#bs4.element.Tag.prettify)
      * [`Tag.previous_element`](#bs4.element.Tag.previous_element)
      * [`Tag.previous_sibling`](#bs4.element.Tag.previous_sibling)
      * [`Tag.replaceWithChildren()`](#bs4.element.Tag.replaceWithChildren)
      * [`Tag.replace_with_children()`](#bs4.element.Tag.replace_with_children)
      * [`Tag.select()`](#bs4.element.Tag.select)
      * [`Tag.select_one()`](#bs4.element.Tag.select_one)
      * [`Tag.self_and_descendants`](#bs4.element.Tag.self_and_descendants)
      * [`Tag.smooth()`](#bs4.element.Tag.smooth)
      * [`Tag.sourceline`](#bs4.element.Tag.sourceline)
      * [`Tag.sourcepos`](#bs4.element.Tag.sourcepos)
      * [`Tag.string`](#bs4.element.Tag.string)
      * [`Tag.strings`](#bs4.element.Tag.strings)
      * [`Tag.unwrap()`](#bs4.element.Tag.unwrap)
    - [`TemplateString`](#bs4.element.TemplateString)
    - [`XMLAttributeDict`](#bs4.element.XMLAttributeDict)
    - [`XMLProcessingInstruction`](#bs4.element.XMLProcessingInstruction)
      * [`XMLProcessingInstruction.PREFIX`](#bs4.element.XMLProcessingInstruction.PREFIX)
      * [`XMLProcessingInstruction.SUFFIX`](#bs4.element.XMLProcessingInstruction.SUFFIX)
    - [`nonwhitespace_re`](#bs4.element.nonwhitespace_re)
  + [bs4.filter module](#module-bs4.filter)
    - [`AttributeValueMatchRule`](#bs4.filter.AttributeValueMatchRule)
      * [`AttributeValueMatchRule.function`](#bs4.filter.AttributeValueMatchRule.function)
    - [`ElementFilter`](#bs4.filter.ElementFilter)
      * [`ElementFilter.allow_string_creation()`](#bs4.filter.ElementFilter.allow_string_creation)
      * [`ElementFilter.allow_tag_creation()`](#bs4.filter.ElementFilter.allow_tag_creation)
      * [`ElementFilter.excludes_everything`](#bs4.filter.ElementFilter.excludes_everything)
      * [`ElementFilter.filter()`](#bs4.filter.ElementFilter.filter)
      * [`ElementFilter.find()`](#bs4.filter.ElementFilter.find)
      * [`ElementFilter.find_all()`](#bs4.filter.ElementFilter.find_all)
      * [`ElementFilter.includes_everything`](#bs4.filter.ElementFilter.includes_everything)
      * [`ElementFilter.match()`](#bs4.filter.ElementFilter.match)
      * [`ElementFilter.match_function`](#bs4.filter.ElementFilter.match_function)
    - [`MatchRule`](#bs4.filter.MatchRule)
      * [`MatchRule.exclude_everything`](#bs4.filter.MatchRule.exclude_everything)
      * [`MatchRule.matches_string()`](#bs4.filter.MatchRule.matches_string)
      * [`MatchRule.pattern`](#bs4.filter.MatchRule.pattern)
      * [`MatchRule.present`](#bs4.filter.MatchRule.present)
      * [`MatchRule.string`](#bs4.filter.MatchRule.string)
    - [`SoupStrainer`](#bs4.filter.SoupStrainer)
      * [`SoupStrainer.allow_string_creation()`](#bs4.filter.SoupStrainer.allow_string_creation)
      * [`SoupStrainer.allow_tag_creation()`](#bs4.filter.SoupStrainer.allow_tag_creation)
      * [`SoupStrainer.attribute_rules`](#bs4.filter.SoupStrainer.attribute_rules)
      * [`SoupStrainer.excludes_everything`](#bs4.filter.SoupStrainer.excludes_everything)
      * [`SoupStrainer.includes_everything`](#bs4.filter.SoupStrainer.includes_everything)
      * [`SoupStrainer.match()`](#bs4.filter.SoupStrainer.match)
      * [`SoupStrainer.matches_any_string_rule()`](#bs4.filter.SoupStrainer.matches_any_string_rule)
      * [`SoupStrainer.matches_tag()`](#bs4.filter.SoupStrainer.matches_tag)
      * [`SoupStrainer.name_rules`](#bs4.filter.SoupStrainer.name_rules)
      * [`SoupStrainer.search_tag()`](#bs4.filter.SoupStrainer.search_tag)
      * [`SoupStrainer.string_rules`](#bs4.filter.SoupStrainer.string_rules)
    - [`StringMatchRule`](#bs4.filter.StringMatchRule)
      * [`StringMatchRule.function`](#bs4.filter.StringMatchRule.function)
    - [`TagNameMatchRule`](#bs4.filter.TagNameMatchRule)
      * [`TagNameMatchRule.function`](#bs4.filter.TagNameMatchRule.function)
      * [`TagNameMatchRule.matches_tag()`](#bs4.filter.TagNameMatchRule.matches_tag)
  + [bs4.formatter module](#module-bs4.formatter)
    - [`Formatter`](#bs4.formatter.Formatter)
      * [`Formatter.HTML`](#bs4.formatter.Formatter.HTML)
      * [`Formatter.HTML_DEFAULTS`](#bs4.formatter.Formatter.HTML_DEFAULTS)
      * [`Formatter.XML`](#bs4.formatter.Formatter.XML)
      * [`Formatter.attribute_value()`](#bs4.formatter.Formatter.attribute_value)
      * [`Formatter.attributes()`](#bs4.formatter.Formatter.attributes)
      * [`Formatter.empty_attributes_are_booleans`](#bs4.formatter.Formatter.empty_attributes_are_booleans)
      * [`Formatter.substitute()`](#bs4.formatter.Formatter.substitute)
    - [`HTMLFormatter`](#bs4.formatter.HTMLFormatter)
      * [`HTMLFormatter.REGISTRY`](#bs4.formatter.HTMLFormatter.REGISTRY)
    - [`XMLFormatter`](#bs4.formatter.XMLFormatter)
      * [`XMLFormatter.REGISTRY`](#bs4.formatter.XMLFormatter.REGISTRY)
  + [bs4.\_typing module](#module-bs4._typing)
    - [`_AttributeValues`](#bs4._typing._AttributeValues)
    - [`_BaseStrainable`](#bs4._typing._BaseStrainable)
    - [`_BaseStrainableAttribute`](#bs4._typing._BaseStrainableAttribute)
    - [`_BaseStrainableElement`](#bs4._typing._BaseStrainableElement)
    - [`_Encoding`](#bs4._typing._Encoding)
    - [`_Encodings`](#bs4._typing._Encodings)
    - [`_IncomingMarkup`](#bs4._typing._IncomingMarkup)
    - [`_InsertableElement`](#bs4._typing._InsertableElement)
    - [`_InvertedNamespaceMapping`](#bs4._typing._InvertedNamespaceMapping)
    - [`_NamespaceMapping`](#bs4._typing._NamespaceMapping)
    - [`_NamespacePrefix`](#bs4._typing._NamespacePrefix)
    - [`_NamespaceURL`](#bs4._typing._NamespaceURL)
    - [`_OneElement`](#bs4._typing._OneElement)
    - [`_PageElementMatchFunction`](#bs4._typing._PageElementMatchFunction)
    - [`_RawAttributeValue`](#bs4._typing._RawAttributeValue)
    - [`_RawAttributeValues`](#bs4._typing._RawAttributeValues)
    - [`_RawMarkup`](#bs4._typing._RawMarkup)
    - [`_RawOrProcessedAttributeValues`](#bs4._typing._RawOrProcessedAttributeValues)
    - [`_RegularExpressionProtocol`](#bs4._typing._RegularExpressionProtocol)
      * [`_RegularExpressionProtocol._abc_impl`](#bs4._typing._RegularExpressionProtocol._abc_impl)
      * [`_RegularExpressionProtocol._is_protocol`](#bs4._typing._RegularExpressionProtocol._is_protocol)
      * [`_RegularExpressionProtocol._is_runtime_protocol`](#bs4._typing._RegularExpressionProtocol._is_runtime_protocol)
      * [`_RegularExpressionProtocol.pattern`](#bs4._typing._RegularExpressionProtocol.pattern)
      * [`_RegularExpressionProtocol.search()`](#bs4._typing._RegularExpressionProtocol.search)
    - [`_StrainableAttribute`](#bs4._typing._StrainableAttribute)
    - [`_StrainableAttributes`](#bs4._typing._StrainableAttributes)
    - [`_StrainableElement`](#bs4._typing._StrainableElement)
    - [`_StrainableString`](#bs4._typing._StrainableString)
    - [`_StringMatchFunction`](#bs4._typing._StringMatchFunction)
    - [`_TagMatchFunction`](#bs4._typing._TagMatchFunction)
  + [bs4.diagnose module](#module-bs4.diagnose)
    - [`AnnouncingParser`](#bs4.diagnose.AnnouncingParser)
      * [`AnnouncingParser.handle_charref()`](#bs4.diagnose.AnnouncingParser.handle_charref)
      * [`AnnouncingParser.handle_comment()`](#bs4.diagnose.AnnouncingParser.handle_comment)
      * [`AnnouncingParser.handle_data()`](#bs4.diagnose.AnnouncingParser.handle_data)
      * [`AnnouncingParser.handle_decl()`](#bs4.diagnose.AnnouncingParser.handle_decl)
      * [`AnnouncingParser.handle_endtag()`](#bs4.diagnose.AnnouncingParser.handle_endtag)
      * [`AnnouncingParser.handle_entityref()`](#bs4.diagnose.AnnouncingParser.handle_entityref)
      * [`AnnouncingParser.handle_pi()`](#bs4.diagnose.AnnouncingParser.handle_pi)
      * [`AnnouncingParser.handle_starttag()`](#bs4.diagnose.AnnouncingParser.handle_starttag)
      * [`AnnouncingParser.unknown_decl()`](#bs4.diagnose.AnnouncingParser.unknown_decl)
    - [`benchmark_parsers()`](#bs4.diagnose.benchmark_parsers)
    - [`diagnose()`](#bs4.diagnose.diagnose)
    - [`htmlparser_trace()`](#bs4.diagnose.htmlparser_trace)
    - [`lxml_trace()`](#bs4.diagnose.lxml_trace)
    - [`profile()`](#bs4.diagnose.profile)

### Quick search







©2004-2025 Leonard Richardson.
|
Powered by [Sphinx 7.2.6](https://www.sphinx-doc.org/)
& [Alabaster 0.7.16](https://alabaster.readthedocs.io)
|
[Page source](../_sources/api/bs4.rst.txt)



---

## Navigation

**Part of beautifulsoup4 Documentation**
- **Main Documentation:** [https://www.crummy.com/software/BeautifulSoup/bs4/doc/](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- **This Section:** api/bs4.html

---

*Generated by lib2docScrape - Comprehensive Documentation Scraping*
