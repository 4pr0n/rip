#!/usr/bin/python

import cgitb; cgitb.enable() # for debugging
import cgi # for getting query keys/values

from sys    import argv
from os     import remove
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
	url = unquote(keys['url'])
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
			print '{'
			print '"zip":"%s",' % ripper.existing_zip_path()
			print '"size":"%s"' % ripper.get_size(ripper.existing_zip_path())
			print '}'
			return

	# Start album download
	if 'start' in keys:
		if ripper.is_downloading():
			print_error("album rip is in progress; check back later")
			return
		try:
			ripper.download()
		except Exception, e:
			print_error('Error while downloading: %s' % str(e))
		try:
			ripper.zip()
		except Exception, e:
			print_error('Error while zipping: %s' % str(e))
		print '{'
		print '"zip":"%s",' % ripper.existing_zip_path()
		print '"size":"%s"' % ripper.get_size(ripper.existing_zip_path())
		print '}'
	# Check status of album download
	elif 'check' in keys:
		lines = ripper.get_log(tail_lines=1)
		print '{'
		print '"log":"%s"' % '\\n'.join(lines)
		print '}'
	else:
		print_error('No status or start parameters found')

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
			getgonewild]
	for site in sites:
		try:
			ripper = site(url)
			return ripper
		except Exception, e:
			error = str(e)
			if error == '': continue
			raise e
	raise Exception('Ripper can not rip given URL')

""" Retrieves key/value pairs from query, puts in dict """
def get_keys():
	form = cgi.FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = form[key].value
	if not 'url' in keys and len(argv) > 1:
		keys['url'] = argv[1]
	return keys

"""
	Print leading/trailing characters,
	attempts to execute main(),
	prints JSON error & reason if exception is caught.
"""
if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	#try:
	main()
	#except Exception, e:
	#print '{"error":"%s"}' % str(e)
	print "\n"
