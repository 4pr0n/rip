function init() {
	handleResize();
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
				$t.find('div.graph')
					.slideDown()
					.highcharts({
						colors: [ '#f00', '#0f0', '#00f', '#ff0', '#f0f', '#0ff'],
						chart: {
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
						yAxis: [{
							min: 0,
							title: null,
							labels: {
								style: {
									color: '#eee',
									fontFamily: 'Verdana, monospace',
								},
							},
						},{
							min: 0,
							opposite: true,
							title: null,
							labels: {
								style: {
									color: '#eee',
									fontFamily: 'Verdana, monospace',
								},
							},
						}],
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
							backgroundColor: '#333',
							borderWidth: '3px',
							style: {
								color: '#eee',
								fontFamily: 'Verdana, monospace',
							},
						},
						credits: {
							enabled: true,
							text: 'data is in ' + (json.interval == '5min' ? '5min' : '1 ' + json.interval) + ' intervals. all times in PST',
							href: null,
							style: {
								color: '#eee',
								fontFamily: 'Verdana, monospace',
							},
						},
						series: json.series,
					})
			});
	});
}

function handleResize() {
	var $bb = $('#bottom_bar');
	var t = $(window).height() - $bb.height();
	$bb.css('top',  t + 'px');
}
$(window).resize(function() {
	handleResize
});

$(document).ready( init() );
