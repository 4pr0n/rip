#!/usr/bin/python

MAX_ALBUMS_PER_USER = 20
MAX_IMAGES_PER_CONTRIBUTOR = 1000

import cgitb; cgitb.enable() # for debugging
import cgi # for getting query keys/values

from sys    import argv, stdout
from os     import remove, path, stat, utime, SEEK_END, sep, walk, environ, listdir
from shutil import rmtree
from stat   import ST_ATIME, ST_MTIME
from time   import strftime
from urllib import unquote
from json   import dumps

from sites.DB import DB # database

from sites.site_deviantart  import  deviantart 
from sites.site_flickr      import      flickr
from sites.site_imagearn    import    imagearn
from sites.site_imagebam    import    imagebam
from sites.site_imagefap    import    imagefap
from sites.site_imgur       import       imgur
#from sites.site_webstagram  import   instagram
from sites.site_statigram   import   instagram
from sites.site_photobucket import photobucket
from sites.site_tumblr      import      tumblr
from sites.site_twitter     import     twitter
from sites.site_xhamster    import    xhamster
from sites.site_getgonewild import getgonewild
from sites.site_anonib      import      anonib
from sites.site_motherless  import  motherless
from sites.site_4chan       import    fourchan
from sites.site_minus       import       minus
from sites.site_gifyo       import       gifyo
from sites.site_five00px    import    five00px
from sites.site_cghub       import       cghub
from sites.site_chickupload import chickupload
from sites.site_teenplanet  import  teenplanet
from sites.site_chansluts   import   chansluts
from sites.site_buttoucher  import  buttoucher
from sites.site_pichunter   import   pichunter
from sites.site_soupio      import      soupio
from sites.site_imgbox      import      imgbox
from sites.site_reddit      import      reddit
from sites.site_gallerydump import gallerydump
from sites.site_fapdu       import       fapdu
from sites.site_fuskator    import    fuskator
from sites.site_kodiefiles  import  kodiefiles
from sites.site_pbase       import       pbase
from sites.site_8muses      import  eightmuses
from sites.site_setsdb      import      setsdb
from sites.site_nfsfw       import       nfsfw
from sites.site_shareimage  import  shareimage
from sites.site_seenive     import     seenive
from sites.site_vinebox     import     vinebox
from sites.site_imgchili    import    imgchili
from sites.site_fapproved   import   fapproved
from sites.site_gonewild    import    gonewild
# No longer supported
from sites.site_occ         import         occ
from sites.site_gonearch    import    gonearch

""" Print error in JSON format """
def print_error(text):
	print dumps( { 'error' : text } )

"""
	Where the magic happens.
	Prints JSON response to query.
"""
def main():
	# Keys are the query that's passed to the rip script, ex:
	#   ./rip.cgi?url=http://x.com&start=true&cached=false
	# The dict would be { url : http://x.com, start: true, cached: false }
	keys = get_keys()
	if  'start' in keys and \
			'url'   in keys:
		
		cached    = True # Default to cached
		if 'cached' in keys and keys['cached'] == 'false':
			cached = False
		rip(keys['url'], cached)
		
	elif 'check' in keys and \
			 'url'   in keys:
		check(keys['url'])
		
	elif 'recent' in keys:
		lines = 10
		if 'lines' in keys:
			lines = int(keys['lines'])
		recent(lines)
	elif 'byuser' in keys:
		ip = keys['byuser']
		if ip == 'me': ip = environ.get('REMOTE_ADDR', '127.0.0.1')
		print dumps({ 'albums' : albums_by_ip(ip) })
	
	else:
		print_error('invalid request')

