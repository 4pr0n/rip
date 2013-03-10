#!/usr/bin/python

from basesite import basesite

class anonib(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'anonib.com/' in url:
			raise Exception('')
		if not '/res/' in url:
			raise Exception('required /res/ not found in URL')
		dirs = url.replace('http://', '').replace('https://', '').split('/')
		if len(dirs) != 4 or dirs[2] != 'res':
			raise Exception('required format: anonib.com/<board>/res/#')
		number = dirs[3]
		if '+' in number:
			number = number[:number.find('+')] + number[number.rfind('.'):]
		return 'http://%s/%s' % ('/'.join(dirs[:2]), number)

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = url.replace('http://', '')
		dirs = u.split('/')
		board = dirs[1]
		number = dirs[3][:dirs[3].find('.')]
		return 'anonib_%s_%s' % (board, number)

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		links = self.web.between(r, '/img.php?path=', '"')
		for index, link in enumerate(links):
			self.download_image(link, index + 1, total=len(links))
			if self.hit_image_limit(): break
		self.wait_for_threads()
