#!/usr/bin/python

from basesite import basesite

"""
	Downloads instagram albums
"""
class instagram(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'web.stagram.com/n/' in url:
			raise Exception('')
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = url[url.find('.com/n/')+len('.com/n/'):]
		if '/' in user: user = user[:user.find('/')]
		return 'instagram_%s' % user

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		totals = self.web.between(r, 'font-size:123.1%;">', '<')
		if len(totals) > 0: total = int(totals[1])
		else: total = -1
		index = 0
		while True:
			chunks = self.web.between(r, '<div class="infolist">', '</div>')
			for chunk in chunks:
				imgs = self.web.between(chunk, '<a href="', '"')
				if len(imgs) < 4: continue
				img = imgs[3].replace('_6.', '_7.')
				
				index += 1
				if self.urls_only:
					self.add_url(index, img, total=total)
				else:
					self.download_image(img, index, total=total) 
					if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			earliers = self.web.between(r, ' [ <a href="/n/', '"')
			if len(earliers) != 2: break
			r = self.web.get('http://web.stagram.com/n/%s' % earliers[0])
		self.wait_for_threads()
	
