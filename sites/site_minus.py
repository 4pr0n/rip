#!/usr/bin/python

from basesite import basesite

class minus(basesite):
	
	# http://minus.com/mdRxu5e95V6ZA
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'minus.com' in url:
			raise Exception('')
		if '/i.minus.com' in url or \
				'/.minus.com' in url:
			raise Exception('required <b>http://&lt;user&gt;.minus.com/</b> not found in URL')
		if not '.minus.com' in url or 'www.minus.com' in url:
			temp = url.replace('http://', '').replace('https://', '')
			if temp.endswith('/'): temp = temp[:-1]
			if not '/' in temp or '/' in temp[temp.find('/')+1:]:
				raise Exception('invalid minus url')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		url = url.replace('http://', '').replace('https://', '')
		if '.minus.com' in url:
			# Account upload
			url = url.replace('.minus.com', '').replace('/uploads', '')
			while url.endswith('/'): url = url[:-1]
			dirs = url.split('/')
			if '' in dirs: dirs.remove('')
			return 'minus_%s' % '_'.join(dirs)
		else:
			# Guest upload
			while url.endswith('/'): url = url[:-1]
			url = url[url.find('/')+1:]
			return 'minus_guest_%s' % url
			
	
	def download(self):
		# Check URL, download all albums or just the URL
		self.init_dir()
		d = self.working_dir
		dirs = d.split('_')[1:] # d[d.find('minus_')+len('minus_'):].split('_')
		self.debug('dirs: %s' % str(dirs))
		if len(dirs) == 1:
			# Account
			self.debug('account')
			user = dirs[0]
			# Albums
			url = 'http://%s.minus.com/uploads' % user
			r = self.web.get(url)
			albumids = self.web.between(r, '"reader_id": "', '"')
			for index, albumid in enumerate(albumids):
				suburl = 'http://%s.minus.com/m%s' % (user, albumid)
				prev_dir = self.working_dir
				self.working_dir += '/%03d_%s' % (index + 1, albumid)
				self.download_album(suburl)
				self.wait_for_threads()
				self.working_dir = prev_dir
			'''
			# photos
			url = 'http://%s.minus.com/' % user
			r = self.web.get(url)
			imageids = self.web.between(r, '<img src="', '"')
			i = 0
			while i < len(imageids):
				if not 'minus.com' in imageids[i] or imageids[i].count('/') > 3:
					imageids.pop(i)
				else:
					i += 1
			for index, imageid in enumerate(imageids):
				url = 'http://i%s' % imageid[imageid.find('.'):]
				url = url[:url.find('_')] + url[url.rfind('.'):]
				self.download_image(url, index + 1, total=len(imageids))
			'''
			
		elif dirs[0] == 'guest':
			# Guest
			self.debug('guest')
			url = 'http://minus.com/%s' % (dirs[1])
			self.download_album(url)
		elif len(dirs) == 2:
			# Account album
			self.debug('account album')
			url = 'http://%s.minus.com/%s' % (dirs[0], dirs[1])
			self.download_album(url)
		else:
			raise Exception('invalid minus URL')
		self.wait_for_threads()

	def download_album(self, url):
		albumid = url[url.rfind('/')+1:]
		r = self.web.get(url)
		if not '"items": [' in r:
			self.debug('no "items" in r at %s' % url)
			self.wait_for_threads()
			raise Exception('could not find items in minus album - %s' % url)
		json = self.web.between(r, '"items": [', '};')[0]
		chunks = self.web.between(json, '{', '}')
		for index, chunk in enumerate(chunks):
			if not '"id": "' in chunk or not '"name": "' in chunk: 
				self.debug('no "id" or "name" in chunk')
				continue
			image = self.web.between(chunk, '"id": "',   '"')[0]
			name  = self.web.between(chunk, '"name": "', '"')[0]
			if '.' in name:
				ext = name[name.rfind('.'):]
			else:
				ext = '.jpg'
			link = 'http://i.minus.com/i%s%s' % (image, ext)
			if self.urls_only:
				self.add_url(index + 1, link, total=len(chunks))
			else:
				self.download_image(link, index + 1, total=len(chunks))
				if self.hit_image_limit(): break
		self.wait_for_threads()
	

