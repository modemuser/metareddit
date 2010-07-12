from os import path
import ConfigParser
import logging
from myapp.lib.storage import Storage

# calculate the path of the folder this module is in
_this_path = path.abspath(path.dirname(__file__))
_root_path = '/'.join(_this_path.split('/')[:-1])

paths = Storage({
    'config': _root_path,
})

def get_list(string, sep=','):
    return [s.strip() for s in string.split(',')]

config = ConfigParser.ConfigParser()
config.read(path.join(paths.config, 'myapp.ini'))

debug = config.getboolean('Default', 'debug')
compress_js = config.getboolean('Default', 'compress_js')
domain = config.get('Default', 'domain')
smtp_server = config.get('Default', 'smtp_server')
my_email = config.get('Default', 'my_email')

login_cookie = config.get('Auth', 'login_cookie')
cookie_key = config.get('Auth', 'cookie_key')
api_key = config.get('Auth', 'api_key')
google_api_key = config.get('Auth', 'google_api_key')
admins = get_list(config.get('Auth', 'admins'))

paths.log =  path.join(_root_path, config.get('Directories', 'log_dir'))
paths.templates = path.join(_this_path, config.get('Directories', 'template_dir'))
paths.logos = path.join(_this_path, config.get('Directories', 'logo_dir'))

cache_addr = get_list(config.get('Cache', 'cache_addr'))
cache_prefix = config.get('Cache', 'cache_prefix')

#logging
log_filename = path.join(paths.log, 'access.log')
if debug:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO
logging.basicConfig(filename=log_filename, level=log_level)
