function gebi(id) { return document.getElementById(id); }
function dce(el)  { return document.createElement(el);  }

// CONSTANTS
var ALBUMS_AT_ONCE             = 6; // Number of albums to return per request
var ALBUM_PREVIEW_SIZE         = 4; // Number of thumbnails per album
var ALBUM_PREVIEW_IMAGE_BREAKS = 4; // Thumbnails per row (all-albums view)
var SINGLE_ALBUM_IMAGE_BREAKS  = 4; // Thumbnails per row (single-album view)
var IMAGES_PER_PAGE           = 12; // Thumbnails per page

// Executes when document has loaded
function init() {
	handleResize();
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
	gebi('albums_area').setAttribute('style', 'display: none');
	gebi('status_area').setAttribute('style', 'display: block');
	gebi('thumbs_area').setAttribute('style', 'display: block');
	if (start == undefined) start = 0;
	if (count == undefined) count = IMAGES_PER_PAGE;
	if (startOver == undefined || startOver) {
		try{
			gebi('thumbs_table').innerHTML = '';
		} catch (error) { }
	}
	var req = 'view.cgi';
	req += '?start=' + start;
	req += '&count=' + count;
	req += '&view=' + album;
	sendRequest(req, albumHandler);
	return true;
}

function albumHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
		return;
	}
	if (json.error != null) {
		throw new Error(json.error);
	} else if (json.album == null) {
		throw new Error("cannot find album");
	}
	var album = json.album;
	if (album.images.length == 0) {
		gebi('album_title').innerHTML = 'album not found';
		gebi('album_download_title').setAttribute('style', 'display: none');
		gebi('album_download').setAttribute(      'style', 'display: none');
		gebi('album_url_title').setAttribute(     'style', 'display: none');
		gebi('album_url').setAttribute(           'style', 'display: none');
		gebi('report').setAttribute(              'style', 'display: none');
		gebi('thumbs_area').setAttribute(         'style', 'display: none');
		gebi('next').innerHTML += '';
		return;
	}
	gebi('album_title').innerHTML = album.album + ' (' + album.total + ' images)';
	gebi('album_download').setAttribute('style', 'display: table-cell');
	gebi('album_url').setAttribute(     'style', 'display: table-cell');
	gebi('report').setAttribute(        'style', 'display: table-cell');
	gebi('thumbs_area').setAttribute(   'style', 'display: table');
	
	if (album.report_reasons != undefined) {
		// Display list of reasons for reporting
		var report = gebi('report');
		report.innerHTML = '';
		report.className = 'fontsmall red';
		if (album.report_reasons.length == 0) {
			var rspan = dce('span');
			rspan.innerHTML = 'no reports found';
			report.appendChild(rspan);
		} else {
			var rdiv = dce('div');
			rdiv.innerHTML = 'reports:';
			report.appendChild(rdiv);
			var rol = dce('ol');
			for (var i = 0; i < album.report_reasons.length; i++) {
				var user = album.report_reasons[i].user;
				var reason = album.report_reasons[i].reason;
				if (reason === '') {
					reason = '[no reason given]';
				}
				var uli = dce('li');
				var ulidiv = dce('div');
				ulidiv.innerHTML = 'ip: <a class="red underline" href="#user=' + user + '" target="_BLANK">' + user + '</a><br>';
				ulidiv.innerHTML += 'reason: ' + reason;
				uli.appendChild(ulidiv);
				rol.appendChild(uli);
			}
			report.appendChild(rol);

			var rclear = dce('a');
			rclear.className = 'orange bold underline space';
			rclear.href = 'javascript:void(0)';
			rclear.setAttribute('album', album.album);
			rclear.setAttribute('onclick', 'clearReports("' + album.album + '"); return false;');
			rclear.innerHTML = 'clear reports';
			report.appendChild(rclear);
			var rclears = dce('span');
			rclears.className = 'green space';
			rclears.setAttribute('style', 'padding-left: 10px;');
			rclears.setAttribute('id', 'report_clear_status');
			report.appendChild(rclears);
		}
		// Show user that uploaded the album
		if (album.user != null) {
			var udiv = dce('div');
			udiv.className = 'space';
			var ua = dce('a');
			ua.className = 'white bold';
			ua.href = '#user=' + album.user;
			ua.setAttribute('target', '_BLANK');
			ua.innerHTML = 'all albums uploaded by ' + album.user;
			udiv.appendChild(ua);
			report.appendChild(udiv);
		}
		// Show 'delete album' link
		var ddiv = dce('div');
		ddiv.className = 'space';
		var adel = dce('a');
		adel.className = 'red bold underline';
		adel.href = "javascript:void(0)";
		adel.setAttribute('onclick', 'deleteAlbum("' + album.album + '")');
		adel.innerHTML = 'delete album';
		ddiv.appendChild(adel);
		var sdel = dce('span');
		sdel.setAttribute('style', 'padding-left: 5px');
		sdel.setAttribute('id', 'delete_status');
		ddiv.appendChild(sdel);
		report.appendChild(ddiv);
		// Show 'delete all albums by user' link
		if (album.user != null) {
			var alldiv = dce('div');
			alldiv.className = 'space';
			var aall = dce('a');
			aall.className = 'red bold underline';
			aall.href = "javascript:void(0)";
			aall.setAttribute('onclick', 'deleteAllAlbums("' + album.user + '")');
			aall.innerHTML = 'delete all albums by ' + album.user;
			alldiv.appendChild(aall);
			report.appendChild(alldiv);

			var bandiv = dce('div');
			bandiv.className = 'space';
			var aban = dce('a');
			aban.className = 'red bold underline';
			aban.href = 'javascript:void(0)';
			aban.setAttribute('onclick', 'banUser("' + album.user + '")');
			aban.innerHTML = 'permanently ban ' + album.user;
			bandiv.appendChild(aban);
			var banspan = dce('span');
			banspan.setAttribute('id', 'ban_status');
			banspan.setAttribute('style', 'padding-left: 5px')
			bandiv.appendChild(banspan);
			report.appendChild(bandiv);
		} else {
			var errdiv = dce('div');
			errdiv.className = 'orange space';
			errdiv.innerHTML += 'unable to determine which user created this rip';
			report.appendChild(errdiv);
		}
	} else {
		// Show report link
		var areport = gebi('report_link');
		if (areport != null) {
			areport.href = "javascript:void(0)";
			areport.setAttribute('album', album.album);
			areport.setAttribute('onclick', 'report("' + album.album + '")');
		}
	}
	
	// .ZIP link
	var albuma = dce('a');
	albuma.className = 'download_box';
	albuma.href = album.archive;
	albuma.innerHTML = album.archive.replace('./', '');
	gebi('album_download').innerHTML = '';
	gebi('album_download').appendChild(albuma);
	
	// URL link
	var urla = dce('a');
	urla.className = 'bold';
	urla.href = album.url;
	urla.target = '_BLANK';
	urla.rel = 'noreferrer';
	urla.innerHTML = album.url;
	gebi('album_url').innerHTML = '';
	gebi('album_url').appendChild(urla);
	
	// Get URLs link
	var urlsa = dce('a');
	urlsa.className = 'download_box fontmed';
	urlsa.href = "javascript:void(0)";
	urlsa.innerHTML = 'get urls';
	urlsa.setAttribute('album', album.album);
	urlsa.album = album.album;
	urlsa.setAttribute('onclick', 'loadUrls(' + album.album + ')');
	urlsa.onclick = function() { loadUrls(this.album) }
	gebi('get_urls').innerHTML = '';
	gebi('get_urls').appendChild(urlsa);
	
	// Table to append thumbnails to
	var thumbtable = gebi('thumbs_table');

	var thumbrow = dce('tr');
	var images = album.images;
	for (var i = 0; i < images.length; i++) {
		var thumbtd = dce('td');
		thumbtd.className = 'image';
		thumbtd.setAttribute('style', 'height: 150px; width: 150px;');
		var thumba = dce('a');
		thumba.href = images[i].image;
		thumba.onclick = function() {
			return loadImage(this.href);
		};
		var thumbi = dce('img');
		thumbi.src = images[i].thumb;
		thumbi.setAttribute('style', 'height: 150px; width: 150px;');
		thumbi.setAttribute('style', 'visibility: hidden');
		thumbi.onload = function() {
			this.setAttribute('style', 'visibility: visible');
		};
		thumba.appendChild(thumbi);
		thumbtd.appendChild(thumba);
		thumbrow.appendChild(thumbtd);
		if ((i + 1) % SINGLE_ALBUM_IMAGE_BREAKS == 0 && i != images.length - 1) {
			thumbtable.appendChild(thumbrow);
			thumbrow = dce('tr');
		}
	}
	thumbtable.appendChild(thumbrow);
	
	albums_table.removeAttribute('loading');
	var next = gebi('next');
	if (album.start + album.count >= album.total) {
		next.innerHTML = album.total + ' images loaded';
		albums_table.setAttribute('loading', 'true');
	} else {
		next.setAttribute('album', album.album);
		next.setAttribute('image_index', (album.start + album.count));
		var remaining = album.total - (album.start + album.count);
		next.innerHTML = remaining + ' images remaining';
	}
	scrollHandler();
}

