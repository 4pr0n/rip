#!/usr/bin/python

from basesite  import basesite
from time      import sleep, time
from threading import Thread
from os        import path
from json      import loads, dumps

BATCH_COUNT = 200 # Number of tweets per request (max)
SLEEP_TIME = 2.5
MAX_REQUESTS_PER_RIP = 15

# Key must contain base64-encoding of UTF-8-encoded 'consumer_key:consumer_secret'
# See https://dev.twitter.com/docs/auth/application-only-auth
TWITTER_API_PATH = 'sites/twitter_api.key'

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
		req  = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
		req += '?screen_name=%s' % user
		req += '&include_entities=true'
		req += '&exclude_replies=true'
		req += '&trim_user=true'
		req += '&include_rts=false'
		req += '&count=%d' % BATCH_COUNT
		if max_id != '0':
			req += '&max_id=%s' % max_id
		self.debug('request: %s' % req)
		return req

	def check_rate_limit(self, headers):
		url = 'https://api.twitter.com/1.1/application/rate_limit_status.json?resources=statuses'
		r = self.web.getter(url, headers=headers)
		print r
		json = loads(r)
		stats = json['resources']['statuses']['/statuses/user_timeline']
		remaining = stats['remaining']
		if remaining < 20:
			# Not enough requests remaining to rip!
			now = int(time())
			diff = stats['reset'] - now # Seconds until reset
			dtime = ''
			if diff > 3600:
				dtime = '%d hours ' % (diff / 3600)
				diff %= 3600
			if diff > 60:
				dtime += '%d min ' % (diff / 60)
				diff %= 60
			if dtime == '' or diff != 0:
				dtime += '%d sec' % diff
			raise Exception('twitter is rate-limited, try again in %s' % dtime)

	""" Magic! """
	def download(self):
		self.init_dir()
		# Get token
		token = self.get_access_token()
		if token == '' or token == None:
			self.wait_for_threads()
			raise Exception('twitter API token not found')
		headers = { 'Authorization' : 'Bearer %s' % token }
		self.check_rate_limit(headers)

		index = 0
		page  = 1
		turl = self.get_request(self.url)
		while page < MAX_REQUESTS_PER_RIP:
			# Make request
			r = self.web.getter(turl, headers=headers)

			try:
				json = loads(r)
			except Exception, e:
				self.wait_for_threads()
				raise Exception('invalid response from twitter: %s' % r)

			if 'errors' in json:
				self.wait_for_threads()
				raise Exception('twitter: %s' % json['errors']['message'])
			elif len(json) == 0:
				break # Empty response, time to go

			max_id = '0'
			for tweet in json:
				max_id = str(tweet.get('id', 1) - 1)
				index = self.get_media(tweet, index)
				index = self.get_url(tweet, index)
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break

			if max_id == '0': break
			turl = self.get_request(self.url, max_id=max_id)
			page += 1
			self.log('loading tweets page %d - %s' % (page, turl))
			sleep(SLEEP_TIME)
		self.wait_for_threads()
	
	""" Retrieve all 'media' URLs from tweet """
	def get_media(self, json, index):
		try:
			medias = json['entities']['media']
		except: # Tweet does not contain media, or some other error occurred
			return index

		for media_chunk in medias:
			if not 'media_url' in media_chunk: continue
			url = media_chunk['media_url']
			self.debug('media_url: %s' % url)
			if '.twimg.com/' in url:
				url += ':large'
			index += 1
			if self.urls_only:
				self.add_url(index, url)
			else:
				sleep(0.5)
				self.download_image(url, index)
		return index

	""" Retrieve all 'expanded_url' from tweet """
	def get_url(self, json, index):
		try:
			urls = json['entities']['urls']
		except: # Tweet does not contain urls, or some other error occurred
			return index
		for url_chunk in urls:
			if not 'display_url' in url_chunk: continue
			url = url_chunk.get('display_url')
			#url = url.replace('\\/', '/')
			self.debug('display_url: %s' % url)
			if  'twitpic.com/' in url or \
					'tumblr.com/'  in url or \
					'vine.co/'     in url:
				index += 1
				while self.thread_count > self.max_threads: sleep(0.1)
				self.thread_count += 1
				t = Thread(target=self.handle_url, args=(url, index))
				t.start()
		return index

	""" Download image from some URL """
	def handle_url(self, url, index):
		try:
			if not url.startswith('http'): url = 'http://%s' % url
			self.debug('handle_url: %s' % url)
			ext = url.lower()[url.rfind('.')+1:]
			imgs = []
			if ext in ['jpg', 'jpeg', 'gif', 'png']:
				imgs = [url]
			else:
				r = self.web.get(url)
				for name in ['twitter:player:stream', 'twitter:image']:
					if '<meta name="%s" value="' % name in r:
						imgs = self.web.between(r, '<meta name="%s" value="' % name, '"')
						break
					if '<meta name="%s" content="' % name in r:
						imgs = self.web.between(r, '<meta name="%s" content="' % name, '"')
						break
			if len(imgs) > 0:
				img = imgs[0]
				if '?' in img: img = img[:img.find('?')]
				if '#' in img: img = img[:img.find('#')]
				if self.urls_only:
					self.add_url(index, img)
					self.thread_count -= 1
					return
				saveas = '%s/%03d_%s' % (self.working_dir, index, img[img.rfind('/')+1:])
				if self.web.download(imgs[0], saveas):
					self.log('downloaded (%d) (%s) - %s' % (index, self.get_size(saveas), img))
					self.create_thumb(saveas)
				else:
					self.log('download failed (%d) - %s' % (index, img))
				sleep(1)
			else:
				self.log('no image found (%d) - %s' % (index, url))
		except Exception, e:
			self.debug('exception in handle_url: %s' % str(e))
		self.thread_count -= 1

	def get_access_token(self):
		global TWITTER_API_PATH
		if not path.exists(TWITTER_API_PATH):
			TWITTER_API_PATH = TWITTER_API_PATH.replace('sites/', '')
		if not path.exists(TWITTER_API_PATH):
			raise Exception('twitter api key not found')
		f = open(TWITTER_API_PATH, 'r')
		key = f.read().strip()
		f.close()
		headers = {
				'Authorization' : 'Basic %s' % key,
				'Content-Type'  : 'application/x-www-form-urlencoded;charset=UTF-8',
				'User-agent'    : 'derv\'s ripe and zipe'
			}
		postdata = { 'grant_type' : 'client_credentials' }
		r = self.web.post('https://api.twitter.com/oauth2/token', postdict=postdata, headers=headers)
		self.debug('token response: %s' % r)
		if not '"access_token":"' in r:
			return ''
		token = self.web.between(r, '"access_token":"', '"')[0]
		return token

