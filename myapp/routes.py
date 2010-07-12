from werkzeug.routing import Rule as WerkzeugRule
from werkzeug.routing import Map, Submount


class Rule(WerkzeugRule):
    """Extends Werkzeug routing to support named routes. Names are the url
    identifiers that don't change, or should not change so often. If the map
    changes when using names, all url_for() calls remain the same.

    The endpoint in each rule becomes the 'name' and a new keyword argument
    'handler' defines the class it maps to. To get the handler, set
    return_rule=True when calling MapAdapter.match(), then access rule.handler.
    """
    def __init__(self, *args, **kwargs):
        self.handler = kwargs.pop('handler', kwargs.get('endpoint', None))
        WerkzeugRule.__init__(self, *args, **kwargs)

    def empty(self):
        """Return an unbound copy of this rule.  This can be useful if you
        want to reuse an already bound URL for another map."""
        defaults = None
        if self.defaults is not None:
            defaults = dict(self.defaults)
        return Rule(self.rule, defaults, self.subdomain, self.methods,
                    self.build_only, self.endpoint, self.strict_slashes,
                    self.redirect_to, handler=self.handler)


url_map = Map([
    Rule('/', endpoint='index', handler='content:index'),
    Rule('/reddits/', endpoint='reddits', handler='content:reddits'),
    Rule('/reddits/<filter>/<view>', endpoint='reddits', handler='content:reddits'),
    Rule('/r/<name>', endpoint='subreddit', handler='content:subreddit'),    
    Rule('/tags/', endpoint='tags', handler='content:tags'),
    Rule('/tags/<view>', endpoint='tags', handler='content:tags'),
    Rule('/t/<name>', endpoint='tag', handler='content:tag'),
    Rule('/monitor', endpoint='monitor', handler='content:monitor'),
    Rule('/monitor/<hash>', endpoint='monitor', handler='content:monitor_detail'),
    Rule('/monitor/<hash>/<slug>', endpoint='monitor', handler='content:monitor_detail'),
    Rule('/stalk', endpoint='stalk', handler='content:user_reddits'),
    Rule('/user/<username>', endpoint='user', handler='content:user'),
    Rule('/logos/', endpoint='logos', handler='content:logos'),
    Rule('/logos/<view>', endpoint='logos', handler='content:logos'),
    
    Rule('/search', endpoint='search', handler='simple:search'),
    Rule('/about', endpoint='about', handler='simple:about'),
    Rule('/help', endpoint='help', handler='simple:help'),
    Rule('/links', endpoint='links', handler='simple:links'),
    Rule('/', subdomain='code', endpoint='code', handler='simple:code'),

    Rule('/login', endpoint='login', handler='access:login'),
    Rule('/logout', endpoint='logout', handler='access:logout'),

    Rule('/admin/', endpoint='admin', handler='admin:index'),
    Rule('/admin/clearcache', endpoint='clearcache', handler='admin:clearcache'),
    Rule('/admin/cleandb', endpoint='cleandb', handler='admin:cleandb'),
    Rule('/admin/restartmonitors', endpoint='restartmonitors', handler='admin:restartmonitors'),
    
    Rule('/robots.txt', handler='simple:robots'),
    Rule('/static/<file>', endpoint='static', build_only=True),
    Rule('/static/<cat>/<file>', endpoint='static', build_only=True),
    
    Submount('/api', [
        Rule('/add_tag', handler='api:add_tag'),
        Rule('/vote', handler='api:vote'),
        Rule('/t/<name>', handler='api:tag'),
        Rule('/r/<name>', handler='api:subreddit'),
        Rule('/login', handler='api:login'),
        Rule('/user', handler='api:user_exists'),
        Rule('/cachedproxy/<name>', handler='api:cachedproxy'),
        Rule('/autocomplete/<name>', handler='api:autocomplete'),
        Rule('/remove_monitoring/<hash>', handler='api:remove_monitoring')
    ])
], strict_slashes=False)

