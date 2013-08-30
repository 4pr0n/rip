function gebi(id) { return document.getElementById(id); }

var SINGLE_ALBUM_IMAGE_BREAKS = 4;
var ALBUM_PREVIEW_SIZE = 12;
var ALBUMS_AT_ONCE = 6;
var IMAGES_PER_PAGE = 20;

var CURRENT_URL = ''; //String(window.location);
// Executes when document has loaded
function init() {
	var url = String(window.location);
	var i = url.indexOf('#');
  if (i >= 0 && i != url.length - 1) {
		if (url.indexOf('#start=') == i) {
			// Viewing page of All Albums
			var start = url.substring(i + 7, url.length);
			loadAllAlbums(parseInt(start));
		} else {
			// Viewing specific album
			var album = url.substring(url.lastIndexOf('#')+1);
			var s = album.indexOf('&start=');
			var start = 0;
			if (s >= 0) {
				start = parseInt(album.substring(s + 7, album.length));
				album = album.substring(0, s);
			}
			console.log('loadAlbum(' + album + ', ' + start + ')');
			loadAlbum(album, start)
		}
	} else {
		// Viewing all albums
		loadAllAlbums();
	}
}

function loadAlbum(album, start, count) {
	if (!isNewPage()) { return true; }
	gebi('albums_area').style.display = "none";
	gebi('status_area').style.display = "block";
	gebi('thumbs_area').style.display = "block";
	gebi('main_table').style.width = "auto";
	if (start == undefined) start = 0;
	if (count == undefined) count = IMAGES_PER_PAGE;
	var req = 'view.cgi';
	req += '?start=' + start;
	req += '&count=' + count;
	req += '&view=' + album;
	console.log(req);
	sendRequest(req, albumHandler);
	return true;
}

function isNewPage() {
	if (CURRENT_URL === String(window.location)) { console.log('not a new page ' + CURRENT_URL); return false; }
	CURRENT_URL = String(window.location);
	return true;
}
	

function albumHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		console.log('unable to parse response:\n' + req.responseText);
		throw new Error('unable to parse response:\n' + req.responseText);
		return;
	}
	if (json.error != null) {
		throw new Error(json.error);
	} else if (json.album == null) {
		throw new Error("cannot find album");
	}
	var album = json.album;
	gebi('album_title').innerHTML = album.album + ' (' + album.total + ' images)';
	gebi('album_download').innerHTML = '<a class="download_box" href="' + album.archive + '">' + album.archive + '</a>';
	var images = album.images;
	var out = '<tr><td>&nbsp;</td></tr><tr>';
	for (var i = 0; i < images.length; i++) {
		out += '<td class="image">';
		out += '<a href="' + images[i].image + '" onclick="return loadImage(\'' + images[i].image + '\')">';
		out += '<img src="' + images[i].thumb + '" onload="this.style.display=\'inline\';">';
		out += '</a>';
		out += '</td>';
		if ((i + 1) % SINGLE_ALBUM_IMAGE_BREAKS == 0 && i != images.length - 1) {
			out += '</tr><tr>';
		}
	}
	out = '<tr>' + out + '</tr>';
	gebi('thumbs_table').innerHTML = out;
	
	gebi('nav_info').innerHTML = 'images ' + (album.start + 1) + '-' + (album.start + album.count) + ' of ' + album.total;
	var back = gebi('back');
	if (album.start > 0) {
		back.style.visibility = 'visible';
		back.onclick = function() { 
			window.location.hash = album.album + '&start=' + (album.start - IMAGES_PER_PAGE);
			loadAlbum(album.album, (album.start - IMAGES_PER_PAGE))
		};
	} else {
		back.style.visibility = 'hidden';
	}
	var next = gebi('next');
	if (album.start + IMAGES_PER_PAGE < album.total) {
		next.style.visibility = 'visible';
		next.onclick = function() { 
			window.location.hash = album.album + '&start=' + (album.start + IMAGES_PER_PAGE);
			loadAlbum(album.album, (album.start + IMAGES_PER_PAGE))
		};
	} else {
		next.style.visibility = 'hidden';
	}
}

function getAllAlbumUrl(start) {
	var req = 'view.cgi';
	req += '?view_all=true';
	req += '&start='   + start;
	req += '&count='   + ALBUMS_AT_ONCE;
	req += '&preview=' + ALBUM_PREVIEW_SIZE;
	return req;
}

function loadAllAlbums(start) {
	if (!isNewPage()) { return true; }
	gebi('albums_area').style.display = "block";
	gebi('status_area').style.display = "none";
	gebi('thumbs_area').style.display = "none";
	gebi('main_table').style.width = "100%";
	if (start == undefined) start = 0;
	window.location.hash = 'start=' + start;
	console.log(getAllAlbumUrl(start));
	sendRequest(getAllAlbumUrl(start), allAlbumsHandler);
	return true;
}

function allAlbumsHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		console.log('unable to parse response:\n' + req.responseText);
		throw new Error('unable to parse response:\n' + req.responseText);
		return;
	}
	if (json.error != null) throw new Error("error: " + json.error);
	var out = '';
	out += '<table width="100%"><tr>';
	for (var a = 0; a < json.albums.length; a++) {
		if (a % 2 == 0) {
			out += '<td valign="top" style="text-align: left;">';
		} else {
			out += '<td valign="top" style="text-align: right; padding-left: 20px;">';
		}
		album = json.albums[a];
		out += '<table class="page"><tr><td class="section_title" colspan="20">';
		out += '<a class="album_title" href="#' + album.album + '" onclick="console.log(\'wtf\'); loadAlbum(\'' + album.album + '\');">';
		out += '' + album.album + ' (' + album.total + ' images)';
		out += '</a><br>';
		out += '</td></tr><tr>';
		for (var i = 0; i < album.images.length; i++) {
			var image = album.images[i].image;
			var thumb = album.images[i].thumb;
			out += '<td class="image">';
			out += '<a href="' + image + '" onclick="return loadImage(\'' + image + '\')">';
			out += '<img src="' + thumb + '" onload="if (this.width > 100) this.width*=0.5; this.onload=null; this.style.display=\'inline\';">';
			out += '</a>';
			out += '</td>';
			if ((i + 1) % SINGLE_ALBUM_IMAGE_BREAKS == 0 && i != album.images.length - 1) {
				out += '</tr><tr>';
			}
		}
		out += '</tr></table>';
		out += '</td>';
		if ((a + 1) % 2 == 0 && a < json.albums.length - 1) {
			out += '</tr><tr>';
		}
	}
	out += '</tr></table>';
	gebi('albums_table').innerHTML = out;
	
	gebi('nav_info').innerHTML = 'albums ' + (json.start + 1) + '-' + (json.start + json.albums.length) + ' of ' + json.total;
	var back = gebi('back');
	if (json.start > 0) {
		back.onclick = function() { loadAllAlbums(json.start - ALBUMS_AT_ONCE) };
		back.onclick = function() { 
			window.location.hash = 'start=' + (json.start - ALBUMS_AT_ONCE);
			loadAllAlbums(json.start - ALBUMS_AT_ONCE)
		};
		back.style.visibility = 'visible';
	} else {
		back.style.visibility = 'hidden';
	}
	var next = gebi('next');
	if (json.start + IMAGES_PER_PAGE < json.total) {
		next.onclick = function() { loadAllAlbums(json.start + ALBUMS_AT_ONCE) };
		next.onclick = function() { 
			window.location.hash = 'start=' + (json.start + ALBUMS_AT_ONCE);
			loadAllAlbums(json.start + ALBUMS_AT_ONCE) 
		};
		next.style.visibility = 'visible';
	} else {
		next.style.visibility = 'hidden';
	}
	
}

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
				console.log('request status ' + req.status + ' for URL ' + url);
				throw new Error('request status ' + req.status + ' for URL ' + url);
			}
		}
	}
}

function updateAlbum(album) {
	sendRequest('view.cgi?update=' + album, updateHandler);
}

function updateHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		console.log('unable to parse response:\n' + req.responseText);
		throw new Error('unable to parse response:\n' + req.responseText);
		return;
	}
	if (json.error != null) throw new Error("error: " + json.error);
	if (json.date != null) {
		gebi('album_created').innerHTML = json.date;
	}
	//window.location.reload(true);
}

window.onload = init;

window.onpopstate = function(event) {
	init();
};

var w = window,
		d = document,
		e = d.documentElement,
		g = d.getElementsByTagName('body')[0],
		SCREEN_WIDTH  = w.innerWidth || e.clientWidth || g.clientWidth,
		SCREEN_HEIGHT = w.innerHeight|| e.clientHeight|| g.clientHeight;
/* Image functions */
var bg = document.getElementById('bgimage');
var fg = document.getElementById('fgimage');
fg.onload = function() {
	if (bg.style.display === 'none') { return; }
	var width  = fg.width;
	var height = fg.height;
	var swidth = SCREEN_WIDTH;
	var sheight = SCREEN_HEIGHT;
	if (width  > swidth)  { height = height * (swidth  / width);  width  = swidth; }
	if (height > sheight) { width  = width  * (sheight / height); height = sheight; }
	fg.style.left = ((swidth / 2) - (width / 2)) + 'px';
	fg.style.top = ((sheight / 2) - (height / 2)) + 'px';
	fg.style.display = 'block';
}
fg.onclick = function() {
	// hide it
	fg.style.display = 'none';
	bg.style.display = 'none';
	fg.src = '';
}
bg.onclick = fg.onclick;

function loadImage(url) {
	bg.style.display = 'block';
	fg.src = url;
	fg.alt = 'loading...';
	return false;
}
