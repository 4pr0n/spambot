#!/usr/bin/python

'''
	Bot functions specific to AmateurArchives.
'''

from Reddit   import Reddit, Child, Comment, Post
from calendar import timegm
from time     import gmtime
from json     import loads

class AmArch(object):
	
	@staticmethod
	def handle_child(child, db, log):
		'''
			Handles reddit child.
			Removes blacklisted users, enforces rules regarding requests.
			
			Returns:
				True if post was removed for some reason.
				False otherwise.
		'''
		if not child.subreddit.lower() == 'amateurarchives':
			return False

		# Remove posts mentioning blacklisted users
		if AmArch.check_for_blacklisted_user(child, db, log):
			return True

		# Detect request
		if AmArch.is_post_request(child):
			if not AmArch.valid_request(child, db, log):
				return True
			# TODO Fulfill GW requests via new API

		pass

	@staticmethod
	def execute(db, log):
		'''
			Execute maintenance, update lists of blacklisted users/urls
		'''
		AmArch.update_blacklisted_users(db, log)
		AmArch.update_blacklisted_urls (db, log)

	@staticmethod
	def check_for_blacklisted_user(child, db, log):
		'''
			Checks if post or comment contains a blacklisted username.
			Removes accordingly.
			
			Returns:
				True if child contains a blacklisted username and was removed.
				False otherwise.
		'''
		txt = ''
		if type(child) == Post:
			if child.title    != None: txt += ' %s ' % child.title.lower()
			if child.selftext != None: txt += ' %s ' % child.selftext.lower()
		elif type(child) == Comment:
			if child.body     != None: txt += ' %s ' % child.body.lower()
			
		for (user,) in db.select('username', 'blacklist_users'):
			if user.lower() in txt:
				child.remove(mark_as_spam=False)
				if type(child) == Post:
					body = '''
						## Rule: Do not request blacklisted content

						The user **%s** was detected in this post.

						**%s** is in the list of [blacklisted users](/r/AmateurArchives/wiki/banned)
					''' % (user, user)
					response = child.reply(body)
					response.distinguish()
				return True
		return False

	@staticmethod
	def is_post_request(child):
		'''
			Checks if post is request
			
			Returns:
				True if post is request, False otherwise
		'''
		if type(child) != Post: return False
		phrases = ['u/', 'request', 'anyone', 'any one', 'anymore', 'any more', 'have more', 'has more']
		for phrase in phrases:
			if phrase in child.title.lower():
				return True
		return False

	@staticmethod
	def is_valid_request(child, db, log):
		'''
			Ensures request is from an account older than 30 days,
			and the accounts last request was over 7 days ago.
			If not, removes the request and comments with the reason for removal

			Returns:
				True if post is valid request,
				False if request is not valid and was removed.
		'''
		if type(child) != Post: return True

		request_is_valid = False

		# Check if last request was < 7 days ago
		now = timegm(gmtime())
		for (date, permalink) in db.select('date, permalink', 'amarch_requests', 'username = ?', [child.author]):
			if date + (3600 * 24 * 7) > now:
				# Last request was < 7 days ago, check if the request was 'removed'
				post = Reddit.get(permalink)
				if post.banned_by == None:
					# Last request was < 7 days ago, wasn't removed
					child.remove(mark_as_spam=False)
					body = '''
						## Rule: Requests must be at least 7 days apart

						Your [last request](%s) was less than 7 days ago.
					''' % permalink
					response = child.reply(body)
					response.distinguish()
					return False
				else:
					# XXX OPTIMIZATION
					# Last request was > 7 days ago and wasn't removed
					# Therefore: User account must be > 30 days old
					request_is_valid = True

		if not request_is_valid:
			# Check if user is < 30 days old
			user = Reddit.get_user_info(child.author)
			if user.created > now - (3600 * 24 * 30):
				child.remove(mark_as_spam=False)
				body = '''
					## Rule: Requests must be from accounts more than 30 days old

					Your account (/u/%s) is less than 30 days old.
				''' % child.author
				response = child.reply(body)
				response.distinguish()
				return False

		# Request is valid. Add it to the database for checking in the future
		if db.count('amarch_requests', 'username = ?', [child.author]) == 0:
			db.insert('amarch_requests', (child.author, child.date, child.permalink()))
		else:
			db.update('amarch_requests', 'date = ?, permalink = ?', 'username = ?', [child.date, child.permalink(), child.author])
		return True


	@staticmethod
	def update_blacklisted_users(db, log):
		'''
			Updates database with most-recent list of blacklisted users from wiki
		'''
		log('AmArch.update_blacklisted_users: Loading blacklist wiki')
		count = 0
		try:
			users = AmArch.get_blacklisted_users()
		except Exception, e:
			log('AmArch.update_blacklisted_users: Got excpetion: %s' % str(e))
			return
		for user in users:
			if db.count('blacklist_users', 'username = ?', [user]) == 0:
				db.insert('blacklist_users', (user, ))
				count += 1
				log('AmArch.update_blacklisted_user: Added "%s"' % user)
		db.commit()

	@staticmethod
	def get_blacklisted_users():
		'''
			Returns:
				List of blacklisted users from wiki
			Raises:
				Exception if anything goes wrong, page times out, etc
		'''
		Reddit.wait()
		r = Reddit.httpy.get('http://www.reddit.com/r/AmateurArchives/wiki/banned.json')
		json = loads(r)
		wiki = json['data']['content_md']
		lines = wiki.split('\r\n')
		blacklisted = []
		for line in lines:
			if not '|' in line:
				continue
			fields = line.split('|')
			if len(fields) != 5:
				continue
			if fields[1] in ['username', ':--']:
				continue
			for user in fields[1].replace('/u/', '').split('/'):
				user = user.strip()
				if user == '': continue
				blacklisted.append(user)
		return blacklisted


	@staticmethod
	def update_blacklisted_urls(db, log):
		'''
			Updates database with most-recent list of blacklisted urls from wiki
		'''
		log('AmArch.update_blacklisted_urls: Loading blacklist wiki')
		count = 0
		try:
			urls = AmArch.get_blacklisted_urls()
		except Exception, e:
			log('AmArch.update_blacklisted_urls: Got excpetion: %s' % str(e))
			return
		for url in urls:
			if db.count('blacklist_urls', 'url = ?', [url]) == 0:
				db.insert('blacklist_urls', (url, ))
				log('AmArch.update_blacklisted_urls: Added: %s' % url)
		db.commit()

	@staticmethod
	def get_blacklisted_urls():
		'''
			Returns:
				List of blacklisted urls from wiki
			Raises:
				Exception if anything goes wrong, page times out, etc
		'''
		Reddit.wait()
		r = Reddit.httpy.get('http://www.reddit.com/r/AmateurArchives/wiki/illicit.json')
		json = loads(r)
		wiki = json['data']['content_md']
		illicit = []
		for url in Reddit.httpy.between(r, '](http://', ')'):
			if not 'imgur' in url: continue
			url = 'http://%s' % url
			illicit.append(url)
		return illicit

if __name__ == '__main__':
	pass
