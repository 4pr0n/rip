#!/usr/bin/python

from basesite import basesite
from threading import Thread
from time import sleep
import os

class setsdb(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'setsdb.org/' in url:
			raise Exception('')
		if '#' in url: url = url[:url.find('#')]
		if '?' in url: url = url[:url.find('?')]
		while url.endswith('/'): url = url[:-1]
		if not 'setsdb.org/' in url:
			raise Exception('required setsdb.org/galleryname not found')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		gid = url[url.rfind('/')+1:]
		return 'setsdb_%s' % gid

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		chunks = self.web.between(r, '</span></p>', '<div class=')
		self.debug('chunks: %d' % len(chunks))
		if len(chunks) == 0:
			self.wait_for_threads()
			raise Exception('unable to download album at %s' % self.url)
		links = self.web.between(chunks[0], 'href="', '"')
		for index, link in enumerate(links):
			while self.thread_count >= self.max_threads: sleep(0.1)
			self.thread_count += 1
			t = Thread(target=self.download_image, args=(link, index+1, len(links)))
			t.start()
			if self.hit_image_limit(): break
		self.wait_for_threads()
	
	def download_image(self, url, index, total):
		r = self.web.get(url)
		before = None
		add_domain = False
		if 'sharenxs' in url:
			before = '\n<img src="'
			after = '"'
			add_domain = True
		elif 'imagevenue.com' in url:
			before = 'scaleImg();"   SRC="'
			after = '"'
			add_domain = True
		elif 'imgchili.com' in url:
			before = '      src="'
			after = '"'
		
		if before == None or not before in r:
			self.log('unable to download image at: %s' % url)
			self.thread_count -= 1
			return
		image = self.web.between(r, before, after)[0]
		
		if add_domain:
			temp = url.replace('http://', '')
			temp = temp[:temp.find('/')+1]
			temp = temp.replace('//', '/')
			image = 'http://%s%s' % (temp, image)
		
		filename = image[image.rfind('/')+1:]
		if '?' in filename: filename = filename[:filename.find('?')]
		saveas = '%s%s%03d_%s' % (self.working_dir, os.sep, index, filename)
		self.save_image(image, saveas, index, total)
		self.thread_count -= 1
	
