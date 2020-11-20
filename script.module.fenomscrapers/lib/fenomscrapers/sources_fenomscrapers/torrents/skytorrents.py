# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 11-19-2020)

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
		self.domains = ['www.skytorrents.org']
		# self.base_link = 'https://www.skytorrents.lol/' # .lol behind cloudflare
		# self.search_link = '?query=%s'
		self.base_link = 'https://skytorrents.org/'
		self.search_link = '?search=%s'
		self.min_seeders = 0
		self.pack_capable = True


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

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			aliases = data['aliases']
			episode_title = data['title'] if 'tvshowtitle' in data else None
			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']

			query = '%s %s' % (title, hdlr)
			query = re.sub('[^A-Za-z0-9\s\.-]+', '', query)

			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)

			r = client.request(url)
			if '<tbody' not in r: return sources
			posts = client.parseDOM(r, 'tbody')[0]
			posts = client.parseDOM(posts, 'tr')

		except:
			source_utils.scraper_error('SKYTORRENTS')
			return sources

		for post in posts:
			try:
				post = re.sub(r'\n', '', post)
				post = re.sub(r'\t', '', post)
				link = re.findall('href="(magnet:.+?)".+<td style="text-align: center;color:green;">([0-9]+|[0-9]+,[0-9]+)</td>', post, re.DOTALL)

				for url, seeders, in link:
					url = unquote_plus(url).replace('&amp;', '&').replace(' ', '.').split('&tr')[0]
					url = source_utils.strip_non_ascii_and_unprintable(url)
					if url in str(sources):
						return
					hash = re.compile('btih:(.*?)&').findall(url)[0]

					name = url.split('&dn=')[1]
					name = source_utils.clean_name(title, name)
					if source_utils.remove_lang(name, episode_title):
						continue

					if not source_utils.check_title(title, aliases, name, hdlr, data['year']):
						continue

					# filter for episode multi packs (ex. S01E01-E17 is also returned in query)
					if episode_title:
						if not source_utils.filter_single_episodes(hdlr, name):
							continue

					try:
						seeders = int(seeders)
						if self.min_seeders > seeders:
							continue
					except:
						seeders = 0
						pass

					quality, info = source_utils.get_release_quality(name, url)
					try:
						size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GiB|MiB|GB|MB))', post)[0]
						dsize, isize = source_utils._size(size)
						info.insert(0, isize)
					except:
						dsize = 0
						pass
					info = ' | '.join(info)

					sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
												'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			except:
				source_utils.scraper_error('SKYTORRENTS')
				return sources
		return sources


	def sources_packs(self, url, hostDict, search_series=False, total_seasons=None, bypass_filter=False):
		self.sources = []
		if not url: return self.sources
		try:
			self.search_series = search_series
			self.total_seasons = total_seasons
			self.bypass_filter = bypass_filter

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'].replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.imdb = data['imdb']
			self.year = data['year']
			self.season_x = data['season']
			self.season_xx = self.season_x.zfill(2)

			query = re.sub('[^A-Za-z0-9\s\.-]+', '', self.title)
			queries = [
						self.search_link % quote_plus(query + ' S%s' % self.season_xx),
						self.search_link % quote_plus(query + ' Season %s' % self.season_x)
							]
			if search_series:
				queries = [
						self.search_link % quote_plus(query + ' Season'),
						self.search_link % quote_plus(query + ' Complete')
								]

			threads = []
			for url in queries:
				link = urljoin(self.base_link, url)
				threads.append(workers.Thread(self.get_sources_packs, link))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('SKYTORRENTS')
			return self.sources


	def get_sources_packs(self, link):
		# log_utils.log('link = %s' % str(link), __name__, log_utils.LOGDEBUG)
		try:
			r = client.request(link)
			if not r: return
			if '<tbody' not in r: return
			posts = client.parseDOM(r, 'tbody')[0]
			posts = client.parseDOM(posts, 'tr')
		except:
			source_utils.scraper_error('SKYTORRENTS')
			return

		for post in posts:
			try:
				post = re.sub(r'\n', '', post)
				post = re.sub(r'\t', '', post)
				link = re.findall('href="(magnet:.+?)".+<td style="text-align: center;color:green;">([0-9]+|[0-9]+,[0-9]+)</td>', post, re.DOTALL)

				for url, seeders, in link:
					url = unquote_plus(url).replace('&amp;', '&').replace(' ', '.').split('&tr')[0]
					url = source_utils.strip_non_ascii_and_unprintable(url)
					if url in str(self.sources):
						return
					hash = re.compile('btih:(.*?)&').findall(url)[0]
					name = url.split('&dn=')[1]
					name = source_utils.clean_name(self.title, name)
					if source_utils.remove_lang(name):
						continue

					if not self.search_series:
						if not self.bypass_filter:
							if not source_utils.filter_season_pack(self.title, self.aliases, self.year, self.season_x, name):
								continue
						package = 'season'

					elif self.search_series:
						if not self.bypass_filter:
							valid, last_season = source_utils.filter_show_pack(self.title, self.aliases, self.imdb, self.year, self.season_x, name, self.total_seasons)
							if not valid:
								continue
						else:
							last_season = self.total_seasons
						package = 'show'

					try:
						seeders = int(seeders)
						if self.min_seeders > seeders:
							continue
					except:
						seeders = 0
						pass

					quality, info = source_utils.get_release_quality(name, url)
					try:
						size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GiB|MiB|GB|MB))', post)[0]
						dsize, isize = source_utils._size(size)
						info.insert(0, isize)
					except:
						dsize = 0
						pass
					info = ' | '.join(info)

					item = {'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
								'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize, 'package': package}
					if self.search_series:
						item.update({'last_season': last_season})
					self.sources.append(item)
			except:
				source_utils.scraper_error('SKYTORRENTS')
				pass


	def resolve(self, url):
		return url