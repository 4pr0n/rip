#!/usr/bin/python

SCHEMA = {
	'albums' :
		'\n\t' +
		'id       integer primary key, \n\t' +
		'path     text unique, \n\t' +
		'count    integer, \n\t' +
		'filesize integer, \n\t' +
		'zipsize  integer, \n\t' +
		'user     text,    \n\t' +
		'views    integer, \n\t' +
		'source   text,    \n\t' +
		'reports  integer, \n\t' +
		'created  integer, \n\t' +
		'accessed integer, \n\t' +
		'deleted  integer, \n\t' +
		'log      string   \n\t',

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
		'path   text,    \n\t' +
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

from os import getcwd
DB_FILE = 'db.db'
if not getcwd().endswith('rip'):
	DB_FILE = '../db.db'

try:
	import sqlite3
except ImportError:
	import sqlite as sqlite3

from time import sleep

class DB:
	def __init__(self):
		self.conn = None
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

	def count(self, table, where):
		cur = self.conn.cursor()
		result = cur.execute('''select count(*) from %s where %s''' % (table, where)).fetchall()
		cur.close()
		return result[0][0]

	def select_one(self, what, table, where, values=None):
		cur = self.conn.cursor()
		query = '''
			select %s
				from %s
			 where %s
		''' % (what, table, where)
		if values == None:
			curexec = cur.execute(query)
		else:
			curexec = cur.execute(query, values)
		return curexec.fetchone()[0]

	def execute(self, statement, values=None):
		cur = self.conn.cursor()
		if values == None:
			result = cur.execute(statement)
		else:
			result = cur.execute(statement, values)
		return result
	
