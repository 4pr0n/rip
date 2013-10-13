var MAX_USER_ALBUMS = 20; // Maximum number of rips allowed per user
var TOS_VERSION = 1;
var SUPPORTED_VIDEO_SITES = [
	'vimeo.com', 'dailymotion.com', 'tumblr.com', 'vine.co', 
	'pornhub.com', 'xvideos.com', 'beeg.com', '4tube.com', 
	'youporn.com', 'redtube.com', 'tube8.com', 'drtuber.com', 
	'motherless.com', 'videobam.com', 'videarn.com', 'fapmenow.com', 
	'xtube.com', 'youjizz.com', 'mobypicture.com', 'sexykarma.com',
	'fapjacks.com', 'setsdb.org', 'spankbang.com', 'fapdu.com', 
	'pornably.com', 'vporn.com', 'seenive.com', 'cliphunter.com',
	'', 'spankwire.com', 'vk.com', '']

function init() { // Executes when DOM is ready
	// Safari is BAD. 
	// I have to append a blank style element to get the darn thing to refresh
	// More info: http://stackoverflow.com/questions/3485365
	$('<style></style>').appendTo($(document.body)).remove();

	if (!over18()) return; // Check if user has agreed to TOS
	if (! $('#rip_text').length ) { return; } // Stop here if they haven't agreed

	$('#vid_text').keyup( function(e) {
		if (e.keyCode == 13) {
			startVid();
		}
	});
	$('#rip_text').keyup( function(e) {
		if (e.keyCode == 13) {
			startRip(); // Start rip when user presses enter
		}
	});
	// Hover list of supported video sites
	var $vids = $('#video_sites')
		.bind('click mouseenter', function(e) {
			$('#list_of_video_sites')
				.stop()
				.remove();
			var $sites = $('<table />')
				.css('cell-spacing', '15px');
			var $siterow = $('<tr />')
				.append(
					$('<td colspan="4" />')
						.append( $('<h2 />').html('compatible with:').css('margin', '3px') )
				).appendTo($sites);
			$siterow = $('<tr />');
			$.each(SUPPORTED_VIDEO_SITES, function(i, site) {
				$('<td />')
					.addClass('site')
					.html( site.substr(0, site.indexOf('.')) )
					.appendTo($siterow);
				if ( (i+1) % 4 == 0
					|| i == SUPPORTED_VIDEO_SITES.length - 1) {
					$sites.append($siterow);
					$siterow = $('<tr />');
				}
			});
			$sites
				.attr('id', 'list_of_video_sites')
				.hide()
				.appendTo(document.body)
				.css({
					'position' : 'absolute',
					'z-index' : 99,
					'top' : $vids.position().top + $vids.height() + 5,
					'left' : $('#video_desc').position().left + ($('#video_desc').width() / 2) - ($sites.width() / 2),
					'background-color' : '#444',
					'color' : '#fff',
					'box-shadow' : '0px  0px 40px rgba(255, 255, 255, 1.0)',
					'padding' : '10px',
					'text-align' : 'center',
					'border-radius' : '20px',
					'font-size' : '0.9em',
				})
				.click(function() {
					$(this)
						.css('margin-top', '0px')
						.animate({'margin-top': '-=200', queue: false}, 400, 'swing')
						.fadeOut({queue: false, duration: 400}, function() { $(this).remove() })
				})
				.css('margin-top', '+200px')
				.fadeIn({queue: false, duration: 400})
				.animate({'margin-top': '-=200', queue: false}, 400, 'swing');
		})
		.bind('mouseout', function(e) {
			$('#list_of_video_sites')
				.css('margin-top', '0px')
				.animate({'margin-top': '-=200', queue: false}, 400, 'swing')
				.fadeOut({queue: false, duration: 400}, function() { $(this).remove() })
		});
	// Display cache if needed
	if (getCookie('cache_enabled') == 'true') {
		$('#rip_cached').show();
		$('#label_cached').show();
	} else {
		$('#rip_cached').hide();
		$('#label_cached').hide();
	}
	$('#recent').fadeOut();
	refreshRecent();

	loadUserRips(); // Load user rips, check if limit is exceeded
}

