#!/usr/bin/python

from basesite import basesite

"""
	Downloads imgur albums
"""
class imgur(basesite):
	
	"""
		Only supports direct links to albums
		Does not support domain-level albums
		such as 'http://username.imgur.com/album_name'
	"""
	def sanitize_url(self, url):
		if not 'imgur.com' in url: 
			raise Exception('')
		if      '.imgur.com'    in url and \
				not 'i.imgur.com'   in url and \
				not 'www.imgur.com' in url:
			# Domain-level
			raise Exception("Direct link to album required")
		elif not '/a/' in url:
			raise Exception("Not a valid imgur album")
		url = url.replace('http://', '').replace('https://', '')
		while url.count('/') > 2:
			url = url[:url.rfind('/')]
		return 'http://%s' % url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = self.url
		aid = u[u.find('/a/')+len('/a/'):]
		if '/' in aid: aid = aid[:aid.find('/')]
		return 'imgur_%s' % aid

	def download(self):
		# Get album source
		r = self.web.get('%s/noscript' % self.url)
		# Get images
		links = self.web.between(r, 'img src="http://i.', '"')
		for index, link in enumerate(links):
			link = self.get_highest_res('http://i.%s' % link)
			# Download every image
			# Uses superclass threaded download method
			self.download_image(link, index, total=len(links)) 
		self.wait_for_threads()
	
	""" Returns highest-res image by checking if imgur has higher res """
	def get_highest_res(self, url):
		if not 'h.' in url:
			return url
		temp = temp.replace('h.', '')
		m = self.web.get_meta(temp)
		if 'Content-Type' in m and 'image' in m['Content-Type'].lower():
			return temp
		else:
			return url
		
