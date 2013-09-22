#!/usr/bin/python

from basesite  import basesite
from threading import Thread
from time      import sleep
from os        import path, remove

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
		self.debug('response size from %s: %d' % (self.url, len(r)))
		index = 0
		links = self.web.between(r, '","url":"', '"')
		for link in links:
			link = link.replace('\\\\', '\\')
			link = link.replace('\\/', '/')
			self.debug('found link: %s' % link)
			if '?' in link: link = link[:link.find('?')]
			while link.endswith('/'): link = link[:-1]
			index += 1
			# Direct link to image
			if link[link.rfind('.')+1:].lower() in ['jpg', 'jpeg', 'gif', 'png']:
				if self.urls_only:
					self.add_url(index, link, total=len(links))
				else:
					self.download_image(link, index, total=len(links)) 
			# Imgur album
			elif 'imgur.com/a/' in link:
				while self.thread_count > self.max_threads: sleep(0.1)
				self.thread_count += 1
				args = (link, index, len(links))
				t = Thread(target=self.download_imgur_album, args=args)
				t.start()
			# Imgur image
			elif 'imgur.com' in link:
				while self.thread_count > self.max_threads: sleep(0.1)
				self.thread_count += 1
				args = (link, index, len(links))
				t = Thread(target=self.download_imgur_image, args=args)
				t.start()
			else:
				self.debug('not sure how to handle this link: %s' % link)
			if self.hit_image_limit(): break
		self.wait_for_threads()
	
	def download_imgur_album(self, link, index, total):
		if '#' in link: link = link[:link.find('#')]
		if '?' in link: link = link[:link.find('?')]
		while link.endswith('/'): link = link[:-1]
		dirs = link.replace('http://', '').split('/')
		if len(dirs) > 3:
			link = 'http://%s' % '/'.join(dirs[0:3])
		r = self.web.get('%s/noscript' % link)
		alb_index = 0
		images = self.web.between(r, 'img src="http://i.', '"')
		if len(images) == 0:
			self.log('failed (%d/%d): album not found - %s' % (index, total, link))
		else: 
			for image in images:
				alb_index += 1
				image = 'http://i.%s' % image
				image = self.get_highest_res(image)
				if self.urls_only:
					self.add_url(index, image, total=total)
					self.thread_count -= 1
					return
				filename = image[image.rfind('/')+1:]
				if '?' in filename: filename = filename[:filename.find('?')]
				if '#' in filename: filename = filename[:filename.find('#')]
				if ':' in filename: filename = filename[:filename.find(':')]
				filename = '%s/%03d_%03d_%s' % (self.working_dir, index, alb_index, filename)
				self.retry_download(image, filename)
				self.log('downloaded (%d/%d) #%d (%s) - %s' % (index, total, alb_index, self.get_size(filename), image))
		self.thread_count -= 1
	
	""" Returns highest-res image by checking if imgur has higher res """
	def get_highest_res(self, url):
		if not 'h.' in url:
			return url
		temp = url.replace('h.', '.')
		m = self.web.get_meta(temp)
		if 'Content-Type' in m and \
				'image' in m['Content-Type'].lower() and \
				'Content-Length' in m and \
				m['Content-Length'] != '503':
			return temp
		else:
			return url

	def download_imgur_image(self, link, index, total):
		r = self.web.get(link)
		links = self.web.between(r, '<meta name="twitter:image" value="', '"')
		if len(links) == 0:
			links = self.web.between(r, '<link rel="image_src" href="', '"')
		if len(links) > 0:
			image = links[0]
			if self.urls_only:
				self.add_url(index, link, total=total)
				self.thread_count -= 1
				return
			filename = image[image.rfind('/')+1:]
			if '?' in filename: filename = filename[:filename.find('?')]
			if '#' in filename: filename = filename[:filename.find('#')]
			if ':' in filename: filename = filename[:filename.find(':')]
			filename = '%s/%03d_%s' % (self.working_dir, index, filename)
			self.retry_download(image, filename)
			self.log('downloaded (%d/%d) (%s) - %s' % (index, total, self.get_size(filename), image))
		self.thread_count -= 1

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
						self.log('file not found: %s' % url)
						remove(saveas)
						return False
				self.image_count += 1
				self.create_thumb(saveas)
				return True
			tries -= 1
		remove(saveas)
		return False
	
