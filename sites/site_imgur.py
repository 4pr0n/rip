#!/usr/bin/python

from basesite import basesite
from os import path, mkdir

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
		self.album_type = None 
		if not 'imgur.com' in url: 
			raise Exception('')
		if      '.imgur.com'    in url and \
				not 'i.imgur.com'   in url and \
				not 'www.imgur.com' in url:
			# Domain-level
			url = url.replace('http://', '').replace('https://', '')
			while url.endswith('/'): url = url[:-1]
			urls = url.split('/')
			url = '/'.join(urls[0:1]) # Only the domain & first subdir
			return 'http://%s' % url
		elif not '/a/' in url:
			raise Exception("Not a valid imgur album")
		url = url.replace('http://', '').replace('https://', '')
		while url.count('/') > 2: url = url[:url.rfind('/')]
		return 'http://%s' % url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = self.url
		u = u.replace('/all', '')
		if '/a/' in u:
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
		if  self.album_type == 'direct' or \
				self.album_type == 'domain':
			# Single album
			self.download_album(self.url)
			return
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
		print album
		r = self.web.get(album)
		covers = self.web.between(r, '<div class="cover">', '</div>')
		for index, cover in enumerate(covers):
			url = self.web.between(cover, '<a href="', '"')[0]
			url = 'http:%s' % url
			alt = self.web.between(cover, 'alt="', '"')[0]
			if alt == '': alt = 'untitled'
			alt = self.text_to_fs_safe(alt)
			prev_dir = self.working_dir
			self.working_dir += '/%03d_%s' % (index + 1, alt)
			if not path.exists(self.working_dir):
				mkdir(self.working_dir)
			self.log('Downloading album (%d/%d) "%s"' % (index + 1, len(covers), alt))
			self.download_album(url)
			self.working_dir = prev_dir

	def download_album(self, album):
		# Get album source
		r = self.web.get('%s/noscript' % album)
		# Get images
		links = self.web.between(r, 'img src="http://i.', '"')
		for index, link in enumerate(links):
			link = self.get_highest_res('http://i.%s' % link)
			# Download every image
			# Uses superclass threaded download method
			self.download_image(link, index, total=len(links)) 
		self.wait_for_threads()
	
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
		
