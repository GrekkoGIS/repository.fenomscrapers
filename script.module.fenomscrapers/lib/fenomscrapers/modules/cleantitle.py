# -*- coding: utf-8 -*-
"""
	Fenomscrapers Module
"""
import re
import unicodedata


def get(title):
	if not title: return
	try: title = title.encode('utf-8')
	except: pass
	title = re.sub(r'&#(\d+);', '', title).lower()
	title = re.sub(r'(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
	title = title.replace(r'&quot;', '\"').replace('&amp;', '&')
	# title = re.sub(r'\n|([[].+?[]])|([(].+?[)])|\s(vs|v[.])\s|(:|;|-|–|"|,|\'|\_|\.|\?)|\~|\s', '', title).lower()
	title = re.sub(r'\n|([\[({].+?[})\]])|\s(vs[.]?|v[.])\s|([:;–\-"\',!_\.\?~])|\s', '', title) # removes bracketed content
	return title


def get_simple(title):
	if not title: return
	title = re.sub(r'(\d{4})', '', title).lower()
	title = re.sub(r'&#(\d+);', '', title)
	title = re.sub(r'(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', title)
	title = title.replace(r'&quot;', '\"').replace('&amp;', '&')
	# title = re.sub(r'\n|\(|\)|\[|\]|\{|\}|\s(vs|v[.])\s|(:|;|-|–|"|,|\'|\_|\.|\?)|\~|\s', '', title).lower()
	title = re.sub(r'\n|[()[\]{}]|\s(vs[.]?|v[.])\s|[:;–\-",\'!_.?~]|\s', '', title) # keeps bracketed content unlike .get()
	title = re.sub(r'<.*?>', '', title) # removes tags?
	return title


def geturl(title):
	if not title: return
	title = title.lower()
	try: 
		title = title.translate(None, ':*?"\'\.<>|&!,')
	except:
		for c in ':*?"\'\.<>|&!,':
			title = title.replace(c, '')
	title = title.replace('/', '-')
	title = title.replace(' ', '-')
	title = title.replace('--', '-')
	return title


def normalize(title):
	try:
		try: return title.decode('ascii').encode("utf-8")
		except: pass
		return str(''.join(c for c in unicodedata.normalize('NFKD', unicode(title.decode('utf-8'))) if unicodedata.category(c) != 'Mn'))
	except:
		return title