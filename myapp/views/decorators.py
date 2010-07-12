from werkzeug.exceptions import Forbidden, NotFound
from myapp.config import admins, domain


class require_admin(object):
    def __init__(self, f):
        self.f = f
    def __call__(self, *args):
        if args[0].user in admins:
            return self.f(*args)
        else:
            raise NotFound

 
class require_login(object):
    def __init__(self, f):
        self.f = f
    def __call__(self, *args, **kwargs):
        if args[0].logged_in:
            return self.f(*args, **kwargs)
        else:
            raise Forbidden


class require_post(object):
    def __init__(self, f):
        self.f = f
    def __call__(self, *args, **kwargs):
        if args[0].method == 'POST':
            return self.f(*args, **kwargs)
        else:
            raise NotFound


class require_referrer(object):
    def __init__(self, f):
        self.f = f
    def __call__(self, *args, **kwargs):
        if 'Referer' in args[0].headers and args[0].headers['Referer'].startswith('http://%s/' % domain):
            return self.f(*args, **kwargs)
        else:
            raise NotFound


