#!/usr/bin/python

from basesite import basesite
from time     import sleep

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
		self.log('loading %s' % turl)
		r = self.web.getter(turl)
		index = 0
		while r.strip() != '[]':
			medias  = self.web.between(r, '"media":[{', '}]')
			for media in medias:
				urls = self.web.between(media, '"media_url":"', '"')
				for url in urls:
					url = url.replace('\\/', '/')
					index += 1
					self.download_image(url, index)
			# Find ID of last tweet
			ids = self.web.between(r, '","id":', ',')
			if len(ids) > 0: max_id = int(ids[-1]) - 1
			else: break
			turl = self.get_request(self.url, max_id=max_id)
			self.log('loading %s' % turl)
			sleep(2)
			r = self.web.getter(turl)
		self.wait_for_threads()
	
