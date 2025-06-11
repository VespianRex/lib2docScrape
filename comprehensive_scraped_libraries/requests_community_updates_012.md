# Community Updates[¶](#community-updates "Link to this heading")

**Library:** requests
**Section:** community/updates
**Source URL:** https://requests.readthedocs.io/en/latest/community/updates/
**Scraped:** 2025-06-03T18:38:06.846751

---

## Document Information

- **Content Length:** 67,599 characters
- **Links Found:** 0
- **Headings Found:** 163
- **Has Code Blocks:** False
- **Has Tables:** False

---

## Content


Community Updates — Requests 2.32.3 documentation







# Community Updates[¶](#community-updates "Link to this heading")

If you’d like to stay up to date on the community and development of Requests,
there are several options:

## GitHub[¶](#github "Link to this heading")

The best way to track the development of Requests is through
[the GitHub repo](https://github.com/psf/requests).



# Release History[¶](#release-history "Link to this heading")

## dev[¶](#dev "Link to this heading")

* [Short description of non-trivial change.]

**Deprecations**
- Added support for pypy 3.11 for Linux and macOS.
- Dropped support for pypy 3.9 following its end of support.


## 2.32.3 (2024-05-29)[¶](#id1 "Link to this heading")

**Bugfixes**
- Fixed bug breaking the ability to specify custom SSLContexts in sub-classes of

> HTTPAdapter. (#6716)

* Fixed issue where Requests started failing to run on Python versions compiled
  without the ssl module. (#6724)

## 2.32.2 (2024-05-21)[¶](#id2 "Link to this heading")

**Deprecations**
- To provide a more stable migration for custom HTTPAdapters impacted

> by the CVE changes in 2.32.0, we’ve renamed \_get\_connection to
> a new public API, get\_connection\_with\_tls\_context. Existing custom
> HTTPAdapters will need to migrate their code to use this new API.
> get\_connection is considered deprecated in all versions of Requests>=2.32.0.
> 
> A minimal (2-line) example has been provided in the linked PR to ease
> migration, but we strongly urge users to evaluate if their custom adapter
> is subject to the same issue described in CVE-2024-35195. (#6710)


## 2.32.1 (2024-05-20)[¶](#id3 "Link to this heading")

**Bugfixes**
- Add missing test certs to the sdist distributed on PyPI.


## 2.32.0 (2024-05-20)[¶](#id4 "Link to this heading")

**Security**
- Fixed an issue where setting verify=False on the first request from a

> Session will cause subsequent requests to the \_same [origin\_](#id156) to also ignore
> cert verification, regardless of the value of verify.
> (<https://github.com/psf/requests/security/advisories/GHSA-9wx4-h78v-vm56>)

**Improvements**
- verify=True now reuses a global SSLContext which should improve

> request time variance between first and subsequent requests. It should
> also minimize certificate load time on Windows systems when using a Python
> version built with OpenSSL 3.x. (#6667)

* Requests now supports optional use of character detection
  (chardet or charset\_normalizer) when repackaged or vendored.
  This enables pip and other projects to minimize their vendoring
  surface area. The Response.text() and apparent\_encoding APIs
  will default to utf-8 if neither library is present. (#6702)

**Bugfixes**
- Fixed bug in length detection where emoji length was incorrectly

> calculated in the request content-length. (#6589)

* Fixed deserialization bug in JSONDecodeError. (#6629)
* Fixed bug where an extra leading / (path separator) could lead
  urllib3 to unnecessarily reparse the request URI. (#6644)

**Deprecations**

* Requests has officially added support for CPython 3.12 (#6503)
* Requests has officially added support for PyPy 3.9 and 3.10 (#6641)
* Requests has officially dropped support for CPython 3.7 (#6642)
* Requests has officially dropped support for PyPy 3.7 and 3.8 (#6641)

**Documentation**
- Various typo fixes and doc improvements.

**Packaging**
- Requests has started adopting some modern packaging practices.

> The source files for the projects (formerly requests) is now located
> in src/requests in the Requests sdist. (#6506)

* Starting in Requests 2.33.0, Requests will migrate to a PEP 517 build system
  using hatchling. This should not impact the average user, but extremely old
  versions of packaging utilities may have issues with the new packaging format.

## 2.31.0 (2023-05-22)[¶](#id5 "Link to this heading")

**Security**
- Versions of Requests between v2.3.0 and v2.30.0 are vulnerable to potential

> forwarding of Proxy-Authorization headers to destination servers when
> following HTTPS redirects.
> 
> When proxies are defined with user info (https://user:pass@proxy:8080), Requests
> will construct a Proxy-Authorization header that is attached to the request to
> authenticate with the proxy.
> 
> In cases where Requests receives a redirect response, it previously reattached
> the Proxy-Authorization header incorrectly, resulting in the value being
> sent through the tunneled connection to the destination server. Users who rely on
> defining their proxy credentials in the URL are *strongly* encouraged to upgrade
> to Requests 2.31.0+ to prevent unintentional leakage and rotate their proxy
> credentials once the change has been fully deployed.
> 
> Users who do not use a proxy or do not supply their proxy credentials through
> the user information portion of their proxy URL are not subject to this
> vulnerability.
> 
> Full details can be read in our [Github Security Advisory](<https://github.com/psf/requests/security/advisories/GHSA-j8r2-6x86-q33q>)
> and [CVE-2023-32681](<https://nvd.nist.gov/vuln/detail/CVE-2023-32681>).


## 2.30.0 (2023-05-03)[¶](#id6 "Link to this heading")

**Dependencies**
- ⚠️ Added support for urllib3 2.0. ⚠️

> This may contain minor breaking changes so we advise careful testing and
> reviewing <https://urllib3.readthedocs.io/en/latest/v2-migration-guide.html>
> prior to upgrading.
> 
> Users who wish to stay on urllib3 1.x can pin to urllib3<2.


## 2.29.0 (2023-04-26)[¶](#id7 "Link to this heading")

**Improvements**

* Requests now defers chunked requests to the urllib3 implementation to improve
  standardization. (#6226)
* Requests relaxes header component requirements to support bytes/str subclasses. (#6356)

## 2.28.2 (2023-01-12)[¶](#id8 "Link to this heading")

**Dependencies**

* Requests now supports charset\_normalizer 3.x. (#6261)

**Bugfixes**

* Updated MissingSchema exception to suggest https scheme rather than http. (#6188)

## 2.28.1 (2022-06-29)[¶](#id9 "Link to this heading")

**Improvements**

* Speed optimization in iter\_content with transition to yield from. (#6170)

**Dependencies**

* Added support for chardet 5.0.0 (#6179)
* Added support for charset-normalizer 2.1.0 (#6169)

## 2.28.0 (2022-06-09)[¶](#id10 "Link to this heading")

**Deprecations**

* ⚠️ Requests has officially dropped support for Python 2.7. ⚠️ (#6091)
* Requests has officially dropped support for Python 3.6 (including pypy3.6). (#6091)

**Improvements**

* Wrap JSON parsing issues in Request’s JSONDecodeError for payloads without
  an encoding to make json() API consistent. (#6097)
* Parse header components consistently, raising an InvalidHeader error in
  all invalid cases. (#6154)
* Added provisional 3.11 support with current beta build. (#6155)
* Requests got a makeover and we decided to paint it black. (#6095)

**Bugfixes**

* Fixed bug where setting CURL\_CA\_BUNDLE to an empty string would disable
  cert verification. All Requests 2.x versions before 2.28.0 are affected. (#6074)
* Fixed urllib3 exception leak, wrapping urllib3.exceptions.SSLError with
  requests.exceptions.SSLError for content and iter\_content. (#6057)
* Fixed issue where invalid Windows registry entries caused proxy resolution
  to raise an exception rather than ignoring the entry. (#6149)
* Fixed issue where entire payload could be included in the error message for
  JSONDecodeError. (#6036)

## 2.27.1 (2022-01-05)[¶](#id11 "Link to this heading")

**Bugfixes**

* Fixed parsing issue that resulted in the auth component being
  dropped from proxy URLs. (#6028)

## 2.27.0 (2022-01-03)[¶](#id12 "Link to this heading")

**Improvements**

* Officially added support for Python 3.10. (#5928)
* Added a requests.exceptions.JSONDecodeError to unify JSON exceptions between
  Python 2 and 3. This gets raised in the response.json() method, and is
  backwards compatible as it inherits from previously thrown exceptions.
  Can be caught from requests.exceptions.RequestException as well. (#5856)
* Improved error text for misnamed InvalidSchema and MissingSchema
  exceptions. This is a temporary fix until exceptions can be renamed
  (Schema->Scheme). (#6017)
* Improved proxy parsing for proxy URLs missing a scheme. This will address
  recent changes to urlparse in Python 3.9+. (#5917)

**Bugfixes**

* Fixed defect in extract\_zipped\_paths which could result in an infinite loop
  for some paths. (#5851)
* Fixed handling for AttributeError when calculating length of files obtained
  by Tarfile.extractfile(). (#5239)
* Fixed urllib3 exception leak, wrapping urllib3.exceptions.InvalidHeader with
  requests.exceptions.InvalidHeader. (#5914)
* Fixed bug where two Host headers were sent for chunked requests. (#5391)
* Fixed regression in Requests 2.26.0 where Proxy-Authorization was
  incorrectly stripped from all requests sent with Session.send. (#5924)
* Fixed performance regression in 2.26.0 for hosts with a large number of
  proxies available in the environment. (#5924)
* Fixed idna exception leak, wrapping UnicodeError with
  requests.exceptions.InvalidURL for URLs with a leading dot (.) in the
  domain. (#5414)

**Deprecations**

* Requests support for Python 2.7 and 3.6 will be ending in 2022. While we
  don’t have exact dates, Requests 2.27.x is likely to be the last release
  series providing support.

## 2.26.0 (2021-07-13)[¶](#id13 "Link to this heading")

**Improvements**

* Requests now supports Brotli compression, if either the brotli or
  brotlicffi package is installed. (#5783)
* Session.send now correctly resolves proxy configurations from both
  the Session and Request. Behavior now matches Session.request. (#5681)

**Bugfixes**

* Fixed a race condition in zip extraction when using Requests in parallel
  from zip archive. (#5707)

**Dependencies**

* Instead of chardet, use the MIT-licensed charset\_normalizer for Python3
  to remove license ambiguity for projects bundling requests. If chardet
  is already installed on your machine it will be used instead of charset\_normalizer
  to keep backwards compatibility. (#5797)
  
  You can also install chardet while installing requests by
  specifying [use\_chardet\_on\_py3] extra as follows:
  
  > ``shell
  > pip install "requests[use_chardet_on_py3]"
  > ``
  
  Python2 still depends upon the chardet module.
* Requests now supports idna 3.x on Python 3. idna 2.x will continue to
  be used on Python 2 installations. (#5711)

**Deprecations**

* The requests[security] extra has been converted to a no-op install.
  PyOpenSSL is no longer the recommended secure option for Requests. (#5867)
* Requests has officially dropped support for Python 3.5. (#5867)

## 2.25.1 (2020-12-16)[¶](#id14 "Link to this heading")

**Bugfixes**

* Requests now treats application/json as utf8 by default. Resolving
  inconsistencies between r.text and r.json output. (#5673)

**Dependencies**

* Requests now supports chardet v4.x.

## 2.25.0 (2020-11-11)[¶](#id15 "Link to this heading")

**Improvements**

* Added support for NETRC environment variable. (#5643)

**Dependencies**

* Requests now supports urllib3 v1.26.

**Deprecations**

* Requests v2.25.x will be the last release series with support for Python 3.5.
* The requests[security] extra is officially deprecated and will be removed
  in Requests v2.26.0.

## 2.24.0 (2020-06-17)[¶](#id16 "Link to this heading")

**Improvements**

* pyOpenSSL TLS implementation is now only used if Python
  either doesn’t have an ssl module or doesn’t support
  SNI. Previously pyOpenSSL was unconditionally used if available.
  This applies even if pyOpenSSL is installed via the
  requests[security] extra (#5443)
* Redirect resolution should now only occur when
  allow\_redirects is True. (#5492)
* No longer perform unnecessary Content-Length calculation for
  requests that won’t use it. (#5496)

## 2.23.0 (2020-02-19)[¶](#id17 "Link to this heading")

**Improvements**

* Remove defunct reference to prefetch in Session \_\_attrs\_\_ (#5110)

**Bugfixes**

* Requests no longer outputs password in basic auth usage warning. (#5099)

**Dependencies**

* Pinning for chardet and idna now uses major version instead of minor.
  This hopefully reduces the need for releases every time a dependency is updated.

## 2.22.0 (2019-05-15)[¶](#id18 "Link to this heading")

**Dependencies**

* Requests now supports urllib3 v1.25.2.
  (note: 1.25.0 and 1.25.1 are incompatible)

**Deprecations**

* Requests has officially stopped support for Python 3.4.

## 2.21.0 (2018-12-10)[¶](#id19 "Link to this heading")

**Dependencies**

* Requests now supports idna v2.8.

## 2.20.1 (2018-11-08)[¶](#id20 "Link to this heading")

**Bugfixes**

* Fixed bug with unintended Authorization header stripping for
  redirects using default ports (http/80, https/443).

## 2.20.0 (2018-10-18)[¶](#id21 "Link to this heading")

**Bugfixes**

* Content-Type header parsing is now case-insensitive (e.g.
  charset=utf8 v Charset=utf8).
* Fixed exception leak where certain redirect urls would raise
  uncaught urllib3 exceptions.
* Requests removes Authorization header from requests redirected
  from https to http on the same hostname. (CVE-2018-18074)
* should\_bypass\_proxies now handles URIs without hostnames (e.g.
  files).

**Dependencies**

* Requests now supports urllib3 v1.24.

**Deprecations**

* Requests has officially stopped support for Python 2.6.

## 2.19.1 (2018-06-14)[¶](#id22 "Link to this heading")

**Bugfixes**

* Fixed issue where status\_codes.py’s init function failed trying
  to append to a \_\_doc\_\_ value of None.

## 2.19.0 (2018-06-12)[¶](#id23 "Link to this heading")

**Improvements**

* Warn user about possible slowdown when using cryptography version
  &lt; 1.3.4
* Check for invalid host in proxy URL, before forwarding request to
  adapter.
* Fragments are now properly maintained across redirects. (RFC7231
  7.1.2)
* Removed use of cgi module to expedite library load time.
* Added support for SHA-256 and SHA-512 digest auth algorithms.
* Minor performance improvement to Request.content.
* Migrate to using collections.abc for 3.7 compatibility.

**Bugfixes**

* Parsing empty Link headers with parse\_header\_links() no longer
  return one bogus entry.
* Fixed issue where loading the default certificate bundle from a zip
  archive would raise an IOError.
* Fixed issue with unexpected ImportError on windows system which do
  not support winreg module.
* DNS resolution in proxy bypass no longer includes the username and
  password in the request. This also fixes the issue of DNS queries
  failing on macOS.
* Properly normalize adapter prefixes for url comparison.
* Passing None as a file pointer to the files param no longer
  raises an exception.
* Calling copy on a RequestsCookieJar will now preserve the cookie
  policy correctly.

**Dependencies**

* We now support idna v2.7.
* We now support urllib3 v1.23.

## 2.18.4 (2017-08-15)[¶](#id24 "Link to this heading")

**Improvements**

* Error messages for invalid headers now include the header name for
  easier debugging

**Dependencies**

* We now support idna v2.6.

## 2.18.3 (2017-08-02)[¶](#id25 "Link to this heading")

**Improvements**

* Running $ python -m requests.help now includes the installed
  version of idna.

**Bugfixes**

* Fixed issue where Requests would raise ConnectionError instead of
  SSLError when encountering SSL problems when using urllib3 v1.22.

## 2.18.2 (2017-07-25)[¶](#id26 "Link to this heading")

**Bugfixes**

* requests.help no longer fails on Python 2.6 due to the absence of
  ssl.OPENSSL\_VERSION\_NUMBER.

**Dependencies**

* We now support urllib3 v1.22.

## 2.18.1 (2017-06-14)[¶](#id27 "Link to this heading")

**Bugfixes**

* Fix an error in the packaging whereby the \*.whl contained
  incorrect data that regressed the fix in v2.17.3.

## 2.18.0 (2017-06-14)[¶](#id28 "Link to this heading")

**Improvements**

* Response is now a context manager, so can be used directly in a
  with statement without first having to be wrapped by
  contextlib.closing().

**Bugfixes**

* Resolve installation failure if multiprocessing is not available
* Resolve tests crash if multiprocessing is not able to determine the
  number of CPU cores
* Resolve error swallowing in utils set\_environ generator

## 2.17.3 (2017-05-29)[¶](#id29 "Link to this heading")

**Improvements**

* Improved packages namespace identity support, for monkeypatching
  libraries.

## 2.17.2 (2017-05-29)[¶](#id30 "Link to this heading")

**Improvements**

* Improved packages namespace identity support, for monkeypatching
  libraries.

## 2.17.1 (2017-05-29)[¶](#id31 "Link to this heading")

**Improvements**

* Improved packages namespace identity support, for monkeypatching
  libraries.

## 2.17.0 (2017-05-29)[¶](#id32 "Link to this heading")

**Improvements**

* Removal of the 301 redirect cache. This improves thread-safety.

## 2.16.5 (2017-05-28)[¶](#id33 "Link to this heading")

* Improvements to $ python -m requests.help.

## 2.16.4 (2017-05-27)[¶](#id34 "Link to this heading")

* Introduction of the $ python -m requests.help command, for
  debugging with maintainers!

## 2.16.3 (2017-05-27)[¶](#id35 "Link to this heading")

* Further restored the requests.packages namespace for compatibility
  reasons.

## 2.16.2 (2017-05-27)[¶](#id36 "Link to this heading")

* Further restored the requests.packages namespace for compatibility
  reasons.

No code modification (noted below) should be necessary any longer.


## 2.16.1 (2017-05-27)[¶](#id37 "Link to this heading")

* Restored the requests.packages namespace for compatibility
  reasons.
* Bugfix for urllib3 version parsing.

**Note**: code that was written to import against the
requests.packages namespace previously will have to import code that
rests at this module-level now.

For example:

> from requests.packages.urllib3.poolmanager import PoolManager

Will need to be re-written to be:

> from requests.packages import urllib3
> urllib3.poolmanager.PoolManager

Or, even better:

> from urllib3.poolmanager import PoolManager


## 2.16.0 (2017-05-26)[¶](#id38 "Link to this heading")

* Unvendor ALL the things!

## 2.15.1 (2017-05-26)[¶](#id39 "Link to this heading")

* Everyone makes mistakes.

## 2.15.0 (2017-05-26)[¶](#id40 "Link to this heading")

**Improvements**

* Introduction of the Response.next property, for getting the next
  PreparedResponse from a redirect chain (when
  allow\_redirects=False).
* Internal refactoring of \_\_version\_\_ module.

**Bugfixes**

* Restored once-optional parameter for
  requests.utils.get\_environ\_proxies().

## 2.14.2 (2017-05-10)[¶](#id41 "Link to this heading")

**Bugfixes**

* Changed a less-than to an equal-to and an or in the dependency
  markers to widen compatibility with older setuptools releases.

## 2.14.1 (2017-05-09)[¶](#id42 "Link to this heading")

**Bugfixes**

* Changed the dependency markers to widen compatibility with older pip
  releases.

## 2.14.0 (2017-05-09)[¶](#id43 "Link to this heading")

**Improvements**

* It is now possible to pass no\_proxy as a key to the proxies
  dictionary to provide handling similar to the NO\_PROXY environment
  variable.
* When users provide invalid paths to certificate bundle files or
  directories Requests now raises IOError, rather than failing at
  the time of the HTTPS request with a fairly inscrutable certificate
  validation error.
* The behavior of SessionRedirectMixin was slightly altered.
  resolve\_redirects will now detect a redirect by calling
  get\_redirect\_target(response) instead of directly querying
  Response.is\_redirect and Response.headers[‘location’]. Advanced
  users will be able to process malformed redirects more easily.
* Changed the internal calculation of elapsed request time to have
  higher resolution on Windows.
* Added win\_inet\_pton as conditional dependency for the [socks]
  extra on Windows with Python 2.7.
* Changed the proxy bypass implementation on Windows: the proxy bypass
  check doesn’t use forward and reverse DNS requests anymore
* URLs with schemes that begin with http but are not http or
  https no longer have their host parts forced to lowercase.

**Bugfixes**

* Much improved handling of non-ASCII Location header values in
  redirects. Fewer UnicodeDecodeErrors are encountered on Python 2,
  and Python 3 now correctly understands that Latin-1 is unlikely to
  be the correct encoding.
* If an attempt to seek file to find out its length fails, we now
  appropriately handle that by aborting our content-length
  calculations.
* Restricted HTTPDigestAuth to only respond to auth challenges made
  on 4XX responses, rather than to all auth challenges.
* Fixed some code that was firing DeprecationWarning on Python 3.6.
* The dismayed person emoticon (/o\) no longer has a big head. I’m
  sure this is what you were all worrying about most.

**Miscellaneous**

* Updated bundled urllib3 to v1.21.1.
* Updated bundled chardet to v3.0.2.
* Updated bundled idna to v2.5.
* Updated bundled certifi to 2017.4.17.

## 2.13.0 (2017-01-24)[¶](#id44 "Link to this heading")

**Features**

* Only load the idna library when we’ve determined we need it. This
  will save some memory for users.

**Miscellaneous**

* Updated bundled urllib3 to 1.20.
* Updated bundled idna to 2.2.

## 2.12.5 (2017-01-18)[¶](#id45 "Link to this heading")

**Bugfixes**

* Fixed an issue with JSON encoding detection, specifically detecting
  big-endian UTF-32 with BOM.

## 2.12.4 (2016-12-14)[¶](#id46 "Link to this heading")

**Bugfixes**

* Fixed regression from 2.12.2 where non-string types were rejected in
  the basic auth parameters. While support for this behaviour has been
  re-added, the behaviour is deprecated and will be removed in the
  future.

## 2.12.3 (2016-12-01)[¶](#id47 "Link to this heading")

**Bugfixes**

* Fixed regression from v2.12.1 for URLs with schemes that begin with
  “http”. These URLs have historically been processed as though they
  were HTTP-schemed URLs, and so have had parameters added. This was
  removed in v2.12.2 in an overzealous attempt to resolve problems
  with IDNA-encoding those URLs. This change was reverted: the other
  fixes for IDNA-encoding have been judged to be sufficient to return
  to the behaviour Requests had before v2.12.0.

## 2.12.2 (2016-11-30)[¶](#id48 "Link to this heading")

**Bugfixes**

* Fixed several issues with IDNA-encoding URLs that are technically
  invalid but which are widely accepted. Requests will now attempt to
  IDNA-encode a URL if it can but, if it fails, and the host contains
  only ASCII characters, it will be passed through optimistically.
  This will allow users to opt-in to using IDNA2003 themselves if they
  want to, and will also allow technically invalid but still common
  hostnames.
* Fixed an issue where URLs with leading whitespace would raise
  InvalidSchema errors.
* Fixed an issue where some URLs without the HTTP or HTTPS schemes
  would still have HTTP URL preparation applied to them.
* Fixed an issue where Unicode strings could not be used in basic
  auth.
* Fixed an issue encountered by some Requests plugins where
  constructing a Response object would cause Response.content to
  raise an AttributeError.

## 2.12.1 (2016-11-16)[¶](#id49 "Link to this heading")

**Bugfixes**

* Updated setuptools ‘security’ extra for the new PyOpenSSL backend in
  urllib3.

**Miscellaneous**

* Updated bundled urllib3 to 1.19.1.

## 2.12.0 (2016-11-15)[¶](#id50 "Link to this heading")

**Improvements**

* Updated support for internationalized domain names from IDNA2003 to
  IDNA2008. This updated support is required for several forms of IDNs
  and is mandatory for .de domains.
* Much improved heuristics for guessing content lengths: Requests will
  no longer read an entire StringIO into memory.
* Much improved logic for recalculating Content-Length headers for
  PreparedRequest objects.
* Improved tolerance for file-like objects that have no tell method
  but do have a seek method.
* Anything that is a subclass of Mapping is now treated like a
  dictionary by the data= keyword argument.
* Requests now tolerates empty passwords in proxy credentials, rather
  than stripping the credentials.
* If a request is made with a file-like object as the body and that
  request is redirected with a 307 or 308 status code, Requests will
  now attempt to rewind the body object so it can be replayed.

**Bugfixes**

* When calling response.close, the call to close will be
  propagated through to non-urllib3 backends.
* Fixed issue where the ALL\_PROXY environment variable would be
  preferred over scheme-specific variables like HTTP\_PROXY.
* Fixed issue where non-UTF8 reason phrases got severely mangled by
  falling back to decoding using ISO 8859-1 instead.
* Fixed a bug where Requests would not correctly correlate cookies set
  when using custom Host headers if those Host headers did not use the
  native string type for the platform.

**Miscellaneous**

* Updated bundled urllib3 to 1.19.
* Updated bundled certifi certs to 2016.09.26.

## 2.11.1 (2016-08-17)[¶](#id51 "Link to this heading")

**Bugfixes**

* Fixed a bug when using iter\_content with decode\_unicode=True for
  streamed bodies would raise AttributeError. This bug was
  introduced in 2.11.
* Strip Content-Type and Transfer-Encoding headers from the header
  block when following a redirect that transforms the verb from
  POST/PUT to GET.

## 2.11.0 (2016-08-08)[¶](#id52 "Link to this heading")

**Improvements**

* Added support for the ALL\_PROXY environment variable.
* Reject header values that contain leading whitespace or newline
  characters to reduce risk of header smuggling.

**Bugfixes**

* Fixed occasional TypeError when attempting to decode a JSON
  response that occurred in an error case. Now correctly returns a
  ValueError.
* Requests would incorrectly ignore a non-CIDR IP address in the
  NO\_PROXY environment variables: Requests now treats it as a
  specific IP.
* Fixed a bug when sending JSON data that could cause us to encounter
  obscure OpenSSL errors in certain network conditions (yes, really).
* Added type checks to ensure that iter\_content only accepts
  integers and None for chunk sizes.
* Fixed issue where responses whose body had not been fully consumed
  would have the underlying connection closed but not returned to the
  connection pool, which could cause Requests to hang in situations
  where the HTTPAdapter had been configured to use a blocking
  connection pool.

**Miscellaneous**

* Updated bundled urllib3 to 1.16.
* Some previous releases accidentally accepted non-strings as
  acceptable header values. This release does not.

## 2.10.0 (2016-04-29)[¶](#id53 "Link to this heading")

**New Features**

* SOCKS Proxy Support! (requires PySocks;
  $ pip install requests[socks])

**Miscellaneous**

* Updated bundled urllib3 to 1.15.1.

## 2.9.2 (2016-04-29)[¶](#id54 "Link to this heading")

**Improvements**

* Change built-in CaseInsensitiveDict (used for headers) to use
  OrderedDict as its underlying datastore.

**Bugfixes**

* Don’t use redirect\_cache if allow\_redirects=False
* When passed objects that throw exceptions from tell(), send them
  via chunked transfer encoding instead of failing.
* Raise a ProxyError for proxy related connection issues.

## 2.9.1 (2015-12-21)[¶](#id55 "Link to this heading")

**Bugfixes**

* Resolve regression introduced in 2.9.0 that made it impossible to
  send binary strings as bodies in Python 3.
* Fixed errors when calculating cookie expiration dates in certain
  locales.

**Miscellaneous**

* Updated bundled urllib3 to 1.13.1.

## 2.9.0 (2015-12-15)[¶](#id56 "Link to this heading")

**Minor Improvements** (Backwards compatible)

* The verify keyword argument now supports being passed a path to a
  directory of CA certificates, not just a single-file bundle.
* Warnings are now emitted when sending files opened in text mode.
* Added the 511 Network Authentication Required status code to the
  status code registry.

**Bugfixes**

* For file-like objects that are not sought to the very beginning, we
  now send the content length for the number of bytes we will actually
  read, rather than the total size of the file, allowing partial file
  uploads.
* When uploading file-like objects, if they are empty or have no
  obvious content length we set Transfer-Encoding: chunked rather
  than Content-Length: 0.
* We correctly receive the response in buffered mode when uploading
  chunked bodies.
* We now handle being passed a query string as a bytestring on Python
  3, by decoding it as UTF-8.
* Sessions are now closed in all cases (exceptional and not) when
  using the functional API rather than leaking and waiting for the
  garbage collector to clean them up.
* Correctly handle digest auth headers with a malformed qop
  directive that contains no token, by treating it the same as if no
  qop directive was provided at all.
* Minor performance improvements when removing specific cookies by
  name.

**Miscellaneous**

* Updated urllib3 to 1.13.

## 2.8.1 (2015-10-13)[¶](#id57 "Link to this heading")

**Bugfixes**

* Update certificate bundle to match certifi 2015.9.6.2’s weak
  certificate bundle.
* Fix a bug in 2.8.0 where requests would raise ConnectTimeout
  instead of ConnectionError
* When using the PreparedRequest flow, requests will now correctly
  respect the json parameter. Broken in 2.8.0.
* When using the PreparedRequest flow, requests will now correctly
  handle a Unicode-string method name on Python 2. Broken in 2.8.0.

## 2.8.0 (2015-10-05)[¶](#id58 "Link to this heading")

**Minor Improvements** (Backwards Compatible)

* Requests now supports per-host proxies. This allows the proxies
  dictionary to have entries of the form
  {‘<scheme>://<hostname>’: ‘<proxy>’}. Host-specific proxies will
  be used in preference to the previously-supported scheme-specific
  ones, but the previous syntax will continue to work.
* Response.raise\_for\_status now prints the URL that failed as part
  of the exception message.
* requests.utils.get\_netrc\_auth now takes an raise\_errors kwarg,
  defaulting to False. When True, errors parsing .netrc files
  cause exceptions to be thrown.
* Change to bundled projects import logic to make it easier to
  unbundle requests downstream.
* Changed the default User-Agent string to avoid leaking data on
  Linux: now contains only the requests version.

**Bugfixes**

* The json parameter to post() and friends will now only be used
  if neither data nor files are present, consistent with the
  documentation.
* We now ignore empty fields in the NO\_PROXY environment variable.
* Fixed problem where httplib.BadStatusLine would get raised if
  combining stream=True with contextlib.closing.
* Prevented bugs where we would attempt to return the same connection
  back to the connection pool twice when sending a Chunked body.
* Miscellaneous minor internal changes.
* Digest Auth support is now thread safe.

**Updates**

* Updated urllib3 to 1.12.

## 2.7.0 (2015-05-03)[¶](#id59 "Link to this heading")

This is the first release that follows our new release process. For
more, see [our
documentation](<https://requests.readthedocs.io/en/latest/community/release-process/>).

**Bugfixes**

* Updated urllib3 to 1.10.4, resolving several bugs involving chunked
  transfer encoding and response framing.

## 2.6.2 (2015-04-23)[¶](#id60 "Link to this heading")

**Bugfixes**

* Fix regression where compressed data that was sent as chunked data
  was not properly decompressed. (#2561)

## 2.6.1 (2015-04-22)[¶](#id61 "Link to this heading")

**Bugfixes**

* Remove VendorAlias import machinery introduced in v2.5.2.
* Simplify the PreparedRequest.prepare API: We no longer require the
  user to pass an empty list to the hooks keyword argument. (c.f.
  #2552)
* Resolve redirects now receives and forwards all of the original
  arguments to the adapter. (#2503)
* Handle UnicodeDecodeErrors when trying to deal with a unicode URL
  that cannot be encoded in ASCII. (#2540)
* Populate the parsed path of the URI field when performing Digest
  Authentication. (#2426)
* Copy a PreparedRequest’s CookieJar more reliably when it is not an
  instance of RequestsCookieJar. (#2527)

## 2.6.0 (2015-03-14)[¶](#id62 "Link to this heading")

**Bugfixes**

* CVE-2015-2296: Fix handling of cookies on redirect. Previously a
  cookie without a host value set would use the hostname for the
  redirected URL exposing requests users to session fixation attacks
  and potentially cookie stealing. This was disclosed privately by
  Matthew Daley of [BugFuzz](<https://bugfuzz.com>). This affects all
  versions of requests from v2.1.0 to v2.5.3 (inclusive on both ends).
* Fix error when requests is an install\_requires dependency and
  python setup.py test is run. (#2462)
* Fix error when urllib3 is unbundled and requests continues to use
  the vendored import location.
* Include fixes to urllib3’s header handling.
* Requests’ handling of unvendored dependencies is now more
  restrictive.

**Features and Improvements**

* Support bytearrays when passed as parameters in the files
  argument. (#2468)
* Avoid data duplication when creating a request with str, bytes,
  or bytearray input to the files argument.

## 2.5.3 (2015-02-24)[¶](#id63 "Link to this heading")

**Bugfixes**

* Revert changes to our vendored certificate bundle. For more context
  see (#2455, #2456, and <<https://bugs.python.org/issue23476>>)

## 2.5.2 (2015-02-23)[¶](#id64 "Link to this heading")

**Features and Improvements**

* Add sha256 fingerprint support.
  ([shazow/urllib3#540](<https://github.com/shazow/urllib3/pull/540>))
* Improve the performance of headers.
  ([shazow/urllib3#544](<https://github.com/shazow/urllib3/pull/544>))

**Bugfixes**

* Copy pip’s import machinery. When downstream redistributors remove
  requests.packages.urllib3 the import machinery will continue to let
  those same symbols work. Example usage in requests’ documentation
  and 3rd-party libraries relying on the vendored copies of urllib3
  will work without having to fallback to the system urllib3.
* Attempt to quote parts of the URL on redirect if unquoting and then
  quoting fails. (#2356)
* Fix filename type check for multipart form-data uploads. (#2411)
* Properly handle the case where a server issuing digest
  authentication challenges provides both auth and auth-int
  qop-values. (#2408)
* Fix a socket leak.
  ([shazow/urllib3#549](<https://github.com/shazow/urllib3/pull/549>))
* Fix multiple Set-Cookie headers properly.
  ([shazow/urllib3#534](<https://github.com/shazow/urllib3/pull/534>))
* Disable the built-in hostname verification.
  ([shazow/urllib3#526](<https://github.com/shazow/urllib3/pull/526>))
* Fix the behaviour of decoding an exhausted stream.
  ([shazow/urllib3#535](<https://github.com/shazow/urllib3/pull/535>))

**Security**

* Pulled in an updated cacert.pem.
* Drop RC4 from the default cipher list.
  ([shazow/urllib3#551](<https://github.com/shazow/urllib3/pull/551>))

## 2.5.1 (2014-12-23)[¶](#id65 "Link to this heading")

**Behavioural Changes**

* Only catch HTTPErrors in raise\_for\_status (#2382)

**Bugfixes**

* Handle LocationParseError from urllib3 (#2344)
* Handle file-like object filenames that are not strings (#2379)
* Unbreak HTTPDigestAuth handler. Allow new nonces to be negotiated
  (#2389)

## 2.5.0 (2014-12-01)[¶](#id66 "Link to this heading")

**Improvements**

* Allow usage of urllib3’s Retry object with HTTPAdapters (#2216)
* The iter\_lines method on a response now accepts a delimiter with
  which to split the content (#2295)

**Behavioural Changes**

* Add deprecation warnings to functions in requests.utils that will be
  removed in 3.0 (#2309)
* Sessions used by the functional API are always closed (#2326)
* Restrict requests to HTTP/1.1 and HTTP/1.0 (stop accepting HTTP/0.9)
  (#2323)

**Bugfixes**

* Only parse the URL once (#2353)
* Allow Content-Length header to always be overridden (#2332)
* Properly handle files in HTTPDigestAuth (#2333)
* Cap redirect\_cache size to prevent memory abuse (#2299)
* Fix HTTPDigestAuth handling of redirects after authenticating
  successfully (#2253)
* Fix crash with custom method parameter to Session.request (#2317)
* Fix how Link headers are parsed using the regular expression library
  (#2271)

**Documentation**

* Add more references for interlinking (#2348)
* Update CSS for theme (#2290)
* Update width of buttons and sidebar (#2289)
* Replace references of Gittip with Gratipay (#2282)
* Add link to changelog in sidebar (#2273)

## 2.4.3 (2014-10-06)[¶](#id67 "Link to this heading")

**Bugfixes**

* Unicode URL improvements for Python 2.
* Re-order JSON param for backwards compat.
* Automatically defrag authentication schemes from host/pass URIs.
  ([#2249](<https://github.com/psf/requests/issues/2249>))

## 2.4.2 (2014-10-05)[¶](#id68 "Link to this heading")

**Improvements**

* FINALLY! Add json parameter for uploads!
  ([#2258](<https://github.com/psf/requests/pull/2258>))
* Support for bytestring URLs on Python 3.x
  ([#2238](<https://github.com/psf/requests/pull/2238>))

**Bugfixes**

* Avoid getting stuck in a loop
  ([#2244](<https://github.com/psf/requests/pull/2244>))
* Multiple calls to iter\* fail with unhelpful error.
  ([#2240](<https://github.com/psf/requests/issues/2240>),
  [#2241](<https://github.com/psf/requests/issues/2241>))

**Documentation**

* Correct redirection introduction
  ([#2245](<https://github.com/psf/requests/pull/2245/>))
* Added example of how to send multiple files in one request.
  ([#2227](<https://github.com/psf/requests/pull/2227/>))
* Clarify how to pass a custom set of CAs
  ([#2248](<https://github.com/psf/requests/pull/2248/>))

## 2.4.1 (2014-09-09)[¶](#id69 "Link to this heading")

* Now has a “security” package extras set,
  $ pip install requests[security]
* Requests will now use Certifi if it is available.
* Capture and re-raise urllib3 ProtocolError
* Bugfix for responses that attempt to redirect to themselves forever
  (wtf?).

## 2.4.0 (2014-08-29)[¶](#id70 "Link to this heading")

**Behavioral Changes**

* Connection: keep-alive header is now sent automatically.

**Improvements**

* Support for connect timeouts! Timeout now accepts a tuple (connect,
  read) which is used to set individual connect and read timeouts.
* Allow copying of PreparedRequests without headers/cookies.
* Updated bundled urllib3 version.
* Refactored settings loading from environment – new
  Session.merge\_environment\_settings.
* Handle socket errors in iter\_content.

## 2.3.0 (2014-05-16)[¶](#id71 "Link to this heading")

**API Changes**

* New Response property is\_redirect, which is true when the
  library could have processed this response as a redirection (whether
  or not it actually did).
* The timeout parameter now affects requests with both stream=True
  and stream=False equally.
* The change in v2.0.0 to mandate explicit proxy schemes has been
  reverted. Proxy schemes now default to http://.
* The CaseInsensitiveDict used for HTTP headers now behaves like a
  normal dictionary when references as string or viewed in the
  interpreter.

**Bugfixes**

* No longer expose Authorization or Proxy-Authorization headers on
  redirect. Fix CVE-2014-1829 and CVE-2014-1830 respectively.
* Authorization is re-evaluated each redirect.
* On redirect, pass url as native strings.
* Fall-back to autodetected encoding for JSON when Unicode detection
  fails.
* Headers set to None on the Session are now correctly not sent.
* Correctly honor decode\_unicode even if it wasn’t used earlier in
  the same response.
* Stop advertising compress as a supported Content-Encoding.
* The Response.history parameter is now always a list.
* Many, many urllib3 bugfixes.

## 2.2.1 (2014-01-23)[¶](#id72 "Link to this heading")

**Bugfixes**

* Fixes incorrect parsing of proxy credentials that contain a literal
  or encoded ‘#’ character.
* Assorted urllib3 fixes.

## 2.2.0 (2014-01-09)[¶](#id73 "Link to this heading")

**API Changes**

* New exception: ContentDecodingError. Raised instead of urllib3
  DecodeError exceptions.

**Bugfixes**

* Avoid many many exceptions from the buggy implementation of
  proxy\_bypass on OS X in Python 2.6.
* Avoid crashing when attempting to get authentication credentials
  from ~/.netrc when running as a user without a home directory.
* Use the correct pool size for pools of connections to proxies.
* Fix iteration of CookieJar objects.
* Ensure that cookies are persisted over redirect.
* Switch back to using chardet, since it has merged with charade.

## 2.1.0 (2013-12-05)[¶](#id74 "Link to this heading")

* Updated CA Bundle, of course.
* Cookies set on individual Requests through a Session (e.g. via
  Session.get()) are no longer persisted to the Session.
* Clean up connections when we hit problems during chunked upload,
  rather than leaking them.
* Return connections to the pool when a chunked upload is successful,
  rather than leaking it.
* Match the HTTPbis recommendation for HTTP 301 redirects.
* Prevent hanging when using streaming uploads and Digest Auth when a
  401 is received.
* Values of headers set by Requests are now always the native string
  type.
* Fix previously broken SNI support.
* Fix accessing HTTP proxies using proxy authentication.
* Unencode HTTP Basic usernames and passwords extracted from URLs.
* Support for IP address ranges for no\_proxy environment variable
* Parse headers correctly when users override the default Host:
  header.
* Avoid munging the URL in case of case-sensitive servers.
* Looser URL handling for non-HTTP/HTTPS urls.
* Accept unicode methods in Python 2.6 and 2.7.
* More resilient cookie handling.
* Make Response objects pickleable.
* Actually added MD5-sess to Digest Auth instead of pretending to like
  last time.
* Updated internal urllib3.
* Fixed @Lukasa’s lack of taste.

## 2.0.1 (2013-10-24)[¶](#id75 "Link to this heading")

* Updated included CA Bundle with new mistrusts and automated process
  for the future
* Added MD5-sess to Digest Auth
* Accept per-file headers in multipart file POST messages.
* Fixed: Don’t send the full URL on CONNECT messages.
* Fixed: Correctly lowercase a redirect scheme.
* Fixed: Cookies not persisted when set via functional API.
* Fixed: Translate urllib3 ProxyError into a requests ProxyError
  derived from ConnectionError.
* Updated internal urllib3 and chardet.

## 2.0.0 (2013-09-24)[¶](#id76 "Link to this heading")

**API Changes:**

* Keys in the Headers dictionary are now native strings on all Python
  versions, i.e. bytestrings on Python 2, unicode on Python 3.
* Proxy URLs now *must* have an explicit scheme. A MissingSchema
  exception will be raised if they don’t.
* Timeouts now apply to read time if Stream=False.
* RequestException is now a subclass of IOError, not
  RuntimeError.
* Added new method to PreparedRequest objects:
  PreparedRequest.copy().
* Added new method to Session objects: Session.update\_request().
  This method updates a Request object with the data (e.g. cookies)
  stored on the Session.
* Added new method to Session objects: Session.prepare\_request().
  This method updates and prepares a Request object, and returns the
  corresponding PreparedRequest object.
* Added new method to HTTPAdapter objects:
  HTTPAdapter.proxy\_headers(). This should not be called directly,
  but improves the subclass interface.
* httplib.IncompleteRead exceptions caused by incorrect chunked
  encoding will now raise a Requests ChunkedEncodingError instead.
* Invalid percent-escape sequences now cause a Requests InvalidURL
  exception to be raised.
* HTTP 208 no longer uses reason phrase “im\_used”. Correctly uses
  “already\_reported”.
* HTTP 226 reason added (“im\_used”).

**Bugfixes:**

* Vastly improved proxy support, including the CONNECT verb. Special
  thanks to the many contributors who worked towards this improvement.
* Cookies are now properly managed when 401 authentication responses
  are received.
* Chunked encoding fixes.
* Support for mixed case schemes.
* Better handling of streaming downloads.
* Retrieve environment proxies from more locations.
* Minor cookies fixes.
* Improved redirect behaviour.
* Improved streaming behaviour, particularly for compressed data.
* Miscellaneous small Python 3 text encoding bugs.
* .netrc no longer overrides explicit auth.
* Cookies set by hooks are now correctly persisted on Sessions.
* Fix problem with cookies that specify port numbers in their host
  field.
* BytesIO can be used to perform streaming uploads.
* More generous parsing of the no\_proxy environment variable.
* Non-string objects can be passed in data values alongside files.

## 1.2.3 (2013-05-25)[¶](#id77 "Link to this heading")

* Simple packaging fix

## 1.2.2 (2013-05-23)[¶](#id78 "Link to this heading")

* Simple packaging fix

## 1.2.1 (2013-05-20)[¶](#id79 "Link to this heading")

* 301 and 302 redirects now change the verb to GET for all verbs, not
  just POST, improving browser compatibility.
* Python 3.3.2 compatibility
* Always percent-encode location headers
* Fix connection adapter matching to be most-specific first
* new argument to the default connection adapter for passing a block
  argument
* prevent a KeyError when there’s no link headers

## 1.2.0 (2013-03-31)[¶](#id80 "Link to this heading")

* Fixed cookies on sessions and on requests
* Significantly change how hooks are dispatched - hooks now receive
  all the arguments specified by the user when making a request so
  hooks can make a secondary request with the same parameters. This is
  especially necessary for authentication handler authors
* certifi support was removed
* Fixed bug where using OAuth 1 with body signature\_type sent no
  data
* Major proxy work thanks to @Lukasa including parsing of proxy
  authentication from the proxy url
* Fix DigestAuth handling too many 401s
* Update vendored urllib3 to include SSL bug fixes
* Allow keyword arguments to be passed to json.loads() via the
  Response.json() method
* Don’t send Content-Length header by default on GET or HEAD
  requests
* Add elapsed attribute to Response objects to time how long a
  request took.
* Fix RequestsCookieJar
* Sessions and Adapters are now picklable, i.e., can be used with the
  multiprocessing library
* Update charade to version 1.0.3

The change in how hooks are dispatched will likely cause a great deal of
issues.


## 1.1.0 (2013-01-10)[¶](#id81 "Link to this heading")

* CHUNKED REQUESTS
* Support for iterable response bodies
* Assume servers persist redirect params
* Allow explicit content types to be specified for file data
* Make merge\_kwargs case-insensitive when looking up keys

## 1.0.3 (2012-12-18)[¶](#id82 "Link to this heading")

* Fix file upload encoding bug
* Fix cookie behavior

## 1.0.2 (2012-12-17)[¶](#id83 "Link to this heading")

* Proxy fix for HTTPAdapter.

## 1.0.1 (2012-12-17)[¶](#id84 "Link to this heading")

* Cert verification exception bug.
* Proxy fix for HTTPAdapter.

## 1.0.0 (2012-12-17)[¶](#id85 "Link to this heading")

* Massive Refactor and Simplification
* Switch to Apache 2.0 license
* Swappable Connection Adapters
* Mountable Connection Adapters
* Mutable ProcessedRequest chain
* /s/prefetch/stream
* Removal of all configuration
* Standard library logging
* Make Response.json() callable, not property.
* Usage of new charade project, which provides python 2 and 3
  simultaneous chardet.
* Removal of all hooks except ‘response’
* Removal of all authentication helpers (OAuth, Kerberos)

This is not a backwards compatible change.


## 0.14.2 (2012-10-27)[¶](#id86 "Link to this heading")

* Improved mime-compatible JSON handling
* Proxy fixes
* Path hack fixes
* Case-Insensitive Content-Encoding headers
* Support for CJK parameters in form posts

## 0.14.1 (2012-10-01)[¶](#id87 "Link to this heading")

* Python 3.3 Compatibility
* Simply default accept-encoding
* Bugfixes

## 0.14.0 (2012-09-02)[¶](#id88 "Link to this heading")

* No more iter\_content errors if already downloaded.

## 0.13.9 (2012-08-25)[¶](#id89 "Link to this heading")

* Fix for OAuth + POSTs
* Remove exception eating from dispatch\_hook
* General bugfixes

## 0.13.8 (2012-08-21)[¶](#id90 "Link to this heading")

* Incredible Link header support :)

## 0.13.7 (2012-08-19)[¶](#id91 "Link to this heading")

* Support for (key, value) lists everywhere.
* Digest Authentication improvements.
* Ensure proxy exclusions work properly.
* Clearer UnicodeError exceptions.
* Automatic casting of URLs to strings (fURL and such)
* Bugfixes.

## 0.13.6 (2012-08-06)[¶](#id92 "Link to this heading")

* Long awaited fix for hanging connections!

## 0.13.5 (2012-07-27)[¶](#id93 "Link to this heading")

* Packaging fix

## 0.13.4 (2012-07-27)[¶](#id94 "Link to this heading")

* GSSAPI/Kerberos authentication!
* App Engine 2.7 Fixes!
* Fix leaking connections (from urllib3 update)
* OAuthlib path hack fix
* OAuthlib URL parameters fix.

## 0.13.3 (2012-07-12)[¶](#id95 "Link to this heading")

* Use simplejson if available.
* Do not hide SSLErrors behind Timeouts.
* Fixed param handling with urls containing fragments.
* Significantly improved information in User Agent.
* client certificates are ignored when verify=False

## 0.13.2 (2012-06-28)[¶](#id96 "Link to this heading")

* Zero dependencies (once again)!
* New: Response.reason
* Sign querystring parameters in OAuth 1.0
* Client certificates no longer ignored when verify=False
* Add openSUSE certificate support

## 0.13.1 (2012-06-07)[¶](#id97 "Link to this heading")

* Allow passing a file or file-like object as data.
* Allow hooks to return responses that indicate errors.
* Fix Response.text and Response.json for body-less responses.

## 0.13.0 (2012-05-29)[¶](#id98 "Link to this heading")

* Removal of Requests.async in favor of
  [grequests](<https://github.com/kennethreitz/grequests>)
* Allow disabling of cookie persistence.
* New implementation of safe\_mode
* cookies.get now supports default argument
* Session cookies not saved when Session.request is called with
  return\_response=False
* Env: no\_proxy support.
* RequestsCookieJar improvements.
* Various bug fixes.

## 0.12.1 (2012-05-08)[¶](#id99 "Link to this heading")

* New Response.json property.
* Ability to add string file uploads.
* Fix out-of-range issue with iter\_lines.
* Fix iter\_content default size.
* Fix POST redirects containing files.

## 0.12.0 (2012-05-02)[¶](#id100 "Link to this heading")

* EXPERIMENTAL OAUTH SUPPORT!
* Proper CookieJar-backed cookies interface with awesome dict-like
  interface.
* Speed fix for non-iterated content chunks.
* Move pre\_request to a more usable place.
* New pre\_send hook.
* Lazily encode data, params, files.
* Load system Certificate Bundle if certify isn’t available.
* Cleanups, fixes.

## 0.11.2 (2012-04-22)[¶](#id101 "Link to this heading")

* Attempt to use the OS’s certificate bundle if certifi isn’t
  available.
* Infinite digest auth redirect fix.
* Multi-part file upload improvements.
* Fix decoding of invalid %encodings in URLs.
* If there is no content in a response don’t throw an error the second
  time that content is attempted to be read.
* Upload data on redirects.

## 0.11.1 (2012-03-30)[¶](#id102 "Link to this heading")

* POST redirects now break RFC to do what browsers do: Follow up with
  a GET.
* New strict\_mode configuration to disable new redirect behavior.

## 0.11.0 (2012-03-14)[¶](#id103 "Link to this heading")

* Private SSL Certificate support
* Remove select.poll from Gevent monkeypatching
* Remove redundant generator for chunked transfer encoding
* Fix: Response.ok raises Timeout Exception in safe\_mode

## 0.10.8 (2012-03-09)[¶](#id104 "Link to this heading")

* Generate chunked ValueError fix
* Proxy configuration by environment variables
* Simplification of iter\_lines.
* New trust\_env configuration for disabling system/environment hints.
* Suppress cookie errors.

## 0.10.7 (2012-03-07)[¶](#id105 "Link to this heading")

* encode\_uri = False

## 0.10.6 (2012-02-25)[¶](#id106 "Link to this heading")

* Allow ‘=’ in cookies.

## 0.10.5 (2012-02-25)[¶](#id107 "Link to this heading")

* Response body with 0 content-length fix.
* New async.imap.
* Don’t fail on netrc.

## 0.10.4 (2012-02-20)[¶](#id108 "Link to this heading")

* Honor netrc.

## 0.10.3 (2012-02-20)[¶](#id109 "Link to this heading")

* HEAD requests don’t follow redirects anymore.
* raise\_for\_status() doesn’t raise for 3xx anymore.
* Make Session objects picklable.
* ValueError for invalid schema URLs.

## 0.10.2 (2012-01-15)[¶](#id110 "Link to this heading")

* Vastly improved URL quoting.
* Additional allowed cookie key values.
* Attempted fix for “Too many open files” Error
* Replace unicode errors on first pass, no need for second pass.
* Append ‘/’ to bare-domain urls before query insertion.
* Exceptions now inherit from RuntimeError.
* Binary uploads + auth fix.
* Bugfixes.

## 0.10.1 (2012-01-23)[¶](#id111 "Link to this heading")

* PYTHON 3 SUPPORT!
* Dropped 2.5 Support. (*Backwards Incompatible*)

## 0.10.0 (2012-01-21)[¶](#id112 "Link to this heading")

* Response.content is now bytes-only. (*Backwards Incompatible*)
* New Response.text is unicode-only.
* If no Response.encoding is specified and chardet is available,
  Response.text will guess an encoding.
* Default to ISO-8859-1 (Western) encoding for “text” subtypes.
* Removal of decode\_unicode. (*Backwards Incompatible*)
* New multiple-hooks system.
* New Response.register\_hook for registering hooks within the
  pipeline.
* Response.url is now Unicode.

## 0.9.3 (2012-01-18)[¶](#id113 "Link to this heading")

* SSL verify=False bugfix (apparent on windows machines).

## 0.9.2 (2012-01-18)[¶](#id114 "Link to this heading")

* Asynchronous async.send method.
* Support for proper chunk streams with boundaries.
* session argument for Session classes.
* Print entire hook tracebacks, not just exception instance.
* Fix response.iter\_lines from pending next line.
* Fix but in HTTP-digest auth w/ URI having query strings.
* Fix in Event Hooks section.
* Urllib3 update.

## 0.9.1 (2012-01-06)[¶](#id115 "Link to this heading")

* danger\_mode for automatic Response.raise\_for\_status()
* Response.iter\_lines refactor

## 0.9.0 (2011-12-28)[¶](#id116 "Link to this heading")

* verify ssl is default.

## 0.8.9 (2011-12-28)[¶](#id117 "Link to this heading")

* Packaging fix.

## 0.8.8 (2011-12-28)[¶](#id118 "Link to this heading")

* SSL CERT VERIFICATION!
* Release of Cerifi: Mozilla’s cert list.
* New ‘verify’ argument for SSL requests.
* Urllib3 update.

## 0.8.7 (2011-12-24)[¶](#id119 "Link to this heading")

* iter\_lines last-line truncation fix
* Force safe\_mode for async requests
* Handle safe\_mode exceptions more consistently
* Fix iteration on null responses in safe\_mode

## 0.8.6 (2011-12-18)[¶](#id120 "Link to this heading")

* Socket timeout fixes.
* Proxy Authorization support.

## 0.8.5 (2011-12-14)[¶](#id121 "Link to this heading")

* Response.iter\_lines!

## 0.8.4 (2011-12-11)[¶](#id122 "Link to this heading")

* Prefetch bugfix.
* Added license to installed version.

## 0.8.3 (2011-11-27)[¶](#id123 "Link to this heading")

* Converted auth system to use simpler callable objects.
* New session parameter to API methods.
* Display full URL while logging.

## 0.8.2 (2011-11-19)[¶](#id124 "Link to this heading")

* New Unicode decoding system, based on over-ridable
  Response.encoding.
* Proper URL slash-quote handling.
* Cookies with [, ], and \_ allowed.

## 0.8.1 (2011-11-15)[¶](#id125 "Link to this heading")

* URL Request path fix
* Proxy fix.
* Timeouts fix.

## 0.8.0 (2011-11-13)[¶](#id126 "Link to this heading")

* Keep-alive support!
* Complete removal of Urllib2
* Complete removal of Poster
* Complete removal of CookieJars
* New ConnectionError raising
* Safe\_mode for error catching
* prefetch parameter for request methods
* OPTION method
* Async pool size throttling
* File uploads send real names
* Vendored in urllib3

## 0.7.6 (2011-11-07)[¶](#id127 "Link to this heading")

* Digest authentication bugfix (attach query data to path)

## 0.7.5 (2011-11-04)[¶](#id128 "Link to this heading")

* Response.content = None if there was an invalid response.
* Redirection auth handling.

## 0.7.4 (2011-10-26)[¶](#id129 "Link to this heading")

* Session Hooks fix.

## 0.7.3 (2011-10-23)[¶](#id130 "Link to this heading")

* Digest Auth fix.

## 0.7.2 (2011-10-23)[¶](#id131 "Link to this heading")

* PATCH Fix.

## 0.7.1 (2011-10-23)[¶](#id132 "Link to this heading")

* Move away from urllib2 authentication handling.
* Fully Remove AuthManager, AuthObject, &c.
* New tuple-based auth system with handler callbacks.

## 0.7.0 (2011-10-22)[¶](#id133 "Link to this heading")

* Sessions are now the primary interface.
* Deprecated InvalidMethodException.
* PATCH fix.
* New config system (no more global settings).

## 0.6.6 (2011-10-19)[¶](#id134 "Link to this heading")

* Session parameter bugfix (params merging).

## 0.6.5 (2011-10-18)[¶](#id135 "Link to this heading")

* Offline (fast) test suite.
* Session dictionary argument merging.

## 0.6.4 (2011-10-13)[¶](#id136 "Link to this heading")

* Automatic decoding of unicode, based on HTTP Headers.
* New decode\_unicode setting.
* Removal of r.read/close methods.
* New r.faw interface for advanced response usage.\*
* Automatic expansion of parameterized headers.

## 0.6.3 (2011-10-13)[¶](#id137 "Link to this heading")

* Beautiful requests.async module, for making async requests w/
  gevent.

## 0.6.2 (2011-10-09)[¶](#id138 "Link to this heading")

* GET/HEAD obeys allow\_redirects=False.

## 0.6.1 (2011-08-20)[¶](#id139 "Link to this heading")

* Enhanced status codes experience o/
* Set a maximum number of redirects (settings.max\_redirects)
* Full Unicode URL support
* Support for protocol-less redirects.
* Allow for arbitrary request types.
* Bugfixes

## 0.6.0 (2011-08-17)[¶](#id140 "Link to this heading")

* New callback hook system
* New persistent sessions object and context manager
* Transparent Dict-cookie handling
* Status code reference object
* Removed Response.cached
* Added Response.request
* All args are kwargs
* Relative redirect support
* HTTPError handling improvements
* Improved https testing
* Bugfixes

## 0.5.1 (2011-07-23)[¶](#id141 "Link to this heading")

* International Domain Name Support!
* Access headers without fetching entire body (read())
* Use lists as dicts for parameters
* Add Forced Basic Authentication
* Forced Basic is default authentication type
* python-requests.org default User-Agent header
* CaseInsensitiveDict lower-case caching
* Response.history bugfix

## 0.5.0 (2011-06-21)[¶](#id142 "Link to this heading")

* PATCH Support
* Support for Proxies
* HTTPBin Test Suite
* Redirect Fixes
* settings.verbose stream writing
* Querystrings for all methods
* URLErrors (Connection Refused, Timeout, Invalid URLs) are treated as
  explicitly raised
  r.requests.get(‘hwe://blah’); r.raise\_for\_status()

## 0.4.1 (2011-05-22)[¶](#id143 "Link to this heading")

* Improved Redirection Handling
* New ‘allow\_redirects’ param for following non-GET/HEAD Redirects
* Settings module refactoring

## 0.4.0 (2011-05-15)[¶](#id144 "Link to this heading")

* Response.history: list of redirected responses
* Case-Insensitive Header Dictionaries!
* Unicode URLs

## 0.3.4 (2011-05-14)[¶](#id145 "Link to this heading")

* Urllib2 HTTPAuthentication Recursion fix (Basic/Digest)
* Internal Refactor
* Bytes data upload Bugfix

## 0.3.3 (2011-05-12)[¶](#id146 "Link to this heading")

* Request timeouts
* Unicode url-encoded data
* Settings context manager and module

## 0.3.2 (2011-04-15)[¶](#id147 "Link to this heading")

* Automatic Decompression of GZip Encoded Content
* AutoAuth Support for Tupled HTTP Auth

## 0.3.1 (2011-04-01)[¶](#id148 "Link to this heading")

* Cookie Changes
* Response.read()
* Poster fix

## 0.3.0 (2011-02-25)[¶](#id149 "Link to this heading")

* Automatic Authentication API Change
* Smarter Query URL Parameterization
* Allow file uploads and POST data together
* New Authentication Manager System
  
  : - Simpler Basic HTTP System
  + Supports all built-in urllib2 Auths
  + Allows for custom Auth Handlers

## 0.2.4 (2011-02-19)[¶](#id150 "Link to this heading")

* Python 2.5 Support
* PyPy-c v1.4 Support
* Auto-Authentication tests
* Improved Request object constructor

## 0.2.3 (2011-02-15)[¶](#id151 "Link to this heading")

* New HTTPHandling Methods
  
  : - Response.\_\_nonzero\_\_ (false if bad HTTP Status)
  + Response.ok (True if expected HTTP Status)
  + Response.error (Logged HTTPError if bad HTTP Status)
  + Response.raise\_for\_status() (Raises stored HTTPError)

## 0.2.2 (2011-02-14)[¶](#id152 "Link to this heading")

* Still handles request in the event of an HTTPError. (Issue #2)
* Eventlet and Gevent Monkeypatch support.
* Cookie Support (Issue #1)

## 0.2.1 (2011-02-14)[¶](#id153 "Link to this heading")

* Added file attribute to POST and PUT requests for multipart-encode
  file uploads.
* Added Request.url attribute for context and redirects

## 0.2.0 (2011-02-14)[¶](#id154 "Link to this heading")

* Birth!

## 0.0.1 (2011-02-13)[¶](#id155 "Link to this heading")

* Frustration
* Conception





Requests is an elegant and simple HTTP library for Python, built for
human beings. You are currently looking at the documentation of the
development release.

### Useful Links

* [Quickstart](../../user/quickstart/)
* [Advanced Usage](../../user/advanced/)
* [API Reference](../../api/)
* [Release History](##release-history)
* [Contributors Guide](../../dev/contributing/)
* [Recommended Packages and Extensions](../recommended/)
* [Requests @ GitHub](https://github.com/psf/requests)
* [Requests @ PyPI](https://pypi.org/project/requests/)
* [Issue Tracker](https://github.com/psf/requests/issues)

### [Table of Contents](../../)

* [Community Updates](#)
  + [GitHub](#github)
* [Release History](#release-history)
  + [dev](#dev)
  + [2.32.3 (2024-05-29)](#id1)
  + [2.32.2 (2024-05-21)](#id2)
  + [2.32.1 (2024-05-20)](#id3)
  + [2.32.0 (2024-05-20)](#id4)
  + [2.31.0 (2023-05-22)](#id5)
  + [2.30.0 (2023-05-03)](#id6)
  + [2.29.0 (2023-04-26)](#id7)
  + [2.28.2 (2023-01-12)](#id8)
  + [2.28.1 (2022-06-29)](#id9)
  + [2.28.0 (2022-06-09)](#id10)
  + [2.27.1 (2022-01-05)](#id11)
  + [2.27.0 (2022-01-03)](#id12)
  + [2.26.0 (2021-07-13)](#id13)
  + [2.25.1 (2020-12-16)](#id14)
  + [2.25.0 (2020-11-11)](#id15)
  + [2.24.0 (2020-06-17)](#id16)
  + [2.23.0 (2020-02-19)](#id17)
  + [2.22.0 (2019-05-15)](#id18)
  + [2.21.0 (2018-12-10)](#id19)
  + [2.20.1 (2018-11-08)](#id20)
  + [2.20.0 (2018-10-18)](#id21)
  + [2.19.1 (2018-06-14)](#id22)
  + [2.19.0 (2018-06-12)](#id23)
  + [2.18.4 (2017-08-15)](#id24)
  + [2.18.3 (2017-08-02)](#id25)
  + [2.18.2 (2017-07-25)](#id26)
  + [2.18.1 (2017-06-14)](#id27)
  + [2.18.0 (2017-06-14)](#id28)
  + [2.17.3 (2017-05-29)](#id29)
  + [2.17.2 (2017-05-29)](#id30)
  + [2.17.1 (2017-05-29)](#id31)
  + [2.17.0 (2017-05-29)](#id32)
  + [2.16.5 (2017-05-28)](#id33)
  + [2.16.4 (2017-05-27)](#id34)
  + [2.16.3 (2017-05-27)](#id35)
  + [2.16.2 (2017-05-27)](#id36)
  + [2.16.1 (2017-05-27)](#id37)
  + [2.16.0 (2017-05-26)](#id38)
  + [2.15.1 (2017-05-26)](#id39)
  + [2.15.0 (2017-05-26)](#id40)
  + [2.14.2 (2017-05-10)](#id41)
  + [2.14.1 (2017-05-09)](#id42)
  + [2.14.0 (2017-05-09)](#id43)
  + [2.13.0 (2017-01-24)](#id44)
  + [2.12.5 (2017-01-18)](#id45)
  + [2.12.4 (2016-12-14)](#id46)
  + [2.12.3 (2016-12-01)](#id47)
  + [2.12.2 (2016-11-30)](#id48)
  + [2.12.1 (2016-11-16)](#id49)
  + [2.12.0 (2016-11-15)](#id50)
  + [2.11.1 (2016-08-17)](#id51)
  + [2.11.0 (2016-08-08)](#id52)
  + [2.10.0 (2016-04-29)](#id53)
  + [2.9.2 (2016-04-29)](#id54)
  + [2.9.1 (2015-12-21)](#id55)
  + [2.9.0 (2015-12-15)](#id56)
  + [2.8.1 (2015-10-13)](#id57)
  + [2.8.0 (2015-10-05)](#id58)
  + [2.7.0 (2015-05-03)](#id59)
  + [2.6.2 (2015-04-23)](#id60)
  + [2.6.1 (2015-04-22)](#id61)
  + [2.6.0 (2015-03-14)](#id62)
  + [2.5.3 (2015-02-24)](#id63)
  + [2.5.2 (2015-02-23)](#id64)
  + [2.5.1 (2014-12-23)](#id65)
  + [2.5.0 (2014-12-01)](#id66)
  + [2.4.3 (2014-10-06)](#id67)
  + [2.4.2 (2014-10-05)](#id68)
  + [2.4.1 (2014-09-09)](#id69)
  + [2.4.0 (2014-08-29)](#id70)
  + [2.3.0 (2014-05-16)](#id71)
  + [2.2.1 (2014-01-23)](#id72)
  + [2.2.0 (2014-01-09)](#id73)
  + [2.1.0 (2013-12-05)](#id74)
  + [2.0.1 (2013-10-24)](#id75)
  + [2.0.0 (2013-09-24)](#id76)
  + [1.2.3 (2013-05-25)](#id77)
  + [1.2.2 (2013-05-23)](#id78)
  + [1.2.1 (2013-05-20)](#id79)
  + [1.2.0 (2013-03-31)](#id80)
  + [1.1.0 (2013-01-10)](#id81)
  + [1.0.3 (2012-12-18)](#id82)
  + [1.0.2 (2012-12-17)](#id83)
  + [1.0.1 (2012-12-17)](#id84)
  + [1.0.0 (2012-12-17)](#id85)
  + [0.14.2 (2012-10-27)](#id86)
  + [0.14.1 (2012-10-01)](#id87)
  + [0.14.0 (2012-09-02)](#id88)
  + [0.13.9 (2012-08-25)](#id89)
  + [0.13.8 (2012-08-21)](#id90)
  + [0.13.7 (2012-08-19)](#id91)
  + [0.13.6 (2012-08-06)](#id92)
  + [0.13.5 (2012-07-27)](#id93)
  + [0.13.4 (2012-07-27)](#id94)
  + [0.13.3 (2012-07-12)](#id95)
  + [0.13.2 (2012-06-28)](#id96)
  + [0.13.1 (2012-06-07)](#id97)
  + [0.13.0 (2012-05-29)](#id98)
  + [0.12.1 (2012-05-08)](#id99)
  + [0.12.0 (2012-05-02)](#id100)
  + [0.11.2 (2012-04-22)](#id101)
  + [0.11.1 (2012-03-30)](#id102)
  + [0.11.0 (2012-03-14)](#id103)
  + [0.10.8 (2012-03-09)](#id104)
  + [0.10.7 (2012-03-07)](#id105)
  + [0.10.6 (2012-02-25)](#id106)
  + [0.10.5 (2012-02-25)](#id107)
  + [0.10.4 (2012-02-20)](#id108)
  + [0.10.3 (2012-02-20)](#id109)
  + [0.10.2 (2012-01-15)](#id110)
  + [0.10.1 (2012-01-23)](#id111)
  + [0.10.0 (2012-01-21)](#id112)
  + [0.9.3 (2012-01-18)](#id113)
  + [0.9.2 (2012-01-18)](#id114)
  + [0.9.1 (2012-01-06)](#id115)
  + [0.9.0 (2011-12-28)](#id116)
  + [0.8.9 (2011-12-28)](#id117)
  + [0.8.8 (2011-12-28)](#id118)
  + [0.8.7 (2011-12-24)](#id119)
  + [0.8.6 (2011-12-18)](#id120)
  + [0.8.5 (2011-12-14)](#id121)
  + [0.8.4 (2011-12-11)](#id122)
  + [0.8.3 (2011-11-27)](#id123)
  + [0.8.2 (2011-11-19)](#id124)
  + [0.8.1 (2011-11-15)](#id125)
  + [0.8.0 (2011-11-13)](#id126)
  + [0.7.6 (2011-11-07)](#id127)
  + [0.7.5 (2011-11-04)](#id128)
  + [0.7.4 (2011-10-26)](#id129)
  + [0.7.3 (2011-10-23)](#id130)
  + [0.7.2 (2011-10-23)](#id131)
  + [0.7.1 (2011-10-23)](#id132)
  + [0.7.0 (2011-10-22)](#id133)
  + [0.6.6 (2011-10-19)](#id134)
  + [0.6.5 (2011-10-18)](#id135)
  + [0.6.4 (2011-10-13)](#id136)
  + [0.6.3 (2011-10-13)](#id137)
  + [0.6.2 (2011-10-09)](#id138)
  + [0.6.1 (2011-08-20)](#id139)
  + [0.6.0 (2011-08-17)](#id140)
  + [0.5.1 (2011-07-23)](#id141)
  + [0.5.0 (2011-06-21)](#id142)
  + [0.4.1 (2011-05-22)](#id143)
  + [0.4.0 (2011-05-15)](#id144)
  + [0.3.4 (2011-05-14)](#id145)
  + [0.3.3 (2011-05-12)](#id146)
  + [0.3.2 (2011-04-15)](#id147)
  + [0.3.1 (2011-04-01)](#id148)
  + [0.3.0 (2011-02-25)](#id149)
  + [0.2.4 (2011-02-19)](#id150)
  + [0.2.3 (2011-02-15)](#id151)
  + [0.2.2 (2011-02-14)](#id152)
  + [0.2.1 (2011-02-14)](#id153)
  + [0.2.0 (2011-02-14)](#id154)
  + [0.0.1 (2011-02-13)](#id155)
### Related Topics

* [Documentation overview](../../)
  + Previous: [Release Process and Rules](../release-process/ "previous chapter")
  + Next: [Developer Interface](../../api/ "next chapter")

### Quick search








©MMXVIX. A Kenneth Reitz Project.

[![Fork me on GitHub](https://github.blog/wp-content/uploads/2008/12/forkme_right_darkblue_121621.png)](https://github.com/requests/requests)


---

## Navigation

**Part of requests Documentation**
- **Main Documentation:** [https://requests.readthedocs.io/en/latest/](https://requests.readthedocs.io/en/latest/)
- **This Section:** community/updates

---

*Generated by lib2docScrape - Comprehensive Documentation Scraping*
