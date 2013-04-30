#!/usr/bin/python

from basesite  import basesite
from threading import Thread
import time, os

"""
	Downloads deviantart albums
"""
class deviantart(basesite):
	# http://riabunnie.deviantart.com/gallery/25814351
	# http://riabunnie.deviantart.com/gallery/
	
	"""
		Ensure URL is relevant to this ripper.
		Return 'sanitized' URL (if needed).
	"""
	def sanitize_url(self, url):
		if not '.deviantart.com' in url: 
			raise Exception('')
		if not url.lower().startswith('http'): url = 'http://%s' % url
		user = self.web.between(url, '//', '.')[0]
		if user == 'www' or user == 'deviantart':
			raise Exception('DeviantArt ID not found')
		if not '.com/gallery/' in url:
			url = 'http://%s.deviantart.com/gallery/?catpath=/' % user
		else:
			num = url[url.find('.com/gallery/')+len('.com/gallery/'):]
			if '/' in num: num = num[:num.find('/')]
			if len(num) == 0 or not num.isdigit():
				url = 'http://%s.deviantart.com/gallery/?catpath=/' % user
			else:
				url = 'http://%s.deviantart.com/gallery/%s' % (user, num)
		return url

	""" Discover directory based on URL """
	def get_dir(self, url):
		user = self.web.between(url, '//', '.')[0]
		while url.endswith('/'): url = url[:-1]
		if '/gallery/' in url and not url.endswith('/gallery/'):
			num = url[url.rfind('/')+1:]
			if '/' in num: num = num[:num.find('/')]
			if len(num) > 0 and num.isdigit():
				return 'deviantart_%s_%s' % (user, num)
		return 'deviantart_%s' % user

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		total = 0
		already_have = [] # List of images already parsed
		while True:
			chunks  = self.web.between(r, 'px;"><a class="thumb', '>')
			total += len(chunks)
			for chunk in chunks:
				link = self.web.between(chunk, 'href="', '"')[0]
				if link in already_have: continue
				already_have.append(link)
				if self.hit_image_limit(): break
				self.download_image(link, len(already_have), total=total) 
			if self.hit_image_limit(): break
			next_page = self.get_next_page(r)
			if next_page == None: break
			if   '?' in self.url: next_page = '&offset=%s' % next_page
			else: next_page = '?offset=%s' % next_page
			r = self.web.getter('%s%s' % (self.url, next_page))
		self.wait_for_threads()
	
	""" Retrive link to 'next' page in gallery. Returns None if last page """
	def get_next_page(self, r):
		lis = self.web.between(r, '<li class="next">', '</li>')
		if len(lis) == 0 or not 'href="' in lis[0]: return None
		
		hrefs = self.web.between(lis[0], 'href="', '"')
		if len(hrefs) == 0 or not 'offset=' in hrefs[0]: return None
		
		return hrefs[0][hrefs[0].rfind('offset=')+len('offset='):]
	
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
		r = self.web.getter(url)
		img = None
		if 'id="download-button"' in r:
			dl = self.web.between(r, 'id="download-button"', '<')[0]
			imgs = self.web.between(dl, 'href="', '"')
			if len(imgs) == 0:
				self.log('unable to download image at: %s' % url)
				self.thread_count -= 1
				return
			img = imgs[0]
		if img == None and 'ResViewSizer_img"' in r:
			sizer = self.web.between(r, 'ResViewSizer_img"', '>')[0]
			imgs = self.web.between(sizer, 'src="', '"')
			if len(imgs) == 0:
				self.log('unable to download image at: %s' % url)
				self.thread_count -= 1
				return
			img = imgs[0]
		if img == None and 'name="og:image" content="' in r:
			img = self.web.between(r, 'name="og:image" content="', '"')[0]
		if img == None and '<div class="preview"' in r:
			chunk = self.web.between(r, '<div class="preview"', '</div>')[0]
			imgs = self.web.between(chunk, '" data-src="', '"')
			if len(imgs) == 0:
				self.log('unable to download image at: %s' % url)
				self.thread_count -= 1
				return
			img = imgs[0]
			img = img.replace('://th', '://fc').replace('/150/f/', '/f/')
		if img == None:
			self.log('image not found at: %s' % url)
			self.thread_count -= 1
			return
		if '/i/' in img:
			splits = img.split('/')
			i = splits.index('i')
			if i == 5:
				splits.pop(i - 1)
				img = '/'.join(splits)
		if '&amp;' in img: img = img.replace('&amp;', '&')
		if self.urls_only:
			self.add_url(index, img, total=total)
			self.thread_count -= 1
			return
		filename = img[img.rfind('/')+1:]
		if '?' in filename: filename = filename[:filename.find('?')]
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

