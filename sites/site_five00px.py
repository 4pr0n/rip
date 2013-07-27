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
		page = 1
		while True:
			url = '%s?nolayout=true&page=%d&format=json&image_size=4&rpp=40' % (self.url, page)
			self.debug(url)
			r = self.web.get(url)
			jsobj = loads(r)
			for item in jsobj['items']:
				if item['type'] != 'photo': continue
				photo_url = self.web.between(item['html'], '<a href="', '"')[0]
				photo_url = 'http://500px.com%s' % photo_url
				index += 1
				self.download_image(photo_url, index)
				if self.hit_image_limit(): break
			page += 1
			if page > jsobj['total_pages']: break
			
			sleep(1)
		self.wait_for_threads()
	
	""" Launches thread to download image """
	def download_image(self, url, index):
		while self.thread_count >= self.max_threads:
			sleep(0.1)
		self.thread_count += 1
		args = (url, index)
		t = Thread(target=self.download_image_thread, args=args)
		t.start()
	
	""" Download image at 500px.com/photo/<id> """
	def download_image_thread(self, url, index):
		r = self.web.getter(url)
		
		if not '"image_url":["' in r: 
			self.debug('no imageurl:[ in r')
			self.thread_count -= 1
			return
		img = self.web.between(r, '"image_url":["', '"')[0]
		img = img.replace('\\', '')
		
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
			self.log('downloaded (%d) (%s) - %s' % (index, self.get_size(saveas), img))
		else:
			self.log('download failed (%d) - %s' % (index, img))
		self.thread_count -= 1

