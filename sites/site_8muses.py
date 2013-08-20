#!/usr/bin/python

from basesite import basesite

class eightmuses(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not '8muses.com/' in url:
			raise Exception('')
		if not '/index/' in url:
			raise Exception('required /index/ not found in URL')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		gid = url[url.rfind('/')+1:]
		return '8muses_%s' % gid

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		chunks = self.web.between(r, '<article class="', '</article>')
		if len(chunks) == 0:
			self.wait_for_threads()
			raise Exception('unable to find article class at %s' % self.url)
		chunk = chunks[0]
		links = self.web.between(chunk, '<a href="', '"')
		for index, link in enumerate(links):
			self.download_image(link, index + 1, total=len(links))
			if self.hit_image_limit(): break
		self.wait_for_threads()
	
