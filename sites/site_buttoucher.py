#!/usr/bin/python

from basesite import basesite

class buttoucher(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'butttoucher.com/' in url:
			raise Exception('')
		if not '/users/' in url:
			raise Exception('required /users/ not found in URL')
		if '#' in url: url = url[:url.find('#')]
		if '?' in url: url = url[:url.find('?')]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		users = url.split('/')
		while users.count('') > 0: users.remove('')
		return 'buttoucher_%s' % users[-1]

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		links = self.web.between(r, 'src="', '"')
		i = 0
		while i < len(links):
			if not 'http://' in links[i]:
				links.pop(i)
			else:
				i += 1
		for index, link in enumerate(links):
			if 'imgur.com' in link:
				try:
					link = self.get_highest_res(link)
				except Exception, e:
					self.log('(%d/%d) unable to download, 404: %s' % (index + 1, len(links), str(e)))
					continue
			self.download_image(link, index + 1, total=len(links))
			if self.hit_image_limit(): break
		self.wait_for_threads()

	""" Returns highest-res image by checking if imgur has higher res """
	def get_highest_res(self, url):
		if not 'm.' in url:
			return url
		temp = url.replace('m.', '.')
		m = self.web.get_meta(temp)
		if 'Content-Length' in m and m['Content-Length'] == '503':
			raise Exception(temp)
		if 'Content-Type' in m and 'image' in m['Content-Type'].lower():
			return temp
		else:
			return url
