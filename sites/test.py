#!/usr/bin/python

from site_imgur       import imgur
from site_deviantart  import deviantart
from site_photobucket import photobucket
from site_flickr      import flickr
from site_twitter     import twitter
from site_tumblr      import tumblr
from site_instagram   import instagram
from site_imagefap    import imagefap
from site_imagebam    import imagebam
from site_imagearn    import imagearn
from site_xhamster    import xhamster
from site_getgonewild import getgonewild

#i = imgur('http://imgur.com/a/8vmpo/noscript')
#i = imgur('http://scopolamina.imgur.com/')
#i = imagefap('http://www.imagefap.com/pictures/2885204/Kentucky-Craigslist')
#i = imagebam('http://www.imagebam.com/gallery/3e4u10fk034871hs6idcil6txauu3ru6/')
#i = imagebam('http://www.imagebam.com/image/1ca1ab109274357')
#i = imagebam('http://www.imagebam.com/gallery/g23rwux1oz1g6n9gzjqw2k4e6yblqxdu')
#i = deviantart('http://angelsfalldown1.deviantart.com/gallery/2498849')
#i = deviantart('http://angelsfalldown1.deviantart.com/gallery/2498856')
#i = deviantart('http://dreamersintheskies.deviantart.com/gallery/') # Gets more than gmi-total
#i = deviantart('http://dreambaloon.deviantart.com/gallery/')
#i = deviantart('http://easy-shutter.deviantart.com/gallery/42198389')
#i = deviantart('http://garv23.deviantart.com')
#i = photobucket('http://s579.beta.photobucket.com/user/merkler/library/')
i = photobucket('http://s1131.beta.photobucket.com/user/Beth_fan/library/')
#i = flickr('http://www.flickr.com/photos/beboastar/sets/72157630130722172/')
#i = flickr('https://secure.flickr.com/photos/peopleofplatt/sets/72157624572361792/with/6344610705/')
#i = twitter('https://twitter.com/darrow_ashley')
#i = twitter('https://twitter.com/lemandicandi')
#i = twitter('https://twitter.com/MrNMissesSmith')
#i = twitter('https://twitter.com/PBAprilLewis')
#i = tumblr('http://caramiaphotography.tumblr.com/tagged/me')
#i = tumblr('http://1fakeyfake.tumblr.com')
#i = tumblr('http://mourning-sex.tumblr.com/tagged/me')
#i = instagram('http://web.stagram.com/n/glitterypubez/')
#i = imagearn('http://imagearn.com/gallery.php?id=128805')
#i = imagearn('http://imagearn.com/gallery.php?id=29839')
#i = imagearn('http://imagearn.com/image.php?id=5046077')
#i = xhamster('http://xhamster.com/photos/gallery/1306566/lovely_teen_naked_for_self_shots.html')
#i = xhamster('http://xhamster.com/photos/gallery/1443114/cute_teens.html')
#i = flickr('http://www.flickr.com/photos/29809540@N04/')
#i = getgonewild('http://getgonewild.com/profile/EW2d')
#i = getgonewild('http://getgonewild.com/s/miss_ginger_biscuit')
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
