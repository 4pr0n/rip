#!/usr/bin/python

from basesite   import basesite
from site_imgur import imgur

class fapproved(imgur):

	""" Verify [and alter] URL to an acceptable format """
	def sanitize_url(self, url):
		if not 'fapproved.com/' in url:
			raise Exception('')
		if '/users/' not in url and '/images' not in url:
			raise Exception('required /users/ and /images not found in URL')
		if '#' in url: url = url[:url.find('#')]
		if '?' in url: url = url[:url.find('?')]
		
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		fields = url.split('/') # Split url by /
		user = fields[fields.index('users')+1] # Username is after /users/
		return 'fapproved_%s' % user

	""" Download images in album """
	def download(self):
		self.init_dir()
		page  = 0
		total = 0
		index = 0
		while True:
			page += 1
			url = '%s?page=%d' % (self.url, page)
			self.debug('loading %s' % url)
			r = self.web.get(url)
			images = self.web.between(r, '" src="//i.imgur.com', '"')
			if len(images) == 0: break
			total += len(images)
			for image in images:
				index += 1
				image = 'http://i.imgur.com%s' % image
				for c in ['?', '#', '&']:
					if c in image:
						image = image[:image.find(c)]
				self.debug('found image (%d/%d): %s' % (index, total, image))
				image = self.get_highest_res(image)
				meta = self.web.get_meta(image)
				if 'Content-Length' in meta and meta['Content-Length'] == '503':
					# Image is 404'd
					self.log('image is 404: %s' % image)
				else:
					self.download_image(image, index, total=total)
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
		self.wait_for_threads()
