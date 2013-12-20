#!/usr/bin/python

'''
	Hacky script to migrate existing spam filters etc 
	from the old bot into the new database
'''

# Commands for injecting necessary values into DB:
#sqlite3 spambot.db "insert into config values ( 'reddit_pw', password )"
#sqlite3 spambot.db "insert into config values ( 'ignore_subreddits', '4_pr0n,reportthespammersNSFW' )"
#sqlite3 spambot.db "insert into config values ( 'gw_api_url', url )"

# TODO Remove /r/4_pr0n
UNREAL_SUBS = ['4_pr0n', 'RealGirls', 'Amateur']

CUSTOM_FILTERS = ['tumblr', 'blogspot']

from Reddit   import Reddit
from AmArch   import AmArch
from DB       import DB
from os       import path, listdir
from time     import gmtime
from calendar import timegm
from datetime import datetime
from sys      import exit

# Root of old version
oldroot = open('oldbot.root', 'r').read().strip()
lists = path.join(oldroot, 'lists')
logs = path.join(oldroot, 'logs')

db = DB() # Database instance

# TLD Filters (hard-coded in old version)
print '[ ] parsing tld filters'
tlds = ['info', 'biz', 'cat',   'in', 'ru', 'me', 'hu', \
        'eu', 're', 'so', 'pl', 'lv', 'kz', 'ac', 'gl', 'im', \
        'bz', 'de', 'ly', 'gs', 'su', 'la', 'sh', 'mu', 'us', \
        'cz', 'mx', 'cc', 'tk', 'ws', 'tw', 'ae', 'at', 'pw', \
        'dk']
for tld in tlds:
	if db.count('filters', 'type = "tld" and text = ?', [tld]) == 0:
		db.insert('filters', (None, 'tld', tld, '', 0, 1369477831, 1, 1))
db.commit()

# Thumb-spam filters (hard-coded in old version)
print '[ ] parsing thumb-spam filters'
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

print '[ ] parsing file: log.aabot'
for line in open(path.join(logs, 'log.aabot'), 'r'):
	line = line.strip()
	datepst = line[1:line.find(']')].replace(' PST', '')
	date = int(datetime.strptime(datepst, '%Y-%m-%d %H:%M:%S').strftime('%s'))
	fields = line.split(' ')
	if ' '.join(fields[3:6]) == 'posted more on':
		if db.count('log_sourced', 'permalink = ?', [fields[6]]) == 0:
			db.insert('log_sourced', (None, date, fields[6]))
			print '[+] inserted sourced url from %s' % fields[6]
	elif ' '.join(fields[3:6]) == 'removed request because':
		reason = line[line.find('removed request because ')+len('removed request because '):]
		reason = reason[:reason.find(':')]
		permalink = fields[-1]
		if db.count('log_amarch', 'permalink = ?', [permalink]) == 0:
			db.insert('log_amarch', ('removed', permalink, date, reason))
			print '[+] inserted amarch removal reason "%s" for %s' % (reason, permalink)
	elif 'removed blacklisted user in ' in line: 
		permalink = fields[-1]
		if db.count('log_amarch', 'permalink = ?', [permalink]) == 0:
			db.insert('log_amarch', ('removed', permalink, date, 'blacklisted user'))
			print '[+] inserted amarch removal reason "blacklisted user" for %s' % (permalink)
	elif 'removed blacklisted/illicit content' in line:
		permalink = fields[-1]
		if db.count('log_amarch', 'permalink = ?', [permalink]) == 0:
			db.insert('log_amarch', ('removed', permalink, date, 'blacklisted url'))
			print '[+] inserted amarch removal reason "blacklisted url" for %s' % (permalink)

db.commit()

# CUSTOM FILTERS (tumblr, blogspot)
print '[ ] parsing custom filters'
for custom in CUSTOM_FILTERS:
	if db.count('filters', 'type = ?', [custom]) == 0:
		db.insert('filters', (None, custom, '%s spam' % custom, '', 0, 1375265101, 1, 1))
		print '[+] filters: inserted custom filter "%s"' % custom

# ADMINS
print '[ ] parsing file: list.admins'
for line in open(path.join(lists, 'list.admins'), 'r'):
	line = line.strip().lower()
	if line == '': continue
	try:
		db.insert('admins', (line, 0, ) )
		print '[+] admins: added admin "%s"' % line
	except: pass
db.commit()

# SUBS TO LOOK FOR & PROVIDE SOURCE
print '[ ] parsing file: list.subs.source'
for line in open(path.join(lists, 'list.subs.source'), 'r'):
	line = line.strip()
	try:
		db.insert('subs_source', (line, ) )
		print '[+] subs_source: added sub to source "%s"' % line
	except: pass
db.commit()

print '[ ] parsing "unreal" subs'
for sub in UNREAL_SUBS:
	try:
		db.insert('subs_unreal', (sub,) )
		print '[+] subs_unreal: added sub "%s" for unreal checks' % sub
	except: pass
db.commit()

# MODERATED SUBREDDITS
print '[ ] parsing file: log.mod.subs'
for line in open(path.join(logs, 'log.mod.subs'), 'r'):
	line = line.strip()
	try:
		db.insert('subs_mod', (line, ) )
		print '[+] subs_mod: added sub to mod "%s"' % line
	except: pass
db.commit()

