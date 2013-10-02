function init() {
	$('table#short').click(function() {
		showGraph( $(this) )
	});
	$('table#mid').click(function() {
		showGraph( $(this) )
	});
	$('table#long').click(function() {
		showGraph( $(this) )
	});
	$('table#short').click();
}

function showGraph($t) {
	if ($t.attr('expanded') === 'true') {
		$t.removeAttr('expanded');
		$t.find('span.arrow').addClass('norotate').removeClass('rotate');
		$t.find('div.graph').slideUp();
		return;
	}
	$t.attr('expanded', 'true')
	$t.find('span.arrow').addClass('rotate').removeClass('norotate');
	$t.find( $('div.graph') )
		.empty()
		.css('vertical-align', 'middle')
		.append( 
				$('<img />')
					.addClass('center')
					.attr('src', '../spinner_dark.gif')
					.css({ width: '80px', height: '80px'})
		)
		.append( $('<div />').html(' loading...') );
	
	$t.find('div.graph').slideDown(function() {
		$.getJSON('get-tsd.cgi?time=' + $t.attr('id'))
			.fail(function(x, s, e) { 
				$t.find('div.graph').html('ERROR: ' + e + '<br><br>' + x.responseText);
			})
			.done(function(json) {
				Highcharts.setOptions({
					global: { useUTC: false }
				});
				$t.find('div.graph').slideDown();
				var chart = new Highcharts.Chart({
					colors: [ 
						'black',
						'white',
						'red',     // Rips
						'orange',  // Images
						'yellow',  // 404
						'lime',    // megabytes
						'blue',    // zips
						'violet',  // album_views
						'cyan',    // requests
					],
					chart: {
						renderTo: $t.find('div.graph')[0],
						type: 'line',
						borderRadius:    '20px',
						backgroundColor: 'rgba(255, 255, 255, 0.0)',
						plotBackgroundColor: 'rgba(255, 255, 255, 0.0)',
						style: {
							fontFamily: 'Verdana, monospace',
							fontSize: '1.2em',
							color: '#fff',
						},
					},
					legend: {
						align: 'left',
						layout: 'vertical',
						verticalAlign: 'top',
						y: 50,
						itemMarginTop: 10,
						itemMarginBottom: 10,
						itemStyle: {
							color: '#ddd',
							fontFamily: 'Verdana, monospace',
						},
						itemHoverStyle: {
							color: '#fff',
							fontFamily: 'Verdana, monospace',
						}
					},
					title: {
						text: null, //json.title,
						style: {
							fontFamily: 'Verdana, monospace',
							fontSize: '1.4em',
							color: '#eee',
						},
					},
					xAxis: {
						type: 'datetime',
						labels: {
							style: {
								color: '#eee',
								fontFamily: 'Verdana, monospace',
							},
						},
					},
					yAxis: {
						type: 'logarithmic',
						min: 1,
						title: null,
						labels: {
							style: {
								color: '#eee',
								fontFamily: 'Verdana, monospace',
							},
						},
					},
					plotOptions: {
						series: {
							pointStart: json.pointStart,
							pointInterval: json.pointInterval,
							style: {
								backgroundColor: '#888',
								fontFamily: 'Verdana, monospace',
							},
						},
					},
					tooltip: {
						backgroundColor: '#555',
						borderWidth: '3px',
						style: {
							color: '#eee',
							fontFamily: 'Verdana, monospace',
							fontWeight: 'bold',
						},
					},
					credits: {
						enabled: true,
						text: 'data is in ' + (json.interval == '5min' ? '5min' : '1 ' + json.interval) + ' intervals.<br>all times in PST',
						align: 'left',
						href: null,
						style: {
							color: '#eee',
							fontFamily: 'Verdana, monospace',
						},
						position: {
							align: 'left',
							x: 10,
							verticalAlign: 'bottom',
							y: -15,
						},
					},
					series: json.series,
				});
			});
	});
}

$(document).ready( init() );
