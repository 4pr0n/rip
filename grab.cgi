#!/usr/bin/python

# Used for zipping directories
from zipfile import ZipFile, ZIP_DEFLATED

import cgitb; cgitb.enable() # for debugging
import cgi # for getting query keys/values

import os, sys

import time
from Web import Web
from threading import Thread

import urllib

web = Web()

MAX_THREADS  = 3
THREAD_COUNT = 0

TOTAL_IMAGES  = 0
CURRENT_IMAGE = 0

LOG = None

TUMBLR_API_KEY = 'v5kUqGQXUtmF7K0itri1DGtgTs0VQpbSEbh1jxYgj9d2Sq18F8'


###########################
# IMGUR
def download_imgur_album(album, dir):
	global TOTAL_IMAGES, CURRENT_IMAGE
	
	if not dir.endswith(os.sep): dir += os.sep
	
	LOG.write("getting list of images\n");
	LOG.flush()
	r = web.get(album)
	
	pics = web.between(r, '<img src="http://i.imgur.com/', '"')
	TOTAL_IMAGES = len(pics)
	count = 0
	for pic in pics:
		count += 1
		download_imgur(pic, count, dir)
	
	LOG.write("waiting for downloads to complete\n")
	LOG.flush()
	while THREAD_COUNT > 0: time.sleep(0.1)


		
def download_imgur(url, index, dir):
	global THREAD_COUNT, MAX_THREADS
	while THREAD_COUNT >= MAX_THREADS: time.sleep(0.1)
	
	u = url
	i = u.find('.')
	# dpugoh.jpg
	if u[i-1] == 'h' and i > 5:
		temp = u[:i-1] + u[i:]
		m = web.get_meta('http://i.imgur.com/%s' % temp)
		if 'Content-Type' in m and 'image' in m['Content-Type']:
			u = temp
	
	save_as = dir + ('%03d' % (index)) + '_' + u[u.rfind('/')+1:]
	if os.path.exists(save_as):
		return
	
	u = 'http://i.imgur.com/' + u
	
	THREAD_COUNT += 1
	t = Thread(target=doit_imgur, args=(u, save_as))
	t.start()


def doit_imgur(url, save_as):
	global THREAD_COUNT, TOTAL_IMAGES, CURRENT_IMAGE
	web.download(url, save_as)
	CURRENT_IMAGE += 1
	THREAD_COUNT -= 1
	LOG.write("downloaded image %d of %d\n" % (CURRENT_IMAGE, TOTAL_IMAGES))
	LOG.flush()


##########################
# DEVIANT ART
def deviant_login():
	d = {	      'ref': 'https://www.deviantart.com/users/loggedin',
			   'username': '',
			   'password': '',
			'remember_me': '0'
		}
	LOG.write('logging into deviantart...\n')
	r = web.post('https://www.deviantart.com/users/login', postdict=d)
	if r.find('{"loggedIn":true') == -1:
		LOG.write('unable to log into deviant art\n')
		exit(1)
	LOG.write('logged in\n')

def download_deviantart(url, dir):
	global MAX_THREADS, THREAD_COUNT, CURRENT_IMAGE, TOTAL_IMAGES
	
	#deviant_login()
	
	user = url[7:url.find('.', 7)]
	
	u = url
	base_url = u[:u.find('.')] + '.deviantart.com'
	
	# check for subdirectory (specific gallery requested)
	sdir = ''
	if u.find('/gallery/') != -1:
		gid = u[u.find('/gallery/') + len('/gallery/'):]
		if gid.find('#') != -1: gid = gid[:gid.find('#')]
		if gid.isdigit():
			sdir = gid
		u = u[:u.find('/gallery/')] + '/gallery/' + gid
	if sdir != '':
		#dir = 'deviantart_' + user + '_' + sdir + os.sep
		pass
	else:
		u = u[:u.find('.')] + '.deviantart.com/gallery/?catpath=/'
		#dir = 'deviantart_' + user + os.sep
	
	already_got = []
	CURRENT_INDEX = 0
	while True:
		LOG.write('loading gallery...\n')
		r = web.get(u)
		
		imgs = web.between(r, '<a class="thumb" href="', '"')
		matures = web.between(r, '<a class="thumb ismature" href="', '"')
		prints = web.between(r, '<a class="thumb hasprint" href="', '"')
		print len(imgs) + len(matures) + len(prints)
		for img in imgs + matures + prints:
			if already_got.count(img) > 0: continue
			already_got.append(img)
			CURRENT_INDEX += 1
			while THREAD_COUNT >= MAX_THREADS: time.sleep(0.1)
			THREAD_COUNT += 1
			t = Thread(target=doit_deviantart, args=(img, dir, CURRENT_INDEX))
			t.start()
		
		nexts = web.between(r, '<li class="next">', '</li>')
		if len(nexts) == 0: break
		next = nexts[0]
		if next.find('href="') == -1: break
		u = base_url + web.between(next, 'href="', '"')[0]
		time.sleep(1)
	while THREAD_COUNT > 0: time.sleep(0.1)
	
