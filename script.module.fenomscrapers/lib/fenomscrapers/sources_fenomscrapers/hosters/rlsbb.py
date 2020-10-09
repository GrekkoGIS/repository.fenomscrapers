# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 9-20-2020)

'''
    Fenomscrapers Project
'''

import re

try: from urlparse import parse_qs, urljoin, urlparse
except ImportError: from urllib.parse import parse_qs, urljoin, urlparse
try: from urllib import urlencode, quote_plus
except ImportError: from urllib.parse import urlencode, quote_plus

from fenomscrapers.modules import cfscrape
from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 26
		self.language = ['en']
		self.domains = ['rlsbb.ru','rlsbb.to','rlsbb.com','rlsbb.unblocked.cx']
		self.base_link = 'http://rlsbb.ru'
		self.search_base_link = 'http://search.rlsbb.ru'
		self.search_cookie = 'serach_mode=rlsbb'
		self.search_link = '/lib/search526049.php?phrase=%s&pindex=1&content=true'


	def movie(self, imdb, title, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			source_utils.scraper_error('RLSBB')
			return


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'aliases': aliases, 'year': year}
			url = urlencode(url)
			return url
		except:
			source_utils.scraper_error('RLSBB')
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
			source_utils.scraper_error('RLSBB')
			return


	def sources(self, url, hostDict):
		sources = []
		try:
			scraper = cfscrape.create_scraper(delay=5)
			if not url: return sources

			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')

			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']

			query = '%s %s' % (title, hdlr)
			query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)
			query = query.replace("&", "and")
			query = re.sub('\s', '-', query)
			# log_utils.log('query = %s' % query, log_utils.LOGDEBUG)

			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			url = "http://rlsbb.ru/" + query

			if 'tvshowtitle' not in data:
				url = url + "-1080p"
			r = scraper.get(url).content

			if r is None and 'tvshowtitle' in data:
				season = re.search('S(.*?)E', hdlr)
				season = season.group(1)
				query = title
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)
				query = query + "-S" + season
				query = query.replace("&", "and")
				query = query.replace("  ", " ")
				query = query.replace(" ", "-")
				url = "http://rlsbb.ru/" + query
				r = scraper.get(url).content

			posts = client.parseDOM(r, "div", attrs={"class": "content"})

			items = []
			for post in posts:
				try:
					u = client.parseDOM(post, 'a', ret='href')
					for i in u:
						try:
							try: name = i.encode('ascii', errors='ignore').decode('ascii', errors='ignore').replace('&nbsp;', ' ')
							except: name = i.replace('&nbsp;', ' ')
							tit = name.rsplit('/', 1)[1]
							t = tit.split(hdlr)[0].replace(data['year'], '').replace('(', '').replace(')', '').replace('&', 'and')
							if cleantitle.get(t) != cleantitle.get(title):
								continue
							if hdlr in name.upper():
								items.append(name)
						except:
							source_utils.scraper_error('RLSBB')
							pass
				except:
					source_utils.scraper_error('RLSBB')
					pass

			seen_urls = set()
			for item in items:
				info = []
				try:
					url = str(item)
					url = client.replaceHTMLCodes(url)
					try: url = url.encode('utf-8')
					except: pass

					if url in seen_urls:
						continue
					seen_urls.add(url)

					host = url.replace("\\", "")
					host2 = host.strip('"')
					if url in str(sources):
						continue
					host = re.findall('([\w]+[.][\w]+)$', urlparse(host2.strip().lower()).netloc)[0]
					if not host in hostDict:
						continue

					if any(x in host2 for x in ['.rar', '.zip', '.iso']):
						continue

					quality, info = source_utils.get_release_quality(host2)
# this site is an absolute nightmare to parse size.  Some comment section 16gb but size reflects all links in comment
					try:
						size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', name)[0]
						dsize, isize = source_utils._size(size)
						info.insert(0, isize)
					except:
						dsize = 0
						pass
					info = ' | '.join(info)

					host = client.replaceHTMLCodes(host)
					try: host = host.encode('utf-8')
					except: pass

					sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': host2, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
				except:
					source_utils.scraper_error('RLSBB')
					pass
			return sources
		except:
			source_utils.scraper_error('RLSBB')
			return sources


	def resolve(self, url):
		return url