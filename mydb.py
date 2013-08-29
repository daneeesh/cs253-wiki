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
        logging.debug("CACHE QUERY RECENTPOSTS")
        recent_posts = db.GqlQuery("SELECT * FROM Post ORDER BY created DESC limit 10")
        recent_posts = list(recent_posts)
        memcache.set(key, recent_posts)
        memcache.set(age, time.time())
    return recent_posts


def allposts(update=False):
    key = 'all'
    key2 = 'recent'
    age = 'age_recent'
    all_posts = memcache.get(key)
    if all_posts is None or update:
        logging.debug("DB QUERY ALLPOSTS")
        a = db.GqlQuery("SELECT * FROM Post ORDER BY created")
        all_posts = list(a)
        memcache.set(key, all_posts)
        memcache.set(key2, all_posts[:10])
    return all_posts


def singlepost(id):
    all_posts = allposts()
    for a in all_posts:
        if a.key().id() == id:
            return a
    return False


def individpost(id, update=False):
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
    return individ_post


def allusers(update=False):
    key = 'users'
    all_users = memcache.get(key)
    if all_users is None or update:
        logging.debug("DB QUERY ALLUSERS")
        a = db.GqlQuery("SELECT * FROM User ORDER BY created")
        all_users = list(a)
        memcache.set(key, all_users)
    return all_users


def single_user_by_name(name):
    all_users = allusers()
    try:
        return [user.name for user in all_users if user.name == name][0]
    except:
        return None


def single_user_by_id(id):
    all_users = allusers()
    try:
        return [user.name for user in all_users if user.key().id() == id][0]
    except:
        return None


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

