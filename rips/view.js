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
	if (window.location.hash !== '' && window.location.hash.indexOf('_') >= 0) {
		// Viewing specific album
		loadAlbum(window.location.hash.substring(1))
	} else {
		// Viewing all albums
		loadAllAlbums();
	}
	window.onscroll = scrollHandler;
	
	if (String(window.location.hash) === '#report') {
		setTimeout(function() {
			window.location.reload(true);
		}, 30000);
	}
}

//////////////////////
// SINGLE ALBUM

function loadAlbum(album, start, count, startOver) {
	if (album == null) { return; }
	$('#albums_area').hide();
	$('#status_area').css('display', 'block');
	$('#thumbs_area').css('display', 'block');
	if (start == undefined) start = 0;
	if (count == undefined) count = IMAGES_PER_PAGE;
	if (startOver == undefined || startOver) {
		try{
			$('#thumbs_table').html('');
		} catch (error) { }
	}
	var req = 'view.cgi';
	req += '?start=' + start;
	req += '&count=' + count;
	req += '&view=' + album;
	$.getJSON(req, function(json) {

		if (json.error != null) {
			throw new Error(json.error);
		} else if (json.album == null) {
			throw new Error("cannot find album");
		}
		var album = json.album;
		if (album.images.length == 0) {
			$('#album_title').html('album not found');
			$('#album_download_title').hide();
			$('#album_download').hide();
			$('#album_url_title').hide();
			$('#album_url').hide();
			$('#report').hide();
			$('#thumbs_area').hide();
			return;
		}
		$('#album_title').html(album.album + ' (' + album.total + ' images)');
		$('#album_download').css('display', 'table-cell');
		$('#album_url').css(     'display', 'table-cell');
		$('#report').css(        'display', 'table-cell');
		$('#thumbs_area').css(   'display', 'table');
		
		if (album.report_reasons != undefined) {
			showReportsToAdmin(album);
		} else if ( $('#report').html().indexOf('delete') == -1 ) {
			// Show report link
			$('<a />')
				.html('report this album')
				.addClass('bold red')
				.attr('href', '')
				.attr('album', album.album)
				.click(function() {
					report($(this).attr('album'))
					return false;
				})
				.appendTo( $('#report').html('') );
		}
		
		// .ZIP link
		$('<a />')
			.html(album.archive.replace('./', ''))
			.attr('href', album.archive)
			.addClass('download_box')
			.appendTo( $('#album_download').html('') );

		// URL link
		$('#album_url').empty();
		$('<a />')
			.html(album.url)
			.attr('href', album.url)
			.addClass('bold')
			.attr('target', '_BLANK')
			.attr('rel', 'noreferrer')
			.appendTo( $('#album_url') );
		
		// Get URLs link
		$('#get_urls').empty();
		$('<a />')
			.html('get urls')
			.addClass('download_box')
			.attr('href', 'urls_raw.cgi?album=' + album.album)
			.attr('target', '_BLANK')
			.appendTo( $('#get_urls') );
		
		// Append thumbnails to table in rows
		var thumbrow = $('<tr />');
		$.each(album.images, function(i, image) {
			var thumbtd = $('<td />')
				.addClass('image')
				.css('height', '150px')
				.css('width',  '150px');
			
			var thumba = $('<a />')
				.attr('href', image.image)
				.click(function() {
					return loadImage( $(this).attr('href') );
				});
			
			var thumbi = $('<img />')
				.attr('src', image.thumb)
				.css('min-height', '150px')
				.css('min-width',  '150px')
				.css('visibility', 'hidden')
				.load( function() {
					$(this).css('visibility', 'visible');
				})
				.appendTo(thumba);
			thumbtd.append(thumba)
				.appendTo(thumbrow);
			if ((i + 1) % SINGLE_ALBUM_IMAGE_BREAKS == 0 && i != album.images.length - 1) {
				$('#thumbs_table').append(thumbrow);
				thumbrow = $('<tr />');
			}
			
		});
		$('#thumbs_table').append(thumbrow);
		
		// Set the next chunk of albums to retrieve
		if (album.start + album.count >= album.total) {
			$('#next').html(album.total + ' images loaded');
			$('albums_table').attr('loading', 'true');
		} else {
			var remaining = album.total - (album.start + album.count);
			$('#next').attr('album', album.album)
				.attr('image_index', album.start + album.count)
				.html(remaining + ' images remaining');
			$('#albums_table').removeAttr('loading');
		}
		scrollHandler();
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
		$('#next').html('<br>loading...'); // Give them hope
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
	if (hash === '') {
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
	$('#albums_area').css('display', 'block');
	$('#status_area').css('display', 'none');
	$('#thumbs_area').css('display', 'none');
	$('#albums_table').attr('loading', 'true');
	
	// Remove existing albums if needed
	if (startOver == undefined || startOver) { 
		$('#albums_table').html('');
	}
	$.getJSON(getAllAlbumUrl(after), function(json) {
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
				
			var imgtable = $('<table />')
				.addClass('page album clickable')
				.css('width', '100%')
				.attr('id', album.album)
				.attr('show_album', 'true')
				.attr('album', album.album)
				.click( function() {
					// Check if click should open album (not on an image)
					if ($(this).attr('show_album') === 'true') {
						window.open($(location).attr('pathname') + '#' + $(this).attr('album'));
					}
				});
			
			// Show title and number of images
			var title = $('<tr />')
				.css('vertical-align', 'top')
				.append( $('<td />')
					.addClass('all_album_title')
					.attr('colspan', ALBUM_PREVIEW_IMAGE_BREAKS)
					.html(album.album + ' (' + album.total + ') images)')
				)
				.appendTo(imgtable);
			
			if (album.reports) {
				// Display number of reports on album
				$('<tr />')
					.css('vertical-align', 'top')
					.addClass('fontsmall orange bold')
					.append( 
							$('<td />')
								.attr('colspan', ALBUM_PREVIEW_IMAGE_BREAKS)
								.css('margin',  '0px')
								.css('padding', '0px')
								.html('reports: ' + album.reports)
							)
					.appendTo(imgtable);
			}

			var imgrow = $('<tr />');
			// Iterate over every image in album
			$.each(album.images, function(image_index, image) {
				var imga = $('<a />')
					.attr('href', image.image)
					.attr('album', album.album)
					.click( function() {
						return loadImage($(this).attr('href'));
					})
					.mouseover( function() {
						$('#' + $(this).attr('album')).removeAttr('show_album');
					})
					.mouseout( function() {
						$('#' + $(this).attr('album')).attr('show_album', 'true');
					});
				var imgi = $('<img />')
					.addClass('image_small')
					.attr('src', image.thumb)
					.css('visibility', 'hidden')
					.load( function() {
						var w = parseInt($(this).attr('width'));
						$(this).css('visibility', 'visible')
							.css('width', w > 100 ? w * 0.5 : w) // Resize to small thumb if needed
							.attr('onload', '').unbind('load'); // Prevent future loads from resizing
					})
					.appendTo(imga);
					
				$('<td />')
					.addClass('image_small')
					.append(imga)
					.appendTo(imgrow);
				if ( (image_index + 1) % ALBUM_PREVIEW_IMAGE_BREAKS == 0 && 
				      image_index != album.images.length - 1 ) {
					imgtable.append(imgrow);
					imgrow = $('<tr />');
				}
				imgtable.append(imgrow);
			}); // End of for-each-image
			albumstable.append(
				albumsrow.append(
					albumscell.append(
						imgtable)
					)
				);
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
		}
		scrollHandler();
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


/////////////////
// UPDATE

// Mark album as recently-viewed
function updateAlbum(album) {
	$.getJSON('view.cgi?update=' + album, function(json) {
		if (json.error != null) throw new Error("error: " + json.error);
		if (json.date != null) {
			$('#album_created').html(json.date);
		}
	});
}

/////////////////////
// INFINITE SCROLLING

function scrollHandler() {
	var page   = document.documentElement.scrollHeight;
	var client = document.documentElement.clientHeight;
	var scroll = document.documentElement.scrollTop || window.pageYOffset;
	var remain = (page - client) - scroll;
	if (remain < 200) {
		if (window.location.hash === '' || window.location.hash.indexOf('_') == -1) {
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

function loadImage(url) {
	var fg = $('#fgimage');
	
	var image_click = function() {
		// hide it
		$('#fgimage').hide()
			.attr('src', '');
		$('#bgimage').hide();
	};
	fg.load( function() {
		if ($(this).attr('src') === '') { return; }
		var w = window, d = document, e = d.documentElement, g = d.getElementsByTagName('body')[0],
				SCREEN_WIDTH  = w.innerWidth || e.clientWidth || g.clientWidth,
				SCREEN_HEIGHT = w.innerHeight|| e.clientHeight|| g.clientHeight;
		var width  = this.width, height = this.height;
		var swidth = SCREEN_WIDTH, sheight = SCREEN_HEIGHT; // Screen width/height
		if (width  > swidth)  { 
			height = height * (swidth  / width);  width  = swidth;
		}
		if (height > sheight) { 
			width  = width  * (sheight / height); height = sheight;
		}
		var ileft = (swidth  / 2) - (width  / 2);
		var itop  = (sheight / 2) - (height / 2);
		$(this).css('display', 'block')
			.css('visibility', 'visible')
			.css('left', ileft + 'px')
			.css('top', itop  + 'px');
		})
		.attr('src', url)
		.attr('alt', 'loading')
		.click(image_click);
	
	var bg = $('#bgimage');
	$('#bgimage').show()
		.click( image_click );
	
	return false;
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
	$('#main_table').hide();
	$('#albums_table').attr('loading', 'true');
	var maindiv = $('<div />')
		.addClass('warning')
		.css('margin', '20px')
		.attr('id', 'maindiv');

	$('<h1 />').html('Warning: This site contains explicit content')
			.appendTo(maindiv);
	$('<div />')
		.html('This website contains adult content and is intended for persons over the age of 18.<p>By entering this site, you agree to the following terms of use:')
		.appendTo(maindiv);
	
	var ul = $('<ul />');
	$('<li />')
		.html('I am over eighteen years old')
		.appendTo(ul);
	$('<li />')
		.html('I will not use this site to download illegal material, or to acquire illegal material in any way.')
		.appendTo(ul);
	$('<li />')
		.html('I will report illegal content to the site administrator immediately via reddit or email')
		.appendTo(ul);
	$('<li />')
		.html('I will not hog the resources of this site, and will not rip more than 20 albums per day.')
		.appendTo(ul);
	maindiv.append(ul);
	
	var lowerdiv = $('<div />');
	$('<input />')
		.attr('type', 'button')
		.attr('value', 'Agree & Enter')
		.addClass('button')
		.click( function() {
			i_agree();
		})
		.appendTo(lowerdiv);
	$('<input />')
		.attr('type', 'button')
		.attr('value', 'Leave')
		.css('margin-left', '30px')
		.addClass('button')
		.click( function() {
			i_disagree();
		})
		.appendTo(lowerdiv);
	maindiv.append(lowerdiv);
	$(document.body).append(maindiv);
	return true;
}

function i_agree() {
	setCookie('rip_tos_v' + TOS_VERSION, 'true');
	$('#main_table').show();
	$('#maindiv').hide();
	$('#albums_table').removeAttr('loading');
	init(); // Load the page
}
function i_disagree() {
	window.location.href = 'about:blank';
}

////////////////////////
// REPORTING

function showReportsToAdmin(album) {
	// Display list of reasons for reporting
	$('#report')
		.html('')
		.addClass('fontsmall red');
	if (album.report_reasons.length == 0) {
		// No reports
		$('<span />')
			.html('no reports')
			.appendTo( $('#report') );
	} else {
		// Show reports
		$('<div />')
			.html('')
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
			.html('all albums ripped by ' + album.user)
			.attr('href', '#user=' + album.user)
			.attr('target', '_BLANK')
			.addClass('white bold')
			.appendTo (
					$('<div />').addClass('space')
						.appendTo( $('#report') )
			);
	}
	
	// Show 'delete album' link
	var adel = $('<a />') // delete link
		.html('delete album')
		.addClass('red bold underline')
		.attr('href', '')
		.attr('album', album.album)
		.click( function() {
				deleteAlbum( $(this).attr('album') );
				return false;
		});
	var sdel = $('<span />') // delete status
		.css('padding-left', '5px')
		.attr('id', 'delete_status');
	$('<div />')
		.addClass('space')
		.append(adel)
		.append(sdel)
		.appendTo( $('#report') );
	
	// Show 'delete all albums by user' link
	if (album.user != null) {
		$('<a />')
			.html('delete all albums ripped by ' + album.user)
			.attr('href', '')
			.addClass('red bold underline')
			.attr('user', album.user)
			.click( function() {
				deleteAllAlbums( $(this).attr('user') );
				return false;
			})
			.appendTo( 
				$('<div />').addClass('space')
					.appendTo( $('#report') )
			);

		var aban = $('<a />')
			.html('permanently ban ' + album.user)
			.addClass('red bold underline')
			.attr('href', '')
			.attr('user', album.user)
			.click( function() {
				banUser($(this).attr('user'));
				return false;
			});
		var sban = $('<span />')
			.attr('id', 'ban_status')
			.css('padding-left', '5px');
		$('<div />')
			.addClass('space')
			.append(aban)
			.append(sban)
			.appendTo( $('#report') );
	} else {
		$('<div />')
			.html('unable to determine which user created this rip')
			.addClass('orange space')
			.appendTo( $('#report') );
	}
}

function report(album) {
	var reason = prompt("please enter the reason why this album should be reported", "enter reason here");
	if (reason == null || reason == '') {
		return false;
	}
	if (reason == "enter reason here") {
		$('#report')
			.html('you must enter a valid reason')
			.addClass('red bold');
		return false;
	}
	$('<img />')
		.attr('src', '../spinner_dark.gif')
		.css('border', 'none')
		.css('padding-right', '5px')
		.appendTo( $('#report') );
	
	$.getJSON('view.cgi?report=' + album + '&reason=' + reason, function(json) {
		if (json.error) {
			$('#report')
				.html(json.error)
				.addClass('red');
		
		} else if (json.warning) {
			$('#report')
				.html(json.warning)
				.addClass('orange');
		} else if (json.reported) {
			$('#report')
				.html('album has been reported')
				.addClass('green');
		} else {
			$('#report')
				.html('unexpected response')
				.addClass('red');
		}
	});
	return false;
}

function clearReports(album) {
	$.getJSON('view.cgi?clear_reports=' + album, function(json) {
		if (json.error != null) {
			$('#report_clear_status')
				.addClass('red')
				.html(json.error);
		}
		else if (json.warning != null) {
			$('#report_clear_status')
				.addClass('warning')
				.html(json.warning);
		}
		else if (json.ok != null) {
			$('#report_clear_status')
				.addClass('green')
				.html(json.ok);
		}
	});
	return false;
}

function deleteAlbum(album) {
	$('<img />')
		.attr('src', '../spinner_dark.gif')
		.css('border', 'none')
		.css('padding-right', '5px')
		.appendTo( $('#delete_status') );
	
	$.getJSON('view.cgi?delete=' + album, function(json) {
		if (json.error != null) {
			$('#report_clear_status')
				.addClass('red')
				.html(json.error);
		}
		else if (json.warning != null) {
			$('#report_clear_status')
				.addClass('warning')
				.html(json.warning);
		}
		else if (json.ok != null) {
			$('#report_clear_status')
				.addClass('green')
				.html(json.ok);
		}
	});
	return false;
}

function deleteAllAlbums(user) {
	$('<img />')
		.attr('src', '../spinner_dark.gif')
		.css('border', 'none')
		.css('padding-right', '5px')
		.appendTo( $('#delete_status') );
	
	$.getJSON('view.cgi?delete_user=' + user, function(json) {
		if (json.error != null) {
			$('#report_clear_status')
				.addClass('red')
				.html(json.error);
		}
		else if (json.deleted != null) {
			var delol = $('<ol />');
			$.each(json.deleted, function (i, deleted) {
				$('<ol />')
					.html(deleted)
					.appendTo(delol);
			});
			$('#delete_status')
				.append( $('<br>') )
				.html('deleted ' + json.deleted.length + ' files/directories from ' + json.user + ':')
				.append(delol);
		}
	});
	return false;
}

function banUser(user) {
	var reason = prompt("enter reason why user is being banned", "enter reason here");
	if (reason == null || reason == '') {
		return;
	}
	if (reason == "enter reason here") {
		$('#ban_status')
			.html('you must enter a reason')
			.addClass('red bold');
		return;
	}
	$('<img />')
		.attr('src', '../spinner_dark.gif')
		.css('border', 'none')
		.css('padding-right', '5px')
		.appendTo( $('#delete_status') );
	$.getJSON('view.cgi?ban_user' + user + '&reason=' + reason, function(json) {
		if (json.error != null) {
			$('#ban_status')
				.addClass('red')
				.html(json.error);
		}
		else if (json.banned != null) {
			$('#ban_status')
				.addClass('green')
				.html('banned ' + json.banned + ' forever!');
		}
	});
	return false;
}

////////////////
// BOTTOM BAR
$(window).on('load resize', function() {
	var bb = $('#bottom_bar');
	if (!bb) { return; }
	var t = document.documentElement.clientHeight - parseInt(bb.height());
	bb.css('top', t + 'px');
});

$(document).ready( function() {
	init();
});
