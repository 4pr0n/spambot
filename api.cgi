#!/usr/bin/python

from traceback import format_exc # Stack traces
from json      import dumps
from cgi       import FieldStorage # Query keys
from cgitb     import enable as cgi_enable; cgi_enable() # for debugging
from urllib    import unquote
from calendar  import timegm
from time      import gmtime

def main():
	'''
		Returns JSON-formatted data.
	'''
	keys = get_keys()
	if not 'method' in keys:
		raise Exception('unspecified method')
	method = keys['method']
	if   method == 'get_scoreboard':     return get_scoreboard()
	elif method == 'get_graph':          return get_graph(keys)
	elif method == 'get_spam':           return get_spam(keys)
	elif method == 'get_sources':        return get_sources(keys)
	elif method == 'get_removals':       return get_removals(keys)
	elif method == 'get_filter_changes': return get_filter_changes(keys)
	elif method == 'get_filter_info':    return get_filter_info(keys)
	elif method == 'get_filters':        return get_filters(keys)
	elif method == 'search_filters':     return search_filters(keys)
	elif method == 'get_modded_subs':    return get_modded_subs(keys)
	elif method == 'get_last_update':    return get_last_update()
	elif method == 'to_automod':         return to_automod(keys)

def get_scoreboard():
	from py.DB import DB
	db = DB()
	result = []
	for (username, score) in db.select('username, score', 'admins'):
		if score == 0: continue
		filters = db.count('filters', 'author = ?', [username])
		if filters == 0: continue
		result.append({
			'user'    : username,
			'score'   : score,
			'filters' : filters
		})
	result = sorted(result, key=lambda x: x['score'], reverse=True)
	return {
		'scoreboard': result
	}

def get_spam(keys):
	start = int(keys.get('start',  0))
	count = int(keys.get('count', 10))
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()

	where = ''
	values = []
	if 'type' in keys:
		where = 'where type = ?'
		values.append(keys['type'])
		if 'text' in keys:
			where += ' AND text = ?'
			values.append(keys['text'])

	q = '''
			select
				type, text, author, isspam, posttype, permalink, date
				from 
					filters
				inner join 
					log_removed
				on
					log_removed.filterid = filters.id
				%s
				order by date desc
				limit %d
				offset %d
		''' % (where, count, start)
	result = []
	for (spamtype, spamtext, author, isspam, posttype, permalink, date) in \
			cursor.execute(q, values):
		if author == '': author = 'internal'
		result.append({
			'spamtype'  : spamtype,
			'spamtext'  : spamtext,
			'user'      : author,
			'is_spam'   : (isspam == 1),
			'posttype'  : posttype,
			'permalink' : permalink,
			'date'      : date
		})
	cursor.close()
	return {
			'removed' : result,
			'start' : start + count,
			'count' : count
		}

def get_filters(keys):
	if 'type' not in keys:
		raise Exception('required "type" not found in keys')
	start = int(keys.get('start',  0))
	count = int(keys.get('count', 10))
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()

	total = db.count('filters', 'type = ?', [keys['type']])
	q = '''
			select
				id, type, text, author, active, isspam, created, count(*) as the_count
				from 
					filters
				inner join log_removed
				on log_removed.filterid = filters.id
				where type = ?
				group by log_removed.filterid
				order by the_count desc
				limit %d
				offset %d
		''' % (count, start)
	result = []
	for (filterid, spamtype, spamtext, author, active, isspam, created, removed_count) in \
			cursor.execute(q, [keys['type']]):
		if author == '': author = 'internal'
		result.append({
			'spamtype' : spamtype,
			'spamtext' : spamtext,
			'user'     : author,
			'active'   : (active == 1),
			'is_spam'  : (isspam == 1),
			'count'    : removed_count,
			'date'     : created
		})
	q = '''
			select
				id, type, text, author, active, isspam, created
				from 
					filters
				where type = ?
				order by created desc
				limit %d
				offset %d
		''' % (count, start)
	for (filterid, spamtype, spamtext, author, active, isspam, created) in \
			cursor.execute(q, [keys['type']]):
		if len(result) >= count: break
		if spamtext not in [x['spamtext'] for x in result]:
			if author == '': author = 'internal'
			result.append({
				'spamtype' : spamtype,
				'spamtext' : spamtext,
				'user'     : author,
				'active'   : (active == 1),
				'is_spam'  : (isspam == 1),
				'count'    : 0,
				'date'     : created
			})
		
	cursor.close()
	return {
			'filters' : result,
			'type'  : keys['type'],
			'start' : start + count,
			'count' : count,
			'total' : total
		}

