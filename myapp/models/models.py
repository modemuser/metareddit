from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relation
from werkzeug import cached_property
from myapp.env import session, metadata
from myapp.lib.auth import salt, hashpw


subreddit_table = Table('subreddit', metadata,
    Column('uid', Integer, primary_key=True, autoincrement=True),
    Column('name', String(64)),
    Column('created', DateTime),
    Column('url', String(64), unique=True, index=True),
    Column('title', String(128)),
    Column('over18', Boolean),
    Column('subscribers', Integer),
    Column('id', String(5)),
    Column('description', Text),
    Column('fp_ups', Integer),
    Column('fp_downs', Integer),
    Column('fp_comments', Integer),
    Column('fp_submissions', Integer),
    Column('fp_media', Integer),
    Column('fp_age_oldest', Integer),
    Column('all_age_latest', Integer),
    Column('all_max_score', Integer),
    Column('selfposts', Integer),
    Column('updated', DateTime),
    Column('logo', Boolean)
)

class Subreddit(object):
    pass


subreddit_tags = Table('subreddit_tags', metadata,
    Column('uid', Integer, primary_key=True, autoincrement=True, unique=True, index=True),
    Column('tag_id', Integer, ForeignKey('tag.uid')),    
    Column('subreddit_id', Integer, ForeignKey('subreddit.uid')),
    Column('user_id', Integer, ForeignKey('user.uid'))    
)

class SubredditTag(object):
    @cached_property
    def score(self):
        total = 0
        for v in self.votes:
            total += v.vote
        return total


tag_table = Table('tag', metadata,
    Column('uid', Integer, primary_key=True, autoincrement=True),
    Column('name', String(20), unique=True, index=True)
)

class Tag(object):
    @cached_property
    def score(self):
        return sum(s.score for s in self.subreddits)


user_table = Table('user', metadata,
    Column('uid', Integer, primary_key=True, autoincrement=True),
    Column('name', String(20), unique=True, index=True),
    Column('pwhash', String(64)),
    Column('pwsalt', String(32))
)

class User(object):
    def __init__(self, name, pw):
        self.name = name 
        pwsalt = salt()
        self.pwhash = hashpw(password=pw, salt=pwsalt)
        self.pwsalt = pwsalt
    def is_valid_pw(self, pw):
        if hashpw(pw, self.pwsalt) == self.pwhash:
            return True
        else:
            return False


vote_table = Table('vote', metadata,
    Column('uid', Integer, primary_key=True, autoincrement=True),
    Column('subreddit_tag_id', Integer, ForeignKey('subreddit_tags.uid')),
    Column('user_id', Integer, ForeignKey('user.uid')),
    Column('vote', Integer, default=0)
)

class Vote(object):
    def __init__(self, subreddit_tag_id, user_id):
        self.subreddit_tag_id = subreddit_tag_id
        self.user_id = user_id
        self.vote = 0
    def up(self):
        if self.vote == 1:
            self.vote = 0
        else:
            self.vote = 1
    def down(self):
        if self.vote == -1:
            self.vote = 0
        else:
            self.vote = -1


keyword_table = Table('keyword', metadata,
    Column('uid', Integer, primary_key=True, autoincrement=True),
    Column('keyword', String(20), unique=True, index=True),
    Column('hash', String(10), index=True),
    Column('created', DateTime),
    Column('accessed', DateTime),
)

class Keyword(object):
    def __init__(self, keyword, hash):
        self.keyword = keyword
        self.hash = hash
        self.created = datetime.utcnow()
        self.accessed = datetime.utcnow()


mention_table = Table('mention', metadata,
    Column('uid', Integer, primary_key=True, autoincrement=True),
    Column('keyword_uid', Integer, ForeignKey('keyword.uid')),
    Column('thread_id', String(10)),
    Column('comment_id', String(10)),
    Column('author', String(20)),
    Column('subreddit', String(20)),
    Column('created', DateTime),
)

class Mention(object):
    def get_link(self):
        if self.comment_id is not None:
            str = 'http://www.reddit.com/r/%s/comments/%s/c/%s?context=3'
            return str % (self.subreddit, self.thread_id, self.comment_id)
        else:
            str = 'http://www.reddit.com/r/%s/comments/%s/'
            return str % (self.subreddit, self.thread_id)


monitoring_table = Table('monitoring', metadata,
    Column('uid', Integer, primary_key=True, autoincrement=True),
    Column('keyword_uid', Integer, ForeignKey('keyword.uid')),
    Column('user_uid', Integer, ForeignKey('user.uid')),
)

class Monitoring(object): 
    def __init__(self, user_uid, keyword_uid):
        self.keyword_uid = keyword_uid
        self.user_uid = user_uid



# mapping
session.mapper(Subreddit, subreddit_table, properties={
    'tags': relation(SubredditTag, backref='subreddit')            
})
session.mapper(SubredditTag, subreddit_tags, properties={
    'tag': relation(Tag, backref='subreddits')    
})
session.mapper(Tag, tag_table)
session.mapper(Vote, vote_table, properties={
    'subreddit_tag': relation(SubredditTag, backref='votes'),
    'user': relation(User)
})
session.mapper(User, user_table, properties={
    'tags': relation(SubredditTag, backref='user'),
    'votes': relation(Vote),
    'monitoring': relation(Monitoring)
})
session.mapper(Keyword, keyword_table, properties={
    'mentions': relation(Mention, backref='keyword', order_by=mention_table.c.created.desc()) 
})
session.mapper(Mention, mention_table)
session.mapper(Monitoring, monitoring_table, properties={
    'keyword': relation(Keyword)    
})


