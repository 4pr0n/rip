// CONSTANTS
var ALBUMS_AT_ONCE             = 6; // Number of albums to return per request
var ALBUM_PREVIEW_SIZE         = 4; // Number of thumbnails per album
var ALBUM_PREVIEW_IMAGE_BREAKS = 4; // Thumbnails per row (all-albums view)
var SINGLE_ALBUM_IMAGE_BREAKS  = 4; // Thumbnails per row (single-album view)
var IMAGES_PER_PAGE           = 12; // Thumbnails per page

// Executes when document has loaded
function init() {
	if (over18()) {
		return;
	}
	var url = String(window.location);
	if (!window.location.hash || window.location.hash.indexOf('_') == -1) {
		// Viewing all albums
		loadAllAlbums();
	} else {
		// Viewing specific album
		loadAlbum(window.location.hash.substring(1))
	}
	$(window).scroll(scrollHandler);
	
	if (String(window.location.hash) === '#report') {
		setTimeout(function() {
			window.location.reload(true);
		}, 30000);
	}
	// Prevent double-click selection
	document.ondblclick = function(evt) {
		if (window.getSelection)     window.getSelection().removeAllRanges();
		else if (document.selection) document.selection.empty();
	}
}


//////////////////////
// LOAD SINGLE ALBUM

function loadAlbum(album, start, count, startOver) {
	if (album == null) { return; }
	$('albums_table').attr('loading', 'true');
	$('#albums_area').hide();
	if (start == undefined) start = 0;
	if (count == undefined) count = IMAGES_PER_PAGE;
	if (startOver == undefined || startOver) {
		$('#thumbs_table').empty();
	}
	var req = 'view.cgi';
	req += '?start=' + start;
	req += '&count=' + count;
	req += '&view=' + album;
	$.getJSON(req)
		.fail( jsonFailHandler )
		.done(function(json) {

			if (json.error != null) {
				throw new Error(json.error);
			} else if (json.album == null) {
				throw new Error("cannot find album");
			}
			var album = json.album;
			if (album.images.length == 0) {
				// Album not found
				$('#status_area').hide();
				$('#thumbs_table').hide()
				$('#thumbs_area')
					.css({
						'text-align': 'center',
						'padding': '30px',
						'padding-top': '20px'
					})
					.append($('<h1 />').html('album not found'))
					.append($('<div />').html('this album (' + window.location.hash.replace('#','') + ') is no longer available'))
					.slideDown();
				if (album.guess != null && album.guess != '') {
					$('#thumbs_area').append(
						$('<div />')
							.html('the album may have originated from:')
							.css('padding-top', '10px')
							.append( 
								$('<div />')
									.css('margin-top', '20px')
									.append(
										$('<a />')
											.addClass('download_box')
											.attr('href', album.guess)
											.attr('target', '_BLANK' + String(Math.random()))
											.attr('rel', 'noreferrer')
											.html(album.guess)
									)
									.append(
										$('<a />')
											.css('margin-left', '10px')
											.addClass('download_box')
											.attr('href', '../#' + album.guess)
											.html('re-rip')
									)
										
							)
					);
				}
				$('#next').html('');
				$('#albums_table').attr('loading', 'true');
				// TODO Reverse-encode the album name into a URL. Provide link to URL & Album ripper
				return;
			}
			if (! $('#status_area').is(':visible')) {
				$('#status_area')
					.fadeIn()
					.css('padding-top', '0')
					.css('padding-bottom', '0')
					.animate( { 
						'padding-top' : '10',
						'padding-bottom' : '10'
						}, {
							queue: false,
							duration: 500
						}
					);
				$('#thumbs_area').fadeIn();
			}
			$('#album_title').html(album.album + ' (' + album.total + ' images)');
			
			if (album.report_reasons != undefined) {
				showReportsToAdmin(album);
			} else if ( $('#report').html().indexOf('delete') == -1 ) {
				// Show report link
				$('<a />')
					.html('report this album')
					.addClass('bold red shadow')
					.attr('href', '')
					.attr('title', 'let the site admins know if any content should be looked at or removed')
					.attr('album', album.album)
					.click(function() {
						report($(this).attr('album'))
						return false;
					})
					.appendTo( $('#report').html('') );
			}
			
			// .ZIP link
			$('<a />')
				.html(album.archive.replace('./', '')+" ("+album.size+")")
				.attr('href', album.archive)
				.attr('title', 'download a .zip archive containing these photos')
				.addClass('download_box')
				.appendTo( $('#album_download').html('') );

			// URL link
			$('#album_url').empty();
			$('<a />')
				.html(album.url)
				.attr('href', album.url)
				.attr('title', 'link to external site where these images were grabbed')
				.addClass('bold')
				.attr('target', '_BLANK' + String(Math.random()))
				.attr('rel', 'noreferrer')
				.appendTo( $('#album_url').html('') );
			
			// Get URLs link
			$('#get_urls').empty();
			$('<a />')
				.html('get list of urls')
				.attr('title', 'easy to copy and paste into imgur')
				.addClass('download_box')
				.attr('href', 'urls_raw.cgi?album=' + album.album)
				.attr('target', '_BLANK' + String(Math.random()))
				.appendTo( $('#get_urls') );
			
			// Append thumbnails to table in rows
			var $thumbrow = $('<tr />');
			$.each(album.images, function(i, image) {
				var thumbtd = $('<td />')
					.addClass('image');
				
				var thumba = $('<a />')
					.attr('href', image.image)
					.click( function() { return false } );
				
				$('<img />')
					.attr('src', image.thumb)
					.css('visibility', 'hidden')
					.attr('full', image.image)
					.load( function() {
						$(this).css('visibility', 'visible');
					})
					.click( function() { 
						loadImage ( $(this) )
					})
					.appendTo(thumba);
				thumbtd.append(thumba)
					.appendTo($thumbrow);
				if ((i + 1) % SINGLE_ALBUM_IMAGE_BREAKS == 0 || i == album.images.length - 1) {
					$thumbrow
						.hide()
						.appendTo( $('#thumbs_table') )
						.fadeIn(1000)
						.css('display', 'table-row');
					$thumbrow = $('<tr />');
				}
			
		});
		
		// Set the next chunk of albums to retrieve
		if (album.start + album.count >= album.total) {
			$('#next').html(album.total + ' images loaded');
			$('#albums_table').attr('loading', 'true');
		} else {
			var remaining = album.total - (album.start + album.count);
			$('#next').attr('album', album.album)
				.attr('image_index', album.start + album.count)
				.html(remaining + ' images remaining');
			$('#albums_table').removeAttr('loading');
			scrollHandler();
		}
	});
	return true;
}

