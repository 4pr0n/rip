#!/usr/bin/python

import os, time

def get_size():
	total = 0
	for file in os.listdir('rips'):
		total += os.path.getsize('rips%s%s' % (os.sep, file))
	return total

l = []

for file in os.listdir('rips'):
	p = 'rips%s%s' % (os.sep, file)
	if not os.path.isfile(p) or not p.endswith('.zip'): continue
	l.append( (p, os.path.getctime(p)) )

l.sort(key=lambda tup: tup[1])

print get_size()

while True:
	while get_size() > 50 * 1024 * 1024 * 1024:
		os.remove(l.pop(0)[0])
	time.sleep(60)
