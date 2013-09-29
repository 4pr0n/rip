#!/usr/bin/python

from sys import stdout
from time import mktime, strptime, strftime, localtime
from json import dumps, loads

STAT_DIR = open('.STAT_DIR', 'r').read().strip() # logs
LOG_FILE = open('.LOG_FILE', 'r').read().strip() # ~/logs/<site>/http/access.log
LAST_LOG = open('.LAST_LOG', 'r').read().strip() # ~/logs/<site>/http/access.log.0

# Breaks log line into separate fields, preserving quoted sections
def split_fields(line):
	line = line.replace('\n', '').strip()
	inq = False
	for i in xrange(0, len(line)):
		if inq and line[i] == '"':
			inq = False
		elif line[i] == '"':
			inq = True
		elif inq and line[i] == ' ':
			lst = list(line)
			lst[i] = chr(0)
			line = ''.join(lst)
	return chr(1).join(line.split(' ')).replace(chr(0), ' ').split(chr(1))

# Split line into sections, interpret data, return tuple of fields
def parse_line(line):
	(ip, x, y, dt, tz, header, status, size, ref, ua) = split_fields(line)
	dt = dt.replace('[', '')
	epoch = int(mktime(strptime(dt, '%d/%b/%Y:%H:%M:%S')))
	url = header.split(' ')[1]
	ref = ref.replace('"', '')
	return (ip, epoch, url, status, size, ref, ua)

# Read log file, return dict containing all information about the log
def parse_log(log, data):
	try:
		last_line = load_last_line()
		print 'last line: %s...' % last_line[:30]
	except Exception, e:
		print 'exception %s' % str(e)
		last_line = ''
	almost_there = there_yet = False
	try:
		for linenumber, line in enumerate(open(log, 'r')):
			#if linenumber % 251 == 0:
			#	stdout.write('\r%d\r' % linenumber)
			#	stdout.flush()
			if not there_yet:
				if last_line == '' or not almost_there and last_line in line:
					almost_there = True
				if last_line == '' or almost_there and last_line not in line:
					there_yet = True
				if not there_yet: continue
			if almost_there:
				almost_there = False
				print 'resuming from line %d' % linenumber
			# We should log this line and below
			(ip, epoch, url, status, size, referer, useragent) = parse_line(line)
			interpret_data(data, epoch, url, size)
	except KeyboardInterrupt:
		print '         \ninterrupted'
		pass
	if there_yet:
		save_last_line(line)

def load_data_from_epoch(tstamp, timekey):
	stime = strftime('%s', localtime(tstamp))
	fname = '%s/%s-%s.log' % (STAT_DIR, stime, timekey)
	try:
		f = open(fname, 'r')
		r = f.read().strip()
		f.close()
	except Exception, e:
		return {}
	print 'loaded %s' % fname.replace(STAT_DIR,''),
	b = loads(r)
	a = {}
	for k in ['hits', 'rips', 'zips', 'album_views', 'images', 'thumbs', 'videos', 'checks', 'cgi', 'others', 'bytes']:
		if k in b: 
			a[k] = b[k]
			print '%s=%s' % (k, str(b[k]).ljust(4)),
	print ''
	return a

def load_last_line():
	f = open('%s/.last_line' % STAT_DIR, 'r')
	t = f.read().strip()
	f.close()
	return t

def save_last_line(last):
	f = open('%s/.last_line' % STAT_DIR, 'w')
	f.write(last)
	f.flush()
	f.close()

def interpret_data(data, epoch, url, size):
	for tim in data.keys():
		tstamp = int(epoch / data[tim]['seconds']) * data[tim]['seconds']
		if not tstamp in data[tim]: data[tim][tstamp] = load_data_from_epoch(tstamp, tim)
		# Hits
		data[tim][tstamp]['hits'] = data[tim][tstamp].get('hits', 0) + 1
		# Bytes
		data[tim][tstamp]['bytes'] = data[tim][tstamp].get('bytes', 0) + int(size)
		# Rips
		if 'url=' in url and '&start=true' in url:
			data[tim][tstamp]['rips'] = data[tim][tstamp].get('rips', 0) + 1
		# Zips
		elif url.endswith('.zip'):
			data[tim][tstamp]['zips'] = data[tim][tstamp].get('zips', 0) + 1
		# Album views
		elif 'start=0' in url and '&view=' in url:
			data[tim][tstamp]['album_views'] = data[tim][tstamp].get('album_views', 0) + 1
		# Image views
		elif '.' in url and url[url.rfind('.'):].lower() in ['.jpg', '.jpeg', '.png', '.gif']:
			if not '/thumbs/' in url:
				data[tim][tstamp]['images'] = data[tim][tstamp].get('images', 0) + 1
			else:
				data[tim][tstamp]['thumbs'] = data[tim][tstamp].get('thumbs', 0) + 1
		# Video views
		elif '.' in url and url[url.find('.'):].lower() in ['.mp4']:
			data[tim][tstamp]['videos'] = data[tim][tstamp].get('videos', 0) + 1
		elif '&check=true' in url:
			data[tim][tstamp]['checks'] = data[tim][tstamp].get('checks', 0) + 1
		elif '.cgi' in url:
			data[tim][tstamp]['cgi'] = data[tim][tstamp].get('cgi', 0) + 1
		else:
			data[tim][tstamp]['others'] = data[tim][tstamp].get('others', 0) + 1

if __name__ == '__main__':
	data = {
			'day'  : {'seconds' : 86400},
			'hour' : {'seconds' : 3600},
			'5min' : {'seconds' : 300},
			#'1min' : {}
		}
	parse_log(LAST_LOG, data)
	parse_log(LOG_FILE, data)
	for timekey in data.keys():
		for k in sorted(data[timekey].keys()):
			if k == 'seconds': continue
			stime = strftime('%s', localtime(int(k)))
			fname = '%s/%s-%s.log' % (STAT_DIR, stime, timekey)
			print 'writing %s:' % fname.replace(STAT_DIR, ''),
			for attr,value in data[timekey][k].iteritems():
				print '%s=%s' % (attr,str(value).ljust(4)),
			print ''
			f = open(fname, 'w')
			f.write('%s\n' % dumps(data[timekey][k]))
			f.close()

