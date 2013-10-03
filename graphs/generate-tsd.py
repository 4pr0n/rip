#!/usr/bin/python

from sys import stdout, exit
from time import mktime, strptime, strftime, localtime, time
from json import dumps, loads
from os import path, mkdir, remove

LOG_FILE = open('.LOG_FILE', 'r').read().strip() # ~/logs/<site>/http/access.log
STAT_DIR = open('.STAT_DIR', 'r').read().strip() # logs
if not path.exists(STAT_DIR):
	mkdir(STAT_DIR)

def log(text, level='INFO'):
	print '[%s] [%s] %s' % (strftime('%Y-%m-%dT%H:%M:%S'), level, text)

# Breaks log line into separate fields, preserving quoted sections
def split_fields(line):
	line = line.replace('\n', '').strip()
	line = line.replace('\\"', '')
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
	fields = split_fields(line)
	if len(fields) == 10:
		(ip, x, y, dt, tz, header, status, size, ref, ua) = fields
	else:
		log('', level='ERROR')
		log('unexpected length of log line fields: %s' % len(fields), level='ERROR')
		log('fields:', level='ERROR')
		for f in fields: 
			log('    %s' % f, level='ERROR')
		log('', level='ERROR')
		raise Exception('unexpected length of line')
	dt = dt.replace('[', '')
	epoch = int(mktime(strptime(dt, '%d/%b/%Y:%H:%M:%S')))
	url = header.split(' ')[1]
	ref = ref.replace('"', '')
	return (ip, epoch, url, status, size, ref, ua)

# Read log file, return dict containing all information about the log
def parse_log(logfile, data, last_line=None):
	if last_line == None:
		try:
			log('loading last line...')
			last_line = load_last_line()
			log('last line: %s...' % last_line[:50])
		except Exception, e:
			log('failed to load last line, defauling to empty line (starting over)', level='WARN')
			log('    exception: %s' % str(e), level='WARN')
			last_line = ''
	almost_there = there_yet = False
	try:
		for linenumber, line in enumerate(open(logfile, 'r')):
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
				log('resuming from line #%d' % linenumber)
			# We should parse this line and below
			try:
				(ip, epoch, url, status, size, referer, useragent) = parse_line(line)
				interpret_data(data, epoch, url, size, status, ip)
			except: pass
	except KeyboardInterrupt:
		log('         \ninterrupted', level='WARN')
		exit(1)
		return
	except Exception, e:
		log('', level='WARN')
		log('got exception while generating TSD: %s' % str(e), level='WARN')
		log('exiting early without saving!', level='WARN')
		log('', level='WARN')
		exit(1)
		return
		

	if there_yet:
		# We found our checkpoint and parsed logs, save the last line as the checkpoint
		save_last_line(line) 
	else:
		# We didn't find the checkpoint, start over with brand-new log file
		parse_log(logfile, data, last_line='') 

def load_data_from_epoch(tstamp, timekey):
	stime = strftime('%s', localtime(tstamp))
	fname = '%s/%s-%s.log' % (STAT_DIR, stime, timekey)
	try:
		f = open(fname, 'r')
		r = f.read().strip()
		f.close()
	except Exception, e:
		log('could not load data in %s' % (fname.replace(STAT_DIR,'')), level='WARN')
		log('   %s' % str(e), level='WARN')
		return {}
	log('loaded %s' % fname.replace(STAT_DIR,''))
	#return loads(r)
	b = loads(r)
	a = {}
	output = ''
	for k in ['hits', 'rips', 'zips', 'album_views', 'images', 
	          'thumbs', 'videos', 'checks', 'cgi', 'others', 
	          'bytes', 'ban', 'err', '404', 'users']:
		if k in b: 
			a[k] = b[k]
			if k != 'users':
				output += ('%s:%s ' % (k, str(b[k]))).rjust(12)
				if len(output) >= 48:
					log('    %s' % output)
					output = ''
	if output != '':
		log('    %s' % output)
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

