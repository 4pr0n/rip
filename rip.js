function gebi(id)        { return document.getElementById(id);    }
function dce(el)         { return document.createElement(el);     }
function strip(text)     { return text.replace(/^\s+|\s+$/g, ''); }
function statusbar(text) { 
	gebi('status_bar').innerHTML = text;
}

// Executes when document has loaded
function init() {
	var url = String(window.location);
  if (url.lastIndexOf('#') >= 0) {
    var link = unescape(url.substring(url.lastIndexOf('#')+1));
		if (link.indexOf('http://') != 0 && link.indexOf('https://') != 0) {
			link = 'http://' + link;
		}
		gebi('rip_text').value = link;
		startRip();
	}
	if (getCookie('cache_enabled') == 'true') {
		gebi('rip_cached').style.display =   'inline-block';
		gebi('label_cached').style.display = 'inline-block';
	} else {
		gebi('rip_cached').style.display =   'none';
		gebi('label_cached').style.display = 'none';
	}
	refreshRecent();
}

function refreshRecent() {
	gebi('recent_spinner').style.visibility = "visible";
	sendRequest('rip.cgi?recent=y', recentHandler);
}

function recentHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	var rec = json['recent'];
	var ul = dce('ul');
	ul.style = 'padding-left: 15px;';
	for (var i = 0; i < rec.length; i++) {
		var li = dce('li');
		li.className = 'recent';
		
		var inpdl = dce('input');
		inpdl.className = 'download_box download_arrow';
		inpdl.style = 'margin: 0px; margin-left: 2px; margin-right: 2px;';
		inpdl.type = 'button';
		inpdl.album = rec[i].url.replace('http://', '').replace('https://', '');
		inpdl.onclick = function() {
			loadAlbum(this.album);
		}
		
		var inpview = dce('input');
		inpview.value = 'view';
		inpview.className = 'download_box';
		inpview.style = 'margin-left: 2px; margin-right: 2px;';
		inpview.type = 'button';
		inpview.album = rec[i].view_url;
		inpview.onclick = function() {
			window.open(this.album);
		}
		
		var a = dce('a');
		a.style = 'padding-left: 3px';
		a.href = rec[i].url;
		a.target = '_BLANK';
		
		var url = rec[i].url.replace('http://www.', '').replace('http://', '').replace('https://', '');
		url = truncate(url, 18);
		a.innerHTML = url;
		
		li.appendChild(inpdl);
		li.appendChild(inpview);
		li.appendChild(a);
		ul.appendChild(li);
	}
	var recent = gebi('recent');
	recent.innerHTML = '';
	recent.appendChild(ul);
	recent.innerHTML += '';
	slowlyShow(recent, 0.0);
	gebi('recent_spinner').style.visibility = "hidden";
}

function albumViewHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	if (json.zip != null) {
		window.open(json.zip.replace('rips/', './rips/#'));
	}
}

// Loads URL in hash and refreshes page
function loadAlbum(url) {
	if (url.indexOf('#') > -1) {
		url = url.substr(0, url.indexOf('#'));
	}
	window.location.href = window.location.pathname + '#' + url;
	window.location.reload(true);
}

// Retrieves cookie
function getCookie(key) {
  var cookies = document.cookie.split(';');
  for (var i in cookies) {
		if (cookies[i].charAt(0) == ' ') {
			cookies[i] = cookies[i].substr(1);
		}
    var pair = cookies[i].split('=');
    if (pair[0] == key)
      return pair[1];
  }
  return "";
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
	if (gebi('rip_urls').checked) {
		query += '&urls_only=true';
	}
	return query;
}