def get_filter_info(keys):
	'''
		Args:
			keys.type : Spam type. Required.
			keys.text : Spam text. Required.

		Returns:
			.user: Author of filter.
			.count: Number of removals the filter has caused.
			.date: Filter created.
			.active: If filter is active or not.
			.is_spam: If filter removes posts/comments as spam or not.
	'''
	if not 'type' in keys: raise Exception('"type" key corresponding to spam type required')
	if not 'text' in keys: raise Exception('"text" key corresponding to spam text required')
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()
	# Get filter info
	q = '''
		select id, author, count, created, active, isspam
		from filters
		where type = ? and text = ?
	'''
	curexec = cursor.execute(q, [keys['type'], keys['text']])
	filterid = None
	for (filterid, author, count, created, active, is_spam) in curexec:
		break
	if filterid == None: # Filter not found
		raise Exception('filter not found for type "%s" and text "%s"' % (keys['type'], keys['text']))
	count = db.count('log_removed', 'filterid = ?', [filterid])
	return {
		'user'   : author,
		'count'  : count,
		'date'   : created,
		'active' : (active == 1),
		'is_spam': (is_spam == 1),
	}

def get_filter_changes(keys):
	start = int(keys.get('start',  0))
	count = int(keys.get('count', 10))
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()
	where = ''
	values = []
	if 'type' in keys:
		where = 'where type = ?'
		values.append(keys['type'])
	q = '''
			select
				type, text, user, action, date
				from 
					filters
				inner join 
					log_filters
				on
					log_filters.filterid = filters.id
				%s
				order by date desc
				limit %d
				offset %d
		''' % (where, count, start)
	result = []
	for (spamtype, spamtext, user, action, date) in \
			cursor.execute(q, values):
		if user == '': user = 'internal'
		result.append({
			'spamtype'  : spamtype,
			'spamtext'  : spamtext,
			'user'      : user,
			'action'    : action,
			'date'      : date
		})
	cursor.close()
	return {
			'filter_changes' : result,
			'start' : start + len(result),
			'count' : count
		}

def get_graph(keys):
	'''
		Args:
			keys.interval: Time-span (in seconds) between datapoints. Default: 3600 (1 hour)
			keys.span: How many iterations of interval to retrieve. Default: 48 (2 days)

		Returns:
			.window:        Human-readable time-span the data covers. ("2 days", "week")
			.pointStart:    .window but in milliseconds.
			.interval:      Human-readable interval between datapoints. ("hour", "3 hours")
			.pointInterval: .interval but in milliseconds.
			.series:        List of dicts, each dict has name, data, and total for that data.
	'''
			
	from calendar import timegm; from time import gmtime
	span     = int(keys.get('span',     48))
	interval = int(keys.get('interval', 3600))
	now      = (timegm(gmtime()) / interval) * interval # Rounded to the last interval
	pointStart = now - (span * interval)

	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()
	q = '''
			select
				posttype, date
				from 
					log_removed
				where date >= %d
				order by date desc
		''' % pointStart
	posts    = [0] * (span + 1)
	comments = [0] * (span + 1)
	for (posttype, date) in cursor.execute(q):
		index = (date - pointStart) / interval
		if   posttype == 'post':    posts[index]    += 1
		elif posttype == 'comment': comments[index] += 1
	cursor.close()
	return {
			'window'   : get_hr_time(span * interval),
			'interval' : get_hr_time(interval),
			'pointInterval' : interval * 1000,
			'pointStart' : pointStart * 1000,
			'series' : [
				{
					'name'  : 'posts',
					'data'  : posts,
					'total' : sum(posts)
				},
				{
					'name'  : 'comments',
					'data'  : comments,
					'total' : sum(comments)
				},
			]
		}


def get_removals(keys):
	'''
		Args:
			keys.start: Starting index. Default: 0
			keys.count: How many records to reutrn. Default: 10
		Returns:
			.content_removals: List of dicts with info about removed content
			.start: The next starting index to query.
			.count: How many results were requested.
	'''
	start = int(keys.get('start',  0))
	count = int(keys.get('count', 10))
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()
	q = '''
			select
				action, permalink, date, reason
				from 
					log_amarch
				where action = 'removed'
				order by date desc
				limit %d
				offset %d
		''' % (count, start)
	result = []
	for (action, permalink, date, reason) in \
			cursor.execute(q):
		result.append({
			'action'    : action,
			'permalink' : permalink,
			'date'      : date,
			'reason'    : reason,
		})
	cursor.close()
	return {
			'content_removals' : result,
			'start' : start + len(result),
			'count' : count
		}


def get_sources(keys):
	'''
		Returns info about posts that the bot provided 'source' for.
		Args:
			keys.start : Starting index. Default: 0
			keys.count : How many to return. Default: 10
		Returns:
			.sources: List of dicts with info about sourced posts.
			.start:   The next starting index to query.
			.count:   How many results were requested.
	'''
	start = int(keys.get('start',  0))
	count = int(keys.get('count', 10))
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()
	q = '''
			select
				date, permalink, album
				from 
					log_sourced
				order by date desc
				limit %d
				offset %d
		''' % (count, start)
	result = []
	for (date, permalink, album) in \
			cursor.execute(q):
		result.append({
			'date'      : date,
			'permalink' : permalink,
			'album'     : album,
		})
	cursor.close()
	return {
			'sources' : result,
			'start' : start + len(result),
			'count' : count
		}


