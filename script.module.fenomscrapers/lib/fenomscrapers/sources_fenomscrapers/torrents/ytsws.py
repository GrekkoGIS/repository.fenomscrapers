# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 10-05-2020)

'''
    Fenomscrapers Project
'''

import re

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote, unquote_plus
except ImportError: from urllib.parse import urlencode, quote, unquote_plus

from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domains = ['yts.ws', 'yts.mx', 'yts.pm']
		self.base_link = 'https://yifyddl.co'
		self.search_link = '/movie/%s'
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
			episode_title = data['title'] if 'tvshowtitle' in data else None
			hdlr = data['year']
			aliases = data['aliases']

			query = '%s %s' % (title, hdlr)
			query = re.sub('[^A-Za-z0-9\s\.-]+', '', query)

			url = self.search_link % quote(query)
			url = urljoin(self.base_link, url).replace('%20', '-')
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)

			html = client.request(url)
			if not html: return sources

			quality_size = client.parseDOM(html, 'p', attrs={'class': 'quality-size'})
			tit = client.parseDOM(html, 'title')[0]

			try: results = client.parseDOM(html, 'div', attrs={'class': 'ava1'})
			except: return sources

			p = 0
			for torrent in results:
				link = re.findall('a data-torrent-id=".+?" href="(magnet:.+?)" class=".+?" title="(.+?)"', torrent, re.DOTALL)

				for url, ref in link:
					url = str(client.replaceHTMLCodes(url).split('&tr')[0].replace(' ', ''))
					hash = re.compile('btih:(.*?)&').findall(url)[0]

					name = url.split('&dn=')[1]
					name = unquote_plus(name)
					name = source_utils.clean_name(title, name)
					if source_utils.remove_lang(name, episode_title):
						continue

					if not source_utils.check_title(title, aliases, tit, hdlr, data['year']):
						continue

					# filter for episode multi packs (ex. S01E01-E17 is also returned in query)
					if episode_title:
						if not source_utils.filter_single_episodes(hdlr, name):
							continue

					seeders = 0 # not available on yts
					quality, info = source_utils.get_release_quality(ref, url)
					try:
						size = re.findall('((?:\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|MB|MiB))', quality_size[p])[-1]
						dsize, isize = source_utils._size(size)
						info.insert(0, isize)
					except:
						dsize = 0
						pass
					p += 1
					info = ' | '.join(info)

					sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
											'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			return sources
		except:
			source_utils.scraper_error('YTSWS')
			return sources


	def resolve(self, url):
		return url