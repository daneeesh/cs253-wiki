#!/usr/bin/env python

import webapp2
import handlers2
import mydb

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)' #Regular expression for wiki entry titles

#Create the required classes.
LoginHandler = handlers2.LoginPage
LogoutHandler = handlers2.LogoutPage
SignupHandler = handlers2.SignupPage
WikiHandler = handlers2.WikiPage
EditHandler = handlers2.EditPage
HistoryPage = handlers2.HistoryPage

#Define the app.
app = webapp2.WSGIApplication([
    ('/login', LoginHandler),
    ('/logout', LogoutHandler),
    ('/signup', SignupHandler),
    ('/_edit'+PAGE_RE, EditHandler),
    ('/_history' + PAGE_RE, HistoryPage),
    (PAGE_RE, WikiHandler)
], debug=True)
