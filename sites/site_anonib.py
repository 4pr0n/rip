#!/usr/bin/python

from basesite import basesite
from os import path, remove

"""
	Rips images from an anonib post.
	Also archives the text from the post
"""
class anonib(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'anonib.com/' in url:
			raise Exception('')
		if not '/res/' in url:
			raise Exception('required /res/ not found in URL')
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		dirs = url.replace('http://', '').replace('https://', '').split('/')
		if len(dirs) != 4 or dirs[2] != 'res':
			raise Exception('required format: http://anonib.com/<board>/res/#.html')
		number = dirs[3]
		if '+' in number:
			number = number[:number.find('+')] + number[number.rfind('.'):]
		return 'http://%s/%s' % ('/'.join(dirs[:3]), number)

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = url.replace('http://', '')
		dirs = u.split('/')
		board = dirs[1]
		number = dirs[3][:dirs[3].find('.')]
		return 'anonib_%s_%s' % (board, number)

	""" Rip images & archive text post """
	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		
		# Rip images
		links = self.web.between(r, '/img.php?path=', '"')
		for index, link in enumerate(links):
			self.download_image(link, index + 1, total=len(links))
			if self.hit_image_limit(): break
		
		# Log the content of the posts to a text file
		if path.exists('%s/post.txt' % self.working_dir):
			remove('%s/post.txt' % self.working_dir)
		posts = self.web.between(r, '<blockquote>', '</blockquote>')
		if len(posts) > 0:
			self.log_post('http://rip.rarchives.com - text log from %s\n' % self.url)
			for post in posts:
				self.log_post(post)
		self.wait_for_threads()
	
	""" Strips HTML from a single post text, appends to text file """
	def log_post(self, text):
		while '<a href="/' in text:
			i = text.find('<a href="/')
			j = text.find('>', i)
			text = text[:i] + text[j+1:] + ' '
		for tag in ['a', 'body', 'html', 'p', 'strong']:
			if  '<%s>' % tag in text: text = text.replace('<%s>' % tag, '')
			if '</%s>' % tag in text: text = text.replace('</%s>' % tag, '')
		if      '\r' in text: text = text.replace('\r',     '')
		if      '  ' in text: text = text.replace('  ',     ' ')
		if  '<br />' in text: text = text.replace('<br />', '\n')
		while '\n\n' in text: text = text.replace('\n\n',   '\n')
		text = text.replace('&gt;', '>').replace('&nbsp;', ' ').replace('&#039;', "'").replace('&quot;', '"')
		text = text.strip()
		if text == '': return # Don't log empty posts
		f = open('%s/post.txt' % self.working_dir, 'a')
		f.write('%s\n' % text);
		f.write('--------------------------\n')
		f.close()

