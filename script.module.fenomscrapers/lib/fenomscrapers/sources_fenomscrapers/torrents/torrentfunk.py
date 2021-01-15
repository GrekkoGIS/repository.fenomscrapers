# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (updated 1-09-2021)
'''
	Fenomscrapers Project
'''

import re
try: #Py2
	from urlparse import parse_qs, urljoin
	from urllib import urlencode, quote_plus
except ImportError: #Py3
	from urllib.parse import parse_qs, urljoin, urlencode, quote_plus

from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 3
		self.language = ['en']
		self.domains = ['torrentfunk.com', 'torrentfunk2.com']
		self.base_link = 'https://www.torrentfunk.com'
		self.search_link = '/all/torrents/%s.html?v=&smi=&sma=&i=100&sort=size&o=desc'
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
		if not url: return self.sources
		try:
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			self.title = self.title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.episode_title = data['title'] if 'tvshowtitle' in data else None
			self.year = data['year']
			self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else self.year

			query = '%s %s' % (self.title, self.hdlr)
			query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', query)
			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)

			r = client.request(url, timeout='5')
			if not r: return self.sources
			r = client.parseDOM(r, 'table', attrs={'class': 'tmain'})[0]
			links = re.findall(r'<a href="(/torrent/.+?)">(.+?)</a>', r, re.DOTALL)

			threads = []
			for link in links:
				threads.append(workers.Thread(self.get_sources, link))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('TORRENTFUNK')
			return self.sources


	def get_sources(self, link):
		try:
			try: url = link[0].encode('ascii', errors='ignore').decode('ascii', errors='ignore').replace('&nbsp;', ' ')
			except: url = link[0].replace('&nbsp;', ' ')
			if '/torrent/' not in url: return

			try: name = link[1].encode('ascii', errors='ignore').decode('ascii', errors='ignore').replace('&nbsp;', '.')
			except: name = link[1].replace('&nbsp;', '.')
			if '<span' in name:
				nam = name.split('<span')[0].replace(' ', '.')
				span = client.parseDOM(name, 'span')[0].replace('-', '.')
				name = '%s%s' % (nam, span)
			name = source_utils.clean_name(name)
			if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year): return
			name_info = source_utils.info_from_name(name, self.title, self.year, self.hdlr, self.episode_title)
			if source_utils.remove_lang(name_info): return

			if not self.episode_title: #filter for eps returned in movie query (rare but movie and show exists for Run in 2020)
				ep_strings = [r'(?:\.|\-)s\d{2}e\d{2}(?:\.|\-|$)', r'(?:\.|\-)s\d{2}(?:\.|\-|$)', r'(?:\.|\-)season(?:\.|\-)\d{1,2}(?:\.|\-|$)']
				if any(re.search(item, name.lower()) for item in ep_strings): return

			if not url.startswith('http'): 
				link = urljoin(self.base_link, url)

			link = client.request(link, timeout='5')
			if link is None: 	return
			hash = re.findall(r'<b>Infohash</b></td><td valign=top>(.+?)</td>', link, re.DOTALL)[0]
			url = 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name)
			if url in str(self.sources): return

			try:
				seeders = int(re.findall(r'<b>Swarm:</b></td><td valign=top><font color=red>([0-9]+)</font>', link, re.DOTALL)[0].replace(',', ''))
				if self.min_seeders > seeders: return  # site does not seem to report seeders
			except:
				seeders = 0

			quality, info = source_utils.get_release_quality(name_info, url)
			try:
				size = re.findall(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', link)[0]
				dsize, isize = source_utils._size(size)
				info.insert(0, isize)
			except:
				dsize = 0
			info = ' | '.join(info)

			self.sources.append({'provider': 'torrentfunk', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info,
												'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
		except:
			source_utils.scraper_error('TORRENTFUNK')


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

			query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', self.title)
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
			source_utils.scraper_error('TORRENTFUNK')
			return self.sources


	def get_sources_packs(self, url):
		try:
			r = client.request(url, timeout='5')
			if not r: return
			r = client.parseDOM(r, 'table', attrs={'class': 'tmain'})[0]
			links = re.findall(r'<a href="(/torrent/.+?)">(.+?)</a>', r, re.DOTALL)

			for link in links:
				try: url = link[0].encode('ascii', errors='ignore').decode('ascii', errors='ignore').replace('&nbsp;', ' ')
				except: url = link[0].replace('&nbsp;', ' ')
				if '/torrent/' not in url: continue

				try: name = link[1].encode('ascii', errors='ignore').decode('ascii', errors='ignore').replace('&nbsp;', '.')
				except: name = link[1].replace('&nbsp;', '.')
				if '<span' in name:
					nam = name.split('<span')[0].replace(' ', '.')
					span = client.parseDOM(name, 'span')[0].replace('-', '.')
					name = '%s%s' % (nam, span)
				name = source_utils.clean_name(name)

				if not self.search_series:
					if not self.bypass_filter:
						if not source_utils.filter_season_pack(self.title, self.aliases, self.year, self.season_x, name): continue
					package = 'season'

				elif self.search_series:
					if not self.bypass_filter:
						valid, last_season = source_utils.filter_show_pack(self.title, self.aliases, self.imdb, self.year, self.season_x, name, self.total_seasons)
						if not valid: continue
					else:
						last_season = self.total_seasons
					package = 'show'

				name_info = source_utils.info_from_name(name, self.title, self.year, season=self.season_x, pack=package)
				if source_utils.remove_lang(name_info): continue

				if not url.startswith('http'): 
					link = urljoin(self.base_link, url)

				link = client.request(link, timeout='5')
				if link is None: 	continue
				hash = re.findall(r'<b>Infohash</b></td><td valign=top>(.+?)</td>', link, re.DOTALL)[0]
				url = 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name)
				if url in str(self.sources): continue

				try:
					seeders = int(re.findall(r'<b>Swarm:</b></td><td valign=top><font color=red>([0-9]+)</font>', link, re.DOTALL)[0].replace(',', ''))
					if self.min_seeders > seeders: continue# site does not seem to report seeders
				except:
					seeders = 0

				quality, info = source_utils.get_release_quality(name_info, url)
				try:
					size = re.findall(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', link)[0]
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except:
					dsize = 0
				info = ' | '.join(info)

				item = {'provider': 'torrentfunk', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
							'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize, 'package': package}
				if self.search_series:
					item.update({'last_season': last_season})
				self.sources.append(item)
		except:
			source_utils.scraper_error('TORRENTFUNK')


	def resolve(self, url):
		return url