#!usr/bin/python

import os   # File exists, mkdir
import time # Sleep
import sys
from threading import Thread
from zipfile   import ZipFile, ZIP_DEFLATED
from Web       import Web

LOG_NAME      = 'log.txt' 
RIP_DIRECTORY = 'rips' # Directory to store rips in
MAX_THREADS   = 3

"""
	Abstract Python 'interface' for a site ripper.
	Each inerhiting/implementing class *must* override:
	 * sanitize_url
	   -- Must raise Exception if given URL is not valid
	 * get_dir
	   -- Must return directory name to download album to
		 -- Usually this is based on the URL/gallery/album name
		 -- Should be unique for every album on site
	 * download
	   -- Retrieves content from URL, downloads albums
	   -- Does not complete until entire album is downloaded
"""
class basesite(object):
	"""
		Constructs object using overriding methods.
		Throws Exception if:
		 * URL is invalid (not appropriate for site class),
		 * Working directory could not be created.
	"""
	def __init__(self, url):
		self.web = Web() # Web object for downloading/parsing
		self.base_dir = RIP_DIRECTORY
		if not os.path.exists(self.base_dir):
			os.mkdir(self.base_dir)
		self.url = self.sanitize_url(url)
		# Directory to store images in
		self.working_dir = '%s%s%s' % (self.base_dir, os.sep, self.get_dir(url))
		if not os.path.exists(self.working_dir) and \
		       self.existing_zip_path() == None:
			os.mkdir(self.working_dir)
		self.max_threads = MAX_THREADS
		self.thread_count = 0
		self.logfile = '%s/%s' % (self.working_dir, LOG_NAME)
		self.first_log = True
	
	""" To be overridden """
	def sanitize_url(self, url):
		raise Exception("Method 'sanitize_url' was not overridden!")

	""" Return directory name to store photos in """
	def get_dir(self, url):
		raise Exception("Method 'get_dir' was not overridden!")
	
	""" To be overridden """
	def download(self):
		raise Exception("Method 'download' was not overridden!")

	""" Checks if album is already being downloaded """
	def is_downloading(self):
		return os.path.exists(self.logfile)
	
	""" Appends line to log file """
	def log(self, text, overwrite=False):
		if self.first_log:
			self.first_log = False
			self.log('http://rip.rarchives.com - file log for URL %s' % self.url, overwrite=True)
		sys.stderr.write('%s\n' % text)
		if overwrite:
			f = open(self.logfile, 'w')
		else:
			f = open(self.logfile, 'a')
		f.write("%s\n" % text)
		f.flush()
		f.close()
	
	""" Gets last line(s) from log """
	def get_log(self, tail_lines=1):
		if not os.path.exists(self.logfile):
			return ''
		f = open(self.logfile, 'r')
		r = f.read().strip()
		f.close()
		while r.endswith('\n'): r = r[:-1]
		lines = r.split('\n')
		return lines[len(lines)-tail_lines:]
	
	""" Starts separate thread to download image from URL """
	def download_image(self, url, index, total='?', subdir=''):
		saveas = url[url.rfind('/')+1:]
		# Strip extraneous / non FS safe characters
		if '?' in saveas: saveas = saveas[:saveas.find('?')]
		if ':' in saveas: saveas = saveas[:saveas.find(':')]
		# Add a file extension if necessary
		if not '.' in saveas:
			m = self.web.get_meta(url)
			ct = 'image/jpeg' # Default to jpg
			if 'Content-Type' in m: ct = m['Content-Type']
			ext = ct[ct.rfind('/')+1:]
			if ext == 'jpeg': ext = 'jpg'
			saveas = '%s.%s' % (saveas, ext)
		# Setup subdirectory saves
		if subdir != '': subdir = '/%s' % subdir
		savedir = '%s%s' % (self.working_dir, subdir)
		if not os.path.exists(savedir): os.mkdir(savedir)
		
		saveas = '%s/%03d_%s' % (savedir, index, saveas)
		if os.path.exists(saveas):
			self.log('file exists: %s' % saveas)
		else:
			while self.thread_count > self.max_threads:
				time.sleep(0.1)
			self.thread_count += 1
			args = (url, saveas, index, total)
			t = Thread(target=self.download_image_thread, args=args)
			t.start()
	
	""" Multi-threaded download of image """
	def download_image_thread(self, url, saveas, index, total):
		m = self.web.get_meta(url)
		if 'Content-Type' not in m or \
			('image' not in m['Content-Type'] and \
			'video' not in m['Content-Type']):
			text = 'no "image"/"video" in Content-Type for URL %s' % (url)
		else:
			if self.web.download(url, saveas):
				text = 'downloaded (%d' % index
				if total != '?': text += '/%s' % total
				text += ') (%s) - %s' % (self.get_size(saveas), url)
			else:
				text = 'download failed (%d' % index
				if total != '?': text += '/%s' % total
				text += ') %s' % url
		self.log(text)
		self.thread_count -= 1
	
	def wait_for_threads(self):
		while self.thread_count > 0:
			time.sleep(0.1)
	
	""" Deconstructor, waits for threads to finish """
	def __del__(self):
		self.wait_for_threads()
	
	""" Returns human-readable filesize for file """
	def get_size(self, filename):
		bytes = os.path.getsize(filename)
		b = 1024 * 1024 * 1024
		a = ['g','m','k','']
		for i in a:
			if bytes >= b:
				return '%.2f%sb' % (float(bytes) / float(b), i)
			b /= 1024
		return '0b'

	
	""" Returns path to zip file if it exists, otherwise None. """
	def existing_zip_path(self):
		zipfile = '%s.zip' % self.working_dir
		if os.path.exists(zipfile):
			return zipfile
		else:
			return None
	
	""" 
		Zips site's working directory,
		Deletes zipped files after zip is created
		Returns path to zip file
	"""
	def zip(self):
		self.log('zipping album...')
		zip_filename = '%s.zip' % self.working_dir
		z = ZipFile(zip_filename, "w", ZIP_DEFLATED)
		for root, dirs, files in os.walk(self.working_dir):
			# NOTE: ignore empty directories
			for fn in files:
				#if 'log.txt' in fn: continue
				absfn = os.path.join(root, fn)
				zfn = absfn[len(self.working_dir)+len(os.sep):] #XXX: relative path
				z.write(absfn, zfn)
		z.close()
		for filename in os.listdir(self.working_dir):
			os.remove('%s%s%s' % (self.working_dir, os.sep, filename))
		os.rmdir(self.working_dir)
		return zip_filename
		

