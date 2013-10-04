#!/usr/bin/python

import cgitb; cgitb.enable() # for debugging
import cgi # for getting query keys/values

from sys    import argv, stdout
from os     import remove, path, stat, utime, SEEK_END, sep, walk, environ, listdir
from shutil import rmtree
from stat   import ST_ATIME, ST_MTIME
from time   import strftime
from urllib import unquote
from json   import dumps

from sites.site_deviantart  import  deviantart 
from sites.site_flickr      import      flickr
from sites.site_imagearn    import    imagearn
from sites.site_imagebam    import    imagebam
from sites.site_imagefap    import    imagefap
from sites.site_imgur       import       imgur
from sites.site_webstagram  import   instagram
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
		urls_only = False
		if 'cached' in keys and keys['cached'] == 'false':
			cached = False
		if 'urls_only' in keys and keys['urls_only'] == 'true':
			urls_only = True
		rip(keys['url'], cached, urls_only)
		
	elif 'check' in keys and \
			 'url'   in keys:
		urls_only = False
		if 'urls_only' in keys and keys['urls_only'] == 'true':
			urls_only = True
		check(keys['url'], urls_only)
		
	elif 'recent' in keys:
		lines = 10
		if 'lines' in keys:
			lines = int(keys['lines'])
		recent(lines)
	elif 'byuser' in keys:
		ip = keys['byuser']
		if ip == 'me': ip = environ.get('REMOTE_ADDR', '127.0.0.1')
		albums_by_ip(ip)
	
	else:
		print_error('invalid request')

""" Gets ripper, checks for existing rip, rips and zips as needed. """
def rip(url, cached, urls_only):
	url = unquote(url.strip()).replace(' ', '%20')
	
	try:
		# Get domain-specific ripper for URL
		ripper = get_ripper(url, urls_only)
	except Exception, e:
		print_error(str(e))
		return

	# Check URL against blacklist
	if path.exists('url_blacklist.txt'):
		for line in open('url_blacklist.txt', 'r'):
			line = line.strip().lower()
			if line == '': continue
			if line in url.lower() or \
			   ripper.working_dir.lower().endswith(line):
				print_error('cannot rip: URL is blacklisted')
				return

	# Check if there's already a zip for the album
	if ripper.existing_zip_path() != None:
		if not cached:
			# If user specified the uncached version, remove the zip
			remove(ripper.existing_zip_path())
			if path.exists(ripper.working_dir):
				rmtree(ripper.working_dir)
		else:
			# Mark the file as recently-accessed (top of FIFO queue)
			update_file_modified(ripper.existing_zip_path())
			add_recent(url)
			response = {}
			response['zip']   = ripper.existing_zip_path().replace(' ', '%20').replace('%20', '%2520')
			response['size']  = ripper.get_size(ripper.existing_zip_path())
			if path.exists(ripper.working_dir):
				update_file_modified(ripper.working_dir)
				image_count = 0
				for root, subdirs, files in walk(ripper.working_dir):
					if 'thumbs' in root: continue
					for f in files:
						if f.endswith('.txt'): continue
						image_count += 1
							
				response['album'] = ripper.working_dir.replace('rips/', '').replace('%20', '%2520')
				response['url']   = './%s' % ripper.working_dir.replace('rips/', 'rips/#')
				response['image_count'] = image_count
			print dumps( response )
			return

	'''
	if ripper.is_downloading():
		print_error("album rip is in progress. check back later")
		return
	'''
	
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
	
	# Save IP of ripper
	f = open('%s%sip.txt' % (ripper.working_dir, sep), 'w')
	f.write(environ.get('REMOTE_ADDR', '127.0.0.1'))
	f.close()
	
	response = {}
	response['image_count'] = ripper.image_count
	if ripper.hit_image_limit():
		response['limit'] = ripper.max_images
	
	# Create zip flag
	f = open('%s%szipping.txt' % (ripper.working_dir, sep), 'w')
	f.write('\n')
	f.close()

	# Zip it
	try:
		ripper.zip()
	except Exception, e:
		print_error('zip failed: %s' % str(e))
		return
	
	# Delete zip flag
	try: remove('%s%szipping.txt' % (ripper.working_dir, sep))
	except: pass

	# Mark album as completed
	if not urls_only:
		f = open('%s%scomplete.txt' % (ripper.working_dir, sep), 'w')
		f.write('\n')
		f.close()
		response['album'] = ripper.working_dir.replace(' ', '%20').replace('%20', '%2520')
		response['url']   = './%s' % ripper.working_dir.replace('rips/', 'rips/#')
	
	response['zip']  = ripper.existing_zip_path().replace(' ', '%20').replace('%20', '%2520')
	response['size'] = ripper.get_size(ripper.existing_zip_path())
	
	# Add to recently-downloaded list
	add_recent(url)
	
	# Print it
	print dumps(response)


