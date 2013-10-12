#!/usr/bin/python

from basesite import basesite

class cghub(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'cghub.com/' in url:
			raise Exception('')
		url = url.replace('http://', '').replace('https://', '')
		user = url[:url.find('.')]
		if user in ['cghub', 'www', '']:
			raise Exception('required &lt;username&gt;.cghub.com not found in URL')
		return 'http://%s.cghub.com/images/' % user

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = self.web.between(url, '://', '.')[0]
		return 'cghub_%s' % user

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		index = 0
		total = 0
		while True:
			chunks = self.web.between(r, '<a name="', '</li>')
			total += len(chunks)
			for chunk in chunks:
				if not '<img src="' in chunk: continue
				img = self.web.between(chunk, '<img src="', '"')[0]
				img = 'http:' + img.replace('_stream', '_max')
				index += 1
				self.download_image(img, index, total=total)
			if '<li class="next"><a href="' in r:
				nextpage = self.web.between(r, '<li class="next"><a href="', '"')[0]
				r = self.web.get(nextpage)
			else:
				break
		self.wait_for_threads()

