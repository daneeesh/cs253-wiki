#!/usr/bin/env python

import webapp2
import handlers2
import mydb

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

LoginHandler = handlers2.LoginPage
LogoutHandler = handlers2.LogoutPage
SignupHandler = handlers2.SignupPage
WikiHandler = handlers2.WikiPage
EditHandler = handlers2.EditPage
#FlushHandler = handlers2.Flush

app = webapp2.WSGIApplication([
    ('/login', LoginHandler),
    ('/logout', LogoutHandler),
    ('/signup', SignupHandler),
    ('/_edit'+PAGE_RE, EditHandler),
    (PAGE_RE, WikiHandler)
], debug=True)