def interpret_data(data, epoch, url, size, status, ip):
	for tim in data.keys():
		tstamp = int(epoch / data[tim]['seconds']) * data[tim]['seconds']
		if not tstamp in data[tim]: data[tim][tstamp] = load_data_from_epoch(tstamp, tim)

		if status in ['403']: # User is banned or forbidden
			data[tim][tstamp]['ban'] = data[tim][tstamp].get('ban', 0) + 1

		elif status in ['404']: # not found
			data[tim][tstamp]['404'] = data[tim][tstamp].get('404', 0) + 1

		elif status.startswith('5'): # Error!
			data[tim][tstamp]['err'] = data[tim][tstamp].get('err', 0) + 1
			
		elif status in ['200', '206', '304']: # Request is OK, partial, or not-modified
			data[tim][tstamp]['hits'] = data[tim][tstamp].get('hits', 0) + 1           # Hits
			data[tim][tstamp]['bytes'] = data[tim][tstamp].get('bytes', 0) + int(size) # Bytes
			if 'url=' in url and '&start=true' in url:
				data[tim][tstamp]['rips'] = data[tim][tstamp].get('rips', 0) + 1         # Rips
			elif url.endswith('.zip'):
				data[tim][tstamp]['zips'] = data[tim][tstamp].get('zips', 0) + 1         # Zips
			elif 'start=0' in url and '&view=' in url:
				data[tim][tstamp]['album_views'] = data[tim][tstamp].get('album_views', 0) + 1       # Album views
			elif '.' in url and url[url.rfind('.'):].lower() in ['.jpg', '.jpeg', '.png', '.gif']: # Image views
				if not '/thumbs/' in url:
					data[tim][tstamp]['images'] = data[tim][tstamp].get('images', 0) + 1  # Full-size images
				else:
					data[tim][tstamp]['thumbs'] = data[tim][tstamp].get('thumbs', 0) + 1  # Thumbnails
			elif '.' in url and url[url.find('.'):].lower() in ['.mp4']:
				data[tim][tstamp]['videos'] = data[tim][tstamp].get('videos', 0) + 1    # Video views
			elif '&check=true' in url:
				data[tim][tstamp]['checks'] = data[tim][tstamp].get('checks', 0) + 1    # Status updates on ongoing rips
			elif '.cgi' in url:
				data[tim][tstamp]['cgi'] = data[tim][tstamp].get('cgi', 0) + 1          # CGI requests
			else:
				data[tim][tstamp]['others'] = data[tim][tstamp].get('others', 0) + 1    # Misc

		# Unique IP check
		if not 'users' in data[tim][tstamp]: data[tim][tstamp]['users'] = []
		if not ip in data[tim][tstamp]['users']:
			data[tim][tstamp]['users'].append(ip)


''' Find and delete old logs we don't care about anymore '''
def cleanup_old_logs():
	log('searching for old logs')
	to_remove = []
	for label, period, threshold in [
	      ('5min',  300,    86400), #  5 min logs expire after  1 day
	      ('hour', 3600,  3888000), # 1-hour logs expire after 45 days
	      ('day', 86400, 31536000), #  1-day logs expire after  1 year
	    ]:
		curtime = ( int( int(time()) / period) * period ) - threshold
		while True:
			logname = '%s/%d-%s.log' % (STAT_DIR, curtime, label)
			if not path.exists(logname): break
			to_remove.append(logname)
			curtime -= period
	
	if len(to_remove) == 0: return
	log('removing %d stale logs:' % len(to_remove))
	for f in to_remove:
		remove(f)
		log('    removed: %s' % f)

if __name__ == '__main__':
	log('starting...')
	cleanup_old_logs()

	data = {
			'day'  : {'seconds' : 86400},
			'hour' : {'seconds' : 3600},
			'5min' : {'seconds' : 300},
		}
	parse_log(LOG_FILE, data)
	for timekey in data.keys():
		for k in sorted(data[timekey].keys()):
			if k == 'seconds': continue
			stime = strftime('%s', localtime(int(k)))
			fname = '%s/%s-%s.log' % (STAT_DIR, stime, timekey)
			log('writing %s' % fname.replace(STAT_DIR, ''))
			output = ''
			for attr,value in data[timekey][k].iteritems():
				if attr != 'users':
					output += ('%s:%d ' % (attr, value)).rjust(12)
					if len(output) >= 48:
						log('    %s' % output)
						output = ''
			if output != '':
				log('    %s' % output)

			f = open(fname, 'w')
			f.write('%s\n' % dumps(data[timekey][k]))
			f.close()

