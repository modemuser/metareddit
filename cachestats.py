#!/usr/bin/env python
import commands

cmd = 'echo -e "stats\nquit" | nc 127.0.0.1 11211'
out = commands.getoutput(cmd)
ret = []
fields = ('get_hits', 'get_misses', 'curr_items', 'evictions', 
          'bytes_read', 'bytes_written', 'cmd_get', 'cmd_set')
for s in out.split('\n')[:-1]:
    tuple = s[5:-1].split(' ')
    if tuple[0] in fields:
        ret.append('%s:%s' % (tuple[0], tuple[1]))
print ','.join(ret)
