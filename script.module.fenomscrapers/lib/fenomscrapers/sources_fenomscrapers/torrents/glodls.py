# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 1-09-2021)
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
			self.year = data['year']
			self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else self.year

			query = '%s %s' % (self.title, self.hdlr)
			query = re.sub(r'[^A-Za-z0-9\s\.-]+', '', query)
			if 'tvshowtitle' in data: url = self.tvsearch.format(quote_plus(query))
			else: url = self.moviesearch.format(quote_plus(query))
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)
			items = self.get_sources(url)
			if not items: return sources
		except:
			source_utils.scraper_error('GLODLS')
			return sources

		for item in items:
			try:
				name = item[0] ; name_info = item[1]
				url = unquote_plus(item[2]).replace('&amp;', '&').replace(' ', '.')
				url = url.split('&tr')[0]
				hash = re.compile(r'btih:(.*?)&').findall(url)[0].lower()
				quality, info = source_utils.get_release_quality(name_info, url)

				if item[3] != '0':
					info.insert(0, item[3])
				info = ' | '.join(info)

				sources.append({'provider': 'glodls', 'source': 'torrent', 'seeders': item[5], 'hash': hash, 'name': name, 'name_info': name_info,
											'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': item[4]})
			except:
				source_utils.scraper_error('GLODLS')
		return sources


	def get_sources(self, url):
		items = []
		try:
			headers = {'User-Agent': client.agent()}
			r = client.request(url, headers=headers, timeout='5')
			if not r: return items
			posts = client.parseDOM(r, 'tr', attrs={'class': 't-row'})
			posts = [i for i in posts if not 'racker:' in i]

			for post in posts:
				ref = client.parseDOM(post, 'a', ret='href')
				url = [i for i in ref if 'magnet:' in i][0]

				name = client.parseDOM(post, 'a', ret='title')[0]
				name = unquote_plus(name)
				name = source_utils.clean_name(name)
				if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year): continue
				name_info = source_utils.info_from_name(name, self.title, self.year, self.hdlr, self.episode_title)
				if source_utils.remove_lang(name_info): continue

				if not self.episode_title: #filter for eps returned in movie query (rare but movie and show exists for Run in 2020)
					ep_strings = [r'(?:\.|\-)s\d{2}e\d{2}(?:\.|\-|$)', r'(?:\.|\-)s\d{2}(?:\.|\-|$)', r'(?:\.|\-)season(?:\.|\-)\d{1,2}(?:\.|\-|$)']
					if any(re.search(item, name.lower()) for item in ep_strings): continue

				try:
					seeders = int(re.findall(r"<td.*?<font color='green'><b>([0-9]+|[0-9]+,[0-9]+)</b>", post)[0].replace(',', ''))
					if self.min_seeders > seeders: continue
				except:
					seeders = 0

				try:
					size = re.findall(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', post)[0]
					dsize, isize = source_utils._size(size)
				except:
					isize = '0' ; dsize = 0

				items.append((name, name_info, url, isize, dsize, seeders))
			return items
		except:
			source_utils.scraper_error('GLODLS')
			return items


	def resolve(self, url):
		return url