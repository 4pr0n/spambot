#!/usr/bin/python

'''
	Interacts with Reddit's API
	Dependent on Httpy.py, json
'''

from json     import loads
from Httpy    import Httpy
from time     import sleep, time as timetime, gmtime
from calendar import timegm

''' Base class for Reddit objects '''
class Child(object):
	def __init__(self, json=None, modhash=''):
		self.id        = ''
		self.subreddit = ''
		self.created   = 0
		self.author    = ''
		self.ups       = 0
		self.downs     = 0
		self.modhash   = modhash
		self.replies   = None
		self.banned_by   = None
		self.approved_by = None
		if json != None:
			self.from_json(json)
	def from_json(self, json):
		self.id        = json['id'].rjust(6, '0')
		self.subreddit = json['subreddit']
		self.created   = json['created_utc']
		self.author    = json['author']
		if 'ups' in json:   self.ups   = json['ups']
		if 'downs' in json: self.downs = json['downs']
		if 'replies' in json and type(json['replies']) == dict:
			self.replies = []
			for child in json['replies']['data']['children']:
				if child['kind'] == 't1':
					self.replies.append(Comment(child['data']))
				elif child['kind'] == 't4':
					self.replies.append(Message(child['data']))
		if 'banned_by'   in json: self.banned_by   = json['banned_by']
		if 'approved_by' in json: self.approved_by = json['approved_by']
	def __str__(self):
		return 'Reddit.%s(%s)' % (type(self).__name__, str(self.__dict__))
	def __repr__(self):
		return self.__str__()
	def full_name(self):
		if   type(self) == Message: t = 't4'
		elif type(self) == Post:    t = 't3'
		elif type(self) == Comment: t = 't1'
		else: raise Exception('unknown type: %s' % str(type(self)))
		return '%s_%s' % (t, self.id)
	def mark_as_read(self):
		d = {
			'uh' : self.modhash,
			'id' : self.full_name()
		}
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/read_message', d)
		self.new = False
	
	# API methods below
	def vote(self, direction=1):
		if type(self) != Comment and type(self) != Post:
			raise Exception('unable to vote on object of type %s' % str(type(self)))
		d = {
			'id'  : self.full_name(),
			'dir' : str(direction),
			'uh'  : self.modhash
		}
		Reddit.wait()
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/vote', d)
		if not r == '{}':
			raise Exception('unexpected response: "%s"' % r)
	def reply(self, body):
		d = {
			'api_type' : 'json',
			'uh'       : self.modhash,
			'text'     : body,
			'thing_id' : self.full_name()
		}
		Reddit.wait()
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/comment', d)
		json = loads(r)['json']
		if 'errors' in json and len(json['errors']) > 0:
			raise Exception(str(json['errors']))
		# Get id of reply, create new object, return it
		full = json['data']['things'][0]['data']['id']
		the_id = full.split('_')[1]
		if full.startswith('t1'):
			result = Comment()
		elif full.startswith('t4'):
			result = Message()
		result.id        = the_id
		result.modhash   = self.modhash
		result.subreddit = self.subreddit
		return result
	def remove(self, mark_as_spam=False):
		d = {
			'id' : self.full_name(),
			'uh' : self.modhash,
			'spam' : str(mark_as_spam)
		}
		Reddit.wait()
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/remove', d)
		if r != '{}' and r != '':
			raise Exception('unexpected response removing %s: "%s"' % (this.permalink(), r))
	def approve(self):
		d = {
			'id' : self.full_name(),
			'uh' : self.modhash
		}
		Reddit.wait()
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/approve', d)
		if not r == '{}':
			raise Exception('unexpected response: "%s"' % r)
	def distinguish(self, remove=False):
		d = {
			'api_type' : 'json',
			'id' : self.full_name(),
			'uh' : self.modhash,
			'how' : 'no' if remove else 'yes'
		}
		Reddit.wait()
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/distinguish', d)
		if not 'errors": []' in r:
			raise Exception('unexpected response: "%s"' % r)


