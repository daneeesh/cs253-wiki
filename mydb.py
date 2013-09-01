#!/usr/env/bin python

import logging
import time

from google.appengine.api import memcache
from google.appengine.ext import db


def recentposts(update=False):
    key = 'recent'
    age = 'age_recent'
    recent_posts = memcache.get(key)
    if recent_posts is None or update:
        logging.error("CACHE QUERY RECENTPOSTS")
        recent_posts = allposts()[:10]
        memcache.set(key, recent_posts)
        memcache.set(age, time.time())
    return recent_posts


def allposts(update=False):
    key = 'all'
    key2 = 'recent'
    age = 'age_recent'
    all_posts = memcache.get(key)
    if all_posts is None or update:
        logging.error("DB QUERY ALLPOSTS")
        a = db.GqlQuery("SELECT * FROM Post ORDER BY created")
        all_posts = list(a)
        memcache.set(key, all_posts)
        memcache.set(key2, all_posts[:10])
        memcache.set(age, time.time())
        print "finished updating all the posts"
    return all_posts


def singlepost(id):
    all_posts = allposts()
    age = 'age_individ'
    key = 'individ'
    for a in all_posts:
        if a.title == id:
            memcache.set(age, time.time())
            return a
    return None


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


def allusers(update=False):
    key = 'users'
    all_users = memcache.get(key)
    if all_users is None or update:
        logging.error("DB QUERY ALLUSERS")
        a = db.GqlQuery("SELECT * FROM User ORDER BY created")
        all_users = list(a)
        memcache.set(key, all_users)
        print "finished refreshing all the users"
    return all_users


def single_user_by_name(name):
    all_users = allusers()
    print [user.username for user in all_users]
    print name
    for user in all_users:
        if str(user.username) == str(name):
            print user.username
            return user
    return None


def single_user_by_id(id):
    all_users = allusers()
    print [user.key().id() for user in all_users]
    print id
    for user in all_users:
        if int(user.key().id()) == int(id):
            print user.username
            return user
    return None


def initialize_memcache():
    allposts(True)
    allusers(True)


def flush_memcache():
    memcache.flush_all()


def memcache_get(key):
    return memcache.get(key)


def memcache_set(key, value):
    memcache.set(key, value)


class User(db.Model):
    username = db.StringProperty(required=True)
    password_hash = db.StringProperty(required=True)
    salt = db.StringProperty(required=True)
    email = db.StringProperty(required=False)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)


class Post(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    def render(self):
        self.render_text = self.content.replace('\n', '<br>')

