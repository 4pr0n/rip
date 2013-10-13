#!/usr/bin/python

import cgitb; cgitb.enable() # for debugging
import cgi # for getting query keys/values

from os       import listdir, path, walk, utime, stat, environ, remove, chdir
from json     import dumps
from random   import randrange
from datetime import datetime
from time     import time
from urllib   import quote, unquote
from shutil   import rmtree
sep = '/'
##################
# MAIN

def main(): # Prints JSON response to query
	keys = get_keys()
	
	if path.exists('rips') and path.exists(path.join('rips', 'view.cgi')):
		chdir('rips')

	# Gets keys or defaults
	start   = int(keys.get('start',   0))   # Starting index (album/images)
	count   = int(keys.get('count',   20))  # Number of images/thumbs to retrieve
	preview = int(keys.get('preview', 10))  # Number of images to retrieve
	after   =     keys.get('after',   '')   # Next album to retrieve
	blacklist =   keys.get('blacklist', '') # Album to blacklist

	# Get from list of all albums
	if  'view_all' in keys: get_all_albums(count, preview, after)

	# Get images from one album
	elif 'view'          in keys: get_album(keys['view'].replace(' ', '%20'), start, count)
	# Get URLs for an album
	elif 'urls'          in keys: get_urls_for_album(keys['urls'])
	# Get albums ripped by a user
	elif 'user'          in keys: get_albums_for_user(keys['user'], count, preview, after)
	# Report an album
	elif 'report'        in keys: report_album(keys['report'], reason=keys.get('reason', ''))
	# Get from list of reported album
	elif 'get_report'    in keys: get_reported_albums(count, preview, after)
	# Remove all reports or an album
	elif 'clear_reports' in keys: clear_reports(keys['clear_reports'])
	# Delete an album, add to blacklist
	elif 'delete'        in keys: delete_album(keys['delete'], blacklist)
	# Delete all albums from a user
	elif 'delete_user'   in keys: delete_albums_by_user(keys['delete_user'], blacklist)
	# Permanently ban a user
	elif 'ban_user'      in keys: ban_user(keys['ban_user'], reason=keys.get('reason', ''), length=keys.get('length', 'temporary'))

	# Unexpected key(s)
	else: print_error('unsupported method(s)')


###################
# ALBUMS

def get_all_albums(count, preview_size, after):
	found_after = False # User-specified 'after' was found in list of directories
	# Get directories and timestamps
	thedirs = []
	for f in listdir('.'):
		if not path.isdir(f): continue
		if not path.exists('%s.zip' % f): continue
		if not found_after and after != '' and f == after: found_after = True
		thedirs.append( (f, path.getmtime(f) ) )
	# Sort by most recent
	thedirs = sorted(thedirs, key=lambda k: k[1], reverse=True)
	
	# Strip out timestamp
	for i in xrange(0, len(thedirs)):
		thedirs[i] = thedirs[i][0]
	
	# Filter results
	filter_albums(thedirs, count, preview_size, after, found_after)


def get_albums_for_user(user, count, preview_size, after):
	found_after = False # User-specified 'after' was found in list of directories
	# Get directories and timestamps
	thedirs = []
	for f in listdir('.'):
		if not path.isdir(f): continue
		if not path.exists('%s.zip' % f): continue
		if not found_after and after != '' and f == after: found_after = True
		iptxt = path.join(f, 'ip.txt')
		if not path.exists(iptxt): continue
		fil = open(iptxt, 'r')
		ip = fil.read().strip()
		fil.close()
		if user == 'me' and ip != environ['REMOTE_ADDR']: continue
		if user != 'me' and ip != user: continue
		thedirs.append( (f, path.getmtime(f) ) )
	
	# Sort by most recent
	thedirs = sorted(thedirs, key=lambda k: k[1], reverse=True)
	
	# Strip out timestamp
	for i in xrange(0, len(thedirs)):
		thedirs[i] = thedirs[i][0]
	
	# Filter results
	filter_albums(thedirs, count, preview_size, after, found_after)
	

def get_reported_albums(count, preview_size, after):
	if not is_admin():
		print_error('')
		return
	
	found_after = False # User-specified 'after' was found in list of directories
	# Get reported directories & number of reports
	thedirs = []
	for f in listdir('.'):
		if not path.isdir(f): continue
		reportstxt = path.join(f, 'reports.txt')
		if not path.exists(reportstxt): continue
		if not found_after and after != '' and f == after: found_after = True
		fil = open(reportstxt, 'r')
		reports = fil.read().split('\n')
		fil.close()
		thedirs.append( (f, len(reports) ) )
	
	# Sort by most recent
	thedirs = sorted(thedirs, key=lambda k: int(k[1]), reverse=True)
	
	# Strip out timestamp
	for i in xrange(0, len(thedirs)):
		thedirs[i] = thedirs[i][0]
	
	# Filter results
	filter_albums(thedirs, count, preview_size, after, found_after)


