# -*- coding: utf-8 -*-
# --[getSum v1.4]--|--[From JewBMX]--
# Lazy Module to make life a little easier.

import re
try:
	from HTMLParser import HTMLParser
except ImportError:
	from html.parser import HTMLParser

from fenomscrapers.modules.utils import byteify
from fenomscrapers.modules import log_utils

headers = {
	'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3555.0 Safari/537.36"}


class GetSum(object):
	_frame_regex = r'(?:iframe|source).+?(?:src)=(?:\"|\')(.+?)(?:\"|\')'
	_datavideo_regex = r'(?:data-video|data-src|data-href)=(?:\"|\')(.+?)(?:\"|\')'
	_filesource_regex = r'(?:file|source)(?:\:)\s*(?:\"|\')(.+?)(?:\"|\')'
	_magnet_regex = r'''(magnet:\?[^"']+)'''
	_timeout = 10

	def findSum(self, text, type=None):
		try:
			self.links = set()
			if not text:
				return
			if re.search(self._frame_regex, text, re.IGNORECASE) or type == 'iframe':
				links = re.compile(self._frame_regex).findall(text)
				if links:
					for link in links:
						link = "https:" + link if not link.startswith('http') else link
						if link in self.links:
							continue
						self.links.add(link)
			if re.search(self._datavideo_regex, text, re.IGNORECASE) or type == 'datavideo':
				links = re.compile(self._datavideo_regex).findall(text)
				if links:
					for link in links:
						link = "https:" + link if not link.startswith('http') else link
						if link in self.links:
							continue
						self.links.add(link)
			if re.search(self._filesource_regex, text, re.IGNORECASE) or type == 'filesource':
				links = re.compile(self._filesource_regex).findall(text)
				if links:
					for link in links:
						link = "https:" + link if not link.startswith('http') else link
						if link in self.links:
							continue
						self.links.add(link)
			if re.search(self._magnet_regex, text, re.IGNORECASE) or type == 'magnet':
				links = re.compile(self._magnet_regex).findall(text)
				if links:
					for link in links:
						link = str(byteify(replaceHTMLCodes(link)).split('&tr')[0])
						link = "magnet:" + link if not link.startswith('magnet') else link
						if link in self.links:
							continue
						self.links.add(link)
			return self.links
		except Exception:
			return self.links


########################################################
########################################################


# Normal = getSum.get(url)
# CFscrape = getSum.get(url, Type='cfscrape')
def get(url, Type=None):
	if not url:
		return
	if Type == 'client' or Type is None:
		from fenomscrapers.modules import client
		content = client.request(url, headers=headers)
	if Type == 'cfscrape':
		from fenomscrapers.modules import cfscrape
		cfscraper = cfscrape.create_scraper()
		content = cfscraper.get(url, headers=headers).content
	if Type == 'redirect':
		import requests
		content = requests.get(url, headers=headers).url
	if content is None:
		log_utils.log('getSum - Get ERROR:  No Content Got for:  ' + str(url))
		raise Exception()
	return content


# results = getSum.findSum(text)
# for result in results:
def findSum(text, type=None, timeout=10):
	if not text:
		return
	getSum = GetSum()
	results = getSum.findSum(text, type=type)
	if results:
		return results
	else:
		return []



def replaceHTMLCodes(text):
	text = re.sub("(&#[0-9]+)([^;^0-9]+)", "\\1;\\2", text)
	text = HTMLParser().unescape(text)
	text = text.replace("&quot;", "\"")
	text = text.replace("&amp;", "&")
	text = text.replace("%2B", "+")
	text = text.replace("\/", "/")
	text = text.replace("\\", "")
	text = text.strip()
	return text

