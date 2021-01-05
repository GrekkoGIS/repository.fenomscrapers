# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 1-04-2021)
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
		# self.base_link = 'http://rlsbb.ru'
		self.base_link = 'http://proxybb.com'
		# self.search_base_link = 'http://search.rlsbb.ru'
		self.search_base_link = 'http://search.proxybb.com'
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
		if not url: return sources
		try:
			scraper = cfscrape.create_scraper(delay=5)
			data = parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			title = title.replace('&', 'and').replace('Special Victims Unit', 'SVU')
			aliases = data['aliases']
			episode_title = data['title'] if 'tvshowtitle' in data else None
			year = data['year']
			hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else year

			query = '%s %s' % (title, hdlr)
			query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)
			query = query.replace("&", "and")
			query = re.sub('\s', '-', query)
			url = self.search_link % quote_plus(query)
			url = urljoin(self.base_link, url)
			# url = "http://rlsbb.ru/" + query
			url = "http://proxybb.com/" + query

			if 'tvshowtitle' not in data: url = url + "-1080p"
			elif 'tvshowtitle' in data:
				season = re.search('S(.*?)E', hdlr).group(1)
				query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', title)
				query = query + "-S" + season
				query = query.replace("&", "and").replace("  ", " ").replace(" ", "-")
				url = "http://rlsbb.ru/" + query

			# log_utils.log('url = %s' % url, log_utils.LOGDEBUG)
			r = scraper.get(url).content
			posts = client.parseDOM(r, "div", attrs={"class": "content"})
			if not posts: return sources
		except:
			source_utils.scraper_error('RLSBB')
			return sources

		items = []
		count = 0
		for post in posts:
			if count == 30: break
			# log_utils.log('post = %s' % post, log_utils.LOGDEBUG)
			# size and release_title in post but inconsistent to parse, needs wild regex
			try:
				links = client.parseDOM(post, 'a', ret='href') #grabs all links in each "content" group
				# log_utils.log('links = %s' % links, log_utils.LOGDEBUG)
				for i in links:
					link = i
					if link.endswith(('.rar', '.zip', '.iso', '.part', '.png', '.jpg', '.bmp', '.gif')): continue

					name = link.rsplit("/", 1)[-1]
					name = source_utils.strip_non_ascii_and_unprintable(name)
					# log_utils.log('name = %s' % name, log_utils.LOGDEBUG)

					if not source_utils.check_title(title, aliases, name, hdlr, year): continue
					name_info = source_utils.info_from_name(name, title, year, hdlr, episode_title)
					# if source_utils.remove_lang(name_info): continue
					items.append((link, name, name_info))
			except:
				source_utils.scraper_error('RLSBB')


			for item in items:
				if count == 30: break
				try:
					url = str(item[0])
					url = client.replaceHTMLCodes(url)
					try: url = url.encode('utf-8')
					except: pass
					if url in str(sources): continue

					name = str(item[1])
					name_info = str(item[2])

					valid, host = source_utils.is_host_valid(url, hostDict)
					if not valid: continue

					quality, info = source_utils.get_release_quality(url)
# this site is an absolute nightmare to parse size.  Some comment section 16gb but size reflects all links in comment
					try:
						size = re.findall('((?:\d+\,\d+\.\d+|\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|Gb|MB|MiB|Mb))', name)[0]
						dsize, isize = source_utils._size(size)
						info.insert(0, isize)
					except:
						dsize = 0
					info = ' | '.join(info)

					sources.append({'provider': 'rlsbb','source': host, 'name': name, 'name_info': name_info, 'quality': quality, 'language': 'en', 'url': url,
												'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
					count += 1
				except:
					source_utils.scraper_error('RLSBB')
		return sources


	def resolve(self, url):
		return url