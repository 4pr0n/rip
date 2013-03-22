#!/usr/bin/python

from basesite import basesite
from time import sleep

class gifyo(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'gifyo.com/' in url:
			raise Exception('')
		while url.endswith('/'): url = url[:-1]
		user = url[url.find('gifyo.com/')+len('gifyo.com/'):]
		if '/' in user:
			user = user.split('/')[0]
		return 'http://gifyo.com/%s/' % user

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = url.split('/')[-2]
		return 'gifyo_%s' % user

	def download(self):
		self.init_dir()
		page = 0
		total_pics   = 0
		current_pics = 0
		already_got = []
		while True:
			if total_pics == 0:
				r = self.web.get(self.url)
			else:
				postdict = {
					'cmd'    : 'refreshData', 
					'view'   : 'gif', 
					'layout' : 'grid',
					'page'   : '%s' % page
				}
				r = self.web.post(self.url, postdict=postdict)
			links = self.web.between(r, "onmouseover='this.src=\"", '"')
			if len(links) == 0: break
			total_pics += len(links)
			for link in links:
				if '/avatars/' in link: 
					total_pics -= 1
					continue
				link = link.replace('_s.gif', '.gif')
				if '/medium/' in link or '/small/' in link:
					templink = link.replace('/medium/', '/large/').replace('/small/', '/large/')
					m = self.web.get_meta(templink)
					if 'Content-Length' in m and m['Content-Length'] != '85':
						link = templink
				if link in already_got: 
					total_pics -= 1
					continue
				current_pics += 1
				already_got.append(link)
				self.download_image(link, current_pics, total=total_pics)
				if self.hit_image_limit(): break
			sleep(1)
			page += 1
		self.wait_for_threads()

