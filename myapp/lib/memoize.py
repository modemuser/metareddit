import hashlib
from myapp.env import cache

class NoneResult(object): pass

def memoize(iden, time=3600):
    def memoize_fn(fn):
        def new_fn(*a, **kw):
            key = _make_key(iden, a, kw)
            res = cache.get(key)
            if res is None:
                res = fn(*a, **kw)
                if res is None:
                    res = NoneResult
                cache.set(key, res, time)
            if res == NoneResult:
                res = None
            return res
        return new_fn
    return memoize_fn


def clear_memo(iden, *a, **kw):
    key = _make_key(iden, a, kw)
    cache.delete(key)


def _make_key(iden, a, kw):
    return _hash(
        iden 
        + str([str(x) for x in a])
        + str([(str(x), str(y)) for (x,y) in sorted(kw.iteritems())])
    )

def _hash(string):
    sha = hashlib.sha256()
    sha.update(string)
    return sha.hexdigest()
