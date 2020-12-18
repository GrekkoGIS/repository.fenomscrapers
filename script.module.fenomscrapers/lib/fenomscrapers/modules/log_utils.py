# -*- coding: utf-8 -*-
"""
	Fenomscrapers Module
"""

from datetime import datetime
import inspect
import xbmc
from xbmc import LOGDEBUG, LOGERROR, LOGFATAL, LOGINFO, LOGNONE, LOGNOTICE, LOGSEVERE, LOGWARNING

from fenomscrapers.modules import control

DEBUGPREFIX = '[COLOR red][ FENOMSCRAPERS DEBUG ][/COLOR]'
LOGPATH = xbmc.translatePath('special://logpath/')


def log(msg, caller=None, level=LOGNOTICE):
	debug_enabled = control.setting('debug.enabled') == 'true'
	debug_log = control.setting('debug.location')

	if not debug_enabled: return
	try:
		if caller is not None and level == LOGDEBUG:
			func = inspect.currentframe().f_back.f_code
			line_number = inspect.currentframe().f_back.f_lineno
			caller = "%s.%s()" % (caller, func.co_name)
			msg = 'From func name: %s Line # :%s\n                       msg : %s' % (caller, line_number, msg)

		if caller is not None and level == LOGERROR:
			msg = 'From func name: %s.%s() Line # :%s\n                       msg : %s'%(caller[0], caller[1], caller[2], msg)
		try:
			if isinstance(msg, unicode):
				msg = '%s (ENCODED)' % (msg.encode('utf-8'))
		except: pass

		if debug_log == '1':
			log_file = control.joinPath(LOGPATH, 'fenomscrapers.log')
			if not control.existsPath(log_file):
				f = open(log_file, 'w')
				f.close()
			with open(log_file, 'a') as f:
				line = '[%s %s] %s: %s' % (datetime.now().date(), str(datetime.now().time())[:8], DEBUGPREFIX, msg)
				f.write(line.rstrip('\r\n') + '\n')
		else:
			xbmc.log('%s: %s' % (DEBUGPREFIX, msg), level)
	except Exception as e:
		xbmc.log('Logging Failure: %s' % (e), LOGERROR)


def error(message=None, exception=True):
	try:
		import sys
		if exception:
			type, value, traceback = sys.exc_info()
			addon = 'script.module.fenomscrapers'
			filename = (traceback.tb_frame.f_code.co_filename)
			filename = filename.split(addon)[1]
			name = traceback.tb_frame.f_code.co_name
			linenumber = traceback.tb_lineno
			errortype = type.__name__
			errormessage = value.message or value # sometimes value.message is null while value is not
			if str(errormessage) == '': return
			if message: message += ' -> '
			else: message = ''
			message += str(errortype) + ' -> ' + str(errormessage)
			caller = [filename, name, linenumber]
		else:
			caller = None
		log(msg=message, caller=caller, level=LOGERROR)
		del(type, value, traceback) # So we don't leave our local labels/objects dangling
	except Exception as e:
		xbmc.log('Logging Failure: %s' % (e), LOGERROR)