#!/usr/bin/python

import cgitb
from os import remove, path, listdir, walk, environ
from shutil import rmtree
from urllib import unquote
from json import dumps
from sys import argv, exit

def remove_by_user(user):
	removed = []
	for d in listdir('rips'):
		d = path.join('rips', d)
		if not path.isdir(d): continue
		iptxt = path.join(d, 'ip.txt')
		if not path.exists(iptxt): continue
		f = open(iptxt, 'r')
		ip = f.read().strip()
		f.close()
		if ip == user:
			# Need to remove
			zipfile = '%s%s' % (d, '.zip')
			if path.exists(zipfile):
				remove(zipfile)
				removed.append(zipfile)
			rmtree(d)
			removed.append(d)
	print dumps( {
		'removed' : removed
		} )


def invalidate_ip(ip):
	return not ip.count('.') == 3 or \
			not ip.replace('.', '').isdigit() or \
			len(ip) < 7 or \
			'..' in ip or \
			ip.startswith('.') or \
			ip.endswith('.')

if __name__ == '__main__':
	ip = argv[-1]
	if invalidate_ip(ip):
		print 'not a valid ip: %s' % ip
		exit(1)
	remove_by_user(ip)
