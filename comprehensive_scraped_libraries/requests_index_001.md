# Requests: HTTP for Humans™[¶](#requests-http-for-humans "Link to this heading")

**Library:** requests
**Section:** 
**Source URL:** https://requests.readthedocs.io/en/latest/
**Scraped:** 2025-06-03T18:38:06.832625

---

## Document Information

- **Content Length:** 9,843 characters
- **Links Found:** 0
- **Headings Found:** 8
- **Has Code Blocks:** False
- **Has Tables:** False

---

## Content


Requests: HTTP for Humans™ — Requests 2.32.3 documentation






# Requests: HTTP for Humans™[¶](#requests-http-for-humans "Link to this heading")

Release v2.32.3. ([Installation](user/install/#install))

[![Requests Downloads Per Month Badge](https://static.pepy.tech/badge/requests/month)](https://pepy.tech/project/requests)
[![License Badge](https://img.shields.io/pypi/l/requests.svg)](https://pypi.org/project/requests/)
[![Wheel Support Badge](https://img.shields.io/pypi/wheel/requests.svg)](https://pypi.org/project/requests/)
[![Python Version Support Badge](https://img.shields.io/pypi/pyversions/requests.svg)](https://pypi.org/project/requests/)

**Requests** is an elegant and simple HTTP library for Python, built for human beings.

---

**Behold, the power of Requests**:

```
>>> r = requests.get('https://api.github.com/user', auth=('user', 'pass'))
>>> r.status_code
200
>>> r.headers['content-type']
'application/json; charset=utf8'
>>> r.encoding
'utf-8'
>>> r.text
'{"type":"User"...'
>>> r.json()
{'private_gists': 419, 'total_private_repos': 77, ...}

```

See [similar code, sans Requests](https://gist.github.com/973705).

**Requests** allows you to send HTTP/1.1 requests extremely easily.
There’s no need to manually add query strings to your
URLs, or to form-encode your POST data. Keep-alive and HTTP connection pooling
are 100% automatic, thanks to [urllib3](https://github.com/urllib3/urllib3).

## Beloved Features[¶](#beloved-features "Link to this heading")

Requests is ready for today’s web.

* Keep-Alive & Connection Pooling
* International Domains and URLs
* Sessions with Cookie Persistence
* Browser-style SSL Verification
* Automatic Content Decoding
* Basic/Digest Authentication
* Elegant Key/Value Cookies
* Automatic Decompression
* Unicode Response Bodies
* HTTP(S) Proxy Support
* Multipart File Uploads
* Streaming Downloads
* Connection Timeouts
* Chunked Requests
* `.netrc` Support

Requests officially supports Python 3.8+, and runs great on PyPy.


## The User Guide[¶](#the-user-guide "Link to this heading")

This part of the documentation, which is mostly prose, begins with some
background information about Requests, then focuses on step-by-step
instructions for getting the most out of Requests.

* [Installation of Requests](user/install/)
  + [$ python -m pip install requests](user/install/#python-m-pip-install-requests)
  + [Get the Source Code](user/install/#get-the-source-code)
* [Quickstart](user/quickstart/)
  + [Make a Request](user/quickstart/#make-a-request)
  + [Passing Parameters In URLs](user/quickstart/#passing-parameters-in-urls)
  + [Response Content](user/quickstart/#response-content)
  + [Binary Response Content](user/quickstart/#binary-response-content)
  + [JSON Response Content](user/quickstart/#json-response-content)
  + [Raw Response Content](user/quickstart/#raw-response-content)
  + [Custom Headers](user/quickstart/#custom-headers)
  + [More complicated POST requests](user/quickstart/#more-complicated-post-requests)
  + [POST a Multipart-Encoded File](user/quickstart/#post-a-multipart-encoded-file)
  + [Response Status Codes](user/quickstart/#response-status-codes)
  + [Response Headers](user/quickstart/#response-headers)
  + [Cookies](user/quickstart/#cookies)
  + [Redirection and History](user/quickstart/#redirection-and-history)
  + [Timeouts](user/quickstart/#timeouts)
  + [Errors and Exceptions](user/quickstart/#errors-and-exceptions)
* [Advanced Usage](user/advanced/)
  + [Session Objects](user/advanced/#session-objects)
  + [Request and Response Objects](user/advanced/#request-and-response-objects)
  + [Prepared Requests](user/advanced/#prepared-requests)
  + [SSL Cert Verification](user/advanced/#ssl-cert-verification)
  + [Client Side Certificates](user/advanced/#client-side-certificates)
  + [CA Certificates](user/advanced/#ca-certificates)
  + [Body Content Workflow](user/advanced/#body-content-workflow)
  + [Keep-Alive](user/advanced/#keep-alive)
  + [Streaming Uploads](user/advanced/#streaming-uploads)
  + [Chunk-Encoded Requests](user/advanced/#chunk-encoded-requests)
  + [POST Multiple Multipart-Encoded Files](user/advanced/#post-multiple-multipart-encoded-files)
  + [Event Hooks](user/advanced/#event-hooks)
  + [Custom Authentication](user/advanced/#custom-authentication)
  + [Streaming Requests](user/advanced/#streaming-requests)
  + [Proxies](user/advanced/#proxies)
  + [Compliance](user/advanced/#compliance)
  + [HTTP Verbs](user/advanced/#http-verbs)
  + [Custom Verbs](user/advanced/#custom-verbs)
  + [Link Headers](user/advanced/#link-headers)
  + [Transport Adapters](user/advanced/#transport-adapters)
  + [Blocking Or Non-Blocking?](user/advanced/#blocking-or-non-blocking)
  + [Header Ordering](user/advanced/#header-ordering)
  + [Timeouts](user/advanced/#timeouts)
* [Authentication](user/authentication/)
  + [Basic Authentication](user/authentication/#basic-authentication)
  + [Digest Authentication](user/authentication/#digest-authentication)
  + [OAuth 1 Authentication](user/authentication/#oauth-1-authentication)
  + [OAuth 2 and OpenID Connect Authentication](user/authentication/#oauth-2-and-openid-connect-authentication)
  + [Other Authentication](user/authentication/#other-authentication)
  + [New Forms of Authentication](user/authentication/#new-forms-of-authentication)


## The Community Guide[¶](#the-community-guide "Link to this heading")

This part of the documentation, which is mostly prose, details the
Requests ecosystem and community.

* [Recommended Packages and Extensions](community/recommended/)
  + [Certifi CA Bundle](community/recommended/#certifi-ca-bundle)
  + [CacheControl](community/recommended/#cachecontrol)
  + [Requests-Toolbelt](community/recommended/#requests-toolbelt)
  + [Requests-Threads](community/recommended/#requests-threads)
  + [Requests-OAuthlib](community/recommended/#requests-oauthlib)
  + [Betamax](community/recommended/#betamax)
* [Frequently Asked Questions](community/faq/)
  + [Encoded Data?](community/faq/#encoded-data)
  + [Custom User-Agents?](community/faq/#custom-user-agents)
  + [Why not Httplib2?](community/faq/#why-not-httplib2)
  + [Python 3 Support?](community/faq/#python-3-support)
  + [Python 2 Support?](community/faq/#python-2-support)
  + [What are “hostname doesn’t match” errors?](community/faq/#what-are-hostname-doesn-t-match-errors)
* [Integrations](community/out-there/)
* [Articles & Talks](community/out-there/#articles-talks)
* [Support](community/support/)
  + [Stack Overflow](community/support/#stack-overflow)
  + [File an Issue](community/support/#file-an-issue)
  + [Send a Tweet](community/support/#send-a-tweet)
* [Vulnerability Disclosure](community/vulnerabilities/)
* [Release Process and Rules](community/release-process/)
  + [Major Releases](community/release-process/#major-releases)
  + [Minor Releases](community/release-process/#minor-releases)
  + [Hotfix Releases](community/release-process/#hotfix-releases)
  + [Reasoning](community/release-process/#reasoning)

* [Community Updates](community/updates/)
* [Release History](community/updates/#release-history)


## The API Documentation / Guide[¶](#the-api-documentation-guide "Link to this heading")

If you are looking for information on a specific function, class, or method,
this part of the documentation is for you.

* [Developer Interface](api/)
  + [Main Interface](api/#main-interface)
  + [Exceptions](api/#exceptions)
  + [Request Sessions](api/#request-sessions)
  + [Lower-Level Classes](api/#lower-level-classes)
  + [Lower-Lower-Level Classes](api/#lower-lower-level-classes)
  + [Authentication](api/#authentication)
  + [Encodings](api/#encodings)
  + [Cookies](api/#cookies)
  + [Status Code Lookup](api/#status-code-lookup)
  + [Migrating to 1.x](api/#migrating-to-1-x)
  + [Migrating to 2.x](api/#migrating-to-2-x)


## The Contributor Guide[¶](#the-contributor-guide "Link to this heading")

If you want to contribute to the project, this part of the documentation is for
you.

* [Contributor’s Guide](dev/contributing/)
  + [Code of Conduct](dev/contributing/#code-of-conduct)
  + [Get Early Feedback](dev/contributing/#get-early-feedback)
  + [Contribution Suitability](dev/contributing/#contribution-suitability)
  + [Code Contributions](dev/contributing/#code-contributions)
    - [Steps for Submitting Code](dev/contributing/#steps-for-submitting-code)
    - [Code Review](dev/contributing/#code-review)
    - [Code Style](dev/contributing/#code-style)
    - [New Contributors](dev/contributing/#new-contributors)
  + [Documentation Contributions](dev/contributing/#documentation-contributions)
  + [Bug Reports](dev/contributing/#bug-reports)
  + [Feature Requests](dev/contributing/#feature-requests)
* [Authors](dev/authors/)
  + [Keepers of the Crystals](dev/authors/#keepers-of-the-crystals)
  + [Previous Keepers of Crystals](dev/authors/#previous-keepers-of-crystals)
  + [Patches and Suggestions](dev/authors/#patches-and-suggestions)

There are no more guides. You are now guideless.
Good luck.






[![Requests logo](_static/requests-sidebar.png)](#)

Requests is an elegant and simple HTTP library for Python, built for
human beings.

### Useful Links

* [Quickstart](user/quickstart/)
* [Advanced Usage](user/advanced/)
* [API Reference](api/)
* [Release History](community/updates/#release-history)
* [Contributors Guide](dev/contributing/)
* [Recommended Packages and Extensions](community/recommended/)
* [Requests @ GitHub](https://github.com/psf/requests)
* [Requests @ PyPI](https://pypi.org/project/requests/)
* [Issue Tracker](https://github.com/psf/requests/issues)


### Quick search








©MMXVIX. A Kenneth Reitz Project.

[![Fork me on GitHub](https://github.blog/wp-content/uploads/2008/12/forkme_right_darkblue_121621.png)](https://github.com/requests/requests)


---

## Navigation

**Part of requests Documentation**
- **Main Documentation:** [https://requests.readthedocs.io/en/latest/](https://requests.readthedocs.io/en/latest/)
- **This Section:** 

---

*Generated by lib2docScrape - Comprehensive Documentation Scraping*