function loadMoreImages() {
	if ($('#albums_table').attr('loading')) { 
		// Already loading, or finished loading full album
		return;
	}
	// Load more images
	$('#albums_table').attr('loading', 'true');
	setTimeout(function() {
		$('#next').html($('#next').html() + '<br>loading...'); // Give them hope
	}, 100);
	
	setTimeout(function() {
		loadAlbum(
			$('#next').attr('album'), 
			$('#next').attr('image_index'), 
			IMAGES_PER_PAGE, 
			false);
	}, 500);
}

/////////////////////////
// ALL ALBUMS

function getAllAlbumUrl(after) {
	var hash = window.location.hash;
	var req = 'view.cgi';
	if (!hash) {
		req += '?view_all=true';
	} else if (hash.indexOf('user=') != -1) {
		hash = hash.substring(hash.indexOf('user=')+5);
		req += '?user=' + hash;
	} else if (hash.indexOf('report') != -1) {
		req += '?get_report=y';
	}
	if (after != undefined) {
		req += '&after=' + after;
	}
	req += '&count='   + ALBUMS_AT_ONCE;
	req += '&preview=' + ALBUM_PREVIEW_SIZE;
	return req;
}

function loadAllAlbums(after, startOver) {
	if (after == undefined) after = '';
	$('#albums_area').show();
	$('#status_area').hide();
	$('#thumbs_area').hide();
	
	// Remove existing albums if needed
	if (startOver == undefined || startOver) { 
		$('#albums_table').html('');
	}
	$.getJSON( getAllAlbumUrl(after) )
		.fail( jsonFailHandler )
		.done( function(json) {
			var albumstable = $('<table />')
				.css('width', '100%');
			var albumsrow = $('<tr />');
			// Iterate over every album
			$.each(json.albums, function (album_index, album) {
				var albumscell = $('<td />')
					.css('vertical-align', 'top')
					.css('width', '50%');
				if (album_index % 2 == 0) {
					albumscell.css('text-align', 'left')
				} else {
					albumscell.css('text-align', 'right')
						.css('padding-left', '20px');
				}
					
				var $imgtable = $('<table />')
					.addClass('page album clickable')
					.attr('id', album.album.replace('%20', '_'))
					.attr('show_album', 'true')
					.attr('album', album.album)
					.click( function() {
						// Check if click should open album (not on an image)
						if ($(this).attr('show_album') === 'true') {
							window.open($(location).attr('pathname') + '#' + $(this).attr('album'));
						}
					});
				
				// Show title and number of images
				var $title = $('<tr />')
					.css('vertical-align', 'top');
				var $titletd = $('<td />')
					.addClass('all_album_title')
					.attr('colspan', ALBUM_PREVIEW_IMAGE_BREAKS);
				var $titlezip = $('<a />')
					.addClass('download_box download_arrow')
					.html('&nbsp;&nbsp;')
					.attr('album', album.album)
					.attr('href', album.album + '.zip')
					.mouseenter( function() {
						$('#' + $(this).attr('album'))
							.removeAttr('show_album')
							.removeClass('clickable');
					})
					.mouseleave( function() {
						$('#' + $(this).attr('album'))
							.attr('show_album', 'true')
							.addClass('clickable');
					});
				var $titletext = $('<span />')
					.html(truncate(album.album, 12) + ' (' + album.total + ' images)');
				if (album_index % 2 == 0) {
					$titletd
						.append($titlezip)
						.append($titletext);
				} else {
					$titletd
						.append($titletext)
						.append($titlezip);
				}
				$title.append($titletd);
				$imgtable.append($title);
				
				if (album.reports) {
					// Display number of reports on album
					$('<tr />')
						.css('vertical-align', 'top')
						.addClass('fontsmall red bold shadow')
						.append( 
								$('<td />')
									.attr('colspan', ALBUM_PREVIEW_IMAGE_BREAKS)
									.css('margin',  '0px')
									.css('padding', '0px')
									.css('padding-bottom', '5px')
									.html('reports: ' + album.reports)
								)
						.appendTo($imgtable);
				}

				var imgrow = $('<tr />');
				// Iterate over every image in album
				$.each(album.images, function(image_index, image) {
					var imga = $('<a />')
						.attr('href', image.image)
						.attr('album', album.album.replace('%20', '_'))
						.click( function() { return false; } )
						.mouseenter( function() {
							$('#' + $(this).attr('album')).removeAttr('show_album').removeClass('clickable');
						})
						.mouseleave( function() {
							$('#' + $(this).attr('album')).attr('show_album', 'true').addClass('clickable');
						});
					$('<img />')
						.addClass('image_small')
						.attr('src', image.thumb)
						.attr('full', image.image)
						.css('visibility', 'hidden')
						.load( function() {
							$(this).css('visibility', 'visible')
								.attr('onload', '').unbind('load'); // Prevent future loads from resizing
						})
						.click( function() { 
							loadImage ( $(this) )
						})
						.appendTo(imga);
						
					$('<td />')
						.addClass('image_small')
						.append(imga)
						.appendTo(imgrow);
					if ( (image_index + 1) % ALBUM_PREVIEW_IMAGE_BREAKS == 0 && 
								image_index != album.images.length - 1 ) {
						$imgtable.append(imgrow);
						imgrow = $('<tr />');
					}
					$imgtable.append(imgrow);
				}); // End of for-each-image
				albumstable.append(
					albumsrow.append(
						albumscell.append(
							$imgtable)
						)
					);

				// Slide up
				$imgtable.css('margin-top', '+100px');
				$imgtable.animate({'margin-top': '-=100'}, 750, 'swing');

				if ( (album_index + 1) % 2 == 0 && 
							album_index < json.albums.length - 1 ) {
					albumsrow = $('<tr />');
				}
			}); // End of for-each-album
			$('#albums_table').append(albumstable);

			// Set up next set of albums to load
			if (json.after == '') {
				// No more albums to load
				$('#next').removeAttr('after')
					.html(json.total + ' albums loaded');
			} else {
				var remaining = json.total - json.index;
				$('#next').attr('after', json.after)
					.html(remaining + ' albums remaining');
				$('#albums_table').removeAttr('loading');
				scrollHandler();
			}
		});
	return true;
}
function loadNextAlbum() {
	if ($('#albums_table').attr('loading')) {
		// Already loading albums, or no more albums to load
		return;
	}
	if ( ! $('#next').attr('after') ) {
		// Already hit end of albums
		return;
	}
	$('#albums_table').attr('loading', 'true');
	$('#next').html( $('#next').html() )
		.append( $('<br>') )
		.append( $('<span />').html('loading...') );
	// Load next albums after a shot delay
	setTimeout( function() {
		loadAllAlbums($('#next').attr('after'), false);
	}, 500);
}


