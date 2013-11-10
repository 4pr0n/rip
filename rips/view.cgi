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
# Need to load modules found in parent directories
from sys import path as syspath
syspath.append('..')
from sites.DB import DB

sep = '/' # File separator


##################
# MAIN

def main(): # Prints JSON response to query
	keys = get_keys()

	if path.exists('rips') and path.exists(path.join('rips', 'view.cgi')):
		chdir('rips')

	# Gets keys or defaults
	start   = int(keys.get('start',   0))    # Starting index (album/images)
	count   = int(keys.get('count',   20))   # Number of images/thumbs to retrieve
	preview = int(keys.get('preview', 10))   # Number of images to retrieve
	after     = keys.get('after',   '')      # Value of last album retrieved
	sorting   = keys.get('sort', 'accessed') # Sort order
	ordering  = keys.get('order', 'desc')    # Ascending/descending
	blacklist = keys.get('blacklist', '')    # Album to blacklist

	# Get from list of all albums
	if  'view_all' in keys: get_all_albums(count, preview, after, sorting, ordering)
	# Get images from one album
	elif 'view'          in keys: get_album(keys['view'], start, count, sorting, ordering)
	# Get URLs for an album
	elif 'urls'          in keys: get_urls_for_album(keys['urls'])
	# Get albums ripped by a user
	elif 'user'          in keys: get_all_albums(count, preview, after, sorting, ordering, userfilter=keys['user'])
	# Report an album
	elif 'report'        in keys: report_album(keys['report'])
	# Get from list of reported album
	elif 'get_report'    in keys: get_all_albums(count, preview, after, sorting, ordering, reportfilter=True)
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
# ALL ALBUMS

def get_all_albums(count, preview_size, after, sorting, ordering, textfilter=None, userfilter=None, reportfilter=None):
	db = DB()
	debug = ''
	# Input sanitization, setup sort order
	if sorting not in ['accessed', 'id', 'count', 'views', 'reports', 'created', 'album', 'zipsize']:
		sorting = 'accessed'
	if ordering not in ['asc', 'desc']:
		ordering = 'desc'

	# Construct 'where' clause
	values = []
	if after == '' or db.count('*', 'albums', '%s %s ?' % (sorting, '>' if ordering == 'asc' else '>'), [after]) == 0:
		where = ''
	else:
		if ordering == 'asc':
			where = 'where %s > ?' % sorting
			values.append(after)
		else:
			where = 'where %s < ?' % sorting
			values.append(after)

	# Apply filters if needed
	if textfilter != None:
		if where == '': where = 'where '
		else: where += ' and '
		where += 'url like ?'
		values.append('%%%s%%' % textfilter)
	elif userfilter != None:
		if where == '': where = 'where '
		else: where += ' and '
		where += 'ip = ?'
		values.append(userfilter)
	elif reportfilter != None:
		if where == '': where = 'where '
		else: where += ' and '
		where += 'reports > 0'

	# Get list of albums
	after = ''
	cur = db.conn.cursor()
	query = '''
		select id, album, count, zipsize, ip, views, created, accessed, reports
			from albums
			%s
			order by %s %s
			limit %d
	''' % (where, sorting, ordering, count)
	curexec = cur.execute(query, values)
	results = curexec.fetchall()
	albums = []
	for (albumid, album, image_count, zipsize, ip, views, created, accessed, reports) in results:
		# Get images from album
		query = '''
			select path, width, height, size, thumb, type
				from images
				where album = %d
				limit %d
		''' % (albumid, preview_size)
		debug += query
		curexec = cur.execute(query)
		image_tuples = curexec.fetchall()
		images = []
		for (imagepath, width, height, imagesize, thumb, imagetype) in image_tuples:
			images.append( {
				'image'  : imagepath,
				'thumb'  : thumb,
				'type'   : imagetype,
				'width'  : width,
				'height' : height
			} )
		# Add album and images to response
		albuminfo = {
			'album'   : album,
			'images'  : images,
			'total'   : image_count,
			'time'    : created,
			'size'    : sizeof_fmt(zipsize),
			'archive' : '/%s.zip' % album,
		}
		if is_admin():
			albuminfo['reports'] = reports
			albuminfo['user'] = ip
		albums.append(albuminfo)
		# Set the 'after' (field of last album returned)
		if   sorting == 'accessed': after = str(accessed)
		elif sorting == 'created' : after = str(created)
		elif sorting == 'id'      : after = str(albumid)
		elif sorting == 'count'   : after = str(image_count)
		elif sorting == 'views'   : after = str(views)
		elif sorting == 'reports' : after = str(reports)
		elif sorting == 'path'    : after = album
		elif sorting == 'zipsize' : after = zipsize

	# Remaining albums
	query = '''select count(id) from albums %s''' % where
	curexec = cur.execute(query, values)
	remaining_albums = max(0, curexec.fetchone()[0] - count)
	cur.close()

	response = {
		'albums' : albums,
		'count'  : count,
		'after'  : after,
		'debug'  : debug,
		'remain' : remaining_albums
	}
	print dumps( response )


