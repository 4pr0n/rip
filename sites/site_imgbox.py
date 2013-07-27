#!/usr/bin/python

from basesite import basesite
from threading import Thread
from time import sleep
from os import path, sep

class imgbox(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'imgbox.com/' in url:
			raise Exception('')
		if not 'imgbox.com/g/' in url:
			raise Exception('required /g/ not found in URL')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		gid = url[url.find('/g/')+3:]
		if '/' in gid: gid = gid[:gid.find('/')]
		if '?' in gid: gid = gid[:gid.find('?')]
		if '#' in gid: gid = gid[:gid.find('#')]
		return 'imgbox_%s' % gid

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		if not 'id="gallery_view_box">' in r:
			self.wait_for_threads()
			return
		chunk = self.web.between(r, 'id="gallery_view_box">', '</div>')[0]
		imgids = self.web.between(chunk, '<a href="/', '"')
		for index, imgid in enumerate(imgids):
			link = 'http://imgbox.com/%s' % imgid
			self.download_image(link, index + 1, len(imgids))
			if self.hit_image_limit(): break
		self.wait_for_threads()
	
	""" Launches thread to download image """
	def download_image(self, url, index, total):
		while self.thread_count >= self.max_threads:
			sleep(0.1)
		self.thread_count += 1
		args = (url, index, total)
		t = Thread(target=self.download_image_thread, args=args)
		t.start()
	
	""" Download image at imgbox.com/<id> """
	def download_image_thread(self, url, index, total):
		r = self.web.get(url)
		
		if not 'onclick="rs()" src="' in r: 
			self.debug('no onclick="rs()" src=" in r at %s' % url)
			self.thread_count -= 1
			return
		img = self.web.between(r, 'onclick="rs()" src="', '"')[0]
		img = img.replace('&amp;', '&')
		
		if self.urls_only:
			self.add_url(index, img)
			self.thread_count -= 1
			return
		urlid = url[url.rfind('/')+1:]
		if '?' in urlid: urlid = urlid[:urlid.find('?')]
		if '&' in urlid: urlid = urlid[:urlid.find('&')]
		if '#' in urlid: urlid = urlid[:urlid.find('#')]
		extension = img[img.rfind('.')+1:]
		if '?' in extension: extension = extension[:extension.find('?')]
		if '&' in extension: extension = extension[:extension.find('&')]
		if '#' in extension: extension = extension[:extension.find('#')]
		saveas = '%s%s%03d_%s.%s' % (self.working_dir, sep, index, urlid, extension)
		if path.exists(saveas):
			self.image_count += 1
			self.log('file exists: %s' % saveas)
		elif self.web.download(img, saveas):
			self.image_count += 1
			self.log('downloaded (%d/%d) (%s) - %s' % (index, total, self.get_size(saveas), img))
		else:
			self.log('download failed (%d/%d) - %s' % (index, total, img))
		self.thread_count -= 1

