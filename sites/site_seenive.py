#!/usr/bin/python

# 'basesite.py' contains lots of functionality required for a ripper
from basesite import basesite

class seenive(basesite):

	""" Verify [and alter] URL to an acceptable format """
	def sanitize_url(self, url):
		if not 'seenive.com/' in url:
			raise Exception('')
		if not 'seenive.com/u/' in url:
			raise Exception('required seenive.com/u/ not found in URL')
		if '#' in url: url = url[:url.find('#')]
		if '?' in url: url = url[:url.find('?')]
		while url.endswith('/'): url = url[:-1]
		fields = url.replace('http://', '').replace('https://', '').split('/')
		if len(fields) < 2 or fields[1] != 'u':
			raise Exception('required format: seenive.com/u/<userid>')
		if len(fields) > 3:
			fields = fields[:3]
		return 'http://%s' % '/'.join(fields)

	""" Discover directory path based on URL """
	def get_dir(self, url):
		return 'seenive_%s' % url[url.rfind('/')+1:]

	""" Download images in album """
	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		total = index = 0
		while True:
			links = self.web.between(r, 'data-video-url="', '"')
			if len(links) == 0: break
			total += len(links)
			for link in links:
				index += 1
				saveas = link[link.rfind('/')+1:]
				saveas = saveas[:saveas.find('_')] + '.mp4'
				saveas = '%03d_%s' % (index, saveas)
				self.download_image(link, index, total=total, saveas=saveas)
				if self.hit_image_limit(): break
			last_posts = self.web.between(r, 'postFeed.lastPostId = "', '"')
			if len(last_posts) == 0:
				last_posts = self.web.between(r, '"LastPostId":"', '"')
			if len(last_posts) == 0: break
			r = self.web.get('%s/next/%s' % (self.url, last_posts[0]))
			r = r.replace('\\"', '"')
		self.wait_for_threads()

