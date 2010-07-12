import httplib2
import re
import simplejson as json
from werkzeug.exceptions import NotFound, Forbidden
from myapp.env import session, cache
from myapp.models import Subreddit, Tag, User, SubredditTag, Vote, Keyword, Monitoring
from myapp.lib.auth import cookie_expires, cookie_lifespan, is_valid_token
from myapp.lib.timetool import unix_days_ago
from myapp.lib.utils import serve_response, serve_json, serve_text
from myapp.lib.db.queries import get_user
from myapp.views.decorators import require_login, require_post, require_referrer


disallowed_chars = r'[^a-zA-Z0-9_\-]'

@require_referrer
@require_post
@require_login
def add_tag(request):
    user = session.query(User).filter_by(name=request.user).first()
    todo = request.form.get('todo')
    token = request.form.get('token')
    if not (todo and token):
        raise NotFound
    if not is_valid_token(todo.split('_')[1], token):
        raise Forbidden
    name = '_'.join(todo.split('_')[2:])
    if len(name) > 20 or re.search(disallowed_chars, name):
        raise Forbidden
    return exec_todo(request, user, todo)


@require_referrer
@require_post
@require_login
def vote(request):
    user = session.query(User).filter_by(name=request.user).first()
    todo = request.form.get('todo')
    token = request.form.get('token')
    if not (todo and token):
        raise NotFound
    if not is_valid_token(todo.split('_')[1], token):
        raise Forbidden
    return exec_todo(request, user, todo)    


@require_referrer
def subreddit(request, name):
    subreddit = session.query(Subreddit).filter(Subreddit.url.ilike(name)).first()
    if not subreddit:
        raise NotFound
    return serve_response('api/subreddit.html', subreddit=subreddit)


@require_referrer
def cachedproxy(request, name):
    cached = cache.get('submissions_' + name)
    if cached:
        return cached
    subreddit = session.query(Subreddit).filter(Subreddit.url.ilike(name)).first()
    if not subreddit:
        raise NotFound
    http = httplib2.Http()
    uri = 'http://www.reddit.com/r/%s/.json?limit=5' % name
    response, content = http.request(uri, 'GET')
    if response['status'] == '200':
        out = json.loads(content)
        if out:
            out = out['data']['children']
        if not out:
            r = serve_json('there doesn\'t seem to be anything here.')
        else:
            subreddit.all_age_latest = unix_days_ago(out[0]['data']['created_utc'])
            session.commit()
            r = serve_response('api/submissions.html', submissions=out)
            cache.set('submissions_' + name, r, timeout=60*60)
    else:
        r = serve_json('fetching submissions failed.')
    return r


@require_referrer
def tag(request, name):
    tag = session.query(Tag).filter(Tag.name.ilike(name)).first()
    if not tag:
        raise NotFound
    return serve_response('api/tag.html', tag=tag)


@require_referrer
def autocomplete(request, name):
    query = request.args.get('q')
    if not query:
        raise NotFound
    if name == 'tags':
        res = session.query(Tag).filter(Tag.name.ilike(query+'%')).limit(10)
        suggestions = '\n'.join(r.name for r in res)
    elif name == 'reddits':
        res = session.query(Subreddit).filter(Subreddit.url.ilike(query+'%')).order_by(Subreddit.subscribers.desc()).limit(10)
        suggestions = '\n'.join(r.url for r in res)
    return serve_text(suggestions)

@require_referrer
def user_exists(request):
    name = request.args.get('name')
    if not name:
        raise Forbidden
    user = get_user(name)
    if user is not None:
        return serve_text('username taken.')
    else:
        return serve_text('') 


@require_referrer
@require_post
def login(request):
    type = request.form.get('do')
    token = request.form.get('token')
    username = request.form.get('user')
    passwd = request.form.get('pw')
    if not (username and passwd and type and token) or not is_valid_token(type, token):
        return serve_text('')
    user = get_user(username)
    if type == 'reg' and user is None:
        user = register(username, passwd)
    if user and user.is_valid_pw(passwd):
        request.login(username)
        todo = request.form.get('reason')
        if not todo:
            response = serve_text('ok')
        else:
            response = exec_todo(request, user, todo)   
        #remember user for n hours
        hours = 24 * (30 if request.form.get('rem') == 'on' else 1)
        request.session.save_cookie(response, expires=cookie_expires(hours), max_age=cookie_lifespan(hours))
        return response
    return serve_text('')


def register(username, passwd):
    if re.search(disallowed_chars, username) or len(username)>20 or get_user(username):
        raise Forbidden
    user = User(username, passwd)
    session.commit()
    return user


def exec_todo(request, user, todo):
    r = todo.split('_');
    type = r[0]
    id = r[1]
    action = '_'.join(r[2:])
    if type == 'vote':
        subreddit_tag = session.query(SubredditTag).filter(SubredditTag.uid==id).first()
        if not subreddit_tag:
            raise NotFound
        vote = session.query(Vote).filter(Vote.subreddit_tag_id==id).filter(Vote.user_id==user.uid).first()
        if not vote:
            vote = Vote(subreddit_tag.uid, user.uid)
        if action == 'up':
            vote.up()
        elif action == 'down':
            vote.down()
        else:
            raise NotFound
        session.commit()
        return serve_response('api/bigtag.html', tag=subreddit_tag)
    elif type == 'tag':
        subreddit = session.query(Subreddit).filter_by(id=id).first()
        tag = session.query(Tag).filter_by(name=action).first()
        if not tag:
            tag = Tag()
            tag.user_id = user.uid
            tag.name = action
            session.commit()
        #see if this reddit is tagged already
        subreddit_tag = session.query(SubredditTag)\
                                .filter(SubredditTag.tag_id==tag.uid)\
                                .filter(SubredditTag.subreddit_id==subreddit.uid).first()
        if subreddit_tag:
            #upvote
            vote = session.query(Vote)\
                            .filter(Vote.subreddit_tag_id==subreddit_tag.uid)\
                            .filter(Vote.user_id==user.uid).first()
            if not vote:
                vote = Vote(subreddit_tag.uid, user.uid)
            vote.up()
            session.commit()
            return serve_response('api/bigtag.html', tag=subreddit_tag)
        subreddit_tag = SubredditTag()
        subreddit_tag.tag_id = tag.uid
        subreddit_tag.subreddit_id = subreddit.uid
        subreddit_tag.user_id = user.uid
        subreddit.tags.append(subreddit_tag)
        session.commit()
        vote = Vote(subreddit_tag.uid, user.uid)
        vote.up()
        session.commit()
        return serve_response('api/bigtag.html', tag=subreddit_tag)
    else:
        raise NotFound


@require_referrer
@require_login
def remove_monitoring(request, hash):
    user = session.query(User).filter(User.name==request.user).first()
    keyword = session.query(Keyword).filter(Keyword.hash==hash).first()
    if not user or not keyword:
        raise Forbidden()
    session.query(Monitoring).filter(Monitoring.user_uid==user.uid).filter(Monitoring.keyword_uid==keyword.uid).delete(synchronize_session=False)
    session.commit()
    return serve_json('')

