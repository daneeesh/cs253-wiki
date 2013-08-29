#!/usr/bin/env python

import webapp2
import handlers
import mydb
import utils

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello world!')

LoginHandler = handlers.LoginPage()
LogoutHandler = handlers.LogoutPage()
SignupHandler = handlers.SignupPage()
WikiHandler = handlers.WikiPage()
EditHandler = handlers.EditPage()

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/login',LoginHandler),
    ('/logout', LogoutHandler),
    ('/signup', SignupHandler),
    (PAGE_RE, WikiHandler),
    ('/_edit'+PAGE_RE, EditHandler)
], debug=True)
