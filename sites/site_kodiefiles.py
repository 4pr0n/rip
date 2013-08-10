#!/usr/bin/python

from basesite import basesite

class kodiefiles(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'kodiefiles.nl/' in url:
			raise Exception('')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		if url.endswith('/'): url = url[:-1]
		gid = url[url.rfind('/')+1:]
		return 'kodiefiles_%s' % gid

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		chunks = self.web.between(r, '<div class="gallery-box">', '</div>')
		for index, chunk in enumerate(chunks):
			img = self.web.between(chunk, 'src="', '"')[0]
			img = img.replace('/tn_', '/').replace('/thumbs/', '/full/')
			self.download_image(img, index + 1, total=len(chunks))
			if self.hit_image_limit(): break
		self.wait_for_threads()
