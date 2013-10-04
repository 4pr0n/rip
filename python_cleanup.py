#!/usr/bin/python

"""
	Scans /rips/ directory
	Totals all .zip's in dir
	Removes LRU files if total size is over max_size
"""

import os, time, datetime
from shutil import rmtree

max_size = 150 * 1024 * 1024 * 1024   # 100 gb
max_incomplete_time   = 3600 * 2      # 2 hours
max_orphaned_zip_time = 3600 * 2      # 2 hours
max_album_time        = 3600 * 24 * 2 # 2 days

logfile = 'log.cleanup'

IGNORE = ['imgur_reactiongifsarchive.zip', \
		'imgur_inphinitechaos.zip', \
		'imgur_jwinston.zip', \
		'flickr_herosjourneymythology45surf.zip', \
		'flickr_herosjourneymythology45surf_72157631380242956.zip', \
		'imgur_markedone911.zip', \
		'imgur_jAjVu.zip', \
		'imgur_iateacrayon.zip', \
		'imgur_wIAaa.zip', \
		'imgur_imouto.zip']

def get_incomplete_albums():
	empties = []
	for f in os.listdir('rips'):
		if f == 'txt': continue
		fp = os.path.join('rips', f)
		if os.path.isdir(fp) and not os.path.exists('%s%scomplete.txt' % (fp, os.sep)):
			# Not completed
			mtime = os.path.getmtime(fp)
			now = int(time.strftime('%s'))
			if now - mtime > (max_incomplete_time):
				empties.append(fp)
	return empties

def get_orphan_zips():
	zips = []
	for f in os.listdir('rips'):
		if f in IGNORE: continue
		fp = os.path.join('rips', f)
		if os.path.isdir(fp) or not fp.endswith('.zip'): continue # Not a zip
		if os.path.exists(fp.replace('.zip', '')): continue       # Not orphaned
		mtime = os.path.getmtime(fp)
		now = int(time.strftime('%s'))
		if now - mtime > (max_orphaned_zip_time): # Stale orphan
			zips.append(fp)
	return zips

'''
	Albums older than max_album_time
'''
def get_stale_albums():
	empties = []
	for f in os.listdir('rips'):
		if f == 'txt': continue
		fp = os.path.join('rips', f)
		if not os.path.isdir(fp): continue
		# Album
		mtime = os.path.getmtime(fp)
		now = int(time.strftime('%s'))
		if now - mtime > (max_album_time):
			empties.append(fp)
	return empties

def get_files_to_remove():
	all_files = []
	total_size = 0
	remove_size = 0
	for f in os.listdir('rips'):
		if f == 'txt': continue
		if f.startswith('gonewild_'): continue # ignore gonewild albums
		
		fp = os.path.join('rips', f)
		if os.path.isfile(fp):
			if not fp.endswith('.zip'): continue # Ignore non-zip files (don't delete .html, .cgi, etc)
			size = os.path.getsize(fp)
		elif os.path.isdir(fp):
			size = get_dir_size(fp)
		else:
			log('ERROR: neither file nor dir "%s"' % fp)
			continue
		total_size += size
		all_files.append( (fp, os.path.getatime(fp), size) )
	all_files.sort(key=lambda tup: tup[1], reverse=True)
	to_remove = []
	total = 0
	for (filename, mtime, filesize) in all_files:
		total += filesize
		if total > max_size: 
			total -= filesize
			remove_size += filesize
			to_remove.append(filename)
	return (total_size, remove_size, to_remove)

def get_dir_size(d):
	size = 0
	for root, dirs, files in os.walk(d):
		for f in files:
			fp = os.path.join(root, f)
			size += os.path.getsize(fp)
	return size

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
	removed = 0
	
	l = get_incomplete_albums()
	removed += remove_files(l, 'incomplete (> %d hours)' % (max_incomplete_time / 3600))
	
	l = get_orphan_zips()
	removed += remove_files(l, 'orphan zips (> %d hours)' % (max_orphaned_zip_time / 3600))
	
	#l = get_stale_albums()
	#removed += remove_files(l, 'stale album (> %d hours)' % (max_album_time / 3600))
	
	(total_size, remove_size, l) = get_files_to_remove()
	removed += remove_files(l, 'max file size reached (%d > %d gb) removing %d bytes' % (total_size, max_size / (1024 * 1024 * 1024), remove_size))
	log('finished!')

def remove_files(l, reason=''):
	if len(l) == 0: return 0
	removed = 0
	log('removing %d files because %s' % (len(l), reason))
	for f in l:
		if os.path.isfile(f):
			try:
				log('removing %s (%d)' % (f.rjust(50), os.path.getsize(f)))
				os.remove(f)
				removed += 1
			except Exception, err:
				log('failed to remove %s: %s' % (f, err))
		elif os.path.isdir(f):
			try:
				log('removing %s     (%d)' % (f.rjust(46), get_dir_size(f)))
				rmtree(f)
				removed += 1
			except Exception, err:
				log('failed to remove %s: %s' % (f, err))
		else:
			log('ERROR: not a file or dir, cannot remove %s' % f)
	log('removed %d files because %s' % (removed, reason))
	log('')
	return removed

if __name__ == '__main__':
	main()

