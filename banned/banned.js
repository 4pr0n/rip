$(document).ready(function() {
	$.getJSON('banned.cgi')
		.fail( function(x, s, e) {
			$('#ban_reason')
				.empty()
				.addClass('center')
				.append( $('<h3 />').html('error while contacting server:') )
				.append( $('<div />').html('status:' + x.status) )
				.append( $('<div />').html(s + ': "' + e + '"') )
				.append( $('<div />').html(x.responseText) )
				.show();
		})
		.done(function(json) {
			if (json.error != null) {
				$('#ban_reason')
					.empty()
					.addClass('center')
					.append( $('<div />').html(json.error) );
				if (!json.banned) {
					$('#ban_reason_title')
						.html('you probably are not banned');
				}
				$('#ban_removal')
					.empty()
					.html('there are no bans to lift');
			} else if (json.reason != null) {
				$('#ban_reason')
					.empty()
					.addClass('center')
					.append( $('<h3 />').html('reason for ban: ' + json.reason) )
					.show();
				if (json.time != null) {
					var date = new Date(json.time * 1000);
					var lifted = new Date(json.lifted * 1000);
					var days = parseInt((lifted - date) / (1000 * 3600 * 24));
					$('#ban_removal')
						.empty()
						.append( $('<h3 />').html('this ban is your <b>final warning</b> <br>your next ban will be <b>permanent</b>') )
					$('<div />')
						.html('your ban will be lifted <b>in ' + days + ' days</b>')
						.css('margin-bottom', '5px')
						.appendTo( $('#ban_removal') );
					$('<div />')
						.html('the ban was placed on ' + date)
						.appendTo( $('#ban_removal') );
					$('<div />')
						.html('the ban will be removed on ' + lifted)
						.appendTo( $('#ban_removal') );
				}
			}
		});
});
