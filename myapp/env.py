from mako.lookup import TemplateLookup
from sqlalchemy import MetaData
from sqlalchemy.orm import create_session, scoped_session
from werkzeug import Local, LocalManager
from werkzeug.contrib.cache import MemcachedCache
from myapp.config import paths, cache_addr, cache_prefix


local = Local()
local_manager = LocalManager([local])
application = local('application')

metadata = MetaData()
session = scoped_session(lambda: create_session(application.database_engine,
                         autocommit=False), local_manager.get_ident)


# create a mako template loader for that folder and set the default input
# encoding to utf-8
template_lookup = TemplateLookup(directories=[paths.templates,], input_encoding='utf-8')


cache = MemcachedCache(cache_addr, key_prefix=cache_prefix)
