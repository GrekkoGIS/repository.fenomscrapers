# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 08-24-2019 by JewBMX in Scrubs.
# modified by Venom for Fenomscrapers (updated url 9-20-2020)

import json
import re

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote_plus
except ImportError: from urllib.parse import urlencode, quote_plus

from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import client
from fenomscrapers.modules import directstream
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 31
		self.language = ['en']
		self.domains = ['5movies.to']
		self.base_link = 'https://5movies.to'
		self.search_link = '/search.php?q=%s'
		self.video_link = '/getlink.php?Action=get&lk=%s'


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


	def _search(self, title, year, aliases, headers):
		try:
			years = [str(year), str(int(year)+1), str(int(year)-1)]
			q = urljoin(self.base_link, self.search_link % quote_plus(cleantitle.getsearch(title)))
			# q = urljoin(self.base_link, self.search_link % quote_plus(cleantitle.getsearch(title) + ' ' + str(year)))
			r = client.request(q)
			r = client.parseDOM(r, 'div', attrs={'class':'ml-img'})
			if not r: return
			r = zip(client.parseDOM(r, 'a', ret='href'), client.parseDOM(r, 'img', ret='alt'))
			# url = [i for i in r if cleantitle.get(title) == cleantitle.get(i[1]) and (any(x in str(i[1]) for x in years))][0][0]
			url = [i for i in r if cleantitle.get(title) == cleantitle.get(i[1]) and (any(x in str(i[1]) for x in years))]
			if not url: return
			else: url = url[0][0]
			return url
		except:
			source_utils.scraper_error('5MOVIES')
			pass


	def sources(self, url, hostDict):
		sources = []
		try:
			if not url: return sources
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
			aliases = eval(data['aliases'])
			headers = {}
			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			year = data['year']
			if 'tvshowtitle' in data:
				episode = data['episode']
				season = data['season']
				url = self._search(title, year, aliases, headers)
				if not url: return sources
				url = url.rstrip('/') + '-s%se%s' % (season, episode)
				# log_utils.log('url = %s' % url, __name__, log_utils.LOGDEBUG)
			else:
				episode = None
				year = data['year']
				url = self._search(data['title'], data['year'], aliases, headers)
			url = url if 'http' in url else urljoin(self.base_link, url)
			result = client.request(url);
			result = client.parseDOM(result, 'li', attrs={'class':'link-button'})
			links = client.parseDOM(result, 'a', ret='href')
			i = 0
			for l in links:
				if i == 30:
					break
				try:
					l = l.split('=')[1]
					l = urljoin(self.base_link, self.video_link % l)
					result = client.request(l, post={}, headers={'Referer':url})
					u = result if 'http' in result else 'http:' + result
					if ' href' in u:
						u = u.replace('\r', '').replace('\n', '').replace('\t', '')
						u = 'http:' + re.compile(r" href='(.+?)'").findall(u)[0]
					if 'google' in u:
						valid, hoster = source_utils.is_host_valid(u, hostDict)
						urls, host, direct = source_utils.check_directstreams(u, hoster)
						for x in urls:
							sources.append({'source': host, 'quality': x['quality'], 'language': 'en', 'url': x['url'], 'direct': direct, 'debridonly': False})
					else:
						valid, hoster = source_utils.is_host_valid(u, hostDict)
						if not valid:
							continue
						try: u = u.decode('utf-8')
						except: u = source_utils.strip_non_ascii_and_unprintable(u)
						sources.append({'source': hoster, 'quality': '720p', 'language': 'en', 'url': u, 'direct': False, 'debridonly': False})
						i += 1
				except:
					source_utils.scraper_error('5MOVIES')
					pass
			return sources
		except:
			source_utils.scraper_error('5MOVIES')
			return sources


	def resolve(self, url):
		if 'google' in url:
			return directstream.googlepass(url)
		else:
			return url