def filter_albums(thedirs, count, preview_size, after, found_after):
	dcount = 0 # Number of albums retrieved & returned to user
	dtotal = 0 # Total number of albums
	dindex = 0 # Current index of last_after
	
	admin = is_admin()
	if not found_after: after = '' # Requested 'after' not found, don't look for it
	
	if after == '': 
		hit_after = True
	else:
		hit_after = False
	
	last_after = '' # Last album retrieved
	albums = []
	# Iterate over directories
	for f in thedirs:
		dtotal += 1
		
		# Check if we hit the 'after' specified by request
		if f == after:
			hit_after = True
		
		if not hit_after:
			# Haven't hit 'after' yet, keep iterating
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
		
		dcount += 1 # Increment number of albums retrieved
		
		# Randomly pick 'preview_size' number of thumbnails from the album
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
		
		album_result = {
			'album'  : f,
			'images' : preview,
			'total'  : result['total'],
			'time'   : path.getmtime(f)
		}

		# Retrieve number of reports if user is admin
		if admin:
			rtxt = path.join(f, 'reports.txt')
			if path.exists(rtxt):
				fil = open(rtxt, 'r')
				album_result['reports'] = len(fil.read().strip().split('\n'))
				fil.close()
		# Add album to response
		albums.append( album_result )
	
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


