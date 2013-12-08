#!/usr/bin/python

from json import loads
from os   import path

from basesite import basesite
class soundcloud(basesite):

	""" Retrieves API key from local file """
	def get_api_key(self):
		api_path = path.join(path.dirname(__file__), 'soundcloud_api.key')
		api_key = ''
		if path.exists(api_path):
			f = open(api_path, 'r')
			api_key = f.read().replace('\n', '').strip()
			f.close()
		if api_key == '':
			raise Exception('no soundcloud API key found at %s' % api_path)
		return api_key

	""" Verify [and alter] URL to an acceptable format """
	def sanitize_url(self, url):
		if not 'soundcloud.com/' in url:
			raise Exception('')
		user = url[url.find('soundcloud.com/')+len('soundcloud.com/'):]
		if '/' in user: user = user.split('/')[0]
		return 'http://soundcloud.com/%s/tracks' % user

	""" Discover directory path based on URL """
	def get_dir(self, url):
		return 'soundcloud_%s' % url.split('/')[-2]

	""" Download images in album """
	def download(self):
		client_id = self.get_api_key()
		url = 'http://api.soundcloud.com/resolve.json?url=%s&client_id=%s' % (self.url, client_id)
		r = self.web.get(url)
		json = None
		try:
			json = loads(r)
		except Exception, e:
			raise Exception('failed to parse json response from soundcloud')
		if 'errors' in json:   raise Exception( str(json['errors']) )
		if type(json) != list: raise Exception('unexpected non-list returned for user')
		if len(json) == 0:     raise Exception('no tracks found for user')
		index = 1
		# Get avatar
		avatar = json[0]['user']['avatar_url']
		avatar = avatar.replace('-large', '-t500x500')
		self.download_image(avatar, index, total=len(json)+1)
		# Get tracks
		for track in json:
			if 'download_url' in track: download_url = track['download_url']
			elif 'stream_url' in track: download_url = track['stream_url']
			else: continue
			download_url = '%s?client_id=%s' % (download_url, client_id)
			index += 1
			saveas = '%03d_%s.m4a' % (index, track['permalink'])
			self.download_image( download_url, index, total=len(json)+1, saveas=saveas )
		self.wait_for_threads()
