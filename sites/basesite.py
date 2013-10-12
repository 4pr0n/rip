#!/usr/bin/python

import os   # fs: exists, mkdir, listdir, rmdir
import time # Sleep
import sys
from threading import Thread
from zipfile   import ZipFile, ZIP_DEFLATED
from Web       import Web
from shutil    import rmtree
from commands  import getstatusoutput
from time      import strftime

# Try to import Python Image Library
try:
	from PIL     import Image
except ImportError:
	# Python Image Library not installed, no thumbnail support
	Image = None

LOG_NAME      = 'log.txt' 
RIP_DIRECTORY = 'rips' # Directory to store rips in
MAX_THREADS   = 3
MAX_IMAGES    = 500

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
	def __init__(self, url, debugging=False):
		self.debugging = debugging
		self.web = Web(debugging=self.debugging) # Web object for downloading/parsing
		self.base_dir = RIP_DIRECTORY
		if not os.path.exists(self.base_dir):
			os.mkdir(self.base_dir)
		self.original_url = url
		self.url = self.sanitize_url(url)
		# Directory to store images in
		self.working_dir  = '%s%s%s' % (self.base_dir, os.sep, self.get_dir(self.url))
		self.max_threads  = MAX_THREADS
		self.thread_count = 0
		self.image_count  = 0
		self.max_images   = MAX_IMAGES
		self.logfile      = '%s%s%s' % (self.working_dir, os.sep, LOG_NAME)
		self.first_log    = True
	
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
		if self.image_count >= self.max_images:
			self.log('hit image limit: %d >= %d' % (self.image_count, self.max_images))
			return True
		return False
	
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
			self.log('http://rip.rarchives.com - file log for URL %s @ %s' % (self.original_url, strftime('%Y-%m-%dT%H:%M:%S PDT')), overwrite=False)
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
			text = 'no image/video/octet-stream in Content-Type (found "%s") for URL %s' % (m['Content-Type'], url)
		else:
			indextotal = self.get_index_total(index, total)
			if self.web.download(url, saveas):
				self.image_count += 1
				# Create thumbnail
				thumbnail = self.create_thumb(saveas)
				text = 'downloaded %s (%s) - source: (%s) thumbnail: (%s)' % (indextotal, self.get_size(saveas), url, thumbnail)
			else:
				text = 'download failed %s - %s' % (indextotal, url)
		self.log(text)
		self.thread_count -= 1

	""" Same-thread downlod/save (does not launch new thread) """
	def save_image(self, url, saveas, index, total='?'):
		indextotal = self.get_index_total(index, total)
		if os.path.exists(saveas):
			self.image_count += 1
			self.log('file exists: %s' % saveas)
		elif self.web.download(url, saveas):
			self.image_count += 1
			thumbnail = self.create_thumb(saveas)
			self.log('downloaded %s (%s) - source: (%s) thumbnail: (%s)' % (indextotal, self.get_size(saveas), url, thumbnail))
		else:
			self.log('download failed %s - %s' % (indextotal, url))

	""" 
		Wait for threads to finish downloading.
		Delete working dir if no images are downloaded
	"""
	def wait_for_threads(self):
		while self.thread_count > 0:
			time.sleep(0.1)
		if os.path.exists(self.working_dir):
			if len(os.listdir(self.working_dir)) <= 1:
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

	""" 
		Returns path to zip file if it exists, otherwise None.
		Does not return path if zipping is in progress.
	"""
	def existing_zip_path(self):
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
		self.log('zipping album...')
		zip_filename = '%s.zip' % self.working_dir
		z = ZipFile(zip_filename, "w", ZIP_DEFLATED)
		for root, dirs, files in os.walk(self.working_dir):
			if root.endswith('/thumbs'): continue # Do not zip thumbnails
			for fn in files:
				# Ignore files used by service:
				if fn.endswith('zipping.txt'):  continue # Album is currently zipping
				if fn.endswith('complete.txt'): continue # Album download completed
				if fn.endswith('ip.txt'):       continue # IP address of ripper
				if fn.endswith('reports.txt'):  continue # Number of reports, report messages
				absfn = os.path.join(root, fn)
				zfn = absfn[len(self.working_dir)+len(os.sep):] #XXX: relative path
				z.write(absfn, zfn)
		z.close()
		return zip_filename

	"""
		Creates thumbnail based on file path.
		Creates /thumbs/ sub dir & stores thumbnail.
		Returns thumbnail path on success, empty string on failure.
	"""
	def create_thumb(self, inp):
		if inp.lower().endswith('.mp4'):
			return self.create_video_thumb(inp)
		if Image == None:
			sys.stderr.write('Python Image Library (PIL) not installed; unable to create thumbnail for %s\n' % inp)
			sys.stderr.write('Go to http://www.pythonware.com/products/pil/ to install PIL\n')
			sys.stderr.flush()
			return ''
		fields = inp.split(os.sep)
		fields.insert(-1, 'thumbs')
		saveas = os.sep.join(fields)
		if os.path.exists(saveas): return ''
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
			return saveas
		except: pass
		return ''

	""" 
		Create thumbnail for video file, uses ffmpeg.
		Returns path to thumbnail or empty string on failure.
	"""
	def create_video_thumb(self, inp):
		fields = inp.split(os.sep)
		fields.insert(-1, 'thumbs')
		saveas = os.sep.join(fields)
		saveas = saveas[:saveas.rfind('.')] + '.png'
		thumbpath = os.sep.join(fields[:-1])
		if not os.path.exists(thumbpath):
			try: os.mkdir(thumbpath)
			except: pass
		overlay = 'play_overlay.png'

		ffmpeg = '/usr/bin/ffmpeg'
		if not os.path.exists(ffmpeg):
			ffmpeg = '/opt/local/bin/ffmpeg'
			if not os.path.exists(ffmpeg):
				return '' # Can't get images if we can't find ffmpeg
		cmd = ffmpeg
		cmd += ' -i "'
		cmd += inp
		cmd += '" -vf \'movie='
		cmd += overlay
		cmd += ' [watermark]; '
		cmd += '[in]scale=200:200 [scale]; '
		cmd += '[scale][watermark] overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2 [out]\' '
		cmd += saveas
		try:
			(s, o) = getstatusoutput(cmd)
			return saveas
		except:
			pass
		return ''

	""" Print text to stderr, only if debugging is enabled """
	def debug(self, text):
		if not self.debugging: return
		sys.stderr.write('%s\n' % text)
	
	""" Remove excess / unnecessary characters from URL """
	def strip_url(url):
		for c in ['?', '#', '&']:
			if c in url: url = url[:url.find(c)]
		return url

	""" Return current index / total (in parenthesis), formatted properly """
	def get_index_total(self, index, total):
		countmsg = '(%s' % str(index)
		if total == '?':
			countmsg += ')'
		else:
			countmsg += '/%s)' % str(total)
		return countmsg