"""
	Checks status of rip. Returns zip/size if finished, otherwise
	returns the last log line from the rip.
"""
def check(url, urls_only):
	url = unquote(url).replace(' ', '%20')
	try:
		ripper = get_ripper(url, urls_only)
	except Exception, e:
		print_error(str(e))
		return

	# Check if there's already a zip for the album
	if ripper.existing_zip_path() != None:
		response = {}
		response['zip']  = ripper.existing_zip_path().replace(' ', '%20').replace('%20', '%2520')
		response['size'] = ripper.get_size(ripper.existing_zip_path())
		# Return link to zip
		if path.exists(ripper.working_dir):
			update_file_modified(ripper.working_dir)
			image_count = 0
			for root, subdirs, files in walk(ripper.working_dir):
				if 'thumbs' in root: continue
				for f in files:
					if f.endswith('.txt'): continue
					image_count += 1
						
			response['album'] = ripper.working_dir.replace('rips/', '').replace('%20', '%2520')
			response['url']   = './%s' % ripper.working_dir.replace('rips/', 'rips/#')
			response['image_count'] = image_count
		print dumps( response )
	else:
		# Print last log line ("status")
		lines = ripper.get_log(tail_lines=1)
		print dumps( { 
			'log' : '\\n'.join(lines)
			} )

""" Returns an appropriate ripper for a URL, or throws exception """
def get_ripper(url, urls_only):
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
			seenive]
	for site in sites:
		try:
			ripper = site(url, urls_only)
			return ripper
		except Exception, e:
			# Rippers that aren't made for the URL throw blank Exception
			error = str(e)
			if error == '': continue
			# If Exception isn't blank, then it's the right ripper but an error occurred
			raise e
	raise Exception('Ripper can not rip given URL')

""" Updates system 'modified time' for file to current time. """
def update_file_modified(f):
	st = stat(f)
	from time import time
	atime = int(time())
	mtime = int(time())
	try:
		utime(f, (atime, mtime))
	except: pass

""" Retrieves key/value pairs from query, puts in dict """
def get_keys():
	form = cgi.FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = form[key].value
	if not 'url' in keys and not 'recent' in keys and len(argv) > 1:
		keys['url'] = argv[1]
		keys['start'] = 'true'
	return keys

"""
	Returns recently-downloaded zips
"""
def recent(lines):
	recents = []
	try:
		f = open('recent_rips.lst', 'r')
		recents = tail(f, lines=lines)
		f.close()
	except: pass
	
	result = []
	for rec in recents:
		d = {}
		try: ripper = get_ripper(rec, False)
		except: continue
		d['url'] = rec
		d['view_url'] = ripper.working_dir.replace('rips/', 'rips/#')
		result.append(d)
		
	print dumps( { 
		'recent' : result
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

""" Adds url to list of recently-downloaded albums """
def add_recent(url):
	if path.exists('recent_rips.lst'):
		already_added = False
		f = open('recent_rips.lst', 'r')
		if url in tail(f, lines=10): already_added = True
		f.close()
		if already_added: return
	
	f = open('recent_rips.lst', 'a')
	f.write('%s\n' % url)
	f.close()

def albums_by_ip(ip):
	albums = []
	for thedir in listdir('rips'):
		d = path.join('rips', thedir)
		if not path.isdir(d): continue
		iptxt = path.join(d, 'ip.txt')
		if not path.exists(iptxt): continue
		f = open(iptxt, 'r')
		albumip = f.read().strip()
		f.close()
		if ip == albumip:
			jsonalbum = {}
			jsonalbum['album'] = thedir
			url = ''
			thelog = path.join(d, 'log.txt')
			if path.exists(thelog):
				f = open(thelog, 'r')
				lines = f.read().split('\n')
				f.close()
				if len(lines) > 0:
					url = lines[0]
					url = url[url.rfind(' ')+1:]
				jsonalbum['url']   = url
					
			albums.append(jsonalbum)
	print dumps( {
		'albums' : albums
		} )

""" Entry point. Print leading/trailing characters, executes main() """
if __name__ == '__main__':
	print "Content-Type: application/json"
	print "Keep-Alive: timeout=300"
	print "Connection: Keep-Alive"
	print ""
	stdout.flush()
	main()
	print "\n"

