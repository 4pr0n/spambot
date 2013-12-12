#!/usr/bin/python

'''
	Glue between reddit objects and the spam filter database
'''

from time     import gmtime, sleep
from calendar import timegm
from Reddit   import Post, Child
from Httpy    import Httpy

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
		'''
		if db.count('admins', 'username = ?', [pm.author.lower()]) == 0:
			# PM is not from an admin. ignore it.
			return ''

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
				response += '[ **!** ] Not enough required fields in line "%s" (expected 3+, got %d)\n\n' % (line, len(fields))
				continue
			while len(fields) > 3: fields[-1] = fields.pop(-1) + ' ' + fields[-1]
			(action, spamtype, spamtext) = fields
			action = action.replace(':', '')

			if action not in Filter.ACTIONS:
				# Undefined action
				response += '[ **!** ] Undefined action: "%s" (expected one of %s)\n\n' % (action, ', '.join(Filter.ACTIONS))
				continue
			if spamtype not in Filter.TYPES:
				# Undefined spam type
				response += '[ **!** ] Unable to %s: Undefined type of spam filter: "%s" (expected one of %s)\n\n' % (action, spamtype, ', '.join(Filter.TYPES))
				continue

			if action == 'add':
				# Add to filter
				if db.count('filters', 'type = ? and text = ? and active = 1', [spamtype, spamtext]) > 0:
					response += '[ **!** ] Unable to add filter: Filter already exists for %s filter "%s"\n\n' % (spamtype, spamtext)
				elif db.count('filters', 'type = ? and text = ? and active = 0', [spamtype, spamtext]) > 0:
					db.update('filters', 'active = 1', 'type = ? and text = ?', [spamtype, spamtext])
					response += '[ **+** ] Successfully activated %s filter "%s"\n\n' % (spamtype, spamtext)
				else:
					db.insert('filters', (None, spamtype, spamtext, pm.author, 0, timegm(gmtime()), True, 1 if is_spam else 0))
					response += '[ **+** ] Successfully added %s "%s" to the spam filter\n\n' % (spamtype, spamtext)
			elif action == 'remove':
				# Remove from filter
				if db.count('filters', 'type = ? and text = ?', [spamtype, spamtext]) == 0:
					response += '[ **!** ] Unable to remove filter: Filter does not exist for %s filter "%s"\n\n' % (spamtype, spamtext)
				elif db.count('filters', 'type = ? and text = ? and active = 1') == 0:
					response += '[ **!** ] Unable to remove filter: Filter is not active for %s filter "%s"\n\n' % (spamtype, spamtext)
				else:
					db.update('filters', 'active = 0', 'type = ? and text = ?', [spamtype, spamtext])
					response += '[ **-** ] Successfully deactivated %s filter "%s"' % (spamtype, spamtext)
		return response

	@staticmethod
	def detect_spam(child, db):
		''' 
			Detects if a reddit Child is spam.
			Returns:
				Tuple.
				[0] is the id of the filter that applied in the 'filters' table
				[1] is the user that gets the credit for the removal
			Raises:
				Exception if the post is NOT spam
		'''
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
				# Need to check for thumb spam
				httpy = Httpy()
				r = httpy.get(url)
				db.insert('checked_albums', (url,) )
				for (spamid, spamtext, credit) in db.select('id, text, author', 'filters', 'type = "thumb"'):
					if spamtext in r:
						return (spamid, credit)
				sleep(0.5)
				
		# Check if child's text/urls match any filters in the db
		for (spamid, spamtype, spamtext, credit) in db.select('id, type, text, author', 'filters', 'active = 1'):
			if spamtype == 'user' and child.author.lower() == spamtext.lower():
				return (spamid, credit)
			elif spamtype == 'link':
				for url in urls:
					if spamtext.lower() in url.lower():
						return (spamid, credit)
			elif spamtype == 'text':
				if spamtext.lower() in text.lower():
					return (spamid, credit)
			elif spamtype == 'tld':
				for url in urls:
					tld = url.lower().replace('http://', '').replace('https://', '').split('/')[0]
					if '.' in tld: tld = tld[tld.rfind('.')+1:]
					if tld.lower() == spamtext.lower():
						return (spamid, credit)
			elif spamtype == 'tumblr':
				for url in urls:
					url = url.lower()
					if '.tumblr.com' in url and not 'media.tumblr.com' in url:
						return (spamid, credit)
			elif spamtype == 'blogspot':
				for url in urls:
					url = url.lower()
					if '.blogspot.' in url and '.html' in url:
						return (spamid, credit)
			
		raise Exception('child was not detected as spam')

	@staticmethod
	def handle_child(child, db):
		'''
			Checks if child is spam. If so, removes from reddit & updates DB.
		'''
		if db.count('checked_posts', 'postid = ?', [child.id]) > 0:
			# Already checked
			return
		try:
			(filterid, credit) = Filter.detect_spam(child, db)
			# It's spam.
			child.remove(mark_as_spam=True)
			if   type(child) == Comment: posttype = 'comment'
			elif type(child) == Post:    posttype = 'post'
			db.insert('removed', ( filterid, posttype, child.permalink(), credit, timegm(gmtime()) ))
			db.update('filters', 'count = count + 1', 'filterid = ?', [filterid])
			db.update('admins', 'score = score + 1', 'username = ?', [credit])
			db.commit()
		except:
			# Not spam
			pass
		db.insert('checked_posts', (child.id))

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

