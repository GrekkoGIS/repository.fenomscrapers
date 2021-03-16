# -*- coding: utf-8 -*-
"""
	Fenomscrapers Module
"""

import re
import unicodedata
from fenomscrapers.modules import log_utils
from fenomscrapers.modules import py_tools


def get(title):
	try:
		if not title: return
		try: title = py_tools.ensure_str(title)
		except: pass
		title = re.sub(r'&#(\d+);', '', title).lower()
		title = re.sub(r'(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
		title = title.replace('&quot;', '\"').replace('&amp;', '&')
		# title = re.sub(r'\n|([[].+?[]])|([(].+?[)])|\s(vs|v[.])\s|(:|;|-|–|"|,|\'|\_|\.|\?)|\~|\s', '', title).lower()
		title = re.sub(r'\n|([\[({].+?[})\]])|\s(vs[.]?|v[.])\s|([:;–\-"\',!_\.\?~])|\s', '', title) # removes bracketed content
		return title
	except:
		log_utils.error()
		return title


def get_simple(title):
	try:
		if not title: return
		try: title = py_tools.ensure_str(title)
		except: pass
		title = re.sub(r'(\d{4})', '', title).lower()
		title = re.sub(r'&#(\d+);', '', title)
		title = re.sub(r'(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
		title = title.replace('&quot;', '\"').replace('&amp;', '&')
		# title = re.sub(r'\n|\(|\)|\[|\]|\{|\}|\s(vs|v[.])\s|(:|;|-|–|"|,|\'|\_|\.|\?)|\~|\s', '', title).lower()
		title = re.sub(r'\n|[()[\]{}]|\s(vs[.]?|v[.])\s|[:;–\-",\'!_.?~]|\s', '', title) # keeps bracketed content unlike .get()
		title = re.sub(r'<.*?>', '', title) # removes tags?
		return title
	except:
		log_utils.error()
		return title


def geturl(title):
	if not title: return
	try:
		try: title = py_tools.ensure_str(title)
		except: pass
		title = title.lower().rstrip()
		try: title = title.translate(None, ':*?"\'\.<>|&!,')
		except:
			try: title = title.translate(title.maketrans('', '', ':*?"\'\.<>|&!,'))
			except:
				for c in ':*?"\'\.<>|&!,': title = title.replace(c, '')
		title = title.replace('/', '-').replace(' ', '-').replace('--', '-').replace('–', '-').replace('!', '')
		return title
	except:
		log_utils.error()
		return title


def normalize(title):
	try:
		if py_tools.isPY2:
			try: return py_tools.ensure_str(py_tools.ensure_text(title, encoding='ascii'))
			except: pass
		# return str(''.join(c for c in unicodedata.normalize('NFKD', unicode(title.decode('utf-8'))) if unicodedata.category(c) != 'Mn'))
		return ''.join(c for c in unicodedata.normalize('NFKD', py_tools.ensure_text(py_tools.ensure_str(title))) if unicodedata.category(c) != 'Mn')
	except:
		log_utils.error()
		return title