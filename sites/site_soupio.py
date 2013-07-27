#!/usr/bin/python

from basesite import basesite

class soupio(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'redditsluts.soup.io/' in url:
			raise Exception('')
		if not '/tag/' in url:
			raise Exception('required /tag/ not found in URL')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		tag = url[url.find('/tag/')+5:]
		if '/' in tag: tag = tag[:tag.find('/')]
		if '?' in tag: tag = tag[:tag.find('?')]
		if '#' in tag: tag = tag[:tag.find('#')]
		return 'soupio_%s' % tag

	def download(self):
		self.init_dir()
		url = self.url
		index = 0
		total = 0
		while True:
			r = self.web.get(url)
			chunks = self.web.between(r, '<div class="imagecontainer"', '</div>')
			total += len(chunks)
			for chunk in chunks:
				if '<a href="' in chunk:
					url = self.web.between(chunk, '<a href="', '"')[0]
				elif ' src="' in chunk:
					url = self.web.between(chunk, ' src="', '"')[0]
				else:
					continue
				index += 1
				if self.urls_only:
					self.add_url(index, url, total=total)
				else:
					self.download_image(url, index, total=total)
				if self.hit_image_limit(): break
			if "SOUP.Endless.next_url = '" in r:
				next_page = self.web.between(r, "SOUP.Endless.next_url = '", "'")[0]
				url = 'http://redditsluts.soup.io%s' % next_page
			else:
				break
		self.wait_for_threads()
