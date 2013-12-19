#!/usr/bin/python

'''
	Glue between reddit objects and the spam filter database
'''

from time      import gmtime, sleep
from calendar  import timegm
from Reddit    import Post, Comment, Child
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
		if db.count('admins', 'username = ?', [pm.author.lower()]) == 0:
			# PM is not from an admin. ignore it.
			raise Exception('Non-Admin PM: %s' % str(pm))

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
				response += '[**!**] Not enough required fields in line "%s" (expected 3+, got %d)\n\n' % (line, len(fields))
				continue
			while len(fields) > 3: fields[-1] = fields.pop(-1) + ' ' + fields[-1]
			(action, spamtype, spamtext) = fields
			action = action.replace(':', '')
			spamtype = spamtype.replace(':', '')

			if action not in Filter.ACTIONS:
				# Undefined action
				response += '[**!**] Undefined action: "%s" (expected one of %s)\n\n' % (action, ', '.join(Filter.ACTIONS))
				continue
			if spamtype not in Filter.TYPES:
				# Undefined spam type
				response += '[**!**] Unable to %s: Undefined type of spam filter: "%s" (expected one of %s)\n\n' % (action, spamtype, ', '.join(Filter.TYPES))
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
					response += '[**!**] Unable to add filter: Filter already exists for %s filter "%s"\n\n' % (spamtype, spamtext)
				elif db.count('filters', 'type = ? and text = ? and active = 0', [spamtype, spamtext]) > 0:
					# Filter exists but is inactive (removed)
					db.update('filters', 'active = 1', 'type = ? and text = ?', [spamtype, spamtext])
					filterid = db.select_one('id', 'filters', 'type = ? and text = ?', [spamtype, spamtext])
					db.insert('log_filters', (filterid, pm.author, 'activate', timegm(gmtime())))
					response += '[**+**] Successfully activated %s filter "%s"\n\n' % (spamtype, spamtext)
				else:
					filterid = db.insert('filters', (None, spamtype, spamtext, pm.author, 0, timegm(gmtime()), True, 1 if is_spam else 0))
					db.insert('log_filters', (filterid, pm.author, action, timegm(gmtime())))
					response += '[**+**] Successfully added %s "%s" to the spam filter\n\n' % (spamtype, spamtext)
			elif action == 'remove':
				# Request to remove filter
				if db.count('filters', 'type = ? and text = ?', [spamtype, spamtext]) == 0:
					response += '[**!**] Unable to remove filter: Filter does not exist for %s filter "%s"\n\n' % (spamtype, spamtext)
				elif db.count('filters', 'type = ? and text = ? and active = 1', [spamtype, spamtext]) == 0:
					response += '[**!**] Unable to remove filter: Filter is not active for %s filter "%s"\n\n' % (spamtype, spamtext)
				else:
					db.update('filters', 'active = 0', 'type = ? and text = ?', [spamtype, spamtext])
					filterid = db.select_one('id', 'filters', 'type = ? and text = ?', [spamtype, spamtext])
					db.insert('log_filters', (filterid, pm.author, action, timegm(gmtime())))
					response += '[**-**] Successfully deactivated %s filter "%s"' % (spamtype, spamtext)
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
		whitelist = []
		if spamtype == 'link' or spamtype == 'text' or spamtype == 'thumb':
			for whitelisted in ['reddit.com', 'reddit.com/r/', 'imgur.com', 'imgur.com/a/', 'min.us', 'minus.com']:
				if whitelisted in spamtext or \
				   spamtext    in whitelisted:
					raise Exception('[**!**] Unable to add filter: Failed sanity test -- might remove relevant "%s" links\n\n' % whitelisted)

		elif spamtype == 'tld':
			if spamtext in ['com', 'net', 'org']:
				raise Exception('[**!**] Unable to add filter: Failed sanity test -- might remove relevant "%s" links\n\n' % whitelisted)

		elif spamtype == 'user':
			if db.count('admins', 'username like ?', [spamtext]) > 0:
				raise Exception('[**!**] Unable to add filter: Failed sanity test -- might remove relevant "%s" links\n\n' % whitelisted)


	@staticmethod
	def detect_spam(child, db, log):
		''' 
			Detects if a reddit Child is spam.
			Returns:
				Tuple.
				[0] is the id of the filter that applied in the 'filters' table
				[1] is the user that gets the credit for the removal
				[2] boolean, true:  post should be removed as spam,
				             false: post should be removed as ham
			Raises:
				Exception if the post is NOT spam
		'''
		# Check that the child is not already approved/banned
		if child.approved_by != None:
			raise Exception('%s is approved by /u/%s' % (child.permalink(), child.approved_by))
		if child.banned_by != None:
			raise Exception('%s is already banned by /u/%s' % (child.permalink(), child.banned_by))

		# Check if child author is an approved submitter/moderator
		if db.count('subs_approved', 'subreddit = ? and username = ?', [child.subreddit, child.author]) > 0:
			raise Exception('/u/%s is approved contributor: %s' % (child.author, child.permalink()))

		# Get 'text' and 'urls' for a reddit child
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

		# Thumb-spam check
		for url in urls:
			if 'imgur.com/a/' in url:
				if db.count('checked_albums', 'url = ?', [url]) > 0:
					continue # already checked
				# Need to check album for spam links
				httpy = Httpy()
				try:
					log('Filter.detect_spam: Checking %s for thumb-spam...' % url)
					unicode_resp = httpy.get(url)
					r = unicode_resp.decode('UTF-8').encode('ascii', 'ignore')
					db.insert('checked_albums', (url,) )
					for (spamid, spamtext, credit, is_spam) in db.select('id, text, author, isspam', 'filters', 'type = "thumb" and active = 1'):
						if spamtext in r:
							return (spamid, credit, is_spam)
				except Exception, e:
					# Error while loading album (404?)
					db.insert('checked_albums', (url,) )
				sleep(0.5)

		# Check if child's text/urls match any filters in the db
		for (spamid, spamtype, spamtext, credit, is_spam) in db.select('id, type, text, author, isspam', 'filters', 'type != "thumb" and active = 1'):
			is_spam = (is_spam == 1)
			if spamtype == 'user' and child.author.lower() == spamtext.lower():
				return (spamid, credit, is_spam)
			elif spamtype == 'link':
				for url in urls:
					if spamtext.lower() in url.lower():
						return (spamid, credit, is_spam)
			elif spamtype == 'text':
				if spamtext.lower() in text.lower():
					return (spamid, credit, is_spam)
			elif spamtype == 'tld':
				for url in urls:
					tld = url.lower().replace('http://', '').replace('https://', '').split('/')[0]
					tld = tld.split('.')[-1]
					if tld == spamtext.lower():
						return (spamid, credit, is_spam)
			elif spamtype == 'tumblr':
				for url in urls:
					url = url.lower()
					if '.tumblr.com' in url and not 'media.tumblr.com' in url:
						return (spamid, credit, is_spam)
			elif spamtype == 'blogspot':
				for url in urls:
					url = url.lower()
					if 'blogspot.' in url and url.split('.')[-1].lower() not in ['jpg', 'jpeg', 'gif', 'png']:
						return (spamid, credit, is_spam)

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
			(filterid, credit, is_spam) = Filter.detect_spam(child, db, log)
			# Needs to be removed
			child.remove(mark_as_spam=is_spam)
			now = timegm(gmtime())
			(spamtype, spamtext, author, count) = db.select('type, text, author, count', 'filters', 'id = ?', [filterid]).fetchone()
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
			db.insert('log_removed', ( filterid, posttype, child.permalink(), credit, timegm(gmtime()) ))
			db.update('filters', 'count = count + 1', 'id = ?', [filterid])
			db.update('admins',  'score = score + 1', 'username = ?', [credit])
			return True
		except Exception, e:
			# Not spam, or something else went wrong
			if not 'was not detected' in str(e) and \
			   not 'approved by' in str(e) and \
				 not 'banned by' in str(e):
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

