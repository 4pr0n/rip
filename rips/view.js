function gebi(id) { return document.getElementById(id); }

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
	if (count == undefined) count = 20;
	var req = 'view.cgi';
	req += '?start=' + start;
	req += '&count=' + count;
	req += '&view=' + album;
	sendRequest(req, albumHandler);
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
	gebi('album_title').innerHTML = album.album + ' (' + album.count + ' images)';
	gebi('album_download').innerHTML = '<a class="download_box" href="' + album.archive + '">' + album.archive + '</a>';
	gebi('album_created').innerHTML = album.ctime;
	gebi('album_expires').innerHTML = album.dtime;
	gebi('album_update').onclick = function() { updateAlbum(album.album) };
	var images = album.images;
	var out = '';
	for (var i = 0; i < images.length; i++) {
		out += '<td>';
		out += '<a href="' + images[i].image + '">';
		out += '<img src="' + images[i].thumb + '">';
		out += '</a>';
		out += '</td>';
		if (i % 5 == 0 && i != 0 && i != images.length - 1) {
			out += '</tr><tr>';
		}
	}
	out = '<tr>' + out + '</tr>';
	gebi('thumbs_table').innerHTML = out;
}

function loadAllAlbums() {
	sendRequest('view.cgi?view_all=true', allAlbumsHandler);
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
		out += '<table class="page"><tr><td>';
		out += '<a href="#' + album.album + '">';
		out += '<h3>' + album.album + ' (' + album.count + ' images)</h3>';
		out += '</a>';
		for (var i = 0; i < album.images.length; i++) {
			var image = album.images[i].image;
			var thumb = album.images[i].thumb;
			out += '<a href="' + image + '">';
			out += '<img src="' + thumb + '">';
			out += '</a>';
		}
		out += '</td></tr></table>';
	}
	gebi('albums_table').innerHTML = out;
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

