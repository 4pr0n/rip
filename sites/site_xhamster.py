#!/usr/bin/python

from basesite import basesite

"""
	Downloads xhamster albums
"""
class xhamster(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'xhamster.com/' in url:
			raise Exception('')
		if not 'xhamster.com/photos/gallery/' in url:
			raise Exception('Required /photos/gallery/ not found in %s' % url)
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		if '.html' in url and url[url.find('.html')-2] == '-':
			i = url.find('.html')
			url = url[:i-2] + url[i:]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		aid = url.split('/')[-2]
		return 'xhamster_%s' % aid

	def download(self):
		self.init_dir()
		page = 1
		r = self.web.get(self.url)
		while True:
			chunks = self.web.between(r, "class='slideTool'", 'Related Galleries')
			if len(chunks) == 0: break
			links = self.web.between(chunks[0], "' src='", "'")
			for index, link in enumerate(links):
				link = link.replace('_160.', '_1000.').replace('http://p2.', 'http://up.')
				self.download_image(link, index + 1, total=len(links)) 
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			page += 1
			next_page = self.url.replace('.html', '-%d.html' % page)
			if next_page in r:
				r = self.web.get(next_page)
			else: break
		self.wait_for_threads()
	