/////////////////////
// INFINITE SCROLLING

function scrollHandler() {
	// Heights
	var page     = $(document).height(); // Height of document
	var viewport = $(window).height();   // Height of viewing window
	var scroll   = $(document).scrollTop() || window.pageYOffset; // Scroll position (top)
	var remain = page - (viewport + scroll);
	if (viewport > page || // Viewport is bigger than entire page
	    remain < 300) {    // User has scrolled down far enough
		if (!window.location.hash || window.location.hash.indexOf('_') == -1) {
			// Viewing all albums
			loadNextAlbum();
		} else {
			// Viewing single album
			loadMoreImages();
		}
	}
}


//////////////////
// IMAGE DISPLAY

function loadImage($thumbnail) {
	// If the image type isn't supported, open in a new tab
	var unsupported = false;
	$.each(Array('.mp4', '.html'), function(i, extension) {
		var full = $thumbnail.attr('full');
		if (full.indexOf(extension) == full.length - extension.length) {
			window.open(full);
			unsupported = true;
			return;
		}
	});
	if (unsupported) { return; }

	// Dim background
	$('#bgimage')
		.stop()
		.fadeIn()
		.click( imageClickHandler );

	// Remove/create/show thumbnail
	$('#fgthumb')
		.stop()
		.hide()
		.remove();
	$('<img />')
		.attr('id', 'fgthumb')
		.hide()
		.appendTo( $(document.body) )
		.click(imageClickHandler)
		.load( function() { thumbLoadHandler($(this), $thumbnail); } )
		.attr('src', $thumbnail.attr('src')); // Start loading thumbnail
	
	return false;
}

