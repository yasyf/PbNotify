var id = "";
var endpoint = "https://pbnotify.herokuapp.com/api/"
var needToSend = false;
var getting = false;
var source, message;
var requested = false;
var init = false;

function dump(arr,level) {
	var dumped_text = "";
	if(!level) level = 0;
	
	//The padding given at the beginning of the line.
	var level_padding = "";
	for(var j=0;j<level+1;j++) level_padding += "    ";
	
	if(typeof(arr) == 'object') { //Array/Hashes/Objects 
		for(var item in arr) {
			var value = arr[item];
			
			if(typeof(value) == 'object') { //If it is an array,
				dumped_text += level_padding + "'" + item + "' ...\n";
				dumped_text += dump(value,level+1);
			} else {
				dumped_text += level_padding + "'" + item + "' => \"" + value + "\"\n";
			}
		}
	} else { //Stings/Chars/Numbers etc.
		dumped_text = "===>"+arr+"<===("+typeof(arr)+")";
	}
	return dumped_text;
}

function markNotificationRead() {
  var response;
  var req = new XMLHttpRequest();
  req.open('GET', endpoint + "notification/delivered/" + id, true);
  req.onload = function(e) {
    if (req.readyState == 4) {
      if(req.status == 200) {
        //console.log(req.responseText);
      } 
    }
  }
  req.send(null);
}


function savePebbleID() {
  var response;
  var req = new XMLHttpRequest();
  req.open('GET', endpoint + "account/token/" + id + "/" + Pebble.getAccountToken(), true);
  req.onload = function(e) {
    if (req.readyState == 4) {
      if(req.status == 200) {
        //console.log(req.responseText);
      } 
    }
  }
  req.send(null);
}

function getIDFromPebble() {
  var response;
  var req = new XMLHttpRequest();
  req.open('GET', endpoint + "account/userid/" + Pebble.getAccountToken(), true);
  req.onload = function(e) {
    if (req.readyState == 4) {
      if(req.status == 200) {
        response = JSON.parse(req.responseText);
        if (response) {
          if(response[1] == "userid"){
          	id = response[2];
          	//console.log("Set Identifier: " + id);
          }
          else{
          	//console.log(dump(response));
          	requestConfig();
          }
       	}
      } 
    }
  }
  req.send(null);
}

function getNotification() {
  if(getting == true || id == ""){
  	return;
  }
  else{
  	getting = true;
  }
  var response;
  var req = new XMLHttpRequest();
  req.open('GET', endpoint + "notification/get/" + id, true);
  req.onload = function(e) {
    if (req.readyState == 4) {
      if(req.status == 200) {
        //console.log(req.responseText);
        response = JSON.parse(req.responseText);
        if (response) {
          if(response[1] != "error" && (source != response[2] || message != response[4])){
	          source = response[2];
            message = response[4];
	          //console.log("Source: "+ source);
	          //console.log("Message: "+ message);
	          needToSend = true;
          }
          else{
            if(source == response[2] && message == response[4]){
              markNotificationRead();
              //console.log("Marking Duplicate As Read");
            }
            else{
              //console.log("No New Messages");
            }
          }
       	}
      } else {
        //console.log("Error");
      }
    }
  }
  req.send(null);
  getting = false;
}

function sendNotification(){
  if(needToSend == false){
    return
  }
  else{
    needToSend = false;
  }
  Pebble.sendAppMessage({
    "source":source,
    "message":message},
    function(e) {
	    //console.log("Successfully delivered message with transactionId=" + e.data.transactionId);
	    markNotificationRead();
	    Pebble.showSimpleNotificationOnPebble(source, message);
	},
  	function(e) {
      needToSend = true;
	    //console.log("Unable to deliver message with transactionId=" + e.data.transactionId + dump(e));
  	});
}

function processNotification(){
	if(needToSend == true){
		sendNotification();
	}
}

function config(){
	if(id != ""){
    //console.log("Set Identifier: " + id);
		return;
	}
	if(Pebble.getAccountToken() != ""){
		//console.log("Getting Identifier From Pebble Token");
		getIDFromPebble(); 
	}else{
    //console.log("Requesting Config");
		requestConfig();
	}
}

function requestConfig(){
  if(requested == true || init == false){
    return;
  }
  else{
    requested = true;
  }
  source = "PbNotify";
  message = "Please Configure PbNotify On Your Mobile Device";
  needToSend = true;
}


Pebble.addEventListener("ready",
  function(e) {
	  if(e.ready){
      init = true;
	  	//console.log("JavaScript app ready and running!");
		  //console.log("Pebble Account Token: " + Pebble.getAccountToken());
      setTimeout(config,1000);
      setInterval(processNotification,1000);
      setInterval(getNotification,10000); 
	  }
	  else{
		  //console.log("Ready Listener: "+ e.type);
	  }                          
  }
);
Pebble.addEventListener("appmessage",
  function(e) {
    //console.log("Received message: " + dump(e.payload));
    if(e.payload.command == "1"){
      getNotification();
    }
  }
);
Pebble.addEventListener("showConfiguration",
  function() {
    Pebble.openURL("https://pbnotify.herokuapp.com/config/pebble");
  }
);

Pebble.addEventListener("webviewclosed",
  function(e) {
    id = e.response;
    //console.log("Set Identifier: " + id);
    savePebbleID();
    source = "PbNotify";
    message = "No Messages";
    needToSend = true;
  }
);