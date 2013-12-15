#!/usr/bin/python

'''
	Functions specific to AmateurArchives.
'''

from Reddit import Reddit, Child, Comment, Post

class AmArch(object):
	def __init__(self, reddit, db, log):
		self.reddit = reddit
		self.db     = db
		self.log    = log
	
	def handle_child(self, child):
		# TODO Detect request
		# TODO Remove requests from users < 30 days old
		# TODO Remove request if user already requested < 7 days ago
		pass

	def execute(self):
		self.update_blacklisted_users()
		self.update_blacklisted_urls()


	def update_blacklisted_users(self):
		self.log('AmArch.update_blacklisted_users: Loading blacklist wiki')
		count = 0
		try:
			users = self.get_blacklisted_users()
		except Exception, e:
			self.log('AmArch.update_blacklisted_users: Got excpetion: %s' % str(e))
			return
		for user in users:
			if self.db.count('blacklist_users', 'username = ?', [user]) == 0:
				self.db.insert('blacklist_users', (user, ))
				count += 1
				self.log('AmArch.update_blacklisted_user: Added "%s"' % user)
		self.db.commit()

	def get_blacklisted_users(self):
		self.reddit.wait()
		r = self.reddit.httpy.get('http://www.reddit.com/r/AmateurArchives/wiki/banned.json')
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


	def update_blacklisted_urls(self):
		self.log('AmArch.update_blacklisted_urls: Loading blacklist wiki')
		count = 0
		try:
			urls = self.get_blacklisted_urls()
		except Exception, e:
			self.log('AmArch.update_blacklisted_urls: Got excpetion: %s' % str(e))
			return
		for url in urls:
			if self.db.count('blacklist_urls', 'url = ?', [url]) == 0:
				self.db.insert('blacklist_urls', (url, ))
				self.log('AmArch.update_blacklisted_urls: Added: %s' % url)
		self.db.commit()

	def get_blacklisted_urls(self):
		self.reddit.wait()
		r = self.reddit.httpy.get('http://www.reddit.com/r/AmateurArchives/wiki/illicit.json')
		json = loads(r)
		wiki = json['data']['content_md']
		illicit = []
		for url in self.reddit.httpy.between(r, '](http://', ')'):
			if not 'imgur' in url: continue
			url = 'http://%s' % url
			illicit.append(url)
		return illicit

if __name__ == '__main__':
	pass
