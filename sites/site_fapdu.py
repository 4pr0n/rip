#!/usr/bin/python

from basesite import basesite
from time import sleep
from threading import Thread
import os

class fapdu(basesite):
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'fapdu.com/' in url:
			raise Exception('')
		if '.view/' in url:
			url = url[:url.find('.view/')+len('.view/')]
		elif '.pics' in url:
			url = url[:url.find('.pics')+len('.pics')]
		else:
			raise Exception('<b>.view/</b> and <b>.pics</b> not found in URL')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		fields = url.replace('http://', '').split('/')
		album = fields[1].replace('.view', '').replace('.pics', '')
		return 'fapdu_%s' % album

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		if self.url.endswith('.view/'):
			if not 'var rp = ' in r:
				self.wait_for_threads()
				raise Exception('could not find "var rp = " at %s' % self.url)
			total = int(self.web.between(r, 'var rp = ', ';')[0])
			for index in xrange(1, total + 1):
				url = '%s%d' % (self.url, index)
				while self.thread_count > self.max_threads:
					sleep(0.1)
				t = Thread(target=self.download_image, args=(url, index, total))
				t.start()
				if self.hit_image_limit(): break
		self.wait_for_threads()
	
	def download_image(self, url, index, total):
		self.thread_count += 1
		r = self.web.get(url)
		if '"image_src" href="' in r:
			image = self.web.between(r, '"image_src" href="', '"')[0]
			filename = image[image.rfind('/')+1:]
			save_as = '%s%s%03d_%s' % (self.working_dir, os.sep, index, filename)
			self.save_image(image, save_as, index, total)
		self.thread_count -= 1
