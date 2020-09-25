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
from fenomscrapers.modules import log_utils


def check_for_addon_update():
	log_utils.log('Fenomscrapers checking available updates', log_utils.LOGNOTICE)
	try:
		import re
		import requests
		repo_xml = requests.get('https://raw.githubusercontent.com/mr-kodi/repository.fenomscrapers/master/zips/addons.xml')
		if not repo_xml.status_code == 200:
			log_utils.log('Could not connect to Fenomscrapers repo XML, status: %s' % repo_xml.status_code, log_utils.LOGNOTICE)
			return
		repo_version = re.findall(r'<addon id=\"script.module.fenomscrapers\".*version=\"(\d*.\d*.\d*.\d*)\"', repo_xml.text)[0]
		local_version = control.addonVersion()
		if control.check_version_numbers(local_version, repo_version):
			while control.condVisibility('Library.IsScanningVideo'):
				control.sleep(10000)
			log_utils.log('A newer version of Fenomscrapers is available. Installed Version: v%s, Repo Version: v%s' % (local_version, repo_version), log_utils.LOGNOTICE)
			control.notification(title = 'default', message = 'A new verison of Fenomscrapers is available from the repository. Please consider updating to v%s' % repo_version, icon = 'default', time=5000, sound=False)
	except:
		log_utils.error()
		pass

def sync_my_accounts():
	return control.syncMyAccounts(silent=True)

sync_my_accounts()

if control.setting('checkAddonUpdates') == 'true':
	check_for_addon_update()