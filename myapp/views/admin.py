import commands
from datetime import datetime
from myapp.env import cache
from myapp.lib.monitor import Monitor
from myapp.lib.utils import serve_response, serve_text
from myapp.views.decorators import require_admin


@require_admin
def index(request):
    return serve_response('admin.html')


@require_admin
def clearcache(request):
    cache.clear()
    #cache.delete('view_simple_search')
    #cache.delete('view_simple_about')
    #cache.delete('view_simple_links')
    #cache.delete('view_simple_robots')
    return serve_text('cache cleared: ' + datetime.now().isoformat(' '))


@require_admin
def cleandb(request):
    rm = Monitor()
    rm.cleandb()
    return serve_text('db cleaned: ' + datetime.now().isoformat(' '))


@require_admin
def restartmonitors(request):
    out = commands.getoutput('supervisorctl -c /home/www/vhost/metareddit/supervisord.conf restart all')
    return serve_text('monitors restarted: ' + out)