function setHash(url) {
	url = url.replace('http://', '').replace('https://', '')
	url = escape(url).replace(/\//g, '%2F');
	window.location = String(window.location).replace(/\#.*$/, "") + '#' + url;
}

function disableControls() {
	window.onbeforeunload = function() {
		return "Exiting during a rip may cause the archive to become corrupted. Are you sure you want to leave this page?";
	}
	gebi('rip_text').setAttribute('disabled', 'disabled');
	gebi('rip_button').setAttribute('disabled', 'disabled');
}
function enableControls() {
	window.onbeforeunload = null;
	gebi('rip_text').removeAttribute('disabled');
	gebi('rip_button').removeAttribute('disabled');
}

// Start ripping album
function startRip() {
	gebi('status_bar').has_download_link = false;
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
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	
	var statbar = gebi('status_bar');
	if (json.error != null) {
		// ERROR
		var div = dce('div');
		div.className = 'error';
		div.innerHTML = 'error: ' + json.error;
		statbar.innerHTML = '';
		statbar.appendChild(div);
		statbar.innerHTML += '';
		enableControls();
		setProgress(0);
		
	} else if (json.zip != null) {
		// ZIPPED
		var zipurl = json.zip;
		var title  = truncate(json.zip.replace("rips/", ""), 12);
		if (!statbar.has_download_link) {
			statbar.has_download_link = true;
			var center = dce('center');
			
			var adl = dce('a');
			adl.className = 'download_box';
			adl.href = zipurl;
			adl.innerHTML = title;
			
			var span = dce('span');
			span.style = 'font-size: 0.8em;';
			span.innerHTML = '&nbsp;(';
			if (json['image_count'] != null) {
				span.innerHTML += json['image_count'] + '&nbsp;pics,&nbsp;';
			}
			span.innerHTML += json.size + ')';
			adl.appendChild(span);
			center.appendChild(adl);
			
			if (json.limit != null) {
				var diverr = dce('div');
				diverr.className = 'error';
				diverr.style = 'padding-top: 5px';
				diverr.innerHTML = 'rip was capped at ' + json.limit + ' images';
				center.appendChild(diverr);
			}
			
			if (json.album != null) {
				var divdl = dce('div');
				divdl.innerHTML = '<br>';
				var aview = dce('a');
				aview.className = 'download_box';
				aview.href = json.url;
				aview.innerHTML = 'view album';
				divdl.appendChild(aview);
				center.appendChild(divdl);
			}
			
			statbar.innerHTML = '';
			statbar.appendChild(center);
			statbar.innerHTML += '';
			slowlyShow(statbar, 0.0);
		}
			
		enableControls();
		setProgress(0);
		
	} else if (json.log != null) {
		// LOGS
		var update = json.log;
		update = update.replace(/\n/g, '');
		if (update !== '' && 
				gebi('rip_button').hasAttribute('disabled') &&
				!statbar.has_download_link) {
			if (update.indexOf(' - ') >= 0) {
				update = update.substr(0, update.indexOf(' - '));
			}
			i = update.indexOf('(');
			j = update.indexOf(')', i);
			k = update.indexOf('/', i);
			if (i >= 0 && j >= 0 && k >= 0 && k < j) {
				var num = parseFloat(update.substr(i+1, k).replace(',', ''));
				var denom = parseFloat(update.substr(k+1, j));
				setProgress(num / denom);
			}

			var div = dce('div');
			var img = dce('img');
			img.src = 'spinner_dark.gif';
			img.style = 'padding-left: 10px; padding-right: 10px';
			div.appendChild(img);
			var span = dce('span');
			span.innerHTML = update;
			div.appendChild(span);
			statbar.innerHTML = '';
			statbar.appendChild(div);
			statbar.innerHTML += '';
		}
		
		// We only get logs if the file isn't done downloading.
		// Restart the 'check rip' function
		if (gebi('rip_button').hasAttribute('disabled')) {
			setTimeout(function() { checkRip(); }, 500);
		}
	}
}

// Removes middle section of long text, replaces with '...'
function truncate(text, split_size) {
	if (text.length > (split_size * 2) + 3) {
		text = text.substr(0, split_size) + "..." + text.substr(text.length-split_size);
	}
	return text;
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
				throw new Error('request status ' + req.status + ' for URL ' + url);
			}
		}
	}
}

