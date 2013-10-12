#!/usr/bin/python

from basesite import basesite

class imgsrc(basesite):
	
	# http://imgsrc.ru/main/pic.php?ad=774665
	# http://imgsrc.ru/jp101091/26666184.html?pwd=&lang=en#
	# http://imgsrc.ru/fotoivanov/a661729.html
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'imgsrc.ru/' in url:
			raise Exception('')
		u = url
		if '?' in u: u = u[:u.find('?')]
		u = u.replace('http://', '').replace('https://', '')
		splits = u.split('/')
		if len(splits) != 3 or \
				splits[1] == 'main' or \
				splits[2] == 'pic.php':
			raise Exception('invalid imgsrc url: expected <b>http://imgsrc.ru/&lt;user&gt;/&lt;album&gt;.html</b>')
		return 'http://imgsrc.ru/%s/%s' % (splits[1], splits[2])

	""" Discover directory path based on URL """
	def get_dir(self, url):
		splits = url.split('/')
		if '.' in splits[-1]: splits[-1] = splits[-1][:splits[-1].find('.')]
		return 'imgsrc_%s' % '_'.join(splits[-2:])

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		if "href='/main/warn.php" in r:
			# Need to verify age
			verify = self.web.between(r, "href='/main/warn.php", "'")[0]
			verify = 'http://imgsrc.ru/main/warn.php%s' % verify
			self.web.get(verify)
			r = self.web.get(self.url)
		if 'Please enter album\'s password' in r:
			self.wait_for_threads()
			raise Exception('album is password protected')
		if not "href='/main/pic_tape.php?ad=" in r:
			self.wait_for_threads()
			raise Exception('could not find "view all images" link')
		skip_amount = 12
		current     = 0
		img_index   = 0
		img_total   = 0
		# Load full-page gallery to save time
		temp_url = self.web.between(r, "href='/main/pic_tape.php?ad=", '&')[0]
		self.url = 'http://imgsrc.ru/main/pic_tape.php?ad=%s' % temp_url
		r = self.web.get(self.url)
		while True:
			links = self.web.between(r, 'class="big" src=\'', "'")
			img_total += len(links)
			for link in links:
				img_index += 1
				self.download_image(link, img_index, total=img_total)
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			if '>next ' not in r: break
			current += skip_amount
			r = self.web.get('%s&way=&skp=%d&pwd=' % (self.url, current))
		self.wait_for_threads()
	