class Post(Child,object):
	def __init__(self, json=None, modhash=''):
		super(Post, self).__init__(json=json, modhash=modhash)
		self.over_18  = False
		self.url      = ''
		self.selftext = None
		self.title    = ''
		self.thumbnail = None
		if json != None:
			self.from_json(json)
	def from_json(self, json, modhash=''):
		super(Post,self).from_json(json)
		self.url       = Reddit.asciify(json['url'])
		self.selftext  = Reddit.asciify(json['selftext']) if json['is_self'] else None
		self.title     = Reddit.asciify(json['title'])
		self.thumbnail = json['thumbnail']
	def permalink(self):
		if self.subreddit != '':
			return 'http://reddit.com/r/%s/comments/%s' % (self.subreddit, self.id)
		else:
			return 'http://reddit.com/comments/%s' % self.id
	def flair(self, text):
		d = {
			'executed' : 'unmarked',
			'spam' : 'False',
			'name' : self.full_name(),
			'flair_template_id' : '76a91748-1518-11e3-8669-12313b04c5c2',
			'text' : text,
			'link' : self.full_name(),
			'id'   : '',
			'r'    : self.subreddit,
			'uh'   : self.modhash,
			'renderstyle' : 'html'
		}
		Reddit.wait()
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/selectflair', d)
	def rescrape(self):
		if self.thumbnail != 'default':
			# Can't rescrape if it already has a thumbnail
			return
		d = {
			'id'          : 't3_%s' % self.id,
			'executed'    : 'retrying',
			'r'           : self.subreddit,
			'renderstyle' : 'html',
			'uh'          : self.modhash
		}
		Reddit.wait()
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/rescrape', d)


class Comment(Child,object):
	def __init__(self, json=None, modhash=''):
		super(Comment, self).__init__(json=json, modhash=modhash)
		self.body     = ''
		self.post_id  = ''
		if json != None:
			self.from_json(json)
	def from_json(self, json):
		super(Comment,self).from_json(json)
		self.body    = Reddit.asciify(json['body'])
		if 'link_id' in json:
			# Regular comment from a post
			self.post_id = json['link_id']
		elif 'context' in json:
			# Comment from the 'messages' view
			self.post_id = json['context'].split('/')[4]
	def permalink(self):
		if self.subreddit != '':
			return 'http://reddit.com/r/%s/comments/%s/_/%s' % (self.subreddit, self.post_id.replace('t3_',''), self.id)
		else:
			return 'http://reddit.com/comments/%s/_/%s' % (self.post_id.replace('t3_',''), self.id)

class Message(Child,object):
	def __init__(self, json=None, modhash=''):
		super(Message, self).__init__(json=json, modhash=modhash)
		self.body     = ''
		self.subject  = ''
		self.new      = False
		if json != None:
			self.from_json(json)
	def from_json(self, json):
		super(Message,self).from_json(json)
		self.body    = Reddit.asciify(json['body'])
		self.subject = Reddit.asciify(json['subject'])
		self.new     = json['new']
	def permalink(self):
		return 'http://reddit.com/message/messages/%s' % self.id
	def has_mod_invite(self):
		''' Checks if message contains a moderator invite '''
		return (self.author == None or self.author == 'reddit') and \
		        self.subject.startswith('invitation to moderate /r/')
	def accept_mod_invite(self):
		''' Joins subreddit as needed '''
		if not self.has_mod_invite():
			raise Exception('Message does not contain a moderator invite')
		d = {
			'id' : '',
			'r'  : self.subreddit,
			'uh' : self.modhash,
			'executed'    : 'you are now a moderator. welcome to the team!',
			'renderstyle' : 'html'
		}
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/accept_moderator_invite', d)
		return (r != '')


class User(object):
	def __init__(self, json=None):
		self.name    = ''
		self.created = 0
		self.comm_karma = 0
		self.link_karma = 0
		if json != None:
			self.name       =     json['name']
			self.created    = int(json['created_utc'])
			self.comm_karma =     json['comment_karma']
			self.link_karma =     json['link_karma']

