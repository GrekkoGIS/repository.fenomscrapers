# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 9-20-2020)

'''
    Fenomscrapers Project
'''

import json
import re
import time

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote_plus
except ImportError: from urllib.parse import urlencode, quote_plus

from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import client
from fenomscrapers.modules import dom_parser  # switch to client.parseDOM() to rid import
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 26
		self.language = ['en']
		self.domains = ['onlineseries.ucoz.com']
		self.base_link = 'https://onlineseries.ucoz.com'
		self.search_link = 'search/?q=%s'


	def movie(self, imdb, title, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return


	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if not url: return
			url = parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urlencode(url)
			return url
		except:
			return


	def sources(self, url, hostDict):
		self.sources = []
		try:
			if not url: return self.sources

			self.hostDict = hostDict
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			self.title = self.title.replace('&', 'and').replace('Special Victims Unit', 'SVU')

			self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
			self.year = data['year']

			query = '%s %s' % (self.title, self.hdlr)
			query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)

			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)

			r = client.request(url)

			# switch to client.parseDOM() to rid import
			posts = dom_parser.parse_dom(r, 'div', {'class':'eTitle'})
			posts = [dom_parser.parse_dom(i.content, 'a', req='href') for i in posts if i]
			posts = [(i[0].attrs['href'], re.sub('<.+?>', '', i[0].content)) for i in posts if i]
			posts = [[i[0], i[1]] for i in posts]
			threads = []
			for i in posts:
				threads.append(workers.Thread(self.get_sources, i))
			[i.start() for i in threads]
			[i.join() for i in threads]

			alive = [x for x in threads if x.is_alive() is True]
			while alive:
				alive = [x for x in threads if x.is_alive() is True]
				time.sleep(0.1)
			return self.sources
		except:
			source_utils.scraper_error('ONLINESERIES')
			return self.sources


	def get_sources(self, url):
		try:
			item = client.request(url[0])
			if not item: return

			name = url[1]
			# log_utils.log('name = %s' % name, log_utils.LOGDEBUG)

			self.title = self.title.replace('!', '')
			t = name.split(self.hdlr)[0].replace(self.year, '').replace('(', '').replace(')', '').replace('&', 'and')
			tc = cleantitle.get(t)
			if tc != cleantitle.get(self.title):
				try:
					if tc == self.aliases[0]: pass
					else: return
				except:
					return
			if self.hdlr not in name:
				return

			links = dom_parser.parse_dom(item, 'a', req='href')
			links = [i.attrs['href'] for i in links]

			info = []
			try:
				size = re.findall('((?:\d+\.\d+|\d+\,\d+|\d+)\s*(?:GiB|MiB|GB|MB))', item)[0]
				div = 1 if size.endswith(('GB', 'GiB')) else 1024
				size = float(re.sub('[^0-9|/.|/,]', '', size)) / div
				size = '%.2f GB' % size
				info.append(size)
			except:
				pass
			info = ' | '.join(info)

			for url in links:
				if any(x in url.lower() for x in ['.rar.', '.zip.', '.iso.']) or any(url.lower().endswith(x) for x in ['.rar', '.zip', '.iso']):
					continue
				if any(x in url.lower() for x in ['youtube', 'sample', 'trailer']):
					continue

				valid, host = source_utils.is_host_valid(url, self.hostDict)
				if not valid:
					continue
				host = client.replaceHTMLCodes(host)
				try: host = host.encode('utf-8')
				except: pass

				quality, info2 = source_utils.get_release_quality(name, url)

				if url in str(self.sources):
					continue
				self.sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url,
														'info': info, 'direct': False, 'debridonly': True})
		except:
			source_utils.scraper_error('ONLINESERIES')
			pass


	def resolve(self, url):
		return url