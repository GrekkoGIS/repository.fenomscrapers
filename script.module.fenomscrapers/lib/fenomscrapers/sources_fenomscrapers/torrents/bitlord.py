# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (updated 2-26-2021)
"""
	Fenomscrapers Project
"""

from json import loads as jsloads
import re
try: #Py2
	from urlparse import parse_qs, urljoin
	from urllib import urlencode, quote_plus, unquote_plus
except ImportError: #Py3
	from urllib.parse import parse_qs, urljoin, urlencode, quote_plus, unquote_plus

from fenomscrapers.modules import cache
from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 2
		self.language = ['en']
		self.domain = ['bitlordsearch.com']
		self.base_link = 'http://www.bitlordsearch.com'
		self.search_link = '/search?q=%s'
		self.api_search_link = '/get_list'
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
			year = data['year']
			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else year

			query = '%s %s' % (title, hdlr)
			query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', query)
			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, __name__, log_utils.LOGDEBUG)
			api_url = urljoin(self.base_link, self.api_search_link)

			headers = cache.get(self._get_token_and_cookies, 1)
			if not headers: return sources
			headers.update({'Referer': url})

			query_data = {
				'query': query,
				'offset': 0,
				'limit': 99,
				'filters[field]': 'seeds',
				'filters[sort]': 'desc',
				'filters[time]': 4,
				'filters[category]': 3 if 'tvshowtitle' not in data else 4,
				'filters[adult]': False,
				'filters[risky]': False}

			rjson = client.request(api_url, post=query_data, headers=headers, timeout='5')
			if not rjson: return sources
			files = jsloads(rjson)
			error = files.get('error')
			if error: return sources
		except:
			source_utils.scraper_error('BITLORD')
			return sources

		for file in files.get('content'):
			try:
				name = source_utils.clean_name(file.get('name'))
				if not source_utils.check_title(title, aliases, name, hdlr, year): continue
				name_info = source_utils.info_from_name(name, title, year, hdlr, episode_title)
				if source_utils.remove_lang(name_info): continue

				url = unquote_plus(file.get('magnet')).replace('&amp;', '&').replace(' ', '.')
				url = re.sub(r'(&tr=.+)&dn=', '&dn=', url) # some links on bitlord &tr= before &dn=
				url = url.split('&tr=')[0].split('&xl=')[0]
				url = source_utils.strip_non_ascii_and_unprintable(url)
				hash = re.compile(r'btih:(.*?)&', re.I).findall(url)[0]

				if not episode_title: #filter for eps returned in movie query (rare but movie and show exists for Run in 2020)
					ep_strings = [r'[.-]s\d{2}e\d{2}([.-]?)', r'[.-]s\d{2}([.-]?)', r'[.-]season[.-]?\d{1,2}[.-]?']
					if any(re.search(item, name.lower()) for item in ep_strings): continue

				try:
					seeders = file.get('seeds')
					if self.min_seeders > seeders: continue
				except: seeders = 0

				quality, info = source_utils.get_release_quality(name_info, url)
				try:
					size = file.get('size')
					size = str(size) + ' GB' if len(str(size)) == 1 else str(size) + ' MB'
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except: dsize = 0
				info = ' | '.join(info)

				sources.append({'provider': 'bitlord', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
											'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			except:
				source_utils.scraper_error('BITLORD')
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
			self.headers = cache.get(self._get_token_and_cookies, 1)

			query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', self.title)
			queries = [
						quote_plus(query + ' S%s' % self.season_xx),
						quote_plus(query + ' Season %s' % self.season_x)]
			if search_series:
				queries = [
						quote_plus(query + ' Season'),
						quote_plus(query + ' Complete')]
			threads = []
			for url in queries:
				link = urljoin(self.base_link, self.search_link % url).replace('+', '-')
				threads.append(workers.Thread(self.get_sources_packs, link, url.replace('+', '-')))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('BITLORD')
			return self.sources


	def get_sources_packs(self, link, url):
		try:
			self.headers.update({'Referer': link})
			query_data = {
				'query': url,
				'offset': 0,
				'limit': 99,
				'filters[field]': 'seeds',
				'filters[sort]': 'desc',
				'filters[time]': 4,
				'filters[category]': 4,
				'filters[adult]': False,
				'filters[risky]': False}
			api_url = urljoin(self.base_link, self.api_search_link)
			rjson = client.request(api_url, post=query_data, headers=self.headers, timeout='5')
			if not rjson: return
			files = jsloads(rjson)
			error = files.get('error')
			if error: return
		except:
			source_utils.scraper_error('BITLORD')
			return

		for file in files.get('content'):
			try:
				name = source_utils.clean_name(file.get('name'))

				url = unquote_plus(file.get('magnet')).replace('&amp;', '&').replace(' ', '.')
				url = re.sub(r'(&tr=.+)&dn=', '&dn=', url) # some links on bitlord &tr= before &dn=
				url = url.split('&tr=')[0].split('&xl=')[0]
				url = source_utils.strip_non_ascii_and_unprintable(url)
				hash = re.compile(r'btih:(.*?)&', re.I).findall(url)[0]

				if not self.search_series:
					if not self.bypass_filter:
						if not source_utils.filter_season_pack(self.title, self.aliases, self.year, self.season_x, name):
							continue
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

				try:
					seeders = file.get('seeds')
					if self.min_seeders > seeders: continue
				except: seeders = 0

				quality, info = source_utils.get_release_quality(name_info, url)
				try:
					size = file.get('size')
					size = str(size) + ' GB' if len(str(size)) == 1 else str(size) + ' MB'
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except: dsize = 0
				info = ' | '.join(info)

				item = {'provider': 'bitlord', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info, 'quality': quality,
							'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize, 'package': package}
				if self.search_series: item.update({'last_season': last_season})
				self.sources.append(item)
			except:
				source_utils.scraper_error('BITLORD')


	def _get_token_and_cookies(self):
		headers = None
		try:
			# returned from client (result, response_code, response_headers, headers, cookie)
			post = client.request(self.base_link, output='extended', timeout='10')
			if not post: return headers
			token_id = re.findall(r'token\: (.*)\n', post[0])[0]
			token = ''.join(re.findall(token_id + r" ?\+?\= ?'(.*)'", post[0]))
			headers = post[3]
			headers.update({'Cookie': post[4].replace('SameSite=Lax, ', ''), 'X-Request-Token': token})
			return headers
		except:
			source_utils.scraper_error('BITLORD')
			return headers


	def resolve(self, url):
		return url