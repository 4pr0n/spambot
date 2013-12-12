#!/usr/bin/python
from time import strftime, gmtime, sleep, time as timetime
from os   import path
from sys  import stderr

try:                import sqlite3
except ImportError: import sqlite as sqlite3

SCHEMA = {
	'admins' :
		'\n\t' +
		'username text primary key, \n\t' +
		'score integer \n\t',

	'subs_source' :
		'\n\t' +
		'subreddit text unique \n\t',

	'subs_mod' :
		'\n\t' +
		'subreddit text unique \n\t',

	'filters' :
		'\n\t' +
		'id       integer primary key autoincrement, \n\t' +
		'type     text,    \n\t' +
		'text     text,    \n\t' +
		'author   text,    \n\t' + 
		'count    integer, \n\t' +
		'created  integer, \n\t' +
		'active   integer, \n\t' +
		'isspam   integer  \n\t',

	'log_removed' :
		'\n\t' +
		'filterid  integer, \n\t' +
		'posttype  text,    \n\t' +
		'permalink text,    \n\t' +
		'credit    text,    \n\t' +
		'date      integer  \n\t',

	'log_sourced' :
		'\n\t' +
		'album     text,    \n\t' +
		'date      integer, \n\t' +
		'permalink text     \n\t',
	
	'log_amateurarchives' :
		'\n\t' +
		'action    text,    \n\t' +
		'permalink text,    \n\t' +
		'date      integer, \n\t' +
		'reason    text     \n\t',

	'checked_albums' :
		'\n\t' +
		'url text primary key \n\t',
	
	'checked_posts' :
		'\n\t' +
		'postid text primary key \n\t',
	
	'blacklist_users' :
		'\n\t' + 
		'username text primary key \n\t',
	
	'blacklist_urls' :
		'\n\t' +
		'url text primary key \n\t',

	'config' :
		'\n\t' +
		'key   text primary key, \n\t' +
		'value text \n\t',
}

INDICES = {
	'filters'     : 'created',
	'removed'     : 'date',
	'subs_mod'    : 'subreddit',
	'admins'      : 'username',
	'subs_source' : 'subreddit',
	'subs_mod'    : 'subreddit',
	'config'      : 'key',
	'checked_albums' : 'url',
	'checked_posts'  : 'postid'
}

DB_FILE = 'spambot.db'

class DB:
	def __init__(self):
		self.logger = stderr
		if path.exists(DB_FILE):
			self.debug('__init__: using database file: %s' % DB_FILE)
		else:
			self.debug('__init__: database file (%s) not found, creating...' % DB_FILE)
		self.conn = sqlite3.connect(DB_FILE)
		self.conn.text_factory = lambda x: unicode(x, "utf-8", "ignore")
		for table in SCHEMA:
			self.create_table(table, SCHEMA[table])
		for index in INDICES:
			self.create_index(index, INDICES[index])

	def debug(self, text):
		tstamp = strftime('[%Y-%m-%dT%H:%M:%SZ]', gmtime())
		text = '%s DB: %s' % (tstamp, text)
		self.logger.write('%s\n' % text)
		if self.logger != stderr:
			stderr.write('%s\n' % text)

	def create_table(self, table_name, schema):
		cur = self.conn.cursor()
		query = '''
			create table 
				if not exists 
				%s (%s)
		''' % (table_name, schema)
		cur.execute(query)
		self.commit()
		cur.close()

	def create_index(self, index, key):
		cur = self.conn.cursor()
		query = '''
			create index 
				if not exists 
				%s_%s on %s(%s)
		''' % (index, key, index, key)
		cur.execute(query)
		self.commit()
		cur.close()
	
	def commit(self):
		while True:
			try:
				self.conn.commit()
				return
			except:
				self.debug('failed to commit, retrying...')
				sleep(0.3)
	
	def insert(self, table, values):
		cur = self.conn.cursor()
		questions = ','.join(['?'] * len(values))
		query = '''
			insert into 
				%s 
				values (%s)
		''' % (table, questions)
		result = cur.execute(query, values)
		last_row_id = cur.lastrowid
		cur.close()
		return last_row_id
	
	def count(self, table, where='', values=[]):
		cur = self.select('count(*)', table, where=where, values=values)
		result = cur.fetchone()
		cur.close()
		return result[0]
	
	def select(self, what, table, where='', values=[]):
		cur = self.conn.cursor()
		query = '''
			select
				%s
				FROM
				%s
		''' % (what, table)
		if where != '':
			query += '''
				WHERE %s
			''' % where
		return cur.execute(query, values)
	
	def select_one(self, what, table, where='', values=[]):
		ex = self.select(what, table, where, values).fetchone()
		if ex == None:
			raise Exception('no rows returned')
		return ex[0]

	def delete(self, table, where, values=[]):
		cur = self.conn.cursor()
		query = '''
			delete from %s
				where %s
			''' % (table, where)
		cur.execute(query, values)
		cur.close()
	
	def update(self, table, changes, where, values=[]):
		cur = self.conn.cursor()
		query = '''
			update %s
				set %s
				where %s
		''' % (table, changes, where)
		cur.execute(query, values)
		cur.close()

	def get_config(self, key):
		cur = self.conn.cursor()
		query = '''
			select value
				from config
				where key = "%s"
		''' % key
		execur = cur.execute(query)
		result = execur.fetchone()
		cur.close()
		if result == None:
			return None
		return result[0]

	def set_config(self, key, value):
		cur = self.conn.cursor()
		query = '''
			insert or replace into
				config (key, value)
				values (?, ?)
		'''
		execur = cur.execute(query, [key, value])
		result = execur.fetchone()
		self.commit()
		cur.close()

if __name__ == '__main__':
	db = DB()
	db.insert('admins', ('asdf', 0))
	print db.count('admins')
	db.delete('admins', 'username = ?', ['asdf'])
	print db.count('admins')
	db.set_config('test', 'yes')
	print db.get_config('test')
