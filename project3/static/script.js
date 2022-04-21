var timeoutID;
var timeout = 1000;

function setup() {
	document.getElementById("submitButton").addEventListener("click", makePost, true);
	//document.getElementById("leaveButton").addEventListener("click", leaveRoom, true);
	timeoutID = window.setTimeout(poller, timeout);
}

function leaveRoom() {
	window.clearTimeout(timeoutID);
	var httpRequest = new XMLHttpRequest();
	if (!httpRequest) {
		alert('Giving up :( Cannot create an XMLHTTP instance');
		return false;
	}

	httpRequest.open("GET", "/leaveroom");
	httpRequest.send();
}


function makePost() {
	window.clearTimeout(timeoutID);
	var httpRequest = new XMLHttpRequest();

	if (!httpRequest) {
		alert('Giving up :( Cannot create an XMLHTTP instance');
		return false;
	}

	var content = document.getElementById("newcontent").value
	httpRequest.onreadystatechange = function() { handlePost(httpRequest) };
	
	httpRequest.open("POST", "/new_message");
	httpRequest.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');

	var data;
	data = "content=" + content;
	
	httpRequest.send(data);
}

function handlePost(httpRequest) {
	if (httpRequest.readyState === XMLHttpRequest.DONE) {
		if (httpRequest.status === 200) {
			clearInput();
			text = JSON.parse(httpRequest.responseText);
			//console.log("in post text is " + text)
			addRows(JSON.parse(httpRequest.responseText));
			timeoutID = window.setTimeout(poller, timeout);
		} else {
			alert("There was a problem with the post request.");
		}
	}
}

function poller() {
	var httpRequest = new XMLHttpRequest();

	if (!httpRequest) {
		alert('Giving up :( Cannot create an XMLHTTP instance');
		return false;
	}

	httpRequest.onreadystatechange = function() { handlePoll(httpRequest) };
	httpRequest.open("GET", "/getMessages");
	httpRequest.send();
}

function handlePoll(httpRequest) {
	if (httpRequest.readyState === XMLHttpRequest.DONE) {
		if (httpRequest.status === 200) {
			text = JSON.parse(httpRequest.responseText);
			console.log("text is " + text)
			if (text == 500) {
				alert("Current room has been canceled")
				window.location.replace("/leaveroom")
			}
			addRows(text);
			timeoutID = window.setTimeout(poller, timeout);
			
		} else {
			alert("There was a problem with the poll request.  you'll need to refresh the page to recieve updates again!");
		}
	}
}

function addCell(row, text) {
	var newCell = row.insertCell();
	var newText = document.createTextNode(text);
	newCell.appendChild(newText);
}

function addRows(rows){
	var tab = document.getElementById("theTable");
	var newRow, newCell, newText;

	var temp = document.getElementById("noMessage")
	if(temp && rows.length > 0){
		temp.remove();
	}
	for(var i = tab.rows.length; i < rows.length; i++) {
		newRow = tab.insertRow();
		addCell(newRow, rows[i][0]+":");
		addCell(newRow, rows[i][1]);
		addCell(newRow, rows[i][2]);
	}
}

function clearInput() {
	document.getElementById("newcontent").value = "";
}

window.addEventListener("load", setup, true);
