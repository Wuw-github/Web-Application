/*
var category = [{"id": 1, "title": "cloth", "budget": 200, "spend": 0}, {"id": 2, "title": "eat", "budget": 200, "spend": 0}, {"id": 3, "title": "food", "budget": 200, "spend": 0}];
var purchase = [{"cat_id": 1, "description": "nike", "amount": 100, "month": 11}, {"cat_id": 1, "description": "adi", "amount": 400, "month": 11},
				{"cat_id": 2, "description": "nike", "amount": 400, "month": 11}];
*/
var category = [];
var purchase = [];
var uncategorized = 0;
function setup() {
	document.getElementById("catButton").addEventListener("click", addCategory, true);
	document.getElementById("purButton").addEventListener("click", addPurchase, true);
	// initialize the table
	poller();
}

/***********************************************************
 * AJAX boilerplate
 ***********************************************************/
function makeRec(method, target, retCode, handlerAction, data) {
	var httpRequest = new XMLHttpRequest();

	if (!httpRequest) {
		alert('Giving up :( Cannot create an XMLHTTP instance');
		return false;
	}

	httpRequest.onreadystatechange = makeHandler(httpRequest, retCode, handlerAction);
	httpRequest.open(method, target);

	if (data) {
		httpRequest.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
		httpRequest.send(data);
	}
	else {
		httpRequest.send();
	}
}


function makeHandler(httpRequest, retCode, action) {
	//console.log("making handler!");
	function handler() {
		if (httpRequest.readyState === XMLHttpRequest.DONE) {
			if (httpRequest.status === retCode) {
				console.log("recieved response text:  " + httpRequest.responseText);
				if(action.length > 1){
					action[0](httpRequest.responseText);
					action[1]();
				}
				else{
					action(httpRequest.responseText);
				}
			} else {
				alert("There was a problem with the request.  you'll need to refresh the page!");
				if(action.length > 1){
					action[2]();
				}
			}
		}
	}
	return handler;
}
/*******************************************************
 * actual client-side app logic
 *******************************************************/
function poller() {
	console.log("in poller")
	const myPromiseA = new Promise((resolve, reject) => { makeRec("GET", "/cats", 200, [init_cat, resolve, reject]); })
	myPromiseA.then(() => { makeRec("GET", "/purchases", 200, init_pur); })

	//makeRec("GET", "/cats", 200, init_cat);
	//makeRec("GET", "/purchases", 200, init_pur);
}

function addCategory() {
	//window.clearTimeout(timeoutID);
	var title = document.getElementById("title").value;
	var budget = document.getElementById("budget").value;
	var data = "title=" + title + "&budget=" + budget;
	makeRec("POST", "/cats", 201, poller, data);
	document.getElementById("title").value = "";
	document.getElementById("budget").value = "";
}

function addPurchase(){
	//window.clearTimeout(timeoutID);
	var cat = document.getElementById("category").value;
	var amount = document.getElementById("amount").value;
	var description = document.getElementById("description").value;
	var date = document.getElementById("date").value;
	var data = "cat="+cat+"&amount="+amount+"&des="+description+"&date="+date;
	makeRec("POST", "/purchases", 201, poller, data);
	document.getElementById("category").value = "";
	document.getElementById("amount").value = "";
	document.getElementById("description").value = "";
	document.getElementById("date").value = "";
}

function addCell(row, text) {
	var newCell = row.insertCell();
	var newText = document.createTextNode(text);
	newCell.appendChild(newText);
}
function init_cat(responseText){
	console.log("init_cat");
	category = JSON.parse(responseText);
}
function init_pur(responseText){
	console.log("init_pur");
	purchase = JSON.parse(responseText);
	calculate_budget_purchase();
	repopulate_cat();
	repopulate_pur();
}
function repopulate_pur(){
	console.log("repopulating purchase");
	console.log(purchase);
}
function delete_cat(cat_id){
	makeRec("DELETE", "/cats/" + cat_id, 204, poller);
}
function repopulate_cat(){
	console.log("repopulating category");
	console.log(category);
	var table = document.getElementById("catTable");
	var newRow, newCell, header, body;
	while (table.rows.length > 0) {
		table.deleteRow(0);
	}
	
	header = table.createTHead();
	newRow = header.insertRow();
	addCell(newRow, "Title");
	addCell(newRow, "Budget");
	addCell(newRow, "spend");
	addCell(newRow, "status");
	body = table.createTBody();
	if(category.length > 0){
		for (var i = 0; i < category.length; i++) {
			newRow = body.insertRow();
			addCell(newRow, category[i]["title"])
			addCell(newRow, category[i]["budget"])
			addCell(newRow, category[i]["spend"])
			if (category[i]["budget"] >= category[i]["spend"]){
				addCell(newRow, (category[i]["budget"] - category[i]["spend"]))
			}
			else{
				addCell(newRow, "overspent")
			}
			var newCell = newRow.insertCell();
			var newButton = document.createElement("input");
			newButton.type = "button";
			newButton.value = "delete";
			(function(_t){ newButton.addEventListener("click", function() { delete_cat(_t); }); })(category[i]["id"]);
			newCell.appendChild(newButton);
		}
	}
	else{
		newRow = body.insertRow();
		addCell(newRow, "none");
		addCell(newRow, "none");
		addCell(newRow, "none");
		addCell(newRow, "none");
	}
	
	var uncat = document.getElementById("uncat");
	uncat.value = uncategorized;
	//timeoutID = window.setTimeout(poller, timeout);
}

function add_purchase(p){
	var temp = category.filter(function(cat){ return cat["id"] == p["cat_id"]})
	if(temp[0]!= undefined){
		temp[0]["spend"] = temp[0]["spend"] + p["amount"]
	}
	else{
		uncategorized += p["amount"]
	}
}

function calculate_budget_purchase(){
	var date = new Date();
	var month = date.getMonth() + 1;
	document.getElementById("head").innerText = "Month: " + month;
	uncategorized = 0;
	purchase_filtered = purchase.filter(function(p) { return p["month"] == month })
	category.map(function(cat){ cat["spend"] = 0; });
	purchase_filtered.map(add_purchase);
}

window.addEventListener("load", setup, true);
