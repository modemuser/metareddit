import hashlib
from os import urandom
from datetime import datetime, timedelta
from werkzeug import BaseRequest, cached_property
from werkzeug.contrib.securecookie import SecureCookie
from myapp.config import login_cookie, cookie_key, api_key
from myapp.lib.timetool import unixtime


class SecRequest(BaseRequest):
    """A request with a secure cookie session."""

    def logout(self):
        """Log the user out."""
        self.session.pop('username', None)

    def login(self, username):
        """Log the user in."""
        self.session['username'] = username

    @property
    def logged_in(self):
        """Is the user logged in?"""
        return self.user is not None

    @property
    def user(self):
        """The user that is logged in."""
        return self.session.get('username')

    @cached_property
    def session(self):
        data = self.cookies.get(login_cookie)
        if not data:
            return SecureCookie(secret_key=cookie_key)
        return SecureCookie.unserialize(data, cookie_key)


def cookie_expires(hours=24):
    return datetime.utcnow() + timedelta(hours=hours)


def cookie_lifespan(hours=24):
    return hours * 3600


def hashpw(password, salt='default salt'):
    sha = hashlib.sha256()
    sha.update(password + salt)
    return sha.hexdigest()


def salt(length=10):
    return urandom(length).encode('hex')


def generate_token(text, salt=api_key):
    hextime = hex(unixtime())[2:]
    sha = hashlib.sha256()
    sha.update(text + salt + hextime)
    return sha.hexdigest()[:32] + hextime


def is_valid_token(text, token, salt=api_key):
    if not (text and token):
        return False
    hextime = token[-8:]
    sha = hashlib.sha256()
    sha.update(text + salt + hextime)
    if sha.hexdigest()[:32] + hextime == token:
        timedelta = unixtime() - int(hextime, 16)
        if 0 < timedelta < 3600:
            return True
    return False


