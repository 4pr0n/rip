#!/usr/bin/python

from basesite import basesite

"""
	Downloads instagram albums
"""
class instagram(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if'web.stagram.com/n/' in url:
			# Legit
			pass
		elif 'instagram.com/' in url:
			# Convert to web.stagram
			user = url[url.find('.com/')+len('.com/'):]
			if '/' in user: user = user[:user.find('/')]
			url = 'http://web.stagram.com/n/%s' % user
		else:
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
			chunks = self.web.between(r, '<div class="infolist">', '<div class="like_comment')
			for chunk in chunks:
				imgs = self.web.between(chunk, '<a href="', '"')
				if len(imgs) < 4: continue
				img = imgs[3].replace('_6.', '_7.')
				self.debug('found img: %s' % img)
				if '<div class="hasvideo' in chunk:
					vid = img.replace('_7.jpg', '_101.mp4')
					self.debug('video found, url: %s' % vid)
					meta = self.web.get_meta(vid)
					if 'Content-Length' in meta and meta['Content-Length'] != '0' and \
						'Content-Type' in meta and 'video' in meta['Content-Type']:
						self.debug('meta shows vid is legit')
						img = vid
					else:
						self.debug('meta shows vid is not legit')
				
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
	
