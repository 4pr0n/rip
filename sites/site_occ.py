#!/usr/bin/python

from basesite import basesite

""" OneClickChicks """
class occ(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		# http://forum.oneclickchicks.com/showthread.php?t=137808
		if not 'oneclickchicks.com/' in url:
			raise Exception('')
		if 'showthread.php?' not in url and 't=' not in url and \
				'album.php?' not in url and 'albumid=' not in url:
			raise Exception('required showthread or albumid not found in URL')
		if '&page=' in url: url = url[:url.find('&page=')]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		url += '&'
		if 't=' in url:
			gid = self.web.between(url, 't=', '&')[0]
		elif 'albumid=' in url:
			gid = self.web.between(url, 'albumid=', '&')[0]
		return 'oneclickchicks_%s' % (gid)

	def login(self):
		f = open('occ.key', 'r')
		lines = f.read().split('\n')
		f.close()
		d = {}
		d['vb_login_username'] = lines[0]
		d['vb_login_password'] = lines[1]
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
			for threadalbum in ['attachment', 'album']:
				links = self.web.between(r, '<a href="' + threadalbum + '.php?', '"')
				total += len(links)
				for link_index, link in enumerate(links):
					if threadalbum == 'album':
						if link_index == 0: 
							total -= 1
							continue
						threadalbum = 'picture'
					link = 'http://forum.oneclickchicks.com/' + threadalbum + '.php?%s' % link.replace('&amp;', '&')
					saveas = self.web.between(link, 'id=', '&')[-1]
					index += 1
					self.download_image(link, index, total=total, saveas=saveas)
					if self.hit_image_limit(): break
			page += 1
			if '&amp;page=%d' % page in r:
				r = self.web.get('%s&page=%d' % (self.url, page))
			else: break
		self.wait_for_threads()

