#!/usr/bin/python

from basesite  import basesite
from threading import Thread
from os import path
import time

"""
	Downloads flickr albums
"""
class flickr(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'flickr.com' in url:
			raise Exception('')
		if not '/photos/' in url:
			raise Exception('required /photos/ not found in URL')
		users = self.web.between(url, '/photos/', '/')
		if len(users) == 0 or users[0] == 'tags':
			raise Exception('invalid flickr album URL')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		return 'flickr_%s' % self.web.between(url, '/photos/', '/')[0]

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		total = '?'
		if '<div class="vsNumbers">' in r:
			count = self.web.between(r, '<div class="vsNumbers">', 'photos')[0].strip()
			while ' '  in count: count = count.replace(' ',  '')
			while '\n' in count: count = count.replace('\n', '')
			if count.isdigit(): total = int(count)
		if 'class="Results">(' in r:
			count = self.web.between(r, 'class="Results">(', ' ')[0]
			count = count.replace(' ', '').replace('\n', '').replace(',', '')
			if count.isdigit(): total = int(count)
		if '<div class="stat statcount"' in r:
			chunk = self.web.between(r, '<div class="stat statcount"', '</div>')[0]
			if '<h1>' in chunk:
				count = self.web.between(chunk, '<h1>', '</h1>')[0].strip()
				if count.isdigit(): total = int(count)
			
		index = 0
		while True:
			# Get images
			links = self.web.between(r, '><a data-track="photo-click" href="', '"')
			for link in links:
				if link == '{{photo_url}}': continue
				link = 'http://www.flickr.com%s' % link
				# Download every image
				# Uses superclass threaded download method
				index += 1
				self.download_image(link, index, total=total) 
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			if 'data-track="next" href="' in r:
				nextpage = self.web.between(r, 'data-track="next" href="', '"')[0]
				if not 'flickr.com' in nextpage:
					nextpage = 'http://flickr.com%s' % nextpage
				r = self.web.get(nextpage)
			else:
				break
		self.wait_for_threads()
	
	def download_image(self, url, index, total='?', subdir=''):
		while self.thread_count >= self.max_threads:
			time.sleep(0.1)
		self.thread_count += 1
		args = (url, index, total)
		t = Thread(target=self.download_image_thread, args=args)
		t.start()
		
	def download_image_thread(self, url, index, total):
		pid = url[:url.rfind('/in/')]
		pid = pid[pid.rfind('/')+1:]
		larger = url.replace('/in/', '/sizes/o/in/')
		r = self.web.get(larger)
		titles = self.web.between(r, 'title="', '"')
		if len(titles) > 0:
			title = titles[0]
			if '|' in title: title = title[:title.find('|')].strip()
			title = self.fix_filename(title)
		else:
			title = 'unknown'
		imgs = self.web.between(r, '<img src="http://farm', '"')
		if len(imgs) == 0:
			self.log('unable to find image @ %s' % url)
		else:
			img = 'http://farm%s' % imgs[0]
			if self.urls_only:
				self.add_url(index, img, total)
				self.thread_count -= 1
				return
			ext = img[img.rfind('.'):]
			saveas = '%s/%03d_%s_%s%s' % (self.working_dir, index, pid, title, ext)
			if '?' in saveas: saveas = saveas[:saveas.find('?')]
			if path.exists(saveas):
				self.image_count += 1
				self.log('%s already exists (%d/%s) (%s)' % (saveas[saveas.rfind('/')+1:], index, total, self.get_size(saveas)))
			elif self.web.download(img, saveas):
				self.image_count += 1
				self.log('downloaded (%d/%s) (%s) - %s' % (index, total, self.get_size(saveas), img))
			else:
				self.log('download failed (%d/%s) - %s' % (index, total, img))
		self.thread_count -= 1
	
	""" Parses non-filename-safe characters """
	def fix_filename(self, text):
		good = 'abcdefghijklmnopqrstuvwxyz0123456789.'
		result = ''
		for i in xrange(0, len(text)):
			if text[i].lower() in good:
				result += text[i]
			elif text[i] in [' ', '_', '\n']:
				result += '-'
		return result
