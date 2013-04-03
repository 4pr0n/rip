#!/usr/bin/python

from basesite import basesite

"""
	Downloads imagefap albums
"""
class imagefap(basesite):
	"""
		Ensure URL is relevant to this ripper.
		Return 'sanitized' URL (if needed).
	"""
	def sanitize_url(self, url):
		if not 'imagefap.com/' in url: 
			raise Exception('')
		if not 'imagefap.com/pictures/' in url:
			raise Exception("required '/pictures/' not found")
		if '?' in url: url = url[:url.find('?')]
		if not url.endswith('/'): url += '/'
		gids = self.web.between(url, '/pictures/', '/')
		if len(gids) == 0:
			raise Exception("required gallery ID /pictures/X/ not found")
		gid = gids[0]
		return '%s?gid=%s&view=2' % (url, gid)

	""" Discover directory path based on URL """
	def get_dir(self, url):
		gid = self.web.between(url, '/pictures/', '/')[0]
		return 'imagefap_%s' % gid

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		r = r[r.find('showMoreGalleries'):] # To ignore user icon
		links = self.web.between(r, 'x.fap.to/images/thumb/', '"')
		for (index, link) in enumerate(links):
			link = 'http://fap.to/images/full/%s' % link
			self.download_image(link, index + 1, total=len(links))
			if self.hit_image_limit(): break
		self.wait_for_threads()
