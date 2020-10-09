# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 08-24-2019 by JewBMX in Scrubs.
# modified by Venom for Fenomscrapers (updated url 9-20-2020)

'''
    Fenomscrapers Project
'''

import re
import requests

from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import directstream
from fenomscrapers.modules import getSum
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 33
		self.language = ['en']
		self.domains = ['watchserieshd.tv']
		self.base_link = 'https://watchserieshd.tv'
		self.search_link = '/series/%s-season-%s-episode-%s'


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = cleantitle.geturl(tvshowtitle)
			return url
		except:
			source_utils.scraper_error('WATCHSERIESHD')
			return


	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if not url: return
			tvshowtitle = url
			url = self.base_link + self.search_link % (tvshowtitle, season, episode)
			return url
		except:
			source_utils.scraper_error('WATCHSERIESHD')
			return


	def sources(self, url, hostDict):
		sources = []
		try:
			if not url: return sources
			r = getSum.get(url)
			match = getSum.findSum(r)
			for url in match:
				if 'vidcloud' in url:
					result = getSum.get(url)
					match = getSum.findSum(result)
					for link in match:
						link = "https:" + link if not link.startswith('http') else link
						link = requests.get(link).url if 'vidnode' in link else link
						if link in str(sources):
							continue
						valid, host = source_utils.is_host_valid(link, hostDict)
						if valid:
							quality, info = source_utils.get_release_quality(link, link)
							sources.append({'source': host, 'quality': quality, 'language': 'en', 'info': info, 'url': link, 'direct': False, 'debridonly': False})
				else:
					if url in str(sources):
						continue
					valid, host = source_utils.is_host_valid(url, hostDict)
					if valid:
						quality, info = source_utils.get_release_quality(url, url)
						sources.append({'source': host, 'quality': quality, 'language': 'en', 'info': info, 'url': url, 'direct': False, 'debridonly': True})
			return sources
		except:
			source_utils.scraper_error('WATCHSERIESHD')
			return sources


	def resolve(self, url):
		if "google" in url:
			return directstream.googlepass(url)
		elif 'vidcloud' in url:
			r = getSum.get(url)
			url = re.findall("file: '(.+?)'", r)[0]
			return url
		else:
			return url