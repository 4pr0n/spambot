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
