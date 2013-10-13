#!/usr/bin/python

from json import dumps
from os import path, environ
import traceback

DAYS_TO_BAN = 3

def main():
	ip = '127.0.0.1'
	if 'REMOTE_ADDR' in environ: ip = environ['REMOTE_ADDR']
	print_ban_info(ip)

def print_ban_info(ip):
	if not path.exists('../.htaccess'):
		print dumps({
			'error' : 'no ip-ban file found',
			'banned' : False,
		})
		return
	f = open('../.htaccess', 'r')
	lines = f.read().split('\n')
	f.close()
	reasonline = None
	found_ip = False
	for i in xrange(0, len(lines) - 1):
		if '^%s$' % ip in lines[i]:
			found_ip = True
			while i > 1 and not lines[i-1].startswith('#'):
				i -= 1
			i -= 1
			if i >= 0:
				reasonline = lines[i]
			break
	if not found_ip:
		print dumps({
			'error' : 'you do not appear to be banned (IP: %s)' % ip,
			'banned' : False,
		})
		return

	if reasonline == None:
		print dumps({
			'error' : 'unable to find reason for ban. IP: %s' % ip,
			'banned' : True,
		})
		return
	response = {}
	if '(reason: ' in reasonline:
		reason = reasonline[reasonline.find('(reason: ')+9:]
		reason = reason[:-1]
		response['reason'] = reason
	else:
		response['reason'] = reasonline
	bantime = 'N/A'
	if ' at ' in reasonline:
		bantime = reasonline[reasonline.find(' at ')+4:]
		bantime = int(bantime[:bantime.find(' ')])
		bantime += (3600 * 7)
		response['time'] = bantime
		response['lifted'] = bantime + (3600 * 24 * DAYS_TO_BAN)
	print dumps(response)

""" Entry point. Print leading/trailing characters, executes main() """
if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	try:
		main()
	except Exception, e:
		print dumps({ 
			'error' : str(e),
			'trace' : traceback.format_exc().replace('module>', 'span>').replace('\n', '<br>').replace(' ', '&nbsp;') })
	print "\n"

