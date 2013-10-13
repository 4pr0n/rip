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
		self.debug('url before: %s' % url)
		if not 'http://imgur.com' in url and not '.imgur.com' in url:
			raise Exception('')
		if '/m.imgur.com/' in url: url = url.replace('/m.imgur.com/', '/imgur.com/')
		if      '.imgur.com'    in url and \
				not url.startswith('i.imgur.com') and \
				not url.startswith('www.imgur.com'):
			url = url.replace('https://', 'http://').replace('http://', '')
			# Domain-level
			while url.endswith('/'): url = url[:-1]
			urls = url.split('/')
			url = '/'.join(urls[0:2]) # Only the domain & first subdir
			if '?' in url: url = url[:url.find('?')]
			if '#' in url: url = url[:url.find('#')]
			url = 'http://%s' % url
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
			url = 'http://imgur.com/r/%s/%s/%s' % (splits[0], splits[1], splits[2])
			
		elif not '/a/' in url:
			raise Exception("Not a valid imgur album")
		else:
			url = url.replace('http://', '').replace('https://', '')
			while url.endswith('/'): url = url[:-1]
			while url.count('/') > 2: url = url[:url.rfind('/')]
			if '?' in url: url = url[:url.find('?')]
			if '#' in url: url = url[:url.find('#')]
			url = 'http://%s' % url
		self.debug('sanitized url: %s' % url)
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = self.url
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
		self.debug('album type: %s' % self.album_type)
		if  self.album_type == 'direct':
			# Single album
			self.max_images = 5000
			self.download_album_json(self.url)
		elif self.album_type == 'domain':
			self.max_images = 5000
			if self.url.endswith('/all'):
				self.download_account_images(self.url)
			else:
				# Single album
				self.download_album_json(self.url)

		elif self.album_type == 'subreddit':
			# Subreddit
			self.download_subreddit(self.url)
		else:
			# Account-level album
			self.max_images = 5000
			self.download_account(self.url)
		self.wait_for_threads()
	
	def text_to_fs_safe(self, text):
		safe = 'abcdefghijklmnopqrstuvwxyz0123456789-_ &()'
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
			postid = url[url.rfind('/')+1:]
			if '?' in postid: postid = postid[:postid.find('?')]
			if '#' in postid: postid = postid[:postid.find('#')]
			postid = '%03d_%s-' % (index + 1, postid)
			prev_dir = self.working_dir
			self.log('downloading album (%d/%d) - %s' % (index + 1, len(covers), url))
			self.download_album_json(url, postid=postid)
			if self.hit_image_limit(): break

	''' Download imgur album using /noscript method '''
	def download_album(self, album, postid=''):
		# Get album source
		r = self.web.get('%s/noscript' % album)
		# Get images
		links = self.web.between(r, 'img src="//i.', '"')
		for index, link in enumerate(links):
			if '?' in link: link = link[:link.find('?')]
			if '#' in link: link = link[:link.find('#')]
			link = self.get_highest_res('http://i.%s' % link)
			# Download every image
			# Uses superclass threaded download method
			fname = link[link.rfind('/')+1:]
			if '?' in fname: fname = fname[:fname.find('?')]
			if '#' in fname: fname = fname[:fname.find('#')]
			saveas = '%s%03d_%s' % (postid, index + 1, fname)
			self.download_image(link, index + 1, total=len(links), saveas=saveas)
			if self.hit_image_limit(): break
	
	''' Escape text '''
	def safe_text(self, text):
		escaped = []
		for c in text:
			if ord(c) < 32 or ord(c) > 126:
				escaped.append('_')
			else:
				escaped.append(c)
		return ''.join(escaped)
	
	''' Download imgur album using API/json request '''
	def download_album_json(self, album, postid=''):
		aid = album[album.find('/a/')+len('/a/'):]
		if '/' in aid: aid = aid[:aid.find('/')]
		r = self.web.get('http://api.imgur.com/2/album/%s.json' % aid)
		try:
			json = loads(r)
		except:
			self.debug('error parsing json:\n\n%s' % r)
			self.download_album(album)
			return
		if 'error' in json and 'message' in json['error'] and json['error']['message'].lower().count('limit') > 0:
			# Exceeded API limits, use fall-back
			self.debug('hit limit; falling back... %s' % json['error']['message'])
			self.download_album(album)
			return
		if not 'album' in json: return
		alb = json['album']
		if not 'images' in alb: return
		captions = []
		header = ''
		if 'title' in json and json['title'] != None:
			header += 'title: %s\n' % self.safe_text(json['title'])
		if 'description' in json and json['description'] != None:
			header += 'description: %s\n' % self.safe_text(json['description'])
			
		total = len(alb['images'])
		for index, image in enumerate(alb['images']):
			# Image
			url = image['links']['original']
			# Captions / Metadata
			meta = image['image']
			title = self.safe_text(meta.get('title', ''))
			caption = self.safe_text(meta.get('caption', ''))
			if title != '' or caption != '':
				captions.append( (url, title, caption) )
			fname = url[url.rfind('/')+1:]
			if '?' in fname: fname = fname[:fname.find('?')]
			if '#' in fname: fname = fname[:fname.find('#')]
			saveas = '%s%03d_%s' % (postid, index + 1, fname)
			self.download_image(url, index + 1, total=total, saveas=saveas)
			if self.hit_image_limit(): break
		if header != '' or captions != []:
			f = open('%s/%scaptions.txt' % (self.working_dir, postid), 'w')
			if header != '':
				f.write(header)
				f.write('\n')
			for meta in captions:
				f.write('image url: %s\n  title: "%s"\n  caption: "%s"\n\n' % (meta[0], meta[1], meta[2]))
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
			links = self.web.between(r, ' src="//i.', '"')
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
				self.download_image(link, index, total=total) 
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			page += 1
	
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
	
	'''
		Receives an imgur link that is not an album.
		http://i.imgur.com/abcde.jpg
		http://i.imgur.com/abcdeh.jpg
		http://imgur.com/abcde.jpg
		http://imgur.com/abcdeh.jpg
		http://imgur.com/abcde
		http://imgur.com/abcdeh
	'''
	def get_highest_res_and_ext(self, url):
		if not '.' in url[-5:-3]:
			# Need to find extension
			iid = url[url.find('imgur.com/')+len('imgur.com/'):]
			if '/' in iid: iid = iid[:iid.find('/')]
			if '?' in iid: iid = iid[:iid.find('?')]
			if '#' in iid: iid = iid[:iid.find('#')]

			self.debug('[imgur] loading http://api.imgur.com/2/image/%s.json' % iid)
			ir = self.web.get('http://api.imgur.com/2/image/%s.json' % iid)
			try:
				ijs = loads(ir)
				if 'image' in ijs and 'links' in ijs['image'] and 'original' in ijs['image']['links']:
					self.debug('[imgur] response from imgurs api: %s' % ijs['image']['links']['original'])
					return ijs['image']['links']['original']
			except Exception, e:
				self.debug('could not parse imgur response %s\n%s' % (str(e), ir))

			r = self.web.get(url)
			imgs = self.web.between(r, '<img src="//', '"')
			if len(imgs) == 0:
				# Image not found
				raise Exception('image not found')
			url = 'http://%s' % imgs[0]
		
		# URL now contains extension
		return self.get_highest_res(url)
	
	def download_account_images(self, url):
		url = url.replace('/all', '')
		page = total = index = 0
		while True:
			page += 1
			next_page = '%s/ajax/images?sort=0&order=1&album=0&page=%d&perPage=60' % (url, page)
			self.debug('loading %s' % next_page)
			r = self.web.get(next_page)
			try:
				json = loads(r)
				data = json['data']
			except Exception, e:
				# Unable to load json
				self.wait_for_threads()
				raise Exception('unable to load JSON, %s' % str(e))
			if total == 0 and 'count' in data:
				total = data['count']
			for image in data['images']:
				index += 1
				self.download_image('http://i.imgur.com/%s%s' % (image['hash'], image['ext']), index, total=total)
			if index >= total or self.hit_image_limit(): break
		self.wait_for_threads()
