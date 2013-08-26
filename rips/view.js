function gebi(id) { return document.getElementById(id); }

var SINGLE_ALBUM_IMAGE_BREAKS = 10;
var ALBUM_PREVIEW_SIZE = 10;
var ALBUMS_AT_ONCE = 5;
var IMAGES_PER_PAGE = 20;

// Executes when document has loaded
function init() {
	var url = String(window.location);
  if (url.lastIndexOf('#') >= 0 && url.lastIndexOf('#') != url.length - 1) {
		// Viewing specific album
		gebi('albums_area').style.display = "none";
		gebi('status_area').style.display = "block";
		gebi('thumbs_area').style.display = "block";
    var album = unescape(url.substring(url.lastIndexOf('#')+1));
		loadAlbum(album)
	
	} else {
		// Viewing all albums
		gebi('albums_area').style.display = "block";
		gebi('status_area').style.display = "none";
		gebi('thumbs_area').style.display = "none";
		loadAllAlbums();
	}
}

function loadAlbum(album, start, count) {
	if (start == undefined) start = 0;
	if (count == undefined) count = IMAGES_PER_PAGE;
	var req = 'view.cgi';
	req += '?start=' + start;
	req += '&count=' + count;
	req += '&view=' + album;
	console.log(req);
	sendRequest(req, albumHandler);
	return false;
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
	gebi('album_created').innerHTML = album.ctime;
	gebi('album_expires').innerHTML = album.dtime;
	gebi('album_update').onclick = function() { updateAlbum(album.album) };
	var images = album.images;
	var out = '<tr><td>&nbsp;</td></tr><tr>';
	for (var i = 0; i < images.length; i++) {
		out += '<td class="image">';
		out += '<a href="' + images[i].image + '">';
		out += '<img src="' + images[i].thumb + '">';
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
		back.onclick = function() { loadAlbum(album.album, (album.start - IMAGES_PER_PAGE)) };
	} else {
		back.style.visibility = 'hidden';
	}
	var next = gebi('next');
	if (album.start + IMAGES_PER_PAGE < album.total) {
		next.style.visibility = 'visible';
		next.onclick = function() { loadAlbum(album.album, (album.start + IMAGES_PER_PAGE)) };
	} else {
		next.style.visibility = 'hidden';
	}
}

function getAllAlbumUrl(start) {
	var req = 'view.cgi';
	req += '?view_all=true';
	req += '&start='   + start;
	req += '&count='   + (start + ALBUMS_AT_ONCE);
	req += '&preview=' + ALBUM_PREVIEW_SIZE;
	return req;
}
function loadAllAlbums(start, count) {
	if (start == undefined) start = 0;
	if (count == undefined) count = ALBUMS_AT_ONCE;
	sendRequest(getAllAlbumUrl(start), allAlbumsHandler);
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
	for (var a = 0; a < json.albums.length; a++) {
		album = json.albums[a];
		out += '<table class="page"><tr><td class="section_title" colspan="20">';
		out += '<a class="album_title" href="#' + album.album + '">';
		out += '' + album.album + ' (' + album.total + ' images)';
		out += '</a><br>';
		out += '</td></tr><tr>';
		for (var i = 0; i < album.images.length; i++) {
			var image = album.images[i].image;
			var thumb = album.images[i].thumb;
			out += '<td class="image">';
			out += '<a href="' + image + '">';
			out += '<img src="' + thumb + '">';
			out += '</a>';
			out += '</td>';
		}
		out += '</tr></table>';
	}
	gebi('albums_table').innerHTML = out;
	
	gebi('nav_info').innerHTML = 'albums ' + (json.start + 1) + '-' + (json.start + json.albums.length) + ' of ' + json.total;
	var back = gebi('back');
	if (json.start > 0) {
		back.style.visibility = 'visible';
		back.onclick = function() { loadAllAlbums((json.start - ALBUMS_AT_ONCE)) };
	} else {
		back.style.visibility = 'hidden';
	}
	var next = gebi('next');
	if (json.start + IMAGES_PER_PAGE < json.total) {
		next.style.visibility = 'visible';
		next.onclick = function() { loadAllAlbums((json.start + ALBUMS_AT_ONCE)) };
	} else {
		next.style.visibility = 'hidden';
	}
	
	/*
	var back = gebi('back');
	if (album.start > 0) {
		back.style.visibility = 'visible';
		back.onclick = sendRequest(getAllAlbumsUrl(album.start - ALBUMS_AT_ONCE));
	} else {
		back.style.visibility = 'hidden';
	}
	var next = gebi('next');
	if (album.start + ALBUMS_AT_ONCE < album.total) {
		next.style.visibility = 'visible';
		next.onclick = sendRequest(getAllAlbumsUrl(album.start + ALBUMS_AT_ONCE));
	} else {
		next.style.visibility = 'hidden';
	}
	*/
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
	window.location.reload(true);
}

window.onload = init;

window.onpopstate = function(event) {
	init();
};

