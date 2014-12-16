Authentication and security
===========================

Cookies and secure cookies
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can set cookies in the user's browser with the ``set_cookie``
method::

    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            if not self.get_cookie("mycookie"):
                self.set_cookie("mycookie", "myvalue")
                self.write("Your cookie was not set yet!")
            else:
                self.write("Your cookie was set!")

Cookies are not secure and can easily be modified by clients.  If you
need to set cookies to, e.g., identify the currently logged in user,
you need to sign your cookies to prevent forgery. Tornado supports
signed cookies with the `~.RequestHandler.set_secure_cookie` and
`~.RequestHandler.get_secure_cookie` methods. To use these methods,
you need to specify a secret key named ``cookie_secret`` when you
create your application. You can pass in application settings as
keyword arguments to your application::

    application = tornado.web.Application([
        (r"/", MainHandler),
    ], cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__")

Signed cookies contain the encoded value of the cookie in addition to a
timestamp and an `HMAC <http://en.wikipedia.org/wiki/HMAC>`_ signature.
If the cookie is old or if the signature doesn't match,
``get_secure_cookie`` will return ``None`` just as if the cookie isn't
set. The secure version of the example above::

    class MainHandler(tornado.web.RequestHandler):
        def get(self):
            if not self.get_secure_cookie("mycookie"):
                self.set_secure_cookie("mycookie", "myvalue")
                self.write("Your cookie was not set yet!")
            else:
                self.write("Your cookie was set!")

Tornado's secure cookies guarantee integrity but not confidentiality.
That is, the cookie cannot be modified but its contents can be seen by the
user.  The ``cookie_secret`` is a symmetric key and must be kept secret --
anyone who obtains the value of this key could produce their own signed
cookies.

By default, Tornado's secure cookies expire after 30 days.  To change this,
use the ``expires_days`` keyword argument to ``set_secure_cookie`` *and* the
``max_age_days`` argument to ``get_secure_cookie``.  These two values are
passed separately so that you may e.g. have a cookie that is valid for 30 days
for most purposes, but for certain sensitive actions (such as changing billing
information) you use a smaller ``max_age_days`` when reading the cookie.

.. _user-authentication:

User authentication
~~~~~~~~~~~~~~~~~~~

The currently authenticated user is available in every request handler
as `self.current_user <.RequestHandler.current_user>`, and in every
template as ``current_user``. By default, ``current_user`` is
``None``.

To implement user authentication in your application, you need to
override the ``get_current_user()`` method in your request handlers to
determine the current user based on, e.g., the value of a cookie. Here
is an example that lets users log into the application simply by
specifying a nickname, which is then saved in a cookie::

    class BaseHandler(tornado.web.RequestHandler):
        def get_current_user(self):
            return self.get_secure_cookie("user")

    class MainHandler(BaseHandler):
        def get(self):
            if not self.current_user:
                self.redirect("/login")
                return
            name = tornado.escape.xhtml_escape(self.current_user)
            self.write("Hello, " + name)

    class LoginHandler(BaseHandler):
        def get(self):
            self.write('<html><body><form action="/login" method="post">'
                       'Name: <input type="text" name="name">'
                       '<input type="submit" value="Sign in">'
                       '</form></body></html>')

        def post(self):
            self.set_secure_cookie("user", self.get_argument("name"))
            self.redirect("/")

    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/login", LoginHandler),
    ], cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__")

You can require that the user be logged in using the `Python
decorator <http://www.python.org/dev/peps/pep-0318/>`_
`tornado.web.authenticated`. If a request goes to a method with this
decorator, and the user is not logged in, they will be redirected to
``login_url`` (another application setting). The example above could be
rewritten::

    class MainHandler(BaseHandler):
        @tornado.web.authenticated
        def get(self):
            name = tornado.escape.xhtml_escape(self.current_user)
            self.write("Hello, " + name)

    settings = {
        "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        "login_url": "/login",
    }
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/login", LoginHandler),
    ], **settings)

