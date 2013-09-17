#!/usr/bin/python

import cgi
from urllib import quote
from os import listdir, path, environ

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
	uri = '%s%s' % (environ['SERVER_NAME'], environ['REQUEST_URI'])
	uri = uri[:uri.find('/rips/')] + '/rips/'
	album = quote(album)
	if not path.exists(album):
		print 'album not found: %s' % album
		return
	result = []
	for f in listdir(album):
		f = path.join(album, f)
		if f.endswith('.txt'): continue
		if path.isdir(f): continue
		result.append( f )
	result = sorted(result)
	for image in result:
		url = 'http://%s%s' % (uri, image)
		print url
		print '<br>'

if __name__ == '__main__':
	print "Content-type: text/html"
	print ""
	main()
	print "\n"
