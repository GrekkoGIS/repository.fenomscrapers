# -*- coding: utf-8 -*-
# modified by Venom for Fenomscrapers (updated 9-20-2020)

'''
	Fenomscrapers Project
'''

import re

try: from urlparse import parse_qs, urljoin
except ImportError: from urllib.parse import parse_qs, urljoin
try: from urllib import urlencode, quote_plus
except ImportError: from urllib.parse import urlencode, quote_plus

from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import client
from fenomscrapers.modules import source_utils


class source:
	def __init__(self):
		self.priority = 22
		self.language = ['en']
		self.domains = ['new.myvideolinks.net']
		self.base_link = 'http://forum.myvideolinks.net'
		self.search_link = '/search.php?keywords=%s'


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
			query = '%s %s' % (title, hdlr)
			query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', '', query)
			url = urljoin(self.base_link, self.search_link)
			url = url % quote_plus(query)
			# log_utils.log('url = %s' % url, __name__, log_utils.LOGDEBUG)

			r = client.request(url, timeout='5')
			if not r or 'Error 404' in r: return sources

			r = client.parseDOM(r, 'div', attrs={'class': 'page-body'})
			r1 = client.parseDOM(r, 'div', attrs={'class': 'postbody'})
			posts = zip(client.parseDOM(r1, 'a', ret='href'), client.parseDOM(r1, 'a'))
		except:
			source_utils.scraper_error('MYVIDEOLINK')
			return sources

		items = []
		for post in posts:
			try:
				name = source_utils.strip_non_ascii_and_unprintable(post[1])
				if '<' in name: name = re.sub('<.*?>', '', name)
				name = client.replaceHTMLCodes(name).replace(' ', '.')
				if 'tvshowtitle' in data:
					if not source_utils.check_title(title, aliases, name, hdlr, data['year']):
						if not source_utils.check_title(title, aliases, name, 'S%02d' % int(data['season']), data['year']): continue
				else:
					if not source_utils.check_title(title, aliases, name, hdlr, data['year']): continue
				link = urljoin(self.base_link, post[0].lstrip('.').replace('&amp;', '&'))
				base_u = client.request(link, timeout='5')
				list = client.parseDOM(base_u, 'div', attrs={'class': 'content'})

				if 'tvshowtitle' in data:
					string = list[0].replace('\r', '').replace('\n', '').replace('\t', '')
					regex = hdlr + '.*?</ul>'
					list = zip(re.findall(hdlr, string), re.findall(regex, string, re.DOTALL))
					for links in list:
						u = re.findall('\'(http.+?)\'', links[1]) + re.findall('\"(http.+?)\"', links[1])
						t = links[0] ; s = 0
						items += [(t, i, s) for i in u]
				else:
					u = client.parseDOM(list, 'ul')[0]
					u = re.findall('\'(http.+?)\'', u) + re.findall('\"(http.+?)\"', u)
					try: t = post[1].encode('utf-8')
					except: t = post[1]
					s = re.findall('((?:\d+\.\d+|\d+\,\d+|\d+)\s*(?:GB|GiB|MB|MiB))', list[0])[0]
					items += [(t, i, s) for i in u]
			except:
				source_utils.scraper_error('MYVIDEOLINK')
				pass

		for item in items:
			try:
				url = client.replaceHTMLCodes(item[1])
				try: url = url.encode('utf-8')
				except: pass
				if url.endswith(('.rar', '.zip', '.iso', '.part', '.png', '.jpg', '.bmp', '.gif')): continue
				if url in str(sources): continue
				valid, host = source_utils.is_host_valid(url, hostDict)
				if not valid: continue
				host = client.replaceHTMLCodes(host)
				try: host = host.encode('utf-8')
				except: pass
				quality, info = source_utils.get_release_quality(name, url)
				try:
					size = item[2]
					dsize, isize = source_utils._size(size)
					if isize:
						info.insert(0, isize)
				except:
					dsize = 0
					pass
				fileType = source_utils.getFileType(name)
				info.append(fileType)
				info = ' | '.join(info) if fileType else info[0]
				sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url,
											'info': info, 'direct': False, 'debridonly': True, 'size': dsize})
			except:
				source_utils.scraper_error('MYVIDEOLINK')
				pass
		return sources


	def resolve(self, url):
		return url