def doit_deviantart(url, save_dir, index):
	global THREAD_COUNT
	
	r = web.get(url)
	u = ''
	dls = web.between(r, 'id="download-button" href="', '"')
	if len(dls) > 0:
		# easy, there's a download button
		u = web.unshorten(dls[0])
	elif r.find('ResViewSizer_img"') != -1:
		bet = web.between(r, 'ResViewSizer_img"', '>')[0]
		u = web.between(bet, 'src="', '"')[0]
	
	if u == '':
		LOG.write('unable to find download link for %s, skipping\n' % url)
		THREAD_COUNT -= 1
		return
	
	filename = u[u.rfind('/')+1:]
	save_as = save_dir + filename
	if os.path.exists(save_as):
		# File already exists, skip
		LOG.write('file already exists %s\n' % save_as)
		THREAD_COUNT -= 1
		return
	
	res = web.download(u, save_as)
	if res:
		LOG.write('downloaded #%d (%s)\n' % (index, inttosize(os.path.getsize(save_as))))
	else:
		LOG.write("%s error downloading %s, skipping\n" % (url))
	THREAD_COUNT -= 1


##########################
# IMAGEVENUE
def download_imagevenue(album, dir):
	global CURRENT_IMAGE
	CURRENT_IMAGE = 1
	
	try: os.mkdir(dir)
	except: pass
	if not dir.endswith(os.sep): dir += os.sep
	
	LOG.write('loading album...\n')
	LOG.flush()
	next_url = album
	while next_url != '':
		r = web.get(next_url)
		urls = web.between(r, 'onLoad="scaleImg();"   SRC="', '"')
		if len(urls) == 0: break # No image
		url = urls[0]
		
		nexts = web.between(r, '<a href=', '>')
		if r.find('>Next>></a>') != -1:
			if r.find('<< Previous</a>') != -1 and len(nexts) >= 3:
				next_url = nexts[2].strip()
			elif len(nexts) >= 2:
				next_url = nexts[1].strip()
		else:
			next_url = ''
		
		j = r.find('get_code.php')
		i = r.rfind('http://', 0, j)
		domain = r[i:j]
		doit_imagevenue(domain + url, dir)

def doit_imagevenue(url, dir):
	global CURRENT_IMAGE
	save_as = str(CURRENT_IMAGE) + url[url.rfind('.'):]
	while os.path.exists(dir + save_as):
		CURRENT_IMAGE += 1
		save_as = str(CURRENT_IMAGE) + url[url.rfind('.'):]
	
	web.download(url, dir + save_as)
	
	LOG.write("downloaded #%d %s (%s)\n" % (CURRENT_IMAGE, save_as, inttosize(os.path.getsize(dir + save_as))))
	LOG.flush()
	CURRENT_IMAGE += 1


##########################
# IMAGEBAM
def download_imagebam(url, dir):
	count = 0
	
	if not dir.endswith('/'): dir += '/'
	try: os.mkdir(dir)
	except OSError: pass
	
	next_url = url
	
	LOG.write('loading album...\n')
	LOG.flush()
	while (next_url != ''):
		r = web.get(next_url)
		
		img_url = web.between(r, 'onclick="scale(this);" src="', '"')[0]
		img_url = img_url.replace('&amp;', '&')
		
		count += 1
		save_as = str(count) + img_url[img_url.rfind('.'):]
		while os.path.exists(dir + save_as):
			count += 1
			save_as = str(count) + img_url[img_url.rfind('.'):]
			
		web.download(img_url, dir + save_as)
		
		LOG.write("downloaded %s (%s)\n" % (save_as, inttosize(os.path.getsize(dir + save_as))))
		LOG.flush()
		
		next_urls = web.between(r, "<a class='buttonblue' href='", "'>")
		if len(next_urls) == 1 and not '<span>next image' in r:
			break
		next_url = next_urls[0]
		next_url = next_url.replace('&amp;', '&')
		next_url = 'http://www.imagebam.com' + next_url


