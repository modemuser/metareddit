#!/usr/bin/env python
# run "python manage.py shell" to get an interactive Python interpreter without traceback
from werkzeug import script

def make_app():
    from myapp.application import MyApp
    return MyApp()

def make_shell():
    from myapp import models
    from myapp import env
    from myapp.lib import utils
    application = make_app()
    return locals()

def shell_init_func():
    from myapp.env import session
    from myapp.models import Subreddit

def log_email(funcs, log_filename):
    import logging
    from os import path
    from datetime import datetime
    from myapp.env import cache, paths
    from myapp.lib import emailer
    from myapp.lib.timetool import timetext
    #logging
    logfile = path.join(paths.log, log_filename)
    logger = logging.getLogger('s')
    logger.addHandler(logging.FileHandler(logfile, 'w'))
    logger.setLevel(logging.INFO)
    #start time
    start = datetime.now()
    logger.info('started: ' + start.isoformat(' '))
    for f in funcs: 
        logger.info('executing: ' + f.__name__)
        f()
    #clear cache
    cache.clear()
    logger.info('memcache cleared')
    #end, delta time
    end = datetime.now()
    logger.info('ended: ' + end.isoformat(' '))
    logger.info('took: ' + timetext(end - start, resultion=2))
    #send mail
    f = open(logfile, 'r')
    emailer.sendmail(you='t.misera@gmail.com', subject='[metareddit] spider', body=f.read())
    f.close()
    logger.info('mail sent.')

def spider():
    from myapp.config import config
    from myapp.lib.spider import Spider
    make_app()
    username = config.get('Reddit', 'username')
    password = config.get('Reddit', 'password')
    spider = Spider(username=username, password=password)
    log_email([spider.get_new, spider.analyse_new], 'spider.log')
    fix_relative_links()

def update():
    from myapp.config import config
    from myapp.lib.spider import Spider
    make_app()
    username = config.get('Reddit', 'username')
    password = config.get('Reddit', 'password')
    spider = Spider(username=username, password=password)
    log_email([spider.analyse_all], 'spider.log')

def minify_js():
    from myapp.lib import minify_js
    application = make_app()
    minify_js.main()

def fix_relative_links():
    import re
    from myapp.env import session
    from myapp.models import Subreddit
    make_app() 
    reddits = session.query(Subreddit).filter(Subreddit.description.ilike('%]\(%')).all()
    for r in reddits:
        print r.url
        r.description = re.sub(r'\]\\\(', '](', r.description)
        session.commit()

def monitor_comments():
    from myapp.config import config
    from myapp.lib.monitor import Monitor
    make_app()
    username = config.get('Reddit', 'username')
    password = config.get('Reddit', 'password')
    m = Monitor(username=username, password=password, delay=10)
    m.monitor_comments()

def monitor_posts():
    from myapp.config import config
    from myapp.lib.monitor import Monitor
    make_app()
    username = config.get('Reddit', 'username')
    password = config.get('Reddit', 'password')
    m = Monitor(username=username, password=password, delay=150)
    m.monitor_posts()
    
def cleandb():
    from myapp.lib.monitor import Monitor
    make_app()
    m = Monitor()
    m.cleandb()

def logos():
    from myapp.config import config
    from myapp.lib.logos import Logos
    make_app()
    username = config.get('Reddit', 'username')
    password = config.get('Reddit', 'password')
    l = Logos(username=username, password=password)
    l.get()


action_runserver = script.make_runserver(make_app, use_reloader=True, use_debugger=True)
action_shell = script.make_shell(make_shell)
action_initdb = lambda: make_app().init_database()
action_spider = lambda: spider()
action_update = lambda: update()
action_minify_js = lambda: minify_js()
action_fix_relative = lambda: fix_relative_links()
action_monitor_comments = lambda: monitor_comments()
action_monitor_posts = lambda: monitor_posts()
action_cleandb = lambda: cleandb()
action_logos = lambda: logos()

script.run()
