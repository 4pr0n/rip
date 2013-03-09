/////////////////////
// STRING PROTOTYPES
// Set new string prototype for 'trim()'
if (typeof (String.prototype.trim) === "undefined") {
	String.prototype.trim = function() {
		return String(this).replace(/^\s+|\s+$/g, '');
	};
}

// Shortened version of getElementById
function gebi(id) {
	return document.getElementById(id);
}

// Display output to user (via status bar)
function statusbar(txt) {
	txt = txt.replace(/\n/g, '');
	gebi("status_bar").innerHTML = txt;
}

statusbar("loading javascript...");

// Imgur validation
function isImgurAlbum(txt) {
	if (txt.indexOf('imgur.com') == -1) return '';
	if (txt.indexOf('i.imgur.com') != -1) return '';
	if (txt.indexOf('/a/') == -1 && txt.indexOf('.imgur.com') == -1) return '';
	if (txt.indexOf('#') >= 0) txt = txt.substr(0, txt.indexOf('#'));
	if (txt.indexOf('/') == -1) return '';
	if (txt.substr(txt.length - 1) == '/') txt = txt.substr(0, txt.length - 1);
	if (txt.indexOf('/') == -1) return '';
	var album = txt.substr(txt.lastIndexOf('/') + 1);
	if (txt.indexOf('/a/') >= 0 && album.length != 5) return '';
	return 'imgur album: ' + album;
}

// DeviantArt validation
function isDAAlbum(txt) {
	if (txt.indexOf('.deviantart.com') == -1) return '';
	var album = txt.substr(0, txt.indexOf('.'));
	album = album.replace('http://', '');
	if (album === '') return '';
	return 'deviantart album: ' + album;
}

// Tumblr validation
function isTumblrAlbum(txt) {
	if (txt.indexOf('.tumblr.com') == -1) return '';
	var album = txt.substr(0, txt.indexOf('.tumblr'));
	album = album.replace('http://', '');
	if (album === '') return '';
	if (txt.indexOf('/tagged/') == -1) {
		return 'tumblr albums must have /tagged/ in url!';
	}
	return 'tumblr album: ' + album;
}

// Twitter validation
function isTwitterAlbum(txt) {
	if (txt.indexOf('twitter.com/') == -1) return '';
	var album = txt.substr(txt.indexOf('twitter.com/') + 12);
	if (album.indexOf('/') >= 0) {
		album = album.substr(0, album.indexOf('/'));
	}
	if (album === '') return '';
	return 'twitter album: ' + album;
}

// Getgonewild validation
function isGetgonewildAlbum(txt) {
	if (txt.indexOf('getgonewild.com/profile/') == -1) return '';
	var album = txt.substr(txt.indexOf('/profile/') + 9);
	if (album === '') return '';
	return 'getgonewild album: ' + album;
}

// Photobucket Validation
function isPBAlbum(txt) {
	return '';
	if (txt.indexOf('photobucket.com') == -1) return '';
	txt = txt.replace('http://', '');
	if (txt.indexOf('#') >= 0) txt = txt.substr(0, txt.indexOf('#'));
	if (txt.indexOf('?') >= 0) txt = txt.substr(0, txt.indexOf('?'));
	if (!txt.substr(txt.length - 1) === '/') txt += '/';
	var album = '';
	if (txt.indexOf('/profile/') >= 0) {
		album = txt.substr(txt.indexOf('/profile/') + 9);
		album = album.replace('/');
	
	} else if (txt.indexOf('/albums/') >= 0) {
		var i = txt.indexOf('/');
		var j = txt.indexOf('/', i+1);
		var k = txt.indexOf('/', j+1);
		var l = txt.indexOf('/', k+1);
		album = txt.substr(k + 1, l - k - 1);
	}
	if (album === '') return '';
	return 'photobucket album: ' + album;
}	

// Flickr validation
function isFlickrAlbum(txt) {
	if (txt.indexOf('flickr.com') == -1) return '';
	if (txt.indexOf('/photos/') == -1) return '';
	if (txt.indexOf('?') >= 0) txt = txt.substr(0, txt.indexOf('?'));
	var album = txt.substr(txt.indexOf('/photos/') + 8);
	if (album.indexOf('/') >= 0) album = album.substr(0, album.indexOf('/'));
	return album;
}