#############################
# IMAGEFAP
def download_imagefap(url, dir):
	global CURRENT_IMAGE, TOTAL_IMAGES, THREAD_COUNT
	CURRENT_IMAGE = 0
	
	if not dir.endswith('/'): dir += '/'
	utemp = url
	if utemp.find("?view=2") == -1:
		if '?' in utemp: utemp = utemp[:utemp.find('?')]
		utemp += "?view=2"
	
	LOG.write('loading album...\n')
	LOG.flush()
	r = web.get(utemp)
	urls = web.between(r, 'x.fap.to/images/thumb/', '"')
	TOTAL_IMAGES = len(urls)
	
	for url in urls:
		# Skip the first url
		if CURRENT_IMAGE == 0:
			CURRENT_IMAGE += 1
			continue
		
		u = 'http://x.fap.to/images/full/' + url
		
		while THREAD_COUNT >= MAX_THREADS: time.sleep(0.1)
		
		t = Thread(target=doit_imagefap, args=(u, dir))
		THREAD_COUNT += 1
		t.start()
	
	while THREAD_COUNT > 0: time.sleep(0.1)
	
def doit_imagefap(url, dir):
	global CURRENT_IMAGE, TOTAL_IMAGES, THREAD_COUNT, MAX_THREADS
	
	save_as = str(CURRENT_IMAGE) + url[url.rfind('.'):]
	while os.path.exists(dir + save_as):
		CURRENT_IMAGE += 1
		save_as = str(CURRENT_IMAGE) + url[url.rfind('.'):]
	
	temp = CURRENT_IMAGE
	CURRENT_IMAGE += 1
	
	web.download(url, dir + save_as)
	LOG.write("%d/%d %s %s\n" % (temp, TOTAL_IMAGES, save_as, inttosize(os.path.getsize(dir + save_as))))
	LOG.flush()
	THREAD_COUNT -= 1



##############################
# PHOTOBUCKET
def download_photobucket(album, dir):
	global CURRENT_IMAGE, TOTAL_IMAGES, THREAD_COUNT, MAX_THREADS
	
	u = album
	if u.startswith('http://') == -1: u = 'http://' + u
	if u.find('#') != -1: u = u[:u.find('#')]
	if u.find('?') != -1: u = u[:u.find('?')]
	if not u.endswith('/'): u += '/'
	
	if u[:u.find('.')] == 'http://www':
		print "\n full photobucket URL required.\n for example: http://s1204.photobucket.com/albums/bb412/spyrotheswaggin/"
		return
	
	i = u.find('/', u.find('/', u.find('/', 8) + 1) + 1)
	j = u.find('/', i + 1)
	if i == -1 or j == -1:
		print "\n invalid photobucket URL.\n use a full URL, for example: http://s1204.photobucket.com/albums/bb412/spyrotheswaggin/"
		return
	user = u[i+1:j]
	
	r = web.get('http://s579.photobucket.com/allalbums?ownername=' + user)
	albs = web.between(r, '''sub_album_link_click');" href="''', '"')
	for u in albs:
		start = 0
		this_total = -1
		this_current = 0
		a = 'default'
		sdir = dir + '/'
		if u.count('/') != 6:
			a = u[u.rfind('/', 0, len(u) - 1)+1:-1]
			a = a.replace('%20', ' ')
			if not dir.endswith('/'):
				sdir = dir + os.sep + a + os.sep
			else:
				sdir = dir + a + os.sep
			try:
				os.mkdir(sdir)
			except: pass
		elif not dir.endswith('/'):
			sdir = dir + '/'
		else: sdir = dir
			
		while True:
			r = web.get(u + '?start=%d' % start)
			if this_total == -1:
				x = web.between(r, '<span class="subMenu">', ' ')
				if len(x) > 0:
					this_total = int(x[0])
			
			fnames = web.between(r, '?action=view&current=', '"')
			for fname in fnames:
				this_current += 1
				dl = u + fname
				while THREAD_COUNT >= MAX_THREADS: time.sleep(0.1)
				
				t = Thread(target=doit_photobucket, args=(dl, sdir, fname, this_total, this_current, a))
				t.start()
			
			if len(fnames) == 0: break
			start += len(fnames)
	
