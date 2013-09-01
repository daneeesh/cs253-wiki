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
        user_id_cookie_val = self.request.cookies.get('user_id')
        print "user_id_cookie_val: %s" % user_id_cookie_val
        if user_id_cookie_val:
            user_id_val = utils.check_secure_val(user_id_cookie_val)
            print "user_id_val: %s" % user_id_val
            if user_id_val:
                uname = mydb.single_user_by_id(user_id_val)
                return uname, True
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
        ret = {"uname":cgi.escape(user_uname), "uname_err":"", "psswrd_err":"", "verify_err":"", "email":cgi.escape(user_email), "email_err":""}

        if not uname:
            ret["uname_err"] = "That's not a valid username!"
        if uname_ex:
            ret["uname_err"] = "This username already exists!"
        if not psswrd:
            ret["psswrd_err"] = "That wasn't a valid password"
        if not verified:
            ret["verify_err"] = "Passwords did not match"
        if not email:
            ret["email_err"] = "That's not a valid email!"

        if not(uname and not uname_ex and psswrd and verified and (email or user_email == "")):
            self.render_signup(uname=ret["uname"], uname_err=ret["uname_err"], psswrd_err=ret["psswrd_err"], verify_err=ret["verify_err"], email=ret["email"], email_err=ret["email_err"])
        else:
            password_hash = utils.make_pw_hash(user_uname, user_psswrd)
            user = mydb.User(username=user_uname, password_hash=password_hash, salt=password_hash.split('|')[1], email=user_email)
            user.put()
            print "added new user %s" % user.username
            mydb.allusers(True)
            redir = self.request.cookies.get('last_post')
            if not redir:
                redir = '/'
            self.response.headers.add_header('Set-Cookie', "user_id=%s;last_post=%s;Path=/" % (utils.make_secure_val(str(user.key().id())), str(redir)))
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

        q = mydb.single_user_by_name(user_uname)
        print q
        if not(q is None):
            valid_user = True
            valid_pwd = utils.valid_pw(user_uname, user_psswrd, q.password_hash)

        if valid_pwd and valid_user:
            redir = self.request.cookies.get('last_post')
            if not redir:
                redir = '/'
            self.response.headers.add_header('Set-Cookie', "user_id=%s;last_post=%s;Path=/" % (utils.make_secure_val(str(q.key().id())), str(redir)))
            self.redirect(str(redir))
        else:
            self.render_login(uname=cgi.escape(user_uname), login_err="Invalid username or password")


class LogoutPage(Handler):
    def get(self):
        redir = self.request.cookies.get('last_post')
        self.response.set_cookie('user_id', '')
        self.redirect(str(redir))


class WikiPage(Handler):
    def render_post(self, entry_id):
        post = mydb.singlepost(entry_id)
        if post:
            uname, logged_in = self.signedin()
            self.response.set_cookie('last_post', entry_id)
            age = '%i' % (time.time() - mydb.memcache_get('age_individ'))
            if logged_in:
                self.render("individpost.html", age=age, entry=post, user=uname.username, logged_in=logged_in)
            else:
                self.render("individpost.html", age=age, entry=post, logged_in=logged_in)
        else:
            logging.error("NO POST, redirect to /_edit%s" % entry_id)
            mydb.allposts(True)
            self.redirect("/_edit"+entry_id)

    def get(self, entry_id):
        self.render_post(entry_id)


class EditPage(Handler):
    def render_edit(self, title="", content="", logged_in=False, user=""):
        self.render("edit.html", title=title, content=content, logged_in=logged_in, user=user)

    def get(self, entry_id):
        uname, logged_in = self.signedin()
        print uname
        if logged_in:
            post = mydb.singlepost(entry_id)
            self.response.set_cookie('last_post', '/_edit'+entry_id)
            logging.debug("entry id for editing: " + entry_id)
            if post:
                logging.error("THERE is a post")
                self.render_edit(post.title, post.content, logged_in=logged_in, user=uname.username)
            else:
                logging.error("NO POST, render %s" % entry_id)
                self.render_edit(title=entry_id, logged_in=logged_in, user=uname.username)
        else:
            self.redirect('/login')

    def post(self, entry_id):
        entry = self.request.get("content")
        title = entry_id
        logging.error("this is the entry_title: " + title)
        p = mydb.Post(title=title, content=entry)
        p.put()
        mydb.allposts(True)
        self.redirect('/..'+title)



#This should be useless but kept it here for now
class JSONHandler(webapp2.RequestHandler):
    def write(self, *a):
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.response.out.write(json.dumps(*a))

    def create_json_entry(self, post):
        return {"content": post.content,
                "subject": post.title, "created": post.created.strftime("%a %b %H:%M:%S %Y"), "last_modified": post.last_modified.strftime("%a %b %H:%M:%S %Y")}


class SingleJSON(JSONHandler):
    def get(self, entry_id):
        post = mydb.singlepost(int(entry_id))
        json_entry = self.create_json_entry(post)
        self.write(json_entry)


class MainJSON(JSONHandler):
    def get(self):
        posts = mydb.allposts()
        post_list = [self.create_json_entry(post) for post in posts]
        self.write(post_list)


class Flush(Handler):
    def get(self):
        mydb.flush_memcache()
        self.redirect('/')


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
            mydb.allposts(True)
            id = a.key().id()
            self.redirect("/"+str(id))
        else:
            error = "we need a title and some content"
            self.render_newpost(title, content, error)


class MainPage(Handler):
    def render_front(self, title="", content="", error=""):
        posts = mydb.recentposts()
        if mydb.memcache_get('age') is None:
            mydb.memcache_set('age', time.time())
        age = '%i' % (time.time() - mydb.memcache_get('age'))
        self.render("front.html", title=title, age=age, content=content, error=error, posts=posts)

    def get(self):
        self.render_front()