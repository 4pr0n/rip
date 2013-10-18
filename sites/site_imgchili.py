#!/usr/bin/python

# 'basesite.py' contains lots of functionality required for a ripper
from basesite import basesite

class imgchili(basesite):
	
	def sanitize_url(self, url):
		if not 'imgchili.com/' in url and \
		   not 'imgchili.net/' in url:
			raise Exception('')
		if not '/album/' in url:
			raise Exception('required /album/ not found in URL')
		if '#' in url: url = url[:url.find('#')]
		if '?' in url: url = url[:url.find('?')]
		fields = url.replace('http://', '').replace('https://', '').split('/')
		while fields[-2] != 'album': fields.pop(-1)
		return url

	def get_dir(self, url):
		return 'imgchili_%s' % url[url.rfind('/')+1:]

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		links = self.web.between(r, '"><img src="', '"')
		while './theme/images/blank.gif' in links: links.remove('./theme/images/blank.gif')
		for index, link in enumerate(links):
			link = link.replace('http://t', 'http://i')
			self.download_image(link, index + 1, total=len(links))
			if self.hit_image_limit(): break
		self.wait_for_threads()