// Return css dict for image expanded to fit the screen
function getFSDimensionsForImage($image) {
	var factor = Math.min(
			$(window).height() / $image.height(), 
			$(window).width()  / $image.width()
	);
	var th = parseInt($image.height() * factor) - 2;
	var tw = parseInt($image.width() * factor) - 4;
	var tt = Math.max(0, parseInt( ($(window).height() - th) / 2.0 ));
	var tl = Math.max(0, parseInt( ($(window).width() - tw) / 2.0 ));
	return {
		'top'    : tt - 2,
		'left'   : tl - 2,
		'height' : th + 'px',
		'width'  : tw + 'px',
	};
}

function thumbLoadHandler($thumb, $thumbnail) {
	$thumb.unbind('load');
	// Old thumbnail dimensions
	var oldDim = {
		'top'    : parseInt($thumbnail.position().top),
		'left'   : parseInt($thumbnail.position().left),
		'height' : parseInt($thumbnail.height()) + 'px',
		'width'  : parseInt($thumbnail.width()) + 'px',
	};
	// New thumbnail dimensions
	var newDim = getFSDimensionsForImage($thumb);
	$thumb
		// Store current location of thumbnail
		.css(oldDim)
		.css({
			'position' : 'fixed',
			'z-index': 45,
			'top' : oldDim['top'] - $(document).scrollTop(),
		})
		.animate( 
			newDim,
			{
				queue: false,
				duration: 300,
				easing: 'swing'
			}
		)
		.show();

	// Remove existing image
	$('#fgimage')
		.hide()
		.removeAttr('src')
		.remove();
	// Load the full-size image
	$image = $('<img />')
		.attr('id', 'fgimage')
		.hide()
		.appendTo( $(document.body) )
		.css({
			'position' : 'fixed',
			'z-index': 50,
		})
		.attr(oldDim)
		.css(oldDim)
		.css('top', oldDim['top'] - $(document).scrollTop())
		.click(imageClickHandler)
		.animate( 
			newDim,
			{
				duration: 300,
				easing: 'swing',
				queue: false,
				complete: function() { /*imageLoadHandler($thumb, 'animation');*/ }
			}
		)
		//.load(function() { imageLoadHandler($thumb, 'load') })
		.attr('src', $thumbnail.attr('full'))
		.show()
		.imagesLoaded( function() { imageLoadHandler($thumb, 'load') } );
}

