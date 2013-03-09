#!/usr/bin/python

from basesite import basesite
from time     import sleep

# Key for querying tumblr's API
API_KEY = 'v5kUqGQXUtmF7K0itri1DGtgTs0VQpbSEbh1jxYgj9d2Sq18F8'

"""
	Downloads tumblr albums
"""
class tumblr(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not '.tumblr.com' in url:
			raise Exception('')
		if 'www.tumblr.com' in url:
			raise Exception('Required user.tumblr.com format')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		return 'tumblr_%s' % self.get_user(url)
	
	""" Returns tumblr user from URL """
	def get_user(self, url):
		url = url.replace('http://', '').replace('https://', '')
		user = url[:url.find('.')]
		return user

	""" Returns URL to retrieve content with """
	def get_base_url(self, url, media='photo', offset=0):
		user  = self.get_user(url)
		turl  = 'http://api.tumblr.com/v2/blog/%s' % user
		turl += '.tumblr.com/posts/%s' % media
		turl += '?api_key=%s' % API_KEY
		turl += '&offset=%d' % offset
		if '/tagged/' in url:
			tag = url[url.find('/tagged/')+len('/tagged/'):]
			if '/' in tag: tag = tag[:tag.find('/')]
			turl += '&tag=%s' % tag
		return turl

	""" Parses media content from tumblr's JSON output """
	def parse_tumblr(self, r, index, total, media_type):
		chunks = self.web.between(r, '"blog_name":', '}]}')
		if len(chunks) == 0: return 0
		for chunk in chunks:
			ids = self.web.between(chunk, '"id":', ',')
			if len(ids) == 0: continue
			id = ids[0]
			if media_type == 'video':
				medias = self.web.between(chunk, '"video_url":"', '"')
			else:
				medias = self.web.between(chunk, '"original_size":{', '}')
			if len(medias) == 0: continue
			for media in medias:
				if media_type == 'video':
					content = media
				else:
					if not '"url":"' in media: continue
					content = media[media.find('"url":"')+len('"url":"'):-1]
				content = content.replace('\\/', '/')
				index += 1
				self.download_image(content, index, total=total)
		return index
	
	""" Returns total # of posts given a JSON response """
	def get_total(self, text):
		totals = self.web.between(text, '"total_posts":', '}')
		if len(totals) > 0: return int(totals[0])
		return 0

	""" Mystery! """
	def download(self):
		self.init_dir()
		index = 0
		total = 0
		for media in ['photo']: #, 'video']:
			offset = 0
			while True:
				base_url = self.get_base_url(self.url, media=media, offset=offset)
				offset += 20
				r = self.web.get(base_url)
				if total == 0: total = self.get_total(r)
				index = self.parse_tumblr(r, index, total, media)
				if index == 0: break
				sleep(2)
		self.wait_for_threads()
	
