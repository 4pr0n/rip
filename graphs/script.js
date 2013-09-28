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
}

function showGraph($t) {
	if ($t.attr('expanded') === 'true') {
		$t.removeAttr('expanded');
		$t.find('h1').html('&#x25BC; ' + $t.attr('id') + '-term stats');
		$t.find('div.graph').slideUp();
		return;
	}
	$t
		.attr('expanded', 'true')
		.find('h1').html('&#x25B2; ' + $t.attr('id') + '-term stats')
	$t.find( $('div.graph') )
		.empty()
		.css('vertical-align', 'center')
		.append( 
				$('<img />')
					.attr('src', '../spinner_dark.gif')
					.css({ width: '80px', height: '80px'})
		)
		.append( $('<div />').html(' rendering...') );
	
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
						chart: {
							type: 'line'
						},
						title: {
							text: json.title,
						},
						xAxis: {
							type: 'datetime',
						},
						yAxis: [{
							min: 0,
							title: null,
						},{
							min: 0,
							opposite: true,
							title: null,
						}],
						series: json.series,
					})
			});
	});
}

$(document).ready( init() );
