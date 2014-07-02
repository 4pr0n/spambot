#!/usr/bin/python

'''
	Bot functions specific to AmateurArchives.
'''

from Reddit   import Reddit, Child, Comment, Post
from calendar import timegm
from time     import gmtime
from json     import loads

class AmArch(object):
	
	MINIMUM_REQUESTER_AGE = 30
	MINIMUM_REQUEST_DAYS  = 7
	@staticmethod
	def handle_child(child, db, log):
		'''
			Handles reddit child.
			Removes blacklisted users, enforces rules regarding requests.
			
			Returns:
				True if post was removed for some reason.
				False otherwise.
		'''
		if child.subreddit.lower() not in ['amateurarchives', '4_pr0n']:
			return False

		# Remove posts mentioning blacklisted users
		if AmArch.check_for_blacklisted_user(child, db, log):
			return True

		# Detect request
		if AmArch.is_post_request(child):
			if not AmArch.is_valid_request(child, db, log):
				return True
			#if AmArch.fulfill_user_request(child, db, log):
			#	return True
		return False


	@staticmethod
	def execute(db, log):
		'''
			Perform maintenance, update lists of blacklisted users/urls
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
			# XXX Not removing comments mentioning blacklisted users
			return False
			if db.count('subs_approved', 'subreddit like ? and username = ?', [child.subreddit, child.author]) > 0:
				# Comment was from a mod/approved submitter, ignore
				return False
			if child.body != None: txt += ' %s ' % child.body.lower()
			
		for (user,) in db.select('username', 'blacklist_users'):

			if user.lower() in txt:
				child.remove(mark_as_spam=False)
				if type(child) == Post:
					body  = '## Rule: [Do not request blacklisted content](/r/AmateurArchives/about/sidebar)\n\n'
					body += 'This post has been removed because it mentions **%s**.\n\n' % user
					body += '**%s** is in the list of [**blacklisted users**](/r/AmateurArchives/wiki/banned).' % user
					response = child.reply(body)
					response.distinguish()
					child.flair('Blacklisted %s' % user)
					log('AmArch.check_for_blacklisted_user: Post requested /u/%s, removed: %s' % (user, child.permalink()))

				elif type(child) == Comment:
					child.remove(mark_as_spam=False)
					log('AmArch.check_for_blacklisted_user: Comment requested /u/%s, removed: %s' % (user, child.permalink()))

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
		phrases = ['u/', 'request', 'anyone', 'any one', 'anymore', 'any more', 'have more', 'has more', 'got more', 'moar']
		for phrase in phrases:
			if phrase in child.title.lower():
				return True
		return False


	@staticmethod
	def is_valid_request(child, db, log):
		'''
			Ensures request is from an account older than MINIMUM_REQUESTER_AGE days,
			and the accounts last request was over MINIMUM_REQUEST_DAYS days ago.
			If not, removes the request and comments with the reason for removal

			Returns:
				True if post is valid request,
				False if request is not valid and was removed.
		'''
		if type(child) != Post: return True

		request_is_valid = False

		# Check if last request was < MINIMUM_REQUEST_DAYS days ago
		now = timegm(gmtime())
		for (date, permalink) in db.select('date, permalink', 'amarch_requests', 'username = ?', [child.author]):
			if date + (3600 * 24 * AmArch.MINIMUM_REQUEST_DAYS) > now:
				# Last request was < MINIMUM_REQUEST_DAYS days ago, check if the request was 'removed'
				post = Reddit.get(permalink)
				if post.banned_by == None:
					# Last request was < MINIMUM_REQUEST_DAYS days ago, wasn't removed
					child.remove(mark_as_spam=False)
					log('AmArch.is_valid_request: Request < %d days old: %s' % (AmArch.MINIMUM_REQUEST_DAYS, child.permalink()))
					body  = '## Rule: [Requests must be at least %d days apart](/r/AmateurArchives/about/sidebar)\n\n' % AmArch.MINIMUM_REQUEST_DAYS
					body += 'The [**last request**](%s) from your account was submitted %s' % (permalink, Reddit.utc_timestamp_to_hr(post.created))
					response = child.reply(body)
					response.distinguish()
					child.flair('last req < %dd' % AmArch.MINIMUM_REQUEST_DAYS)
					return False
				else:
					# XXX OPTIMIZATION
					# Last request was > MINIMUM_REQUEST_DAYS days ago but was removed
					# Therefore: User account must be > MINIMUM_REQUESTER_AGE days old
					request_is_valid = True

		if not request_is_valid:
			# Check if user is < MINIMUM_REQUESTER_AGE days old
			user = Reddit.get_user_info(child.author)
			if user.created > now - (3600 * 24 * AmArch.MINIMUM_REQUESTER_AGE):
				child.remove(mark_as_spam=False)
				log('AmArch.is_valid_request: Requester /u/%s < %d days old: %s' % (child.author, AmArch.MINIMUM_REQUESTER_AGE, child.permalink()))
				body  = '## Rule: [Requests must be from accounts more than %d days old](/r/AmateurArchives/about/sidebar)\n\n' % AmArch.MINIMUM_REQUESTER_AGE
				body += 'The account (/u/%s) was created %s.' % (child.author, Reddit.utc_timestamp_to_hr(user.created))
				response = child.reply(body)
				response.distinguish()
				child.flair('user < %dd' % AmArch.MINIMUM_REQUESTER_AGE)
				return False

		# Request is valid. Add it to the database for checking in the future
		log('AmArch.is_valid_request: Allowing request from /u/%s' % child.author)
		if db.count('amarch_requests', 'username = ?', [child.author]) == 0:
			db.insert('amarch_requests', (child.author, child.created, child.permalink()))
		else:
			db.update('amarch_requests', 'date = ?, permalink = ?', 'username = ?', [child.created, child.permalink(), child.author])
		return True


	@staticmethod
	def update_blacklisted_users(db, log):
		'''
			Updates database with most-recent list of blacklisted users from wiki
		'''
		#log('AmArch.update_blacklisted_users: Loading blacklist wiki')
		count = 0
		try:
			users = AmArch.get_blacklisted_users()
		except Exception, e:
			log('AmArch.update_blacklisted_users: Got exception: %s' % str(e))
			return
		for user in users:
			if user.strip() == '': continue
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
		#log('AmArch.update_blacklisted_urls: Loading blacklist wiki')
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


	@staticmethod
	def fulfill_user_request(child, db, log):
		'''
			Rips user via rip.rarchives API
			Returns:
				True if request is fulfilled
				False otherwise
		'''
		if not 'u/' in child.title: return False

		# Get user
		# TODO Handle multiple users
		title = child.title[child.title.find('u/')+2:]
		user = ''
		for char in title:
			if char.lower() not in 'abcdefghijklmnopqrstuvwxyz0123456789_-': break
			user += char
		if len(user) < 3: return False

		# Use rip.rarchives to rip album
		RIP = 'http://rip.rarchives.com'
		api_url = '%s/api.cgi?method=rip_album&url=gonewild:%s' % (RIP, user)

		# Send request
		log('AmArch.fulfill_user_request: Fulfilling /u/%s via %s' % (user, api_url))
		try:
			r = Reddit.httpy.get(api_url)
			json = loads(r)
		except Exception, e:
			log('AmArch.fulfill_user_request: Error fulfilling /u/%s: Exception: %s\n' % (user, str(e)))

		if 'error' in json: 
			log('AmArch.fulfill_user_request: Error fulfilling /u/%s: %s' % (user, json['error']))
			return False
		if 'count' not in json or \
			 'path'  not in json:
			log('AmArch.fulfill_user_request: Error fulfilling /u/%s: Missing info in response:\n' % (user, r))
			return False

		# Reply to child with the result
		body = '[**album**](%s/#album=%s) / [**zip**](%s/rips/%s.zip) ^[%d ^pics]' % (RIP, json['path'], RIP, json['path'], json['count'])
		child.reply(body)
		child.flair('Bot-Fulfilled (%d)' % json['count'])
		log('AmArch.fulfill_user_request: Fulfilled /u/%s: %s' % (user, child.permalink()))
		return True


if __name__ == '__main__':
	pass
