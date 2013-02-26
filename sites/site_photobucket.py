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
		url = url.replace('https://', 'http://')
		if not url.startswith('http://'): url = 'http://%s' % url
		subdir = ''
		if '/library/' in url:
			subdir = url[url.rfind('/library/')+len('/library/'):]
		if '/profile/' in url:
			url = url[:url.find('/profile/'):] + '/library/'
		return '%s%s' % (url, subdir)

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = self.web.between(url, '/user/', '/')[0]
		if '/library/' in url:
			subdir = url[url.rfind('/library/')+len('/library/'):]
			if subdir != '': subdir = '_%s' % subdir
		return 'photobucket_%s%s' % (user, subdir)

	def download(self):
		'''http://s579.beta.photobucket.com/user/merkler/library/'''
		r = self.web.get('%s' % self.url)
		path = self.web.between(r, "currentAlbumPath: '", "'")[0]
		murl = self.url.replace('http://s', 'http://m').replace('.beta.', '.')
		murl = murl[:murl.find('/user')] + path
		'''http://m579.photobucket.com/albums/ss239/merkler'''
		r = self.web.get(murl)
		# Root album
		print 'MURL=%s' % murl
		self.download_album(path, murl)
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
			print 'MURL=%s' % murl
			name = album.split('/')[1].replace('%20', '-')
			print 'NAME=%s' % name
			self.download_album(path, murl, name=name)
			
		self.wait_for_threads()
	
	def download_album(self, path, murl, name=''):
		offset = 0
		index  = 0
		r = self.web.get(murl)
		while True:
			links = self.web.between(r, '<a class="nolink" href="/albumview/', '"')
			for link in links:
				link = '%s/%s' % (path[1:], '/'.join(link.split('/')[2:])) #[link.rfind('/'):]
				link = self.url[:self.url.rfind('/user')+1] + 'download-' + link
				link = link[:link.rfind('/')+1:] + '.highres' + link[link.rfind('/'):]
				link = link.replace('.html', '').replace('.beta.', '.')
				if '?' in link:
					link = link[:link.find('?')]
				'''http://s579.photobucket.com/download-albums/ss239/merkler.highres/image.jpg'''
				index += 1
				self.download_image(link, index, subdir=name)
			offset += 4
			if 'href="?o=%d' % offset in r:
				nexturl = murl
				if '?' in nexturl: nexturl += '&'
				else: nexturl += '?'
				nexturl += 'o=%d' % offset
				print 'loading next url: %s' % nexturl
				r = self.web.get(nexturl)
			else:
				print 'no next page found'
				break
		
	
