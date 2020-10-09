# -*- coding: utf-8 -*-
# (updated 9-20-2020)

'''
    Fenomscrapers Project
'''

import json

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote_plus
except ImportError: from urllib.parse import urlencode, quote_plus

from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 32
		self.language = ['en']
		self.domains = ['watchepisodes.com', 'watchepisodes.unblocked.pl']
		self.base_link = 'http://www.watchepisodes4.com/'
		self.search_link = 'search/ajax_search?q=%s'


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			source_utils.scraper_error('WATCHEPISODES')
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
			source_utils.scraper_error('WATCHEPISODES')
			return


	def sources(self, url, hostDict):
		sources = []
		try:
			if not url: return sources

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle']
			hdlr = 's%02de%02d' % (int(data['season']), int(data['episode']))
			query = quote_plus(cleantitle.getsearch(title))
			surl = urljoin(self.base_link, self.search_link % query)
			# log_utils.log('surl = %s' % surl, log_utils.LOGDEBUG)
			r = client.request(surl, XHR=True)
			if not r or 'series' not in r:
				return sources
			r = json.loads(r)
			r = r['series']

			for i in r:
				tit = i['value']
				if cleantitle.get(title) != cleantitle.get(tit):
					continue
				slink = i['seo']
				slink = urljoin(self.base_link, slink)
				r = client.request(slink)
				if not data['imdb'] in r:
					continue

				data = client.parseDOM(r, 'div', {'class': 'el-item\s*'})

				epis = [client.parseDOM(i, 'a', ret='href')[0] for i in data if i]
				epis = [i for i in epis if hdlr in i.lower()][0]

				r = client.request(epis)
				links = client.parseDOM(r, 'a', ret='data-actuallink')

				for url in links:
					if url in str(sources):
						continue
					valid, host = source_utils.is_host_valid(url, hostDict)
					if not valid:
						continue
					sources.append({'source': host, 'quality': 'SD', 'info': '', 'language': 'en', 'url': url, 'direct': False, 'debridonly': True})
			return sources
		except:
			source_utils.scraper_error('WATCHEPISODES')
			return sources


	def resolve(self, url):
		return url