def doit_photobucket(url, dir, save_as, ttl, cur, album):
	global THREAD_COUNT, MAX_THREADS
	
	temp = cur
	THREAD_COUNT += 1
	if os.path.exists(dir + save_as):
		#print "!file already exists: %s" % save_as
		THREAD_COUNT -= 1
		return
	
	web.download(url, dir + save_as)
	LOG.write("(%s) %d/%d %s %s\n" % (album, temp, ttl, save_as, inttosize(os.path.getsize(dir + save_as))))
	LOG.flush()
	
	THREAD_COUNT -= 1


############################
# FLICKR
def download_flickr(album, dir):
	global MAX_THREADS, THREAD_COUNT, CURRENT_IMAGE, TOTAL_IMAGES
	
	u = album
	if not dir.endswith('/'): dir += '/'
	
	CURRENT_IMAGE = 0
	TOTAL_IMAGES = 0
	
	LOG.write("loading album...\n")
	LOG.flush()
	while u != '':
		r = web.get(u)
		if TOTAL_IMAGES == 0:
			ttls = web.between(r, '<div class="Results">(', ' i')
			if len(ttls) > 0:
				TOTAL_IMAGES = int(ttls[0].replace(',', ''))
		
		pages = web.between(r, '><a data-track="photo-click" href="', '"')
		if len(pages) == 0:
			pages = web.between(r, '"photo_container pc_t"><a href="', '"')
		
		for page in pages:
			p = 'http://www.flickr.com' + page
			
			while THREAD_COUNT >= MAX_THREADS: time.sleep(0.1)
			THREAD_COUNT += 1
			CURRENT_IMAGE += 1
			t = Thread(target=doit_flickr, args=(p, dir, CURRENT_IMAGE))
			t.start()
		
		nexts = web.between(r, 'data-track="next" href="', '"')
		if len(nexts) > 0:
			u = 'http://www.flickr.com' + nexts[0]
		else:
			u = ''
	while THREAD_COUNT > 0: time.sleep(0.1)	
	

def doit_flickr(url, dir, index):
	global THREAD_COUNT, TOTAL_IMAGES
	id = url
	if id.find('/in/set') != -1:
		id = id[:id.find('/in/set')]
	elif id.find('/in/photostream') != -1:
		id = id.replace('/in/photostream', '')
	if id.endswith('/'): id = id[:-1]
	if id.find('/') != -1: id = id[id.rfind('/')+1:]
	
	r = web.get(url)
	chunks = web.between(r, 'sizes: {', 'tags:')
	if len(chunks) == 0: return
	sizes = web.between(chunks[0], "url: '", "'")
	if len(sizes) == 0: return
	u = sizes[-1]
	save_as = id + u[u.rfind('.'):]
	if save_as.find('?') != -1: save_as = save_as[:save_as.find('?')]
	
	if os.path.exists(dir + save_as):
		LOG.write('%d already exists! %s %9s\n' % (index, save_as, inttosize(os.path.getsize(dir + save_as))))
		LOG.flush()
		THREAD_COUNT -= 1
		return
	
	result = web.download(u, dir + save_as)
	if not result:
		web.download(u, dir + save_as)
	
	if TOTAL_IMAGES != 0:
		LOG.write('%d/%d downloaded %s\n' % (index, TOTAL_IMAGES, inttosize(os.path.getsize(dir + save_as))))
		LOG.flush()
	else:
		LOG.write('#%d downloaded %s %s\n' % (index, save_as, inttosize(os.path.getsize(dir + save_as))))
		LOG.flush()
	
	THREAD_COUNT -= 1