function refreshRecent() { // Refresh list of "recent rips"
	$('#recent_spinner').css('visibility', 'visible');
	$('#recent').fadeOut();
	$.getJSON('rip.cgi?recent=y')
		.fail( function(x, s, e) {
			$('#recent')
				.hide()
				.empty()
				.addClass('center')
				.append( $('<h3 />').html('error while contacting server:') )
				.append( $('<div />').html('status:' + x.status) )
				.append( $('<div />').html(s + ': "' + e + '"') )
				//.append( $('<div />').html(x.responseText) )
				.fadeIn();
			$('#recent_spinner').css('visibility', 'hidden');
		})
		.done(function(json) {
			var $ul = $('<ul />').css('padding-left', '15px');
			$.each(json.recent, function(i, rec) {
				var url = rec.url.replace('http://www.', '').replace('http://', '').replace('https://', '');
				var $li = $('<li />').addClass('recent');
				$('<a />') // DOWNLOAD
					.addClass('download_box download_arrow')
					.html('&nbsp;&nbsp;')
					.attr('album', url)
					.attr('href', '#' + escape(url).replace(/\//g, '%2F'))
					.click(function() {
						return loadAlbum($(this).attr('album'));
					})
					.appendTo($li);
				$('<a />') // VIEW ALBUM
					.addClass('download_box')
					.css('margin-right', '5px')
					.attr('href', rec.view_url)
					.attr('target', '_BLANK' + String(Math.random()) )
					.html('view')
					.appendTo($li);
				$('<a />') // SOURCE LINK
					.css('padding-left', '3px')
					.css('font-size', '0.9em')
					.attr('href', rec.url)
					.attr('target', '_BLANK')
					.html(truncate(url, 20))
					.appendTo($li);
				$ul.append($li);
			});
			$('#recent')
				.empty()
				.append($ul)
				.fadeIn(400, function() { 
					$('#recent_spinner').css('visibility', 'hidden');
				});
	});
}

function loadAlbum(url) { // Loads URL in hash and refreshes page
	if (url.indexOf('#') > -1) {
		url = url.substr(0, url.indexOf('#'));
	}
	window.location.hash = url;
	window.location.reload(true);
}

function getCookie(key) { // Retrieves cookie
  var cookies = document.cookie.split(';');
  for (var i in cookies) {
		if (cookies[i].charAt(0) == ' ') {
			cookies[i] = cookies[i].substr(1);
		}
    var pair = cookies[i].split('=');
    if (pair[0] == key)
      return pair[1];
  }
  return "";
}

function getQueryString(start) { // Gets URL for backend album rip
	// var url = escape($('#rip_text').val());
	// because python CGI doesn't like // in the url
	var url = encodeURIComponent($('#rip_text').val());
	var query = 'rip.cgi?url=' + url;
	if (start == true) {
		query += '&start=true';
		if ( ! $('#rip_cached').prop('checked') ) {
			query += '&cached=false';
		}
	} else {
		query += '&check=true';
	}
	return query;
}

function setHash(url) { // Adds a site to the URL hash
	if (url) {
		url = url.replace('http://', '').replace('https://', '')
		url = escape(url).replace(/\//g, '%2F');
		window.location.hash = url;
	}
}

function disableRipControls() {
	$(window).bind('beforeunload', function() {
		return "Exiting during a rip may cause the archive to become corrupted. Are you sure you want to leave this page?";
	});
	$('#rip_text, #rip_button')
		.stop()
		.prop('disabled', true)
		.animate(
			{
				'opacity': 0.3,
			},
			600
		);
}
function enableRipControls() {
	$(window).unbind('beforeunload');
	$('#rip_text, #rip_button')
		.stop()
		.prop('disabled', false)
		.animate(
			{
				'opacity': 1.0,
			},
			600
		);
}

function startRip() { // Start ripping album
	if ($('#status_bar').attr('exceeded')) {
		return; // User has exceeded max number of rips, short-circuit
	}
	disableRipControls();
	setHash( $('#rip_text').val() );
	var $statbar = $('#status_bar')
		.slideUp(function() {
			$statbar.empty()
				.attr('has_download_link', 'false')
				.append( $('<img />').attr('src', './images/spinner_dark.gif') )
				.append( $('<span />').html(' loading...') )
				.slideDown();
			var query = getQueryString(true);
			$.getJSON(query)
				.fail(ripFailHandler)
				.done(ripRequestHandler);
			setTimeout(function() { checkRip() }, 500);
		});
}

function ripFailHandler(x, s, e) {
	var $statbar = $('#status_bar');
	$statbar
		.slideUp(400, function() {
			$statbar.empty()
				.hide()
				.addClass('center')
				.append( $('<h3 />').html('error occurred while trying to rip') )
				.append( $('<div />').html('this sometimes happens. try to rip again.') )
				.append( 
					$('<div />')
						.css('padding-top', '10px')
						.css('padding-bottom', '10px')
						.html('if the issue persists, ') 
						.append( 
							$('<a />')
								.html('tell 4_pr0n')
								.attr('href', 'http://www.reddit.com/message/compose/?to=4_pr0n' +
									'&subject=about%20rip.rarchives.com&message=' +
									'Bad%20things%20happened%20when%20I%20tried%20to%20rip%20' + encodeURIComponent($('#rip_text').val()) + 
									'%0A%0A%20%20%20%20status: ' + encodeURIComponent(x.status) + 
									'%0A%20%20%20%20' + encodeURIComponent(s) + ': "' + encodeURIComponent(e) + '"' + 
									'%0A%0A%20%20%20%20' + encodeURIComponent(x.responseText.substring(x.responseText.indexOf('Traceback (most recent')).replace('\n', '\n    ')).replace('%0A', '%0A%20%20%20%20')
								)
								.addClass('box')
								.attr('target', '_BLANK')
							)
					)
				.slideDown(750)
				.css('opacity', '0')
				.animate(
						{ opacity: 1 },
						{ queue: false, duration: 750 }
				)
		});
	setProgress(0);
	enableRipControls();
}

function ripRequestHandler(json) { // Handles rip requests (both 'start' and 'check')
	var $statbar = $('#status_bar');
	if (json.error) {
		var err = $('<div />')
			.addClass('error')
			.html('error: ' + json.error);
		$statbar.empty()
			.append(err);
		setProgress(0);
		enableRipControls();
		return;
	}
	else if ($statbar.html().indexOf('error: ') >= 0) {
		return;
	}
	else if (json.zip && $statbar.attr('has_download_link') === 'false') {
		$statbar.attr('has_download_link', 'true')
		var $result = $('<div />')
			.addClass('center');
		var ziptext = json.image_count ? 
				'download .zip (' + json.image_count + ' pics)' :
				'download .zip';
		$('<a />') // DOWNLOAD LINK
			.addClass('download_box pre')
			.attr('href', json.zip)
			.html(ziptext)
			.appendTo($result);
		if (json.album) {
			$('<a />') // VIEW ALBUM
				.html('view album')
				.attr('href', json.url)
				.attr('target', '_BLANK')
				.addClass('download_box pre')
				.css('margin-left', '10px')
				.appendTo($result);
		}
		if (json.limit) {
			$('<div />') // LIMIT EXCEEDED
				.addClass('error')
				.css('padding-top', '5px')
				.html('rip was capped at ' + json.limit + ' images')
				.appendTo($result);
		}
		$('<div />') // SHARE
			.addClass('fontmed pre')
			.css('margin-top', '15px')
			.append( $('<span />').html('share: ') )
			.append( $('<input />')
					.addClass('textbox')
					.attr('id', 'share_box')
					.attr('name', 'share_box')
					.css('width', '75%')
					.css('font-size', '0.8em')
					.focus(   function() { $(this).select(); })
					.mouseup( function() { return false; })
					.prop('readonly', true)
					.val($(window.location).attr('href'))
			)
			.appendTo($result);
		
		setProgress(0);
		$statbar
			.slideUp(400, function() {
				$statbar.empty()
				.hide()
				.append($result)
				.slideDown(750)
				.css('opacity', '0')
				.animate(
						{ opacity: 1 },
						{ queue: false, duration: 750 }
				)
			});
		enableRipControls();
	}
	else if (json.log || json.log == '') {
		var log = json.log.replace(/\n/g, '');
		if ( !$('#rip_button').prop('disabled')
		   || $statbar.attr('has_download_link') === 'true')
		{
			return; // Already ripped, nothing to see here
		}
		// Check for thumbnails
		if (log.indexOf('thumbnail: (') >= 0) {
			var thumbnail = log.substr(log.indexOf('thumbnail: (') + 12);
			thumbnail = thumbnail.substr(0, thumbnail.length - 1);
			if ($statbar.data('lastThumb') !== thumbnail) {
				$statbar.data('lastThumb', thumbnail);
				var $img = $('<img />');
				$img
					.hide()
					.appendTo($(document.body));
				$img
					.attr('src', thumbnail)
					.imagesLoaded(function() {
						$img
							.css({
								'width' : 'auto',
								'height' : 'auto',
								'position' : 'absolute',
								'top'  : $statbar.position().top,
								'left' : $statbar.position().left + ($statbar.width() / 2) - ($img.width() / 2),
								'opacity' : '1.0',
							})
							.show()
							.animate({
								'width'   : '10px',
								'height'  : '10px',
								'top'     : $statbar.position().top,
								'left'    : $statbar.position().left + ($statbar.width() / 2),
								'opacity' : '0.0',
							},
							1000,
							function() {
								$img.remove()
							});
					});
			}
		}
		
		if (log.indexOf(' - ') != -1) {
			log = log.substr(0, log.indexOf(' - '));
		}
		// Update progress bar
		var i = log.indexOf('(');
		var j = log.indexOf(')', i);
		var k = log.indexOf('/', i);
		if (i >= 0 && j >= 0 && k >= 0 && k < j) {
			var num = parseFloat(log.substr(i+1, k).replace(',', ''));
			var denom = parseFloat(log.substr(k+1, j));
			setProgress(num / denom);
		}
		if (log !== '') {
			$statbar.empty();
			$('<div />')
				.append( $('<img />')
						.attr('src', './images/spinner_dark.gif')
						.css('padding-right', '10px')
						.css('padding-left', '10px')
				)
				.append( $('<span />').html(log) )
				.appendTo($statbar);
			
			$statbar.show();
		}
		
		// Check for more updates in 0.5 sec
		if ( $('#rip_button').prop('disabled') ) {
			setTimeout(function() { 
				checkRip();
			}, 500);
		}
	}
}

// Removes middle section of long text, replaces with '...'
function truncate(text, split_size) {
	if (text.length > (split_size * 2) + 3) {
		text = text.substr(0, split_size) + "..." + text.substr(text.length-split_size);
	}
	return text;
}

function checkRip() { // Check the status of the currently-ripping album
	var query = getQueryString(false);
	$.getJSON(query, ripRequestHandler);
}

function setExample(site) {
	var dic = {
		'imgur'       : 'http://imgur.com/a/DU74E', //'http://imgur.com/a/RdXNa',
		'tumblr'      : 'http://owlberta.tumblr.com/tagged/me',
		'twitter'     : 'https://twitter.com/MrNMissesSmith',
		'deviantart'  : 'http://geekysica.deviantart.com/gallery/40343783',
		'flickr'      : 'https://secure.flickr.com/photos/peopleofplatt/sets/72157624572361792/with/6166517381/',
		'photobucket' : 'http://s1216.beta.photobucket.com/user/Liebe_Dich/profile/',
		'webstagram'  : 'http://instagram.com/joselyncano#',
		'imagefap'    : 'http://www.imagefap.com/pictures/2885204/Kentucky-Craigslist',
		'imagearn'    : 'http://imagearn.com/gallery.php?id=1616', // 'http://imagearn.com/gallery.php?id=82587',
		'imagebam'    : 'http://www.imagebam.com/gallery/3b73c0f6ba797e77a33b46779fbfe678/',
		'xhamster'    : 'http://xhamster.com/photos/gallery/1479233/sarah_from_glasgow.html',
		'getgonewild' : 'http://getgonewild.com/profile/EW2d',
		'anonib'      : 'http://www.anonib.com/azn/res/74347.html',
		'oneclickchicks' : 'http://forum.oneclickchicks.com/album.php?albumid=12510',
		'4chan'       : 'http://boards.4chan.org/s/res/14020907',
		'motherless'  : 'http://motherless.com/GC1FEFF5',
		'minus'       : 'http://nappingdoneright.minus.com/mu6fuBNNdfPG0',
		'gifyo'       : 'http://gifyo.com/robynsteen/', // http://gifyo.com/LinzieNeon/',
		'cghub'       : 'http://katiedesousa.cghub.com/images/',
		'chansluts'   : 'http://www.chansluts.com/camwhores/girls/res/3405.php',
		'teenplanet'  : 'http://photos.teenplanet.org/atomicfrog/Latino_M4N/Ass_Beyond_Belief',
		'buttoucher'  : 'http://butttoucher.com/users/Shelbolovesnate',
		'imgbox'      : 'http://imgbox.com/g/UyaOUEBXzO',
		'reddit'      : 'http://reddit.com/user/thatnakedgirl',
		'fuskator'    : 'http://fuskator.com/full/l4IoKiE51-K/1012_chicas123_exotic_landysh_met-art_old+chicks.html#',
		'redditsluts' : 'http://redditsluts.soup.io/tag/Miss_Ginger_Biscuit',
		'kodiefiles'  : 'http://www.kodiefiles.nl/2010/10/ff-eerder-gezien.html',
		'gallerydump' : 'http://www.gallery-dump.com/index.php?gid=553056',
		'fapdu'       : 'http://fapdu.com/cuties-4.view/',
		'seenive'     : 'http://seenive.com/u/911429150038953984',
		'nfsfw'       : 'http://nfsfw.com/gallery/v/Emily%20Ratajkowski',
	};
	loadAlbum(dic[site].replace('http://', ''));
	return false;
}

function setProgress(perc) {
	var value;
	if (perc > 1) {
		value = "100";
	} else if (perc < 0) {
		value = "0";
	} else {
		value = "" + (100 * perc);
	}
	if (value == "0") {
		$('#progress_bar_div').hide();
	} else if (!isNaN(parseFloat(value)) && isFinite(value)) {
		$('#progress_bar_div').show();
		$('#progress_bar').val(value);
	}
}

/////////////////////
// Video ripper


// Start ripping album
function startVid() {
	$('#vid_text, #vid_button')
		.stop()
		.prop('disabled', true)
		.animate(
			{
				'opacity': 0.3,
			},
			600
		);
	$('#vid_status')
		.css('text-align', 'center')
		.empty()
		.append( $('<img />') .attr('src', './images/spinner_dark.gif') )
		.append( $('<span />').html(' loading...') );
	
	var query = 'vid.cgi?url=' + encodeURIComponent($('#vid_text').val());
	$.getJSON(query, function(json) {
		if (json.url) {
			var $result = $('<div />');
			if (json.type && json.size) {
				$('<div />')
					.addClass('fontmed bold')
					.css('margin-bottom', '15px')
					.html(json.type + ' (' + json.size + ')')
					.appendTo($result);
			}
			$('<a />') // VIDEO REDIRECT
				.addClass('download_box pre')
				.css('padding', '5px')
				.attr('href', 
								'data:text/html;charset=utf-8,\n\n' +
			          '<html><head><meta http-equiv=\'REFRESH\' content=\'0;url=' +
								json.url + 
								'\'></head><body><h1>redirecting...</h1></body></html>\n\n')
				.attr('rel', 'noreferrer')
				.html('redirect to video')
				.appendTo($result);
			$('<a />') // VIDEO DOWNLOAD
				.attr('href', json.url)
				.attr('rel', 'noreferrer')
				.addClass('download_box pre')
				.css('padding', '5px')
				.css('margin-left', '15px')
				.click(function() { return false; })
				.html('right click, save as')
				.appendTo($result);
			
			var $link = $('<div />')
				.css('margin-top', '10px');
			$('<input />')
				.addClass('textbox')
				.attr('id', 'vid_rip_textbox')
				.css('padding', '5px')
				.attr('type', 'text')
				.focus(   function() { return false; })
				.mouseup( function() { $(this).select(); })
				.val(json.url)
				.appendTo($link);
			$result.append($link);
			$('#vid_status')
				.empty().hide()
				.append($result)
				.slideDown(1000)
		}
		else if (json.error) {
			$('#vid_status')
				.empty().hide()
				.append(
					$('<div />')
						.addClass('error')
						.html('error: ' + json.error)
				)
				.fadeIn();
		} else {
			$('#vid_status')
				.empty().hide()
				.append(
					$('<div />')
						.addClass('error')
						.html('error: unexpected response')
				)
				.fadeIn();
		}
		$('#vid_text, #vid_button')
			.stop()
			.prop('disabled', false)
			.animate(
				{
					'opacity': 1.0,
				},
				600
			);
	});
}

function showMoreNews() {
	$('#more_news_link').hide();
	$('#more_news').slideDown(2000);
}

///////////////////////////
// COOKIES & TOS
function setCookie(key, value) {
	document.cookie = key + '=' + value + '; expires=Fri, 27 Dec 2999 00:00:00 UTC; path=/';
}
function getCookie(key) {
	var cookies = document.cookie.split('; ');
	for (var i in cookies) {
		var pair = cookies[i].split('=');
		if (pair[0] == key)
			return pair[1];
	}
	return "";
}
var TOS_VERSION = '1';
function over18() {
	if (! $('#rip_text') ) { return true; } // Not at the rip page
	if (getCookie('rip_tos_v' + TOS_VERSION) === 'true') { return true; } // Already agreed
	// User hasn't agreed to TOS or verified age.
	$('#maintable').hide();
	$('#footer').hide();
	var $tos = $('<div />')
		.append( $('<h1 />').html('Warning: This site may contain explicit content') )
		.addClass('warning')
		.attr('id', 'maindiv')
		.css('margin', '20px')
		.css('padding-top', '5px');
		
	$('<div />')
		.html(
			'This website may contain adult content which is not appropriate for persons over the age of 18.' +
			'<p>' +
			'By entering this site, you agree to the following terms of use:')
		.appendTo($tos);
	
	$('<ul />') // LIST OF TOS
		.append( $('<li />').html('I am over eighteen years old') )
		.append( $('<li />').html('I will not use this site to acquire illegal material in any way. This includes:') )
		.append( $('<li />').html('<b>"Jailbait"</b> or any sexual content depicting persons under the age of 18 (including non-nude)').css('margin-left', '20px') )
		.append( $('<li />').html('<b>Beastiality</b>').css('margin-left', '20px') )
		.append( $('<li />').html('<b>Incest</b> (even implied)').css('margin-left', '20px') )
		.append( $('<li />').html('<b>Copyrighted content</b>').css('margin-left', '20px') )
		.append( $('<li />').html('<b>Gore/violent imagery</b> intended to shock or disturb').css('margin-left', '20px') )
		.append( $('<li />').html('I will report illegal content found on the site immediately') )
		.append( $('<li />').html('Each album has a <b class="red">report</b> button').css('margin-left', '20px') )
		.append( $('<li />').html('I will not rip more than 20 albums per day.') )
		.append( $('<li />').html('I am aware that the albums I rip are visible to others.') )
		.appendTo($tos);

	$('<div />')
		.html('<b>Failure to follow the above rules will result in a ban</b>')
		.css('margin-bottom', '20px')
		.appendTo($tos);

	$('<input />') // AGREE
		.attr('type', 'button')
		.val('Agree & Enter')
		.addClass('button')
		.click(function() { i_agree() })
		.appendTo($tos);
	$('<input />') // DISAGREE
		.attr('type', 'button')
		.val('Leave')
		.addClass('button')
		.css('margin-left', '20px')
		.click(function() { window.location.href = 'about:blank' })
		.appendTo($tos);
	
	$(document.body).append($tos);
	return false;
}

function i_agree() {
	setCookie('rip_tos_v' + TOS_VERSION, 'true');
	$('#maintable').show()
	$('#footer').show()
	$('#maindiv').hide()
	init(); // Load the page again
}

//////////////////////
// USER'S RECENT RIPS
function loadUserRips() {
	$.getJSON('rip.cgi?byuser=me', function(json) {
		if (json.albums && json.albums.length > 0) {
			var $userrips = $('#user_rips_td').empty();
			var $ol = $('<ol />');
			$.each(json.albums, function(i, rip) {
				$('<li />')
				.append( 
					$('<a />')
						.attr('href', './rips/#' + rip.album)
						.html(rip.album)
				).appendTo($ol);
			});
			$ol.appendTo($userrips);
			$('<div />')
				.addClass('center')
				.append(
					$('<a />')
						.attr('href', './rips/#user=me')
						.html('view your ripped albums')
				).appendTo($userrips);
			
			$('#user_rips_tab')
				.css('margin-top', '30px')
				.slideDown(750)
				.css('opacity', '0')
				.animate(
						{ opacity: 1 },
						{ queue: false, duration: 750 }
				);

			if (json.albums.length > MAX_USER_ALBUMS && false) {
				$('#rip_text').hide();
				$('#rip_button').hide();
				$('#rip_cached').hide();
				$('#label_cached').hide();
				var $err = $('<div />')
					.addClass('error center')
					.html(
							'you have ripped too much' +
							'<br>the maximum number of active rips is ' + MAX_USER_ALBUMS +
							'<br>try again later'
					);
					$('#status_bar')
						.empty()
						.attr('exceeded', 'true')
						.hide()
						.append($err)
						.fadeIn();
			}
		}
		// Start rip if needed
		var url = String(window.location);
		if (url.lastIndexOf('#') >= 0) {
			var link = unescape(url.substring(url.lastIndexOf('#')+1));
			if (link.indexOf('http://') != 0 && link.indexOf('https://') != 0) {
				link = 'http://' + link;
			}
			$('#rip_text').val(link);
			startRip();
		}
	});
}

$.fn.imagesLoaded = function(callback, fireOne) {
	var
		args = arguments,
		elems = this.filter('img'),
		elemsLen = elems.length - 1;

	elems
		.bind('load', function(e) {
			if (fireOne) {
				!elemsLen-- && callback.call(elems, e);
			} else {
				callback.call(this, e);
			}
		}).each(function() {
			// cached images don't fire load sometimes, so we reset src.
			if (this.complete || this.complete === undefined){
				this.src = this.src;
			}
		});
}

// Call initialization function after entire JS file is parsed
$(document).ready(init);
