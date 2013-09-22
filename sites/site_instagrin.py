#!/usr/bin/python

from basesite import basesite
from time import sleep

"""
	Downloads instagram albums
"""
class instagram(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if'instagram.com/' in url:
			# Legit
			pass
		elif 'web.stagram.com/n/' in url:
			# Convert to instagram
			user = url[url.find('.com/n/')+len('.com/n/'):]
			if '/' in user: user = user[:user.find('/')]
			url = 'http://instagram.com/%s' % user
		else:
			raise Exception('')
		url = url.replace('instagram.com/', 'instagr.in/u/')
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		while url.endswith('/'): url = url[:-1]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = url[url.rfind('/')+1:]
		return 'instagram_%s' % user

	def download(self):
		self.init_dir()
		url = self.url
		index = 0
		r = self.web.get(url)
		if not '"pod-title">Photos' in r:
			self.wait_for_threads()
			raise Exception('could not find total photos at %s' % url)
		chunk = self.web.between(r, '"pod-title">Photos</div>', 'Followers')[0]
		total = int(self.web.between(chunk, 'value">', '<')[0])
		while True:
			if not '<div class="image">' in r:
				self.log('could not find image at %s' % url)
				break
			links = self.web.between(r, '<div class="image">', '</div>')
			for link in links:
				index += 1
				media_url = self.web.between(link, 'src="', '"')[0]
				media_url = media_url.replace('_102.mp4', '_101.mp4')
				media_url = media_url.replace('_6.jpg',   '_7.jpg')
				if self.urls_only:
					self.add_url(index, media_url, total=total)
				else:
					self.download_image(media_url, index, total=total)
					sleep(0.2)
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			if not '<div class="next_url">' in r: break
			next_url = self.web.between(r, '<div class="next_url">', '</div>')[0]
			if next_url.strip() == '' or index >= total: break
			d = {
					'next_url' : next_url,
					'request'  : next_url
				}
			headers = {
					'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8',
					'X-Requested-With' : 'XMLHttpReqeust',
					'Referer' : self.url,
					'Accept' : '*/*',
					'Accept-Language' : 'en-US,en;q=0.5',
					'DNT' : '1'
				}

			url = 'http://instagr.in/action/load-more'
			r = self.web.oldpost(url, postdict=d)
			sleep(1)
		self.wait_for_threads()
	