########################
# TUMBLR
def download_tumblr(url, dir):
	global CURRENT_IMAGE, TOTAL_IMAGES, THREAD_COUNT, MAX_THREADS
	
	# Get user
	url = url.replace('https://', '')
	url = url.replace('http://', '')
	user = url[:url.find('.')]
	
	# Get API URL
	domain = '%s.tumblr.com' % user
	base_url = 'http://api.tumblr.com/v2/blog/%s/posts/photo' % domain
	base_url += '?api_key=%s' % TUMBLR_API_KEY
	
	offset = 0
	tag = None
	if '/tagged/' in url:
		tag = url[url.find('/tagged/')+len('/tagged/'):]
	
	TOTAL_IMAGES = -1
	while True:
		u = base_url + '&offset=%d' % offset
		if tag != None:
			u += '&tag=%s' % (tag.replace(' ', '+'))
		r = web.get(u)
		if TOTAL_IMAGES < 0:
			totals = web.between(r, '"total_posts":', '}')
			if len(totals) > 0:
				TOTAL_IMAGES = int(totals[0])
		post_chunks = web.between(r, '"blog_name":', '}]}')
		if len(post_chunks) == 0: break
		for post_chunk in post_chunks:
			ids = web.between(post_chunk, '"id":', ',')
			if len(ids) == 0: continue
			id = ids[0]
			photo_chunks = web.between(post_chunk, '"original_size":{', '}')
			if len(photo_chunks) == 0: break
			for chunk in photo_chunks:
				if not '"url":"' in chunk: continue
				photo = chunk[chunk.find('"url":"')+len('"url":"'):-1]
				photo = photo.replace('\\/', '/')
				
				while THREAD_COUNT >= MAX_THREADS: time.sleep(0.1)
				THREAD_COUNT += 1
				
				t = Thread(target=doit_tumblr, args=(photo, user, dir, id, CURRENT_IMAGE))
				CURRENT_IMAGE += 1
				t.start()
		if CURRENT_IMAGE >= TOTAL_IMAGES: break
		time.sleep(2)
		offset += 20
	
	# Videos
	LOG.write("loading videos...\n")
	LOG.flush()
	base_url = base_url.replace('/posts/photo?', '/posts/video?')
	added_total = False
	offset = 0
	while True:
		u = base_url + '&offset=%d' % offset
		if tag != None:
			u += '&tag=%s' % (tag.replace(' ', '+'))
		r = web.get(u)
		if not added_total:
			totals = web.between(r, '"total_posts":', '}')
			if len(totals) > 0:
				TOTAL_IMAGES += int(totals[0])
				added_total += 1
		vid_chunks = web.between(r, '"blog_name":', '}]}')
		if len(vid_chunks) == 0: break
		for vid_chunk in vid_chunks:
			ids = web.between(vid_chunk, '"id":', ',')
			if len(ids) == 0: continue
			id = ids[0]
			videos = web.between(vid_chunk, '"video_url":"', '"')
			if len(videos) == 0: continue
			video = videos[0].replace('\\/', '/')
			LOG.write("waiting for threads\n")
			LOG.flush()
			while THREAD_COUNT >= MAX_THREADS: time.sleep(0.1)
			THREAD_COUNT += 1
			
			LOG.write("downloading %s to %s, id=%s\n" % (video, dir, id))
			LOG.flush()
			t = Thread(target=doit_tumblr, args=(video, user, dir, id, CURRENT_IMAGE))
			CURRENT_IMAGE += 1
			t.start()
	
		if CURRENT_IMAGE >= TOTAL_IMAGES: break
		time.sleep(2)
		offset += 20
	
	# Wait for threads to finish
	while THREAD_COUNT > 0: time.sleep(0.1)

def doit_tumblr(url, user, dir, id, index):
	global THREAD_COUNT
	
	# Get extension (.jpg, .gif, etc)
	ext = url
	if ext.find('?') != -1: ext = ext[:ext.find('?')]
	ext = ext[ext.rfind('.'):]
	save_as = dir + '/tumblr_%s_%s%s' % (user, id, ext)
	
	if os.path.exists(save_as):
		#print "!file already exists: %s" % (save_as)
		THREAD_COUNT -= 1
		return
	
	if '_500.jpg' in url:
		url2 = url.replace('_500.jpg', '_1280.jpg')
		if web.check(url2): url = url2
	
	LOG.write("downloading %d of %d\n" % (index + 1, TOTAL_IMAGES))
	LOG.flush()
	web.download(url, save_as)
	#LOG.write("downloaded %d of %d (%s)\n" % (index + 1, TOTAL_IMAGES, inttosize(os.path.getsize(save_as))))
	#LOG.flush()
	
	THREAD_COUNT -= 1