function loadMoreImages() {
	var albums = gebi('albums_table');
	if (albums.getAttribute('loading')) { 
		// Already loading
		return;
	}
	var al = next.getAttribute('album');
	var ii = next.getAttribute('image_index');

	// Load more images
	albums.setAttribute('loading', 'true');
	setTimeout(function() {
		gebi('next').innerHTML += '<br>loading...'; // Give them hope
	}, 150);
	setTimeout(function() {
		loadAlbum(al, ii, IMAGES_PER_PAGE, false);
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
	gebi('albums_area').setAttribute('style', 'display: block');
	gebi('status_area').setAttribute('style', 'display: none');
	gebi('thumbs_area').setAttribute('style', 'display: none');
	gebi('albums_table').setAttribute('loading', 'true');
	// Remove existing albums if needed
	if (startOver == undefined || startOver) { 
		gebi('albums_table').innerHTML = '';
	}
	sendRequest(getAllAlbumUrl(after), allAlbumsHandler);
	return true;
}

function allAlbumsHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	if (json.error != null) throw new Error("error: " + json.error);

	var maintable = dce('table');
	maintable.setAttribute('width', '100%');
	var mainrow = dce('tr');
	for (var a = 0; a < json.albums.length; a++) {
		var maintd = dce('td');
		maintd.setAttribute('valign', 'top');
		if (a % 2 == 0) {
			maintd.setAttribute('style', 'text-align: left;');
		} else {
			maintd.setAttribute('style', 'text-align: right; padding-left: 20px;');
		}
		maintd.setAttribute('width', '50%');
		var album = json.albums[a];
		var table = dce('table');
		table.className = 'page album clickable';
		table.setAttribute('id',album.album);
		table.setAttribute('album', album.album);
		table.setAttribute('show_album', 'true');
		table.setAttribute('width', '100%');
		table.setAttribute('onclick', 
			'if (this.getAttribute("show_album") === "true") { ' +
				'var u = window.location.href; ' + 
				'if (u.indexOf("#") >= 0) { ' + 
					'u = u.substring(0, u.indexOf("#")); ' + 
				'} ' + 
				'window.open(u + "#" + album.album)' +
			'}'
		);
		table.onclick = function() {
			if (this.getAttribute('show_album') === 'true' || this.album === 'true') {
				// Open albums in new tab
				var u = window.location.href;
				if (u.indexOf('#') >= 0) { 
					u = u.substring(0, u.indexOf('#'));
				}
				window.open(u + '#' + this.getAttribute('album'));
			}
		}
		var titletr = dce('tr');
		titletr.setAttribute('valign', 'top');
		var titletd = dce('td');
		titletd.className = 'all_album_title';
		titletd.setAttribute('colspan', ALBUM_PREVIEW_IMAGE_BREAKS);
		titletd.innerHTML = album.album + ' (' + album.total + ' images)';
		titletr.appendChild(titletd);
		table.appendChild(titletr);

		if (album.reports != undefined) {
			var rtr = dce('tr');
			rtr.setAttribute('valign', 'top');
			rtr.className = 'fontsmall orange bold';
			var rtd = dce('td');
			rtd.setAttribute('colspan', ALBUM_PREVIEW_IMAGE_BREAKS);
			rtd.setAttribute('style', 'margin: 0px; padding: 0px;');
			rtd.innerHTML = 'reports: ' + album.reports;
			rtr.appendChild(rtd);
			table.appendChild(rtr);
		}

		// Spacing so table doesn't resize when images load
		var spacetr = dce('tr');
		for (var i = 0; i < ALBUM_PREVIEW_IMAGE_BREAKS; i++) {
			var spacetd = dce('td');
			spacetd.setAttribute('style', 'width: 115px');
			spacetd.setAttribute('style', 'height: 0px');
			spacetr.appendChild(spacetd);
		}
		table.appendChild(spacetr);

		var imgrow = dce('tr');
		for (var i = 0; i < album.images.length; i++) {
			
			var imgtd = dce('td');
			imgtd.className = 'image_small';
			
			var imga = dce('a');
			imga.setAttribute('album', album.album);
			imga.href = album.images[i].image;
			imga.setAttribute('onclick', 'return loadImage(' + album.images[i].image + ')');
			imga.onclick = function() {
				return loadImage(this.href);
			}
			imga.setAttribute('onmouseover', 'gebi("' + album.album + '").removeAttribute("show_album")');
			imga.onmouseover = function() {
				gebi(this.getAttribute('album')).removeAttribute('show_album');
			}
			imga.setAttribute('onmouseout', 'gebi("' + album.album + '").setAttribute("show_album", "true")');
			imga.onmouseout = function() {
				gebi(this.getAttribute('album')).setAttribute('show_album', 'true');
			}
			
			var img = dce('img');
			img.className = 'image_small';
			img.src = album.images[i].thumb;
			img.setAttribute('style', 'visibility: hidden');
			img.onload = function() {
				this.setAttribute('style', 'visibility: visible');
				var w = parseInt(this.getAttribute('width'));
				if (w > 100) {
					this.setAttribute('width', w * 0.5);
				}
				this.onload = null;
				//this.setAttribute('style', 'display: inline');
			}
			
			imga.appendChild(img);
			imgtd.appendChild(imga);
			imgrow.appendChild(imgtd);
			if ((i + 1) % ALBUM_PREVIEW_IMAGE_BREAKS == 0 && i != album.images.length - 1) {
				table.appendChild(imgrow);
				imgrow = dce('tr');
			}
		}
		var spacetdh = dce('td');
		spacetdh.setAttribute('style', 'height: 105px');
		spacetdh.setAttribute('style', 'width: 0px');
		imgrow.appendChild(spacetdh);
		table.appendChild(imgrow);
		maintd.appendChild(table);
		mainrow.appendChild(maintd);
		if ((a + 1) % 2 == 0 && a < json.albums.length - 1) {
			maintable.appendChild(mainrow);
			mainrow = dce('tr');
		}
		maintable.appendChild(mainrow);
	}
	var albums_table = gebi('albums_table');
	albums_table.appendChild(maintable);
	albums_table.removeAttribute('loading');
	
	// "Next" button
	var next = gebi('next');
	if (json.after == '') {
		next.removeAttribute('after');
		next.innerHTML = json.total + ' albums loaded';
	} else {
		next.setAttribute('after', json.after);
		var remaining = json.total - json.index;
		next.innerHTML = remaining + ' albums remaining';
	}
	scrollHandler();
}
function loadNextAlbum() {
	var albums = gebi('albums_table');
	if (albums.getAttribute('loading')) { 
		// Already loading
		return;
	}
	
	var next = gebi('next');
	if (!next.getAttribute('after')) { 
		// Hit end of albums
		return; 
	}
	
	// Load next album
	albums.setAttribute('loading', 'true');
	next.innerHTML += '<br>loading...'; // Give them hope
	setTimeout(function() {
		loadAllAlbums(gebi('next').getAttribute('after'), false);
	}, 500);
}
	

/////////////////
// UPDATE

// Mark album as recently-viewed
function updateAlbum(album) {
	sendRequest('view.cgi?update=' + album, updateHandler);
}
function updateHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	if (json.error != null) throw new Error("error: " + json.error);
	if (json.date != null) {
		gebi('album_created').innerHTML = json.date;
	}
}

