# (created 10-29-2020)
'''
	Fenomscrapers Project
'''

import re
import requests
try:
	from urllib import unquote
except ImportError:
	from urllib.parse import unquote

from fenomscrapers.modules import cleantitle
from fenomscrapers.modules import control
from fenomscrapers.modules import source_utils

cloudflare_worker_url = control.setting('gdrive.cloudflare_url').strip()


def getResults(searchTerm):
	url = '{}/searchjson/{}'.format(cloudflare_worker_url, searchTerm)
	if not url.startswith("https://"): url = "https://" + url
	results = requests.get(url).json()
	return results


def get_simple(title):
	title = title.lower()
	if "/" in title:
		title = title.split("/")[-1].replace("'", "").replace("%20", " ")
	title = re.sub("[^a-zA-Z0-9]", " ", title)
	while "  " in title:
		title = title.replace("  ", " ")
	title = title.strip()
	return title


def filteredResults(results, simpleQuery):
	filtered = []
	for result in results:
		if get_simple(result["link"]).startswith(simpleQuery):
			filtered.append(result)
	return filtered


class source:
	def __init__(self):
		self.priority = 0
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
			search_id = url + " S" + str(season.zfill(2)) + "e" + str(episode.zfill(2))
			return search_id
		except:
			source_utils.scraper_error('GDRIVE')
			return


	def movie(self, imdb, title, aliases, year):
		try:
			search_id = title + " " + str(year)
			return search_id
		except:
			source_utils.scraper_error('GDRIVE')
			return


	def sources(self, url, hostDict):
		sources = []
		try:
			if cloudflare_worker_url == '': return sources
			simpleQuery = get_simple(url)
			results = getResults(url)
			results = filteredResults(results, simpleQuery)
			if not results:
				return sources

			for result in results:
				link = result["link"]
				name = unquote(link.rsplit("/")[-1])
				# log_utils.log('name = %s' % name, log_utils.LOGDEBUG)

				quality, info = source_utils.get_release_quality(link, link)
				try:
					size = result["size_gb"]
					size = str(size) + ' GB'
					dsize, isize = source_utils._size(size)
					info.insert(0, isize)
				except:
					source_utils.scraper_error('GDRIVE')
					dsize = 0
					pass
				info = ' | '.join(info)

				sources.append({'source': 'Google Drive', 'quality': quality, 'name': name, 'language': 'en',
											'info': info, 'url': link, 'direct': True, 'debridonly': False, 'size': dsize})
			return sources
		except:
			source_utils.scraper_error('GDRIVE')
			return sources


	def resolve(self, url):
		return url