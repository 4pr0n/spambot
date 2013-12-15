#!/usr/bin/python

'''
	Contains infinite loop for all spambot functions.
'''

from DB        import DB
from Reddit    import Reddit
from Filter    import Filter
from AmArch    import AmArch
from time      import strftime, gmtime
from sys       import stderr, exit
from traceback import format_exc

PAGES_TO_REITERATE = 5

class Bot(object):
	db = DB()
	iterations = 0
	logger = open('history.log', 'a')
	amarch = None
	
	@staticmethod
	def execute():
		'''
			Do one atomic operation.
			Looks for spam posts/comments.
			Might do other functions as well (depending on iteration #)
			such as check for messages, update moderated subs, etc
		'''
		if Bot.amarch == None: Bot.amarch = AmArch(Reddit, Bot.db, Bot.log)
		Bot.iterations += 1
		it = Bot.iterations

		pages = 1
		if it % 5 == 1:
			Bot.log('Checking messages...')
			if Bot.check_messages():
				pages = PAGES_TO_REITERATE

		#Bot.check_spam('/r/mod/new',      pages=pages)
		#Bot.check_spam('/r/mod/comments', pages=pages)
		Bot.check_spam('/r/4_pr0n/comments', pages=pages)

		if it % 60 == 58:
			Bot.log('Updating moderated subreddits...')
			Bot.update_modded_subreddits()

		if it % 60 == 59:
			Bot.amarch.execute()

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
			#msg.mark_as_read()
		return has_new_messages
	
	@staticmethod
	def check_spam(url, pages=1):
		'''
			Looks for and handles spam found at url
			
			Args:
				url: URL on reddit containing posts/comments
				pages: Number of pages to view (loads 'next' page for pages-1 times)
		'''
		page = 0
		Bot.log('Loading %s' % url)
		posts = Reddit.get(url)
		while True:
			page += 1
			for post in posts:
				Filter.handle_child(post, Bot.db, Bot.log)
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
	Bot.log('Logging in...')
	Reddit.login('rarchives', Bot.db.get_config('reddit_pw'))
	while True:
		try:
			Bot.execute()
		except Exception, e:
			Bot.log('Exception: %s' % str(e))
			Bot.log(format_exc())
