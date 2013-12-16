#!/usr/bin/python

'''
	Functions for interacting with the i.rarchives.com search site
'''

from Reddit import Reddit, Child, Comment, Post
from json   import loads
from time   import sleep

class Rarchives(object):
	
	TRUSTED_AUTHORS = ['4_pr0n', 'wakinglife', 'pervertedbylanguage']
	TRUSTED_SUBREDDITS = ['AmateurArchives', 'UnrealGirls', 'gonewild']

	@staticmethod
	def handle_child(child, db, log):
		# We only care about posts that have URLs (not self-text)
		if type(child) != Post or child.url == None: return

		# Check child's subreddit is in the list of 'subs_source'
		if db.count('subs_source', 'subreddit like ?', [child.subreddit]) == 0: return

		# Get results from i.rarchives
		try:
			json = Rarchives.get_results(child.url)
		except Exception, e:
			log('Rarchives.get_results: Exception: %s' % str(e))
			return

		# Remove blacklisted URLs
		if Rarchives.blacklist_check(child, json, db, log): return

		# Remove Gonewild posts not from original author
		if Rarchives.gonewild_check(child, json, db, log): return

		# TODO Check for 'unreal' posts in some subreddits
		if Rarchives.unreal_check(child, json, db, log): return
		# Provide source
		Rarchives.provide_source(child, json, db, log)
	

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
				child.remove(remove_as_spam=False)
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
				child.remove(remove_as_spam=False)
				# TODO Remove and comment the gonewild post['permalink'] and post['author'] if ! [deleted]
				body = 'The post was removed because it is a repost of a /r/gonewild contributor.'
				body += '* /u/%s submitted ["%s"](%s)' % (post['author'], post['title'], post['permalink'])
				response = child.reply(body)
				response.distinguish()
				# TODO Update 'log_amarch' db table
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
			if db.count('subs_unreal', 'subreddit like ?', [post['subreddit']]) == 0: continue
			# Found result on UnrealGirls, we're supposed to enforce that on this subreddit
			# Remove and comment the unreal name & permalink
			child.remove(remove_as_spam=False)
			title = post['title']
			if '(' in title and ')' in title:
				title = title[title.find('(')+1:]
				title = title[:title.rfind(')')]
			body = '%s is "Unreal": ' % title
			body += '\n\n* %s' % post['permalink']
			response = child.reply(body)
			response.distinguish()
			# TODO Update 'log_amarch' db table
			return True
		return False


	@staticmethod
	def provide_source(child, json, db, log):
		for post in json['posts'] + json['comments']:
			if post['author'].lower()    not in Rarchives.TRUSTED_AUTHORS and \
				 post['subreddit'].lower() not in Rarchives.TRUSTED_SUBREDDITS or \
				 'imgur.com/a/' not in post['url']:
				continue
			# Comment from trusted user/subreddit to imgur album. Looks legit.
			# Construct comment & reply with post['url']
			body  = '[album](%s) in [this ' % post['url']
			if 'comments' in post:
				body += 'post'
			else:
				body += 'comment'
			body += '](%s) by /u/%s' % (post['permalink'], post['author'])
			response = child.reply(body)
			# TODO Update 'log_source' db table
			return


if __name__ == '__main__':
	print Rarchives.get_results('http://i.imgur.com/iHjXO.jpg')
	pass
