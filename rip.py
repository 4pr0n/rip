#!/usr/bin/python

from sys import argv, exit
import os
import platform

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
# No longer supported
from sites.site_occ         import         occ
from sites.site_gonearch    import    gonearch

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
		nfsfw]

def main():
	print '\nrarchives\' album ripper\n'
	if len(argv) == 0 or argv[-1].endswith('rip.py'):
		usage()
		exit(1)
	url = argv[-1]
	ripper = get_ripper(url)
	ripper.download()
	print ''
	print '  images ripped: %d' % ripper.image_count
	print '  ripped to:     %s' % ripper.working_dir
	print ''
	open_dir(ripper.working_dir)

def open_dir(path):
	plat = platform.system()
	if plat == 'Windows':
		os.startfile(path)
	elif plat == 'Darwin':
		os.system('open "%s"' % path)
	else:
		os.system('xdg-open "%s"' % path)

def usage():
	print '    usage:'
	print '      python rip.py URL'
	print ''
	print '     supported sites:',
	for i, site in enumerate(sites):
		if i % 5 == 0:
			print '\n      ',
		print site.__name__.ljust(12),
	print '\n'

""" Returns an appropriate ripper for a URL, or throws exception """
def get_ripper(url):
	for site in sites:
		try:
			ripper = site(url, debugging=False, urls_only=False)
			return ripper
		except Exception, e:
			# Rippers that aren't made for the URL throw blank Exception
			error = str(e)
			if error == '': continue
			# If Exception isn't blank, then it's the right ripper but an error occurred
			raise e
	raise Exception('cannot rip given URL: "%s"' % url)

if __name__ == '__main__':
	try:
		main()
	except Exception, e:
		usage()
		if type(e) == OSError and 'Permission denied' in str(e):
			print '[!] ERROR'
			print '    ensure you have write access to the these directories:'
			print '      %s' % os.getcwd()
			print '    or execute as root/admin\n'
		elif type(e) == KeyboardInterrupt:
			print '\n[!] ^C keyboard interrupt, exiting\n'
		else:
			print '[!] rip.py ended with error message:\n      %s\n' % str(e)

