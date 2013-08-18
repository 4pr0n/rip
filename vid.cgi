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
			'xvideos.com/'  :  { 'begend' : ['url=',   '&amp;'],    'unquote' : 1 },
			'videobam.com/' :  { 'begend' : ['"',      '"'],        'unquote' : 1 },
			'xhamster.com/' :  { 'begend' : ['"',      '"'],        'unquote' : 1 },
			'videarn.com/'  :  { 'begend' : ["src='",  "'"],        'unquote' : 1 },
			'beeg.com/'     :  { 'begend' : ['"',      '"'],        'unquote' : 1 },
			'drtuber.com/'  :  { 'begend' : ['url%3D', '"'],        'unquote' : 1 },
			'youporn.com/'  :  { 'begend' : ['href="', '&amp;'],    'unquote' : 1 },
			'redtube.com/'  :  { 'begend' : ['&flv_url=', '&'],     'unquote' : 1 },
			'motherless.com/': { 'begend' : ["__fileurl = '", '"'], 'unquote' : 1 },
			'vine.co/'      :  { 'begend' : ['source src="', '"'],  'unquote' : 1 },
		}
	if 'fapmenow.com/' in siteurl:
		return get_site_fapmenow(siteurl)
	if 'vimeo.com/' in siteurl:
		return get_site_vimeo(siteurl)
	if 'tumblr.com/' in siteurl:
		return get_site_tumblr(siteurl)
	site_key = None
	for key in sites.keys():
		if key in siteurl:
			supported = True
			site_key = key
	if site_key == None:
		raise Exception('site not supported, <a href="http://www.reddit.com/message/compose/?to=4_pr0n&subject=rip.rarchives.com&message=Support%%20this%%20video%%20site:%%20`%s`">ask 4_pr0n to support it</a>' % siteurl)
	source = web.getter(siteurl)
	ext_inds = get_extension_indexes(source)
	index = get_deepest_ind(source, ext_inds)
	url = between(source, index, sites[key]['begend'][0], sites[key]['begend'][1])
	url = url.replace('\\/', '/')
	while sites[site_key]['unquote'] > 0 and '%' in url:
		sites[site_key]['unquote'] -= 1
		url = unquote(url)
	return url

def get_site_fapmenow(siteurl):
	r = web.getter(siteurl)
	if not '"video_src" href="' in r:
		raise Exception('could not find video_src at %s' % siteurl)
	return web.between(r, '"video_src" href="', '"')[0]

def get_site_vimeo(siteurl):
	r = web.getter(siteurl)
	if not "window.addEvent('domready'" in r:
		raise Exception('could not find domready at %s' % siteurl)
	chunk = web.between(r, "window.addEvent('domready'", 'window.addEvent(')[0]
	ts  = web.between(chunk, '"timestamp":',   ',')[0]
	sig = web.between(chunk, '"signature":"',  '"')[0]
	vid = web.between(chunk, '"video":{"id":', ',')[0]
	url  = 'http://player.vimeo.com/play_redirect'
	url += '?clip_id=%s' % vid
	url += '&sig=%s' % sig
	url += '&time=%s' % ts
	url += '&quality=hd&codecs=H264,VP8,VP6&type=moogaloop_local&embed_location=&seek=0'
	return url

def get_site_tumblr(siteurl):
	r = web.getter(siteurl)
	if not 'source src=\\x22' in r:
		raise Exception('could not find source src at %s' % siteurl)
	url = web.between(r, 'source src=\\x22', '\\x22')[0]
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

