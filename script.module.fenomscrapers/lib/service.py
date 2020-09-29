# -*- coding: utf-8 -*-
"""
	Fenomscrapers Module

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from fenomscrapers.modules import control
import xbmc


class AddonCheckUpdate:
	def run(self):
		xbmc.log('[ script.module.fenomscrapers ]  Addon checking available updates', xbmc.LOGNOTICE)
		try:
			import re
			import requests
			repo_xml = requests.get('https://raw.githubusercontent.com/mr-kodi/repository.fenomscrapers/master/zips/addons.xml')
			if not repo_xml.status_code == 200:
				xbmc.log('[ script.module.fenomscrapers ]  Could not connect to remote repo XML: status code = %s' % repo_xml.status_code, xbmc.LOGNOTICE)
				return
			repo_version = re.findall(r'<addon id=\"script.module.fenomscrapers\".*version=\"(\d*.\d*.\d*.\d*)\"', repo_xml.text)[0]
			local_version = control.addonVersion()
			if control.check_version_numbers(local_version, repo_version):
				while control.condVisibility('Library.IsScanningVideo'):
					control.sleep(10000)
				xbmc.log('[ script.module.fenomscrapers ]  A newer version is available. Installed Version: v%s, Repo Version: v%s' % (local_version, repo_version), xbmc.LOGNOTICE)
				control.notification(title = 'default', message = 'A new verison of Fenomscrapers is available from the repository. Please consider updating to v%s' % repo_version, icon='default', time=5000, sound=False)
		except:
			import traceback
			traceback.print_exc()
			pass


class SyncMyAccounts:
	def run(self):
		xbmc.log('[ script.module.fenomscrapers ]  Sync "My Accounts" Service Starting...', 2)
		control.syncMyAccounts(silent=True)
		return xbmc.log('[ script.module.fenomscrapers ]  Finished Sync "My Accounts" Service', 2)


SyncMyAccounts().run()

if control.setting('checkAddonUpdates') == 'true':
	AddonCheckUpdate().run()
	xbmc.log('[ script.module.fenomscrapers ]  Addon update check complete', xbmc.LOGNOTICE)

xbmc.log('[ script.module.fenomscrapers ]  service stopped', xbmc.LOGNOTICE)