def search_filters(keys):
	'''
		Searches for text within filters

		Args:
			keys.q: URL-encoded query string. Required.
			keys.limit: Number of results to return. Default: 5
		Returns:
			List of dicts containing info about matching filters.
	'''
	# Inputs
	if not 'q' in keys or keys['q'].strip() == '': raise Exception('no query key "q" provided')
	limit = keys.get('limit', '5')
	if not limit.isdigit(): limit = '5'
	# Queries
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()
	q = '''
		select
			type, text, author, count, created, active, isspam
		from filters
			where
	'''
	words = keys['q'].strip().split(' ')
	q += ' AND '.join(["text like '%%' || ? || '%%'"] * len(words))
	q += ' limit %d' % int(limit)
	curexec = cursor.execute(q, words)
	result = []
	for (spamtype, spamtext, author, count, created, active, isspam) in curexec:
		icon = spamtype.replace('text', 'pencil').replace('thumb', 'picture').replace('tld', 'globe')
		result.append({
			'type'   : spamtype,
			'text'   : spamtext,
			'user'   : author,
			'count'  : count,
			'date'   : created,
			'active' : (active == 1),
			'is_spam': (isspam == 1),
			'tokens' : spamtext.split(' '),
			'icon'   : icon
		})
	return result

def get_modded_subs(keys):
	start = int(keys.get('start',  0))
	count = int(keys.get('count', 10))
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()
	total = db.count('subs_mod')
	q = '''
		select subreddit
		from subs_mod
		limit %d
		offset %d
	''' % (count, start)
	curexec = cursor.execute(q)
	result = []
	for (subreddit,) in curexec:
		result.append(subreddit)
	cursor.close()
	return {
			'subreddits' : result,
			'start' : start + len(result),
			'count' : count,
			'total' : total
		}

def get_last_update():
	from py.DB import DB
	db = DB()
	last_update = db.get_config('last_update')
	hr_time = None
	diff = None
	if last_update != None:
		from calendar import timegm; from time import gmtime
		last_update = int(last_update)
		diff = timegm(gmtime()) - last_update
		hr_time = get_hr_time(diff)
	return {
		'last_update' : last_update,
		'diff' : diff,
		'hr_time' : hr_time
	}
	

def to_automod(keys):
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()

	response = []

	texts = []
	links = []
	users = []
	tlds  = []
	for (spamtype,text) in db.select('type, text', 'filters', 'active = 1 and (type = ? or type = ? or type = ? or type = ?)', ['text', 'link', 'user',' tld']):
		if   spamtype == 'text': texts.append(text)
		elif spamtype == 'link': links.append(text)
		elif spamtype == 'user': users.append(text)
		elif spamtype == 'tld' : tlds.append(text)

	response.append( '''
    # TUMBLR - Ignore tumblr links that are not directly to images/videos (e.g. 24.media.tumblr.com)
    url: "^https?://[a-zA-Z0-9\\\\-]+\\\\.tumblr\\\\.com.*$"
		modifiers: regex
		action: spam
---''' )

	response.append( '''
    # BLOGSPOT
    url: "^https?://.*\\\\.blogspot\\\\..*(?!jpg$|png$|gif$|jpeg$|JPG$|PNG$|GIF$|JPEG$)[^.]+$"
    modifiers: regex
    action: spam
----''' )

	response.append( '''
    # TLD
    url: "^https?://[a-zA-Z0-9\-\_\.]*\.(%s)(/.*)?$"
    modifiers: regex
    action: spam
---''' % '|'.join(tlds) )

	response.append( '''
    # USER
    user: ["%s"]
    modifiers: [includes, regex: false]
    action: spam
---''' % '","'.join(users) )

	response.append( '''
    # TEXT
    url+body+title: ["%s"]
    modifiers: [includes, regex: false]
    action: spam
---''' % '","'.join(texts) )

	response.append( '''
    # LINK
    url: ["%s"]
    modifiers: [includes, regex: false]
    action: spam
---''' % '","'.join(links) )

	return response

def get_hr_time(interval):
	'''
		Converts seconds into a human-readable unit.
		Ex:
			60   -> "min"
			120  -> "2 mins"
			300  -> "5 mins"
			3600 -> "hour"
			7200 -> "2 hours"
	'''
	(value, unit) = (interval, 'sec')
	if   interval >= 31536000:(value, unit) = (interval / 31536000,'year')
	elif interval >= 2592000: (value, unit) = (interval / 2592000, 'month')
	elif interval >= 86400:   (value, unit) = (interval / 86400,   'day')
	elif interval >= 3600:    (value, unit) = (interval / 3600,    'hour')
	elif interval >= 60:      (value, unit) = (interval / 60,      'min')
	return '%s%s%s' % ('%d ' % value if value != 1 else '', unit, 's' if value != 1 else '')


def get_keys(): # Get query keys
	form = FieldStorage()
	keys = {}
	for key in form.keys():
		keys[key] = unquote(form[key].value)
	return keys

########################
# ENTRY POINT
if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	try:
		print dumps(main(), indent=2)
	except Exception, e:
		print dumps({
			'error': str(e),
			'stack': str(format_exc())
		})
	print "\n\n"
