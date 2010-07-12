import calendar
import math
import time
from datetime import datetime, timedelta


def unixtime():
    return int(time.time())

def currentyear():
    return datetime.now().year

def days_ago(days):
    return datetime.utcnow() - timedelta(days=days)

def unix_timesince(unix):
    return timesince(datetime.fromtimestamp(unix))

def unix_string(unix):
    return time.strftime('%Y-%m-%d %H:%M', time.gmtime(unix))

def unix_days_ago(unix):
    now = calendar.timegm(time.gmtime())
    diff =  now - unix
    return int(diff / (60 * 60 * 24))


WEEKDAY = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
}

def timetext(delta, resultion=1, bare=True):
    
    chunks = (
      (60 * 60 * 24 * 365, lambda n: _ungettext('year', 'years', n)),
      (60 * 60 * 24 * 30, lambda n: _ungettext('month', 'months', n)),
      (60 * 60 * 24, lambda n : _ungettext('day', 'days', n)),
      (60 * 60, lambda n: _ungettext('hour', 'hours', n)),
      (60, lambda n: _ungettext('minute', 'minutes', n)),
      (1, lambda n: _ungettext('second', 'seconds', n))
    )
    delta = max(delta, timedelta(0))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    for i, (seconds, name) in enumerate(chunks):
        count = math.floor(since / seconds)
        if count != 0:
            break
    s = '%(num)d %(time)s' % dict(num=count, time=name(int(count)))
    if resultion > 1:
        if i + 1 < len(chunks):
            # Now get the second item
            seconds2, name2 = chunks[i + 1]
            count2 = (since - (seconds * count)) / seconds2
            if count2 != 0:
                s += ', %d %s' % (count2, name2(count2))
    if not bare: s += ' ago'
    return s

def _ungettext(singular, plural, n):
    if n == 1:
        return singular
    else:
        return plural

def timesince(d, resultion=1, bare=True):
    return timetext(datetime.utcnow() - d, resultion, bare)

def timeuntil(d, resultion=1, bare=True):
    return timetext(d - datetime.utcnow(), resultion, bare)

