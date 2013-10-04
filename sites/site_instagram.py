#!/usr/bin/python

from basesite import basesite
from json import loads
from time import sleep
from os   import path

"""
	Downloads instagram albums
"""
class instagram(basesite):
	
	""" Retrieves API key from local file """
	def get_api_key(self):
		api_path = path.join(path.dirname(__file__), 'instagram_api.key')
		api_key = ''
		if path.exists(api_path):
			f = open(api_path, 'r')
			api_key = f.read().replace('\n', '').strip()
			f.close()
		if api_key == '':
			raise Exception('no instagram API key found at %s' % api_path)
		return api_key

	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if'instagram.com/' in url:
			# Legit
			pass
		elif 'web.stagram.com/n/' in url:
			# Convert to web.stagram
			user = url[url.find('.com/n/')+len('.com/n/'):]
			if '/' in user: user = user[:user.find('/')]
			url = 'http://instagram.com/%s' % user
		else:
			raise Exception('')
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		while url.endswith('/'): url = url[:-1]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = url[url.rfind('/')+1:]
		return 'instagram_%s' % user

	def download(self):
		self.init_dir()
		client_id = self.get_api_key()
		baseurl = '%s/media?client_id=%s' % (self.url, client_id)
		url = baseurl
		index = 0
		while True:
			self.debug('loading %s' % url)
			r = self.web.get(url)
			try: json = loads(r)
			except:
				self.wait_for_threads()
				self.debug('invalid json response:\n%s' % r)
				raise Exception('unable to parse json at %s' % url)
			if not json['status'] == 'ok':
				self.wait_for_threads()
				self.log('status NOT OK: %s' % json['status'])
				raise Exception('status not "ok": %s' % json['status'])
			last_id = 0
			for item in json['items']:
				last_id = item['id']
				for media_type in ['videos', 'images']:
					if not media_type in item: continue
					index += 1
					media_url = item[media_type]['standard_resolution']['url']
					if self.urls_only:
						self.add_url(index, media_url)
					else:
						self.download_image(media_url, index)
						sleep(0.5)
					break
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			if not json['more_available'] or last_id == 0: break
			sleep(2)
			url = '%s&max_id=%s' % (baseurl, last_id)
		self.wait_for_threads()
	
