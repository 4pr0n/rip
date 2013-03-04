function gebi(id)        { return document.getElementById(id);    }
function strip(text)     { return text.replace(/^\s+|\s+$/g, ''); }
function statusbar(text) { gebi('status_bar').innerHTML = text;   }

// Executes when document has loaded
function init() {
	// TODO do something?
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

// Start ripping album
function startRip() {
	statusbar('loading...');
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
		statusbar('error: ' + json.error);
		
	} else if (json.zip != null) {
		// ZIPPED
		statusbar('download rip: <a class="box" href="' + json.zip + '">' + json.zip + '</a> (' + json.size + ')');
		
	} else if (json.log != null) {
		// LOGS
		var update = json.log;
		update = update.replace(/\n/g, '');
		if (update !== '') {
			if (update.indexOf(' - ') >= 0) {
				update = update.substr(0,update.indexOf(' - '));
			}
			statusbar(update);
		}
		// We only get logs if the file isn't done downloading.
		// Restart the 'check rip' function
		setTimeout(function() { checkRip(); }, 500);
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

// Call initialization function after entire JS file is parsed
window.onload = init;
