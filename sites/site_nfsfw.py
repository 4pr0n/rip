#!/usr/bin/python

from basesite import basesite
from time import sleep
from threading import Thread
from os import path

class nfsfw(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'nfsfw.com/' in url:
			raise Exception('')
		if not '/gallery/v/' in url:
			raise Exception('required /gallery/v/ not found in URL')
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		while url.endswith('/'): url = url[:-1]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = url
		g = u[u.rfind('/')+1:]
		g = g.replace('+', '').replace('%20', '').replace(' ', '')
		return 'nfsfw_%s' % g

	def download(self):
		self.init_dir()
		index = 0
		page = 1
		total = '?'
		while True:
			url = '%s/?g2_page=%d' % (self.url, page)
			self.debug('url = %s' % url)
			r = self.web.get(url)
			if total == '?' and 'Size: ' in r:
				total = int(self.web.between(r, 'Size: ', ' ')[0])
			imgs = self.web.between(r, 'img src="/gallery/d/', '"')
			for img in imgs:
				fs = img.split('-')
				f1 = int(fs[0]) + 1
				img = '%d-%s' % (f1, fs[1])
				img = 'http://nfsfw.com/gallery/d/%d-%s' % (f1, fs[1])
				index += 1
				self.download_image(img, index, total=total)
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			page += 1
			if 'g2_page=%d' % page not in r: break

		self.wait_for_threads()
