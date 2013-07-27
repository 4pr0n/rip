#!/usr/bin/python

from basesite import basesite

class pichunter(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'pichunter.com/' in url:
			raise Exception('')
		if not 'society.pichunter.com/php/gallery.php' in url:
			raise Exception('required society.pichunter.com/php/gallery.php not found')
		if not 'u=' in url:
			raise Exception('required u= not found in url')
		if '&p=' in url:
			self.debug('stripping page number from url')
			left = url[:url.find('&p=')]
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		gid = url[url.find('u=')+2:]
		if '&' in gid: gid = gid[:gid.find('&')]
		return 'pichunter_%s' % gid

	def download(self):
		self.init_dir()
		index = 0
		total = '?'
		# Iterate over every page
		pagenum = 0
		while True:
			url = '%s&p=%d' % (self.url, pagenum)
			self.debug(url)
			r = self.web.get(url)
			if total == '?': total = self.get_total(r)
			imageids = self.web.between(r, "href='photo.php?id=", "'")
			for imageid in imageids:
				index += 1
				url = 'http://img2.pichunter.com/photos/%s/%s.jpg' % (imageid[0:2], imageid)
				self.download_image(url, index, total=total)
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			if 'Next &#187;</span>' in r: break
			pagenum += 1
		self.wait_for_threads()
	
	def get_total(self, r):
		if not "tab_switcher.activate($('" in r:
			self.debug('get_total: could not find tab_switcher.activate')
			return '?'
		tab = self.web.between(r, "tab_switcher.activate($('", "'")[0]
		chunks = self.web.between(r, '&t=%s">' % tab, '<')
		if len(chunks) == 0:
			self.debug('get_total: could not find &t=%s">' % tab)
			return '?'
		totals = self.web.between(chunks[0], '(', ')')
		if len(totals) == 0:
			self.debug('get_total: could not find parenthesis in "%s"' % chunks[0])
			return '?'
		if not totals[0].replace(',', '').isdigit():
			self.debug('get_total: total "%s" is not numeric' % totals[0])
			return '?'
		return int(totals[0].replace(',', ''))
