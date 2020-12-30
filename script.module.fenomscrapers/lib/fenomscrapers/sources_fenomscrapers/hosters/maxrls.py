# -*- coding: UTF-8 -*-
# modified by Venom for Fenomscrapers (updated 12-23-2020)
'''
	Fenomscrapers Project
'''

import re

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote_plus, unquote
except ImportError: from urllib.parse import urlencode, quote_plus, unquote

from fenomscrapers.modules import cfscrape
from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils
from fenomscrapers.modules import workers


class source:
	def __init__(self):
		self.priority = 28
		self.language = ['en']
		self.domains = ['max-rls.com']
		self.base_link = 'http://max-rls.com'
		self.search_link = '/?s=%s&submit=Find'


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
			self.scraper = cfscrape.create_scraper(delay=5)
			self.hostDict = hostDict

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
			self.title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			self.title = self.title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			self.aliases = data['aliases']
			self.episode_title = data['title'] if 'tvshowtitle' in data else None
			self.year = data['year']
			self.hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else self.year

			query = '%s %s' % (self.title, self.hdlr)
			query = re.sub('[^A-Za-z0-9\s\.-]+', '', query)

			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url).replace('%3A+', '+')
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)
			try:
				result = self.scraper.get(url).content
				links = client.parseDOM(result, "h2", attrs={"class": "postTitle"})
				threads = []
				for link in links:
					threads.append(workers.Thread(self.get_sources, link))
				[i.start() for i in threads]
				[i.join() for i in threads]
				return self.sources
			except:
				source_utils.scraper_error('MAXRLS')
				return self.sources
		except:
			source_utils.scraper_error('MAXRLS')
			return self.sources


	def get_sources(self, link):
		items = []
		try:
			url = client.parseDOM(link, 'a', ret='href')[0]
			name = client.parseDOM(link, 'a', ret='title')[0].replace('Permalink to ', '')
			if not source_utils.check_title(self.title, self.aliases, name, self.hdlr, self.year): return
			name_info = source_utils.info_from_name(name, self.title, self.year, self.hdlr, self.episode_title)
			if source_utils.remove_lang(name_info): return
			items.append(url)
		except:
			source_utils.scraper_error('MAXRLS')

		for item in items:
			try:
				r = self.scraper.get(str(item)).content
				u = client.parseDOM(r, "div", attrs={"class": "postContent"})
				links = zip(re.findall(r'Download: (.*?)</strong>', u[0], re.DOTALL), re.findall(r'((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GiB|MiB|GB|MB|gb|mb))', u[0], re.DOTALL), re.findall(r'<p dir="ltr"><strong>(?![<]|[IMB]|[Links])(.*?)</strong><br />', u[0], re.DOTALL))
				for link in links:
					urls = link[0]
					results = re.compile('href="(.+?)"', re.DOTALL).findall(urls)
					for url in results:
						if url in str(self.sources): return
						name = re.sub(r'(<span.*?>)', '', link[2]).replace('</span>', '')
						name_info = source_utils.info_from_name(name, self.title, self.year, self.hdlr, self.episode_title)
						quality, info = source_utils.get_release_quality(name_info, url)

						try:
							dsize, isize = source_utils._size(link[1])
							info.insert(0, isize)
						except:
							dsize = 0
						info = ' | '.join(info)

						valid, host = source_utils.is_host_valid(url, self.hostDict)
						if not valid:
							continue
						self.sources.append({'provider': 'maxrls', 'source': host, 'name': name, 'name_info': name_info, 'quality': quality, 'language': 'en', 'url': url,
														'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			except:
				source_utils.scraper_error('MAXRLS')


	def resolve(self, url):
		return url