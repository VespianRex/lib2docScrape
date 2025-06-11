# Frequently Asked Questions[¶](#frequently-asked-questions "Link to this heading")

**Library:** requests
**Section:** community/faq
**Source URL:** https://requests.readthedocs.io/en/latest/community/faq/
**Scraped:** 2025-06-03T18:38:06.841005

---

## Document Information

- **Content Length:** 5,233 characters
- **Links Found:** 0
- **Headings Found:** 11
- **Has Code Blocks:** False
- **Has Tables:** False

---

## Content


Frequently Asked Questions — Requests 2.32.3 documentation







# Frequently Asked Questions[¶](#frequently-asked-questions "Link to this heading")

This part of the documentation answers common questions about Requests.

## Encoded Data?[¶](#encoded-data "Link to this heading")

Requests automatically decompresses gzip-encoded responses, and does
its best to decode response content to unicode when possible.

When either the [brotli](https://pypi.org/project/Brotli/) or [brotlicffi](https://pypi.org/project/brotlicffi/)
package is installed, requests also decodes Brotli-encoded responses.

You can get direct access to the raw response (and even the socket),
if needed as well.


## Custom User-Agents?[¶](#custom-user-agents "Link to this heading")

Requests allows you to easily override User-Agent strings, along with
any other HTTP Header. See [documentation about headers](../../user/quickstart/#custom-headers).


## Why not Httplib2?[¶](#why-not-httplib2 "Link to this heading")

Chris Adams gave an excellent summary on
[Hacker News](http://news.ycombinator.com/item?id=2884406):

> httplib2 is part of why you should use requests: it’s far more respectable
> as a client but not as well documented and it still takes way too much code
> for basic operations. I appreciate what httplib2 is trying to do, that
> there’s a ton of hard low-level annoyances in building a modern HTTP
> client, but really, just use requests instead. Kenneth Reitz is very
> motivated and he gets the degree to which simple things should be simple
> whereas httplib2 feels more like an academic exercise than something
> people should use to build production systems[1].
> 
> Disclosure: I’m listed in the requests AUTHORS file but can claim credit
> for, oh, about 0.0001% of the awesomeness.
> 
> 1. <http://code.google.com/p/httplib2/issues/detail?id=96> is a good example:
> an annoying bug which affect many people, there was a fix available for
> months, which worked great when I applied it in a fork and pounded a couple
> TB of data through it, but it took over a year to make it into trunk and
> even longer to make it onto PyPI where any other project which required ”
> httplib2” would get the working version.


## Python 3 Support?[¶](#python-3-support "Link to this heading")

Yes! Requests officially supports Python 3.8+ and PyPy.


## Python 2 Support?[¶](#python-2-support "Link to this heading")

No! As of Requests 2.28.0, Requests no longer supports Python 2.7. Users who
have been unable to migrate should pin to requests<2.28. Full information
can be found in [psf/requests#6023](https://github.com/psf/requests/issues/6023).

It is *highly* recommended users migrate to Python 3.8+ now since Python
2.7 is no longer receiving bug fixes or security updates as of January 1, 2020.


## What are “hostname doesn’t match” errors?[¶](#what-are-hostname-doesn-t-match-errors "Link to this heading")

These errors occur when [SSL certificate verification](../../user/advanced/#verification)
fails to match the certificate the server responds with to the hostname
Requests thinks it’s contacting. If you’re certain the server’s SSL setup is
correct (for example, because you can visit the site with your browser) and
you’re using Python 2.7, a possible explanation is that you need
Server-Name-Indication.

[Server-Name-Indication](https://en.wikipedia.org/wiki/Server_Name_Indication), or SNI, is an official extension to SSL where the
client tells the server what hostname it is contacting. This is important
when servers are using [Virtual Hosting](https://en.wikipedia.org/wiki/Virtual_hosting). When such servers are hosting
more than one SSL site they need to be able to return the appropriate
certificate based on the hostname the client is connecting to.

Python 3 already includes native support for SNI in their SSL modules.






Requests is an elegant and simple HTTP library for Python, built for
human beings. You are currently looking at the documentation of the
development release.

### Useful Links

* [Quickstart](../../user/quickstart/)
* [Advanced Usage](../../user/advanced/)
* [API Reference](../../api/)
* [Release History](../updates/#release-history)
* [Contributors Guide](../../dev/contributing/)
* [Recommended Packages and Extensions](../recommended/)
* [Requests @ GitHub](https://github.com/psf/requests)
* [Requests @ PyPI](https://pypi.org/project/requests/)
* [Issue Tracker](https://github.com/psf/requests/issues)

### [Table of Contents](../../)

* [Frequently Asked Questions](#)
  + [Encoded Data?](#encoded-data)
  + [Custom User-Agents?](#custom-user-agents)
  + [Why not Httplib2?](#why-not-httplib2)
  + [Python 3 Support?](#python-3-support)
  + [Python 2 Support?](#python-2-support)
  + [What are “hostname doesn’t match” errors?](#what-are-hostname-doesn-t-match-errors)
### Related Topics

* [Documentation overview](../../)
  + Previous: [Recommended Packages and Extensions](../recommended/ "previous chapter")
  + Next: [Integrations](../out-there/ "next chapter")

### Quick search








©MMXVIX. A Kenneth Reitz Project.

[![Fork me on GitHub](https://github.blog/wp-content/uploads/2008/12/forkme_right_darkblue_121621.png)](https://github.com/requests/requests)


---

## Navigation

**Part of requests Documentation**
- **Main Documentation:** [https://requests.readthedocs.io/en/latest/](https://requests.readthedocs.io/en/latest/)
- **This Section:** community/faq

---

*Generated by lib2docScrape - Comprehensive Documentation Scraping*
