# Requests: HTTP for Humans™ — Requests 2.32.3 documentation

**Library:** requests
**Description:** HTTP library for Python
**Source URL:** https://requests.readthedocs.io/en/latest/
**Scraped:** 2025-06-03T18:04:26.639006
**Content Length:** 9843 characters

---

## Raw Content


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
  + [Digest Authentication](user/authentication/#digest-authentic...

---

## Metadata

- **Document Index:** 1 of 2
- **Crawl Duration:** 2.25 seconds
- **Success Rate:** 2/2

## Additional Information

This documentation was automatically scraped from requests's official documentation
using lib2docScrape. The content above represents the raw scraped data.

For the most up-to-date information, please visit the original source at:
https://requests.readthedocs.io/en/latest/
