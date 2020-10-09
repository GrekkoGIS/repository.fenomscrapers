# -*- coding: utf-8 -*-
# (updated 9-20-2020)

'''
    Fenomscrapers Project
'''

import re

try: from urlparse import urljoin
except ImportError: from urllib.parse import urljoin

from fenomscrapers.modules import cfscrape
from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 31
		self.language = ['en']
		self.domains = ['filmxy.nl', 'filmxy.me', 'filmxy.one', 'filmxy.ws', 'filmxy.live']
		self.base_link = 'https://www.filmxy.nl'
		self.search_link = '/%s-%s'
		self.scraper = cfscrape.create_scraper()


	def movie(self, imdb, title, aliases, year):
		try:
			title = cleantitle.geturl(title)
			url = urljoin(self.base_link, (self.search_link % (title, year)))
			return url
		except:
			source_utils.scraper_error('FILEXY')
			return


	def sources(self, url, hostDict):
		sources = []
		try:
			if not url: return sources
			headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0'}
			result = self.scraper.get(url, headers=headers).content
			streams = re.compile('data-player="&lt;[A-Za-z]{6}\s[A-Za-z]{3}=&quot;(.+?)&quot;', re.DOTALL).findall(
				result)
			for link in streams:
				quality = source_utils.check_url(link)
				valid, host = source_utils.is_host_valid(link, hostDict)
				if valid:
					if link in str(sources):
						continue
					if quality == 'SD':
						sources.append({'source': host, 'quality': '720p', 'info': '', 'language': 'en', 'url': link, 'direct': False, 'debridonly': True})
					else:
						sources.append({'source': host, 'quality': quality, 'info': '', 'language': 'en', 'url': link, 'direct': False, 'debridonly': True})
			return sources
		except:
			source_utils.scraper_error('FILEXY')
			return sources


	def resolve(self, url):
		return url