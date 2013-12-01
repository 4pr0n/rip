#!/usr/bin/python

from basesite import basesite

class vidble(basesite):
	""" Verify [and alter] URL to an acceptable format """
	def sanitize_url(self, url):
		if not 'vidble.com/' in url:
			raise Exception('')
		if not '/album/' in url:
			raise Exception('required /album/ not found in URL')
		if '#' in url: url = url[:url.find('#')]
		if '?' in url: url = url[:url.find('?')]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		url = url[url.find('/album/')+len('/album/'):]
		if '/' in url: url = url[:url.find('/')]
		if '#' in url: url = url[:url.find('#')]
		if '?' in url: url = url[:url.find('?')]
		return 'vidble_%s' % url

	""" Download images in album """
	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		links = self.web.between(r, "</a><img src='", "'")
		for index, link in enumerate(links):
			link = 'http://www.vidble.com%s' % link.replace('_med.', '.')
			self.download_image(link, index + 1, total=len(links))
			if self.hit_image_limit(): break
		self.wait_for_threads()
