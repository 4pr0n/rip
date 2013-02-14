#!/usr/bin/python
# -*- coding: utf-8 -*-

"""

Web class.

Holds commonly-used HTTP/web request/post methods.

Compatible with Python 2.4.*
"""

import time

import urllib2, cookielib, urllib
from httplib import HTTPException

class Web:
	"""
		Class used for communicating with web servers.
	"""
	
	def __init__(self, user_agent=None):
		"""
			Sets this class's user agent.
		"""
		self.urlopen = urllib2.urlopen
		self.Request = urllib2.Request
		self.cj			= cookielib.LWPCookieJar()
		self.opener	= urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
		urllib2.install_opener(self.opener)
		
		if user_agent != None:
			self.user_agent = user_agent
		else:
			self.user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.186 Safari/535.1'
	
	def raise_timeout(self, signum, frame):
		raise Exception("Timeout")
	
	def get_meta(self, url):
		""" Reads file info (content type, length, etc) without downloading
		    Times out after 10 seconds (5 to unshorten, 5 to get meta) """
		previous = ''
		url = self.unshorten(url)
		try:
			site = urllib.urlopen(url)
		except Exception:
			return {'content-type': 'unknown', 'content-length': '0'}
		return site.info()
	
	def unshorten(self, url):
		""" Unshortens URL. Follows until no more redirects. Times out after 5 seconds """
		try:
			site = urllib2.urlopen(url)
		except urllib2.HTTPError:
			return url
		except Exception:
			return url
		return site.url

	def check(self, url):
		""" Check if a URL is valid """
		try:
			self.urlopen(url)
		except:
			return False
		return True
	
	def get(self, url):
		"""
			Attempts GET request with web server.
			
			Returns html source of a webpage (string).
			Returns '' if unable to retrieve webpage for any reason.
			
			Will attempt to repeatedly post if '504' response error is received
			or 'getaddrinfo' fails.
		"""
		headers = {'User-agent' : self.user_agent}
		
		try_again = True
		while try_again:
			try:
				req = self.Request(url, '', headers)
				handle = self.urlopen(req)
				
			except IOError, e:
				if str(e) == 'HTTP Error 504: Gateway Time-out' or \
					 str(e) == 'getaddrinfo failed':
					try_again = True
					time.sleep(2)
				
				else: return ''
			
			except HTTPException: return ''
			except UnicodeEncodeError: return ''
			except ValueError: return ''
				
			else:
				try_again = False
			
		try:
			result = handle.read()
		except IncompleteRead:
			return ''
		
		return result

	def getter(self, url):
		"""
			Attempts GET request with TWITTER.
			
			Returns html source of a webpage (string).
			Returns '' if unable to retrieve webpage for any reason.
			
			Will attempt to repeatedly post if '504' response error is received
			or 'getaddrinfo' fails.
		"""
		headers = { 'User-agent' : self.user_agent }
		try:
			req = self.Request(url, headers=headers)
			handle = self.urlopen(req)
		except Exception:
			return ''
		try: result = handle.read()
		except IncompleteRead: return ''
		return result
	
	
	def fix_string(self, s):
		r = ''
		for c in s:
			c2 = ''
			try:
				c2 = str(c)
			except UnicodeEncodeError:
				c2 = ''
			r += c2
		return r
	
	def fix_dict(self, dict):
		d = {}
		
		for key in dict:
			value = dict[key]
			d[key] = self.fix_string(value)
		return d
		
		
	def post(self, url, postdict=None):
		"""
			Attempts POST request with web server.
			
			Returns response of a POST request to a web server.
			'postdict' must be a dictionary of keys/values to post to the server.
			Returns '' if unable to post/retrieve response.
			
			Will attempt to repeatedly post if '504' response error is received
			or 'getaddrinfo' fails.
		"""
		headers = {'User-agent' : self.user_agent}
		
		data = ''
		if postdict != None:
			fixed_dict = self.fix_dict(postdict)
			data = urllib.urlencode(fixed_dict)
		
		try_again = True
		while try_again:
			try:
				req = self.Request(url, data, headers)
				handle = self.urlopen(req)
				
			except IOError, e:
				if str(e) == 'HTTP Error 504: Gateway Time-out' or \
					 str(e) == 'getaddrinfo failed':
					try_again = True
					time.sleep(2)
				
				else: return ''
			
			except HTTPException: return ''
			except UnicodeEncodeError: return ''
			except ValueError: return ''
				
			else:
				try_again = False
			
		result = handle.read()
		
		return result
	
	
	def download(self, url, save_as):
		"""
			Downloads a file from 'url' and saves the file locally as 'save_as'.
			Returns True if download is successful, False otherwise.
		"""
		
		result = False
		output = open(save_as, "wb")
		
		try:
			file_on_web = self.urlopen(url)
			while True:
				buf = file_on_web.read(65536)
				if len(buf) == 0:
					break
				output.write(buf)
			result = True
			
		except IOError, e: pass
		except HTTPException, e: pass
		except ValueError: return ''
		
		output.close()
		return result
	
	
	def clear_cookies(self):
		"""
			Clears cookies in cookie jar.
		"""
		self.cj.clear()
	
	
	def set_user_agent(user_agent):
		"""
			Changes the user-agent used when connecting.
		"""
		self.user_agent = user_agent
	
	
	def between(self, source, start, finish):
		"""
			Helper method. Useful when parsing responses from web servers.
			
			Looks through a given source string for all items between two other strings, 
			returns the list of items (or empty list if none are found).
			
			Example:
				test = 'hello >30< test >20< asdf >>10<< sadf>'
				print between(test, '>', '<')
				
			would print the list:
				['30', '20', '>10']
		"""
		result = []
		i = source.find(start)
		j = source.find(finish, i + len(start) + 1)
		
		while i >= 0 and j >= 0:
			i = i + len(start)
			result.append(source[i:j])
			i = source.find(start, i + len(start) + 1)
			j = source.find(finish, i + len(start) + 1)
		
		return result
	
	
if __name__ == "__main__":
	web = Web()
	url = "http://www.mp3-center.org/mp3song.php?name=Eric_Clapton_-_Layla.mp3&url=t62XabuWw8iblM9kmtChxtGRkqmPhqzZuquGqoLOgPGfy424u6qY6GNHaM21d4_MtZiChK7lmGql1YfisImC"
	print web.unshorten(url)