function setExample(site) {
	var dic = {
		'imgur'       : 'http://imgur.com/a/DU74E', //'http://imgur.com/a/RdXNa',
		'tumblr'      : 'http://mourning-sex.tumblr.com/tagged/me',
		'twitter'     : 'https://twitter.com/MrNMissesSmith',
		'deviantart'  : 'http://geekysica.deviantart.com/gallery/40343783',
		'flickr'      : 'https://secure.flickr.com/photos/peopleofplatt/sets/72157624572361792/with/6166517381/',
		'photobucket' : 'http://s1216.beta.photobucket.com/user/Liebe_Dich/profile/',
		'webstagram'  : 'http://web.stagram.com/n/glitterypubez/',
		'imagefap'    : 'http://www.imagefap.com/pictures/2885204/Kentucky-Craigslist',
		'imagearn'    : 'http://imagearn.com/gallery.php?id=1616', // 'http://imagearn.com/gallery.php?id=82587',
		'imagebam'    : 'http://www.imagebam.com/gallery/3b73c0f6ba797e77a33b46779fbfe678/',
		'xhamster'    : 'http://xhamster.com/photos/gallery/1479233/sarah_from_glasgow.html',
		'getgonewild' : 'http://getgonewild.com/profile/EW2d',
		'anonib'      : 'http://www.anonib.com/azn/res/74347.html',
		'oneclickchicks' : 'http://forum.oneclickchicks.com/album.php?albumid=12510',
		'4chan'       : 'http://boards.4chan.org/s/res/14020907',
		'motherless'  : 'http://motherless.com/GC1FEFF5',
		'minus'       : 'http://nappingdoneright.minus.com/mu6fuBNNdfPG0',
		'gifyo'       : 'http://gifyo.com/robynsteen/', // http://gifyo.com/LinzieNeon/',
		'cghub'       : 'http://katiedesousa.cghub.com/images/',
		'chansluts'   : 'http://www.chansluts.com/camwhores/girls/res/3405.php',
		'teenplanet'  : 'http://photos.teenplanet.org/atomicfrog/Latino_M4N/Ass_Beyond_Belief',
		'buttoucher'  : 'http://butttoucher.com/users/Shelbolovesnate',
		'imgbox'      : 'http://imgbox.com/g/UyaOUEBXzO',
		'reddit'      : 'http://reddit.com/user/thatnakedgirl',
		'fuskator'    : 'http://fuskator.com/full/l4IoKiE51-K/1012_chicas123_exotic_landysh_met-art_old+chicks.html#',
		'redditsluts' : 'http://redditsluts.soup.io/tag/Miss_Ginger_Biscuit',
		'kodiefiles'  : 'http://www.kodiefiles.nl/2010/10/ff-eerder-gezien.html',
		'gallerydump' : 'http://www.gallery-dump.com/index.php?gid=553056',
		'fapdu'       : 'http://fapdu.com/cuties-4.view/'
	};
	loadAlbum(dic[site].replace('http://', ''));
	/*
	// Slow fade in
	var r = gebi('rip_text');
	if (!r.hasAttribute('disabled')) {
		darker(r, 0.0);
		r.value = dic[site];
	}
	*/
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

function setProgress(perc) {
	var value;
	if (perc > 1) {
		value = "100";
	} else if (perc < 0) {
		value = "0";
	} else {
		value = "" + (100 * perc);
	}
	if (value == "0") {
		gebi('progress_bar_div').style.display = "none";
	} else if (!isNaN(parseFloat(value)) && isFinite(value)) {
		gebi('progress_bar_div').style.display = "inline-block";
		gebi('progress_bar').value = value;
	}
}

/************************
 * Video stuff
 */
function vidstatusbar(text) { 
	var center = dce('center');
	center.innerHTML = text;
	var vsb = gebi('vid_status_bar');
	vsb.innerHTML = '';
	vsb.appendChild(center);
}

// Start vid download when user presses enter key in textbox
function vidboxKeyUp(evt) {
	var theEvent = evt || window.event;
	var key = theEvent.keyCode || theEvent.which;
	key = String.fromCharCode( key );
	if (theEvent.keyCode == 13) {
		startVid();
	}
}

// Start ripping album
function startVid() {
	vidstatusbar('loading...');
	var query = 'vid.cgi?url=' + encodeURIComponent(gebi('vid_text').value);
	sendRequest(query, vidRequestHandler);
}

// Handles requests (both 'status' and 'start')
function vidRequestHandler(req) {
	var json;
	try {
		json = JSON.parse(req.responseText);
	} catch (error) {
		throw new Error('unable to parse response:\n' + req.responseText);
	}
	
	if (json.error != null) {
		// ERROR
		vidstatusbar('<div class="error">error: ' + json.error + '</div>');
	} else if (json.url != null) {
		// do stuff
		var stat = '';
		stat += '<a class="download_box" href="';
		stat += 'data:text/html;charset=utf-8, ';
		stat += '<html><head><meta http-equiv=\'REFRESH\' content=\'0;url=';
		stat += json.url;
		stat += '\'></head><body><h1>redirecting...</h1></body></html>" ';
		stat += 'rel="noreferrer">redirect to video</a>';
		
		stat += '&nbsp;<a class="download_box" href="';
		stat += json.url;
		stat += '" onclick="return false;">right click, save as</a>';
		
		stat += '<div style="padding-top: 10px;">';
		stat += '<input type="text" class="textbox" value="';
		stat += json.url;
		stat += '" id="video_textarea" onfocus="this.select()" onmouseup="return false" readonly></textarea>';
		vidstatusbar(stat);
	} else {
		vidstatusbar("unexpected stuff!");
	}
}

function showMoreNews() {
	gebi('more_news_link').style.display = 'none';
	gebi('more_news').style.display = 'block';
}

// Call initialization function after entire JS file is parsed
window.onload = init;

