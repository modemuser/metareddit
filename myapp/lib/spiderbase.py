import httplib2
import simplejson as json
import time
import urllib
from myapp.lib.memoize import memoize


class SpiderBase(object):

    def __init__(self, username=None, password=None, delay=None):
        self.username = username
        self.password = password
        self.delay = delay
        self.http = httplib2.Http()

    @memoize('reddit_login', time=24*60*60)
    def _login(self):
        headers = {}
        if self.username and self.password:
            url = 'http://www.reddit.com/api/login/' + self.username   
            body = {'user': self.username, 'passwd': self.password}
            headers = {'Content-type': 'application/x-www-form-urlencoded'}
            response, content = self.http.request(url, 'POST', headers=headers, body=urllib.urlencode(body))
            headers = {'Cookie': response['set-cookie']}
        return headers

    def _get_json(self, uri):
        try:
            response, content = self.http.request(uri, 'GET', headers=self._login())
        except httplib2.ServerNotFoundError, e:
            self._recurse(uri)
        if response['status'] == '200':
            out = json.loads(content)
            if out is None:
                self._recurse(uri)
            return out
        else:
            self._recurse(uri)

    def _recurse(self, uri):
        self.delay.more_exp()
        self.delay.sleep()
        self._get_json(uri)



class Delay(object):
    def __init__(self, seconds):
        self.delay = seconds
        self.delta = seconds/10
        self.delay_exp = 0
        self.min_delay = 2
    def sleep(self):
        s = self.delay + 2**self.delay_exp
        time.sleep(s)
    def more(self):
        self.delay += self.delta
    def more_exp(self):
        self.delay_exp += self.delta
    def less(self):
        if self.delay > self.min_delay: 
            self.delay -= self.delta
        if self.delay_exp > 0:
            self.delay_exp -= 1



