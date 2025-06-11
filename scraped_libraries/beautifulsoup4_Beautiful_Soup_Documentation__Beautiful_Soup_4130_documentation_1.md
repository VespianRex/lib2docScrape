# Beautiful Soup Documentation — Beautiful Soup 4.13.0 documentation

**Library:** beautifulsoup4
**Description:** HTML/XML parser
**Source URL:** https://www.crummy.com/software/BeautifulSoup/bs4/doc/
**Scraped:** 2025-06-03T18:04:35.742012
**Content Length:** 138730 characters

---

## Raw Content


Beautiful Soup Documentation — Beautiful Soup 4.13.0 documentation





# Beautiful Soup Documentation[¶](#beautiful-soup-documentation "Link to this heading")

!["The Fish-Footman began by producing from under his arm a great letter, nearly as large as himself."](_images/6.1.jpg)

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

* [这篇文档当然还有中文版.](https://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/)
* このページは日本語で利用できます([外部リンク](http://kondou.com/BS4/))
* [이 문서는 한국어 번역도 가능합니다.](https://www.crummy.com/software/BeautifulSoup/bs4/doc.ko/)
* [Este documento também está disponível em Português do Brasil.](https://www.crummy.com/software/BeautifulSoup/bs4/doc.ptbr)
* [Este documento también está disponible en una traducción al español.](https://www.crummy.com/software/BeautifulSoup/bs4/doc.es/)
* [Эта документация доступна на русском языке.](https://www.crummy.com/software/BeautifulSoup/bs4/doc.ru/)

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
document. It's part of a story from *Alice in Wonderland*:

```
html_doc = """<html><head><title>The Dormouse's story</title></head>
<body>
<p class="title"><b>The Dormouse's story</b></p>

<p class="story">Once upon a time there were three little sisters; and their names were
<a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
<a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
<a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
and they lived at the bottom of a well.</p>

<p class="story">...</p>
"""

```

Running the "three sisters" document through Beautiful Soup gives us a
`BeautifulSoup` object, which represents the document as a nested
data structure:

```
from bs4 import BeautifulSoup
soup = BeautifulSoup(html_doc, 'html.parser')

print(soup.prettify())
# <html>
#  <head>
#   <title>
#    The Dormouse's story
#   </title>
#  </head>
#  <body>
#   <p class="title">
#    <b>
#     The Dormouse's story
#    </b>
#   </p>
#   <p class="story">
#    Once upon a time there were three little sisters; and their names were
#    <a class="sister" href="http://example.com/elsie" id="link1">
#     Elsie
#    </a>
#    ,
#    <a class="sister" href="http://example.com/lacie" id="link2">
#     Lacie
#    </a>
#    and
#    <a class="sister" href="http://example.com/tillie" id="link3">
#     Tillie
#    </a>
#    ; and they lived at the bottom of a well.
#   </p>
#   <p class="story">
#    ...
#   </p>
#  </body>
# </html>

```

Here are some simple ways to navigate that data structure:

```
soup.title
# <title>The Dormouse's story</title>

soup.title.name
# u'title'

soup.title.string
# u'The Dormouse's story'

soup.title.parent.name
# u'head'

soup.p
# <p class="title"><b>The Dormouse's story</b></p>

soup.p['class']
# u'title'

soup.a
# <a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>

soup.find_all('a')
# [<a class="sister" href="http://example.com/elsie" id="link1">Elsie</a>,
#  <a class="sister" href="http://e...

---

## Metadata

- **Document Index:** 1 of 2
- **Crawl Duration:** 9.10 seconds
- **Success Rate:** 2/2

## Additional Information

This documentation was automatically scraped from beautifulsoup4's official documentation
using lib2docScrape. The content above represents the raw scraped data.

For the most up-to-date information, please visit the original source at:
https://www.crummy.com/software/BeautifulSoup/bs4/doc/
