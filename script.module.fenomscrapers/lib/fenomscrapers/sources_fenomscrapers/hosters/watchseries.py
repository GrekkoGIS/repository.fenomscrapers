# -*- coding: utf-8 -*-
# (updated 9-20-2020)

'''
	Fenomscrapers Project
'''

import re

try: from urlparse import urljoin
except ImportError: from urllib.parse import urljoin

from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import client
from fenomscrapers.modules import dom_parser
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 31
		self.language = ['en']
		self.domains = ['watchseries.movie', 'watch-series.co']
		self.base_link = 'https://www6.watchseries.movie'
		self.search_link = '/series/%s-season-%s-episode-%s'


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = tvshowtitle.replace(" ", "-").lower()
			return url
		except:
			source_utils.scraper_error('WATCHSERIES')
			return


	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			url = urljoin(self.base_link, self.search_link % (url, season, episode))
			return url
		except:
			source_utils.scraper_error('WATCHSERIES')
			return


	def sources(self, url, hostDict):
		sources = []
		try:
			if not url: return sources

			result = client.request(url)
			dom = dom_parser.parse_dom(result, 'a', req='data-video')
			urls = [i.attrs['data-video'] if i.attrs['data-video'].startswith('https') else 'https:' + i.attrs['data-video'] for i in dom]

			for url in urls:
				if url in str(sources):
					continue
				valid, host = source_utils.is_host_valid(url, hostDict)
				if not valid:
					continue
				try: url.decode('utf-8')
				except: pass
				sources.append({'source': host, 'quality': 'SD', 'info': '', 'language': 'en', 'url': url, 'direct': False, 'debridonly': True})

			return sources
		except:
			source_utils.scraper_error('WATCHSERIES')
			return sources


	def resolve(self, url):
		return url