#!/usr/bin/python

from basesite import basesite
from os import path, remove

"""
	Downloads getgonewild albums
"""
class getgonewild(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'getgonewild.com/profile/' in url and \
				not 'getgonewild.com/s/' in url:
			raise Exception('')
		while url.endswith('/'): url = url[:-1]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = url[url.rfind('/')+1:]
		return 'getgonewild_%s' % user

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		index = 0
		links = web.between(r, '","url":"', '"')
		for link in links:
			link = link.replace('\\/', '/')
			while link.endswith('/'): link = link[:-1]
			index += 1
			if link[link.rfind('.')+1:].lower() in ['jpg', 'jpeg', 'gif', 'png']:
				self.download_image(link, index, total=len(links)) 
			elif 'imgur.com/a/' in url:
				self.download_imgur_album(link, index, total=len(links))
			elif 'imgur.com' in url:
				self.download_imgur_image(link, index, total=len(links))
		self.wait_for_threads()
	
	def download_imgur_album(self, link, index, total):
		r = self.web.get('%s/noscript' % link)
		alb_index = 1
		images = self.web.between(r, '<a class="zoom" href="', '"')
		for image in images:
			filename = '%s/%03d_%03d_%s' % (self.working_dir, index, alb_index, link[link.rfind('/')+1:])
			self.retry_download(link, filename)

	def download_imgur_image(self, link, index, total):
		r = self.web.get(url)
		links = self.web.between(r, '<meta name="twitter:image" value="', '"')
		if len(links) == 0:
			links = self.web.between(r, '<link rel="image_src" href="', '"')
		if len(links) > 0:
			link = links[0]
			filename = '%s/%03d_%s' % (dir, index, link[link.rfind('/')+1:])
			self.retry_download(link, filename)

	def retry_download(self, url, saveas):
		dot = url.rfind('.')
		if url[dot-1] == 'h':
			tempurl = url[:dot-1] + url[dot:]
			m = self.web.get_meta(tempurl)
			if 'Content-Type' in m and 'image' in m['Content-Type']:
				url = tempurl
		tries = 3
		while tries > 0:
			if self.web.download(url, saveas): 
				if path.getsize(saveas) < 5000:
					f = open(saveas, 'r')
					txt = f.read()
					f.close()
					if 'File not found!' in txt:
						remove(saveas)
				return
			tries -= 1
		remove(saveas)
	
