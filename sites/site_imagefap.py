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
		gid = self.get_gid(url)
		if gid == '':
			raise Exception('?gid= and /pictures/ not found in URL')
		return 'http://www.imagefap.com/gallery.php?gid=%s&view=2' % gid

	""" Extract gallery id from URL. Return empty string if not found """
	def get_gid(self, url):
		gid = ''
		for before in ['?gid=', '/pictures/']:
			if before in url:
				gid = url[url.rfind(before)+len(before):]
		for c in ['/', '?', '#', '&']:
			if c in gid: gid = gid[:gid.find(c)]
		return gid

	""" Discover directory path based on URL """
	def get_dir(self, url):
		return 'imagefap_%s' % self.get_gid(url)

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		r = r[r.find('showMoreGalleries'):] # To ignore user icon
		links = self.web.between(r, 'x.fap.to/images/thumb/', '"')
		for (index, link) in enumerate(links):
			link = 'http://fap.to/images/full/%s' % link
			if self.urls_only:
				self.add_url(index + 1, link, total=len(links))
			else:
				self.download_image(link, index + 1, total=len(links))
				if self.hit_image_limit(): break
		self.wait_for_threads()
