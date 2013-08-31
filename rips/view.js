function gebi(id) { return document.getElementById(id); }
function dce(el)  { return document.createElement(el);  }

var SINGLE_ALBUM_IMAGE_BREAKS = 4;
var ALBUM_PREVIEW_SIZE = 4;
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
	sendRequest(req, albumHandler);
	return true;
}

function isNewPage() {
	if (CURRENT_URL === String(window.location)) { return false; }
	CURRENT_URL = String(window.location);
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
	out = out; //'<tr>' + out + '</tr>';
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

function loadAllAlbums(start, startOver) {
	if (!isNewPage()) { return true; }
	gebi('albums_area').style.display = "block";
	gebi('status_area').style.display = "none";
	gebi('thumbs_area').style.display = "none";
	gebi('main_table').style.width = "100%";
	// Remove existing albums if needed
	if (startOver == undefined || startOver) gebi('albums_table').innerHTML = '';
	if (start == undefined) start = 0;
	window.location.hash = 'start=' + start;
	sendRequest(getAllAlbumUrl(start), allAlbumsHandler);
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
		var album = json.albums[a];
		var table = dce('table');
		table.className = 'page album';
		table.setAttribute('id',album.album);
		table.album = album.album;
		table.show_album = true;
		table.onclick = function() {
			if (this.show_album) {
				window.location.hash = this.album;
			}
		}
		var titletr = dce('tr');
		var titletd = dce('td');
		titletd.className = 'section_title';
		titletd.setAttribute('colspan', SINGLE_ALBUM_IMAGE_BREAKS);
		titletd.innerHTML = album.album + ' (' + album.total + ' images)';
		titletr.appendChild(titletd);
		table.appendChild(titletr);

		// Spacing so table doesn't resize when images load
		var spacetr = dce('tr');
		for (var i = 0; i < SINGLE_ALBUM_IMAGE_BREAKS; i++) {
			var spacetd = dce('td');
			spacetd.style.width = '105px';
			spacetd.style.height = '0px';
			spacetr.appendChild(spacetd);
		}
		table.appendChild(spacetr);

		var imgrow = dce('tr');
		for (var i = 0; i < album.images.length; i++) {
			
			var imgtd = dce('td');
			imgtd.className = 'image';
			
			var imga = dce('a');
			imga.album = album.album;
			imga.href = album.images[i].image;
			imga.onclick = function() {
				return loadImage(this.href);
			}
			imga.onmouseover = function() {
				gebi(this.album).show_album = false;
			}
			imga.onmouseout = function() {
				gebi(this.album).show_album = true;
			}
			var img = dce('img');
			img.src = album.images[i].thumb;
			img.onload = function() {
				if (this.width > 100) 
					this.width *= 0.5;
				this.onload = null;
				this.style.display = 'inline';
			}
			imga.appendChild(img);
			imgtd.appendChild(imga);
			imgrow.appendChild(imgtd);
			if ((i + 1) % SINGLE_ALBUM_IMAGE_BREAKS == 0 && i != album.images.length - 1) {
				table.appendChild(imgrow);
				imgrow = dce('tr');
			}
		}
		var spacetdh = dce('td');
		spacetdh.style.height = '105px';
		spacetdh.style.width = '0px';
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
	gebi('albums_table').appendChild(maintable);
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
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	if (json.error != null) throw new Error("error: " + json.error);
	if (json.date != null) {
		gebi('album_created').innerHTML = json.date;
	}
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
