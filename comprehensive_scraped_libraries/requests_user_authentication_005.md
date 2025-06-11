# Authentication[¶](#authentication "Link to this heading")

**Library:** requests
**Section:** user/authentication
**Source URL:** https://requests.readthedocs.io/en/latest/user/authentication/
**Scraped:** 2025-06-03T18:38:06.839069

---

## Document Information

- **Content Length:** 6,933 characters
- **Links Found:** 0
- **Headings Found:** 12
- **Has Code Blocks:** False
- **Has Tables:** False

---

## Content


Authentication — Requests 2.32.3 documentation







# Authentication[¶](#authentication "Link to this heading")

This document discusses using various kinds of authentication with Requests.

Many web services require authentication, and there are many different types.
Below, we outline various forms of authentication available in Requests, from
the simple to the complex.

## Basic Authentication[¶](#basic-authentication "Link to this heading")

Many web services that require authentication accept HTTP Basic Auth. This is
the simplest kind, and Requests supports it straight out of the box.

Making requests with HTTP Basic Auth is very simple:

```
>>> from requests.auth import HTTPBasicAuth
>>> basic = HTTPBasicAuth('user', 'pass')
>>> requests.get('https://httpbin.org/basic-auth/user/pass', auth=basic)
<Response [200]>

```

In fact, HTTP Basic Auth is so common that Requests provides a handy shorthand
for using it:

```
>>> requests.get('https://httpbin.org/basic-auth/user/pass', auth=('user', 'pass'))
<Response [200]>

```

Providing the credentials in a tuple like this is exactly the same as the
`HTTPBasicAuth` example above.

### netrc Authentication[¶](#netrc-authentication "Link to this heading")

If no authentication method is given with the `auth` argument, Requests will
attempt to get the authentication credentials for the URL’s hostname from the
user’s netrc file. The netrc file overrides raw HTTP authentication headers
set with headers=.

If credentials for the hostname are found, the request is sent with HTTP Basic
Auth.



## Digest Authentication[¶](#digest-authentication "Link to this heading")

Another very popular form of HTTP Authentication is Digest Authentication,
and Requests supports this out of the box as well:

```
>>> from requests.auth import HTTPDigestAuth
>>> url = 'https://httpbin.org/digest-auth/auth/user/pass'
>>> requests.get(url, auth=HTTPDigestAuth('user', 'pass'))
<Response [200]>

```



## OAuth 1 Authentication[¶](#oauth-1-authentication "Link to this heading")

A common form of authentication for several web APIs is OAuth. The `requests-oauthlib`
library allows Requests users to easily make OAuth 1 authenticated requests:

```
>>> import requests
>>> from requests_oauthlib import OAuth1

>>> url = 'https://api.twitter.com/1.1/account/verify_credentials.json'
>>> auth = OAuth1('YOUR_APP_KEY', 'YOUR_APP_SECRET',
...               'USER_OAUTH_TOKEN', 'USER_OAUTH_TOKEN_SECRET')

>>> requests.get(url, auth=auth)
<Response [200]>

```

For more information on how to OAuth flow works, please see the official [OAuth](https://oauth.net/) website.
For examples and documentation on requests-oauthlib, please see the [requests\_oauthlib](https://github.com/requests/requests-oauthlib)
repository on GitHub


## OAuth 2 and OpenID Connect Authentication[¶](#oauth-2-and-openid-connect-authentication "Link to this heading")

The `requests-oauthlib` library also handles OAuth 2, the authentication mechanism
underpinning OpenID Connect. See the [requests-oauthlib OAuth2 documentation](https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html) for
details of the various OAuth 2 credential management flows:

* [Web Application Flow](https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#web-application-flow)
* [Mobile Application Flow](https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#mobile-application-flow)
* [Legacy Application Flow](https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#legacy-application-flow)
* [Backend Application Flow](https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#backend-application-flow)

## Other Authentication[¶](#other-authentication "Link to this heading")

Requests is designed to allow other forms of authentication to be easily and
quickly plugged in. Members of the open-source community frequently write
authentication handlers for more complicated or less commonly-used forms of
authentication. Some of the best have been brought together under the
[Requests organization](https://github.com/requests), including:

* [Kerberos](https://github.com/requests/requests-kerberos)
* [NTLM](https://github.com/requests/requests-ntlm)

If you want to use any of these forms of authentication, go straight to their
GitHub page and follow the instructions.


## New Forms of Authentication[¶](#new-forms-of-authentication "Link to this heading")

If you can’t find a good implementation of the form of authentication you
want, you can implement it yourself. Requests makes it easy to add your own
forms of authentication.

To do so, subclass [`AuthBase`](../../api/#requests.auth.AuthBase "requests.auth.AuthBase") and implement the
`__call__()` method:

```
>>> import requests
>>> class MyAuth(requests.auth.AuthBase):
...     def __call__(self, r):
...         # Implement my authentication
...         return r
...
>>> url = 'https://httpbin.org/get'
>>> requests.get(url, auth=MyAuth())
<Response [200]>

```

When an authentication handler is attached to a request,
it is called during request setup. The `__call__` method must therefore do
whatever is required to make the authentication work. Some forms of
authentication will additionally add hooks to provide further functionality.

Further examples can be found under the [Requests organization](https://github.com/requests) and in the
`auth.py` file.






Requests is an elegant and simple HTTP library for Python, built for
human beings. You are currently looking at the documentation of the
development release.

### Useful Links

* [Quickstart](../quickstart/)
* [Advanced Usage](../advanced/)
* [API Reference](../../api/)
* [Release History](../../community/updates/#release-history)
* [Contributors Guide](../../dev/contributing/)
* [Recommended Packages and Extensions](../../community/recommended/)
* [Requests @ GitHub](https://github.com/psf/requests)
* [Requests @ PyPI](https://pypi.org/project/requests/)
* [Issue Tracker](https://github.com/psf/requests/issues)

### [Table of Contents](../../)

* [Authentication](#)
  + [Basic Authentication](#basic-authentication)
    - [netrc Authentication](#netrc-authentication)
  + [Digest Authentication](#digest-authentication)
  + [OAuth 1 Authentication](#oauth-1-authentication)
  + [OAuth 2 and OpenID Connect Authentication](#oauth-2-and-openid-connect-authentication)
  + [Other Authentication](#other-authentication)
  + [New Forms of Authentication](#new-forms-of-authentication)
### Related Topics

* [Documentation overview](../../)
  + Previous: [Advanced Usage](../advanced/ "previous chapter")
  + Next: [Recommended Packages and Extensions](../../community/recommended/ "next chapter")

### Quick search








©MMXVIX. A Kenneth Reitz Project.

[![Fork me on GitHub](https://github.blog/wp-content/uploads/2008/12/forkme_right_darkblue_121621.png)](https://github.com/requests/requests)


---

## Navigation

**Part of requests Documentation**
- **Main Documentation:** [https://requests.readthedocs.io/en/latest/](https://requests.readthedocs.io/en/latest/)
- **This Section:** user/authentication

---

*Generated by lib2docScrape - Comprehensive Documentation Scraping*
