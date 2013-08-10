#!/usr/bin/python

from basesite import basesite

class testsite(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'testsite.com/' in url:
			raise Exception('')
		if not '/something/' in url:
			raise Exception('required /something/ not found in URL')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		gid = url[url.rfind('/')+1:]
		return 'testsite_%s' % gid

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		links = self.web.between(r, '<a href="', '"')
		for index, link in enumerate(links):
			self.download_image(link, index + 1, total=len(links))
			if self.hit_image_limit(): break
		self.wait_for_threads()
