#!/usr/bin/python

from basesite import basesite

class soupio(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'redditsluts.soup.io/' in url:
			raise Exception('')
		if not '/tag/' in url:
			raise Exception('required /tag/ not found in URL')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		tag = url[url.find('/tag/')+5:]
		if '/' in tag: tag = tag[:tag.find('/')]
		if '?' in tag: tag = tag[:tag.find('?')]
		if '#' in tag: tag = tag[:tag.find('#')]
		return 'soupio_%s' % tag

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		chunks = self.web.between(r, '<div class="imagecontainer"', '</div>')
		for index, chunk in enumerate(chunks):
			if '<a href="' in chunk:
				url = self.web.between(chunk, '<a href="', '"')[0]
			elif ' src="' in chunk:
				url = self.web.between(chunk, ' src="', '"')[0]
			else:
				continue
			if self.urls_only:
				self.add_url(index + 1, url, total=len(chunks))
			else:
				self.download_image(url, index + 1, total=len(chunks))
			if self.hit_image_limit(): break
		self.wait_for_threads()
