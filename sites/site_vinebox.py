#!/usr/bin/python

from basesite import basesite
from json import loads
from time import sleep

class vinebox(basesite):

	def sanitize_url(self, url):
		if not 'vinebox.co/' in url:
			raise Exception('')
		if not 'vinebox.co/u/' in url:
			raise Exception('required /u/ not found in URL')
		if '#' in url: url = url[:url.find('#')]
		if '?' in url: url = url[:url.find('?')]
		url = url.replace('http://', '').replace('https://', '')
		fields = url.split('/')
		while not fields[-2] == 'u': fields.pop(-1)
		if fields[-1] == '':
			raise Exception('required username after /u/')
		return 'http://%s' % '/'.join(fields)

	def get_dir(self, url):
		return 'vinebox_%s' % url[url.rfind('/')+1:]

	def download(self):
		self.init_dir()
		user  = self.url[self.url.rfind('/')+1:]
		page  = 0
		index = 0
		total = 0
		while True:
			apicall = 'http://vinebox.co/api/?action=more&page=%d&vt=1&oid=%s' % (page, user)
			self.debug('loading %s' % apicall)
			r = self.web.get(apicall)
			try:
				json = loads(r)
			except Exception, e:
				self.exception('failed to parse json at %s' % apicall)
			if not 'results' in json:
				self.exception('no "results" found in json at %s' % apicall)
			total += len(json['results'])
			for sresult in json['results']:
				try:
					jresult = loads(sresult)
					index += 1
					self.download_image(jresult['video'], index, total=total)
				except: continue
			if len(json['results']) == 0 or json['status'] != 'ok': break
			page += 1
			sleep(1)
		self.wait_for_threads()
