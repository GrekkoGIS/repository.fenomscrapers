# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (updated 10-05-2020)

'''
    Fenomscrapers Project
'''

import re

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote_plus, unquote_plus
except ImportError: from urllib.parse import urlencode, quote_plus, unquote_plus

from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domains = ['nyaa.si']
		self.base_link = 'https://nyaa.si'
		self.search_link = '/?f=0&c=0_0&q=%s'
		self.min_seeders = 1
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
		try:
			if not url: return sources

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			aliases = data['aliases']

			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
			hdlr2 = 'S%d - %d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']

			query = '%s %s' % (title, hdlr)
			query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)

			query2 = '%s %s' % (title, hdlr2)
			query2 = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query2)

			urls = []
			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			urls.append(url)
			url2 = self.search_link % quote_plus(query2)
			url2 = urljoin(self.base_link, url2)
			urls.append(url2)
			# log_utils.log('urls = %s' % urls, log_utils.LOGDEBUG)

			for url in urls:
				try:
					r = client.request(url)
					if 'magnet' not in r:
						return sources
					r = re.sub(r'\n', '', r)
					r = re.sub(r'\t', '', r)
					tbody = client.parseDOM(r, 'tbody')
					rows = client.parseDOM(tbody, 'tr')

					for row in rows:
						links = zip(re.findall('href="(magnet:.+?)"', row, re.DOTALL), re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', row, re.DOTALL), [re.findall('<td class="text-center">([0-9]+)</td>', row, re.DOTALL)])

						for link in links:
							url = unquote_plus(link[0]).replace('&amp;', '&').replace(' ', '.').split('&tr')[0]
							url = source_utils.strip_non_ascii_and_unprintable(url)
							hash = re.compile('btih:(.*?)&').findall(url)[0]
							name = url.split('&dn=')[1]
							name = source_utils.clean_name(title, name)

							if hdlr not in name and hdlr2 not in name:
								continue

							if source_utils.remove_lang(name):
								continue

							if hdlr in name:
								t = name.split(hdlr)[0].replace(data['year'], '').replace('(', '').replace(')', '').replace('&', 'and').replace('.US.', '.').replace('.us.', '.')

							if hdlr2 in name:
								t = name.split(hdlr2)[0].replace(data['year'], '').replace('(', '').replace(')', '').replace('&', 'and').replace('.US.', '.').replace('.us.', '.')

							# if cleantitle.get(t) != cleantitle.get(title):
								# continue

							seeders = int(link[2][0])
							if self.min_seeders > seeders:
								continue

							quality, info = source_utils.get_release_quality(name, url)

							try:
								size = link[1]
								dsize, isize = source_utils._size(size)
								info.insert(0, isize)
							except:
								dsize = 0
								pass

							info = ' | '.join(info)

							sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
														'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
				except:
					source_utils.scraper_error('NYAA')
					return sources
			return sources
		except:
			source_utils.scraper_error('NYYAA')
			return sources


	def resolve(self, url):
		return url