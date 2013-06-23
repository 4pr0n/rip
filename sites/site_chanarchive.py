#!/usr/bin/python

from basesite import basesite
from os import path, remove

"""
	Rips images from an 4chan post.
	Also archives the text from the post
"""
class chanarchive(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'chanarchive.org/' in url:
			raise Exception('')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = url.replace('http://', '')
		dirs = u.split('/')[1:3]
		return 'chanarchive_%s' % ('-'.join(dirs))

	""" Rip images & archive text post """
	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		
		if path.exists('%s/post.txt' % self.working_dir):
			remove('%s/post.txt' % self.working_dir)
		if not self.urls_only:
			self.log_post('http://rip.rarchives.com - text log from %s\n' % self.url)
		
		posts = self.web.between(r, '<div class="postContainer', '</blockquote>')
		for index, post in enumerate(posts):
			if ',"tim":' in post and ',"ext":"' in post:
				# Has image
				imgid = self.web.between(post, ',"tim":', ',')[0]
				imgext = self.web.between(post, ',"ext":"', '"')[0]
				link = 'http://images.4chan.org/%s/src/%s%s' % (board, imgid, imgext)
				if self.urls_only:
					self.add_url(index + 1, link, total=len(posts))
				else:
					self.download_image(link, index + 1, total=len(posts))
					if self.hit_image_limit(): break
			
			if ',"com":"' in post and not self.urls_only:
				# Has comment
				comment = self.web.between(post, ',"com":"', '","')[0]
				comment = comment.replace('\\"', '"')
				comment = comment.replace('\\/', '/')
				self.log_post(comment)
		self.wait_for_threads()
	
	""" Strips HTML from a single post text, appends to text file """
	def log_post(self, text):
		while '<a href="' in text:
			i = text.find('<a href="')
			j = text.find('>', i)
			text = text[:i] + text[j+1:] + ' '
		for tag in ['a', 'body', 'html', 'p', 'strong']:
			if  '<%s>' % tag in text: text = text.replace('<%s>' % tag, '')
			if '</%s>' % tag in text: text = text.replace('</%s>' % tag, '')
		if      '\r' in text: text = text.replace('\r',     '')
		if      '  ' in text: text = text.replace('  ',    ' ')
		if    '<br>' in text: text = text.replace('<br>', '\n')
		while '\n\n' in text: text = text.replace('\n\n', '\n')
		text = text.replace('&gt;', '>').replace('&nbsp;', ' ').replace('&#039;', "'").replace('&quot;', '"')
		text = text.strip()
		if text == '': return # Don't log empty posts
		f = open('%s/post.txt' % self.working_dir, 'a')
		f.write('%s\n' % text);
		f.write('--------------------------\n')
		f.close()

