#!/usr/bin/env python

import webapp2
import handlers
import mydb

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

#mydb.initialize_memcache()

LoginHandler = handlers.LoginPage
LogoutHandler = handlers.LogoutPage
SignupHandler = handlers.SignupPage
WikiHandler = handlers.WikiPage
EditHandler = handlers.EditPage
FlushHandler = handlers.Flush

app = webapp2.WSGIApplication([
    ('/login', LoginHandler),
    ('/logout', LogoutHandler),
    ('/signup', SignupHandler),
    ('/_edit'+PAGE_RE, EditHandler),
    ('/flush', FlushHandler),
    (PAGE_RE, WikiHandler)
], debug=True)