/////////////////////
// HELPER FUNCTIONS

// Create new XML/AJAX request object
function makeHttpObject() {
	try { return new XMLHttpRequest();
	} catch (error) {}
	try { return new ActiveXObject('Msxml2.XMLHTTP');
	} catch (error) {}
	try { return new ActiveXObject('Microsoft.XMLHTTP');
	} catch (error) {}
	throw new Error('could not create HTTP request object');
}

// Sends request, shoots request to handler if/when successful.
function sendRequest(url, handler) {
	var req = makeHttpObject();
	req.open('GET', url, true);
	req.send(null);
	req.onreadystatechange = function() {
		if (req.readyState == 4) {
			if (req.status == 200) {
				handler(req);
			} else {
				throw new Error('request status ' + req.status + ' for URL ' + url);
			}
		}
	}
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

/////////////////////
// WINDOW FUNCTIONS
window.onload = init;

//////////////////
// IMAGE DISPLAY

function loadImage(url) {
	var bg = document.getElementById('bgimage');
	var fg = document.getElementById('fgimage');
	
	fg.onload = function() {
		var w = window, d = document, e = d.documentElement, g = d.getElementsByTagName('body')[0],
				SCREEN_WIDTH  = w.innerWidth || e.clientWidth || g.clientWidth,
				SCREEN_HEIGHT = w.innerHeight|| e.clientHeight|| g.clientHeight;
		var fg = document.getElementById('fgimage');
		if (fg.src === '') { return; }
		var width  = fg.width,  height = fg.height; // Image width/height
		var swidth = SCREEN_WIDTH, sheight = SCREEN_HEIGHT; // Screen width/height
		if (width  > swidth)  { height = height * (swidth  / width);  width  = swidth;  }
		if (height > sheight) { width  = width  * (sheight / height); height = sheight; }
		var ileft = (swidth  / 2) - (width  / 2);
		var itop  = (sheight / 2) - (height / 2);
		fg.setAttribute('style', 'display: block; visibility: visible; left: ' + ileft + 'px; top: '  + itop  + 'px');
	}
	fg.onclick = function() {
		// hide it
		gebi('fgimage').setAttribute('style', 'display: none');
		gebi('bgimage').setAttribute('style', 'display: none');
		gebi('fgimage').src = '';
	}
	bg.setAttribute('style', 'display: block');
	bg.onclick = fg.onclick;
	
	fg.src = url;
	fg.alt = 'loading...';
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
	gebi('main_table').setAttribute('style', 'display: none');
	gebi('albums_table').setAttribute('loading', 'true');
	// User hasn't agreed to TOS or verified age.
	var maindiv = dce('div');
	maindiv.setAttribute('style', 'margin: 20px');
	maindiv.setAttribute('id', 'maindiv');
	var h1 = dce('h1');
	h1.innerHTML = 'Warning: This site contains explicit content';
	maindiv.appendChild(h1);

	var div = dce('div');
	div.className = 'warning';
	div.innerHTML  = 'This website contains adult content and is intended for persons over the age of 18.';
	div.innerHTML += '<p>';
	div.innerHTML += 'By entering this site, you agree to the following terms of use:';
	
	var ul = dce('ul');
	
	var li = dce('li');
	li.innerHTML = 'I am over eighteen years old.';
	ul.appendChild(li);
	
	li = dce('li');
	li.innerHTML = 'I will not use this site to download illegal material, or to acquire illegal material in any way.';
	ul.appendChild(li);
	
	li = dce('li');
	li.innerHTML = 'I will report illegal content to the site administrator immediately via reddit or email';
	ul.appendChild(li);
	
	li = dce('li');
	li.innerHTML = 'I will not hog the resources of this site, and will not rip more than 20 albums per day.';
	ul.appendChild(li);
	
	div.appendChild(ul);
	
	var agree = dce('input');
	agree.type = 'button';
	agree.value = 'Agree & Enter';
	agree.className = 'button';
	agree.setAttribute('onclick', 'i_agree()');
	agree.onclick = function() { i_agree(); };
	var disagree = dce('input');
	disagree.type = 'button';
	disagree.value = 'Leave';
	disagree.className = 'button';
	disagree.setAttribute('style', 'margin-left: 20px');
	disagree.setAttribute('onclick', 'i_disagree()');
	disagree.onclick = function() { i_disagree(); };
	div.appendChild(agree);
	div.appendChild(disagree);
	maindiv.appendChild(div);
	document.body.appendChild(maindiv);
	return true;
}

function i_agree() {
	setCookie('rip_tos_v' + TOS_VERSION, 'true');
	gebi('main_table').setAttribute('style', 'display: table');
	gebi('maindiv').setAttribute('style', 'display: none');
	gebi('albums_table').removeAttribute('loading');
	init();
}
function i_disagree() {
	window.location.href = 'about:blank';
}

function loadUrls(album) {
	gebi('get_urls').innerHTML = 'loading <img src="../spinner_dark.gif" style="border: none">';
	var url = 'view.cgi?urls=' + album;
	sendRequest(url, loadUrlsHandler);
	return false;
}
function loadUrlsHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	if (json.error != null) throw new Error("error: " + json.error);
	if (json.urls != null) {
		if (json.urls.length == 0) {
			// No urls found
			gebi('get_urls').innerHTML = 'no urls found';
			return;
		}
		var root = window.location.href;
		if (root.indexOf('#') != -1) {
			root = root.substring(0, root.indexOf('#'));
		}
		var out = '';
		for (var i = 0; i < json.urls.length; i++) {
			out += root + json.urls[i] + '<br>';
		}
		gebi('get_urls').setAttribute('style', 'font-size: 0.8em; padding-left: 20px;');
		gebi('get_urls').innerHTML = out;
	}
}

