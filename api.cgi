#!/usr/bin/python

from json import dumps
from traceback import format_exc # Stack traces
from cgi   import FieldStorage # Query keys
from cgitb import enable as cgi_enable; cgi_enable() # for debugging

def main():
	'''
		Returns JSON-formatted data.
	'''
	keys = get_keys()
	if not 'method' in keys:
		return {'error':'unspecified method'}
	method = keys['method']
	if   method == 'get_scoreboard': return get_scoreboard()
	elif method == 'get_removed':    return get_removed(keys)
	elif method == 'get_filter':     return get_filter(keys)
	elif method == 'get_graph':      return get_graph(keys)
	elif method == 'get_content_removals': return get_content_removals(keys)

def get_scoreboard():
	from py.DB import DB
	db = DB()
	result = []
	for (username, score) in db.select('username, score', 'admins'):
		if score == 0: continue
		filters = db.count('filters', 'author = ?', [username])
		result.append({
			'user'    : username,
			'score'   : score,
			'filters' : filters
		})
	result = sorted(result, key=lambda x: x['score'], reverse=True)
	return {
		'scoreboard': result
	}

def get_removed(keys):
	start = int(keys.get('start',  0))
	count = int(keys.get('count', 10))
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()
	q = '''
			select
				type, text, author, isspam, posttype, permalink, date
				from 
					filters
				inner join 
					log_removed
				on
					log_removed.filterid = filters.id
				order by date desc
				limit %d
				offset %d
		''' % (count, start)
	result = []
	for (spamtype, spamtext, author, isspam, posttype, permalink, date) in \
			cursor.execute(q):
		if author == '': author = 'internal'
		result.append({
			'spamtype'  : spamtype,
			'spamtext'  : spamtext,
			'author'    : author,
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

def get_filter(keys):
	start = int(keys.get('start',  0))
	count = int(keys.get('count', 10))
	from py.DB import DB
	db = DB()
	cursor = db.conn.cursor()
	q = '''
			select
				type, text, user, action, date
				from 
					filters
				inner join 
					log_filters
				on
					log_filters.filterid = filters.id
				order by date desc
				limit %d
				offset %d
		''' % (count, start)
	result = []
	for (spamtype, spamtext, user, action, date) in \
			cursor.execute(q):
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
	alltypes = [0] * (span + 1)
	for (posttype, date) in cursor.execute(q):
		index = (date - pointStart) / interval
		if   posttype == 'post':    posts[index]    += 1
		elif posttype == 'comment': comments[index] += 1
		alltypes[index] += 1
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
				{
					'name'  : 'all',
					'data'  : alltypes,
					'total' : sum(alltypes)
				}
			]
		}


def get_content_removals(keys):
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
		keys[key] = form[key].value
	return keys

########################
# ENTRY POINT
if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	try:
		print dumps(main(), indent=2)
	except Exception, e:
		# Return stacktrace
		print dumps({'error': str(format_exc())})
	print "\n\n"
