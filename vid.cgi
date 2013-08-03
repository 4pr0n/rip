#!/usr/bin/python

import cgitb#; cgitb.enable() # for debugging
import cgi # for getting query keys/values

from urllib import unquote
from json   import dumps

from sites.Web import Web
web = Web()

def main():
	keys = get_keys()
	if 'url' in keys:
		get_video_url(keys['url'])
	elif 'download' in keys:
		get_download(keys['download'])
	else:
		print_error("expected 'url' or 'download' not found")

def get_video_url(siteurl):
	url = get_url(siteurl)
	meta = web.get_meta(url)
	if not 'Content-Type' in meta or ('video' not in meta['Content-Type'].lower() and 'application/octet-stream' not in meta['Content-Type'].lower()):
		print_error('no video content at %s' % url)
		return
	print dumps( {
		'url' : url
	})

def get_url(siteurl):
	is_supported(siteurl)
	sites = {
			'xvideos.com/'  : { 'begend' : ['url=',   '&amp;'], 'unquote' : 1 },
			'videobam.com/' : { 'begend' : ['"',      '"'],     'unquote' : 1 },
			'xhamster.com/' : { 'begend' : ['"',      '"'],     'unquote' : 1 },
			'videarn.com/'  : { 'begend' : ["src='",  "'"],     'unquote' : 1 },
			'beeg.com/'     : { 'begend' : ['"',      '"'],     'unquote' : 1 },
			'drtuber.com/'  : { 'begend' : ['url%3D', '"'],     'unquote' : 1 },
			'youporn.com/'  : { 'begend' : ['href="', '&amp;'], 'unquote' : 1 }
		}
	supported = False
	for key in sites.keys():
		if key in siteurl:
			supported = True
	if not supported:
		raise Exception('site not supported, <a href="http://www.reddit.com/message/compose/?to=4_pr0n&subject=rip.rarchives.com&message=Support%20this%20site:%20enter_site_here.com">ask 4_pr0n to support it</a>')
	source = web.getter(siteurl)
	ext_inds = get_extension_indexes(source)
	index = get_deepest_ind(source, ext_inds)
	site_key = None
	for key in sites.keys():
		if key in siteurl:
			site_key = key
			url = between(source, index, sites[key]['begend'][0], sites[key]['begend'][1])
			break
	url = url.replace('\\/', '/')
	while sites[site_key]['unquote'] > 0 and '%' in url:
		sites[site_key]['unquote'] -= 1
		url = unquote(url)
	return url

def is_supported(url):
	for not_supported in ['pornhub.com/', 'youtube.com/', 'dailymotion.com/']:
		if not_supported in url:
			raise Exception('%s is not supported' % not_supported)

def get_deepest_ind(source, ext_inds):
	deep_ind = 0
	for (ext, ind) in ext_inds:
		if ind > deep_ind:
			extension = ext
			deep_ind = ind
	return deep_ind

def between(text, i, before, after):
	start = text.rfind(before, 0, i)
	end = text.find(after, i)
	if start == -1 or end == -1:
		raise Exception('could not find begin=%s end=%s around %s' % (before, after, text))
	return text[start+len(before):end]
	

def get_extension_indexes(source):
	extensions = ['.mp4', '.flv']
	result = []
	for ext in extensions:
		index = -1
		while True:
			index = source.lower().find(ext.lower(), index + 1)
			if index == -1:
				break
			result.append( (ext, index) )
	if result == []:
		raise Exception("mp4 or flv video not found")
	return result

""" Retrieves key/value pairs from query, puts in dict """
def get_keys():
	form = cgi.FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = form[key].value
	return keys

""" Print error in JSON format """
def print_error(text):
	print dumps( { 'error' : text } )

if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	try:
		main()
	except Exception, e:
		print_error(str(e))
	print "\n"

