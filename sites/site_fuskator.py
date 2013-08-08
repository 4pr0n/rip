#!/usr/bin/python

from basesite import basesite
from urllib import unquote

class fuskator(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'fuskator.com/' in url:
			raise Exception('')
		if not '/full/' in url:
			raise Exception('required /full/ not found in URL')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		fields = url.replace('http://', '').replace('https://', '').split('/')
		return 'fuskator_%s' % fields[2]

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		baseurls = {}
		bchunks = self.web.between(r, 'var base', "')")
		for bchunk in bchunks:
			key = bchunk[:bchunk.find(' ')]
			value = unquote(bchunk[bchunk.find("'")+1:])
			baseurls[key] = value
		ichunks = self.web.between(r, '.src=base', "'<")
		for index, ichunk in enumerate(ichunks):
			key = ichunk[:ichunk.find('+')]
			img_index = ichunk[ichunk.find("'")+1:]
			if not key in baseurls:
				self.debug('key "%s" not found in baseurls ("%s")' % (key, str(baseurls)))
				continue
			image = '%s%s' % (baseurls[key], img_index)
			self.download_image(image, index + 1, total=len(ichunks))
			if self.hit_image_limit(): break
		self.wait_for_threads()
