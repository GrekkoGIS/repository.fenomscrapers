# -*- coding: utf-8 -*-
"""
	Fenomscrapers Module
"""

import os.path
import xbmc
import xbmcaddon
import xbmcgui


def get(file):
	addonInfo = xbmcaddon.Addon().getAddonInfo
	addonPath = xbmc.translatePath(addonInfo('path'))
	helpFile = os.path.join(addonPath, 'lib', 'fenomscrapers', 'help', file + '.txt')
	r = open(helpFile)
	text = r.read()
	r.close()
	xbmcgui.Dialog().textviewer('[COLOR red]Fenomscrapers[/COLOR] -  v%s - %s' % (xbmcaddon.Addon().getAddonInfo('version'), file), text)