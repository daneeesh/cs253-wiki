#!/usr/env/bin python

import logging
import time
import datetime

from google.appengine.api import memcache
from google.appengine.ext import db, ndb


def allposts(update=False, newpost=None, entry=None):
    key = 'all'
    age = 'age_recent'
    all_posts = memcache.get(key)
    if not(update) and newpost and not(all_posts is None):
        all_posts.append(newpost)
        memcache.set(key, all_posts)
        memcache.set(age, time.time())
        print "new post added to allposts"
    elif update and entry and not(all_posts is None):
        replace_post = [post for post in all_posts if post.title == entry[0]][0]
        i = all_posts.index(replace_post)
        post = all_posts.pop(i)
        cont = post.content
        cont.append(entry[1])
        print cont
        post.content = cont
        l = post.last_modified
        l.append(datetime.datetime.now())
        print l
        post.last_modified = l
        all_posts.insert(i,post)
        memcache.set(key, all_posts)
        memcache.set(age, time.time())
        print "a post has been updated in all_posts"
    elif all_posts is None or update:
        logging.debug("NDB QUERY ALLPOSTS")
        a = Posts.query().order(Posts.created)
        all_posts = list(a)
        memcache.set(key, all_posts)
        memcache.set(age, time.time())
        print "intialized/updated allposts"
    return all_posts


def singlepost_allversions(title):
    all_posts = allposts()
    entry = [post for post in all_posts if post.title == title]
    if entry:
        a = entry[0]
        print "title: " + str(a.title)
    else:
        a = None
    return a


def singlepost_latest(title):
    all_posts = allposts()
    entry = [post for post in all_posts if post.title == title]
    if entry:
        a = entry[0]
        return Post(title=title, content=a.content[-1])
    else:
        return None


def singlepost_version(title, version):
    all_posts = allposts()
    entry = [post for post in all_posts if post.title == title]
    if entry:
        a = entry[0]
        if version <= len(a.content):
            return Post(title=title, content=a.content[version])
    return None


def allusers(update=False, newuser=None):
    key = 'users'
    all_users = memcache.get(key)
    if newuser and update and not(all_users is None):
        all_users.append(newuser)
        memcache.set(key, all_users)
        print "new user added to allusers"
    elif all_users is None or update:
        logging.error("NDB QUERY ALLUSERS")
        a = User.query().order(User.created)
        all_users = list(a)
        memcache.set(key, all_users)
        print "allusers in memcache initialized/updated"
    print all_users
    return all_users


def single_user_by_name(name):
    all_users = allusers()
    for user in all_users:
        if str(user.username) == str(name):
            return user
    return None


def flush_memcache():
    memcache.flush_all()


"""def memcache_get(key):
    return memcache.get(key)


def memcache_set(key, value):
    memcache.set(key, value)"""


class User(ndb.Model):
    '''The user entity.'''
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
    '''A single wiki entry.'''
    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    #last_modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def get_by_title(cls, title):
        return Post.query(Post.title==title).get()

class Posts(ndb.Model):
    '''This is a post with a history.'''
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
        print "p is not none in add_new"
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