# -*- coding: utf-8 -*-
"""
	Fenomscrapers Module
"""

import os.path
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

addon = xbmcaddon.Addon
addonObject = addon('script.module.fenomscrapers')
addonInfo = addonObject.getAddonInfo
getLangString = addonObject.getLocalizedString
condVisibility = xbmc.getCondVisibility
execute = xbmc.executebuiltin
jsonrpc = xbmc.executeJSONRPC
monitor = xbmc.Monitor()
dialog = xbmcgui.Dialog()
openFile = xbmcvfs.File
makeFile = xbmcvfs.mkdir

SETTINGS_PATH = xbmc.translatePath(os.path.join(addonInfo('path'), 'resources', 'settings.xml'))

try:
	dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8')
except:
	dataPath = xbmc.translatePath(addonInfo('profile'))

cacheFile = os.path.join(dataPath, 'cache.db')


def setting(id):
	return xbmcaddon.Addon('script.module.fenomscrapers').getSetting(id)


def setSetting(id, value):
	return xbmcaddon.Addon('script.module.fenomscrapers').setSetting(id, value)


def sleep(time):  # Modified `sleep` command that honors a user exit request
	while time > 0 and not monitor.abortRequested():
		xbmc.sleep(min(100, time))
		time = time - 100


def getKodiVersion():
	return int(xbmc.getInfoLabel("System.BuildVersion")[:2])

def lang(language_id):
	text = getLangString(language_id)
	if getKodiVersion() < 19:
		text = text.encode('utf-8', 'replace')
	return text

def check_version_numbers(current, new):
	# Compares version numbers and return True if new version is newer
	current = current.split('.')
	new = new.split('.')
	step = 0
	for i in current:
		if int(new[step]) > int(i):
			return True
		if int(i) == int(new[step]):
			step += 1
			continue
	return False


def addonId():
	return addonInfo('id')


def addonName():
	return addonInfo('name')


def addonVersion():
	return addonInfo('version')


def addonIcon():
	return addonInfo('icon')


def openSettings(query=None, id=addonInfo('id')):
	try:
		idle()
		execute('Addon.OpenSettings(%s)' % id)
		if not query: return
		c, f = query.split('.')
		if getKodiVersion() >= 18:
			execute('SetFocus(%i)' % (int(c) - 100))
			execute('SetFocus(%i)' % (int(f) - 80))
		else:
			execute('SetFocus(%i)' % (int(c) + 100))
			execute('SetFocus(%i)' % (int(f) + 200))
	except:
		return


def getSettingDefault(id):
	import re
	try:
		settings = open(SETTINGS_PATH, 'r')
		value = ' '.join(settings.readlines())
		value.strip('\n')
		settings.close()
		value = re.findall(r'id=\"%s\".*?default=\"(.*?)\"' % (id), value)[0]
		return value
	except:
		return None


def idle():
	if getKodiVersion() >= 18 and condVisibility('Window.IsActive(busydialognocancel)'):
		return execute('Dialog.Close(busydialognocancel)')
	else:
		return execute('Dialog.Close(busydialog)')


def notification(title=None, message=None, icon=None, time=3000, sound=False):
	if title == 'default' or title is None:
		title = addonName()
	if isinstance(title, (int, long)):
		heading = lang(title)
	else:
		heading = str(title)
	if isinstance(message, (int, long)):
		body = lang(message)
	else:
		body = str(message)
	if icon is None or icon == '' or icon == 'default':
		icon = addonIcon()
	elif icon == 'INFO':
		icon = xbmcgui.NOTIFICATION_INFO
	elif icon == 'WARNING':
		icon = xbmcgui.NOTIFICATION_WARNING
	elif icon == 'ERROR':
		icon = xbmcgui.NOTIFICATION_ERROR
	dialog.notification(heading, body, icon, time, sound=sound)


def syncMyAccounts(silent=False):
	import myaccounts
	all_acct = myaccounts.getAllScraper()

	fp_acct = all_acct.get('filepursuit')
	if setting('filepursuit.api') != fp_acct.get('api_key'):
		setSetting('filepursuit.api', fp_acct.get('api_key'))

	fu_acct = all_acct.get('furk')
	if setting('furk.user_name') != fu_acct.get('username'):
		setSetting('furk.user_name', fu_acct.get('username'))
		setSetting('furk.user_pass', fu_acct.get('password'))
	if fu_acct.get('api_key', None):
		if setting('furk.api') != fu_acct.get('api_key'):
			setSetting('furk.api', fu_acct.get('api_key'))

	en_acct = all_acct.get('easyNews')
	if setting('easynews.user') != en_acct.get('username'):
		setSetting('easynews.user', en_acct.get('username'))
		setSetting('easynews.password', en_acct.get('password'))

	or_acct = all_acct.get('ororo')
	if setting('ororo.user') != or_acct.get('email'):
		setSetting('ororo.user', or_acct.get('email'))
		setSetting('ororo.pass', or_acct.get('password'))

	if not silent: notification(title='default', message=lang(32038), icon='default', sound=(setting('notification.sound') == 'true'))