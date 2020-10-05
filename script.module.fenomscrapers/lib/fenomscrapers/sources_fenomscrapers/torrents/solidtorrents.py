# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (updated 10-05-2020)

'''
    Fenomscrapers Project
'''

import re
import json

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
		self.domains = ['solidtorrents.net']
		self.base_link = 'https://solidtorrents.net'
		self.search_link = '/api/v1/search?q=%s&category=all&sort=size'
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
		self.sources = []
		try:
			if not url: return self.sources

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

			urls = []
			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			urls.append(url)
			urls.append(url + '&skip=20')
			urls.append(url + '&skip=40')
			urls.append(url + '&skip=60')
			urls.append(url + '&skip=80')
			# log_utils.log('urls = %s' % urls, log_utils.LOGDEBUG)

			threads = []
			for url in urls:
				threads.append(workers.Thread(self.get_sources, url))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('SOLIDTORRENTS')
			return self.sources


	def get_sources(self, url):
		try:
			r = client.request(url)
			if not r: return
			r = json.loads(r)
			results = r['results']

			for item in results:
				try:
					url = unquote_plus(item['magnet']).replace(' ', '.')
					url = re.sub(r'(&tr=.+)&dn=', '&dn=', url) # some links on solidtorrents &tr= before &dn=
					url = source_utils.strip_non_ascii_and_unprintable(url)
					hash = item['infohash'].lower()

					name = item['title']
					name = source_utils.clean_name(self.title, name)
					if source_utils.remove_lang(name, self.episode_title):
						continue

					if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year):
						continue

					# filter for episode multi packs (ex. S01E01-E17 is also returned in query)
					if self.episode_title:
						if not source_utils.filter_single_episodes(self.hdlr, name):
							continue

					if url in str(self.sources):
						continue

					try:
						seeders = int(item['swarm']['seeders'])
						if self.min_seeders > seeders: 
							continue
					except:
						seeders = 0
						pass

					quality, info = source_utils.get_release_quality(name, url)
					try:
						dsize, isize = source_utils.convert_size(item["size"], to='GB')
						info.insert(0, isize)
					except:
						dsize = 0
						pass
					info = ' | '.join(info)

					self.sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
												'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
				except:
					source_utils.scraper_error('SOLIDTORRENTS')
					pass
		except:
			source_utils.scraper_error('SOLIDTORRENTS')
			pass


	def sources_packs(self, url, hostDict, search_series=False, total_seasons=None, bypass_filter=False):
		self.sources = []
		try:
			self.search_series = search_series
			self.total_seasons = total_seasons
			self.bypass_filter = bypass_filter

			if not url: return self.sources

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'].replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.imdb = data['imdb']
			self.year = data['year']
			self.season_x = data['season']
			self.season_xx = self.season_x.zfill(2)

			# query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', self.title)
			query = re.sub('[^A-Za-z0-9\s\.-]+', '', self.title)
			queries = [
						self.search_link % quote_plus(query + ' S%s' % self.season_xx),
						self.search_link % quote_plus(query + ' Season %s' % self.season_x)
							]
			if self.search_series:
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
			source_utils.scraper_error('SOLIDTORRENTS')
			return self.sources


	def get_sources_packs(self, link):
		# log_utils.log('link = %s' % str(link), __name__, log_utils.LOGDEBUG)
		try:
			r = client.request(link)
			if not r: return
			r = json.loads(r)
			results = r['results']

			for item in results:
				try:
					url = unquote_plus(item['magnet']).replace(' ', '.')
					url = re.sub(r'(&tr=.+)&dn=', '&dn=', url) # some links on solidtorrents &tr= before &dn=
					url = source_utils.strip_non_ascii_and_unprintable(url)
					hash = item['infohash'].lower()

					name = item['title']
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

					if url in str(self.sources):
						continue

					try:
						seeders = int(item['swarm']['seeders'])
						if self.min_seeders > seeders: 
							continue
					except:
						seeders = 0
						pass

					quality, info = source_utils.get_release_quality(name, url)
					try:
						dsize, isize = source_utils.convert_size(item["size"], to='GB')
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
					source_utils.scraper_error('SOLIDTORRENTS')
					pass
		except:
			source_utils.scraper_error('SOLIDTORRENTS')
			pass


	def resolve(self, url):
		return url