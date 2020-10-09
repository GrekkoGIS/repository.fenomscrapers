# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (10-06-2020)

'''
    Fenomscrapers Project
'''

import re
try:
	from urlparse import parse_qs, urljoin
	from urllib import urlencode, quote_plus, unquote_plus
except:
	from urllib.parse import parse_qs, urljoin
	from urllib.parse import urlencode, quote_plus, unquote_plus

from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers

class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domains = ['ext.io']
		self.base_link = 'https://ext.to'
		self.search_link = '/search/?q=%s'
		self.min_seeders = 1
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
		try:
			if not url: return sources
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			episode_title = data['title'] if 'tvshowtitle' in data else None
			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
			year = data['year']
			aliases = data['aliases']

			query = '%s %s' % (title, hdlr)
			query = re.sub('[^A-Za-z0-9\s\.-]+', '', query)

			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)

			html = client.request(url)
			table = client.parseDOM(html, 'tbody')
			rows = client.parseDOM(table, 'tr')
		except:
			source_utils.scraper_error('EXT.TO')
			return sources

		for row in rows:
			try:
				if 'dwn-btn torrent-dwn' not in row:
					continue
				link = client.parseDOM(row, 'a', attrs={'class': 'dwn-btn torrent-dwn'}, ret='href')[0]
				hash = re.search('/torrent/(?:.+/)(.+?).torrent', link).group(1)
				name = re.search('\?title=(?:.+])(.+?).torrent', link).group(1)
				name = source_utils.clean_name(title, name)
				if source_utils.remove_lang(name, episode_title):
					continue

				url = 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name)
				if not source_utils.check_title(title, aliases, name, hdlr, year):
					continue

				# filter for episode multi packs (ex. S01E01-E17 is also returned in query)
				if episode_title:
					if not source_utils.filter_single_episodes(hdlr, name):
						continue

				try:
					seeders = int(re.findall('<span class="text-success">([0-9]+)</span>', row, re.DOTALL)[0])
					if self.min_seeders > seeders:
						continue
				except:
					seeders = 0
					pass

				quality, info = source_utils.get_release_quality(name, url)
				try:
					size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', row, re.DOTALL)[0]
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except:
					dsize = 0
					pass
				info = ' | '.join(info)

				sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
										'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			except:
				source_utils.scraper_error('EXT.TO')
				return sources
		return sources


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
			source_utils.scraper_error('EXT.TO')
			return self.sources


	def get_sources_packs(self, link):
		# log_utils.log('link = %s' % str(link), __name__, log_utils.LOGDEBUG)
		try:
			html = client.request(link)
			table = client.parseDOM(html, 'tbody')
			rows = client.parseDOM(table, 'tr')
		except:
			source_utils.scraper_error('EXT.TO')
			return sources

		for row in rows:
			try:
				if 'dwn-btn torrent-dwn' not in row:
					continue
				link = client.parseDOM(row, 'a', attrs={'class': 'dwn-btn torrent-dwn'}, ret='href')[0]
				hash = re.search('/torrent/(?:.+/)(.+?).torrent', link).group(1)
				name = re.search('\?title=(?:.+])(.+?).torrent', link).group(1)
				name = source_utils.clean_name(self.title, name)
				if source_utils.remove_lang(name):
					continue

				url = 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name)
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
					seeders = int(re.findall('<span class="text-success">([0-9]+)</span>', row, re.DOTALL)[0])
					if self.min_seeders > seeders:
						continue
				except:
					seeders = 0
					pass

				quality, info = source_utils.get_release_quality(name, url)
				try:
					size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', row, re.DOTALL)[0]
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
				source_utils.scraper_error('EXT.TO')
				pass


	def resolve(self, url):
		return url