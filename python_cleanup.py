#!/usr/bin/python

"""
	Scans /rips/ directory
	Totals all .zip's in dir
	Removes LRU files if total size is over max_size
"""

import os, time, datetime

max_size = 50 * 1024 * 1024 * 1024
logfile = 'log.cleanup'

def get_files_to_remove():
	all_files = []
	for filename in os.listdir('rips'):
		filename = 'rips%s%s' % (os.sep, filename)
		if not os.path.isfile(filename) or not filename.endswith('.zip'): continue
		all_files.append( (filename, os.path.getatime(filename), os.path.getsize(filename)) )
	all_files.sort(key=lambda tup: tup[1], reverse=True)
	total = 0
	to_remove = []
	for (filename, mtime, filesize) in all_files:
		total += filesize
		if total > max_size: 
			to_remove.append(filename)
			print 'need to delete %s, filetime=%d' % (filename, mtime)
	return to_remove

# Writes log line to file
def log(line):
	print line
	now = datetime.datetime.now()
	f = open(logfile, 'a')
	f.write("%s %s\n" % (now.strftime("%Y-%m-%d %H:%M:%S"), line))
	f.flush()
	f.close()

def main():
	log('starting...')
	while True:
		l = get_files_to_remove()
		if len(l) > 0:
			log('removing %d files:' % len(l))
			for f in l:
				os.remove(f)
				log('removed %s' % f)
		else:
			log('')
		time.sleep(60 * 5)

if __name__ == '__main__':
	main()
