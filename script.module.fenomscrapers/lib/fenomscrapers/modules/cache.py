# -*- coding: utf-8 -*-
"""
	Fenomscrapers Module
"""

import ast
import hashlib
import re
import time
try:
	from sqlite3 import dbapi2 as db
except ImportError:
	from pysqlite2 import dbapi2 as db

from fenomscrapers.modules import control
from fenomscrapers.modules import log_utils


def get(function, duration, *args):
	"""
	:param function: Function to be executed
	:param duration: Duration of validity of cache in hours
	:param args: Optional arguments for the provided function
	"""
	try:
		key = _hash_function(function, args)
		cache_result = cache_get(key)
		if cache_result:
			try: result = ast.literal_eval(cache_result['value'].encode('utf-8'))
			except: result = ast.literal_eval(cache_result['value'])
			if _is_cache_valid(cache_result['date'], duration):
				return result

		fresh_result = repr(function(*args))
		try:  # Sometimes None is returned as a string instead of None type for "fresh_result"
			invalid = False
			if not fresh_result: invalid = True
			elif fresh_result == 'None' or fresh_result == '' or fresh_result == '[]' or fresh_result == '{}': invalid = True
			elif len(fresh_result) == 0: invalid = True
		except: pass

		if invalid: # If the cache is old, but we didn't get "fresh_result", return the old cache
			if cache_result: return result
			else: return None
		else:
			cache_insert(key, fresh_result)
			try: return ast.literal_eval(fresh_result.encode('utf-8'))
			except: result = ast.literal_eval(fresh_result)
	except:
		log_utils.error()
		return None


def cache_get(key):
	try:
		cursor = _get_connection_cursor()
		ck_table = cursor.execute('''SELECT * FROM sqlite_master WHERE type='table' AND name='cache';''').fetchone()
		if not ck_table: return None
		results = cursor.execute('''SELECT * FROM cache WHERE key=?''', (key,)).fetchone()
		return results
	except:
		log_utils.error()
		return None
	finally:
		cursor.close()


def cache_insert(key, value):
	try:
		cursor = _get_connection_cursor()
		now = int(time.time())
		cursor.execute('''CREATE TABLE IF NOT EXISTS cache (key TEXT, value TEXT, date INTEGER, UNIQUE(key));''')
		update_result = cursor.execute('''UPDATE cache SET value=?,date=? WHERE key=?''', (value, now, key))
		if update_result.rowcount is 0:
			cursor.execute('''INSERT INTO cache Values (?, ?, ?)''', (key, value, now))
		cursor.connection.commit()
	except:
		log_utils.error()
	finally:
		cursor.close()


def _get_connection_cursor():
	conn = _get_connection()
	return conn.cursor()


def _get_connection():
	control.makeFile(control.dataPath)
	conn = db.connect(control.cacheFile)
	conn.row_factory = _dict_factory
	return conn


def _dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d


def _hash_function(function_instance, *args):
	return _get_function_name(function_instance) + _generate_md5(args)


def _get_function_name(function_instance):
	return re.sub(r'.+\smethod\s|.+function\s|\sat\s.+|\sof\s.+', '', repr(function_instance))


def _generate_md5(*args):
	md5_hash = hashlib.md5()
	try: [md5_hash.update(str(arg)) for arg in args]
	except: [md5_hash.update(str(arg).encode('utf-8')) for arg in args]
	return str(md5_hash.hexdigest())


def _is_cache_valid(cached_time, cache_timeout):
	now = int(time.time())
	diff = now - cached_time
	return (cache_timeout * 3600) > diff