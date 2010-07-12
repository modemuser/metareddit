from myapp.lib.memoize import memoize
from myapp.lib.utils import serve_response, serve_text


@memoize('view_simple_search')
def search(request):
    return serve_response('search.html')


@memoize('view_simple_about')
def about(request):
    return serve_response('about.html')


@memoize('view_simple_help')
def help(request):
    return serve_response('help.html')


@memoize('view_simple_links')
def links(request):
    return serve_response('links.html')


@memoize('view_simple_robots')
def robots(request):
    txt = 'User-agent: * \nDisallow: /login \nDisallow: /api/ \nAllow: /'
    return serve_text(txt)


def code(request):
    return serve_text('bla')
    

def not_found(request, error):
    return serve_response('error.html', status=404, error=error)

