import re
from sqlalchemy import create_engine
from werkzeug import ClosingIterator, import_string
from werkzeug.exceptions import HTTPException, NotFound
from myapp.config import config, logging, domain
from myapp.env import session, metadata, local, local_manager
from myapp.routes import url_map
from myapp.lib.utils import Request
from myapp.views.simple import not_found


class MyApp(object):

    def __init__(self):
        local.application = self
        user = config.get('Database', 'user')
        pw   = config.get('Database', 'pw')
        host = config.get('Database', 'host')
        db   = config.get('Database', 'db')
        db_uri = 'postgres://%s:%s@%s/%s' % (user, pw, host, db)
        self.database_engine = create_engine(db_uri, convert_unicode=True)
    
    def init_database(self):
        metadata.create_all(self.database_engine)

    def dispatch(self, environ, start_response):
        local.application = self
        local.request = request = Request(environ)
        logging.info('[request %s]' % request)
        local.url_adapter = adapter = url_map.bind_to_environ(environ, server_name=domain)
        try:
            rule, args = adapter.match(return_rule=True)
            handler = import_string('myapp.views.' + rule.handler)
            response = handler(request, **args)
        except NotFound:
            error = {'title': '404 Not Found', 'msg': 'Please check URL.'}
            response = not_found(request, error)
        except HTTPException, e:
            response = e
        if not request.is_xhr:
            #fill in placeholder so caching works
            from myapp.views import placeholder
            if request.logged_in:
                header_bottom_right = placeholder.header(username=request.user)
                highlight = popup =  ''
            else:
                header_bottom_right = placeholder.header()
                popup = placeholder.popup()
                try:
                    highlight = placeholder.highlight(rule.endpoint)
                except:
                    highlight = ''
            response.data = re.sub('{% header %}', header_bottom_right, response.data, 1)
            response.data = re.sub('{% highlight %}', highlight, response.data, 1)
            response.data = re.sub('{% popup %}', popup, response.data, 1)
        return ClosingIterator(response(environ, start_response),
                               [session.remove, local_manager.cleanup])
    
    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)


