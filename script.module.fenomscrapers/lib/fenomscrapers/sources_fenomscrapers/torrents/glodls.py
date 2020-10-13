# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 10-05-2020)

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
		self.domains = ['glodls.to']
		self.base_link = 'https://glodls.to/'
		self.tvsearch = 'search_results.php?search={0}&cat=41&incldead=0&inclexternal=0&lang=1&sort=seeders&order=desc'
		self.moviesearch = 'search_results.php?search={0}&cat=1&incldead=0&inclexternal=0&lang=1&sort=size&order=desc'
		self.min_seeders = 0 # to many items with no value but cached links
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
		sources = []
		if not url: return sources
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

			if 'tvshowtitle' in data:
				url = self.tvsearch.format(quote_plus(query))
			else:
				url = self.moviesearch.format(quote_plus(query))
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)

			items = self.get_sources(url)
			for item in items:
				try:
					name = item[0]
					url = unquote_plus(item[1]).replace('&amp;', '&').replace(' ', '.')
					url = url.split('&tr')[0]

					hash = re.compile('btih:(.*?)&').findall(url)[0].lower()
					quality, info = source_utils.get_release_quality(name, url)

					if item[2] != '0':
						info.insert(0, item[2])
					info = ' | '.join(info)

					sources.append({'source': 'torrent', 'seeders': item[4], 'hash': hash, 'name': name, 'quality': quality,
											'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': item[3]})
				except:
					source_utils.scraper_error('GLODLS')
					pass
			return sources
		except:
			source_utils.scraper_error('GLODLS')
			return sources


	def get_sources(self, url):
		items = []
		try:
			headers = {'User-Agent': client.agent()}
			r = client.request(url, headers=headers)
			posts = client.parseDOM(r, 'tr', attrs={'class': 't-row'})
			posts = [i for i in posts if not 'racker:' in i]

			for post in posts:
				ref = client.parseDOM(post, 'a', ret='href')
				url = [i for i in ref if 'magnet:' in i][0]

				name = client.parseDOM(post, 'a', ret='title')[0]
				name = unquote_plus(name)
				name = source_utils.clean_name(self.title, name)
				if source_utils.remove_lang(name, self.episode_title):
					continue

				if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year):
					continue

				# filter for episode multi packs (ex. S01E01-E17 is also returned in query)
				if self.episode_title:
					if not source_utils.filter_single_episodes(self.hdlr, name):
						continue

				try:
					seeders = int(re.findall("<td.*?<font color='green'><b>([0-9]+|[0-9]+,[0-9]+)</b>", post)[0].replace(',', ''))
					if self.min_seeders > seeders:
						continue
				except:
					seeders = 0
					pass

				try:
					size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GiB|MiB|GB|MB))', post)[0]
					dsize, isize = source_utils._size(size)
				except:
					isize = '0'
					dsize = 0
					pass

				items.append((name, url, isize, dsize, seeders))

			return items
		except:
			source_utils.scraper_error('GLODLS')
			return items


	def resolve(self, url):
		return url