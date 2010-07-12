#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from os import path
import ConfigParser
root_path = path.abspath(path.dirname(__file__))
sys.path.append(root_path)
from myapp.application import MyApp
from werkzeug import DebuggedApplication
from werkzeug.contrib.profiler import ProfilerMiddleware

config = ConfigParser.ConfigParser()
config.read(root_path + '/myapp.ini')
debug = config.getboolean('Default', 'debug')

if debug:
    log = open(root_path + '/log/profile.log', 'w')
    sys.stdout = sys.stderr = log
    application = DebuggedApplication(MyApp(), False)
    application = ProfilerMiddleware(application, stream=log)
else:
    application = MyApp()
