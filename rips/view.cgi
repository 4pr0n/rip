#!/usr/bin/python

import cgitb; cgitb.enable() # for debugging
import cgi # for getting query keys/values

from os       import listdir, path, sep, walk, utime, stat
from json     import dumps
from random   import randrange
from datetime import datetime
from time     import strftime

""" Print error in JSON format """
def print_error(text):
	print dumps( { 'error' : text } )

"""
	Where the magic happens.
	Prints JSON response to query.
"""
def main():
	keys = get_keys()
	
	start   = 0
	count   = 20
	after   = ''
	preview = 10
	if 'start' in keys and keys['start'].isdigit():
		start = int(keys['start'])
	if 'count' in keys and keys['count'].isdigit():
		count = int(keys['count'])
	if 'preview' in keys and keys['preview'].isdigit():
		preview = int(keys['preview'])
	if 'after' in keys:
		after = keys['after']
	
	if  'view_all' in keys and keys['view_all'] == 'true':
		# Retrieve list of all albums
		get_all_albums(count, preview, after)

	elif 'view' in keys:
		album = keys['view']
		album = album.replace(' ', '%20')
		get_album(album, start, count)

	elif 'update' in keys:
		if path.exists(keys['update']):
			if not update_file_modified(keys['update']): return
		zipfile = '%s.zip' % keys['update']
		if path.exists(zipfile):
			if not update_file_modified(zipfile): return
		print dumps( { 'date' : utime_to_hrdate(int(strftime('%s'))) } )
		
	else:
		print_error('unsupported method')

def get_all_albums(count, preview_size, after):
	dcount = 0 # Number of albums retrieved & returned to user
	dtotal = 0 # Total number of albums
	dindex = 0 # Current index of last_after
	
	found_after = False # User-specified 'after' was found in list of directories
	# Get directories, sorted by most-recent
	thedirs = []
	for f in listdir('.'):
		if not path.isdir(f): continue
		if not path.exists('%s.zip' % f): continue
		if not found_after and after != '' and f == after: found_after = True
		thedirs.append( (f, path.getmtime(f) ) )
	thedirs = sorted(thedirs, key=lambda k: k[1], reverse=True)
	
	if not found_after: after = '' # Requested 'after' not found, don't look for it
	
	if after == '': 
		hit_after = True
	else:
		hit_after = False
	
	last_after = '' # Last album retrieved
	albums = []
	# Iterate over directories
	for (f, mtime) in thedirs:
		dtotal += 1
		
		# User specified an 'after' and we haven't hit it yet
		if not hit_after:
			if f == after:
				hit_after = True
			dindex += 1
			continue
		
		# We hit the number of albums we're supposed to grab
		if (dcount >= count and count != -1):
			last_after = f
			break
		dindex += 1
		
		result = get_images_for_album(f, 0, -1) # Get all images
		images = result['images']
		if len(images) == 0: continue # Don't consider empty albums
		
		dcount += 1
		
		# Randomless pick 'preview_size' number of thumbnails
		rand = []
		if len(images) <= preview_size:
			rand = xrange(0, len(images))
		else:
			while len(rand) < preview_size:
				i = randrange(len(images) - 1)
				if not i in rand:
					rand.append(i)
			rand.sort()
		preview = []
		for i in rand:
			preview.append( images[i] )
		# Add album to response
		albums.append( {
			'album'  : f,
			'images' : preview,
			'total'  : result['total'],
			'time'   : path.getmtime(f)
		})
	
	if dindex == len(thedirs):
		last_after = ''
	
	# Dump response
	print dumps( { 
		'albums' : albums,
		'total'  : len(thedirs),
		'after'  : last_after,
		'index'  : dindex,
		'count'  : dtotal
		} )

def get_thumb(img):
	fs = img.split(sep)
	fs.insert(-1, 'thumbs')
	f = sep.join(fs)
	if not path.exists(f.replace('%25', '%')):
		return 'nothumb.png'
	return sep.join(fs)
	
def get_images_for_album(album, start, count, thumbs=False):
	if not path.exists(album):
		return {
			'images'  : [],
			'count'   : 0,
			'album'   : '[not found]',
			'archive' : './'
		}
	result = {}
	images = []
	dstart = 0
	dcount = 0
	dtotal = 0
	while album.endswith(sep): album = album[:-1]
	for roots, dirs, files in walk(album):
		if thumbs and not roots.endswith('/thumbs'): continue
		if not thumbs and roots.endswith('/thumbs'): continue
		files.sort()
		for f in files:
			if f.endswith('.txt'): continue
			if dstart >= start and (dcount < count or count == -1):
				image = '%s%s%s' % (roots, sep, f)
				image = image.replace('%', '%25')
				images.append( { 
						'image' : image, 
						'thumb' : get_thumb(image) 
					})
				dcount += 1
			dstart += 1
			dtotal += 1

	result['images']  = images
	result['total']   = dtotal
	result['start']   = start
	result['count']   = dcount
	result['album']   = album
	result['archive'] = './%s.zip' % album
	return result

def get_album(album, start, count):
	result = get_images_for_album(album, start, count)
	if path.exists(album):
		update_file_modified(album)
		zipfile = '%s.zip' % album
		if path.exists(zipfile):
			update_file_modified(zipfile)
	print dumps( { 'album' : result } )

def utime_to_hrdate(utime):
	dt = datetime.fromtimestamp(utime)
	return dt.strftime('%Y-%m-%d %H:%M:%S')

def utime_to_hrdate2(utime):
	dt = datetime.fromtimestamp(utime)
	delta = dt - datetime.now()
	result = ''
	if delta.days > 0:
		result += '%dd' % delta.days
	s = delta.seconds
	if s > 3600:
		result += ' %dh' % (s / 3600)
	s = s % 3600
	if s > 60:
		result += ' %dm' % (s / 60)
	s = s % 60
	if s > 0:
		result += ' %ds' % (s)
	return result
		
	
""" Updates system 'modified time' for file to current time. """
def update_file_modified(f):
	st = stat(f)
	atime = int(st.st_atime)
	mtime = int(strftime('%s'))
	try:
		utime(f, (atime, mtime))
	except Exception, e:
		return False
	return True

""" Retrieves key/value pairs from query, puts in dict """
def get_keys():
	form = cgi.FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = form[key].value
	return keys

def get_logs(album, lines):
	recents = []
	try:
		f = open('%s/log.txt', 'r')
		recents = tail(f, lines=lines)
		f.close()
	except:  pass
	
	print dumps( { 
		'recent' : recents
		} )

""" Tail a file and get X lines from the end """
def tail(f, lines=1, _buffer=4098):
	lines_found = []
	block_counter = -1
	while len(lines_found) < lines:
			try:
					f.seek(block_counter * _buffer, SEEK_END)
			except IOError:  # either file is too small, or too many lines requested
					f.seek(0)
					lines_found = f.readlines()
					break
			lines_found = f.readlines()
			if len(lines_found) > lines:
					break
			block_counter -= 1
	result = [word.strip() for word in lines_found[-lines:]]
	result.reverse()
	return result

""" Entry point. Print leading/trailing characters, executes main() """
if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	main()
	print "\n"

