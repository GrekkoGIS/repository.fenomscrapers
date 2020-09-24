# -*- coding: UTF-8 -*-
# (updated 9-20-2020)

import re
import requests
import json

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote_plus
except ImportError: from urllib.parse import urlencode, quote_plus

from fenomscrapers.modules import control
from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 35
		self.language = ['en']
		self.base_link = 'https://filepursuit.p.rapidapi.com'
		# 'https://rapidapi.com/azharxes/api/filepursuit' to obtain key
		self.search_link = '/?type=video&q=%s'


	def movie(self, imdb, title, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			source_utils.scraper_error('FILEPURSUIT')
			return


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			source_utils.scraper_error('FILEPURSUIT')
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
			source_utils.scraper_error('FILEPURSUIT')
			return


	def sources(self, url, hostDict):
		sources = []
		try:
			api_key = control.setting('filepursuit.api')
			if api_key == '': return sources
			headers = {"x-rapidapi-host": "filepursuit.p.rapidapi.com",
				"x-rapidapi-key": api_key}

			if not url: return sources
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			self.title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			self.title = self.title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
			self.year = data['year']

			query = '%s %s' % (self.title, self.hdlr)
			query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)

			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)

			r = client.request(url, headers=headers)
			if not r:
				return sources
			r = json.loads(r)

			if 'not_found' in r['status']:
				return sources

			results = r['files_found']
			for item in results:
				url = item['file_link']
				link_header = client.request(url, output='headers', timeout='5')
				if not any(value in str(link_header) for value in ['stream', 'video/mkv']):
					continue

				try: size = int(item['file_size_bytes'])
				except: size = 0

				try: name = item['file_name']
				except: name = item['file_link'].split('/')[-1]

				if source_utils.remove_lang(name):
					continue

				if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year):
					continue

				quality, info = source_utils.get_release_quality(name, url)
				try:
					dsize, isize = source_utils.convert_size(size, to='GB')
					if isize:
						info.insert(0, isize)
				except:
					source_utils.scraper_error('FILEPURSUIT')
					dsize = 0
					pass
				info = ' | '.join(info)

				sources.append({'source': 'direct', 'quality': quality, 'name': name, 'language': "en",
							'url': url, 'info': info, 'direct': True, 'debridonly': False, 'size': dsize})
			return sources
		except:
			source_utils.scraper_error('FILEPURSUIT')
			return sources


	def resolve(self, url):
		return url