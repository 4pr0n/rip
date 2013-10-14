#!/usr/bin/python

from basesite import basesite
from time import sleep
from json import loads

"""
	Downloads instagram albums
"""
class instagram(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if'instagram.com/' in url:
			# Legit
			pass
		elif 'web.stagram.com/n/' in url:
			# Convert to instagram
			user = url[url.find('.com/n/')+len('.com/n/'):]
			if '/' in user: user = user[:user.find('/')]
			url = 'http://instagram.com/%s' % user
		elif 'statigr.am/' in url:
			# Convert to instagram
			user = url[url.find('gr.am/')+len('gr.am/'):]
			if '/' in user: user = user[:user.find('/')]
			url = 'http://instagram.com/%s' % user
			
		else:
			raise Exception('')
		url = url.replace('instagram.com/', 'statigr.am/')
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
		# Need user ID
		r = self.web.get(self.url)
		# http://statigr.am/controller_nl.php?action=getPhotoUserPublic&user_id=24052074&max_id=531938115663720187_24052074
		if not 'id="user_public" value="' in r:
			self.wait_for_threads()
			raise Exception('unable to find user_id at %s' % self.url)
		# And total
		total = '?'
		if '<span class="chiffre">' in r:
			total = self.web.between(r, '<span class="chiffre">', '<')[0].lower().replace(',', '')
			if '.' in total and 'k' in total:
				total = int(float(total.replace('.', '').replace('k', '')) * 1000)
			elif total.isdigit():
				total = int(total)
			else:
				total = '?'

		userid = self.web.between(r, 'id="user_public" value="', '"')[0]
		baseurl = 'http://statigr.am/controller_nl.php?action=getPhotoUserPublic&user_id=%s' % userid
		params = ''
		index = 0
		while True:
			self.debug('loading %s%s' % (baseurl, params))
			r = self.web.get('%s%s' % (baseurl, params))
			max_id = ''
			try:
				json = loads(r)
			except Exception, e:
				self.wait_for_threads()
				raise Exception('unable to load json at %s%s' % (baseurl, params))
			if not 'data' in json or len(json['data']) == 0:
				self.debug('no data found in json response')
				break
			for data in json['data']:
				if 'id' in data:
					max_id = '%s_%s' % (data['id'], userid)
					self.debug('max_id=%s' % max_id)
				if 'videos' in data:
					media = data['videos']['standard_resolution']['url']
				elif 'images' in data:
					media = data['images']['standard_resolution']['url']
				else:
					# No video ro images
					continue
				index += 1
				self.download_image(media, index, total=total)
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			if max_id == '':
				if not 'pagination' in json:
					self.debug('no pagination in json, stopping')
					break
				if not 'next_max_id' in json['pagination']:
					self.debug('no next_max_id in json.pagination, stopping')
					break
				max_id = json['pagination']['next_max_id']
			params = '&max_id=%s' % max_id
			sleep(2)
		self.wait_for_threads()
