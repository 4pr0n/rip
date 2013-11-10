#!/usr/bin/python

from os   import path, mkdir, listdir, sep, walk, getcwd
from time import sleep, gmtime, mktime
from sys  import stderr
from threading import Thread
from zipfile   import ZipFile, ZIP_DEFLATED
from Web       import Web
from shutil    import rmtree, copy2
from commands  import getstatusoutput
from time      import strftime
from DB        import DB

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
MAX_THUMB_DIM = 4000
MAX_THUMB_SIZE= 5 * 1024 * 1024

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
	def __init__(self, url, debugging=False, ip='127.0.0.1'):
		self.debugging = debugging
		self.web = Web(debugging=self.debugging) # Web object for downloading/parsing
		self.base_dir = RIP_DIRECTORY
		if getcwd().endswith('rips'):
			self.base_dir = '.'
		if not path.exists(self.base_dir):
			mkdir(self.base_dir)
		self.original_url = url
		self.url = self.sanitize_url(url)
		# Directory to store images in
		self.album_name = self.get_dir(self.url)
		self.working_dir  = '%s%s%s' % (self.base_dir, sep, self.album_name)
		self.max_threads  = MAX_THREADS
		self.thread_count = 0
		self.image_count  = 0
		self.max_images   = MAX_IMAGES
		self.logfile      = '%s%s%s' % (self.working_dir, sep, LOG_NAME)
		self.first_log    = True
		self.albumid      = None # Album ID in database
		self.ip           = ip
		self.db = DB()
		self.images_to_add = []
	
	""" To be overridden """
	def sanitize_url(self, url):
		raise Exception("Method 'sanitize_url' was not overridden!")

	""" Return directory name to store photos in """
	def get_dir(self, url):
		raise Exception("Method 'get_dir' was not overridden!")
	
	""" Creates working dir if zip does not exist """
	def init_dir(self):
		if not path.exists(self.working_dir) and \
		       self.existing_zip_path() == None:
			mkdir(self.working_dir)
		try:
			self.add_album_to_db()
		except Exception, e:
			# Album already exists!
			self.debug('got error on %s: %s' % (self.working_dir, str(e)))
			self.albumid = int(self.db.select_one('id', 'albums', 'album = "%s"' % self.album_name))
	
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
		return path.exists(self.logfile)
	
	""" Appends line to log file """
	def log(self, text, overwrite=False):
		if self.first_log:
			self.first_log = False
			self.log('http://rip.rarchives.com - file log for URL %s @ %s' % (self.original_url, strftime('%Y-%m-%dT%H:%M:%S GMT', gmtime())), overwrite=False)
		if self.debugging:
			stderr.write('%s\n' % text)
		text = text.replace('"', '\\"')
		try:
			if overwrite:
				f = open(self.logfile, 'w')
			else:
				f = open(self.logfile, 'a')
			f.write("%s\n" % text)
			f.flush()
			f.close()
		except: pass
	
	""" Gets last line(s) from log """
	def get_log(self, tail_lines=1):
		if not path.exists(self.logfile):
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
		if not path.exists(savedir): mkdir(savedir)
		
		if unique_saveas:
			saveas = '%s/%s' % (savedir, saveas)
		else:
			saveas = '%s/%03d_%s' % (savedir, index, saveas)
		if path.exists(saveas):
			self.log('file exists: %s' % saveas)
			self.image_count += 1
		else:
			while self.thread_count > self.max_threads:
				sleep(0.1)
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
				self.images_to_add.append( (index, saveas, url, thumbnail) )
				text = 'downloaded %s (%s) - source: (%s) thumbnail: (%s)' % (indextotal, self.get_size(saveas), url, thumbnail)
			else:
				text = 'download failed %s - %s' % (indextotal, url)
		self.log(text)
		self.thread_count -= 1

	""" Same-thread downlod/save (does not launch new thread) """
	def save_image(self, url, saveas, index, total='?'):
		indextotal = self.get_index_total(index, total)
		if path.exists(saveas):
			self.image_count += 1
			self.log('file exists: %s' % saveas)
		elif self.web.download(url, saveas):
			self.image_count += 1
			thumbnail = self.create_thumb(saveas)
			self.images_to_add.append( (index, saveas, url, thumbnail) )
			self.log('downloaded %s (%s) - source: (%s) thumbnail: (%s)' % (indextotal, self.get_size(saveas), url, thumbnail))
		else:
			self.log('download failed %s - %s' % (indextotal, url))

	""" 
		Wait for threads to finish downloading.
		Delete working dir if no images are downloaded
	"""
	def wait_for_threads(self):
		while self.thread_count > 0:
			sleep(0.1)
		if path.exists(self.working_dir):
			if len(listdir(self.working_dir)) <= 1:
				rmtree(self.working_dir) # Delete everything in working dir
				return
		for (index, saveas, url, thumbnail) in self.images_to_add:
			self.add_image_to_db(index + 1, saveas, url, thumbnail)
		self.images_to_clear[:] = []
	
	""" Returns human-readable filesize for file """
	def get_size(self, filename):
		try:
			bytes = path.getsize(filename)
		except:
			return '?b'
		return self.bytes_to_hr(bytes)
	
	def bytes_to_hr(self, bytes):
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
		if path.exists(zipfile):
			if not path.exists(self.working_dir):
				# No direcotry; only zip exists
				return zipfile
			else:
				if not path.exists('%s%szipping.txt' % (self.working_dir, sep)):
					# 'zipping' file/flag does not exist
					return zipfile
		return None
	
	""" 
		Zips site's working directory,
		Deletes zipped files after zip is created
		Returns path to zip file
	"""
	def zip(self):
		do_not_zip  = ['zipping.txt', 'complete.txt', 'ip.txt', 'reports.txt']
		not_an_image = ['log.txt']
		self.log('zipping album...')
		zip_filename = '%s.zip' % self.working_dir
		z = ZipFile(zip_filename, "w", ZIP_DEFLATED)
		image_count = 0
		total_size  = 0
		for root, dirs, files in walk(self.working_dir):
			if root.endswith('/thumbs'): continue # Do not zip thumbnails
			for fn in files:
				# Ignore files used by service:
				if fn in do_not_zip: continue
				absfn = path.join(root, fn)
				total_size  += path.getsize(absfn)
				if fn not in not_an_image:
					image_count += 1
				zfn = absfn[len(self.working_dir)+len(sep):] #XXX: relative path
				z.write(absfn, zfn)
		z.close()
		zipsize = path.getsize(zip_filename)
		# Update album with totals
		now = int(mktime(gmtime()))
		query = '''
			update albums
				set
					count    = ?,
					filesize = ?,
					zipsize  = ?,
					accessed = ?,
					complete = 1
				where
					id = ?
			'''
		self.db.execute(query, [image_count, total_size, zipsize, now, self.albumid])
		self.db.commit()
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
			stderr.write('Python Image Library (PIL) not installed; unable to create thumbnail for %s\n' % inp)
			stderr.write('Go to http://www.pythonware.com/products/pil/ to install PIL\n')
			stderr.flush()
			return 'rips/nothumb.png'
		fields = inp.split(sep)
		fields.insert(-1, 'thumbs')
		saveas = sep.join(fields)
		if path.exists(saveas): return ''
		thumbpath = sep.join(fields[:-1])
		if not path.exists(thumbpath):
			try: mkdir(thumbpath)
			except: pass
		try:
			im = Image.open(inp)
			(width, height) = im.size
			if width > MAX_THUMB_DIM or height > MAX_THUMB_DIM:
				# Image too large to create thumbnail
				self.log('unable to create thumbnail, %dx%d > %d' % (width, height, MAX_THUMB_DIM))
				return 'rips/nothumb.png'
			if path.getsize(inp) > MAX_THUMB_SIZE:
				self.log('unable to create thumbnail, %db > %db' % (path.getsize(inp), MAX_THUMB_SIZE))
				return 'rips/nothumb.png'
			if im.mode != 'RGB': im = im.convert('RGB')
			im.thumbnail( (200,200), Image.ANTIALIAS)
			im.save(saveas, 'JPEG')
			return saveas
		except Exception, e:
			self.log('failed to create thumb: %s' % str(e))
			pass
		return 'rips/nothumb.png'

	""" 
		Create thumbnail for video file, uses ffmpeg.
		Returns path to thumbnail or empty string on failure.
	"""
	def create_video_thumb(self, inp):
		fields = inp.split(sep)
		fields.insert(-1, 'thumbs')
		saveas = sep.join(fields)
		saveas = saveas[:saveas.rfind('.')] + '.png'
		thumbpath = sep.join(fields[:-1])
		if not path.exists(thumbpath):
			try: mkdir(thumbpath)
			except: pass
		overlay = 'play_overlay.png'

		ffmpeg = '/usr/bin/ffmpeg'
		if not path.exists(ffmpeg):
			ffmpeg = '/opt/local/bin/ffmpeg'
			if not path.exists(ffmpeg):
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
		stderr.write('%s\n' % text)
	
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

	""" (Correctly) waits for threads to finish before throwing exception """
	def exception(self, e):
		self.wait_for_threads()
		raise Exception(e)

	"""
		Adds album to database, saves album ID
	"""
	def add_album_to_db(self):
		now = int(mktime(gmtime()))
		values = [
				None, # album id
				self.album_name, # album
				0,   # image count
				0,   # size
				0,   # zipsize
				self.ip, # user
				0,   # views
				self.original_url, # source
				0,   # reports
				now, # created
				now, # accessed
				0,   # deleted
				self.logfile, # log
				0    # completed
			]
		self.albumid = self.db.insert('albums', values)
		self.db.commit()

	def add_image_to_db(self, index, image, url, thumb):
		try:
			filetype = self.get_media_type(image)
		except Exception, e:
			self.debug('failed to get file (%s) to DB: %s' % (image, str(e)))

		width = height = 0
		try:
			(width, height) = self.get_dimensions(image)
		except Exception, e:
			# Failed to get dimensions, don't fail completely.
			pass

		filesize = path.getsize(image)
		if image.startswith('rips/'): image = './%s' % image[5:]
		if thumb.startswith('rips/'): thumb = './%s' % thumb[5:]
		values = [
				None,    # image id
				self.albumid, # album id
				index,   # number in album
				image,   # image path
				url,     # source
				width,   # dimensions
				height,
				filesize,# image filesize
				thumb,   # thumbnail path
				filetype # image/video/etc
			]
		self.db.insert('images', values)
		self.db.commit()

	def get_media_type(self, filename):
		ext = filename.lower()[-4:]
		if ext in ['.mp4', '.flv']:
			return 'video'
		elif ext in ['.jpg', 'jpeg', '.gif', '.png']:
			return 'image'
		elif ext in ['.txt']:
			return 'text'
		elif ext in ['html']:
			return 'html'
		raise Exception('unknown file type: %s (in %s)' % (ext, filename))

	def get_dimensions(self, image):
		if image.lower()[-4:] in ['.mp4', '.flv']:
			ffmpeg = '/usr/bin/ffmpeg'
			if not path.exists(ffmpeg):
				ffmpeg = '/opt/local/bin/ffmpeg'
				if not path.exists(ffmpeg):
					raise Exception('ffmpeg not found; unable to get video dimensions')
			(status, output) = getstatusoutput('%s -i "%s"' % (ffmpeg, image))
			for line in output.split('\n'):
				if 'Stream' in line and 'Video:' in line:
					line = line[line.find('Video:')+6:]
					fields = line.split(', ')
					dims = fields[2]
					if not 'x' in dims: raise Exception('invalid video dimensions')
					(width, height) = dims.split('x')
					if ' ' in height: height = height[:height.find(' ')]
					try:
						width  = int(width)
						height = int(height)
					except:
						raise Exception('invalid video dimensions: %sx%s' % (width, height))
					return (width, height)
			raise Exception('unable to get video dimensions')
		else:
			im = Image.open(image)
			return im.size

	''' Adds album that already exists on filesystem to database '''
	def add_existing_album_to_db(self):
		try:
			self.add_album_to_db()
		except: pass
		zipfile = '%s.zip' % self.working_dir
		if not path.exists(zipfile):
			self.zip()
		zipsize = path.getsize('%s.zip' % self.working_dir)
		image_count = 0
		images = []
		thumbs = []
		for root, subdirs, files in walk(self.working_dir):
			for fn in files:
				if fn.endswith('.txt') or fn.endswith('.html'): continue
				if root.endswith('/thumbs'):
					thumbs.append(path.join(root, fn))
				else:
					images.append(path.join(root, fn))
		images.sort()
		thumbs.sort()
		if len(images) != len(thumbs):
			print '# of images != # of thumbs'
			print images
			print thumbs
			return
		total_size = 0
		for i in xrange(0, len(images)):
			self.add_image_to_db(i, images[i], '', thumbs[i])
			total_size += path.getsize(images[i])
		now = int(mktime(gmtime()))
		query = '''
			update albums
				set
					count    = ?,
					filesize = ?,
					zipsize  = ?,
					accessed = ?,
					complete = 1
				where
					id = ?
			'''
		self.db.execute(query, [len(images), total_size, zipsize, now, self.albumid])
		self.db.commit()

	def add_recent(self, ip):
		self.db.add_recent(self.original_url, self.album_name, ip)

if __name__ == '__main__':
	# Test the base site functionality
	#url = 'http://seenive.com/u/911429150038953984'
	url = 'http://imgur.com/a/RdXNa'
	import site_seenive, site_imgur
	bs = site_imgur.imgur(url, debugging=True)
	bs.debug('deleting')
	bs.db.delete_album(bs.album_name, blacklist=False, delete_files=False)
	bs.debug('adding')
	bs.add_existing_album_to_db()
	'''
	# Download & zip
	bs.download()
	bs.zip()
	# Dump the whole database
	curexec = bs.db.execute('select * from albums where source = "%s"' % url)
	for tup in curexec:
		for field in tup:
			print field,
		print ''
		print 'executing: select * from images where album = %d order by path asc' % tup[0]
		iexec = bs.db.execute('select * from images where album = %d order by path asc' % tup[0])
		for image in iexec:
			print '\t',
			for field in image:
				print field,
			print ''
	# Delete album from filesystem and database
	#bs.db.delete_album(bs.album_name, blacklist=True)
	'''