function imageLoadHandler($thumb, loaded_from) {
	var $image = $('#fgimage');
	var top    = $thumb.position().top, 
	    left   = $thumb.position.left, 
	    width  = $thumb.width(), 
	    height = $thumb.height();
	$thumb.hide();
	if ($image.attr('already_loaded') == 'true') {
		return;
	}
	$image.attr('already_loaded', 'true');
	$image
		.css('height', 'auto')
		.css('width',  'auto');
	var newDim = getFSDimensionsForImage($image);
	$image
		.css('top', top)
		.css('left', left)
		.css('width',  width  + 'px')
		.css('height', height + 'px');
	$image
		.animate(
				newDim, 
				{
					queue: false,
					duration: 300,
					easing: 'swing',
					complete: function() {
						//$thumb.hide()
					},
				})
		.show();
}

function imageClickHandler() { // Hide the image
	$('#bgimage')
		.unbind('click')
		.fadeOut(100);
	$('#fgimage')
		.stop(true, false)
		.unbind('click')
		.unbind('load');
	$('#fgthumb')
		.stop(true, false)
		.unbind('click')
		.unbind('load');
	$('#fgthumb')
		.hide()
		.remove();
	var $fg = $('#fgimage');
	$fg
		.attr('stopping', 'true')
		.fadeOut(300)
		.animate( 
			{ 
				'top'    : $fg.attr('top') - $(document).scrollTop(),
				'left'   : $fg.attr('left'),
				'height' : $fg.attr('height'),
				'width'  : $fg.attr('width'),
			},
			{
				queue: false,
				duration: 300,
				easing: 'swing'
			},
			function() { 
				$fg
					.removeAttr('src')
					.hide();
			}
		);
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
	if (getCookie('rip_tos_v' + TOS_VERSION) === 'true') { return false; }
	// User hasn't agreed to TOS or verified age.
	$('#maintable').hide();
	$('#albums_table').attr('loading', 'true');
	var $tos = $('<div />')
		.append( $('<h1 />').html('Warning: This site may contain explicit content') )
		.addClass('warning')
		.attr('id', 'maindiv')
		.css('margin', '20px')
		.css('padding-top', '5px');
		
	$('<div />')
		.html(
			'This website may contain adult content which is not appropriate for persons under the age of 18.' +
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
	return true;
}

function i_agree() {
	setCookie('rip_tos_v' + TOS_VERSION, 'true');
	$('#maintable').show();
	$('#maindiv').hide();
	$('#albums_table').removeAttr('loading');
	init(); // Load the page
}

////////////////////////
// REPORTING

function showReportsToAdmin(album) {
	// Display list of reasons for reporting
	$('#report')
		.html('')
		.addClass('fontsmall red shadow');
	if (album.report_reasons.length == 0) {
		// No reports
		$('<span />')
			.html('no reports')
			.addClass('green')
			.css('padding-left', '5px')
			.appendTo( $('#report') );
	} else {
		// Show reports
		$('<div />')
			.addClass('shadow')
			.html('reports:')
			.appendTo( $('#report') );
		var reasonlist = $('<ol />');
		$.each(album.report_reasons, function(i, reasonattr) {
			var reason = reasonattr.reason || '[no reason given]';
			$('<div />')
				.append( $('<span />').html('ip: ' + reasonattr.user) )
				.append( $('<br>') )
				.append( $('<span />').html('reason: ' + reason) )
				.appendTo( 
					$('<li />').appendTo( reasonlist )
				);
		});
		$('#report').append( reasonlist );

		$('<a />')
			.html('clear reports')
			.attr('href', '')
			.addClass('orange bold underline space')
			.attr('album', album.album)
			.click( function() {
				clearReports($(this).attr('album'));
				return false;
			})
			.appendTo( $('#report') );
		$('<span />')
			.attr('id', 'report_clear_status')
			.addClass('green space')
			.css('padding-left', '10px')
			.appendTo( $('#report') );
	}
	if (album.user) {
		// Link to all albums ripped by user
		$('<a />')
			.html('view all albums ripped by ' + album.user)
			.attr('href', '#user=' + album.user)
			.attr('target', '_BLANK' + String(Math.random()))
			.addClass('white bold')
			.appendTo (
					$('<div />').addClass('space')
						.appendTo( $('#report') )
			);
	}
	
	// Show 'delete album' link
	var $adel = $('<a />') // delete link
		.html('delete album')
		.addClass('red bold underline')
		.attr('href', '')
		.attr('album', album.album)
		.click( function() {
				deleteAlbum( $(this).attr('album'), false );
				return false;
		});
	var $adelbl = $('<a />')
		.html('and blacklist')
		.addClass('black bold underline')
		.attr('href', '')
		.attr('album', album.album)
		.css('padding-left', '5px')
		.click( function() {
				deleteAlbum( $(this).attr('album'), true );
				return false;
		});
	var $sdel = $('<span />') // delete status
		.css('padding-left', '5px')
		.attr('id', 'delete_status');
	$('<div />')
		.addClass('space')
		.append($adel)
		.append($adelbl)
		.append($sdel)
		.appendTo( $('#report') );
	
	// Show 'delete all albums by user' link
	if (album.user != null) {
		var $delall = $('<a />')
			.html('delete all albums ripped by ' + album.user)
			.attr('href', '')
			.addClass('red bold underline')
			.attr('user', album.user)
			.click( function() {
				deleteAllAlbums( $(this).attr('user'), false );
				return false;
			});
		var $delallbl = $('<a />')
			.html('and blacklist all')
			.attr('href', '')
			.css('padding-left', '5px')
			.addClass('black bold underline')
			.attr('user', album.user)
			.click( function() {
				deleteAllAlbums( $(this).attr('user'), true );
				return false;
			});
		
		$('<div />')
			.addClass('space')
			.append($delall)
			.append($delallbl)
			.appendTo( $('#report') );

		// Temporary ban
		var atban = $('<a />')
			.html('temporarily ban ' + album.user)
			.addClass('orange bold underline')
			.attr('href', '')
			.attr('user', album.user)
			.click( function() {
				banUser($(this).attr('user'), 'temporary');
				return false;
			});
		var stban = $('<span />')
			.attr('id', 'ban_status_temporary')
			.css('padding-left', '5px');
		$('<div />')
			.addClass('space')
			.append(atban)
			.append(stban)
			.appendTo( $('#report') );
		// Permanent ban
		var apban = $('<a />')
			.html('permanently ban ' + album.user)
			.addClass('red bold underline')
			.attr('href', '')
			.attr('user', album.user)
			.click( function() {
				banUser($(this).attr('user'), 'permanent');
				return false;
			});
		var spban = $('<span />')
			.attr('id', 'ban_status_permanent')
			.css('padding-left', '5px');
		$('<div />')
			.addClass('space')
			.append(apban)
			.append(spban)
			.appendTo( $('#report') );
	} else {
		$('<div />')
			.html('unable to determine which user created this rip')
			.addClass('orange space')
			.appendTo( $('#report') );
	}
}

// Populates $stat with response depending on json response
// Returns True if request is handled as expected
function adminRequestHandler(json, $stat) {
	if (json.error) {
		$stat
			.html(json.error)
			.removeClass().addClass('red shadow');
	} else if (json.warning) {
		$stat
			.html(json.warning)
			.removeClass().addClass('orange shadow');
	} else if (json.ok) {
		$stat
			.html(json.ok)
			.removeClass().addClass('green shadow');
	} else {
		return false;
	}
	return true;
}

function report(album) {
	var reason = prompt("please enter the reason why this album should be reported", "enter reason here");
	if (reason == null || reason == '') {
		return false;
	}
	if (reason == "enter reason here") {
		$('#report')
			.html('you must enter a valid reason')
			.removeClass().addClass('red bold shadow');
		return false;
	}
	$('#report')
		.empty()
		.append(
			$('<img />')
				.attr('src', '../spinner_dark.gif')
				.css('border', 'none')
				.css('padding-right', '5px')
		);
	
	$.getJSON('view.cgi?report=' + album + '&reason=' + reason)
		.fail( adminJsonFailHandler )
		.done( function(json) { 
			adminRequestHandler(json, $('#report'))
		});

	return false;
}

function clearReports(album) {
	$.getJSON('view.cgi?clear_reports=' + album)
		.fail( adminJsonFailHandler )
		.done( function(json) { 
			adminRequestHandler(json, $('#report_clear_status'))
		});
	return false;
}

function deleteAlbum(album, blacklist) {
	$('#delete_status')
		.empty()
		.append(
			$('<img />')
				.attr('src', '../spinner_dark.gif')
				.css('border', 'none')
				.css('padding-right', '5px')
		);
	
	$.getJSON('view.cgi?delete=' + album + '&blacklist=' + blacklist)
		.fail( adminJsonFailHandler )
		.done( function(json) { 
			adminRequestHandler(json, $('#delete_status'))
		});
	return false;
}

function deleteAllAlbums(user, blacklist) {
	$('#delete_status')
		.empty()
		.append(
			$('<img />')
				.attr('src', '../spinner_dark.gif')
				.css('border', 'none')
				.css('padding-right', '5px')
		);
	
	$.getJSON('view.cgi?delete_user=' + user + '&blacklist=' + blacklist)
		.fail( adminJsonFailHandler )
		.done( function(json) { 
			if ( adminRequestHandler(json, $('#delete_status')) ) {
				return; // Handled error/warning/ok
			}
			if (json.deleted != null) {
				var delol = $('<ol />');
				$.each(json.deleted, function (i, deleted) {
					$('<ol />')
						.html(deleted)
						.appendTo(delol);
				});
				$('#delete_status')
					.removeClass().addClass('green shadow')
					.html('<br>deleted ' + json.deleted.length + ' files/directories from ' + json.user + ':')
					.append(delol);
			}
		});
	return false;
}

function banUser(user, length) {
	var reason = prompt("enter reason why user is being banned", "enter reason here");
	if (reason == null || reason == '') {
		return;
	}
	if (reason == "enter reason here") {
		$('#ban_status')
			.html('you must enter a reason')
			.removeClass().addClass('red bold shadow');
		return;
	}
	$('#ban_status')
		.empty()
		.append(
			$('<img />')
				.attr('src', '../spinner_dark.gif')
				.css('border', 'none')
				.css('padding-right', '5px')
		);
	$.getJSON('view.cgi?ban_user=' + user + '&reason=' + reason + '&length=' + length)
		.fail( adminJsonFailHandler )
		.done( function(json) { 
			adminRequestHandler(json, $('#ban_status_' + length))
		});
	return false;
}


//////////////////////
// ERROR HANDLING
function jsonFailHandler(jqxhr, textStatus, error) {
	$('#status_area').hide();
	// Append error to whatever area is visible
	$('#thumbs_area:visible, #albums_area:visible')
		.css('text-align', 'center')
		.append( $('<h1 />').html('error while loading album') )
		.append( $('<div />').html('status ' + jqxhr.status + ', ' + textStatus + ': "' + error + '"') )
		.append( $('<div />') // Error dump
			.addClass('fontsmall')
			.css('margin', '50px')
			.css('text-align', 'left')
			.append( $('<h3 />').html('response / stack trace:') )
			.append( $('<div />').html(jqxhr.responseText) )
		)
		.css('padding-bottom', '30px')
		.show();
	$('#next').html('');
	$('#albums_table').attr('loading', 'true');
}
function adminJsonFailHandler(x, s, e) {
	$('#report')
		.empty()
		.append( $('<h3 /> ').addClass('red bold').html('error while contacting server:') )
		.append( $('<div />').addClass('red')     .html('status:' + x.status) )
		.append( $('<div />').addClass('red')     .html(s + ': "' + e + '"') )
		.append( $('<div />').addClass('white left fontsmall').html(x.responseText) )
		.removeClass().addClass('red shadow');
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

///////////////////
// MISC
function truncate(text, split_size) { // Truncates text
	if (text.length > (split_size * 2) + 3) {
		text = text.substr(0, split_size) + "..." + text.substr(text.length-split_size);
	}
	return text;
}

$(document).ready(init);
