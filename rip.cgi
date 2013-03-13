#!/usr/bin/python

import cgitb; cgitb.enable() # for debugging
import cgi # for getting query keys/values

from sys    import argv
from os     import remove, path, stat, utime
from stat   import ST_ATIME, ST_MTIME
from time   import strftime
from urllib import unquote

from sites.site_deviantart  import  deviantart 
from sites.site_flickr      import      flickr
from sites.site_imagearn    import    imagearn
from sites.site_imagebam    import    imagebam
from sites.site_imagefap    import    imagefap
from sites.site_imgur       import       imgur
from sites.site_instagram   import   instagram
from sites.site_photobucket import photobucket
from sites.site_tumblr      import      tumblr
from sites.site_twitter     import     twitter
from sites.site_xhamster    import    xhamster
from sites.site_getgonewild import getgonewild
from sites.site_anonib      import      anonib
from sites.site_motherless  import  motherless
from sites.site_4chan       import    fourchan
from sites.site_occ         import         occ
from sites.site_minus       import       minus

""" Print error in JSON format """
def print_error(text):
	print '{"error":"%s"}' % text

"""
	Where the magic happens.
	Exceptions are raised if download/status fails.
"""
def main():
	keys = get_keys()
	if not 'url' in keys:
		print_error("Required URL field not found")
		return
	url = unquote(keys['url']).replace(' ', '+')
	try:
		ripper = get_ripper(url)
	except Exception, e:
		print_error(str(e))
		return

	# Check if there's already a zip for the album
	if ripper.existing_zip_path() != None:
		# If user specified the uncached version, remove the zip
		if 'cached' in keys and keys['cached'] == 'false':
			remove(ripper.existing_zip_path())
		else:
			update_file_modified(ripper.existing_zip_path())
			print '{'
			print '"zip":"%s",' % ripper.existing_zip_path()
			print '"size":"%s"' % ripper.get_size(ripper.existing_zip_path())
			print '}'
			return

	# Start album download
	if 'start' in keys:
		if ripper.is_downloading():
			print_error("album rip is in progress. check back later")
			return
		try:
			ripper.download()
		except Exception, e:
			print_error('download failed: %s' % str(e))
			return
		if not path.exists(ripper.working_dir):
			print_error('unable to download album (empty? 404?)')
			return
		try:
			ripper.zip()
		except Exception, e:
			print_error('zip failed: %s' % str(e))
			return
		print '{'
		print '"zip":"%s",' % ripper.existing_zip_path().replace('"', '\\"')
		print '"size":"%s",' % ripper.get_size(ripper.existing_zip_path())
		print '"image_count":%d' % ripper.image_count
		if ripper.hit_image_limit():
			print ',"limit":%d' % ripper.max_images
		print '}'
	# Check status of album download
	elif 'check' in keys:
		lines = ripper.get_log(tail_lines=1)
		print '{'
		print '"log":"%s"' % '\\n'.join(lines)
		print '}'
	else:
		print_error('no status or start parameters found')

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
			minus]
	for site in sites:
		try:
			ripper = site(url)
			return ripper
		except Exception, e:
			error = str(e)
			if error == '': continue
			raise e
	raise Exception('Ripper can not rip given URL')

""" Updates system 'modified time' for file to current time. """
def update_file_modified(f):
	st = stat(f)
	atime = int(strftime('%s'))
	mtime = int(strftime('%s'))
	utime(f, (atime, mtime))

""" Retrieves key/value pairs from query, puts in dict """
def get_keys():
	form = cgi.FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = form[key].value
	if not 'url' in keys and len(argv) > 1:
		keys['url'] = argv[1]
		keys['start'] = 'true'
	return keys

"""
	Print leading/trailing characters,
	attempts to execute main(),
	prints JSON error & reason if exception is caught.
"""
if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	main()
	print "\n"
