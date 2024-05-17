# Security Headers

Security headers are statements we add to HTTP responses that instruct the web browser on how to handle the content it obtains without giving unauthorized access to its user's information or computing resources.

It is possible to tamper with the network and the documents it transports, in many ways. Consequently a browser may compromise its host computer as it processes content manipulated by a third-party with malicious intent.

Modern browsers implement security measures to avert or mitigate these dangers. Security headers play a role in these mechanisms.

[Security headers on OWASP](https://owasp.org/www-project-secure-headers/)

## Headers defined in `ssl.conf`

### X-Frame-Options

Value: `"DENY"`

This header tells the browser it should not render any of our content on a web page that embeds it.

[X-Frame-Options on MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options)

### X-Content-Type-Options

Value: `"nosniff"`

The browser should not decide that one of our files is executable if we have not said it is

[X-Content-Type-Options on MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Content-Type-Options)

### X-XSS-Protection

Value: `"1; mode-block"`

We are telling the browser to not render our content if it detects a reflected cross site scripting attack.

The basic form of reflected XSS begins with a URL, crafted by an attacker, in which data that should be user input is in reality executable content. If the server that handles the URL does not sanitize the user input in it, the visitor browser will execute the malicious payload as it receives the server's reply.

[XSS on OWASP](https://owasp.org/www-community/attacks/xss/)  
[Cross site scripting article on Wikipedia](https://en.wikipedia.org/wiki/Cross-site_scripting)

Handling of X-XSS-Protection has been deprecated in latest browsers. But we still deploy the header for the older browsers that will visit our site.

[OWASP XSS Prevention Cheat Sheet - header deprecated](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html#x-xss-protection-header)

### Referrer-Policy

Value: `"same-origin"`

The browser should not pass information about any site that links to us in the "Referer" header.

[Referrer-Policy on MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy)  
["Referer" header on MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referer)

### Feature-Policy and Permissions-Policy

With these headers we are declaring we do not need to access any special feature the browser may offer, such as camera, microphone, speaker and so on.

[Feature-Policy on MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Feature-Policy)

## Content-Security-Policy

This header identifies what content and which web locations the browser should trust. We create the header on Django, using the django-csp package.

The file django/base_app/settings.py contains the directives in the CSP header.

[CSP quick reference](https://content-security-policy.com/)  
[CSP on OWASP](https://owasp.org/www-project-secure-headers/#content-security-policy)

### Nonces in `style` and `script` elements

CSP lets us define trusted `style` and `script` elements in the HTML. These elements occur in the templates we have in Django. They are now decorated with nonce attributes.

For every page that Django generates, django-csp creates a new nonce that it inserts in the HTTP response. The nonce is then available to be used in the templates.

    <script nonce="{{ request.csp_nonce }}"></script>
    <style nonce="{{ request.csp_nonce }}"></style>

The browser receives the nonce in the CSP header. It then knows it can trust the nonce'd elements by checking their values are equal to the nonce in the header. All script and style elements without a nonce are discarded.

[django-csp on GitHub](https://github.com/mozilla/django-csp)  
[django-csp readthedocs](https://django-csp.readthedocs.io/en/latest/)
