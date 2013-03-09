function gebi(id)        { return document.getElementById(id);    }
function strip(text)     { return text.replace(/^\s+|\s+$/g, ''); }
function statusbar(text) { 
	gebi('status_bar').innerHTML = text;
}

// Executes when document has loaded
function init() {
	var url = String(window.location);
  if (url.lastIndexOf('#') >= 0) {
    var link = url.substring(url.lastIndexOf('#')+1);
		gebi('rip_text').value = 'http://' + unescape(link);
		startRip();
	}
}

function getQueryString(start) {
	var url = escape(gebi('rip_text').value);
	var query = 'rip.cgi?url=' + url;
	if (start == true) {
		query += '&start=true';
		if (!gebi('rip_cached').checked) {
			query += '&cached=false';
		}
	} else {
		query += '&check=true';
	}
	return query;
}

function setHash(url) {
	url = url.replace('http://', '').replace('https://', '')
	url = escape(url).replace(/\//g, '%2F');
	window.location = String(window.location).replace(/\#.*$/, "") + '#' + url;
}

function disableControls() {
	gebi('rip_text').setAttribute('disabled', 'disabled');
	gebi('rip_button').setAttribute('disabled', 'disabled');
}
function enableControls() {
	gebi('rip_text').removeAttribute('disabled');
	gebi('rip_button').removeAttribute('disabled');
}

// Start ripping album
function startRip() {
	disableControls();
	setHash(gebi('rip_text').value);
	statusbar('<img src="spinner_dark.gif">&nbsp;loading...');
	var query = getQueryString(true);
	sendRequest(query, requestHandler);
	setTimeout(function() { checkRip(); }, 500);
}

// Handles requests (both 'status' and 'start')
function requestHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		console.log('unable to parse response:\n' + req.responseText);
		throw new Error('unable to parse response:\n' + req.responseText);
		return;
	}
	
	if (json.error != null) {
		// ERROR
		statusbar('<div class="error">error: ' + json.error + '</div>');
		enableControls();
	} else if (json.zip != null) {
		// ZIPPED
		var zipurl = json.zip;
		var title  = json.zip;
		var split_size = 15;
		if (title.length > (split_size * 2) + 3) {
			title = title.substr(0, split_size) + "..." + title.substr(title.length-split_size);
		}
		if (gebi('status_bar').innerHTML.indexOf('class="box" href="') < 0) {
			var result = '<center><a class="box" href="' + zipurl + '">';
			result += title + '</a>';
			if (json['image_count'] != null) {
				result += ' (' + json['image_count'] + ' pics @ ' + json.size + ')';
			} else {
				result += ' (' + json.size + ')';
			}
			if (json.limit != null) {
				result += '<br><div class="error" style="padding-top: 5px;">rip was capped at ' + json.limit + ' images</div>';
			}
			statusbar(result);
			slowlyShow(gebi('status_bar'), 0.0);
		}
		enableControls();
		
	} else if (json.log != null) {
		// LOGS
		var update = json.log;
		update = update.replace(/\n/g, '');
		if (update !== '') {
			if (update.indexOf(' - ') >= 0) {
				update = update.substr(0,update.indexOf(' - '));
			}
			update = '<img src="spinner_dark.gif">&nbsp;' + update;
			statusbar(update);
		}
		// We only get logs if the file isn't done downloading.
		// Restart the 'check rip' function
		if (gebi('rip_button').hasAttribute('disabled')) {
			setTimeout(function() { checkRip(); }, 500);
		}
	}
}

// Check the status of the currently-ripping album
function checkRip() {
	var query = getQueryString(false);
	sendRequest(query, requestHandler);
}

// Start rip when user presses enter key in textbox
function ripboxKeyUp(evt) {
	var theEvent = evt || window.event;
	var key = theEvent.keyCode || theEvent.which;
	key = String.fromCharCode( key );
	if (theEvent.keyCode == 13) {
		startRip();
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

function setExample(site) {
	var dic = {
		'imgur'       : 'http://imgur.com/a/4Qflh', //'http://imgur.com/a/RdXNa',
		'tumblr'      : 'http://mourning-sex.tumblr.com/tagged/me',
		'twitter'     : 'https://twitter.com/PBAprilLewis',
		'deviantart'  : 'http://geekysica.deviantart.com/gallery/40343783',
		'flickr'      : 'https://secure.flickr.com/photos/peopleofplatt/sets/72157624572361792/with/6166517381/',
		'photobucket' : 'http://s1069.beta.photobucket.com/user/mandymgray/library/Album%203',
		'webstagram'  : 'http://web.stagram.com/n/glitterypubez/',
		'imagefap'    : 'http://www.imagefap.com/pictures/2885204/Kentucky-Craigslist',
		'imagearn'    : 'http://imagearn.com/gallery.php?id=82587',
		'imagebam'    : 'http://www.imagebam.com/gallery/3b73c0f6ba797e77a33b46779fbfe678/',
		'xhamster'    : 'http://xhamster.com/photos/gallery/1479233/sarah_from_glasgow.html',
		'getgonewild' : 'http://getgonewild.com/profile/EW2d'
	};
	// Slow fade in
	var r = gebi('rip_text');
	if (!r.hasAttribute('disabled')) {
		darker(r, 0.0);
		r.value = dic[site];
	}
	return false;
}

function darker(obj, alpha) {
	obj.style.color = "rgba(0, 0, 0, " + alpha + ")";
	alpha += 0.01;
	if (alpha > 1) {
		obj.style.color = "#000";
	} else {
		setTimeout(function() { darker(obj, alpha); } , 5);
	}
}

function slowlyShow(obj, alpha) {
	obj.style.opacity = alpha;
	obj.style.filter  = "alpha(opacity=" + (alpha * 100) + ")";
	alpha += 0.02;
	if (alpha > 1) {
		obj.style.opacity = "1";
	} else {
		setTimeout(function() { slowlyShow(obj, alpha); } , 5);
	}
}

// Call initialization function after entire JS file is parsed
window.onload = init;
