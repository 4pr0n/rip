#!/usr/bin/python

import cgi, cgitb; cgitb.enable()

from json import loads, dumps
from time import strftime, localtime
from os   import path, listdir

def main():
	keys = get_keys()
	if 'time' in keys:
		time = keys['time']
		if time == 'hourly': get_hourly_graphs('hour')
		if time == 'daily':  get_daily_graphs('day')
		if time == 'weekly': get_daily_weekly('week')
	else:
		print dumps({'error':'unspecified error'})

def get_graphs(time, num=24):
	cur = int(strftime('%s', localtime()))
	t = int(cur / 3600) * 3600 # last hour
	result = []
	while num > 0:
		fname = '%d-hour.log' % t
		if not path.exists(fname): break
		r = open(fname, 'r').read().strip()
		result.append({
			t : loads(r)
		})
		num -= 1
		t -= 3600
	print dumps(result)

""" Retrieves key/value pairs from query, puts in dict """
def get_keys(): 
	storage = cgi.FieldStorage()
	keys = {}
	for key in storage.keys():
		keys[key] = storage[key].value
	return keys

""" Entry point. Print leading/trailing characters, executes main() """
if __name__ == '__main__':
	print "Content-Type: application/json"
	print ""
	main()
	print "\n"

