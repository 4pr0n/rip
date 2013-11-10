#!/usr/bin/python

import cgitb; cgitb.enable() # for debugging
import cgi
from urllib import quote
from os import listdir, path, environ

from sys import path as syspath
syspath.append('..')
from sites.DB import DB

def main():
	keys = get_keys()
	if not 'album' in keys:
		print 'no album provided'
		return
	get_urls_for_album(keys['album'])

def get_keys():
	form = cgi.FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = form[key].value
	return keys

def get_urls_for_album(album):
	db = DB()
	cur = db.conn.cursor()
	query = '''
		select path
			from images
			where album in
				(select id from albums where album = ?)
			order by path
		'''
	curexec = cur.execute(query, [album])

	uri = '%s%s' % (environ['SERVER_NAME'], environ['REQUEST_URI'])
	uri = uri[:uri.find('/rips/')] + '/rips/'
	for (image) in curexec.fetchall():
		print 'http://%s%s' % (uri, image[0])
		print '<br>'

if __name__ == '__main__':
	print "Content-type: text/html"
	print ""
	main()
	print "\n"
