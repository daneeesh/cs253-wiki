#!/usr/bin/env python

import os, re, random, string
import webapp2
import jinja2
import hashlib
import hmac
import json
import logging
import time
import utils
import mydb

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


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
        ret = {"uname":user_uname, "uname_err":"", "psswrd_err":"", "verify_err":"", "email":user_email, "email_err":""}

        if not uname:
            ret["uname_err"] = "That's not a valid username!"
        if uname_ex:
            ret["uname_err"] = "This username already exists!"
        if not psswrd:
            ret["psswrd_err"] = "That wasn't a valid password"
        if not verified:
            ret["verify_err"] = "Passwords did not match: %s %s %s" % (user_psswrd, user_ver, verified)
        if not email:
            ret["email_err"] = "That's not a valid email!"

        if not(uname and not(uname_ex) and psswrd and verified and (email or user_email == "")):
            self.render_signup(uname=ret["uname"], uname_err=ret["uname_err"], psswrd_err=ret["psswrd_err"], verify_err=ret["verify_err"], email=ret["email"], email_err=ret["email_err"])
        else:
            password_hash = utils.make_pw_hash(user_uname, user_psswrd)
            user = User(username=user_uname, password_hash=password_hash, salt=password_hash.split('|')[1], email=user_email)
            user.put()
            self.response.headers.add_header('Set-Cookie', "user_id=%s" % utils.make_secure_val(str(user.key().id())))
            self.redirect('/welcome')

class WelcomePage(Handler):
    def render_welcome(self, user=""):
        self.render("welcome.html", username=user)

    def get(self):
        user_id_cookie_val = self.request.cookies.get('user_id')
        if user_id_cookie_val:
            user_id_val = utils.check_secure_val(user_id_cookie_val)
            if user_id_val:
                uname = mydb.single_user_by_id(user_id_val)
                self.render_welcome(uname)
        else:
            self.redirect('/signup')


class LoginPage(Handler):
    def render_login(self, uname="", login_err=""):
        self.render("login.html", style=css_style, uname=uname, login_err=login_err)

    def get(self):
        self.render_login()

    def post(self):
        user_uname = self.request.get('username')
        user_psswrd = self.request.get('password')

        valid_pwd = False
        valid_user = False

        q = mydb.single_user_by_name(user_uname)
        if q.count() != 0:
            valid_user = True
            user = q.fetch(1)[0]
            valid_pwd = utils.valid_pw(user_uname, user_psswrd, user.password_hash)

        if valid_pwd and valid_user:
            self.response.headers.add_header('Set-Cookie', "user_id=%s" % utils.make_secure_val(str(user.key().id())))
            self.redirect('/welcome')
        else:
            self.render_login(uname=user_uname, login_err="Invalid username or password")

class LogoutPage(Handler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', "user_id=;Path=/")
        self.redirect('/signup')

class MainPage(Handler):
    def render_front(self, title="", content="", error=""):
        posts = mydb.recentposts()
        if memcache.get('age') is None:
            memcache.set('age', time.time())
        age = '%i' % (time.time() - memcache.get('age'))
        self.render("front.html", title=title, age=age, content=content, error=error, posts=posts)

    def get(self):
        self.render_front()

class NewPost(Handler):
    def render_newpost(self, title="", content="", error=""):
        self.render("newpost.html", title=title, content=content, error=error)

    def get(self):
        self.render_newpost()

    def post(self):
        title = self.request.get("subject")
        content = self.request.get("content")

        if title and content:
            a = mydb.Post(title = title, content = content)
            a.put()
            allposts(True)
            recentposts(True)
            id = a.key().id()
            self.redirect("/"+str(id))
        else:
            error = "we need a title and some content"
            self.render_newpost(title, content, error)

class SinglePost(Handler):
    def render_post(self, entry_id, title="", content="", error=""):
        post = individpost(int(entry_id))
        age = '%i' % (time.time() - memcache.get('age_individ'))

        self.render("individpost.html", style=css_style, age=age, entry=post)

    def get(self, entry_id):
        self.render_post(entry_id)

class JSONHandler(webapp2.RequestHandler):
    def write(self, *a):
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.response.out.write(json.dumps(*a))

    def create_json_entry(self, post):
        return {"content": post.content,
                "subject": post.title, "created": post.created.strftime("%a %b %H:%M:%S %Y"), "last_modified": post.last_modified.strftime("%a %b %H:%M:%S %Y")}


class SingleJSON(JSONHandler):
    def get(self, entry_id):

        post = singlepost(int(entry_id))
        json_entry = self.create_json_entry(post)
        self.write(json_entry)

class MainJSON(JSONHandler):
    def get(self):
        posts = allposts()
        post_list = [self.create_json_entry(post) for post in posts]
        self.write(post_list)

class Flush(Handler):
    def get(self):
        memcache.flush_all()
        self.redirect('/')
