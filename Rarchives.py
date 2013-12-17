#!/usr/bin/python

'''
	Functions for interacting with the i.rarchives.com search site.
'''

from Reddit import Reddit, Child, Comment, Post
from Httpy  import Httpy
from json   import loads
from time   import sleep

class Rarchives(object):
	
	TRUSTED_AUTHORS = ['4_pr0n', 'wakinglife', 'pervertedbylanguage']
	TRUSTED_SUBREDDITS = ['AmateurArchives', 'UnrealGirls', 'gonewild']

	@staticmethod
	def handle_child(child, db, log):
		'''
			Handles reddit child.
			Checks and removes child if it should be (blacklisted, illicit, gonewild repost)
			Returns:
				True if child was removed for some reason
				False otherwise
		'''
		# We only care about posts that have URLs (not self-text)
		if type(child) != Post or child.url == None: return False

		# Ensure the child's subreddit is in the list of subreddits to provide source in
		if db.count('subs_source', 'subreddit like ?', [child.subreddit]) == 0: return False

		# Get results from i.rarchives
		try:
			json = Rarchives.get_results(child.url)
		except Exception, e:
			log('Rarchives.get_results: Exception: %s' % str(e))
			return

		# Do the thing, checking for removals first
		if Rarchives.blacklist_check(child, json, db, log): return True
		if Rarchives.gonewild_check (child, json, db, log): return True
		if Rarchives.unreal_check   (child, json, db, log): return True
		if Rarchives.provide_source (child, json, db, log): return True
		return False
	

	@staticmethod
	def get_results(url):
		url = 'http://i.rarchives.com/search.cgi?url=' + url
		r = Reddit.httpy.get(url)
		json = loads(r)
		if 'imgur.com/a/' in url  and \
		   'cached'       in json and \
		   not json['cached']:
			# URL is an album and it hasn't been cached by i.rarchives yet
			# Wait a few seconds for the site to index some of the images
			sleep(5)
			# And try again
			r = Reddit.httpy.get(url)
			json = loads(r)

		if 'error' in json:
			raise Exception(json['error'])
		return json


	@staticmethod
	def blacklist_check(child, json, db, log):
		'''
			Checks if child contains blacklisted url.
			Removes if it does
		'''
		urls = []
		for post in json['posts']:
			urls.append(post['url'])
			urls.append(post['imageurl'])
		for comment in json['comments']:
			urls.append(comment['url'])
			urls.append(comment['imageurl'])
		for (url,) in db.select('url'):
			if url in urls:
				# Image/album is blacklisted! Remove post
				log('Rarchives.blacklist_check: Removed %s - matches %s' % (child.permalink(), url))
				child.remove(remove_as_spam=False)
				db.insert('log_amarch', ('remove', child.permalink(), timegm(gmtime()), 'illicit content: %s' % url))
				return True
		return False


	@staticmethod
	def gonewild_check(child, json, db, log):
		'''
			Check if image(s) in child were posted to gonewild
			and the child author is not the original gonewild author.
			Remove child and explain in comment.
			Args:
				child: reddit child (post)
				json: results from rarchives
			Returns:
				True if post originated on gonewild, False otherwise.
		'''
		# Disable this on /r/AmateurArchives
		if child.subreddit.lower() == 'amateurarchives': return False

		# XXX Only enforce posts by gonewild users (not comments)
		for post in json['posts']:
			if post['subreddit'].lower() == 'gonewild' and \
			   post['author'].lower() != child.author.lower() and \
				 post['author'] != '[deleted]':
				# Child author is not the gonewild user, image *is* though
				# Remove and comment the source
				log('Rarchives.gonewild_check: Removed %s - matches /u/%s @ %s' % (child.permalink(), post['author'], post['permalink']))
				child.remove(remove_as_spam=False)
				body = 'The post was removed because it is a repost of a /r/gonewild contributor.'
				body += '* /u/%s submitted ["%s"](%s)' % (post['author'], post['title'], post['permalink'])
				response = child.reply(body)
				response.distinguish()
				# Update 'log_amarch' db table
				db.insert('log_amarch', ('remove', child.permalink(), timegm(gmtime()), 'gonewild repost of /u/%s: %s' % (post['author'], post['permalink'])))
				return True
		return False


	@staticmethod
	def unreal_check(child, json, db, log):
		'''
			If the json results contain a post/comment from UnrealGirls
			and the child is in an unreal-enforced subreddit,
			remove the post and comment with the json result
			Args:
				child: reddit child (post)
				json: results from rarchives
			Returns:
				True if post is of an unreal girl in an unreal-enforced subreddit.
				False otherwise.
		'''
		for post in json['posts'] + json['comments']:
			if post['subreddit'].lower() != 'unrealgirls': continue
			# Found matching result on UnrealGirls,
			if db.count('subs_unreal', 'subreddit like ?', [post['subreddit']]) == 0: continue
			# And we're supposed to enforce that on this subreddit
			log('Rarchives.unreal_check: Removed %s - matches %s' % (child.permalink(), post['permalink']))
			child.remove(remove_as_spam=False)
			title = post['title']
			if '(' in title and ')' in title[title.find('(')+1:]:
				title = title[title.find('(')+1:]
				title = title[:title.rfind(')')]
			body = '%s is "Unreal": ' % title
			body += '\n\n* %s' % post['permalink']
			response = child.reply(body)
			response.distinguish()
			# Update 'log_amarch' db table
			db.insert('log_amarch', ('remove', child.permalink(), timegm(gmtime()), 'unreal post: %s' % post['permalink']))
			return True
		return False


	@staticmethod
	def provide_source(child, json, db, log):
		for post in json['posts'] + json['comments']:
			if post['author'].lower()    not in Rarchives.TRUSTED_AUTHORS and \
				 post['subreddit'].lower() not in Rarchives.TRUSTED_SUBREDDITS or \
				 'imgur.com/a/' not in post['url']:
				continue
			# Confirm the album still exists and contains at least 2 photos.
			httpy = Httpy()
			r = httpy.get(post['url'])
			if not 'Album: ' in r:
				return False
			count = httpy.web.between(r, 'Album: ', ' ')[0].replace(',' '')
			if not count.isdigit() or int(count) < 2:
				return False
			# Comment from trusted user/subreddit to imgur album. Looks legit.
			# Construct comment & reply with post['url']
			body  = '[album](%s) in [this ' % post['url']
			if 'comments' in post:
				body += 'post'
			else:
				body += 'comment'
			body += '](%s) by /u/%s' % (post['permalink'], post['author'])
			response = child.reply(body)
			# Update 'log_source' db table
			log('Rarchives.provide_source: Post %s matches %s' % (child.permalink(), post['url']))
			db.insert('log_sourced', (post['url'], timegm(gmtime()), child.permalink()))
			return True
		return False


if __name__ == '__main__':
	print Rarchives.get_results('http://i.imgur.com/iHjXO.jpg')
	pass
