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

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=False)

class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)


    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)


    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


    def signedin(self):
        try:
            user_id_cookie_val = self.request.cookies.get('user_id')
            user_id_val = utils.check_secure_val(user_id_cookie_val)
            print "user_id_val: %s" % user_id_val
            if user_id_val:
                uname = mydb.User.get_by_id(int(user_id_val))
                print "uname: " + str(uname)
                if not (uname is None):
                    return uname, True
            else:
                return None, False
        except:
            return None, False


class SignupPage(Handler):

    def render_signup(self, uname="", uname_err="", psswrd_err="", verify_err="", email="", email_err=""):
        self.render("signup.html", uname=uname, uname_err=uname_err, psswrd_err=psswrd_err, verify_err=verify_err, email=email, email_err=email_err)


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

        # this will store the values to be returned
        #ret = {"uname":cgi.escape(user_uname), "uname_err":"", "psswrd_err":"", "verify_err":"", "email":cgi.escape(user_email), "email_err":""}

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
            self.render_signup(uname=cgi.escape(user_uname), uname_err=uname_err, psswrd_err=psswrd_err, verify_err=verify_err, email=cgi.escape(user_email), email_err=email_err)
        else:
            password_hash = utils.make_pw_hash(user_uname, user_psswrd)
            user = mydb.User(username=user_uname, password_hash=password_hash, salt=password_hash.split('|')[1], email=user_email)
            user.put()
            print "added new user %s" % user.username
            #mydb.allusers(True, user)
            time.sleep(0.2)

            redir = self.request.cookies.get('Location')

            if not redir:
                redir = '/'

            self.response.headers.add_header('Set-Cookie', "user_id=%s;Location=%s;Path=/" % (utils.make_secure_val(str(user.key().id())), str(redir)))
            print "this is where we're being redirected: " + redir
            self.redirect(str(redir))


class LoginPage(Handler):

    def render_login(self, uname="", login_err=""):
        self.render("login.html", uname=uname, login_err=login_err)

    def get(self):
        self.render_login()

    def post(self):
        user_uname = self.request.get('username')
        user_psswrd = self.request.get('password')

        print user_uname

        valid_pwd = False
        valid_user = False

        q = mydb.User.get_by_name(user_uname)
        print q.username
        if not(q is None):
            valid_user = True
            valid_pwd = utils.valid_pw(user_uname, user_psswrd, q.password_hash)

        if valid_pwd and valid_user:
            redir = self.request.cookies.get('Location')
            if not redir:
                redir = '/'
            self.response.headers.add_header('Set-Cookie', "user_id=%s;Location=%s;Path=/" % (utils.make_secure_val(str(q.key().id())), str(redir)))
            self.redirect(str(redir))
        else:
            self.render_login(uname=cgi.escape(user_uname), login_err="Invalid username or password")


class LogoutPage(Handler):

    def get(self):
        redir = self.request.cookies.get('Location')
        self.response.set_cookie('user_id', '')
        self.redirect(str(redir))


class WikiPage(Handler):

    def render_post(self, title):
        post = mydb.Post.get_by_title(title)

        if post:
            uname, logged_in = self.signedin()
            self.response.set_cookie('Location', title)

            if logged_in:
                self.render("individpost.html", entry=post, user=uname.username, logged_in=logged_in)
            else:
                self.render("individpost.html", entry=post, logged_in=logged_in)

        else:
            logging.error("NO POST, redirect to /_edit%s" % title)
            #mydb.allposts(True)
            self.redirect("/_edit" + title)

    def get(self, title):
        self.render_post(title)


class EditPage(Handler):

    def render_edit(self, title="", content="", logged_in=False, user=""):
        self.render("edit.html", title=title, content=content, logged_in=logged_in, user=user)

    def get(self, title):
        uname, logged_in = self.signedin()
        post = mydb.Post.get_by_title(title)
        if logged_in:
            self.response.set_cookie('Location', '/_edit'+title)
            logging.debug("entry id for editing: " + title)

            if post:
                logging.error("THERE is a post")
                self.render_edit(post.title, post.content, logged_in=logged_in, user=uname.username)
            else:
                logging.error("NO POST, render for edit: %s" % title)
                self.render_edit(title=title, logged_in=logged_in, user=uname.username)

        else:

            if post is None:
                self.redirect('/login')
            else:
                self.redirect('..' + title)

    def post(self, title):
        uname, logged_in = self.signedin()
        print title
        p = mydb.Post.get_by_title(title)

        if logged_in:
            entry = self.request.get("content")
            print entry
            logging.error("this is the entry_title: " + title)
            print "p is none: " + str(p is None)

            if p is None:
                print "tried to post to edit page and s/he was logged in and there wasn't a post"
                p = mydb.Post(title=title, content=entry)
            else:
                print "tried to post to edit page and s/he was logged in and there was a post"

            p.content = entry
            p.put()
            print "updated content: " + str(p.content)
            print "edit post entry key after put: " + str(p.key())
            #mydb.allposts(True, p)
            time.sleep(0.2)
            self.redirect('..'+title)

        else:
            if p is None:
                print "tried to post to edit page but wasn't logged in and there was no post"
                self.redirect('/login')
            else:
                print "tried to post to edit page but wasn't logged in and there was a post"
                self.redirect('..'+title)

