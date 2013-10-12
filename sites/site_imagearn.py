#!/usr/bin/python

from basesite  import basesite
from os        import path
from time      import sleep
from threading import Thread

"""
	Downloads imagearn albums
"""
RETRIES = 4
RETRY_SECOND_MULTIPLIER = 4
class imagearn(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'imagearn.com/' in url:
			raise Exception('')
		elif '/image.php' in url:
			# Find gallery
			r = self.web.get(url)
			gals = self.web.between(r, 'View complete gallery: <a href="', '"')
			if len(gals) == 0:
				raise Exception('No gallery found at URL %s' % url)
			url = 'http://imagearn.com/%s' % gals[0]
		elif not '/gallery.php' in url:
			raise Exception('Required /gallery.php not found')
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		aid = url[url.find('id=')+len('id='):]
		if '&' in aid: aid = aid[:aid.find('&')]
		return 'imagearn_%s' % aid

	def download(self):
		self.init_dir()
		r = self.web.get(self.url)
		# Get images
		links = self.web.between(r, '<a href="image.php?id=', '"')
		for index, link in enumerate(links):
			link = 'http://imagearn.com/image.php?id=%s' % link
			self.download_image(link, index + 1, total=len(links)) 
			if self.hit_image_limit(): break
		self.wait_for_threads()

	""" Checks if file exists, launches downloader thread """
	def download_image(self, url, index, total):
		iid = url[url.find('id=')+3:]
		if '&' in iid: iid = iid[:iid.find('&')]
		saveas = '%s/%03d_%s' % (self.working_dir, index, iid)
		for ext in ['jpg', 'jpeg', 'gif', 'png']:
			if path.exists('%s.%s' % (saveas, ext)):
				self.log('file exists (%d/%d) - %s.%s' % (index, total, saveas, ext))
				return
		while self.thread_count > self.max_threads: sleep(0.1)
		self.thread_count += 1
		args = (url, saveas, index, total)
		t = Thread(target=self.download_image_thread, args=args)
		t.start()
		
	""" Loads image page, finds & downloads image """
	def download_image_thread(self, url, saveas, index, total):
		# Attempt to get image page, retry if necessary
		retries = RETRIES
		for i in xrange(0, retries):
			r = self.web.get(url)
			images = self.web.between(r, '<div id="image"><center><a href="', '"')
			if len(images) == 0: 
				retries -= 1
				if retries == 0:
					self.log('download (%d/%d) FAILED after %d retries - %s' % (index, total, RETRIES, url))
					self.thread_count -= 1
					return
				self.log('download (%d/%d) failed, retrying %d/%d' % (index, total, RETRIES - retries, RETRIES))
				sleep((RETRIES - retries) * RETRY_SECOND_MULTIPLIER) # Linear retry backoff
				continue
			break
		# Download image
		image = images[0]
		extension = image[image.rfind('.'):]
		saveas += extension
		self.save_image(image, saveas, index, total)
		self.thread_count -= 1
	
