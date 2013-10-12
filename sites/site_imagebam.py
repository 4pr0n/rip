#!/usr/bin/python

from basesite  import basesite
from threading import Thread
import time, os

"""
	Downloads imagebam albums
"""
class imagebam(basesite):
	
	"""
		Ensure URL is relevant to this ripper.
		Return 'sanitized' URL (if needed).
	"""
	def sanitize_url(self, url):
		if not 'imagebam.com/' in url: 
			raise Exception('')
		if 'imagebam.com/image/' in url:
			r = self.web.get(url)
			galleries = self.web.between(r, "class='gallery_title'><a href='", "'")
			if len(galleries) == 0 or '/gallery/' not in galleries[0]:
				raise Exception("Required '/gallery/' not found")
			url = galleries[0]
		if not url.endswith('/'): url += '/'
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = self.url
		while u.endswith('/'): u = u[:-1]
		name = u[u.rfind('/')+1:]
		return 'imagebam_%s' % name

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		index = 0
		total = 0
		page = 1
		while True:
			links = self.web.between(r, "href='http://www.imagebam.com/image/", "'")
			total += len(links)
			for link in links:
				index += 1
				link = "http://www.imagebam.com/image/%s" % link
				self.download_image(link, index, total=total) 
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			page += 1
			if 'class="pagination_link">%d</a>' % page in r:
				r = self.web.get('%s%d' % (self.url, page))
			else:
				break
		self.wait_for_threads()
	
	def download_image(self, url, index, total):
		while self.thread_count >= self.max_threads:
			time.sleep(0.1)
		self.thread_count += 1
		args = (url, index, total)
		t = Thread(target=self.download_image_thread, args=args)
		t.start()
	
	def download_image_thread(self, url, index, total):
		r = self.web.get(url)
		imgs = self.web.between(r, ';" src="', '"')
		if len(imgs) == 0:
			self.log('unable to find image - %s' % url)
			self.thread_count -= 1
			return
		img = imgs[0]
		filename = img[img.rfind('/')+1:]
		if '?' in filename: filename = filename[:filename.find('?')]
		if '#' in filename: filename = filename[:filename.find('#')]
		if '&' in filename: filename = filename[:filename.find('&')]
		if not '.' in filename:
			m = self.web.get_meta(img)
			ext = '.jpg'
			if 'Content-Type' in m:
				if '/gif' in m['Content-Type']:
					ext = '.gif'
				elif '/png' in m['Content-Type']:
					ext = '.png'
				elif '/jpeg' in m['Content-Type'] or '/jpg' in m['Content-Type']:
					ext = '.jpg'
			filename += ext
		saveas = '%s%s%03d_%s' % (self.working_dir, os.sep, index, filename)
		self.save_image(img, saveas, index, total)
		self.thread_count -= 1

