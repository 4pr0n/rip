#!/usr/bin/python

from basesite import basesite
from os import path, walk
from shutil import copy2

class gonewild(basesite):
	
	def sanitize_url(self, url):
		if not 'gonewild:' in url:
			raise Exception('')
		
		user = url[url.rfind(':')+1:]
		if len(user) < 3 or not self.valid_username(user):
			raise Exception('not a valid reddit username: %s' % user)
		key_path = path.join(path.dirname(__file__), 'gonewild.key')
		if not path.exists(key_path):
			raise Exception('required gonewild.key not found')
		f = open(key_path, 'r')
		self.gonewild_root = f.read().strip()
		f.close()
		self.gonewild_user = user
		userroot = path.join(self.gonewild_root, 'users', user)
		if not path.exists(userroot):
			raise Exception('unable to rip this specific gonewild user')
		return url

	def valid_username(self, user):
		alpha = 'abcdefghijklmnopqrstuvwxyz-_0123456789'
		for c in user:
			if not c.lower() in alpha:
				return False
		return True

	""" Discover directory path based on URL """
	def get_dir(self, url):
		return 'gonewild_%s' % url[url.rfind(':')+1:]

	""" Download images in album """
	def download(self):
		self.init_dir()
		userroot = path.join(self.gonewild_root, 'users', self.gonewild_user)
		already_got = []
		for root, subdirs, files in walk(userroot):
			for filename in files:
				f = path.join(root, filename)
				n = filename
				if not root.endswith(self.gonewild_user): # Subdir
					n = '%s_%s' % (root[root.rfind('/')+1:], filename)

				# Avoid duplicates
				no_post = n[n.rfind('_')+1:]
				if no_post in already_got: continue
				already_got.append(no_post)

				saveas = path.join(self.working_dir, n)
				copy2(f, saveas)
				thumbnail = self.create_thumb(saveas)
				self.image_count += 1
		self.wait_for_threads()
