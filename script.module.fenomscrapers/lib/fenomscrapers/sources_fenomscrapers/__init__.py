# -*- coding: UTF-8 -*-

import os.path

from . import hosters
from . import torrents

scraper_source = os.path.dirname(__file__)
__all__ = [x[1] for x in os.walk(os.path.dirname(__file__))][0]

##--hosters--##
hoster_source = hosters.sourcePath
hoster_providers = hosters.__all__

##--torrent--##
torrent_source = torrents.sourcePath
torrent_providers = torrents.__all__

##--All Providers--##
total_providers = {'hosters': hoster_providers, 'torrents': torrent_providers}
all_providers = []
try:
	for key, value in total_providers.iteritems():
		all_providers += value
except:
	for key, value in total_providers.items():
		all_providers += value