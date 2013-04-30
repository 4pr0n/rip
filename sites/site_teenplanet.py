#!/usr/bin/python

from basesite import basesite
from threading import Thread
import time, os

class teenplanet(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'teenplanet.org/' in url:
			raise Exception('')
		url = url.replace('http://', '')
		splits = url.split('/')
		if splits[-1].startswith('page'): splits.pop(-1)
		if len(splits) != 4:
			raise Exception('expected teenplanet.org/user/folder/set format not found')
		return 'http://%s' % '/'.join(splits)

	""" Discover directory path based on URL """
	def get_dir(self, url):
		splits = url.replace('http://', '').split('/')
		return 'teenplanet_%s' % '_'.join(splits[-2:])

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		index = 0
		total = 0
		page  = 1
		while True:
			chunk = self.web.between(r, "<div id='thumbnails'>", '<div id="description">')[0]
			links = self.web.between(chunk, '<a href="', '"')
			total += len(links)
			for link in links:
				img = 'http://photos.teenplanet.org%s' % link.replace(' ', '%20')
				index += 1
				self.download_image(img, index, total=total)
			page += 1
			if '/page%d">' % page in r:
				r = self.web.get('%s/page%d' % (self.url, page))
			else:
				break
		self.wait_for_threads()

	""" Launches thread to download image """
	def download_image(self, url, index, total):
		while self.thread_count >= self.max_threads:
			time.sleep(0.1)
		self.thread_count += 1
		args = (url, index, total)
		t = Thread(target=self.download_image_thread, args=args)
		t.start()
	
	""" Downloads image from deviantart image page """
	def download_image_thread(self, url, index, total):
		r = self.web.get(url)
		if not '<img id="thepic" src="' in r:
			self.thread_count -= 1
			return
		img = 'http://photos.teenplanet.org%s' % self.web.between(r, '<img id="thepic" src="', '"')[0]
		img = img.replace(' ', '%20')
		if self.urls_only:
			self.add_url(index, img, total=total)
			self.thread_count -= 1
			return
		filename = img[img.rfind('/')+1:]
		saveas = '%s%s%03d_%s' % (self.working_dir, os.sep, index, filename)
		if os.path.exists(saveas):
			self.image_count += 1
			self.log('file exists: %s' % saveas)
		elif self.web.download(img, saveas):
			self.image_count += 1
			self.log('downloaded (%d/%d) (%s) - %s' % (index, total, self.get_size(saveas), img))
		else:
			self.log('download failed (%d/%d) - %s' % (index, total, img))
		self.thread_count -= 1

