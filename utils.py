#!/usr/bin/env python

import re, random, string
import hashlib
import hmac
import mydb


def hash_str(s):
    """Create SHA256 hash"""
    return hashlib.sha256(s).hexdigest()

#This should not be stored here but I'm not planning to use this program for world domination so it's fine.
secret = 'MvzGTrleqoBLnwyXgCmQUbAcOpVDRNYFhxWPifksSIJtujZadE' #"".join(random.sample(string.letters, 50))


def make_secure_val(s):
    """Create secure value to be used for cookie."""
    return "%s|%s" % (s, hmac.new(secret, s).hexdigest())


def check_secure_val(h):
    """Check that the secure value in the cookie is correct."""
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val


def make_salt():
    """Create salt for someone's password."""
    # This could probably be more complicated and stored separately, but again, no world domination this time.
    return ''.join(random.sample(string.letters, 5))


def make_pw_hash(name, pw, hsh=None):
    """Create a hash for the password that will be stored for each user."""
    if hsh:
        salt = hsh.split('|')[1] #if there's already a password, use its salt
    else:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s|%s' % (h, salt)


def valid_pw(name, pw, h):
    """Check if the password is valid."""
    new_h = make_pw_hash(name, pw, h)
    return new_h == h


def valid_uname(uname):
    """Check if the username is valid."""
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return USER_RE.match(uname)


def valid_psswrd(psswrd):
    """Check if the password is valid."""
    PSSWRD_RE = re.compile(r"^.{3,20}$")
    return PSSWRD_RE.match(psswrd)


def valid_email(email):
    """Check if the email address is valid."""
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
    return EMAIL_RE.match(email)


def verify_psswrd(orig, rep):
    """Check if the two passwords entered by the user match."""
    return orig == rep


def user_exists(uname):
    """Check if the username already exists."""
    #q = mydb.User.get_by_name(uname)
    q = mydb.single_user_by_name(uname)
    return not(q is None)