# SPAM FILTER (author, type, filter, date)
print '[ ] parsing file: log.spamfilter'
for line in open(path.join(logs, 'log.spamfilter'), 'r'):
	line = line.strip()
	datepst = line[1:line.find(']')].replace(' PST', '')
	date = int(datetime.strptime(datepst, '%Y-%m-%d %H:%M:%S').strftime('%s'))
	fields = line.split(' ')
	if 'PST]' in fields: fields.remove('PST]')
	credit = fields[2]
	if credit == 'the_bot': credit = ''
	action = fields[3]
	spamtype = fields[4]
	if spamtype == 'word': spamtype = 'text'
	spamtext = line[line.rfind('filter: "')+len('filter: "'):-1]
	if db.count('filters', 'type = ? and text = ?', [spamtype, spamtext]) == 0:
		try:
			filterid = db.insert('filters', (None, spamtype, spamtext, credit, 0, date, 1, 1))
			print '[+] filters: added %s filter "%s" for %s at %d' % (spamtype, spamtext, credit, date)
		except Exception, e:
			print '[!] %s' % str(e)
			continue
	else:
		filterid = db.select_one('id', 'filters', 'type = ? and text = ?', [spamtype, spamtext])
	if action == 'removed':
		#db.delete('filters', 'type = ? and text = ?', [spamtype, spamtext])
		db.update('filters', 'active = 0', 'type = ? and text = ?', [spamtype, spamtext])
		print '[+] filters: removed %s filter "%s" for %s at %d' % (spamtype, spamtext, credit, date)
	else:
		db.update('filters', 'active = 1', 'id = ?', [filterid])
	if db.count('log_filters', 'filterid = ? and user = ? and action = ? and date = ?', [filterid, credit, action, date]) == 0:
		db.insert('log_filters', (filterid, credit, action, date))
db.commit()


# SPAM FILTER (scores)
print '[ ] parsing file: list.spamfilter'
for line in open(path.join(lists, 'list.spamfilter'), 'r'):
	line = line.strip()
	(spamtype, credit, score, spamtext) = line.split('|')
	oldscore = db.select('count', 'filters', 'type = ? and text = ?', [spamtype, spamtext]).fetchone()
	if oldscore != None and oldscore[0] < score:
		db.update('filters', 'count = ?', 'type = ? and text = ?', [int(score), spamtype, spamtext])
		print '[+] filters: updated %s filter "%s" for %s with score %d' % (spamtype, spamtext, credit, int(score))
db.commit()


# ADMIN SCORES
print '[ ] parsing file: log.scores'
for line in open(path.join(logs, 'log.scores'), 'r'):
	line = line.strip()
	if line == '': continue
	(username, score, filters) = line.split('|')
	db.update('admins', 'score = ?', 'username like ?', [int(score), username])
	print '[+] admins: updated admin %s with score %d' % (username, int(score))


# REMOVED SPAM
for fil in listdir(logs):
	if fil != 'log.spam' and not fil.startswith('log.spam.'): continue
	# pass
	print '[ ] parsing file:',fil
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
				#print '[!] log_removed: no filter found for type %s, text "%s"' % (spamtype, spamtext)
				continue
			filterid = result[0]
			db.insert('log_removed', (filterid, posttype, permalink, credit, date))
			print '[+] log_removed: added removed %s: %s filter "%s" for %s at %d (%s)' % (posttype, spamtype, spamtext, credit, date, permalink)
	db.commit()


# Login to reddit
print '[ ] logging in to reddit'
password = db.get_config('reddit_pw')
Reddit.login('rarchives', password)

print '[ ] executing amarch...'
def log(txt): print txt
AmArch.execute(db, log)

# MODERATED SUBS (real-time)
print '[ ] loading modded subs...'
current = Reddit.get_modded_subreddits()
print '[ ] found %d modded subs' % len(current)
for ignore in db.get_config('ignore_subreddits').split(','):
	if ignore in current:
		print '[-] removing ignored subreddit: %s' % ignore
		current.remove(ignore)
existing = []
for (sub, ) in db.select('subreddit', 'subs_mod'):
	if not sub in current:
		print '[-] subs_mod: deleting existing sub (no longer a mod): %s' % sub
		db.delete('subs_mod', 'subreddit = ?', [sub])
	else:
		existing.append(sub)
for sub in current:
	if not sub in existing:
		print '[+] subs_mod: inserting new sub into db: %s' % sub
		db.insert('subs_mod', (sub, ) )
db.commit()

# APPROVED SUBMITTERS
for sub in current:
	count = 0
	try:
		print '[ ] loading approved submitters for /r/%s' % sub,
		for user in Reddit.get_approved_submitters(sub):
			if db.count('subs_approved', 'subreddit = ? and username = ?', [sub, user]) == 0:
				db.insert('subs_approved', (sub, user))
				count += 1
		print '[+] subs_approved: added %d contributors' % count
		if count > 0:
			db.commit()
	except Exception, e:
		print '[!] %s' % str(e)
	# MODERATORS
	try:
		print '[ ] loading moderators for /r/%s' % sub,
		for user in Reddit.get_moderators(sub):
			if db.count('subs_approved', 'subreddit = ? and username = ?', [sub, user]) == 0:
				db.insert('subs_approved', (sub, user))
				count += 1
		print '[+] subs_approved: added %d moderators' % count
		if count > 0:
			db.commit()
	except Exception, e:
		print '[!] %s' % str(e)

