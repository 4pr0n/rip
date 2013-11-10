#!/usr/bin/python

from os import path, listdir
from time import mktime, gmtime
from sys import path as syspath
from shutil import move

syspath.append('..')
from rip import get_ripper
from sites.DB import DB
db = DB()

for f in listdir('.'):
	if not path.isdir(f): continue # Not a dir
	f = path.join('rips', f)
	count = db.count('id', 'albums', 'album = ?', [f])
	if count == 1: continue # Already in db

	txt = path.join('..', f, 'log.txt')
	url = None
	if not path.exists(txt) and '/gonewild_' in f:
		url = 'http://reddit.com/user/%s' % (f[f.find('_')+1:])
	else:
		for line in open(txt, 'r'):
			if 'file log for URL ' not in line: continue
			line = line.strip()
			url = line[line.find('file log for URL ')+len('file log for URL '):]
			if ' @ ' in url: url = url[:url.find(' @ ')]
	if url == None: continue

	txt = path.join('..', f, 'ip.txt')
	ip = '127.0.0.1'
	if path.exists(txt):
		fil = open(txt, 'r')
		ip = fil.read().strip()
		fil.close()
	print f, url, ip
	try:
		ripper = get_ripper(url, ip=ip)
	except Exception, e:
		print str(e)
		continue
	print ripper.working_dir
	if ripper.db.count('id', 'albums', 'album = ?', [ripper.album_name]) == 0:
		# Not in DB
		ripper.add_existing_album_to_db()
		ripper.db.update_album(ripper.album_name)

for url in open('../recent_rips.lst', 'r'):
	url = url.strip()
	print 'adding:',url
	try:
		ripper = get_ripper(url, ip='127.0.0.1')
	except Exception, e:
		print str(e)
		continue
	if db.count('url', 'recent', 'url = ?', [url]) == 0:
		db.add_recent(url, ripper.album_name, '127.0.0.1')
db.commit()
