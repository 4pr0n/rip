#!/usr/bin/python

# 'basesite.py' contains lots of functionality required for a ripper
from basesite import basesite

"""
	Example class for ripping sites.
	
	Contains skeleton code for creating a new ripper.
	
	Inherits functionality from abstract 'basesite' super-class
	
	We have to override:
	 * sanitize_url() - Ensures URL is rippable, alters URL as needed
	 * get_dir()      - Creates unique working directory for album
	 * download()     - Downloads images from the album
	
	There's lots of helpful methods, such as:
	 * self.log()              - writes text to 'log.txt'
	 * self.debug()            - prints text to stderr (only when debugging is enabled)
	 * self.download_image()   - downloads an image using threads
	 * self.wait_for_threads() - waits for threads to finish
	 * self.hit_image_limit    - True if we hit the max number of images
	 * self.get_size()         - gets size of a file (in bytes)
	 * self.create_thumb()     - creates thumbnail of a file
	 * self.add_url()          - adds url to log; only used when urls_only is True
	
	And helpful fields:
	 * self.url          - URL of album to be downloaded - set by sanitize_url()
	 * self.working_dir  - working directory for this album - set by get_dir()
	 * self.urls_only    - True if user only wants URLs
	 * self.max_threads  - maximum number of threads to run at one time
	 * self.thread_count - current number of threads running
"""
class testsite(basesite):
	

	""" Verify [and alter] URL to an acceptable format """
	def sanitize_url(self, url):
		# If this site isn't in the URL, pass an empty exception
		# This tells the main script to move onto the next ripper
		if not 'testsite.com/' in url:
			raise Exception('')
		
		# If this ripper requires a specific URL, ensure we have that.
		# Ex: We might require the URL contains "?galleryid=" or something like that
		if not '/something/' in url:
			raise Exception('required /something/ not found in URL')

		# Strip hashtags and query strings from URL
		# Ex: http://site.com/galleryid#image becomes http://site.com/galleryid
		if '#' in url: url = url[:url.find('#')]
		if '?' in url: url = url[:url.find('?')]
		
		# Return the properly-formatted URL
		return url
		# This URL is stored in self.url


	""" Discover directory path based on URL """
	def get_dir(self, url):
		# We need to return the directory name for this specific album
		# We can enforce that the URL contains specific strings
		#   within the sanitize_url() method.
		
		# For example, http://site.com/012345
		# 012345 is a unique album id, it's specific to one album
		
		# Get gallery ID after the last / in the URL
		galleryid = url[url.rfind('/')+1:]
		
		# Return the site prefix + the unique gallery name
		return 'testsite_%s' % galleryid


	""" Download images in album """
	def download(self):
		
		# Create & initialize working directory
		self.init_dir()

		# Get webpage source
		r = self.web.get(self.url)

		# Example "logging" statement, written to log.txt
		#   and included in the archive once completed.
		self.log('loading %s' % self.url)
		
		# Find all links on page
		links = self.web.between(r, '<a href="', '"')
		
		# Iterate over links
		for index, link in enumerate(links):
			if self.urls_only:
				# User only wants URLs to direct images, not the downloaded images
				self.add_url(index, img, total=total)
			else:
				# Download the image (threaded)
				self.download_image(link, index + 1, total=len(links))
			# Stop if we hit the maximum number of images
			if self.hit_image_limit(): break

		# Wait for existing threads to finish
		# Also, delete working directory if album could not be downloaded
		self.wait_for_threads()

