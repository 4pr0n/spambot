#!/usr/bin/python

'''
	Glue between reddit objects and the spam filter database
'''

from time      import gmtime, sleep
from calendar  import timegm
from Reddit    import Post, Comment, Child, Message
from Httpy     import Httpy
from traceback import format_exc

class Filter(object):
	ACTIONS = ['add', 'remove']
	TYPES   = ['link', 'user', 'text', 'tld', 'thumb']


	@staticmethod
	def parse_pm(pm, db):
		'''
			Parses private message,
			Ensures PM is from an admin,
			Adds/removes filters from DB accordingly,
			Returns appropriate response
			Args:
				pm: Reddit.Message representing the PM
				db: Database instance
			Returns:
				Reddit-markdown'd response explaining what happened
				empty string if no response is appropriate
			Raises:
				Exception if PM should not be replied to
		'''
		# Check for moderator invites
		if type(pm) == Message and pm.has_mod_invite():
			if not pm.accept_mod_invite():
				raise Exception('failure when accepting mod invite for /r/%s:\n%s' % (pm.subreddit, str(pm)))
			if db.count('subs_mod', 'subreddit like ?', [pm.subreddit]) > 0:
				raise Exception('accepted invite to /r/%s (but it is already in the db)' % pm.subreddit)
			db.insert('subs_mod', (pm.subreddit, ))
			raise Exception('accepted invite to /r/%s, added to db' % pm.subreddit)

		if type(pm) == Comment:
			raise Exception('comment from /u/%s:\n%s' % (pm.author, pm.body))
		if db.count('admins', 'username = ?', [pm.author.lower()]) == 0:
			# PM is not from an admin. ignore it.
			raise Exception('PM from *non-admin* /u/%s:\n%s' % (pm.author, pm.body))
		if pm.subject != 'dowhatisay' and not pm.subject == 're: dowhatisay':
			raise Exception('PM (subj: "%s") from *admin* /u/%s:\n%s' % (pm.subject, pm.author, pm.body))

		response = ''
		for line in pm.body.split('\n'):
			line = line.strip().lower()
			if line == '': continue
			fields = line.split(' ')
			is_spam = True
			if fields[1] in ['non-spam', 'nonspam', 'not-spam', 'notspam', 'no-spam', 'nospam']:
				fields.pop(1)
				is_spam = False
			if len(fields) < 3:
				# Not enough fields
				response += '[**!**] Not enough required fields in line `%s`. Expected 3 or more, got `%d`.\n\n' % (line, len(fields))
				continue
			while len(fields) > 3:
				t = fields.pop(-1)
				fields[-1] += ' ' + t
			(action, spamtype, spamtext) = fields
			action = action.replace(':', '')
			spamtype = spamtype.replace(':', '')

			if action not in Filter.ACTIONS:
				# Undefined action
				response += '[**!**] Undefined action: `%s`. Expected one of the following: `%s`\n\n' % (action, ', '.join(Filter.ACTIONS))
				continue
			if spamtype not in Filter.TYPES:
				# Undefined spam type
				response += '[**!**] Unable to %s filter: Undefined type of spam filter: "`%s`". Expected one of the following: `%s`\n\n' % (action, spamtype, ', '.join(Filter.TYPES))
				continue

			if action == 'add':
				# Request to add filter
				try:
					# Ensure the request is not crazy (tld: .com, url: imgur, etc)
					Filter.sanity_check(db, spamtype, spamtext)
				except Exception, e:
					response += str(e)
					continue
				# Ensure filter does not already exist
				if db.count('filters', 'type = ? and text = ? and active = 1', [spamtype, spamtext]) > 0:
					response += '[**!**] Unable to add filter: Filter already exists for [%s filter "%s"](http://spambot.rarchives.com/#filter=%s&text=%s)\n\n' % (spamtype, spamtext, spamtype, spamtext)
				elif db.count('filters', 'type = ? and text = ? and active = 0', [spamtype, spamtext]) > 0:
					# Filter exists but is inactive (removed)
					db.update('filters', 'active = 1', 'type = ? and text = ?', [spamtype, spamtext])
					filterid = db.select_one('id', 'filters', 'type = ? and text = ?', [spamtype, spamtext])
					db.insert('log_filters', (filterid, pm.author, 'added', timegm(gmtime())))
					response += '[**+**] Successfully enabled [%s filter "%s"](http://spambot.rarchives.com/#filter=%s&text=%s)\n\n' % (spamtype, spamtext, spamtype, spamtext)
				else:
					filterid = db.insert('filters', (None, spamtype, spamtext, pm.author, 0, timegm(gmtime()), True, 1 if is_spam else 0))
					db.insert('log_filters', (filterid, pm.author, 'added', timegm(gmtime())))
					response += '[**+**] Successfully added [%s "%s"](http://spambot.rarchives.com/#filter=%s&text=%s) to the %s filter\n\n' % (spamtype, spamtext, spamtype, spamtext, 'spam' if is_spam else 'remove')
			elif action == 'remove':
				# Request to remove filter
				if db.count('filters', 'type = ? and text = ?', [spamtype, spamtext]) == 0:
					response += '[**!**] Unable to remove filter: There are no `%s` filters for "`%s`".\n\n' % (spamtype, spamtext)
				elif db.count('filters', 'type = ? and text = ? and active = 1', [spamtype, spamtext]) == 0:
					response += '[**!**] Unable to remove filter: The `%s` filter "`%s`" is not currently enabled.\n\n' % (spamtype, spamtext)
				else:
					db.update('filters', 'active = 0', 'type = ? and text = ?', [spamtype, spamtext])
					filterid = db.select_one('id', 'filters', 'type = ? and text = ?', [spamtype, spamtext])
					db.insert('log_filters', (filterid, pm.author, 'removed', timegm(gmtime())))
					response += '[**-**] Successfully disabled [%s filter "%s"](http://spambot.rarchives.com/#filter=%s&text=%s)\n\n' % (spamtype, spamtext, spamtype, spamtext)
		if response == '':
			raise Exception('No response for PM: %s' % str(pm))
		return response


	@staticmethod
	def sanity_check(db, spamtype, spamtext):
		'''
			Ensures the spam filter is not malicious.
			Raises:
				Exception if filter is malicious and should not be added.
		'''
		spamtext = spamtext.lower()
		whitelist = [
				# URLS
				'http://reddit.com/r/',
				'http://reddit.com/comments/',
				'http://www.reddit.com/r/',
				'http://www.reddit.com/comments',
				'http://imgur.com/',
				'http://imgur.com/a/',
				'http://i.imgur.com/',
				'http://www.imgur.com/',
				'http://www.imgur.com/a/',
				'http://i.rarchives.com/'
				'http://www.rarchives.com/',
				'http://rip.rarchives.com/',
				# TEXT - TODO Get a better text whitelist
				'''the quick brown fox jumped over the lazy dog'''
			]
		if spamtype == 'link' or spamtype == 'text':
			if len(spamtext) <= 3:
				raise Exception('[**!**] `%s` filter "`%s`" was **not** added because it is not long enough (must be more than 3 characters long).\n\n' % (spamtype, spamtext))
			for whitelisted in whitelist:
				if spamtext in whitelisted.lower():
					raise Exception('[**!**] `%s` filter "`%s`" was **not** added because it might remove relevant posts/comments (e.g. `%s...`).\n\n' % (spamtype, spamtext, whitelisted))

		elif spamtype == 'tld':
			if spamtext in ['com', 'net', 'org']:
				raise Exception('[**!**] TLD `%s` was **not** added because it might remove relevant links (e.g. `.com` or `.net` or `.org`).\n\n' % spamtext)

		elif spamtype == 'user':
			if db.count('admins', 'username like ?', [spamtext]) > 0:
				raise Exception('[**!**] User `%s` was **not** added because you cannot add an admin to the spam filter\n\n' % spamtext)

		elif spamtype == 'thumb':
			# To validate the thumb-spam filter, load a non-spam imgur album and test the filter on that
			httpy = Httpy()
			unicode_resp = httpy.get('http://imgur.com/a/RdXNa')
			r = unicode_resp.decode('UTF-8').encode('ascii', 'ignore')
			if spamtext in r:
				raise Exception('[**!**] Thumb-spam filter `%s` was **not** added because the bot detected a false-positive (non-spam imgur albums would be detected as spam).\n\n' % spamtext)


	@staticmethod
	def detect_spam(child, db, log):
		''' 
			Detects if a reddit Child is spam.
			Returns:
				ID of filter that detected the spam
			Raises:
				Exception if the post is NOT spam
		'''
		# Check that the child is not already approved/banned
		if child.approved_by != None:
			raise Exception('%s is approved by /u/%s' % (child.permalink(), child.approved_by))
		if child.banned_by != None:
			raise Exception('%s is already banned by /u/%s' % (child.permalink(), child.banned_by))

		# Check if child author is an approved submitter/moderator
		if db.count('subs_approved', 'subreddit like ? and username like ?', [child.subreddit, child.author]) > 0:
			raise Exception('/u/%s is approved contributor: %s' % (child.author, child.permalink()))

		# Get 'text' and 'urls' from the reddit child
		if type(child) == Post:
			text = child.title
			if child.selftext != None:
				text += ' ' + child.selftext
				urls = Filter.get_links_from_text(child.selftext)
			else:
				text += ' ' + child.url
				urls = [child.url]
		elif type(child) == Comment:
			urls = Filter.get_links_from_text(child.body)
			text = child.body

		# Check if child's text/urls match any filters in the db

		# User filter
		for (filterid,) in db.select('id', 'filters', "type = 'user' and active = 1 and text like ?", [child.author]):
			return filterid

		# TLD filter
		if len(urls) > 0:
			tlds = ' ' # Join all TLDs with spaces
			for url in urls:
				tld = url.lower().replace('http://', '').replace('https://', '').split('/')[0]
				tld = tld.split('.')[-1]
				tlds = '%s%s ' % (tlds, tld)
			for (filterid,) in db.select('id', 'filters', "type = 'tld' and active = 1 and ? like '%' || text || '%'", [tlds]):
				return filterid

		# Link filter
		if len(urls) > 0:
			where = '''
				type = 'link'
					AND
				active = 1
					AND
				? like '%' || text || '%'
			'''
			for (filterid,) in db.select('id', 'filters', where, [' '.join(urls)]):
				return filterid

		# Text filter
		where  = '''
			type = 'text' and active = 1
			AND (
				(? like '%' || text || '%')
					OR
				(? like '%' || text || '%')
			)
		'''
		for (filterid,) in db.select('id', 'filters', where, [text,' '.join(urls)]):
			return filterid

		if len(urls) > 0:
			# Tumblr and blogspot filters
			for url in urls:
				url = url.lower()
				if '.tumblr.com' in url and not 'media.tumblr.com' in url:
					for (filterid,) in db.select('id', 'filters', "type = 'tumblr' and active = 1"):
						return filterid
				if 'blogspot.' in url and url.split('.')[-1].lower() not in ['jpg', 'jpeg', 'gif', 'png']:
					for (filterid,) in db.select('id', 'filters', "type = 'blogspot' and active = 1"):
						return filterid

		# Thumb-spam check
		for url in urls:
			if 'imgur.com/a/' in url:
				if db.count('checked_albums', 'url = ?', [url]) > 0:
					continue # already checked
				# Need to check album for spam links
				httpy = Httpy()
				try:
					#log('Filter.detect_spam: Checking %s for thumb-spam...' % url)
					unicode_resp = httpy.get(url)
					r = unicode_resp.decode('UTF-8').encode('ascii', 'ignore')
					db.insert('checked_albums', (url,) )
					for (filterid, spamtext) in db.select('id, text', 'filters', "type = 'thumb' and active = 1"):
						if spamtext in r:
							return filterid
				except Exception, e:
					# Error while loading album (404?)
					db.insert('checked_albums', (url,) )
				sleep(0.5)

		# TODO whois filter (use external service?)

		raise Exception('child was not detected as spam')


	@staticmethod
	def handle_child(child, db, log):
		'''
			Checks if child is spam. If so, removes from reddit & updates DB.

			Args:
				child: Reddit object to check
				db:    Database instance
				log:   Logging function
		'''
		try:
			# detect_spam will throw an exception if it does not detect the child as spam
			filterid = Filter.detect_spam(child, db, log)
			# Needs to be removed
			now = timegm(gmtime())
			(spamtype, spamtext, author, count, is_spam) = db.select('type, text, author, count, isspam', 'filters', 'id = ?', [filterid]).fetchone()
			child.remove( mark_as_spam=(is_spam == 1) )
			if type(child) == Comment:
				posttype = 'comment'
				msg  = 'Filter.handle_child: Removing comment by /u/%s\n' % child.author
				msg += '   Reason: Detected %s\'s %s filter "%s" (%d)\n' % (author, spamtype, spamtext, count)
				msg += '     Body: %s\n' % child.body.replace('\n', ' ')[:50]
			elif type(child) == Post:
				posttype = 'post'
				msg  = 'Filter.handle_child: Removing post by /u/%s\n' % child.author
				msg += '   Reason: Detected %s\'s %s filter "%s" (%d)\n' % (author, spamtype, spamtext, count)
				msg += '    Title: %s\n' % child.title.replace('\n', ' ')[:50]
				if child.selftext != None:
					msg += 'Self-text: %s\n' % child.selftext.replace('\n', ' ')[:50]
				else:
					msg += '      URL: %s\n' % child.url
			msg += 'Permalink: %s\n' % child.permalink()
			log(msg)
			db.insert('log_removed', ( filterid, posttype, child.permalink(), author, timegm(gmtime()) ))
			db.update('filters', 'count = count + 1', 'id = ?', [filterid])
			db.update('admins',  'score = score + 1', 'username = ?', [author])
			db.commit()
			return True
		except Exception, e:
			# Not spam, or something else happened; child was not removed
			if not 'was not detected' in str(e) and \
			   not 'approved by' in str(e) and \
				 not 'banned by' in str(e) and \
				 not 'approved contributor' in str(e):
				# Log the exception if it's not expected
				log('Filter.handle_child: Exception: %s' % str(e))
				log(format_exc())
		return False


	@staticmethod
	def update_modded_subs(db, log):
		'''
			Retrieves list of moderated subreddits, updates database
		'''
		current = Reddit.get_modded_subreddits()
		for ignore in db.get_config('ignore_subreddits').split(','):
			if ignore in current:
				current.remove(ignore)
		if len(current) == 0: return # We expect at least one subreddit
		existing = []
		for (sub, ) in db.select('subreddit', 'subs_mod'):
			if not sub in current:
				log('Filter.update_modded_subs: deleting existing sub, no longer a mod: /r/%s' % sub)
				db.delete('subs_mod', 'subreddit = ?', [sub])
			else:
				existing.append(sub)
		for sub in current:
			if not sub in existing:
				log('Filter.update_modded_subs: adding new moderated sub: /r/%s' % sub)
				db.insert('subs_mod', (sub, ) )
		db.commit()

	@staticmethod
	def update_approved_submitters(subreddit, db, log):
		count = 0
		try:
			for user in Reddit.get_approved_submitters(sub):
				if db.count('subs_approved', 'subreddit = ? and username = ?', [sub, user]) == 0:
					db.insert('subs_approved', (sub, user))
					count += 1
		except: pass
		try:
			for user in Reddit.get_moderators(sub):
				if db.count('subs_approved', 'subreddit = ? and username = ?', [sub, user]) == 0:
					db.insert('subs_approved', (sub, user))
					count += 1
		except: pass
		if count > 0:
			log('Filter.update_approved_submitters: Added %d contributors to /r/%s' % (count, subreddit))
			db.commit()


	@staticmethod
	def get_links_from_text(text):
		'''
			Returns list of URLs from given text (e.g. comment or selftext)
		'''
		urls = []
		i = -1
		while True:
			i = text.find('://', i+1)
			if i == -1: break
			j = i
			while j < len(text) and text[j] not in [')', ']', ' ', '"', '\n', '\t']:
				j += 1
			urls.append('http%s' % text[i:j])
			i = j
		return list(set(urls)) # Kill duplicates

if __name__ == '__main__':
	from DB import DB
	db = DB()
	print Filter.sanity_check(db, 'text', 'imgur.com')