def download_getgonewild(url, dir):
	global THREAD_COUNT
	while dir.endswith('/'): dir = dir[:-1]
	LOG.write("loading album\n")
	LOG.flush()
	r = web.get(url)
	index = 1
	links = web.between(r, '","url":"', '"')
	total = len(links)
	for link in links:
		while THREAD_COUNT >= MAX_THREADS: time.sleep(0.1)
		THREAD_COUNT += 1
		t = Thread(target=doit_getgonewild, args=(link, dir, index, total))
		index += 1
		t.start()
	LOG.write("waiting for downloads to complete\n")
	LOG.flush()
	while THREAD_COUNT > 0: time.sleep(0.1)

def doit_getgonewild(url, dir, index, total):
	global THREAD_COUNT
	try:
		url = url.replace('\\/', '/')
		if 'imgur.com/a/' in url:
			pass
			# album
			while url.endswith('/'): url = url[:-1]
			r = web.get('%s/noscript' % url)
			alb_index = 1
			links = web.between(r, '<a class="zoom" href="', '"')
			alb_total = len(links)
			for link in links:
				LOG.write("downloading (%d/%d) - (%d/%d)\n" % (index, total, alb_index, alb_total))
				LOG.flush()
				filename = '%s/%03d_%03d_%s' % (dir, index, alb_index, link[link.rfind('/')+1:])
				retry_download(link, filename)
				alb_index += 1
		else:
			LOG.write("downloading (%d/%d)\n" % (index, total))
			LOG.flush()
			# image
			if url.lower().endswith('.jpeg') or \
					url.lower().endswith('.jpg') or \
					url.lower().endswith('.gif') or \
					url.lower().endswith('.png'):
				# Direct link
				filename = '%s/%03d_%s' % (dir, index, url[url.rfind('/')+1:])
				retry_download(url, filename)
			else:
				r = web.get(url)
				links = web.between(r, '<meta name="twitter:image" value="', '"')
				if len(links) == 0:
					links = web.between(r, '<link rel="image_src" href="', '"')
				if len(links) > 0:
					link = links[0]
					filename = '%s/%03d_%s' % (dir, index, link[link.rfind('/')+1:])
					retry_download(link, filename)
	except Exception, e:
		LOG.write('%s: %s\n' % (url, str(e)))
		LOG.flush()
	THREAD_COUNT -= 1

def retry_download(url, saveas):
	dot = url.rfind('.')
	if url[dot-1] == 'h':
		tempurl = url[:dot-1] + url[dot:]
		m = web.get_meta(tempurl)
		if 'Content-Type' in m and 'image' in m['Content-Type']:
			url = tempurl
	tries = 3
	while tries > 0:
		if web.download(url, saveas): 
			if os.path.getsize(saveas) < 5000:
				f = open(saveas, 'r')
				txt = f.read()
				f.close()
				if 'File not found!' in txt:
					os.remove(saveas)
			return
		tries -= 1
	os.remove(saveas)


def download_twitter(user, dir):
	global THREAD_COUNT
	retrieve_count = 200
	if not dir.endswith(os.sep): dir += os.sep
	LOG.write('loading tweets...\n')
	LOG.flush()
	r = web.getter('https://api.twitter.com/1/statuses/user_timeline.json?screen_name=%s&include_entities=true&exclude_replies=true&trim_user=true&include_rts=false&count=%d' % (user, retrieve_count))
	all_urls = []
	index = 0
	while True:
		medias = web.between(r, '"media":[{', '}]')
		maxid = '0'
		new_urls = []
		beforecount = len(all_urls)
		for media in medias:
			ids = web.between(media, '"id":', ',')
			if len(ids) > 0:
				maxid = ids[0]
			urls = web.between(media, '"media_url":"', '"')
			for url in urls:
				url = url.replace('\\/', '/')
				if not url in all_urls:
					new_urls.append(url)
				all_urls.append(url)
		all_urls = list(set(all_urls))
		aftercount = len(all_urls)
		if beforecount == aftercount: break
		for url in new_urls:
			while THREAD_COUNT >= MAX_THREADS: time.sleep(0.1)
			THREAD_COUNT += 1
			index += 1
			t = Thread(target=doit_twitter, args=(url, dir, index, len(all_urls)))
			t.start()
		if maxid != '0':
			LOG.write('checking for more tweets...\n')
			LOG.flush()
			time.sleep(2)
			r = web.getter('https://api.twitter.com/1/statuses/user_timeline.json?screen_name=%s&include_entities=true&exclude_replies=true&trim_user=true&include_rts=false&count=%d&max_id=%s' % (user, retrieve_count, maxid))
	while THREAD_COUNT > 0: time.sleep(0.1)