""" Gets ripper, checks for existing rip, rips and zips as needed. """
def rip(url, cached):
	url = unquote(url.strip()).replace(' ', '%20').replace('https://', 'http://')

	if not passes_pre_rip_check(url): return

	try:
		# Get domain-specific ripper for URL
		ripper = get_ripper(url)
	except Exception, e:
		print_error(str(e))
		return

	# Check if album is blacklisted
	if ripper.is_blacklisted():
		print_error('cannot rip: URL is blacklisted')
		return

	# Check if there's already a zip for the album
	if cached:
		# Using cached version
		try:
			# See if album exists in DB, return it if it does (else error)
			(zipsize, source, count) = ripper.db.select_first('zipsize, source, count', 'albums', 'album = ?', [ripper.album_name])
			# Album already exists in DB
			ripper.db.update_album(ripper.album_name)
			print dumps ( {
					'album' : ripper.working_dir.replace('rips/', '').replace('%20', '%2520'),
					'zip'   : ripper.existing_zip_path().replace(' ', '%20').replace('%20', '%2520'),
					'size'  : ripper.bytes_to_hr(zipsize),
					'image_count' : count,
					'url'   : './%s' % ripper.working_dir.replace('rips/', 'rips/#')
				} )
			return
		except: pass
		if path.exists(ripper.working_dir) and ripper.existing_zip_path() != None:
			# ...But the album and zip exist.
			ripper.add_existing_album_to_db() # Add it to the DB
			(zipsize, source, count) = ripper.db.select_first('zipsize, source, count', 'albums', 'album = ?', [ripper.album_name])
			ripper.db.update_album(ripper.album_name)
			print dumps ( {
					'album' : ripper.working_dir.replace('rips/', '').replace('%20', '%2520'),
					'zip'   : ripper.existing_zip_path().replace(' ', '%20').replace('%20', '%2520'),
					'size'  : ripper.bytes_to_hr(zipsize),
					'image_count' : count,
					'url'   : './%s' % ripper.working_dir.replace('rips/', 'rips/#')
				} )
			return
	elif not cached: # User wants to delete existing verison and re-rip
		ripper.db.delete_album(ripper.album_name)
	
	if is_contributor():
		ripper.max_images = MAX_IMAGES_PER_CONTRIBUTOR
	# Rip it
	try:
		ripper.download()
		ripper.wait_for_threads()
	except Exception, e:
		print_error('download failed: %s' % str(e))
		return

	# If ripper fails silently, it will remove the directory of images
	if not path.exists(ripper.working_dir):
		print_error('unable to download album (empty? 404?)')
		return
	
	# Zip it
	try:
		ripper.zip()
	except Exception, e:
		print_error('zip failed: %s' % str(e))
		return
	
	# Add to recently-downloaded list
	ripper.add_recent(environ.get('REMOTE_ADDR', '127.0.0.1'))

	response = {
			'image_count' : ripper.image_count,
			'album' : ripper.working_dir.replace(' ', '%20').replace('%20', '%2520'),
			'url'   : './%s' % ripper.working_dir.replace('rips/', 'rips/#'),
			'zip'   : ripper.existing_zip_path().replace(' ', '%20').replace('%20', '%2520'),
			'size'  : ripper.get_size(ripper.existing_zip_path())
		}
	if ripper.hit_image_limit():
		response['limit'] = ripper.max_images
	
	# Print it
	print dumps(response)

""" Checks if current user is a 'contributor' """
def is_contributor():
	if not path.exists('contributors.txt'): return False
	cookies = get_cookies()
	if not 'rip_contributor_password' in cookies: return False
	f = open('contributors.txt', 'r')
	contributors = f.read().split('\n')
	f.close()
	while '' in contributors: contributors.remove('')
	return cookies['rip_contributor_password'] in contributors

""" Returns dict of requester's cookies """
def get_cookies():
	if not 'HTTP_COOKIE' in environ: return {}
	cookies = {}
	txt = environ['HTTP_COOKIE']
	for line in txt.split(';'):
		if not '=' in line: continue
		pairs = line.strip().split('=')
		cookies[pairs[0]] = pairs[1]
	return cookies

""" Ensures url can be ripped by user """
def passes_pre_rip_check(url):
	# Check if site is in unsupported list
	if not is_supported(url):
		print_error('site is not supported; will not be supported')
		return False
	# Check if user passed max albums allowed
	'''
	if not is_contributor():
		ip = environ.get('REMOTE_ADDR', '127.0.0.1')
		if len(albums_by_ip(ip)) >= MAX_ALBUMS_PER_USER:
			print_error('users are only allowed to rip %d albums at a time' % MAX_ALBUMS_PER_USER)
			return False
	'''
	return True

