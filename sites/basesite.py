#!/usr/bin/python

import os   # fs: exists, mkdir, listdir, rmdir
import time # Sleep
import sys
from threading import Thread
from zipfile   import ZipFile, ZIP_DEFLATED
from Web       import Web
from shutil    import rmtree
from PIL       import Image

LOG_NAME      = 'log.txt' 
RIP_DIRECTORY = 'rips' # Directory to store rips in
MAX_THREADS   = 3
MAX_IMAGES    = 1000

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
	def __init__(self, url, urls_only=False, debugging=False):
		self.debugging = debugging
		self.web = Web(debugging=self.debugging) # Web object for downloading/parsing
		self.base_dir = RIP_DIRECTORY
		if not os.path.exists(self.base_dir):
			os.mkdir(self.base_dir)
		self.url = self.sanitize_url(url)
		# Directory to store images in
		self.working_dir  = '%s%s%s' % (self.base_dir, os.sep, self.get_dir(self.url))
		self.max_threads  = MAX_THREADS
		self.thread_count = 0
		self.image_count  = 0
		self.max_images   = MAX_IMAGES
		self.logfile      = '%s%s%s' % (self.working_dir, os.sep, LOG_NAME)
		self.first_log    = True
		self.urls_only    = urls_only
	
	""" To be overridden """
	def sanitize_url(self, url):
		raise Exception("Method 'sanitize_url' was not overridden!")

	""" Return directory name to store photos in """
	def get_dir(self, url):
		raise Exception("Method 'get_dir' was not overridden!")
	
	""" Creates working dir if zip does not exist """
	def init_dir(self):
		if not os.path.exists(self.working_dir) and \
		       self.existing_zip_path() == None:
			os.mkdir(self.working_dir)
	
	""" Returns true if we hit the image limit, false otherwise """
	def hit_image_limit(self):
		return self.image_count >= self.max_images
	
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
		if self.debugging:
			sys.stderr.write('%s\n' % text)
		text = text.replace('"', '\\"')
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
	def download_image(self, url, index, total='?', subdir='', saveas=None):
		unique_saveas = True
		if saveas == None:
			unique_saveas = False
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
		
		if unique_saveas:
			saveas = '%s/%s' % (savedir, saveas)
		else:
			saveas = '%s/%03d_%s' % (savedir, index, saveas)
		if os.path.exists(saveas):
			self.log('file exists: %s' % saveas)
			self.image_count += 1
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
		if 'Content-Type' not in m:
			text = 'no Content-Type found at URL %s' % (url)
		elif ('image'        not in m['Content-Type'] and \
		      'video'        not in m['Content-Type'] and \
		      'octet-stream' not in m['Content-Type']):
			text = 'no "image"/"video"/"octet-stream" in Content-Type (found "%s") for URL %s' % (m['Content-Type'], url)
		else:
			if self.web.download(url, saveas):
				self.image_count += 1
				text = 'downloaded (%d' % index
				if total != '?': text += '/%s' % total
				text += ') (%s) - %s' % (self.get_size(saveas), url)
				# Create thumbnail
				self.create_thumb(saveas)
			else:
				text = 'download failed (%d' % index
				if total != '?': text += '/%s' % total
				text += ') - %s' % url
		self.log(text)
		self.thread_count -= 1
	
	def wait_for_threads(self):
		while self.thread_count > 0:
			time.sleep(0.1)
		if os.path.exists(self.working_dir):
			if not self.urls_only and len(os.listdir(self.working_dir)) <= 1 \
					or self.urls_only and len(os.listdir(self.working_dir)) == 0:
				rmtree(self.working_dir) # Delete everything in working dir
	
	""" Returns human-readable filesize for file """
	def get_size(self, filename):
		try:
			bytes = os.path.getsize(filename)
		except:
			return '?b'
		b = 1024 * 1024 * 1024
		a = ['g','m','k','']
		for i in a:
			if bytes >= b:
				return '%.2f%sb' % (float(bytes) / float(b), i)
			b /= 1024
		return '0b'

	""" Returns path to zip file if it exists, otherwise None. """
	def existing_zip_path(self):
		if self.urls_only:
			txtfile = '%s.txt' % self.working_dir
			f = txtfile.split('/')
			f.insert(-1, 'txt')
			txtfile = '/'.join(f)
			if os.path.exists(txtfile):
				return txtfile
			return None
		zipfile = '%s.zip' % (self.working_dir)
		if os.path.exists(zipfile):
			if not os.path.exists(self.working_dir):
				# No direcotry; only zip exists
				return zipfile
			else:
				if not os.path.exists('%s%szipping.txt' % (self.working_dir, os.sep)):
					# 'zipping' file/flag does not exist
					return zipfile
		return None
	
	""" 
		Zips site's working directory,
		Deletes zipped files after zip is created
		Returns path to zip file
	"""
	def zip(self):
		if self.urls_only:
			# Just URLs, need to store in order & store to a .txt file
			if not os.path.exists('%s/log.txt' % self.working_dir):
				raise Exception('no log found')
			if not os.path.exists('txt/'):
				try: os.mkdir('txt')
				except: pass
			f = self.working_dir.split('/')
			f.insert(-1, 'txt')
			url_filename = '%s.txt' % '/'.join(f)
			f = open('%s/log.txt' % self.working_dir, 'r')
			lines = f.read().split('\n')[1:]
			tuples = []
			for line in lines:
				if line.strip() == '' or ' - ' not in line: continue
				if line.count('|') < 1: continue
				line = line[line.find(' - ')+3:]
				splits = line.split('|')
				index  = splits[0]
				url    = '|'.join(splits[1:])
				tuples.append( (index, url) )
			tuples = sorted(tuples, key=lambda tup: int(tup[0]))
			f = open(url_filename, 'w')
			for (index, url) in tuples:
				f.write('%s\n' % url)
			f.close()
			rmtree(self.working_dir) # Delete everything in working dir
			return url_filename
		
		self.log('zipping album...')
		zip_filename = '%s.zip' % self.working_dir
		z = ZipFile(zip_filename, "w", ZIP_DEFLATED)
		for root, dirs, files in os.walk(self.working_dir):
			# NOTE: ignore empty directories & thumbnails
			if root.endswith('/thumbs'): continue
			for fn in files:
				#if 'log.txt' in fn: continue
				if fn.endswith('zipping.txt'): continue
				if fn.endswith('complete.txt'): continue
				absfn = os.path.join(root, fn)
				zfn = absfn[len(self.working_dir)+len(os.sep):] #XXX: relative path
				z.write(absfn, zfn)
		z.close()
		#rmtree(self.working_dir) # Delete everything in working dir
		return zip_filename

	"""
		Creates thumbnail based on file path
		Creates /thumbs/ sub dir & stores thumbnail
	"""
	def create_thumb(self, inp):
		fields = inp.split(os.sep)
		fields.insert(-1, 'thumbs')
		saveas = os.sep.join(fields)
		if os.path.exists(saveas): return
		thumbpath = os.sep.join(fields[:-1])
		if not os.path.exists(thumbpath):
			try: os.mkdir(thumbpath)
			except: pass
		try:
			im = Image.open(inp)
			if im.mode != 'RGB': im = im.convert('RGB')
			im.thumbnail( (200,200), Image.ANTIALIAS)
			im.save(saveas, 'JPEG')
			del im
		except: pass
		
	"""
		Add url to list of URLs found. For "URLs Only" feature
	"""
	def add_url(self, index, url, total=0):
		self.image_count += 1
		string = '(%d' % index
		if total > 0:
			string += '/%d' % total
		string += ')'
		self.log('%s - %d|%s' % (string, index, url))

	def debug(self, text):
		if not self.debugging: return
		sys.stderr.write('%s\n' % text)

