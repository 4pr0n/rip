#!/usr/bin/python

from basesite import basesite

"""
	Downloads twitter albums
"""
class twitter(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'twitter.com' in url:
			raise Exception('')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		return 'twitter_%s' % aid

	def download(self):
		r = self.web.get('%s' % self.url)
		# Get images
		links = self.web.between(r, 'img src="http://i.', '"')
		for index, link in enumerate(links):
			link = self.get_highest_res('http://%s' % link)
			# Download every image
			# Uses superclass threaded download method
			self.download_image(link, index, total=len(links)) 
		self.wait_for_threads()
	
