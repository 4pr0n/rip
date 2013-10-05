#!/usr/bin/python

from basesite import basesite
from site_imgur import imgur
from json import loads
from time import sleep

class reddit(imgur):
	
	""" Parse/strip URL to acceptable format """
	def sanitize_url(self, url):
		if not 'reddit.com/' in url:
			raise Exception('')
		if not 'reddit.com/user/' in url:
			raise Exception('required /user/ not found in URL')
		user = url[url.find('/user/')+6:]
		if '/' in user: user = user[:user.find('/')]
		if '?' in user: user = user[:user.find('?')]
		if '#' in user: user = user[:user.find('#')]
		return 'http://reddit.com/user/%s' % user

	""" Discover directory path based on URL """
	def get_dir(self, url):
		user = url[url.find('/user/')+6:]
		return 'reddit_%s' % user

	def download(self):
		self.init_dir()
		params = ''
		already_downloaded = []
		index = 0
		total = 0
		while True:
			url = '%s/submitted.json%s' % (self.url, params)
			self.log('loading %s' % url)
			r = self.web.get(url)
			try: json = loads(r)
			except: break
			if not 'data' in json: break
			if not 'children' in json['data']: break
			children = json['data']['children']
			total += len(children)
			for child in children:
				url = child['data']['url']
				postid = child['data']['id'] + '-' # to separate postid from index
				index += 1
				if not 'imgur.com' in url: continue
				if '#' in url: url = url[:url.find('#')]
				if '?' in url: url = url[:url.find('?')]
				if 'imgur.com/a/' in url:
					while url[url.find('/a/')+3:].count('/') > 0:
						url = url[:url.rfind('/')]
					aid = url[url.rfind('/')+1:]
					if not aid in already_downloaded:
						already_downloaded.append(aid)
						self.download_album_json(url, postid=postid)
					else:
						self.log('already downloaded %s' % url)
				else:
					if not 'i.imgur.com' in url and not (url[-4] == '.' or url[-5] == '.'):
						# Need to get direct link to image
						iid = url[url.find('imgur.com/')+len('imgur.com/'):]
						if '/' in iid: iid = iid[:iid.find('/')]
						if '?' in iid: iid = iid[:iid.find('?')]
						if '#' in iid: iid = iid[:iid.find('#')]
						ir = self.web.get('http://api.imgur.com/2/image/%s' % iid)
						try: ijs = loads(ir)
						except: continue
						if not 'image' in ijs or not 'links' in ijs['image'] or not 'original' in ijs['image']['links']: continue
						url = ijs['image']['links']['original']
					fname = url[url.rfind('/')+1:]
					if '?' in fname: fname = fname[:fname.find('?')]
					if '#' in fname: fname = fname[:fname.find('#')]
					if not fname in already_downloaded:
						already_downloaded.append(fname)
						saveas = '%s%03d_%s' % (postid, index, fname)
						self.download_image(url, index, total=total, saveas=saveas)
					else:
						self.log('already downloaded %s' % url)
				if self.hit_image_limit(): break
			if self.hit_image_limit(): break
			after = json['data']['after']
			if total == 0 or after == None: break
			params = '?total=%d&after=%s' % (total, after)
			sleep(2)
		self.wait_for_threads()
	
