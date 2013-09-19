#!/usr/bin/env python

import os
import webapp2
import jinja2
import json
import time
import utils
import mydb
import cgi
import logging
import datetime

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=False)

class Handler(webapp2.RequestHandler):
    """This is the main Handler class that has all the common functions."""
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)


    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)


    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


    def signedin(self):
        """Check if the user is signed in"""
        try:
            user_id_cookie_val = self.request.cookies.get('user_id')
            user_id_val = utils.check_secure_val(user_id_cookie_val)
            #print "user_id_val: %s" % user_id_val
            if user_id_val:
                user = mydb.single_user_by_id(int(user_id_val))
                print "user: " + str(user)
                if not (user is None):
                    return user, True
            else:
                return None, False
        except:
            return None, False


class SignupPage(Handler):
    """This class handles the Signup page."""
    def render_signup(self, uname="", uname_err="", psswrd_err="", verify_err="", email="", email_err=""):
        self.render("signup.html",
                     uname=uname,
                     uname_err=uname_err,
                     psswrd_err=psswrd_err,
                     verify_err=verify_err,
                     email=email,
                     email_err=email_err)


    def get(self):
        self.render_signup()


    def post(self):
        user_uname = self.request.get('username')
        user_psswrd = self.request.get('password')
        user_ver = self.request.get('verify')
        user_email = self.request.get('email')

        uname = utils.valid_uname(user_uname)
        uname_ex = utils.user_exists(user_uname)
        psswrd = utils.valid_psswrd(user_psswrd)
        verified = utils.verify_psswrd(user_psswrd, user_ver)
        email = utils.valid_email(user_email)

        #Create error messages
        if not uname:
            uname_err = "That's not a valid username!"
        if uname_ex:
            uname_err = "This username already exists!"
        if not psswrd:
            psswrd_err = "That wasn't a valid password"
        if not verified:
            verify_err = "Passwords did not match"
        if not email:
            email_err = "That's not a valid email!"

        if not(uname and not uname_ex and psswrd and verified and (email or user_email == "")):
            #There was an error in one of the fields.
            self.render_signup(uname=cgi.escape(user_uname),
                               uname_err=uname_err,
                               psswrd_err=psswrd_err,
                               verify_err=verify_err,
                               email=cgi.escape(user_email),
                               email_err=email_err)
        else:
            #Create a new user.
            password_hash = utils.make_pw_hash(user_uname, user_psswrd)
            user = mydb.User(username=user_uname, password_hash=password_hash, salt=password_hash.split('|')[1], email=user_email)
            user.put()
            mydb.allusers(update=True, newuser=user)
            print "added new user %s" % user.username

            #Redirect the user back to entry where they came from.
            redir = self.request.cookies.get('Location')

            if not redir:
                redir = '/'

            self.response.headers.add_header('Set-Cookie', "user_id=%s;Location=%s;Path=/" % (utils.make_secure_val(str(user.key.id())), str(redir)))
            self.redirect(str(redir))


class LoginPage(Handler):
    """This class handles the Login page."""
    def render_login(self, uname="", login_err=""):
        self.render("login.html", uname=uname, login_err=login_err)

    def get(self):
        self.render_login()

    def post(self):
        user_uname = self.request.get('username')
        user_psswrd = self.request.get('password')

        valid_pwd = False
        valid_user = False
        #Get user and check password.
        q = mydb.single_user_by_name(user_uname)
        if not(q is None):
            valid_user = True
            valid_pwd = utils.valid_pw(user_uname, user_psswrd, q.password_hash)

        if valid_pwd and valid_user:
            # Set cookie and redirect.
            redir = self.request.cookies.get('Location')
            if not redir:
                redir = '/'
            self.response.headers.add_header('Set-Cookie', "user_id=%s;Location=%s;Path=/" % (utils.make_secure_val(str(q.key.id())), str(redir)))
            self.redirect(str(redir))
        else:
            self.render_login(uname=cgi.escape(user_uname), login_err="Invalid username or password")