##################
# SINGLE ALBUM
def get_album(album, start, count, sorting, ordering):
	db = DB()
	# Input sanitization, setup sort order
	if sorting not in ['number', 'path', 'size', 'type']:
		sorting = 'number'
	if ordering not in ['asc', 'desc']:
		ordering = 'desc'

	# Get album
	try:
		(albumid,    \
			total,     \
			filesize,  \
			zipsize,   \
			views,     \
			albumsource, \
			created,   \
			accessed,  \
			log,       \
			complete,  \
			reports,   \
			ip) = \
		db.select_first(
			'id,'       +
			'count,'    +
			'filesize,' +
			'zipsize,'  +
			'views,'    +
			'source,'   +
			'created,'  +
			'accessed,' +
			'log,'      +
			'complete,' +
			'reports,'  +
			'ip',
			'albums', 'album = ?', [album])
	except Exception, e:
		# Album not found, return default info
		print dumps( {
			'album' : {
				'images'  : [],
				'count'   : 0,
				'album'   : '[not found]',
				'guess'   : guess_url(album),
				'archive' : './'
			}
		} )
		return
	cur = db.conn.cursor()
	# Get images
	query = '''
		select number, path, source, width, height, size, thumb, type
			from images
			where album = ?
			order by %s %s
			limit %d,%d
	''' % (sorting, ordering, start, count)
	curexec = cur.execute(query, [albumid])
	images = []
	for (number, path, imagesource, width, height, size, thumb, imagetype) in curexec.fetchall():
		images.append( {
			'image'  : path,
			'thumb'  : thumb,
			'index'  : number,
			'source' : imagesource,
			'width'  : width,
			'height' : height,
			'type'   : imagetype
		} )
	cur.close()
	# Construct response
	response = {
		'images'  : images,
		'start'   : start,
		'count'   : count,
		'album'   : album,
		'url'     : albumsource,
		'total'   : total,
		'size'    : sizeof_fmt(filesize),
		'zipsize' : zipsize,
		'created' : created,
		'accessed': accessed,
		'log'     : log,
		'complete': complete,
		'archive' : '%s.zip' % album,
	}
	if is_admin():
		response['reports'] = reports
		response['user'] = ip
	if start == 0:
		db.update_album(album)
	print dumps( {
		'album' : response
	} )


# Return all direct URLs for all images in an album
def get_urls_for_album(album):
	db = DB()
	cur = db.conn.cursor()
	query = '''
		select source 
			from images 
			where albumid in 
				(select id from albums where album = ?)
			order by number
	'''
	curexec = cur.execute(query, [album])
	urls = []
	for (url) in curexec.fetchall():
		urls.append(url)
	print dumps( {
		'urls' : urls
	} )


#############
# ADMIN
def report_album(album):
	db = DB()
	cur = db.conn.cursor()
	query = '''
		update albums
			set reports = reports + 1
			where album = ?
	'''
	cur.execute(query, [album])
	cur.close()
	db.commit()
	print_ok('this album has been reported. the admins will look into this soon')

def clear_reports(album):
	if not is_admin():
		print_error('you are not an admin: %s' % environ.get('REMOTE_ADDR', '127.0.0.1'))
		return
	db = DB()
	cur = db.conn.cursor()
	query = '''
		update albums
			set reports = 0
			where album = ?
	'''
	cur.execute(query, [album])
	cur.close()
	db.commit()
	print_ok('reports cleared')

def delete_album(album, blacklist=''):
	if not is_admin():
		print_error('you are not an admin: %s' % environ.get('REMOTE_ADDR', '127.0.0.1'))
		return
	db = DB()
	blacklist = False if blacklist == '' else True
	db.delete_album(album, blacklist=blacklist)
	response = 'album was deleted'
	if blacklisted:
		response = ' and blacklisted'
	print_ok(response)

def delete_albums_by_user(user, blacklist=''):
	blacklist = False if blacklist == '' else True
	if not is_admin():
		print_error('you are not an admin: %s' % environ.get('REMOTE_ADDR', '127.0.0.1'))
		return
	db = DB()
	cur = db.conn.cursor()
	query = '''
		select album
			from albums
			where ip = ?
	'''
	curexec = cur.execute(query, [user])
	deleted = []
	for (album) in curexec.fetchall():
		db.delete_album(album, blacklist=blacklist)
		msg = '%s was deleted' % album
		if blacklist:
			msg += 'and blacklisted'
		deleted.append(msg)
	cur.close()
	print dumps( {
		'deleted' : deleted,
		'user' : user
	} )

def ban_user(user, reason='', length='permanent'):
	if not is_admin():
		print_error('you (%s) are not an admin' % environ.get('REMOTE_ADDR', '127.0.0.1'))
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
	# Temporary vs Permanent. See .htaccess file in *root* directory for more info.
	reason = reason.replace('\n', '').replace('\r', '')
	if length == 'permanent':
		lines.insert(lines.index('allow from all'), '# added by admin %s at %s (reason: %s)' % (environ.get('REMOTE_ADDR', '127.0.0.1'), int(time()), reason))
		lines.insert(lines.index('allow from all'), ' deny from %s' % user)
		lines.insert(lines.index('allow from all'), '')
	elif length == 'temporary':
		lines.insert(lines.index('RewriteCond %{REMOTE_HOST} ^0.0.0.0$'), '# added by admin %s at %s (reason: %s)' % (environ.get('REMOTE_ADDR', '127.0.0.1'), int(time()), reason))
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
	print_ok('%s-banned %s' % (length, user))

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

# Get human-readable size of file
def sizeof_fmt(num):
	for x in ['bytes','KB','MB','GB','TB']:
		if num < 1024.0:
			return "%3.1f %s" % (num, x)
		num /= 1024.0
	return '?bytes'

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

# Entry point. Print leading/trailing characters, execute main()
if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	main()
	print "\n"

