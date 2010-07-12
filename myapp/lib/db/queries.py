from myapp.env import session
from myapp.models import User, Subreddit
from myapp.lib.memoize import memoize


def get_user(username):
    return session.query(User).filter_by(name=username).first()


@memoize('query_total_reddit_count')
def total_reddit_count():
    return session.query(Subreddit).count()
