# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (updated 1-09-2021)
'''
	Fenomscrapers Project
'''

import re
try: #Py2
	from urlparse import parse_qs, urljoin
	from urllib import urlencode, quote_plus, unquote_plus
except ImportError: #Py3
	from urllib.parse import parse_qs, urljoin, urlencode, quote_plus, unquote_plus

from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 10
		self.language = ['en']
		self.domains = ['isohunt.nz']
		self.base_link = 'https://isohunt.nz'
		self.search_link = '/torrent/?ihq=%s&fiht=2&age=0&Torrent_sort=seeders&Torrent_page=0'
		self.min_seeders = 0
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
			urls = []
			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			urls.append(url)
			# urls.append(url.replace('page=0', 'page=40')) # server response time WAY to slow to parse 2 pages deep, site sucks.
			# log_utils.log('urls = %s' % urls, log_utils.LOGDEBUG)

			threads = []
			for url in urls:
				threads.append(workers.Thread(self.get_sources, url))
			[i.start() for i in threads]
			[i.join() for i in threads]
			return self.sources
		except:
			source_utils.scraper_error('ISOHUNT2')
			return self.sources


	def get_sources(self, url):
		try:
			r = client.request(url, timeout='10')
			if not r or '<tbody' not in r: return
			posts = client.parseDOM(r, 'tbody')[0]
			posts = client.parseDOM(posts, 'tr')

			for post in posts:
				post = re.sub(r'\n', '', post)
				post = re.sub(r'\t', '', post)
				links = re.compile(r'<a href="(/torrent_details/.+?)"><span>(.+?)</span>.*?<td class="size-row">(.+?)</td><td class="sn">([0-9]+)</td>').findall(post)
				for items in links:
					# item[1] does not contain full info like the &dn= portion of magnet
					link = urljoin(self.base_link, items[0])
					link = client.request(link, timeout='10')
					if not link: continue

					magnet = re.compile(r'(magnet.+?)"').findall(link)[0]
					url = unquote_plus(magnet).replace('&amp;', '&').replace(' ', '.').split('&tr')[0]
					hash = re.compile(r'btih:(.*?)&').findall(url)[0]
					name = unquote_plus(url.split('&dn=')[1])
					name = source_utils.clean_name(name)
					if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year): continue
					name_info = source_utils.info_from_name(name, self.title, self.year, self.hdlr, self.episode_title)
					if source_utils.remove_lang(name_info): continue

					if not self.episode_title: #filter for eps returned in movie query (rare but movie and show exists for Run in 2020)
						ep_strings = [r'(?:\.|\-)s\d{2}e\d{2}(?:\.|\-|$)', r'(?:\.|\-)s\d{2}(?:\.|\-|$)', r'(?:\.|\-)season(?:\.|\-)\d{1,2}(?:\.|\-|$)']
						if any(re.search(item, name.lower()) for item in ep_strings): continue

					try:
						seeders = int(items[3].replace(',', ''))
						if self.min_seeders > seeders: continue
					except:
						seeders = 0

					quality, info = source_utils.get_release_quality(name_info, url)
					try:
						size = re.findall(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', items[2])[0]
						dsize, isize = source_utils._size(size)
						info.insert(0, isize)
					except:
						dsize = 0
					info = ' | '.join(info)

					self.sources.append({'provider': 'isohunt2', 'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'name_info': name_info,
														'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
		except:
			source_utils.scraper_error('ISOHUNT2')


	def resolve(self, url):
		return url