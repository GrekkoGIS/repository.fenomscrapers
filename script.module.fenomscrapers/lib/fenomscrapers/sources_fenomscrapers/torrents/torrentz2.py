# -*- coding: utf-8 -*-
# created by Venom for Fenomscrapers (updated url 10-05-2020)

'''
    Fenomscrapers Project
'''

import re
try:
	from urlparse import parse_qs, urljoin
	from urllib import urlencode, quote_plus
except:
	from urllib.parse import parse_qs, urljoin
	from urllib.parse import urlencode, quote_plus

from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 15
		self.language = ['en']
		self.domains = ['torrentz2.is', 'torrentz.pl', 'torrentz2.uno']
		self.base_link = 'https://torrentz2.is'

# https://torrentz.pl/
# https://torrentsmirror.com/
# https://torrentz2in.site/
# https://torrentz2.uno
# https://utorrentz2.in/v1.php?q=joker+2019

		self.search_link = '/search?f=%s'
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
		sources = []
		if not url: return sources
		try:
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			aliases = data['aliases']
			episode_title = data['title'] if 'tvshowtitle' in data else None
			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
			year = data['year']

			query = '"^%s" %s' % (title, hdlr)
			query = re.sub('[^A-Za-z0-9\s\.\-\"\^]+', '', query)
			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)
			try:
				r = client.request(url)
				posts = client.parseDOM(r, 'div', attrs={'class': 'results'})[0]
				posts = client.parseDOM(posts, 'dl')

				for post in posts:
					links = re.findall('<dt><a href=/(.+)</a>', post, re.DOTALL)
					try:
						seeders = int(re.findall('<span>([0-9]+|[0-9]+,[0-9]+)</span>', post, re.DOTALL)[0].replace(',', ''))
						if self.min_seeders > seeders:
							continue
					except:
						seeders = 0
						pass

					for link in links:
						hash = link.split('>')[0]
						name = link.split('>')[1]
						name = source_utils.clean_name(title, name)
						if source_utils.remove_lang(name, episode_title):
							continue
						if not source_utils.check_title(title, aliases, name, hdlr, year):
							continue

						url = 'magnet:?xt=urn:btih:%s&dn=%s' % (hash, name)

						# filter for episode multi packs (ex. S01E01-E17 is also returned in query)
						if episode_title:
							if not source_utils.filter_single_episodes(hdlr, name):
								continue

						quality, info = source_utils.get_release_quality(name, url)
						try:
							size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GiB|MiB|GB|MB))', post)[0]
							dsize, isize = source_utils._size(size)
							info.insert(0, isize)
						except:
							dsize = 0
							pass
						info = ' | '.join(info)

						sources.append({'source': 'torrent', 'seeders': seeders, 'hash': hash, 'name': name, 'quality': quality,
													'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
				return sources
			except:
				source_utils.scraper_error('TORRENTZ2')
				return
		except:
			source_utils.scraper_error('TORRENTZ2')
			return sources


	def resolve(self, url):
		return url