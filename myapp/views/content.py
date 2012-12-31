import httplib2
import random
import time
import urllib
import simplejson as json
from datetime import datetime
from werkzeug import redirect
from werkzeug.exceptions import NotFound
from sqlalchemy import or_
from sqlalchemy.sql.functions import random as sql_random
from myapp.env import session, cache
from myapp.config import config
from myapp.models import Subreddit, Tag, SubredditTag, Keyword, User, Monitoring
from myapp.lib.memoize import memoize, _hash
from myapp.lib.storage import Storage
from myapp.lib.timetool import days_ago
from myapp.lib.utils import serve_response, Pagination, url_for


@memoize('content_view_index', time=30)
def index(request):
    subreddits = session.query(Subreddit)\
                    .filter(Subreddit.subscribers>100)\
                    .filter(Subreddit.fp_submissions==50)\
                    .filter(Subreddit.all_age_latest<31)\
                    .filter(Subreddit.over18==False)\
                    .order_by(sql_random()).limit(30).all()
    logos = session.query(Subreddit)\
            .filter(Subreddit.logo==True)\
            .filter(Subreddit.all_age_latest<90)\
            .filter(Subreddit.over18==False)\
            .filter(Subreddit.subscribers>100)\
            .order_by(sql_random()).limit(30).all()
    return serve_response('index.html', subreddits=subreddits, logos=logos)


def reddits(request, view='cloud', filter='biggest'):
    key = _hash('view_reddits_' + filter + view + ';'.join(['%s:%s' % (k,v) for k,v in request.args.items()]))
    value = cache.get(key)
    if value is not None:
        return value
    subscribers = request.args.get('s') or 100
    page = int(request.args.get('page', 1))
    query = session.query(Subreddit).filter(Subreddit.subscribers>=subscribers).filter(Subreddit.fp_submissions>0)
    if filter == 'new':
        query = query.filter(Subreddit.created>days_ago(90))
    elif filter == 'biggest':
        query = query.filter(Subreddit.subscribers>10000)
    elif filter == 'active':
        query = query.filter(Subreddit.fp_submissions==50).filter(Subreddit.all_age_latest<=7).filter(Subreddit.over18==False)
    elif filter == 'over18':
        query = query.filter(Subreddit.all_age_latest<91).filter(Subreddit.over18==True)
    elif filter == 'inactive':
        query = query.filter(Subreddit.all_age_latest<360).filter(Subreddit.all_age_latest>90)
    elif filter == 'dead':
        query = query.filter(Subreddit.all_age_latest>360)
    elif filter == 'self':
        query = query.filter(Subreddit.selfposts>20)
    elif filter == 'media':
        query = query.filter(Subreddit.fp_media>20)
    elif filter == 'filter':
        q = request.args.get('q')
        t = request.args.get('t')
        l = request.args.get('l') or 1
        o = request.args.get('o')
        if q and len(q) > 2:
            query = query.filter(or_(Subreddit.title.ilike('%'+q+'%'),
                                    Subreddit.url.ilike('%'+q+'%'), 
                                    Subreddit.description.ilike('%'+q+'%')))
        if t:
            tag = session.query(Tag).filter(Tag.name==t).first() 
            query = query.filter(Subreddit.tags.any(SubredditTag.tag == tag))
        query = query.filter(Subreddit.all_age_latest<l)
        if o and o != 'all':
            over18 = True if o == 'True' else False
            query = query.filter(Subreddit.over18==o)
    else:
        query = query.filter(Subreddit.fp_submissions==25)\
                         .filter(Subreddit.all_age_latest==0)\
                         .filter(Subreddit.over18==False)
    if view == 'cloud':
        subreddits = query.order_by(Subreddit.url).all()
        response = serve_response('reddits.html', view=view, filter=filter, subreddits=subreddits, querystring=request.args)
    elif view == 'list':
        query = query.order_by(Subreddit.subscribers.desc())
        pagination = Pagination(query, 50, page, 'reddits')
        response = serve_response('reddits.html', view=view, filter=filter, pagination=pagination, querystring=request.args)
    if not 'response' in locals():
        raise NotFound
    cache.set(key, response, 3600)
    return response


def subreddit(request, name):
    names = name.split('+')
    subreddits = session.query(Subreddit).filter(Subreddit.url.in_(names)).order_by(Subreddit.url).all()
    if not subreddits:
        raise NotFound
    return serve_response('subreddit.html', subreddits=subreddits)


@memoize('content_view_tags', time=30)
def tags(request, view='cloud'):
    tags = session.query(Tag).order_by(Tag.name)
    return serve_response('tags.html', view=view, tags=tags)

def tag(request, name):
    tag = session.query(Tag).filter(Tag.name.ilike(name)).first()
    if not tag:
        raise NotFound
    return serve_response('tag.html', tag=tag)


