# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (11-30-2020)

'''
    Fenomscrapers Project
'''

import json
import re

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode
except ImportError: from urllib.parse import urlencode

from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domains = ['yts.mx']
		self.base_link = 'https://yts.mx'
		self.search_link = '/api/v2/list_movies.json?query_term=%s'
		self.min_seeders = 0
		self.pack_capable = False


	def movie(self, imdb, title, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return


	def sources(self, url, hostDict):
		sources = []
		if not url: return sources
		try:
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['title'].replace('&', 'and')
			hdlr = data['year']
			aliases = data['aliases']
			imdb = data['imdb']

			url = self.search_link % imdb
			api_url = urljoin(self.base_link, url)
			# log_utils.log('api_url = %s' % api_url, log_utils.LOGDEBUG)

			rjson = client.request(api_url)
			if not rjson: return sources
			files = json.loads(rjson)
			if files.get('status') == 'error' or files.get('data').get('movie_count') == 0:
				return sources

			title_long = files.get('data').get('movies')[0].get('title_long').replace(' ', '.')
			torrents = files.get('data').get('movies')[0].get('torrents')

			for torrent in torrents:
				quality = torrent.get('quality')
				type = torrent.get('type')
				hash = torrent.get('hash')
				name = '%s.[%s].[%s].[YTS.MX]' % (title_long, quality, type)
				url = 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name)

				try:
					seeders = torrent.get('seeds')
					if self.min_seeders > seeders:
						continue
				except:
					seeders = 0
					pass

				if source_utils.remove_lang(name):
					continue

				if not source_utils.check_title(title, aliases, name, hdlr, data['year']):
					continue

				quality, info = source_utils.get_release_quality(name, url)
				try:
					size = torrent.get('size')
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
			source_utils.scraper_error('YTSWS')
			return sources


	def resolve(self, url):
		return url