import httplib2
from BeautifulSoup import BeautifulSoup, SoupStrainer
from myapp.config import paths
from myapp.env import session
from myapp.models import Subreddit
from myapp.lib.spiderbase import SpiderBase, Delay


class Logos(SpiderBase):

    def __init__(self, username=None, password=None):
        SpiderBase.__init__(self, username=username, password=password)
        self.delay = Delay(5)

    def get(self):
        http = httplib2.Http()
        headers = self._login()
        print headers
        images = SoupStrainer('img')
        subreddits = session.query(Subreddit).filter(Subreddit.logo==None).order_by(Subreddit.subscribers.desc()).all()
        for subreddit in subreddits:
            url = 'http://www.reddit.com/r/%s' % subreddit.url
            response, content = http.request(url, headers=headers)
            if response['status'] >= '500':
                self.delay.more_exp()
                print response['status'], subreddit.url
            elif response['status'] >= '400':
                subreddit.logo = False
                session.commit()
            else:
                self.delay.less()
                soup =  BeautifulSoup(content, parseOnlyThese=images)
                img_link = soup.findAll(id='header-img')[0]['src']
                if img_link == 'http://static.reddit.com/reddit.com.header.png':
                    subreddit.logo = False
                else:
                    try:
                        resp, img = http.request(img_link)
                        f = open(paths.logos + '/' + subreddit.url + '.png', "w")
                        f.write(img) 
                        f.close()
                        subreddit.logo = True
                    except:
                        print 'Saving image failed for %s.' % subreddit.url
                session.commit()
            self.delay.sleep()