class LogoutPage(Handler):
    """This class handles the Logout page."""
    def get(self):
        redir = self.request.cookies.get('Location')
        self.response.set_cookie('user_id', '')
        self.redirect(str(redir))


class WikiPage(Handler):
    """This class handles the Wiki page (i.e. single entries)."""
    def render_post(self, title):
        #Get the right entry.
        version = self.request.get("v")
        if version.isdigit():
            post = mydb.singlepost_version(title, int(version))
        else:
            post = mydb.singlepost_latest(title)


        if post:
            #If there is a post, update the cookie and load the post.
            uname, logged_in = self.signedin()
            self.response.set_cookie('Location', title)

            if logged_in:
                self.render("individpost.html", entry=post, user=uname.username, logged_in=logged_in)
            else:
                self.render("individpost.html", entry=post, logged_in=logged_in)

        else:
            #Else redirect to its edit page.
            logging.error("NO POST, redirect to /_edit%s" % title)
            self.redirect("/_edit" + title)

    def get(self, title):
        self.render_post(title)


class EditPage(Handler):
    """This class handles the Edit page."""
    def render_edit(self, title="", content="", logged_in=False, user=""):
        self.render("edit.html", title=title, content=content, user=user)

    def get(self, title):
        uname, logged_in = self.signedin() #Check if the user's logged in.
        post = mydb.singlepost_latest(title)
        if logged_in:
            #Set cookie and display the content.
            self.response.set_cookie('Location', '/_edit'+title)
            logging.debug("entry id for editing: " + title)

            if post:
                logging.error("THERE is a post")
                self.render_edit(post.title, post.content, user=uname.username)
            else:
                logging.error("NO POST, render for edit: %s" % title)
                self.render_edit(title=title, user=uname.username)

        else:
            #Either redirect to login or to the post if it exists.
            if post is None:
                self.redirect('/login')
            else:
                self.redirect('..' + title)

    def post(self, title):
        #Check if the user is logged in and get the latest version of the entry.
        uname, logged_in = self.signedin()
        p = mydb.singlepost_latest(title)

        if logged_in:
            #Get the content for the wiki page and modify it if there has already been some content for it.
            #Else create the instance in the database.
            entry = self.request.get("content")
            logging.error("this is the entry_title: " + title)
            print "p is none: " + str(p is None)

            if p is None:
                print "tried to post to edit page and s/he was logged in and there wasn't a post"
                p = mydb.Posts(title=title, content=[entry], last_modified=[datetime.datetime.now()])
                p.put()
                mydb.allposts(newpost=p)
            else:
                print "tried to post to edit page and s/he was logged in and there was a post"
                mydb.Posts.add_new(title,entry)
                mydb.allposts(update=True, entry=[title, entry])
            self.redirect('..'+title)

        else:
            #Either redirect to login or to the post if it exists.
            if p is None:
                self.redirect('/login')
            else:
                self.redirect('..'+title)


class HistoryPage(Handler):
    """This class handles the History page."""
    def render_history(self, title="", entry="", logged_in=False, user=""):
        self.render("history.html", title=title, entry=entry, user=user)

    def create_history(self, title):
        #Get all the versions of the entries and create a list of mydb.Post from them.
        ps = mydb.singlepost_allversions(title)
        posts = []
        n = len(ps.content)
        i = 0
        while i < n:
            posts.append((mydb.Post(title=title, content=cgi.escape(ps.content[i]), created=ps.last_modified[i]), i))
            i += 1
        posts.reverse()
        return posts

    def get(self, title):
        #Check if the user is logged in and create the history of the entry.
        uname, logged_in = self.signedin()
        posts = self.create_history(title)

        if logged_in:
            self.render_history(title=title, entry=posts, user=uname.username)

        else:
            #Either redirect to login or to the post if it exists.
            if p is None:
                self.redirect('/login')
            else:
                self.redirect('..'+title)