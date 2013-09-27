function init() {
	$('table#hourly').click(function() {
		showGraph( $(this) )
	});
	$('table#daily').click(function() {
		showGraph( $(this) )
	});
	$('table#weekly').click(function() {
		showGraph( $(this) )
	});
}

function showGraph($t) {
	if ($t.attr('expanded') === 'true') {
		$t.removeAttr('expanded');
		$t.find('h1').html('[+] ' + $t.attr('id') + ' stats');
		$t.find('div.graph').slideUp();
		return;
	}
	$t
		.attr('expanded', 'true')
		.find('h1').html('[-] ' + $t.attr('id') + ' stats')
	$t.find( $('div.graph') )
		.empty()
		.append( 
				$('<img />').addClass('spinner').attr('src', '../spinner_dark.gif')
		)
		.slideDown();
	$t.find('td').slideDown();
	$.getJSON('get-tsd.cgi?time=' + $t.attr('id'))
		.fail(function(x, s, e) { 
			$t.find( $('div.graph') ).html('ERROR: ' + e);
		})
		.done(function(json) {
			$t.find( $('div.graph') ).html('WE GOT A GRAPH! ' + json);
		});
}

$(document).ready( init() );