If you decorate ``post()`` methods with the ``authenticated``
decorator, and the user is not logged in, the server will send a
``403`` response.  The ``@authenticated`` decorator is simply
shorthand for ``if not self.current_user: self.redirect()`` and may
not be appropriate for non-browser-based login schemes.

Check out the `Tornado Blog example application
<https://github.com/tornadoweb/tornado/tree/stable/demos/blog>`_ for a
complete example that uses authentication (and stores user data in a
MySQL database).

Third party authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~

The `tornado.auth` module implements the authentication and
authorization protocols for a number of the most popular sites on the
web, including Google/Gmail, Facebook, Twitter, and FriendFeed.
The module includes methods to log users in via these sites and, where
applicable, methods to authorize access to the service so you can, e.g.,
download a user's address book or publish a Twitter message on their
behalf.

Here is an example handler that uses Google for authentication, saving
the Google credentials in a cookie for later access::

    class GoogleHandler(tornado.web.RequestHandler, tornado.auth.GoogleMixin):
        @tornado.web.asynchronous
        def get(self):
            if self.get_argument("openid.mode", None):
                self.get_authenticated_user(self._on_auth)
                return
            self.authenticate_redirect()

        def _on_auth(self, user):
            if not user:
                self.authenticate_redirect()
                return
            # Save the user with, e.g., set_secure_cookie()

See the `tornado.auth` module documentation for more details.

.. _xsrf:

Cross-site request forgery protection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Cross-site request
forgery <http://en.wikipedia.org/wiki/Cross-site_request_forgery>`_, or
XSRF, is a common problem for personalized web applications. See the
`Wikipedia
article <http://en.wikipedia.org/wiki/Cross-site_request_forgery>`_ for
more information on how XSRF works.

The generally accepted solution to prevent XSRF is to cookie every user
with an unpredictable value and include that value as an additional
argument with every form submission on your site. If the cookie and the
value in the form submission do not match, then the request is likely
forged.

Tornado comes with built-in XSRF protection. To include it in your site,
include the application setting ``xsrf_cookies``::

    settings = {
        "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        "login_url": "/login",
        "xsrf_cookies": True,
    }
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/login", LoginHandler),
    ], **settings)

If ``xsrf_cookies`` is set, the Tornado web application will set the
``_xsrf`` cookie for all users and reject all ``POST``, ``PUT``, and
``DELETE`` requests that do not contain a correct ``_xsrf`` value. If
you turn this setting on, you need to instrument all forms that submit
via ``POST`` to contain this field. You can do this with the special
`.UIModule` ``xsrf_form_html()``, available in all templates::

    <form action="/new_message" method="post">
      {% module xsrf_form_html() %}
      <input type="text" name="message"/>
      <input type="submit" value="Post"/>
    </form>

If you submit AJAX ``POST`` requests, you will also need to instrument
your JavaScript to include the ``_xsrf`` value with each request. This
is the `jQuery <http://jquery.com/>`_ function we use at FriendFeed for
AJAX ``POST`` requests that automatically adds the ``_xsrf`` value to
all requests::

    function getCookie(name) {
        var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
        return r ? r[1] : undefined;
    }

    jQuery.postJSON = function(url, args, callback) {
        args._xsrf = getCookie("_xsrf");
        $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
            success: function(response) {
            callback(eval("(" + response + ")"));
        }});
    };

For ``PUT`` and ``DELETE`` requests (as well as ``POST`` requests that
do not use form-encoded arguments), the XSRF token may also be passed
via an HTTP header named ``X-XSRFToken``.  The XSRF cookie is normally
set when ``xsrf_form_html`` is used, but in a pure-Javascript application
that does not use any regular forms you may need to access
``self.xsrf_token`` manually (just reading the property is enough to
set the cookie as a side effect).

If you need to customize XSRF behavior on a per-handler basis, you can
override `.RequestHandler.check_xsrf_cookie()`. For example, if you
have an API whose authentication does not use cookies, you may want to
disable XSRF protection by making ``check_xsrf_cookie()`` do nothing.
However, if you support both cookie and non-cookie-based authentication,
it is important that XSRF protection be used whenever the current
request is authenticated with a cookie.
