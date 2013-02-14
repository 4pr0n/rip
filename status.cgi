#!/usr/bin/python

import cgitb; cgitb.enable() # for debugging
import cgi # for getting query keys/values
import os, sys, time
import urllib # Decoding url strings

""" Retrieves key/value pairs from query, puts in dict """
def get_keys():
	form = cgi.FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = form[key].value
	if len(keys) == 0 and len(sys.argv) > 1:
		keys['url'] = sys.argv[1]
	return keys

""" Where the magic happens """
def main():
	keys = get_keys()
	if not 'url' in keys: 
		usage()
		return
	given_album = keys['url']
	
	album = urllib.unquote(given_album)
	if not album.startswith('http'): album = 'http://' + album
	
	dir = None
	if 'imgur.com' in album:
		if '#' in album: album = album[:album.find('#')]
		if album.endswith('/'): album = album[:len(album)-1]
		if not '/' in album:
			return
		albumid = album[album.rfind('/')+1:]
		if 'i.imgur.com' in album or \
			 not '/a/' in album and not '.imgur.com' in album or \
			 len(albumid) != 5:
			usage()
			return
			
		dir = 'rips/imgur_' + albumid
	elif 'photobucket.com' in album:
		u = album
		if u.startswith('http://') == -1: u = 'http://' + u
		if u.find('#') != -1: u = u[:u.find('#')]
		if u.find('?') != -1: u = u[:u.find('?')]
		if not u.endswith('/'): u += '/'
		
		if u[:u.find('.')] == 'http://www':
			usage()
			return
		
		i = u.find('/', u.find('/', u.find('/', 8) + 1) + 1)
		j = u.find('/', i + 1)
		if i == -1 or j == -1:
			usage()
			return
		user = u[i+1:j]
		dir = 'rips/photobucket_%s' % (user)
	elif 'flickr.com' in album:
		# get username
		user = 'unknown'
		if u.find('/photos/') != -1:
			user = u[u.find('/photos/') + len('/photos/'):]
			if user.find('/') != -1: user = user[:user.find('/')]
		dir = "rips/flickr_" + user + os.sep
	elif '.deviantart.com' in album:
		if album.startswith('http://'): album = album[7:]
		user = album[:album.find('.')]
		if user.lower() == 'www':
			usage()
			return()
		dir = 'rips/deviantart_' + user
	elif 'imagevenue.com' in album:
		txt = album
		if '?image=' in txt:
			i = txt.find('?image=') + 7
			j = txt.find('_', i)
			if txt.find('.', i) < j:
				j = txt.find('.', i)
			txt = 'imagevenue_' + txt[i:j]
		else:
			txt = 'imagevenue'
		dir = 'rips/' + txt
	elif 'imagebam.com' in album:
		dir = 'rips/imagebam'
	elif 'imagefap.com/pictures/' in album:
		dir = 'rips/imagefap'
		if '/pictures/' in album:
			dir += '_' + album[album.find('/pictures/')+len('/pictures/'):].replace('/', '_')
	elif '.tumblr.com' in album:
		url = album.replace('https://', '')
		url = url.replace('http://', '')
		user = url[:url.find('.')]
		dir = 'rips/tumblr_' + user
	elif 'getgonewild.com/profile/' in album:
		while album.endswith('/'): album = album[:-1]
		user = album[album.rfind('/')+1:]
		dir = 'rips/getgonewild_%s' % user
	elif 'twitter.com/' in album:
		user = album[album.find('twitter.com/') + len('twitter.com/'):]
		if '/' in user: user = user[:user.find('/')]
		dir = 'rips/twitter_%s' % user
		
	if dir == None: 
		#print 'no dir!'
		print ''
	elif os.path.exists(dir + '/log.txt'):
		f = open(dir + '/log.txt', 'r')
		lines = f.read().split('\n')
		if len(lines) <= 1: return
		lastline = lines[len(lines)-2]
		f.close()
		print lastline
	else:
		print ''
		#print 'no log: ' + dir + '/log.txt'

def usage():
	print '*error*'
	
if __name__ == '__main__':
	print "Content-Type: text/html"
	print ""
	main()
	print "\n\n"
