#!/usr/bin/python

import cgi, cgitb; cgitb.enable()

import time
from json import loads, dumps
from os   import path, listdir

#METRICS = ['hits', 'rips', 'zips', 'album_views', 'images', 'thumbs', 'videos', 'checks', 'cgi', 'others', 'megabytes']
METRICS = {
	'requests'    : 'requests',
	'rips'        : 'album rips',
	'users'       : 'users',
	'zips'        : 'zip downloads',
	'album_views' : 'album views',
	'images'      : 'image views',
	'megabytes'   : 'mb downloaded',
	'404'         : 'error: 404',
	'err'         : 'error: 5xx',
	'ban'         : 'error: 403'
}

def main():
	keys = get_keys()
	span = 0        # Number of days to get metrics for
	if 'span' in keys and keys['span'].isdigit(): span = int(keys['span'])
	graphtype = keys.get('time', 'short')
	get_graphs(graphtype, span)

def get_graphtype_span_period(graphtype, span):
	if graphtype == 'short': 
		graphtype = '5min'
		period = 300 # 5 minutes
		defaultspan = 6 * 12 # X hours of 5min metrics
	elif graphtype == 'mid':  
		graphtype = 'hour'
		period = 3600 # 1 hour
		defaultspan = 3 * 24 # X days of 1hour metrics
	elif graphtype == 'long': 
		graphtype = 'day'
		period = 86400 # 1 day
		defaultspan = 30 # X days of 1day metrics
	else:
		raise Exception('Unknown graph type: %s' % graphtype)
	if span == 0:
		span = defaultspan
	return (graphtype, span, period)

def get_graphs(graphtype, span):
	(graphtype, timespan, period) = get_graphtype_span_period(graphtype, span)
	span = timespan
	cur = int(time.time())
	#cur = 1380782100 # For testing, TODO remove!

	t = int(cur / period) * period # Get starting point for metrics
	point_start = (t - ( (timespan - 1) * period)) * 1000
	datas = []
	missed_count = 0
	while timespan > 0:
		fname = path.join('logs', '%d-%s.log' % (t, graphtype)) # Path to log file
		data = {}
		if path.exists(fname): 
			r = open(fname, 'r').read().strip()
			data = loads(r)
			missed_count = 0
		else:
			data = {}
			missed_count += 1
		if 'users' in data: data['users'] = len(data['users']) # Return # of unique IPs, NOT the IPs
		if not 'bytes' in data: data['bytes'] = 0
		if not 'hits'  in data: data['hits']  = 0
		data['megabytes'] = data['bytes'] / (1024 * 1024)
		data['requests'] = data['hits']
		data.pop('bytes')
		data.pop('hits')
		datas.append(data)
		timespan -= 1
		t -= period
	if graphtype == '5min':
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
	result['interval'] = graphtype
	print dumps(result)

''' Convert raw data into highchart format '''
def format_data(datas):
	data = group_data(datas)
	result = []
	for index,key in enumerate(data.keys()):
		d = {
				'name' : key,
				'data' : data[key],
			}
		#if key in ['requests', 'mb downloaded']:
		#	d['yAxis'] = 1
		result.append(d)
	result = order_data(result)
	return result

''' Order the metrics '''
def order_data(result):
	result = sorted(result, key=lambda x: x.values(), reverse=True)
	for i, d in enumerate(result):
		d['legendIndex'] = i
		d['total'] = sum(d['data'])
	return result


''' Groups all data into lists of timestamps and metrics '''
def group_data(datas):
	result = {}
	for m in METRICS.keys():
		result[METRICS[m]] = []
	for data in datas:
		for m in METRICS.keys():
			result[METRICS[m]].append( data.get(m, 0) )
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

