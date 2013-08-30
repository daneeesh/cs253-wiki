#!/usr/bin/env python

import webapp2
import handlers
import mydb
import utils

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

mydb.initialize_memcache()

LoginHandler = handlers.LoginPage()
LogoutHandler = handlers.LogoutPage()
SignupHandler = handlers.SignupPage()
WikiHandler = handlers.WikiPage()
EditHandler = handlers.EditPage()

app = webapp2.WSGIApplication([
    ('/login', LoginHandler),
    ('/logout', LogoutHandler),
    ('/signup', SignupHandler),
    (PAGE_RE, WikiHandler),
    ('/_edit'+PAGE_RE, EditHandler)
], debug=True)
