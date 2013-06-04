#!/usr/bin/python

from sys import exit

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
from site_anonib      import anonib
from site_motherless  import motherless
from site_4chan       import fourchan
from site_occ         import occ
from site_minus       import minus
from site_gifyo       import gifyo
from site_imgsrc      import imgsrc
from site_five00px    import five00px
from site_chickupload import chickupload
from site_cghub       import cghub
from site_teenplanet  import teenplanet
from site_chansluts   import chansluts
from site_gonearch    import gonearch

try:
	#i = imgur('http://imgur.com/a/8vmpo/noscript')
	#i = imgur('http://scopolamina.imgur.com/')
	#i = imgur('http://fuckmyusername.imgur.com')
	#i = imgur('http://imgur.com/a/brixs')
	#i = imgur('http://imgur.com/a/nvE9y')
	#i = imgur('http://spicymustard.imgur.com/') # empty user acct

	#i = imagefap('http://www.imagefap.com/pictures/2885204/Kentucky-Craigslist')
	#i = imagefap('http://www.imagefap.com/pictures/3958759/Busty-Selfshooter')
	#i = imagefap('http://www.imagefap.com/pictures/3960306/teen-fun/')

	#i = imagebam('http://www.imagebam.com/gallery/3e4u10fk034871hs6idcil6txauu3ru6/')
	#i = imagebam('http://www.imagebam.com/image/1ca1ab109274357')
	#i = imagebam('http://www.imagebam.com/gallery/g23rwux1oz1g6n9gzjqw2k4e6yblqxdu')

	#i = deviantart('http://angelsfalldown1.deviantart.com/gallery/2498849')
	#i = deviantart('http://angelsfalldown1.deviantart.com/gallery/2498856')
	#i = deviantart('http://dreamersintheskies.deviantart.com/gallery/') # Gets more than gmi-total
	#i = deviantart('http://dreambaloon.deviantart.com/gallery/')
	#i = deviantart('http://easy-shutter.deviantart.com/gallery/42198389')
	#i = deviantart('http://garv23.deviantart.com')
	#i = deviantart('http://wrouinr.deviantart.com/')

	#i = photobucket('http://s579.beta.photobucket.com/user/merkler/library/')
	#i = photobucket('http://s1131.beta.photobucket.com/user/Beth_fan/library/')
	#i = photobucket('http://s1069.beta.photobucket.com/user/mandymgray/library/Album%203')
	#i = photobucket('http://s1216.beta.photobucket.com/user/Liebe_Dich/profile/')

	#i = flickr('http://www.flickr.com/photos/beboastar/sets/72157630130722172/')
	#i = flickr('https://secure.flickr.com/photos/peopleofplatt/sets/72157624572361792/with/6344610705/')
	#i = flickr('http://www.flickr.com/photos/rphotoit/sets/72157631879138251/with/8525941976/')
	#i = flickr('http://www.flickr.com/photos/29809540@N04/')

	#i = twitter('https://twitter.com/darrow_ashley')
	#i = twitter('https://twitter.com/lemandicandi')
	#i = twitter('https://twitter.com/MrNMissesSmith')
	#i = twitter('https://twitter.com/PBAprilLewis') # GONE
	#i = twitter('https://twitter.com/EversSecrets') # GONE

	#i = tumblr('http://caramiaphotography.tumblr.com/tagged/me')
	#i = tumblr('http://1fakeyfake.tumblr.com')
	#i = tumblr('http://mourning-sex.tumblr.com/tagged/me')
	#i = tumblr('http://i-was-masturbating-when-i.tumblr.com/')

	#i = instagram('http://web.stagram.com/n/glitterypubez/')

	#i = imagearn('http://imagearn.com/gallery.php?id=128805')
	#i = imagearn('http://imagearn.com/gallery.php?id=29839')
	#i = imagearn('http://imagearn.com/image.php?id=5046077')

	#i = xhamster('http://xhamster.com/photos/gallery/1306566/lovely_teen_naked_for_self_shots.html')
	#i = xhamster('http://xhamster.com/photos/gallery/1443114/cute_teens.html')
	#i = xhamster('http://xhamster.com/photos/gallery/1742221/amateur_black_girls_volume_4-2.html')

	#i = getgonewild('http://getgonewild.com/profile/EW2d')
	#i = getgonewild('http://getgonewild.com/s/miss_ginger_biscuit')
	#i = getgonewild('http://getgonewild.com/profile/yaymuffinss')

	#i = anonib('http://www.anonib.com/t/res/1780.html')
	#i = anonib('http://www.anonib.com/t/res/5019.html')
	#i = anonib('http://www.anonib.com/tblr/res/12475.html')
	#i = anonib('http://www.anonib.com/t/res/1780+50.html')
	#i = anonib('http://www.anonib.com/tblr/res/12475+50.html')

	#i = motherless('http://motherless.com/GI39ADA2C')
	#i = motherless('http://motherless.com/GABDCF08')
	#i = motherless('http://motherless.com/G7DC1B74')
	#i = motherless('http://motherless.com/GV9719092')

	#i = fourchan('http://boards.4chan.org/s/res/14035564')

	#i = occ('http://forum.oneclickchicks.com/showthread.php?t=137808')
	#i = occ('http://forum.oneclickchicks.com/showthread.php?t=102994')
	#i = occ('http://forum.oneclickchicks.com/album.php?albumid=12579')
	#i = occ('http://forum.oneclickchicks.com/showthread.php?t=146037')

	#i = minus('http://minus.com')
	#i = minus('http://.minus.com')
	#i = minus('http://i.minus.com')
	#i = minus('http://www.minus.com')
	#i = minus('http://zuzahgaming.minus.com/mF31aoo7kNdiM')
	#i = minus('https://nappingdoneright.minus.com/mu6fuBNNdfPG0')
	#i = minus('http://nappingdoneright.minus.com/mu6fuBNNdfPG0')
	#i = minus('https://nappingdoneright.minus.com/')
	#i = minus('https://nappingdoneright.minus.com')
	#i = minus('https://nappingdoneright.minus.com/uploads')

	#i = gifyo('http://gifyo.com/ccrystallinee/')
	#i = gifyo('http://gifyo.com/deanandhepburn/') # private

	#i = imgsrc('http://imgsrc.ru/main/pic.php?ad=774665')
	#i = imgsrc('http://imgsrc.ru/jp101091/26666184.html?pwd=&lang=en#')
	#i = imgsrc('http://imgsrc.ru/hugo004/21447611.html')
	#i = imgsrc('http://imgsrc.ru/fotoivanov/a661729.html')

	#i = imagefap('http://www.imagefap.com/pictures/1561127/young-porn-girlie-masterbating')
	#i = imagefap('http://www.imagefap.com/pictures/3883233/Maya-Black-Hot-Ts-2013')
	#i = xhamster('http://xhamster.com/photos/gallery/635024/kira_the_beautiful_busty_redhead_xxx.html')

	#i = five00px('http://500px.com/xxxsweetxxx')
	
	#i = imgur('http://imgur.com/r/realgirls/new/day/')
	#i = imgur('http://imgur.com/r/amateurarchives/top/all/')
	#i = chickupload('http://chickupload.com/gallery/106023/Z64FYY7Q')
	#i = deviantart('http://depingo.deviantart.com/gallery/')
	#i = teenplanet('http://photos.teenplanet.org/atomicfrog/Dromeus/Skinny_Babe_vs_Bfs_Cock')
	#i = cghub('http://wacomonkey.cghub.com/images/', urls_only=True)
	#i = fourchan('http://boards.4chan.org/s/res/14177077', urls_only=True)
	#i = anonib('http://www.anonib.com/azn/res/74347.html', urls_only=True)
	#i = chickupload('http://chickupload.com/gallery/30621/OMTDRPYU', urls_only=True)
	#i = deviantart('http://kindi-k.deviantart.com/gallery/', urls_only=True)
	#i = five00px('http://500px.com/xxxsweetxxx', urls_only=True)
	#i = getgonewild('http://getgonewild.com/profile/twoholes101', urls_only=True)
	#i = gifyo('http://gifyo.com/ccrystallinee/', urls_only=True)
	#i = imagearn('http://imagearn.com/gallery.php?id=226220', urls_only=True)
	#i = imagebam('http://www.imagebam.com/gallery/3e4u10fk034871hs6idcil6txauu3ru6/', urls_only=True)
	#i = imagefap('http://www.imagefap.com/pictures/2885204/Kentucky-Craigslist', urls_only=True)
	#i = imgsrc('http://imgsrc.ru/fotoivanov/a661729.html', urls_only=True)
	#i = imgur('http://imgur.com/a/brixs', urls_only=True)
	#i = instagram('http://web.stagram.com/n/glitterypubez/', urls_only=True)
	#i = minus('http://zuzahgaming.minus.com/mF31aoo7kNdiM', urls_only=True)
	#i = motherless('http://motherless.com/G7DC1B74', urls_only=True)
	#i = tumblr('http://caramiaphotography.tumblr.com/tagged/me', urls_only=True)
	#i = twitter('https://twitter.com/darrow_ashley', urls_only=True)
	#i = xhamster('http://xhamster.com/photos/gallery/1443114/cute_teens.html', urls_only=True)
	#i = occ('http://forum.oneclickchicks.com/showthread.php?t=137808', urls_only=True)
	#i = chansluts('http://www.chansluts.com/camwhores/girls/res/9447.php')
	#i = flickr('http://www.flickr.com/photos/sabrina-dacos/') # NSFW, "bad panda"
	#i = flickr('http://www.flickr.com/photos/alifewortheating/sets/72157632351550870/')
	#i = flickr('http://www.flickr.com/photos/vichollo/')
	#i = c('', urls_only=True)
	#http://vk.com/album-34908971_163639688
	#i = gonearch('http://gonearchiving.com/indexpics.php?author=personally-yours')
	i = gonearch('http://gonearchiving.com/indexlist.php?author=nutmegster')

	print i.working_dir
	print i.url
	if i.existing_zip_path() != None:
		print 'Zip exists: %s' % i.existing_zip_path()
	else:
		print 'downloading...'
		i.download()
		'''
		print 'checking for zip:',
		print str(i.existing_zip_path())
		print "zip = %s" % i.zip()
		print 'checking for zip:',
		print str(i.existing_zip_path())
		if i.existing_zip_path().endswith('.txt'):
			f = open(i.existing_zip_path(), 'r')
			print f.read()
			f.close()
		'''
except KeyboardInterrupt:
	print '\ninterrupted'
#except Exception, e:
	#print "\nEXCEPTION: %s" % str(e)