def monitor(request):
    if request.method == 'POST':
        key = request.form.get('keyword')
        if not key or len(key) < 5 or len(key) > 20:
            raise NotFound()
        keyword = session.query(Keyword).filter(Keyword.keyword.ilike(key)).first()
        if not keyword:
            chars = '1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM'
            hash = ''.join([random.choice(chars) for c in range(5)])
            keyword = Keyword(key, hash)
            session.commit()
        if request.logged_in:
            user = session.query(User).filter(User.name==request.user).first()
            monitored = session.query(Monitoring).filter(Monitoring.user_uid==user.uid).filter(Monitoring.keyword_uid==keyword.uid).first()
            if not monitored:
                m = Monitoring(user.uid, keyword.uid)
                session.commit()
        return redirect(url_for('monitor', hash=keyword.hash, slug=keyword.keyword))
    cachekey = _hash('views_content_monitor')
    cached = cache.get(cachekey)
    if cached:
        return cached
    keys = ['bozarking', 'reddit search', 'jailbait']
    keywords = session.query(Keyword).filter(Keyword.keyword.in_(keys)).all()
    response = serve_response('monitor.html', keywords=keywords)
    cache.set(cachekey, response, 10*60)
    return response


@memoize('content_view_monitor_detail', time=10*60)
def monitor_detail(request, hash, slug=None):
    if slug is not None and slug[-4:] == '.rss':
        template = 'monitor-detail.xml'
        slug = slug[:-4]
    else:
        template = 'monitor-detail.html'
    keyword = session.query(Keyword).filter(Keyword.hash==hash).first()
    if keyword is None:
        raise NotFound()
    return serve_response(template, keyword=keyword)


def user(request, username):
    if request.user != username:
        raise NotFound()
    user = session.query(User).filter(User.name==username).first()
    return serve_response('user.html', user=user)


def user_reddits(request):
    username = request.args.get('user').strip()
    if not username:
        cached = serve_response('stalk.html', username=None)
    else:
        key = _hash('stalk_' + username)
        cached = cache.get(key)
    if cached:
        return cached
    headers = _login()
    reddits = set()
    registered = lastseen = None
    links = comments = {}
    types = ('about', 'comments', 'submitted')
    for type in types:
        url = 'http://www.reddit.com/user/%s/%s.json' % (username, type)
        out = _get_page(url, headers)
        if not out:
            break
        if type == 'about': 
            data = out['data']
            username = data['name']
            registered = datetime.fromtimestamp(data['created_utc']) 
            links = {'karma': data['link_karma']}
            comments = {'karma': data['comment_karma']}
        else:
            ups = downs = 0
            data = out['data']['children']
            count = len(data)
            for i in data:
                date = i['data']['created_utc']
                if lastseen is None or lastseen < date:
                    lastseen = date
                ups += i['data']['ups']
                downs += i['data']['downs']
            reddits.update(set(s['data']['subreddit'] for s in data))
            if type == 'comments':
                comments.update({'ups':ups, 'downs': downs, 'count': count})
            elif type == 'submitted':
                links.update({'ups':ups, 'downs': downs, 'count': count})
    if lastseen is not None:
        lastseen = datetime.fromtimestamp(lastseen)
        reddits = list(reddits)
        reddits.sort(lambda x, y: cmp(x.lower(), y.lower()))
    response = serve_response('stalk.html', 
                                username=username, registered=registered, lastseen=lastseen, 
                                links=Storage(links), comments=Storage(comments), reddits=reddits)
    cache.set(key, response, timeout=24*60*60)
    return response

def _login():
    key = _hash('reddit_login_headers')
    cached = cache.get(key)
    if cached:
        return cached
    username = config.get('Reddit', 'username')
    password = config.get('Reddit', 'password')
    http = httplib2.Http()
    url = 'http://www.reddit.com/api/login/' + username   
    body = {'user': username, 'passwd': password}
    headers = {'Content-type': 'application/x-www-form-urlencoded'}
    response, content = http.request(url, 'POST', headers=headers, body=urllib.urlencode(body))
    headers = {'Cookie': response['set-cookie']}
    cache.set(key, headers, timeout=24*60*60)
    return headers

def _get_page(uri, headers):
    http = httplib2.Http()
    response, content = http.request(uri, 'GET', headers=headers)
    if response['status'] == '200':
        return json.loads(content)
    elif response['status'] >= '500':
        time.sleep(10)
        return _get_page(uri, headers)
    else:
        return None


@memoize('content_view_index', time=30)
def logos(request, view='random'):
    per_page = 30
    query = session.query(Subreddit).filter(Subreddit.logo==True)
    if view == 'all':
        page = int(request.args.get('page', 1))
        query = query.filter(Subreddit.over18==False).order_by(Subreddit.subscribers.desc())
        pagination = Pagination(query, per_page, page, 'logos')
        return serve_response('logos.html', pagination=pagination, view='all')
    elif view == 'over18':
        page = int(request.args.get('page', 1))
        query = query.filter(Subreddit.over18==True).order_by(Subreddit.subscribers.desc())
        pagination = Pagination(query, per_page, page, 'logos')
        return serve_response('logos.html', pagination=pagination, view='over18')
    else:
        logos = query.filter(Subreddit.over18==False).filter(Subreddit.subscribers>100).order_by(sql_random()).limit(per_page).all()
        return serve_response('logos.html', logos=logos, view='random')



