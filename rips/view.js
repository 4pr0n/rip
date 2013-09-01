function gebi(id) { return document.getElementById(id); }
function dce(el)  { return document.createElement(el);  }

var ALBUMS_AT_ONCE             = 6; // Number of albums to return per request
var ALBUM_PREVIEW_SIZE         = 4; // Number of thumbnails per album
var ALBUM_PREVIEW_IMAGE_BREAKS = 4; // Thumbnails per row (all-albums view)
var SINGLE_ALBUM_IMAGE_BREAKS  = 4; // Thumbnails per row (single-album view)
var IMAGES_PER_PAGE            = 8; // Thumbnails per page

// Check if current page has already been loaded
// Some browsers don't call the popupstate event properly, this hopefully fixes it.
var CURRENT_URL = '';
function isNewPage() {
	if (CURRENT_URL === String(window.location)) { return false; }
	CURRENT_URL = String(window.location);
	return true;
}

// Executes when document has loaded
function init() {
	var url = String(window.location);
	if (window.location.hash !== '') {
		// Viewing specific album
		loadAlbum(window.location.hash.substring(1))
	} else {
		// Viewing all albums
		loadAllAlbums();
	}
}

function loadAlbum(album, start, count, startOver) {
	if (!isNewPage() && (startOver == undefined || startOver)) { return true; }
	if (gebi('albums_table').loading == true) { return true; }
	gebi('albums_area').style.display = "none";
	gebi('status_area').style.display = "block";
	gebi('thumbs_area').style.display = "block";
	if (start == undefined) start = 0;
	if (count == undefined) count = IMAGES_PER_PAGE;
	if (startOver == undefined || startOver) {
		gebi('thumbs_table').innerHTML = '';
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
		gebi('album_download_title').style.display = 'none';
		gebi('album_download').style.display = 'none';
		gebi('thumbs_area').style.display = 'none';
		gebi('next').style.visibility = 'hidden';
		return;
	}
	gebi('album_title').innerHTML = album.album + ' (' + album.total + ' images)';
	gebi('album_download').style.display = 'inline';
	gebi('album_download_title').style.display = 'inline';
	gebi('thumbs_area').style.display = 'table';
	var albuma = dce('a');
	albuma.className = 'download_box';
	albuma.href = album.archive;
	albuma.innerHTML = album.archive.replace('./', '');
	gebi('album_download').innerHTML = '';
	gebi('album_download').appendChild(albuma);
	
	// Table to append thumbnails to
	var thumbtable = gebi('thumbs_table');

	var thumbrow = dce('tr');
	var images = album.images;
	for (var i = 0; i < images.length; i++) {
		var thumbtd = dce('td');
		thumbtd.className = 'image';
		var thumba = dce('a');
		thumba.href = images[i].image;
		thumba.onclick = function() {
			return loadImage(this.href);
		};
		var thumbi = dce('img');
		thumbi.src = images[i].thumb;
		thumbi.onload = function() {
			this.style.display = 'inline';
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
	
	var next = gebi('next');
	if (album.start + album.count >= album.total) {
		next.style.visibility = 'hidden';
	} else {
		next.style.visibility = 'visible';
		next.album = album.album;
		next.image_index = album.start + album.count;
		var remaining = album.total - (album.start + album.count);
		next.innerHTML = 'load more (' + remaining + ' images remaining)';
		next.onclick = function() {
			loadAlbum(this.album, this.image_index, IMAGES_PER_PAGE, false);
		}
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
	if (!isNewPage() && (startOver == undefined || startOver)) { return true; }
	if (gebi('albums_table').loading == true) { return true; }
	if (start == undefined) start = 0;
	gebi('albums_area').style.display = "block";
	gebi('status_area').style.display = "none";
	gebi('thumbs_area').style.display = "none";
	gebi('main_table').style.width = "100%";
	gebi('albums_table').loading = true;
	// Remove existing albums if needed
	if (startOver == undefined || startOver) { 
		gebi('albums_table').innerHTML = '';
	}
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
				// Open albums in new tab
				window.open(window.location.origin + window.location.pathname + '#' + this.album);
			}
		}
		var titletr = dce('tr');
		var titletd = dce('td');
		titletd.className = 'all_album_title';
		titletd.setAttribute('colspan', ALBUM_PREVIEW_IMAGE_BREAKS);
		titletd.innerHTML = album.album + ' (' + album.total + ' images)';
		titletr.appendChild(titletd);
		table.appendChild(titletr);

		// Spacing so table doesn't resize when images load
		var spacetr = dce('tr');
		for (var i = 0; i < ALBUM_PREVIEW_IMAGE_BREAKS; i++) {
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
				if (this.width > 100) {
					this.width *= 0.5;
				}
				this.onload = null;
				this.style.display = 'inline';
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
	var albums_table = gebi('albums_table');
	albums_table.appendChild(maintable);
	albums_table.loading = false;
	
	// "Next" button
	var next = gebi('next');
	if (json.start + json.count >= json.total) {
		next.style.visibility = 'hidden';
	} else {
		next.style.visibility = 'visible';
		next.album_index = json.start + json.count
		var remaining = json.total - (json.start + json.count);
		next.innerHTML = 'load more (' + remaining + ' albums remaining)';
		next.onclick = function() {
			loadAllAlbums(this.album_index, false);
		}
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

// Image functions

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
