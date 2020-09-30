# -*- coding: utf-8 -*-
"""
	Fenomscrapers Module
"""

import os.path
import xbmc
import xbmcaddon
import xbmcgui


def get():
	addonInfo = xbmcaddon.Addon().getAddonInfo
	addonPath = xbmc.translatePath(addonInfo('path'))
	helpFile = os.path.join(addonPath, 'changelog.txt')
	r = open(helpFile)
	text = r.read()
	r.close()
	xbmcgui.Dialog().textviewer('[COLOR red]Fenomscrapers[/COLOR] -  v%s - ChangeLog' % (xbmcaddon.Addon().getAddonInfo('version')), text)