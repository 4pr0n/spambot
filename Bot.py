#!/usr/bin/python

'''
	Contains infinite loop for all spambot functions.
'''

from py.DB        import DB
from py.Reddit    import Reddit
from py.Filter    import Filter
from py.AmArch    import AmArch
from py.Rarchives import Rarchives
from time         import strftime, gmtime
from sys          import stderr, exit
from traceback    import format_exc

PAGES_TO_REITERATE = 1
MOD_SUB = '4_pr0n', #'mod' # TODO Change back to 'mod'

class Bot(object):
	db = DB()
	iterations = 0
	logger = open('history.log', 'a')
	

	@staticmethod
	def execute():
		'''
			Do one atomic operation.
			Looks for spam posts/comments.
			Might do other functions as well (depending on iteration #)
			such as check for messages, update moderated subs, etc
		'''
		Bot.iterations += 1
		it = Bot.iterations

		pages = 1
		if it == 1: pages = PAGES_TO_REITERATE # look back on first load

		# TODO Allow checking comments
		if False and it % 5 == 1:
			Bot.log('Bot.execute: Checking messages...')
			if Bot.check_messages():
				# Got a PM to add/remove filter, need to look back further
				pages = PAGES_TO_REITERATE 

		# Check posts and comments
		# Removes spam and enforces AmateurArchives rules
		Bot.handle_url('/r/%s/comments' % MOD_SUB, pages=pages)
		children = Bot.handle_url('/r/%s/new' % MOD_SUB, pages=pages)

		# 'children' contains all 'unchecked' posts
		for child in children:
			# Check for sources
			Rarchives.handle_child(child, Bot.db, Bot.log)
		del children

		if it % 60 == 58:
			Bot.log('Bot.execute: Updating moderated subreddits...')
			Bot.update_modded_subreddits()

		if it % 60 == 59:
			Bot.log('Bot.execute: Updating AmateurArchives...')
			AmArch.execute()


	@staticmethod
	def check_messages():
		'''
			Checks for new messages, handles incoming messages

			Returns:
				true: New messages altered the database (added/removed filters)
				false: No messages, or the messages were innocuous
		'''
		has_new_messages = False
		last_pm_time = Bot.db.get_config('last_pm_time')
		if last_pm_time == None:
			last_pm_time = 0
		else:
			last_pm_time = int(last_pm_time)

		for msg in Reddit.get('/message/unread'):
			if msg.created < last_pm_time: continue
			try:
				response = Filter.parse_pm(pm, Bot.db)
				Bot.log('Bot.check_messages: Replying to %s with: %s' % (msg.author, response))
				has_new_messages = True
			except Exception, e:
				# No need to reply
				Bot.log('Bot.check_messages: %s' % str(e))
			last_pm_time = msg.created
			Bot.db.set_config('last_pm_time', str(last_pm_time))
			# TODO Mark as unread
			#msg.mark_as_read()
		return has_new_messages


	@staticmethod
	def handle_url(url, pages=1):
		children = []
		for child in Bot.get_content(url, pages=pages):
			if Filter.handle_child(child, Bot.db, Bot.log):
				# Filter removed the child for spam
				continue
			if Bot.db.count('checked_posts', 'postid = ?', [child.id]) == 0:
				# Has not been checked yet
				children.append(child)
				AmArch.handle_child(child, Bot.db, Bot.log)
				Bot.db.insert('checked_posts', (child.id, ))
				Bot.db.commit()
		return children


	@staticmethod
	def get_content(url, pages=1):
		'''
			Retrieves and iterates the posts/comments found at 'url'
			
			Args:
				url: URL on reddit containing posts/comments
				pages: Number of pages to view (loads 'next' page for pages-1 times)

			Yields:
				Each post or comment found at 'url'
		'''
		page = 0
		Bot.log('Loading %s' % url)
		posts = Reddit.get(url)
		while True:
			page += 1
			for post in posts:
				yield post
			if page < pages:
				Bot.log('Loading %s (page %d)' % (url, page))
				posts = Reddit.next()
			else:
				break


	@staticmethod
	def update_modded_subreddits():
		current = Reddit.get_modded_subreddits()
		if current == []: return
		for ignore in Bot.db.get_config('ignore_subreddits').split(','):
			if ignore in current:
				current.remove(ignore)
		existing = []
		for (sub, ) in Bot.db.select('subreddit', 'subs_mod'):
			if not sub in current:
				Bot.db.delete('subs_mod', 'subreddit = ?', [sub])
			else:
				existing.append(sub)
		for sub in current:
			if not sub in existing:
				Bot.db.insert('subs_mod', (sub, ) )
		Bot.db.commit()


	@staticmethod
	def log(txt):
		'''
			Logs text to history file and to stderr.
			Includes timestamp and formatting
		'''
		tstamp = strftime('[%Y-%m-%dT%H:%M:%SZ] ', gmtime())
		gap = ' ' * len(tstamp)
		line = '%s%s' % (tstamp, txt.replace('\n', '\n%s' % gap))
		Bot.logger.write('%s\n' % line)
		Bot.logger.flush()
		stderr.write('%s\n' % line)
		stderr.flush()


if __name__ == '__main__':
	Bot.log('Bot.main: Logging in...')
	Reddit.login('rarchives', Bot.db.get_config('reddit_pw'))
	while True:
		try:
			Bot.execute()
		except Exception, e:
			Bot.log('Bot.main: Exception: %s' % str(e))
			Bot.log(format_exc())
