#!/usr/bin/python

from basesite  import basesite
from time      import sleep
from threading import Thread

class gallerydump(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'gallery-dump.com/' in url:
			raise Exception('')
		if not 'gid=' in url:
			raise Exception('required gid= not found in URL')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		gid = url[url.rfind('gid=')+4:]
		if '/' in gid: gid = gid[:gid.find('/')]
		if '?' in gid: gid = gid[:gid.find('?')]
		if '#' in gid: gid = gid[:gid.find('#')]
		return 'gallerydump_%s' % gid

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		links = self.web.between(r, 'rel="nofollow" href="', '"')
		for index, link in enumerate(links):
			self.trigger_image_download(link, index + 1, len(links))
			if self.hit_image_limit(): break
		self.wait_for_threads()
	
	def trigger_image_download(self, url, index, total):
		while self.thread_count >= self.max_threads:
			sleep(0.1)
		self.thread_count += 1
		args = (url, index, total)
		t = Thread(target=self.handle_link, args=args)
		t.start()
		
	
	def handle_link(self, url, img_index, total):
		# <domain>/img-<ID> - requires POST and 'centred'
		# or not, imgonion is the exception?
		# Check for linkbucks
		self.debug('url: %s' % url)
		u = url
		u = u.replace('http://', '')
		if u.count('/') == 0 or u[u.find('/')+1:].strip() == '':
			# Linkbucks!
			self.debug('looks like linkbucks: %s' % url)
			sleep(5)
			r = self.web.get(url)
			if "TargetUrl = '" in r:
				f = open('wtf.txt', 'w')
				f.write(r)
				f.close()
				url = self.web.between(r, "TargetUrl = '", "'")[0]
				self.debug('it was linkbucks, new url: %s' % url)
			else:
				self.debug('could not find TargetUrl at %s' % url)
		
		post = None
		index = 0
		if 'imagetwist.com' in url:
			before = 'auto;"><img src="'
			after  = '"'
		elif 'imgdino.com' in url:
			before = 'scale(this);" src="'
			after  = '"'
		elif 'imgchili.com' in url or 'imgchili.net' in url:
			before = '     src="'
			after  = '"'
		elif 'imgmoney.com' in url:
			before = "' src='"
			after  = "'"
			post   = 'imgContinue=Continue+to+image+...+'
		elif 'imageporter.com' in url:
			before = '()" ><img src="'
			after  = '"'
		elif 'imgtiger.com' in url:
			before = '><img src="'
			after  = '"'
			index  = 1
		elif 'imgcloud.co' in url:
			before = "' src='"
			after  = "'"
			post   = 'imgContinue=Continue+to+image+...+'
		elif 'imgserve.net' in url:
			before = "' src='"
			after  = "'"
			index  = 1
		elif 'imagefolks.com' in url.lower():
			before = "'centred' src='"
			after  = "'"
			post   = 'imgContinue=Continue+to+image+...+'
		elif 'imgonion.com' in url:
			before = "resized' src='"
			after  = "'"
			post   = 'imgContinue=Click+if+you+are+human'
		elif 'imgbunk.com' in url:
			before = '<br><img src="'
			after  = '"'
			r = self.web.get(url)
			post = ''
			for chunk in self.web.between(r, 'type="hidden" name="', '>'):
				fields = chunk.split('"')
				key = fields[0]
				value = fields[2]
				if post != '': post += '&'
				post += '%s=%s' % (key, value)
			post += '&method_free=%0D%0A%0D%0AI%27m+a+human.+I+promise.+Take+me+to+the+image+please%21%0D%0A%0D%0A+'
			#post = 'op=download1&usr_login=&id=hoitgeby3ttm&fname=171381806.jpg&referer=&method_free=%0D%0A%0D%0AI%27m+a+human.+I+promise.+Take+me+to+the+image+please%21%0D%0A%0D%0A+'
		elif 'imgtube.net' in url:
			before = "' src='"
			after  = "'"
			post   = 'imgContinue=Continue+to+image+...+'
		elif 'imgah.com' in url:
			before = 'class="pic" src="'
			after  = '"'
		elif 'imagefap.com' in url:
			before = '" src="'
			after  = '"'
			index  = 4
			'''
		elif 'imgcandy.com' in url:
			before = ''
			after  = ''
			'''
		else:
			self.debug('do not know how to handle %s' % url)
			self.thread_count -= 1
			return
		# TODO remove!
		'''
		if 'imgserve.net' in url: return
		if 'imgdino'      in url: return
		if 'imgmoney.com' in url: return
		if 'imagetwist.com' in url: return
		if 'imagefolks.com' in url.lower(): return
		if 'imgcloud.co' in url: return
		if 'imgtiger.com' in url: return
		if 'imgonion.com' in url: return
		if 'imgbunk.com' in url: return
		if 'imgchili.net' in url: return
		if 'imgtube.net' in url: return
		if 'imagefap.com' in url: return
		if 'imageporter.com' in url: return
		'''
		
		if post != None:
			self.debug('posting %s to %s' % (post, url))
			r = self.web.oldpost(url, postdict=post)
		else:
			self.debug('getting %s' % url)
			r = self.web.get(url)

		self.thread_count -= 1
		
		if not before in r: 
			self.debug('could not find "%s" in response' % before)
			return
		if not after in r:
			self.debug('could not find "%s" in response' % after)
			return
		images = self.web.between(r, before, after)
		if index >= len(images):
			self.debug('image index %d larger than image count %d' % (index, len(images)))
			return
		image = images[index]
		# Kick off a new thread to get the image
		self.download_image(image, img_index, total)
		
