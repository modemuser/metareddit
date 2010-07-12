import logging
import re
import time
from datetime import datetime, timedelta
from os import path
from myapp.config import paths
from myapp.env import session
from myapp.models import Keyword, Mention, Monitoring
from myapp.lib.memoize import memoize
from myapp.lib.spiderbase import SpiderBase, Delay
from myapp.lib.timetool import unix_string


class Monitor(SpiderBase):

    def __init__(self, username=None, password=None, delay=10, log='monitor.log'):
        #logging
        logfile = path.join(paths.log, log)
        self.logger = logging.getLogger('monitor')
        self.logger.addHandler(logging.FileHandler(logfile))
        self.logger.setLevel(logging.INFO)
        #init
        self.delay = Delay(delay)
        self.spider = SpiderBase(username=username, password=password, delay=self.delay)

    def cleandb(self):
        for k in self._keywords():
            if k.accessed < (datetime.utcnow() - timedelta(30)):
                session.query(Mention)\
                    .filter(Mention.keyword_uid==k.uid)\
                    .delete(synchronize_session=False)
                session.query(Monitoring)\
                    .filter(Monitoring.keyword_uid==k.uid)\
                    .delete(synchronize_session=False)
                session.query(Keyword)\
                    .filter(Keyword.uid==k.uid)\
                    .delete(synchronize_session=False)
            elif len(k.mentions) > 50:
                m = session.query(Mention)\
                        .filter(Mention.keyword_uid==k.uid)\
                        .order_by(Mention.created.desc())\
                        .offset(49).first()
                session.query(Mention)\
                    .filter(Mention.keyword_uid==k.uid)\
                    .filter(Mention.uid<m.uid)\
                    .delete(synchronize_session=False)
        session.commit()

    def monitor_posts(self):
        url = 'http://www.reddit.com/r/all/new.json?sort=new'
        newest = None
        while True:
            seen, after, next_newest = self._scan_posts(url, newest)
            if seen > 20:
                self.delay.more()
            elif seen < 10:
                self.delay.less()
            if seen == 0:
                time.sleep(5)
                after_url = '%s&count=50&after=%s' % (url, after)
                seen = self._scan_posts(after_url, newest)[0]
            newest = next_newest
            self.delay.sleep()

    def _scan_posts(self, url, newest):
        seen = 0
        data = self.spider._get_json(url) 
        posts = data['data']['children']
        after = data['data']['after']
        for i, c in enumerate(posts):
            post = c['data']
            if i == 0:
                next_newest = post['id']
            if post['id'] <= newest:
                seen = len(posts) - i
                break
            title = post['title'].lower()
            selftext = post['selftext'].lower()
            for k in self._mentioned_keywords(title, text2=selftext):
                mention = Mention()
                mention.keyword_uid = k.uid
                mention.thread_id = post['id']
                mention.author = post['author']
                mention.subreddit = post['subreddit']
                mention.created = unix_string(int(post['created_utc']))
        session.commit()
        return (seen, after, next_newest)
    
    def monitor_comments(self):
        url = 'http://www.reddit.com/comments.json'
        newest = None
        while True:
            seen, after, next_newest = self._scan_comments(url, newest)
            if seen > 20:
                self.delay.more()
            elif seen < 10:
                self.delay.less()
            if seen == 0:
                time.sleep(5)
                after_url = '%s?count=50&after=%s' % (url, after)
                seen = self._scan_comments(after_url, newest)[0]
            newest = next_newest
            self.delay.sleep()

    def _scan_comments(self, url, newest):
        seen = 0
        data = self.spider._get_json(url) 
        comments = data['data']['children']
        after = data['data']['after']
        for i, c in enumerate(comments):
            comment = c['data']
            if i == 0:
                next_newest = comment['id']
            if comment['id'] <= newest:
                seen = len(comments) - i - 1
                break
            body = comment['body'].lower()
            for k in self._mentioned_keywords(body):
                mention = Mention()
                mention.keyword_uid = k.uid
                mention.thread_id = comment['link_id'][3:]
                mention.comment_id = comment['id']
                mention.author = comment['author']
                mention.subreddit = comment['subreddit']
                mention.created = unix_string(int(comment['created_utc']))
        session.commit()
        return (seen, after, next_newest)

    def _mentioned_keywords(self, text, text2=None):
        for k in self._keywords():
            regex = re.compile('(^|.*\W)%s($|\W|s$|s\W)' % re.escape(k.keyword), re.IGNORECASE)
            if regex.match(text) or (text2 is not None and regex.match(text2)):
                yield k

    @memoize('monitor_keywords', time=60)
    def _keywords(self):
        keywords = session.query(Keyword).order_by(Keyword.keyword.asc()).all()
        return keywords


