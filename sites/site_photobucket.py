#!/usr/bin/python

from basesite import basesite

"""
	Downloads photobucket albums
"""
class photobucket(basesite):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'photobucket.com' in url:
			raise Exception('')
		if not '/user/' in url:
			raise Exception('URL must contain /user/')
		self.debug('url before: %s' % url)
		url = url.replace('https://', 'http://')
		if not url.startswith('http://'): url = 'http://%s' % url
		if '?' in url: url = url[:url.find('?')]
		if '#' in url: url = url[:url.find('#')]
		subdir = ''
		if '/library/' in url:
			subdir = url[url.rfind('/library/')+len('/library/'):]
			self.debug('subdir: %s' % subdir)
		if '/profile/' in url:
			url = url[:url.find('/profile/'):] + '/library/'
			url += subdir
		self.debug('url after: %s' % url)
		return url

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = self.web.between(url, '/user/', '/')[0]
		subdir = ''
		if '/library/' in url:
			subdir = url[url.rfind('/library/')+len('/library/'):]
			if subdir != '': subdir = '_%s' % subdir
		self.debug('got directory: "photobucket_%s%s"' % (user, subdir))
		return 'photobucket_%s%s' % (user, subdir)

	def download(self):
		self.init_dir()
		r = self.web.getter(self.url)
		paths = self.web.between(r, "currentAlbumPath: '", "'")
		if len(paths) == 0:
			self.debug('currentAlbumpPath not found')
			paths = self.web.between(r, "setCurrentAlbum('", "'")
		if len(paths) == 0:
			self.debug('setCurrentAlbum not found')
			if 'This is a Private Album' in r:
				self.log('Private album! %s' % self.url)
				return
			self.log('Unable to find currentAlbumPath at %s' % self.url)
			return
		totals = self.web.between(r, '"albumStats":{"images":{"count":', ',')
		if len(totals) > 0 and totals[0].isdigit():
			total = int(totals[0])
			self.debug('total: %s' % total)
		else:
			total = '?'
			self.debug('total not found')
		path = paths[0]
		self.debug('path: %s' % path)
		subpath = path
		if path.count('/') >= 4:
			subpath = '/'.join(path.split('/')[0:3])
		murl = self.url.replace('http://s', 'http://m').replace('.beta.', '.')
		subpath = murl[:murl.find('/user')] + subpath
		subpath = subpath.replace(' ', '%20')
		murl = murl[:murl.find('/user')] + path
		murl = murl.replace(' ', '%20')
		'''http://m579.photobucket.com/albums/ss239/merkler'''
		r = self.web.get(murl)
		# Root album
		self.download_album(subpath, murl, total=total)
		# Subalbums
		albums = self.web.between(r, '<a href="/albums/', '"')
		skip = True
		for albindex, album in enumerate(albums):
			if 'newest=1' in album: continue
			if skip:
				skip = False
				continue
			else:
				skip = True
			if '?' in album: album = album[:album.find('?')]
			murl = murl[:murl.find('/albums/')+len('/albums/')] + album
			name = album.split('/')[1].replace('%20', '-')
			self.download_album(path, murl, name=name)
			
		self.wait_for_threads()
	
	def download_album(self, path, murl, name='', total='?'):
		offset = 0
		index  = 0
		r = self.web.get(murl)
		while True:
			links = self.web.between(r, '<a class="nolink" href="/albumview/', '"')
			for link in links:
				'''path=http://m1069.photobucket.com/albums/u461'''
				'''link=albums/mandymgray/Album%203/2011-12-219514_08_46_.jpg.html'''
				username = link.split('/')[1]
				link = '%s/%s' % (path, '/'.join(link.split('/')[2:])) #[link.rfind('/'):]
				if link.endswith('.html'): link = link[:-5]
				full = self.url[:self.url.rfind('/user')+1].replace('://s', '://i').replace('.beta.', '.')
				full += 'download-albums/'
				dirs = link.replace('://', '').split('/')
				full += dirs[2] + '/' + username + '/'
				if dirs[3] != username:
					full += '/'.join(dirs[3:])
				else:
					full += '/'.join(dirs[4:])
				full = full[:full.rfind('/')+1:] + '.highres' + full[full.rfind('/'):]
				if '?' in full:
					full = full[:full.find('?')]
				'''http://i579.photobucket.com/download-albums/ss239/merkler/.highres/a90a5a9d.jpg'''
				index += 1
				if self.urls_only:
					self.add_url(index, full, total=total)
				else:
					self.download_image(full, index, subdir=name, total=total)
					if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			offset += 4
			if 'href="?o=%d' % offset in r:
				nexturl = murl
				if '?' in nexturl: nexturl += '&'
				else: nexturl += '?'
				nexturl += 'o=%d' % offset
				r = self.web.get(nexturl)
			else:
				break
		
	
