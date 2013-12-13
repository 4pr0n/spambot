#!/usr/bin/python

'''
	Hacky script to migrate existing spam filters etc 
	from the old bot into the new database
'''

#sqlite3 spambot.db "insert into config values ( 'reddit_pw', password )"
#sqlite3 spambot.db "insert into config values ( 'ignore_subreddits', '4_pr0n,reportthespammersNSFW' )"

from DB import DB
from Reddit import Reddit
from time import gmtime
from calendar import timegm
from datetime import datetime
from os import path, listdir

db = DB()

tlds = ['info', 'biz', 'cat', 'in', 'ru', 'me', 'hu', \
		 'eu', 're', 'so', 'pl', 'lv', 'kz', 'ac', 'gl', 'im', \
		 'bz', 'de', 'ly', 'gs', 'su', 'la', 'sh', 'mu', 'us', \
		 'cz', 'mx', 'cc', 'tk', 'ws', 'tw', 'ae', 'at', 'pw', \
		 'dk']
for tld in tlds:
	if db.count('filters', 'type = "tld" and text = ?', [tld]) == 0:
		db.insert('filters', (None, 'tld', tld, '', 0, 1369477831, 1, 1))
db.commit()

thumbs = ['hq gif',
		'imgserve.net',
		'cn-hd.org',
		'exgirlfriend-photos.com',
		'pornstr8.com',
		'sexvideogif.com',
		'niceandquite.com',
		'selfshot.us',
		'.tumblr.com/',
		'dailynsfwhd.com',
		'imgtiger.com',
		'selfpicamateurs',
		'amateurdump.info',
		'click below',
		'assno1.com',
		'gifsfor.com',
		'xxxbunker.com',
		'teenxxxtubes.com',
		'classybro',
		'porn.com/',
		'raxionmedia',
		'vipescorts']
for thumb in thumbs:
	if db.count('filters', 'type = "thumb" and text = ?', [thumb]) == 0:
		db.insert('filters', (None, 'thumb', thumb, '', 0, 1375265101, 1, 1))
db.commit()

lists = '/Users/derv82/Sites/aabot/lists/'
logs = '/Users/derv82/Sites/aabot/logs/'

for line in open(path.join(lists, 'list.admins'), 'r'):
	line = line.strip().lower()
	try:
		db.insert('admins', (line, ) )
		print 'added admin "%s"' % line
	except: pass
db.commit()

for line in open(path.join(lists, 'list.subs.source'), 'r'):
	line = line.strip()
	try:
		db.insert('subs_source', (line, ) )
		print 'added sub to source "%s"' % line
	except: pass
db.commit()


for line in open(path.join(logs, 'log.mod.subs'), 'r'):
	line = line.strip()
	try:
		db.insert('subs_mod', (line, ) )
		print 'added sub to mod "%s"' % line
	except: pass
db.commit()

for line in open(path.join(logs, 'log.spamfilter'), 'r'):
	line = line.strip()
	datepst = line[1:line.find(']')].replace(' PST', '')
	date = int(datetime.strptime(datepst, '%Y-%m-%d %H:%M:%S').strftime('%s'))
	fields = line.split(' ')
	if 'PST]' in fields: fields.remove('PST]')
	credit = fields[2]
	action = fields[3]
	spamtype = fields[4]
	if spamtype == 'word': spamtype = 'text'
	spamtext = line[line.rfind('filter: "')+len('filter: "'):-1]
	if db.count('filters', 'type = ? and text = ?', [spamtype, spamtext]) == 0:
		try:
			db.insert('filters', (None, spamtype, spamtext, credit, 0, date, 1, 1))
			print 'added %s filter "%s" for %s at %d' % (spamtype, spamtext, credit, date)
		except Exception, e:
			print str(e)
	if action == 'removed':
		#db.delete('filters', 'type = ? and text = ?', [spamtype, spamtext])
		db.update('filters', 'active = 0', 'type = ? and text = ?', [spamtype, spamtext])
		print 'removed %s filter "%s" for %s at %d' % (spamtype, spamtext, credit, date)
db.commit()


# Update counts on spam filters
for line in open(path.join(lists, 'list.spamfilter'), 'r'):
	line = line.strip()
	(spamtype, credit, score, spamtext) = line.split('|')
	db.update('filters', 'count = ?', 'type = ? and text = ?', [int(score), spamtype, spamtext])
	print 'updated %s filter "%s" for %s with score %d' % (spamtype, spamtext, credit, int(score))
db.commit()

for fil in listdir(logs):
	if fil != 'log.spam' and not fil.startswith('log.spam.'): continue
	# pass
	print 'parsing file:',fil
	for line in open(path.join(logs, fil), 'r'):
		line = line.strip()
		datepst = line[1:line.find(']')].replace(' PST', '')
		date = int(datetime.strptime(datepst, '%Y-%m-%d %H:%M:%S').strftime('%s'))
		fields = line.split(' ')
		if fields[-2] == '+1':
			credit = fields[-1].lower()
			permalink = fields[-3]
			posttype = fields[-4][:-1]
		else:
			credit = ''
			permalink = fields[-1]
			posttype = fields[-2][:-1]
		if fields[2] == 'PST]': fields.pop(2)
		spamtype = fields[5]
		if spamtype == 'word': spamtype = 'text'
		spamtext = line[line.rfind(' "')+len(' "'):]
		spamtext = spamtext[:spamtext.find('" in ')]
		if spamtext in ['thumb-spam', 'tumblr-spam', 'spammy-TLD']: continue
		if db.count('log_removed', 'permalink = ? and date = ?', [permalink, date]) == 0:
			result = db.select('id', 'filters', 'type = ? and text = ?', [spamtype, spamtext]).fetchone()
			if result == None:
				#print 'no filter found for type %s, text "%s"' % (spamtype, spamtext)
				continue
			filterid = result[0]
			db.insert('log_removed', (filterid, posttype, permalink, credit, date))
			print 'added removed %s: %s filter "%s" for %s at %d (%s)' % (posttype, spamtype, spamtext, credit, date, permalink)
	db.commit()


password = db.get_config('reddit_pw')
print 'logging in...'
Reddit.login('rarchives', password)

print 'loading blacklisted users...'
users = Reddit.get_blacklisted_users()
for user in users:
	if db.count('blacklist_users', 'username = ?', [user]) == 0:
		db.insert('blacklist_users', (user, ))
		print 'inserted %s into blacklist_users' % user

print 'loading modded subs...'
current = Reddit.get_modded_subreddits()
print 'found %d modded subs' % len(current)
for ignore in db.get_config('ignore_subreddits').split(','):
	if ignore in current:
		print 'removing ignored subreddit: %s' % ignore
		current.remove(ignore)
existing = []
for (sub, ) in db.select('subreddit', 'subs_mod'):
	if not sub in current:
		print 'deleting existing sub (no longer a mod): %s' % sub
		db.delete('subs_mod', 'subreddit = ?', [sub])
	else:
		existing.append(sub)
for sub in current:
	if not sub in existing:
		print 'inserting new sub into db: %s' % sub
		db.insert('subs_mod', (sub, ) )
db.commit()

'''
# Approved submitters
for sub in current:
	print 'loading approved submitters for /r/%s' % sub
	for user in Reddit.get_approved_submitters(sub):
		if db.count('subs_approved', 'subreddit = ? and user = ?', [sub, user]) == 0:
			db.insert('subs_approved', (sub, user))
db.commit()
'''
