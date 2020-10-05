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


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domains = ['topnow.se']
		self.base_link = 'http://topnow.se'
		self.search_link = '/index.php?search=%s'
		self.show_link = '/index.php?show=%s'
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
		try:
			sources = []
			if not url: return sources

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			aliases = data['aliases']
			episode_title = data['title'] if 'tvshowtitle' in data else None
			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else ('(' + data['year'] + ')')

			# query = '%s %s' % (title, hdlr) #site now  fails with year in query
			query = title
			query = re.sub('[^A-Za-z0-9\s\.-]+', '', query)

			if 'tvshowtitle' in data:
				url = self.show_link % query.replace(' ', '-')
			else:
				url = self.search_link % quote_plus(query)

			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, __name__, log_utils.LOGDEBUG)

			r = client.request(url)
			if not r: return sources
			if 'No results were found' in r:
				return sources

			r = client.parseDOM(r, 'div', attrs={'class': 'card'})
			for i in r:
				url = re.compile('href="(magnet.+?)\s*?"').findall(i)[0]
				try: url = unquote_plus(url).decode('utf8').replace('&amp;', '&').replace(' ', '.')
				except: url = unquote_plus(url).replace('&amp;', '&').replace(' ', '.')
				url = url.split('&tr=')[0].replace(' ', '.')
				hash = re.compile('btih:(.*?)&').findall(url)[0]

				name = url.split('&dn=')[1]
				name = source_utils.clean_name(title, name)
				if source_utils.remove_lang(name, episode_title):
					continue

				if not source_utils.check_title(title, aliases, name, hdlr.replace('(', '').replace(')', ''), data['year']):
					continue

				seeders = 0 # seeders not available on topnow
				quality, info = source_utils.get_release_quality(name, url)
				try:
					size = re.findall('((?:\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|MB|MiB))', i)[-1] # file size is no longer available on topnow's new site
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except:
					dsize = 0
					pass
				info = ' | '.join(info)

				sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
										'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})

			return sources
		except:
			source_utils.scraper_error('TOPNOW')
			return sources

	def resolve(self, url):
		return url