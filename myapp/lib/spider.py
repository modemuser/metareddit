#!/usr/bin/env python

import httplib2
import logging
import simplejson as json
import time
import urllib
from os import path
from datetime import datetime
from myapp.config import paths
from myapp.env import session
from myapp.models import Subreddit
from myapp.lib.timetool import unix_days_ago, unix_string


class Spider(object):

    def __init__(self, username=None, password=None, log='spider.log'):
        #logging
        logfile = path.join(paths.log, log)
        self.logger = logging.getLogger('spider')
        self.logger.addHandler(logging.FileHandler(logfile))
        self.logger.setLevel(logging.INFO)
        #init
        self.http = httplib2.Http()
        self.delay_exp = 0 #delay between requests is 2**delay_exp, exponential backoff
        if username and password:
            self.login(username, password)
        else:
            self.headers = {}

    def login(self, username, password):
        url = 'http://www.reddit.com/api/login/' + username   
        body = {'user': username, 'passwd': password}
        headers = {'Content-type': 'application/x-www-form-urlencoded'}
        self.logger.info('Login to reddit as ' + username)
        response, content = self.http.request(url, 'POST', headers=headers, body=urllib.urlencode(body))
        self.headers = {'Cookie': response['set-cookie']}

    def _get_json(self, uri):
        try:
            response, content = self.http.request(uri, 'GET', headers=self.headers)
        except httplib2.ServerNotFoundError, e:
            self.logger.error('Reddit is down. ', e)
            self.delay_exp += 1
            time.sleep(2**self.delay_exp)
            self._get_json(uri)
        if response['status'] == '200':
            if self.delay_exp > 0:
                self.delay_exp -= 1
            time.sleep(2**self.delay_exp)
            return json.loads(content)
        elif response['status'] >= '500':
            self.logger.info('%s: %s' % (response['status'], uri))
            self.delay_exp += 1
            time.sleep(2**self.delay_exp)
            self._get_json(uri)
        else:
            self.logger.info('%s: %s' % (response['status'], uri))
            return None

    def get_new(self):
        new_reddits = 0
        first_uri = 'http://www.reddit.com/reddits/new/.json' 
        current_uri = first_uri
        counter = 0
        while True:
            page = self._get_json(current_uri)
            if not page:
                self.logger.error('ERROR retrieving page %s. Spidering aborted.\n'
                        '%s reddits scanned.\n%s new reddits found.' 
                        % (current_uri, counter, new_reddits))
                return
            reddits = page['data']['children']
            for reddit in reddits:
                reddit = reddit['data']
                id = reddit['id']
                s = session.query(Subreddit).filter_by(id=id).first()
                if not s: 
                    self.logger.info('new subreddit: %s' % reddit['url'])
                    new_reddits += 1
                    s = Subreddit()
                s.name = reddit['name']
                s.created = unix_string(int(reddit['created']))
                s.url = reddit['url'][3:-1]
                s.title = reddit['title']
                s.over18 = reddit['over18']
                s.subscribers = reddit['subscribers']
                s.id = reddit['id']
                s.description = reddit['description'] 
                session.commit()
            counter += len(reddits)
            after = page['data']['after']
            current_uri = '%s?count=%s&after=%s' % (first_uri, counter, after)
            if not after:
                self.logger.info('Finished spidering.\n'
                        '%s reddits scanned.\n%s new reddits found.' 
                        % (counter, new_reddits))
                return

    def _analyse(self, reddit):
        out = {}
        url = 'http://www.reddit.com/r/%s/.json' % reddit
        j = self._get_json(url)
        if not j:
            return out
        submissions = j['data']['children']
        if len(submissions) == 0:
            return out
        ups = downs = comments = media = selfposts = 0
        for s in submissions:
            s = s['data']
            ups += s['ups']
            downs += s['downs']
            comments += s['num_comments']
            media += 1 if s['media_embed'] else 0
            selfposts += 1 if s['domain'].split('.')[0] == 'self' else 0
        out.update({'ups':ups, 'downs':downs, 'comments':comments, 'media':media, 'submissions':len(submissions), 'selfposts':selfposts})
        if submissions:
            out['oldest'] = unix_days_ago(submissions[-1]['data']['created_utc'])
            out['latest'] = unix_days_ago(submissions[0]['data']['created_utc'])
        else:
            out['oldest'] = out['latest'] = -1
        return out
    
    def _set_new(self, reddit, new):
        reddit.updated = datetime.utcnow()
        reddit.fp_ups = new['ups']
        reddit.fp_downs = new['downs']
        reddit.fp_comments = new['comments']
        reddit.fp_media = new['media']
        reddit.fp_submissions = new['submissions']
        reddit.selfposts = new['selfposts']
        reddit.fp_oldest = new['oldest']
        reddit.all_age_latest = new['latest']
        session.commit()

    def analyse_one(self, name):
        reddit = session.query(Subreddit).filter(Subreddit.url.ilike(name)).first()
        new = self._analyse(reddit.url)
        if not new:
            return
        self._set_new(reddit, new)
        return

    def analyse_new(self):
        reddits = session.query(Subreddit).filter(Subreddit.updated==None).order_by(Subreddit.uid.asc()).all()
        self.logger.info('Analysing %s new reddits.' % len(reddits))
        for reddit in reddits:
            new = self._analyse(reddit.url)
            if not new:
                continue
            self._set_new(reddit, new)
        return

    def analyse_all(self):
        empty = {'ups':None, 'downs':None, 'comments':None, 'media':None, 
                 'submissions':None, 'selfposts':None, 'oldest':0, 'latest':0}
        reddits = session.query(Subreddit).order_by(Subreddit.uid.asc()).all()
        self.logger.info('Analysing all (%s) reddits.' % len(reddits))
        for reddit in reddits:
            new = self._analyse(reddit.url)
            if new:
                self._set_new(reddit, new)
            else:
                self._set_new(reddit, empty)
        return