def doit_twitter(url, dir, index, total):
	global THREAD_COUNT
	filename = url[url.rfind('/')+1:]
	saveas = '%s%04d_%s' % (dir, index, filename)
	if not os.path.exists(saveas):
		time.sleep(0.3)
		result = web.download(url, saveas)
		if result:
			LOG.write('downloaded (%d/%d)\n' % (index, total))
			LOG.flush()
		else:
			LOG.write('download FAILED (%d/%d)\n' % (index, total))
			LOG.flush()
	THREAD_COUNT -= 1


""" Zip all files in a directory """
def zipdir(basedir, archivename):
	assert os.path.isdir(basedir)
	z = ZipFile(archivename, "w", ZIP_DEFLATED)
	for root, dirs, files in os.walk(basedir):
		#NOTE: ignore empty directories
		for fn in files:
			if 'log.txt' in fn: continue
			absfn = os.path.join(root, fn)
			zfn = absfn[len(basedir)+len(os.sep):] #XXX: relative path
			z.write(absfn, zfn)
	z.close()

# converts numeric bytes into human-readable format
def inttosize(bytes):
	b = 1024 * 1024 * 1024 * 1024
	a = ['t','g','m','k','']
	for i in a:
		if bytes >= b:
			return '%.2f%sb' % (float(bytes) / float(b), i)
		b /= 1024
	return '0b'

""" Retrieves key/value pairs from query, puts in dict """
def get_keys():
	form = cgi.FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = form[key].value
	if not 'url' in keys and len(sys.argv) > 1:
		keys['url'] = sys.argv[1]
	return keys


