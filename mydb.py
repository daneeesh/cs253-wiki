#!/usr/env/bin python

import logging
import time
import datetime

from google.appengine.api import memcache
from google.appengine.ext import db, ndb


def allposts(update=False, newpost=None, entry=None):
    """
    Method to handle every post in memcache.
    newpost type is mydb.Post
    entry is [title,content]
    """
    key = 'all'
    age = 'age_recent'
    all_posts = memcache.get(key)
    if not(update) and newpost and not(all_posts is None):
        # add a brand new post to memcache
        all_posts.append(newpost)
        memcache.set(key, all_posts)
        memcache.set(age, time.time())
        print "new post added to allposts"
    elif update and entry and not(all_posts is None):
        # update an existing post with the new content
        replace_post = [post for post in all_posts if post.title == entry[0]][0]
        i = all_posts.index(replace_post)
        post = all_posts.pop(i)
        # add newest version of content
        cont = post.content
        cont.append(entry[1])
        post.content = cont
        # add last modification time
        l = post.last_modified
        l.append(datetime.datetime.now())
        post.last_modified = l
        # save it again
        all_posts.insert(i,post)
        memcache.set(key, all_posts)
        memcache.set(age, time.time())
        print "a post has been updated in all_posts"
    elif all_posts is None or update:
        # initialize or synchronize posts for memcache
        logging.debug("NDB QUERY ALLPOSTS")
        a = Posts.query().order(Posts.created)
        all_posts = list(a)
        memcache.set(key, all_posts)
        memcache.set(age, time.time())
        print "intialized/updated allposts"
    return all_posts


def singlepost_allversions(title):
    """Return an entry with all of its versions (mydb.Posts)"""
    all_posts = allposts()
    entry = [post for post in all_posts if post.title == title] #there's probably a better way to do this
    if entry:
        a = entry[0]
        print "title: " + str(a.title)
    else:
        a = None
    return a


def singlepost_latest(title):
    """Return the latest version of an entry (mydb.Post)"""
    all_posts = allposts()
    entry = [post for post in all_posts if post.title == title] #there's probably a better way to do this
    if entry:
        a = entry[0]
        return Post(title=title, content=a.content[-1])
    else:
        return None


def singlepost_version(title, version):
    """Return a given version of an entry (mydb.Post)"""
    all_posts = allposts()
    entry = [post for post in all_posts if post.title == title] #there's probably a better way to do this
    if entry:
        a = entry[0]
        if version <= len(a.content):
            return Post(title=title, content=a.content[version])
    return None


def allusers(update=False, newuser=None):
    """
    Method to handle the users in memcache.
    newuser is of type mydb.User
    """
    key = 'users'
    all_users = memcache.get(key)
    if newuser and update and not(all_users is None):
        #add a new user to the memcache
        all_users.append(newuser)
        memcache.set(key, all_users)
        print "new user added to allusers"
    elif all_users is None or update:
        # initialize or synchronize memcache
        logging.error("NDB QUERY ALLUSERS")
        a = User.query().order(User.created)
        all_users = list(a)
        memcache.set(key, all_users)
        print "allusers in memcache initialized/updated"
    return all_users


def single_user_by_name(name):
    """
    Get a user by their username.
    """
    all_users = allusers()
    for user in all_users: #There's probably a better way to do this.
        if str(user.username) == str(name):
            return user
    return None


def single_user_by_id(id):
    """Get a user by their ID"""
    all_users = allusers()
    for user in all_users:
        if str(user.key.id()) == str(id):
            return user
    return None

def flush_memcache():
    """Flush memcache. Pretty self-explanatory."""
    memcache.flush_all()


class User(ndb.Model):
    '''The user entity.'''
    username = ndb.StringProperty(required=True)
    password_hash = ndb.StringProperty(required=True)
    salt = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=False)
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def get_by_name(cls, name):
        #This should never really be called if we're using memcache.
        return User.query(User.username==name).get()


class Post(ndb.Model):
    '''A single wiki entry.'''
    title = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def get_by_title(cls, title):
        #This should never really be called if we're using memcache.
        return Post.query(Post.title==title).get()

class Posts(ndb.Model):
    '''This is a post with a history.'''
    title = ndb.StringProperty(required=True)
    content = ndb.StringProperty(repeated=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    last_modified = ndb.DateTimeProperty(repeated=True)

    @classmethod
    def get_by_title_version(cls, title, version):
        #This should never really be called if we're using memcache.
        ps = Posts.query(Posts.title==title).get()
        if version <= len(ps.content):
            return Post(title=title, content=ps.content[version])
        else:
            return None

    @classmethod
    def get_latest_by_title(cls, title):
        #This should never really be called if we're using memcache.
        ps = Posts.query(Posts.title==title).get()
        if ps is None:
            return None
        else:
            return Post(title=title, content=ps.content[-1])

    @classmethod
    def get_all_versions(cls, title):
        #This should never really be called if we're using memcache.
        return Posts.query(Posts.title==title).get()

    @classmethod
    def add_new(cls, title, content):
        #This should never really be called if we're using memcache.
        p = Posts.query(Posts.title==title).get()
        # modify the content
        cont = p.content
        cont.append(content)
        p.content = cont
        # change last modification time
        l = p.last_modified
        l.append(datetime.datetime.now())
        p.last_modified = l
        p.put()