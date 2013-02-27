#!/usr/bin/python

from basesite import basesite

"""
	Downloads xhamster albums
"""
class xhamster(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'xhamster.com' in url:
			raise Exception('')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		return 'xhamster_%s' % aid

	def download(self):
		r = self.web.get(self.url)
		links = self.web.between(r, 'img src="http://i.', '"')
		for index, link in enumerate(links):
			link = 'http://%s' % link
			self.download_image(link, index, total=len(links)) 
		self.wait_for_threads()
	
