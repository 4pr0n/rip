#!/usr/bin/python

from basesite  import  basesite
from os        import path, sep
from threading import    Thread
from time      import     sleep

class chickupload(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'chickupload.com/' in url:
			raise Exception('')
		if 'chickupload.com/gallery/' in url:
			while url[-1] == '/': url = url[:-1]
			if len(url[url.find('/gallery/')+len('/gallery/'):].split('/')) != 2:
				raise Exception('expected "chickupload.com/gallery/XXXXX/YYYYY" not found')
			if not url.startswith('http://'): url = 'http://%s' % url
			return url
		elif 'chickupload.com/showpicture/' in url:
			while url[-1] == '/': url = url[:-1]
			splits = url.split('/')
			if len(splits) < 4 or splits[-4] != 'showpicture':
				raise Exception('expected URL format "chickupload.com/showpicture/#####/XXXXX/YYYYY" not found')
			if not url.startswith('http://'): url = 'http://%s' % url
			return url
		else:
			raise Exception('Unable to rip URL, required "/gallery" or "/showpicture/" not found')
			

	""" Discover directory path based on URL """
	def get_dir(self, url):
		splits = url.split('/')
		return 'chickupload_%s' % '_'.join(splits[-2:])

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		index = 0
		total = 0
		page  = 1
		while True:
			gal_chunks = self.web.between(r, '<div class="actions">', '</div>')
			if len(gal_chunks) > 0:
				totals = self.web.between(gal_chunks[0], ' (', ' picture')
				if len(totals) > 0:
					total = int(totals[0].replace(',', '').replace(' ', ''))
			link_chunks = self.web.between(r, '<div id="gallery_index"', '</div>')
			self.debug('link_chunks: %d' % len(link_chunks))
			if len(link_chunks) == 0: break
			for link in self.web.between(link_chunks[0], '<a href="', '"'):
				link = 'http://chickupload.com%s' % link
				self.debug('found link: %s' % link)
				index += 1
				self.download_image(link, index, total=total)
				if self.hit_image_limit(): break
			page += 1
			if '/page:%d"' % page in r:
				r = self.web.get('%s/page:%d' % (self.url, page))
			else:
				break
		self.wait_for_threads()
	
	""" Launches thread to download image """
	def download_image(self, url, index, total):
		while self.thread_count >= self.max_threads:
			sleep(0.1)
		self.thread_count += 1
		args = (url, index, total)
		t = Thread(target=self.download_image_thread, args=args)
		t.start()
	
	""" Downloads image from deviantart image page """
	def download_image_thread(self, url, index, total):
		r = self.web.get(url)
		pics = self.web.between(r, '<img src="/picture/', '"')
		if len(pics) > 0:
			pic = 'http://chickupload.com/picture/%s' % pics[0]
			filename = pic[pic.rfind('/')+1:]
			saveas = '%s%s%03d_%s' % (self.working_dir, sep, index, filename)
			self.save_image(pic, saveas, index, total)
		self.thread_count -= 1
