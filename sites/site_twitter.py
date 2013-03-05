#!/usr/bin/python

from basesite  import basesite
from time      import sleep
from threading import Thread

BATCH_COUNT = 200 # Number of tweets per request (max)

"""
	Downloads twitter albums
"""
class twitter(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'twitter.com/' in url:
			raise Exception('')
		if url.endswith('twitter.com/'):
			raise Exception('No twitter username given')
		return url
	
	""" Gets twitter user from URL """
	def get_user(self, url):
		user = url[url.find('twitter.com/')+len('twitter.com/'):]
		if '/' in user: user = user[:user.find('/')]
		return user

	""" Discover directory path based on URL """
	def get_dir(self, url):
		return 'twitter_%s' % self.get_user(url)

	""" Returns URL request string for user from URL """
	def get_request(self, url, max_id='0'):
		user = self.get_user(url)
		req  = 'https://api.twitter.com/1/statuses/user_timeline.json'
		req += '?screen_name=%s' % user
		req += '&include_entities=true'
		req += '&exclude_replies=true'
		req += '&trim_user=true'
		req += '&include_rts=false'
		req += '&count=%d' % BATCH_COUNT
		if max_id != '0':
			req += '&max_id=%s' % max_id
		return req

	""" Magic! """
	def download(self):
		turl = self.get_request(self.url)
		self.log('loading tweets... - %s' % turl)
		r = self.web.getter(turl)
		index = 0
		while r.strip() != '[]':
			index = self.get_medias(r, index)
			index = self.get_urls(r, index)
			# Find ID of last tweet
			ids = self.web.between(r, '","id":', ',')
			if len(ids) > 0: max_id = int(ids[-1]) - 1
			else: break
			turl = self.get_request(self.url, max_id=max_id)
			self.log('loading tweets... - %s' % turl)
			sleep(2)
			r = self.web.getter(turl)
		self.wait_for_threads()
	
	""" Retrieve all 'media' URLs from tweets """
	def get_medias(self, json, index):
		medias = self.web.between(json, '"media":[{', '}]')
		for media in medias:
			urls = self.web.between(media, '"media_url":"', '"')
			for url in urls:
				url = url.replace('\\/', '/')
				index += 1
				self.download_image(url, index)
		return index

	""" Retrieve all 'expanded_url' from tweets """
	def get_urls(self, json, index):
		urls = self.web.between(json, '"expanded_url":"', '"')
		for url in urls:
			url = url.replace('\\/', '/')
			if  'twitpic.com/'       in url or \
					'someothersite.com/' in url:
				index += 1
				while self.thread_count > self.max_threads: sleep(0.1)
				self.thread_count += 1
				t = Thread(target=self.get_url, args=(url, index))
				t.start()
		return index

	""" Download image from some URL """
	def get_url(self, url, index):
		ext = url.lower()[url.rfind('.')+1:]
		if ext in ['jpg', 'jpeg', 'gif', 'png']:
			imgs = [url]
		else:
			r = self.web.get(url)
			imgs = self.web.between(r, '<meta name="twitter:image" value="', '"')
		if len(imgs) > 0:
			img = imgs[0]
			if '?' in img: img = img[:img.find('?')]
			if '#' in img: img = img[:img.find('#')]
			saveas = '%s/%03d_%s' % (self.working_dir, index, img[img.rfind('/')+1:])
			if self.web.download(imgs[0], saveas):
				self.log('downloaded (%d) (%s) - %s' % (index, self.get_size(saveas), img))
			else:
				self.log('download failed (%d) - %s' % (index, img))
			sleep(1)
		else:
			self.log('no image found (%d) - %s' % (index, url))
		self.thread_count -= 1
