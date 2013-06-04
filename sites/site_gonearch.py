#!/usr/bin/python

from basesite import basesite
import zlib

class gonearch(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'gonearchiving.com/' in url:
			raise Exception('')
		if not 'author=' in url:
			raise Exception('required <b>author=</b> not found in URL')
		author = self.get_author(url)
		if len(author) < 3:
			raise Exception('author name not valid')
		return 'http://gonearchiving.com/indexpics.php?author=%s' % author

	def get_author(self, url):
		author = url[url.find('author=')+len('author='):]
		if '&' in author: author = author[:author.find('&')]
		return author

	""" Discover directory path based on URL """
	def get_dir(self, url):
		return 'gonearch_%s' % self.get_author(url)

	def is_zip(self, text):
		return ord(text[0]) == 31 and ord(text[1]) == 139 and ord(text[2]) == 8

	def decompress(self, text):
		if ord(text[0]) == 31 and ord(text[1]) == 139 and ord(text[2]) == 8:
			d = zlib.decompressobj(16+zlib.MAX_WBITS)
			return d.decompress(text)
		else:
			return text

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		r = self.decompress(r)
		links = self.web.between(r, 'data-src="', '"')
		shows = self.web.between(r, ".load('displayimg.php?rid=", "'")
		total = len(links) + len(shows)
		index = 0
		for link in links:
			index += 1
			link = 'http://gonearchiving.com/%s' % link
			self.download_image(link, index, total=total)
			if self.hit_image_limit(): break
		for show in shows:
			index += 1
			url = 'http://gonearchiving.com/displayimg.php?rid=%s' % show
			r = self.web.get(url)
			r = self.decompress(r)
			if not 'src="gwimg' in r:
				self.log('download failed (%d/%d) - unable to find image at %s' % (index, total, url))
			else:
				img = self.web.between(r, 'src="gwimg', '"')[0]
				img = 'http://gonearchiving.com/gwimg%s' % img
				self.download_image(link, index, total=total)
				if self.hit_image_limit(): break
		self.wait_for_threads()

