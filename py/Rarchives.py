#!/usr/bin/python

'''
	Functions for interacting with the i.rarchives.com search site.
'''

from Reddit   import Reddit, Child, Comment, Post
from Httpy    import Httpy
from json     import loads
from time     import sleep, gmtime
from calendar import timegm

class Rarchives(object):
	
	TRUSTED_AUTHORS    = ['4_pr0n', 'wakinglife', 'pervertedbylanguage']
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
		if 'reddit.com' in child.url: return False # Ignore reddit posts

		# Ensure the child's subreddit is in the list of subreddits to provide source in
		if db.count('subs_source', 'subreddit like ?', [child.subreddit]) == 0: return False

		# Get results from i.rarchives
		try:
			log('Rarchives.handle_child: Getting results for %s' % child.url)
			json = Rarchives.get_results(child.url)
		except Exception, e:
			log('Rarchives.get_results: Exception : %s\nwhen querying %s' % (str(e), child.url))
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
			if 'url' in post:      urls.append(post['url'])
			if 'imageurl' in post: urls.append(post['imageurl'])
		for comment in json['comments']:
			if 'url' in comment:      urls.append(comment['url'])
			if 'imageurl' in comment: urls.append(comment['imageurl'])
		for (url,) in db.select('url', 'blacklist_urls'):
			if url in urls:
				# Image/album is blacklisted! Remove post
				log('Rarchives.blacklist_check: Removed %s - matches %s' % (child.permalink(), url))
				child.remove(mark_as_spam=False)
				db.insert('log_amarch', ('removed', child.permalink(), timegm(gmtime()), 'illicit content: %s' % url))
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
				child.remove(mark_as_spam=False)
				log('Rarchives.gonewild_check: Removed %s - matches /u/%s @ http://reddit.com%s' % (child.permalink(), post['author'], post['permalink']))
				title = post['title'].replace('[', '\\[').replace('(', '\\(').replace(']', '\\]').replace(')', '\\)').replace('*', '')
				body = '## This post was removed because it is a repost of a /r/gonewild submission:\n\n'
				body += '* **/u/%s** submitted [*%s*](%s) %s' % (post['author'], title, post['permalink'], Reddit.utc_timestamp_to_hr(post['created']))
				try:
					response = child.reply(body)
					response.distinguish()
					child.flair('Removed/Gonewild')
				except Exception, e:
					log('Rarchives.gonewild_check: Error while replying to %s : %s' % (child.permalink(), str(e)))
				# Update 'log_amarch' db table
				db.insert('log_amarch', ('removed', child.permalink(), timegm(gmtime()), 'gonewild repost of /u/%s: %s' % (post['author'], post['permalink'])))
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
			if db.count('subs_unreal', 'subreddit like ?', [child.subreddit]) == 0: continue
			# And we're supposed to enforce that on this subreddit
			log('Rarchives.unreal_check: Removed %s - matches %s' % (child.permalink(), post['permalink']))
			child.remove(mark_as_spam=False)
			title = post['title']
			if '(' in title and ')' in title[title.find('(')+1:]:
				title = title[title.find('(')+1:]
				title = title[:title.rfind(')')]
				if title.lower() in ['photoshop', 'photoshopped']:
					body = 'Photoshopped:'
				else:
					body = '*%s* is a professional model and/or celebrity:' % title
			else:
				body = '*%s*:' % title
			body += '\n\n* %s' % post['permalink']
			try:
				response = child.reply(body)
				response.distinguish()
				child.flair('Removed/Unreal')
			except Exception, e:
				log('Rarchives.unreal_check: Error while replying to %s : %s' % (child.permalink(), str(e)))
			# Update 'log_amarch' db table
			db.insert('log_amarch', ('removed', child.permalink(), timegm(gmtime()), 'unreal post: %s' % post['permalink']))
			return True
		return False


	@staticmethod
	def provide_source(child, json, db, log):

		# Count number of images in child album (if there is any)
		child_album_count = 1 # Default to '1 image'
		if 'imgur.com/a/' in child.url:
			child_album_count = Rarchives.get_image_count_for_album(child.url)

		for post in json['posts'] + json['comments']:
			if post['author'].lower()    not in Rarchives.TRUSTED_AUTHORS and \
				 post['subreddit'].lower() not in Rarchives.TRUSTED_SUBREDDITS or \
				 'imgur.com/a/' not in post['url']:
				continue

			if db.count('do_not_source', 'url = ?', [post['url']]) > 0:
					continue

			# Confirm the album still exists and contains more photos than the child
			image_count = Rarchives.get_image_count_for_album(post['url'])
			if image_count <= child_album_count:
				continue

			# Comment from trusted user/subreddit to imgur album. Looks legit.
			# Construct comment & reply with post['url']
			body  = '[**album**^+%d](%s) ^\[[**' % (image_count - child_album_count, post['url'])
			if 'comments' in post:
				body += 'post'
			else:
				body += 'comment'
			body += '**](%s) ^by ^/u/%s\]' % (post['permalink'], post['author'])
			try:
				response = child.reply(body)
			except Exception, e:
				log('Rarchives.provide_source: Error while replying to %s : %s' % (child.permalink(), str(e)))
			# Update 'log_source' db table
			log('Rarchives.provide_source: Post %s matches %s' % (child.permalink(), post['url']))
			db.insert('log_sourced', (post['url'], timegm(gmtime()), child.permalink()))
			return True
		return False


	@staticmethod
	def get_image_count_for_album(url):
		url = url.replace('m.imgur.com', 'imgur.com').replace('https://', '').replace('http://', '')
		aid = url.split('/')[2]
		url = 'http://imgur.com/a/%s/noscript' % aid
		httpy = Httpy()
		r = httpy.get(url)
		return r.count('src="//i.imgur.com')


if __name__ == '__main__':
	print Rarchives.get_image_count_for_album('http://imgur.com/a/erraa/rearrange')
	#print Rarchives.get_results('http://i.imgur.com/iHjXO.jpg')
	pass
