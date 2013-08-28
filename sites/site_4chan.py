#!/usr/bin/python

from basesite import basesite
from os import path, remove
from json import loads
from unicodedata import normalize

"""
	Rips images from an 4chan post.
	Also archives the text from the post
"""
class fourchan(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not '4chan.org/' in url:
			raise Exception('')
		if not '/res/' in url:
			raise Exception('required /res/ not found in URL')
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		url = url[url.find('4chan.org/'):]
		dirs = url.split('/')
		if len(dirs) != 4 or dirs[2] != 'res':
			raise Exception('required format: http://4chan.org/<board>/res/#')
		number = dirs[3]
		if '+' in number:
			number = number[:number.find('+')] + number[number.rfind('.'):]
		return 'http://api.%s/%s.json' % ('/'.join(dirs[:3]), number)

	""" Discover directory path based on URL """
	def get_dir(self, url):
		u = url.replace('http://', '')
		dirs = u.split('/')
		board = dirs[1]
		number = dirs[3][:dirs[3].find('.')]
		return '4chan_%s_%s' % (board, number)

	""" Rip images & archive text post """
	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		board = self.url.replace('://', '').split('/')[1]
		
		try:
			json = loads(r)
			total = len(json['posts'])
		except:
			self.wait_for_threads()
			raise Exception('failure when parsing json at %s' % self.url)
		
		for index, post in enumerate(json['posts']):
			if 'tim' in post and 'ext' in post:
				link = 'http://images.4chan.org/%s/src/%s%s' % (board, post['tim'], post['ext'])
				if self.urls_only:
					self.add_url(index + 1, link, total=len(json['posts']))
				else:
					self.download_image(link, index + 1, total=len(json['posts']), saveas='%s%s' % (post['tim'], post['ext']))
					if self.hit_image_limit(): break
		
		# Save thread
		f = open('%s/thread.html' % self.working_dir, 'w')
		f.write(self.json_to_text(json))
		f.close()
		
		self.wait_for_threads()
	
	def safe(self, text):
		''' Safely encode unicode strings '''
		result = ''
		if type(text) == unicode:
			result = normalize('NFKD', text).encode('ascii', 'ignore')
		else:
			result = text
		return result
	
	def json_to_text(self, json):
		out  = '<!doctype html>'
		out += '<html><head>'
		out += '<style>'
		out += 'body { background: #FFFFEE; color: rgb(128, 0, 0); margin-top: 40px; margin-bottom: 20px; font-family: arial,helvetica,sans-serif; font-size: 10pt; }'
		out += 'a,a:visited { color: #00E; }'
		out += 'a:hover { color: red; }'
		out += 'span,div { font-size: 10pt; }'
		out += 'div { display: table; padding: 0px; margin: 0px; }'
		out += 'div.first { margin-left: 5px; }'
		out += 'span.sub { color: rgb(204, 17, 5); font-weight: 700 }'
		out += 'input { padding: 0px; margin: 0px; font-size: 10pt; }'
		
		out += 'div.arrows { width: 20px; font-size: 10pt; color: rgb(224, 191, 183); }'
		out += 'td.reply { text-align: left; vertical-align: top; }'
		out += 'div.reply { padding-left: 10px; padding-right: 20px; background: #f0e0d6; margin: 3px; }'
		out += 'span.name { color: rgb(17, 119, 67); font-weight: 700; }'
		
		out += 'div.com { padding-top: 10px; padding-left: 5px; font-size: 13.3333px; }'
		out += 'span.quote { color: rgb(120, 153, 34); }'
		out += 'span.deadlink { color: rgb(0, 0, 128); text-decoration: line-through; }'
		out += 'span.quotelink { color: rgb(255, 0, 0); }'
		out += '</style>'
		out += '<body>'
		for index, post in enumerate(json['posts']):
			if 'sub' in post:
				# First post
				out += '<div class="first">'
				out += self.file_info(post)
				out += '<table><tr><td class="reply">'
				out += '<a href="%s%s" target="_BLANK">' % (post['tim'], post['ext'])
				out += '<img src="%s%s" width="%d" height="%d">' % (post['tim'], post['ext'], post['tn_w'], post['tn_h'])
				out += '</a>'
				out += '</td><td class="reply">'
				out += self.post_info(post)
				out += self.text_reply(post)
			else:
				out += '<table><tr><td class="reply"><div class="arrows">&gt;&gt;</div></td><td><div class="reply">'
				out += self.post_info(post)
				out += self.file_info(post)
				out += '<table><tr>'
				if 'tim' in post:
					# Image
					out += '<td>'
					out += '<a href="%s%s" target="_BLANK">' % (post['tim'], post['ext'])
					out += '<img src="%s%s" width="%d" height="%d">' % (post['tim'], post['ext'], post['tn_w'], post['tn_h'])
					out += '</a>'
					out += '</td>'
				# Text
				out += '<td class="reply">'
				out += self.text_reply(post)
				out += '</td></tr></table>'
				out += '</div>'
			out += '</td></tr></table>'
		out += '</div></body></html>'
		return out
	
	def post_info(self, post):
		# Anchor
		header = '<a name="p%d"></a>' % post['no']
		header += '<table><tr><td><input type="checkbox" /></td><td>'
		# Name & time
		header += '<div class="postInfo">'
		if 'sub' in post:
			header += '<span class="sub">%s</span> ' % self.safe(post['sub'])
		header += '<span class="name">%s</span> ' % self.safe(post['name'])
		header += '%s No. %d' % (post['now'], post['no'])
		header += '</div>'
		header += '</td></tr></table>'
		return header
	
	def file_info(self, post):
		if not 'tim' in post: return ''
		out = '<div class="fileInfo">'
		out += 'File: <a href="%s%s">%s%s</a>' % (post['tim'], post['ext'], post['tim'], post['ext'])
		out += '-(%s, %dx%d, %s%s)' % (str(post['fsize']), post['w'], post['h'], self.safe(post['filename']), post['ext'])
		out += '</div>'
		return out

	def text_reply(self, post):
		if not 'com' in post: return ''
		out = '<div class="com">'
		
		com = self.safe(post['com'])
		com = com.replace('%d#' % post['resto'], '#')
		out += com
		
		out += '</div>'
		return out