''' Retrieve posts/comments from reddit '''
class Reddit(object):
	httpy = Httpy(user_agent='spambot by /u/4_pr0n, or contact admin@rarchives.com')
	last_request = 0.0
	modhash = ''
	next_url = None

	''' Safely convert Unicode to ASCII '''
	@staticmethod
	def asciify(text):
		return text.encode('UTF-8').decode('ascii', 'ignore')

	'''
		Prevent API rate limiting.
		Wait until more than 2 seconds have passed since last request was SENT
	'''
	@staticmethod
	def wait():
		now = float(timetime())
		if now - Reddit.last_request < 2:
			sleep(2 - (now - Reddit.last_request))
		Reddit.last_request = float(timetime())

	@staticmethod
	def login(user, password):
		Reddit.httpy.clear_cookies()
		d = {
				'user'   : user,
				'passwd' : password,
				'api_type' : 'json'
			}
		Reddit.wait()
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/login/%s' % user, d)
		if 'WRONG_PASSWORD' in r:
			raise Exception('invalid password')
		if 'RATELIMIT' in r:
			json = loads(r)
			errors = ''
			if 'json' in json and 'errors' in json['json']:
				errors = json['json']['errors']
			raise Exception('rate limit: %s' % errors)
		json = loads(r)
		if not 'json' in json or not 'data' in json['json']:
			raise Exception('failed: %s' % r)
		# Logged in

	@staticmethod
	def get(url):
		'''
			Gets reddit page containing a single post, 
			or a list of posts, comments, and/or messages.

			Returns a single Post object, or a list of Child-inheriting 
			objects (Post, Comment, Message).

			Does not extranous pages such as handle user pages, lists of contributors, etc.

			Args:
				url: Link to reddit page. Can be shortened ('/r/pics/new').
				     Does not need .json extension

			Returns:
				Post object, or list of Children (Posts, Comments, and/or Messages)

			Raises:
				Descriptive Exception if unable to load or parse page.
		'''
		if url.startswith('/'):
			url = 'http://www.reddit.com%s' % url
		if not 'json' in url.lower():
			if '?' in url:
				url = url.replace('?', '.json?', 1)
			else:
				url += '.json'
		results = []
		Reddit.wait()
		try:
			r = Reddit.httpy.get(url)
			json = loads(r)
		except Exception, e:
			raise e
		if type(json) == unicode:
			raise Exception('empty response')
		after = None
		if type(json) == dict and 'after' in json['data']:
			after = json['data']['after']
		elif type(json) == list and len(json) > 0 and 'after' in json[0]['data']:
			after = json[0]['data']['after']
		if after != None:
			sep = '?'
			if '?' in url: sep = '&'
			Reddit.next_url = '%s%safter=%s' % (url, sep, json['data']['after'])
		else:
			Reddit.next_url = None
		return Reddit.parse_json(json)

	''' Get 'next' reddit page. See get() '''
	@staticmethod
	def next():
		if Reddit.next_url == None:
			raise Exception('no next page to retrieve')
		return Reddit.get(Reddit.next_url)

	'''
		Parses reddit response.
		Returns either:
			Post - if link is to a post
			     - Comments will be contained within Post.replies
			List of objects - if link is to a list (/new, /comments, /user/*)
	'''
	@staticmethod
	def parse_json(json):
		if type(json) == list:
			modhash = json[0]['data']['modhash']
			# First item is post
			post = Post(json=json[0]['data']['children'][0]['data'], modhash=modhash)
			# Other items are comment replies to post
			post.replies = []
			for child in json[1:]:
				post.replies.extend(Reddit.parse_json(child))
			return post
		elif type(json) == dict:
			modhash = json['data']['modhash']
			result = []
			for item in json['data']['children']:
				if item['kind'] == 't3':
					# Post
					result.append(Post(json=item['data'], modhash=modhash))
				elif item['kind'] == 't1':
					# Comment
					result.append(Comment(json=item['data'], modhash=modhash))
				elif item['kind'] == 't4':
					# Message
					result.append(Message(json=item['data'], modhash=modhash))
			return result
		raise Exception('unable to parse:\n%s' % str(json))
		
	@staticmethod
	def get_user_info(user):
		url = 'http://www.reddit.com/user/%s/about.json' % user
		try:
			Reddit.wait()
			r = Reddit.httpy.get(url)
			json = loads(r)
		except Exception, e:
			raise e
		if not 'data' in json:
			raise Exception('data not found at %s' % url)
		data = json['data']
		user_info = User(json=data)
		return user_info

	''' Recursively print replies '''
	@staticmethod
	def print_replies(replies, depth=''):
		for i in xrange(0, len(replies)):
			comment = replies[i]
			print depth + '  \\_ "%s" -/u/%s' % (comment.body.replace('\n', ' '), comment.author)
			if comment.replies != None and len(comment.replies) > 0:
				more = '   '
				if i < len(replies) - 1:
					more = ' | '
				Reddit.print_replies(comment.replies, depth=depth+more)
	
	@staticmethod
	def accept_invite(subreddit, modhash):
		d = {
			'id' : '',
			'r'  : subreddit,
			'uh' : modhash,
			'executed' : 'you are now a moderator. welcome to the team!',
			'renderstyle' : 'html'
		}
		Reddit.wait()
		r = Reddit.httpy.oldpost('http://www.reddit.com/api/accept_moderator_invite', d)
		if r == '':
			raise Exception('empty response when accepting invite to %s with modhash %s' % (subreddit, modhash))
	
	@staticmethod
	def get_modded_subreddits():
		Reddit.wait()
		r = Reddit.httpy.get('http://reddit.com/r/mod')
		if not '<ul><a href="http://www.reddit.com/r/' in r:
			raise Exception('unable to find moderated subreddits')
		return Reddit.httpy.between(r, '<ul><a href="http://www.reddit.com/r/', '"')[0].split('+')

	@staticmethod
	def get_approved_submitters(subreddit):
		'''
			Returns list of approved submitters for a subreddit.
			Requires: 'access' mod permissions, or for the sub to be private apparently
		'''
		Reddit.wait()
		r = Reddit.httpy.get('http://www.reddit.com/r/%s/about/contributors.json' % subreddit)
		json = loads(r)
		approved = []
		for item in json['data']['children']:
			approved.append(item['name'].lower())
		return approved

	@staticmethod
	def get_moderators(subreddit):
		'''
			Returns list of moderators for a subreddit.
		'''
		Reddit.wait()
		r = Reddit.httpy.get('http://www.reddit.com/r/%s/about/moderators.json' % subreddit)
		json = loads(r)
		mods = []
		for item in json['data']['children']:
			mods.append(item['name'].lower())
		return mods

	@staticmethod
	def utc_timestamp_to_hr(tstamp):
		'''
			Subtracts timestamp from current time (in GMT) and returns difference
			in a human-readable ("HR") format.

			Examples:
				> utc_timestamp_to_hr(138103491)
				> 3 days ago
				> utc_timestamp_to_hr(148103491)
				> 5 days from now

			Args:
				tstamp: Timestamp in seconds since epoch, UTC-timezoned

			Returns:
				Human-readable difference between timestamp and now
		'''
		units = [
				(31536000, 'year'  ),
				(2592000,  'month' ),
				(86400,    'day'   ),
				(3600,     'hour'  ),
				(60,       'minute'),
				(1,        'second')
			]

		# Calculate difference
		diff = timegm(gmtime()) - tstamp
		if diff == 0: return 'now'
		in_future = (diff < 0)
		diff = abs(diff)

		hr_time = '?'
		for (secs, label) in units:
			if diff >= secs:
				parsecs = diff / secs
				hr_time = '%d %s%s %s' % (\
						parsecs, \
						label, \
						'' if parsecs == 1 else 's', \
						'from now' if in_future else 'ago'\
					)
				break
		return hr_time


if __name__ == '__main__':
	#Reddit.login(user, pass)
	#r = Reddit.get('/r/boltedontits/comments/.json') # Comment feed
	#r = Reddit.get('/r/boltedontits/comments/1r9f6a.json') # Post with comments
	#r = Reddit.get('/r/boltedontits/comments/1r9f6a/_/cdkxy92.json') # Single comment
	#r = Reddit.get('/message/moderator/')
	#r = Reddit.get('/message/inbox/')
	'''
	if type(r) == Post:
		print '"%s" by /u/%s' % (r.title, r.author)
		Reddit.print_replies(r.replies)
	elif type(r) == list:
		for item in r:
			if type(item) == Post:
				print 'POST:    "%s" by /u/%s %s' % (item.title, item.author, item.modhash),
			elif type(item) == Comment:
				print 'COMMENT: /u/%s: "%s" %s' % (item.author, item.body.replace('\n', ' '), item.modhash),
			elif type(item) == Message:
				print 'MESSAGE: /u/%s: "%s" %s' % (item.author, item.permalink(), item.modhash),
			print '(+%d/-%d)' % (item.ups, item.downs)
	'''
