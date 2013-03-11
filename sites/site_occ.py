#!/usr/bin/python

from basesite import basesite

""" OneClickChicks """
class occ(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		# http://forum.oneclickchicks.com/showthread.php?t=137808
		if not 'oneclickchicks.com/' in url:
			raise Exception('')
		if not 'showthread.php?' in url:
			raise Exception('required showthread.php not found in URL')
		if not 't=' in url:
			raise Exception('required t= not found in URL')
		if '&page=' in url: url = url[:url.find('&page=')]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		url += '&'
		gid = self.web.between(url, 't=', '&')[0]
		return 'oneclickchicks_%s' % (gid)

	def login(self):
		d = {}
		d['vb_login_username'] = '1fakeyfake'
		d['vb_login_password'] = 'fakers'
		d['do'] = 'login'
		r = self.web.post('http://forum.oneclickchicks.com/login.php?do=login', postdict=d)
		if not 'redirecting' in r.lower():
			raise Exception('could not log in to oneclickchicks')

	def download(self):
		self.init_dir()
		self.login()
		r = self.web.get(self.url)
		page  = 1
		index = 0
		total = 0
		while True:
			links = self.web.between(r, '<a href="attachment.php?', '"')
			total += len(links)
			for link in links:
				link = 'http://forum.oneclickchicks.com/attachment.php?%s' % link.replace('&amp;', '&')
				saveas = self.web.between(link, 'id=', '&')[0]
				index += 1
				self.download_image(link, index, total=total, saveas=saveas)
				if self.hit_image_limit(): break
			page += 1
			if '&amp;page=%d' % page in r:
				r = self.web.get('%s&page=%d' % (self.url, page))
			else: break
		self.wait_for_threads()

