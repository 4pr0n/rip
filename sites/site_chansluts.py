#!/usr/bin/python

from basesite import basesite
from os import path, remove

"""
	Rips images from chansluts post.
	Also archives the text from the post
"""
class chansluts(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'chansluts.com/' in url:
			raise Exception('')
		if not '/res/' in url:
			raise Exception('required /res/ not found in URL')
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		url = url[url.find('chansluts.com/'):]
		dirs = url.split('/')
		if len(dirs) < 2 or dirs[-2] != 'res':
			raise Exception('required format: http://chansluts.com/.../res/&lt;id&gt;.php')
		return 'http://www.chansluts.com/%s' % '/'.join(dirs[1:])

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = url.replace('http://', '')
		dirs = u.split('/')
		dirs.remove('res')
		dirs[-1] = dirs[-1].replace('.php', '')
		return 'chansluts_%s' % ('_'.join(dirs[1:]))

	""" Rip images & archive text post """
	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		
		if path.exists('%s/post.txt' % self.working_dir):
			remove('%s/post.txt' % self.working_dir)
		if not self.urls_only:
			self.log_post('http://rip.rarchives.com - text log from %s\n' % self.url)
		
		chunk = self.web.between(r, '<form id="delform"', '</form>')[0]
		posts = self.web.between(r, 'daposts">', '</div> </div> </div>')
		for index, post in enumerate(posts):
			imgs = self.web.between(post, 'href="', '"')
			if len(imgs) > 0 and 'javascript:' not in imgs[0]:
				link = 'http://www.chansluts.com%s' % imgs[0]
				if self.urls_only:
					self.add_url(index + 1, link, total=len(posts))
				else:
					self.download_image(link, index + 1, total=len(posts))
					if self.hit_image_limit(): break
			
			if 'class="comment">' in post:
				comment = post[post.find('class="comment">')+len('class="comment">'):]
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

