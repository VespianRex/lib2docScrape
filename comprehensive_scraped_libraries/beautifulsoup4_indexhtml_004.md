# The Dormouse's story

**Library:** beautifulsoup4
**Section:** index.html
**Source URL:** https://www.crummy.com/software/BeautifulSoup/bs4/doc/index.html
**Scraped:** 2025-06-03T18:38:23.750476

---

## Document Information

- **Content Length:** 17,552 characters
- **Links Found:** 11
- **Headings Found:** 0
- **Has Code Blocks:** False
- **Has Tables:** False

---

## Content


Beautiful Soup Documentation — Beautiful Soup 4.13.0 documentation
# Beautiful Soup Documentation[¶](#beautiful-soup-documentation "Link to this heading")
!["The Fish-Footman began by producing from under his arm a great letter, nearly as large as himself."](\_images/6.1.jpg)
[Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/) is a
Python library for pulling data out of HTML and XML files. It works
with your favorite parser to provide idiomatic ways of navigating,
searching, and modifying the parse tree. It commonly saves programmers
hours or days of work.
These instructions illustrate all major features of Beautiful Soup 4,
with examples. I show you what the library is good for, how it works,
how to use it, how to make it do what you want, and what to do when it
violates your expectations.
This document covers Beautiful Soup version 4.13.3. The examples in
this documentation were written for Python 3.8.
You might be looking for the documentation for [Beautiful Soup 3](http://www.crummy.com/software/BeautifulSoup/bs3/documentation.html).
If so, you should know that Beautiful Soup 3 is no longer being
developed and that all support for it was dropped on December
31, 2020. If you want to learn about the differences between Beautiful
Soup 3 and Beautiful Soup 4, see [Porting code to BS4](#porting-code-to-bs4).
This documentation has been translated into other languages by
Beautiful Soup users:
\* [这篇文档当然还有中文版.](https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/)
\* このページは日本語で利用できます([外部リンク](http://kondou.com/BS4/))
\* [이 문서는 한국어 번역도 가능합니다.](https://www.crummy.com/software/BeautifulSoup/bs4/doc.ko/)
\* [Este documento também está disponível em Português do Brasil.](https://www.crummy.com/software/BeautifulSoup/bs4/doc.ptbr)
\* [Este documento también está disponible en una traducción al español.](https://www.crummy.com/software/BeautifulSoup/bs4/doc.es/)
\* [Эта документация доступна на русском языке.](https://www.crummy.com/software/BeautifulSoup/bs4/doc.ru/)
## Getting help[¶](#getting-help "Link to this heading")
If you have questions about Beautiful Soup, or run into problems,
[send mail to the discussion group](https://groups.google.com/forum/?fromgroups#!forum/beautifulsoup). If
your problem involves parsing an HTML document, be sure to mention
[what the diagnose() function says](#diagnose) about
that document.
When reporting an error in this documentation, please mention which
translation you're reading.
### API documentation[¶](#api-documentation "Link to this heading")
This document is written like an instruction manual, but you can also read
[traditional API documentation](api/modules.html)
generated from the Beautiful Soup source code. If you want details
about Beautiful Soup's internals, or a feature not covered in this
document, try the API documentation.
# Quick Start[¶](#quick-start "Link to this heading")
Here's an HTML document I'll be using as an example throughout this
document. It's part of a story from \*Alice in Wonderland\*:
```
html\_doc = """The Dormouse's story

**The Dormouse's story**

Once upon a time there were three little sisters; and their names were
[Elsie](http://example.com/elsie),
[Lacie](http://example.com/lacie) and
[Tillie](http://example.com/tillie);
and they lived at the bottom of a well.

...

"""
```
Running the "three sisters" document through Beautiful Soup gives us a
`BeautifulSoup` object, which represents the document as a nested
data structure:
```
from bs4 import BeautifulSoup
soup = BeautifulSoup(html\_doc, 'html.parser')
print(soup.prettify())
#
#
# 
# The Dormouse's story
# 
#
#
#

# **# The Dormouse's story
#** 
#

#

# Once upon a time there were three little sisters; and their names were
# [# Elsie
#](http://example.com/elsie) 
# ,
# [# Lacie
#](http://example.com/lacie) 
# and
# [# Tillie
#](http://example.com/tillie) 
# ; and they lived at the bottom of a well.
#

#

# ...
#

#
#
```
Here are some simple ways to navigate that data structure:
```
soup.title
# The Dormouse's story
soup.title.name
# u'title'
soup.title.string
# u'The Dormouse's story'
soup.title.parent.name
# u'head'
soup.p
#

**The Dormouse's story**

soup.p['class']
# u'title'
soup.a
# [Elsie](http://example.com/elsie)
soup.find\_all('a')
# [[Elsie](http://example.com/elsie),
# [Lacie](http://example.com/lacie),
# [Tillie](http://example.com/tillie)]
soup.find(id="link3")
# [Tillie](http://example.com/tillie)
```
One common task is extracting all the URLs found within a page's tags:
```
for link in soup.find\_all('a'):
print(link.get('href'))
# http://example.com/elsie
# http://example.com/lacie
# http://example.com/tillie
```
Another common task is extracting all the text from a page:
```
print(soup.get\_text())
# The Dormouse's story
#
# The Dormouse's story
#
# Once upon a time there were three little sisters; and their names were
# Elsie,
# Lacie and
# Tillie;
# and they lived at the bottom of a well.
#
# ...
```
Does this look like what you need? If so, read on.
# Installing Beautiful Soup[¶](#installing-beautiful-soup "Link to this heading")
If you're using a recent version of Debian or Ubuntu Linux, you can
install Beautiful Soup with the system package manager:
$ apt-get install python3-bs4
Beautiful Soup 4 is published through PyPi, so if you can't install it
with the system packager, you can install it with `easy\_install` or
`pip`. The package name is `beautifulsoup4`. Make sure you use the
right version of `pip` or `easy\_install` for your Python version
(these may be named `pip3` and `easy\_install3` respectively).
$ easy\\_install beautifulsoup4
$ pip install beautifulsoup4
(The `BeautifulSoup` package is \*not\* what you want. That's
the previous major release, [Beautiful Soup 3](http://www.crummy.com/software/BeautifulSoup/bs3/documentation.html). Lots of software uses
BS3, so it's still available, but if you're writing new code you
should install `beautifulsoup4`.)
If you don't have `easy\_install` or `pip` installed, you can
[download the Beautiful Soup 4 source tarball](http://www.crummy.com/software/BeautifulSoup/download/4.x/) and
install it with `setup.py`.
$ python setup.py install
If all else fails, the license for Beautiful Soup allows you to
package the entire library with your application. You can download the
tarball, copy its `bs4` directory into your application's codebase,
and use Beautiful Soup without installing it at all.
I use Python 3.10 to develop Beautiful Soup, but it should work with
other recent versions.
## Installing a parser[¶](#installing-a-parser "Link to this heading")
Beautiful Soup supports the HTML parser included in Python's standard
library, but it also supports a number of third-party Python parsers.
One is the [lxml parser](http://lxml.de/). Depending on your setup,
you might install lxml with one of these commands:
$ apt-get install python-lxml
$ easy\\_install lxml
$ pip install lxml
Another alternative is the pure-Python [html5lib parser](http://code.google.com/p/html5lib/), which parses HTML the way a
web browser does. Depending on your setup, you might install html5lib
with one of these commands:
$ apt-get install python3-html5lib
$ pip install html5lib
This table summarizes the advantages and disadvantages of each parser library:
| Parser | Typical usage | Advantages | Disadvantages |
| --- | --- | --- | --- |
| Python's html.parser | `BeautifulSoup(markup, "html.parser")` | \* Batteries included \* Decent speed | \* Not as fast as lxml, less lenient than html5lib. |
| lxml's HTML parser | `BeautifulSoup(markup, "lxml")` | \* Very fast | \* External C dependency |
| lxml's XML parser | `BeautifulSoup(markup, "lxml-xml")` `BeautifulSoup(markup, "xml")` | \* Very fast \* The only currently supported XML parser | \* External C dependency |
| html5lib | `BeautifulSoup(markup, "html5lib")` | \* Extremely lenient \* Parses pages the same way a web browser does \* Creates valid HTML5 | \* Very slow \* External Python dependency |
If you can, I recommend you install and use lxml for speed.
Note that if a document is invalid, different parsers will generate
different Beautiful Soup trees for it. See [Differences
between parsers](#differences-between-parsers) for details.
# Making the soup[¶](#making-the-soup "Link to this heading")
To parse a document, pass it into the `BeautifulSoup`
constructor. You can pass in a string or an open filehandle:
```
from bs4 import BeautifulSoup
with open("index.html") as fp:
soup = BeautifulSoup(fp, 'html.parser')
soup = BeautifulSoup("a web page", 'html.parser')
```
First, the document is converted to Unicode, and HTML entities are
converted to Unicode characters:
```
print(BeautifulSoup("Sacré bleu!", "html.parser"))
# Sacré bleu!
```
Beautiful Soup then parses the document using the best available
parser. It will use an HTML parser unless you specifically tell it to
use an XML parser. (See [Parsing XML](#id15).)
# Kinds of objects[¶](#kinds-of-objects "Link to this heading")
Beautiful Soup transforms a complex HTML document into a complex tree
of Python objects. But you'll only ever have to deal with about four
\*kinds\* of objects: [`Tag`](#Tag "Tag"), [`NavigableString`](#NavigableString "NavigableString"), `BeautifulSoup`,
and [`Comment`](#Comment "Comment"). These objects represent the HTML \*elements\*
that comprise the page.
\*class\* Tag[¶](#Tag "Link to this definition")
A [`Tag`](#Tag "Tag") object corresponds to an XML or HTML tag in the original document.
```
soup = BeautifulSoup('**Extremely bold**', 'html.parser')
tag = soup.b
type(tag)
#
```
Tags have a lot of attributes and methods, and I'll cover most of them
in [Navigating the tree](#navigating-the-tree) and [Searching the tree](#searching-the-tree). For now, the most
important methods of a tag are for accessing its name and attributes.
name[¶](#Tag.name "Link to this definition")
Every tag has a name:
```
tag.name
# 'b'
```
If you change a tag's name, the change will be reflected in any
markup generated by Beautiful Soup down the line:
```
tag.name = "blockquote"
tag
#
> Extremely bold

```
attrs[¶](#Tag.attrs "Link to this definition")
An HTML or XML tag may have any number of attributes. The tag `**` has an attribute "id" whose value is
"boldest". You can access a tag's attributes by treating the tag like
a dictionary:
```
tag = BeautifulSoup('**bold**', 'html.parser').b
tag['id']
# 'boldest'
```
You can access the dictionary of attributes directly as `.attrs`:
```
tag.attrs
# {'id': 'boldest'}
tag.attrs.keys()
# dict\_keys(['id'])
```
You can add, remove, and modify a tag's attributes. Again, this is
done by treating the tag as a dictionary:
```
tag['id'] = 'verybold'
tag['another-attribute'] = 1
tag
# 
del tag['id']
del tag['another-attribute']
tag
# **bold**
tag['id']
# KeyError: 'id'
tag.get('id')
# None
```
## Multi-valued attributes[¶](#multi-valued-attributes "Link to this heading")
HTML 4 defines a few attributes that can have multiple values. HTML 5
removes a couple of them, but defines a few more. The most common
multi-valued attribute is `class` (that is, a tag can have more than
one CSS class). Others include `rel`, `rev`, `accept-charset`,
`headers`, and `accesskey`. By default, Beautiful Soup stores the value(s)
of a multi-valued attribute as a list:
```
css\_soup = BeautifulSoup('', 'html.parser')
css\_soup.p['class']
# ['body']
css\_soup = BeautifulSoup('', 'html.parser')
css\_soup.p['class']
# ['body', 'strikeout']
```
When you turn a tag back into a string, the values of any multi-valued
attributes are consolidated:
```
rel\_soup = BeautifulSoup('****Back to thehomepage

', 'html.parser')
rel\_soup.a['rel']
# ['index', 'first']
rel\_soup.a['rel'] = ['index', 'contents']
print(rel\_soup.p)
#

Back to the homepage

```
If an attribute \*looks\* like it has more than one value, but it's not
a multi-valued attribute as defined by any version of the HTML
standard, Beautiful Soup stores it as a simple string:
```
id\_soup = BeautifulSoup('', 'html.parser')
id\_soup.p['id']
# 'my id'
```
You can force all attributes to be stored as strings by passing
`multi\_valued\_attributes=None` as a keyword argument into the
`BeautifulSoup` constructor:
```
no\_list\_soup = BeautifulSoup('', 'html.parser', multi\_valued\_attributes=None)
no\_list\_soup.p['class']
# 'body strikeout'
```
You can use `get\_attribute\_list` to always return the value in a list
container, whether it's a string or multi-valued attribute value:
```
id\_soup.p['id']
# 'my id'
id\_soup.p.get\_attribute\_list('id')
# ["my id"]
```
If you parse a document as XML, there are no multi-valued attributes:
```
xml\_soup = BeautifulSoup('', 'xml')
xml\_soup.p['class']
# 'body strikeout'
```
Again, you can configure this using the `multi\_valued\_attributes` argument:
```
class\_is\_multi= { '\*' : 'class'}
xml\_soup = BeautifulSoup('', 'xml', multi\_valued\_attributes=class\_is\_multi)
xml\_soup.p['class']
# ['body', 'strikeout']
```
You probably won't need to do this, but if you do, use the defaults as
a guide. They implement the rules described in the HTML specification:
```
from bs4.builder import builder\_registry
builder\_registry.lookup('html').DEFAULT\_CDATA\_LIST\_ATTRIBUTES
```
\*class\* NavigableString[¶](#NavigableString "Link to this definition")
---
A tag can contain strings as pieces of text. Beautiful Soup
uses the [`NavigableString`](#NavigableString "NavigableString") class to contain these pieces of text:
```
soup = BeautifulSoup('**Extremely bold**', 'html.parser')
tag = soup.b
tag.string
# 'Extremely bold'
type(tag.string)
#
```
A [`NavigableString`](#NavigableString "NavigableString") is just like a Python Unicode string, except
that it also supports some of the features described in [Navigating
the tree](#navigating-the-tree) and [Searching the tree](#searching-the-tree). You can convert a
[`NavigableString`](#NavigableString "NavigableString") to a Unicode string with `str`:
```
unicode\_string = str(tag.string)
unicode\_string
# 'Extremely bold'
type(unicode\_string)
#
```
You can't edit a string in place, but you can replace one string with
another, using [replace\\_with()](#replace-with):
```
tag.string.replace\_with("No longer bold")
tag
# **No longer bold**
```
[`NavigableString`](#NavigableString "NavigableString") supports most of the features described in
[Navigating the tree](#navigating-the-tree) and [Searching the tree](#searching-the-tree), but not all of
them. In particular, since a string can't contain anything (the way a
tag may contain a string or another tag), strings don't support the
`.contents` or `.string` attributes, or the `find()` method.
If you want to use a [`NavigableString`](#NavigableString "NavigableString") outside of Beautiful Soup,
you should call `unicode()` on it to turn it into a normal Python
Unicode string. If you don't, your string will carry around a
reference to the entire Beautiful Soup parse tree, even when you're
done using Beautiful Soup. This is a big waste of memory.
---
The `BeautifulSoup` object represents the parsed document as a
whole. For most purposes, you can treat it as a [`Tag`](#Tag "Tag")
object. This means it supports most of the methods described in
[Navigating the tree](#navigating-the-tree) and [Searching the tree](#searching-the-tree).
You can also pass a `BeautifulSoup` object into one of the methods
defined in [Modifying the tree](#modifying-the-tree), just as you would a [`Tag`](#Tag "Tag"). This
lets you do things like combine two parsed documents:
```
doc = BeautifulSoup("INSERT FOOTER HEREHere's the footer", "xml")
doc.find(text="INSERT FOOTER HERE").replace\_with(footer)
# 'INSERT FOOTER HERE'
print(doc)
#
# Here's the footer
```
Since the `BeautifulSoup` object doesn't correspond to an actual
HTML or XML tag, it has no name and no attributes. But sometimes it's
useful to reference its `.name` (such as when writing code that works
with both [`Tag`](#Tag "Tag") and `BeautifulSoup` objects),
so it's been given the special `.name` "[document]":
```
soup.name
# '[document]'
```
## Special strings[¶](#special-strings "Link to this heading")
[`Tag`](#Tag "Tag"), [`NavigableString`](#NavigableString "NavigableString"), and
`BeautifulSoup` cover almost everything you'll see in an
HTML or XML file, but there are a few leftover bits. The main one
you'll probably encounter is the [`Comment`](#Comment "Comment").
\*class\* Comment[¶](#Comment "Link to this definition")
```
markup = ""
soup = BeautifulSoup(markup, 'html.parser')
comment = soup.b.string
type(comment)
#
```
The [`Comment`](#Comment "Comment") object is just a special type of [`NavigableString`](#NavigableString "NavigableString"):
```
comment
# 'Hey, buddy. Want to buy a used parser'
```
But when it appears as part of an HTML document, a [`Comment`](#Comment "Comment") is
displayed with special formatting:
```
print(soup.b.prettify())
# **#
#** 
```
### For HTML documents[¶](#for-html-documents "Link to this heading")
Beautiful Soup defines a few [`NavigableString`](#NavigableString "NavigableString") subclasses to
contain strings found inside specific HTML tags. This makes it easier
to pick out the main body of the page, by ignoring strings that
probably represent programming directives found within the
page. \*(These classes are new in Beautiful Soup 4.9.0, and the
html5lib parser doesn't use them.)\*
\*class\* Stylesheet[¶](#Stylesheet "Link to this definition")
A [`NavigableString`](#NavigableString "NavigableString") subclass that represents embedded CSS
stylesheets; that is, any strings found inside a `**

---

## Navigation

**Part of beautifulsoup4 Documentation**
- **Main Documentation:** [https://www.crummy.com/software/BeautifulSoup/bs4/doc/](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- **This Section:** index.html

---

*Generated by lib2docScrape - Comprehensive Documentation Scraping*