"""
	Checks status of rip. Returns zip/size if finished, otherwise
	returns the last log line from the rip.
"""
def check(url):
	url = unquote(url).replace(' ', '%20')

	try:
		ripper = get_ripper(url)
	except Exception, e:
		print_error(str(e))
		return

	# Check if there's already a zip for the album
	if path.exists(ripper.working_dir) and ripper.existing_zip_path() != None:
		(zipsize, source, count) = ripper.db.select_first('zipsize, source, count', 'albums', 'album = ?', [ripper.album_name])
		ripper.db.update_album(ripper.album_name)
		print dumps ( {
				'album' : ripper.working_dir.replace('rips/', '').replace('%20', '%2520'),
				'zip'   : ripper.existing_zip_path().replace(' ', '%20').replace('%20', '%2520'),
				'size'  : ripper.bytes_to_hr(zipsize),
				'image_count' : count,
				'url'   : './%s' % ripper.working_dir.replace('rips/', 'rips/#')
			} )
	else:
		# Print last log line ("status")
		lines = ripper.get_log(tail_lines=1)
		print dumps( { 
			'log' : '\\n'.join(lines)
			} )

""" Returns an appropriate ripper for a URL, or throws exception """
def get_ripper(url):
	sites = [        \
			deviantart,  \
			flickr,      \
			imagearn,    \
			imagebam,    \
			imagefap,    \
			imgur,       \
			instagram,   \
			photobucket, \
			tumblr,      \
			twitter,     \
			xhamster,    \
			getgonewild, \
			anonib,      \
			motherless,  \
			fourchan,    \
			occ,         \
			minus,       \
			gifyo,       \
			five00px,    \
			chickupload, \
			cghub,       \
			teenplanet,  \
			chansluts,   \
			buttoucher,  \
			pichunter,   \
			soupio,      \
			imgbox,      \
			reddit,      \
			gallerydump, \
			fapdu,       \
			fuskator,    \
			kodiefiles,  \
			pbase,       \
			eightmuses,  \
			setsdb,      \
			nfsfw,       \
			shareimage,  \
			seenive,     \
			vinebox,     \
			imgchili,    \
			fapproved,   \
			gonewild]
	for site in sites:
		try:
			ripper = site(url, ip=environ.get('REMOTE_ADDR', '127.0.0.1'))
			return ripper
		except Exception, e:
			# Rippers that aren't made for the URL throw blank Exception
			error = str(e)
			if error == '': continue
			# If Exception isn't blank, then it's the right ripper but an error occurred
			raise e
	raise Exception('Ripper can not rip given URL')

""" Retrieves key/value pairs from query, puts in dict """
def get_keys():
	form = cgi.FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = form[key].value
	if not 'url' in keys and not 'recent' in keys and not 'byuser' in keys and len(argv) > 1:
		keys['url'] = argv[1]
		keys['start'] = 'true'
	return keys

"""
	Returns recently-downloaded zips
"""
def recent(lines):
	query = '''
		select url, album
			from recent
			limit %d
	''' % lines
	db = DB()
	cur = db.conn.cursor()
	curexec = cur.execute(query)
	results = curexec.fetchall()
	cur.close()
	response = []
	for (url, album) in results:
		response.append( {
			'url'      : url,
			'view_url' : 'rips/#%s' % album
		} )
	print dumps( {
		'recent' : response
	} )

""" Tail a file and get X lines from the end """
def tail(f, lines=1, _buffer=4098):
	lines_found = []
	block_counter = -1
	while len(lines_found) < lines:
		try:
			f.seek(block_counter * _buffer, SEEK_END)
		except IOError, e:  # either file is too small, or too many lines requested
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

def albums_by_ip(ip):
	db = DB()
	query = '''
		select album, count, zipsize, source
			from albums
			where ip = ?
	'''
	cur = db.conn.cursor()
	curexec = cur.execute(query, [ip])
	results = curexec.fetchall()
	cur.close()
	if results == None: return []
	response = []
	for (album, count, zipsize, source) in results:
		response.append( {
			'album'  : album,
			'count'  : count,
			'size'   : zipsize,
			'source' : source
		})
	return response

def is_supported(url):
	if not path.exists('unsupported.txt'): return True
	for line in open('unsupported.txt', 'r'):
		line = line.strip()
		if line.lower() in url.lower():
			return False
	return True

""" Entry point. Print leading/trailing characters, executes main() """
if __name__ == '__main__':
	print "Content-Type: application/json"
	print "Keep-Alive: timeout=900"
	print "Connection: Keep-Alive"
	print ""
	stdout.flush()
	main()
	print "\n"

