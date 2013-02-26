#!/usr/bin/python

from site_imgur       import imgur
from site_imagefap    import imagefap
from site_imagebam    import imagebam
from site_deviantart  import deviantart
from site_photobucket import photobucket
from site_flickr      import flickr
from site_twitter     import twitter

#i = imgur('http://imgur.com/a/8vmpo/noscript')
#i = imagefap('http://www.imagefap.com/pictures/2885204/Kentucky-Craigslist')
#i = imagebam('http://www.imagebam.com/gallery/3e4u10fk034871hs6idcil6txauu3ru6/')
#i = imagebam('http://www.imagebam.com/image/1ca1ab109274357')
#i = imagebam('http://www.imagebam.com/gallery/g23rwux1oz1g6n9gzjqw2k4e6yblqxdu')
#i = deviantart('http://angelsfalldown1.deviantart.com/gallery/2498849')
#i = deviantart('http://angelsfalldown1.deviantart.com/gallery/2498856')
#i = deviantart('http://dreamersintheskies.deviantart.com/gallery/') # Gets more than gmi-total
#i = deviantart('http://dreambaloon.deviantart.com/gallery/')
#i = photobucket('http://s579.beta.photobucket.com/user/merkler/library/')
#i = flickr('http://www.flickr.com/photos/beboastar/sets/72157630130722172/')
#i = flickr('https://secure.flickr.com/photos/peopleofplatt/sets/72157624572361792/with/6344610705/')
i = twitter('https://twitter.com/darrow_ashley')
print i.working_dir
if i.existing_zip_path() != None:
	print 'Zip exists: %s' % i.existing_zip_path()
else:
	print 'downloading...'
	i.download()
	#print 'checking for zip'
	#print str(i.existing_zip_path())
	#print 'zipping'
	#print i.zip()
