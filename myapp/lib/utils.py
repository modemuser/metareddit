import re
from werkzeug import BaseResponse, cached_property
from mako import exceptions
from myapp.config import debug
from myapp.env import local, template_lookup
from myapp.lib.auth import SecRequest


class Request(SecRequest):
    max_content_length = 1024 * 1024 #1mb
    max_form_memory_size = 1024 * 1024 #1mb

class Response(BaseResponse): pass


def url_for(endpoint, _external=False, **values):
    if values.has_key('slug'):
        disallowed_chars = r'[^a-zA-Z0-9_\-\.]'
        values['slug'] = re.sub(disallowed_chars, '_', values['slug'])
    return local.url_adapter.build(endpoint, values, force_external=_external)


def render_template(templatename, **kwargs):
     return template_lookup.get_template(templatename).render_unicode(**kwargs)


def serve_response(templatename, status=200, **kwargs):
    temp = template_lookup.get_template(templatename)
    kwargs['request'] = local.request
    kwargs['url_for'] = url_for
    try:
        rendered = temp.render_unicode(**kwargs)
    except:
        if debug:
            rendered = exceptions.html_error_template().render()
    if templatename[-4:] == '.xml':
        mimetype = 'application/rss+xml'
    else:
        mimetype = 'text/html'
    return Response(rendered, mimetype=mimetype, status=status)


def serve_json(text):
    return Response(text, mimetype='application/json')


def serve_text(text):
    return Response(text, mimetype='text/html')


class Pagination(object):

    def __init__(self, query, per_page, page, endpoint):
        self.query = query
        self.per_page = per_page
        self.page = page
        self.endpoint = endpoint

    @cached_property
    def count(self):
        return self.query.count()

    @cached_property
    def entries(self):
        return self.query.offset((self.page - 1) * self.per_page) \
                         .limit(self.per_page).all()

    has_previous = property(lambda x: x.page > 1)
    has_next = property(lambda x: x.page < x.pages)
    pages = property(lambda x: max(0, x.count - 1) // x.per_page + 1)

    def previous(self, **kw):
        return url_for(self.endpoint, page=self.page - 1, **kw)

    def next(self, **kw):
        return url_for(self.endpoint, page=self.page + 1, **kw)

