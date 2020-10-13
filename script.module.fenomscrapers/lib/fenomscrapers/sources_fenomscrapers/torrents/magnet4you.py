# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (updated 10-05-2020)

'''
    Fenomscrapers Project
'''

import re

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote_plus, unquote_plus
except ImportError: from urllib.parse import urlencode, quote_plus, unquote_plus

from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domains = ['magnet4you.me']
		self.base_link = 'http://magnet4you.me'
		self.search_link = '/search.php?s=%s'
		self.min_seeders = 0
		self.pack_capable = False


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
		if not url: return self.sources
		try:
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			self.title = self.title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.episode_title = data['title'] if 'tvshowtitle' in data else None
			self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
			self.year = data['year']

			query = '%s %s' % (self.title, self.hdlr)
			query = re.sub('[^A-Za-z0-9\s\.-]+', '', query)

			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)

			r = client.request(url)
			if not r: return self.sources
			rows = client.parseDOM(r, 'div', attrs={'id': 'profile1'})

			threads = []
			for row in rows:
				threads.append(workers.Thread(self.get_sources, row))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('MAGNET4YOU')
			return self.sources


	def get_sources(self, row):
		try:
			if 'magnet' not in row: return
			url = re.findall('href="(magnet:.+?)"', row, re.DOTALL)[0]
			url = unquote_plus(url).replace('&amp;', '&').replace(' ', '.').split('&tr')[0]
			if url in str(self.sources):
				return
			hash = re.compile('btih:(.*?)&').findall(url)[0]
			name = url.split('&dn=')[1]
			name = source_utils.clean_name(self.title, name)
			if source_utils.remove_lang(name, self.episode_title):
				return

			if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year):
				return

			# filter for episode multi packs (ex. S01E01-E17 is also returned in query)
			if self.episode_title:
				if not source_utils.filter_single_episodes(self.hdlr, name):
					return

			try:
				seeders = int(re.findall('<span style="color:#008000"><strong>\s*([0-9]+)\s*</strong>', row, re.DOTALL)[0].replace(',', ''))
				if self.min_seeders > seeders: 
					return
			except:
				seeders = 0
				pass

			quality, info = source_utils.get_release_quality(name, url)
			try:
				size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', row, re.DOTALL)[0]
				dsize, isize = source_utils._size(size)
				info.insert(0, isize)
			except:
				dsize = 0
				pass
			info = ' | '.join(info)

			self.sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
												'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
		except:
			source_utils.scraper_error('MAGNET4YOU')
			pass


	def resolve(self, url):
		return url