""" Where the magic happens """
def main():
	global LOG, CURRENT_IMAGE
	
	try: os.mkdir('rips')
	except OSError: pass
	
	keys = get_keys()
	if not 'url' in keys:
		print 'no input link given; exiting.'
		return
	given_album = keys['url']
	
	album = urllib.unquote(given_album)
	if not album.startswith('http'): album = 'http://' + album
	
	domain_ripper = None
	
	# Check for IMGUR
	if 'imgur.com' in album:
		if '#' in album: album = album[:album.find('#')]
		if album.endswith('/'): album = album[:len(album)-1]
		if not '/' in album:
			print 'imgur album required'
			return
		albumid = album[album.rfind('/')+1:]
		if 'i.imgur.com' in album or \
			 not '/a/' in album and not '.imgur.com' in album or \
			 len(albumid) != 5:
			print 'invalid imgur album format.<br>'
			print 'please use the format:<br><br>'
			print 'http://imgur.com<b>/a/$$$$</b><br>'
			print 'where $ is letter or number.'
			return
			
		dir = 'rips/imgur_' + albumid
		album += "/noscript"
		
		domain_ripper = download_imgur_album
		
	# Check for PHOTOBUCKET
	elif 'photobucket.com' in album and False:
		u = album
		if u.startswith('http://') == -1: u = 'http://' + u
		if u.find('#') != -1: u = u[:u.find('#')]
		if u.find('?') != -1: u = u[:u.find('?')]
		if not u.endswith('/'): u += '/'
		
		if u[:u.find('.')] == 'http://www':
			print "\n full photobucket URL required.\n for example: http://s1204.photobucket.com/albums/bb412/spyrotheswaggin/"
			return
		
		i = u.find('/', u.find('/', u.find('/', 8) + 1) + 1)
		j = u.find('/', i + 1)
		if i == -1 or j == -1:
			print "\n invalid photobucket URL.\n use a full URL, for example: http://s1204.photobucket.com/albums/bb412/spyrotheswaggin/"
			return
		user = u[i+1:j]
		dir = 'rips/photobucket_%s' % (user)
		domain_ripper = download_photobucket
	
	# Check for FLICKR
	elif 'flickr.com' in album:
		# get username
		user = 'unknown'
		if u.find('/photos/') != -1:
			user = u[u.find('/photos/') + len('/photos/'):]
			if user.find('/') != -1: user = user[:user.find('/')]
		DIR = "rips/flickr_" + user
		domain_ripper = download_flickr
		
	# Check for DEVIANT ART
	elif '.deviantart.com' in album:
		if album.startswith('http://'): album = album[7:]
		user = album[:album.find('.')]
		if user.lower() == 'www':
			usage()
			return()
		dir = 'rips/deviantart_' + user
		album = 'http://' + album
		domain_ripper = download_deviantart
		
	# Check for IMAGEVENUE
	elif 'imagevenue.com' in album:
		txt = album
		if '?image=' in txt:
			i = txt.find('?image=') + 7
			j = txt.find('_', i)
			if txt.find('.', i) < j:
				j = txt.find('.', i)
			txt = 'imagevenue_' + txt[i:j]
		else:
			txt = 'imagevenue'
		dir = 'rips/' + txt
		domain_ripper = download_imagevenue
		
	# Check for IMAGEBAM
	elif 'imagebam.com' in album:
		dir = 'rips/imagebam'
		if os.path.exists(dir + '.zip'): os.remove(dir + '.zip')
		domain_ripper = download_imagebam
		
	# Check for IMAGEFAP
	elif 'imagefap.com/pictures/' in album:
		dir = 'rips/imagefap'
		if '/pictures/' in album:
			dir += '_' + album[album.find('/pictures/')+len('/pictures/'):].replace('/', '_')
		if '?' in dir: dir = dir[:dir.find('?')]
		domain_ripper = download_imagefap
		
	# Check for TUMBLR
	elif '.tumblr.com' in album:
		url = album.replace('https://', '')
		url = url.replace('http://', '')
		user = url[:url.find('.')]
		dir = 'rips/tumblr_%s' % user
		domain_ripper = download_tumblr
	
	elif 'getgonewild.com/profile/' in album:
		while album.endswith('/'): album = album[:-1]
		user = album[album.rfind('/')+1:]
		dir = 'rips/getgonewild_%s' % user
		domain_ripper = download_getgonewild
	
	elif 'twitter.com/' in album:
		user = album[album.find('twitter.com/')+len('twitter.com/'):]
		if '/' in user:
			user = user[:user.find('/')]
		dir = 'rips/twitter_%s' % user
		album = user
		domain_ripper = download_twitter
		
	if domain_ripper == None:
		usage(given_album)
		return
	
	# Check if 'dir' already exists (or more importantly dir.zip)
	if os.path.exists(dir + '.zip'):
		print 'album zipped to <a href="%s%s">%s%s</a>' % (dir, '.zip', dir, '.zip')
		return
	
	if os.path.exists(dir + '/'):
		print 'album download in progress; check back later'
		return
	
	try: os.mkdir(dir)
	except OSError, e: 
		print "UNABLE TO CREATE DIRECTORY: %s" % str(e)
		return
	
	LOG = open(dir + '/log.txt', 'w')
	try:
		domain_ripper(album, dir)
	except Exception, e:
		LOG.write("Error occurred while ripping %s: %s\n" % (url, str(e)))
		LOG.flush()
		os.rename('%s/log.txt' % dir, '%s_error.txt' % dir.replace('rips/', ''))
	if len(os.listdir(dir)) <= 1: # If there's only one file (log file)
		print 'ERROR: no images were downloaded <br>check the URL and try again'
		for f in os.listdir(dir):
			os.remove("%s/%s" % (dir, f))
		os.rmdir(dir)
		return
	
	time.sleep(0.5)
	LOG.write('zipping files...\n')
	LOG.flush()
	zipped = dir + '.zip'
	zipdir(dir, zipped)
	LOG.close()
	for filename in os.listdir(dir):
		os.remove(dir + '/' + filename)
	os.rmdir(dir)
	print 'album zipped to <a href="%s%s">%s%s</a>' % (dir, '.zip', dir, '.zip')
	
'''
try: os.mkdir('test')
except OSError: pass
LOG = open('test/log.txt', 'w')
download_photobucket('http://s1204.photobucket.com/albums/bb412/spyrotheswaggin/', 'test')
LOG.close()
exit(0)
'''

def usage(given_album):
	print '\n\n incompatible image host: %s<br>' % given_album
	print ' please use only the approved image hosts:<br><br>\n'
	print '    * imgur.com<br>'
	print '    * tumblr.com<br>'
	print '    * flickr.com<br>'
	print '    * deviantart.com<br>'
	print '    * imagefap.com<br>'
	print '    * imagebam.com<br>'
	print '    * imagevenue.com<br>'
	return
	print '    * imagearn.com<br>'
	print '    * imgsrc.ru<br>'
	print '    * webshots.com<br>'
	
if __name__ == '__main__':
	print "Content-Type: text/html"
	print ""
	main()
	print "\n\n"
