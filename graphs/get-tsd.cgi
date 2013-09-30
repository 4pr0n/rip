#!/usr/bin/python

import cgi, cgitb; cgitb.enable()

from json import loads, dumps
from time import localtime, gmtime
import time as tim # you used time as a variable! :(
from os   import path, listdir

#METRICS = ['hits', 'rips', 'zips', 'album_views', 'images', 'thumbs', 'videos', 'checks', 'cgi', 'others', 'megabytes']
METRICS = ['requests', 'rips', 'zips', 'album_views', 'images', 'megabytes']

def main():
	keys = get_keys()
	span = 0        # Number of days to get metrics for
	time = 'hourly' # Type of metrics to retrieve
	if 'span' in keys and keys['span'].isdigit(): span = int(keys['span'])
	if 'time' in keys: time = keys['time']
	#try:
	get_graphs(time, span)
	#except Exception, e:
	#print dumps({'error' : e})

def get_time_span_period(time, span):
	if time == 'short': 
		time = '5min'
		period = 300 # 5 minutes
		defaultspan = 6 * 12 # X hours of 5min metrics
	elif time == 'mid':  
		time = 'hour'
		period = 3600 # 1 hour
		defaultspan = 3 * 24 # X days of 1hour metrics
	elif time == 'long': 
		time = 'day'
		period = 86400 # 1 day
		defaultspan = 30 # X days of 1day metrics
	else:
		raise Exception('Unknown time period: %s' % time)
	if span == 0:
		span = defaultspan
	return (time, span, period)

def get_graphs(time, span):
	(time, timespan, period) = get_time_span_period(time, span)
	span = timespan
	cur = int(tim.time())
	#cur = 1380335700 # For testing, TODO remove!

	t = int(cur / period) * period # Get starting point for metrics
	point_start = (t - ( (timespan - 1) * period)) * 1000
	datas = []
	missed_count = 0
	while timespan > 0:
		fname = path.join('logs', '%d-%s.log' % (t, time)) # Path to log file
		data = {}
		if path.exists(fname): 
			r = open(fname, 'r').read().strip()
			data = loads(r)
			missed_count = 0
		else:
			data = {}
			missed_count += 1
		if not 'bytes' in data: data['bytes'] = 0
		if not 'hits'  in data: data['hits']  = 0
		data['megabytes'] = data['bytes'] / (1024 * 1024)
		data['requests'] = data['hits']
		data.pop('bytes')
		data.pop('hits')
		datas.append(data)
		timespan -= 1
		t -= period
	if time == '5min':
		datas.pop(0) # Remove last datapoint for 5min intervals (not stable)
	datas.reverse()
	result = {}
	result['series'] = format_data(datas)
	if   period == 300:   timerange = '%dH' % (span / 12)
	elif period == 3600:  timerange = '%dD'  % (span / 24)
	elif period == 86400: timerange = '%dD'  % span
	result['pointStart'] = point_start
	result['pointInterval'] = period * 1000
	result['title'] = 'server statistics for the past %s' % timerange
	result['timespan'] = timerange
	result['interval'] = time
	print dumps(result)

''' Convert raw data into highchart format '''
def format_data(datas):
	data = group_data(datas)
	result = []
	for index,key in enumerate(data.keys()):
		d = {
				'name' : key,
				'data' : data[key],
				'legendIndex' : index
			}
		if key in ['requests', 'megabytes']:
			d['yAxis'] = 1
		result.append(d)
	return result

''' Groups all data into lists of timestamps and metrics '''
def group_data(datas):
	result = {}
	for m in METRICS:
		result[m] = []
	for data in datas:
		for m in METRICS:
			result[m].append( data.get(m, 0) )
	return result

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

