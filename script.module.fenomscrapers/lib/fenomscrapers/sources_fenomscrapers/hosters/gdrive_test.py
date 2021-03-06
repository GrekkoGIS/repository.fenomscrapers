# -*- coding: UTF-8 -*-
# (updated 12-23-2020)
'''
	Fenomscrapers Project
'''

import re
import requests
try: #Py2
	from urllib import unquote
except ImportError: #Py3
	from urllib.parse import unquote

from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import control
from fenomscrapers.modules import source_utils, log_utils

cloudflare_worker_url = control.setting('gdrive.cloudflare_url').strip()


def getResults(searchTerm):
	url = '{}/searchjson/{}'.format(cloudflare_worker_url, searchTerm)
	if not url.startswith("https://"): url = "https://" + url
	log_utils.log('url = %s' % url, __name__, log_utils.LOGDEBUG)
	results = requests.get(url).json()
	return results


def get_simple(title):
	log_utils.log('title = %s' % title, __name__, log_utils.LOGDEBUG)
	# title = title.lower()
	# if "/" in title:
		# title = title.split("/")[-1].replace("'", "").replace("%20", " ")
	# title = re.sub(r"[^a-zA-Z0-9]", " ", title)
	# while "  " in title:
		# title = title.replace("  ", " ")
	title = title.strip()
	log_utils.log('title = %s' % title, __name__, log_utils.LOGDEBUG)
	return title


def filteredResults(results, simpleQuery):
	filtered = []
	log_utils.log('simpleQuery = %s' % simpleQuery, __name__, log_utils.LOGDEBUG)
	log_utils.log('results = %s' % results, __name__, log_utils.LOGDEBUG)
	for result in results:
		log_utils.log('result = %s' % result, __name__, log_utils.LOGDEBUG)
		if get_simple(result["link"]).startswith(simpleQuery):
			filtered.append(result)
	return filtered


class source:
	def __init__(self):
		self.priority = 1
		self.language = ['en']


	def tvshow(self, imdb, tvdb, tvshowtitle, aliases, year):
		try:
			url = cleantitle.geturl(tvshowtitle)
			return url
		except:
			source_utils.scraper_error('GDRIVE')
			return


	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			# search_id = url + " S" + str(season.zfill(2)) + "E" + str(episode.zfill(2))
			search_id = url + " S" + season.zfill(2) + "E" + episode.zfill(2)
			return search_id
		except:
			source_utils.scraper_error('GDRIVE')
			return


	def movie(self, imdb, title, aliases, year):
		try:
			log_utils.log('title = %s' % title, __name__, log_utils.LOGDEBUG)
			# title = re.sub(r'[^A-Za-z0-9\s\.-]+', '', title)
			title = re.sub(r'[^A-Za-z0-9\s\.-]+', '', title).replace(' ', '%20')
			log_utils.log('title = %s' % title, __name__, log_utils.LOGDEBUG)
			# search_id = title + " " + str(year)
			search_id = title + "%20" + str(year)
			log_utils.log('search_id = %s' % search_id, __name__, log_utils.LOGDEBUG)
			return search_id
		except:
			source_utils.scraper_error('GDRIVE')
			return


	def sources(self, url, hostDict):
		sources = []
		if not url: return sources
		try:
			if cloudflare_worker_url == '': return sources
			simpleQuery = get_simple(url)
			log_utils.log('url = %s' % url, __name__, log_utils.LOGDEBUG)
			results = getResults(url)
			log_utils.log('results = %s' % results, __name__, log_utils.LOGDEBUG)

			results = filteredResults(results, simpleQuery)
			if not results: return sources
		except:
			source_utils.scraper_error('GDRIVE')
			return sources

		for result in results:
			try:
				link = result["link"]
				name = unquote(link.rsplit("/")[-1])
				# name_info = source_utils.info_from_name(name, title, year, hdlr, episode_title) # needs a decent rewrite to get this

				quality, info = source_utils.get_release_quality(name, link)
				try:
					size = str(result["size_gb"]) + ' GB'
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except:
					source_utils.scraper_error('GDRIVE')
					dsize = 0
				info = ' | '.join(info)

				sources.append({'provider': 'gdrive', 'source': 'Google Drive', 'quality': quality, 'name': name, 'language': 'en',
											'info': info, 'url': link, 'direct': True, 'debridonly': False, 'size': dsize})
			except:
				source_utils.scraper_error('GDRIVE')
		return sources


	def resolve(self, url):
		return url