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

from fenomscrapers.modules import cfscrape
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']
		self.domain = ['moviemagnet.co']
		self.base_link = 'http://moviemagnet.co'
		self.search_link = '/movies/search_movies?term=%s'
		self.min_seeders = 1
		self.pack_capable = False


	def movie(self, imdb, title, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			return


	def sources(self, url, hostDict):
		scraper = cfscrape.create_scraper()
		sources = []
		try:
			if not url: return sources

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['title']
			aliases = data['aliases']
			episode_title = data['title'] if 'tvshowtitle' in data else None
			year = data['year']

			query = re.sub('[^A-Za-z0-9\s\.-]+', '', title)

			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)
			try:
				r = scraper.get(url).content
				if not r:
					return sources
				if any(value in str(r) for value in ['No movies found', 'something went wrong', 'Connection timed out']):
					return sources
				r = json.loads(r)
				id = ''
				for i in r:
					if i['original_title'] == title and i['release_date'] == year:
						id = i['id']
						break
				if id == '':
					return sources
				link = '%s%s%s' % (self.base_link, '/movies/torrents?id=', id)

				result = scraper.get(link).content
				if 'magnet' not in result:
					return sources
				result = re.sub(r'\n', '', result)
				links = re.findall(r'<tr>.*?<a title="Download:\s*(.+?)"href="(magnet:.+?)">.*?title="File Size">\s*(.+?)\s*</td>.*?title="Seeds">([0-9]+|[0-9]+,[0-9]+)\s*<', result)

				for link in links:
					name = link[0]
					name = unquote_plus(name)
					name = source_utils.clean_name(title, name)
					if source_utils.remove_lang(name, episode_title):
						continue

					if not source_utils.check_title(title.replace('&', 'and'), aliases, name, year, year):
						continue

					url = link[1]
					try:
						url = unquote_plus(url).decode('utf8').replace('&amp;', '&').replace(' ', '.')
					except:
						url = unquote_plus(url).replace('&amp;', '&').replace(' ', '.')
					url = url.split('&tr')[0]
					hash = re.compile('btih:(.*?)&').findall(url)[0]

					quality, info = source_utils.get_release_quality(name, url)
					try:
						size = link[2]
						dsize, isize = source_utils._size(size)
						info.insert(0, isize)
					except:
						dsize = 0
						pass
					info = ' | '.join(info)

					try:
						seeders = int(link[3].replace(',', ''))
						if self.min_seeders > seeders:
							continue
					except:
						seeders = 0
						pass

					sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
												'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
				return sources
			except:
				source_utils.scraper_error('MOVIEMAGNET')
				return sources
		except:
			source_utils.scraper_error('MOVIEMAGNET')
			return sources


	def resolve(self, url):
		return url