#!/usr/bin/python

from basesite import basesite
import re # regex

class shareimage(basesite):
	def sanitize_url(self, url):
		# Verify URL is share-image
		if not 'share-image.com/' in url:
			raise Exception('')
		# Ensure URL points to image-share album
		if not re.compile('^.*share-image\.com\/\d*-?[a-zA-Z0-9\-]*$').match(url):
			raise Exception('required share-image.com/[numbers]-... not found in URL')
		# Strip excess fields from URL
		if '#' in url: url = url[:url.find('#')]
		if '?' in url: url = url[:url.find('?')]
		return url

	def get_dir(self, url):
		gid = url[url.rfind('/')+1:] # Get trailing full gallery name
		gid = gid[:gid.find('-')]    # Strip off trailing gallery name
		return 'shareimage_%s' % gid # Save

	def download(self):
		self.init_dir()
		r = self.web.get(self.url) # Get page source
		thumbs = self.web.between(r, '_self"><img src="', '"') # Extract thumbnail URLs
		for index, thumb in enumerate(thumbs):
			# Convert thumbnail URL to full-size image URL
			full = thumb.replace('pics.share-image.com', 'pictures.share-image.com')
			full = full.replace('/thumb/', '/big/')
			if self.urls_only:
				# User only wants URLs to direct images, not the downloaded images
				self.add_url(index, full, total=total)
			else:
				# Download the image (threaded)
				self.download_image(full, index + 1, total=len(thumbs))
			if self.hit_image_limit(): break # Stop if we hit the maximum number of images
		self.wait_for_threads()            # Wait for existing threads to finish

