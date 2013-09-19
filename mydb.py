#!/usr/env/bin python

import logging
import time
import datetime

from google.appengine.api import memcache
from google.appengine.ext import db, ndb


def recentposts(update=False):
    key = 'recent'
    age = 'age_recent'
    recent_posts = memcache.get(key)
    if recent_posts is None or update:
        logging.debug("CACHE QUERY RECENTPOSTS")
        recent_posts = allposts()[:10]
        memcache.set(key, recent_posts)
        memcache.set(age, time.time())
    return recent_posts


def allposts(update=False, newpost=None):
    key = 'all'
    #key2 = 'recent'
    age = 'age_recent'
    all_posts = memcache.get(key)
    if update and newpost:
        all_posts.append(newpost)
        memcache.set(key, all_posts)
    elif all_posts is None or update:
        logging.debug("DB QUERY ALLPOSTS")
        a = db.GqlQuery("SELECT * FROM Post ORDER BY created")
        all_posts = list(a)
        memcache.set(key, all_posts)
        #memcache.set(key2, all_posts[:10])
        memcache.set(age, time.time())
        print "finished updating all the posts"
    return all_posts


def singlepost(id):
    all_posts = allposts()
    entries = [post for post in all_posts if post.title == id]
    try:
        a = entries[-1]
        print "title: " + str(a.title)
        print "key: " + str(a.key())
    except:
        a = None
    return a


"""def individpost(id, update=False):
    key = 'individ'
    age = 'age_individ'
    individ_post = memcache.get(key)
    try:
        update = not(individ_post.key().id() == id)
    except:
        pass
    if individ_post is None or update:
        logging.debug("CACHE QUERY INDIVID")
        individ_post = singlepost(id)
        memcache.set(key, individ_post)
        memcache.set(age, time.time())
    return individ_post"""


def allusers(update=False, newuser=None):
    key = 'users'
    all_users = memcache.get(key)
    if newuser and update and not(all_users is None):
        all_users.append(newuser)
        memcache.set(key, all_users)
        print "allusers in memcache replaced"
    elif all_users is None or update:
        logging.error("DB QUERY ALLUSERS")
        a = db.GqlQuery("SELECT * FROM User ORDER BY created")
        all_users = list(a)
        memcache.set(key, all_users)
    return all_users


def single_user_by_name(name):
    all_users = allusers()
    for user in all_users:
        if str(user.username) == str(name):
            return user
    return None


"""def single_user_by_id(id):
    all_users = allusers(True)
    for user in all_users:
        if int(user.key().id()) == int(id):
            return user
    return None"""


def initialize_memcache():
    allposts(True)
    allusers(True)


def flush_memcache():
    memcache.flush_all()


def memcache_get(key):
    return memcache.get(key)


def memcache_set(key, value):
    memcache.set(key, value)


class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    password_hash = ndb.StringProperty(required=True)
    salt = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=False)
    created = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def get_by_name(cls, name):
        return User.query(User.username==name).get()


class Post(ndb.Model):
    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    #last_modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def get_by_title(cls, title):
        return Post.query(Post.title==title).get()

class Posts(ndb.Model):
    title = ndb.StringProperty(required=True)
    content = ndb.StringProperty(repeated=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(repeated=True)

    @classmethod
    def get_by_title_version(cls, title, version):
        ps = Posts.query(Posts.title==title).get()
        if version <= len(ps.content):
            return Post(title=title, content=ps.content[version])
        else:
            return None

    @classmethod
    def get_latest_by_title(cls, title):
        ps = Posts.query(Posts.title==title).get()
        if ps is None:
            return None
        else:
            return Post(title=title, content=ps.content[-1])

    @classmethod
    def get_all_versions(cls, title):
        return Posts.query(Posts.title==title).get()

    @classmethod
    def add_new(cls, title, content):
        p = Posts.query(Posts.title==title).get()
        print "p is not none is add_new"
        cont = p.content
        cont.append(content)
        print cont
        p.content = cont
        l = p.last_modified
        l.append(datetime.datetime.now())
        p.last_modified = l
        p.put()
        print p.content
        print p.last_modified