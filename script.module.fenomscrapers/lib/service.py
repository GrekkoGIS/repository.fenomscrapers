# -*- coding: utf-8 -*-
"""
	Fenomscrapers Module
"""

import xbmc
from fenomscrapers.modules import control
LOGNOTICE = xbmc.LOGNOTICE if control.getKodiVersion() < 19 else xbmc.LOGINFO # (2 in 18, deprecated in 19 use LOGINFO(1))


class AddonCheckUpdate:
	def run(self):
		xbmc.log('[ script.module.fenomscrapers ]  Addon checking available updates', LOGNOTICE)
		try:
			import re
			import requests
			repo_xml = requests.get('https://raw.githubusercontent.com/mr-kodi/repository.fenomscrapers/master/zips/addons.xml')
			if not repo_xml.status_code == 200:
				xbmc.log('[ script.module.fenomscrapers ]  Could not connect to remote repo XML: status code = %s' % repo_xml.status_code, LOGNOTICE)
				return
			repo_version = re.findall(r'<addon id=\"script.module.fenomscrapers\".*version=\"(\d*.\d*.\d*.\d*)\"', repo_xml.text)[0]
			local_version = control.addonVersion()
			if control.check_version_numbers(local_version, repo_version):
				while control.condVisibility('Library.IsScanningVideo'):
					control.sleep(10000)
				xbmc.log('[ script.module.fenomscrapers ]  A newer version is available. Installed Version: v%s, Repo Version: v%s' % (local_version, repo_version), LOGNOTICE)
				control.notification(message=control.lang(32037) % repo_version, time=5000)
		except:
			import traceback
			traceback.print_exc()


class SyncMyAccounts:
	def run(self):
		xbmc.log('[ script.module.fenomscrapers ]  Sync "My Accounts" Service Starting...', LOGNOTICE)
		control.syncMyAccounts(silent=True)
		return xbmc.log('[ script.module.fenomscrapers ]  Finished Sync "My Accounts" Service', LOGNOTICE)


def main():
	while not control.monitor.abortRequested():
		xbmc.log('[ script.module.fenomscrapers ]  Service Started', LOGNOTICE)
		SyncMyAccounts().run()
		if control.setting('checkAddonUpdates') == 'true':
			AddonCheckUpdate().run()
			xbmc.log('[ script.module.fenomscrapers ]  Addon update check complete', LOGNOTICE)
		if control.isVersionUpdate():
			control.clean_settings()
			xbmc.log('[ script.module.fenomscrapers ]  Settings file cleaned complete', LOGNOTICE)
		xbmc.log('[ script.module.fenomscrapers ]  Service Stopped', LOGNOTICE)
		break

main()