// Imagevenue validation
function isIVAlbum(txt) {
	if (txt.indexOf('imagevenue.com') == -1) return '';
	var album = 'imagevenue album';
	if (txt.indexOf('?image=') >= 0) {
		txt = txt.substr(txt.indexOf('?image=')+7);
		txt = txt.substr(0, txt.indexOf('_'));
		//txt = txt.substr(0, txt.indexOf('.'));
		album = 'imagevenue album: ' + txt;
	}
	return album;
}

// Imagebam validation
function isIBAlbum(txt) {
	if (txt.indexOf('imagebam.com') == -1) return '';
	return 'imagebam album';
}

// Imagefap validation
function isIFAlbum(txt) {
	if (txt.indexOf('imagefap.com') == -1) return '';
	var album = 'imagefap album';
	if (txt.indexOf('/pictures/') >= 0) {
		txt = txt.substr(txt.indexOf('/pictures/') + 10);
		txt = txt.replace(/\//g, '_');
		album = 'imagefap album: ' + txt;
	}
	return album;
}

// Parse URL box, check if album is valid, update site ID bar.
function urlboxChange() {
	var txt = gebi('album_url').value;
	var site;
	site = isImgurAlbum(txt);
	if (site === '') site = isDAAlbum(txt);
	if (site === '') site = isPBAlbum(txt);
	if (site === '') site = isFlickrAlbum(txt);
	if (site === '') site = isIVAlbum(txt);
	if (site === '') site = isIBAlbum(txt);
	if (site === '') site = isIFAlbum(txt);
	if (site === '') site = isTumblrAlbum(txt);
	if (site === '') site = isTwitterAlbum(txt);
	if (site === '') site = isGetgonewildAlbum(txt);
	if (site === '') site = '&nbsp;'
	
	gebi('siteid').innerHTML = site;
	// Recursive call back every 1/4th of a sec
	setTimeout('urlboxChange()', 250);
}
// Start recursive timeouts
urlboxChange();

// Start rip when user presses enter key
function urlboxKeyUp(evt) {
	var theEvent = evt || window.event;
	var key = theEvent.keyCode || theEvent.which;
	key = String.fromCharCode( key );
	if (theEvent.keyCode == 13) {
		buttonClick();
	}
}

// Create new XML request object
function makeHttpObject() {
	try { return new XMLHttpRequest();
	} catch (error) {}
	try { return new ActiveXObject("Msxml2.XMLHTTP");
	} catch (error) {}
	try { return new ActiveXObject("Microsoft.XMLHTTP");
	} catch (error) {}
	throw new Error("Could not create HTTP request object.");
}

// Handle button click; send request to server
function buttonClick() {
	statusbar("loading...");
	var url = '?url=' + escape(gebi("album_url").value);
	var request = makeHttpObject();
	var waitingInterval;
	waitingInterval = setInterval('checkRip()', 500);
	request.open("GET", 'grab.cgi' + url, true);
	request.send(null);
	request.onreadystatechange = function() {
		if (request.readyState == 4) { 
			clearInterval(waitingInterval);
			if (request.status == 200) {
				var resp = request.responseText;
				statusbar('<b>' + resp + '</b>');
			} else
				statusbar("Failure! Status code:  " + request.status);
		}
	}
}

// Periodically query the server for new information
function checkRip() {
	var url = '?url=' + escape(gebi("album_url").value);
	var request = makeHttpObject();
	var waitingInterval;
	request.open("GET", 'status.cgi' + url, true);
	request.send(null);
	request.onreadystatechange = function() {
		if (request.readyState == 4) { 
			if (request.status == 200) {
				var resp = request.responseText.replace(/\n/g, '').trim();
				if (resp !== '') {
					statusbar('status: ' + resp + '');
				}
			} else
				statusbar("Failure! Status code:  " + request.status);
		}
	}
}

// Clear statusbar
statusbar("&nbsp;");

