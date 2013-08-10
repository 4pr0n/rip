#!/usr/bin/python

from basesite import basesite
from json import loads
from time import sleep
from threading import Thread
from os import path, sep

""" 500px.com """
class five00px(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not '500px.com/' in url:
			raise Exception('')
		user = url[url.find('500px.com/')+len('500px.com/'):]
		if len(user) == 0:
			raise Exception('required 500px.com/&lt;user&gt; not found')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = url[url.find('500px.com/')+len('500px.com/'):]
		if '?' in user: user = user[:user.find('?')]
		if '#' in user: user = user[:user.find('#')]
		if '/' in user: user = user[:user.find('/')]
		return '500px_%s' % user

	""" Download all pics at 500px.com """
	def download(self):
		self.init_dir()
		index = 0
		total = 0
		page = 1
		while True:
			url = '%s?nolayout=true&page=%d&format=json&image_size=4&rpp=20' % (self.url, page)
			self.debug(url)
			r = self.web.getter(url)
			jsobj = loads(r)
			if 'total_pages' in jsobj:
				total = jsobj['total_pages'] * 40
			for item in jsobj['items']:
				if item['type'] != 'photo': continue
				index += 1
				photo_url = self.web.between(item['html'], '<img src="', '"')[0]
				photo_url = photo_url.replace('/3.jpg', '/1080.jpg')
				if '/nude/' in photo_url:
					# Need to visit photo page to get image
					photo_url = self.web.between(item['html'], '<a href="', '"')[0]
					photo_url = 'http://500px.com%s' % photo_url
					self.download_500px_image(photo_url, index, total=total)
				else:
					# Can directly download image
					self.download_image(photo_url, index, total)
				if self.hit_image_limit(): break
			page += 1
			if page > jsobj['total_pages']: break
			
		self.wait_for_threads()
	
	""" Launches thread to download image """
	def download_500px_image(self, url, index, total):
		while self.thread_count >= self.max_threads:
			sleep(0.1)
		self.thread_count += 1
		args = (url, index, total)
		t = Thread(target=self.download_500px_image_thread, args=args)
		t.start()
	
	""" Download image at 500px.com/photo/<id> """
	def download_500px_image_thread(self, url, index, total):
		r = self.web.getter(url)
		
		if not '"image_url":["' in r: 
			self.debug('no imageurl:[ in r at %s' % url)
			self.thread_count -= 1
			return
		imgs = self.web.between(r, '"image_url":[', ']')[0].split(',')
		img = None
		for tmp_img in imgs:
			tmp_img = tmp_img.replace('\\', '').replace('"', '')
			if '/placeholder/' in tmp_img: continue
			img = tmp_img
			break
		
		if img == None:
			self.debug('unable to find image at' % url)
			self.thread_count -= 1
			return
		if self.urls_only:
			self.add_url(index, img)
			self.thread_count -= 1
			return
		urlid = url[url.rfind('/')+1:]
		extension = img[img.rfind('.')+1:]
		saveas = '%s%s%03d_%s.%s' % (self.working_dir, sep, index, urlid, extension)
		if path.exists(saveas):
			self.image_count += 1
			self.log('file exists: %s' % saveas)
		elif self.web.download(img, saveas):
			self.image_count += 1
			self.log('downloaded (%d/%d) (%s) - %s' % (index, total, self.get_size(saveas), img))
		else:
			self.log('download failed (%d/%d) - %s' % (index, total, img))
		sleep(1)
		self.thread_count -= 1