////////////////////////
// REPORTING

function report(album) {
	var reason = prompt("please enter the reason why this album should be reported", "enter reason here");
	if (reason == null || reason == '') {
		return;
	}
	if (reason == "enter reason here") {
		var rstat = gebi('report_status');
		rstat.className = 'red bold';
		rstat.innerHTML = 'you must enter a valid reason';
		return;
	}
	var url = 'view.cgi';
	url += '?report=' + album;
	url += '&reason=' + reason;
	gebi('report_status').innerHTML = '<img src="../spinner_dark.gif" style="border: none">&nbsp;reporting...';
	sendRequest(url, reportHandler);
	return false;
}
function reportHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	var rstat = gebi('report_status');
	if (json.error != null) {
		rstat.className = 'red';
		rstat.innerHTML = json.error;
	}
	else if (json.warning != null) {
		rstat.className = 'orange';
		rstat.innerHTML = json.warning;
	}
	else if (json.reported) {
		rstat.className = 'green';
		gebi('report_link').innerHTML = '';
		rstat.innerHTML = 'album has been reported';
	}
	else {
		rstat.innerHTML = 'unknown response';
	}
}
function clearReports(album) {
	var url = 'view.cgi?clear_reports=' + album;
	sendRequest(url, clearReportsHandler);
}
function clearReportsHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	var rstat = gebi('report_clear_status');
	if (json.error != null) {
		rstat.className = 'red';
		rstat.innerHTML = json.error;
	}
	else if (json.warning != null) {
		rstat.className = 'warning';
		rstat.innerHTML = json.warning;
	}
	else if (json.ok != null) {
		rstat.className = 'green';
		rstat.innerHTML = json.ok;
	}
}
function deleteAlbum(album) {
	gebi('delete_status').innerHTML = '<img src="../spinner_dark.gif" style="border: none">&nbsp;deleting...';
	var url = 'view.cgi?delete=' + album;
	sendRequest(url, deleteAlbumHandler);
}
function deleteAlbumHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	var dstat = gebi('delete_status');
	if (json.error != null) {
		dstat.className = 'red';
		dstat.innerHTML = json.error;
	}
	else if (json.warning != null) {
		dstat.className = 'warning';
		dstat.innerHTML = json.warning;
	}
	else if (json.ok != null) {
		dstat.className = 'green';
		dstat.innerHTML = json.ok;
	}
}
function deleteAllAlbums(user) {
	gebi('delete_status').innerHTML = '<img src="../spinner_dark.gif" style="border: none">&nbsp;deleting...';
	var url = 'view.cgi?delete_user=' + user;
	sendRequest(url, deleteUserHandler);
}
function deleteUserHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	var dstat = gebi('delete_status');
	if (json.error != null) {
		dstat.className = 'red';
		dstat.innerHTML = json.error;
	}
	else if (json.deleted != null) {
		dstat.className = 'green';
		var out = 'deleted ' + json.deleted.length + ' files/directories from ' + json.user + ':';
		out += '<ol>';
		for (var i = 0; i < json.deleted.length; i++) {
			out += '<li>' + json.deleted[i];
		}
		out += '</ol>';
		dstat.innerHTML = out;
	}
}
function banUser(user) {
	var reason = prompt("enter reason why user is being banned", "enter reason here");
	if (reason == null || reason == '') {
		return;
	}
	if (reason == "enter reason here") {
		var rstat = gebi('ban_status');
		rstat.className = 'red bold';
		rstat.innerHTML = 'you must enter a reason';
		return;
	}
	gebi('ban_status').innerHTML = '<img src="../spinner_dark.gif" style="border: none">&nbsp;banning...';
	var url = 'view.cgi?ban_user=' + user + '&reason=' + reason;
	sendRequest(url, banUserHandler);
}
function banUserHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	var dstat = gebi('ban_status');
	if (json.error != null) {
		dstat.className = 'red';
		dstat.innerHTML = json.error;
	}
	else if (json.banned != null) {
		dstat.className = 'green';
		dstat.innerHTML = 'banned ' + json.banned + ' forever!';
	}
}

////////////////
// BOTTOM BAR
function handleResize() {
	var bb = gebi('bottom_bar');
	var t = document.documentElement.clientHeight - bb.clientHeight;
	bb.setAttribute('style', 'top: ' + t + 'px');
}
window.onresize = handleResize;