def sizeof_fmt(num):
    for x in ['bytes','KB','MB','GB','TB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0

# Attempts to guess URL from album name
def guess_url(album):
	fields = album.split('_')
	if album.startswith('kodiefiles_'): return '' # No way to find the date
	if album.startswith('photobucket_'): return '' # Unable to determine server, subdir, etc.
	# Simple one-to-one correspondence
	if album.startswith('500px_'): return 'http://500px.com/%s' % '_'.join(fields[1:])
	if album.startswith('cghub_'): return 'http://%s.cghub.com/images/' % '_'.join(fields[1:])
	if album.startswith('nfsfw_'): return 'http://nfsfw.com/gallery/v/%s' % '_'.join(fields[1:])
	if album.startswith('4chan_'): return 'http://boards.4chan.org/%s/res/%s' % (fields[1], fields[2])
	if album.startswith('setsdb_'): return 'http://setsdb.org/%s/' % '_'.join(fields[1:])
	if album.startswith('imgbox_'): return 'http://imgbox.com/g/%s' % '_'.join(fields[1:])
	if album.startswith('reddit_'): return 'http://www.reddit.com/user/%s' % '_'.join(fields[1:])
	if album.startswith('soupio_'): return 'http://redditsluts.soup.io/tag/%s' % '_'.join(fields[1:])
	if album.startswith('anonib_'): return 'http://www.anonib.com/%s/res/%s.html' % (fields[1], fields[2])
	if album.startswith('twitter_'): return 'http://twitter.com/%s' % '_'.join(fields[1:])
	if album.startswith('fuskator_'): return 'http://fuskator.com/full/%s/' % '_'.join(fields[1:])
	if album.startswith('gonewild_'): return 'http://www.reddit.com/user/%s' % '_'.join(fields[1:])
	if album.startswith('imagebam_'): return 'http://www.imagebam.com/gallery/%s' % '_'.join(fields[1:])
	if album.startswith('imagearn_'): return 'http://imagearn.com/gallery.php?id=%s' % fields[-1]
	if album.startswith('imagefap_'): return 'http://www.imagefap.com/gallery.php?gid=%s' % fields[-1]
	if album.startswith('xhamster_'): return 'http://xhamster.com/photos/gallery/%s/asdf.html' % fields[-1]
	if album.startswith('instagram_'): return 'http://instagram.com/%s' % '_'.join(fields[1:])
	if album.startswith('shareimage_'): return 'www.share-image.com/%s-asdf' % '_'.join(fields[1:])
	if album.startswith('buttoucher_'): return 'http://butttoucher.com/users/%s' % '_'.join(fields[1:])
	if album.startswith('getgonewild_'): return 'http://www.getgonewild.com/profile/%s' % '_'.join(fields[1:])
	if album.startswith('gallerydump_'): return 'http://www.gallery-dump.com/index.php?gid=%s' % fields[-1]
	# Semi-complicated
	if album.startswith('deviantart_'): 
		if len(fields) == 2:
			return 'http://%s.deviantart.com/gallery/' % fields[1]
		else:
			return 'http://%s.deviantart.com/gallery/%s' % (fields[1], fields[2])
	if album.startswith('chansluts_'):
		fields.insert(-1, 'res')
		return 'http://www.chansluts.com/%s.php' % '/'.join(fields[1:])
	if album.startswith('flickr_'):
		if len(fields) > 2:
			return 'http://www.flickr.com/photos/%s/sets/%s/' % (fields[1], fields[2])
		else:
			return 'http://www.flickr.com/photos/%s/' % fields[1]
			
	# Complicated
	if album.startswith('minus_'):
		if len(fields) > 2:
			if fields[1] == 'guest':
				fields[1] = ''
			else:
				fields[1] += '.'
			return 'http://%sminus.com/%s' % (fields[1], fields[2])
	if album.startswith('tumblr_'):
		if len(fields) > 2: # Uses tags
			return 'http://%s.tumblr.com/tagged/%s' % (fields[1], '_'.join(fields[2:]))
		else: # No tags
			return 'http://%s.tumblr.com/' % fields[-1]
	# More complicated
	if album.startswith('teenplanet_'):
		if 'Latino' in fields and 'M4N' in fields:
			fields.remove('Latino')
			fields.remove('M4N')
			fields.insert(1, 'Latino_M4N')
		elif 'AF' in fields and 'Pix' in fields:
			fields.remove('AF')
			fields.remove('Pix')
			fields.insert(1, 'AF_Pix')
		return 'http://photos.teenplanet.org/atomicfrog/%s/%s' % (fields[1], '_'.join(fields[2:]))
	if album.startswith('imgur_'):
		if len(fields) == 2: # Album or user
			if len(fields[1]) == 5: # probably an album
				return 'http://imgur.com/a/%s' % fields[1]
			else: # probably a user
				return 'http://%s.imgur.com/' % fields[1]
		elif fields[1] == 'r': # Subreddit
			return 'http://imgur.com/%s' % '/'.join(fields[1:])
	return ''
	
	
##################
# SINGLE ALBUM
def get_images_for_album(album, start, count, thumbs=False):
	if not path.exists(album):
		return {
			'images'  : [],
			'count'   : 0,
			'album'   : '[not found]',
			'guess'   : guess_url(album),
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
	result['album']   = album.replace('%20', ' ')
	result['size']    = sizeof_fmt(path.getsize('./%s.zip' % album))
	result['archive'] = './%s.zip' % album.replace(' ', '%20').replace('%20', '%2520')
	return result


def get_album(album, start, count):
	result = get_images_for_album(album, start, count)
	if start == 0:
		update_album(album) # Mark album as recently-viewed
	result['url'] = get_url_for_album(album)
	if start == 0 and is_admin():
		result['report_reasons'] = get_report_reasons(album)
		iptxt = path.join(album, 'ip.txt')
		if path.exists(iptxt):
			f = open(iptxt, 'r')
			ip = f.read()
			f.close()
			result['user'] = ip
	print dumps( { 'album' : result } )


# Return external URL for album that was ripped
def get_url_for_album(album):
	logtxt = path.join(album, 'log.txt')
	if not path.exists(logtxt): return ''
	f = open(logtxt, 'r')
	lines = f.read().split('\n')
	f.close()
	if len(lines) == 0: return ''
	url = lines[0]
	if not ' ' in url: return ''
	if ' @ ' in url:
		url = url[:url.rfind(' @ ')]
	return url[url.rfind(' ')+1:]


# Return all URLs for an album
def get_urls_for_album(album):
	album = quote(album)
	if not path.exists(album):
		print dumps( { 'urls' : [] } )
		return
	result = []
	for f in listdir(album):
		f = path.join(album, f)
		if f.endswith('.txt'): continue
		if f.endswith('.html'): continue
		if path.isdir(f): continue
		result.append( f )
	result = sorted(result)
	print dumps( { 'urls' : result } )


#############
# REPORT
def report_album(album, reason=""):
	album = quote(album)
	if '..' in album or '/' in album or not path.isdir(album):
		print_error('unable to reported: invalid album specified')
		return
	if not path.exists(album):
		print_error('album does not exist: %s' % album)
		return
	reports = path.join(album, 'reports.txt')
	if path.exists(reports):
		f = open(reports, 'r')
		lines = f.read().split('\n')
		f.close()
		for line in lines:
			if line.startswith(environ['REMOTE_ADDR']):
				print_warning('you (%s) have already reported this album' % environ['REMOTE_ADDR'])
				return
	try:
		f = open(reports, 'a')
		f.write('%s:%s\n' % (environ['REMOTE_ADDR'], reason))
		f.close()
	except Exception, e:
		print_error('unable to report album: %s' % str(e))
		return

	print_ok('this album has been reported. the admins will look into this soon')


def get_report_reasons(album):
	# Sanitization, check if album
	if '..' in album or '/' in album or not path.isdir(album):
		return []
	# No album
	if not path.exists(album):
		return []
	# No reports
	reports = path.join(album, 'reports.txt')
	if not path.exists(reports):
		return []
	f = open(reports, 'r')
	lines = f.read().split('\n')
	f.close()
	reasons = []
	for line in lines:
		if line.strip() == '': continue
		ip = line[:line.find(':')]
		reason = line[line.find(':')+1:]
		reasons.append( {
			'user'   : ip,
			'reason' : reason
		} )
	return reasons

def clear_reports(album):
	if not is_admin():
		print_error('you are not an admin: %s' % environ['REMOTE_ADDR'])
		return
	album = quote(album)
	# Sanitization, check if album
	if '..' in album or '/' in album or not path.isdir(album):
		print_error('album is not valid: %s' % album)
		return
	# No album
	if not path.exists(album):
		print_warning('album not found: %s' % album)
		return
	# No reports
	reports = path.join(album, 'reports.txt')
	if not path.exists(reports):
		print_warning('no reports found: %s' % reports)
		return
	remove(reports)
	print_ok('reports cleared')
	
def delete_album(album, blacklist=''):
	if not is_admin():
		print_error('you are not an admin: %s' % environ['REMOTE_ADDR'])
		return
	album = quote(album)
	# Sanitization, check if album
	if '..' in album or '/' in album or not path.isdir(album):
		print_error('album is not valid: %s' % album)
		return
	# No album
	if not path.exists(album):
		print_warning('album not found: %s' % album)
		return
	
	blacklisted = zipdel = albumdel = False
	# Add URL to blacklist
	url = get_url_for_album(album)
	if blacklist == 'true' and url != '':
		blacklist_url(url)
		blacklisted = True

	# Delete zip
	try:
		remove('%s.zip' % album)
		zipdel = True
	except: pass
	
	# Delete album dir
	try:
		rmtree(album)
		albumdel = True
	except: pass

	# Respond accordingly
	response = ''
	if blacklisted:
		response = ' and album was blacklisted'
	if albumdel and zipdel:
		print_ok('album and zip were both deleted%s' % response)
	elif albumdel:
		print_warning('album was deleted, zip was not found%s' % response)
	elif zipdel:
		print_warning('zip was deleted, album was not found%s' % response)
	else:
		print_error('neither album nor zip were deleted%s' % response)

def delete_albums_by_user(user, blacklist=''):
	if not is_admin():
		print_error('you are not an admin: %s' % environ['REMOTE_ADDR'])
		return
	deleted = []
	for d in listdir('.'):
		if not path.isdir(d): continue
		iptxt = path.join(d, 'ip.txt')
		if not path.exists(iptxt): continue
		f = open(iptxt, 'r')
		ip = f.read().replace('\n', '').strip()
		f.close()
		if ip != user: continue

		blacklisted = delalbum = delzip = False

		# Add URL to blacklist
		url = get_url_for_album(d)
		if blacklist == 'true' and url != '':
			blacklist_url(url)
			blacklisted = True
	
		# Delete zip
		try: 
			remove('%s.zip' % d)
			delzip = True
		except: pass
		# Delete album
		try: 
			rmtree(d)
			delalbum = True
		except: pass

		blresponse = ''
		if blacklisted:
			blresponse = ' + blacklist'
		if delzip and delalbum:
			deleted.append('%s/ and %s.zip%s' % (d, d, blresponse))
		elif delzip:
			deleted.append('%s.zip%s' % (d, blresponse))
		elif delalbum:
			deleted.append('%s/%s' % (d, blresponse))
	print dumps( {
		'deleted' : deleted,
		'user'    : user
	} )

def ban_user(user, reason='', length='temporary'):
	if not is_admin():
		print_error('you (%s) are not an admin' % environ['REMOTE_ADDR'])
		return
	try:
		f = open('../.htaccess', 'r')
		lines = f.read().split('\n')
		f.close()
	except:
		print_error('unable to read from ../.htaccess file -- user not banned.')
		return

	if length == 'permanent' and not 'allow from all' in lines:
		print_error('unable to permanently ban user; cannot find "allow from all" line in htaccess')
		return

	if ' deny from %s' % user in lines:
		print_warning('user is already permanently banned')
		return
	if length == 'temporary' and 'RewriteCond %%{REMOTE_HOST} ^%s$ [OR]' % user in lines:
		print_warning('user is already temporarily banned')
		return

	reason = reason.replace('\n', '').replace('\r', '')
	# Temporary vs Permanent. See .htaccess file in *root* directory for more info.
	if length == 'permanent':
		lines.insert(lines.index('allow from all'), '# added by admin %s at %s (reason: %s)' % (environ['REMOTE_ADDR'], int(time()), reason))
		lines.insert(lines.index('allow from all'), ' deny from %s' % user)
		lines.insert(lines.index('allow from all'), '')
	elif length == 'temporary':
		lines.insert(lines.index('RewriteCond %{REMOTE_HOST} ^0.0.0.0$'), '# added by admin %s at %s (reason: %s)' % (environ['REMOTE_ADDR'], int(time()), reason))
		lines.insert(lines.index('RewriteCond %{REMOTE_HOST} ^0.0.0.0$'), 'RewriteCond %%{REMOTE_HOST} ^%s$ [OR]' % user)
		lines.insert(lines.index('RewriteCond %{REMOTE_HOST} ^0.0.0.0$'), '')
	else:
		print_error('unexpected length of ban: %s' % length)
		return

	# Write ban to file
	try:
		f = open('../.htaccess', 'w')
		f.write('\n'.join(lines))
		f.close()
	except Exception, e:
		print_error('failed to ban %s: %s' % (user, str(e)))
		return
	# Save ban to log
	try:
		f = open(path.join('..', 'banned.log'), 'a')
		f.write('%s %d %s\n' % (user, int(time()), reason))
		f.close()
	except: pass

	if length == 'permanent':
		print_ok('permanently banned %s' % user)
	elif length == 'temporary':
		print_ok('temporarily banned %s' % user)


##################
# HELPER FUNCTIONS

# Print generic messages in JSON format
def print_error  (text): print dumps( { 'error'   : text } )
def print_warning(text): print dumps( { 'warning' : text } )
def print_ok     (text): print dumps( { 'ok'      : text } )

def get_keys(): # Retrieve key/value pairs from query, puts in dict
	form = cgi.FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = form[key].value
	return keys

def get_thumb(img): # Get thumbnail based on image, or 'nothumb.png' if not found
	fs = img.split(sep)
	fs.insert(-1, 'thumbs')
	f = sep.join(fs)
	if f.endswith('.mp4'):
		fname = fs.pop(-1).replace('.mp4', '.png')
		fs.append(fname)
		f = sep.join(fs)
		if path.exists(f):
			return f
		else:
			return 'playthumb.png'
	if f.endswith('.html'):
		return 'albumthumb.png'
	if not path.exists(f.replace('%25', '%')):
		return 'nothumb.png'
	return sep.join(fs)


##############
# UPDATE

def update_album(album): # Mark album as recently-viewed
	if path.exists(album):
		update_file_modified(album)
	zipfile = '%s.zip' % album
	if path.exists(zipfile):
		update_file_modified(zipfile)
	
def update_file_modified(f): # Sets system 'modified time' to current time
	st = stat(f)
	atime = int(st.st_atime)
	mtime = int(time())
	try:
		utime(f, (atime, mtime))
	except Exception, e:
		return False
	return True

def get_cookies():
	if not 'HTTP_COOKIE' in environ: return {}
	cookies = {}
	txt = environ['HTTP_COOKIE']
	for line in txt.split(';'):
		if not '=' in line: continue
		pairs = line.strip().split('=')
		cookies[pairs[0]] = pairs[1]
	return cookies

def is_admin(): # True if user's IP is in the admin list
	secretfile = path.join('..', 'admin_password.txt')
	if not path.exists(secretfile):
		return False
	cookies = get_cookies()
	if not 'rip_admin_password' in cookies: return False
	f = open(secretfile, 'r')
	password = f.read().strip()
	f.close()
	return cookies['rip_admin_password'] == password

def blacklist_url(url):
	if not url.startswith('http://') and \
	   not url.startswith('https://'):
		url = 'http://%s' % line
	# Use site's main 'rip.cgi' to get the ripper from the URL
	from sys import path as syspath
	syspath.append('..')
	from rip import get_ripper
	try:
		ripper = get_ripper(url)
		# Get directory name from URL
		to_blacklist = path.basename(ripper.working_dir)
	except Exception, e:
		# Default to just the URL
		to_blacklist = url.replace('http://', '').replace('https://', '')
	# Add to blacklist
	f = open('../url_blacklist.txt', 'a')
	f.write('%s\n' % to_blacklist)
	f.close()

# Entry point. Print leading/trailing characters, execute main()
if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	main()
	print "\n"

