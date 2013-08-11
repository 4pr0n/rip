#!/usr/bin/python

from basesite  import basesite
from threading import Thread
from time      import sleep
import os

class pbase(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'pbase.com/' in url:
			raise Exception('')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		if url.endswith('/'): url = url[:-1]
		gid = url[url.rfind('/')+1:]
		return 'pbase_%s' % gid

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		links = self.web.between(r, 'class="thumbnail"><A HREF="', '"')
		for index, link in enumerate(links):
			link = '%s/original' % link
			while self.thread_count > self.max_threads:
				sleep(0.1)
			t = Thread(target=self.download_image, args=(link, index + 1, len(links)))
			t.start()
			if self.hit_image_limit(): break
		self.wait_for_threads()
	
	def download_image(self, url, index, total):
		self.thread_count += 1
		r = self.web.get(url)
		if not '<IMG class="display" src="' in r:
			self.debug('could not find image at %s' % url)
		else:
			image = self.web.between(r, '<IMG class="display" src="', '"')[0]
			if self.urls_only:
				self.add_url(index, image, total=total)
			else:
				filename = image[image.rfind('/')+1:]
				save_as = '%s%s%03d_%s' % (self.working_dir, os.sep, index, filename)
				if os.path.exists(save_as):
					self.image_count += 1
					self.log('file exists: %s' % save_as)
				elif self.web.download(image, save_as):
					self.image_count += 1
					self.log('downloaded (%d/%d) (%s) - %s' % (index, total, self.get_size(save_as), image))
				else:
					self.log('download failed (%d/%d) - %s' % (index, total, image))
		
		self.thread_count -= 1

