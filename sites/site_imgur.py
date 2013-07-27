#!/usr/bin/python

from basesite import basesite
from os import path, mkdir, listdir, rmdir
from json import loads

"""
	Downloads imgur albums
"""
class imgur(basesite):
	"""
		Only supports direct links to albums
		Does not support domain-level albums
		such as 'http://username.imgur.com/album_name'
	"""
	def sanitize_url(self, url):
		# Specifies type of imgur link
		#   "direct": imgur.com/a/XXXXX
		#   "domain": user.imgur.com
		#   "account": user.imgur.com/album_name
		#   "subreddit": imgur.com/r/subreddit
		self.album_type = None 
		if not 'http://imgur.com' in url and not '.imgur.com' in url:
			raise Exception('')
		if      '.imgur.com'    in url and \
				not 'i.imgur.com'   in url and \
				not 'www.imgur.com' in url:
			# Domain-level
			url = url.replace('http://', '').replace('https://', '')
			while url.endswith('/'): url = url[:-1]
			urls = url.split('/')
			url = '/'.join(urls[0:1]) # Only the domain & first subdir
			if '?' in url: url = url[:url.find('?')]
			if '#' in url: url = url[:url.find('#')]
			return 'http://%s' % url
		elif 'imgur.com/r/' in url:
			# Subreddit
			sub = url[url.find('imgur.com/r/')+len('imgur.com/r/'):]
			if sub.strip() == '':
				raise Exception("Not a valid imgur subreddit")
			while sub.endswith('/'): sub = sub[:-1]
			splits = sub.split('/')
			if len(splits) == 1:
				return 'http://imgur.com/r/%s/new/day' % splits[0]
			if splits[1] not in ['new', 'top']:
				raise Exception('Unexpected imgur subreddit sort order: %s' % splits[1])
			if len(splits) == 2:
				return 'http://imgur.com/r/%s/%s/all' % (splits[0], splits[1])
			if splits[2] not in ['day', 'month', 'year', 'all']:
				raise Exception('Unexpected imgur subreddit sort time: %s' % splits[2])
			return 'http://imgur.com/r/%s/%s/%s' % (splits[0], splits[1], splits[2])
			
		elif not '/a/' in url:
			raise Exception("Not a valid imgur album")
		else:
			url = url.replace('http://', '').replace('https://', '')
			while url.endswith('/'): url = url[:-1]
			while url.count('/') > 2: url = url[:url.rfind('/')]
			if '?' in url: url = url[:url.find('?')]
			if '#' in url: url = url[:url.find('#')]
			return 'http://%s' % url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = self.url
		u = u.replace('/all', '')
		if 'imgur.com/r/' in u:
			# Subreddit
			self.album_type = 'subreddit'
			trail = u[u.find('imgur.com/r/')+len('imgur.com/r/'):]
			return 'imgur_r_%s' % trail.replace('/', '_')
		
		elif '/a/' in u:
			# Album
			self.album_type = 'direct'
			aid = u[u.find('/a/')+len('/a/'):]
			if '/' in aid: aid = aid[:aid.find('/')]
			return 'imgur_%s' % aid
			
		elif u.replace('/', '').endswith('imgur.com'):
			# Domain-level full account URL (Multiple albums)
			self.album_type = 'account'
			user = u[u.find('//')+2:]
			user = user[:user.find('.')]
			return 'imgur_%s' % user
			
		else:
			# Domain-level album
			self.album_type = 'domain'
			while u.endswith('/'): u = u[:-1]
			user = u[u.find('//')+2:]
			user = user[:user.find('.')]
			slashes = u.split('/')
			return 'imgur_%s_%s' % (user, slashes[-1])

	def download(self):
		self.init_dir()
		self.max_images = 5000
		if  self.album_type == 'direct' or \
				self.album_type == 'domain':
			# Single album
			self.download_album(self.url)
		elif self.album_type == 'subreddit':
			# Subreddit
			self.download_subreddit(self.url)
		else:
			# Account-level album
			self.download_account(self.url)
	
	def text_to_fs_safe(self, text):
		safe = 'abcdefghijklmnopqrstuvwxyz0123456789-_ &'
		text = text.replace('&amp;', '&')
		result = ''
		for c in xrange(0, len(text)):
			if text[c].lower() in safe:
				result += text[c]
		return result
	
	def download_account(self, album):
		r = self.web.get(album)
		covers = self.web.between(r, '<div class="cover">', '</div>')
		for index, cover in enumerate(covers):
			url = self.web.between(cover, '<a href="', '"')[0]
			url = 'http:%s' % url
			alts = self.web.between(cover, 'alt="', '"')
			if len(alts) > 0:
				alt = alts[0].replace('"', '').replace('/', '').replace('\\', '')
			else: 
				alt = 'untitled'
			alt = self.text_to_fs_safe(alt)
			prev_dir = self.working_dir
			self.working_dir += '/%03d_%s' % (index + 1, alt)
			if not path.exists(self.working_dir):
				mkdir(self.working_dir)
			self.log('downloading album (%d/%d) \\"%s\\"' % (index + 1, len(covers), alt))
			self.download_album(url)
			self.working_dir = prev_dir
			if self.hit_image_limit(): break
		self.wait_for_threads()

	def download_album(self, album):
		# Temporary fix (this is ugly)
		# Use imgur's API to download album, this gets captions as well
		# Remove below lines to revert back to "noscript" method
		if '/a/' in album:
			self.download_album_json(album)
			self.wait_for_threads()
			return
		# Get album source
		r = self.web.get('%s/noscript' % album)
		# Get images
		links = self.web.between(r, 'img src="http://i.', '"')
		for index, link in enumerate(links):
			if '?' in link: link = link[:link.find('?')]
			if '#' in link: link = link[:link.find('#')]
			link = self.get_highest_res('http://i.%s' % link)
			# Download every image
			# Uses superclass threaded download method
			if self.urls_only:
				self.add_url(index + 1, link, total=len(links))
			else:
				self.download_image(link, index + 1, total=len(links)) 
				if self.hit_image_limit(): break
		self.wait_for_threads()
	
	def download_album_json(self, album):
		aid = album[album.find('/a/')+len('/a/'):]
		if '/' in aid: aid = aid[:aid.find('/')]
		r = self.web.get('http://api.imgur.com/2/album/%s.json' % aid)
		try:
			json = loads(r)
		except:
			return
		if not 'album' in json: return
		alb = json['album']
		if not 'images' in alb: return
		captions = []
		total = len(alb['images'])
		for index, image in enumerate(alb['images']):
			# Image
			url = image['links']['original']
			# Captions / Metadata
			meta = image['image']
			title = meta.get('title', '')
			caption = meta.get('caption', '')
			if title != '' or caption != '':
				captions.append( (url, title, caption) )
			if self.urls_only:
				self.add_url(index + 1, url, total=total)
			else:
				self.download_image(url, index + 1, total=total) 
				if self.hit_image_limit(): break
		if captions != []:
			f = open('%s/captions.txt' % self.working_dir, 'w')
			for meta in captions:
				f.write('url: %s\n  title: "%s"\n  caption: "%s"\n\n' % (meta[0], meta[1], meta[2]))
			f.close()
		
	def download_subreddit(self, album):
		self.max_images = 500
		index = 0
		total = 0
		page  = 0
		first_links = []
		stop = False
		while True:
			r = self.web.get('%s/page/%d' % (album, page))
			# Get images
			links = self.web.between(r, ' src="http://i.', '"')
			if len(links) == 0: break
			if len(first_links) == 0:
				first_links = links[:]
			else:
				for link in links:
					stop = link in first_links
			if stop: break
			total += len(links)
			for link in links:
				link = 'http://i.%s' % link.replace('b.jpg', '.jpg')
				ext = self.get_filetype(link)
				link = link.replace('.jpg', '.%s' % ext)
				if '?' in link: link = link[:link.find('?')]
				if '#' in link: link = link[:link.find('#')]
				link = self.get_highest_res(link)
				# Download every image
				# Uses superclass threaded download method
				index += 1
				if self.urls_only:
					self.add_url(index, link, total=total)
				else:
					self.download_image(link, index, total=total) 
					if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			page += 1
		self.wait_for_threads()
	
	def get_filetype(self, url):
		m = self.web.get_meta(url)
		if 'Content-Type' in m:
			ct = m['Content-Type']
			ext = ct[ct.find('/')+1:]
			if ext.lower() == 'jpeg': ext = 'jpg'
			return ext
		return 'jpg'
	
	""" Returns highest-res image by checking if imgur has higher res """
	def get_highest_res(self, url):
		if not 'h.' in url:
			return url
		temp = url.replace('h.', '.')
		m = self.web.get_meta(temp)
		if 'Content-Type' in m and 'image' in m['Content-Type'].lower():
			return temp
		else:
			return url
		
