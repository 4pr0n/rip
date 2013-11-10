#!/usr/bin/python

SCHEMA = {
	'albums' :
		'\n\t' +
		'id       integer primary key, \n\t' +
		'album    text unique, \n\t' +
		'count    integer, \n\t' +
		'filesize integer, \n\t' +
		'zipsize  integer, \n\t' +
		'ip       text,    \n\t' +
		'views    integer, \n\t' +
		'source   text,    \n\t' +
		'reports  integer, \n\t' +
		'created  integer, \n\t' +
		'accessed integer, \n\t' +
		'deleted  integer, \n\t' +
		'log      string,  \n\t' +
		'complete integer  \n\t',

	'images' :
		'\n\t' +
		'id     integer primary key, \n\t' +
		'album  integer, \n\t' +
		'number integer, \n\t' +
		'path   text,    \n\t' +
		'source text,    \n\t' +
		'width  integer, \n\t' +
		'height integer, \n\t' +
		'size   integer, \n\t' +
		'thumb  text,    \n\t' +
		'type   text,    \n\t' + # image/video
		'foreign key(album) references albums(id)',

	'recent' :
		'\n\t' +
		'url    text,    \n\t' +
		'album  text,    \n\t' +
		'time   integer, \n\t' +
		'ip     text     \n\t',

	'banned' :
		'\n\t' +
		'ip     text primary key, \n\t' +
		'reason text, \n\t' +
		'album  text, \n\t' +
		'url    text, \n\t' +
		'type   text  \n\t', # permanent/temporary

	'blacklist' :
		'\n\t' +
		'album text primary key \n\t',

	'unsupported' :
		'\n\t' +
		'domain text primary key, \n\t' +
		'reason text \n\t',
}

from os import getcwd, path, utime

try:
	import sqlite3
except ImportError:
	import sqlite as sqlite3

from time import sleep, mktime, gmtime, time as timetime
DB_FILE = 'db.db'
if getcwd().endswith('sites') or getcwd().endswith('rips'):
	DB_FILE = '../db.db'

class DB:
	def __init__(self):
		self.conn = sqlite3.connect(DB_FILE) #TODO CHANGE BACK, encoding='utf-8')
		self.conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
		if SCHEMA != None and SCHEMA != {} and len(SCHEMA) > 0:
			# Create table for every schema given.
			for key in SCHEMA:
				self.create_table(key, SCHEMA[key])

	def create_table(self, table_name, schema):
		cur = self.conn.cursor()
		try:
			cur.execute('''CREATE TABLE IF NOT EXISTS %s (%s)''' % (table_name, schema) )
			self.conn.commit()
		except sqlite3.OperationalError, e:
			# Ignore if table already exists, otherwise print error
			if str(e).find('already exists') == -1:
				raise e
		cur.close()

	def commit(self):
		try_again = True
		while try_again:
			try:
				self.conn.commit()
				try_again = False
			except:
				sleep(0.1)

	def insert(self, table, values):
		cur = self.conn.cursor()
		questions = ','.join(['?'] * len(values))
		exec_string = '''insert into %s values (%s)''' % (table, questions)
		result = cur.execute(exec_string, values)
		last_row_id = cur.lastrowid
		cur.close()
		return last_row_id

	def count(self, table, where, values=[]):
		cur = self.conn.cursor()
		result = cur.execute('''select count(*) from %s where %s''' % (table, where), values).fetchall()
		cur.close()
		return result[0][0]

	def select_first(self, what, table, where, values=[]):
		cur = self.conn.cursor()
		query = '''
			select %s
				from %s
			 where %s
		''' % (what, table, where)
		curexec = cur.execute(query, values)
		result = curexec.fetchone()
		cur.close()
		if result == None:
			raise Exception('query did not return anything')
		return result
	
	def select_one(self, what, table, where, values=[]):
		return self.select_first(what, table, where, values)[0]

	def execute(self, statement, values=[]):
		cur = self.conn.cursor()
		result = cur.execute(statement, values)
		return result
	
	def delete_album(self, album, blacklist=False, delete_files=True):
		del_album = del_zip = was_blacklisted = False
		if delete_files:
			from shutil import rmtree
			from os import path, remove
			albumpath = album
			if not getcwd().endswith('rips'):
				albumpath = path.join('rips', album)
			# Delete directory
			if path.exists(albumpath):
				del_album = True
				rmtree(albumpath)
			# Delete zip
			zipfile = '%s.zip' % albumpath
			if path.exists(zipfile):
				del_zip = True
				remove(zipfile)
			if not del_album or not del_zip:
				raise Exception('could not delete album/zip, cwd: %s, looked for %s and %s' % (getcwd(), albumpath, zipfile))

		try:
			albumid = self.select_one('id', 'albums', 'album = "%s"' % album)
		except:
			# Album doesn't exist in DB
			return
		q_images = '''
			delete from images
				where album = ?
		'''
		q_album = '''
			delete from albums
				where id = ?
		'''
		cur = self.conn.cursor()
		cur.execute(q_images, [albumid])
		cur.execute(q_album, [albumid])
		if blacklist:
			try:
				cur.execute('insert into blacklist values (?)', [album])
				was_blacklisted = True
			except Exception, e:
				# Failed to blacklist (already blacklisted?)
				pass
		cur.close()
		self.commit()
		if not del_album or not del_zip or (not was_blacklisted and blacklist):
			raise Exception('album was %sdeleted, zip was %sdeleted, album was %sblacklisted' % ('' if del_album else 'not ', '' if del_zip else 'not ', '' if was_blacklisted else 'not '))

	def update_album(self, album):
		# update album / zip modified times
		for f in [album, '%s.zip' % album]:
			try:
				utime(path.join('rips', f), ( int(timetime()), int(timetime())))
			except: pass
		# Update database accessed time
		query = '''
			update albums
				set accessed = %d
			where album = ?
		''' % int(mktime(gmtime()))
		cur = self.conn.cursor()
		curexec = cur.execute(query, [album])
		cur.close()
		self.commit()

	def add_recent(self, url, album, ip):
		values = [
			url,
			album,
			int(mktime(gmtime())),
			ip
		]
		self.insert('recent', values)
		self.commit()

	def count(self, what, table, where, values=[]):
		query = '''
			select
				count (%s)
				from %s
				where %s
		''' % (what, table, where)
		cur = self.conn.cursor()
		curexec = cur.execute(query, values)
		count = curexec.fetchone()[0]
		cur.close()
		return count

